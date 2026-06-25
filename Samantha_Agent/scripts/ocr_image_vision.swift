import AppKit
import Foundation
import Vision

struct OCRResult: Codable {
    let image: String
    let text: String
    let lines: [String]
}

struct OCRError: Codable {
    let error: String
    let image: String
}

func fail(_ message: String, image: String = "") -> Never {
    let payload = OCRError(error: message, image: image)
    if let data = try? JSONEncoder().encode(payload),
       let json = String(data: data, encoding: .utf8) {
        print(json)
    } else {
        print("{\"error\":\"\(message)\"}")
    }
    exit(1)
}

let args = CommandLine.arguments
if args.count < 2 {
    fail("usage: swift ocr_image_vision.swift <image-path>")
}

let imagePath = args[1]
let url = URL(fileURLWithPath: imagePath)
guard NSImage(contentsOf: url) != nil else {
    fail("cannot load image", image: imagePath)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = ["cs-CZ", "sk-SK", "en-US", "de-DE"]

let handler = VNImageRequestHandler(url: url, options: [:])
do {
    try handler.perform([request])
} catch {
    fail("vision request failed: \(error.localizedDescription)", image: imagePath)
}

let observations = (request.results ?? []).sorted {
    if abs($0.boundingBox.minY - $1.boundingBox.minY) > 0.02 {
        return $0.boundingBox.minY > $1.boundingBox.minY
    }
    return $0.boundingBox.minX < $1.boundingBox.minX
}
let lines = observations.compactMap { $0.topCandidates(1).first?.string.trimmingCharacters(in: .whitespacesAndNewlines) }
    .filter { !$0.isEmpty }
let result = OCRResult(image: imagePath, text: lines.joined(separator: "\n"), lines: lines)

guard let data = try? JSONEncoder().encode(result),
      let json = String(data: data, encoding: .utf8) else {
    fail("cannot encode OCR result", image: imagePath)
}
print(json)
