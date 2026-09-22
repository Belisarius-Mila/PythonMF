import Foundation

public enum LocalPrivacy: String, Codable, Sendable, CaseIterable {
    case ownerOnly = "owner_only"
    case diary

    public var title: String {
        switch self {
        case .ownerOnly: "Jen pro mě"
        case .diary: "Do deníku"
        }
    }
}

public enum LocalMomentKind: String, Codable, Sendable {
    case marker, comment, reflection, photo, video

    public var title: String {
        switch self {
        case .marker: "Označený okamžik"
        case .comment: "Komentář"
        case .reflection: "Úvaha"
        case .photo: "Fotografie"
        case .video: "Video"
        }
    }
}

public enum LocalMediaKind: String, Codable, Sendable {
    case photo, video

    public var fileExtension: String { self == .photo ? "jpg" : "mov" }
    public var momentKind: LocalMomentKind { self == .photo ? .photo : .video }
    public var title: String { self == .photo ? "Fotografie" : "Video" }
}

public struct LocalTrip: Equatable, Identifiable, Sendable {
    public let id: UUID
    public let name: String
    public let language: String
    public let active: Bool
    public let isTest: Bool
    public let viewerEnabled: Bool
    public let startDate: String?
}

public struct CaptureStamp: Equatable, Sendable {
    public let utcMilliseconds: Int64
    public let localWall: String
    public let chapterDate: String
    public let offsetMinutes: Int
    public let timeZoneID: String

    public static func record(_ date: Date, timeZone: TimeZone) -> CaptureStamp {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.timeZone = timeZone
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        let wall = formatter.string(from: date)
        return CaptureStamp(
            utcMilliseconds: Int64((date.timeIntervalSince1970 * 1_000).rounded()),
            localWall: wall,
            chapterDate: String(wall.prefix(10)),
            offsetMinutes: timeZone.secondsFromGMT(for: date) / 60,
            timeZoneID: timeZone.identifier
        )
    }
}

public struct LocalMoment: Equatable, Identifiable, Sendable {
    public let id: UUID
    public let tripID: UUID
    public let dayID: UUID
    public let kind: LocalMomentKind
    public let capture: CaptureStamp
    /// Current diary chapter. The immutable capture stamp keeps the original date.
    public let chapterDate: String
    public let privacy: LocalPrivacy
    public let revision: Int
    public let hidden: Bool
    public let important: Bool
    public let audioSessionID: UUID?
    public let partialAudio: Bool
    /// A private addendum is a separate Moment linked to, not merged into, this parent.
    public let relatedMomentID: UUID?
}

public enum LocalTextRole: String, Codable, Sendable, CaseIterable {
    case typedSource = "typed_source"
    case transcriptRaw = "transcript_raw"
    case transcriptClean = "transcript_clean"
    case humanRevision = "human_revision"

    public var title: String {
        switch self {
        case .typedSource: "Psaný zdroj"
        case .transcriptRaw: "Původní přepis"
        case .transcriptClean: "Upravený přepis"
        case .humanRevision: "Ruční revize"
        }
    }
}

public struct LocalTextRevision: Codable, Equatable, Identifiable, Sendable {
    public let id: UUID
    public let momentID: UUID
    public let role: LocalTextRole
    public let content: String
    public let sourceIDs: [UUID]
    public let parentRevisionID: UUID?
    public let createdAtUTCMilliseconds: Int64

    public init(id: UUID, momentID: UUID, role: LocalTextRole, content: String,
                sourceIDs: [UUID], parentRevisionID: UUID?,
                createdAtUTCMilliseconds: Int64) {
        self.id = id
        self.momentID = momentID
        self.role = role
        self.content = content
        self.sourceIDs = sourceIDs
        self.parentRevisionID = parentRevisionID
        self.createdAtUTCMilliseconds = createdAtUTCMilliseconds
    }
}

public struct LocalTextDraft: Codable, Equatable, Sendable {
    public let momentID: UUID
    public let baseRevisionID: UUID?
    public let content: String
    public let updatedAtUTCMilliseconds: Int64

    public init(momentID: UUID, baseRevisionID: UUID?, content: String,
                updatedAtUTCMilliseconds: Int64) {
        self.momentID = momentID
        self.baseRevisionID = baseRevisionID
        self.content = content
        self.updatedAtUTCMilliseconds = updatedAtUTCMilliseconds
    }
}

public struct LocalTextHistory: Codable, Equatable, Sendable {
    public let revisions: [LocalTextRevision]
    public let draft: LocalTextDraft?

    public init(revisions: [LocalTextRevision] = [], draft: LocalTextDraft? = nil) {
        self.revisions = revisions
        self.draft = draft
    }

    /// A late automated result never replaces a human revision.
    public var readerRevision: LocalTextRevision? {
        for role in [LocalTextRole.humanRevision, .transcriptClean,
                     .typedSource, .transcriptRaw] {
            if let value = revisions.last(where: { $0.role == role }) { return value }
        }
        return nil
    }
}

public enum LocalPrivacyAction: String, Codable, Sendable {
    case lock
    case unlock
    case insertReflectionIntoDiary = "insert_reflection_into_diary"
}

public enum LocalOperationKind: String, Codable, Sendable {
    case privacy, hidden, chapter, appendText = "append_text"
}

/// Durable, ordered local operation prepared for the later C05 server handoff.
public struct LocalPendingOperation: Codable, Equatable, Identifiable, Sendable {
    public let id: UUID
    public let momentID: UUID
    public let deviceSequence: Int64
    public let expectedRevision: Int
    public let kind: LocalOperationKind
    public let createdAtUTCMilliseconds: Int64
    public let privacy: LocalPrivacy?
    public let privacyAction: LocalPrivacyAction?
    public let hidden: Bool?
    public let chapterDate: String?
    public let textRevisionID: UUID?

    public init(id: UUID, momentID: UUID, deviceSequence: Int64,
                expectedRevision: Int, kind: LocalOperationKind,
                createdAtUTCMilliseconds: Int64, privacy: LocalPrivacy? = nil,
                privacyAction: LocalPrivacyAction? = nil, hidden: Bool? = nil,
                chapterDate: String? = nil, textRevisionID: UUID? = nil) {
        self.id = id
        self.momentID = momentID
        self.deviceSequence = deviceSequence
        self.expectedRevision = expectedRevision
        self.kind = kind
        self.createdAtUTCMilliseconds = createdAtUTCMilliseconds
        self.privacy = privacy
        self.privacyAction = privacyAction
        self.hidden = hidden
        self.chapterDate = chapterDate
        self.textRevisionID = textRevisionID
    }
}

public struct AudioIntent: Equatable, Sendable {
    public let sessionID: UUID
    public let momentID: UUID
    public let tripID: UUID
    public let kind: LocalMomentKind
    public let privacy: LocalPrivacy
    public let capture: CaptureStamp
    public let attaching: Bool
}

public struct LocalMediaIntent: Equatable, Sendable {
    public let assetID: UUID
    public let momentID: UUID
    public let tripID: UUID
    public let kind: LocalMediaKind
    public let privacy: LocalPrivacy
    public let capture: CaptureStamp
    public let attaching: Bool
    public let silentRequested: Bool

    public var pendingRelativePath: String {
        "Media/Pending/\(assetID.uuidString).\(kind.fileExtension)"
    }
    public var originalRelativePath: String {
        "Media/Originals/\(assetID.uuidString).\(kind.fileExtension)"
    }
}

public struct LocalMediaInspection: Equatable, Sendable {
    public let byteCount: Int64
    public let sha256: String
    public let width: Int
    public let height: Int
    /// EXIF orientation for JPEG; display rotation in degrees for a movie.
    public let orientation: Int
    public let durationMilliseconds: Int64?
    public let hasAudio: Bool
    public let partial: Bool

    public init(byteCount: Int64, sha256: String, width: Int, height: Int,
                orientation: Int, durationMilliseconds: Int64?,
                hasAudio: Bool, partial: Bool) {
        self.byteCount = byteCount; self.sha256 = sha256
        self.width = width; self.height = height; self.orientation = orientation
        self.durationMilliseconds = durationMilliseconds
        self.hasAudio = hasAudio; self.partial = partial
    }
}

public struct LocalMediaAsset: Equatable, Identifiable, Sendable {
    public let id: UUID
    public let momentID: UUID
    public let tripID: UUID
    public let kind: LocalMediaKind
    public let relativePath: String
    public let inspection: LocalMediaInspection
    public let silentRequested: Bool
}

public enum LocalStoreError: Error, LocalizedError, Equatable {
    case invalidName
    case noActiveTrip
    case tripMissing
    case momentMissing
    case invalidAudioIntent
    case invalidMediaIntent
    case invalidMedia
    case invalidText
    case invalidMetadataChange
    case revisionConflict
    case operationConflict
    case insufficientSpace
    case duplicateIdentity
    case inconsistentStore

    public var errorDescription: String? {
        switch self {
        case .invalidName: "Zadej název cesty."
        case .noActiveTrip: "Nejdřív vyber cestu."
        case .tripMissing: "Cesta není dostupná. Nic se nesmazalo."
        case .momentMissing: "Moment není dostupný. Nic se nesmazalo."
        case .invalidAudioIntent: "Vazbu nahrávky nelze ověřit. Audio zůstalo zachované."
        case .invalidMediaIntent: "Vazbu média nelze ověřit. Soubor zůstal zachovaný."
        case .invalidMedia: "Médium se nepodařilo ověřit. Dostupný soubor zůstal zachovaný."
        case .invalidText: "Textovou revizi nelze bezpečně uložit. Předchozí verze zůstala zachovaná."
        case .invalidMetadataChange: "Tuto změnu Momentu nelze bezpečně provést. Původní stav zůstal zachovaný."
        case .revisionConflict: "Moment se mezitím změnil. Obnov detail a změnu zopakuj."
        case .operationConflict: "Stejné ID operace už označuje jinou změnu. Nic se nepřepsalo."
        case .insufficientSpace: "Pro tento záznam není dost bezpečného volného místa. Nic se nemaže."
        case .duplicateIdentity: "Stejné ID už patří jinému záznamu. Nic se nepřepsalo."
        case .inconsistentStore: "Místní evidence není konzistentní. Nic se nemaže."
        }
    }
}
