import Foundation
import XCTest
@testable import CaminoLocalCore

@MainActor final class LocationTests: XCTestCase {
    private let date = Date(timeIntervalSince1970: 1_790_496_000)
    private var milliseconds: Int64 { Int64(date.timeIntervalSince1970 * 1_000) }
    private func fix(age: Int64 = 0, accuracy: Double = 8,
                     latitude: Double = 12.25, longitude: Double = 34.5) -> LocalLocationFix {
        LocalLocationFix(latitude: latitude, longitude: longitude,
                         measuredAtUTCMilliseconds: milliseconds - age,
                         horizontalAccuracyMeters: accuracy)
    }

    func testFreshnessAccuracyAndInvalidValues() {
        XCTAssertTrue(fix().usable(at: milliseconds))
        XCTAssertTrue(fix(age: 120_000).usable(at: milliseconds))
        for value in [fix(age: 120_001), fix(age: -1), fix(accuracy: -1),
                      fix(latitude: .nan), fix(longitude: .infinity),
                      fix(latitude: 91), fix(longitude: -181), fix(accuracy: .nan)] {
            XCTAssertFalse(value.usable(at: milliseconds))
        }
        XCTAssertFalse(fix(accuracy: 100).approximate)
        XCTAssertTrue(fix(accuracy: 101).approximate)
    }

    func testOldAndDeniedMomentsStayWithoutGPSAfterReopenAndEdits() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-gps-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let trip = try store.createTrip(name: "Synthetic GPS")
        let old = try store.markMoment(at: date)
        let stale = try store.markMoment(at: date, location: fix(age: 120_001))
        let fresh = try store.markMoment(at: date, location: fix())
        _ = try store.changePrivacy(momentID: fresh.id, to: .ownerOnly, action: .lock)
        _ = try store.setHidden(momentID: fresh.id, hidden: true)
        _ = try store.moveMoment(momentID: fresh.id, toChapterDate: "2026-09-28")
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.activeTrip()?.id, trip.id)
        XCTAssertNil(try reopened.syncSnapshot(momentID: old.id).moment.location)
        XCTAssertNil(try reopened.syncSnapshot(momentID: stale.id).moment.location)
        XCTAssertEqual(try reopened.syncSnapshot(momentID: fresh.id).moment.location, fix())
    }

    func testAudioIntentKeepsStartGPSAcrossReopenAndRetry() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-gps-audio-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        _ = try store.createTrip(name: "Synthetic GPS")
        let session = UUID()
        let intent = try store.beginAudioIntent(sessionID: session, kind: .reflection,
                                               startedAt: date, location: fix())
        let reopened = try CaminoLocalStore(storeURL: url)
        _ = try reopened.beginAudioIntent(sessionID: session, kind: .reflection,
                                          startedAt: date.addingTimeInterval(900), location: fix(latitude: 22))
        let moment = try reopened.acceptCompletedAudio(sessionID: session, kind: .reflection, partial: true)
        XCTAssertEqual(moment.id, intent.momentID)
        XCTAssertEqual(moment.location, fix())
        XCTAssertEqual(moment.privacy, .ownerOnly)
        XCTAssertEqual(try reopened.acceptCompletedAudio(sessionID: session, kind: .reflection,
                                                         partial: true).location, fix())
    }

    func testPhotoVideoAndAttachmentsNeverReplaceTheOriginalPoint() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-gps-media-\(UUID())/metadata.sqlite")
        var store = try CaminoLocalStore(storeURL: url)
        let trip = try store.createTrip(name: "Synthetic GPS")
        for kind in [LocalMediaKind.photo, .video] {
            let intent = try store.beginMediaIntent(kind: kind, at: date, location: fix())
            store = try CaminoLocalStore(storeURL: url)
            XCTAssertTrue(try store.pendingMediaIntents().contains(intent))
            let inspection = LocalMediaInspection(byteCount: 10, sha256: String(repeating: "a", count: 64),
                width: 10, height: 10, orientation: 1, durationMilliseconds: kind == .video ? 1000 : nil,
                hasAudio: kind == .video, partial: false)
            _ = try store.acceptMedia(intent, inspection: inspection)
            let attachment = try store.beginMediaIntent(kind: kind, targetMomentID: intent.momentID,
                at: date.addingTimeInterval(1), location: fix(latitude: 22))
            _ = try store.acceptMedia(attachment, inspection: inspection)
            let session = UUID()
            _ = try store.beginAudioIntent(sessionID: session, kind: .comment, startedAt: date,
                                           targetMomentID: intent.momentID, location: fix(latitude: 22))
            _ = try store.acceptCompletedAudio(sessionID: session, kind: .comment, partial: false)
            XCTAssertEqual(try store.syncSnapshot(momentID: intent.momentID).moment.location, fix())
        }
        XCTAssertEqual(try store.moments(tripID: trip.id).count, 2)
    }

    func testGPSPayloadReplayAndLegacyNullAreStable() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic GPS")
        let legacy = try store.markMoment(at: date)
        let fresh = try store.markMoment(at: date, location: fix(accuracy: 150))
        let discovery = try CaminoSyncDiscovery(trips: [trip], days: store.days(tripID: trip.id),
            moments: [store.syncSnapshot(momentID: legacy.id), store.syncSnapshot(momentID: fresh.id)], media: [])
        let freshItem = try XCTUnwrap(discovery.metadata.first { $0.objectID == fresh.id })
        let payload = try JSONSerialization.jsonObject(with: freshItem.payload) as! [String: Any]
        let location = try XCTUnwrap(payload["location"] as? [String: Any])
        XCTAssertEqual(location["latitude"] as? Double, 12.25)
        XCTAssertEqual(location["longitude"] as? Double, 34.5)
        XCTAssertEqual(location["horizontal_accuracy_m"] as? Double, 150)
        XCTAssertEqual(location["measured_at_utc_ms"] as? Int64, milliseconds)
        let legacyItem = try XCTUnwrap(discovery.metadata.first { $0.objectID == legacy.id })
        let oldPayload = try JSONSerialization.jsonObject(with: legacyItem.payload) as! [String: Any]
        XCTAssertTrue(oldPayload["location"] is NSNull)
        var journal = CaminoSyncJournal()
        journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        journal.merge(metadata: discovery.metadata, media: [])
        var envelopes: [Any] = []
        for item in journal.metadata {
            let exact = try journal.exactEnvelope(for: item.id)
            envelopes.append(try JSONSerialization.jsonObject(with: exact))
            var reopened = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
            XCTAssertEqual(try reopened.exactEnvelope(for: item.id), exact)
        }
        // Optional synthetic Swift -> actual ASGI API contract test. Never private data.
        if let path = ProcessInfo.processInfo.environment["CAMINO_GPS_WIRE_FIXTURE"] {
            try JSONSerialization.data(withJSONObject: envelopes, options: [.sortedKeys])
                .write(to: URL(fileURLWithPath: path), options: .atomic)
        }
    }
}
