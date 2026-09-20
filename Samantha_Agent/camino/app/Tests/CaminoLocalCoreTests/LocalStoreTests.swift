import Foundation
import XCTest
@testable import CaminoLocalCore

@MainActor final class LocalStoreTests: XCTestCase {
    private let prague = TimeZone(identifier: "Europe/Prague")!

    private func instant(_ value: String) -> Date {
        let formatter = ISO8601DateFormatter()
        return formatter.date(from: value)!
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
