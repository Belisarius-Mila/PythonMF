import XCTest
import AVFAudio
import CaminoAudioCore
import CaminoAudioInspection

@MainActor final class AudioInspectionTests: XCTestCase {
    private func tone(at url: URL, silent: Bool = false) throws {
        let format = AVAudioFormat(standardFormatWithSampleRate: 48000, channels: 1)!
        let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 24000)!
        buffer.frameLength = 24000
        for index in 0..<24000 {
            buffer.floatChannelData![0][index] = silent ? 0 : Float(sin(Double(index) * 2 * .pi * 440 / 48000) * 0.2)
        }
        let settings: [String: Any] = [AVFormatIDKey: kAudioFormatLinearPCM,
            AVSampleRateKey: 48000, AVNumberOfChannelsKey: 1, AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false, AVLinearPCMIsBigEndianKey: false]
        let file = try AVAudioFile(forWriting: url, settings: settings)
        try file.write(from: buffer)
    }
    private func root() -> URL {
        FileManager.default.temporaryDirectory.appendingPathComponent("camino-audio-fixture-\(UUID())")
    }

    func testPCMCAFDecodesAndSurvivesStoreRestart() throws {
        let directory = root()
        let s = try RecordingStore(root: directory, inspect: AudioFileInspector.inspect)
        let d = try s.begin(kind: .reflection); try tone(at: s.url(for: d))
        let result = try s.finish(d, interrupted: false)
        XCTAssertEqual(result.audio.duration, 0.5, accuracy: 0.0001)
        XCTAssertEqual(result.audio.sampleRate, 48000); XCTAssertEqual(result.audio.channels, 1)
        XCTAssertGreaterThan(result.audio.byteCount, 48000)
        let reopened = try RecordingStore(root: directory, inspect: AudioFileInspector.inspect)
        XCTAssertEqual(try reopened.library().clips, [result])
    }

    func testSilentAudioIsStillValidAudio() throws {
        let s = try RecordingStore(root: root(), inspect: AudioFileInspector.inspect)
        let d = try s.begin(kind: .comment); try tone(at: s.url(for: d), silent: true)
        XCTAssertEqual(try s.finish(d, interrupted: false).audio.duration, 0.5, accuracy: 0.0001)
    }

    func testCorruptMediaRejectedAndRetained() throws {
        let s = try RecordingStore(root: root(), inspect: AudioFileInspector.inspect)
        let d = try s.begin(kind: .comment)
        try Data("synthetic invalid CAF".utf8).write(to: s.url(for: d))
        XCTAssertThrowsError(try s.finish(d, interrupted: false))
        XCTAssertEqual(try s.library().unfinishedCount, 1)
        XCTAssertTrue(FileManager.default.fileExists(atPath: s.url(for: d).path))
    }
}
