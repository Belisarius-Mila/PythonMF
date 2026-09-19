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
        let grant = app.switches["cellularBatchGrant"]
        XCTAssertTrue(grant.exists)
        XCTAssertEqual(grant.value as? String, "0")
        grant.tap()
        let alert = app.alerts.firstMatch
        XCTAssertTrue(alert.waitForExistence(timeout: 5))
        XCTAssertTrue(alert.buttons["Povolit pro tuto dávku"].exists)
        XCTAssertEqual(grant.value as? String, "0")
        alert.buttons["Povolit pro tuto dávku"].tap()
        let granted = NSPredicate(format: "value == %@", "1")
        expectation(for: granted, evaluatedWith: grant)
        waitForExpectations(timeout: 5)
    }
}
