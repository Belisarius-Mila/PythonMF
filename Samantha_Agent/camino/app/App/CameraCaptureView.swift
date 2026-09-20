import AVFoundation
import AVKit
import ImageIO
import SwiftUI

private final class CaminoPreviewUIView: UIView {
    override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }
    var previewLayer: AVCaptureVideoPreviewLayer { layer as! AVCaptureVideoPreviewLayer }
}

private struct CaminoCameraPreview: UIViewRepresentable {
    @ObservedObject var camera: CameraCaptureController

    func makeUIView(context: Context) -> CaminoPreviewUIView {
        let view = CaminoPreviewUIView()
        camera.attachPreview(view.previewLayer)
        return view
    }

    func updateUIView(_ view: CaminoPreviewUIView, context: Context) {
        if view.previewLayer.session !== camera.session { camera.attachPreview(view.previewLayer) }
    }
}

struct CameraCaptureView: View {
    @ObservedObject var model: CaminoViewModel
    @StateObject private var camera = CameraCaptureController()
    @Environment(\.scenePhase) private var scenePhase
    @State private var silent = false
    @State private var lastAsset: LocalMediaAsset?
    @State private var leaveAfterFinish = false

    private var kind: LocalMediaKind { model.selectedMediaKind }
    private var target: LocalMoment? {
        model.moments.first { $0.id == model.cameraTargetMomentID }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    targetHeader
                    cameraPreview
                    captureStatus
                    captureControls
                    recentMedia
                    Text("Uložení na Mac zatím nebylo ověřeno.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .padding()
            }
            .navigationTitle(kind.title)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Zpět") { leave() }
                        .disabled([.capturing, .finishing, .saving].contains(camera.phase))
                }
            }
        }
        .interactiveDismissDisabled(true)
        .overlay {
            if scenePhase != .active {
                Color(.systemBackground).ignoresSafeArea()
                    .overlay(Label("Camino je skryté", systemImage: "lock.fill"))
            }
        }
        .onAppear {
            camera.onPhoto = { data, error in
                guard let data else {
                    camera.finishSaving(success: false,
                        message: error ?? "Fotografii se nepodařilo zachytit")
                    return
                }
                Task {
                    let asset = await model.savePhoto(data)
                    lastAsset = asset
                    camera.finishSaving(success: asset != nil,
                        message: model.message ?? "Fotografii nelze potvrdit")
                }
            }
            camera.onMovie = { url, interrupted, _ in
                Task {
                    let asset = await model.finalizeVideo(at: url, interrupted: interrupted)
                    lastAsset = asset
                    camera.finishSaving(success: asset != nil,
                        message: model.message ?? "Video nelze potvrdit")
                    if leaveAfterFinish {
                        camera.shutdown()
                        model.closeCamera()
                    }
                }
            }
            Task { await camera.prepare(mode: kind) }
        }
        .onDisappear { camera.shutdown() }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                Task {
                    if camera.phase == .idle || camera.phase == .failed {
                        await camera.prepare(mode: kind)
                    } else {
                        await camera.resumePreview()
                    }
                }
            } else {
                camera.pauseForBackground()
            }
        }
        .onReceive(Timer.publish(every: 5, on: .main, in: .common).autoconnect()) { _ in
            if camera.phase == .recording && model.stopVideoForLowSpace() {
                camera.stopMovie(interrupted: true)
            }
        }
    }

    @ViewBuilder private var targetHeader: some View {
        if let target {
            Label("Přidáváš do: \(target.kind.title) · \(time(target.capture))",
                  systemImage: "link")
                .font(.headline)
            if let photo = model.mediaByMoment[target.id]?.first(where: { $0.kind == .photo }),
               let url = model.originalURL(for: photo) {
                CaminoPhotoThumbnail(url: url).frame(width: 120, height: 90)
            }
            Text("Soukromí cílového Momentu: \(target.privacy.title)")
                .font(.subheadline)
        } else {
            Text("Nový Moment · \(model.newPrivacy.title)").font(.headline)
        }
    }

    private var cameraPreview: some View {
        CaminoCameraPreview(camera: camera)
            .frame(height: 390)
            .background(.black)
            .clipShape(RoundedRectangle(cornerRadius: 18))
            .overlay(alignment: .topLeading) {
                if kind == .video {
                    Label(silent ? "Bez zvuku" : "Se zvukem",
                          systemImage: silent ? "speaker.slash.fill" : "mic.fill")
                        .padding(10)
                        .background(.black.opacity(0.8), in: Capsule())
                        .foregroundStyle(.white)
                        .padding(12)
                }
            }
    }

    @ViewBuilder private var captureStatus: some View {
        Text(camera.message).font(.headline)
            .accessibilityIdentifier("cameraStatus")
        if let message = model.message {
            Text(message).font(.subheadline).foregroundStyle(.orange)
        }
    }

    @ViewBuilder private var captureControls: some View {
        if kind == .video {
            videoControls
        } else {
            Button("Vyfotit", systemImage: "camera.fill") { camera.capturePhoto() }
                .buttonStyle(.borderedProminent)
                .frame(maxWidth: .infinity, minHeight: 60)
                .disabled(!camera.canCapture)
                .accessibilityIdentifier("takePhoto")
        }
        Button("Přepnout kameru", systemImage: "camera.rotate") {
            Task { await camera.switchCamera() }
        }.disabled(!camera.canCapture)
    }

    @ViewBuilder private var videoControls: some View {
        Toggle("Natočit bez zvuku", isOn: $silent)
            .disabled(camera.isBusy)
            .accessibilityIdentifier("silentVideo")
        Text(silent ? "Tento klip bude trvale označený Bez zvuku."
                    : "Video se zvukem začne jen s povoleným mikrofonem. Bez zvuku se samo nepřepne.")
            .font(.footnote).foregroundStyle(.secondary)
        if camera.phase == .recording || camera.phase == .finishing {
            Text(duration(camera.recordedSeconds))
                .font(.system(.largeTitle, design: .monospaced).bold())
        }
        if camera.phase == .recording || camera.phase == .starting {
            Button("Ukončit a uložit video", systemImage: "stop.fill") {
                camera.stopMovie()
            }
            .buttonStyle(.borderedProminent).tint(.red)
            .frame(maxWidth: .infinity, minHeight: 60)
            .accessibilityIdentifier("stopVideo")
        } else {
            Button("Spustit video", systemImage: "record.circle") {
                Task { await startVideo() }
            }
            .buttonStyle(.borderedProminent)
            .frame(maxWidth: .infinity, minHeight: 60)
            .disabled(!camera.canCapture)
            .accessibilityIdentifier("startVideo")
        }
    }

    @ViewBuilder private var recentMedia: some View {
        if let asset = lastAsset {
            VStack(alignment: .leading, spacing: 8) {
                Text(recentTitle(asset)).font(.headline)
                if asset.kind == .photo,
                   let url = model.originalURL(for: asset) {
                    CaminoPhotoThumbnail(url: url).frame(width: 160, height: 130)
                }
                Text(recentDescription(asset)).font(.subheadline)
                Button("Přidat komentář", systemImage: "mic.fill") {
                    camera.shutdown()
                    model.requestCommentFromCamera(momentID: asset.momentID)
                }
                .disabled(camera.isBusy)
                .accessibilityIdentifier("commentOnRecentMedia")
                Text("Připojeno ke konkrétnímu Momentu. Originál se nemaže.")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
        }
    }

    private func recentTitle(_ asset: LocalMediaAsset) -> String {
        if asset.kind == .photo { return "Fotografie v telefonu" }
        return asset.inspection.partial ? "Částečné video v telefonu" : "Video v telefonu"
    }

    private func recentDescription(_ asset: LocalMediaAsset) -> String {
        if asset.kind == .photo {
            return "\(asset.inspection.width) × \(asset.inspection.height) px"
        }
        let time = duration(Double(asset.inspection.durationMilliseconds ?? 0) / 1_000)
        return time + " · " + (asset.inspection.hasAudio ? "Se zvukem" : "Bez zvuku")
    }

    private func startVideo() async {
        guard await camera.prepareVideoSound(silent: silent) else { return }
        if let url = model.beginVideo(silent: silent) {
            camera.startMovie(at: url)
        } else {
            camera.finishSaving(success: false, message: model.message ?? "Video nezačalo")
        }
    }

    private func leave() {
        if camera.phase == .recording || camera.phase == .starting {
            leaveAfterFinish = true
            camera.stopMovie(interrupted: true)
        } else if !camera.isBusy {
            camera.shutdown()
            model.closeCamera()
        }
    }

    private func time(_ stamp: CaptureStamp) -> String {
        String(stamp.localWall.dropFirst(11).prefix(5))
    }

    private func duration(_ value: Double) -> String {
        let seconds = value.isFinite ? max(0, Int(value)) : 0
        return String(format: "%02d:%02d", seconds / 60, seconds % 60)
    }
}

struct CaminoPhotoThumbnail: View {
    let url: URL
    @State private var image: UIImage?

    var body: some View {
        Group {
            if let image {
                Image(uiImage: image).resizable().scaledToFit()
            } else {
                Image(systemName: "photo").font(.largeTitle)
            }
        }
        .task(id: url) {
            image = await Task.detached(priority: .utility) {
                guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
                      let thumbnail = CGImageSourceCreateThumbnailAtIndex(source, 0,
                        [kCGImageSourceCreateThumbnailFromImageAlways: true,
                         kCGImageSourceThumbnailMaxPixelSize: 320,
                         kCGImageSourceCreateThumbnailWithTransform: true] as CFDictionary) else {
                    return nil as UIImage?
                }
                return UIImage(cgImage: thumbnail)
            }.value
        }
    }
}

struct CaminoMediaDetailView: View {
    @ObservedObject var model: CaminoViewModel
    let moment: LocalMoment
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text(moment.kind.title).font(.title2.bold())
                    Text("\(moment.capture.localWall) · \(moment.privacy.title)")
                        .font(.subheadline)
                    let assets = model.mediaByMoment[moment.id] ?? []
                    ForEach(assets) { asset in
                        VStack(alignment: .leading, spacing: 8) {
                            Text(asset.kind.title).font(.headline)
                            if let url = model.originalURL(for: asset) {
                                if asset.kind == .photo {
                                    CaminoPhotoThumbnail(url: url)
                                        .frame(maxWidth: .infinity, minHeight: 240)
                                } else {
                                    VideoPlayer(player: AVPlayer(url: url))
                                        .frame(height: 240)
                                }
                            } else {
                                Text("Originál teď není dostupný. Nic se nemaže.")
                            }
                            Text("\(asset.inspection.byteCount) B · \(asset.inspection.width) × \(asset.inspection.height) px")
                                .font(.caption)
                            if asset.kind == .video {
                                Text(asset.silentRequested ? "Bez zvuku · vědomě zvoleno"
                                     : asset.inspection.hasAudio ? "Se zvukem" : "Zvuk chybí")
                                if asset.inspection.partial {
                                    Text("Částečný záznam; konec může chybět.")
                                        .foregroundStyle(.orange)
                                }
                            }
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
                    }
                    if assets.isEmpty { Text("Moment zatím nemá fotografii ani video.") }
                    if let audio = model.audio {
                        let linked = model.audioSessionIDs(for: moment.id)
                        ForEach(audio.library.sessions.filter { linked.contains($0.id) }) { session in
                            VStack(alignment: .leading, spacing: 8) {
                                Text("Připojený komentář").font(.headline)
                                ForEach(session.parts) { clip in
                                    Button("Přehrát komentář", systemImage: "play.fill") {
                                        model.play(clip)
                                    }
                                    .disabled(!audio.canPlay)
                                }
                                if audio.phase == .playing {
                                    Button("Zastavit přehrávání") { model.stopPlayback() }
                                }
                            }
                        }
                    }
                    Button("Přidat komentář", systemImage: "mic.fill") {
                        model.requestCommentFromDetail(momentID: moment.id)
                    }
                    .accessibilityIdentifier("commentOnMoment")
                    Button("Přidat fotografii") {
                        dismiss()
                        DispatchQueue.main.async {
                            model.openCamera(.photo, targetMomentID: moment.id)
                        }
                    }
                    Button("Přidat video") {
                        dismiss()
                        DispatchQueue.main.async {
                            model.openCamera(.video, targetMomentID: moment.id)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Moment")
            .toolbar { ToolbarItem(placement: .topBarTrailing) {
                Button("Hotovo") { dismiss() }
            } }
        }
    }
}
