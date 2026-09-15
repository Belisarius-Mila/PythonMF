import XCTest
@testable import CaminoAudioCore

@MainActor final class RecordingStoreTests: XCTestCase {
    // Synthetic fixtures only. Retained in system temporary storage; no user files touched.
    private func directory() throws -> URL {
        let root = FileManager.default.temporaryDirectory.appendingPathComponent("camino-test-\(UUID())")
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: false)
        return root
    }
    private func inspect(_ url: URL) throws -> AudioInspection {
        let data = try Data(contentsOf: url)
        guard data == Data([1, 2, 3, 4]) else { throw AudioPrototypeError.invalidAudio }
        return AudioInspection(duration: 1, byteCount: 4, sampleRate: 48000, channels: 1)
    }

    func testCollisionCannotOverwriteOriginalAudioOrReceipts() throws {
        let id = UUID(); let root = try directory()
        let store = try RecordingStore(root: root, makeID: { id }, inspect: inspect)
        let d = try store.begin(kind: .reflection)
        try Data([1, 2, 3, 4]).write(to: store.url(for: d))
        _ = try store.finish(d, interrupted: false)
        XCTAssertThrowsError(try store.begin(kind: .comment))
        XCTAssertEqual(try Data(contentsOf: store.url(for: d)), Data([1, 2, 3, 4]))
        XCTAssertEqual(try store.library().clips[0].draft.kind, .reflection)
    }

    func testRepeatedFinishCannotRewriteCompletion() throws {
        let store = try RecordingStore(root: directory(), inspect: inspect)
        let d = try store.begin(kind: .comment)
        try Data([1, 2, 3, 4]).write(to: store.url(for: d))
        _ = try store.finish(d, interrupted: false)
        XCTAssertThrowsError(try store.finish(d, interrupted: true))
        XCTAssertFalse(try store.library().clips[0].interrupted)
    }

    func testCorruptAndIncompleteAttemptsRemainOnDisk() throws {
        let store = try RecordingStore(root: directory(), inspect: inspect)
        let d = try store.begin(kind: .comment)
        try Data([9]).write(to: store.url(for: d))
        XCTAssertThrowsError(try store.finish(d, interrupted: false))
        let library = try store.library()
        XCTAssertEqual(library.unfinishedCount, 1); XCTAssertEqual(library.clips.count, 0)
        XCTAssertEqual(try Data(contentsOf: store.url(for: d)), Data([9]))
    }

    func testNewStoreRecoversCompletedRecordsWithoutChangingThem() throws {
        let root = try directory(); let s = try RecordingStore(root: root, inspect: inspect)
        let d = try s.begin(kind: .reflection)
        try Data([1, 2, 3, 4]).write(to: s.url(for: d))
        let clip = try s.finish(d, interrupted: true)
        let restarted = try RecordingStore(root: root, inspect: inspect)
        XCTAssertEqual(try restarted.library().clips, [clip])
    }

    func testMissingMediaIsNotListedAsSaved() throws {
        let root = try directory(); let s = try RecordingStore(root: root, inspect: inspect)
        _ = try s.begin(kind: .reflection)
        XCTAssertEqual(try s.library().unfinishedCount, 1)
        XCTAssertTrue(try s.library().clips.isEmpty)
    }

    func testInvalidDurationIsRejected() throws {
        let s = try RecordingStore(root: directory(), inspect: { _ in
            AudioInspection(duration: .nan, byteCount: 4, sampleRate: 48000, channels: 1)
        })
        let d = try s.begin(kind: .comment)
        XCTAssertThrowsError(try s.finish(d, interrupted: false))
    }

    func testMismatchedDraftCannotBeCommitted() throws {
        let s = try RecordingStore(root: directory(), inspect: inspect)
        let d = try s.begin(kind: .reflection)
        try Data([1, 2, 3, 4]).write(to: s.url(for: d))
        let forged = RecordingDraft(id: d.id, kind: .comment, startedAt: d.startedAt)
        XCTAssertThrowsError(try s.finish(forged, interrupted: false))
        XCTAssertTrue(try s.library().clips.isEmpty)
    }
}
