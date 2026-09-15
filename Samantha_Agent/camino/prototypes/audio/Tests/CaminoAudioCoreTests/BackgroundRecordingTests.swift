import XCTest
@testable import CaminoAudioCore

@MainActor final class BackgroundRecordingTests: XCTestCase {
    private func settle(_ c: AudioController) async {
        for _ in 0..<1000 {
            if c.phase != .finishing { return }
            await Task.yield()
        }
        XCTFail("Completion did not settle")
    }

    func testRunningCaptureSurvivesBackgroundAndReturnWithoutRestart() async {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .reflection); d.reading.time = 1; c.tick()
        c.leaveForeground(); await c.start(kind: .comment)
        d.reading.time = 1800; c.tick(); c.enterForeground()
        XCTAssertEqual(c.phase, .recording); XCTAssertEqual(c.elapsed, 1800)
        XCTAssertEqual(d.starts, 1); XCTAssertEqual(d.stops, 0); XCTAssertEqual(d.pauses, 0)
        await c.stop(); XCTAssertEqual(s.completed.count, 1)
        XCTAssertFalse(s.completed[0].interrupted)
    }

    func testBackgroundCannotStartMicrophoneOrPermissionRequest() async {
        let d = FakeDriver(); d.permission = .undetermined
        let c = AudioController(driver: d, store: FakeStore())
        c.leaveForeground(); await c.start(kind: .comment)
        XCTAssertEqual(d.starts, 0); XCTAssertEqual(d.permissionRequests, 0)
        c.enterForeground(); XCTAssertEqual(d.starts, 0)
    }

    func testInterruptionPausesImmediatelyAndContinuesOnlyIntoNewLinkedPart() async {
        let d = FakeDriver(); let s = FakeStore(); var clock = 10.0
        let c = AudioController(driver: d, store: s, now: { clock })
        await c.start(kind: .reflection); d.reading.time = 1; c.tick()
        let original = s.began[0]
        c.interrupt(); c.interrupt()
        XCTAssertEqual(d.pauses, 1); XCTAssertFalse(c.canContinue)
        await c.continueRecording(); XCTAssertEqual(d.starts, 1)
        await settle(c)
        c.interruptionEnded(); c.leaveForeground(); await c.continueRecording(); c.enterForeground()
        XCTAssertEqual(d.starts, 1); XCTAssertEqual(c.phase, .interrupted)
        clock = 17
        await c.continueRecording()
        XCTAssertEqual(d.starts, 2); XCTAssertEqual(s.began.count, 2)
        let next = s.began[1]
        XCTAssertNotEqual(next.id, original.id); XCTAssertEqual(next.sessionID, original.id)
        XCTAssertEqual(next.continuation?.previousPartID, original.id)
        XCTAssertEqual(next.continuation?.gapSeconds, 7); XCTAssertEqual(next.kind, .reflection)
        await c.stop()
        XCTAssertEqual(s.completed.count, 2); XCTAssertTrue(s.completed[0].interrupted)
        XCTAssertFalse(s.completed[1].interrupted); XCTAssertEqual(c.library.sessions.count, 1)
    }

    func testFailedContinuationKeepsOriginalAndCanRetryWithoutAutoStart() async {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment); c.interrupt(); await settle(c)
        let original = s.completed[0]
        d.failStart = true; await c.continueRecording()
        XCTAssertEqual(c.phase, .interrupted); XCTAssertTrue(c.canContinue)
        XCTAssertEqual(s.completed, [original]); XCTAssertEqual(d.starts, 2)
        c.interruptionEnded(); c.enterForeground(); XCTAssertEqual(d.starts, 2)
        d.failStart = false; await c.continueRecording()
        XCTAssertEqual(s.began.last?.continuation?.previousPartID, original.id)
        XCTAssertEqual(d.starts, 3)
    }

    func testPermissionRevokedDuringInterruptionDoesNotLoseContinuation() async {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .reflection); c.interrupt(); await settle(c)
        d.permission = .denied; await c.continueRecording()
        XCTAssertEqual(c.phase, .interrupted); XCTAssertTrue(c.microphoneDenied)
        XCTAssertEqual(d.starts, 1); XCTAssertTrue(c.canPlay)
        d.permission = .granted; c.enterForeground(); XCTAssertEqual(d.starts, 1)
        await c.continueRecording(); XCTAssertEqual(d.starts, 2)
    }

    func testPlayingPreservedPartDoesNotDismissInterruptedSession() async {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment); c.interrupt(); await settle(c)
        c.play(s.completed[0]); XCTAssertEqual(c.phase, .playing)
        c.stopPlayback(); XCTAssertEqual(c.phase, .interrupted); XCTAssertTrue(c.canContinue)
        XCTAssertFalse(c.canStart); XCTAssertEqual(d.starts, 1)
        c.endInterruptedSession(); XCTAssertTrue(c.canStart); XCTAssertFalse(c.canContinue)
        await c.start(kind: .reflection)
        XCTAssertNil(s.began.last?.continuation); XCTAssertEqual(s.began.last?.kind, .reflection)
    }

    func testFailedInterruptedCloseRetainsAttemptWithoutClaimingSaved() async {
        let d = FakeDriver(); d.stopSuccess = false
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment); c.interrupt(); await settle(c)
        XCTAssertTrue(s.completed.isEmpty); XCTAssertEqual(s.began.count, 1)
        XCTAssertEqual(c.phase, .interrupted); XCTAssertTrue(c.message.contains("nepodařilo ověřit"))
        d.stopSuccess = true; await c.continueRecording(); await c.stop()
        XCTAssertEqual(s.completed.count, 1)
        XCTAssertEqual(s.completed[0].draft.continuation?.previousPartID, s.began[0].id)
    }

    func testRouteNotificationChecksActualInputWithoutRequiringTimeAdvance() async {
        let d = FakeDriver(); let c = AudioController(driver: d, store: FakeStore())
        await c.start(kind: .comment); d.reading.time = 1; c.tick()
        c.routeChanged(); XCTAssertEqual(d.pauses, 0)
        d.reading.inputID = ""; c.routeChanged()
        XCTAssertEqual(d.pauses, 1); XCTAssertEqual(c.phase, .finishing)
        await settle(c); XCTAssertEqual(c.phase, .interrupted); XCTAssertEqual(d.starts, 1)
    }

    func testInputChangeBeforeFirstMediaTickStillInterrupts() async {
        let d = FakeDriver(); let c = AudioController(driver: d, store: FakeStore())
        await c.start(kind: .comment); XCTAssertEqual(c.phase, .preparing)
        d.reading.inputID = "headset"; c.routeChanged()
        XCTAssertEqual(d.pauses, 1)
        await settle(c); XCTAssertEqual(c.phase, .interrupted)
    }

    func testInvalidClockDoesNotInventPauseDuration() async {
        let d = FakeDriver(); let s = FakeStore(); var clock = 20.0
        let c = AudioController(driver: d, store: s, now: { clock })
        await c.start(kind: .comment); c.interrupt(); await settle(c)
        clock = 10; await c.continueRecording()
        XCTAssertNil(s.began.last?.continuation?.gapSeconds)
    }

    func testSecondInterruptionKeepsSessionAndLinksImmediatePredecessor() async {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .reflection); c.interrupt(); await settle(c)
        await c.continueRecording(); c.interrupt(); await settle(c)
        await c.continueRecording()
        XCTAssertEqual(s.began[2].sessionID, s.began[0].id)
        XCTAssertEqual(s.began[2].continuation?.previousPartID, s.began[1].id)
    }

    func testPartOrderUsesLinksWhenWallClockMovesBackwards() {
        let first = RecordingDraft(id: UUID(), kind: .reflection, startedAt: Date(timeIntervalSince1970: 100))
        let second = RecordingDraft(id: UUID(), kind: .reflection, startedAt: Date(timeIntervalSince1970: 50),
            continuation: RecordingContinuation(sessionID: first.id, previousPartID: first.id, gapSeconds: 10))
        let third = RecordingDraft(id: UUID(), kind: .reflection, startedAt: Date(timeIntervalSince1970: 1),
            continuation: RecordingContinuation(sessionID: first.id, previousPartID: second.id, gapSeconds: 10))
        var library = RecordingLibrary()
        library.clips = [third, first, second].map { RecordingClip(draft: $0,
            audio: AudioInspection(duration: 1, byteCount: 1, sampleRate: 48000, channels: 1), interrupted: true) }
        XCTAssertEqual(library.sessions[0].parts.map(\.id), [first.id, second.id, third.id])
    }
}
