import CoreData
import Foundation

private struct LocalMomentJournal: Codable, Equatable {
    let schemaVersion: Int
    let momentID: UUID
    let tripID: UUID
    let baseRevision: Int
    let originalPrivacy: LocalPrivacy
    let originalHidden: Bool
    let originalChapterDate: String
    var currentChapterDate: String
    var relatedMomentID: UUID?
    var textHistory: LocalTextHistory
    var operations: [LocalPendingOperation]
}

private struct LocalPendingMomentLink: Codable, Equatable {
    let sessionID: UUID
    let parentMomentID: UUID
}

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
        timeZone: TimeZone = .current, targetMomentID: UUID? = nil,
        relatedMomentID: UUID? = nil
    ) throws -> AudioIntent {
        guard kind == .comment || kind == .reflection else { throw LocalStoreError.invalidAudioIntent }
        if let existing = try object("AudioIntentRecord", id: sessionID, key: "sessionID") {
            let intent = try decodeIntent(existing)
            let pendingLink = try pendingMomentLink(sessionID: sessionID)
            guard intent.kind == kind,
                  intent.attaching == (targetMomentID != nil),
                  !intent.attaching || intent.momentID == targetMomentID,
                  pendingLink?.parentMomentID == relatedMomentID else {
                throw LocalStoreError.duplicateIdentity
            }
            return intent
        }
        guard targetMomentID == nil || relatedMomentID == nil,
              relatedMomentID == nil || kind == .reflection else {
            throw LocalStoreError.invalidAudioIntent
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
        if let relatedMomentID {
            guard let row = try object("MomentRecord", id: relatedMomentID) else {
                throw LocalStoreError.invalidAudioIntent
            }
            let decoded = try decodeMoment(row)
            guard decoded.tripID == trip.id, !decoded.hidden else {
                throw LocalStoreError.invalidAudioIntent
            }
        }
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
            if let relatedMomentID {
                try setEncodedSetting(LocalPendingMomentLink(
                    sessionID: sessionID, parentMomentID: relatedMomentID),
                    key: pendingLinkKey(sessionID))
            }
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
            if let link = try pendingMomentLink(sessionID: sessionID) {
                guard kind == .reflection,
                      let parent = try object("MomentRecord", id: link.parentMomentID),
                      (try required(parent, "tripID") as UUID) == intent.tripID else {
                    throw LocalStoreError.invalidAudioIntent
                }
                var journal = try momentJournal(row)
                journal.relatedMomentID = link.parentMomentID
                try setMomentJournal(journal)
            }
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

    public func moments(tripID: UUID, includeHidden: Bool = false) throws -> [LocalMoment] {
        guard try object("TripRecord", id: tripID) != nil else { throw LocalStoreError.tripMissing }
        return try fetch("MomentRecord", predicate: NSPredicate(format: "tripID == %@", tripID as NSUUID))
            .map(decodeMoment)
            .filter { includeHidden || !$0.hidden }
            .sorted { $0.capture.utcMilliseconds > $1.capture.utcMilliseconds }
    }

    public func textHistory(momentID: UUID) throws -> LocalTextHistory {
        guard let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.momentMissing
        }
        return try momentJournal(row).textHistory
    }

    public func pendingOperations(momentID: UUID) throws -> [LocalPendingOperation] {
        guard let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.momentMissing
        }
        return try momentJournal(row).operations
    }

    /// A draft is durable local state, but never a published text revision.
    public func saveTextDraft(momentID: UUID, content: String,
                              at date: Date = Date()) throws {
        guard let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.momentMissing
        }
        do {
            var journal = try momentJournal(row)
            let base = journal.textHistory.draft?.baseRevisionID ??
                journal.textHistory.readerRevision?.id
            journal.textHistory = LocalTextHistory(
                revisions: journal.textHistory.revisions,
                draft: LocalTextDraft(momentID: momentID, baseRevisionID: base,
                    content: content, updatedAtUTCMilliseconds: milliseconds(date)))
            try setMomentJournal(journal)
            try save()
        } catch { context.rollback(); throw error }
    }

    public func discardTextDraft(momentID: UUID) throws {
        guard let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.momentMissing
        }
        do {
            var journal = try momentJournal(row)
            journal.textHistory = LocalTextHistory(
                revisions: journal.textHistory.revisions, draft: nil)
            try setMomentJournal(journal)
            try save()
        } catch { context.rollback(); throw error }
    }

    /// Saves the current draft as a typed source or a later human revision.
    @discardableResult public func commitTextDraft(
        momentID: UUID, revisionID: UUID = UUID(), operationID: UUID = UUID(),
        expectedRevision: Int? = nil, at date: Date = Date()
    ) throws -> LocalTextRevision {
        guard let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.momentMissing
        }
        var journal = try momentJournal(row)
        guard let draft = journal.textHistory.draft,
              !draft.content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw LocalStoreError.invalidText
        }
        let currentRevision: Int = try required(row, "revision")
        let expected = expectedRevision ?? currentRevision
        guard expected == currentRevision else { throw LocalStoreError.revisionConflict }
        guard !journal.textHistory.revisions.contains(where: { $0.id == revisionID }) else {
            throw LocalStoreError.operationConflict
        }
        if try existingOperation(id: operationID) != nil {
            throw LocalStoreError.operationConflict
        }
        let parent = journal.textHistory.readerRevision?.id
        let text = LocalTextRevision(
            id: revisionID, momentID: momentID,
            role: journal.textHistory.revisions.isEmpty ? .typedSource : .humanRevision,
            content: draft.content, sourceIDs: parent.map { [$0] } ?? [],
            parentRevisionID: parent, createdAtUTCMilliseconds: milliseconds(date))
        do {
            let operation = try makeOperation(
                id: operationID, momentID: momentID, expectedRevision: expected,
                kind: .appendText, at: date, textRevisionID: revisionID)
            journal.textHistory = LocalTextHistory(
                revisions: journal.textHistory.revisions + [text], draft: nil)
            journal.operations.append(operation)
            row.setValue(currentRevision + 1, forKey: "revision")
            try setMomentJournal(journal)
            try save()
            return text
        } catch { context.rollback(); throw error }
    }

    /// Used by later transcription integration; a late AI revision stays in
    /// history and cannot become the reader text over a human revision.
    @discardableResult public func appendTextRevision(
        momentID: UUID, role: LocalTextRole, content: String,
        sourceIDs: [UUID] = [], parentRevisionID: UUID? = nil,
        revisionID: UUID = UUID(), operationID: UUID = UUID(),
        expectedRevision: Int? = nil, at date: Date = Date()
    ) throws -> LocalTextRevision {
        guard !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.invalidText
        }
        var journal = try momentJournal(row)
        let candidate = LocalTextRevision(
            id: revisionID, momentID: momentID, role: role, content: content,
            sourceIDs: sourceIDs, parentRevisionID: parentRevisionID,
            createdAtUTCMilliseconds: milliseconds(date))
        if let prior = journal.textHistory.revisions.first(where: { $0.id == revisionID }) {
            guard prior == candidate else { throw LocalStoreError.operationConflict }
            return prior
        }
        if let parentRevisionID,
           !journal.textHistory.revisions.contains(where: { $0.id == parentRevisionID }) {
            throw LocalStoreError.invalidText
        }
        let currentRevision: Int = try required(row, "revision")
        if let prior = try existingOperation(id: operationID) {
            let requestedExpected = expectedRevision ?? prior.expectedRevision
            guard prior.momentID == momentID, prior.kind == .appendText,
                  prior.expectedRevision == requestedExpected,
                  prior.textRevisionID == revisionID else {
                throw LocalStoreError.operationConflict
            }
            guard let saved = journal.textHistory.revisions.first(where: { $0.id == revisionID }) else {
                throw LocalStoreError.inconsistentStore
            }
            return saved
        }
        let expected = expectedRevision ?? currentRevision
        guard expected == currentRevision else { throw LocalStoreError.revisionConflict }
        do {
            let operation = try makeOperation(
                id: operationID, momentID: momentID, expectedRevision: expected,
                kind: .appendText, at: date, textRevisionID: revisionID)
            journal.textHistory = LocalTextHistory(
                revisions: journal.textHistory.revisions + [candidate],
                draft: journal.textHistory.draft)
            journal.operations.append(operation)
            row.setValue(currentRevision + 1, forKey: "revision")
            try setMomentJournal(journal)
            try save()
            return candidate
        } catch { context.rollback(); throw error }
    }

    @discardableResult public func changePrivacy(
        momentID: UUID, to privacy: LocalPrivacy, action: LocalPrivacyAction,
        operationID: UUID = UUID(), expectedRevision: Int? = nil,
        at date: Date = Date()
    ) throws -> LocalMoment {
        guard let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.momentMissing
        }
        let current = try decodeMoment(row)
        let currentRevision = current.revision
        if let prior = try existingOperation(id: operationID) {
            let requestedExpected = expectedRevision ?? prior.expectedRevision
            guard prior.momentID == momentID, prior.kind == .privacy,
                  prior.expectedRevision == requestedExpected, prior.privacy == privacy,
                  prior.privacyAction == action else {
                throw LocalStoreError.operationConflict
            }
            return current
        }
        let expected = expectedRevision ?? currentRevision
        guard expected == currentRevision else { throw LocalStoreError.revisionConflict }
        guard current.privacy != privacy else { throw LocalStoreError.invalidMetadataChange }
        let requiredAction: LocalPrivacyAction
        if privacy == .ownerOnly {
            requiredAction = .lock
        } else if current.kind == .reflection {
            requiredAction = .insertReflectionIntoDiary
        } else {
            requiredAction = .unlock
        }
        guard action == requiredAction else { throw LocalStoreError.invalidMetadataChange }
        do {
            var journal = try momentJournal(row)
            let operation = try makeOperation(
                id: operationID, momentID: momentID, expectedRevision: expected,
                kind: .privacy, at: date, privacy: privacy, privacyAction: action)
            journal.operations.append(operation)
            row.setValue(privacy.rawValue, forKey: "privacy")
            row.setValue(currentRevision + 1, forKey: "revision")
            try setMomentJournal(journal)
            try save()
            return try decodeMoment(row)
        } catch { context.rollback(); throw error }
    }

    @discardableResult public func setHidden(
        momentID: UUID, hidden: Bool, operationID: UUID = UUID(),
        expectedRevision: Int? = nil, at date: Date = Date()
    ) throws -> LocalMoment {
        guard let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.momentMissing
        }
        let current = try decodeMoment(row)
        if let prior = try existingOperation(id: operationID) {
            let requestedExpected = expectedRevision ?? prior.expectedRevision
            guard prior.momentID == momentID, prior.kind == .hidden,
                  prior.expectedRevision == requestedExpected, prior.hidden == hidden else {
                throw LocalStoreError.operationConflict
            }
            return current
        }
        let expected = expectedRevision ?? current.revision
        guard expected == current.revision else { throw LocalStoreError.revisionConflict }
        guard current.hidden != hidden else { throw LocalStoreError.invalidMetadataChange }
        do {
            var journal = try momentJournal(row)
            let operation = try makeOperation(
                id: operationID, momentID: momentID, expectedRevision: expected,
                kind: .hidden, at: date, hidden: hidden)
            journal.operations.append(operation)
            row.setValue(hidden, forKey: "hidden")
            row.setValue(current.revision + 1, forKey: "revision")
            try setMomentJournal(journal)
            try save()
            return try decodeMoment(row)
        } catch { context.rollback(); throw error }
    }

    @discardableResult public func moveMoment(
        momentID: UUID, toChapterDate chapterDate: String,
        operationID: UUID = UUID(), expectedRevision: Int? = nil,
        at date: Date = Date()
    ) throws -> LocalMoment {
        guard validChapterDate(chapterDate),
              let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.invalidMetadataChange
        }
        let current = try decodeMoment(row)
        if let prior = try existingOperation(id: operationID) {
            let requestedExpected = expectedRevision ?? prior.expectedRevision
            guard prior.momentID == momentID, prior.kind == .chapter,
                  prior.expectedRevision == requestedExpected,
                  prior.chapterDate == chapterDate else {
                throw LocalStoreError.operationConflict
            }
            return current
        }
        let expected = expectedRevision ?? current.revision
        guard expected == current.revision else { throw LocalStoreError.revisionConflict }
        guard current.chapterDate != chapterDate else {
            throw LocalStoreError.invalidMetadataChange
        }
        do {
            var journal = try momentJournal(row)
            let operation = try makeOperation(
                id: operationID, momentID: momentID, expectedRevision: expected,
                kind: .chapter, at: date, chapterDate: chapterDate)
            journal.currentChapterDate = chapterDate
            journal.operations.append(operation)
            row.setValue(try dayID(for: current.tripID, date: chapterDate), forKey: "dayID")
            row.setValue(current.revision + 1, forKey: "revision")
            try setMomentJournal(journal)
            try save()
            return try decodeMoment(row)
        } catch { context.rollback(); throw error }
    }

    /// The star is currently a local reading aid. C05 must decide how it enters
    /// the versioned wire contract, which does not yet define this operation.
    @discardableResult public func setImportant(momentID: UUID,
                                                important: Bool) throws -> LocalMoment {
        guard let row = try object("MomentRecord", id: momentID) else {
            throw LocalStoreError.momentMissing
        }
        do {
            row.setValue(important, forKey: "important")
            try save()
            return try decodeMoment(row)
        } catch { context.rollback(); throw error }
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

    private func momentJournal(_ row: NSManagedObject) throws -> LocalMomentJournal {
        let id: UUID = try required(row, "id")
        let tripID: UUID = try required(row, "tripID")
        let revision: Int = try required(row, "revision")
        let privacyRaw: String = try required(row, "privacy")
        let hidden: Bool = try required(row, "hidden")
        let capture = try decodeStamp(row)
        guard let privacy = LocalPrivacy(rawValue: privacyRaw) else {
            throw LocalStoreError.inconsistentStore
        }
        guard let journal: LocalMomentJournal = try encodedSetting(journalKey(id)) else {
            return LocalMomentJournal(
                schemaVersion: 1, momentID: id, tripID: tripID,
                baseRevision: revision, originalPrivacy: privacy,
                originalHidden: hidden, originalChapterDate: capture.chapterDate,
                currentChapterDate: capture.chapterDate, relatedMomentID: nil,
                textHistory: LocalTextHistory(), operations: [])
        }
        guard journal.schemaVersion == 1, journal.momentID == id,
              journal.tripID == tripID, journal.baseRevision >= 1,
              validChapterDate(journal.originalChapterDate),
              validChapterDate(journal.currentChapterDate),
              journal.baseRevision + journal.operations.count == revision,
              journal.textHistory.revisions.allSatisfy({ $0.momentID == id }),
              journal.textHistory.draft?.momentID == id || journal.textHistory.draft == nil,
              journal.operations.allSatisfy({ $0.momentID == id }),
              Set(journal.operations.map(\.id)).count == journal.operations.count,
              Set(journal.operations.map(\.deviceSequence)).count == journal.operations.count else {
            throw LocalStoreError.inconsistentStore
        }
        return journal
    }

    private func setMomentJournal(_ journal: LocalMomentJournal) throws {
        try setEncodedSetting(journal, key: journalKey(journal.momentID))
    }

    private func pendingMomentLink(sessionID: UUID) throws -> LocalPendingMomentLink? {
        let value: LocalPendingMomentLink? = try encodedSetting(pendingLinkKey(sessionID))
        guard value?.sessionID == sessionID || value == nil else {
            throw LocalStoreError.inconsistentStore
        }
        return value
    }

    private func existingOperation(id: UUID) throws -> LocalPendingOperation? {
        let rows = try fetch("SettingRecord", predicate: NSPredicate(
            format: "key BEGINSWITH %@", Self.journalPrefix))
        var matches: [LocalPendingOperation] = []
        for row in rows {
            guard let raw = row.value(forKey: "value") as? String,
                  let data = raw.data(using: .utf8),
                  let journal = try? JSONDecoder().decode(LocalMomentJournal.self, from: data) else {
                throw LocalStoreError.inconsistentStore
            }
            matches.append(contentsOf: journal.operations.filter { $0.id == id })
        }
        guard matches.count <= 1 else { throw LocalStoreError.inconsistentStore }
        return matches.first
    }

    private func makeOperation(
        id: UUID, momentID: UUID, expectedRevision: Int,
        kind: LocalOperationKind, at date: Date,
        privacy: LocalPrivacy? = nil, privacyAction: LocalPrivacyAction? = nil,
        hidden: Bool? = nil, chapterDate: String? = nil,
        textRevisionID: UUID? = nil
    ) throws -> LocalPendingOperation {
        let sequence = try nextDeviceSequence()
        return LocalPendingOperation(
            id: id, momentID: momentID, deviceSequence: sequence,
            expectedRevision: expectedRevision, kind: kind,
            createdAtUTCMilliseconds: milliseconds(date), privacy: privacy,
            privacyAction: privacyAction, hidden: hidden,
            chapterDate: chapterDate, textRevisionID: textRevisionID)
    }

    private func nextDeviceSequence() throws -> Int64 {
        let raw = try settingValue(Self.deviceSequenceKey)
        let current: Int64
        if let raw {
            guard let value = Int64(raw), value >= 0 else {
                throw LocalStoreError.inconsistentStore
            }
            current = value
        } else {
            current = 0
        }
        guard current < Int64.max else { throw LocalStoreError.inconsistentStore }
        let next = current + 1
        try setSettingValue(String(next), key: Self.deviceSequenceKey)
        return next
    }

    private func encodedSetting<T: Decodable>(_ key: String) throws -> T? {
        guard let value = try settingValue(key), let data = value.data(using: .utf8) else {
            return nil
        }
        do { return try JSONDecoder().decode(T.self, from: data) }
        catch { throw LocalStoreError.inconsistentStore }
    }

    private func setEncodedSetting<T: Encodable>(_ value: T, key: String) throws {
        let data: Data
        do { data = try JSONEncoder().encode(value) }
        catch { throw LocalStoreError.inconsistentStore }
        guard let string = String(data: data, encoding: .utf8) else {
            throw LocalStoreError.inconsistentStore
        }
        try setSettingValue(string, key: key)
    }

    private func settingValue(_ key: String) throws -> String? {
        let rows = try fetch("SettingRecord", predicate: NSPredicate(format: "key == %@", key))
        guard rows.count <= 1 else { throw LocalStoreError.inconsistentStore }
        guard let row = rows.first else { return nil }
        return try required(row, "value")
    }

    private func setSettingValue(_ value: String, key: String) throws {
        let rows = try fetch("SettingRecord", predicate: NSPredicate(format: "key == %@", key))
        guard rows.count <= 1 else { throw LocalStoreError.inconsistentStore }
        let row = rows.first ?? NSEntityDescription.insertNewObject(
            forEntityName: "SettingRecord", into: context)
        row.setValue(key, forKey: "key")
        row.setValue(value, forKey: "value")
    }

    private func journalKey(_ momentID: UUID) -> String {
        Self.journalPrefix + momentID.uuidString.lowercased()
    }

    private func pendingLinkKey(_ sessionID: UUID) -> String {
        Self.pendingLinkPrefix + sessionID.uuidString.lowercased()
    }

    private func validChapterDate(_ value: String) -> Bool {
        guard value.count == 10 else { return false }
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd"
        guard let parsed = formatter.date(from: value) else { return false }
        return formatter.string(from: parsed) == value
    }

    private func milliseconds(_ date: Date) -> Int64 {
        Int64((date.timeIntervalSince1970 * 1_000).rounded())
    }

    private static let journalPrefix = "c04d.moment."
    private static let pendingLinkPrefix = "c04d.pending-link."
    private static let deviceSequenceKey = "c04d.device-sequence"

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
        let journal = try momentJournal(row)
        return LocalMoment(id: try required(row, "id"), tripID: try required(row, "tripID"),
                           dayID: try required(row, "dayID"), kind: kind,
                           capture: try decodeStamp(row), chapterDate: journal.currentChapterDate,
                           privacy: privacy,
                           revision: try required(row, "revision"),
                           hidden: try required(row, "hidden"),
                           important: try required(row, "important"),
                           audioSessionID: row.value(forKey: "audioSessionID") as? UUID,
                           partialAudio: try required(row, "partialAudio"),
                           relatedMomentID: journal.relatedMomentID)
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
