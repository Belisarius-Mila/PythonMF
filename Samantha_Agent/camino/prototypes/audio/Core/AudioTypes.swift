import Foundation

public enum RecordingKind: String, Codable, CaseIterable, Sendable {
    case comment = "Komentář"
    case reflection = "Úvaha"
}

public enum CapturePhase: Equatable, Sendable {
    case idle, permission, preparing, recording, finishing, playing, failed
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

public struct RecordingDraft: Codable, Equatable, Sendable {
    public let id: UUID
    public let kind: RecordingKind
    public let startedAt: Date
    public init(id: UUID, kind: RecordingKind, startedAt: Date) {
        self.id = id; self.kind = kind; self.startedAt = startedAt
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
    func stop() async -> Bool
    func play(url: URL) throws
    func stopPlayback()
    var isPlaying: Bool { get }
    var playbackTime: Double { get }
    var playbackDuration: Double { get }
}

@MainActor public protocol RecordingStorage: AnyObject {
    func begin(kind: RecordingKind) throws -> RecordingDraft
    func url(for draft: RecordingDraft) -> URL
    func finish(_ draft: RecordingDraft, interrupted: Bool) throws -> RecordingClip
    func library() throws -> RecordingLibrary
}

public enum AudioPrototypeError: Error { case collision, invalidAudio, invalidMetadata, startFailed }
