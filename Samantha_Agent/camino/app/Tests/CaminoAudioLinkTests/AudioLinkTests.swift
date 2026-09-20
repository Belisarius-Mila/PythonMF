import Foundation
import XCTest
import CaminoAudioCore
import CaminoLocalCore

@MainActor final class AudioLinkTests: XCTestCase {
    func testValidatedAudioIsLinkedAfterRestartWithoutChangingItsPrivateIntent() throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04a-audio-link-\(UUID())", isDirectory: true)
        let url = root.appendingPathComponent("metadata.sqlite")
        let local = try CaminoLocalStore(storeURL: url)
        let trip = try local.createTrip(name: "Synthetic")
        try local.setNewMomentPrivacy(.diary)
        let media = try RecordingStore(root: root.appendingPathComponent("Audio"),
                                       inspect: inspect)
        let linked = IntentRecordingStore(media: media, metadata: local)
        let draft = try linked.begin(kind: .reflection, continuation: nil)
        let pending = try XCTUnwrap(local.pendingAudioIntents().first)
        XCTAssertEqual(pending.sessionID, draft.sessionID)
        XCTAssertEqual(pending.privacy, .ownerOnly)
        XCTAssertTrue(try local.moments(tripID: trip.id).isEmpty)

        try Data([1, 2, 3, 4]).write(to: linked.url(for: draft))
        _ = try linked.finish(draft, interrupted: false)

        let reopened = try CaminoLocalStore(storeURL: url)
        let recoveredMedia = try RecordingStore(root: root.appendingPathComponent("Audio"),
                                                inspect: inspect)
        let session = try XCTUnwrap(recoveredMedia.library().sessions.first)
        XCTAssertEqual(session.id, draft.sessionID)
        let moment = try reopened.acceptCompletedAudio(sessionID: session.id,
                                                        kind: .reflection, partial: false)
        XCTAssertEqual(moment.id, pending.momentID)
        XCTAssertEqual(moment.privacy, .ownerOnly)
        XCTAssertEqual(moment.audioSessionID, draft.sessionID)
        XCTAssertEqual(try reopened.acceptCompletedAudio(sessionID: session.id,
                                                         kind: .reflection, partial: false), moment)
        XCTAssertEqual(try reopened.moments(tripID: trip.id).count, 1)
        XCTAssertTrue(try reopened.pendingAudioIntents().isEmpty)
    }

    private func inspect(_ url: URL) throws -> AudioInspection {
        guard try Data(contentsOf: url) == Data([1, 2, 3, 4]) else {
            throw AudioPrototypeError.invalidAudio
        }
        return AudioInspection(duration: 1, byteCount: 4, sampleRate: 48_000, channels: 1)
    }
}
