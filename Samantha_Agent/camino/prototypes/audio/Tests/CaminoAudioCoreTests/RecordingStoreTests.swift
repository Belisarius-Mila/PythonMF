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
    private func segmentFolder(_ root: URL, _ id: UUID) -> URL {
        root.appendingPathComponent(id.uuidString).appendingPathComponent("segments")
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

    func testContinuationSurvivesReloadWithoutRewritingPreviousPart() throws {
        let root = try directory(); let s = try RecordingStore(root: root, inspect: inspect)
        let first = try s.begin(kind: .reflection)
        try Data([1, 2, 3, 4]).write(to: s.url(for: first))
        _ = try s.finish(first, interrupted: true)
        let receipt = root.appendingPathComponent(first.id.uuidString).appendingPathComponent("completed.json")
        let original = try Data(contentsOf: receipt)
        let continuation = RecordingContinuation(sessionID: first.id, previousPartID: first.id, gapSeconds: 12)
        let second = try s.begin(kind: .reflection, continuation: continuation)
        try Data([1, 2, 3, 4]).write(to: s.url(for: second))
        _ = try s.finish(second, interrupted: false)
        let reloaded = try RecordingStore(root: root, inspect: inspect).library()
        XCTAssertEqual(reloaded.sessions.count, 1); XCTAssertEqual(reloaded.sessions[0].parts.count, 2)
        XCTAssertEqual(reloaded.sessions[0].parts[1].draft.continuation, continuation)
        XCTAssertEqual(try Data(contentsOf: receipt), original)
        XCTAssertEqual(try Data(contentsOf: s.url(for: first)), Data([1, 2, 3, 4]))
    }

    func testLegacyC01aJSONLoadsWithoutMigrationOrRewriting() throws {
        let root = try directory(); let id = UUID()
        let folder = root.appendingPathComponent(id.uuidString)
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: false)
        let draftJSON = "{\"id\":\"\(id.uuidString)\",\"kind\":\"Komentář\",\"startedAt\":12345}"
        let clipJSON = "{\"draft\":\(draftJSON),\"audio\":{\"duration\":1,\"byteCount\":4,\"sampleRate\":48000,\"channels\":1},\"interrupted\":false}"
        let receipt = folder.appendingPathComponent("completed.json")
        try Data(draftJSON.utf8).write(to: folder.appendingPathComponent("started.json"))
        try Data(clipJSON.utf8).write(to: receipt)
        try Data([1, 2, 3, 4]).write(to: folder.appendingPathComponent("audio.caf"))
        let lib = try RecordingStore(root: root, inspect: inspect).library()
        XCTAssertEqual(lib.clips.count, 1); XCTAssertEqual(lib.unfinishedCount, 0)
        XCTAssertNil(lib.clips[0].draft.continuation); XCTAssertEqual(lib.clips[0].draft.sessionID, id)
        XCTAssertEqual(try Data(contentsOf: receipt), Data(clipJSON.utf8))
    }

    func testContinuationRejectsWrongKindSessionAndNegativeGapBeforeCreatingAttempt() throws {
        let root = try directory(); let s = try RecordingStore(root: root, inspect: inspect)
        let first = try s.begin(kind: .reflection)
        for (kind, session, gap) in [(RecordingKind.comment, first.id, 1.0),
                                      (.reflection, UUID(), 1.0), (.reflection, first.id, -1.0)] {
            XCTAssertThrowsError(try s.begin(kind: kind, continuation:
                RecordingContinuation(sessionID: session, previousPartID: first.id, gapSeconds: gap)))
        }
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: root.path).count, 1)
    }

    func testCheckpointPolicyRotatesBeforeSixtySecondCeiling() {
        let policy = SegmentCheckpointPolicy()
        XCTAssertTrue(policy.valid)
        let rate = 48_000.0
        var current: Int64 = 0
        var longest = 0.0
        for _ in 0..<900 { // 90 seconds in 100 ms buffers.
            let incoming: Int64 = 4_800
            if policy.shouldRotate(framesWritten: current, incomingFrames: incoming,
                                   sampleRate: rate) {
                longest = max(longest, Double(current) / rate); current = 0
            }
            current += incoming
        }
        longest = max(longest, Double(current) / rate)
        XCTAssertLessThanOrEqual(longest, policy.maximumSeconds)
        XCTAssertGreaterThan(longest, 50)
    }

    func testRestartRecoversValidOpenPartAsPartialRecording() throws {
        let root = try directory()
        let store = try RecordingStore(root: root, inspect: inspect)
        let draft = try store.begin(kind: .reflection)
        let partial = store.url(for: draft)
        try Data([1, 2, 3, 4]).write(to: partial)

        let restarted = try RecordingStore(root: root, inspect: inspect)
        let library = try restarted.library()
        XCTAssertEqual(library.clips.count, 1); XCTAssertEqual(library.unfinishedCount, 0)
        let clip = try XCTUnwrap(library.clips.first)
        XCTAssertEqual(clip.recovery,
            RecordingRecovery(recoveredAfterCrash: true, missingTail: true))
        XCTAssertTrue(clip.interrupted)
        XCTAssertEqual(clip.segments?.map(\.index), [0])
        XCTAssertEqual(clip.segments?.first?.recovered, true)
        XCTAssertFalse(FileManager.default.fileExists(atPath: partial.path))
        XCTAssertEqual(try restarted.playbackURLs(for: clip).count, 1)
        let driver = FakeDriver()
        let controller = AudioController(driver: driver, store: restarted)
        XCTAssertEqual(controller.phase, .idle)
        XCTAssertEqual(controller.library.clips.count, 1)
        XCTAssertEqual(driver.starts, 0); XCTAssertEqual(driver.permissionRequests, 0)
    }

    func testRecoveryKeepsInvalidTailAndDoesNotDuplicateClosedPart() throws {
        let root = try directory()
        let store = try RecordingStore(root: root, inspect: inspect)
        let draft = try store.begin(kind: .comment)
        let media = segmentFolder(root, draft.id)
        let first = store.url(for: draft)
        try Data([1, 2, 3, 4]).write(to: first)
        try FileManager.default.moveItem(at: first,
            to: media.appendingPathComponent("segment-000000.caf"))
        let invalidTail = media.appendingPathComponent("segment-000001.partial.caf")
        try Data([9]).write(to: invalidTail)

        let restarted = try RecordingStore(root: root, inspect: inspect)
        let clip = try XCTUnwrap(try restarted.library().clips.first)
        XCTAssertEqual(clip.segments?.map(\.index), [0])
        XCTAssertTrue(FileManager.default.fileExists(atPath: invalidTail.path))
        let restartedAgain = try RecordingStore(root: root, inspect: inspect)
        let secondLibrary = try restartedAgain.library()
        XCTAssertEqual(secondLibrary.clips.count, 1)
        XCTAssertEqual(secondLibrary.clips[0].segments?.count, 1)
    }

    func testRecoveryRetainsValidOrphanAfterIndexGapAndMarksDiscontinuity() throws {
        let root = try directory()
        let store = try RecordingStore(root: root, inspect: inspect)
        let draft = try store.begin(kind: .reflection)
        let media = segmentFolder(root, draft.id)
        let first = store.url(for: draft)
        try Data([1, 2, 3, 4]).write(to: first)
        try FileManager.default.moveItem(at: first,
            to: media.appendingPathComponent("segment-000000.caf"))
        try Data([1, 2, 3, 4]).write(
            to: media.appendingPathComponent("segment-000002.caf"))

        let restarted = try RecordingStore(root: root, inspect: inspect)
        let clip = try XCTUnwrap(try restarted.library().clips.first)
        XCTAssertEqual(clip.segments?.map(\.index), [0, 2])
        XCTAssertEqual(clip.segments?.map(\.discontinuityBefore), [false, true])
        XCTAssertEqual(try restarted.playbackURLs(for: clip).count, 2)
    }

    func testNormalFinishCommitsEveryClosedPartWithoutRecoveryLabel() throws {
        let root = try directory()
        let store = try RecordingStore(root: root, inspect: inspect)
        let draft = try store.begin(kind: .comment)
        let media = segmentFolder(root, draft.id)
        let first = store.url(for: draft)
        try Data([1, 2, 3, 4]).write(to: first)
        try FileManager.default.moveItem(at: first,
            to: media.appendingPathComponent("segment-000000.caf"))
        try Data([1, 2, 3, 4]).write(
            to: media.appendingPathComponent("segment-000001.partial.caf"))

        let clip = try store.finish(draft, interrupted: false)
        XCTAssertNil(clip.recovery); XCTAssertFalse(clip.interrupted)
        XCTAssertEqual(clip.segments?.map(\.index), [0, 1])
        XCTAssertEqual(clip.audio.duration, 2)
        XCTAssertEqual(clip.audio.byteCount, 8)
        XCTAssertEqual(try store.playbackURLs(for: clip).count, 2)
    }
}
