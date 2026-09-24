import XCTest

@MainActor final class CaminoHomeUITests: XCTestCase {
    func testSimulatedLowSpaceBlocksLargeCapturesButKeepsMarker() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("This uses simulator-only safety injection.")
        #endif
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchEnvironment["CAMINO_UI_TEST_SESSION"] = UUID().uuidString
        app.launchEnvironment["CAMINO_TEST_AVAILABLE_BYTES"] = "419430400"
        app.launch()
        XCTAssertTrue(app.buttons["Založit Zkoušku"].waitForExistence(timeout: 15))
        app.buttons["Založit Zkoušku"].tap()
        XCTAssertTrue(app.staticTexts["Zkušební cesta"].waitForExistence(timeout: 10))

        app.buttons["startComment"].tap()
        XCTAssertTrue(app.staticTexts[
            "Pro audio není dost bezpečného volného místa. Nahrávání nezačalo a nic se nemaže."
        ].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["startPhoto"].exists)

        app.buttons["startVideoCamera"].tap()
        XCTAssertTrue(app.staticTexts[
            "Pro video není dost bezpečného volného místa. Nahrávání nezačalo a nic se nemaže."
        ].waitForExistence(timeout: 5))

        app.buttons["startPhoto"].tap()
        XCTAssertTrue(app.staticTexts[
            "Pro fotografii není dost bezpečného volného místa. Nic se nemaže."
        ].waitForExistence(timeout: 5))

        app.buttons["Nabídka"].tap()
        app.buttons["Označit okamžik"].tap()
        XCTAssertTrue(app.staticTexts["Označený okamžik"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts[
            "Volné místo je pod 2 GiB. Krátký zápis zkusím uložit; nic se nemaže."
        ].exists)

        app.terminate()
        app.launch()
        XCTAssertTrue(app.staticTexts["Zkušební cesta"].waitForExistence(timeout: 15))
        XCTAssertTrue(app.staticTexts["Označený okamžik"].exists)
    }

    func testSimulatedCriticalThermalStateBlocksVideoStart() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("This uses simulator-only thermal injection.")
        #endif
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchEnvironment["CAMINO_UI_TEST_SESSION"] = UUID().uuidString
        app.launchEnvironment["CAMINO_TEST_AVAILABLE_BYTES"] = "3221225472"
        app.launchEnvironment["CAMINO_TEST_THERMAL_LEVEL"] = "critical"
        app.launch()
        XCTAssertTrue(app.buttons["Založit Zkoušku"].waitForExistence(timeout: 15))
        app.buttons["Založit Zkoušku"].tap()
        XCTAssertTrue(app.staticTexts["Zkušební cesta"].waitForExistence(timeout: 10))

        app.buttons["startVideoCamera"].tap()

        XCTAssertTrue(app.staticTexts[
            "Telefon hlásí kritickou teplotu. Video nezačalo a kvalita se skrytě nemění."
        ].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["startPhoto"].exists)
        XCTAssertFalse(app.buttons["startVideo"].exists)
    }

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

    func testDraftRevisionLockHideAndRestoreStayLocalAcrossRelaunch() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("This uses a simulator-only isolated Camino store.")
        #endif
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchEnvironment["CAMINO_UI_TEST_SESSION"] = UUID().uuidString
        app.launch()
        XCTAssertTrue(app.buttons["Založit Zkoušku"].waitForExistence(timeout: 15))
        app.buttons["Založit Zkoušku"].tap()
        app.buttons["Nabídka"].tap()
        app.buttons["Označit okamžik"].tap()
        XCTAssertTrue(app.buttons["momentRow"].waitForExistence(timeout: 10))
        app.buttons["momentRow"].tap()
        XCTAssertTrue(app.buttons["editMomentText"].waitForExistence(timeout: 10))
        app.buttons["editMomentText"].tap()
        let editor = app.textViews["momentTextEditor"]
        XCTAssertTrue(editor.waitForExistence(timeout: 10))
        editor.tap()
        editor.typeText("synthetic local note")

        app.terminate()
        app.launch()
        XCTAssertTrue(app.buttons["momentRow"].waitForExistence(timeout: 15))
        app.buttons["momentRow"].tap()
        app.buttons["editMomentText"].tap()
        XCTAssertTrue(app.staticTexts[
            "Obnovený místní koncept · dosud není publikovanou revizí"
        ].waitForExistence(timeout: 10))
        XCTAssertEqual(app.textViews["momentTextEditor"].value as? String,
                       "synthetic local note")
        app.buttons["saveMomentText"].tap()
        XCTAssertTrue(app.staticTexts["synthetic local note"].waitForExistence(timeout: 10))

        app.buttons["lockMoment"].tap()
        XCTAssertTrue(app.staticTexts["Jen pro mě"].waitForExistence(timeout: 10))
        app.buttons["hideMoment"].tap()
        XCTAssertTrue(app.alerts["Skrýt Moment?"].waitForExistence(timeout: 5))
        app.alerts["Skrýt Moment?"].buttons["Skrýt"].tap()
        app.buttons["Hotovo"].tap()
        XCTAssertFalse(app.buttons["momentRow"].exists)

        app.buttons["Nabídka"].tap()
        let hidden = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'Skryté'"))
            .firstMatch
        XCTAssertTrue(hidden.waitForExistence(timeout: 5))
        hidden.tap()
        XCTAssertTrue(app.buttons["restoreHiddenMoment"].waitForExistence(timeout: 10))
        app.buttons["restoreHiddenMoment"].tap()
        app.buttons["Hotovo"].tap()
        XCTAssertTrue(app.buttons["momentRow"].waitForExistence(timeout: 10))
    }

    func testSyncQueuePauseSurvivesRelaunchWithoutBlockingLocalCapture() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("This uses a simulator-only isolated Camino store.")
        #endif
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchEnvironment["CAMINO_UI_TEST_SESSION"] = UUID().uuidString
        app.launch()
        XCTAssertTrue(app.buttons["Založit Zkoušku"].waitForExistence(timeout: 15))
        app.buttons["Založit Zkoušku"].tap()

        app.buttons["Nabídka"].tap()
        app.buttons["Uložení a přenosy"].tap()
        XCTAssertTrue(app.navigationBars["Uložení a přenosy"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts["c05cPhoneStatus"].exists)
        app.swipeUp()
        XCTAssertTrue(app.buttons["toggleSyncPause"].waitForExistence(timeout: 5))
        app.buttons["toggleSyncPause"].tap()
        XCTAssertTrue(app.staticTexts["Přenosy jsou pozastavené"].waitForExistence(timeout: 5))

        app.terminate()
        app.launch()
        XCTAssertTrue(app.staticTexts["Zkušební cesta"].waitForExistence(timeout: 15))
        XCTAssertTrue(app.buttons["startComment"].exists)
        app.buttons["Nabídka"].tap()
        app.buttons["Uložení a přenosy"].tap()
        app.swipeUp()
        XCTAssertTrue(app.buttons["Pokračovat v přenosech"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts["Přenosy jsou pozastavené"].exists)
    }

    func testC05cShowsFourIndependentTruthfulStatusAxes() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("This uses a simulator-only synthetic C05c status fixture.")
        #endif
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchEnvironment["CAMINO_UI_TEST_SESSION"] = UUID().uuidString
        app.launchEnvironment["CAMINO_TEST_C05C_SCENARIO"] = "ai_without_backup"
        app.launch()
        XCTAssertTrue(app.buttons["Založit Zkoušku"].waitForExistence(timeout: 15))
        app.buttons["Založit Zkoušku"].tap()

        app.buttons["Nabídka"].tap()
        app.buttons["Uložení a přenosy"].tap()
        XCTAssertTrue(app.navigationBars["Uložení a přenosy"].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts["c05cPhoneStatus"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.staticTexts["syncStatus"].exists)
        app.swipeUp()
        XCTAssertTrue(app.staticTexts["c05cBackupStatus"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.staticTexts["c05cBackupStatus"].label,
                       "Další záloha zatím není ověřená")
        XCTAssertTrue(app.staticTexts["c05cAIStatus"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.staticTexts["c05cAIStatus"].label,
                       "1 výsledek AI je hotový")
        XCTAssertTrue(app.staticTexts["c05cAIStatusDetail"].label.contains(
            "Přepis není záloha"))
    }
}
