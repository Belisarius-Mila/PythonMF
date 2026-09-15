import Foundation
import AVFAudio
#if canImport(CaminoAudioCore)
import CaminoAudioCore
#endif

public enum AudioFileInspector {
    /// Decode the entire short sample; metadata or nonzero bytes alone are not acceptance.
    public static func inspect(_ url: URL) throws -> AudioInspection {
        guard try url.resourceValues(forKeys: [.isSymbolicLinkKey]).isSymbolicLink != true else {
            throw AudioPrototypeError.invalidAudio
        }
        let file = try AVAudioFile(forReading: url)
        guard file.length > 0, file.processingFormat.sampleRate > 0,
              let buffer = AVAudioPCMBuffer(pcmFormat: file.processingFormat, frameCapacity: 4096) else {
            throw AudioPrototypeError.invalidAudio
        }
        var frames: AVAudioFramePosition = 0
        while file.framePosition < file.length {
            try file.read(into: buffer)
            guard buffer.frameLength > 0 else { throw AudioPrototypeError.invalidAudio }
            frames += AVAudioFramePosition(buffer.frameLength)
        }
        guard frames == file.length else { throw AudioPrototypeError.invalidAudio }
        let bytes = try FileManager.default.attributesOfItem(atPath: url.path)[.size] as? NSNumber
        return AudioInspection(duration: Double(frames) / file.processingFormat.sampleRate,
            byteCount: bytes?.int64Value ?? 0, sampleRate: file.fileFormat.sampleRate,
            channels: file.fileFormat.channelCount)
    }
}
