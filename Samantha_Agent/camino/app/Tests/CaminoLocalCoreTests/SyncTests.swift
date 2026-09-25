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

    func testCoverageCountsMomentsSeparatelyFromFilesAndSegments() throws {
        let completeID = UUID(), waitingID = UUID()
        let payload = try JSONSerialization.data(withJSONObject: ["synthetic": true])
        let completeOperation = CaminoSyncMetadataItem(
            id: UUID(), uniqueKey: "moment:complete", kind: "create_moment",
            objectID: completeID, expectedRevision: nil, payload: payload,
            phase: .accepted)
        let waitingOperation = CaminoSyncMetadataItem(
            id: UUID(), uniqueKey: "moment:waiting", kind: "create_moment",
            objectID: waitingID, expectedRevision: nil, payload: payload)
        var verifiedAudio = media(kind: .audio, batch: UUID(), bytes: 8)
        verifiedAudio = CaminoSyncMediaItem(
            id: verifiedAudio.id, momentID: completeID, kind: .audio,
            sourceRelativePath: verifiedAudio.sourceRelativePath,
            byteCount: verifiedAudio.byteCount, sha256: verifiedAudio.sha256,
            durationMilliseconds: verifiedAudio.durationMilliseconds,
            batchID: verifiedAudio.batchID, chunkSize: verifiedAudio.chunkSize,
            acceptedChunks: [0, 1], phase: .verified)
        let waitingVideo = CaminoSyncMediaItem(
            id: UUID(), momentID: waitingID, kind: .video,
            sourceRelativePath: "Media/Originals/waiting.bin", byteCount: 10,
            sha256: String(repeating: "b", count: 64), durationMilliseconds: 1_000,
            batchID: UUID(), chunkSize: 4)
        var journal = CaminoSyncJournal(deviceID: UUID())
        journal.metadata = [completeOperation, waitingOperation]
        journal.media = [verifiedAudio, waitingVideo]

        let coverage = journal.coverage(momentIDs: [completeID, waitingID])
        XCTAssertEqual(coverage.phoneMomentCount, 2)
        XCTAssertEqual(coverage.macCompleteMomentCount, 1)
        XCTAssertEqual(coverage.macWaitingMomentCount, 1)
        XCTAssertEqual(coverage.pendingMetadataCount, 1)
        XCTAssertEqual(coverage.pendingMediaCount, 1)
        XCTAssertEqual(coverage.pendingMediaBytes, 10)
    }

    func testT054FourAxesStayIndependent() {
        let coverage = CaminoSyncCoverage(
            phoneMomentCount: 2, macCompleteMomentCount: 2,
            macWaitingMomentCount: 0)
        let aiWithoutBackup = CaminoC05cDashboard(
            coverage: coverage, macState: .verified,
            backupState: .notVerified, aiState: .completed(count: 1))
        XCTAssertEqual(aiWithoutBackup.axes.map(\.id), ["phone", "mac", "backup", "ai"])
        XCTAssertEqual(aiWithoutBackup.mac.tone, .verified)
        XCTAssertEqual(aiWithoutBackup.phone.tone, .verified)
        XCTAssertEqual(aiWithoutBackup.ai.tone, .verified)
        XCTAssertEqual(aiWithoutBackup.backup.tone, .neutral)
        XCTAssertEqual(aiWithoutBackup.backup.value,
                       "Další záloha zatím není ověřená")
        XCTAssertTrue(aiWithoutBackup.ai.detail.contains("Přepis není záloha"))

        let backupWithoutAI = CaminoC05cDashboard(
            coverage: coverage, macState: .verified,
            backupState: .verified(through: "18:42"),
            aiState: .waiting(count: 1))
        XCTAssertEqual(backupWithoutAI.backup.tone, .verified)
        XCTAssertEqual(backupWithoutAI.backup.value, "Ověřeno do 18:42")
        XCTAssertEqual(backupWithoutAI.ai.tone, .waiting)
        XCTAssertEqual(backupWithoutAI.mac.tone, .verified)
    }

    func testT055MetadataChangeStalesOnlyBackupMetadataCoverage() {
        let dashboard = CaminoC05cDashboard(
            coverage: CaminoSyncCoverage(
                phoneMomentCount: 1, macCompleteMomentCount: 1,
                macWaitingMomentCount: 0),
            macState: .verified,
            backupState: .mediaVerifiedMetadataPending(through: "18:42"),
            aiState: .completed(count: 1))
        XCTAssertEqual(dashboard.mac.tone, .verified,
                       "the already verified Mac media remains verified")
        XCTAssertEqual(dashboard.backup.tone, .waiting)
        XCTAssertEqual(dashboard.backup.value,
                       "Média zálohována, novější změny ještě čekají")
        XCTAssertTrue(dashboard.backup.detail.contains("text nebo soukromí"))
        XCTAssertEqual(dashboard.ai.tone, .verified,
                       "backup freshness must not rewrite the AI axis")
    }

    func testC05cUserMessagesDoNotInventNetworkCauseOrExposeServerCodes() {
        let coverage = CaminoSyncCoverage(phoneMomentCount: 1,
                                          macWaitingMomentCount: 1)
        let wifi = CaminoC05cDashboard(
            coverage: coverage, macState: .waitingForWiFi,
            backupState: .notVerified, aiState: .notConfigured)
        XCTAssertEqual(wifi.mac.value, "Čeká na Wi‑Fi. V telefonu je uloženo.")

        let unavailable = CaminoC05cDashboard(
            coverage: coverage, macState: .unavailable,
            backupState: .notVerified, aiState: .notConfigured)
        XCTAssertEqual(unavailable.mac.value, "Domácí Mac teď není dostupný")
        XCTAssertTrue(unavailable.mac.detail.contains("Příčinu nelze spolehlivě určit"))

        let verifying = CaminoC05cDashboard(
            coverage: coverage, macState: .verifying,
            backupState: .notVerified, aiState: .notConfigured)
        XCTAssertEqual(verifying.mac.value, "Ověřuji")
        XCTAssertTrue(verifying.mac.detail.contains("Ještě není Ověřeno na Macu"))

        let rejected = CaminoC05cDashboard(
            coverage: coverage, macState: .rejected,
            backupState: .notVerified, aiState: .notConfigured)
        XCTAssertFalse(rejected.mac.detail.contains("revision_conflict"))
        XCTAssertTrue(rejected.mac.detail.contains("Originály zůstávají v telefonu"))

        let inconsistentSuccess = CaminoC05cDashboard(
            coverage: coverage, macState: .verified,
            backupState: .notVerified, aiState: .notConfigured)
        XCTAssertEqual(inconsistentSuccess.mac.tone, .attention,
                       "a waiting Moment must fail closed even if the driver says verified")
        XCTAssertEqual(CaminoC05cDashboard.initial.phone.tone, .neutral)
    }

    func testAudioLayoutBackfillsWithoutReuploadOrRewritingOldJournalEnvelopes() throws {
        let local = try CaminoLocalStore(inMemory: true)
        let trip = try local.createTrip(name: "Synthetic")
        let moment = try local.markMoment(at: instant("2026-09-25T08:00:00Z"), timeZone: prague)
        let asset = CaminoSyncMediaItem(id: UUID(), momentID: moment.id, kind: .audio,
            sourceRelativePath: "audio.caf", byteCount: 4, sha256: String(repeating: "a", count: 64),
            durationMilliseconds: 1000, batchID: UUID(), phase: .verified)
        let clip = UUID()
        let layout = CaminoSyncAudioLayout(clipID: clip, momentID: moment.id, sessionID: clip,
            previousClipID: nil, gapBeforeMilliseconds: nil, missingTail: false,
            parts: [.init(assetID: asset.id, index: 0, discontinuityBefore: false)])
        let original = try CaminoSyncDiscovery(trips: [trip], days: local.days(tripID: trip.id),
            moments: [local.syncSnapshot(momentID: moment.id)], media: [asset])
        let newer = try CaminoSyncDiscovery(trips: [trip], days: local.days(tripID: trip.id),
            moments: [local.syncSnapshot(momentID: moment.id)], media: [asset], audioLayouts: [layout])
        XCTAssertEqual(original.metadata, newer.metadata.filter { $0.kind != "create_audio_layout" })
        var journal = CaminoSyncJournal(deviceID: UUID())
        _ = journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        journal.merge(metadata: original.metadata, media: [asset])
        for item in original.metadata {
            _ = try journal.exactEnvelope(for: item.id)
            let index = try XCTUnwrap(journal.metadata.firstIndex { $0.id == item.id })
            journal.metadata[index].phase = .accepted
        }
        let oldEnvelopes = journal.metadata.map(\.exactEnvelope)
        let drafts = newer.metadata.filter { $0.kind == "create_audio_layout" }
        try journal.mergeAudioLayouts(drafts, serverFeatures: nil)
        XCTAssertEqual(journal.metadata.count, original.metadata.count)
        try journal.mergeAudioLayouts(drafts, serverFeatures: ["audio_layout_v1"])
        XCTAssertEqual(journal.metadata.dropLast().map(\.exactEnvelope), oldEnvelopes)
        XCTAssertEqual(journal.media, [asset])
        let item = try XCTUnwrap(journal.metadata.last)
        XCTAssertEqual(item.relatedMomentID, moment.id)
        let exact = try journal.exactEnvelope(for: item.id)
        var reopened = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
        XCTAssertEqual(try reopened.exactEnvelope(for: item.id), exact)
        XCTAssertThrowsError(try reopened.mergeAudioLayouts(drafts, serverFeatures: []))
        XCTAssertEqual(try reopened.exactEnvelope(for: item.id), exact)
        try reopened.mergeAudioLayouts(drafts, serverFeatures: ["audio_layout_v1"])
        XCTAssertEqual(reopened.metadata.count, original.metadata.count + 1)
        XCTAssertEqual(reopened.media.first?.phase, .verified)
    }
}
