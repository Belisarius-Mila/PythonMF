import Foundation
import XCTest
@testable import CaminoLocalCore

@MainActor final class PendingMediaReviewTests: XCTestCase {
    private func fixture() throws -> (URL, CaminoLocalStore, CaminoMediaVault) {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("camino-review-\(UUID())")
        let store = try CaminoLocalStore(storeURL: root.appendingPathComponent("metadata.sqlite"))
        _ = try store.createTrip(name: "Synthetic review")
        return (root, store, try CaminoMediaVault(root: root, metadata: store))
    }

    func testTwoEmptyAttemptsDisappearAfterConfirmedBatchAndReopen() async throws {
        let (root, store, vault) = try fixture()
        let trip = try XCTUnwrap(store.activeTrip())
        let survivor = try store.markMoment()
        try store.saveTextDraft(momentID: survivor.id, content: "Keep this draft")
        let history = try store.pendingOperations(momentID: survivor.id)
        _ = try store.beginMediaIntent(kind: .video)
        _ = try store.beginMediaIntent(kind: .video)
        let recovery = try await vault.reconcile()
        XCTAssertEqual(recovery.pendingCount, 2, "Launch recovery must not silently discard")
        let review = try vault.pendingMediaReview()
        XCTAssertTrue(review.allSatisfy(\.isEmpty))
        try vault.discardPendingMedia(review)
        let reopened = try CaminoLocalStore(storeURL: root.appendingPathComponent("metadata.sqlite"))
        XCTAssertTrue(try reopened.pendingMediaIntents().isEmpty)
        XCTAssertEqual(try reopened.moments(tripID: trip.id).map(\.id), [survivor.id])
        XCTAssertEqual(try reopened.textHistory(momentID: survivor.id).draft?.content, "Keep this draft")
        XCTAssertEqual(try reopened.pendingOperations(momentID: survivor.id), history)
    }

    func testRefusedStartCancelsOnlyEmptyIntentAndPreservesAFile() throws {
        let (root, store, vault) = try fixture()
        let empty = try store.beginMediaIntent(kind: .video)
        XCTAssertTrue(try vault.cancelEmptyMediaIntent(empty))
        let retained = try store.beginMediaIntent(kind: .video)
        let file = root.appendingPathComponent(retained.pendingRelativePath)
        try Data([1, 2, 3]).write(to: file)
        XCTAssertFalse(try vault.cancelEmptyMediaIntent(retained))
        XCTAssertEqual(try store.pendingMediaIntents().map(\.assetID), [retained.assetID])
        XCTAssertEqual(try Data(contentsOf: file), Data([1, 2, 3]))
    }

    func testConfirmedBrokenFileRemovalPreservesUnknownAndAcceptedBytes() throws {
        let (root, store, vault) = try fixture()
        let acceptedIntent = try store.beginMediaIntent(kind: .photo)
        let original = root.appendingPathComponent(acceptedIntent.originalRelativePath)
        let bytes = Data([12, 23, 34, 45])
        try bytes.write(to: original)
        let accepted = try store.acceptMedia(acceptedIntent, inspection: LocalMediaInspection(
            byteCount: 4, sha256: String(repeating: "a", count: 64), width: 2, height: 2,
            orientation: 1, durationMilliseconds: nil, hasAudio: false, partial: false))
        let history = try store.pendingOperations(momentID: accepted.momentID)
        let broken = try store.beginMediaIntent(kind: .video, targetMomentID: accepted.momentID)
        let pending = root.appendingPathComponent(broken.pendingRelativePath)
        try Data([9, 8, 7]).write(to: pending)
        let unknown = root.appendingPathComponent("Media/Pending/unknown.mov")
        try bytes.write(to: unknown)
        let review = try vault.pendingMediaReview()
        XCTAssertEqual(review.count, 1)
        XCTAssertEqual(review[0].byteCount, 3)
        try vault.discardPendingMedia(review)
        XCTAssertFalse(FileManager.default.fileExists(atPath: pending.path))
        XCTAssertEqual(try Data(contentsOf: original), bytes)
        XCTAssertEqual(try Data(contentsOf: unknown), bytes)
        XCTAssertEqual(try store.allMediaAssets().map(\.id), [accepted.id])
        XCTAssertEqual(try store.pendingOperations(momentID: accepted.momentID), history)
    }

    func testChangedFileRejectsWholeBatchBeforeAnyDiscard() throws {
        let (root, store, vault) = try fixture()
        let empty = try store.beginMediaIntent(kind: .video)
        let changed = try store.beginMediaIntent(kind: .video)
        let file = root.appendingPathComponent(changed.pendingRelativePath)
        try Data([1]).write(to: file)
        let review = try vault.pendingMediaReview()
        try Data([1, 2]).write(to: file)
        XCTAssertThrowsError(try vault.discardPendingMedia(review))
        XCTAssertEqual(Set(try store.pendingMediaIntents().map(\.assetID)), [empty.assetID, changed.assetID])
        XCTAssertEqual(try Data(contentsOf: file), Data([1, 2]))
        try vault.discardPendingMedia(vault.pendingMediaReview())
        XCTAssertTrue(try store.pendingMediaIntents().isEmpty)
    }

    func testAcceptedAfterReviewCannotBeDeletedFromStaleReview() throws {
        let (root, store, vault) = try fixture()
        let intent = try store.beginMediaIntent(kind: .photo)
        let original = root.appendingPathComponent(intent.originalRelativePath)
        try Data([1, 2, 3]).write(to: original)
        let review = try vault.pendingMediaReview()
        _ = try store.acceptMedia(intent, inspection: LocalMediaInspection(
            byteCount: 3, sha256: String(repeating: "b", count: 64), width: 2, height: 2,
            orientation: 1, durationMilliseconds: nil, hasAudio: false, partial: false))
        XCTAssertThrowsError(try vault.discardPendingMedia(review))
        XCTAssertEqual(try Data(contentsOf: original), Data([1, 2, 3]))
    }

    func testProjectTrashBlocksIndependentDiscard() throws {
        let (_, store, vault) = try fixture()
        let trip = try XCTUnwrap(store.activeTrip())
        _ = try store.beginMediaIntent(kind: .video)
        let review = try vault.pendingMediaReview()
        _ = try store.requestProjectTrash(trip.id)
        XCTAssertThrowsError(try vault.discardPendingMedia(review))
        XCTAssertEqual(try store.pendingMediaIntents().count, 1)
    }

    func testSymlinkAndDirectoryCannotBecomeDiscardableFiles() throws {
        let (root, store, vault) = try fixture()
        let intent = try store.beginMediaIntent(kind: .video)
        let file = root.appendingPathComponent(intent.pendingRelativePath)
        let outside = root.appendingPathComponent("keep.mov")
        try Data([42]).write(to: outside)
        try FileManager.default.createSymbolicLink(at: file, withDestinationURL: outside)
        XCTAssertThrowsError(try vault.pendingMediaReview())
        try FileManager.default.removeItem(at: file)
        try FileManager.default.createDirectory(at: file, withIntermediateDirectories: false)
        XCTAssertThrowsError(try vault.pendingMediaReview())
        XCTAssertEqual(try Data(contentsOf: outside), Data([42]))
    }

    func testRetryAfterUnlinkFinishesDurableIntent() throws {
        let (root, store, vault) = try fixture()
        let intent = try store.beginMediaIntent(kind: .video)
        let file = root.appendingPathComponent(intent.pendingRelativePath)
        try Data([3, 2, 1]).write(to: file)
        let old = try vault.pendingMediaReview()
        try CaminoErasureEntry.remove(root: root, entries: old[0].files)
        // Simulated interruption after unlink and before the metadata commit.
        XCTAssertEqual(try store.pendingMediaIntents().count, 1)
        try vault.discardPendingMedia(vault.pendingMediaReview())
        XCTAssertTrue(try store.pendingMediaIntents().isEmpty)
    }
}
