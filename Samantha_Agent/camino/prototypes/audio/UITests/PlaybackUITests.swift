import XCTest

@MainActor final class PlaybackUITests: XCTestCase {
    private var app: XCUIApplication!

    private func launchFixture() throws {
        #if !targetEnvironment(simulator)
        throw XCTSkip("These tests use simulator-only synthetic media.")
        #endif
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchEnvironment["CAMINO_UI_TEST_SESSION"] = UUID().uuidString
        app.launchEnvironment["CAMINO_UI_TEST_SEED"] = "1"
        app.launch()
        app.launchEnvironment["CAMINO_UI_TEST_SEED"] = nil
        XCTAssertTrue(app.staticTexts["captureStatus"].waitForExistence(timeout: 15))
        XCTAssertEqual(app.staticTexts["captureStatus"].label, "Připraveno")
    }

    private func play() {
        let button = app.buttons["Přehrát"]
        for _ in 0..<4 {
            if button.isHittable { break }
            app.swipeUp()
        }
        XCTAssertTrue(button.isHittable)
        button.tap()
        XCTAssertTrue(app.staticTexts["playbackTime"].waitForExistence(timeout: 5))
        // Keep playback controls visible after reaching a library item below the fold.
        app.swipeDown()
    }

    func testPlaybackProgressStopAndReplay() throws {
        try launchFixture()
        play()
        let time = app.staticTexts["playbackTime"]
        let progress = app.progressIndicators["playbackProgress"]
        XCTAssertTrue(progress.exists)
        let firstTime = time.label
        let firstProgress = progress.value as? String
        let advances = NSPredicate { _, _ in time.label != firstTime && progress.value as? String != firstProgress }
        expectation(for: advances, evaluatedWith: nil)
        waitForExpectations(timeout: 8)
        XCTAssertTrue(time.label.contains("00:30"))
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = "Synthetic playback progress"; screenshot.lifetime = .keepAlways
        add(screenshot)
        app.buttons["Zastavit přehrávání"].tap()
        XCTAssertEqual(app.staticTexts["captureStatus"].label, "Připraveno")
        XCTAssertFalse(time.exists)
        play()
        XCTAssertEqual(app.staticTexts["captureStatus"].label, "Přehrávám")
        app.buttons["Zastavit přehrávání"].tap()
    }

    func testRelaunchPreservesClipWithoutAutomaticPlayback() throws {
        try launchFixture()
        play()
        app.terminate()
        app.launch()
        XCTAssertTrue(app.staticTexts["captureStatus"].waitForExistence(timeout: 15))
        XCTAssertEqual(app.staticTexts["captureStatus"].label, "Připraveno")
        XCTAssertFalse(app.staticTexts["playbackTime"].exists)
        XCTAssertEqual(app.buttons.matching(identifier: "Přehrát").count, 1)
        XCTAssertEqual(app.buttons.matching(identifier: "Start").count, 1)
        play()
        XCTAssertEqual(app.staticTexts["captureStatus"].label, "Přehrávám")
        app.buttons["Zastavit přehrávání"].tap()
    }
}
