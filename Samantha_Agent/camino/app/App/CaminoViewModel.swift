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
    @Published private(set) var audioTargetMomentID: UUID?
    @Published private(set) var launchingAudio = false
    @Published private(set) var audioUpdate = 0
    @Published var showCamera = false
    @Published private(set) var selectedMediaKind: LocalMediaKind = .photo
    @Published private(set) var cameraTargetMomentID: UUID?
    @Published private(set) var mediaByMoment: [UUID: [LocalMediaAsset]] = [:]
    @Published private(set) var mediaRecovery = LocalMediaRecovery(
        repairedCount: 0, pendingCount: 0, orphanCount: 0, missingCount: 0)
    @Published private(set) var cameraError: String?
    @Published var momentDetail: LocalMoment?

    private let local: CaminoLocalStore?
    private let recording: IntentRecordingStore?
    private let mediaVault: CaminoMediaVault?
    private var activeVideoIntent: LocalMediaIntent?
    private var pendingCommentTargetID: UUID?
    let audio: AudioController?
    private var subscriptions = Set<AnyCancellable>()
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid
    private var videoBackgroundTask: UIBackgroundTaskIdentifier = .invalid
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
            let vault = try? CaminoMediaVault(root: root, metadata: local)
            let driver = IOSAudioDriver()
            let audio = AudioController(driver: driver, store: recording)
            self.local = local
            self.recording = recording
            self.mediaVault = vault
            self.audio = audio
            startupError = nil
            cameraError = vault == nil ? "Místní úložiště fotek a videí není dostupné." : nil
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
            Task { await reconcileMedia() }
        } catch {
            local = nil
            recording = nil
            mediaVault = nil
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
        guard !audioBusy, !showCamera, let local else { return }
        do {
            _ = try local.createTrip(name: name, isTest: isTest)
            message = nil
            refresh()
        } catch { message = error.localizedDescription }
    }

    func selectTrip(_ id: UUID) {
        guard !audioBusy, !showCamera, let local else { return }
        do { try local.selectTrip(id); message = nil; refresh() }
        catch { message = error.localizedDescription }
    }

    func setNewPrivacy(_ value: LocalPrivacy) {
        guard !audioBusy, !showCamera, let local else { return }
        do { try local.setNewMomentPrivacy(value); message = nil; refresh() }
        catch { message = error.localizedDescription; refresh() }
    }

    func markMoment() {
        guard !audioBusy, !showCamera, let local else { return }
        do {
            _ = try local.markMoment()
            message = "Okamžik označen. Uloženo v telefonu."
            refresh()
        } catch { message = error.localizedDescription }
    }

    func startAudio(_ kind: RecordingKind, targetMomentID: UUID? = nil) {
        guard !audioBusy, !showCamera, activeTrip != nil, let audio, !showAudio else { return }
        let target = targetMomentID.flatMap { id in moments.first { $0.id == id } }
        guard targetMomentID == nil || (kind == .comment && target != nil) else {
            message = LocalStoreError.invalidAudioIntent.localizedDescription
            return
        }
        audio.stopPlayback()
        audioTargetMomentID = targetMomentID
        recording?.targetMomentID = targetMomentID
        selectedAudioKind = kind
        selectedAudioPrivacy = target?.privacy ?? (kind == .reflection ? .ownerOnly : newPrivacy)
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
        guard selectedAudioKind == .comment, audioTargetMomentID == nil,
              audio?.phase == .recording,
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
            if !showCamera { Task { await reconcileMedia() } }
            refresh()
        } else {
            if activeVideoIntent != nil && videoBackgroundTask == .invalid {
                videoBackgroundTask = UIApplication.shared.beginBackgroundTask(
                    withName: "Finish Camino video") { [weak self] in
                    Task { @MainActor in self?.endVideoBackgroundTask() }
                }
            }
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

    private func endVideoBackgroundTask() {
        guard videoBackgroundTask != .invalid else { return }
        UIApplication.shared.endBackgroundTask(videoBackgroundTask)
        videoBackgroundTask = .invalid
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
            mediaByMoment = try Dictionary(uniqueKeysWithValues:
                moments.map { ($0.id, try local.mediaAssets(momentID: $0.id)) })
            pendingAudioCount = try local.pendingAudioIntents().count
        } catch {
            message = "Místní evidenci nelze načíst. Žádná data se nemažou."
            moments = []
        }
    }

    func openCamera(_ kind: LocalMediaKind, targetMomentID: UUID? = nil) {
        guard !audioBusy, !showAudio, !showCamera, mediaVault != nil,
              activeTrip != nil else {
            message = cameraError ?? "Kamera teď není dostupná."
            return
        }
        if let targetMomentID, !moments.contains(where: { $0.id == targetMomentID }) {
            message = LocalStoreError.momentMissing.localizedDescription
            return
        }
        audio?.stopPlayback()
        selectedMediaKind = kind
        cameraTargetMomentID = targetMomentID
        message = nil
        showCamera = true
    }

    func closeCamera() {
        showCamera = false
        cameraTargetMomentID = nil
        refresh()
    }

    func requestCommentFromCamera(momentID: UUID) {
        pendingCommentTargetID = momentID
        closeCamera()
    }

    func requestCommentFromDetail(momentID: UUID) {
        pendingCommentTargetID = momentID
        momentDetail = nil
    }

    func startPendingComment() {
        guard let target = pendingCommentTargetID else { return }
        pendingCommentTargetID = nil
        startAudio(.comment, targetMomentID: target)
    }

    func audioSessionIDs(for momentID: UUID) -> Set<UUID> {
        Set((try? local?.audioSessionIDs(momentID: momentID)) ?? [])
    }

    @discardableResult func savePhoto(_ data: Data) async -> LocalMediaAsset? {
        guard let mediaVault, showCamera else { return nil }
        do {
            let asset = try await mediaVault.savePhoto(data,
                targetMomentID: cameraTargetMomentID)
            message = "Fotografie uložena v telefonu. Mac zatím neověřen."
            refresh()
            await reconcileMedia()
            return asset
        } catch {
            message = "Fotografii nelze potvrdit jako uloženou. Dostupný soubor zůstal zachovaný."
            await reconcileMedia()
            return nil
        }
    }

    func beginVideo(silent: Bool) -> URL? {
        guard let mediaVault, showCamera, activeVideoIntent == nil else { return nil }
        do {
            let (intent, pendingURL, warning) = try mediaVault.beginVideo(
                targetMomentID: cameraTargetMomentID, silent: silent)
            activeVideoIntent = intent
            message = warning ? "Volné místo kleslo pod 2 GiB. Video včas ukonči." : nil
            return pendingURL
        } catch {
            message = error.localizedDescription
            return nil
        }
    }

    @discardableResult func finalizeVideo(at url: URL, interrupted: Bool) async -> LocalMediaAsset? {
        guard let mediaVault, let intent = activeVideoIntent,
              url.lastPathComponent == URL(fileURLWithPath: intent.pendingRelativePath).lastPathComponent else {
            endVideoBackgroundTask()
            message = "Vazbu videa nelze ověřit. Dostupný soubor zůstal zachovaný."
            return nil
        }
        activeVideoIntent = nil
        defer { endVideoBackgroundTask() }
        do {
            let asset = try await mediaVault.finalize(intent, interrupted: interrupted)
            message = asset.inspection.partial
                ? "Částečné video uloženo v telefonu; konec nebo zvuk může chybět."
                : "Video uloženo v telefonu. Mac zatím neověřen."
            refresh()
            await reconcileMedia()
            return asset
        } catch {
            message = "Video nelze potvrdit jako uložené. Dostupný soubor zůstal zachovaný."
            await reconcileMedia()
            return nil
        }
    }

    func originalURL(for asset: LocalMediaAsset) -> URL? {
        try? mediaVault?.originalURL(for: asset)
    }

    func stopVideoForLowSpace() -> Bool {
        guard let mediaVault else { return true }
        guard let available = try? mediaVault.availableBytes(),
              available >= 536_870_912 else {
            message = "Volné místo kleslo k bezpečnostní rezervě. Ukončuji video; nic se nemaže."
            return true
        }
        if available < 2_147_483_648 {
            message = "Volné místo je pod 2 GiB. Video včas ukonči."
        }
        return false
    }

    private func reconcileMedia() async {
        guard let mediaVault else { return }
        do {
            mediaRecovery = try await mediaVault.reconcile()
            refresh()
        } catch {
            cameraError = "Místní média nelze teď úplně ověřit; soubory se nemažou."
        }
    }
}
