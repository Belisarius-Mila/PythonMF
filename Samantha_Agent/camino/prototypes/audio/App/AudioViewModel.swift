import SwiftUI
import AVFAudio

@MainActor final class AudioViewModel: ObservableObject {
    let controller: AudioController?
    let startupError: String?
    @Published var kind: RecordingKind = .comment

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
            driver.event = { [weak controller] in controller?.interrupt() }
            controller.changed = { [weak self] in self?.objectWillChange.send() }
        } catch {
            controller = nil
            startupError = "Soukromé úložiště nelze připravit. Nahrávání není dostupné; žádné soubory se nemažou."
        }
    }

    func tick() { controller?.tick() }
    func interruption(_ notification: Notification) {
        let value = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt
        if value == AVAudioSession.InterruptionType.began.rawValue { controller?.interrupt() }
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
