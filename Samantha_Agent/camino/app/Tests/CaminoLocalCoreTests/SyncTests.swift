import Foundation
import CryptoKit
import XCTest
@testable import CaminoLocalCore

@MainActor final class SyncTests: XCTestCase {
    private let prague = TimeZone(identifier: "Europe/Prague")!

    private func instant(_ value: String) -> Date {
        ISO8601DateFormatter().date(from: value)!
    }

    func testTripRenamePreservesIdentityMediaAndExactQueueAcrossReopen() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-trip-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let trip = try store.createTrip(name: "Zkouška", isTest: true)
        let moment = try store.markMoment()
        let photo = try store.beginMediaIntent(kind: .photo, targetMomentID: moment.id)
        _ = try store.acceptMedia(photo, inspection: LocalMediaInspection(byteCount: 12,
            sha256: String(repeating: "a", count: 64), width: 4, height: 3, orientation: 1,
            durationMilliseconds: nil, hasAudio: false, partial: false))
        let assets = try store.allMediaAssets()
        let before = try store.syncSnapshot(momentID: moment.id)
        let days = try store.days(tripID: trip.id)
        var journal = CaminoSyncJournal()
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        let candidate = CaminoSyncMediaItem(id: photo.assetID, momentID: moment.id, kind: .photo,
            sourceRelativePath: "synthetic/photo.jpg", byteCount: 12, sha256: String(repeating: "a", count: 64),
            durationMilliseconds: nil, batchID: journal.openBatchID)
        let original = try CaminoSyncDiscovery(trips: store.trips(), days: days, moments: [before], media: [candidate])
        journal.mergeDiscovery(original)
        var envelopes: [Any] = []
        for item in journal.metadata {
            envelopes.append(try JSONSerialization.jsonObject(with: journal.exactEnvelope(for: item.id)))
        }
        for index in journal.metadata.indices { journal.metadata[index].phase = .accepted }
        for index in journal.media.indices { journal.media[index].phase = .verified }
        let oldQueue = journal.metadata
        let renamed = try store.updateTrip(trip.id, name: " Camino de Santiago ", isTest: false)
        XCTAssertEqual(renamed.id, trip.id)
        XCTAssertEqual(renamed.name, "Camino de Santiago")
        XCTAssertFalse(renamed.isTest)
        _ = try store.updateTrip(trip.id, name: renamed.name, isTest: false)
        XCTAssertThrowsError(try store.updateTrip(trip.id, name: "", isTest: true))
        XCTAssertThrowsError(try store.updateTrip(trip.id, name: "a\u{2028}b", isTest: true))
        XCTAssertThrowsError(try store.updateTrip(trip.id, name: String(repeating: "x", count: 161), isTest: true))
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.activeTrip(), renamed)
        XCTAssertEqual(try reopened.allMediaAssets(), assets)
        XCTAssertEqual(try reopened.days(tripID: trip.id), days)
        XCTAssertEqual(try reopened.syncSnapshot(momentID: moment.id), before)
        let next = try CaminoSyncDiscovery(trips: reopened.trips(), days: days, moments: [before], media: [candidate])
        XCTAssertEqual(next.metadata.first?.payload, original.metadata.first?.payload)
        journal.mergeDiscovery(next)
        XCTAssertEqual(Array(journal.metadata.prefix(oldQueue.count)), oldQueue)
        XCTAssertEqual(journal.metadata.count, oldQueue.count + 1)
        XCTAssertTrue(journal.media.allSatisfy { $0.phase == .verified })
        XCTAssertThrowsError(try journal.requireTitleSupport(serverFeatures: []))
        XCTAssertNoThrow(try journal.requireTitleSupport(serverFeatures: ["trip_title_v1"]))
        let change = try XCTUnwrap(journal.metadata.last)
        XCTAssertEqual(change.expectedRevision, 1)
        let raw = try journal.exactEnvelope(for: change.id)
        envelopes.append(try JSONSerialization.jsonObject(with: raw))
        var restoredJournal = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
        XCTAssertEqual(try restoredJournal.exactEnvelope(for: change.id), raw)
        _ = try reopened.updateTrip(trip.id, name: "Druhé jméno", isTest: false)
        let second = try CaminoSyncDiscovery(trips: reopened.trips(), days: days, moments: [before], media: [candidate])
        restoredJournal.mergeDiscovery(second)
        let last = try XCTUnwrap(restoredJournal.metadata.last)
        XCTAssertEqual(last.expectedRevision, 2)
        envelopes.append(try JSONSerialization.jsonObject(with: restoredJournal.exactEnvelope(for: last.id)))
        if let path = ProcessInfo.processInfo.environment["CAMINO_TRIP_WIRE_FIXTURE"] {
            try JSONSerialization.data(withJSONObject: envelopes, options: [.sortedKeys])
                .write(to: URL(fileURLWithPath: path), options: .atomic)
        }
    }

    func testTitleWireSequenceDoesNotRewriteCreateAndRequiresServerSupport() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic title")
        let moment = try store.markMoment()
        func discovery() throws -> CaminoSyncDiscovery {
            try CaminoSyncDiscovery(trips: [trip], days: store.days(tripID: trip.id),
                moments: [store.syncSnapshot(momentID: moment.id)], media: [])
        }
        let original = try XCTUnwrap(discovery().metadata.first { $0.kind == "create_moment" }).payload
        _ = try store.setTitle(momentID: moment.id, title: "Káva u řeky 🥾")
        _ = try store.setTitle(momentID: moment.id, title: "Opravený název")
        let items = try discovery().metadata
        XCTAssertEqual(items.first { $0.kind == "create_moment" }?.payload, original)
        XCTAssertEqual(items.filter(\.isTitleChange).map(\.expectedRevision), [1, 2])
        var journal = CaminoSyncJournal()
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        journal.merge(metadata: items, media: [])
        XCTAssertThrowsError(try journal.requireTitleSupport(serverFeatures: ["audio_layout_v1"]))
        XCTAssertNoThrow(try journal.requireTitleSupport(serverFeatures: ["moment_title_v1"]))
        var envelopes: [Any] = []
        for item in journal.metadata {
            let data = try journal.exactEnvelope(for: item.id)
            envelopes.append(try JSONSerialization.jsonObject(with: data))
            var reopened = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
            XCTAssertEqual(try reopened.exactEnvelope(for: item.id), data)
        }
        if let path = ProcessInfo.processInfo.environment["CAMINO_TITLE_WIRE_FIXTURE"] {
            try JSONSerialization.data(withJSONObject: envelopes, options: [.sortedKeys])
                .write(to: URL(fileURLWithPath: path), options: .atomic)
        }
    }

    func testAttachmentWireDependenciesOldQueueAndMetadataOnlyRename() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic attachments")
        let moment = try store.markMoment()
        let photo = try store.beginMediaIntent(kind: .photo, targetMomentID: moment.id)
        _ = try store.acceptMedia(photo, inspection: LocalMediaInspection(byteCount: 12,
            sha256: String(repeating: "a", count: 64), width: 4, height: 3, orientation: 1,
            durationMilliseconds: nil, hasAudio: false, partial: false))
        let session = UUID(), audioID = UUID()
        _ = try store.beginAudioIntent(sessionID: session, kind: .comment, startedAt: Date(), targetMomentID: moment.id)
        _ = try store.acceptCompletedAudio(sessionID: session, kind: .comment, partial: false)
        var journal = CaminoSyncJournal()
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        let candidates = [(photo.assetID, CaminoSyncMediaKind.photo), (audioID, .audio)].map { id, kind in
            CaminoSyncMediaItem(id: id, momentID: moment.id, kind: kind,
                sourceRelativePath: "synthetic/\(id).bin", byteCount: 12,
                sha256: String(repeating: "a", count: 64), durationMilliseconds: kind == .audio ? 1000 : nil,
                batchID: journal.openBatchID)
        }
        let layout = CaminoSyncAudioLayout(clipID: session, momentID: moment.id, sessionID: session,
            previousClipID: nil, gapBeforeMilliseconds: nil, missingTail: false,
            parts: [.init(assetID: audioID, index: 0, discontinuityBefore: false)])
        func discovery() throws -> CaminoSyncDiscovery {
            try CaminoSyncDiscovery(trips: [trip], days: store.days(tripID: trip.id),
                moments: [store.syncSnapshot(momentID: moment.id)], media: candidates, audioLayouts: [layout])
        }
        let old = try discovery()
        journal.mergeDiscovery(old) // Old pending journal has no optional audio layout yet.
        var envelopes: [Any] = []
        for item in journal.metadata {
            let data = try journal.exactEnvelope(for: item.id)
            envelopes.append(try JSONSerialization.jsonObject(with: data))
        }
        let original = journal.metadata
        _ = try store.setTitle(momentID: moment.id, title: "Okamžik")
        _ = try store.setAttachmentTitle(momentID: moment.id, kind: .asset, targetID: photo.assetID, title: "Fotografie 🥾")
        _ = try store.setAttachmentTitle(momentID: moment.id, kind: .audioSession, targetID: session, title: "Komentář 🥾")
        let updated = try discovery()
        journal.mergeDiscovery(updated)
        XCTAssertEqual(Array(journal.metadata.prefix(original.count)), original)
        XCTAssertThrowsError(try journal.requireTitleSupport(serverFeatures: ["moment_title_v1", "audio_layout_v1"]))
        XCTAssertNoThrow(try journal.requireTitleSupport(serverFeatures: ["moment_title_v1", "audio_layout_v1", "attachment_title_v1"]))
        let layoutIndex = try XCTUnwrap(journal.metadata.firstIndex { $0.kind == "create_audio_layout" })
        let lastTitle = try XCTUnwrap(journal.metadata.lastIndex(where: \.isAttachmentTitleChange))
        XCTAssertLessThan(layoutIndex, lastTitle)
        for item in journal.metadata.dropFirst(original.count) {
            envelopes.append(try JSONSerialization.jsonObject(with: journal.exactEnvelope(for: item.id)))
        }
        for index in journal.metadata.indices { journal.metadata[index].phase = .accepted }
        for index in journal.media.indices { journal.media[index].phase = .verified }
        let before = journal.metadata.count
        _ = try store.setAttachmentTitle(momentID: moment.id, kind: .audioSession, targetID: session, title: "Opravený komentář")
        journal.mergeDiscovery(try discovery())
        XCTAssertEqual(journal.metadata.count, before + 1)
        XCTAssertTrue(journal.media.allSatisfy { $0.phase == .verified })
        let last = try XCTUnwrap(journal.metadata.last)
        let raw = try journal.exactEnvelope(for: last.id)
        envelopes.append(try JSONSerialization.jsonObject(with: raw))
        var reopened = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
        XCTAssertEqual(try reopened.exactEnvelope(for: last.id), raw)
        if let path = ProcessInfo.processInfo.environment["CAMINO_ATTACHMENT_WIRE_FIXTURE"] {
            try JSONSerialization.data(withJSONObject: envelopes, options: [.sortedKeys])
                .write(to: URL(fileURLWithPath: path), options: .atomic)
        }
    }

    func testCompletedCellularBatchKeepsVerifiedButNewWorkAndLostReceiptDoNot() throws {
        var journal = CaminoSyncJournal()
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        var asset = media(kind: .video, batch: journal.openBatchID)
        let momentID = asset.momentID
        journal.metadata = [CaminoSyncMetadataItem(id: UUID(), uniqueKey: "moment", kind: "create_moment",
            objectID: momentID, expectedRevision: nil, payload: Data("{}".utf8), phase: .accepted)]
        journal.media = [asset]
        _ = journal.grantCellularForDisplayedBatch()
        XCTAssertNil(journal.blockedNetworkState(networkAvailable: true, expensive: true, momentIDs: [momentID]))
        asset.phase = .verified
        journal.media[0] = asset
        journal.revokeCellularIfFinished()
        XCTAssertNil(journal.cellularBatchID)
        XCTAssertEqual(journal.blockedNetworkState(networkAvailable: true, expensive: true, momentIDs: [momentID]), .verified)
        XCTAssertEqual(journal.blockedNetworkState(networkAvailable: false, expensive: true, momentIDs: [momentID]), .verified)
        XCTAssertEqual(journal.blockedNetworkState(networkAvailable: true, expensive: true,
            momentIDs: [momentID], hasUnqueuedMetadata: true), .waitingForWiFi)
        journal.reconciliationRequired = true
        XCTAssertEqual(journal.blockedNetworkState(networkAvailable: true, expensive: true, momentIDs: [momentID]), .reconciliationRequired)
        journal.reconciliationRequired = false
        journal.media[0].phase = .verifying // Server success without a client receipt is not green.
        XCTAssertEqual(journal.blockedNetworkState(networkAvailable: false, expensive: true, momentIDs: [momentID]), .waitingForNetwork)
        journal.media[0].phase = .verified
        journal.media.append(media(kind: .photo, batch: journal.openBatchID))
        XCTAssertEqual(journal.blockedNetworkState(networkAvailable: true, expensive: true, momentIDs: [momentID]), .waitingForWiFi)
        XCTAssertEqual(journal.nextWork(networkAvailable: true, expensive: true), .none)
        let empty = CaminoSyncJournal()
        XCTAssertNotEqual(empty.blockedNetworkState(networkAvailable: true, expensive: true, momentIDs: []), .verified)
    }

    private func recoveryJournal() throws -> CaminoSyncJournal {
        var journal = CaminoSyncJournal()
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        let item = CaminoSyncMetadataItem(id: UUID(), uniqueKey: "recovery-trip",
            kind: "create_trip", objectID: UUID(), expectedRevision: nil,
            payload: Data("{\"name\":\"synthetic\"}".utf8))
        journal.metadata = [item]
        _ = try journal.exactEnvelope(for: item.id)
        journal.metadata[0].phase = .accepted
        journal.observeServer(serverID: journal.serverID!, epoch: UUID(), cursor: 1)
        journal.paused = true
        return journal
    }

    private func recoveryReceipt(_ proof: CaminoRecoveryProof,
                                 digest: String? = nil) throws -> CaminoRecoveryReceipt {
        let data = try JSONSerialization.data(withJSONObject: [
            "contract_version": 1, "server_id": proof.server_id, "epoch": proof.epoch,
            "cursor": proof.cursor, "exports_blocked": false, "reconciliation_required": false,
            "request_sha256": digest ?? SHA256.hash(data: proof.encoded())
                .map { String(format: "%02x", $0) }.joined(),
        ])
        return try JSONDecoder().decode(CaminoRecoveryReceipt.self, from: data)
    }

    func testRecoveryPreservesExactHistoryPauseAndPersistsNewEpoch() throws {
        var journal = try recoveryJournal()
        let original = journal.metadata[0].exactEnvelope
        let proof = try journal.recoveryProof(serverID: journal.serverID!,
            epoch: journal.observedEpoch!, cursor: 1, moments: [])
        try journal.finishRecovery(recoveryReceipt(proof), proof: proof)
        XCTAssertTrue(journal.valid)
        XCTAssertTrue(journal.paused)
        XCTAssertFalse(journal.reconciliationRequired)
        XCTAssertEqual(journal.epoch, UUID(uuidString: proof.epoch))
        XCTAssertEqual(journal.metadata[0].exactEnvelope, original)
        let decoded = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
        XCTAssertEqual(decoded, journal)
        XCTAssertTrue(decoded.valid)
        let fresh = CaminoSyncMetadataItem(id: UUID(), uniqueKey: "later", kind: "create_trip",
            objectID: UUID(), expectedRevision: nil, payload: Data("{}".utf8))
        journal.metadata.append(fresh)
        let envelope = try JSONSerialization.jsonObject(with: journal.exactEnvelope(for: fresh.id)) as! [String: Any]
        XCTAssertEqual(envelope["epoch"] as? String, proof.epoch)
        XCTAssertEqual(envelope["device_sequence"] as? Int, 2)
    }

    func testRecoveryLostReceiptCanRetryButBadReceiptCannotMutateJournal() throws {
        var journal = try recoveryJournal()
        journal.metadata[0].phase = .pending // Server accepted it, client lost the response.
        let original = journal
        let proof = try journal.recoveryProof(serverID: journal.serverID!,
            epoch: journal.observedEpoch!, cursor: 1, moments: [])
        XCTAssertThrowsError(try journal.finishRecovery(recoveryReceipt(proof, digest: "wrong"), proof: proof))
        XCTAssertEqual(journal, original)
        var reopened = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
        XCTAssertEqual(try reopened.recoveryProof(serverID: journal.serverID!,
            epoch: journal.observedEpoch!, cursor: 1, moments: []), proof)
        try reopened.finishRecovery(recoveryReceipt(proof), proof: proof)
        XCTAssertEqual(reopened.metadata[0].phase, .accepted)
        XCTAssertEqual(reopened.metadata[0].exactEnvelope, original.metadata[0].exactEnvelope)
    }

    func testRecoveryRejectsOtherServerMissingSequencePendingWorkAndMedia() throws {
        var journal = try recoveryJournal()
        XCTAssertThrowsError(try journal.recoveryProof(serverID: UUID(), epoch: UUID(), cursor: 1, moments: []))
        XCTAssertThrowsError(try journal.recoveryProof(serverID: journal.serverID!, epoch: UUID(), cursor: 0, moments: []))
        journal.media = [media(kind: .video, batch: journal.openBatchID)]
        XCTAssertThrowsError(try journal.recoveryProof(serverID: journal.serverID!, epoch: UUID(), cursor: 1, moments: []))
        journal.media = []
        journal.metadata[0].sequence = 2
        XCTAssertThrowsError(try journal.recoveryProof(serverID: journal.serverID!, epoch: UUID(), cursor: 1, moments: []))
        journal = try recoveryJournal()
        journal.metadata.append(CaminoSyncMetadataItem(id: UUID(), uniqueKey: "unsent", kind: "create_trip",
            objectID: UUID(), expectedRevision: nil, payload: Data("{}".utf8)))
        XCTAssertThrowsError(try journal.recoveryProof(serverID: journal.serverID!, epoch: UUID(), cursor: 1, moments: []))
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

    func testAdoptEmptyServerResetsOnlySyncIdentityAndPreservesPause() throws {
        var journal = CaminoSyncJournal(deviceID: UUID())
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        journal.reconciliationRequired = true
        journal.paused = true
        let serverID = UUID(), epoch = UUID()
        try journal.adoptEmptyServer(serverID: serverID, epoch: epoch, cursor: 0)
        XCTAssertEqual(journal.serverID, serverID)
        XCTAssertEqual(journal.epoch, epoch)
        XCTAssertEqual(journal.observedEpoch, epoch)
        XCTAssertEqual(journal.serverCursor, 0)
        XCTAssertFalse(journal.reconciliationRequired)
        XCTAssertTrue(journal.paused)
        XCTAssertTrue(journal.metadata.isEmpty)
        XCTAssertTrue(journal.media.isEmpty)
    }

    func testAdoptEmptyServerRejectsPendingHistoryOrNonzeroCursor() throws {
        var journal = CaminoSyncJournal()
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        journal.reconciliationRequired = true
        journal.metadata = [CaminoSyncMetadataItem(id: UUID(), uniqueKey: "pending",
            kind: "create_trip", objectID: UUID(), expectedRevision: nil,
            payload: Data("{}".utf8))]
        XCTAssertThrowsError(try journal.adoptEmptyServer(serverID: UUID(), epoch: UUID(), cursor: 0))
        journal.metadata.removeAll()
        XCTAssertThrowsError(try journal.adoptEmptyServer(serverID: UUID(), epoch: UUID(), cursor: 1))
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

    func testDeletedContentSuppressesOnlyPendingWorkAndKeepsAcceptedHistory() throws {
        let momentID = UUID(), assetID = UUID()
        var journal = CaminoSyncJournal(deviceID: UUID())
        let moment = CaminoSyncMetadataItem(id: UUID(), uniqueKey: "moment",
            kind: "create_moment", objectID: momentID, expectedRevision: nil,
            payload: Data("{}".utf8), phase: .pending)
        let asset = CaminoSyncMetadataItem(id: assetID, uniqueKey: "asset",
            kind: "create_asset", objectID: assetID, expectedRevision: nil,
            payload: Data("{\"moment_id\":\"\(momentID.uuidString.lowercased())\"}".utf8), phase: .pending)
        let accepted = CaminoSyncMetadataItem(id: UUID(), uniqueKey: "accepted",
            kind: "create_asset", objectID: assetID, expectedRevision: nil,
            payload: Data("{}".utf8), phase: .accepted)
        journal.metadata = [moment, asset, accepted]
        journal.media = [media(id: assetID, kind: .photo, batch: journal.openBatchID)]
        journal.suppressDeletedContent(momentIDs: [momentID], assetIDs: [assetID])
        XCTAssertEqual(journal.metadata.map(\.uniqueKey), ["accepted"])
        XCTAssertTrue(journal.media.isEmpty)
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
