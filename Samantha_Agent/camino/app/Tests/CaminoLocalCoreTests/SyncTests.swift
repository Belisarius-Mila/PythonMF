import Foundation
import XCTest
@testable import CaminoLocalCore

@MainActor final class SyncTests: XCTestCase {
    private let prague = TimeZone(identifier: "Europe/Prague")!

    private func instant(_ value: String) -> Date {
        ISO8601DateFormatter().date(from: value)!
    }

    private func media(id: UUID = UUID(), kind: CaminoSyncMediaKind,
                       batch: UUID, bytes: Int64 = 10) -> CaminoSyncMediaItem {
        CaminoSyncMediaItem(
            id: id, momentID: UUID(), kind: kind,
            sourceRelativePath: "Media/Originals/\(id).bin",
            byteCount: bytes, sha256: String(repeating: "a", count: 64),
            durationMilliseconds: kind == .photo ? nil : 1_000,
            batchID: batch, chunkSize: 4)
    }

    func testPriorityPauseAndOneDisplayedCellularBatch() throws {
        var journal = CaminoSyncJournal(deviceID: UUID(), openBatchID: UUID())
        let displayed = journal.openBatchID
        let video = media(kind: .video, batch: displayed)
        let photo = media(kind: .photo, batch: displayed)
        let audio = media(kind: .audio, batch: displayed)
        journal.merge(metadata: [], media: [video, photo, audio])
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: false), .media(audio.id))

        journal.paused = true
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: false), .none)
        journal.paused = false
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: true), .none)

        let granted = journal.grantCellularForDisplayedBatch()
        XCTAssertEqual(granted.mediaCount, 3)
        XCTAssertEqual(granted.mediaBytes, 30)
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: true), .media(audio.id))

        let later = media(kind: .audio, batch: journal.openBatchID)
        journal.merge(metadata: [], media: [later])
        journal.media.removeAll { $0.id != later.id }
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: true), .none,
                       "a later capture must never inherit the old cellular grant")
    }

    func testServerTruthAndEpochChangeFailClosed() throws {
        var journal = CaminoSyncJournal(deviceID: UUID())
        let server = UUID(), epoch = UUID()
        XCTAssertEqual(journal.observeServer(serverID: server, epoch: epoch, cursor: 0), .adopted)
        let item = media(kind: .video, batch: journal.openBatchID, bytes: 8)
        journal.media = [item]
        journal.media[0].acceptedChunks = [0, 1]
        journal.media[0].phase = .verifying
        XCTAssertEqual(journal.stats.mediaCount, 1,
                       "100 percent bytes is still waiting until server finalization")
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: false), .media(item.id))

        let restoredEpoch = UUID()
        XCTAssertEqual(
            journal.observeServer(serverID: server, epoch: restoredEpoch, cursor: 0),
            .epochChanged(previous: epoch, observed: restoredEpoch))
        XCTAssertTrue(journal.reconciliationRequired)
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: false), .none)
    }

    func testExactEnvelopeSurvivesJournalRestart() throws {
        let payload = try JSONSerialization.data(
            withJSONObject: ["id": UUID().uuidString.lowercased(), "name": "Synthetic"],
            options: [.sortedKeys])
        let operation = CaminoSyncMetadataItem(
            id: UUID(), uniqueKey: "synthetic", kind: "create_trip",
            objectID: UUID(), expectedRevision: nil, payload: payload)
        var journal = CaminoSyncJournal(deviceID: UUID())
        _ = journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        journal.metadata = [operation]
        let first = try journal.exactEnvelope(for: operation.id)
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c05b-\(UUID()).json")
        let store = CaminoSyncJournalStore(url: url)
        try store.save(journal)
        var reopened = try store.loadOrCreate()
        XCTAssertEqual(try reopened.exactEnvelope(for: operation.id), first)
        XCTAssertEqual(reopened.metadata[0].sequence, 1)
    }

    func testDiscoveryMapsTextWithoutAdvancingServerMomentRevision() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        let moment = try store.markMoment(
            at: instant("2026-09-20T08:00:00Z"), timeZone: prague)
        let text = try store.appendTextRevision(
            momentID: moment.id, role: .typedSource, content: "synthetic",
            at: instant("2026-09-20T08:01:00Z"))
        _ = try store.changePrivacy(
            momentID: moment.id, to: .ownerOnly, action: .lock,
            at: instant("2026-09-20T08:02:00Z"))
        let snapshot = try store.syncSnapshot(momentID: moment.id)
        let discovery = try CaminoSyncDiscovery(
            trips: [trip], days: try store.days(tripID: trip.id),
            moments: [snapshot], media: [])
        let append = try XCTUnwrap(discovery.metadata.first { $0.kind == "append_text" })
        let privacy = try XCTUnwrap(discovery.metadata.first {
            $0.kind == "update_metadata"
        })
        XCTAssertEqual(append.expectedRevision, 1)
        XCTAssertEqual(privacy.expectedRevision, 1,
                       "append_text does not advance C03b Moment metadata revision")
        let decoded = try JSONSerialization.jsonObject(with: append.payload) as? [String: Any]
        XCTAssertEqual(decoded?["id"] as? String, text.id.uuidString.lowercased())
    }

    func testMetadataChangeDoesNotQueueMediaAgain() throws {
        var journal = CaminoSyncJournal(deviceID: UUID())
        let batch = journal.openBatchID
        var photo = media(kind: .photo, batch: batch)
        photo.phase = .verified
        journal.media = [photo]
        let metadata = CaminoSyncMetadataItem(
            id: UUID(), uniqueKey: "operation:privacy", kind: "update_metadata",
            objectID: photo.momentID, expectedRevision: 1,
            payload: try JSONSerialization.data(withJSONObject: ["synthetic": true]))
        journal.merge(metadata: [metadata], media: [photo])
        XCTAssertEqual(journal.media.count, 1)
        XCTAssertEqual(journal.media[0].phase, .verified)
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: false),
                       .metadata(metadata.id))
        journal.metadata[0].phase = .needsAttention
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: false), .none,
                       "unresolved metadata must block lower-priority media")
    }

    func testInvalidJournalCannotClaimVerifiedOrAcceptedState() throws {
        let payload = try JSONSerialization.data(withJSONObject: ["synthetic": true])
        var journal = CaminoSyncJournal(deviceID: UUID())
        journal.metadata = [CaminoSyncMetadataItem(
            id: UUID(), uniqueKey: "synthetic", kind: "create_trip",
            objectID: UUID(), expectedRevision: nil, payload: payload,
            phase: .accepted)]
        XCTAssertFalse(journal.valid, "accepted metadata needs its exact persisted envelope")

        journal.metadata = []
        var item = media(kind: .video, batch: journal.openBatchID, bytes: 8)
        item.phase = .verified
        item.acceptedChunks = [0]
        journal.media = [item]
        XCTAssertFalse(journal.valid, "verified media needs every server-accepted chunk")
    }

    func testNewEnvelopeContinuesObservedServerCursor() throws {
        let payload = try JSONSerialization.data(withJSONObject: ["synthetic": true])
        var journal = CaminoSyncJournal(deviceID: UUID())
        _ = journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 5)
        let older = CaminoSyncMetadataItem(
            id: UUID(), uniqueKey: "old", kind: "create_trip", objectID: UUID(),
            expectedRevision: nil, payload: payload, sequence: 1,
            exactEnvelope: Data("old".utf8), phase: .accepted)
        let next = CaminoSyncMetadataItem(
            id: UUID(), uniqueKey: "next", kind: "create_day", objectID: UUID(),
            expectedRevision: nil, payload: payload)
        journal.metadata = [older, next]
        _ = try journal.exactEnvelope(for: next.id)
        XCTAssertEqual(journal.metadata[1].sequence, 6)
    }
}
