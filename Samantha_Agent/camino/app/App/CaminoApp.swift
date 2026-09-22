import SwiftUI

@main struct CaminoApp: App {
    @StateObject private var model = CaminoViewModel()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            Group {
                if let error = model.startupError {
                    ContentUnavailableView("Úložiště není dostupné",
                        systemImage: "externaldrive.badge.exclamationmark",
                        description: Text(error))
                } else if model.activeTrip == nil {
                    TripSetupView(model: model)
                } else {
                    CaptureHomeView(model: model)
                }
            }
            .overlay {
                if scenePhase != .active {
                    Color(.systemBackground).ignoresSafeArea()
                        .overlay(Label("Camino je skryté", systemImage: "lock.fill"))
                }
            }
            .fullScreenCover(isPresented: $model.showAudio) {
                AudioCaptureView(model: model)
            }
            .fullScreenCover(isPresented: $model.showCamera, onDismiss: {
                model.startPendingComment()
            }) {
                CameraCaptureView(model: model)
            }
            .sheet(item: $model.momentDetail, onDismiss: {
                model.startPendingAudioFromDetail()
            }) { moment in
                CaminoMediaDetailView(model: model, moment: moment)
            }
            .onChange(of: scenePhase) { _, phase in model.scenePhaseChanged(phase) }
        }
    }
}

private struct TripSetupView: View {
    @ObservedObject var model: CaminoViewModel
    @State private var name = "Nová cesta"

    var body: some View {
        NavigationStack {
            Form {
                Section("Cesta") {
                    Text("Cestu můžeš založit bez Macu a bez připojení k síti.")
                    TextField("Název cesty", text: $name)
                        .accessibilityIdentifier("tripName")
                    Button("Vytvořit cestu") { model.createTrip(name: name) }
                        .frame(minHeight: 48)
                        .accessibilityIdentifier("createTrip")
                    Button("Založit Zkoušku") {
                        model.createTrip(name: "Zkouška", isTest: true)
                    }.frame(minHeight: 48)
                }
                Section("Záznam") {
                    Text("Mikrofon si vyžádá povolení až při prvním Komentáři nebo Úvaze.")
                }
                Section("Domácí Mac") {
                    Text("Zatím není připojený. Místní záznam funguje samostatně.")
                }
                if let message = model.message { Text(message).foregroundStyle(.red) }
            }
            .navigationTitle("Připravit Camino")
        }
    }
}

private enum CaminoMomentFilter: String, CaseIterable {
    case all = "Vše"
    case important = "Důležité"
    case reflections = "Úvahy"
}

private struct CaptureHomeView: View {
    @ObservedObject var model: CaminoViewModel
    @State private var showTrips = false
    @State private var showArchive = false
    @State private var selectedDay = Date()
    @State private var filter: CaminoMomentFilter = .all

    private var chapterDate: String {
        CaptureStamp.record(selectedDay, timeZone: .current).chapterDate
    }

    private var selectedMoments: [LocalMoment] {
        model.moments(on: chapterDate).filter { moment in
            switch filter {
            case .all: true
            case .important: moment.important
            case .reflections: moment.kind == .reflection
            }
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    if let trip = model.activeTrip {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(trip.name).font(.title2.bold())
                            Text(Date(), format: .dateTime.day().month(.wide).year())
                                .font(.subheadline).foregroundStyle(.secondary)
                            if trip.isTest {
                                Label("Zkušební cesta", systemImage: "testtube.2")
                                    .font(.subheadline)
                            }
                        }
                    }
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Nové záznamy").font(.headline)
                        Picker("Soukromí nových záznamů", selection: Binding(
                            get: { model.newPrivacy },
                            set: { model.setNewPrivacy($0) }
                        )) {
                            ForEach(LocalPrivacy.allCases, id: \.self) { privacy in
                                Text(privacy.title).tag(privacy)
                            }
                        }
                        .pickerStyle(.segmented)
                        .disabled(model.audioBusy)
                        .accessibilityIdentifier("newPrivacy")
                        Text(model.newPrivacy == .diary
                             ? "Po synchronizaci může být celý Moment dostupný v soukromém Vieweru."
                             : "Jen pro mě zůstane mimo Viewer. Úvaha začíná takto vždy.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                    .padding()
                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))

                    HStack(spacing: 12) {
                        cameraAction("Foto", symbol: "camera", kind: .photo)
                        cameraAction("Video", symbol: "video", kind: .video)
                    }
                    HStack(spacing: 12) {
                        captureAction("Komentář", symbol: "mic.fill", kind: .comment)
                        captureAction("Úvaha", symbol: "bubble.left.and.text.bubble.right.fill",
                                      kind: .reflection)
                    }
                    if let error = model.cameraError {
                        Text(error).font(.footnote).foregroundStyle(.orange)
                    }

                    VStack(alignment: .leading, spacing: 10) {
                        DatePicker("Den deníku", selection: $selectedDay,
                                   displayedComponents: .date)
                            .accessibilityIdentifier("journalDay")
                        Picker("Filtr Momentů", selection: $filter) {
                            ForEach(CaminoMomentFilter.allCases, id: \.self) { value in
                                Text(value.rawValue).tag(value)
                            }
                        }
                        .pickerStyle(.segmented)
                        Text("\(Calendar.current.isDateInToday(selectedDay) ? "Dnes" : chapterDate): \(selectedMoments.count) · Momentů")
                            .font(.headline)
                        if selectedMoments.isEmpty {
                            Text(filter == .all
                                 ? "Zatím tu nejsou žádné záznamy. Souhrn není místně dostupný."
                                 : "Tomuto filtru neodpovídá žádný Moment.")
                                .foregroundStyle(.secondary)
                        } else {
                            ForEach(selectedMoments) { moment in
                                Button { model.momentDetail = moment } label: {
                                    HStack {
                                        Image(systemName: symbol(for: moment.kind))
                                        Text(moment.kind.title)
                                        if moment.important {
                                            Image(systemName: "star.fill").foregroundStyle(.yellow)
                                        }
                                        if moment.privacy == .ownerOnly {
                                            Image(systemName: "lock.fill")
                                        }
                                        Spacer()
                                        Text(String(moment.capture.localWall.dropFirst(11).prefix(5)))
                                            .monospacedDigit()
                                    }
                                }
                                .font(.subheadline)
                                .accessibilityIdentifier("momentRow")
                                Text(moment.privacy.title + (moment.partialAudio ? " · Částečný záznam" : ""))
                                    .font(.caption).foregroundStyle(.secondary)
                                if let text = model.textHistory(for: moment.id).readerRevision?.content {
                                    Text(text).lineLimit(2).font(.caption)
                                }
                                Divider()
                            }
                        }
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))

                    Label(model.moments.isEmpty
                          ? "Místní úložiště připraveno · Mac zatím neověřen"
                          : "Uloženo v telefonu · Mac zatím neověřen",
                          systemImage: "iphone")
                        .font(.subheadline)
                    if model.pendingAudioCount > 0 || model.unmatchedAudioCount > 0 {
                        Label("Rozpracované nebo neověřené audio: \(model.pendingAudioCount + model.unmatchedAudioCount). Soubory zůstávají zachované.",
                              systemImage: "exclamationmark.triangle")
                            .font(.subheadline).foregroundStyle(.orange)
                    }
                    if model.mediaRecovery.pendingCount > 0 ||
                       model.mediaRecovery.orphanCount > 0 ||
                       model.mediaRecovery.missingCount > 0 {
                        Label("Média ke kontrole: \(model.mediaRecovery.pendingCount) rozpracovaných, \(model.mediaRecovery.orphanCount) neznámých, \(model.mediaRecovery.missingCount) nedostupných. Nic se nemaže.",
                              systemImage: "exclamationmark.triangle")
                            .font(.subheadline).foregroundStyle(.orange)
                    }
                    if let message = model.message { Text(message).font(.subheadline) }
                }
                .padding()
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Zachytit")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button("Označit okamžik", systemImage: "mappin") {
                            model.markMoment()
                        }
                        .disabled(model.audioBusy)
                        Button("Cesty", systemImage: "map") { showTrips = true }
                            .disabled(model.audioBusy)
                        Button("Skryté (\(model.hiddenMoments.count))",
                               systemImage: "archivebox") { showArchive = true }
                            .disabled(model.audioBusy)
                    } label: { Label("Nabídka", systemImage: "ellipsis.circle") }
                }
            }
            .sheet(isPresented: $showTrips) { TripListView(model: model) }
            .sheet(isPresented: $showArchive) { CaminoHiddenArchiveView(model: model) }
        }
    }

    private func symbol(for kind: LocalMomentKind) -> String {
        switch kind {
        case .marker: "mappin"
        case .comment, .reflection: "waveform"
        case .photo: "photo"
        case .video: "video"
        }
    }

    private func cameraAction(_ title: String, symbol: String,
                              kind: LocalMediaKind) -> some View {
        Button { model.openCamera(kind) } label: {
            Label(title, systemImage: symbol)
                .frame(maxWidth: .infinity, minHeight: 72)
        }
        .buttonStyle(.borderedProminent)
        .disabled(model.audioBusy || model.cameraError != nil)
        .accessibilityIdentifier(kind == .photo ? "startPhoto" : "startVideoCamera")
    }

    private func captureAction(_ title: String, symbol: String,
                               kind: RecordingKind) -> some View {
        Button { model.startAudio(kind) } label: {
            Label(title, systemImage: symbol)
                .frame(maxWidth: .infinity, minHeight: 72)
        }
        .buttonStyle(.borderedProminent)
        .disabled(model.audioBusy)
        .accessibilityIdentifier(kind == .comment ? "startComment" : "startReflection")
    }
}

private struct CaminoHiddenArchiveView: View {
    @ObservedObject var model: CaminoViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var selected: LocalMoment?

    var body: some View {
        NavigationStack {
            List {
                if model.hiddenMoments.isEmpty {
                    Text("Archiv skrytých Momentů je prázdný.")
                        .foregroundStyle(.secondary)
                }
                ForEach(model.hiddenMoments) { moment in
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text(moment.kind.title)
                            Spacer()
                            Text(moment.capture.localWall)
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        Text(moment.privacy.title + " · Skryté neuvolňuje místo")
                            .font(.caption).foregroundStyle(.secondary)
                        Button("Zobrazit detail") { selected = moment }
                            .buttonStyle(.borderless)
                        Button("Obnovit se stejným soukromím") {
                            model.setHidden(momentID: moment.id, hidden: false)
                        }
                        .buttonStyle(.borderless)
                        .accessibilityIdentifier("restoreHiddenMoment")
                    }
                }
            }
            .navigationTitle("Skryté")
            .toolbar { ToolbarItem(placement: .topBarTrailing) {
                Button("Hotovo") { dismiss() }
            } }
            .sheet(item: $selected) { moment in
                CaminoMediaDetailView(model: model, moment: moment)
            }
        }
    }
}

private struct TripListView: View {
    @ObservedObject var model: CaminoViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Cesty") {
                    ForEach(model.trips) { trip in
                        Button {
                            model.selectTrip(trip.id)
                            dismiss()
                        } label: {
                            HStack {
                                Text(trip.name + (trip.isTest ? " · Zkouška" : ""))
                                Spacer()
                                if trip.active { Image(systemName: "checkmark") }
                            }
                        }
                        .disabled(model.audioBusy)
                    }
                }
                Section("Nová cesta") {
                    TextField("Název cesty", text: $name)
                    Button("Vytvořit") {
                        model.createTrip(name: name)
                        if model.message == nil { dismiss() }
                    }.disabled(model.audioBusy)
                    Button("Založit Zkoušku") {
                        model.createTrip(name: "Zkouška", isTest: true)
                        if model.message == nil { dismiss() }
                    }.disabled(model.audioBusy)
                }
                if let message = model.message { Text(message).foregroundStyle(.red) }
            }
            .navigationTitle("Cesty")
            .toolbar { ToolbarItem(placement: .topBarTrailing) {
                Button("Hotovo") { dismiss() }
            } }
        }
    }
}

private struct AudioCaptureView: View {
    @ObservedObject var model: CaminoViewModel
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    if let audio = model.audio {
                        Text(model.selectedAudioKind == .reflection ? "Úvaha" : "Komentář")
                            .font(.title2.bold())
                        if model.selectedAudioKind == .reflection {
                            if let relatedID = model.audioRelatedMomentID,
                               let related = model.moment(with: relatedID) {
                                Text("Soukromý dovětek k: \(related.kind.title) · \(related.capture.localWall)")
                                    .font(.subheadline)
                            }
                            Text("Soukromí: Jen pro mě. Vložení do deníku vyžaduje pozdější vědomý krok.")
                                .font(.subheadline).foregroundStyle(.secondary)
                        } else if let targetID = model.audioTargetMomentID,
                                  let target = model.moments.first(where: { $0.id == targetID }) {
                            Text("Přidáváš komentář do: \(target.kind.title) · \(target.privacy.title)")
                                .font(.subheadline)
                        } else {
                            Picker("Soukromí celého Komentáře", selection: Binding(
                                get: { model.selectedAudioPrivacy },
                                set: { model.setCurrentAudioPrivacy($0) }
                            )) {
                                ForEach(LocalPrivacy.allCases, id: \.self) { privacy in
                                    Text(privacy.title).tag(privacy)
                                }
                            }
                            .pickerStyle(.segmented)
                            .disabled(audio.phase != .recording)
                            Text("Změna platí pro celý tento Komentář. Režim dalších Momentů zůstane stejný.")
                                .font(.footnote).foregroundStyle(.secondary)
                        }
                        Text(audio.message).font(.headline)
                            .accessibilityIdentifier("captureStatus")
                        if let message = model.message {
                            Text(message).foregroundStyle(.red)
                        }
                        Text(duration(audio.elapsed))
                            .font(.system(.largeTitle, design: .monospaced).bold())
                        Text(audio.input).font(.subheadline)
                        ProgressView(value: meter(audio.power))
                            .accessibilityLabel("Úroveň mikrofonu")

                        if audio.canStop {
                            Button("Ukončit a uložit", systemImage: "stop.fill") {
                                model.stopAudio()
                            }
                            .buttonStyle(.borderedProminent).tint(.red)
                            .frame(minHeight: 56)
                            .accessibilityIdentifier("stopAudio")
                        } else if audio.phase == .interrupted {
                            Button("Pokračovat", systemImage: "mic.fill") {
                                model.continueAudio()
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(!audio.canContinue)
                            Button("Ukončit nahrávání") { model.endInterruptedAudio() }
                        } else if audio.phase == .playing {
                            Button("Zastavit přehrávání") { model.stopPlayback() }
                        } else if audio.phase == .idle || audio.phase == .failed {
                            Button("Spustit nahrávání", systemImage: "mic.fill") {
                                model.startAgainAfterPermission()
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(!audio.canStart)
                            .accessibilityIdentifier("startAudioAgain")
                        }
                        if audio.microphoneDenied {
                            Button("Otevřít nastavení aplikace") {
                                if let url = URL(string: UIApplication.openSettingsURLString) {
                                    UIApplication.shared.open(url)
                                }
                            }
                        }
                        if model.unmatchedAudioCount > 0 {
                            Text("Některé části vyžadují kontrolu. Soubory zůstaly zachované.")
                                .foregroundStyle(.orange)
                        }
                        let allowed = Set(model.moments.flatMap {
                            model.audioSessionIDs(for: $0.id)
                        })
                        ForEach(audio.library.sessions.filter { allowed.contains($0.id) }) { session in
                            VStack(alignment: .leading, spacing: 8) {
                                Text(session.parts.first?.draft.kind == .reflection
                                     ? "Úvaha" : "Komentář")
                                    .font(.headline)
                                ForEach(session.parts) { clip in
                                    Text(clip.recovery != nil
                                         ? "Obnovená částečná nahrávka"
                                         : clip.interrupted ? "Přerušený záznam"
                                         : "Uloženo v telefonu")
                                        .font(.subheadline)
                                    Button("Přehrát", systemImage: "play.fill") {
                                        model.play(clip)
                                    }.disabled(!audio.canPlay)
                                }
                            }
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
                        }
                    } else {
                        Text(model.startupError ?? "Audio není dostupné.")
                    }
                }
                .padding()
            }
            .navigationTitle("Nahrávání")
            .toolbar { ToolbarItem(placement: .topBarLeading) {
                Button("Zpět") { model.leaveAudio() }
                    .disabled(!model.canLeaveAudio)
            } }
        }
        .interactiveDismissDisabled(!model.canLeaveAudio)
        .overlay {
            if scenePhase != .active {
                Color(.systemBackground).ignoresSafeArea()
                    .overlay(Label("Camino je skryté", systemImage: "lock.fill"))
            }
        }
    }

    private func duration(_ value: Double) -> String {
        let seconds = value.isFinite ? max(0, Int(value)) : 0
        return String(format: "%02d:%02d", seconds / 60, seconds % 60)
    }

    private func meter(_ power: Float) -> Double {
        min(1, max(0, Double((power + 60) / 60)))
    }
}
