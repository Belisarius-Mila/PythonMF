import Foundation

@MainActor public final class AudioController {
    public private(set) var phase: CapturePhase = .idle
    public private(set) var message = "Připraveno"
    public private(set) var elapsed: Double = 0
    public private(set) var power: Float = -160
    public private(set) var input = "Mikrofon se ověří při spuštění"
    public private(set) var library = RecordingLibrary()
    public private(set) var playingID: UUID?
    public private(set) var playbackElapsed: Double = 0
    public private(set) var playbackDuration: Double = 0
    public var playbackProgress: Double {
        playbackDuration > 0 ? playbackElapsed / playbackDuration : 0
    }
    public var changed: (() -> Void)?
    public var canStart: Bool { foreground && resumeDraft == nil && (phase == .idle || phase == .failed) }
    public var canContinue: Bool { foreground && resumeDraft != nil && phase == .interrupted }
    public var canPlay: Bool { foreground && (canStart || phase == .interrupted) }
    public var canStop: Bool { phase == .preparing || phase == .recording }
    public var isFinishingInterrupted: Bool { phase == .finishing && interrupted }
    public var microphoneDenied: Bool { driver.permission == .denied }
    private let driver: AudioDriver
    private let store: RecordingStorage
    private let now: () -> Double
    private var draft: RecordingDraft?
    private var starting = false
    private var stopRequested = false
    private var interrupted = false
    private var routeID = ""
    private var lastAdvance = 0.0
    private var foreground = true
    private var resumeDraft: RecordingDraft?
    private var interruptedAt: Double?
    private var interruptionReason = "Nahrávání přerušeno"

    public init(driver: AudioDriver, store: RecordingStorage,
                now: @escaping () -> Double = { ProcessInfo.processInfo.systemUptime }) {
        self.driver = driver; self.store = store; self.now = now
        refreshLibrary()
    }

    public func start(kind: RecordingKind) async {
        guard canStart else { return }
        await begin(kind: kind, continuation: nil)
    }

    public func continueRecording() async {
        guard canContinue, let previous = resumeDraft else { return }
        let gap = interruptedAt.map { now() - $0 }
        let continuation = RecordingContinuation(sessionID: previous.sessionID,
            previousPartID: previous.id, gapSeconds: gap.flatMap { $0.isFinite && $0 >= 0 ? $0 : nil })
        await begin(kind: previous.kind, continuation: continuation)
    }

    public func endInterruptedSession() {
        guard phase == .interrupted else { return }
        resumeDraft = nil; interruptedAt = nil; phase = .idle
        message = "Nahrávání ukončeno. Zachované části jsou v seznamu."; changed?()
    }

    private func begin(kind: RecordingKind, continuation: RecordingContinuation?) async {
        switch driver.permission {
        case .denied:
            fail("Mikrofon není povolený. Povol jej v Nastavení; uložené nahrávky lze přehrát.")
            if resumeDraft != nil { phase = .interrupted; changed?() }
            return
        case .undetermined:
            phase = .permission; message = "Povolení mikrofonu"; changed?()
            let granted = await driver.requestPermission()
            phase = resumeDraft == nil ? .idle : .interrupted
            message = granted ? "Mikrofon povolen. Nahrávání spustíš tlačítkem Start."
                : "Mikrofon není povolený. Nahrávání nezačalo."
            changed?(); return
        case .granted: break
        }
        phase = .preparing; message = "Připravuji mikrofon"
        elapsed = 0; power = -160; stopRequested = false; interrupted = false
        routeID = ""; starting = true; changed?()
        do {
            let attempt = try store.begin(kind: kind, continuation: continuation); draft = attempt
            try await driver.start(url: store.url(for: attempt))
            starting = false
            lastAdvance = now()
            if stopRequested { await finish(); return }
            resumeDraft = nil; interruptedAt = nil
            let initialInput = driver.sample()
            routeID = initialInput.inputID; input = initialInput.inputLabel
            tick()
        } catch {
            starting = false; phase = .finishing; changed?()
            _ = await driver.stop()
            draft = nil
            fail("Nahrávání se nepodařilo spustit. Případný neúplný soubor zůstal zachovaný.")
            if resumeDraft != nil { phase = .interrupted; changed?() }
            refreshLibrary()
        }
    }

    /// The timer only observes recorder media time; wall time can never assert recording.
    public func tick() {
        if phase == .playing {
            if !driver.isPlaying { stopPlayback() }
            else { updatePlaybackProgress(); changed?() }
            return
        }
        guard !starting, phase == .preparing || phase == .recording else { return }
        let value = driver.sample()
        if !routeID.isEmpty && value.inputID != routeID {
            interrupt(); return
        }
        if value.time.isFinite && value.time > elapsed && value.running && !value.inputID.isEmpty {
            routeID = value.inputID; input = value.inputLabel
            elapsed = value.time; power = value.power.isFinite ? value.power : -160
            lastAdvance = now(); phase = .recording; message = "Nahrávám"
        } else if !value.running || now() - lastAdvance >= 2 {
            interrupt(); return
        }
        changed?()
    }

    public func stop() async {
        guard canStop else { return }
        stopRequested = true; phase = .finishing; message = "Ukončuji a ověřuji soubor"; changed?()
        if !starting { await finish() }
    }

    public func interrupt(reason: String = "Nahrávání přerušeno") {
        if phase == .playing {
            endPlayback(message: "Přehrávání přerušeno. Spustíš je znovu tlačítkem Přehrát.")
            return
        }
        guard canStop else { return }
        interrupted = true
        interruptionReason = reason; interruptedAt = now(); resumeDraft = draft
        driver.pauseCapture()
        // Transition before scheduling the task: a second event cannot race a new Start.
        stopRequested = true; phase = .finishing; message = "Přerušeno — ověřuji zachovaný záznam"; changed?()
        if !starting { Task { await finish() } }
    }

    public func leaveForeground() {
        foreground = false
        if phase == .playing { stopPlayback() }
        // A verified running recorder continues. Pending activation must never start behind a lock.
        else if phase == .preparing { interrupt(reason: "Příprava nahrávání přerušena") }
        changed?()
    }

    public func enterForeground() {
        foreground = true
        if phase == .recording || phase == .preparing { tick() }
        else { refreshLibrary() }
        changed?()
    }

    public func interruptionEnded() {
        // Some interruptions have no end event. Only explicit Continue may try activation again.
        changed?()
    }

    public func routeChanged() {
        guard !starting, canStop else { return }
        if !routeID.isEmpty && driver.sample().inputID != routeID {
            interrupt(reason: "Mikrofon se změnil")
        }
    }

    public func play(_ clip: RecordingClip) {
        guard canPlay else { return }
        do {
            try driver.play(url: store.url(for: clip.draft))
            updatePlaybackProgress()
            playingID = clip.id; phase = .playing; message = "Přehrávám"; changed?()
        } catch AudioPrototypeError.missingAudio {
            fail("Soubor nahrávky není dostupný. Její evidenci jsme zachovali.")
        } catch { fail("Nahrávku nelze načíst nebo přehrát. Soubor se nemaže.") }
    }

    public func stopPlayback() {
        endPlayback(message: "Připraveno")
    }

    private func endPlayback(message: String) {
        guard phase == .playing else { return }
        driver.stopPlayback(); playingID = nil
        playbackElapsed = 0; playbackDuration = 0
        phase = resumeDraft == nil ? .idle : .interrupted
        self.message = resumeDraft == nil ? message : "Nahrávání přerušeno. Pokračování spustíš vědomě."
        changed?()
    }

    private func updatePlaybackProgress() {
        // Observe the player's media position; timer ticks never invent progress.
        let duration = driver.playbackDuration
        let position = driver.playbackTime
        playbackDuration = duration.isFinite && duration > 0 ? duration : 0
        playbackElapsed = position.isFinite ? min(playbackDuration, max(0, position)) : 0
    }

    private func finish() async {
        guard let attempt = draft else { return }
        // Taking ownership prevents duplicate delegate, Stop and interruption completion.
        draft = nil
        let closed = await driver.stop()
        do {
            guard closed else { throw AudioPrototypeError.invalidAudio }
            let clip = try store.finish(attempt, interrupted: interrupted)
            elapsed = clip.audio.duration; power = -160; phase = interrupted ? .interrupted : .idle
            message = interrupted ? "\(interruptionReason). Zachovanou část lze přehrát."
                : "Uloženo v telefonu"
        } catch {
            fail("Uložení se nepodařilo ověřit. Neúplný záznam zůstal zachovaný.")
            if interrupted { phase = .interrupted }
        }
        if foreground { refreshLibrary() }
        changed?()
    }

    private func refreshLibrary() {
        do { library = try store.library() }
        catch { fail("Seznam nahrávek nelze načíst. Stávající soubory zůstaly zachované.") }
    }

    private func fail(_ text: String) {
        phase = resumeDraft == nil ? .failed : .interrupted
        message = text; power = -160; changed?()
    }
}
