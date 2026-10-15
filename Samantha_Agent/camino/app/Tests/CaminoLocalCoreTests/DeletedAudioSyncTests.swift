import Foundation
import XCTest
@testable import CaminoLocalCore

@MainActor final class DeletedAudioSyncTests: XCTestCase {
    private func fixture() throws -> (CaminoLocalStore, UUID, UUID, UUID, CaminoSyncJournal) {
        let local = try CaminoLocalStore(inMemory: true)
        let trip = try local.createTrip(name: "Synthetic deleted audio")
        let moment = try local.markMoment()
        let session = UUID(), assetID = UUID()
        _ = try local.beginAudioIntent(sessionID: session, kind: .comment, startedAt: Date(),
                                       targetMomentID: moment.id)
        _ = try local.acceptCompletedAudio(sessionID: session, kind: .comment, partial: false)
        var journal = CaminoSyncJournal()
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        let asset = CaminoSyncMediaItem(id: assetID, momentID: moment.id, kind: .audio,
            sourceRelativePath: "synthetic/audio.caf", byteCount: 4,
            sha256: String(repeating: "a", count: 64), durationMilliseconds: 1000,
            batchID: journal.openBatchID)
        let layout = CaminoSyncAudioLayout(clipID: session, momentID: moment.id, sessionID: session,
            previousClipID: nil, gapBeforeMilliseconds: nil, missingTail: false,
            parts: [.init(assetID: assetID, index: 0, discontinuityBefore: false)])
        let discovery = try CaminoSyncDiscovery(trips: [trip], days: local.days(tripID: trip.id),
            moments: [local.syncSnapshot(momentID: moment.id)], media: [asset], audioLayouts: [layout])
        journal.mergeDiscovery(discovery)
        try journal.mergeAudioLayouts(discovery.metadata.filter { $0.kind == "create_audio_layout" },
                                      serverFeatures: ["audio_layout_v1"])
        return (local, moment.id, session, assetID, journal)
    }

    func testDeletedUnsentAudioLayoutMustNotOutliveItsSuppressedSource() throws {
        let (local, momentID, session, assetID, initial) = try fixture()
        var journal = initial
        _ = try local.deleteAudioSession(sessionID: session, momentID: momentID)
        XCTAssertTrue(try local.audioSessionIDs(momentID: momentID).isEmpty)
        XCTAssertEqual(try local.deletionRecords().filter { $0.kind == .audioSession }.map(\.targetID), [session])
        journal.suppressDeletedContent(momentIDs: [], assetIDs: [assetID])
        XCTAssertFalse(journal.metadata.contains { $0.kind == "create_asset" })
        XCTAssertTrue(journal.media.isEmpty)
        XCTAssertFalse(journal.metadata.contains { $0.kind == "create_audio_layout" },
                       "Deleted audio must not leave a layout referring to its removed source declaration")
    }

    func testDeletionMustPreserveAlreadyAssignedEnvelopeAndItsSequence() throws {
        let (_, momentID, _, assetID, initial) = try fixture()
        var journal = initial
        let asset = try XCTUnwrap(journal.metadata.first { $0.kind == "create_asset" })
        let exact = try journal.exactEnvelope(for: asset.id)
        let sequence = journal.metadata.first { $0.id == asset.id }?.sequence
        journal.suppressDeletedContent(momentIDs: [momentID], assetIDs: [assetID])
        XCTAssertEqual(journal.metadata.first { $0.id == asset.id }?.exactEnvelope, exact,
                       "An attempted packet cannot disappear before a receipt or explicit repair")
        XCTAssertEqual(journal.metadata.first { $0.id == asset.id }?.sequence, sequence)
    }

    private func rejected() throws -> (CaminoSyncJournal, CaminoLocalStore, LocalDeletionRecord,
                                       UUID, CaminoDeletedAudioLayoutRepairProof) {
        let (local, momentID, session, _, initial) = try fixture()
        var journal = initial
        // Build the exact legacy build-18 state: a pending layout outlived the
        // unsent source declaration. No live database or recording is touched.
        journal.metadata.removeAll { $0.kind == "create_asset" }
        journal.media = []
        for index in journal.metadata.indices where journal.metadata[index].kind != "create_audio_layout" {
            _ = try journal.exactEnvelope(for: journal.metadata[index].id)
            journal.metadata[index].phase = .accepted
            journal.serverCursor = try XCTUnwrap(journal.metadata[index].sequence)
        }
        let layoutID = try XCTUnwrap(journal.metadata.first { $0.kind == "create_audio_layout" }?.id)
        _ = try journal.exactEnvelope(for: layoutID)
        let deletion = try local.deleteAudioSession(sessionID: session, momentID: momentID)
        let proof = CaminoDeletedAudioLayoutRepairProof(serverID: try XCTUnwrap(journal.serverID),
            epoch: try XCTUnwrap(journal.epoch), cursor: journal.serverCursor)
        return (journal, local, deletion, layoutID, proof)
    }

    func testRejectedDeletedLayoutRepairKeepsOriginalAndTombstoneAcrossRetryAndReopen() throws {
        let (initial, _, deletion, id, proof) = try rejected()
        var journal = initial
        XCTAssertTrue(try journal.repairRejectedDeletedAudioLayout(id: id, deletions: [deletion],
            status: 404, code: "not_found", proof: proof, serverBlocked: false))
        let original = try XCTUnwrap(initial.metadata.first { $0.id == id })
        let repaired = try XCTUnwrap(journal.metadata.first { $0.id == id })
        XCTAssertEqual(repaired.id, original.id)
        XCTAssertEqual(repaired.sequence, original.sequence)
        XCTAssertEqual(repaired.expectedRevision, original.expectedRevision)
        XCTAssertEqual(journal.metadata.filter { $0.id != id }, initial.metadata.filter { $0.id != id })
        XCTAssertEqual(journal.media, initial.media)
        XCTAssertEqual(journal.rejectedAudioLayoutHistory?.first?.original, original)
        XCTAssertEqual(journal.rejectedAudioLayoutHistory?.first?.deletion, deletion)
        let payload = try XCTUnwrap(JSONSerialization.jsonObject(with: repaired.payload) as? [String: Any])
        XCTAssertEqual(payload["type"] as? String, "cancel_deleted_audio_layout")
        XCTAssertEqual(payload["rejected_envelope"] as? String,
                       String(data: try XCTUnwrap(original.exactEnvelope), encoding: .utf8))
        let exact = try journal.exactEnvelope(for: id)
        var reopened = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
        XCTAssertTrue(reopened.valid)
        XCTAssertEqual(try reopened.exactEnvelope(for: id), exact)
        XCTAssertEqual(reopened.rejectedAudioLayoutHistory, journal.rejectedAudioLayoutHistory)
        XCTAssertFalse(try reopened.repairRejectedDeletedAudioLayout(id: id, deletions: [deletion],
            status: 404, code: "not_found", proof: proof, serverBlocked: false))
        reopened.suppressDeletedContent(momentIDs: [deletion.momentID], assetIDs: [],
                                         audioSessionIDs: [deletion.targetID])
        XCTAssertEqual(try reopened.exactEnvelope(for: id), exact)
    }

    func testRepairRefusesOtherStatusIdentityCursorAcceptedPacketAndUnrelatedDeletion() throws {
        let (initial, _, deletion, id, proof) = try rejected()
        let unrelated = LocalDeletionRecord(kind: .audioSession, targetID: deletion.targetID,
            momentID: UUID(), createdAtUTCMilliseconds: 1, expectedRevision: 1)
        let assetDeletion = LocalDeletionRecord(kind: .asset, targetID: deletion.targetID,
            momentID: deletion.momentID, createdAtUTCMilliseconds: 1, expectedRevision: 1)
        let cases: [(Int, String, Bool, [LocalDeletionRecord], CaminoDeletedAudioLayoutRepairProof)] = [
            (422, "not_found", false, [deletion], proof),
            (503, "not_found", false, [deletion], proof),
            (404, "invalid_request", false, [deletion], proof),
            (404, "not_found", true, [deletion], proof),
            (404, "not_found", false, [], proof),
            (404, "not_found", false, [unrelated], proof),
            (404, "not_found", false, [assetDeletion], proof),
            (404, "not_found", false, [deletion], .init(serverID: UUID(), epoch: proof.epoch, cursor: proof.cursor)),
            (404, "not_found", false, [deletion], .init(serverID: proof.serverID, epoch: UUID(), cursor: proof.cursor)),
            (404, "not_found", false, [deletion], .init(serverID: proof.serverID, epoch: proof.epoch, cursor: proof.cursor + 1)),
            (404, "not_found", false, [deletion], .init(serverID: proof.serverID, epoch: proof.epoch, cursor: 0)),
            (404, "not_found", false, [deletion], .init(serverID: proof.serverID, epoch: proof.epoch, cursor: Int64.max)),
        ]
        for (status, code, blocked, deletions, evidence) in cases {
            var journal = initial
            XCTAssertFalse(try journal.repairRejectedDeletedAudioLayout(id: id, deletions: deletions,
                status: status, code: code, proof: evidence, serverBlocked: blocked))
            XCTAssertEqual(journal, initial)
        }
        var accepted = initial
        accepted.metadata[accepted.metadata.firstIndex { $0.id == id }!].phase = .accepted
        let before = accepted
        XCTAssertFalse(try accepted.repairRejectedDeletedAudioLayout(id: id, deletions: [deletion],
            status: 404, code: "not_found", proof: proof, serverBlocked: false))
        XCTAssertEqual(accepted, before)
    }

    func testLateOptionalLayoutBackfillIsSuppressedByTheSameSessionTombstone() throws {
        let (_, momentID, session, _, initial) = try fixture()
        var journal = initial
        let drafts = journal.metadata.filter { $0.kind == "create_audio_layout" }
        journal.suppressDeletedContent(momentIDs: [], assetIDs: [], audioSessionIDs: [session])
        XCTAssertFalse(journal.metadata.contains { $0.kind == "create_asset" || $0.kind == "create_audio_layout" })
        XCTAssertTrue(journal.media.isEmpty)
        try journal.mergeAudioLayouts(drafts, serverFeatures: ["audio_layout_v1"])
        journal.suppressDeletedContent(momentIDs: [], assetIDs: [], audioSessionIDs: [session])
        XCTAssertFalse(journal.metadata.contains { $0.kind == "create_audio_layout" })
        XCTAssertTrue(journal.metadata.contains { $0.kind == "create_moment" && $0.objectID == momentID })
    }

    func testLegacyDeletedAudioRepairThenPhotoAndPrivacyEmitsActualSwiftWireFixture() throws {
        let (initial, local, deletion, id, proof) = try rejected()
        var journal = initial
        let original = try journal.exactEnvelope(for: id)
        XCTAssertTrue(try journal.repairRejectedDeletedAudioLayout(id: id, deletions: [deletion],
            status: 404, code: "not_found", proof: proof, serverBlocked: false))
        let repairedIndex = try XCTUnwrap(journal.metadata.firstIndex { $0.id == id })
        journal.metadata[repairedIndex].phase = .accepted
        journal.serverCursor = try XCTUnwrap(journal.metadata[repairedIndex].sequence)
        let photo = try local.beginMediaIntent(kind: .photo, targetMomentID: deletion.momentID)
        _ = try local.acceptMedia(photo, inspection: LocalMediaInspection(byteCount: 12,
            sha256: String(repeating: "a", count: 64), width: 4, height: 3, orientation: 1,
            durationMilliseconds: nil, hasAudio: false, partial: false))
        _ = try local.setHidden(momentID: deletion.momentID, hidden: true)
        let trip = try XCTUnwrap(local.trips().first)
        let media = CaminoSyncMediaItem(id: photo.assetID, momentID: deletion.momentID, kind: .photo,
            sourceRelativePath: "synthetic/live.jpg", byteCount: 12, sha256: String(repeating: "a", count: 64),
            durationMilliseconds: nil, batchID: journal.openBatchID)
        journal.mergeDiscovery(try CaminoSyncDiscovery(trips: [trip], days: local.days(tripID: trip.id),
            moments: [local.syncSnapshot(momentID: deletion.momentID)], media: [media]))
        for index in journal.metadata.indices where journal.metadata[index].phase != .accepted {
            _ = try journal.exactEnvelope(for: journal.metadata[index].id)
            journal.metadata[index].phase = .accepted
            journal.serverCursor = try XCTUnwrap(journal.metadata[index].sequence)
        }
        XCTAssertTrue(journal.valid)
        XCTAssertEqual(journal.media.map(\.id), [photo.assetID])
        if let path = ProcessInfo.processInfo.environment["CAMINO_DELETED_AUDIO_WIRE_FIXTURE"] {
            let packets = try journal.metadata.map {
                try JSONSerialization.jsonObject(with: XCTUnwrap($0.exactEnvelope))
            }
            try JSONSerialization.data(withJSONObject: ["server_id": proof.serverID.uuidString.lowercased(),
                "epoch": proof.epoch.uuidString.lowercased(), "rejected": JSONSerialization.jsonObject(with: original),
                "repaired": packets], options: [.sortedKeys]).write(to: URL(fileURLWithPath: path), options: .atomic)
        }
    }
}
