import Combine
import CryptoKit
import Foundation
import Network
import Security
import UIKit

private struct CaminoServerState: Decodable {
    let contractVersion: Int
    let serverID: UUID
    let epoch: UUID
    let cursor: Int64
    let exportsBlocked: Bool
    let reconciliationRequired: Bool

    enum CodingKeys: String, CodingKey {
        case contractVersion = "contract_version"
        case serverID = "server_id"
        case epoch, cursor
        case exportsBlocked = "exports_blocked"
        case reconciliationRequired = "reconciliation_required"
    }
}

private struct CaminoMediaStatus: Decodable {
    let assetID: UUID
    let state: String
    let byteCount: Int64
    let sha256: String
    let chunkSize: Int
    let chunkCount: Int
    let acceptedChunks: [Int]
    let missingChunks: [Int]

    enum CodingKeys: String, CodingKey {
        case assetID = "asset_id"
        case state
        case byteCount = "byte_count"
        case sha256
        case chunkSize = "chunk_size"
        case chunkCount = "chunk_count"
        case acceptedChunks = "accepted_chunks"
        case missingChunks = "missing_chunks"
    }
}

private struct CaminoInventoryMoment: Encodable, Sendable {
    let id: String
    let revision: Int
    let privacy: String
}

private enum CaminoSyncAPIError: Error, Equatable {
    case invalidConfiguration
    case invalidResponse
    case server(Int, String)
}

private struct CaminoSyncAPI: Sendable {
    let baseURL: URL
    let token: String
    let allowsCellular: Bool

    init(baseURL: URL, token: String, allowsCellular: Bool) throws {
        guard baseURL.scheme?.lowercased() == "https", baseURL.host != nil,
              baseURL.user == nil, baseURL.password == nil,
              baseURL.query == nil, baseURL.fragment == nil,
              token.count >= 32, !token.contains("\n"), !token.contains("\r") else {
            throw CaminoSyncAPIError.invalidConfiguration
        }
        self.baseURL = baseURL
        self.token = token
        self.allowsCellular = allowsCellular
    }

    func state() async throws -> CaminoServerState {
        try await send(path: ["api", "v1", "state"], method: "GET")
    }

    func operation(exactBody: Data) async throws -> Int64 {
        struct Receipt: Decodable { let cursor: Int64 }
        let receipt: Receipt = try await send(
            path: ["api", "v1", "operations"], method: "POST",
            contentType: "application/json", body: exactBody)
        return receipt.cursor
    }

    func reconcile(lastEpoch: UUID, moments: [CaminoInventoryMoment]) async throws {
        struct Request: Encodable {
            let contract_version: Int
            let last_known_epoch: String
            let moments: [CaminoInventoryMoment]
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        let body = try encoder.encode(Request(
            contract_version: 1,
            last_known_epoch: lastEpoch.uuidString.lowercased(), moments: moments))
        let _: ReconcileReceipt = try await send(
            path: ["api", "v1", "reconcile"], method: "POST",
            contentType: "application/json", body: body)
    }

    func createSession(for item: CaminoSyncMediaItem) async throws -> CaminoMediaStatus {
        let body = try JSONSerialization.data(withJSONObject: [
            "contract_version": 1, "chunk_size": item.chunkSize,
        ], options: [.sortedKeys])
        return try await send(
            path: ["api", "v1", "assets", item.id.uuidString.lowercased(), "upload-session"],
            method: "POST", contentType: "application/json", body: body)
    }

    func mediaStatus(for item: CaminoSyncMediaItem) async throws -> CaminoMediaStatus {
        try await send(path: ["api", "v1", "assets", item.id.uuidString.lowercased(),
                              "upload-status"], method: "GET")
    }

    func finalize(_ item: CaminoSyncMediaItem) async throws -> CaminoMediaStatus {
        struct FinalizeReceipt: Decodable {
            let assetID: UUID
            let byteCount: Int64
            let sha256: String
            let chunkCount: Int
            let state: String
            enum CodingKeys: String, CodingKey {
                case assetID = "asset_id"
                case byteCount = "byte_count"
                case sha256
                case chunkCount = "chunk_count"
                case state
            }
        }
        let receipt: FinalizeReceipt = try await send(
            path: ["api", "v1", "assets", item.id.uuidString.lowercased(), "finalize"],
            method: "POST")
        guard receipt.assetID == item.id, receipt.byteCount == item.byteCount,
              receipt.sha256 == item.sha256, receipt.chunkCount == item.chunkCount,
              receipt.state == "verified" else {
            throw CaminoSyncAPIError.invalidResponse
        }
        return try await mediaStatus(for: item)
    }

    func chunkRequest(item: CaminoSyncMediaItem, index: Int,
                      byteCount: Int, sha256: String) -> URLRequest {
        var request = request(path: ["api", "v1", "assets",
            item.id.uuidString.lowercased(), "chunks", String(index)], method: "PUT")
        request.setValue("application/octet-stream", forHTTPHeaderField: "Content-Type")
        request.setValue(String(byteCount), forHTTPHeaderField: "Content-Length")
        request.setValue(sha256, forHTTPHeaderField: "X-Camino-Chunk-SHA256")
        return request
    }

    private struct ReconcileReceipt: Decodable {
        let epoch: UUID
        let differences: [Difference]
        let exportsBlocked: Bool
        let reconciliationRequired: Bool
        struct Difference: Decodable { let id: UUID; let reason: String }
        enum CodingKeys: String, CodingKey {
            case epoch, differences
            case exportsBlocked = "exports_blocked"
            case reconciliationRequired = "reconciliation_required"
        }
    }

    private func request(path: [String], method: String) -> URLRequest {
        var url = baseURL
        for component in path { url.appendPathComponent(component) }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 30
        request.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData
        request.allowsCellularAccess = allowsCellular
        request.allowsExpensiveNetworkAccess = allowsCellular
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("no-store", forHTTPHeaderField: "Cache-Control")
        return request
    }

    private func send<T: Decodable>(path: [String], method: String,
                                    contentType: String? = nil,
                                    body: Data? = nil) async throws -> T {
        var request = request(path: path, method: method)
        request.httpBody = body
        if let contentType { request.setValue(contentType, forHTTPHeaderField: "Content-Type") }
        let configuration = URLSessionConfiguration.ephemeral
        configuration.waitsForConnectivity = false
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 60
        configuration.urlCache = nil
        let (data, response) = try await URLSession(configuration: configuration).data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw CaminoSyncAPIError.invalidResponse
        }
        guard (200...299).contains(http.statusCode) else {
            let code = Self.safeErrorCode(data) ?? "server_error"
            throw CaminoSyncAPIError.server(http.statusCode, code)
        }
        do { return try JSONDecoder().decode(T.self, from: data) }
        catch { throw CaminoSyncAPIError.invalidResponse }
    }

    private static func safeErrorCode(_ data: Data) -> String? {
        guard let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let error = root["error"] as? [String: Any],
              let value = error["code"] as? String else { return nil }
        let safe = value.filter { $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "_") }
        return safe.isEmpty ? nil : String(safe.prefix(64))
    }
}

private struct CaminoKeychainTokenStore: Sendable {
    private let service = "cz.pythonmf.camino.app.sync"
    private let account = "private-owner-bearer-token"

    func save(_ token: String) throws {
        guard let data = token.data(using: .utf8) else {
            throw CaminoSyncAPIError.invalidConfiguration
        }
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(query as CFDictionary)
        var item = query
        item[kSecValueData as String] = data
        item[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        guard SecItemAdd(item as CFDictionary, nil) == errSecSuccess else {
            throw CaminoSyncAPIError.invalidConfiguration
        }
    }

    func load() throws -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess, let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            throw CaminoSyncAPIError.invalidConfiguration
        }
        return token
    }
}

private struct CaminoNetworkState: Sendable {
    let available: Bool
    let expensive: Bool
}

private final class CaminoSyncNetworkMonitor: @unchecked Sendable {
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "cz.pythonmf.camino.app.sync.network")

    init(handler: @escaping @Sendable (CaminoNetworkState) -> Void) {
        monitor.pathUpdateHandler = { path in
            handler(CaminoNetworkState(
                available: path.status == .satisfied,
                expensive: path.isExpensive || path.usesInterfaceType(.cellular)))
        }
    }

    func start() { monitor.start(queue: queue) }
    func cancel() { monitor.cancel() }
}

fileprivate enum CaminoBackgroundEvent: Sendable {
    case completed(description: String, statusCode: Int?, errorCode: Int?)
    case finishedEvents
}

final class CaminoSyncBackgroundDriver: NSObject, URLSessionTaskDelegate,
    @unchecked Sendable
{
    static let identifier = "cz.pythonmf.camino.app.sync.background.v1"
    private static let lock = NSLock()
    nonisolated(unsafe) private static var completionHandler: (() -> Void)?

    static func installCompletionHandler(_ handler: @escaping () -> Void) {
        lock.lock(); completionHandler = handler; lock.unlock()
    }

    fileprivate static func finishEvents() {
        lock.lock(); let handler = completionHandler; completionHandler = nil; lock.unlock()
        handler?()
    }

    private let handler: @Sendable (CaminoBackgroundEvent) -> Void
    private var sessionStorage: URLSession!

    fileprivate init(handler: @escaping @Sendable (CaminoBackgroundEvent) -> Void) {
        self.handler = handler
        super.init()
        let configuration = URLSessionConfiguration.background(withIdentifier: Self.identifier)
        configuration.sessionSendsLaunchEvents = true
        configuration.isDiscretionary = false
        configuration.waitsForConnectivity = true
        configuration.allowsCellularAccess = true
        configuration.allowsExpensiveNetworkAccess = true
        configuration.timeoutIntervalForResource = 24 * 60 * 60
        configuration.urlCache = nil
        sessionStorage = URLSession(configuration: configuration, delegate: self,
                                    delegateQueue: nil)
    }

    func activeDescriptions() async -> Set<String> {
        Set(await sessionStorage.allTasks.compactMap(\.taskDescription))
    }

    func schedule(request: URLRequest, fileURL: URL, description: String) {
        let task = sessionStorage.uploadTask(with: request, fromFile: fileURL)
        task.taskDescription = description
        task.resume()
    }

    func suspendAll() async {
        for task in await sessionStorage.allTasks { task.suspend() }
    }

    func resumeAll() async {
        for task in await sessionStorage.allTasks { task.resume() }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask,
                    didCompleteWithError error: (any Error)?) {
        handler(.completed(
            description: task.taskDescription ?? "",
            statusCode: (task.response as? HTTPURLResponse)?.statusCode,
            errorCode: (error as NSError?)?.code))
    }

    func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        handler(.finishedEvents)
    }
}

final class CaminoAppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                     handleEventsForBackgroundURLSession identifier: String,
                     completionHandler: @escaping () -> Void) {
        guard identifier == CaminoSyncBackgroundDriver.identifier else {
            completionHandler(); return
        }
        CaminoSyncBackgroundDriver.installCompletionHandler(completionHandler)
    }
}

@MainActor final class CaminoSyncCoordinator: ObservableObject {
    @Published var serverURL: String
    @Published var tokenInput = ""
    @Published private(set) var tokenStored = false
    @Published private(set) var statusText = "Připravuji frontu…"
    @Published private(set) var detailText = ""
    @Published private(set) var stats = CaminoSyncQueueStats(
        metadataCount: 0, mediaCount: 0, mediaBytes: 0)
    @Published private(set) var cellularStats = CaminoSyncQueueStats(
        metadataCount: 0, mediaCount: 0, mediaBytes: 0)
    @Published private(set) var paused = false
    @Published private(set) var busy = false
    @Published private(set) var reconciliationRequired = false

    private let local: CaminoLocalStore
    private let recording: IntentRecordingStore
    private let root: URL
    private let journalStore: CaminoSyncJournalStore
    private let keychain = CaminoKeychainTokenStore()
    private var journal: CaminoSyncJournal
    private var path = CaminoNetworkState(available: false, expensive: false)
    private var running = false
    private lazy var driver = CaminoSyncBackgroundDriver { [weak self] event in
        Task { @MainActor in self?.handle(event) }
    }
    private lazy var monitor = CaminoSyncNetworkMonitor { [weak self] state in
        Task { @MainActor in self?.networkChanged(state) }
    }

    init(local: CaminoLocalStore, recording: IntentRecordingStore, root: URL) throws {
        self.local = local
        self.recording = recording
        self.root = root.standardizedFileURL
        journalStore = CaminoSyncJournalStore(
            url: root.appendingPathComponent("Sync/c05b-journal.json"))
        journal = try journalStore.loadOrCreate()
        serverURL = UserDefaults.standard.string(forKey: "camino.c05b.serverURL") ?? ""
        tokenStored = (try? keychain.load()) != nil
        paused = journal.paused
        reconciliationRequired = journal.reconciliationRequired
        refreshPublishedState()
        _ = driver
        if paused { Task { await driver.suspendAll() } }
        monitor.start()
    }

    var configurationReady: Bool { !serverURL.isEmpty && tokenStored }
    var cellularGranted: Bool { journal.cellularBatchID != nil }

    func saveConfiguration() {
        do {
            let clean = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
            guard let url = URL(string: clean) else {
                throw CaminoSyncAPIError.invalidConfiguration
            }
            let entered = tokenInput.trimmingCharacters(in: .whitespacesAndNewlines)
            let selected = entered.isEmpty ? (try keychain.load() ?? "") : entered
            _ = try CaminoSyncAPI(baseURL: url, token: selected, allowsCellular: false)
            if !entered.isEmpty { try keychain.save(entered) }
            UserDefaults.standard.set(clean, forKey: "camino.c05b.serverURL")
            serverURL = clean
            tokenInput = ""
            tokenStored = true
            detailText = "Soukromá HTTPS adresa je uložená; token zůstává v Keychain."
        } catch {
            detailText = "Zadej platnou HTTPS adresu a token o délce alespoň 32 znaků."
        }
    }

    func refreshInventory() {
        Task { await discoverOnly() }
    }

    func synchronizeNow() {
        Task { await synchronize() }
    }

    func setPaused(_ value: Bool) {
        journal.paused = value
        paused = value
        try? journalStore.save(journal)
        if value {
            Task { await driver.suspendAll() }
            statusText = "Přenosy jsou pozastavené"
            detailText = "Nové úlohy se neplánují. Záznam a místní čtení dál fungují."
        } else {
            Task {
                await driver.resumeAll()
                await synchronize()
            }
        }
    }

    func grantCellularForDisplayedBatch() {
        let granted = journal.grantCellularForDisplayedBatch()
        do {
            try journalStore.save(journal)
            refreshPublishedState()
            detailText = "Mobilní data platí jen pro zobrazenou dávku: \(granted.mediaCount) souborů."
        } catch {
            detailText = "Mobilní povolení se nepodařilo trvale uložit; přenos nezačal."
        }
    }

    func applicationBecameActive() {
        Task { await synchronize() }
    }

    private func discoverOnly() async {
        do {
            try await discover()
            statusText = journal.paused ? "Přenosy jsou pozastavené"
                : stats.metadataCount == 0 && stats.mediaCount == 0
                    ? "Vše známé je ověřeno na Macu" : "Fronta je připravená"
        } catch {
            detailText = CaminoSyncError.incompleteLocalInventory.localizedDescription
        }
    }

    private func discover() async throws {
        let trips = try local.trips()
        var days: [LocalDay] = []
        var snapshots: [LocalMomentSyncSnapshot] = []
        for trip in trips {
            days.append(contentsOf: try local.days(tripID: trip.id))
            for moment in try local.moments(tripID: trip.id, includeHidden: true) {
                snapshots.append(try local.syncSnapshot(momentID: moment.id))
            }
        }
        var candidates = try local.allMediaAssets().map { asset in
            CaminoSyncMediaItem(
                id: asset.id, momentID: asset.momentID,
                kind: asset.kind == .photo ? .photo : .video,
                sourceRelativePath: asset.relativePath,
                byteCount: asset.inspection.byteCount,
                sha256: asset.inspection.sha256,
                durationMilliseconds: asset.inspection.durationMilliseconds,
                batchID: journal.openBatchID)
        }
        let momentBySession = try Dictionary(uniqueKeysWithValues:
            snapshots.flatMap { snapshot in
                try local.audioSessionIDs(momentID: snapshot.moment.id).map {
                    ($0, snapshot.moment.id)
                }
            })
        let library = try recording.library()
        for clip in library.clips {
            guard let momentID = momentBySession[clip.draft.sessionID] else { continue }
            let urls = try recording.playbackURLs(for: clip)
            for (offset, url) in urls.enumerated() {
                guard let relative = relativePath(for: url) else {
                    throw CaminoSyncError.incompleteLocalInventory
                }
                let values = try url.resourceValues(forKeys: [.isRegularFileKey,
                    .isSymbolicLinkKey, .fileSizeKey])
                guard values.isRegularFile == true, values.isSymbolicLink != true,
                      let size = values.fileSize, size > 0 else {
                    throw CaminoSyncError.incompleteLocalInventory
                }
                let digest = try await Task.detached(priority: .utility) {
                    try Self.sha256(of: url)
                }.value
                let duration: Int64
                if let segments = clip.segments, offset < segments.count {
                    duration = Int64((segments[offset].audio.duration * 1_000).rounded())
                } else {
                    duration = Int64((clip.audio.duration * 1_000).rounded())
                }
                let id = CaminoStableID.uuid(
                    namespace: "camino-c05b-audio-asset",
                    value: "\(clip.id.uuidString.lowercased())|\(url.lastPathComponent)")
                candidates.append(CaminoSyncMediaItem(
                    id: id, momentID: momentID, kind: .audio,
                    sourceRelativePath: relative, byteCount: Int64(size),
                    sha256: digest, durationMilliseconds: max(0, duration),
                    batchID: journal.openBatchID))
            }
        }
        let discovery = try CaminoSyncDiscovery(
            trips: trips, days: days, moments: snapshots, media: candidates)
        journal.merge(metadata: discovery.metadata, media: discovery.media)
        try journalStore.save(journal)
        refreshPublishedState()
    }

    private func synchronize() async {
        guard !running else { return }
        running = true
        busy = true
        defer { running = false; busy = false }
        do {
            try await discover()
            guard !journal.paused else { return }
            guard configurationReady else {
                statusText = "Domácí Mac není nastavený"
                detailText = "Místní záznam funguje dál. Vlož soukromou HTTPS adresu a token."
                return
            }
            guard path.available else {
                statusText = "Čeká na síť"
                detailText = "Domácí Mac teď není dostupný. Data zůstávají v telefonu."
                return
            }
            guard !path.expensive || journal.cellularBatchID != nil else {
                statusText = "Čeká na Wi‑Fi"
                detailText = "Mobilní data nejsou pro zobrazenou dávku povolená."
                return
            }
            let api = try makeAPI()
            let state = try await api.state()
            let previousEpoch = journal.epoch
            let transition = journal.observeServer(
                serverID: state.serverID, epoch: state.epoch, cursor: state.cursor)
            if state.reconciliationRequired || state.exportsBlocked {
                journal.reconciliationRequired = true
            }
            try journalStore.save(journal)
            if case .epochChanged = transition, let previousEpoch {
                try await api.reconcile(lastEpoch: previousEpoch,
                    moments: try reconciliationInventory())
                journal.reconciliationRequired = true
                try journalStore.save(journal)
            }
            guard !journal.reconciliationRequired else {
                reconciliationRequired = true
                statusText = "Nutné porovnání po obnově Macu"
                detailText = "Inventář byl porovnán bez mazání. Server zůstává bezpečně zablokovaný pro servisní kontrolu."
                return
            }
            while true {
                switch journal.nextWork(networkAvailable: true, expensive: path.expensive) {
                case .metadata(let id):
                    try await sendMetadata(id: id, api: api)
                case .media(let id):
                    try await processMedia(id: id, api: api)
                    refreshPublishedState()
                    return
                case .none:
                    journal.revokeCellularIfFinished()
                    try journalStore.save(journal)
                    refreshPublishedState()
                    statusText = "Vše známé je ověřeno na Macu"
                    detailText = "Server potvrdil metadata, délku a SHA‑256 všech známých médií."
                    return
                }
            }
        } catch {
            handle(error)
        }
    }

    private func sendMetadata(id: UUID, api: CaminoSyncAPI) async throws {
        guard let index = journal.metadata.firstIndex(where: { $0.id == id }) else {
            throw CaminoSyncError.invalidJournal
        }
        let body = try journal.exactEnvelope(for: id)
        try journalStore.save(journal)
        statusText = "Odesílám prioritní metadata"
        do {
            journal.serverCursor = try await api.operation(exactBody: body)
            journal.metadata[index].phase = .accepted
            journal.metadata[index].lastErrorCode = nil
            journal.lastContactUTCMilliseconds = Int64(Date().timeIntervalSince1970 * 1_000)
            try journalStore.save(journal)
            refreshPublishedState()
        } catch CaminoSyncAPIError.server(_, let code) {
            if code == "epoch_mismatch" || code == "reconciliation_required" {
                journal.reconciliationRequired = true
                try journalStore.save(journal)
            } else if ["identity_conflict", "operation_id_conflict",
                       "revision_conflict", "writer_mismatch"].contains(code) {
                journal.metadata[index].phase = .needsAttention
                journal.metadata[index].lastErrorCode = code
                try journalStore.save(journal)
            }
            throw CaminoSyncError.serverConflict(code)
        }
    }

    private func processMedia(id: UUID, api: CaminoSyncAPI) async throws {
        guard let index = journal.media.firstIndex(where: { $0.id == id }) else {
            throw CaminoSyncError.invalidJournal
        }
        var item = journal.media[index]
        statusText = item.phase == .verifying ? "Ověřuji" : "Porovnávám médium se serverem"
        let status = try await api.createSession(for: item)
        try validate(status, for: item)
        item.acceptedChunks = Set(status.acceptedChunks)
        if status.state == "verified" {
            item.phase = .verified
            item.lastErrorCode = nil
            journal.media[index] = item
            journal.revokeCellularIfFinished()
            try journalStore.save(journal)
            Task { await synchronize() }
            return
        }
        if status.state == "verification_failed" || status.state == "recovery_required" {
            item.phase = .needsAttention
            item.lastErrorCode = status.state
            journal.media[index] = item
            try journalStore.save(journal)
            throw CaminoSyncError.serverConflict(status.state)
        }
        if status.missingChunks.isEmpty {
            item.phase = .verifying
            journal.media[index] = item
            try journalStore.save(journal)
            statusText = "Ověřuji"
            detailText = "Všechny bajty dorazily; čekám na serverové ověření celého souboru."
            let verified = try await api.finalize(item)
            try validate(verified, for: item)
            guard verified.state == "verified" else {
                throw CaminoSyncAPIError.invalidResponse
            }
            item.acceptedChunks = Set(verified.acceptedChunks)
            item.phase = .verified
            journal.media[index] = item
            journal.revokeCellularIfFinished()
            try journalStore.save(journal)
            Task { await synchronize() }
            return
        }
        let active = await driver.activeDescriptions()
        if active.contains(where: { $0.hasPrefix("c05b:\(item.id.uuidString.lowercased()):") }) {
            item.phase = .uploading
            journal.media[index] = item
            try journalStore.save(journal)
            statusText = "Nahrávám médium"
            detailText = "Běží nejvýše dvě souborové úlohy; po návratu se stav znovu porovná."
            return
        }
        let chunkIndex = status.missingChunks[0]
        let prepared = try prepareChunk(item: item, index: chunkIndex)
        let description = "c05b:\(item.id.uuidString.lowercased()):\(chunkIndex)"
        driver.schedule(
            request: api.chunkRequest(item: item, index: chunkIndex,
                byteCount: prepared.byteCount, sha256: prepared.sha256),
            fileURL: prepared.url, description: description)
        item.phase = .uploading
        journal.media[index] = item
        try journalStore.save(journal)
        statusText = "Nahrávám médium"
        detailText = "Připravená je jedna část z bezpečného maxima dvou."
    }

    private func validate(_ status: CaminoMediaStatus,
                          for item: CaminoSyncMediaItem) throws {
        let accepted = Set(status.acceptedChunks)
        let missing = Set(status.missingChunks)
        guard status.assetID == item.id, status.byteCount == item.byteCount,
              status.sha256 == item.sha256, status.chunkSize == item.chunkSize,
              status.chunkCount == item.chunkCount,
              accepted.count == status.acceptedChunks.count,
              missing.count == status.missingChunks.count,
              accepted.isDisjoint(with: missing),
              accepted.union(missing) == Set(0..<item.chunkCount) else {
            throw CaminoSyncAPIError.invalidResponse
        }
    }

    private struct PreparedChunk {
        let url: URL
        let byteCount: Int
        let sha256: String
    }

    private func prepareChunk(item: CaminoSyncMediaItem, index: Int) throws -> PreparedChunk {
        guard index >= 0, index < item.chunkCount else {
            throw CaminoSyncError.invalidJournal
        }
        let source = root.appendingPathComponent(item.sourceRelativePath).standardizedFileURL
        guard source.path.hasPrefix(root.path + "/") else {
            throw CaminoSyncError.incompleteLocalInventory
        }
        let sourceValues = try source.resourceValues(forKeys: [.isRegularFileKey,
            .isSymbolicLinkKey, .fileSizeKey])
        guard sourceValues.isRegularFile == true, sourceValues.isSymbolicLink != true,
              Int64(sourceValues.fileSize ?? -1) == item.byteCount else {
            throw CaminoSyncError.incompleteLocalInventory
        }
        let preparedRoot = root.appendingPathComponent("Sync/Prepared", isDirectory: true)
        try FileManager.default.createDirectory(at: preparedRoot, withIntermediateDirectories: true)
        #if os(iOS)
        try FileManager.default.setAttributes(
            [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
            ofItemAtPath: preparedRoot.path)
        #endif
        let destination = preparedRoot.appendingPathComponent("slot-0.bin")
        if !FileManager.default.fileExists(atPath: destination.path) {
            guard FileManager.default.createFile(atPath: destination.path, contents: nil,
                attributes: [.posixPermissions: 0o600]) else {
                throw CaminoSyncError.incompleteLocalInventory
            }
        }
        #if os(iOS)
        try FileManager.default.setAttributes(
            [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
            ofItemAtPath: destination.path)
        #endif
        let count = Int(min(Int64(item.chunkSize),
            item.byteCount - Int64(index * item.chunkSize)))
        let input = try FileHandle(forReadingFrom: source)
        let output = try FileHandle(forWritingTo: destination)
        defer { try? input.close(); try? output.close() }
        try input.seek(toOffset: UInt64(index * item.chunkSize))
        try output.truncate(atOffset: 0)
        var remaining = count
        var hasher = SHA256()
        while remaining > 0 {
            guard let data = try input.read(upToCount: min(remaining, 1024 * 1024)),
                  !data.isEmpty else { throw CaminoSyncError.incompleteLocalInventory }
            try output.write(contentsOf: data)
            hasher.update(data: data)
            remaining -= data.count
        }
        try output.synchronize()
        return PreparedChunk(url: destination, byteCount: count,
            sha256: hasher.finalize().map { String(format: "%02x", $0) }.joined())
    }

    private func reconciliationInventory() throws -> [CaminoInventoryMoment] {
        try local.trips().flatMap { trip in
            try local.moments(tripID: trip.id, includeHidden: true).map { moment in
                let snapshot = try local.syncSnapshot(momentID: moment.id)
                let metadataRevision = snapshot.baseRevision + snapshot.operations.filter {
                    $0.kind != .appendText
                }.count
                return CaminoInventoryMoment(
                    id: moment.id.uuidString.lowercased(), revision: metadataRevision,
                    privacy: moment.privacy.rawValue)
            }
        }
    }

    private func makeAPI() throws -> CaminoSyncAPI {
        guard let url = URL(string: serverURL), let token = try keychain.load() else {
            throw CaminoSyncAPIError.invalidConfiguration
        }
        return try CaminoSyncAPI(baseURL: url, token: token,
            allowsCellular: journal.cellularBatchID != nil)
    }

    private func relativePath(for url: URL) -> String? {
        let source = url.standardizedFileURL.path
        let prefix = root.path + "/"
        guard source.hasPrefix(prefix) else { return nil }
        return String(source.dropFirst(prefix.count))
    }

    nonisolated private static func sha256(of url: URL) throws -> String {
        let input = try FileHandle(forReadingFrom: url)
        defer { try? input.close() }
        var hasher = SHA256()
        while let data = try input.read(upToCount: 1024 * 1024), !data.isEmpty {
            hasher.update(data: data)
        }
        return hasher.finalize().map { String(format: "%02x", $0) }.joined()
    }

    private func networkChanged(_ state: CaminoNetworkState) {
        let wasAvailable = path.available
        path = state
        if !state.available {
            statusText = "Čeká na síť"
            detailText = "Domácí Mac teď není dostupný. Záznam a místní čtení fungují dál."
        } else if !wasAvailable {
            Task { await synchronize() }
        }
    }

    private func handle(_ event: CaminoBackgroundEvent) {
        switch event {
        case .completed(_, let statusCode, let errorCode):
            if errorCode != nil {
                statusText = "Přenos byl přerušen"
                detailText = "Po dalším spojení se porovná skutečný stav; originál zůstává v telefonu."
            } else if let statusCode, (200...299).contains(statusCode) {
                Task { await synchronize() }
            } else if statusCode == 507 {
                statusText = "Na Macu není místo"
                detailText = "Server část nepřijal. Připravená část i originál zůstávají v telefonu."
            } else if statusCode == 401 {
                statusText = "Obnov připojení k domácímu Macu"
                detailText = "Token server odmítl. Originál zůstává v telefonu."
            } else {
                statusText = "Server část nepotvrdil"
                detailText = "Připravená část i originál zůstávají v telefonu pro bezpečné opakování."
            }
        case .finishedEvents:
            CaminoSyncBackgroundDriver.finishEvents()
        }
    }

    private func handle(_ error: Error) {
        if let value = error as? CaminoSyncAPIError {
            switch value {
            case .invalidConfiguration:
                statusText = "Domácí Mac není nastavený"
                detailText = "Oprav soukromou HTTPS adresu nebo token. Místní data zůstávají."
            case .invalidResponse:
                statusText = "Odpověď Macu nelze ověřit"
                detailText = "Přenos zůstává čekat; žádný falešný úspěch se nezapsal."
            case .server(let status, let code):
                statusText = status == 401 ? "Obnov připojení k domácímu Macu"
                    : code == "insufficient_storage" ? "Na Macu není místo"
                    : "Domácí Mac změnu odmítl"
                detailText = "Kód: \(code). Originály zůstávají v telefonu."
            }
        } else if let value = error as? CaminoSyncError {
            statusText = "Synchronizace vyžaduje pozornost"
            detailText = value.localizedDescription
        } else {
            statusText = "Domácí Mac teď není dostupný"
            detailText = "Příčinu nelze ze sítě spolehlivě určit. Data zůstávají v telefonu."
        }
        refreshPublishedState()
    }

    private func refreshPublishedState() {
        stats = journal.stats
        cellularStats = journal.cellularBatchStats
        paused = journal.paused
        reconciliationRequired = journal.reconciliationRequired
    }
}
