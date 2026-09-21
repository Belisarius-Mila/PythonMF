import AVFoundation
import CryptoKit
import Darwin
import Foundation
import ImageIO

public protocol CaminoStorageCapacityProviding {
    func availableBytes() throws -> Int64
}

public enum CaminoStorageActivity: Equatable, Sendable {
    case text
    case photo
    case audio
    case video
}

public enum CaminoSafetyAction: Equatable, Sendable {
    case allow
    case warn
    case block
    case finish
}

/// Pure policy so thresholds can be exercised without filling a device.
public struct CaminoStorageSafetyPolicy: Sendable {
    public static let warningBytes: Int64 = 2_147_483_648
    public static let operatingReserveBytes: Int64 = 536_870_912
    public static let videoStartBytes: Int64 = 1_073_741_824

    public init() {}

    public func action(for activity: CaminoStorageActivity, availableBytes: Int64,
                       active: Bool = false) -> CaminoSafetyAction {
        if active && (activity == .audio || activity == .video) &&
            availableBytes < Self.operatingReserveBytes {
            return .finish
        }
        if !active {
            switch activity {
            case .video:
                if availableBytes < Self.videoStartBytes { return .block }
            case .photo, .audio:
                if availableBytes < Self.operatingReserveBytes { return .block }
            case .text:
                break
            }
        }
        return availableBytes < Self.warningBytes ? .warn : .allow
    }
}

public enum CaminoThermalLevel: Equatable, Sendable {
    case nominal
    case fair
    case serious
    case critical
}

/// Thermal pressure never changes capture quality behind the user's back.
public struct CaminoThermalSafetyPolicy: Sendable {
    public init() {}

    public func videoAction(for level: CaminoThermalLevel,
                            active: Bool = false) -> CaminoSafetyAction {
        switch level {
        case .nominal, .fair:
            return .allow
        case .serious:
            return .warn
        case .critical:
            return active ? .finish : .block
        }
    }
}

private struct CaminoVolumeCapacityProvider: CaminoStorageCapacityProviding {
    let root: URL

    func availableBytes() throws -> Int64 {
        let values = try root.resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey])
        guard let capacity = values.volumeAvailableCapacityForImportantUsage else {
            throw LocalStoreError.insufficientSpace
        }
        return capacity
    }
}

public struct LocalMediaRecovery: Equatable, Sendable {
    public let repairedCount: Int
    public let pendingCount: Int
    public let orphanCount: Int
    public let missingCount: Int
}

/// Media originals live in Application Support. Pending and final paths are
/// deterministic from an already persisted intent; neither path is overwritten.
@MainActor public final class CaminoMediaVault {
    private let root: URL
    private let metadata: CaminoLocalStore
    private let files = FileManager.default
    private let capacity: any CaminoStorageCapacityProviding
    private let storagePolicy = CaminoStorageSafetyPolicy()

    public init(root: URL, metadata: CaminoLocalStore,
                capacityProvider: (any CaminoStorageCapacityProviding)? = nil) throws {
        self.root = root.standardizedFileURL
        self.metadata = metadata
        self.capacity = capacityProvider ?? CaminoVolumeCapacityProvider(root: root)
        for component in ["Media/Pending", "Media/Originals"] {
            let url = root.appendingPathComponent(component, isDirectory: true)
            try files.createDirectory(at: url, withIntermediateDirectories: true)
            #if os(iOS)
            try files.setAttributes(
                [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
                ofItemAtPath: url.path)
            #endif
        }
    }

    public func availableBytes() throws -> Int64 {
        try capacity.availableBytes()
    }

    public func storageAction(for activity: CaminoStorageActivity,
                              active: Bool = false) throws -> CaminoSafetyAction {
        storagePolicy.action(for: activity, availableBytes: try availableBytes(), active: active)
    }

    /// A working guard, not a promise of remaining video duration.
    public func checkSpace(for kind: LocalMediaKind) throws -> Bool {
        let action = try storageAction(for: kind == .video ? .video : .photo)
        guard action != .block else { throw LocalStoreError.insufficientSpace }
        return action == .warn
    }

    @discardableResult public func savePhoto(_ data: Data, targetMomentID: UUID? = nil,
                                              at date: Date = Date(),
                                              timeZone: TimeZone = .current) async throws -> LocalMediaAsset {
        _ = try checkSpace(for: .photo)
        let intent = try metadata.beginMediaIntent(kind: .photo, targetMomentID: targetMomentID,
                                                   at: date, timeZone: timeZone)
        let pending = url(intent.pendingRelativePath)
        try await Task.detached(priority: .utility) {
            try Self.writeExclusive(data, to: pending)
        }.value
        return try await finalize(intent, interrupted: false)
    }

    /// The movie delegate writes to this create-only pending URL. A sound
    /// capture never silently falls back to video-only when mic access fails.
    public func beginVideo(targetMomentID: UUID? = nil, silent: Bool,
                           at date: Date = Date()) throws -> (LocalMediaIntent, URL, Bool) {
        let lowSpaceWarning = try checkSpace(for: .video)
        let intent = try metadata.beginMediaIntent(kind: .video,
            targetMomentID: targetMomentID, silentRequested: silent, at: date)
        let pending = url(intent.pendingRelativePath)
        guard !files.fileExists(atPath: pending.path),
              !files.fileExists(atPath: url(intent.originalRelativePath).path) else {
            throw LocalStoreError.duplicateIdentity
        }
        return (intent, pending, lowSpaceWarning)
    }

    @discardableResult public func finalize(_ intent: LocalMediaIntent,
                                            interrupted: Bool) async throws -> LocalMediaAsset {
        let pending = url(intent.pendingRelativePath)
        let original = url(intent.originalRelativePath)
        let source = files.fileExists(atPath: original.path) ? original : pending
        guard files.fileExists(atPath: source.path) else { throw LocalStoreError.invalidMedia }
        let inspection: LocalMediaInspection
        if intent.kind == .photo {
            inspection = try await Self.inspectPhoto(source)
        } else {
            inspection = try await Self.inspectVideo(source, interrupted: interrupted,
                                                     silentRequested: intent.silentRequested)
        }
        if source == pending {
            try files.moveItem(at: pending, to: original)
        }
        #if os(iOS)
        try files.setAttributes(
            [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
            ofItemAtPath: original.path)
        #endif
        return try metadata.acceptMedia(intent, inspection: inspection)
    }

    /// Run at launch and on return. A valid pending file is linked; unknown
    /// files and unplayable partial clips remain present for later review.
    public func reconcile() async throws -> LocalMediaRecovery {
        let pending = try metadata.pendingMediaIntents()
        var repaired = 0
        for intent in pending {
            let pendingURL = url(intent.pendingRelativePath)
            let originalURL = url(intent.originalRelativePath)
            guard files.fileExists(atPath: pendingURL.path) ||
                  files.fileExists(atPath: originalURL.path) else { continue }
            if (try? await finalize(intent, interrupted: true)) != nil { repaired += 1 }
        }
        let remaining = try metadata.pendingMediaIntents()
        let assets = try metadata.allMediaAssets()
        let knownPaths = Set(assets.map(\.relativePath))
            .union(remaining.flatMap { [$0.pendingRelativePath, $0.originalRelativePath] })
        let originalFiles = try files.contentsOfDirectory(
            at: url("Media/Originals"), includingPropertiesForKeys: nil)
        let pendingFiles = try files.contentsOfDirectory(
            at: url("Media/Pending"), includingPropertiesForKeys: nil)
        let orphanCount = originalFiles.filter {
            !knownPaths.contains("Media/Originals/" + $0.lastPathComponent)
        }.count + pendingFiles.filter {
            !knownPaths.contains("Media/Pending/" + $0.lastPathComponent)
        }.count
        let missingCount = assets.filter { !files.fileExists(atPath: url($0.relativePath).path) }.count
        return LocalMediaRecovery(repairedCount: repaired, pendingCount: remaining.count,
                                  orphanCount: orphanCount, missingCount: missingCount)
    }

    public func originalURL(for asset: LocalMediaAsset) throws -> URL {
        guard asset.relativePath == "Media/Originals/\(asset.id.uuidString).\(asset.kind.fileExtension)" else {
            throw LocalStoreError.invalidMedia
        }
        let result = url(asset.relativePath)
        guard files.fileExists(atPath: result.path) else { throw LocalStoreError.invalidMedia }
        return result
    }

    private func url(_ relativePath: String) -> URL {
        root.appendingPathComponent(relativePath)
    }

    private nonisolated static func inspectPhoto(_ url: URL) async throws -> LocalMediaInspection {
        try await Task.detached(priority: .utility) {
            guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
                  CGImageSourceGetCount(source) > 0,
                  CGImageSourceGetType(source) as String? == "public.jpeg",
                  let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
                  let width = properties[kCGImagePropertyPixelWidth] as? Int,
                  let height = properties[kCGImagePropertyPixelHeight] as? Int,
                  width > 0, height > 0 else {
                throw LocalStoreError.invalidMedia
            }
            let orientation = properties[kCGImagePropertyOrientation] as? Int ?? 1
            let (bytes, hash) = try digest(url)
            return LocalMediaInspection(byteCount: bytes, sha256: hash,
                width: width, height: height, orientation: orientation,
                durationMilliseconds: nil, hasAudio: false, partial: false)
        }.value
    }

    private nonisolated static func inspectVideo(
        _ url: URL, interrupted: Bool, silentRequested: Bool
    ) async throws -> LocalMediaInspection {
        let asset = AVURLAsset(url: url)
        let duration = try await asset.load(.duration)
        let seconds = CMTimeGetSeconds(duration)
        let videoTracks = try await asset.loadTracks(withMediaType: .video)
        guard seconds.isFinite, seconds > 0, let track = videoTracks.first else {
            throw LocalStoreError.invalidMedia
        }
        let natural = try await track.load(.naturalSize)
        let transform = try await track.load(.preferredTransform)
        let transformed = CGRect(origin: .zero, size: natural).applying(transform)
        let width = Int(abs(transformed.width).rounded())
        let height = Int(abs(transformed.height).rounded())
        guard width > 0, height > 0 else { throw LocalStoreError.invalidMedia }
        let angle = Int((atan2(Double(transform.b), Double(transform.a)) * 180 / .pi).rounded())
        let audioTracks = try await asset.loadTracks(withMediaType: .audio)
        let hasAudio = !audioTracks.isEmpty
        let (bytes, hash) = try await Task.detached(priority: .utility) { try digest(url) }.value
        return LocalMediaInspection(byteCount: bytes, sha256: hash,
            width: width, height: height, orientation: (angle + 360) % 360,
            durationMilliseconds: Int64((seconds * 1_000).rounded()),
            hasAudio: hasAudio, partial: interrupted || (!silentRequested && !hasAudio))
    }

    private nonisolated static func digest(_ url: URL) throws -> (Int64, String) {
        let handle = try FileHandle(forReadingFrom: url)
        defer { try? handle.close() }
        var hash = SHA256()
        var bytes: Int64 = 0
        while let chunk = try handle.read(upToCount: 1_048_576), !chunk.isEmpty {
            hash.update(data: chunk)
            bytes += Int64(chunk.count)
        }
        guard bytes > 0 else { throw LocalStoreError.invalidMedia }
        return (bytes, hash.finalize().map { String(format: "%02x", $0) }.joined())
    }

    private nonisolated static func writeExclusive(_ data: Data, to url: URL) throws {
        let descriptor = Darwin.open(url.path, O_WRONLY | O_CREAT | O_EXCL, 0o600)
        guard descriptor >= 0 else { throw POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO) }
        defer { _ = Darwin.close(descriptor) }
        try data.withUnsafeBytes { buffer in
            guard let base = buffer.baseAddress else { throw LocalStoreError.invalidMedia }
            var written = 0
            while written < buffer.count {
                let count = Darwin.write(descriptor, base.advanced(by: written),
                                         buffer.count - written)
                if count < 0 {
                    if errno == EINTR { continue }
                    throw POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO)
                }
                written += count
            }
        }
        guard Darwin.fsync(descriptor) == 0 else {
            throw POSIXError(POSIXErrorCode(rawValue: errno) ?? .EIO)
        }
    }
}
