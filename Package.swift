// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ANCSoftware",
    platforms: [
        .macOS(.v13),
        .iOS(.v16)
    ],
    products: [
        .library(
            name: "ANCSoftware",
            targets: ["ANCSoftware"]
        ),
        .executable(
            name: "anc-cli",
            targets: ["ANCCLI"]
        )
    ],
    dependencies: [],
    targets: [
        .target(
            name: "ANCSoftware",
            dependencies: []
        ),
        .executableTarget(
            name: "ANCCLI",
            dependencies: ["ANCSoftware"]
        ),
        .testTarget(
            name: "ANCSoftwareTests",
            dependencies: ["ANCSoftware"]
        )
    ]
)
