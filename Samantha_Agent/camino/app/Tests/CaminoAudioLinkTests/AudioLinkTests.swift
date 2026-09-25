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

    func testAudioLayoutUsesRecordedSegmentOrderAndKeepsStableAssetIDs() throws {
        let clipID = UUID(), momentID = UUID()
        let audio = AudioInspection(duration: 1, byteCount: 4, sampleRate: 48_000, channels: 1)
        let segments = [RecordingSegment(index: 2, fileName: "segment-2.caf", audio: audio),
                        RecordingSegment(index: 0, fileName: "segment-0.caf", audio: audio)]
        let clip = RecordingClip(draft: RecordingDraft(id: clipID, kind: .comment, startedAt: Date()),
                                 audio: audio, interrupted: true, segments: segments,
                                 recovery: RecordingRecovery(recoveredAfterCrash: true, missingTail: true))
        let urls = [URL(fileURLWithPath: "/synthetic/segment-0.caf"), URL(fileURLWithPath: "/synthetic/segment-2.caf")]
        let layout = try CaminoAudioSyncLayout.make(clip: clip, urls: urls, momentID: momentID)
        XCTAssertEqual(layout.parts.map(\.index), [0, 2])
        XCTAssertFalse(layout.parts[0].discontinuityBefore)
        XCTAssertTrue(layout.parts[1].discontinuityBefore)
        XCTAssertTrue(layout.missingTail)
        XCTAssertEqual(layout.parts[0].assetID, CaminoStableID.uuid(
            namespace: "camino-c05b-audio-asset", value: "\(clipID.uuidString.lowercased())|segment-0.caf"))
        XCTAssertNoThrow(try layout.payload())
        XCTAssertThrowsError(try CaminoAudioSyncLayout.make(clip: clip, urls: urls.reversed(), momentID: momentID))
    }

    func testLegacyContinuationCarriesPredecessorAndObservedOrUnknownGap() throws {
        let sessionID = UUID(), previousID = UUID(), clipID = UUID()
        let audio = AudioInspection(duration: 1, byteCount: 4, sampleRate: 48_000, channels: 1)
        for gap in [Optional(12.345), nil, Optional(Double.nan), Optional(-1.0)] {
            let draft = RecordingDraft(id: clipID, kind: .comment, startedAt: Date(timeIntervalSince1970: 1),
                continuation: RecordingContinuation(sessionID: sessionID, previousPartID: previousID, gapSeconds: gap))
            let clip = RecordingClip(draft: draft, audio: audio, interrupted: false)
            let layout = try CaminoAudioSyncLayout.make(clip: clip, urls: [URL(fileURLWithPath: "/synthetic/audio.caf")], momentID: UUID())
            XCTAssertEqual(layout.sessionID, sessionID)
            XCTAssertEqual(layout.previousClipID, previousID)
            XCTAssertEqual(layout.gapBeforeMilliseconds, gap == 12.345 ? 12_345 : nil)
            XCTAssertEqual(layout.parts.map(\.index), [0])
            XCTAssertNoThrow(try layout.payload())
        }
    }
}
