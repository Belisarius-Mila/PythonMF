import XCTest

@MainActor final class CaminoHomeUITests: XCTestCase {
    func testOfflineSetupPrivacyMarkerAndRelaunch() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("This uses a simulator-only isolated Camino store.")
        #endif
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchEnvironment["CAMINO_UI_TEST_SESSION"] = UUID().uuidString
        app.launch()
        XCTAssertTrue(app.buttons["Založit Zkoušku"].waitForExistence(timeout: 15))
        app.buttons["Založit Zkoušku"].tap()
        XCTAssertTrue(app.staticTexts["Zkušební cesta"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.buttons["startComment"].exists)
        XCTAssertTrue(app.buttons["startReflection"].exists)
        XCTAssertTrue(app.buttons["startPhoto"].exists)
        XCTAssertTrue(app.buttons["startVideoCamera"].exists)
        XCTAssertTrue(app.staticTexts[
            "Po synchronizaci může být celý Moment dostupný v soukromém Vieweru."
        ].exists)
        app.buttons["Jen pro mě"].tap()
        XCTAssertTrue(app.staticTexts[
            "Jen pro mě zůstane mimo Viewer. Úvaha začíná takto vždy."
        ].exists)
        app.buttons["Nabídka"].tap()
        app.buttons["Označit okamžik"].tap()
        XCTAssertTrue(app.staticTexts["Označený okamžik"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts["Jen pro mě"].exists)
        app.buttons["momentRow"].firstMatch.tap()
        XCTAssertTrue(app.buttons["commentOnMoment"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.buttons["Přidat fotografii"].exists)
        app.buttons["Hotovo"].tap()
        app.terminate()
        app.launch()
        XCTAssertTrue(app.staticTexts["Zkušební cesta"].waitForExistence(timeout: 15))
        XCTAssertTrue(app.staticTexts["Označený okamžik"].exists)
        XCTAssertTrue(app.staticTexts[
            "Jen pro mě zůstane mimo Viewer. Úvaha začíná takto vždy."
        ].exists)
        XCTAssertFalse(app.staticTexts["Nahrávám"].exists)
    }
}
