import Foundation

public enum RecordingKind: String, Codable, CaseIterable, Sendable {
    case comment = "Komentář"
    case reflection = "Úvaha"
}

public enum CapturePhase: Equatable, Sendable {
    case idle, permission, preparing, recording, finishing, interrupted, playing, failed
}

public enum MicrophonePermission: Sendable { case undetermined, denied, granted }

public struct AudioInspection: Codable, Equatable, Sendable {
    public let duration: Double
    public let byteCount: Int64
    public let sampleRate: Double
    public let channels: UInt32
    public init(duration: Double, byteCount: Int64, sampleRate: Double, channels: UInt32) {
        self.duration = duration; self.byteCount = byteCount
        self.sampleRate = sampleRate; self.channels = channels
    }
    public var valid: Bool {
        duration.isFinite && duration > 0 && byteCount > 0 && sampleRate.isFinite
            && sampleRate > 0 && channels > 0
    }
}

/// An explicit user continuation, not an automatic C01c segment or a loss guarantee.
public struct RecordingContinuation: Codable, Equatable, Sendable {
    public let sessionID: UUID
    public let previousPartID: UUID
    /// Observed interruption to the next Start request; nil if the clock is invalid.
    public let gapSeconds: Double?
    public init(sessionID: UUID, previousPartID: UUID, gapSeconds: Double?) {
        self.sessionID = sessionID; self.previousPartID = previousPartID
        self.gapSeconds = gapSeconds
    }
}

public struct RecordingDraft: Codable, Equatable, Sendable {
    public let id: UUID
    public let kind: RecordingKind
    public let startedAt: Date
    public let continuation: RecordingContinuation?
    public var sessionID: UUID { continuation?.sessionID ?? id }
    public init(id: UUID, kind: RecordingKind, startedAt: Date,
                continuation: RecordingContinuation? = nil) {
        self.id = id; self.kind = kind; self.startedAt = startedAt
        self.continuation = continuation
    }
}

public struct RecordingClip: Codable, Equatable, Identifiable, Sendable {
    public let draft: RecordingDraft
    public let audio: AudioInspection
    public let interrupted: Bool
    public var id: UUID { draft.id }
    public init(draft: RecordingDraft, audio: AudioInspection, interrupted: Bool) {
        self.draft = draft; self.audio = audio; self.interrupted = interrupted
    }
}

public struct RecordingLibrary: Sendable {
    public var clips: [RecordingClip] = []
    public var unfinishedCount = 0
    public init() {}
    public var sessions: [RecordingSession] {
        Dictionary(grouping: clips, by: { $0.draft.sessionID }).map { id, clips in
            // Follow recorded predecessor links, even if the wall clock changed during a pause.
            var remaining = clips.sorted { $0.draft.startedAt < $1.draft.startedAt }
            var ordered: [RecordingClip] = []
            while !remaining.isEmpty {
                let index = remaining.firstIndex { $0.id == id }
                    ?? remaining.firstIndex { clip in
                        guard let prior = clip.draft.continuation?.previousPartID else { return true }
                        return !remaining.contains { $0.id == prior }
                    } ?? remaining.startIndex
                ordered.append(remaining.remove(at: index))
            }
            return RecordingSession(id: id, parts: ordered)
        }.sorted { ($0.parts.first?.draft.startedAt ?? .distantPast) > ($1.parts.first?.draft.startedAt ?? .distantPast) }
    }
}

public struct RecordingSession: Identifiable, Sendable {
    public let id: UUID
    public let parts: [RecordingClip]
}

public struct CaptureSample: Sendable {
    public var running: Bool
    public var time: Double
    public var power: Float
    public var inputID: String
    public var inputLabel: String
    public init(running: Bool, time: Double, power: Float, inputID: String, inputLabel: String) {
        self.running = running; self.time = time; self.power = power
        self.inputID = inputID; self.inputLabel = inputLabel
    }
}

@MainActor public protocol AudioDriver: AnyObject {
    var permission: MicrophonePermission { get }
    func requestPermission() async -> Bool
    func start(url: URL) async throws
    func sample() -> CaptureSample
    func pauseCapture()
    func stop() async -> Bool
    func play(url: URL) throws
    func stopPlayback()
    var isPlaying: Bool { get }
    var playbackTime: Double { get }
    var playbackDuration: Double { get }
}

@MainActor public protocol RecordingStorage: AnyObject {
    func begin(kind: RecordingKind, continuation: RecordingContinuation?) throws -> RecordingDraft
    func url(for draft: RecordingDraft) -> URL
    func finish(_ draft: RecordingDraft, interrupted: Bool) throws -> RecordingClip
    func library() throws -> RecordingLibrary
}

public extension RecordingStorage {
    func begin(kind: RecordingKind) throws -> RecordingDraft {
        try begin(kind: kind, continuation: nil)
    }
}

public enum AudioPrototypeError: Error { case collision, missingAudio, invalidAudio, invalidMetadata, startFailed }
