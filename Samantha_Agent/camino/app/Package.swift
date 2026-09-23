// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "CaminoLocalCore",
    platforms: [.macOS(.v13), .iOS(.v17)],
    products: [.library(name: "CaminoLocalCore", targets: ["CaminoLocalCore"])],
    dependencies: [.package(path: "../prototypes/audio")],
    targets: [
        .target(name: "CaminoLocalCore", path: "Core"),
        .testTarget(name: "CaminoLocalCoreTests", dependencies: ["CaminoLocalCore"]),
        .testTarget(
            name: "CaminoAudioLinkTests",
            dependencies: ["CaminoLocalCore", .product(name: "CaminoAudioCore", package: "audio")],
            path: ".",
            exclude: ["Camino.xcodeproj", "Config.xcconfig", "LocalSigning.xcconfig",
                      "C04b_IPHONE_TEST_PLAN.md", "C04d_IPHONE_TEST_PLAN.md",
                      "C05b_IPHONE_TEST_PLAN.md", "Core", "README.md", "UITests",
                      "Tests/CaminoLocalCoreTests", "App/CaminoApp.swift",
                      "App/CaminoViewModel.swift", "App/CameraCaptureController.swift",
                      "App/CameraCaptureView.swift", "App/CaminoSyncCoordinator.swift",
                      "App/Info.plist"],
            sources: ["App/IntentRecordingStore.swift", "Tests/CaminoAudioLinkTests/AudioLinkTests.swift"]
        ),
    ]
)
