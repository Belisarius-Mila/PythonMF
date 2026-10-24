import Foundation
import XCTest
@testable import CaminoLocalCore

@MainActor final class ProjectTrashTests: XCTestCase {
    private func root() throws -> URL {
        let url = FileManager.default.temporaryDirectory.resolvingSymlinksInPath()
            .appendingPathComponent("camino-trash-test-\(UUID())")
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        addTeardownBlock { try? FileManager.default.removeItem(at: url) }
        return url
    }

    func testRequestHidesOnlyOneProjectAndRestoreKeepsItsOriginalHistory() throws {
        let url = try root().appendingPathComponent("metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let a = try store.createTrip(name: "Same name")
        let m = try store.markMoment()
        try store.saveTextDraft(momentID: m.id, content: "Synthetic draft")
        _ = try store.updateTrip(a.id, name: "Current title", isTest: true)
        let b = try store.createTrip(name: "Same name")
        var request = try store.requestProjectTrash(a.id)
        XCTAssertEqual(request.name, "Current title")
        XCTAssertEqual(try store.trips().map(\.id), [b.id])
        XCTAssertEqual(try store.trips(includingTrash: true).count, 2)
        XCTAssertEqual(try store.activeTrip()?.id, b.id)
        XCTAssertThrowsError(try store.selectTrip(a.id))
        XCTAssertThrowsError(try store.saveTextDraft(momentID: m.id, content: "late"))
        XCTAssertThrowsError(try store.eraseProjectMetadata(a.id, receiptID: request.id))
        request.state = "trashed"; request.purgeMilliseconds = 0
        try store.saveProjectTrash(request)
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.moments(tripID: a.id).map(\.id), [m.id], "local clock cannot purge a project")
        request.state = "restored"; try reopened.saveProjectTrash(request)
        XCTAssertNoThrow(try reopened.selectTrip(a.id))
        XCTAssertEqual(try reopened.textHistory(momentID: m.id).draft?.content, "Synthetic draft")
    }

    func testConfirmedPurgeRemovesPendingFilesTextAndSqlitePagesButPreservesOtherProject() throws {
        let directory = try root(), url = directory.appendingPathComponent("metadata.sqlite")
        let store = try CaminoLocalStore(storeURL: url)
        let a = try store.createTrip(name: "ERASED-PROJECT-NAME")
        let m = try store.markMoment()
        try store.saveTextDraft(momentID: m.id, content: String(repeating: "ERASED-PRIVATE-TEXT-", count: 20_000))
        let media = try store.beginMediaIntent(kind: .photo, targetMomentID: m.id)
        let pending = directory.appendingPathComponent(media.pendingRelativePath)
        try FileManager.default.createDirectory(at: pending.deletingLastPathComponent(), withIntermediateDirectories: true)
        try Data(repeating: 77, count: 1_000_000).write(to: pending)
        let b = try store.createTrip(name: "Survivor")
        let mb = try store.markMoment()
        try store.saveTextDraft(momentID: mb.id, content: "Keep this text")
        var receipt = try store.requestProjectTrash(a.id)
        receipt.state = "restored"; try store.saveProjectTrash(receipt)
        receipt = try store.requestProjectTrash(a.id)
        receipt.state = "purged" // Synthetic authenticated-Mac result.
        let owned = try store.projectErasurePaths(a.id)
        XCTAssertTrue(owned.paths.contains(media.pendingRelativePath))
        receipt.files = try CaminoErasureEntry.inventory(root: directory, paths: owned.paths)
        try store.saveProjectTrash(receipt)
        func databaseBytes() throws -> Int {
            try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
                .filter { $0.lastPathComponent.hasPrefix("metadata.sqlite") }
                .reduce(0) { try $0 + Data(contentsOf: $1).count }
        }
        let before = try databaseBytes()
        try CaminoErasureEntry.remove(root: directory, entries: receipt.files!)
        // Replay after a simulated crash: missing planned files are already done.
        try CaminoErasureEntry.remove(root: directory, entries: receipt.files!)
        try store.eraseProjectMetadata(a.id, receiptID: receipt.id)
        try store.compactAfterProjectErasure()
        XCTAssertFalse(FileManager.default.fileExists(atPath: pending.path))
        XCTAssertEqual(try store.trips(includingTrash: true).map(\.id), [b.id])
        XCTAssertEqual(try store.textHistory(momentID: mb.id).draft?.content, "Keep this text")
        let bytes = try Data(contentsOf: url)
        XCTAssertNil(bytes.range(of: Data("ERASED-PRIVATE-TEXT-".utf8)))
        XCTAssertNil(bytes.range(of: Data("ERASED-PROJECT-NAME".utf8)))
        for file in try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
            where file.lastPathComponent.hasPrefix("metadata.sqlite") {
            let stored = try Data(contentsOf: file)
            XCTAssertNil(stored.range(of: Data("ERASED-PRIVATE-TEXT-".utf8)), file.lastPathComponent)
            XCTAssertNil(stored.range(of: Data("ERASED-PROJECT-NAME".utf8)), file.lastPathComponent)
        }
        XCTAssertLessThan(try databaseBytes(), before, "VACUUM must reclaim persistent store space")
        XCTAssertTrue(try store.projectTrash().allSatisfy { $0.name.isEmpty && $0.files == nil && $0.momentIDs.isEmpty })
        let reopened = try CaminoLocalStore(storeURL: url)
        XCTAssertEqual(try reopened.projectTrash().first { $0.id == receipt.id }?.state, "phone_deleted")
    }

    func testHeldMetadataIsNeverResequencedAndErasedHistoryDoesNotReuseCursor() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let a = try store.createTrip(name: "A"), ma = try store.markMoment()
        let b = try store.createTrip(name: "B"), mb = try store.markMoment()
        var journal = CaminoSyncJournal()
        _ = journal.observeServer(serverID: UUID(), epoch: UUID(), cursor: 0)
        let discovery = try CaminoSyncDiscovery(trips: store.trips(),
            days: store.days(tripID: a.id) + store.days(tripID: b.id),
            moments: [store.syncSnapshot(momentID: ma.id), store.syncSnapshot(momentID: mb.id)], media: [])
        journal.mergeDiscovery(discovery)
        let held = Set(journal.metadata.filter { $0.belongsToProject(a.id, momentIDs: [ma.id]) }.map(\.id))
        let first = journal.metadata.first { held.contains($0.id) }!
        let raw = try journal.exactEnvelope(for: first.id)
        XCTAssertThrowsError(try journal.eraseProject(a.id, momentIDs: [ma.id]))
        let index = journal.metadata.firstIndex { $0.id == first.id }!
        journal.metadata[index].phase = .accepted; journal.serverCursor = 1
        XCTAssertEqual(try journal.exactEnvelope(for: first.id), raw)
        guard case .metadata(let nextID) = journal.nextWork(networkAvailable: true, expensive: false,
            excludedMetadataIDs: held, excludedMomentIDs: [ma.id]) else { return XCTFail("B must continue") }
        XCTAssertTrue(journal.metadata.first { $0.id == nextID }!.belongsToProject(b.id, momentIDs: [mb.id]))
        try journal.eraseProject(a.id, momentIDs: [ma.id])
        _ = try journal.exactEnvelope(for: nextID)
        XCTAssertEqual(journal.metadata.first { $0.id == nextID }?.sequence, 2)
        XCTAssertFalse(journal.metadata.contains { $0.belongsToProject(a.id, momentIDs: [ma.id]) })
        XCTAssertTrue(journal.valid)
    }

    func testAlreadyDeletedMomentsRemainInWholeProjectErasureOwnership() throws {
        let store = try CaminoLocalStore(inMemory: true)
        let trip = try store.createTrip(name: "Synthetic"), moment = try store.markMoment()
        _ = try store.deleteMoment(momentID: moment.id)
        XCTAssertTrue(try store.moments(tripID: trip.id, includeHidden: true).isEmpty)
        let request = try store.requestProjectTrash(trip.id)
        XCTAssertEqual(request.momentIDs, [moment.id], "accepted private packets of hidden tombstones must also be erased")
    }

    func testErasurePlanRejectsEscapeSymlinkAndExternalHardlink() throws {
        let directory = try root(), selected = directory.appendingPathComponent("selected")
        try FileManager.default.createDirectory(at: selected, withIntermediateDirectories: true)
        let a = selected.appendingPathComponent("a"), outside = directory.appendingPathComponent("outside")
        try Data("synthetic".utf8).write(to: a)
        XCTAssertThrowsError(try CaminoErasureEntry.inventory(root: directory, paths: ["../outside"]))
        try FileManager.default.linkItem(at: a, to: outside)
        XCTAssertThrowsError(try CaminoErasureEntry.inventory(root: directory, paths: ["selected"]))
        try FileManager.default.removeItem(at: outside)
        let internalLink = selected.appendingPathComponent("internal")
        try FileManager.default.linkItem(at: a, to: internalLink)
        let planned = try CaminoErasureEntry.inventory(root: directory, paths: ["selected"])
        try FileManager.default.removeItem(at: a) // Simulated interruption after one unlink.
        try CaminoErasureEntry.remove(root: directory, entries: planned)
        try FileManager.default.createDirectory(at: selected, withIntermediateDirectories: true)
        try FileManager.default.createSymbolicLink(at: selected.appendingPathComponent("link"), withDestinationURL: outside)
        XCTAssertThrowsError(try CaminoErasureEntry.inventory(root: directory, paths: ["selected"]))
        try FileManager.default.removeItem(at: selected.appendingPathComponent("link"))
        try Data("system-root-alias".utf8).write(to: a)
        let alias = directory.appendingPathComponent("root-alias")
        try FileManager.default.createSymbolicLink(at: alias, withDestinationURL: directory)
        let viaAlias = try CaminoErasureEntry.inventory(root: alias, paths: ["selected"])
        try CaminoErasureEntry.remove(root: alias, entries: viaAlias)
        XCTAssertFalse(FileManager.default.fileExists(atPath: a.path), "system aliases of the container root are permitted")
    }
}
