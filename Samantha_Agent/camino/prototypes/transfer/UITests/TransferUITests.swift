import XCTest

@MainActor
final class TransferUITests: XCTestCase {
    func testCreatesSyntheticBatchWithoutConfigurationOrPersonalMedia() {
        let app = XCUIApplication()
        app.launchArguments = ["-uiTestReset"]
        app.launch()

        XCTAssertTrue(app.textFields["serverURL"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.secureTextFields["bearerToken"].exists)
        XCTAssertTrue(app.buttons["createSyntheticBatch"].isEnabled)
        app.buttons["createSyntheticBatch"].tap()

        let status = app.staticTexts["transferStatus"]
        XCTAssertTrue(status.waitForExistence(timeout: 5))
        let predicate = NSPredicate(format: "label == %@", "Dávka připravena")
        expectation(for: predicate, evaluatedWith: status)
        waitForExpectations(timeout: 60)
        XCTAssertTrue(app.progressIndicators["transferProgress"].exists)
        XCTAssertTrue(app.switches["cellularBatchGrant"].exists)
        XCTAssertEqual(app.switches["cellularBatchGrant"].value as? String, "0")
    }
}
