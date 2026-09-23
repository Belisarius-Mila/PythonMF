import CryptoKit
import Foundation

public enum CaminoSyncMediaKind: String, Codable, Sendable, CaseIterable {
    case audio, photo, video

    public var priority: Int {
        switch self {
        case .audio: 0
        case .photo: 1
        case .video: 2
        }
    }
}

public enum CaminoSyncMetadataPhase: String, Codable, Sendable {
    case pending, accepted, needsAttention = "needs_attention"
}

public enum CaminoSyncMediaPhase: String, Codable, Sendable {
    case ready, uploading, verifying, verified, needsAttention = "needs_attention"
}

public struct CaminoSyncMetadataItem: Codable, Equatable, Identifiable, Sendable {
    public let id: UUID
    public let uniqueKey: String
    public let kind: String
    public let objectID: UUID
    public let expectedRevision: Int?
    public let payload: Data
    public var sequence: Int64?
    public var exactEnvelope: Data?
    public var phase: CaminoSyncMetadataPhase
    public var lastErrorCode: String?

    public init(id: UUID, uniqueKey: String, kind: String, objectID: UUID,
                expectedRevision: Int?, payload: Data,
                sequence: Int64? = nil, exactEnvelope: Data? = nil,
                phase: CaminoSyncMetadataPhase = .pending,
                lastErrorCode: String? = nil) {
        self.id = id
        self.uniqueKey = uniqueKey
        self.kind = kind
        self.objectID = objectID
        self.expectedRevision = expectedRevision
        self.payload = payload
        self.sequence = sequence
        self.exactEnvelope = exactEnvelope
        self.phase = phase
        self.lastErrorCode = lastErrorCode
    }

    public var valid: Bool {
        guard !uniqueKey.isEmpty, !kind.isEmpty,
              expectedRevision.map({ $0 >= 1 }) ?? true,
              sequence.map({ $0 >= 1 }) ?? true,
              (sequence == nil) == (exactEnvelope == nil),
              let payloadObject = try? JSONSerialization.jsonObject(with: payload),
              payloadObject is [String: Any] else { return false }
        if phase != .pending && exactEnvelope == nil { return false }
        if let exactEnvelope {
            guard let envelope = try? JSONSerialization.jsonObject(with: exactEnvelope)
                    as? [String: Any],
                  Set(envelope.keys) == Set([
                    "contract_version", "epoch", "operation_id", "device_sequence",
                    "device_id", "kind", "expected_revision", "payload",
                  ]),
                  (envelope["contract_version"] as? NSNumber)?.intValue == 1,
                  envelope["operation_id"] as? String == id.uuidString.lowercased(),
                  (envelope["device_sequence"] as? NSNumber)?.int64Value == sequence,
                  envelope["kind"] as? String == kind,
                  let envelopePayload = envelope["payload"],
                  let canonicalPayload = try? JSONSerialization.data(
                    withJSONObject: envelopePayload,
                    options: [.sortedKeys, .withoutEscapingSlashes]),
                  canonicalPayload == payload else { return false }
            if let expectedRevision {
                guard (envelope["expected_revision"] as? NSNumber)?.intValue
                        == expectedRevision else { return false }
            } else if !(envelope["expected_revision"] is NSNull) { return false }
        }
        return true
    }
}

public struct CaminoSyncMediaItem: Codable, Equatable, Identifiable, Sendable {
    public let id: UUID
    public let momentID: UUID
    public let kind: CaminoSyncMediaKind
    public let sourceRelativePath: String
    public let byteCount: Int64
    public let sha256: String
    public let durationMilliseconds: Int64?
    public let batchID: UUID
    public let chunkSize: Int
    public let chunkCount: Int
    public var acceptedChunks: Set<Int>
    public var phase: CaminoSyncMediaPhase
    public var lastErrorCode: String?

    public init(id: UUID, momentID: UUID, kind: CaminoSyncMediaKind,
                sourceRelativePath: String, byteCount: Int64, sha256: String,
                durationMilliseconds: Int64?, batchID: UUID,
                chunkSize: Int = 8 * 1024 * 1024,
                acceptedChunks: Set<Int> = [],
                phase: CaminoSyncMediaPhase = .ready,
                lastErrorCode: String? = nil) {
        self.id = id
        self.momentID = momentID
        self.kind = kind
        self.sourceRelativePath = sourceRelativePath
        self.byteCount = byteCount
        self.sha256 = sha256
        self.durationMilliseconds = durationMilliseconds
        self.batchID = batchID
        self.chunkSize = chunkSize
        self.chunkCount = byteCount > 0 && chunkSize > 0
            ? Int((byteCount + Int64(chunkSize) - 1) / Int64(chunkSize)) : 0
        self.acceptedChunks = acceptedChunks
        self.phase = phase
        self.lastErrorCode = lastErrorCode
    }

    public var valid: Bool {
        !sourceRelativePath.isEmpty && !sourceRelativePath.hasPrefix("/")
            && !sourceRelativePath.split(separator: "/").contains("..")
            && byteCount > 0 && chunkSize > 0 && chunkCount > 0
            && chunkCount == Int((byteCount + Int64(chunkSize) - 1) / Int64(chunkSize))
            && (durationMilliseconds.map { $0 >= 0 } ?? true)
            && sha256.count == 64
            && sha256.utf8.allSatisfy { (48...57).contains($0) || (97...102).contains($0) }
            && acceptedChunks.allSatisfy { $0 >= 0 && $0 < chunkCount }
            && (![.verifying, .verified].contains(phase)
                || acceptedChunks.count == chunkCount)
    }
}

public struct CaminoSyncQueueStats: Equatable, Sendable {
    public let metadataCount: Int
    public let mediaCount: Int
    public let mediaBytes: Int64
}

public enum CaminoSyncServerTransition: Equatable, Sendable {
    case adopted
    case unchanged
    case epochChanged(previous: UUID, observed: UUID)
}

public enum CaminoSyncNextWork: Equatable, Sendable {
    case metadata(UUID)
    case media(UUID)
    case none
}

public struct CaminoSyncJournal: Codable, Equatable, Sendable {
    public let schema: Int
    public let deviceID: UUID
    public var serverID: UUID?
    public var epoch: UUID?
    public var observedEpoch: UUID?
    public var serverCursor: Int64
    public var paused: Bool
    public var reconciliationRequired: Bool
    public var openBatchID: UUID
    public var cellularBatchID: UUID?
    public var metadata: [CaminoSyncMetadataItem]
    public var media: [CaminoSyncMediaItem]
    public var lastContactUTCMilliseconds: Int64?

    public init(deviceID: UUID = UUID(), openBatchID: UUID = UUID()) {
        schema = 1
        self.deviceID = deviceID
        serverID = nil
        epoch = nil
        observedEpoch = nil
        serverCursor = 0
        paused = false
        reconciliationRequired = false
        self.openBatchID = openBatchID
        cellularBatchID = nil
        metadata = []
        media = []
        lastContactUTCMilliseconds = nil
    }

    public var valid: Bool {
        schema == 1 && serverCursor >= 0
            && ((serverID == nil) == (epoch == nil))
            && Set(metadata.map(\.id)).count == metadata.count
            && Set(metadata.map(\.uniqueKey)).count == metadata.count
            && metadata.allSatisfy(\.valid)
            && metadata.allSatisfy { item in
                guard let exact = item.exactEnvelope,
                      let envelope = try? JSONSerialization.jsonObject(with: exact)
                        as? [String: Any], let epoch else {
                    return item.exactEnvelope == nil
                }
                return envelope["epoch"] as? String == epoch.uuidString.lowercased()
                    && envelope["device_id"] as? String == deviceID.uuidString.lowercased()
            }
            && Set(media.map(\.id)).count == media.count
            && media.allSatisfy(\.valid)
    }

    public var stats: CaminoSyncQueueStats {
        let waitingMetadata = metadata.filter { $0.phase != .accepted }
        let waitingMedia = media.filter { $0.phase != .verified }
        return CaminoSyncQueueStats(
            metadataCount: waitingMetadata.count,
            mediaCount: waitingMedia.count,
            mediaBytes: waitingMedia.reduce(0) { $0 + $1.byteCount })
    }

    public var cellularBatchStats: CaminoSyncQueueStats {
        let waiting = media.filter { $0.batchID == openBatchID && $0.phase != .verified }
        return CaminoSyncQueueStats(
            metadataCount: metadata.filter { $0.phase != .accepted }.count,
            mediaCount: waiting.count,
            mediaBytes: waiting.reduce(0) { $0 + $1.byteCount })
    }

    public mutating func merge(metadata drafts: [CaminoSyncMetadataItem],
                               media candidates: [CaminoSyncMediaItem]) {
        let knownMetadata = Set(metadata.map(\.uniqueKey))
        metadata.append(contentsOf: drafts.filter { !knownMetadata.contains($0.uniqueKey) })
        let knownMedia = Set(media.map(\.id))
        media.append(contentsOf: candidates.filter { !knownMedia.contains($0.id) })
    }

    @discardableResult public mutating func observeServer(
        serverID newServerID: UUID, epoch newEpoch: UUID, cursor: Int64,
        at date: Date = Date()
    ) -> CaminoSyncServerTransition {
        lastContactUTCMilliseconds = Int64((date.timeIntervalSince1970 * 1_000).rounded())
        serverCursor = max(0, cursor)
        guard let epoch else {
            serverID = newServerID
            self.epoch = newEpoch
            observedEpoch = newEpoch
            return .adopted
        }
        guard epoch == newEpoch, serverID == newServerID else {
            observedEpoch = newEpoch
            reconciliationRequired = true
            return .epochChanged(previous: epoch, observed: newEpoch)
        }
        observedEpoch = newEpoch
        return .unchanged
    }

    /// The grant is frozen to the currently displayed batch. A fresh batch ID
    /// is opened immediately, so later captures can never inherit this grant.
    public mutating func grantCellularForDisplayedBatch() -> CaminoSyncQueueStats {
        let granted = cellularBatchStats
        cellularBatchID = openBatchID
        openBatchID = UUID()
        return granted
    }

    public mutating func revokeCellularIfFinished() {
        guard let cellularBatchID else { return }
        if !media.contains(where: { $0.batchID == cellularBatchID && $0.phase != .verified }) {
            self.cellularBatchID = nil
        }
    }

    public func nextWork(networkAvailable: Bool, expensive: Bool) -> CaminoSyncNextWork {
        guard !paused, networkAvailable, !reconciliationRequired else { return .none }
        guard !expensive || cellularBatchID != nil else { return .none }
        if let item = metadata.first(where: { $0.phase != .accepted }) {
            return item.phase == .pending ? .metadata(item.id) : .none
        }
        let candidate = media
            .filter { item in
                guard item.phase != .verified && item.phase != .needsAttention else { return false }
                return !expensive || item.batchID == cellularBatchID
            }
            .sorted { lhs, rhs in
                lhs.kind.priority == rhs.kind.priority
                    ? lhs.id.uuidString < rhs.id.uuidString
                    : lhs.kind.priority < rhs.kind.priority
            }.first
        return candidate.map { .media($0.id) } ?? .none
    }

    public mutating func exactEnvelope(for id: UUID) throws -> Data {
        guard let epoch, let index = metadata.firstIndex(where: { $0.id == id }) else {
            throw CaminoSyncError.invalidJournal
        }
        if let exact = metadata[index].exactEnvelope { return exact }
        let sequence = max(metadata.compactMap(\.sequence).max() ?? 0, serverCursor) + 1
        let payload = try JSONSerialization.jsonObject(with: metadata[index].payload)
        let envelope: [String: Any] = [
            "contract_version": 1,
            "epoch": epoch.uuidString.lowercased(),
            "operation_id": metadata[index].id.uuidString.lowercased(),
            "device_sequence": sequence,
            "device_id": deviceID.uuidString.lowercased(),
            "kind": metadata[index].kind,
            "expected_revision": metadata[index].expectedRevision.map { $0 as Any } ?? NSNull(),
            "payload": payload,
        ]
        let exact = try JSONSerialization.data(
            withJSONObject: envelope, options: [.sortedKeys, .withoutEscapingSlashes])
        metadata[index].sequence = sequence
        metadata[index].exactEnvelope = exact
        return exact
    }
}

public struct CaminoSyncDiscovery: Sendable {
    public let metadata: [CaminoSyncMetadataItem]
    public let media: [CaminoSyncMediaItem]

    public init(trips: [LocalTrip], days: [LocalDay],
                moments: [LocalMomentSyncSnapshot],
                media: [CaminoSyncMediaItem]) throws {
        let dayByTripAndDate = Dictionary(uniqueKeysWithValues: days.map {
            ("\($0.tripID.uuidString.lowercased())|\($0.localDate)", $0)
        })
        var drafts: [CaminoSyncMetadataItem] = []
        for trip in trips.sorted(by: { $0.id.uuidString < $1.id.uuidString }) {
            drafts.append(try Self.item(
                key: "trip:\(trip.id)", kind: "create_trip", objectID: trip.id,
                payload: [
                    "id": trip.id.uuidString.lowercased(), "name": trip.name,
                    "language": trip.language, "active": trip.active,
                    "viewer_enabled": trip.viewerEnabled,
                    "start_date": trip.startDate.map { $0 as Any } ?? NSNull(),
                ]))
        }
        for day in days.sorted(by: { $0.localDate == $1.localDate
            ? $0.id.uuidString < $1.id.uuidString : $0.localDate < $1.localDate }) {
            drafts.append(try Self.item(
                key: "day:\(day.id)", kind: "create_day", objectID: day.id,
                payload: [
                    "id": day.id.uuidString.lowercased(),
                    "trip_id": day.tripID.uuidString.lowercased(),
                    "local_date": day.localDate,
                ]))
        }
        let orderedMoments = moments.sorted { lhs, rhs in
            if (lhs.relatedMomentID == nil) != (rhs.relatedMomentID == nil) {
                return lhs.relatedMomentID == nil
            }
            return lhs.moment.capture.utcMilliseconds < rhs.moment.capture.utcMilliseconds
        }
        for snapshot in orderedMoments {
            let moment = snapshot.moment
            let key = "\(moment.tripID.uuidString.lowercased())|\(snapshot.originalChapterDate)"
            guard let originalDay = dayByTripAndDate[key] else {
                throw CaminoSyncError.incompleteLocalInventory
            }
            drafts.append(try Self.item(
                key: "moment:\(moment.id)", kind: "create_moment", objectID: moment.id,
                payload: [
                    "id": moment.id.uuidString.lowercased(),
                    "trip_id": moment.tripID.uuidString.lowercased(),
                    "day_id": originalDay.id.uuidString.lowercased(),
                    "chapter_date": snapshot.originalChapterDate,
                    "kind": moment.kind.rawValue,
                    "captured": [
                        "utc_ms": moment.capture.utcMilliseconds,
                        "local_wall": moment.capture.localWall,
                        "utc_offset_minutes": moment.capture.offsetMinutes,
                        "time_zone_id": moment.capture.timeZoneID,
                        "source": "device_capture", "uncertain": false,
                    ],
                    "privacy": snapshot.originalPrivacy.rawValue,
                    "revision": snapshot.baseRevision,
                    "hidden": snapshot.originalHidden,
                    "important": moment.important,
                    "related_moment_id": snapshot.relatedMomentID.map {
                        $0.uuidString.lowercased() as Any
                    } ?? NSNull(),
                    "location": NSNull(),
                ]))
        }
        for asset in media.sorted(by: { $0.id.uuidString < $1.id.uuidString }) {
            drafts.append(try Self.item(
                key: "asset:\(asset.id)", kind: "create_asset", objectID: asset.id,
                payload: [
                    "id": asset.id.uuidString.lowercased(),
                    "moment_id": asset.momentID.uuidString.lowercased(),
                    "media_kind": asset.kind.rawValue,
                    "origin": asset.kind == .audio ? "recording" : "camera",
                    "byte_count": asset.byteCount,
                    "sha256": asset.sha256,
                    "duration_ms": asset.durationMilliseconds.map { $0 as Any } ?? NSNull(),
                ]))
        }
        struct OrderedLocalOperation {
            let snapshot: LocalMomentSyncSnapshot
            let operation: LocalPendingOperation
        }
        let edits = moments.flatMap { snapshot in
            snapshot.operations.map { OrderedLocalOperation(snapshot: snapshot, operation: $0) }
        }.sorted { $0.operation.deviceSequence < $1.operation.deviceSequence }
        var wireRevision = Dictionary(uniqueKeysWithValues: moments.map {
            ($0.moment.id, $0.baseRevision)
        })
        for edit in edits {
            let operation = edit.operation
            guard let expected = wireRevision[operation.momentID] else {
                throw CaminoSyncError.incompleteLocalInventory
            }
            switch operation.kind {
            case .privacy:
                guard let privacy = operation.privacy,
                      let action = operation.privacyAction else {
                    throw CaminoSyncError.incompleteLocalInventory
                }
                drafts.append(try Self.item(
                    id: operation.id, key: "operation:\(operation.id)",
                    kind: "update_metadata", objectID: operation.momentID,
                    expectedRevision: expected,
                    payload: ["moment_id": operation.momentID.uuidString.lowercased(),
                              "change": ["type": "privacy",
                                         "new_privacy": privacy.rawValue,
                                         "user_action": action.rawValue]]))
                wireRevision[operation.momentID] = expected + 1
            case .hidden:
                guard let hidden = operation.hidden else {
                    throw CaminoSyncError.incompleteLocalInventory
                }
                drafts.append(try Self.item(
                    id: operation.id, key: "operation:\(operation.id)",
                    kind: "update_metadata", objectID: operation.momentID,
                    expectedRevision: expected,
                    payload: ["moment_id": operation.momentID.uuidString.lowercased(),
                              "change": ["type": "hidden", "hidden": hidden]]))
                wireRevision[operation.momentID] = expected + 1
            case .chapter:
                guard let date = operation.chapterDate,
                      let day = dayByTripAndDate[
                        "\(edit.snapshot.moment.tripID.uuidString.lowercased())|\(date)"] else {
                    throw CaminoSyncError.incompleteLocalInventory
                }
                drafts.append(try Self.item(
                    id: operation.id, key: "operation:\(operation.id)",
                    kind: "update_metadata", objectID: operation.momentID,
                    expectedRevision: expected,
                    payload: ["moment_id": operation.momentID.uuidString.lowercased(),
                              "change": ["type": "chapter",
                                         "day_id": day.id.uuidString.lowercased()]]))
                wireRevision[operation.momentID] = expected + 1
            case .appendText:
                guard let revisionID = operation.textRevisionID,
                      let text = edit.snapshot.textHistory.revisions.first(where: {
                        $0.id == revisionID }) else {
                    throw CaminoSyncError.incompleteLocalInventory
                }
                drafts.append(try Self.item(
                    id: operation.id, key: "operation:\(operation.id)",
                    kind: "append_text", objectID: text.id,
                    expectedRevision: expected,
                    payload: [
                        "id": text.id.uuidString.lowercased(),
                        "moment_id": text.momentID.uuidString.lowercased(),
                        "role": text.role.rawValue, "content": text.content,
                        "source_ids": text.sourceIDs.map { $0.uuidString.lowercased() },
                        "parent_revision_id": text.parentRevisionID.map {
                            $0.uuidString.lowercased() as Any
                        } ?? NSNull(),
                        "created_at_utc_ms": text.createdAtUTCMilliseconds,
                    ]))
                // C03b append_text intentionally keeps Moment metadata revision.
            }
        }
        self.metadata = drafts
        self.media = media
    }

    private static func item(id: UUID? = nil, key: String, kind: String,
                             objectID: UUID, expectedRevision: Int? = nil,
                             payload: [String: Any]) throws -> CaminoSyncMetadataItem {
        let payloadData = try JSONSerialization.data(
            withJSONObject: payload, options: [.sortedKeys, .withoutEscapingSlashes])
        return CaminoSyncMetadataItem(
            id: id ?? CaminoStableID.uuid(namespace: "camino-c05b-operation", value: key),
            uniqueKey: key, kind: kind, objectID: objectID,
            expectedRevision: expectedRevision, payload: payloadData)
    }
}

public enum CaminoStableID {
    public static func uuid(namespace: String, value: String) -> UUID {
        let digest = SHA256.hash(data: Data("\(namespace)\u{0}\(value)".utf8))
        var bytes = Array(digest.prefix(16))
        bytes[6] = (bytes[6] & 0x0f) | 0x50
        bytes[8] = (bytes[8] & 0x3f) | 0x80
        return UUID(uuid: (bytes[0], bytes[1], bytes[2], bytes[3],
                           bytes[4], bytes[5], bytes[6], bytes[7],
                           bytes[8], bytes[9], bytes[10], bytes[11],
                           bytes[12], bytes[13], bytes[14], bytes[15]))
    }
}

public enum CaminoSyncError: Error, LocalizedError, Equatable {
    case invalidJournal
    case incompleteLocalInventory
    case invalidServerResponse
    case serverConflict(String)

    public var errorDescription: String? {
        switch self {
        case .invalidJournal:
            "Frontu přenosů nelze bezpečně načíst. Místní data se nemažou."
        case .incompleteLocalInventory:
            "Místní inventář není úplný. Přenos se zastavil a data zůstávají v telefonu."
        case .invalidServerResponse:
            "Odpověď domácího Macu nelze ověřit. Přenos zůstává čekat."
        case .serverConflict(let code):
            "Domácí Mac odmítl změnu (\(code)). Data zůstávají v telefonu."
        }
    }
}

public struct CaminoSyncJournalStore: Sendable {
    public let url: URL

    public init(url: URL) { self.url = url }

    public func loadOrCreate() throws -> CaminoSyncJournal {
        guard FileManager.default.fileExists(atPath: url.path) else {
            return CaminoSyncJournal()
        }
        do {
            let value = try JSONDecoder().decode(
                CaminoSyncJournal.self, from: Data(contentsOf: url, options: .uncached))
            guard value.valid else { throw CaminoSyncError.invalidJournal }
            return value
        } catch let error as CaminoSyncError { throw error }
        catch { throw CaminoSyncError.invalidJournal }
    }

    public func save(_ journal: CaminoSyncJournal) throws {
        guard journal.valid else { throw CaminoSyncError.invalidJournal }
        let parent = url.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: parent, withIntermediateDirectories: true)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        var options: Data.WritingOptions = .atomic
        #if os(iOS)
        options.insert(.completeFileProtectionUntilFirstUserAuthentication)
        #endif
        try encoder.encode(journal).write(to: url, options: options)
    }
}
