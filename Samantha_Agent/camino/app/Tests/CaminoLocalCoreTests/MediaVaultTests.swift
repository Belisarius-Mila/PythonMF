import AVFoundation
import CoreGraphics
import CoreVideo
import Foundation
import ImageIO
import XCTest
@testable import CaminoLocalCore

@MainActor final class MediaVaultTests: XCTestCase {
    func testTwoPhotosStaySeparateAndExplicitAttachmentInheritsPrivacy() async throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04b-photos-\(UUID())", isDirectory: true)
        let store = try CaminoLocalStore(storeURL: root.appendingPathComponent("metadata.sqlite"))
        let trip = try store.createTrip(name: "Synthetic")
        let vault = try CaminoMediaVault(root: root, metadata: store)
        let pixels = try jpeg()
        let first = try await vault.savePhoto(pixels)
        let second = try await vault.savePhoto(pixels)
        XCTAssertNotEqual(first.id, second.id)
        XCTAssertNotEqual(first.momentID, second.momentID)
        XCTAssertEqual(first.inspection.width, 4)
        XCTAssertEqual(first.inspection.height, 3)
        XCTAssertEqual(first.inspection.sha256, second.inspection.sha256)
        XCTAssertTrue(FileManager.default.fileExists(atPath: try vault.originalURL(for: first).path))
        try store.setNewMomentPrivacy(.ownerOnly)
        let attached = try await vault.savePhoto(pixels, targetMomentID: first.momentID)
        XCTAssertEqual(attached.momentID, first.momentID)
        XCTAssertEqual(try store.mediaAssets(momentID: first.momentID).count, 2)
        XCTAssertEqual(try store.mediaAssets(momentID: second.momentID).count, 1)
        XCTAssertEqual(try store.moments(tripID: trip.id).count, 2)
        XCTAssertEqual(try store.moments(tripID: trip.id)
            .first(where: { $0.id == first.momentID })?.privacy, .diary)
        _ = try store.createTrip(name: "Other")
        XCTAssertThrowsError(try store.beginMediaIntent(kind: .photo,
                                                        targetMomentID: first.momentID))
    }

    func testPendingPhotoIsRecoveredWithoutDuplicateAndUnknownFileIsPreserved() async throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04b-recovery-\(UUID())", isDirectory: true)
        let store = try CaminoLocalStore(storeURL: root.appendingPathComponent("metadata.sqlite"))
        let trip = try store.createTrip(name: "Synthetic")
        let vault = try CaminoMediaVault(root: root, metadata: store)
        let intent = try store.beginMediaIntent(kind: .photo)
        try jpeg().write(to: root.appendingPathComponent(intent.pendingRelativePath))
        let unknown = root.appendingPathComponent("Media/Originals/unknown.jpg")
        try jpeg().write(to: unknown)
        let recovered = try await vault.reconcile()
        XCTAssertEqual(recovered.repairedCount, 1)
        XCTAssertEqual(recovered.pendingCount, 0)
        XCTAssertEqual(recovered.orphanCount, 1)
        XCTAssertEqual(try store.moments(tripID: trip.id).count, 1)
        XCTAssertEqual(try store.mediaAssets(momentID: intent.momentID).count, 1)
        let repeated = try await vault.reconcile()
        XCTAssertEqual(repeated.repairedCount, 0)
        XCTAssertEqual(repeated.orphanCount, 1)
        XCTAssertTrue(FileManager.default.fileExists(atPath: unknown.path))
    }

    func testInvalidPhotoStaysPendingAndDoesNotClaimSavedMoment() async throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04b-invalid-\(UUID())", isDirectory: true)
        let store = try CaminoLocalStore(storeURL: root.appendingPathComponent("metadata.sqlite"))
        let trip = try store.createTrip(name: "Synthetic")
        let vault = try CaminoMediaVault(root: root, metadata: store)
        let intent = try store.beginMediaIntent(kind: .photo)
        let pending = root.appendingPathComponent(intent.pendingRelativePath)
        try Data([1, 2, 3, 4]).write(to: pending)
        let result = try await vault.reconcile()
        XCTAssertEqual(result.pendingCount, 1)
        XCTAssertEqual(result.repairedCount, 0)
        XCTAssertTrue(try store.moments(tripID: trip.id).isEmpty)
        XCTAssertTrue(FileManager.default.fileExists(atPath: pending.path))
    }

    func testSilentVideoIsVerifiedAndMissingRequestedAudioIsMarkedPartial() async throws {
        let root = FileManager.default.temporaryDirectory
            .appendingPathComponent("camino-c04b-video-\(UUID())", isDirectory: true)
        let store = try CaminoLocalStore(storeURL: root.appendingPathComponent("metadata.sqlite"))
        let trip = try store.createTrip(name: "Synthetic")
        let vault = try CaminoMediaVault(root: root, metadata: store)
        let silent = try vault.beginVideo(silent: true)
        try await writeSyntheticMovie(silent.1)
        let saved = try await vault.finalize(silent.0, interrupted: false)
        XCTAssertFalse(saved.inspection.hasAudio)
        XCTAssertFalse(saved.inspection.partial)
        XCTAssertTrue(saved.silentRequested)
        XCTAssertGreaterThan(saved.inspection.durationMilliseconds ?? 0, 0)
        XCTAssertEqual(try store.moments(tripID: trip.id).count, 1)

        let expectedSound = try vault.beginVideo(silent: false)
        try await writeSyntheticMovie(expectedSound.1)
        let partial = try await vault.finalize(expectedSound.0, interrupted: false)
        XCTAssertTrue(partial.inspection.partial)
        XCTAssertFalse(partial.inspection.hasAudio)
        XCTAssertFalse(partial.silentRequested)
        XCTAssertNotEqual(saved.momentID, partial.momentID)
    }

    private func jpeg() throws -> Data {
        let context = try XCTUnwrap(CGContext(data: nil, width: 4, height: 3,
            bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue))
        context.setFillColor(CGColor(red: 0.1, green: 0.3, blue: 0.7, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: 4, height: 3))
        let image = try XCTUnwrap(context.makeImage())
        let result = NSMutableData()
        let destination = try XCTUnwrap(CGImageDestinationCreateWithData(
            result as CFMutableData, "public.jpeg" as CFString, 1, nil))
        CGImageDestinationAddImage(destination, image, nil)
        XCTAssertTrue(CGImageDestinationFinalize(destination))
        return result as Data
    }

    private func writeSyntheticMovie(_ url: URL) async throws {
        let writer = try AVAssetWriter(outputURL: url, fileType: .mov)
        let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
            AVVideoCodecKey: AVVideoCodecType.h264,
            AVVideoWidthKey: 32,
            AVVideoHeightKey: 24,
        ])
        input.expectsMediaDataInRealTime = false
        let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input,
            sourcePixelBufferAttributes: [
                kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
                kCVPixelBufferWidthKey as String: 32,
                kCVPixelBufferHeightKey as String: 24,
            ])
        writer.add(input)
        XCTAssertTrue(writer.startWriting())
        writer.startSession(atSourceTime: .zero)
        var buffer: CVPixelBuffer?
        XCTAssertEqual(CVPixelBufferCreate(kCFAllocatorDefault, 32, 24,
            kCVPixelFormatType_32ARGB, nil, &buffer), kCVReturnSuccess)
        let frame = try XCTUnwrap(buffer)
        CVPixelBufferLockBaseAddress(frame, [])
        if let base = CVPixelBufferGetBaseAddress(frame) {
            memset(base, 127, CVPixelBufferGetDataSize(frame))
        }
        CVPixelBufferUnlockBaseAddress(frame, [])
        for index in 0..<4 {
            while !input.isReadyForMoreMediaData { await Task.yield() }
            XCTAssertTrue(adaptor.append(frame,
                withPresentationTime: CMTime(value: CMTimeValue(index), timescale: 10)))
        }
        input.markAsFinished()
        await withCheckedContinuation { continuation in
            writer.finishWriting { continuation.resume() }
        }
        XCTAssertEqual(writer.status, .completed)
    }
}
