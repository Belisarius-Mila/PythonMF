import Foundation

public enum TransferProtocolError: Error, Equatable {
    case invalidBaseURL
    case invalidToken
    case invalidPayload
    case unexpectedStatus(Int)
}

public struct TransferStatusPayload: Codable, Equatable, Sendable {
    public let assetID: String
    public let state: TransferRemoteState
    public let byteCount: Int64
    public let sha256: String
    public let chunkSize: Int
    public let chunkCount: Int
    public let acceptedChunks: [Int]
    public let missingChunks: [Int]

    enum CodingKeys: String, CodingKey {
        case assetID = "asset_id"
        case state
        case byteCount = "byte_count"
        case sha256
        case chunkSize = "chunk_size"
        case chunkCount = "chunk_count"
        case acceptedChunks = "accepted_chunks"
        case missingChunks = "missing_chunks"
    }

    public var snapshot: TransferServerSnapshot {
        TransferServerSnapshot(acceptedChunks: Set(acceptedChunks), state: state)
    }

    public func isValid(for journal: TransferJournal) -> Bool {
        guard assetID == journal.assetID,
              byteCount == journal.byteCount,
              sha256 == journal.sha256,
              chunkSize == journal.chunkSize,
              chunkCount == journal.chunkCount else {
            return false
        }
        let accepted = Set(acceptedChunks)
        let missing = Set(missingChunks)
        let all = Set(0..<journal.chunkCount)
        guard accepted.count == acceptedChunks.count,
              missing.count == missingChunks.count,
              accepted.isDisjoint(with: missing),
              accepted.union(missing) == all else {
            return false
        }
        switch state {
        case .uploading:
            return true
        case .verifying, .verified, .verificationFailed:
            return accepted == all && missing.isEmpty
        }
    }
}

public struct TransferFinalizePayload: Codable, Equatable, Sendable {
    public let assetID: String
    public let byteCount: Int64
    public let sha256: String
    public let chunkCount: Int
    public let state: TransferRemoteState

    enum CodingKeys: String, CodingKey {
        case assetID = "asset_id"
        case byteCount = "byte_count"
        case sha256
        case chunkCount = "chunk_count"
        case state
    }
}

public struct TransferEndpoint: Sendable {
    public let baseURL: URL
    private let bearerToken: String

    public init(baseURL: URL, bearerToken: String) throws {
        guard baseURL.scheme?.lowercased() == "https",
              baseURL.host != nil,
              baseURL.user == nil,
              baseURL.password == nil,
              baseURL.query == nil,
              baseURL.fragment == nil else {
            throw TransferProtocolError.invalidBaseURL
        }
        guard bearerToken.count >= 32,
              !bearerToken.contains("\n"),
              !bearerToken.contains("\r") else {
            throw TransferProtocolError.invalidToken
        }
        self.baseURL = baseURL
        self.bearerToken = bearerToken
    }

    public func createSessionRequest(for journal: TransferJournal) throws -> URLRequest {
        guard journal.valid else { throw TransferProtocolError.invalidPayload }
        struct Manifest: Encodable {
            let byte_count: Int64
            let sha256: String
            let chunk_size: Int
        }
        var request = try authenticatedRequest(
            method: "POST",
            components: ["v1", "c02b", "synthetic-assets", journal.assetID, "sessions"],
            allowsCellular: journal.cellularAllowed
        )
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("1", forHTTPHeaderField: "X-Camino-Synthetic")
        request.httpBody = try JSONEncoder().encode(
            Manifest(
                byte_count: journal.byteCount,
                sha256: journal.sha256,
                chunk_size: journal.chunkSize
            )
        )
        return request
    }

    public func statusRequest(assetID: String, allowsCellular: Bool = false) throws -> URLRequest {
        try authenticatedRequest(
            method: "GET",
            components: ["v1", "c02b", "synthetic-assets", assetID, "status"],
            allowsCellular: allowsCellular
        )
    }

    public func finalizeRequest(assetID: String, allowsCellular: Bool = false) throws -> URLRequest {
        try authenticatedRequest(
            method: "POST",
            components: ["v1", "c02b", "synthetic-assets", assetID, "finalize"],
            allowsCellular: allowsCellular
        )
    }

    public func chunkRequest(
        assetID: String,
        chunk: PreparedChunk,
        allowsCellular: Bool
    ) throws -> URLRequest {
        guard chunk.assetID == assetID,
              chunk.index >= 0,
              chunk.byteCount > 0,
              TransferJournal.validHash(chunk.sha256) else {
            throw TransferProtocolError.invalidPayload
        }
        var request = try authenticatedRequest(
            method: "PUT",
            components: [
                "v1", "c02b", "synthetic-assets", assetID, "chunks", String(chunk.index),
            ],
            allowsCellular: allowsCellular
        )
        request.setValue("application/octet-stream", forHTTPHeaderField: "Content-Type")
        request.setValue("1", forHTTPHeaderField: "X-Camino-Synthetic")
        request.setValue(chunk.sha256, forHTTPHeaderField: "X-Camino-Chunk-SHA256")
        request.setValue(String(chunk.byteCount), forHTTPHeaderField: "Content-Length")
        return request
    }

    private func authenticatedRequest(
        method: String,
        components: [String],
        allowsCellular: Bool = false
    ) throws -> URLRequest {
        guard components.allSatisfy({ TransferJournal.validIdentifier($0) || Int($0) != nil }) else {
            throw TransferProtocolError.invalidPayload
        }
        var url = baseURL
        for component in components {
            url.appendPathComponent(component, isDirectory: false)
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 30
        request.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
        request.allowsCellularAccess = allowsCellular
        request.allowsExpensiveNetworkAccess = allowsCellular
        request.setValue("Bearer \(bearerToken)", forHTTPHeaderField: "Authorization")
        request.setValue("no-store", forHTTPHeaderField: "Cache-Control")
        return request
    }
}
