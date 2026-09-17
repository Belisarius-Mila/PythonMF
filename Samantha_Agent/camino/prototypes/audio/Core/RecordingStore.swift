import Foundation
#if canImport(Darwin)
import Darwin
#else
import Glibc
#endif

private struct RecordingJournal: Codable, Equatable {
    let schema: Int
    let draftID: UUID
    let checkpoint: SegmentCheckpointPolicy
}

private struct RecordingFinalization: Codable, Equatable {
    let schema: Int
    let draftID: UUID
    let segmentCount: Int
}

private struct SegmentScan {
    var segments: [RecordingSegment]
    var invalidOrOpenFiles: Bool
}

/// One private directory per attempt. C01c media is written to immutable,
/// ordered CAF parts under a durable journal. Legacy C01a/C01b folders remain
/// readable and are never migrated or rewritten.
@MainActor public final class RecordingStore: RecordingStorage {
    public static let checkpointPolicy = SegmentCheckpointPolicy()

    private let root: URL
    private let inspect: (URL) throws -> AudioInspection
    private let makeID: () -> UUID

    public init(root: URL, makeID: @escaping () -> UUID = UUID.init,
                inspect: @escaping (URL) throws -> AudioInspection) throws {
        self.root = root; self.makeID = makeID; self.inspect = inspect
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        try recoverJournaledAttempts()
    }

    public func begin(kind: RecordingKind,
                      continuation: RecordingContinuation? = nil) throws -> RecordingDraft {
        if let continuation {
            let prior = try JSONDecoder().decode(RecordingDraft.self,
                from: Data(contentsOf: folder(continuation.previousPartID).appendingPathComponent("started.json")))
            guard prior.id == continuation.previousPartID, prior.kind == kind,
                  prior.sessionID == continuation.sessionID,
                  continuation.gapSeconds.map({ $0.isFinite && $0 >= 0 }) ?? true else {
                throw AudioPrototypeError.invalidMetadata
            }
        }
        guard Self.checkpointPolicy.valid else { throw AudioPrototypeError.invalidMetadata }
        let draft = RecordingDraft(id: makeID(), kind: kind, startedAt: Date(), continuation: continuation)
        let directory = folder(draft.id)
        guard mkdir(directory.path, 0o700) == 0 else {
            if errno == EEXIST { throw AudioPrototypeError.collision }
            throw NSError(domain: NSPOSIXErrorDomain, code: Int(errno))
        }
        #if os(iOS)
        try FileManager.default.setAttributes(
            [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
            ofItemAtPath: directory.path)
        #endif
        try writeReceipt(JSONEncoder().encode(draft), to: directory.appendingPathComponent("started.json"))
        let media = segmentsFolder(draft.id)
        try FileManager.default.createDirectory(at: media, withIntermediateDirectories: false)
        #if os(iOS)
        try FileManager.default.setAttributes(
            [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
            ofItemAtPath: media.path)
        #endif
        let journal = RecordingJournal(schema: 1, draftID: draft.id,
                                       checkpoint: Self.checkpointPolicy)
        try writeReceipt(JSONEncoder().encode(journal),
                         to: directory.appendingPathComponent("journal.json"))
        return draft
    }

    /// During capture this is the first partial part. After completion it resolves
    /// to the first stable part so existing diagnostic callers remain useful.
    public func url(for draft: RecordingDraft) -> URL {
        let legacy = folder(draft.id).appendingPathComponent("audio.caf")
        if FileManager.default.fileExists(atPath: legacy.path) { return legacy }
        let stable = segmentURL(draft.id, index: 0, partial: false)
        if FileManager.default.fileExists(atPath: stable.path) { return stable }
        return segmentURL(draft.id, index: 0, partial: true)
    }

    public func finish(_ draft: RecordingDraft, interrupted: Bool) throws -> RecordingClip {
        let directory = folder(draft.id)
        let saved = try JSONDecoder().decode(RecordingDraft.self,
            from: Data(contentsOf: directory.appendingPathComponent("started.json")))
        guard saved == draft else { throw AudioPrototypeError.invalidMetadata }
        let journal = try JSONDecoder().decode(RecordingJournal.self,
            from: Data(contentsOf: directory.appendingPathComponent("journal.json")))
        guard journal.schema == 1, journal.draftID == draft.id, journal.checkpoint.valid else {
            throw AudioPrototypeError.invalidMetadata
        }
        let scan = try scanSegments(for: draft.id, promoteValidPartials: true, recovered: false)
        guard !scan.invalidOrOpenFiles, !scan.segments.isEmpty else {
            throw AudioPrototypeError.invalidAudio
        }
        let clip = RecordingClip(draft: draft, audio: try aggregate(scan.segments),
                                 interrupted: interrupted, segments: scan.segments)
        // Create-only completion is the local database stand-in. Repeated Stop or
        // a restart cannot rewrite it.
        try writeReceipt(JSONEncoder().encode(clip),
                         to: directory.appendingPathComponent("completed.json"))
        let finalized = RecordingFinalization(schema: 1, draftID: draft.id,
                                              segmentCount: scan.segments.count)
        try writeReceipt(JSONEncoder().encode(finalized),
                         to: directory.appendingPathComponent("journal-completed.json"))
        return clip
    }

    public func library() throws -> RecordingLibrary {
        var result = RecordingLibrary()
        for directory in try FileManager.default.contentsOfDirectory(
            at: root, includingPropertiesForKeys: [.isSymbolicLinkKey]) {
            do {
                guard try directory.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true,
                      let id = UUID(uuidString: directory.lastPathComponent) else {
                    result.unfinishedCount += 1; continue
                }
                let clip = try JSONDecoder().decode(RecordingClip.self,
                    from: Data(contentsOf: directory.appendingPathComponent("completed.json")))
                let draft = try JSONDecoder().decode(RecordingDraft.self,
                    from: Data(contentsOf: directory.appendingPathComponent("started.json")))
                guard clip.id == id, clip.draft == draft, clip.audio.valid else {
                    throw AudioPrototypeError.invalidMetadata
                }
                if let segments = clip.segments {
                    guard !segments.isEmpty,
                          try validatedSegments(segments, draftID: id) == segments,
                          try aggregate(segments) == clip.audio else {
                        throw AudioPrototypeError.invalidAudio
                    }
                } else {
                    // Legacy C01a/C01b single-file record, intentionally unchanged.
                    guard try inspect(directory.appendingPathComponent("audio.caf")) == clip.audio else {
                        throw AudioPrototypeError.invalidAudio
                    }
                }
                result.clips.append(clip)
            } catch { result.unfinishedCount += 1 }
        }
        result.clips.sort { $0.draft.startedAt > $1.draft.startedAt }
        return result
    }

    public func playbackURLs(for clip: RecordingClip) throws -> [URL] {
        guard let segments = clip.segments else {
            return [folder(clip.id).appendingPathComponent("audio.caf")]
        }
        return try validatedSegments(segments, draftID: clip.id).map {
            segmentsFolder(clip.id).appendingPathComponent($0.fileName)
        }
    }

    private func recoverJournaledAttempts() throws {
        for directory in try FileManager.default.contentsOfDirectory(
            at: root, includingPropertiesForKeys: [.isSymbolicLinkKey]) {
            guard try directory.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true,
                  let id = UUID(uuidString: directory.lastPathComponent),
                  FileManager.default.fileExists(atPath: directory.appendingPathComponent("journal.json").path),
                  !FileManager.default.fileExists(atPath: directory.appendingPathComponent("completed.json").path)
            else { continue }
            do {
                let draft = try JSONDecoder().decode(RecordingDraft.self,
                    from: Data(contentsOf: directory.appendingPathComponent("started.json")))
                let journal = try JSONDecoder().decode(RecordingJournal.self,
                    from: Data(contentsOf: directory.appendingPathComponent("journal.json")))
                guard draft.id == id, journal.schema == 1, journal.draftID == id,
                      journal.checkpoint.valid else { continue }
                let scan = try scanSegments(for: id, promoteValidPartials: true, recovered: true)
                guard !scan.segments.isEmpty else { continue }
                let recovery = RecordingRecovery(recoveredAfterCrash: true, missingTail: true)
                let clip = RecordingClip(draft: draft, audio: try aggregate(scan.segments),
                                         interrupted: true, segments: scan.segments,
                                         recovery: recovery)
                try writeReceipt(JSONEncoder().encode(clip),
                                 to: directory.appendingPathComponent("completed.json"))
                let finalized = RecordingFinalization(schema: 1, draftID: id,
                                                      segmentCount: scan.segments.count)
                try writeReceipt(JSONEncoder().encode(finalized),
                                 to: directory.appendingPathComponent("journal-recovered.json"))
            } catch {
                // Fail closed: retain every byte and expose the attempt as unfinished.
                continue
            }
        }
    }

    private func scanSegments(for id: UUID, promoteValidPartials: Bool,
                              recovered: Bool) throws -> SegmentScan {
        let media = segmentsFolder(id)
        guard try media.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true else {
            throw AudioPrototypeError.invalidAudio
        }
        let files = try FileManager.default.contentsOfDirectory(
            at: media, includingPropertiesForKeys: [.isSymbolicLinkKey])
        var invalidOrOpen = files.contains {
            Self.partialIndex($0.lastPathComponent) == nil
                && Self.stableIndex($0.lastPathComponent) == nil
        }
        if promoteValidPartials {
            for partial in files.filter({ Self.partialIndex($0.lastPathComponent) != nil }) {
                guard try partial.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true,
                      let index = Self.partialIndex(partial.lastPathComponent) else {
                    invalidOrOpen = true; continue
                }
                do {
                    let inspected = try inspect(partial)
                    guard inspected.valid else { throw AudioPrototypeError.invalidAudio }
                    let stable = segmentURL(id, index: index, partial: false)
                    guard !FileManager.default.fileExists(atPath: stable.path) else {
                        throw AudioPrototypeError.collision
                    }
                    try FileManager.default.moveItem(at: partial, to: stable)
                } catch { invalidOrOpen = true }
            }
        }
        let stableFiles = try FileManager.default.contentsOfDirectory(
            at: media, includingPropertiesForKeys: [.isSymbolicLinkKey])
            .compactMap { url -> (Int, URL)? in
                guard let index = Self.stableIndex(url.lastPathComponent) else { return nil }
                return (index, url)
            }.sorted { $0.0 < $1.0 }
        var segments: [RecordingSegment] = []
        var expected = 0
        for (index, url) in stableFiles {
            do {
                guard try url.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true else {
                    throw AudioPrototypeError.invalidAudio
                }
                let value = try inspect(url)
                guard value.valid else { throw AudioPrototypeError.invalidAudio }
                segments.append(RecordingSegment(index: index, fileName: url.lastPathComponent,
                    audio: value, recovered: recovered,
                    discontinuityBefore: index != expected))
                expected = index + 1
            } catch { invalidOrOpen = true }
        }
        let remainingPartials = try FileManager.default.contentsOfDirectory(at: media,
            includingPropertiesForKeys: nil).contains { Self.partialIndex($0.lastPathComponent) != nil }
        return SegmentScan(segments: segments, invalidOrOpenFiles: invalidOrOpen || remainingPartials)
    }

    private func validatedSegments(_ segments: [RecordingSegment],
                                   draftID: UUID) throws -> [RecordingSegment] {
        var seen = Set<Int>()
        for segment in segments {
            guard segment.index >= 0, seen.insert(segment.index).inserted,
                  segment.fileName == Self.stableName(segment.index), segment.audio.valid else {
                throw AudioPrototypeError.invalidMetadata
            }
            let url = segmentsFolder(draftID).appendingPathComponent(segment.fileName)
            guard try url.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true,
                  try inspect(url) == segment.audio else {
                throw AudioPrototypeError.invalidAudio
            }
        }
        return segments.sorted { $0.index < $1.index }
    }

    private func aggregate(_ segments: [RecordingSegment]) throws -> AudioInspection {
        guard let first = segments.first, !segments.isEmpty,
              segments.allSatisfy({ $0.audio.valid
                  && $0.audio.sampleRate == first.audio.sampleRate
                  && $0.audio.channels == first.audio.channels }) else {
            throw AudioPrototypeError.invalidAudio
        }
        return AudioInspection(duration: segments.reduce(0) { $0 + $1.audio.duration },
            byteCount: segments.reduce(0) { $0 + $1.audio.byteCount },
            sampleRate: first.audio.sampleRate, channels: first.audio.channels)
    }

    private func folder(_ id: UUID) -> URL {
        root.appendingPathComponent(id.uuidString, isDirectory: true)
    }
    private func segmentsFolder(_ id: UUID) -> URL {
        folder(id).appendingPathComponent("segments", isDirectory: true)
    }
    private func segmentURL(_ id: UUID, index: Int, partial: Bool) -> URL {
        segmentsFolder(id).appendingPathComponent(
            partial ? Self.partialName(index) : Self.stableName(index))
    }
    private static func stableName(_ index: Int) -> String {
        String(format: "segment-%06d.caf", index)
    }
    private static func partialName(_ index: Int) -> String {
        String(format: "segment-%06d.partial.caf", index)
    }
    private static func stableIndex(_ name: String) -> Int? {
        guard name.hasPrefix("segment-"), name.hasSuffix(".caf"),
              !name.hasSuffix(".partial.caf") else { return nil }
        return Int(name.dropFirst(8).dropLast(4))
    }
    private static func partialIndex(_ name: String) -> Int? {
        guard name.hasPrefix("segment-"), name.hasSuffix(".partial.caf") else { return nil }
        return Int(name.dropFirst(8).dropLast(12))
    }

    private func writeReceipt(_ data: Data, to url: URL) throws {
        var options: Data.WritingOptions = .withoutOverwriting
        #if os(iOS)
        options.insert(.completeFileProtectionUntilFirstUserAuthentication)
        #endif
        try data.write(to: url, options: options)
    }
}
