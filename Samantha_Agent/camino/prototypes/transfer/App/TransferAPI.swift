import Foundation

enum TransferAPIError: Error, Equatable {
    case invalidResponse
    case server(Int, String)
    case identityMismatch
}

final class TransferAPI: @unchecked Sendable {
    private let endpoint: TransferEndpoint
    private let session: URLSession

    init(endpoint: TransferEndpoint) {
        self.endpoint = endpoint
        let configuration = URLSessionConfiguration.ephemeral
        configuration.waitsForConnectivity = false
        configuration.timeoutIntervalForRequest = 20
        configuration.timeoutIntervalForResource = 30
        configuration.urlCache = nil
        self.session = URLSession(configuration: configuration)
    }

    func createSession(for journal: TransferJournal) async throws -> TransferStatusPayload {
        try await statusPayload(for: endpoint.createSessionRequest(for: journal), journal: journal)
    }

    func status(for journal: TransferJournal) async throws -> TransferStatusPayload {
        try await statusPayload(
            for: endpoint.statusRequest(
                assetID: journal.assetID,
                allowsCellular: journal.cellularAllowed
            ),
            journal: journal
        )
    }

    func finalize(_ journal: TransferJournal) async throws -> TransferFinalizePayload {
        let (data, response) = try await session.data(
            for: endpoint.finalizeRequest(
                assetID: journal.assetID,
                allowsCellular: journal.cellularAllowed
            )
        )
        try validate(response: response, data: data)
        let payload = try JSONDecoder().decode(TransferFinalizePayload.self, from: data)
        guard payload.assetID == journal.assetID,
              payload.byteCount == journal.byteCount,
              payload.sha256 == journal.sha256,
              payload.chunkCount == journal.chunkCount,
              payload.state == .verified else {
            throw TransferAPIError.identityMismatch
        }
        return payload
    }

    func chunkRequest(
        journal: TransferJournal,
        chunk: PreparedChunk
    ) throws -> URLRequest {
        try endpoint.chunkRequest(
            assetID: journal.assetID,
            chunk: chunk,
            allowsCellular: journal.cellularAllowed
        )
    }

    private func statusPayload(
        for request: URLRequest,
        journal: TransferJournal
    ) async throws -> TransferStatusPayload {
        let (data, response) = try await session.data(for: request)
        try validate(response: response, data: data)
        let payload = try JSONDecoder().decode(TransferStatusPayload.self, from: data)
        guard payload.isValid(for: journal) else {
            throw TransferAPIError.identityMismatch
        }
        return payload
    }

    private func validate(response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else {
            throw TransferAPIError.invalidResponse
        }
        guard (200...299).contains(http.statusCode) else {
            struct Failure: Decodable { let error: String }
            let code = (try? JSONDecoder().decode(Failure.self, from: data).error)
                .map(Self.safeServerCode) ?? "server_error"
            throw TransferAPIError.server(http.statusCode, code)
        }
    }

    private static func safeServerCode(_ value: String) -> String {
        let filtered = value.filter { $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "_") }
        return filtered.isEmpty ? "server_error" : String(filtered.prefix(64))
    }
}
