import SwiftUI
import AVFAudio

@MainActor final class AudioViewModel: ObservableObject {
    let controller: AudioController?
    let startupError: String?
    @Published var kind: RecordingKind = .comment

    init() {
        do {
            let root = try FileManager.default.url(for: .applicationSupportDirectory,
                in: .userDomainMask, appropriateFor: nil, create: true)
                .appendingPathComponent("CaminoAudio", isDirectory: true)
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
