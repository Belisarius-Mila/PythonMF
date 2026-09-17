import Combine
import Foundation

@MainActor final class TransferViewModel: ObservableObject {
    static let shared = TransferViewModel()
    nonisolated static let syntheticByteCount: Int64 = 96 * 1024 * 1024 + 257
    nonisolated static let chunkSize = 8 * 1024 * 1024

    @Published var serverURL = UserDefaults.standard.string(forKey: "serverURL") ?? ""
    @Published var tokenInput = ""
    @Published private(set) var tokenStored = false
    @Published private(set) var statusText = "Připravuji lokální frontu…"
    @Published private(set) var detailText = ""
    @Published private(set) var progress = 0.0
    @Published private(set) var preparedCount = 0
    @Published private(set) var isBusy = false
    @Published private(set) var journal: TransferJournal?

    private let store: TransferJournalStore
    private let preparer: FileChunkPreparer
    private let keychain = KeychainTokenStore()
    private let driver: BackgroundTransferDriver
    private let monitor: TransferNetworkMonitor
    private var path = NetworkPathState(available: false, expensive: false)
    private var partialSent: [Int: Int64] = [:]
    private var reconciling = false

    private init() {
        do {
            let applicationSupport = try FileManager.default.url(
                for: .applicationSupportDirectory,
                in: .userDomainMask,
                appropriateFor: nil,
                create: true
            )
            let root = applicationSupport.appendingPathComponent(
                "CaminoTransferTest",
                isDirectory: true
            )
            if ProcessInfo.processInfo.arguments.contains("-uiTestReset") {
                try? FileManager.default.removeItem(at: root)
            }
            store = try TransferJournalStore(root: root)
            preparer = try FileChunkPreparer(root: store.preparedRoot)
        } catch {
            fatalError("Camino Transfer storage initialization failed")
        }
        driver = Self.makeDriver()
        monitor = Self.makeMonitor()
        monitor.start()
        tokenStored = (try? keychain.load()) != nil
        do {
            journal = try store.load()
            refreshLocalDisplay()
            statusText = truthfulText(for: journal!.phase)
            detailText = "Obnovená trvalá fronta čeká na porovnání se serverem."
        } catch TransferJournalError.missingJournal {
            statusText = "Připraveno vytvořit syntetickou dávku"
            detailText = "Žádná rozpracovaná dávka."
        } catch {
            statusText = "Fronta vyžaduje pozornost"
            detailText = "Lokální journal je neplatný; zdrojová data nebyla smazána."
        }
    }

    var canCreateBatch: Bool {
        !isBusy && (journal == nil || journal?.phase == .verified)
    }

    var canSynchronize: Bool {
        !isBusy && journal != nil && journal?.phase != .verified && journal?.phase != .paused
    }

    var canPause: Bool {
        journal != nil && journal?.phase != .paused && journal?.phase != .verified
    }

    var canResume: Bool { journal?.phase == .paused }
    var cellularAllowed: Bool { journal?.cellularAllowed == true }

    func saveConfiguration() {
        do {
            let cleanURL = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
            let token = tokenInput.trimmingCharacters(in: .whitespacesAndNewlines)
            guard let url = URL(string: cleanURL) else {
                throw TransferProtocolError.invalidBaseURL
            }
            let existing = try keychain.load()
            let selected = token.isEmpty ? (existing ?? "") : token
            _ = try TransferEndpoint(baseURL: url, bearerToken: selected)
            if !token.isEmpty { try keychain.save(token) }
            UserDefaults.standard.set(cleanURL, forKey: "serverURL")
            serverURL = cleanURL
            tokenInput = ""
            tokenStored = true
            detailText = "Soukromá HTTPS konfigurace je uložená; token zůstává v Keychain."
        } catch {
            detailText = "Konfigurace musí mít soukromou HTTPS adresu a platný token."
        }
    }

    func createSyntheticBatch() async {
        guard canCreateBatch else { return }
        isBusy = true
        statusText = "Vytvářím syntetický zdroj…"
        detailText = "Osobní média se nečtou."
        do {
            let sourcesRoot = store.sourcesRoot
            let source = try await Task.detached(priority: .userInitiated) {
                try SyntheticSourceFactory.create(
                    in: sourcesRoot,
                    byteCount: Self.syntheticByteCount
                )
            }.value
            let batchID = UUID()
            let created = TransferJournal(
                assetID: "asset-\(UUID().uuidString.lowercased())",
                batchID: batchID,
                sourceFileName: source.fileName,
                byteCount: source.byteCount,
                sha256: source.sha256,
                chunkSize: Self.chunkSize,
                chunkCount: Int(
                    (source.byteCount + Int64(Self.chunkSize) - 1) / Int64(Self.chunkSize)
                )
            )
            try store.save(created)
            journal = created
            partialSent = [:]
            refreshLocalDisplay()
            statusText = "Dávka připravena"
            detailText = "Nová dávka nemá povolená mobilní data."
        } catch {
            statusText = "Dávku se nepodařilo vytvořit"
            detailText = "Žádný serverový úspěch nebyl zaznamenán."
        }
        isBusy = false
    }

    func setCellularAllowed(_ allowed: Bool) async {
        guard var current = journal, current.phase != .verified else { return }
        current.cellularBatchID = allowed ? current.batchID : nil
        do {
            try store.save(current)
            journal = current
            await driver.cancelAll()
            detailText = allowed
                ? "Mobilní data platí jen pro tuto existující dávku."
                : "Dávka čeká na neplacenou síť."
        } catch {
            detailText = "Změnu mobilního povolení se nepodařilo uložit."
        }
    }

    func synchronize() async {
        await reconcile(userInitiated: true)
    }

    func pause() async {
        guard var current = journal else { return }
        current.phase = .paused
        current.lastError = nil
        try? store.save(current)
        journal = current
        await driver.suspendAll()
        statusText = "Pozastaveno"
        detailText = "Nové části se neplánují."
    }

    func resume() async {
        guard var current = journal, current.phase == .paused else { return }
        current.phase = .uploading
        try? store.save(current)
        journal = current
        await driver.resumeAll()
        await reconcile(userInitiated: true)
    }

    func applicationBecameActive() {
        Task { await reconcile(userInitiated: false) }
    }

    func reconnectBackgroundSession(identifier: String) {
        guard identifier == BackgroundTransferDriver.identifier else { return }
        detailText = "Systém předal dokončené background události; porovnávám server."
    }

    func handle(_ event: BackgroundTransferEvent) {
        switch event {
        case let .progress(description, sent, expected):
            guard let index = Self.chunkIndex(from: description), expected > 0 else { return }
            partialSent[index] = min(max(0, sent), expected)
            refreshLocalDisplay()
        case let .completed(description, statusCode, _, errorCode):
            guard let index = Self.chunkIndex(from: description) else { return }
            partialSent[index] = nil
            if errorCode != nil {
                setWaiting("Přenos části byl přerušen; skutečný stav se ověří po dalším spojení.")
            } else if let statusCode, (200...299).contains(statusCode) {
                try? preparer.removePrepared(assetID: journal?.assetID ?? "", index: index)
                Task { await reconcile(userInitiated: false) }
            } else {
                setNeedsAttention("Server část nepotvrdil; originál a připravená část zůstaly zachované.")
            }
        case .finishedEvents:
            TransferAppDelegate.finishBackgroundEvents()
        }
    }

    func networkChanged(_ newPath: NetworkPathState) {
        let wasPermitted = networkPermitted
        path = newPath
        if !networkPermitted, journal?.phase != .paused, journal?.phase != .verified {
            setWaiting(newPath.expensive && !cellularAllowed
                ? "Čeká na Wi-Fi; mobilní data nejsou pro tuto dávku povolena."
                : "Soukromá síť není dosažitelná; veřejný fallback neexistuje.")
        } else if !wasPermitted && networkPermitted {
            Task { await reconcile(userInitiated: false) }
        }
    }

    private var networkPermitted: Bool {
        path.available && (!path.expensive || cellularAllowed)
    }

    private func reconcile(userInitiated: Bool) async {
        guard !reconciling, var current = journal,
              current.phase != .paused, current.phase != .verified else { return }
        guard networkPermitted else {
            setWaiting(path.expensive && !current.cellularAllowed
                ? "Čeká na Wi-Fi; mobilní data nejsou pro tuto dávku povolena."
                : "Soukromá síť není dosažitelná; veřejný fallback neexistuje.")
            return
        }
        reconciling = true
        isBusy = userInitiated
        defer { reconciling = false; isBusy = false }
        do {
            let api = try makeAPI()
            _ = try await api.createSession(for: current)
            let remote = try await api.status(for: current)
            current.acceptedChunks = Set(remote.acceptedChunks)
            current.locallySentByteCount = acceptedByteCount(for: current)
            current.lastError = nil

            let active = await activeChunkIndices(assetID: current.assetID)
            for index in current.acceptedChunks where !active.contains(index) {
                try? preparer.removePrepared(assetID: current.assetID, index: index)
            }

            let plan = TransferReconciler.plan(
                item: current.queueItem,
                server: remote.snapshot,
                networkAvailable: true,
                userPaused: false
            )
            switch plan.displayState {
            case .verifiedOnMac:
                current.phase = .verified
                try? preparer.removeAllPrepared(assetID: current.assetID)
                statusText = "Ověřeno na Macu"
                detailText = "Server potvrdil celkovou délku a SHA-256."
            case .verifying:
                current.phase = .verifying
                journal = current
                try store.save(current)
                refreshLocalDisplay()
                statusText = "Ověřuji"
                detailText = "100 % bytů ještě není serverové potvrzení."
                _ = try await api.finalize(current)
                let verified = try await api.status(for: current)
                guard verified.state == .verified else {
                    throw TransferAPIError.identityMismatch
                }
                current.phase = .verified
                current.acceptedChunks = Set(verified.acceptedChunks)
                current.locallySentByteCount = current.byteCount
                try? preparer.removeAllPrepared(assetID: current.assetID)
                statusText = "Ověřeno na Macu"
                detailText = "Server potvrdil celkovou délku a SHA-256."
            case .needsAttention:
                current.phase = .needsAttention
                statusText = "Vyžaduje pozornost"
                detailText = "Server závěrečné ověření odmítl; originál zůstává v telefonu."
            case .uploading:
                current.phase = .uploading
                statusText = "Nahrávám části"
                detailText = "Naplánované jsou nejvýše dvě připravené části."
                journal = current
                try store.save(current)
                try await scheduleMissing(plan.missingChunks, journal: current, api: api)
            case .paused:
                current.phase = .paused
            case .waitingForNetwork:
                current.phase = .waitingForNetwork
            }
            try store.save(current)
            journal = current
            refreshLocalDisplay()
        } catch {
            if isConnectivityError(error) {
                setWaiting("Server nebo soukromá síť nejsou dosažitelné; originál zůstává v telefonu.")
            } else {
                setNeedsAttention(safeMessage(for: error))
            }
        }
    }

    private func scheduleMissing(
        _ missing: [Int],
        journal: TransferJournal,
        api: TransferAPI
    ) async throws {
        let source = try store.sourceURL(fileName: journal.sourceFileName)
        let active = await activeChunkIndices(assetID: journal.assetID)
        let candidates = missing.filter { !active.contains($0) }
        let prepared = try preparer.prepare(
            journal: journal,
            sourceURL: source,
            missingChunks: candidates
        )
        preparedCount = prepared.count
        for chunk in prepared where missing.contains(chunk.index) && !active.contains(chunk.index) {
            let request = try api.chunkRequest(journal: journal, chunk: chunk)
            _ = driver.scheduleUpload(
                request: request,
                fileURL: try preparer.fileURL(for: chunk),
                description: Self.taskDescription(assetID: journal.assetID, index: chunk.index)
            )
        }
    }

    private func activeChunkIndices(assetID: String) async -> Set<Int> {
        let snapshots = await driver.taskSnapshots()
        return Set(snapshots.compactMap { snapshot in
            guard snapshot.description.hasPrefix("chunk:\(assetID):") else { return nil }
            return Self.chunkIndex(from: snapshot.description)
        })
    }

    private func makeAPI() throws -> TransferAPI {
        let cleanURL = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: cleanURL), let token = try keychain.load() else {
            throw TransferProtocolError.invalidBaseURL
        }
        return TransferAPI(endpoint: try TransferEndpoint(baseURL: url, bearerToken: token))
    }

    private func acceptedByteCount(for journal: TransferJournal) -> Int64 {
        journal.acceptedChunks.reduce(0) { total, index in
            let start = Int64(index * journal.chunkSize)
            return total + max(0, min(Int64(journal.chunkSize), journal.byteCount - start))
        }
    }

    private func refreshLocalDisplay() {
        guard let journal else { progress = 0; preparedCount = 0; return }
        let accepted = acceptedByteCount(for: journal)
        let partial = partialSent.values.reduce(0, +)
        progress = journal.byteCount > 0
            ? min(1, Double(accepted + partial) / Double(journal.byteCount)) : 0
        preparedCount = (try? preparer.preparedChunks(for: journal).count) ?? 0
    }

    private func setWaiting(_ detail: String) {
        guard var current = journal, current.phase != .paused, current.phase != .verified else { return }
        current.phase = .waitingForNetwork
        current.lastError = nil
        try? store.save(current)
        journal = current
        statusText = "Čeká na síť"
        detailText = detail
        refreshLocalDisplay()
    }

    private func setNeedsAttention(_ detail: String) {
        guard var current = journal, current.phase != .verified else { return }
        current.phase = .needsAttention
        current.lastError = String(detail.prefix(160))
        try? store.save(current)
        journal = current
        statusText = "Vyžaduje pozornost"
        detailText = detail
        refreshLocalDisplay()
    }

    private func truthfulText(for phase: TransferJournalPhase) -> String {
        switch phase {
        case .ready: "Dávka připravena"
        case .uploading: "Nahrávám části"
        case .waitingForNetwork: "Čeká na síť"
        case .paused: "Pozastaveno"
        case .verifying: "Ověřuji"
        case .verified: "Ověřeno na Macu"
        case .needsAttention: "Vyžaduje pozornost"
        }
    }

    private func isConnectivityError(_ error: Error) -> Bool {
        guard let urlError = error as? URLError else { return false }
        return [
            .notConnectedToInternet, .networkConnectionLost, .cannotConnectToHost,
            .cannotFindHost, .dnsLookupFailed, .timedOut,
        ].contains(urlError.code)
    }

    private func safeMessage(for error: Error) -> String {
        if let apiError = error as? TransferAPIError {
            switch apiError {
            case let .server(status, code): return "Server odmítl operaci (\(status), \(code))."
            case .identityMismatch: return "Server vrátil jinou identitu nebo neověřený výsledek."
            case .invalidResponse: return "Server nevrátil platnou HTTPS odpověď."
            }
        }
        return "Přenos nebyl potvrzen; originál a journal zůstaly zachované."
    }

    private nonisolated static func makeDriver() -> BackgroundTransferDriver {
        BackgroundTransferDriver { event in
            Task { @MainActor in TransferViewModel.shared.handle(event) }
        }
    }

    private nonisolated static func makeMonitor() -> TransferNetworkMonitor {
        TransferNetworkMonitor { state in
            Task { @MainActor in TransferViewModel.shared.networkChanged(state) }
        }
    }

    private static func taskDescription(assetID: String, index: Int) -> String {
        "chunk:\(assetID):\(index)"
    }

    private static func chunkIndex(from description: String) -> Int? {
        guard description.hasPrefix("chunk:") else { return nil }
        return Int(description.split(separator: ":").last ?? "")
    }
}
