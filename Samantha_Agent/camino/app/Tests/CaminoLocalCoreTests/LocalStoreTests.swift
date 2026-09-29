import Foundation
import XCTest
@testable import CaminoLocalCore

@MainActor final class LocalStoreTests: XCTestCase {
    private let prague = TimeZone(identifier: "Europe/Prague")!

    private func instant(_ value: String) -> Date {
        let formatter = ISO8601DateFormatter()
        return formatter.date(from: value)!
    }

    func testTitleReopenRetryClearAndLegacyJournal() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-title-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let trip = try store.createTrip(name: "Synthetic")
        let moment = try store.markMoment()
        XCTAssertEqual(moment.title, "")
        let operation = UUID()
        let changed = try store.setTitle(momentID: moment.id, title: " Káva u řeky 🥾 ", operationID: operation)
        XCTAssertEqual(changed.title, "Káva u řeky 🥾")
        XCTAssertEqual(changed.revision, 2)
        XCTAssertEqual(changed.capture, moment.capture)
        XCTAssertEqual(changed.privacy, moment.privacy)
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.moments(tripID: trip.id).first?.title, changed.title)
        XCTAssertEqual(try reopened.setTitle(momentID: moment.id, title: changed.title,
            operationID: operation).revision, 2)
        XCTAssertThrowsError(try reopened.setTitle(momentID: moment.id, title: "Other", operationID: operation))
        XCTAssertThrowsError(try reopened.setTitle(momentID: moment.id, title: "Other", expectedRevision: 1))
        XCTAssertThrowsError(try reopened.setTitle(momentID: moment.id, title: "x\ny"))
        XCTAssertThrowsError(try reopened.setTitle(momentID: moment.id, title: String(repeating: "x", count: 161)))
        XCTAssertEqual(try reopened.setTitle(momentID: moment.id, title: "").revision, 3)
        XCTAssertEqual(try reopened.setTitle(momentID: moment.id, title: "").revision, 3)
        let oldOperation = LocalPendingOperation(id: UUID(), momentID: moment.id,
            deviceSequence: 7, expectedRevision: 3, kind: .hidden,
            createdAtUTCMilliseconds: 1, hidden: true)
        let encoded = try JSONEncoder().encode(oldOperation)
        XCTAssertFalse(String(decoding: encoded, as: UTF8.self).contains("title"))
        XCTAssertNil(try JSONDecoder().decode(LocalPendingOperation.self, from: encoded).title)
    }

    func testBackgroundTitleWriteKeepsTargetedMomentAndRetryIdempotent() async throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        let first = try store.markMoment(at: instant("2026-09-27T07:00:00Z"))
        let second = try store.markMoment(at: instant("2026-09-27T08:00:00Z"))
        let operation = UUID()

        let changed = try await store.setTitleInBackground(
            momentID: first.id, title: "Název z backgroundu", operationID: operation)
        XCTAssertEqual(changed.title, "Název z backgroundu")
        XCTAssertEqual(changed.revision, first.revision + 1)
        XCTAssertEqual(try store.moments(tripID: trip.id).first(where: { $0.id == first.id })?.title,
                       changed.title)
        XCTAssertEqual(try store.moments(tripID: trip.id).first(where: { $0.id == second.id })?.revision,
                       second.revision)

        let retry = try await store.setTitleInBackground(
            momentID: first.id, title: changed.title, operationID: operation)
        XCTAssertEqual(retry, changed)
        XCTAssertEqual(try store.pendingOperations(momentID: first.id).count, 1)
    }

    func testBackgroundAttachmentTitleValidatesOnlyTargetAsset() async throws {
        let store = try CaminoLocalStore(inMemory: true)
        _ = try store.createTrip(name: "Synthetic")
        let moment = try store.markMoment(at: instant("2026-09-27T07:00:00Z"))
        let intent = try store.beginMediaIntent(kind: .photo, targetMomentID: moment.id)
        _ = try store.acceptMedia(intent, inspection: LocalMediaInspection(
            byteCount: 12, sha256: String(repeating: "a", count: 64), width: 4, height: 3,
            orientation: 1, durationMilliseconds: nil, hasAudio: false, partial: false))
        let changed = try await store.setTitleInBackground(
            momentID: moment.id,
            title: "Fotografie z backgroundu",
            attachment: LocalAttachmentTitle(kind: .asset, targetID: intent.assetID, title: ""))
        XCTAssertEqual(changed.attachmentTitle(.asset, id: intent.assetID), "Fotografie z backgroundu")
        XCTAssertEqual(try store.mediaAssets(momentID: moment.id).count, 1)
    }

    func testAttachmentTitlesAreIndependentDurableAndValidateOwnership() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-attachment-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let trip = try store.createTrip(name: "Synthetic")
        let moment = try store.markMoment(at: instant("2026-09-27T07:00:00Z"))
        _ = try store.setTitle(momentID: moment.id, title: "Celý okamžik")
        var ids: [UUID] = []
        for kind in [LocalMediaKind.photo, .video] {
            let intent = try store.beginMediaIntent(kind: kind, targetMomentID: moment.id)
            _ = try store.acceptMedia(intent, inspection: LocalMediaInspection(byteCount: 12,
                sha256: String(repeating: "a", count: 64), width: 4, height: 3, orientation: 1,
                durationMilliseconds: kind == .video ? 1000 : nil, hasAudio: kind == .video, partial: false))
            ids.append(intent.assetID)
            _ = try store.setAttachmentTitle(momentID: moment.id, kind: .asset,
                targetID: intent.assetID, title: "\(kind.title) 🥾")
        }
        let originalAssets = try store.allMediaAssets()
        let sessionID = UUID()
        _ = try store.beginAudioIntent(sessionID: sessionID, kind: .comment,
            startedAt: Date(), targetMomentID: moment.id)
        _ = try store.acceptCompletedAudio(sessionID: sessionID, kind: .comment, partial: true)
        let operationID = UUID()
        let named = try store.setAttachmentTitle(momentID: moment.id, kind: .audioSession,
            targetID: sessionID, title: " Celý komentář ", operationID: operationID)
        XCTAssertEqual(named.title, "Celý okamžik")
        XCTAssertEqual(named.attachmentTitles.count, 3)
        XCTAssertEqual(named.capture, moment.capture)
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.moments(tripID: trip.id).first?.attachmentTitles, named.attachmentTitles)
        XCTAssertEqual(try reopened.setAttachmentTitle(momentID: moment.id, kind: .audioSession,
            targetID: sessionID, title: "Celý komentář", operationID: operationID), named)
        XCTAssertThrowsError(try reopened.setAttachmentTitle(momentID: moment.id, kind: .audioSession,
            targetID: sessionID, title: "Other", operationID: operationID))
        XCTAssertThrowsError(try reopened.setAttachmentTitle(momentID: moment.id, kind: .asset,
            targetID: ids[0], title: "New", expectedRevision: 1))
        XCTAssertThrowsError(try reopened.setAttachmentTitle(momentID: moment.id, kind: .asset,
            targetID: ids[0], title: "line\nbreak"))
        let other = try reopened.markMoment(at: instant("2026-09-27T08:00:00Z"))
        for (kind, id) in [(LocalAttachmentTitle.Kind.asset, ids[0]), (.audioSession, sessionID)] {
        XCTAssertThrowsError(try reopened.setAttachmentTitle(momentID: other.id,
                kind: kind, targetID: id, title: "Wrong parent"))
        }
        let cleared = try reopened.setAttachmentTitle(momentID: moment.id, kind: .asset, targetID: ids[0], title: "")
        XCTAssertEqual(cleared.attachmentTitles.count, 2)
        XCTAssertEqual(cleared.attachmentTitle(.asset, id: ids[0]), "")
        XCTAssertEqual(try reopened.setAttachmentTitle(momentID: moment.id, kind: .asset,
            targetID: ids[0], title: "").revision, cleared.revision)
        XCTAssertEqual(try reopened.allMediaAssets(), originalAssets)
        let newest = try reopened.moments(tripID: trip.id).sorted(by: LocalMoment.newestFirst)
        XCTAssertEqual(newest.map(\.id), [other.id, moment.id])
        _ = try reopened.setTitle(momentID: moment.id, title: "Pozdější úprava")
        XCTAssertEqual(try reopened.moments(tripID: trip.id).sorted(by: LocalMoment.newestFirst).map(\.id), newest.map(\.id))
    }

    func testAttachmentDeletionKeepsParentAndSurvivesRestart() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-delete-asset-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let trip = try store.createTrip(name: "Synthetic")
        let moment = try store.markMoment()
        let intent = try store.beginMediaIntent(kind: .photo, targetMomentID: moment.id)
        _ = try store.acceptMedia(intent, inspection: LocalMediaInspection(
            byteCount: 12, sha256: String(repeating: "a", count: 64), width: 4, height: 3,
            orientation: 1, durationMilliseconds: nil, hasAudio: false, partial: false))

        let deletion = try store.deleteAsset(assetID: intent.assetID)
        XCTAssertEqual(deletion.kind, .asset)
        XCTAssertEqual(try store.moments(tripID: trip.id).map(\.id), [moment.id])
        XCTAssertTrue(try store.mediaAssets(momentID: moment.id).isEmpty)
        XCTAssertEqual(try store.deletionRecords(momentID: moment.id).count, 1)
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.moments(tripID: trip.id).map(\.id), [moment.id])
        XCTAssertTrue(try reopened.mediaAssets(momentID: moment.id).isEmpty)
        XCTAssertThrowsError(try reopened.deleteAsset(assetID: intent.assetID))
    }

    func testWholeMomentDeletionHidesTextMediaAndAudioAndIsIdempotentlyBlocked() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        let moment = try store.markMoment()
        _ = try store.appendTextRevision(momentID: moment.id, role: .typedSource,
            content: "synthetic", at: Date())
        let photo = try store.beginMediaIntent(kind: .photo, targetMomentID: moment.id)
        _ = try store.acceptMedia(photo, inspection: LocalMediaInspection(
            byteCount: 12, sha256: String(repeating: "b", count: 64), width: 4, height: 3,
            orientation: 1, durationMilliseconds: nil, hasAudio: false, partial: false))
        let session = UUID()
        _ = try store.beginAudioIntent(sessionID: session, kind: .comment,
            startedAt: Date(), targetMomentID: moment.id)
        _ = try store.acceptCompletedAudio(sessionID: session, kind: .comment, partial: false)

        let records = try store.deleteMoment(momentID: moment.id)
        XCTAssertEqual(records.map(\.kind), [.moment, .asset, .audioSession])
        XCTAssertTrue(try store.moments(tripID: trip.id).isEmpty)
        XCTAssertTrue(try store.allMediaAssets().isEmpty)
        XCTAssertTrue(try store.audioSessionIDs(momentID: moment.id).isEmpty)
        XCTAssertThrowsError(try store.textHistory(momentID: moment.id))
        XCTAssertThrowsError(try store.deleteMoment(momentID: moment.id))
    }

    func testDeleteActiveCaptureIsBlockedWithoutTombstone() throws {
        let store = try CaminoLocalStore(inMemory: true)
        _ = try store.createTrip(name: "Synthetic")
        let moment = try store.markMoment()
        let intent = try store.beginMediaIntent(kind: .photo, targetMomentID: moment.id)
        XCTAssertThrowsError(try store.deleteMoment(momentID: moment.id)) { error in
            XCTAssertEqual(error as? LocalStoreError, .activeCapture)
        }
        XCTAssertTrue(try store.deletionRecords().isEmpty)
        XCTAssertEqual(try store.pendingMediaIntents(), [intent])
    }

    func testOfflineTripsStaySeparateAndOnlyOneIsActive() throws {
        let store = try CaminoLocalStore(inMemory: true)
        XCTAssertNil(try store.activeTrip())
        XCTAssertThrowsError(try store.markMoment())
        let testTrip = try store.createTrip(name: "Zkouška", isTest: true)
        let testMarker = try store.markMoment(at: instant("2026-09-20T08:00:00Z"), timeZone: prague)
        let realTrip = try store.createTrip(name: "  Cesta  ")
        let realMarker = try store.markMoment(at: instant("2026-09-20T09:00:00Z"), timeZone: prague)
        XCTAssertNotEqual(testTrip.id, realTrip.id)
        XCTAssertNotEqual(testMarker.id, realMarker.id)
        XCTAssertEqual(try store.activeTrip()?.id, realTrip.id)
        XCTAssertEqual(try store.moments(tripID: testTrip.id).map(\.id), [testMarker.id])
        XCTAssertEqual(try store.moments(tripID: realTrip.id).map(\.id), [realMarker.id])
        try store.selectTrip(testTrip.id)
        XCTAssertEqual(try store.activeTrip()?.id, testTrip.id)
        XCTAssertEqual(try store.trips().filter(\.active).count, 1)
        XCTAssertEqual(try store.trips().first(where: { $0.id == testTrip.id })?.isTest, true)
    }

    func testPrivacyChoiceSurvivesRestartWithoutChangingOldMoments() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04a-synthetic-\(UUID())", isDirectory: true)
            .appendingPathComponent("metadata.sqlite")
        let first = try CaminoLocalStore(storeURL: url)
        let trip = try first.createTrip(name: "Synthetic")
        let diary = try first.markMoment(at: instant("2026-09-20T08:00:00Z"), timeZone: prague)
        XCTAssertEqual(diary.privacy, .diary)
        try first.setNewMomentPrivacy(.ownerOnly)
        let locked = try first.markMoment(at: instant("2026-09-20T08:01:00Z"), timeZone: prague)
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.activeTrip()?.id, trip.id)
        XCTAssertEqual(try reopened.newMomentPrivacy(), .ownerOnly)
        let moments = try reopened.moments(tripID: trip.id)
        XCTAssertEqual(moments.first(where: { $0.id == locked.id })?.privacy, .ownerOnly)
        XCTAssertEqual(moments.first(where: { $0.id == diary.id })?.privacy, .diary)
        try reopened.setNewMomentPrivacy(.diary)
        XCTAssertEqual(try reopened.moments(tripID: trip.id)
            .first(where: { $0.id == locked.id })?.privacy, .ownerOnly)
    }

    func testMarkerKeepsOriginalLocalDateAndOffset() throws {
        let store = try CaminoLocalStore(inMemory: true)
        _ = try store.createTrip(name: "Synthetic")
        let beforeMidnight = try store.markMoment(
            at: instant("2026-09-19T21:59:59Z"), timeZone: prague)
        let afterMidnight = try store.markMoment(
            at: instant("2026-09-19T22:00:01Z"), timeZone: prague)
        XCTAssertEqual(beforeMidnight.capture.chapterDate, "2026-09-19")
        XCTAssertEqual(afterMidnight.capture.chapterDate, "2026-09-20")
        XCTAssertEqual(afterMidnight.capture.offsetMinutes, 120)
        XCTAssertNotEqual(beforeMidnight.dayID, afterMidnight.dayID)
        XCTAssertNil(afterMidnight.audioSessionID)
    }

    func testReflectionIntentStaysPrivateAndCompletionIsIdempotent() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        try store.setNewMomentPrivacy(.diary)
        let sessionID = UUID()
        let started = instant("2026-09-20T09:00:00Z")
        let intent = try store.beginAudioIntent(sessionID: sessionID, kind: .reflection,
                                                startedAt: started, timeZone: prague)
        XCTAssertEqual(intent.privacy, .ownerOnly)
        XCTAssertEqual(try store.beginAudioIntent(sessionID: sessionID, kind: .reflection,
                                                  startedAt: started), intent)
        XCTAssertEqual(try store.pendingAudioIntents().count, 1)
        XCTAssertTrue(try store.moments(tripID: trip.id).isEmpty)
        let saved = try store.acceptCompletedAudio(sessionID: sessionID, kind: .reflection,
                                                   partial: true)
        XCTAssertEqual(saved.id, intent.momentID)
        XCTAssertEqual(saved.audioSessionID, sessionID)
        XCTAssertEqual(saved.privacy, .ownerOnly)
        XCTAssertTrue(saved.partialAudio)
        XCTAssertEqual(try store.acceptCompletedAudio(sessionID: sessionID,
                                                      kind: .reflection, partial: true), saved)
        XCTAssertTrue(try store.pendingAudioIntents().isEmpty)
        XCTAssertEqual(try store.moments(tripID: trip.id).count, 1)
    }

    func testUnfinishedAudioIntentIsPreservedWithoutGuessingIdentity() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04a-intent-\(UUID())", isDirectory: true)
            .appendingPathComponent("metadata.sqlite")
        let first = try CaminoLocalStore(storeURL: url)
        let trip = try first.createTrip(name: "Synthetic")
        let sessionID = UUID()
        let intent = try first.beginAudioIntent(sessionID: sessionID, kind: .comment,
                                                startedAt: instant("2026-09-20T09:00:00Z"))
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.pendingAudioIntents(), [intent])
        XCTAssertTrue(try reopened.moments(tripID: trip.id).isEmpty)
        XCTAssertThrowsError(try reopened.acceptCompletedAudio(sessionID: UUID(),
                                                                kind: .comment, partial: false))
        XCTAssertThrowsError(try reopened.acceptCompletedAudio(sessionID: sessionID,
                                                                kind: .reflection, partial: false))
        XCTAssertEqual(try reopened.pendingAudioIntents(), [intent])
        XCTAssertTrue(try reopened.moments(tripID: trip.id).isEmpty)
    }

    func testCommentPrivacyCanChangeForWholeCaptureWithoutChangingDefault() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        let sessionID = UUID()
        _ = try store.beginAudioIntent(sessionID: sessionID, kind: .comment, startedAt: Date())
        XCTAssertEqual(try store.pendingAudioIntents().first?.privacy, .diary)
        try store.setAudioIntentPrivacy(sessionID: sessionID, privacy: .ownerOnly)
        XCTAssertEqual(try store.pendingAudioIntents().first?.privacy, .ownerOnly)
        XCTAssertEqual(try store.newMomentPrivacy(), .diary)
        let moment = try store.acceptCompletedAudio(sessionID: sessionID,
                                                    kind: .comment, partial: false)
        XCTAssertEqual(moment.privacy, .ownerOnly)
        XCTAssertEqual(try store.moments(tripID: trip.id).first?.privacy, .ownerOnly)
        XCTAssertThrowsError(try store.setAudioIntentPrivacy(sessionID: sessionID,
                                                            privacy: .diary))
        let reflection = try store.beginAudioIntent(sessionID: UUID(),
                                                    kind: .reflection, startedAt: Date())
        XCTAssertThrowsError(try store.setAudioIntentPrivacy(sessionID: reflection.sessionID,
                                                            privacy: .diary))
    }

    func testCommentsAttachToExactPhotoMomentAndInheritItsPrivacy() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        let photo = try store.beginMediaIntent(kind: .photo)
        let inspected = LocalMediaInspection(byteCount: 12,
            sha256: String(repeating: "a", count: 64), width: 4, height: 3,
            orientation: 1, durationMilliseconds: nil, hasAudio: false, partial: false)
        _ = try store.acceptMedia(photo, inspection: inspected)
        try store.setNewMomentPrivacy(.ownerOnly)
        let firstID = UUID()
        let first = try store.beginAudioIntent(sessionID: firstID, kind: .comment,
            startedAt: Date(), targetMomentID: photo.momentID)
        XCTAssertTrue(first.attaching)
        XCTAssertEqual(first.privacy, .diary)
        XCTAssertThrowsError(try store.setAudioIntentPrivacy(sessionID: firstID,
                                                             privacy: .ownerOnly))
        let attached = try store.acceptCompletedAudio(sessionID: firstID,
            kind: .comment, partial: false)
        XCTAssertEqual(attached.id, photo.momentID)
        XCTAssertEqual(attached.kind, .photo)
        XCTAssertEqual(try store.audioSessionIDs(momentID: photo.momentID), [firstID])
        let secondID = UUID()
        _ = try store.beginAudioIntent(sessionID: secondID, kind: .comment,
            startedAt: Date(), targetMomentID: photo.momentID)
        _ = try store.acceptCompletedAudio(sessionID: secondID,
            kind: .comment, partial: true)
        XCTAssertEqual(Set(try store.audioSessionIDs(momentID: photo.momentID)),
                       Set([firstID, secondID]))
        XCTAssertEqual(try store.moments(tripID: trip.id).count, 1)
    }

    func testDraftSurvivesRestartAndHumanRevisionWinsLateAutomation() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04d-text-\(UUID())", isDirectory: true)
            .appendingPathComponent("metadata.sqlite")
        let first = try CaminoLocalStore(storeURL: url)
        let trip = try first.createTrip(name: "Synthetic")
        let moment = try first.markMoment(at: instant("2026-09-20T08:00:00Z"),
                                          timeZone: prague)
        let raw = try first.appendTextRevision(
            momentID: moment.id, role: .transcriptRaw, content: "synthetic raw",
            revisionID: UUID(), operationID: UUID(),
            at: instant("2026-09-20T08:01:00Z"))
        try first.saveTextDraft(momentID: moment.id, content: "synthetic draft",
                                at: instant("2026-09-20T08:02:00Z"))

        let reopened = try CaminoLocalStore(storeURL: url)
        var history = try reopened.textHistory(momentID: moment.id)
        XCTAssertEqual(history.draft?.content, "synthetic draft")
        XCTAssertEqual(history.readerRevision, raw)
        let human = try reopened.commitTextDraft(
            momentID: moment.id, at: instant("2026-09-20T08:03:00Z"))
        XCTAssertEqual(human.role, .humanRevision)
        XCTAssertNil(try reopened.textHistory(momentID: moment.id).draft)
        _ = try reopened.appendTextRevision(
            momentID: moment.id, role: .transcriptClean, content: "synthetic late AI",
            sourceIDs: [raw.id], parentRevisionID: raw.id,
            at: instant("2026-09-20T08:04:00Z"))
        history = try reopened.textHistory(momentID: moment.id)
        XCTAssertEqual(history.revisions.count, 3)
        XCTAssertEqual(history.readerRevision, human)
        XCTAssertEqual(try reopened.moments(tripID: trip.id).first?.revision, 4)
    }

    func testReflectionReleaseRequiresConsciousActionAndCreatesOrderedOperations() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        let sessionID = UUID()
        _ = try store.beginAudioIntent(sessionID: sessionID, kind: .reflection,
                                       startedAt: instant("2026-09-20T08:00:00Z"))
        let reflection = try store.acceptCompletedAudio(
            sessionID: sessionID, kind: .reflection, partial: false)
        XCTAssertThrowsError(try store.changePrivacy(
            momentID: reflection.id, to: .diary, action: .unlock))
        let releaseID = UUID()
        let released = try store.changePrivacy(
            momentID: reflection.id, to: .diary,
            action: .insertReflectionIntoDiary, operationID: releaseID)
        XCTAssertEqual(released.privacy, .diary)
        XCTAssertEqual(released.revision, 2)
        XCTAssertEqual(try store.changePrivacy(
            momentID: reflection.id, to: .diary,
            action: .insertReflectionIntoDiary, operationID: releaseID), released)
        let locked = try store.changePrivacy(
            momentID: reflection.id, to: .ownerOnly, action: .lock)
        XCTAssertEqual(locked.privacy, .ownerOnly)
        let operations = try store.pendingOperations(momentID: reflection.id)
        XCTAssertEqual(operations.map(\.deviceSequence), [1, 2])
        XCTAssertEqual(operations.map(\.expectedRevision), [1, 2])
        XCTAssertEqual(try store.moments(tripID: trip.id).first?.revision, 3)
    }

    func testHideRestoreKeepsPrivacyAndMediaOriginalMetadata() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        try store.setNewMomentPrivacy(.ownerOnly)
        let intent = try store.beginMediaIntent(kind: .photo)
        let inspection = LocalMediaInspection(
            byteCount: 12, sha256: String(repeating: "b", count: 64),
            width: 4, height: 3, orientation: 1, durationMilliseconds: nil,
            hasAudio: false, partial: false)
        let asset = try store.acceptMedia(intent, inspection: inspection)
        let hidden = try store.setHidden(momentID: intent.momentID, hidden: true)
        XCTAssertTrue(hidden.hidden)
        XCTAssertEqual(hidden.privacy, .ownerOnly)
        XCTAssertTrue(try store.moments(tripID: trip.id).isEmpty)
        XCTAssertEqual(try store.moments(tripID: trip.id, includeHidden: true).count, 1)
        XCTAssertEqual(try store.mediaAssets(momentID: intent.momentID), [asset])
        let restored = try store.setHidden(momentID: intent.momentID, hidden: false)
        XCTAssertFalse(restored.hidden)
        XCTAssertEqual(restored.privacy, .ownerOnly)
        XCTAssertEqual(try store.mediaAssets(momentID: intent.momentID).first?.inspection,
                       inspection)
    }

    func testPrivateAddendumIsSeparateLinkedOwnerOnlyMoment() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic")
        let photoIntent = try store.beginMediaIntent(kind: .photo)
        _ = try store.acceptMedia(photoIntent, inspection: LocalMediaInspection(
            byteCount: 12, sha256: String(repeating: "c", count: 64),
            width: 4, height: 3, orientation: 1, durationMilliseconds: nil,
            hasAudio: false, partial: false))
        let sessionID = UUID()
        let addendumIntent = try store.beginAudioIntent(
            sessionID: sessionID, kind: .reflection,
            startedAt: instant("2026-09-20T09:00:00Z"),
            relatedMomentID: photoIntent.momentID)
        let addendum = try store.acceptCompletedAudio(
            sessionID: sessionID, kind: .reflection, partial: false)
        XCTAssertNotEqual(addendum.id, photoIntent.momentID)
        XCTAssertEqual(addendum.id, addendumIntent.momentID)
        XCTAssertEqual(addendum.relatedMomentID, photoIntent.momentID)
        XCTAssertEqual(addendum.privacy, .ownerOnly)
        let photo = try XCTUnwrap(try store.moments(tripID: trip.id)
            .first(where: { $0.id == photoIntent.momentID }))
        XCTAssertEqual(photo.privacy, .diary)
        XCTAssertNil(photo.relatedMomentID)
    }

    func testChapterMovePreservesOriginalCaptureTimeAcrossRestart() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04d-chapter-\(UUID())", isDirectory: true)
            .appendingPathComponent("metadata.sqlite")
        let first = try CaminoLocalStore(storeURL: url)
        let trip = try first.createTrip(name: "Synthetic")
        let original = try first.markMoment(at: instant("2026-09-20T08:00:00Z"),
                                            timeZone: prague)
        let moved = try first.moveMoment(momentID: original.id,
                                         toChapterDate: "2026-09-21")
        XCTAssertEqual(moved.chapterDate, "2026-09-21")
        XCTAssertEqual(moved.capture, original.capture)
        XCTAssertNotEqual(moved.dayID, original.dayID)
        let reopened = try CaminoLocalStore(storeURL: url)
        let recovered = try XCTUnwrap(try reopened.moments(tripID: trip.id).first)
        XCTAssertEqual(recovered.chapterDate, "2026-09-21")
        XCTAssertEqual(recovered.capture.chapterDate, "2026-09-20")
        XCTAssertEqual(recovered.capture.utcMilliseconds, original.capture.utcMilliseconds)
    }

    func testInvalidTripAndDuplicateIdentityCannotReplaceExistingData() throws {
        let store = try CaminoLocalStore(inMemory: true)
        XCTAssertThrowsError(try store.createTrip(name: "   "))
        let id = UUID()
        let original = try store.createTrip(name: "Original", id: id)
        XCTAssertThrowsError(try store.createTrip(name: "Replacement", id: id))
        XCTAssertThrowsError(try store.selectTrip(UUID()))
        XCTAssertEqual(try store.activeTrip(), original)
        XCTAssertEqual(try store.trips().count, 1)
    }
}
