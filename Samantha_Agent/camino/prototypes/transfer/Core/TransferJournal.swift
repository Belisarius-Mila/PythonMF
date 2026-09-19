import Foundation

public enum TransferJournalPhase: String, Codable, Sendable {
    case ready
    case uploading
    case waitingForNetwork
    case paused
    case verifying
    case verified
    case needsAttention
}

public struct TransferJournal: Codable, Equatable, Sendable {
    public let schema: Int
    public let assetID: String
    public let batchID: UUID
    public let sourceFileName: String
    public let byteCount: Int64
    public let sha256: String
    public let chunkSize: Int
    public let chunkCount: Int
    public var acceptedChunks: Set<Int>
    public var locallySentByteCount: Int64
    public var phase: TransferJournalPhase
    public var cellularBatchID: UUID?
    /// Nil is a journal from an older build; keep its existing recovery behavior.
    public var startAuthorized: Bool?
    public var lastError: String?

    public init(
        schema: Int = 1,
        assetID: String,
        batchID: UUID,
        sourceFileName: String,
        byteCount: Int64,
        sha256: String,
        chunkSize: Int,
        chunkCount: Int,
        acceptedChunks: Set<Int> = [],
        locallySentByteCount: Int64 = 0,
        phase: TransferJournalPhase = .ready,
        cellularBatchID: UUID? = nil,
        startAuthorized: Bool = false,
        lastError: String? = nil
    ) {
        self.schema = schema
        self.assetID = assetID
        self.batchID = batchID
        self.sourceFileName = sourceFileName
        self.byteCount = byteCount
        self.sha256 = sha256
        self.chunkSize = chunkSize
        self.chunkCount = chunkCount
        self.acceptedChunks = acceptedChunks
        self.locallySentByteCount = locallySentByteCount
        self.phase = phase
        self.cellularBatchID = cellularBatchID
        self.startAuthorized = startAuthorized
        self.lastError = lastError
    }

    public var queueItem: TransferQueueItem {
        TransferQueueItem(
            assetID: assetID,
            batchID: batchID,
            chunkCount: chunkCount,
            byteCount: byteCount,
            locallySentByteCount: locallySentByteCount
        )
    }

    public var cellularAllowed: Bool {
        cellularBatchID == batchID
    }

    public var requiresExplicitStart: Bool {
        cellularAllowed && startAuthorized == false
    }

    public var valid: Bool {
        schema == 1
            && Self.validIdentifier(assetID)
            && Self.validFileName(sourceFileName)
            && byteCount > 0
            && Self.validHash(sha256)
            && chunkSize > 0
            && chunkCount == Int((byteCount + Int64(chunkSize) - 1) / Int64(chunkSize))
            && acceptedChunks.allSatisfy { $0 >= 0 && $0 < chunkCount }
            && locallySentByteCount >= 0
            && locallySentByteCount <= byteCount
    }

    public static func validIdentifier(_ value: String) -> Bool {
        !value.isEmpty && value.count <= 96
            && value.allSatisfy { $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "-") }
    }

    public static func validHash(_ value: String) -> Bool {
        value.count == 64 && value.allSatisfy { $0.isHexDigit && !$0.isUppercase }
    }

    public static func validFileName(_ value: String) -> Bool {
        !value.isEmpty && value.count <= 128 && value != "." && value != ".."
            && !value.contains("/") && !value.contains("\\")
    }
}

public enum TransferJournalError: Error, Equatable {
    case unsafeRoot
    case invalidJournal
    case missingJournal
    case unsafeFileName
}

public struct TransferJournalStore: Sendable {
    public let root: URL

    public init(root: URL) throws {
        self.root = root.standardizedFileURL
        try Self.ensureDirectory(self.root)
        try Self.ensureDirectory(sourcesRoot)
        try Self.ensureDirectory(preparedRoot)
    }

    public var sourcesRoot: URL { root.appendingPathComponent("sources", isDirectory: true) }
    public var preparedRoot: URL { root.appendingPathComponent("prepared", isDirectory: true) }
    public var journalURL: URL { root.appendingPathComponent("current-transfer.json") }

    public func sourceURL(fileName: String) throws -> URL {
        guard TransferJournal.validFileName(fileName) else {
            throw TransferJournalError.unsafeFileName
        }
        return sourcesRoot.appendingPathComponent(fileName, isDirectory: false)
    }

    public func save(_ journal: TransferJournal) throws {
        guard journal.valid else { throw TransferJournalError.invalidJournal }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(journal)
        try data.write(to: journalURL, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
    }

    public func load() throws -> TransferJournal {
        guard FileManager.default.fileExists(atPath: journalURL.path) else {
            throw TransferJournalError.missingJournal
        }
        let journal: TransferJournal
        do {
            journal = try JSONDecoder().decode(
                TransferJournal.self,
                from: Data(contentsOf: journalURL, options: .uncached)
            )
        } catch {
            throw TransferJournalError.invalidJournal
        }
        guard journal.valid else { throw TransferJournalError.invalidJournal }
        let source = try sourceURL(fileName: journal.sourceFileName)
        guard !source.hasDirectoryPath,
              FileManager.default.fileExists(atPath: source.path) else {
            throw TransferJournalError.invalidJournal
        }
        return journal
    }

    private static func ensureDirectory(_ url: URL) throws {
        var isDirectory: ObjCBool = false
        let manager = FileManager.default
        if manager.fileExists(atPath: url.path, isDirectory: &isDirectory) {
            guard isDirectory.boolValue,
                  (try url.resourceValues(forKeys: [.isSymbolicLinkKey])).isSymbolicLink != true else {
                throw TransferJournalError.unsafeRoot
            }
            return
        }
        try manager.createDirectory(
            at: url,
            withIntermediateDirectories: false,
            attributes: [.posixPermissions: 0o700]
        )
    }
}
