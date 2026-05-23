import AppKit
import Foundation
import PDFKit
import Vision

struct OCRPage: Codable {
    let page: Int
    let text: String
}

struct OCRResult: Codable {
    let path: String
    let backend: String
    let page_count: Int
    let processed_pages: Int
    let pages: [OCRPage]
}

func fail(_ message: String, code: Int32 = 2) -> Never {
    let payload: [String: Any] = [
        "error": message,
        "backend": "macos-vision",
    ]
    if let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted]),
       let text = String(data: data, encoding: .utf8) {
        FileHandle.standardOutput.write(text.data(using: .utf8)!)
        FileHandle.standardOutput.write("\n".data(using: .utf8)!)
    } else {
        FileHandle.standardError.write(message.data(using: .utf8)!)
        FileHandle.standardError.write("\n".data(using: .utf8)!)
    }
    exit(code)
}

let args = CommandLine.arguments
guard args.count >= 2 else {
    fail("usage: swift ocr_pdf_vision.swift <pdf-path> [max-pages]")
}

let path = args[1]
let maxPages = args.count >= 3 ? max(1, Int(args[2]) ?? 8) : 8
let url = URL(fileURLWithPath: path)

func recognize(cgImage: CGImage) -> String {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["en-US"]

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do {
        try handler.perform([request])
    } catch {
        return ""
    }

    return (request.results ?? [])
        .compactMap { observation in observation.topCandidates(1).first?.string }
        .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        .joined(separator: "\n")
}

func recognize(imageURL: URL) -> String {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["en-US"]

    let handler = VNImageRequestHandler(url: imageURL, options: [:])
    do {
        try handler.perform([request])
    } catch {
        return ""
    }

    return (request.results ?? [])
        .compactMap { observation in observation.topCandidates(1).first?.string }
        .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        .joined(separator: "\n")
}

let imageExtensions = ["png", "jpg", "jpeg", "tif", "tiff", "webp"]
if imageExtensions.contains(url.pathExtension.lowercased()) {
    let text = recognize(imageURL: url)
    let result = OCRResult(
        path: path,
        backend: "macos-vision",
        page_count: 1,
        processed_pages: 1,
        pages: text.isEmpty ? [] : [OCRPage(page: 1, text: text)]
    )
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    do {
        let data = try encoder.encode(result)
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write("\n".data(using: .utf8)!)
        exit(0)
    } catch {
        fail("cannot encode OCR result")
    }
}

guard let document = PDFDocument(url: url) else {
    fail("cannot open PDF")
}

let pageCount = document.pageCount
let pagesToProcess = min(pageCount, maxPages)
var pages: [OCRPage] = []

for pageIndex in 0..<pagesToProcess {
    guard let page = document.page(at: pageIndex) else {
        continue
    }

    let scale: CGFloat = 2.0
    let bounds = page.bounds(for: .mediaBox)
    let imageSize = NSSize(width: bounds.width * scale, height: bounds.height * scale)
    let image = page.thumbnail(of: imageSize, for: .mediaBox)

    guard let tiff = image.tiffRepresentation,
          let bitmap = NSBitmapImageRep(data: tiff),
          let cgImage = bitmap.cgImage else {
        continue
    }

    let text = recognize(cgImage: cgImage)
    if !text.isEmpty {
        pages.append(OCRPage(page: pageIndex + 1, text: text))
    }
}

let result = OCRResult(
    path: path,
    backend: "macos-vision",
    page_count: pageCount,
    processed_pages: pagesToProcess,
    pages: pages
)

let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
do {
    let data = try encoder.encode(result)
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write("\n".data(using: .utf8)!)
} catch {
    fail("cannot encode OCR result")
}
