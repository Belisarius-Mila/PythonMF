import Foundation
@preconcurrency import AVFAudio

@MainActor final class IOSAudioDriver: NSObject, AudioDriver, AVAudioRecorderDelegate, AVAudioPlayerDelegate {
    var event: (() -> Void)?
    private var recorder: AVAudioRecorder?
    private var player: AVAudioPlayer?
    private var stopContinuation: CheckedContinuation<Bool, Never>?
    private var completion: Bool?
    private var stopToken = UUID()
    private let session = AVAudioSession.sharedInstance()

    var permission: MicrophonePermission {
        switch AVAudioApplication.shared.recordPermission {
        case .granted: .granted
        case .denied: .denied
        default: .undetermined
        }
    }

    func requestPermission() async -> Bool { await AVAudioApplication.requestRecordPermission() }

    func start(url: URL) async throws {
        guard recorder == nil, player == nil,
              !FileManager.default.fileExists(atPath: url.path) else {
            throw AudioPrototypeError.collision
        }
        completion = nil
        try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker])
        try session.setPreferredSampleRate(48_000)
        try session.setActive(true)
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM, AVSampleRateKey: 48_000,
            AVNumberOfChannelsKey: 1, AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false, AVLinearPCMIsBigEndianKey: false
        ]
        let new = try AVAudioRecorder(url: url, settings: settings)
        recorder = new; new.delegate = self; new.isMeteringEnabled = true
        guard new.prepareToRecord(), new.record() else { throw AudioPrototypeError.startFailed }
        // C01a is foreground only; retain normal data protection.
        try FileManager.default.setAttributes([.protectionKey: FileProtectionType.complete],
                                             ofItemAtPath: url.path)
    }

    func sample() -> CaptureSample {
        recorder?.updateMeters()
        let route = session.currentRoute.inputs
        return CaptureSample(running: recorder?.isRecording == true,
            time: recorder?.currentTime ?? 0,
            power: recorder?.averagePower(forChannel: 0) ?? -160,
            inputID: route.map(\.uid).joined(separator: "/"),
            inputLabel: route.map(\.portName).joined(separator: ", "))
    }

    func stop() async -> Bool {
        guard let current = recorder else {
            try? session.setActive(false, options: [.notifyOthersOnDeactivation])
            return false
        }
        let successful: Bool
        if let completion { successful = completion }
        else {
            successful = await withCheckedContinuation { continuation in
                stopContinuation = continuation
                let token = UUID(); stopToken = token
                current.stop()
                // Missing delegate callback is a failure, never an invented success.
                Task { [weak self] in
                    try? await Task.sleep(for: .seconds(3))
                    guard let self, self.stopToken == token else { return }
                    self.resolveStop(false)
                }
            }
        }
        current.stop(); current.delegate = nil; recorder = nil
        try? session.setActive(false, options: [.notifyOthersOnDeactivation])
        return successful
    }

    private func resolveStop(_ success: Bool) {
        stopToken = UUID()
        completion = success
        stopContinuation?.resume(returning: success); stopContinuation = nil
    }

    nonisolated func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        Task { @MainActor [weak self] in
            guard let self, self.recorder === recorder else { return }
            let requested = self.stopContinuation != nil
            self.resolveStop(flag)
            if !requested { self.event?() }
        }
    }

    nonisolated func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        Task { @MainActor [weak self] in
            guard let self, self.recorder === recorder else { return }
            self.resolveStop(false); self.event?()
        }
    }

    func play(url: URL) throws {
        guard recorder == nil, player == nil else { throw AudioPrototypeError.startFailed }
        guard FileManager.default.fileExists(atPath: url.path) else { throw AudioPrototypeError.invalidAudio }
        do {
            try session.setCategory(.playback, mode: .default)
            try session.setActive(true)
            let new = try AVAudioPlayer(contentsOf: url)
            new.delegate = self
            guard new.prepareToPlay(), new.play() else { throw AudioPrototypeError.invalidAudio }
            player = new
        } catch {
            try? session.setActive(false, options: [.notifyOthersOnDeactivation])
            throw error
        }
    }

    var isPlaying: Bool { player?.isPlaying == true }
    func stopPlayback() {
        player?.stop(); player = nil
        try? session.setActive(false, options: [.notifyOthersOnDeactivation])
    }

}
