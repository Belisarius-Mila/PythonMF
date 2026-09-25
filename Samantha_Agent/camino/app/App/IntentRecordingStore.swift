import Foundation
#if canImport(CaminoAudioCore)
import CaminoAudioCore
#endif
#if canImport(CaminoLocalCore)
import CaminoLocalCore
#endif

/// Read-only export of already finalized recorder receipts; never changes capture.
enum CaminoAudioSyncLayout {
    static func assetID(clipID: UUID, fileName: String) -> UUID {
        CaminoStableID.uuid(namespace: "camino-c05b-audio-asset",
                            value: "\(clipID.uuidString.lowercased())|\(fileName)")
    }

    static func make(clip: RecordingClip, urls: [URL], momentID: UUID) throws -> CaminoSyncAudioLayout {
        let segments = clip.segments?.sorted { $0.index < $1.index }
        guard !urls.isEmpty, urls.count == (segments?.count ?? 1) else {
            throw CaminoSyncError.incompleteLocalInventory
        }
        var previous = -1
        let parts = try urls.enumerated().map { offset, url in
            let segment = segments?[offset]
            if let segment, segment.fileName != url.lastPathComponent {
                throw CaminoSyncError.incompleteLocalInventory
            }
            let index = segment?.index ?? 0
            let discontinuity = segment?.discontinuityBefore == true || index != previous + 1
            previous = index
            return CaminoSyncAudioLayout.Part(assetID: assetID(clipID: clip.id, fileName: url.lastPathComponent),
                                               index: index, discontinuityBefore: discontinuity)
        }
        let gap = clip.draft.continuation?.gapSeconds
        let milliseconds: Int64? = gap.flatMap { seconds in
            guard seconds.isFinite, seconds >= 0, seconds * 1_000 < 9_007_199_254_740_991 else { return nil }
            return Int64((seconds * 1_000).rounded())
        }
        return CaminoSyncAudioLayout(
            clipID: clip.id, momentID: momentID, sessionID: clip.draft.sessionID,
            previousClipID: clip.draft.continuation?.previousPartID,
            gapBeforeMilliseconds: milliseconds, missingTail: clip.recovery?.missingTail == true,
            parts: parts)
    }
}

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
