import Foundation
import UIKit
@preconcurrency import AVFAudio

/// Audio-engine tap stays installed while files rotate. The lock serializes the
/// render callback with Stop without restarting the physical input at checkpoints.
private final class SegmentedCaptureWriter: @unchecked Sendable {
    private let lock = NSLock()
    private let directory: URL
    private let format: AVAudioFormat
    private let policy: SegmentCheckpointPolicy
    private var file: AVAudioFile?
    private var index = 0
    private var currentFrames: Int64 = 0
    private var totalFrames: Int64 = 0
    private var failed = false
    private var finished = false
    private var averagePower: Float = -160

    init(firstPartialURL: URL, format: AVAudioFormat,
         policy: SegmentCheckpointPolicy) throws {
        guard policy.valid, format.sampleRate > 0, format.channelCount > 0,
              firstPartialURL.lastPathComponent == Self.partialName(0) else {
            throw AudioPrototypeError.invalidMetadata
        }
        self.directory = firstPartialURL.deletingLastPathComponent()
        self.format = format
        self.policy = policy
        self.file = try Self.open(url: firstPartialURL, format: format)
    }

    func append(_ buffer: AVAudioPCMBuffer) {
        lock.lock()
        defer { lock.unlock() }
        guard !failed, !finished, buffer.frameLength > 0,
              buffer.format.sampleRate == format.sampleRate,
              buffer.format.channelCount == format.channelCount else {
            failed = true; return
        }
        let incoming = Int64(buffer.frameLength)
        guard Double(incoming) / format.sampleRate
                <= policy.maximumSeconds - policy.targetSeconds,
              file != nil else {
            failed = true; return
        }
        do {
            if policy.shouldRotate(framesWritten: currentFrames,
                                   incomingFrames: incoming,
                                   sampleRate: format.sampleRate) {
                try closeCurrentPart()
                index += 1; currentFrames = 0
                file = try Self.open(url: partialURL(index), format: format)
            }
            try file?.write(from: buffer)
            currentFrames += incoming; totalFrames += incoming
            averagePower = Self.power(buffer)
        } catch {
            failed = true; file = nil
        }
    }

    func finish() -> Bool {
        lock.lock()
        defer { lock.unlock() }
        guard !finished else { return false }
        finished = true
        do {
            if currentFrames > 0 { try closeCurrentPart() }
            else { file = nil }
        } catch { failed = true }
        return !failed && totalFrames > 0
    }

    func sample(engineRunning: Bool) -> (running: Bool, time: Double, power: Float) {
        lock.lock()
        defer { lock.unlock() }
        return (engineRunning && !failed && !finished,
                Double(totalFrames) / format.sampleRate, averagePower)
    }

    private func closeCurrentPart() throws {
        let partial = partialURL(index)
        let stable = stableURL(index)
        file = nil // AVAudioFile closes and updates the CAF header before rename.
        guard FileManager.default.fileExists(atPath: partial.path),
              !FileManager.default.fileExists(atPath: stable.path) else {
            throw AudioPrototypeError.collision
        }
        try FileManager.default.moveItem(at: partial, to: stable)
    }

    private func partialURL(_ value: Int) -> URL {
        directory.appendingPathComponent(Self.partialName(value))
    }
    private func stableURL(_ value: Int) -> URL {
        directory.appendingPathComponent(Self.stableName(value))
    }
    private static func partialName(_ value: Int) -> String {
        String(format: "segment-%06d.partial.caf", value)
    }
    private static func stableName(_ value: Int) -> String {
        String(format: "segment-%06d.caf", value)
    }

    private static func open(url: URL, format: AVAudioFormat) throws -> AVAudioFile {
        guard !FileManager.default.fileExists(atPath: url.path) else {
            throw AudioPrototypeError.collision
        }
        let result = try AVAudioFile(forWriting: url, settings: format.settings,
                                     commonFormat: format.commonFormat,
                                     interleaved: format.isInterleaved)
        try FileManager.default.setAttributes(
            [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
            ofItemAtPath: url.path)
        return result
    }

    private static func power(_ buffer: AVAudioPCMBuffer) -> Float {
        guard let channels = buffer.floatChannelData, buffer.frameLength > 0 else { return -160 }
        let values = channels[0]
        var sum: Float = 0
        for index in 0..<Int(buffer.frameLength) { sum += values[index] * values[index] }
        let rms = sqrt(sum / Float(buffer.frameLength))
        guard rms.isFinite, rms > 0 else { return -160 }
        return max(-160, min(0, 20 * log10(rms)))
    }
}

@MainActor final class IOSAudioDriver: NSObject, AudioDriver, AVAudioPlayerDelegate {
    var event: (() -> Void)?
    private var engine: AVAudioEngine?
    private var writer: SegmentedCaptureWriter?
    private var player: AVAudioPlayer?
    private var playbackQueue: [URL] = []
    private var playbackIndex = 0
    private var completedPlaybackDuration: Double = 0
    private var totalPlaybackDuration: Double = 0
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
        guard UIApplication.shared.applicationState == .active else {
            throw AudioPrototypeError.startFailed
        }
        guard engine == nil, writer == nil, player == nil,
              !FileManager.default.fileExists(atPath: url.path) else {
            throw AudioPrototypeError.collision
        }
        try session.setCategory(.playAndRecord, mode: .default,
                                options: [.defaultToSpeaker, .allowBluetoothHFP])
        try session.setPreferredSampleRate(48_000)
        try? session.setPreferredInputNumberOfChannels(1)
        try session.setActive(true)

        let nextEngine = AVAudioEngine()
        let input = nextEngine.inputNode
        let format = input.outputFormat(forBus: 0)
        guard format.sampleRate > 0, format.channelCount > 0 else {
            throw AudioPrototypeError.startFailed
        }
        let nextWriter = try SegmentedCaptureWriter(firstPartialURL: url,
            format: format, policy: RecordingStore.checkpointPolicy)
        input.installTap(onBus: 0, bufferSize: 4_096, format: format) { buffer, _ in
            nextWriter.append(buffer)
        }
        engine = nextEngine; writer = nextWriter
        do {
            nextEngine.prepare()
            try nextEngine.start()
        } catch {
            input.removeTap(onBus: 0); nextEngine.stop()
            engine = nil; writer = nil
            try? session.setActive(false, options: [.notifyOthersOnDeactivation])
            throw error
        }
    }

    func pauseCapture() { engine?.pause() }

    func sample() -> CaptureSample {
        let value = writer?.sample(engineRunning: engine?.isRunning == true)
            ?? (running: false, time: 0, power: -160)
        let route = session.currentRoute.inputs
        return CaptureSample(running: value.running, time: value.time, power: value.power,
            inputID: route.map(\.uid).joined(separator: "/"),
            inputLabel: route.map(\.portName).joined(separator: ", "))
    }

    func stop() async -> Bool {
        guard let currentEngine = engine, let currentWriter = writer else {
            try? session.setActive(false, options: [.notifyOthersOnDeactivation])
            return false
        }
        currentEngine.inputNode.removeTap(onBus: 0)
        currentEngine.stop()
        let successful = currentWriter.finish()
        engine = nil; writer = nil
        try? session.setActive(false, options: [.notifyOthersOnDeactivation])
        return successful
    }

    func play(urls: [URL]) throws {
        guard engine == nil, writer == nil, player == nil, !urls.isEmpty else {
            throw AudioPrototypeError.startFailed
        }
        for url in urls {
            guard FileManager.default.fileExists(atPath: url.path),
                  try url.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true else {
                throw AudioPrototypeError.missingAudio
            }
        }
        do {
            let durations = try urls.map { url -> Double in
                let file = try AVAudioFile(forReading: url)
                guard file.length > 0, file.processingFormat.sampleRate > 0 else {
                    throw AudioPrototypeError.invalidAudio
                }
                return Double(file.length) / file.processingFormat.sampleRate
            }
            try session.setCategory(.playback, mode: .default)
            try session.setActive(true)
            playbackQueue = urls; playbackIndex = 0
            completedPlaybackDuration = 0
            totalPlaybackDuration = durations.reduce(0, +)
            try startPlaybackPart(at: 0)
        } catch {
            resetPlayback()
            try? session.setActive(false, options: [.notifyOthersOnDeactivation])
            throw error
        }
    }

    private func startPlaybackPart(at index: Int) throws {
        let next = try AVAudioPlayer(contentsOf: playbackQueue[index])
        next.delegate = self
        guard next.prepareToPlay(), next.play() else { throw AudioPrototypeError.invalidAudio }
        player = next; playbackIndex = index
    }

    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer,
                                                  successfully flag: Bool) {
        Task { @MainActor [weak self] in
            guard let self, self.player === player else { return }
            if flag, self.playbackIndex + 1 < self.playbackQueue.count {
                self.completedPlaybackDuration += player.duration
                do { try self.startPlaybackPart(at: self.playbackIndex + 1) }
                catch { self.resetPlayback(); self.event?() }
            } else {
                self.player = nil
                try? self.session.setActive(false, options: [.notifyOthersOnDeactivation])
            }
        }
    }

    var isPlaying: Bool { player?.isPlaying == true }
    var playbackTime: Double { completedPlaybackDuration + (player?.currentTime ?? 0) }
    var playbackDuration: Double { totalPlaybackDuration }

    func stopPlayback() {
        player?.stop(); resetPlayback()
        try? session.setActive(false, options: [.notifyOthersOnDeactivation])
    }

    private func resetPlayback() {
        player?.delegate = nil; player = nil; playbackQueue = []
        playbackIndex = 0; completedPlaybackDuration = 0; totalPlaybackDuration = 0
    }
}
