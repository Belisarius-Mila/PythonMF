import CoreData
import Foundation

/// C04 metadata only. Media bytes live in create-only audio/media journals.
/// A failed save never recreates, deletes, or silently migrates an existing store.
@MainActor public final class CaminoLocalStore {
    private let container: NSPersistentContainer
    private var context: NSManagedObjectContext { container.viewContext }

    public init(storeURL: URL? = nil, inMemory: Bool = false) throws {
        let container = NSPersistentContainer(name: "CaminoLocal", managedObjectModel: Self.model())
        let description = NSPersistentStoreDescription()
        if inMemory {
            description.type = NSInMemoryStoreType
        } else {
            let url = try storeURL ?? Self.defaultURL()
            try FileManager.default.createDirectory(
                at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
            #if os(iOS)
            try FileManager.default.setAttributes(
                [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
                ofItemAtPath: url.deletingLastPathComponent().path)
            description.setOption(
                FileProtectionType.completeUntilFirstUserAuthentication as NSObject,
                forKey: NSPersistentStoreFileProtectionKey)
            #endif
            description.url = url
            description.type = NSSQLiteStoreType
        }
        description.shouldMigrateStoreAutomatically = false
        description.shouldInferMappingModelAutomatically = false
        container.persistentStoreDescriptions = [description]
        var loadingError: Error?
        container.loadPersistentStores { _, error in loadingError = error }
        if let loadingError { throw loadingError }
        container.viewContext.undoManager = nil
        self.container = container
    }

    public func trips() throws -> [LocalTrip] {
        try fetch("TripRecord").map(decodeTrip).sorted { $0.name < $1.name }
    }

    public func activeTrip() throws -> LocalTrip? {
        let rows = try fetch("TripRecord", predicate: NSPredicate(format: "active == YES"))
        guard rows.count <= 1 else { throw LocalStoreError.inconsistentStore }
        return try rows.first.map(decodeTrip)
    }

    @discardableResult public func createTrip(name: String, isTest: Bool = false,
                                              id: UUID = UUID()) throws -> LocalTrip {
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { throw LocalStoreError.invalidName }
        guard try object("TripRecord", id: id) == nil else { throw LocalStoreError.duplicateIdentity }
        do {
            for old in try fetch("TripRecord") { old.setValue(false, forKey: "active") }
            let row = NSEntityDescription.insertNewObject(forEntityName: "TripRecord", into: context)
            row.setValue(id, forKey: "id")
            row.setValue(trimmed, forKey: "name")
            row.setValue("cs", forKey: "language")
            row.setValue(true, forKey: "active")
            row.setValue(isTest, forKey: "isTest")
            row.setValue(false, forKey: "viewerEnabled")
            try save()
            return try decodeTrip(row)
        } catch { context.rollback(); throw error }
    }

    public func selectTrip(_ id: UUID) throws {
        guard try object("TripRecord", id: id) != nil else { throw LocalStoreError.tripMissing }
        do {
            for row in try fetch("TripRecord") {
                row.setValue((row.value(forKey: "id") as? UUID) == id, forKey: "active")
            }
            try save()
        } catch { context.rollback(); throw error }
    }

    /// The choice applies only to future ordinary Moments, never old Moments.
    public func newMomentPrivacy() throws -> LocalPrivacy {
        let rows = try fetch("SettingRecord", predicate: NSPredicate(format: "key == %@", "newPrivacy"))
        guard rows.count <= 1 else { throw LocalStoreError.inconsistentStore }
        guard let row = rows.first else { return .diary }
        guard let raw = row.value(forKey: "value") as? String,
              let privacy = LocalPrivacy(rawValue: raw) else {
            throw LocalStoreError.inconsistentStore
        }
        return privacy
    }

    public func setNewMomentPrivacy(_ privacy: LocalPrivacy) throws {
        do {
            let rows = try fetch("SettingRecord", predicate: NSPredicate(format: "key == %@", "newPrivacy"))
            guard rows.count <= 1 else { throw LocalStoreError.inconsistentStore }
            let row = rows.first ?? NSEntityDescription.insertNewObject(
                forEntityName: "SettingRecord", into: context)
            row.setValue("newPrivacy", forKey: "key")
            row.setValue(privacy.rawValue, forKey: "value")
            try save()
        } catch { context.rollback(); throw error }
    }

    @discardableResult public func markMoment(at date: Date = Date(),
                                               timeZone: TimeZone = .current) throws -> LocalMoment {
        guard let trip = try activeTrip() else { throw LocalStoreError.noActiveTrip }
        let stamp = CaptureStamp.record(date, timeZone: timeZone)
        let privacy = try newMomentPrivacy()
        do {
            let dayID = try dayID(for: trip.id, date: stamp.chapterDate)
            let row = insertMoment(id: UUID(), tripID: trip.id, dayID: dayID,
                                   kind: .marker, privacy: privacy, stamp: stamp,
                                   audioSessionID: nil, partialAudio: false)
            try save()
            return try decodeMoment(row)
        } catch { context.rollback(); throw error }
    }

    /// Called after RecordingStore.begin creates its journal, before the driver starts.
    /// An unresolved intent remains visible after any audio or database failure.
    @discardableResult public func beginAudioIntent(
        sessionID: UUID, kind: LocalMomentKind, startedAt: Date,
        timeZone: TimeZone = .current, targetMomentID: UUID? = nil
    ) throws -> AudioIntent {
        guard kind == .comment || kind == .reflection else { throw LocalStoreError.invalidAudioIntent }
        if let existing = try object("AudioIntentRecord", id: sessionID, key: "sessionID") {
            let intent = try decodeIntent(existing)
            guard intent.kind == kind,
                  intent.attaching == (targetMomentID != nil),
                  !intent.attaching || intent.momentID == targetMomentID else {
                throw LocalStoreError.duplicateIdentity
            }
            return intent
        }
        guard let trip = try activeTrip() else { throw LocalStoreError.noActiveTrip }
        let target: LocalMoment?
        if let targetMomentID {
            guard kind == .comment,
                  let row = try object("MomentRecord", id: targetMomentID) else {
                throw LocalStoreError.invalidAudioIntent
            }
            let decoded = try decodeMoment(row)
            guard decoded.tripID == trip.id, !decoded.hidden else {
                throw LocalStoreError.invalidAudioIntent
            }
            target = decoded
        } else { target = nil }
        let privacy = try target?.privacy ??
            (kind == .reflection ? LocalPrivacy.ownerOnly : newMomentPrivacy())
        let stamp = CaptureStamp.record(startedAt, timeZone: timeZone)
        do {
            let row = NSEntityDescription.insertNewObject(
                forEntityName: "AudioIntentRecord", into: context)
            row.setValue(sessionID, forKey: "sessionID")
            row.setValue(targetMomentID ?? UUID(), forKey: "momentID")
            row.setValue(trip.id, forKey: "tripID")
            row.setValue(kind.rawValue, forKey: "kind")
            row.setValue(privacy.rawValue, forKey: "privacy")
            row.setValue(target != nil, forKey: "attaching")
            write(stamp, to: row)
            row.setValue(false, forKey: "finalized")
            try save()
            return try decodeIntent(row)
        } catch { context.rollback(); throw error }
    }

    /// The capture screen changes one ordinary Comment as a whole. A standalone
    /// Reflection requires a later conscious diary revision and stays private.
    public func setAudioIntentPrivacy(sessionID: UUID, privacy: LocalPrivacy) throws {
        guard let row = try object("AudioIntentRecord", id: sessionID, key: "sessionID"),
              let kind = LocalMomentKind(rawValue: try required(row, "kind")),
              kind == .comment,
              !(try required(row, "attaching") as Bool),
              !(try required(row, "finalized") as Bool) else {
            throw LocalStoreError.invalidAudioIntent
        }
        do {
            row.setValue(privacy.rawValue, forKey: "privacy")
            try save()
        } catch { context.rollback(); throw error }
    }

    /// Caller must first obtain this session from RecordingStore.library(), which
    /// verifies completed media. Both the Moment and intent state save together.
    @discardableResult public func acceptCompletedAudio(
        sessionID: UUID, kind: LocalMomentKind, partial: Bool
    ) throws -> LocalMoment {
        guard let intentRow = try object("AudioIntentRecord", id: sessionID, key: "sessionID") else {
            throw LocalStoreError.invalidAudioIntent
        }
        let intent = try decodeIntent(intentRow)
        guard intent.kind == kind else { throw LocalStoreError.invalidAudioIntent }
        if intent.attaching {
            if let linked = try object("AudioAttachmentRecord", id: sessionID, key: "sessionID") {
                guard (try required(linked, "momentID") as UUID) == intent.momentID else {
                    throw LocalStoreError.duplicateIdentity
                }
                guard let target = try object("MomentRecord", id: intent.momentID) else {
                    throw LocalStoreError.momentMissing
                }
                return try decodeMoment(target)
            }
            guard let target = try object("MomentRecord", id: intent.momentID),
                  (try required(target, "tripID") as UUID) == intent.tripID,
                  (try required(target, "privacy") as String) == intent.privacy.rawValue else {
                throw LocalStoreError.invalidAudioIntent
            }
            do {
                let link = NSEntityDescription.insertNewObject(
                    forEntityName: "AudioAttachmentRecord", into: context)
                link.setValue(sessionID, forKey: "sessionID")
                link.setValue(intent.momentID, forKey: "momentID")
                link.setValue(intent.tripID, forKey: "tripID")
                link.setValue(partial, forKey: "partial")
                intentRow.setValue(true, forKey: "finalized")
                try save()
                return try decodeMoment(target)
            } catch { context.rollback(); throw error }
        }
        if let existing = try object("MomentRecord", id: intent.momentID) {
            let moment = try decodeMoment(existing)
            guard moment.audioSessionID == sessionID, moment.tripID == intent.tripID,
                  moment.kind == kind, moment.privacy == intent.privacy else {
                throw LocalStoreError.duplicateIdentity
            }
            return moment
        }
        guard try object("TripRecord", id: intent.tripID) != nil else {
            throw LocalStoreError.tripMissing
        }
        do {
            let day = try dayID(for: intent.tripID, date: intent.capture.chapterDate)
            let row = insertMoment(id: intent.momentID, tripID: intent.tripID,
                                   dayID: day, kind: kind, privacy: intent.privacy,
                                   stamp: intent.capture, audioSessionID: sessionID,
                                   partialAudio: partial)
            intentRow.setValue(true, forKey: "finalized")
            try save()
            return try decodeMoment(row)
        } catch { context.rollback(); throw error }
    }

    public func pendingAudioIntents() throws -> [AudioIntent] {
        try fetch("AudioIntentRecord", predicate: NSPredicate(format: "finalized == NO"))
            .map(decodeIntent)
    }

    public func audioSessionIDs(momentID: UUID) throws -> [UUID] {
        let primary = try object("MomentRecord", id: momentID)
            .flatMap { $0.value(forKey: "audioSessionID") as? UUID }
        let attached: [UUID] = try fetch("AudioAttachmentRecord",
            predicate: NSPredicate(format: "momentID == %@", momentID as NSUUID))
            .map { try required($0, "sessionID") }
        return (primary.map { [$0] } ?? []) + attached
    }

    /// Persist identity/privacy before starting a video file or accepting a photo.
    /// An attachment explicitly names its existing Moment; proximity never links it.
    public func beginMediaIntent(kind: LocalMediaKind, targetMomentID: UUID? = nil,
                                 silentRequested: Bool = false, at date: Date = Date(),
                                 timeZone: TimeZone = .current) throws -> LocalMediaIntent {
        guard let trip = try activeTrip() else { throw LocalStoreError.noActiveTrip }
        guard kind == .video || !silentRequested else { throw LocalStoreError.invalidMediaIntent }
        let target: LocalMoment?
        if let targetMomentID {
            guard let row = try object("MomentRecord", id: targetMomentID) else {
                throw LocalStoreError.momentMissing
            }
            let decoded = try decodeMoment(row)
            guard decoded.tripID == trip.id, !decoded.hidden else {
                throw LocalStoreError.invalidMediaIntent
            }
            target = decoded
        } else { target = nil }
        let privacy = try target?.privacy ?? newMomentPrivacy()
        let stamp = CaptureStamp.record(date, timeZone: timeZone)
        do {
            let row = NSEntityDescription.insertNewObject(
                forEntityName: "MediaIntentRecord", into: context)
            row.setValue(UUID(), forKey: "assetID")
            row.setValue(target?.id ?? UUID(), forKey: "momentID")
            row.setValue(trip.id, forKey: "tripID")
            row.setValue(kind.rawValue, forKey: "kind")
            row.setValue(privacy.rawValue, forKey: "privacy")
            row.setValue(target != nil, forKey: "attaching")
            row.setValue(silentRequested, forKey: "silentRequested")
            row.setValue(false, forKey: "finalized")
            write(stamp, to: row)
            try save()
            return try decodeMediaIntent(row)
        } catch { context.rollback(); throw error }
    }

    /// Called only after the original file has been verified in its stable path.
    /// The Asset and any new Moment enter the database in one transaction.
    @discardableResult public func acceptMedia(_ intent: LocalMediaIntent,
                                               inspection: LocalMediaInspection) throws -> LocalMediaAsset {
        guard inspection.byteCount > 0, inspection.width > 0, inspection.height > 0,
              inspection.sha256.count == 64,
              inspection.sha256.allSatisfy({ $0.isHexDigit && !$0.isUppercase }),
              intent.kind == .video ||
                (inspection.durationMilliseconds == nil && !inspection.hasAudio),
              intent.kind == .photo || (inspection.durationMilliseconds ?? 0) > 0,
              !(!intent.silentRequested && intent.kind == .video && !inspection.hasAudio && !inspection.partial),
              !(intent.silentRequested && inspection.hasAudio) else {
            throw LocalStoreError.invalidMedia
        }
        guard let intentRow = try object("MediaIntentRecord", id: intent.assetID,
                                         key: "assetID"),
              try decodeMediaIntent(intentRow) == intent else {
            throw LocalStoreError.invalidMediaIntent
        }
        if let existing = try object("AssetRecord", id: intent.assetID) {
            let decoded = try decodeMediaAsset(existing)
            guard decoded.inspection == inspection,
                  decoded.momentID == intent.momentID,
                  decoded.tripID == intent.tripID else {
                throw LocalStoreError.duplicateIdentity
            }
            return decoded
        }
        do {
            if intent.attaching {
                guard let target = try object("MomentRecord", id: intent.momentID),
                      (try required(target, "tripID") as UUID) == intent.tripID,
                      (try required(target, "privacy") as String) == intent.privacy.rawValue else {
                    throw LocalStoreError.invalidMediaIntent
                }
            } else {
                guard try object("MomentRecord", id: intent.momentID) == nil else {
                    throw LocalStoreError.duplicateIdentity
                }
                let day = try dayID(for: intent.tripID, date: intent.capture.chapterDate)
                _ = insertMoment(id: intent.momentID, tripID: intent.tripID, dayID: day,
                                 kind: intent.kind.momentKind, privacy: intent.privacy,
                                 stamp: intent.capture, audioSessionID: nil,
                                 partialAudio: false)
            }
            let row = NSEntityDescription.insertNewObject(forEntityName: "AssetRecord", into: context)
            row.setValue(intent.assetID, forKey: "id")
            row.setValue(intent.momentID, forKey: "momentID")
            row.setValue(intent.tripID, forKey: "tripID")
            row.setValue(intent.kind.rawValue, forKey: "kind")
            row.setValue(intent.originalRelativePath, forKey: "relativePath")
            row.setValue(inspection.byteCount, forKey: "byteCount")
            row.setValue(inspection.sha256, forKey: "sha256")
            row.setValue(inspection.width, forKey: "width")
            row.setValue(inspection.height, forKey: "height")
            row.setValue(inspection.orientation, forKey: "orientation")
            row.setValue(inspection.durationMilliseconds, forKey: "durationMilliseconds")
            row.setValue(inspection.hasAudio, forKey: "hasAudio")
            row.setValue(inspection.partial, forKey: "partial")
            row.setValue(intent.silentRequested, forKey: "silentRequested")
            intentRow.setValue(true, forKey: "finalized")
            try save()
            return try decodeMediaAsset(row)
        } catch { context.rollback(); throw error }
    }

    public func pendingMediaIntents() throws -> [LocalMediaIntent] {
        try fetch("MediaIntentRecord", predicate: NSPredicate(format: "finalized == NO"))
            .map(decodeMediaIntent)
    }

    public func mediaAssets(momentID: UUID) throws -> [LocalMediaAsset] {
        try fetch("AssetRecord", predicate: NSPredicate(format: "momentID == %@", momentID as NSUUID))
            .map(decodeMediaAsset)
    }

    public func allMediaAssets() throws -> [LocalMediaAsset] {
        try fetch("AssetRecord").map(decodeMediaAsset)
    }

    public func moments(tripID: UUID) throws -> [LocalMoment] {
        guard try object("TripRecord", id: tripID) != nil else { throw LocalStoreError.tripMissing }
        return try fetch("MomentRecord", predicate: NSPredicate(format: "tripID == %@", tripID as NSUUID))
            .map(decodeMoment)
            .filter { !$0.hidden }
            .sorted { $0.capture.utcMilliseconds > $1.capture.utcMilliseconds }
    }

    private func dayID(for tripID: UUID, date: String) throws -> UUID {
        let rows = try fetch("DayRecord", predicate: NSPredicate(
            format: "tripID == %@ AND localDate == %@", tripID as NSUUID, date))
        guard rows.count <= 1 else { throw LocalStoreError.inconsistentStore }
        if let row = rows.first { return try required(row, "id") }
        let id = UUID()
        let row = NSEntityDescription.insertNewObject(forEntityName: "DayRecord", into: context)
        row.setValue(id, forKey: "id")
        row.setValue(tripID, forKey: "tripID")
        row.setValue(date, forKey: "localDate")
        return id
    }

    private func insertMoment(id: UUID, tripID: UUID, dayID: UUID,
                              kind: LocalMomentKind, privacy: LocalPrivacy,
                              stamp: CaptureStamp, audioSessionID: UUID?,
                              partialAudio: Bool) -> NSManagedObject {
        let row = NSEntityDescription.insertNewObject(forEntityName: "MomentRecord", into: context)
        row.setValue(id, forKey: "id")
        row.setValue(tripID, forKey: "tripID")
        row.setValue(dayID, forKey: "dayID")
        row.setValue(kind.rawValue, forKey: "kind")
        row.setValue(privacy.rawValue, forKey: "privacy")
        row.setValue(1, forKey: "revision")
        row.setValue(false, forKey: "hidden")
        row.setValue(false, forKey: "important")
        row.setValue(audioSessionID, forKey: "audioSessionID")
        row.setValue(partialAudio, forKey: "partialAudio")
        write(stamp, to: row)
        return row
    }

    private func write(_ stamp: CaptureStamp, to row: NSManagedObject) {
        row.setValue(stamp.utcMilliseconds, forKey: "utcMilliseconds")
        row.setValue(stamp.localWall, forKey: "localWall")
        row.setValue(stamp.chapterDate, forKey: "chapterDate")
        row.setValue(stamp.offsetMinutes, forKey: "offsetMinutes")
        row.setValue(stamp.timeZoneID, forKey: "timeZoneID")
    }

    private func decodeTrip(_ row: NSManagedObject) throws -> LocalTrip {
        LocalTrip(id: try required(row, "id"), name: try required(row, "name"),
                  language: try required(row, "language"),
                  active: try required(row, "active"), isTest: try required(row, "isTest"),
                  viewerEnabled: try required(row, "viewerEnabled"),
                  startDate: row.value(forKey: "startDate") as? String)
    }

    private func decodeMoment(_ row: NSManagedObject) throws -> LocalMoment {
        let kindRaw: String = try required(row, "kind")
        let privacyRaw: String = try required(row, "privacy")
        guard let kind = LocalMomentKind(rawValue: kindRaw),
              let privacy = LocalPrivacy(rawValue: privacyRaw) else {
            throw LocalStoreError.inconsistentStore
        }
        return LocalMoment(id: try required(row, "id"), tripID: try required(row, "tripID"),
                           dayID: try required(row, "dayID"), kind: kind,
                           capture: try decodeStamp(row), privacy: privacy,
                           revision: try required(row, "revision"),
                           hidden: try required(row, "hidden"),
                           important: try required(row, "important"),
                           audioSessionID: row.value(forKey: "audioSessionID") as? UUID,
                           partialAudio: try required(row, "partialAudio"))
    }

    private func decodeIntent(_ row: NSManagedObject) throws -> AudioIntent {
        let kindRaw: String = try required(row, "kind")
        let privacyRaw: String = try required(row, "privacy")
        guard let kind = LocalMomentKind(rawValue: kindRaw),
              let privacy = LocalPrivacy(rawValue: privacyRaw),
              kind != .reflection || privacy == .ownerOnly else {
            throw LocalStoreError.inconsistentStore
        }
        return AudioIntent(sessionID: try required(row, "sessionID"),
                           momentID: try required(row, "momentID"),
                           tripID: try required(row, "tripID"), kind: kind,
                           privacy: privacy, capture: try decodeStamp(row),
                           attaching: try required(row, "attaching"))
    }

    private func decodeMediaIntent(_ row: NSManagedObject) throws -> LocalMediaIntent {
        let kindRaw: String = try required(row, "kind")
        let privacyRaw: String = try required(row, "privacy")
        guard let kind = LocalMediaKind(rawValue: kindRaw),
              let privacy = LocalPrivacy(rawValue: privacyRaw) else {
            throw LocalStoreError.inconsistentStore
        }
        return LocalMediaIntent(assetID: try required(row, "assetID"),
                                momentID: try required(row, "momentID"),
                                tripID: try required(row, "tripID"), kind: kind,
                                privacy: privacy, capture: try decodeStamp(row),
                                attaching: try required(row, "attaching"),
                                silentRequested: try required(row, "silentRequested"))
    }

    private func decodeMediaAsset(_ row: NSManagedObject) throws -> LocalMediaAsset {
        let kindRaw: String = try required(row, "kind")
        guard let kind = LocalMediaKind(rawValue: kindRaw) else {
            throw LocalStoreError.inconsistentStore
        }
        let inspection = LocalMediaInspection(
            byteCount: try required(row, "byteCount"), sha256: try required(row, "sha256"),
            width: try required(row, "width"), height: try required(row, "height"),
            orientation: try required(row, "orientation"),
            durationMilliseconds: row.value(forKey: "durationMilliseconds") as? Int64,
            hasAudio: try required(row, "hasAudio"), partial: try required(row, "partial"))
        return LocalMediaAsset(id: try required(row, "id"),
                               momentID: try required(row, "momentID"),
                               tripID: try required(row, "tripID"), kind: kind,
                               relativePath: try required(row, "relativePath"),
                               inspection: inspection,
                               silentRequested: try required(row, "silentRequested"))
    }

    private func decodeStamp(_ row: NSManagedObject) throws -> CaptureStamp {
        let localWall: String = try required(row, "localWall")
        let chapterDate: String = try required(row, "chapterDate")
        guard localWall.hasPrefix(chapterDate) else { throw LocalStoreError.inconsistentStore }
        return CaptureStamp(utcMilliseconds: try required(row, "utcMilliseconds"),
                            localWall: localWall, chapterDate: chapterDate,
                            offsetMinutes: try required(row, "offsetMinutes"),
                            timeZoneID: try required(row, "timeZoneID"))
    }

    private func required<T>(_ row: NSManagedObject, _ key: String) throws -> T {
        guard let value = row.value(forKey: key) as? T else { throw LocalStoreError.inconsistentStore }
        return value
    }

    private func object(_ entity: String, id: UUID, key: String = "id") throws -> NSManagedObject? {
        let rows = try fetch(entity, predicate: NSPredicate(format: "%K == %@", key, id as NSUUID))
        guard rows.count <= 1 else { throw LocalStoreError.inconsistentStore }
        return rows.first
    }

    private func fetch(_ entity: String, predicate: NSPredicate? = nil) throws -> [NSManagedObject] {
        let request = NSFetchRequest<NSManagedObject>(entityName: entity)
        request.predicate = predicate
        return try context.fetch(request)
    }

    private func save() throws {
        if context.hasChanges { try context.save() }
    }

    private static func defaultURL() throws -> URL {
        try FileManager.default.url(for: .applicationSupportDirectory,
                                    in: .userDomainMask, appropriateFor: nil, create: true)
            .appendingPathComponent("Camino", isDirectory: true)
            .appendingPathComponent("metadata.sqlite")
    }

    private static func model() -> NSManagedObjectModel {
        let model = NSManagedObjectModel()
        func attribute(_ name: String, _ type: NSAttributeType,
                       optional: Bool = false) -> NSAttributeDescription {
            let result = NSAttributeDescription()
            result.name = name
            result.attributeType = type
            result.isOptional = optional
            return result
        }
        func entity(_ name: String, _ fields: [NSAttributeDescription],
                    unique: [[String]]) -> NSEntityDescription {
            let result = NSEntityDescription()
            result.name = name
            result.managedObjectClassName = NSStringFromClass(NSManagedObject.self)
            result.properties = fields
            result.uniquenessConstraints = unique
            return result
        }
        let uuid = NSAttributeType.UUIDAttributeType
        let text = NSAttributeType.stringAttributeType
        let flag = NSAttributeType.booleanAttributeType
        let integer = NSAttributeType.integer64AttributeType
        let offset = NSAttributeType.integer32AttributeType
        func stamp() -> [NSAttributeDescription] { [
            attribute("utcMilliseconds", integer), attribute("localWall", text),
            attribute("chapterDate", text), attribute("offsetMinutes", offset),
            attribute("timeZoneID", text),
        ] }
        model.entities = [
            entity("TripRecord", [
                attribute("id", uuid), attribute("name", text), attribute("language", text),
                attribute("active", flag), attribute("isTest", flag),
                attribute("viewerEnabled", flag), attribute("startDate", text, optional: true),
            ], unique: [["id"]]),
            entity("DayRecord", [
                attribute("id", uuid), attribute("tripID", uuid), attribute("localDate", text),
            ], unique: [["id"], ["tripID", "localDate"]]),
            entity("MomentRecord", [
                attribute("id", uuid), attribute("tripID", uuid), attribute("dayID", uuid),
                attribute("kind", text), attribute("privacy", text), attribute("revision", integer),
                attribute("hidden", flag), attribute("important", flag),
                attribute("audioSessionID", uuid, optional: true), attribute("partialAudio", flag),
            ] + stamp(), unique: [["id"], ["audioSessionID"]]),
            entity("AudioIntentRecord", [
                attribute("sessionID", uuid), attribute("momentID", uuid),
                attribute("tripID", uuid), attribute("kind", text),
                attribute("privacy", text), attribute("attaching", flag),
                attribute("finalized", flag),
            ] + stamp(), unique: [["sessionID"]]),
            entity("AudioAttachmentRecord", [
                attribute("sessionID", uuid), attribute("momentID", uuid),
                attribute("tripID", uuid), attribute("partial", flag),
            ], unique: [["sessionID"]]),
            entity("SettingRecord", [attribute("key", text), attribute("value", text)],
                   unique: [["key"]]),
            entity("MediaIntentRecord", [
                attribute("assetID", uuid), attribute("momentID", uuid),
                attribute("tripID", uuid), attribute("kind", text),
                attribute("privacy", text), attribute("attaching", flag),
                attribute("silentRequested", flag), attribute("finalized", flag),
            ] + stamp(), unique: [["assetID"]]),
            entity("AssetRecord", [
                attribute("id", uuid), attribute("momentID", uuid),
                attribute("tripID", uuid), attribute("kind", text),
                attribute("relativePath", text), attribute("byteCount", integer),
                attribute("sha256", text), attribute("width", integer),
                attribute("height", integer), attribute("orientation", integer),
                attribute("durationMilliseconds", integer, optional: true),
                attribute("hasAudio", flag), attribute("partial", flag),
                attribute("silentRequested", flag),
            ], unique: [["id"], ["relativePath"]]),
        ]
        return model
    }
}
