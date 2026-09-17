import CryptoKit
import Foundation

public struct SyntheticSource: Equatable, Sendable {
    public let fileName: String
    public let byteCount: Int64
    public let sha256: String

    public init(fileName: String, byteCount: Int64, sha256: String) {
        self.fileName = fileName
        self.byteCount = byteCount
        self.sha256 = sha256
    }
}

public enum TransferFileError: Error, Equatable {
    case invalidSize
    case collision
    case invalidSource
    case invalidChunk
    case preparedConflict
}

public enum SyntheticSourceFactory {
    public static func create(
        in directory: URL,
        byteCount: Int64,
        id: UUID = UUID()
    ) throws -> SyntheticSource {
        guard byteCount > 0 else { throw TransferFileError.invalidSize }
        let fileName = "synthetic-\(id.uuidString.lowercased()).bin"
        let destination = directory.appendingPathComponent(fileName)
        guard !FileManager.default.fileExists(atPath: destination.path) else {
            throw TransferFileError.collision
        }
        let temporary = directory.appendingPathComponent(".\(fileName).\(UUID().uuidString)")
        guard FileManager.default.createFile(
            atPath: temporary.path,
            contents: nil,
            attributes: [.posixPermissions: 0o600]
        ) else { throw TransferFileError.collision }

        var hasher = SHA256()
        var remaining = byteCount
        let blockCapacity = 1024 * 1024
        var template = Data(count: blockCapacity)
        template.withUnsafeMutableBytes { raw in
            guard let bytes = raw.bindMemory(to: UInt8.self).baseAddress else { return }
            for offset in 0..<blockCapacity {
                bytes[offset] = UInt8(truncatingIfNeeded: offset)
            }
        }
        do {
            let output = try FileHandle(forWritingTo: temporary)
            defer { try? output.close() }
            while remaining > 0 {
                let count = Int(min(remaining, Int64(blockCapacity)))
                let block = count == blockCapacity ? template : Data(template.prefix(count))
                try output.write(contentsOf: block)
                hasher.update(data: block)
                remaining -= Int64(count)
            }
            try output.synchronize()
            try FileManager.default.moveItem(at: temporary, to: destination)
        } catch {
            try? FileManager.default.removeItem(at: temporary)
            throw error
        }
        return SyntheticSource(
            fileName: fileName,
            byteCount: byteCount,
            sha256: hexDigest(hasher.finalize())
        )
    }
}

public struct PreparedChunk: Codable, Equatable, Sendable {
    public let schema: Int
    public let assetID: String
    public let index: Int
    public let fileName: String
    public let byteCount: Int
    public let sha256: String

    public init(
        schema: Int = 1,
        assetID: String,
        index: Int,
        fileName: String = "chunk.bin",
        byteCount: Int,
        sha256: String
    ) {
        self.schema = schema
        self.assetID = assetID
        self.index = index
        self.fileName = fileName
        self.byteCount = byteCount
        self.sha256 = sha256
    }
}

public struct FileChunkPreparer: Sendable {
    public let root: URL
    public let maximumPreparedChunks: Int

    public init(root: URL, maximumPreparedChunks: Int = 2) throws {
        guard maximumPreparedChunks > 0 && maximumPreparedChunks <= 2 else {
            throw TransferFileError.invalidChunk
        }
        self.root = root.standardizedFileURL
        self.maximumPreparedChunks = maximumPreparedChunks
        var isDirectory: ObjCBool = false
        if FileManager.default.fileExists(atPath: self.root.path, isDirectory: &isDirectory) {
            guard isDirectory.boolValue,
                  (try self.root.resourceValues(forKeys: [.isSymbolicLinkKey])).isSymbolicLink != true else {
                throw TransferJournalError.unsafeRoot
            }
        } else {
            try FileManager.default.createDirectory(
                at: self.root,
                withIntermediateDirectories: false,
                attributes: [.posixPermissions: 0o700]
            )
        }
    }

    public func preparedChunks(for journal: TransferJournal) throws -> [PreparedChunk] {
        let directory = try assetDirectory(for: journal.assetID, create: true)
        let children = try FileManager.default.contentsOfDirectory(
            at: directory,
            includingPropertiesForKeys: [.isDirectoryKey, .isSymbolicLinkKey],
            options: [.skipsHiddenFiles]
        )
        return try children.compactMap { child in
            let values = try child.resourceValues(forKeys: [.isDirectoryKey, .isSymbolicLinkKey])
            guard values.isDirectory == true, values.isSymbolicLink != true,
                  let index = Int(child.lastPathComponent) else {
                throw TransferFileError.preparedConflict
            }
            return try validatedChunk(in: child, journal: journal, expectedIndex: index)
        }.sorted { $0.index < $1.index }
    }

    public func prepare(
        journal: TransferJournal,
        sourceURL: URL,
        missingChunks: [Int]
    ) throws -> [PreparedChunk] {
        guard journal.valid else { throw TransferJournalError.invalidJournal }
        let sourceValues = try sourceURL.resourceValues(
            forKeys: [.isRegularFileKey, .isSymbolicLinkKey, .fileSizeKey]
        )
        guard sourceValues.isRegularFile == true,
              sourceValues.isSymbolicLink != true,
              Int64(sourceValues.fileSize ?? -1) == journal.byteCount else {
            throw TransferFileError.invalidSource
        }

        var prepared = try preparedChunks(for: journal)
        guard prepared.count <= maximumPreparedChunks else {
            throw TransferFileError.preparedConflict
        }
        let existing = Set(prepared.map(\.index))
        let candidates = missingChunks.filter {
            $0 >= 0 && $0 < journal.chunkCount && !existing.contains($0)
        }
        for index in candidates.prefix(maximumPreparedChunks - prepared.count) {
            prepared.append(try prepareOne(journal: journal, sourceURL: sourceURL, index: index))
        }
        return prepared.sorted { $0.index < $1.index }
    }

    public func fileURL(for chunk: PreparedChunk) throws -> URL {
        guard chunk.schema == 1,
              TransferJournal.validIdentifier(chunk.assetID),
              chunk.index >= 0,
              chunk.fileName == "chunk.bin" else {
            throw TransferFileError.invalidChunk
        }
        return try assetDirectory(for: chunk.assetID, create: false)
            .appendingPathComponent(String(format: "%08d", chunk.index), isDirectory: true)
            .appendingPathComponent(chunk.fileName)
    }

    public func removePrepared(assetID: String, index: Int) throws {
        guard index >= 0 else { throw TransferFileError.invalidChunk }
        let directory = try assetDirectory(for: assetID, create: false)
            .appendingPathComponent(String(format: "%08d", index), isDirectory: true)
        if FileManager.default.fileExists(atPath: directory.path) {
            try FileManager.default.removeItem(at: directory)
        }
    }

    public func removeAllPrepared(assetID: String) throws {
        let directory = try assetDirectory(for: assetID, create: false)
        if FileManager.default.fileExists(atPath: directory.path) {
            try FileManager.default.removeItem(at: directory)
        }
    }

    private func prepareOne(
        journal: TransferJournal,
        sourceURL: URL,
        index: Int
    ) throws -> PreparedChunk {
        let asset = try assetDirectory(for: journal.assetID, create: true)
        let final = asset.appendingPathComponent(String(format: "%08d", index), isDirectory: true)
        guard !FileManager.default.fileExists(atPath: final.path) else {
            throw TransferFileError.preparedConflict
        }
        let staging = asset.appendingPathComponent(".\(index).\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(
            at: staging,
            withIntermediateDirectories: false,
            attributes: [.posixPermissions: 0o700]
        )
        let chunkURL = staging.appendingPathComponent("chunk.bin")
        guard FileManager.default.createFile(
            atPath: chunkURL.path,
            contents: nil,
            attributes: [.posixPermissions: 0o600]
        ) else { throw TransferFileError.collision }

        let expectedCount = Int(min(
            Int64(journal.chunkSize),
            journal.byteCount - (Int64(index) * Int64(journal.chunkSize))
        ))
        var hasher = SHA256()
        do {
            let source = try FileHandle(forReadingFrom: sourceURL)
            let output = try FileHandle(forWritingTo: chunkURL)
            defer { try? source.close(); try? output.close() }
            try source.seek(toOffset: UInt64(index * journal.chunkSize))
            var remaining = expectedCount
            while remaining > 0 {
                guard let data = try source.read(upToCount: min(remaining, 1024 * 1024)),
                      !data.isEmpty else {
                    throw TransferFileError.invalidSource
                }
                try output.write(contentsOf: data)
                hasher.update(data: data)
                remaining -= data.count
            }
            try output.synchronize()
            let receipt = PreparedChunk(
                assetID: journal.assetID,
                index: index,
                byteCount: expectedCount,
                sha256: hexDigest(hasher.finalize())
            )
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.sortedKeys]
            try encoder.encode(receipt).write(
                to: staging.appendingPathComponent("receipt.json"),
                options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication]
            )
            try FileManager.default.moveItem(at: staging, to: final)
            return receipt
        } catch {
            try? FileManager.default.removeItem(at: staging)
            throw error
        }
    }

    private func validatedChunk(
        in directory: URL,
        journal: TransferJournal,
        expectedIndex: Int
    ) throws -> PreparedChunk {
        let dataURL = directory.appendingPathComponent("chunk.bin")
        let receiptURL = directory.appendingPathComponent("receipt.json")
        let receipt: PreparedChunk
        do {
            receipt = try JSONDecoder().decode(
                PreparedChunk.self,
                from: Data(contentsOf: receiptURL, options: .uncached)
            )
        } catch {
            throw TransferFileError.preparedConflict
        }
        let values = try dataURL.resourceValues(
            forKeys: [.isRegularFileKey, .isSymbolicLinkKey, .fileSizeKey]
        )
        guard receipt.schema == 1,
              receipt.assetID == journal.assetID,
              receipt.index == expectedIndex,
              receipt.fileName == "chunk.bin",
              receipt.byteCount > 0,
              receipt.sha256 == (try sha256(of: dataURL)),
              values.isRegularFile == true,
              values.isSymbolicLink != true,
              values.fileSize == receipt.byteCount else {
            throw TransferFileError.preparedConflict
        }
        return receipt
    }

    private func assetDirectory(for assetID: String, create: Bool) throws -> URL {
        guard TransferJournal.validIdentifier(assetID) else {
            throw TransferFileError.invalidChunk
        }
        let directory = root.appendingPathComponent(assetID, isDirectory: true)
        var isDirectory: ObjCBool = false
        if FileManager.default.fileExists(atPath: directory.path, isDirectory: &isDirectory) {
            guard isDirectory.boolValue,
                  (try directory.resourceValues(forKeys: [.isSymbolicLinkKey])).isSymbolicLink != true else {
                throw TransferFileError.preparedConflict
            }
        } else if create {
            try FileManager.default.createDirectory(
                at: directory,
                withIntermediateDirectories: false,
                attributes: [.posixPermissions: 0o700]
            )
        }
        return directory
    }
}

public func sha256(of url: URL) throws -> String {
    let values = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
    guard values.isRegularFile == true, values.isSymbolicLink != true else {
        throw TransferFileError.invalidSource
    }
    let input = try FileHandle(forReadingFrom: url)
    defer { try? input.close() }
    var hasher = SHA256()
    while let data = try input.read(upToCount: 1024 * 1024), !data.isEmpty {
        hasher.update(data: data)
    }
    return hexDigest(hasher.finalize())
}

private func hexDigest<D: Sequence>(_ digest: D) -> String where D.Element == UInt8 {
    digest.map { String(format: "%02x", $0) }.joined()
}
