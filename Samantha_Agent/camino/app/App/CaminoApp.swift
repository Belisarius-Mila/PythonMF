import SwiftUI

@main struct CaminoApp: App {
    @UIApplicationDelegateAdaptor(CaminoAppDelegate.self) private var appDelegate
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
            .onAppear { model.location.setForeground(scenePhase == .active) }
            .onChange(of: scenePhase) { _, phase in model.scenePhaseChanged(phase) }
        }
    }
}

private struct TripSetupView: View {
    @ObservedObject var model: CaminoViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var showTrips = false
    @State private var showSync = false
    @State private var name = "Nový projekt"
    @State private var showMediaReview = false
    @State private var hasStart = false
    @State private var startDate = Date()
    @State private var hasEnd = false
    @State private var endDate = Date()

    private var details: LocalProjectDetails {
        LocalProjectDetails(startDate: hasStart ? ProjectDateSupport.string(startDate) : nil,
                            endDate: hasEnd ? ProjectDateSupport.string(endDate) : nil)
    }

    var body: some View {
        NavigationStack {
            Form {
                if !model.trips.isEmpty || !model.projectTrash.isEmpty {
                    Section("Tvoje projekty") {
                        Button("Projekty a koš", systemImage: "map") { showTrips = true }
                            .accessibilityIdentifier("projectList")
                        Text("Vyber jiný projekt nebo se podívej na stav žádosti o smazání.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }
                if model.mediaRecovery.pendingCount > 0 {
                    Section("Média ke kontrole") {
                        Button("Zkontrolovat a odstranit pokusy") { showMediaReview = true }
                            .accessibilityIdentifier("reviewPendingMedia")
                    }
                }
                Section("Projekt") {
                    Text("Projekt můžeš založit bez Macu a bez připojení k síti.")
                    TextField("Název projektu", text: $name)
                        .accessibilityIdentifier("tripName")
                    ProjectDateFields(hasStart: $hasStart, startDate: $startDate,
                                      hasEnd: $hasEnd, endDate: $endDate,
                                      startToggleID: "newProjectHasStart",
                                      startDateID: "newProjectStartDate",
                                      endToggleID: "newProjectHasEnd",
                                      endDateID: "newProjectEndDate")
                    if !details.valid {
                        Text("Datum konce nesmí předcházet začátku.").foregroundStyle(.red)
                    }
                    Button("Vytvořit projekt") {
                        if model.createTrip(name: name, details: details) { dismiss() }
                    }
                    .frame(minHeight: 48)
                    .disabled(!model.canManageProjects || !details.valid || name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    .accessibilityIdentifier("createTrip")
                    Button("Založit Zkoušku") {
                        if model.createTrip(name: "Zkouška", isTest: true) { dismiss() }
                    }
                    .frame(minHeight: 48)
                    .disabled(!model.canManageProjects)
                }
                Section("Záznam") {
                    Text("Mikrofon si vyžádá povolení až při prvním Komentáři nebo Úvaze.")
                }
                Section("Domácí Mac") {
                    Button("Uložení a přenosy", systemImage: "arrow.triangle.2.circlepath") {
                        showSync = true
                    }
                    .disabled(model.sync == nil || model.audioBusy)
                    .accessibilityIdentifier("setupSync")
                    Text("Tady připojíš Mac a ověříš doručení žádosti o smazání. Obnovení cesty potvrdíš na Macu.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                if let message = model.message { Text(message).foregroundStyle(.red) }
            }
            .navigationTitle("Připravit projekt")
            .sheet(isPresented: $showTrips) { TripListView(model: model) }
            .sheet(isPresented: $showMediaReview) { PendingMediaReviewView(model: model) }
            .sheet(isPresented: $showSync) {
                if let sync = model.sync { CaminoSyncView(sync: sync) }
            }
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
    @State private var showSync = false
    @State private var showMediaReview = false
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
                            Text("Camino").font(.title2.bold())
                            Text(trip.name).font(.headline)
                            Text(Date(), format: .dateTime.day().month(.wide).year())
                                .font(.subheadline).foregroundStyle(.secondary)
                            if let period = ProjectDateSupport.period(trip.projectDetails) {
                                Text("Období: \(period)")
                                    .font(.subheadline).foregroundStyle(.secondary)
                                    .accessibilityIdentifier("projectPeriod")
                            }
                            if trip.projectDetails.status == .archived {
                                Text("Archivovaný projekt – záznamy lze dál číst, nové pořizování je vypnuté.")
                                    .font(.subheadline).foregroundStyle(.secondary)
                                    .accessibilityIdentifier("archivedProjectBanner")
                            }
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

                    CaminoLocationStatusView(location: model.location)

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
                                        Text(moment.displayTitle).lineLimit(2)
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
                                let attachments = model.attachmentSummary(for: moment.id)
                                if !attachments.isEmpty {
                                    Text(attachments).font(.caption).foregroundStyle(.secondary)
                                }
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
                    if model.mediaRecovery.pendingCount > 0 {
                        Button("Zkontrolovat a odstranit pokusy") { showMediaReview = true }
                            .accessibilityIdentifier("reviewPendingMedia")
                    }
                    if let message = model.message { Text(message).font(.subheadline) }
                }
                .padding()
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Caminos de descubrimiento")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("Caminos de descubrimiento")
                        .font(.subheadline.weight(.semibold))
                        .lineLimit(1)
                        .minimumScaleFactor(0.65)
                        .accessibilityIdentifier("caminoHeading")
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button("Označit okamžik", systemImage: "mappin") {
                            model.markMoment()
                        }
                        .disabled(!model.canCaptureInActiveProject || model.audioBusy || model.awaitingLocation)
                        Button("Projekty", systemImage: "map") { showTrips = true }
                            .accessibilityIdentifier("projectList")
                            .disabled(!model.canManageProjects)
                        Button("Skryté (\(model.hiddenMoments.count))",
                               systemImage: "archivebox") { showArchive = true }
                            .disabled(model.audioBusy)
                        Button("Uložení a přenosy", systemImage: "arrow.triangle.2.circlepath") {
                            showSync = true
                        }
                        .disabled(model.audioBusy || model.sync == nil)
                    } label: { Label("Nabídka", systemImage: "ellipsis.circle") }
                }
            }
            .sheet(isPresented: $showTrips) { TripListView(model: model) }
            .sheet(isPresented: $showArchive) { CaminoHiddenArchiveView(model: model) }
            .sheet(isPresented: $showMediaReview) { PendingMediaReviewView(model: model) }
            .sheet(isPresented: $showSync) {
                if let sync = model.sync { CaminoSyncView(sync: sync) }
            }
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
        .disabled(!model.canCaptureInActiveProject || model.audioBusy || model.cameraError != nil)
        .accessibilityIdentifier(kind == .photo ? "startPhoto" : "startVideoCamera")
    }

    private func captureAction(_ title: String, symbol: String,
                               kind: RecordingKind) -> some View {
        Button { model.startAudio(kind) } label: {
            Label(title, systemImage: symbol)
                .frame(maxWidth: .infinity, minHeight: 72)
        }
        .buttonStyle(.borderedProminent)
        .disabled(!model.canCaptureInActiveProject || model.audioBusy || model.awaitingLocation)
        .accessibilityIdentifier(kind == .comment ? "startComment" : "startReflection")
    }
}

private struct PendingMediaReviewView: View {
    @ObservedObject var model: CaminoViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var selection: [LocalPendingMediaReview] = []
    @State private var confirming = false

    private var emptyItems: [LocalPendingMediaReview] {
        model.mediaReviewItems.filter { $0.isEmpty && model.canDiscardMedia($0) }
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("Tady jsou nedokončené pokusy. Přijaté fotografie a videa zůstanou zachované.")
                    if !emptyItems.isEmpty {
                        Button("Odstranit prázdné pokusy (\(emptyItems.count))", role: .destructive) {
                            selection = emptyItems
                            confirming = true
                        }
                        .accessibilityIdentifier("discardEmptyMedia")
                    }
                    Button("Obnovit seznam") { model.loadMediaReview() }
                        .disabled(model.mediaReviewBusy)
                }
                if let error = model.mediaReviewError { Text(error).foregroundStyle(.orange) }
                if model.mediaReviewItems.isEmpty && model.mediaReviewError == nil {
                    Text("Žádné nedokončené pokusy.")
                        .accessibilityIdentifier("noPendingMedia")
                }
                ForEach(model.mediaReviewItems) { item in
                    Section {
                        Text(item.intent.kind == .video ? "Video" : "Fotografie").font(.headline)
                        Text(Date(timeIntervalSince1970: Double(item.intent.capture.utcMilliseconds) / 1000),
                             format: .dateTime.day().month().year().hour().minute())
                        Text(model.trips.first { $0.id == item.intent.tripID }?.name ??
                             "Projekt · \(item.intent.tripID.uuidString.suffix(8))")
                            .foregroundStyle(.secondary)
                        if item.isEmpty {
                            Text("Prázdný pokus · žádný soubor")
                        } else {
                            Text("Nedokončený soubor · \(ByteCountFormatter.string(fromByteCount: Int64(clamping: item.byteCount), countStyle: .file))")
                        }
                        if model.projectTrash.contains(where: { $0.tripID == item.intent.tripID && $0.blocksProject }) {
                            Text("Patří k cestě čekající na smazání. Její koš dokončíš na Macu.")
                                .font(.footnote)
                        }
                        Button("Odstranit tento pokus", role: .destructive) {
                            selection = [item]
                            confirming = true
                        }
                        .disabled(!model.canDiscardMedia(item))
                        .accessibilityIdentifier("discardPendingMedia-\(item.id.uuidString)")
                    }
                }
            }
            .navigationTitle("Nedokončená média")
            .toolbar { ToolbarItem(placement: .topBarTrailing) {
                Button("Hotovo") { dismiss() }.disabled(model.mediaReviewBusy)
            } }
            .onAppear { model.loadMediaReview() }
            .alert("Odstranit vybrané nedokončené pokusy?", isPresented: $confirming) {
                Button("Odstranit natrvalo", role: .destructive) {
                    let reviewed = selection
                    Task { await model.discardMediaReview(reviewed) }
                }
                Button("Zrušit", role: .cancel) {}
            } message: {
                Text(selection.allSatisfy(\.isEmpty)
                    ? "Odstraní se \(selection.count) prázdných pokusů bez souboru. Hotové záznamy zůstanou zachované."
                    : "Vybraný nedokončený soubor se smaže natrvalo. Hotové záznamy zůstanou zachované.")
            }
        }
    }
}

private struct CaminoSyncView: View {
    @ObservedObject var sync: CaminoSyncCoordinator
    @Environment(\.dismiss) private var dismiss
    @State private var confirmCellular = false
    @State private var confirmEmptyBootstrap = false
    @State private var confirmFilmDay = false
    @State private var selectedFilmDayID: UUID?

    var body: some View {
        NavigationStack {
            Form {
                Section("Domácí Mac") {
                    TextField("Soukromá HTTPS adresa", text: $sync.serverURL)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        .autocorrectionDisabled()
                        .accessibilityIdentifier("syncServerURL")
                    SecureField(sync.tokenStored ? "Token je uložený" : "Soukromý token",
                                text: $sync.tokenInput)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .accessibilityIdentifier("syncToken")
                    Button("Uložit připojení") { sync.saveConfiguration() }
                        .accessibilityIdentifier("saveSyncConfiguration")
                    Text("Token zůstává v Keychain. Aplikace přijímá jen HTTPS a nemá veřejný fallback.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                Section("Telefon") {
                    statusAxis(sync.dashboard.phone, identifier: "c05cPhoneStatus")
                    LabeledContent("Prioritní metadata", value: "\(sync.stats.metadataCount)")
                    LabeledContent("Čekající média", value: "\(sync.stats.mediaCount)")
                    LabeledContent("Čekající objem", value: formatBytes(sync.stats.mediaBytes))
                }
                Section("Mac") {
                    statusAxis(sync.dashboard.mac, identifier: "syncStatus",
                               detailOverride: sync.detailText)
                    if sync.reconciliationRequired {
                        Label("Po změně epochy je nutná servisní kontrola. Nic se automaticky nemaže.",
                              systemImage: "exclamationmark.shield")
                            .foregroundStyle(.orange)
                        Button("Ověřit a dokončit obnovu") { sync.completeRecovery() }
                            .disabled(sync.busy || !sync.configurationReady)
                            .accessibilityIdentifier("completeRecovery")
                        Text("Jen na Wi‑Fi. Povolí pokračování pouze při shodných úplných kopiích. Při rozdílu zůstane obnova k řešení.")
                            .font(.footnote).foregroundStyle(.secondary)
                        Button("Připojit k novému prázdnému serveru") {
                            confirmEmptyBootstrap = true
                        }
                        .disabled(sync.busy || !sync.configurationReady)
                        .accessibilityIdentifier("bootstrapEmptyServer")
                        Text("Použij jen tehdy, když byly všechny Momenty a média v telefonu smazané. Místní soubory se nemažou.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }
                Section("Další záloha") {
                    statusAxis(sync.dashboard.backup, identifier: "c05cBackupStatus")
                }
                Section("AI") {
                    statusAxis(sync.dashboard.ai, identifier: "c05cAIStatus")
                }
                Section("Film · 6. 10. 2026") {
                    ForEach(sync.filmDays.filter { $0.localDate == "2026-10-06" }) { day in
                        Button("Ověřit a uzavřít den") {
                            selectedFilmDayID = day.id
                            confirmFilmDay = true
                        }
                        .disabled(sync.busy || !sync.configurationReady)
                        .accessibilityIdentifier("closeFilmDay")
                    }
                    Text(sync.filmResult).font(.footnote).foregroundStyle(.secondary)
                        .accessibilityIdentifier("filmDayResult")
                    Text("Telefon a Mac musí mít shodný úplný den. Soukromé Úvahy se do filmu nezařadí; video zůstane celé. Uzavření uloží projekt na Macu, film zatím nevyrenderuje.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
                Section("Ovládání") {
                    Button("Synchronizovat nyní", systemImage: "arrow.clockwise") {
                        sync.synchronizeNow()
                    }
                    .disabled(sync.busy || sync.paused || !sync.configurationReady)
                    .accessibilityIdentifier("syncNow")
                    Button(sync.paused ? "Pokračovat v přenosech" : "Pozastavit přenosy",
                           systemImage: sync.paused ? "play.fill" : "pause.fill") {
                        sync.setPaused(!sync.paused)
                    }
                    .accessibilityIdentifier("toggleSyncPause")
                    Button("Odeslat zobrazenou dávku i přes mobilní data",
                           systemImage: "antenna.radiowaves.left.and.right") {
                        confirmCellular = true
                    }
                    .disabled(sync.cellularStats.mediaCount == 0 || sync.cellularGranted)
                    .accessibilityIdentifier("grantCellularBatch")
                    Text("Jednorázové povolení se nevztahuje na fotografie, audio ani video pořízené později.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Uložení a přenosy")
            .toolbar { ToolbarItem(placement: .topBarTrailing) {
                Button("Hotovo") { dismiss() }
            } }
            .onAppear { sync.refreshInventory() }
            .alert("Povolit mobilní data jen pro tuto dávku?", isPresented: $confirmCellular) {
                Button("Zrušit", role: .cancel) {}
                Button("Povolit tuto dávku") { sync.grantCellularForDisplayedBatch() }
            } message: {
                Text("\(sync.cellularStats.mediaCount) souborů · \(formatBytes(sync.cellularStats.mediaBytes)). Retry může přenést další bajty; nové záznamy povolení nezdědí.")
            }
            .alert("Připojit k novému prázdnému serveru?", isPresented: $confirmEmptyBootstrap) {
                Button("Zrušit", role: .cancel) { }
                Button("Přijmout nový server", role: .destructive) {
                    sync.bootstrapEmptyServer()
                }
            } message: {
                Text("Ověří se prázdný telefon i server. Resetuje se pouze historie synchronizace; Momenty, média a nastavení telefonu zůstanou.")
            }
            .alert("Uzavřít den 6. 10. 2026 pro film?", isPresented: $confirmFilmDay) {
                Button("Zrušit", role: .cancel) { selectedFilmDayID = nil }
                Button("Ověřit a uložit projekt") {
                    if let selectedFilmDayID { sync.closeFilmDay(selectedFilmDayID) }
                    selectedFilmDayID = nil
                }
            } message: {
                Text("Porovná se inventář telefonu a Macu a ověří se originály. Samotný film se nyní nevytvoří.")
            }
        }
    }

    private func formatBytes(_ value: Int64) -> String {
        ByteCountFormatter.string(fromByteCount: value, countStyle: .file)
    }

    @ViewBuilder private func statusAxis(_ axis: CaminoStatusAxis,
                                         identifier: String,
                                         detailOverride: String? = nil) -> some View {
        Label(axis.value, systemImage: statusSymbol(axis.tone))
            .font(.headline)
            .foregroundStyle(statusColor(axis.tone))
            .accessibilityIdentifier(identifier)
        Text(detailOverride ?? axis.detail).font(.subheadline).foregroundStyle(.secondary)
            .accessibilityIdentifier(identifier + "Detail")
    }

    private func statusSymbol(_ tone: CaminoStatusTone) -> String {
        switch tone {
        case .verified: "checkmark.circle.fill"
        case .waiting: "clock.fill"
        case .attention: "exclamationmark.triangle.fill"
        case .neutral: "minus.circle"
        }
    }

    private func statusColor(_ tone: CaminoStatusTone) -> Color {
        switch tone {
        case .verified: .green
        case .waiting: .orange
        case .attention: .red
        case .neutral: .secondary
        }
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

private enum ProjectDateSupport {
    static var timeZone: TimeZone { TimeZone(secondsFromGMT: 0)! }
    static var calendar: Calendar {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = timeZone
        return calendar
    }

    static func string(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = calendar
        formatter.timeZone = timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }

    static func date(_ value: String?) -> Date {
        guard let value else { return Date() }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = calendar
        formatter.timeZone = timeZone
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.date(from: value) ?? Date()
    }

    static func period(_ details: LocalProjectDetails) -> String? {
        switch (details.startDate, details.endDate) {
        case let (start?, end?): return "\(start) – \(end)"
        case let (start?, nil): return "od \(start)"
        case let (nil, end?): return "do \(end)"
        case (nil, nil): return nil
        }
    }
}

private struct ProjectDateFields: View {
    @Binding var hasStart: Bool
    @Binding var startDate: Date
    @Binding var hasEnd: Bool
    @Binding var endDate: Date
    let startToggleID: String
    let startDateID: String
    let endToggleID: String
    let endDateID: String

    var body: some View {
        Toggle("Má datum začátku", isOn: $hasStart)
            .accessibilityIdentifier(startToggleID)
        if hasStart {
            DatePicker("Začátek", selection: $startDate, displayedComponents: .date)
                .environment(\.calendar, ProjectDateSupport.calendar)
                .environment(\.timeZone, ProjectDateSupport.timeZone)
                .accessibilityIdentifier(startDateID)
        }
        Toggle("Má datum konce", isOn: $hasEnd)
            .accessibilityIdentifier(endToggleID)
        if hasEnd {
            DatePicker("Konec", selection: $endDate, displayedComponents: .date)
                .environment(\.calendar, ProjectDateSupport.calendar)
                .environment(\.timeZone, ProjectDateSupport.timeZone)
                .accessibilityIdentifier(endDateID)
        }
    }
}

private struct TripListView: View {
    @ObservedObject var model: CaminoViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var hasStart = false
    @State private var startDate = Date()
    @State private var hasEnd = false
    @State private var endDate = Date()
    @State private var editingTrip: LocalTrip?

    private var newProjectDetails: LocalProjectDetails {
        LocalProjectDetails(startDate: hasStart ? ProjectDateSupport.string(startDate) : nil,
                            endDate: hasEnd ? ProjectDateSupport.string(endDate) : nil)
    }

    var body: some View {
        NavigationStack {
            Form {
                if let trip = model.activeTrip {
                    Section("Současný projekt") {
                        Button("Upravit projekt") { editingTrip = trip }
                            .accessibilityIdentifier("editCurrentProject")
                            .disabled(!model.canManageProjects)
                    }
                }
                Section("Probíhající") {
                    ForEach(model.trips.filter { $0.projectDetails.status == .active }) { trip in
                        projectRow(trip)
                    }
                }
                Section("Archivované") {
                    ForEach(model.trips.filter { $0.projectDetails.status == .archived }) { trip in
                        projectRow(trip)
                    }
                }
                if !model.projectTrash.isEmpty {
                    Section("Koš a žádosti o smazání") {
                        ForEach(model.projectTrash.filter { $0.state != "restored" }) { item in
                            VStack(alignment: .leading) {
                                Text(item.name.isEmpty ? "Projekt · \(item.tripID.uuidString.suffix(8))" : item.name)
                                Text(item.statusText).font(.footnote).foregroundStyle(.secondary)
                                if let deadline = item.purgeMilliseconds {
                                    Text("Lhůta Macu: \(Date(timeIntervalSince1970: Double(deadline) / 1000).formatted())")
                                        .font(.caption)
                                }
                            }
                        }
                        Text("Celou cestu smažeš žádostí zde a potvrzením ve střižně na Macu. Offline telefon čeká na ověřený výmaz Macu.")
                            .font(.footnote)
                    }
                }
                Section("Nový projekt") {
                    Text("Nový projekt začíná s Viewerem vypnutým. Přístup pro Janu povolíš na Macu.")
                        .font(.footnote).foregroundStyle(.secondary)
                    TextField("Název projektu", text: $name)
                        .accessibilityIdentifier("newProjectName")
                    ProjectDateFields(hasStart: $hasStart, startDate: $startDate,
                                      hasEnd: $hasEnd, endDate: $endDate,
                                      startToggleID: "newProjectHasStart",
                                      startDateID: "newProjectStartDate",
                                      endToggleID: "newProjectHasEnd",
                                      endDateID: "newProjectEndDate")
                    if !newProjectDetails.valid {
                        Text("Datum konce nesmí předcházet začátku.").foregroundStyle(.red)
                    }
                    Button("Vytvořit") {
                        if model.createTrip(name: name, details: newProjectDetails) { dismiss() }
                    }
                    .accessibilityIdentifier("createProject")
                    .disabled(!model.canManageProjects || !newProjectDetails.valid || name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    Button("Založit Zkoušku") {
                        if model.createTrip(name: "Zkouška", isTest: true) { dismiss() }
                    }
                    .disabled(!model.canManageProjects)
                }
                if let message = model.message { Text(message).foregroundStyle(.red) }
            }
            .navigationTitle("Projekty")
            .toolbar { ToolbarItem(placement: .topBarTrailing) {
                Button("Hotovo") { dismiss() }
            } }
            .sheet(item: $editingTrip) { trip in
                TripEditView(model: model, trip: trip)
            }
        }
    }

    @ViewBuilder private func projectRow(_ trip: LocalTrip) -> some View {
        Button {
            if model.selectTrip(trip.id) { dismiss() }
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    Text(trip.name + (trip.isTest ? " · Zkouška" : ""))
                    if let period = ProjectDateSupport.period(trip.projectDetails) {
                        Text(period).font(.caption).foregroundStyle(.secondary)
                    }
                    if model.trips.filter({ $0.name == trip.name }).count > 1 {
                        Text("Projekt · \(trip.id.uuidString.suffix(8))")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
                Spacer()
                if trip.active { Image(systemName: "checkmark") }
            }
        }
        .accessibilityIdentifier("projectRow-\(trip.id.uuidString)")
        .disabled(!model.canManageProjects)
    }
}

private struct TripEditView: View {
    @ObservedObject var model: CaminoViewModel
    let trip: LocalTrip
    @Environment(\.dismiss) private var dismiss
    @State private var name: String
    @State private var isTest: Bool
    @State private var hasStart: Bool
    @State private var startDate: Date
    @State private var hasEnd: Bool
    @State private var endDate: Date
    @State private var isArchived: Bool
    @State private var confirmProjectTrash = false

    init(model: CaminoViewModel, trip: LocalTrip) {
        self.model = model
        self.trip = trip
        _name = State(initialValue: trip.name)
        _isTest = State(initialValue: trip.isTest)
        _hasStart = State(initialValue: trip.projectDetails.startDate != nil)
        _startDate = State(initialValue: ProjectDateSupport.date(trip.projectDetails.startDate))
        _hasEnd = State(initialValue: trip.projectDetails.endDate != nil)
        _endDate = State(initialValue: ProjectDateSupport.date(trip.projectDetails.endDate))
        _isArchived = State(initialValue: trip.projectDetails.status == .archived)
    }

    private var details: LocalProjectDetails {
        LocalProjectDetails(startDate: hasStart ? ProjectDateSupport.string(startDate) : nil,
                            endDate: hasEnd ? ProjectDateSupport.string(endDate) : nil,
                            status: isArchived ? .archived : .active)
    }
    private var validName: Bool { !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Název projektu", text: $name)
                        .accessibilityIdentifier("editTripName")
                    Toggle("Zkušební projekt", isOn: $isTest)
                        .accessibilityIdentifier("editProjectIsTest")
                    ProjectDateFields(hasStart: $hasStart, startDate: $startDate,
                                      hasEnd: $hasEnd, endDate: $endDate,
                                      startToggleID: "editProjectHasStart",
                                      startDateID: "editProjectStartDate",
                                      endToggleID: "editProjectHasEnd",
                                      endDateID: "editProjectEndDate")
                    Toggle("Archivovat projekt", isOn: $isArchived)
                        .accessibilityIdentifier("editProjectArchived")
                } footer: {
                    Text("Archivace ponechá existující záznamy i jejich přenosy. Projekt můžeš znovu otevřít vypnutím archivace a uložením.")
                }
                if !validName {
                    Text("Zadej název projektu.").foregroundStyle(.red)
                } else if !details.valid {
                    Text("Zkontroluj data: použij platná data a datum konce nesmí předcházet začátku.")
                        .foregroundStyle(.red)
                }
                if let message = model.message { Text(message).foregroundStyle(.red) }
                Section {
                    Button("Požádat o smazání celé cesty", role: .destructive) { confirmProjectTrash = true }
                        .disabled(!model.canManageProjects || model.sync?.busy == true)
                        .accessibilityIdentifier("requestProjectTrash")
                } footer: {
                    Text("Cesta se skryje a zastaví se její přenosy. Na Macu potvrdíš přesun do koše na 7 dní; tam ji můžeš včas obnovit. Po výmazu Macu odstraní iPhone i místní data. Kopie v aplikaci Fotky a mimo Camino zůstávají samostatné.")
                }
            }
            .confirmationDialog("Požádat o smazání celé cesty a všech jejích dat?", isPresented: $confirmProjectTrash,
                                titleVisibility: .visible) {
                Button("Skrýt cestu a odeslat žádost Macu", role: .destructive) {
                    if model.requestProjectTrash(trip.id) { dismiss() }
                }
            }
            .navigationTitle("Upravit projekt")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Zrušit") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Uložit") {
                        if model.updateTrip(trip.id, name: name, isTest: isTest, details: details) { dismiss() }
                    }
                    .disabled(!model.canManageProjects || !validName || !details.valid)
                }
            }
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
