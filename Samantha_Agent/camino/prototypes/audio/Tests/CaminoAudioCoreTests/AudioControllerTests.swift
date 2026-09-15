import XCTest
@testable import CaminoAudioCore

@MainActor final class FakeDriver: AudioDriver {
    var permission: MicrophonePermission = .granted
    var granted = true
    var permissionRequests = 0
    var starts = 0
    var stops = 0
    var plays = 0
    var stopSuccess = true
    var failStart = false
    var failPlay = false
    var delayStart = false
    var pendingStart: CheckedContinuation<Void, Never>?
    var reading = CaptureSample(running: true, time: 0, power: -160,
                                inputID: "built-in", inputLabel: "Test microphone")
    var isPlaying = false
    func requestPermission() async -> Bool { permissionRequests += 1; return granted }
    func start(url: URL) async throws {
        starts += 1
        if delayStart { await withCheckedContinuation { pendingStart = $0 } }
        if failStart { throw AudioPrototypeError.startFailed }
    }
    func sample() -> CaptureSample { reading }
    func stop() async -> Bool { stops += 1; return stopSuccess }
    func play(url: URL) throws {
        if failPlay { throw AudioPrototypeError.invalidAudio }
        plays += 1; isPlaying = true
    }
    func stopPlayback() { isPlaying = false }
}

@MainActor final class FakeStore: RecordingStorage {
    var began: [RecordingDraft] = []
    var completed: [RecordingClip] = []
    var failFinish = false
    func begin(kind: RecordingKind) throws -> RecordingDraft {
        let d = RecordingDraft(id: UUID(), kind: kind, startedAt: Date()); began.append(d); return d
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
    }

    func testPlaybackFailureDoesNotStartMicrophoneOrClaimPlaying() throws {
        let d = FakeDriver(); d.failPlay = true
        let s = FakeStore(); let c = AudioController(driver: d, store: s)
        c.play(try s.finish(s.begin(kind: .comment), interrupted: false))
        XCTAssertEqual(c.phase, .failed); XCTAssertNil(c.playingID)
        XCTAssertEqual(d.starts, 0); XCTAssertEqual(s.completed.count, 1)
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
