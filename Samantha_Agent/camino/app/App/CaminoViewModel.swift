import AVFAudio
import Combine
import CoreLocation
import Foundation
import PhotosUI
import SwiftUI
import UserNotifications

#if DEBUG && targetEnvironment(simulator)
private struct CaminoSimulatedCapacityProvider: CaminoStorageCapacityProviding {
    let bytes: Int64
    func availableBytes() throws -> Int64 { bytes }
}
#endif

@MainActor final class CaminoViewModel: ObservableObject {
    let location = CaminoLocationProvider()
    @Published private(set) var trips: [LocalTrip] = []
    @Published private(set) var activeTrip: LocalTrip?
    @Published private(set) var moments: [LocalMoment] = []
    @Published private(set) var hiddenMoments: [LocalMoment] = []
    @Published private(set) var textByMoment: [UUID: LocalTextHistory] = [:]
    @Published private(set) var pendingServerMomentIDs: Set<UUID> = []
    @Published private(set) var newPrivacy: LocalPrivacy = .diary
    @Published private(set) var pendingAudioCount = 0
    @Published private(set) var unmatchedAudioCount = 0
    @Published private(set) var message: String?
    @Published private(set) var startupError: String?
    @Published var showAudio = false
    @Published private(set) var selectedAudioKind: RecordingKind = .comment
    @Published private(set) var selectedAudioPrivacy: LocalPrivacy = .diary
    @Published private(set) var audioTargetMomentID: UUID?
    @Published private(set) var audioRelatedMomentID: UUID?
    @Published private(set) var launchingAudio = false
    @Published private(set) var audioUpdate = 0
    @Published var showCamera = false
    @Published private(set) var selectedMediaKind: LocalMediaKind = .photo
    @Published private(set) var cameraTargetMomentID: UUID?
    @Published private(set) var mediaByMoment: [UUID: [LocalMediaAsset]] = [:]
    @Published private(set) var mediaRecovery = LocalMediaRecovery(
        repairedCount: 0, pendingCount: 0, orphanCount: 0, missingCount: 0)
    @Published private(set) var cameraError: String?
    @Published private(set) var awaitingLocation = false
    @Published private(set) var importingMedia = false
    @Published private(set) var canCancelLibraryLoad = false
    private var libraryLoadID: UUID?
    private var libraryLoadProgress: Progress?
    private var libraryLoadContinuation: CheckedContinuation<CaminoPickedFile?, Error>?
    @Published var momentDetail: LocalMoment?

    private let local: CaminoLocalStore?
    private let recording: IntentRecordingStore?
    private let mediaVault: CaminoMediaVault?
    let sync: CaminoSyncCoordinator?
    private var activeVideoIntent: LocalMediaIntent?
    private var pendingCommentTargetID: UUID?
    private var pendingAddendumTargetID: UUID?
    let audio: AudioController?
    private var subscriptions = Set<AnyCancellable>()
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid
    private var videoBackgroundTask: UIBackgroundTaskIdentifier = .invalid
    private var wasFinishing = false
    private var lastLinkedClipCount = -1
    private let thermalPolicy = CaminoThermalSafetyPolicy()
    private var thermalLevel: CaminoThermalLevel = .nominal
    private var simulatedThermalLevel: CaminoThermalLevel?

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
            var capacityProvider: (any CaminoStorageCapacityProviding)?
            #if DEBUG && targetEnvironment(simulator)
            if let raw = ProcessInfo.processInfo.environment["CAMINO_TEST_AVAILABLE_BYTES"],
               let bytes = Int64(raw), bytes >= 0 {
                capacityProvider = CaminoSimulatedCapacityProvider(bytes: bytes)
            }
            simulatedThermalLevel = Self.parseSimulatedThermalLevel(
                ProcessInfo.processInfo.environment["CAMINO_TEST_THERMAL_LEVEL"])
            #endif
            let vault = try? CaminoMediaVault(root: root, metadata: local,
                                              capacityProvider: capacityProvider)
            #if DEBUG && targetEnvironment(simulator)
            if ProcessInfo.processInfo.environment["CAMINO_TEST_ATTACHMENTS"] == "1",
               UUID(uuidString: ProcessInfo.processInfo.environment["CAMINO_UI_TEST_SESSION"] ?? "") != nil,
               try local.trips().isEmpty {
                try Self.seedAttachmentUITest(local: local, recording: recording)
            }
            #endif
            let driver = IOSAudioDriver()
            let audio = AudioController(driver: driver, store: recording)
            self.local = local
            self.recording = recording
            self.mediaVault = vault
            self.audio = audio
            self.sync = try? CaminoSyncCoordinator(local: local, recording: recording, root: root)
            recording.locationAtCapture = { [weak location] date in location?.snapshot(at: date) }
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
            observe(ProcessInfo.thermalStateDidChangeNotification) { [weak self] _ in
                self?.thermalStateChanged()
            }
            thermalStateChanged()
            Timer.publish(every: 5, on: .main, in: .common).autoconnect()
                .sink { [weak self] _ in self?.monitorActiveAudioSafety() }
                .store(in: &subscriptions)
            refresh()
            reconcileAudio()
            Task { await reconcileMedia() }
        } catch {
            local = nil
            recording = nil
            mediaVault = nil
            audio = nil
            sync = nil
            startupError = "Místní úložiště nelze bezpečně otevřít. Žádná data se nemažou."
        }
    }

    #if DEBUG && targetEnvironment(simulator)
    private static func seedAttachmentUITest(local: CaminoLocalStore, recording: IntentRecordingStore) throws {
        _ = try local.createTrip(name: "Synthetic attachments", isTest: true)
        let old = try local.markMoment(at: Date().addingTimeInterval(-120))
        _ = try local.setTitle(momentID: old.id, title: "Older moment")
        let current = try local.markMoment()
        _ = try local.setTitle(momentID: current.id, title: "Newer moment")
        // Deliberately missing photo bytes: this fixture tests metadata controls,
        // including a retained name when the original is unavailable, not capture.
        let photo = try local.beginMediaIntent(kind: .photo, targetMomentID: current.id)
        _ = try local.acceptMedia(photo, inspection: LocalMediaInspection(byteCount: 12,
            sha256: String(repeating: "a", count: 64), width: 4, height: 3, orientation: 1,
            durationMilliseconds: nil, hasAudio: false, partial: false))
        recording.targetMomentID = current.id
        let draft = try recording.begin(kind: .comment, continuation: nil)
        let format = AVAudioFormat(standardFormatWithSampleRate: 16000, channels: 1)!
        let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 16000)!
        buffer.frameLength = 16000
        buffer.floatChannelData![0].initialize(repeating: 0, count: 16000)
        do {
            let file = try AVAudioFile(forWriting: recording.url(for: draft), settings: format.settings)
            try file.write(from: buffer)
        }
        _ = try recording.finish(draft, interrupted: false)
        _ = try local.acceptCompletedAudio(sessionID: draft.sessionID, kind: .comment, partial: false)
        recording.targetMomentID = nil
    }
    #endif

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
        return moments.filter { $0.chapterDate == today }
            .sorted(by: LocalMoment.newestFirst)
    }

    var allMoments: [LocalMoment] { moments + hiddenMoments }

    func moments(on chapterDate: String) -> [LocalMoment] {
        moments.filter { $0.chapterDate == chapterDate }
            .sorted(by: LocalMoment.newestFirst)
    }

    func moment(with id: UUID) -> LocalMoment? {
        allMoments.first { $0.id == id }
    }

    func textHistory(for momentID: UUID) -> LocalTextHistory {
        textByMoment[momentID] ?? LocalTextHistory()
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

    func updateTrip(_ id: UUID, name: String, isTest: Bool) -> Bool {
        guard !audioBusy, !showCamera, let local else { return false }
        do {
            _ = try local.updateTrip(id, name: name, isTest: isTest)
            message = nil
            refresh()
            return true
        } catch { message = error.localizedDescription; return false }
    }

    func setNewPrivacy(_ value: LocalPrivacy) {
        guard !audioBusy, !showCamera, let local else { return }
        do { try local.setNewMomentPrivacy(value); message = nil; refresh() }
        catch { message = error.localizedDescription; refresh() }
    }

    func markMoment() {
        guard !audioBusy, !showCamera, !awaitingLocation, local != nil else { return }
        awaitingLocation = true
        message = "Ověřuji GPS…"
        Task { [weak self] in
            guard let self else { return }
            let (fix, gpsWarning) = await self.captureLocationForNewMoment()
            self.awaitingLocation = false
            guard let local = self.local else { return }
            let warning = self.storageMessage(for: .text)
            do {
                let moment = try local.markMoment(at: Date(), location: fix)
                let saved = moment.location == nil
                    ? "Okamžik označen. Uloženo v telefonu bez GPS."
                    : "Okamžik označen včetně GPS. Uloženo v telefonu."
                self.message = Self.joinMessages(gpsWarning, warning, saved)
                self.refresh()
            } catch { self.message = error.localizedDescription }
        }
    }

    func startAudio(_ kind: RecordingKind, targetMomentID: UUID? = nil,
                    relatedMomentID: UUID? = nil) {
        guard !audioBusy, !showCamera, activeTrip != nil, audio != nil, !showAudio,
              !awaitingLocation else { return }
        let safety = storageAction(for: .audio)
        guard safety != .block else {
            message = blockedStorageMessage(for: .audio)
            return
        }
        let target = targetMomentID.flatMap { id in moments.first { $0.id == id } }
        let related = relatedMomentID.flatMap { id in moments.first { $0.id == id } }
        guard (targetMomentID == nil || (kind == .comment && target != nil)),
              (relatedMomentID == nil || (kind == .reflection && related != nil)),
              targetMomentID == nil || relatedMomentID == nil else {
            message = LocalStoreError.invalidAudioIntent.localizedDescription
            return
        }
        if targetMomentID == nil {
            awaitingLocation = true
            message = "Ověřuji GPS…"
            Task { [weak self] in
                guard let self else { return }
                let (_, gpsWarning) = await self.captureLocationForNewMoment()
                self.awaitingLocation = false
                self.startAudioNow(kind, targetMomentID: targetMomentID,
                                   relatedMomentID: relatedMomentID,
                                   storageWarning: safety == .warn ? self.warningStorageMessage(for: .audio) : nil,
                                   gpsWarning: gpsWarning)
            }
            return
        }
        startAudioNow(kind, targetMomentID: targetMomentID, relatedMomentID: relatedMomentID,
                      storageWarning: safety == .warn ? warningStorageMessage(for: .audio) : nil,
                      gpsWarning: nil)
    }

    private func startAudioNow(_ kind: RecordingKind, targetMomentID: UUID?,
                               relatedMomentID: UUID?, storageWarning: String?,
                               gpsWarning: String?) {
        guard let audio, !audioBusy, !showCamera, !showAudio else { return }
        let target = targetMomentID.flatMap { id in moments.first { $0.id == id } }
        audio.stopPlayback()
        audioTargetMomentID = targetMomentID
        audioRelatedMomentID = relatedMomentID
        recording?.targetMomentID = targetMomentID
        recording?.relatedMomentID = relatedMomentID
        selectedAudioKind = kind
        selectedAudioPrivacy = target?.privacy ?? (kind == .reflection ? .ownerOnly : newPrivacy)
        message = Self.joinMessages(gpsWarning, storageWarning)
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
        let safety = storageAction(for: .audio)
        guard safety != .block else {
            message = blockedStorageMessage(for: .audio)
            return
        }
        if safety == .warn { message = warningStorageMessage(for: .audio) }
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
        location.setForeground(phase == .active)
        if phase == .active {
            audio?.enterForeground()
            if audioBusy { showAudio = true }
            reconcileAudio()
            if !showCamera && !importingMedia { Task { await reconcileMedia() } }
            refresh()
            sync?.applicationBecameActive()
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

    private var thermalWarningMessage: String {
        "Telefon hlásí vysokou teplotu. Kvalita videa se skrytě nemění; záznam včas ukonči."
    }

    private func storageAction(for activity: CaminoStorageActivity,
                               active: Bool = false) -> CaminoSafetyAction {
        guard let mediaVault else { return active ? .finish : .block }
        do { return try mediaVault.storageAction(for: activity, active: active) }
        catch {
            if active { return .finish }
            return activity == .text ? .warn : .block
        }
    }

    private func warningStorageMessage(for activity: CaminoStorageActivity) -> String {
        switch activity {
        case .text:
            "Volné místo je pod 2 GiB. Krátký zápis zkusím uložit; nic se nemaže."
        case .photo:
            "Volné místo je pod 2 GiB. Fotografie může selhat; nic se nemaže."
        case .audio:
            "Volné místo je pod 2 GiB. Audio včas ukonči; nic se nemaže."
        case .video:
            "Volné místo je pod 2 GiB. Video včas ukonči; nic se nemaže."
        }
    }

    private func blockedStorageMessage(for activity: CaminoStorageActivity) -> String {
        switch activity {
        case .text:
            "Místní zápis teď nelze bezpečně potvrdit. Nic se nemaže."
        case .photo:
            "Pro fotografii není dost bezpečného volného místa. Nic se nemaže."
        case .audio:
            "Pro audio není dost bezpečného volného místa. Nahrávání nezačalo a nic se nemaže."
        case .video:
            "Pro video není dost bezpečného volného místa. Nahrávání nezačalo a nic se nemaže."
        }
    }

    private func storageMessage(for activity: CaminoStorageActivity) -> String? {
        switch storageAction(for: activity) {
        case .warn:
            warningStorageMessage(for: activity)
        case .block:
            blockedStorageMessage(for: activity)
        case .allow, .finish:
            nil
        }
    }

    private func monitorActiveAudioSafety() {
        guard let audio, audio.phase == .recording || audio.phase == .preparing else { return }
        let action = storageAction(for: .audio, active: true)
        if action == .finish {
            message = "Volné místo kleslo k bezpečnostní rezervě. Ukončuji audio; nic se nemaže."
            Task { await audio.stop() }
        } else if action == .warn {
            message = warningStorageMessage(for: .audio)
        }
    }

    private func thermalStateChanged() {
        thermalLevel = simulatedThermalLevel ?? Self.thermalLevel(
            from: ProcessInfo.processInfo.thermalState)
        switch thermalPolicy.videoAction(for: thermalLevel) {
        case .warn:
            message = thermalWarningMessage
        case .block:
            message = "Telefon hlásí kritickou teplotu. Nové video nezačínej."
        case .allow, .finish:
            break
        }
    }

    private func captureLocationForNewMoment() async -> (LocalLocationFix?, String?) {
        let fix = await location.snapshotForCapture()
        guard fix == nil else { return (fix, nil) }
        let warning: String
        switch location.authorization {
        case .denied, .restricted:
            warning = "GPS není povolená. Ukládám bez GPS."
        case .notDetermined:
            warning = "GPS není zapnutá. Ukládám bez GPS."
        default:
            warning = "GPS se během 5 s nepodařilo získat. Ukládám bez GPS."
        }
        return (nil, warning)
    }

    private static func joinMessages(_ messages: String?...) -> String? {
        let values = messages.compactMap { $0 }.filter { !$0.isEmpty }
        return values.isEmpty ? nil : values.joined(separator: " ")
    }

    private static func thermalLevel(from state: ProcessInfo.ThermalState) -> CaminoThermalLevel {
        switch state {
        case .nominal: .nominal
        case .fair: .fair
        case .serious: .serious
        case .critical: .critical
        @unknown default: .critical
        }
    }

    #if DEBUG && targetEnvironment(simulator)
    private static func parseSimulatedThermalLevel(_ raw: String?) -> CaminoThermalLevel? {
        switch raw?.lowercased() {
        case "nominal": .nominal
        case "fair": .fair
        case "serious": .serious
        case "critical": .critical
        default: nil
        }
    }
    #endif

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
            let all = try activeTrip.map {
                try local.moments(tripID: $0.id, includeHidden: true)
            } ?? []
            moments = all.filter { !$0.hidden }
            hiddenMoments = all.filter(\.hidden)
            mediaByMoment = try Dictionary(uniqueKeysWithValues:
                all.map { ($0.id, try local.mediaAssets(momentID: $0.id)) })
            textByMoment = try Dictionary(uniqueKeysWithValues:
                all.map { ($0.id, try local.textHistory(momentID: $0.id)) })
            pendingServerMomentIDs = Set(try all.compactMap {
                try local.pendingOperations(momentID: $0.id).isEmpty ? nil : $0.id
            })
            if let selected = momentDetail,
               let current = all.first(where: { $0.id == selected.id }) {
                momentDetail = current
            }
            pendingAudioCount = try local.pendingAudioIntents().count
        } catch {
            message = "Místní evidenci nelze načíst. Žádná data se nemažou."
            moments = []
            hiddenMoments = []
            textByMoment = [:]
            pendingServerMomentIDs = []
        }
    }

    func openCamera(_ kind: LocalMediaKind, targetMomentID: UUID? = nil) {
        location.refresh()
        guard !audioBusy, !showAudio, !showCamera, mediaVault != nil,
              activeTrip != nil else {
            message = cameraError ?? "Kamera teď není dostupná."
            return
        }
        let activity: CaminoStorageActivity = kind == .video ? .video : .photo
        let storage = storageAction(for: activity)
        guard storage != .block else {
            message = blockedStorageMessage(for: activity)
            return
        }
        if kind == .video && thermalPolicy.videoAction(for: thermalLevel) == .block {
            message = "Telefon hlásí kritickou teplotu. Video nezačalo a kvalita se skrytě nemění."
            return
        }
        if let targetMomentID, !moments.contains(where: { $0.id == targetMomentID }) {
            message = LocalStoreError.momentMissing.localizedDescription
            return
        }
        audio?.stopPlayback()
        selectedMediaKind = kind
        cameraTargetMomentID = targetMomentID
        message = storage == .warn ? warningStorageMessage(for: activity) : nil
        if kind == .video && thermalPolicy.videoAction(for: thermalLevel) == .warn {
            message = thermalWarningMessage
        }
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

    func requestPrivateAddendumFromDetail(momentID: UUID) {
        pendingAddendumTargetID = momentID
        momentDetail = nil
    }

    func startPendingComment() {
        guard let target = pendingCommentTargetID else { return }
        pendingCommentTargetID = nil
        startAudio(.comment, targetMomentID: target)
    }

    func startPendingAudioFromDetail() {
        if let target = pendingCommentTargetID {
            pendingCommentTargetID = nil
            startAudio(.comment, targetMomentID: target)
        } else if let target = pendingAddendumTargetID {
            pendingAddendumTargetID = nil
            startAudio(.reflection, relatedMomentID: target)
        }
    }

    func attachmentSummary(for momentID: UUID) -> String {
        let assets = mediaByMoment[momentID] ?? []
        let photos = assets.filter { $0.kind == .photo }.count
        let videos = assets.filter { $0.kind == .video }.count
        let comments = audioSessionIDs(for: momentID).count
        return [(photos, "Foto"), (videos, "Video"), (comments, "Audio")]
            .filter { $0.0 > 0 }.map { "\($0.1): \($0.0)" }.joined(separator: " · ")
    }

    func saveTitle(momentID: UUID, title: String,
                   attachment: LocalAttachmentTitle? = nil) async -> Bool {
        guard let local, let before = moment(with: momentID) else { return false }
        do {
            let updated = try await local.setTitleInBackground(
                momentID: momentID, title: title, attachment: attachment)
            applyTitleUpdate(updated, previousRevision: before.revision)
            return true
        } catch {
            message = error.localizedDescription
            return false
        }
    }

    private func applyTitleUpdate(_ updated: LocalMoment, previousRevision: Int) {
        if let index = moments.firstIndex(where: { $0.id == updated.id }) {
            moments[index] = updated
        }
        if let index = hiddenMoments.firstIndex(where: { $0.id == updated.id }) {
            hiddenMoments[index] = updated
        }
        if momentDetail?.id == updated.id {
            momentDetail = updated
        }
        if updated.revision > previousRevision {
            pendingServerMomentIDs.insert(updated.id)
        }
        message = nil
    }

    func saveTextDraft(momentID: UUID, content: String) {
        guard let local else { return }
        do {
            try local.saveTextDraft(momentID: momentID, content: content)
            textByMoment[momentID] = try local.textHistory(momentID: momentID)
        } catch { message = error.localizedDescription }
    }

    func discardTextDraft(momentID: UUID) {
        guard let local else { return }
        do {
            try local.discardTextDraft(momentID: momentID)
            message = nil
            refresh()
        } catch { message = error.localizedDescription }
    }

    @discardableResult func commitTextDraft(momentID: UUID) -> Bool {
        guard let local else { return false }
        guard storageAction(for: .text) != .block else {
            message = blockedStorageMessage(for: .text)
            return false
        }
        do {
            _ = try local.commitTextDraft(momentID: momentID)
            message = storageMessage(for: .text) ?? "Textová revize uložena v telefonu."
            refresh()
            return true
        } catch {
            message = error.localizedDescription
            refresh()
            return false
        }
    }

    func changePrivacy(momentID: UUID, to privacy: LocalPrivacy) {
        guard !audioBusy, !showCamera, let local,
              let moment = moment(with: momentID) else { return }
        let action: LocalPrivacyAction = privacy == .ownerOnly ? .lock
            : moment.kind == .reflection ? .insertReflectionIntoDiary : .unlock
        do {
            _ = try local.changePrivacy(momentID: momentID, to: privacy, action: action)
            message = privacy == .ownerOnly
                ? "Jen pro mě nastaveno v telefonu · čeká na server."
                : "Do deníku nastaveno v telefonu · čeká na server."
            refresh()
        } catch { message = error.localizedDescription; refresh() }
    }

    func setHidden(momentID: UUID, hidden: Bool) {
        guard !audioBusy, !showCamera, let local else { return }
        do {
            _ = try local.setHidden(momentID: momentID, hidden: hidden)
            message = hidden
                ? "Moment je v místním archivu. Skrytí neuvolnilo místo · čeká na server."
                : "Moment je obnoven se stejným soukromím · čeká na server."
            refresh()
        } catch { message = error.localizedDescription; refresh() }
    }

    /// Deletes a complete Moment after the UI confirmation. Metadata tombstones
    /// are committed first; byte cleanup is then best-effort and never restores
    /// a deleted item after a restart.
    func deleteMoment(momentID: UUID) {
        guard !audioBusy, !showCamera, let local,
              moment(with: momentID) != nil else { return }
        let assets = mediaByMoment[momentID] ?? []
        let sessions = audioSessionIDs(for: momentID)
        do {
            _ = try local.deleteMoment(momentID: momentID)
            var cleanupFailed = false
            for asset in assets {
                var deleted = asset; deleted.deleted = true
                if let mediaVault {
                    do { try mediaVault.delete(deleted) } catch { cleanupFailed = true }
                } else {
                    cleanupFailed = true
                }
            }
            for sessionID in sessions {
                if let recording {
                    do { try recording.delete(sessionID: sessionID) } catch { cleanupFailed = true }
                } else {
                    cleanupFailed = true
                }
            }
            message = cleanupFailed
                ? "Moment je smazaný z telefonu; úklid některého souboru se dokončí později."
                : "Moment a jeho přílohy jsou smazané z telefonu."
            momentDetail = nil
            refresh()
        } catch { message = error.localizedDescription; refresh() }
    }

    /// Deletes only the selected photo/video attachment; the parent Moment stays.
    func deleteAsset(assetID: UUID) {
        guard !audioBusy, !showCamera, let local else { return }
        do {
            guard let asset = mediaByMoment.values.flatMap({ $0 }).first(where: { $0.id == assetID }) else {
                throw LocalStoreError.invalidDeletion
            }
            _ = try local.deleteAsset(assetID: assetID)
            var deleted = asset; deleted.deleted = true
            guard let mediaVault else { throw LocalStoreError.invalidMedia }
            try mediaVault.delete(deleted)
            message = "Příloha je smazaná z telefonu; ostatní obsah Momentu zůstal zachovaný."
            refresh()
        } catch { message = error.localizedDescription; refresh() }
    }

    /// Deletes one complete audio session, including all technical segments.
    func deleteAudioSession(sessionID: UUID, momentID: UUID) {
        guard !audioBusy, !showCamera, let local else { return }
        do {
            _ = try local.deleteAudioSession(sessionID: sessionID, momentID: momentID)
            guard let recording else { throw LocalStoreError.invalidAudioIntent }
            try recording.delete(sessionID: sessionID)
            message = "Nahrávka a všechny její části jsou smazané z telefonu."
            refresh()
        } catch { message = error.localizedDescription; refresh() }
    }

    func setImportant(momentID: UUID, important: Bool) {
        guard !audioBusy, !showCamera, let local else { return }
        do {
            _ = try local.setImportant(momentID: momentID, important: important)
            message = important ? "Hvězdička uložena v telefonu." : "Hvězdička odebrána."
            refresh()
        } catch { message = error.localizedDescription; refresh() }
    }

    func moveMoment(momentID: UUID, to date: Date) {
        guard !audioBusy, !showCamera, let local else { return }
        let chapter = CaptureStamp.record(date, timeZone: .current).chapterDate
        do {
            _ = try local.moveMoment(momentID: momentID, toChapterDate: chapter)
            message = "Kapitola změněna; původní čas zůstal zachovaný · čeká na server."
            refresh()
        } catch { message = error.localizedDescription; refresh() }
    }

    func audioSessionIDs(for momentID: UUID) -> Set<UUID> {
        Set((try? local?.audioSessionIDs(momentID: momentID)) ?? [])
    }


    /// Cancellation releases the UI immediately, even if iCloud's provider has
    /// not returned yet. A late provider callback only disposes its own copy.
    private func loadLibraryItem(_ item: PhotosPickerItem) async throws -> CaminoPickedFile? {
        let id = UUID()
        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                guard !Task.isCancelled else {
                    continuation.resume(throwing: CancellationError())
                    return
                }
                libraryLoadID = id
                libraryLoadContinuation = continuation
                canCancelLibraryLoad = true
                libraryLoadProgress = item.loadTransferable(type: CaminoPickedFile.self) { result in
                    Task { @MainActor [weak self] in
                        guard let self, self.libraryLoadID == id,
                              let continuation = self.libraryLoadContinuation else {
                            if case .success(let copy) = result { copy?.removeTemporaryCopy() }
                            return
                        }
                        self.libraryLoadID = nil
                        self.libraryLoadContinuation = nil
                        self.libraryLoadProgress = nil
                        self.canCancelLibraryLoad = false
                        continuation.resume(with: result)
                    }
                }
            }
        } onCancel: {
            Task { @MainActor [weak self] in self?.cancelLibraryLoad(id: id) }
        }
    }

    func cancelLibraryLoad(id: UUID? = nil) {
        guard id == nil || libraryLoadID == id else { return }
        let continuation = libraryLoadContinuation
        libraryLoadContinuation = nil
        libraryLoadID = nil
        libraryLoadProgress?.cancel()
        libraryLoadProgress = nil
        canCancelLibraryLoad = false
        continuation?.resume(throwing: CancellationError())
    }

    func importFromPhotos(_ item: PhotosPickerItem, into momentID: UUID) async {
        guard !importingMedia, !audioBusy, !showCamera, let mediaVault else { return }
        importingMedia = true
        defer { importingMedia = false }
        message = "Načítám z Fotek… Pokud je soubor na iCloudu, může to chvíli trvat."
        do {
            guard let picked = try await loadLibraryItem(item) else {
                throw LocalStoreError.invalidMedia
            }
            defer { picked.removeTemporaryCopy() }
            try Task.checkCancellation()
            message = "Připravuji a ověřuji médium…"
            _ = try await mediaVault.importLibraryFile(picked.url, kind: picked.kind,
                                                       targetMomentID: momentID)
            message = "Médium vloženo do okamžiku. Originál ve Fotkách zůstal zachovaný."
            refresh()
        } catch is CancellationError {
            message = "Výběr z Fotek byl zrušen."
        } catch LocalStoreError.insufficientSpace {
            message = "Na vložení média není dost volného místa. Originál ve Fotkách zůstal zachovaný."
        } catch {
            message = "Médium se nepodařilo vložit. Zkontroluj jeho dostupnost ve Fotkách a případné připojení k iCloudu."
        }
        await reconcileMedia()
    }

    @discardableResult func savePhoto(_ data: Data) async -> LocalMediaAsset? {
        guard let mediaVault, showCamera else { return nil }
        let targetMomentID = cameraTargetMomentID
        if targetMomentID == nil { message = "Ověřuji GPS…" }
        let (fix, gpsWarning) = targetMomentID == nil
            ? await captureLocationForNewMoment()
            : (nil, nil)
        do {
            let date = Date()
            let asset = try await mediaVault.savePhoto(data,
                targetMomentID: targetMomentID, at: date, location: fix)
            message = Self.joinMessages(gpsWarning,
                "Fotografie uložena v telefonu. Mac zatím neověřen.")
            refresh()
            await reconcileMedia()
            return asset
        } catch LocalStoreError.insufficientSpace {
            message = blockedStorageMessage(for: .photo)
            await reconcileMedia()
            return nil
        } catch {
            message = "Fotografii nelze potvrdit jako uloženou. Dostupný soubor zůstal zachovaný."
            await reconcileMedia()
            return nil
        }
    }

    func beginVideo(silent: Bool) async -> URL? {
        guard let mediaVault, showCamera, activeVideoIntent == nil else { return nil }
        let thermal = thermalPolicy.videoAction(for: thermalLevel)
        guard thermal != .block else {
            message = "Telefon hlásí kritickou teplotu. Video nezačalo a kvalita se skrytě nemění."
            return nil
        }
        let targetMomentID = cameraTargetMomentID
        if targetMomentID == nil { message = "Ověřuji GPS…" }
        let (fix, gpsWarning) = targetMomentID == nil
            ? await captureLocationForNewMoment()
            : (nil, nil)
        do {
            let date = Date()
            let (intent, pendingURL, warning) = try mediaVault.beginVideo(
                targetMomentID: targetMomentID, silent: silent, at: date, location: fix)
            activeVideoIntent = intent
            message = Self.joinMessages(gpsWarning,
                thermal == .warn ? thermalWarningMessage : nil,
                warning ? warningStorageMessage(for: .video) : nil)
            return pendingURL
        } catch LocalStoreError.insufficientSpace {
            message = blockedStorageMessage(for: .video)
            return nil
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

    func stopVideoForSafety() -> Bool {
        let storage = storageAction(for: .video, active: true)
        if storage == .finish {
            message = "Volné místo kleslo k bezpečnostní rezervě. Ukončuji video; nic se nemaže."
            return true
        }
        let thermal = thermalPolicy.videoAction(for: thermalLevel, active: true)
        if thermal == .finish {
            message = "Telefon hlásí kritickou teplotu. Video bezpečně ukončuji; kvalita se skrytě nemění."
            return true
        }
        if thermal == .warn { message = thermalWarningMessage }
        else if storage == .warn { message = warningStorageMessage(for: .video) }
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
