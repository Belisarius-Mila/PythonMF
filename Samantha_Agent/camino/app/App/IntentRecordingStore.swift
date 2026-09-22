import Foundation
#if canImport(CaminoAudioCore)
import CaminoAudioCore
#endif
#if canImport(CaminoLocalCore)
import CaminoLocalCore
#endif

/// Keeps the accepted C01c recorder unchanged. The metadata intent is saved
/// after its create-only draft journal and before the microphone starts.
@MainActor final class IntentRecordingStore: RecordingStorage {
    let media: RecordingStore
    private let metadata: CaminoLocalStore
    private(set) var currentSessionID: UUID?
    var targetMomentID: UUID?
    var relatedMomentID: UUID?

    init(media: RecordingStore, metadata: CaminoLocalStore) {
        self.media = media
        self.metadata = metadata
    }

    func begin(kind: RecordingKind,
               continuation: RecordingContinuation?) throws -> RecordingDraft {
        let draft = try media.begin(kind: kind, continuation: continuation)
        _ = try metadata.beginAudioIntent(
            sessionID: draft.sessionID,
            kind: kind == .reflection ? .reflection : .comment,
            startedAt: draft.startedAt,
            targetMomentID: kind == .comment ? targetMomentID : nil,
            relatedMomentID: kind == .reflection ? relatedMomentID : nil)
        currentSessionID = draft.sessionID
        return draft
    }

    func setCurrentPrivacy(_ privacy: LocalPrivacy) throws {
        guard let currentSessionID else { throw LocalStoreError.invalidAudioIntent }
        try metadata.setAudioIntentPrivacy(sessionID: currentSessionID, privacy: privacy)
    }

    func url(for draft: RecordingDraft) -> URL { media.url(for: draft) }
    func finish(_ draft: RecordingDraft, interrupted: Bool) throws -> RecordingClip {
        try media.finish(draft, interrupted: interrupted)
    }
    func library() throws -> RecordingLibrary { try media.library() }
    func playbackURLs(for clip: RecordingClip) throws -> [URL] {
        try media.playbackURLs(for: clip)
    }
}
