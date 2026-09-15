// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "CaminoAudioCore",
    platforms: [.macOS(.v13), .iOS(.v17)],
    products: [.library(name: "CaminoAudioCore", targets: ["CaminoAudioCore"])],
    targets: [
        .target(name: "CaminoAudioCore", path: "Core"),
        .target(name: "CaminoAudioInspection", dependencies: ["CaminoAudioCore"], path: "AudioIO"),
        .testTarget(name: "CaminoAudioCoreTests", dependencies: ["CaminoAudioCore", "CaminoAudioInspection"])
    ]
)
