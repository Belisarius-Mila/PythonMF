import Foundation
#if canImport(Darwin)
import Darwin
#else
import Glibc
#endif

/// One private directory per attempt. Draft and completion receipts are immutable.
/// Unfinished/corrupt attempts are retained; this is not the C01c segment journal.
@MainActor public final class RecordingStore: RecordingStorage {
    private let root: URL
    private let inspect: (URL) throws -> AudioInspection
    private let makeID: () -> UUID

    public init(root: URL, makeID: @escaping () -> UUID = UUID.init,
                inspect: @escaping (URL) throws -> AudioInspection) throws {
        self.root = root; self.makeID = makeID; self.inspect = inspect
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
    }

    public func begin(kind: RecordingKind) throws -> RecordingDraft {
        let draft = RecordingDraft(id: makeID(), kind: kind, startedAt: Date())
        let directory = folder(draft.id)
        guard mkdir(directory.path, 0o700) == 0 else {
            if errno == EEXIST { throw AudioPrototypeError.collision }
            throw NSError(domain: NSPOSIXErrorDomain, code: Int(errno))
        }
        try JSONEncoder().encode(draft).write(to: directory.appendingPathComponent("started.json"),
                                            options: .withoutOverwriting)
        return draft
    }

    public func url(for draft: RecordingDraft) -> URL {
        folder(draft.id).appendingPathComponent("audio.caf")
    }

    public func finish(_ draft: RecordingDraft, interrupted: Bool) throws -> RecordingClip {
        let saved = try JSONDecoder().decode(RecordingDraft.self,
            from: Data(contentsOf: folder(draft.id).appendingPathComponent("started.json")))
        guard saved == draft else { throw AudioPrototypeError.invalidMetadata }
        let result = try inspect(url(for: draft))
        guard result.valid else { throw AudioPrototypeError.invalidAudio }
        let clip = RecordingClip(draft: draft, audio: result, interrupted: interrupted)
        // Create-only: a later Stop or restart cannot overwrite a completed receipt.
        try JSONEncoder().encode(clip).write(to: folder(draft.id).appendingPathComponent("completed.json"),
                                           options: .withoutOverwriting)
        return clip
    }

    public func library() throws -> RecordingLibrary {
        var result = RecordingLibrary()
        for directory in try FileManager.default.contentsOfDirectory(at: root,
            includingPropertiesForKeys: [.isSymbolicLinkKey]) {
            do {
                guard try directory.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true,
                      let id = UUID(uuidString: directory.lastPathComponent) else {
                    result.unfinishedCount += 1; continue
                }
                let clip = try JSONDecoder().decode(RecordingClip.self,
                    from: Data(contentsOf: directory.appendingPathComponent("completed.json")))
                let draft = try JSONDecoder().decode(RecordingDraft.self,
                    from: Data(contentsOf: directory.appendingPathComponent("started.json")))
                guard clip.id == id, clip.draft == draft, clip.audio.valid,
                      try inspect(url(for: draft)) == clip.audio else {
                    throw AudioPrototypeError.invalidAudio
                }
                result.clips.append(clip)
            } catch { result.unfinishedCount += 1 }
        }
        result.clips.sort { $0.draft.startedAt > $1.draft.startedAt }
        return result
    }

    private func folder(_ id: UUID) -> URL { root.appendingPathComponent(id.uuidString, isDirectory: true) }
}
