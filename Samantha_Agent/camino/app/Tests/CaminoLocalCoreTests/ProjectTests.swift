import CryptoKit
import Foundation
import XCTest
@testable import CaminoLocalCore

@MainActor final class ProjectTests: XCTestCase {
    func testProjectFormCreateAndEditAreAtomicAndKeepIdentityAcrossReopen() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-project-form-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let original = try store.createTrip(name: "Original", isTest: true)
        let invalid = LocalProjectDetails(startDate: "2027-07-14", endDate: "2027-07-01")
        XCTAssertThrowsError(try store.createTrip(name: "Incomplete", details: invalid))
        XCTAssertEqual(try store.trips(), [original])
        XCTAssertEqual(try store.activeTrip(), original)
        XCTAssertThrowsError(try store.updateTrip(original.id, name: "Must not persist", isTest: false, details: invalid))
        XCTAssertEqual(try store.trips(), [original])
        let dates = LocalProjectDetails(startDate: "2027-07-01", endDate: "2027-07-14")
        let next = try store.createTrip(name: "Holiday", details: dates)
        XCTAssertEqual(next.projectDetails, dates)
        XCTAssertEqual(next.detailsChanges.count, 1)
        XCTAssertNil(next.startDate, "original create_trip must not be rewritten")
        let archived = LocalProjectDetails(startDate: dates.startDate, endDate: dates.endDate, status: .archived)
        let updated = try store.updateTrip(original.id, name: "Renamed", isTest: false, details: archived)
        XCTAssertEqual(updated.id, original.id)
        XCTAssertEqual(updated.originalName, original.name)
        XCTAssertEqual(updated.projectDetails, archived)
        XCTAssertFalse(updated.isTest)
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.trips(), try store.trips())
        XCTAssertEqual(try reopened.activeTrip()?.id, next.id)
    }

    func testProjectDetailsReopenArchiveAndPendingIntentKeepOriginals() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-project-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let trip = try store.createTrip(name: "Original")
        let moment = try store.markMoment()
        let pending = try store.beginMediaIntent(kind: .photo, targetMomentID: moment.id)
        let operationID = UUID()
        let archived = LocalProjectDetails(startDate: "2027-07-01", endDate: "2027-07-14", status: .archived)
        let result = try store.setProjectDetails(trip.id, details: archived, operationID: operationID)
        XCTAssertEqual(result.originalName, trip.originalName)
        XCTAssertEqual(result.startDate, trip.startDate, "immutable create payload must survive")
        XCTAssertEqual(try store.activeTrip()?.id, trip.id, "archival does not change local selection")
        XCTAssertThrowsError(try store.markMoment()) { XCTAssertEqual($0 as? LocalStoreError, .archivedTrip) }
        XCTAssertThrowsError(try store.beginAudioIntent(sessionID: UUID(), kind: .comment, startedAt: Date()))
        XCTAssertThrowsError(try store.beginMediaIntent(kind: .video))
        _ = try store.acceptMedia(pending, inspection: LocalMediaInspection(byteCount: 12,
            sha256: String(repeating: "a", count: 64), width: 4, height: 3, orientation: 1,
            durationMilliseconds: nil, hasAudio: false, partial: false))
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.trips().first, result)
        XCTAssertEqual(try reopened.moments(tripID: trip.id), [moment])
        XCTAssertEqual(try reopened.allMediaAssets().first?.momentID, moment.id)
        XCTAssertEqual(try reopened.setProjectDetails(trip.id, details: archived, operationID: operationID), result)
        XCTAssertThrowsError(try reopened.setProjectDetails(trip.id, details: LocalProjectDetails(), operationID: operationID))
        _ = try reopened.setProjectDetails(trip.id, details: LocalProjectDetails())
        XCTAssertNoThrow(try reopened.markMoment())
        for details in [LocalProjectDetails(startDate: "2027-02-29"),
                        LocalProjectDetails(startDate: "2027-7-01"),
                        LocalProjectDetails(startDate: "2027-07-14", endDate: "2027-07-01")] {
            XCTAssertThrowsError(try reopened.setProjectDetails(trip.id, details: details))
        }
        XCTAssertTrue(LocalProjectDetails(startDate: "2028-02-29", endDate: "2028-02-29").valid)
    }

    func testTwoProjectsKeepFrozenTransfersAndEmitActualWireFixture() throws {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("camino-project-wire-\(UUID())/metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let date = ISO8601DateFormatter().date(from: "2027-07-01T10:00:00Z")!
        let zone = TimeZone(secondsFromGMT: 0)!
        var journal = CaminoSyncJournal()
        let serverID = UUID(), epoch = UUID()
        journal.observeServer(serverID: serverID, epoch: epoch, cursor: 0)
        let a = try store.createTrip(name: "Synthetic holiday")
        let ma = try store.markMoment(at: date, timeZone: zone)
        func photo(_ moment: UUID, content: String) throws -> CaminoSyncMediaItem {
            let intent = try store.beginMediaIntent(kind: .photo, targetMomentID: moment, at: date, timeZone: zone)
            let bytes = Data(content.utf8)
            let hash = SHA256.hash(data: bytes).map { String(format: "%02x", $0) }.joined()
            let asset = try store.acceptMedia(intent, inspection: LocalMediaInspection(byteCount: Int64(bytes.count),
                sha256: hash, width: 4, height: 3, orientation: 1, durationMilliseconds: nil,
                hasAudio: false, partial: false))
            return CaminoSyncMediaItem(id: asset.id, momentID: moment, kind: .photo,
                sourceRelativePath: asset.relativePath, byteCount: Int64(bytes.count), sha256: hash,
                durationMilliseconds: nil, batchID: journal.openBatchID)
        }
        let aa = try photo(ma.id, content: "synthetic-A")
        let first = try CaminoSyncDiscovery(trips: store.trips(), days: store.days(tripID: a.id),
            moments: [store.syncSnapshot(momentID: ma.id)], media: [aa])
        journal.mergeDiscovery(first)
        let initial = try journal.metadata.map { try journal.exactEnvelope(for: $0.id) }
        journal.media[0].phase = .uploading
        let frozen = journal.metadata, uploading = journal.media[0]
        let b = try store.createTrip(name: "Synthetic holiday")
        let mb = try store.markMoment(at: date, timeZone: zone)
        let ab = try photo(mb.id, content: "synthetic-B")
        _ = try store.setProjectDetails(a.id, details: LocalProjectDetails(
            startDate: "2027-07-01", endDate: "2027-07-14", status: .archived))
        _ = try store.setProjectDetails(b.id, details: LocalProjectDetails(startDate: "2027-07-01", endDate: "2027-07-14"))
        _ = try store.updateTrip(a.id, name: "First holiday", isTest: false)
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.activeTrip()?.id, b.id)
        let days = try reopened.days(tripID: a.id) + reopened.days(tripID: b.id)
        XCTAssertEqual(Set(days.map(\.localDate)).count, 1)
        XCTAssertEqual(Set(days.map(\.id)).count, 2)
        let snapshots = try [reopened.syncSnapshot(momentID: ma.id), reopened.syncSnapshot(momentID: mb.id)]
        let next = try CaminoSyncDiscovery(trips: reopened.trips(), days: days, moments: snapshots, media: [aa, ab])
        journal.mergeDiscovery(next)
        XCTAssertEqual(Array(journal.metadata.prefix(frozen.count)), frozen)
        XCTAssertEqual(journal.media[0], uploading)
        XCTAssertThrowsError(try journal.requireTitleSupport(serverFeatures: ["trip_title_v1"]))
        XCTAssertNoThrow(try journal.requireTitleSupport(serverFeatures: ["trip_title_v1", "project_details_v1"]))
        let continued = try journal.metadata.dropFirst(frozen.count).map { try journal.exactEnvelope(for: $0.id) }
        var restored = try JSONDecoder().decode(CaminoSyncJournal.self, from: JSONEncoder().encode(journal))
        XCTAssertTrue(restored.valid)
        for (item, raw) in zip(restored.metadata, initial + continued) {
            XCTAssertEqual(try restored.exactEnvelope(for: item.id), raw)
        }
        XCTAssertThrowsError(try CaminoSyncDiscovery(trips: reopened.trips(), days: days + [days[0]], moments: snapshots, media: [aa, ab]))
        XCTAssertThrowsError(try CaminoSyncDiscovery(trips: [b], days: days, moments: snapshots, media: [aa, ab]))
        XCTAssertThrowsError(try CaminoSyncDiscovery(trips: reopened.trips(), days: days, moments: [snapshots[1]], media: [aa, ab]))
        if let path = ProcessInfo.processInfo.environment["CAMINO_PROJECT_WIRE_FIXTURE"] {
            let object: [String: Any] = ["server_id": serverID.uuidString.lowercased(), "epoch": epoch.uuidString.lowercased(),
                "a_id": a.id.uuidString.lowercased(), "b_id": b.id.uuidString.lowercased(),
                "a_moment": ma.id.uuidString.lowercased(), "b_moment": mb.id.uuidString.lowercased(),
                "a_asset": aa.id.uuidString.lowercased(), "b_asset": ab.id.uuidString.lowercased(),
                "initial": try initial.map { try JSONSerialization.jsonObject(with: $0) },
                "continued": try continued.map { try JSONSerialization.jsonObject(with: $0) }]
            try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys, .withoutEscapingSlashes])
                .write(to: URL(fileURLWithPath: path), options: .atomic)
        }
    }
}
