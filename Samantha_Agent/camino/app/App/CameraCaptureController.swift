@preconcurrency import AVFoundation
import Combine
import Foundation
import SwiftUI

private final class CameraSessionBox: @unchecked Sendable {
    let session = AVCaptureSession()
    let queue = DispatchQueue(label: "cz.pythonmf.camino.camera.session")

    func start() async {
        await withCheckedContinuation { continuation in
            queue.async {
                if !self.session.isRunning { self.session.startRunning() }
                continuation.resume()
            }
        }
    }

    func stop() async {
        await withCheckedContinuation { continuation in
            queue.async {
                if self.session.isRunning { self.session.stopRunning() }
                continuation.resume()
            }
        }
    }
}

@MainActor final class CameraCaptureController: NSObject, ObservableObject {
    enum Phase { case idle, permission, preparing, ready, capturing, starting, recording, finishing, saving, failed }

    @Published private(set) var phase: Phase = .idle
    @Published private(set) var message = "Kamera se připravuje"
    @Published private(set) var recordedSeconds: Double = 0
    @Published private(set) var cameraPosition: AVCaptureDevice.Position = .back
    @Published private(set) var zoomFactor: Double = 1
    @Published private(set) var zoomPresets: [Double] = []
    @Published private(set) var zoomRange: ClosedRange<Double> = 1...1
    @Published private(set) var zoomMessage: String?

    private let hardware = CameraSessionBox()
    private let photoOutput = AVCapturePhotoOutput()
    private let movieOutput = AVCaptureMovieFileOutput()
    private var videoInput: AVCaptureDeviceInput?
    private var audioInput: AVCaptureDeviceInput?
    private weak var previewLayer: AVCaptureVideoPreviewLayer?
    private var rotationCoordinator: AVCaptureDevice.RotationCoordinator?
    private var subscriptions = Set<AnyCancellable>()
    private var mode: LocalMediaKind = .photo
    private var interrupted = false
    private var soundRequested = true
    private var pendingMovieURL: URL?
    private var zoomObservations: [NSKeyValueObservation] = []

    var onPhoto: ((Data?, String?) -> Void)?
    var onMovie: ((URL, Bool, String?) -> Void)?
    var session: AVCaptureSession { hardware.session }
    var canCapture: Bool { phase == .ready && session.isRunning }
    var canAdjustZoom: Bool {
        (phase == .ready || phase == .recording) && session.isRunning &&
        zoomRange.lowerBound < zoomRange.upperBound
    }
    var isBusy: Bool { [.capturing, .starting, .recording, .finishing, .saving].contains(phase) }

    override init() {
        super.init()
        NotificationCenter.default.publisher(for: AVCaptureSession.wasInterruptedNotification,
                                             object: hardware.session)
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in self?.handleInterruption("Kamera byla přerušena") }
            .store(in: &subscriptions)
        NotificationCenter.default.publisher(for: AVCaptureSession.runtimeErrorNotification,
                                             object: hardware.session)
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in self?.handleInterruption("Kamera hlásí chybu") }
            .store(in: &subscriptions)
        NotificationCenter.default.publisher(for: UIDevice.orientationDidChangeNotification)
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in self?.applyRotation() }
            .store(in: &subscriptions)
        Timer.publish(every: 0.2, on: .main, in: .common).autoconnect()
            .sink { [weak self] _ in self?.tick() }
            .store(in: &subscriptions)
    }

    func attachPreview(_ layer: AVCaptureVideoPreviewLayer) {
        previewLayer = layer
        layer.session = hardware.session
        layer.videoGravity = .resizeAspectFill
        if let device = videoInput?.device {
            rotationCoordinator = AVCaptureDevice.RotationCoordinator(device: device,
                                                                        previewLayer: layer)
            applyRotation()
        }
    }

    func prepare(mode: LocalMediaKind) async {
        guard phase == .idle || phase == .failed else { return }
        self.mode = mode
        phase = .permission
        message = "Povol kameru pro vlastní fotky a videa Camina."
        guard await AVCaptureDevice.requestAccess(for: .video) else {
            phase = .failed
            message = "Povol kameru v nastavení telefonu. Audio a deník dál fungují."
            return
        }
        phase = .preparing
        message = "Připravuji náhled"
        do {
            try configureVideoInput(position: .back)
            let session = hardware.session
            session.beginConfiguration()
            session.sessionPreset = mode == .video && session.canSetSessionPreset(.hd1920x1080)
                ? .hd1920x1080 : .photo
            if mode == .photo {
                if !session.outputs.contains(photoOutput) {
                    guard session.canAddOutput(photoOutput) else {
                        session.commitConfiguration()
                        throw LocalStoreError.invalidMedia
                    }
                    session.addOutput(photoOutput)
                }
            } else {
                if !session.outputs.contains(movieOutput) {
                    guard session.canAddOutput(movieOutput) else {
                        session.commitConfiguration()
                        throw LocalStoreError.invalidMedia
                    }
                    session.addOutput(movieOutput)
                }
                movieOutput.movieFragmentInterval = CMTime(seconds: 2, preferredTimescale: 600)
            }
            session.commitConfiguration()
            configureZoom()
            if let device = videoInput?.device {
                rotationCoordinator = AVCaptureDevice.RotationCoordinator(
                    device: device, previewLayer: previewLayer)
            }
            applyRotation()
            await hardware.start()
            guard session.isRunning else { throw LocalStoreError.invalidMedia }
            phase = .ready
            message = mode == .photo ? "Připraveno k fotografování" : "Připraveno k videu"
        } catch {
            phase = .failed
            message = "Kameru nelze připravit. Nic se nesmazalo."
        }
    }

    func switchCamera() async {
        guard phase == .ready else { return }
        phase = .preparing
        await hardware.stop()
        do {
            try configureVideoInput(position: cameraPosition == .back ? .front : .back)
            configureZoom()
            if let device = videoInput?.device {
                rotationCoordinator = AVCaptureDevice.RotationCoordinator(
                    device: device, previewLayer: previewLayer)
            }
            applyRotation()
            await hardware.start()
            phase = session.isRunning ? .ready : .failed
            message = phase == .ready ? "Kamera připravena" : "Kameru nelze spustit"
        } catch {
            phase = .failed
            message = "Kameru nelze přepnout."
        }
    }

    func capturePhoto() {
        guard mode == .photo, canCapture else { return }
        phase = .capturing
        message = "Zachycuji fotografii"
        applyRotation()
        let settings = AVCapturePhotoSettings(format: [AVVideoCodecKey: AVVideoCodecType.jpeg])
        settings.photoQualityPrioritization = .balanced
        photoOutput.capturePhoto(with: settings, delegate: self)
    }

    /// Changes the captured image, without stopping the session or the movie.
    func setZoom(_ factor: Double, animated: Bool = false) {
        guard canAdjustZoom, factor.isFinite, let device = videoInput?.device else { return }
        do {
            try device.lockForConfiguration()
            defer { device.unlockForConfiguration() }
            // Re-read dynamic limits while holding the configuration lock.
            guard let scale = zoomScale(for: device),
                  let target = scale.deviceFactor(forDisplayFactor: factor) else { return }
            device.cancelVideoZoomRamp()
            if animated {
                device.ramp(toVideoZoomFactor: CGFloat(target), withRate: 3)
            } else {
                device.videoZoomFactor = CGFloat(target)
            }
            zoomMessage = nil
            refreshZoomState()
        } catch {
            // A zoom error must not stop a recording or change its audio mode.
            zoomMessage = "Přiblížení teď nelze změnit."
        }
    }

    /// Checks the requested audio path before the caller writes a video intent.
    func prepareVideoSound(silent: Bool) async -> Bool {
        guard mode == .video, phase == .ready else { return false }
        if !silent {
            message = "Povol mikrofon pro video se zvukem."
            guard await AVCaptureDevice.requestAccess(for: .audio) else {
                message = "Mikrofon není povolený. Chceš-li video bez zvuku, zvol to výslovně."
                return false
            }
        }
        phase = .preparing
        await hardware.stop()
        let session = hardware.session
        session.beginConfiguration()
        if let audioInput {
            session.removeInput(audioInput)
            self.audioInput = nil
        }
        if !silent {
            guard let microphone = AVCaptureDevice.default(for: .audio),
                  let input = try? AVCaptureDeviceInput(device: microphone),
                  session.canAddInput(input) else {
                session.commitConfiguration()
                phase = .failed
                message = "Mikrofon videa není dostupný. Bez zvuku se nezačne automaticky."
                return false
            }
            session.addInput(input)
            audioInput = input
        }
        session.commitConfiguration()
        refreshZoomState()
        await hardware.start()
        guard session.isRunning else {
            phase = .failed
            message = "Kameru nelze spustit."
            return false
        }
        soundRequested = !silent
        phase = .ready
        message = silent ? "Bez zvuku · připraveno" : "Se zvukem · připraveno"
        return true
    }

    func startMovie(at url: URL) {
        guard mode == .video, canCapture, !movieOutput.isRecording else { return }
        pendingMovieURL = url
        interrupted = false
        recordedSeconds = 0
        phase = .starting
        message = soundRequested ? "Zahajuji video se zvukem" : "Zahajuji video bez zvuku"
        applyRotation()
        movieOutput.startRecording(to: url, recordingDelegate: self)
    }

    func stopMovie(interrupted: Bool = false) {
        guard mode == .video,
              [.starting, .recording, .finishing].contains(phase) else { return }
        self.interrupted = self.interrupted || interrupted
        phase = .finishing
        message = interrupted ? "Přerušeno · bezpečně ukončuji video"
                              : "Ukončuji a ověřuji video"
        if movieOutput.isRecording { movieOutput.stopRecording() }
    }

    func pauseForBackground() {
        if [.starting, .recording].contains(phase) {
            stopMovie(interrupted: true)
        } else if phase == .ready {
            Task { await hardware.stop() }
        }
    }

    func resumePreview() async {
        guard phase == .ready else { return }
        await hardware.start()
        refreshZoomState()
        if !session.isRunning {
            phase = .failed
            message = "Náhled kamery nelze obnovit. Záznam se nespustil."
        }
    }

    func finishSaving(success: Bool, message: String) {
        self.message = message
        phase = session.isRunning ? .ready : (success ? .idle : .failed)
    }

    func shutdown() {
        if [.starting, .recording].contains(phase) { stopMovie(interrupted: true) }
        zoomObservations.removeAll()
        Task { await hardware.stop() }
    }

    private func configureVideoInput(position: AVCaptureDevice.Position) throws {
        let session = hardware.session
        session.beginConfiguration()
        let previous = videoInput
        if let previous { session.removeInput(previous) }
        let types: [AVCaptureDevice.DeviceType] = position == .back
            ? [.builtInTripleCamera, .builtInDualWideCamera, .builtInDualCamera, .builtInWideAngleCamera]
            : [.builtInWideAngleCamera]
        var selected: AVCaptureDeviceInput?
        for type in types {
            guard let device = AVCaptureDevice.default(type, for: .video, position: position),
                  let candidate = try? AVCaptureDeviceInput(device: device),
                  session.canAddInput(candidate) else { continue }
            session.addInput(candidate)
            selected = candidate
            break
        }
        guard let input = selected else {
            if let previous, session.canAddInput(previous) { session.addInput(previous) }
            session.commitConfiguration()
            throw LocalStoreError.invalidMedia
        }
        session.commitConfiguration()
        videoInput = input
        cameraPosition = position
        let device = input.device
        if mode == .video {
            try device.lockForConfiguration()
            defer { device.unlockForConfiguration() }
            if device.activeFormat.videoSupportedFrameRateRanges.contains(where: {
                $0.minFrameRate <= 30 && $0.maxFrameRate >= 30
            }) {
                device.activeVideoMinFrameDuration = CMTime(value: 1, timescale: 30)
                device.activeVideoMaxFrameDuration = CMTime(value: 1, timescale: 30)
            }
            if device.activeFormat.supportedColorSpaces.contains(.sRGB) {
                device.activeColorSpace = .sRGB
            }
        }
    }

    private func zoomScale(for device: AVCaptureDevice) -> LocalCameraZoomScale? {
        let multiplier: Double
        if #available(iOS 18.0, *) {
            multiplier = Double(device.displayVideoZoomFactorMultiplier)
        } else if device.deviceType == .builtInTripleCamera || device.deviceType == .builtInDualWideCamera,
                  let wideAngleFactor = device.virtualDeviceSwitchOverVideoZoomFactors.first?.doubleValue,
                  wideAngleFactor.isFinite, wideAngleFactor > 0 {
            multiplier = 1 / wideAngleFactor
        } else {
            multiplier = 1
        }
        return LocalCameraZoomScale(minimumDeviceFactor: Double(device.minAvailableVideoZoomFactor),
                                    maximumDeviceFactor: Double(device.maxAvailableVideoZoomFactor),
                                    displayMultiplier: multiplier)
    }

    private func configureZoom() {
        zoomObservations.removeAll()
        zoomMessage = nil
        guard let device = videoInput?.device else {
            refreshZoomState()
            return
        }
        var paths: [KeyPath<AVCaptureDevice, CGFloat>] = [\.videoZoomFactor,
            \.minAvailableVideoZoomFactor, \.maxAvailableVideoZoomFactor]
        if #available(iOS 18.0, *) { paths.append(\.displayVideoZoomFactorMultiplier) }
        zoomObservations = paths.map { path in
            device.observe(path, options: [.new]) { [weak self] _, _ in
                Task { @MainActor [weak self] in self?.refreshZoomState() }
            }
        }
        do {
            try device.lockForConfiguration()
            defer { device.unlockForConfiguration() }
            device.cancelVideoZoomRamp()
            // Start at the normal wide-angle view, including virtual cameras.
            if let scale = zoomScale(for: device),
               let normal = scale.deviceFactor(forDisplayFactor: 1) {
                device.videoZoomFactor = CGFloat(normal)
            }
        } catch {
            zoomMessage = "Výchozí přiblížení se nepodařilo nastavit."
        }
        refreshZoomState()
    }

    private func refreshZoomState() {
        guard let device = videoInput?.device, let scale = zoomScale(for: device) else {
            zoomFactor = 1
            zoomRange = 1...1
            zoomPresets = []
            return
        }
        zoomRange = scale.displayRange
        zoomPresets = scale.presets
        zoomFactor = scale.displayFactor(forDeviceFactor: Double(device.videoZoomFactor))
            ?? scale.displayRange.lowerBound
    }

    private func applyRotation() {
        guard let rotationCoordinator else { return }
        let previewAngle = rotationCoordinator.videoRotationAngleForHorizonLevelPreview
        if let preview = previewLayer?.connection,
           preview.isVideoRotationAngleSupported(previewAngle) {
            preview.videoRotationAngle = previewAngle
        }
        let captureAngle = rotationCoordinator.videoRotationAngleForHorizonLevelCapture
        let output = mode == .photo ? photoOutput.connection(with: .video)
                                    : movieOutput.connection(with: .video)
        if let output, output.isVideoRotationAngleSupported(captureAngle) {
            output.videoRotationAngle = captureAngle
        }
    }

    private func handleInterruption(_ text: String) {
        if [.starting, .recording].contains(phase) {
            stopMovie(interrupted: true)
        } else if phase == .ready {
            phase = .failed
        }
        message = text + ". Dostupný soubor zůstane zachovaný."
    }

    private func tick() {
        guard phase == .recording else { return }
        let seconds = CMTimeGetSeconds(movieOutput.recordedDuration)
        if seconds.isFinite && seconds > recordedSeconds { recordedSeconds = seconds }
    }
}

extension CameraCaptureController: AVCapturePhotoCaptureDelegate {
    nonisolated func photoOutput(_ output: AVCapturePhotoOutput,
                                 didFinishProcessingPhoto photo: AVCapturePhoto,
                                 error: Error?) {
        let data = error == nil ? photo.fileDataRepresentation() : nil
        let failure = error?.localizedDescription
        Task { @MainActor [weak self] in
            guard let self else { return }
            self.phase = .saving
            self.message = data == nil ? "Fotografii se nepodařilo zachytit"
                                       : "Ukládám originál fotografie"
            self.onPhoto?(data, failure)
        }
    }
}

extension CameraCaptureController: AVCaptureFileOutputRecordingDelegate {
    nonisolated func fileOutput(_ output: AVCaptureFileOutput,
                                didStartRecordingTo fileURL: URL,
                                from connections: [AVCaptureConnection]) {
        Task { @MainActor [weak self] in
            guard let self else { return }
            if self.phase == .finishing {
                if self.movieOutput.isRecording { self.movieOutput.stopRecording() }
                return
            }
            guard self.phase == .starting else { return }
            self.phase = .recording
            self.message = self.soundRequested ? "Nahrávám video se zvukem"
                                                : "Nahrávám video bez zvuku"
        }
    }

    nonisolated func fileOutput(_ output: AVCaptureFileOutput,
                                didFinishRecordingTo outputFileURL: URL,
                                from connections: [AVCaptureConnection],
                                error: Error?) {
        let failure = error?.localizedDescription
        Task { @MainActor [weak self] in
            guard let self else { return }
            self.phase = .saving
            self.message = "Ověřuji a ukládám video"
            self.onMovie?(outputFileURL, self.interrupted || failure != nil, failure)
            self.pendingMovieURL = nil
        }
    }
}
