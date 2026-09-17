// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "CaminoTransferCore",
    platforms: [.macOS(.v13), .iOS(.v17)],
    products: [.library(name: "CaminoTransferCore", targets: ["CaminoTransferCore"])],
    targets: [
        .target(name: "CaminoTransferCore", path: "Core"),
        .testTarget(
            name: "CaminoTransferCoreTests",
            dependencies: ["CaminoTransferCore"]
        ),
    ]
)
