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
            if camera.phase == .recording && model.stopVideoForSafety() {
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

private struct CaminoVideoPlayer: View {
    let url: URL
    @State private var player: AVPlayer?

    var body: some View {
        Group {
            if let player {
                VideoPlayer(player: player)
            } else {
                ProgressView()
                    .frame(maxWidth: .infinity, minHeight: 80)
            }
        }
        .task(id: url) {
            player?.pause()
            player = AVPlayer(url: url)
        }
        .onDisappear {
            player?.pause()
        }
    }
}

struct CaminoMediaDetailView: View {
    @ObservedObject var model: CaminoViewModel
    let moment: LocalMoment
    @Environment(\.dismiss) private var dismiss
    @State private var showTextEditor = false
    @State private var showTitleEditor = false
    @State private var titleAttachment: LocalAttachmentTitle? = nil
    @State private var showChapterPicker = false
    @State private var chapterDate = Date()
    @State private var confirmDiary = false
    @State private var confirmHide = false
    @State private var confirmDelete = false
    @State private var deleteTarget: CaminoDeleteTarget?

    private var current: LocalMoment { model.moment(with: moment.id) ?? moment }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    HStack {
                        Text(current.displayTitle).font(.title2.bold())
                        Spacer()
                        Button {
                            model.setImportant(momentID: current.id,
                                               important: !current.important)
                        } label: {
                            Image(systemName: current.important ? "star.fill" : "star")
                                .font(.title2)
                        }
                        .accessibilityLabel(current.important
                            ? "Odebrat hvězdičku" : "Přidat hvězdičku")
                    }
                    Button(current.title.isEmpty ? "Přidat název" : "Upravit název", systemImage: "pencil") {
                        titleAttachment = nil
                        showTitleEditor = true
                    }
                    .accessibilityIdentifier("editMomentTitle")
                    Text("\(current.kind.title) · Nahráno: \(current.capture.localWall) · kapitola \(current.chapterDate)")
                        .font(.subheadline)
                    if let fix = current.location {
                        Label(fix.approximate ? "GPS uložena · přibližná poloha" : "GPS uložena",
                              systemImage: "location.fill")
                        Text(String(format: "%.6f, %.6f · přesnost ±%.0f m",
                                    fix.latitude, fix.longitude, fix.horizontalAccuracyMeters))
                            .font(.caption).foregroundStyle(.secondary)
                    } else {
                        Label("GPS u tohoto okamžiku není uložená", systemImage: "location.slash")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Label(current.privacy.title,
                          systemImage: current.privacy == .ownerOnly ? "lock.fill" : "book")
                    if model.pendingServerMomentIDs.contains(current.id) {
                        Label("Místní revize · čeká na server",
                              systemImage: "arrow.triangle.2.circlepath")
                            .font(.caption).foregroundStyle(.orange)
                    }
                    if let parentID = current.relatedMomentID,
                       let parent = model.moment(with: parentID) {
                        Label("Patří k: \(parent.kind.title) · \(parent.capture.localWall)",
                              systemImage: "link")
                            .font(.subheadline)
                    }

                    if !current.hidden {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Přidat do tohoto Momentu")
                                .font(.headline)
                            HStack(spacing: 12) {
                                Button {
                                    model.requestCommentFromDetail(momentID: current.id)
                                } label: {
                                    Label("Komentář", systemImage: "mic.fill")
                                        .frame(maxWidth: .infinity, minHeight: 56)
                                }
                                .buttonStyle(.borderedProminent)
                                .accessibilityIdentifier("commentOnMoment")
                                Button {
                                    model.requestPrivateAddendumFromDetail(momentID: current.id)
                                } label: {
                                    Label("Úvaha", systemImage: "lock.bubble.left")
                                        .frame(maxWidth: .infinity, minHeight: 56)
                                }
                                .buttonStyle(.borderedProminent)
                                .accessibilityIdentifier("privateAddendum")
                            }
                            HStack(spacing: 12) {
                                Button {
                                    dismiss()
                                    DispatchQueue.main.async {
                                        model.openCamera(.photo, targetMomentID: current.id)
                                    }
                                } label: {
                                    Label("Přidat fotografii", systemImage: "camera")
                                        .frame(maxWidth: .infinity, minHeight: 56)
                                }
                                .buttonStyle(.borderedProminent)
                                Button {
                                    dismiss()
                                    DispatchQueue.main.async {
                                        model.openCamera(.video, targetMomentID: current.id)
                                    }
                                } label: {
                                    Label("Přidat video", systemImage: "video")
                                        .frame(maxWidth: .infinity, minHeight: 56)
                                }
                                .buttonStyle(.borderedProminent)
                            }
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
                    }

                    let history = model.textHistory(for: current.id)
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Text").font(.headline)
                        if let reader = history.readerRevision {
                            Text(reader.content)
                            Text("\(reader.role.title) · revize \(history.revisions.count)")
                                .font(.caption).foregroundStyle(.secondary)
                        } else {
                            Text("Zatím bez čtenářského textu.")
                                .foregroundStyle(.secondary)
                        }
                        if history.draft != nil {
                            Label("Obnovitelný koncept je uložen jen v telefonu",
                                  systemImage: "square.and.pencil")
                                .font(.caption).foregroundStyle(.orange)
                        }
                        Button("Upravit text", systemImage: "pencil") {
                            showTextEditor = true
                        }
                        .accessibilityIdentifier("editMomentText")
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))

                    // AssetRecord has no separate presentation timestamp yet; Core Data
                    // returns accepted assets in insertion order, so the newest is shown first.
                    let assets = Array((model.mediaByMoment[current.id] ?? []).reversed())
                    ForEach(assets) { asset in
                        VStack(alignment: .leading, spacing: 8) {
                            let name = current.attachmentTitle(.asset, id: asset.id)
                            Text(name.isEmpty ? asset.kind.title : name).font(.headline)
                            if !name.isEmpty { Text(asset.kind.title).font(.caption).foregroundStyle(.secondary) }
                            attachmentTitleButton(.asset, id: asset.id, title: name)
                            Button("Smazat tuto přílohu", systemImage: "trash", role: .destructive) {
                                deleteTarget = .asset(asset.id, asset.kind.title)
                                confirmDelete = true
                            }
                            if let url = model.originalURL(for: asset) {
                                if asset.kind == .photo {
                                    CaminoPhotoThumbnail(url: url)
                                        .frame(maxWidth: .infinity, minHeight: 240)
                                } else {
                                    CaminoVideoPlayer(url: url)
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
                        let linked = model.audioSessionIDs(for: current.id)
                        ForEach(audio.library.sessions.filter { linked.contains($0.id) }) { session in
                            VStack(alignment: .leading, spacing: 8) {
                                let name = current.attachmentTitle(.audioSession, id: session.id)
                                Text(!name.isEmpty ? name : current.kind == .reflection
                                     ? "Úvaha" : "Připojený komentář")
                                    .font(.headline)
                                attachmentTitleButton(.audioSession, id: session.id, title: name)
                                ForEach(session.parts) { clip in
                                    Button("Přehrát komentář", systemImage: "play.fill") {
                                        model.play(clip)
                                    }
                                    .disabled(!audio.canPlay)
                                }
                                if audio.phase == .playing {
                                Button("Zastavit přehrávání") { model.stopPlayback() }
                                }
                                let standalone = current.audioSessionID == session.id
                                    && (current.kind == .comment || current.kind == .reflection)
                                Button(standalone ? "Smazat celý Moment" : "Smazat celou nahrávku",
                                       systemImage: "trash", role: .destructive) {
                                    deleteTarget = standalone ? .moment : .audio(session.id)
                                    confirmDelete = true
                                }
                            }
                        }
                    }
                    Divider()
                    if current.privacy == .ownerOnly {
                        Button(current.kind == .reflection
                               ? "Vložit Úvahu do deníku" : "Nastavit Do deníku",
                               systemImage: "book") {
                            confirmDiary = true
                        }
                        .accessibilityIdentifier("insertIntoDiary")
                    } else {
                        Button("Nastavit Jen pro mě", systemImage: "lock.fill") {
                            model.changePrivacy(momentID: current.id, to: .ownerOnly)
                        }
                        .accessibilityIdentifier("lockMoment")
                    }
                    Button("Změnit den kapitoly", systemImage: "calendar") {
                        chapterDate = date(from: current.chapterDate) ?? Date()
                        showChapterPicker = true
                    }
                    if current.hidden {
                        Button("Obnovit ze skrytých", systemImage: "arrow.uturn.backward") {
                            model.setHidden(momentID: current.id, hidden: false)
                        }
                    } else {
                        Button("Skrýt z deníku", systemImage: "archivebox") {
                            confirmHide = true
                        }
                        .foregroundStyle(.orange)
                        .accessibilityIdentifier("hideMoment")
                    }
                    Button("Smazat celý Moment", systemImage: "trash", role: .destructive) {
                        deleteTarget = .moment
                        confirmDelete = true
                    }
                    .accessibilityIdentifier("deleteMoment")
                }
                .padding()
            }
            .navigationTitle("Moment")
            .toolbar { ToolbarItem(placement: .topBarTrailing) {
                Button("Hotovo") { dismiss() }
            } }
        }
        .sheet(isPresented: $showTitleEditor) {
            CaminoTitleEditorView(model: model, moment: current, attachment: titleAttachment)
        }
        .sheet(isPresented: $showTextEditor) {
            CaminoTextEditorView(model: model, momentID: current.id)
        }
        .sheet(isPresented: $showChapterPicker) {
            NavigationStack {
                Form {
                    DatePicker("Kapitola", selection: $chapterDate,
                               displayedComponents: .date)
                    Text("Čas původní fotografie nebo nahrávky zůstane zachován.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                .navigationTitle("Změnit kapitolu")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Zrušit") { showChapterPicker = false }
                    }
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Uložit") {
                            model.moveMoment(momentID: current.id, to: chapterDate)
                            showChapterPicker = false
                        }
                    }
                }
            }
            .presentationDetents([.medium])
        }
        .alert(current.kind == .reflection ? "Vložit Úvahu do deníku?" : "Změnit soukromí?",
               isPresented: $confirmDiary) {
            Button("Zrušit", role: .cancel) {}
            Button("Vložit do deníku") {
                model.changePrivacy(momentID: current.id, to: .diary)
            }
        } message: {
            Text("Po přijetí serverem může být text a povolené původní audio dostupné Janě v soukromém Vieweru. Změna teď zůstane jen v telefonu a bude čekat na server.")
        }
        .alert("Skrýt Moment?", isPresented: $confirmHide) {
            Button("Zrušit", role: .cancel) {}
            Button("Skrýt", role: .destructive) {
                model.setHidden(momentID: current.id, hidden: true)
            }
        } message: {
            Text("Moment i originály zůstanou v archivu. Skrytí neuvolní místo a již odeslané kopie nelze vzít zpět.")
        }
        .alert("Smazat z telefonu?", isPresented: $confirmDelete) {
            Button("Zrušit", role: .cancel) { deleteTarget = nil }
            Button("Smazat", role: .destructive) {
                guard let target = deleteTarget else { return }
                switch target {
                case .moment:
                    model.deleteMoment(momentID: current.id)
                case .asset(let id, _):
                    model.deleteAsset(assetID: id)
                case .audio(let id):
                    model.deleteAudioSession(sessionID: id, momentID: current.id)
                }
                deleteTarget = nil
            }
        } message: {
            Text(deleteMessage)
        }
    }

    private var deleteMessage: String {
        switch deleteTarget {
        case .moment:
            return "Smaže se celý Moment včetně textu, fotek, videí a nahrávek z telefonu. Již odeslaná kopie na Macu zůstane do samostatného serverového mazání."
        case .asset(_, let title):
            return "Smaže se pouze \(title.lowercased()) z telefonu. Ostatní obsah Momentu zůstane zachovaný."
        case .audio:
            return "Smaže se celá nahrávka včetně všech technických částí z telefonu."
        case .none:
            return "Obsah se smaže z telefonu."
        }
    }

    private func attachmentTitleButton(_ kind: LocalAttachmentTitle.Kind, id: UUID, title: String) -> some View {
        Button(title.isEmpty ? "Přidat název" : "Upravit název", systemImage: "pencil") {
            titleAttachment = LocalAttachmentTitle(kind: kind, targetID: id, title: title)
            showTitleEditor = true
        }
        .accessibilityIdentifier("editAttachmentTitle-\(id.uuidString)")
    }

    private func date(from chapter: String) -> Date? {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.date(from: chapter)
    }
}

private enum CaminoDeleteTarget: Equatable {
    case moment
    case asset(UUID, String)
    case audio(UUID)
}

private struct CaminoTitleEditorView: View {
    @ObservedObject var model: CaminoViewModel
    let moment: LocalMoment
    let attachment: LocalAttachmentTitle?
    @Environment(\.dismiss) private var dismiss
    @State private var draft: String
    @State private var saveFailed = false
    @State private var saving = false

    private var current: LocalMoment { model.moment(with: moment.id) ?? moment }

    init(model: CaminoViewModel, moment: LocalMoment,
         attachment: LocalAttachmentTitle?) {
        self.model = model
        self.moment = moment
        self.attachment = attachment
        _draft = State(initialValue: attachment?.title ?? moment.title)
    }

    var body: some View {
        NavigationStack {
            Form {
                TextField("Nepovinný název", text: $draft)
                    .accessibilityIdentifier("momentTitleEditor")
                Text(attachment == nil
                     ? "Název celého okamžiku, nejvýše 160 znaků. Prázdné pole název odstraní. Média se nemění."
                     : "Název této přílohy, nejvýše 160 znaků. Prázdné pole název odstraní. Celý hlasový komentář má jeden název; média se nemění.")
                    .font(.footnote)
                Text(current.privacy == .ownerOnly
                     ? "Jen pro mě: také název zůstává soukromý."
                     : "Do deníku: po synchronizaci uvidí název také Jana.")
                    .font(.footnote)
                if !LocalMoment.validTitle(draft.trimmingCharacters(in: .whitespacesAndNewlines)) {
                    Text("Použij jeden řádek do 160 znaků.").foregroundStyle(.orange)
                }
                if saveFailed {
                    Text("Název se nepodařilo uložit. Text zůstává zde, zkus to znovu.")
                        .foregroundStyle(.orange)
                }
            }
            .navigationTitle(attachment == nil ? "Název okamžiku" : "Název přílohy")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Zrušit") { dismiss() }
                        .disabled(saving)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Uložit") {
                        saving = true
                        Task { @MainActor in
                            let saved = await model.saveTitle(
                                momentID: current.id, title: draft, attachment: attachment)
                            saving = false
                            if saved { dismiss() }
                            else { saveFailed = true }
                        }
                    }
                    .disabled(saving || !LocalMoment.validTitle(
                        draft.trimmingCharacters(in: .whitespacesAndNewlines)))
                    .accessibilityIdentifier("saveMomentTitle")
                }
            }
        }
        .interactiveDismissDisabled(saving)
    }
}

private struct CaminoTextEditorView: View {
    @ObservedObject var model: CaminoViewModel
    let momentID: UUID
    @Environment(\.dismiss) private var dismiss
    @State private var text = ""
    @State private var loaded = false
    @State private var confirmDiscard = false

    private var history: LocalTextHistory { model.textHistory(for: momentID) }
    private var readerText: String { history.readerRevision?.content ?? "" }

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 12) {
                if history.draft != nil {
                    Label("Obnovený místní koncept · dosud není publikovanou revizí",
                          systemImage: "arrow.counterclockwise")
                        .font(.footnote).foregroundStyle(.orange)
                }
                TextEditor(text: $text)
                    .padding(8)
                    .background(Color(.secondarySystemBackground),
                                in: RoundedRectangle(cornerRadius: 12))
                    .accessibilityIdentifier("momentTextEditor")
                Text("Koncept se ukládá průběžně jen do telefonu. Uložit vytvoří novou lidskou revizi; původní audio, média a starší text zůstávají zachované.")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            .padding()
            .navigationTitle("Upravit text")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Zrušit") {
                        if text != readerText || history.draft != nil {
                            confirmDiscard = true
                        } else {
                            dismiss()
                        }
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Uložit") {
                        model.saveTextDraft(momentID: momentID, content: text)
                        if model.commitTextDraft(momentID: momentID) { dismiss() }
                    }
                    .disabled(text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    .accessibilityIdentifier("saveMomentText")
                }
            }
        }
        .interactiveDismissDisabled()
        .onAppear {
            guard !loaded else { return }
            text = history.draft?.content ?? readerText
            loaded = true
        }
        .onChange(of: text) { _, value in
            guard loaded else { return }
            model.saveTextDraft(momentID: momentID, content: value)
        }
        .alert("Zahodit koncept?", isPresented: $confirmDiscard) {
            Button("Pokračovat v úpravě", role: .cancel) {}
            Button("Zahodit koncept", role: .destructive) {
                model.discardTextDraft(momentID: momentID)
                dismiss()
            }
        } message: {
            Text("Předchozí uložená revize zůstane zachovaná. Zahodí se jen tento rozpracovaný koncept.")
        }
    }
}
