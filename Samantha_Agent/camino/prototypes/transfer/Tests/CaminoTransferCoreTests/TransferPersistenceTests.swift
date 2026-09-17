import Foundation
import XCTest
@testable import CaminoTransferCore

final class TransferPersistenceTests: XCTestCase {
    private func root() throws -> URL {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-transfer-test-\(UUID())", isDirectory: true)
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: false)
        addTeardownBlock { try? FileManager.default.removeItem(at: url) }
        return url
    }

    private func fixture(byteCount: Int64 = 2_500_000) throws -> (
        store: TransferJournalStore,
        journal: TransferJournal,
        sourceURL: URL
    ) {
        let store = try TransferJournalStore(root: try root())
        let source = try SyntheticSourceFactory.create(
            in: store.sourcesRoot,
            byteCount: byteCount,
            id: UUID(uuidString: "11111111-2222-3333-4444-555555555555")!
        )
        let batchID = UUID(uuidString: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")!
        let chunkSize = 1_000_000
        let journal = TransferJournal(
            assetID: "asset-123",
            batchID: batchID,
            sourceFileName: source.fileName,
            byteCount: source.byteCount,
            sha256: source.sha256,
            chunkSize: chunkSize,
            chunkCount: Int((source.byteCount + Int64(chunkSize) - 1) / Int64(chunkSize))
        )
        return (store, journal, try store.sourceURL(fileName: source.fileName))
    }

    func testJournalRoundTripPreservesAuthoritativeQueueState() throws {
        let fixture = try fixture()
        var journal = fixture.journal
        journal.acceptedChunks = [0, 2]
        journal.locallySentByteCount = 2_000_000
        journal.phase = .waitingForNetwork
        journal.cellularBatchID = journal.batchID
        try fixture.store.save(journal)

        let loaded = try fixture.store.load()
        XCTAssertEqual(loaded, journal)
        XCTAssertTrue(loaded.valid)
        XCTAssertTrue(loaded.cellularAllowed)
        XCTAssertEqual(loaded.queueItem.localByteProgress, 0.8, accuracy: 0.0001)
    }

    func testCorruptJournalFailsClosedWithoutTouchingSource() throws {
        let fixture = try fixture()
        let original = try Data(contentsOf: fixture.sourceURL)
        try Data("not-json".utf8).write(to: fixture.store.journalURL, options: .atomic)

        XCTAssertThrowsError(try fixture.store.load()) { error in
            XCTAssertEqual(error as? TransferJournalError, .invalidJournal)
        }
        XCTAssertEqual(try Data(contentsOf: fixture.sourceURL), original)
    }

    func testChunkPreparerKeepsAtMostTwoFilesAndFillsNextMissingPart() throws {
        let fixture = try fixture()
        let preparer = try FileChunkPreparer(root: fixture.store.preparedRoot)

        let first = try preparer.prepare(
            journal: fixture.journal,
            sourceURL: fixture.sourceURL,
            missingChunks: [0, 1, 2]
        )
        XCTAssertEqual(first.map(\.index), [0, 1])
        XCTAssertEqual(first.map(\.byteCount), [1_000_000, 1_000_000])
        XCTAssertEqual(
            try first.map { try Data(contentsOf: preparer.fileURL(for: $0)).count }.reduce(0, +),
            2_000_000
        )

        try preparer.removePrepared(assetID: fixture.journal.assetID, index: 0)
        let next = try preparer.prepare(
            journal: fixture.journal,
            sourceURL: fixture.sourceURL,
            missingChunks: [2]
        )
        XCTAssertEqual(next.map(\.index), [1, 2])
        XCTAssertEqual(next.last?.byteCount, 500_000)
        XCTAssertLessThanOrEqual(next.count, 2)
    }

    func testPreparedChunkIsReusedAndConflictIsNotOverwritten() throws {
        let fixture = try fixture(byteCount: 1_500_000)
        let preparer = try FileChunkPreparer(root: fixture.store.preparedRoot)
        let first = try XCTUnwrap(try preparer.prepare(
            journal: fixture.journal,
            sourceURL: fixture.sourceURL,
            missingChunks: [0]
        ).first)
        let file = try preparer.fileURL(for: first)
        let original = try Data(contentsOf: file)

        let repeated = try preparer.prepare(
            journal: fixture.journal,
            sourceURL: fixture.sourceURL,
            missingChunks: [0]
        )
        XCTAssertEqual(repeated, [first])
        XCTAssertEqual(try Data(contentsOf: file), original)

        try Data("tampered".utf8).write(to: file)
        XCTAssertThrowsError(try preparer.preparedChunks(for: fixture.journal)) { error in
            XCTAssertEqual(error as? TransferFileError, .preparedConflict)
        }
        XCTAssertEqual(try Data(contentsOf: file), Data("tampered".utf8))
    }

    func testSymlinkedStorageRootsAreRejected() throws {
        let parent = try root()
        let target = parent.appendingPathComponent("target", isDirectory: true)
        try FileManager.default.createDirectory(at: target, withIntermediateDirectories: false)
        let link = parent.appendingPathComponent("link", isDirectory: true)
        try FileManager.default.createSymbolicLink(at: link, withDestinationURL: target)

        XCTAssertThrowsError(try TransferJournalStore(root: link)) { error in
            XCTAssertEqual(error as? TransferJournalError, .unsafeRoot)
        }
        XCTAssertThrowsError(try FileChunkPreparer(root: link)) { error in
            XCTAssertEqual(error as? TransferJournalError, .unsafeRoot)
        }
    }

    func testEndpointBuildsPrivateHTTPSRequestsWithoutPublicFallback() throws {
        let fixture = try fixture(byteCount: 1_500_000)
        let endpoint = try TransferEndpoint(
            baseURL: URL(string: "https://camino.example.test/private-path")!,
            bearerToken: "synthetic-token-with-at-least-32-characters"
        )
        let preparer = try FileChunkPreparer(root: fixture.store.preparedRoot)
        let chunk = try XCTUnwrap(try preparer.prepare(
            journal: fixture.journal,
            sourceURL: fixture.sourceURL,
            missingChunks: [0]
        ).first)

        let create = try endpoint.createSessionRequest(for: fixture.journal)
        let upload = try endpoint.chunkRequest(
            assetID: fixture.journal.assetID,
            chunk: chunk,
            allowsCellular: false
        )
        XCTAssertEqual(create.url?.scheme, "https")
        XCTAssertEqual(
            create.url?.path,
            "/private-path/v1/c02b/synthetic-assets/asset-123/sessions"
        )
        XCTAssertEqual(create.value(forHTTPHeaderField: "X-Camino-Synthetic"), "1")
        XCTAssertEqual(upload.httpMethod, "PUT")
        XCTAssertEqual(upload.allowsCellularAccess, false)
        XCTAssertEqual(upload.allowsExpensiveNetworkAccess, false)
        XCTAssertEqual(
            upload.value(forHTTPHeaderField: "X-Camino-Chunk-SHA256"),
            chunk.sha256
        )
    }

    func testEndpointRejectsHTTPCredentialsAndShortToken() throws {
        let goodToken = "synthetic-token-with-at-least-32-characters"
        for value in [
            "http://camino.example.test",
            "https://user:secret@camino.example.test",
            "https://camino.example.test/path?fallback=public",
        ] {
            XCTAssertThrowsError(
                try TransferEndpoint(baseURL: URL(string: value)!, bearerToken: goodToken)
            ) { error in
                XCTAssertEqual(error as? TransferProtocolError, .invalidBaseURL)
            }
        }
        XCTAssertThrowsError(
            try TransferEndpoint(
                baseURL: URL(string: "https://camino.example.test")!,
                bearerToken: "short"
            )
        ) { error in
            XCTAssertEqual(error as? TransferProtocolError, .invalidToken)
        }
    }

    func testStatusPayloadDecodesServerTruth() throws {
        let fixture = try fixture()
        let data = Data("""
        {
          "asset_id":"asset-123",
          "state":"verifying",
          "byte_count":2500000,
          "sha256":"\(fixture.journal.sha256)",
          "chunk_size":1000000,
          "chunk_count":3,
          "accepted_chunks":[0,1,2],
          "missing_chunks":[]
        }
        """.utf8)
        let payload = try JSONDecoder().decode(TransferStatusPayload.self, from: data)

        XCTAssertEqual(payload.state, .verifying)
        XCTAssertEqual(payload.snapshot.acceptedChunks, [0, 1, 2])
        XCTAssertEqual(payload.missingChunks, [])
        XCTAssertTrue(payload.isValid(for: fixture.journal))
    }

    func testStatusPayloadRejectsOutOfRangeAndFalseVerifiedSnapshots() throws {
        let fixture = try fixture()
        let outOfRange = TransferStatusPayload(
            assetID: fixture.journal.assetID,
            state: .uploading,
            byteCount: fixture.journal.byteCount,
            sha256: fixture.journal.sha256,
            chunkSize: fixture.journal.chunkSize,
            chunkCount: fixture.journal.chunkCount,
            acceptedChunks: [0, 3],
            missingChunks: [1, 2]
        )
        let falseVerified = TransferStatusPayload(
            assetID: fixture.journal.assetID,
            state: .verified,
            byteCount: fixture.journal.byteCount,
            sha256: fixture.journal.sha256,
            chunkSize: fixture.journal.chunkSize,
            chunkCount: fixture.journal.chunkCount,
            acceptedChunks: [0, 1],
            missingChunks: [2]
        )

        XCTAssertFalse(outOfRange.isValid(for: fixture.journal))
        XCTAssertFalse(falseVerified.isValid(for: fixture.journal))
    }
}
