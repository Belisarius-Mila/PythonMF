import AVFAudio
import Combine
import Foundation
import SwiftUI
import UserNotifications

@MainActor final class CaminoViewModel: ObservableObject {
    @Published private(set) var trips: [LocalTrip] = []
    @Published private(set) var activeTrip: LocalTrip?
    @Published private(set) var moments: [LocalMoment] = []
    @Published private(set) var newPrivacy: LocalPrivacy = .diary
    @Published private(set) var pendingAudioCount = 0
    @Published private(set) var unmatchedAudioCount = 0
    @Published private(set) var message: String?
    @Published private(set) var startupError: String?
    @Published var showAudio = false
    @Published private(set) var selectedAudioKind: RecordingKind = .comment
    @Published private(set) var selectedAudioPrivacy: LocalPrivacy = .diary
    @Published private(set) var launchingAudio = false
    @Published private(set) var audioUpdate = 0

    private let local: CaminoLocalStore?
    private let recording: IntentRecordingStore?
    let audio: AudioController?
    private var subscriptions = Set<AnyCancellable>()
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid
    private var wasFinishing = false
    private var lastLinkedClipCount = -1

    init() {
        do {
            var root = try FileManager.default.url(for: .applicationSupportDirectory,
                in: .userDomainMask, appropriateFor: nil, create: true)
                .appendingPathComponent("Camino", isDirectory: true)
            #if DEBUG && targetEnvironment(simulator)
            if let value = ProcessInfo.processInfo.environment["CAMINO_UI_TEST_SESSION"],
               let session = UUID(uuidString: value) {
                root = root.deletingLastPathComponent()
                    .appendingPathComponent("CaminoUITests", isDirectory: true)
                    .appendingPathComponent(session.uuidString, isDirectory: true)
            }
            #endif
            let local = try CaminoLocalStore(storeURL: root.appendingPathComponent("metadata.sqlite"))
            let media = try RecordingStore(root: root.appendingPathComponent("Audio", isDirectory: true),
                                           inspect: AudioFileInspector.inspect)
            let recording = IntentRecordingStore(media: media, metadata: local)
            let driver = IOSAudioDriver()
            let audio = AudioController(driver: driver, store: recording)
            self.local = local
            self.recording = recording
            self.audio = audio
            startupError = nil
            driver.event = { [weak audio] in audio?.interrupt(reason: "Zvukový vstup se zastavil") }
            audio.changed = { [weak self] in self?.audioChanged() }
            Timer.publish(every: 0.15, on: .main, in: .common).autoconnect()
                .sink { [weak self] _ in self?.audio?.tick() }
                .store(in: &subscriptions)
            observe(AVAudioSession.interruptionNotification) { [weak self] in
                self?.interruption($0)
            }
            observe(AVAudioSession.routeChangeNotification) { [weak audio] _ in
                audio?.routeChanged()
            }
            observe(AVAudioSession.mediaServicesWereLostNotification) { [weak audio] _ in
                audio?.interrupt(reason: "Zvuková služba není dostupná")
            }
            observe(AVAudioSession.mediaServicesWereResetNotification) { [weak audio] _ in
                audio?.interrupt(reason: "Zvuková služba byla obnovena")
            }
            refresh()
            reconcileAudio()
        } catch {
            local = nil
            recording = nil
            audio = nil
            startupError = "Místní úložiště nelze bezpečně otevřít. Žádná data se nemažou."
        }
    }

    var audioBusy: Bool {
        guard let audio else { return false }
        return launchingAudio || [.permission, .preparing, .recording, .finishing,
                                  .interrupted].contains(audio.phase)
    }

    var canLeaveAudio: Bool {
        guard let audio else { return true }
        return !launchingAudio && (audio.phase == .idle || audio.phase == .failed)
    }

    var todayMoments: [LocalMoment] {
        let today = CaptureStamp.record(Date(), timeZone: .current).chapterDate
        return moments.filter { $0.capture.chapterDate == today }
    }

    func createTrip(name: String, isTest: Bool = false) {
        guard !audioBusy, let local else { return }
        do {
            _ = try local.createTrip(name: name, isTest: isTest)
            message = nil
            refresh()
        } catch { message = error.localizedDescription }
    }

    func selectTrip(_ id: UUID) {
        guard !audioBusy, let local else { return }
        do { try local.selectTrip(id); message = nil; refresh() }
        catch { message = error.localizedDescription }
    }

    func setNewPrivacy(_ value: LocalPrivacy) {
        guard !audioBusy, let local else { return }
        do { try local.setNewMomentPrivacy(value); message = nil; refresh() }
        catch { message = error.localizedDescription; refresh() }
    }

    func markMoment() {
        guard !audioBusy, let local else { return }
        do {
            _ = try local.markMoment()
            message = "Okamžik označen. Uloženo v telefonu."
            refresh()
        } catch { message = error.localizedDescription }
    }

    func startAudio(_ kind: RecordingKind) {
        guard !audioBusy, activeTrip != nil, let audio, !showAudio else { return }
        selectedAudioKind = kind
        selectedAudioPrivacy = kind == .reflection ? .ownerOnly : newPrivacy
        message = nil
        showAudio = true
        launchingAudio = true
        Task {
            await audio.start(kind: kind)
            launchingAudio = false
            audioChanged()
        }
    }

    func startAgainAfterPermission() {
        guard !audioBusy, let audio, showAudio else { return }
        launchingAudio = true
        Task {
            await audio.start(kind: selectedAudioKind)
            launchingAudio = false
            audioChanged()
        }
    }

    func stopAudio() { guard let audio else { return }; Task { await audio.stop() } }
    func setCurrentAudioPrivacy(_ privacy: LocalPrivacy) {
        guard selectedAudioKind == .comment, audio?.phase == .recording,
              let recording else { return }
        do {
            try recording.setCurrentPrivacy(privacy)
            selectedAudioPrivacy = privacy
            message = nil
        } catch { message = error.localizedDescription }
    }
    func continueAudio() { guard let audio else { return }; Task { await audio.continueRecording() } }
    func endInterruptedAudio() { audio?.endInterruptedSession() }
    func play(_ clip: RecordingClip) { audio?.play(clip) }
    func stopPlayback() { audio?.stopPlayback() }
    func leaveAudio() { if canLeaveAudio { showAudio = false; refresh() } }

    func scenePhaseChanged(_ phase: ScenePhase) {
        if phase == .active {
            audio?.enterForeground()
            if audioBusy { showAudio = true }
            reconcileAudio()
            refresh()
        } else {
            audio?.leaveForeground()
        }
    }

    private func observe(_ name: Notification.Name,
                         action: @escaping @MainActor (Notification) -> Void) {
        NotificationCenter.default.publisher(for: name).receive(on: RunLoop.main)
            .sink { notification in action(notification) }
            .store(in: &subscriptions)
    }

    private func interruption(_ notification: Notification) {
        let value = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt
        if value == AVAudioSession.InterruptionType.began.rawValue { audio?.interrupt() }
        else if value == AVAudioSession.InterruptionType.ended.rawValue {
            audio?.interruptionEnded()
        }
    }

    private func audioChanged() {
        guard let audio else { return }
        if audio.phase == .finishing && !wasFinishing {
            backgroundTask = UIApplication.shared.beginBackgroundTask(withName: "Finish Camino audio") {
                [weak self] in Task { @MainActor in self?.endBackgroundTask() }
            }
            if audio.isFinishingInterrupted { notifyInterruptionIfAllowed() }
        } else if audio.phase != .finishing { endBackgroundTask() }
        wasFinishing = audio.phase == .finishing
        audioUpdate += 1
        if audio.phase == .idle || audio.phase == .interrupted || audio.phase == .failed {
            let count = audio.library.clips.count
            if count != lastLinkedClipCount { reconcileAudio() }
        }
    }

    private func endBackgroundTask() {
        guard backgroundTask != .invalid else { return }
        UIApplication.shared.endBackgroundTask(backgroundTask)
        backgroundTask = .invalid
    }

    private func notifyInterruptionIfAllowed() {
        Task {
            let center = UNUserNotificationCenter.current()
            let settings = await center.notificationSettings()
            guard settings.authorizationStatus == .authorized ||
                  settings.authorizationStatus == .provisional else { return }
            let content = UNMutableNotificationContent()
            content.title = "Nahrávání přerušeno"
            content.body = "Otevři Camino a zkontroluj zachovaný záznam."
            try? await center.add(UNNotificationRequest(identifier: "camino-interrupted",
                content: content, trigger: nil))
        }
    }

    /// Audio library validates the completed files. Missing metadata is surfaced
    /// for review; a new identity or privacy is never guessed after a crash.
    private func reconcileAudio() {
        guard let recording, let local else { return }
        do {
            let library = try recording.library()
            var unmatched = 0
            for session in library.sessions {
                guard let first = session.parts.first else { continue }
                let kind: LocalMomentKind = first.draft.kind == .reflection ? .reflection : .comment
                let partial = session.parts.contains {
                    $0.recovery != nil ||
                    ($0.segments?.contains(where: { $0.discontinuityBefore }) ?? false)
                }
                do {
                    _ = try local.acceptCompletedAudio(sessionID: session.id,
                                                       kind: kind, partial: partial)
                } catch { unmatched += 1 }
            }
            unmatchedAudioCount = unmatched + library.unfinishedCount
            pendingAudioCount = try local.pendingAudioIntents().count
            lastLinkedClipCount = unmatched == 0 ? library.clips.count : -1
            refresh()
        } catch {
            message = "Nahrávky teď nelze ověřit. Soubory se nemažou."
        }
    }

    private func refresh() {
        guard let local else { return }
        do {
            trips = try local.trips()
            activeTrip = try local.activeTrip()
            newPrivacy = try local.newMomentPrivacy()
            moments = try activeTrip.map { try local.moments(tripID: $0.id) } ?? []
            pendingAudioCount = try local.pendingAudioIntents().count
        } catch {
            message = "Místní evidenci nelze načíst. Žádná data se nemažou."
            moments = []
        }
    }
}
