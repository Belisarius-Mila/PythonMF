import XCTest
@testable import CaminoLocalCore

final class CameraZoomTests: XCTestCase {
    func testVirtualUltraWideUsesDisplayedScaleAndSupportedPresets() throws {
        let scale = try XCTUnwrap(LocalCameraZoomScale(minimumDeviceFactor: 1,
            maximumDeviceFactor: 10, displayMultiplier: 0.5))
        XCTAssertEqual(scale.displayRange, 0.5...5)
        XCTAssertEqual(scale.presets, [0.5, 1, 2])
        XCTAssertEqual(scale.deviceFactor(forDisplayFactor: 1), 2)
        XCTAssertEqual(scale.deviceFactor(forDisplayFactor: 2), 4)
        XCTAssertEqual(scale.displayFactor(forDeviceFactor: 3), 1.5)
    }

    func testSingleWideCameraDoesNotOfferUltraWide() throws {
        let scale = try XCTUnwrap(LocalCameraZoomScale(minimumDeviceFactor: 1,
            maximumDeviceFactor: 4, displayMultiplier: 1))
        XCTAssertEqual(scale.presets, [1, 2])
        XCTAssertEqual(scale.deviceFactor(forDisplayFactor: 0.5), 1)
        XCTAssertEqual(scale.deviceFactor(forDisplayFactor: 400), 4)
        XCTAssertEqual(scale.deviceFactor(forDisplayFactor: -20), 1)
    }

    func testChangingHardwareLimitsClampBothDirectionsAndHideUnavailablePresets() throws {
        let scale = try XCTUnwrap(LocalCameraZoomScale(minimumDeviceFactor: 2.5,
            maximumDeviceFactor: 3.5, displayMultiplier: 0.5))
        XCTAssertEqual(scale.presets, [])
        XCTAssertEqual(scale.deviceFactor(forDisplayFactor: 1), 2.5)
        XCTAssertEqual(scale.deviceFactor(forDisplayFactor: 2), 3.5)
        XCTAssertEqual(scale.displayFactor(forDeviceFactor: 100), 1.75)
        XCTAssertEqual(scale.displayFactor(forDeviceFactor: -1), 1.25)
    }

    func testUnavailableZoomKeepsOneFixedValue() throws {
        let scale = try XCTUnwrap(LocalCameraZoomScale(minimumDeviceFactor: 1,
            maximumDeviceFactor: 1, displayMultiplier: 1))
        XCTAssertEqual(scale.presets, [1])
        XCTAssertEqual(scale.displayRange, 1...1)
        XCTAssertEqual(scale.deviceFactor(forDisplayFactor: 2), 1)
    }

    func testNonFiniteGestureAndHardwareValuesAreRejected() throws {
        let scale = try XCTUnwrap(LocalCameraZoomScale(minimumDeviceFactor: 1,
            maximumDeviceFactor: 8, displayMultiplier: 0.5))
        for invalid in [Double.nan, .infinity, -.infinity] {
            XCTAssertNil(scale.deviceFactor(forDisplayFactor: invalid))
            XCTAssertNil(scale.displayFactor(forDeviceFactor: invalid))
            XCTAssertNil(LocalCameraZoomScale(minimumDeviceFactor: invalid,
                maximumDeviceFactor: 8, displayMultiplier: 1))
            XCTAssertNil(LocalCameraZoomScale(minimumDeviceFactor: 1,
                maximumDeviceFactor: invalid, displayMultiplier: 1))
            XCTAssertNil(LocalCameraZoomScale(minimumDeviceFactor: 1,
                maximumDeviceFactor: 8, displayMultiplier: invalid))
        }
        XCTAssertNil(LocalCameraZoomScale(minimumDeviceFactor: 0, maximumDeviceFactor: 8, displayMultiplier: 1))
        XCTAssertNil(LocalCameraZoomScale(minimumDeviceFactor: 2, maximumDeviceFactor: 1, displayMultiplier: 1))
        XCTAssertNil(LocalCameraZoomScale(minimumDeviceFactor: 1, maximumDeviceFactor: 8, displayMultiplier: 0))
        XCTAssertNil(LocalCameraZoomScale(minimumDeviceFactor: 1, maximumDeviceFactor: .greatestFiniteMagnitude,
            displayMultiplier: 2))
    }
}
