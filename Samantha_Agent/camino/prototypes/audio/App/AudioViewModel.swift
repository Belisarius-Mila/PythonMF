import SwiftUI
import AVFAudio
import Combine
import UserNotifications

@MainActor final class AudioViewModel: ObservableObject {
    let controller: AudioController?
    let startupError: String?
    @Published var kind: RecordingKind = .comment
    private var subscriptions = Set<AnyCancellable>()
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid
    private var wasFinishing = false

    init() {
        do {
            var root = try FileManager.default.url(for: .applicationSupportDirectory,
                in: .userDomainMask, appropriateFor: nil, create: true)
                .appendingPathComponent("CaminoAudio", isDirectory: true)
            #if DEBUG && targetEnvironment(simulator)
            if let value = ProcessInfo.processInfo.environment["CAMINO_UI_TEST_SESSION"],
               let session = UUID(uuidString: value) {
                root = root.deletingLastPathComponent()
                    .appendingPathComponent("CaminoAudioUITests", isDirectory: true)
                    .appendingPathComponent(session.uuidString, isDirectory: true)
                try SimulatorAudioFixture.prepare(root: root,
                    allowSeed: ProcessInfo.processInfo.environment["CAMINO_UI_TEST_SEED"] == "1")
            }
            #endif
            let driver = IOSAudioDriver()
            let store = try RecordingStore(root: root, inspect: AudioFileInspector.inspect)
            var backupValues = URLResourceValues(); backupValues.isExcludedFromBackup = true
            var privateRoot = root; try privateRoot.setResourceValues(backupValues)
            let controller = AudioController(driver: driver, store: store)
            self.controller = controller; startupError = nil
            driver.event = { [weak controller] in controller?.interrupt(reason: "Zvukový vstup se zastavil") }
            controller.changed = { [weak self] in
                self?.captureChanged()
                self?.objectWillChange.send()
            }
            // The model owns observation while audio runs behind the lock; no view timer dependency.
            Timer.publish(every: 0.15, on: .main, in: .common).autoconnect()
                .sink { [weak self] _ in self?.tick() }.store(in: &subscriptions)
            observe(AVAudioSession.interruptionNotification) { [weak self] in self?.interruption($0) }
            observe(AVAudioSession.routeChangeNotification) { [weak controller] _ in controller?.routeChanged() }
            observe(AVAudioSession.mediaServicesWereLostNotification) { [weak controller] _ in
                controller?.interrupt(reason: "Zvuková služba není dostupná")
            }
            observe(AVAudioSession.mediaServicesWereResetNotification) { [weak controller] _ in
                controller?.interrupt(reason: "Zvuková služba byla obnovena")
            }
        } catch {
            controller = nil
            startupError = "Soukromé úložiště nelze připravit. Nahrávání není dostupné; žádné soubory se nemažou."
        }
    }

    private func observe(_ name: Notification.Name, action: @escaping @MainActor (Notification) -> Void) {
        NotificationCenter.default.publisher(for: name).receive(on: RunLoop.main)
            .sink { notification in action(notification) }.store(in: &subscriptions)
    }

    private func captureChanged() {
        guard let controller else { return }
        if controller.phase == .finishing && !wasFinishing {
            backgroundTask = UIApplication.shared.beginBackgroundTask(withName: "Finish audio") { [weak self] in
                Task { @MainActor in self?.endBackgroundTask() }
            }
            if controller.isFinishingInterrupted { notifyInterruptionIfAllowed() }
        } else if controller.phase != .finishing { endBackgroundTask() }
        wasFinishing = controller.phase == .finishing
    }

    private func endBackgroundTask() {
        guard backgroundTask != .invalid else { return }
        UIApplication.shared.endBackgroundTask(backgroundTask); backgroundTask = .invalid
    }

    private func notifyInterruptionIfAllowed() {
        Task {
            let center = UNUserNotificationCenter.current()
            let settings = await center.notificationSettings()
            guard settings.authorizationStatus == .authorized || settings.authorizationStatus == .provisional else { return }
            let content = UNMutableNotificationContent()
            content.title = "Nahrávání přerušeno"
            content.body = "Otevři Camino a zkontroluj stav."
            try? await center.add(UNNotificationRequest(identifier: "camino-audio-interrupted",
                content: content, trigger: nil))
        }
    }

    func tick() { controller?.tick() }
    func interruption(_ notification: Notification) {
        let value = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt
        if value == AVAudioSession.InterruptionType.began.rawValue {
            controller?.interrupt()
        } else if value == AVAudioSession.InterruptionType.ended.rawValue {
            controller?.interruptionEnded()
        }
    }
}

#if DEBUG && targetEnvironment(simulator)
/// Synthetic media for UI tests only; absent from physical-device and Release builds.
@MainActor private enum SimulatorAudioFixture {
    static func prepare(root: URL, allowSeed: Bool) throws {
        let store = try RecordingStore(root: root, inspect: AudioFileInspector.inspect)
        let library = try store.library()
        guard library.unfinishedCount == 0 else { throw AudioPrototypeError.invalidMetadata }
        guard library.clips.isEmpty else { return } // Relaunch must reuse the completed clip.
        guard allowSeed else { throw AudioPrototypeError.invalidMetadata }
        let draft = try store.begin(kind: .comment)
        try writeSilence(to: store.url(for: draft))
        _ = try store.finish(draft, interrupted: false)
    }

    private static func writeSilence(to url: URL) throws {
        let format = AVAudioFormat(standardFormatWithSampleRate: 48_000, channels: 1)!
        let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 4_800)!
        buffer.frameLength = 4_800
        for frame in 0..<4_800 { buffer.floatChannelData![0][frame] = 0 }
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM, AVSampleRateKey: 48_000,
            AVNumberOfChannelsKey: 1, AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false, AVLinearPCMIsBigEndianKey: false
        ]
        let file = try AVAudioFile(forWriting: url, settings: settings)
        for _ in 0..<300 { try file.write(from: buffer) } // 30 seconds, no microphone.
    }
}
#endif
