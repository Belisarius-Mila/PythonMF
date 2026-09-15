import XCTest
@testable import CaminoAudioCore

@MainActor final class FakeDriver: AudioDriver {
    var permission: MicrophonePermission = .granted
    var granted = true
    var permissionRequests = 0
    var starts = 0
    var stops = 0
    var pauses = 0
    var plays = 0
    var playbackStops = 0
    var stopSuccess = true
    var failStart = false
    var failPlay = false
    var missingPlaybackFile = false
    var delayStart = false
    var pendingStart: CheckedContinuation<Void, Never>?
    var reading = CaptureSample(running: true, time: 0, power: -160,
                                inputID: "built-in", inputLabel: "Test microphone")
    var isPlaying = false
    var playbackTime: Double = 0
    var playbackDuration: Double = 30
    func requestPermission() async -> Bool { permissionRequests += 1; return granted }
    func start(url: URL) async throws {
        starts += 1
        if delayStart { await withCheckedContinuation { pendingStart = $0 } }
        if failStart { throw AudioPrototypeError.startFailed }
    }
    func sample() -> CaptureSample { reading }
    func pauseCapture() { pauses += 1 }
    func stop() async -> Bool { stops += 1; return stopSuccess }
    func play(url: URL) throws {
        if missingPlaybackFile { throw AudioPrototypeError.missingAudio }
        if failPlay { throw AudioPrototypeError.invalidAudio }
        plays += 1; isPlaying = true; playbackTime = 0
    }
    func stopPlayback() { playbackStops += 1; isPlaying = false }
}

@MainActor final class FakeStore: RecordingStorage {
    var began: [RecordingDraft] = []
    var completed: [RecordingClip] = []
    var failFinish = false
    func begin(kind: RecordingKind, continuation: RecordingContinuation? = nil) throws -> RecordingDraft {
        let d = RecordingDraft(id: UUID(), kind: kind, startedAt: Date(), continuation: continuation); began.append(d); return d
    }
    func url(for draft: RecordingDraft) -> URL { URL(fileURLWithPath: "/synthetic/\(draft.id).caf") }
    func finish(_ draft: RecordingDraft, interrupted: Bool) throws -> RecordingClip {
        if failFinish { throw AudioPrototypeError.invalidAudio }
        let c = RecordingClip(draft: draft,
            audio: AudioInspection(duration: 1, byteCount: 96000, sampleRate: 48000, channels: 1),
            interrupted: interrupted)
        completed.append(c); return c
    }
    func library() throws -> RecordingLibrary { var l = RecordingLibrary(); l.clips = completed; return l }
}

@MainActor final class AudioControllerTests: XCTestCase {
    func testFirstPermissionNeverStartsRecording() async {
        let d = FakeDriver(); d.permission = .undetermined
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment)
        XCTAssertEqual(d.permissionRequests, 1); XCTAssertEqual(d.starts, 0)
        XCTAssertEqual(s.began.count, 0); XCTAssertEqual(c.phase, .idle)
        d.permission = .granted
        await c.start(kind: .comment)
        XCTAssertEqual(d.starts, 1)
    }

    func testDeniedPermissionDoesNotLoopOrBlockPlayback() async {
        let d = FakeDriver(); d.permission = .denied
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment); await c.start(kind: .comment)
        XCTAssertEqual(d.permissionRequests, 0); XCTAssertEqual(d.starts, 0)
        let draft = try! s.begin(kind: .comment)
        let clip = try! s.finish(draft, interrupted: false)
        c.play(clip); XCTAssertEqual(c.phase, .playing)
    }

    func testMediaTimeRequiredAndSilenceIsValid() async {
        let d = FakeDriver(); let c = AudioController(driver: d, store: FakeStore())
        await c.start(kind: .reflection)
        XCTAssertEqual(c.phase, .preparing)
        d.reading.time = 0.5; c.tick()
        XCTAssertEqual(c.phase, .recording); XCTAssertEqual(c.power, -160)
        XCTAssertEqual(c.elapsed, 0.5)
    }

    func testDoubleStartAndStopDuringDelayedActivation() async {
        let d = FakeDriver(); d.delayStart = true
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        let first = Task { await c.start(kind: .reflection) }
        while d.pendingStart == nil { await Task.yield() }
        await c.start(kind: .comment)
        await c.stop()
        XCTAssertEqual(c.phase, .finishing); XCTAssertEqual(d.stops, 0)
        await c.start(kind: .comment)
        d.pendingStart?.resume(); await first.value
        XCTAssertEqual(d.starts, 1); XCTAssertEqual(d.stops, 1)
        XCTAssertEqual(s.completed.count, 1); XCTAssertEqual(s.completed[0].draft.kind, .reflection)
    }

    func testNoCompetingPlaybackOrRecording() async throws {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        let existing = try s.finish(s.begin(kind: .comment), interrupted: false)
        await c.start(kind: .comment); c.play(existing)
        XCTAssertEqual(d.plays, 0)
        await c.stop(); c.play(existing)
        await c.start(kind: .reflection)
        XCTAssertEqual(d.starts, 1); XCTAssertEqual(c.phase, .playing)
    }

    func testFailedCloseNeverClaimsSaved() async {
        let d = FakeDriver(); d.stopSuccess = false
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment); await c.stop()
        XCTAssertEqual(c.phase, .failed); XCTAssertEqual(s.completed.count, 0)
    }

    func testFailedPersistenceNeverClaimsSaved() async {
        let d = FakeDriver(); let s = FakeStore(); s.failFinish = true
        let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment); await c.stop()
        XCTAssertEqual(c.phase, .failed); XCTAssertEqual(s.completed.count, 0)
    }

    func testStartFailureClosesDriverAndKeepsAttempt() async {
        let d = FakeDriver(); d.failStart = true
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment)
        XCTAssertEqual(c.phase, .failed); XCTAssertEqual(d.stops, 1)
        XCTAssertEqual(s.began.count, 1); XCTAssertEqual(s.completed.count, 0)
    }

    func testStalledRecorderCannotKeepRecordingLabel() async {
        let d = FakeDriver(); let s = FakeStore(); var clock = 0.0
        let c = AudioController(driver: d, store: s, now: { clock })
        await c.start(kind: .comment)
        d.reading.time = 1; c.tick(); XCTAssertEqual(c.phase, .recording)
        clock = 3; c.tick(); XCTAssertEqual(c.phase, .finishing)
        while c.phase == .finishing { await Task.yield() }
        XCTAssertTrue(s.completed[0].interrupted); XCTAssertEqual(d.starts, 1)
    }

    func testRouteChangeStopsWithoutAutomaticResume() async {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment); d.reading.time = 1; c.tick()
        d.reading.inputID = "another-input"; d.reading.time = 2; c.tick()
        while c.phase == .finishing { await Task.yield() }
        XCTAssertTrue(s.completed[0].interrupted)
        c.tick(); XCTAssertEqual(d.starts, 1)
    }

    func testForegroundExitAndRepeatedInterruptCompleteOnlyOnce() async {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment)
        c.leaveForeground(); c.interrupt(); await c.stop()
        while c.phase == .finishing { await Task.yield() }
        XCTAssertEqual(d.stops, 1); XCTAssertEqual(s.completed.count, 1)
        XCTAssertTrue(s.completed[0].interrupted)
    }

    func testRestartLoadsLibraryWithoutMicrophone() throws {
        let d = FakeDriver(); let s = FakeStore()
        _ = try s.finish(s.begin(kind: .reflection), interrupted: false)
        let c = AudioController(driver: d, store: s)
        XCTAssertEqual(c.library.clips.count, 1); XCTAssertEqual(c.phase, .idle)
        XCTAssertEqual(d.starts, 0); XCTAssertEqual(d.permissionRequests, 0)
    }

    func testNaturalPlaybackEndReturnsToReady() throws {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        c.play(try s.finish(s.begin(kind: .comment), interrupted: false))
        d.isPlaying = false; c.tick()
        XCTAssertEqual(c.phase, .idle); XCTAssertNil(c.playingID)
        XCTAssertEqual(c.playbackElapsed, 0); XCTAssertEqual(c.playbackDuration, 0)
    }

    func testPlaybackProgressFollowsPlayerNotRecordingOrWallClock() async throws {
        let d = FakeDriver(); let s = FakeStore(); var clock = 0.0
        let c = AudioController(driver: d, store: s, now: { clock })
        await c.start(kind: .comment); await c.stop()
        XCTAssertEqual(c.elapsed, 1)
        c.play(try XCTUnwrap(s.completed.first))
        XCTAssertEqual(c.playbackElapsed, 0); XCTAssertEqual(c.playbackDuration, 30)
        var changes = 0; c.changed = { changes += 1 }
        d.playbackTime = 12; c.tick()
        XCTAssertEqual(c.playbackElapsed, 12); XCTAssertEqual(c.playbackProgress, 0.4, accuracy: 0.001)
        XCTAssertEqual(c.elapsed, 1); XCTAssertEqual(changes, 1)
        clock = 100; c.tick(); c.tick()
        XCTAssertEqual(c.playbackElapsed, 12) // A stalled player must not gain elapsed time.
        XCTAssertEqual(d.starts, 1)
    }

    func testPlaybackProgressClampsInvalidPlayerValues() throws {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        c.play(try s.finish(s.begin(kind: .comment), interrupted: false))
        d.playbackTime = 45; c.tick(); XCTAssertEqual(c.playbackProgress, 1)
        d.playbackTime = -1; c.tick(); XCTAssertEqual(c.playbackElapsed, 0)
        d.playbackTime = .nan; c.tick(); XCTAssertEqual(c.playbackElapsed, 0)
        d.playbackDuration = .infinity; c.tick()
        XCTAssertEqual(c.playbackDuration, 0); XCTAssertEqual(c.playbackProgress, 0)
        d.playbackDuration = -1; c.tick(); XCTAssertEqual(c.playbackDuration, 0)
    }

    func testPlaybackStopReplayAndForegroundExitResetProgress() throws {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        let clip = try s.finish(s.begin(kind: .reflection), interrupted: false)
        c.play(clip); d.playbackTime = 9; c.tick(); c.stopPlayback()
        XCTAssertEqual(c.phase, .idle); XCTAssertEqual(c.playbackProgress, 0)
        XCTAssertEqual(c.playbackElapsed, 0); XCTAssertNil(c.playingID)
        c.play(clip); XCTAssertEqual(c.playbackElapsed, 0)
        d.playbackTime = 4; c.tick(); c.leaveForeground()
        XCTAssertEqual(c.phase, .idle); XCTAssertEqual(c.playbackElapsed, 0)
        XCTAssertEqual(c.playbackDuration, 0); XCTAssertFalse(d.isPlaying)
        XCTAssertEqual(d.starts, 0); XCTAssertEqual(s.completed.count, 1)
    }

    func testPlaybackFailureDoesNotStartMicrophoneOrClaimPlaying() throws {
        let d = FakeDriver(); d.failPlay = true
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        c.play(try s.finish(s.begin(kind: .comment), interrupted: false))
        XCTAssertEqual(c.phase, .failed); XCTAssertNil(c.playingID)
        XCTAssertEqual(d.starts, 0); XCTAssertEqual(s.completed.count, 1)
        XCTAssertTrue(c.message.contains("nelze načíst nebo přehrát"))
        XCTAssertFalse(c.microphoneDenied)
    }

    func testMissingPlaybackFileKeepsMetadataAndAllowsAnotherClip() throws {
        let d = FakeDriver(); let s = FakeStore()
        let missing = try s.finish(s.begin(kind: .comment), interrupted: false)
        let available = try s.finish(s.begin(kind: .reflection), interrupted: false)
        let c = AudioController(driver: d, store: s)
        d.missingPlaybackFile = true; c.play(missing)
        XCTAssertEqual(c.phase, .failed); XCTAssertNil(c.playingID)
        XCTAssertTrue(c.message.contains("Soubor nahrávky není dostupný"))
        XCTAssertEqual(c.library.clips.map(\.id), [missing.id, available.id])
        XCTAssertEqual(s.completed.count, 2); XCTAssertEqual(d.starts, 0)
        d.missingPlaybackFile = false; c.play(available)
        XCTAssertEqual(c.phase, .playing); XCTAssertEqual(c.playingID, available.id)
        XCTAssertEqual(d.plays, 1)
    }

    func testMicrophoneSettingsReflectPermissionNotUnrelatedFailure() async {
        let d = FakeDriver(); let s = FakeStore(); s.failFinish = true
        let c = AudioController(driver: d, store: s)
        await c.start(kind: .comment); await c.stop()
        XCTAssertEqual(c.phase, .failed); XCTAssertFalse(c.microphoneDenied)
        d.permission = .denied
        XCTAssertTrue(c.microphoneDenied)
        d.permission = .undetermined
        XCTAssertFalse(c.microphoneDenied)
        d.permission = .granted
        XCTAssertFalse(c.microphoneDenied)
        XCTAssertEqual(d.permissionRequests, 0); XCTAssertEqual(d.starts, 1)
    }

    func testPlaybackInterruptionUpdatesStateWithoutWaitingForTimer() throws {
        for playerStillReportsPlaying in [true, false] {
            let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
            c.play(try s.finish(s.begin(kind: .comment), interrupted: false))
            d.playbackTime = 12; c.tick()
            d.isPlaying = playerStillReportsPlaying
            var changes = 0; c.changed = { changes += 1 }
            c.interrupt()
            XCTAssertEqual(c.phase, .idle); XCTAssertNil(c.playingID)
            XCTAssertEqual(c.playbackElapsed, 0); XCTAssertEqual(c.playbackDuration, 0)
            XCTAssertFalse(d.isPlaying); XCTAssertEqual(d.playbackStops, 1)
            XCTAssertEqual(changes, 1)
            XCTAssertTrue(c.message.contains("přerušeno"))
        }
    }

    func testRepeatedPlaybackInterruptionDoesNotRestartOrChangeRecordings() throws {
        let d = FakeDriver(); let s = FakeStore(); let c = AudioController(driver: d, store: s)
        let clip = try s.finish(s.begin(kind: .reflection), interrupted: false)
        c.play(clip); c.interrupt(); c.interrupt(); c.tick()
        XCTAssertEqual(d.playbackStops, 1); XCTAssertEqual(d.plays, 1)
        XCTAssertEqual(d.starts, 0); XCTAssertEqual(d.stops, 0)
        XCTAssertEqual(s.began.count, 1); XCTAssertEqual(s.completed.count, 1)
        XCTAssertEqual(s.completed[0].id, clip.id); XCTAssertFalse(s.completed[0].interrupted)
        c.play(clip) // Only an explicit Play starts a new player.
        XCTAssertEqual(d.plays, 2); XCTAssertEqual(c.phase, .playing)
        XCTAssertEqual(c.playbackElapsed, 0)
    }

    func testInterruptionDuringPreparationClosesBeforeNewStart() async {
        let d = FakeDriver(); d.delayStart = true
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        let first = Task { await c.start(kind: .comment) }
        while d.pendingStart == nil { await Task.yield() }
        c.leaveForeground()
        await c.start(kind: .reflection)
        d.pendingStart?.resume(); await first.value
        XCTAssertEqual(d.starts, 1); XCTAssertEqual(d.stops, 1)
        XCTAssertTrue(s.completed[0].interrupted)
    }
}
