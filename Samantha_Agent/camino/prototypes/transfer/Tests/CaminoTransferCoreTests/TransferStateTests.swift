import XCTest
@testable import CaminoTransferCore

final class TransferStateTests: XCTestCase {
    private let firstBatch = UUID()

    private func item(
        batchID: UUID? = nil,
        locallySent: Int64 = 0
    ) -> TransferQueueItem {
        TransferQueueItem(
            assetID: "synthetic-video",
            batchID: batchID ?? firstBatch,
            chunkCount: 3,
            byteCount: 300,
            locallySentByteCount: locallySent
        )
    }

    func testRelaunchTrustsServerAndRequestsOnlyMissingChunks() {
        let plan = TransferReconciler.plan(
            item: item(locallySent: 300),
            server: TransferServerSnapshot(
                acceptedChunks: [0, 2],
                state: .uploading
            ),
            networkAvailable: true,
            userPaused: false
        )

        XCTAssertEqual(
            plan.displayState,
            .uploading(acceptedChunks: 2, totalChunks: 3)
        )
        XCTAssertEqual(plan.missingChunks, [1])
    }

    func testUnavailableNetworkWaitsWithoutClaimingRemoteState() {
        let plan = TransferReconciler.plan(
            item: item(locallySent: 300),
            server: TransferServerSnapshot(acceptedChunks: [0, 1, 2], state: .verified),
            networkAvailable: false,
            userPaused: false
        )

        XCTAssertEqual(plan.displayState, .waitingForNetwork)
        XCTAssertEqual(plan.missingChunks, [0, 1, 2])
    }

    func testMissingSnapshotStartsReconciliationWithoutInventingAcceptedChunks() {
        let plan = TransferReconciler.plan(
            item: item(locallySent: 300),
            server: nil,
            networkAvailable: true,
            userPaused: false
        )

        XCTAssertEqual(
            plan.displayState,
            .uploading(acceptedChunks: 0, totalChunks: 3)
        )
        XCTAssertEqual(plan.missingChunks, [0, 1, 2])
    }

    func testOneHundredPercentBytesStillShowsVerifyingUntilServerReceipt() {
        let pending = TransferReconciler.plan(
            item: item(locallySent: 300),
            server: TransferServerSnapshot(acceptedChunks: [0, 1, 2], state: .uploading),
            networkAvailable: true,
            userPaused: false
        )
        let verifying = TransferReconciler.plan(
            item: item(locallySent: 300),
            server: TransferServerSnapshot(acceptedChunks: [0, 1, 2], state: .verifying),
            networkAvailable: true,
            userPaused: false
        )

        XCTAssertEqual(item(locallySent: 300).localByteProgress, 1)
        XCTAssertEqual(pending.displayState, .verifying)
        XCTAssertEqual(verifying.displayState, .verifying)
    }

    func testOnlyVerifiedServerReceiptShowsVerifiedOnMac() {
        let plan = TransferReconciler.plan(
            item: item(),
            server: TransferServerSnapshot(acceptedChunks: [0, 1, 2], state: .verified),
            networkAvailable: true,
            userPaused: false
        )

        XCTAssertEqual(plan.displayState, .verifiedOnMac)
        XCTAssertEqual(plan.missingChunks, [])
    }

    func testServerVerificationFailureNeedsAttention() {
        let plan = TransferReconciler.plan(
            item: item(locallySent: 300),
            server: TransferServerSnapshot(
                acceptedChunks: [0, 1, 2],
                state: .verificationFailed
            ),
            networkAvailable: true,
            userPaused: false
        )

        XCTAssertEqual(plan.displayState, .needsAttention)
        XCTAssertEqual(plan.missingChunks, [])
    }

    func testPauseWinsWithoutChangingTheQueueItem() {
        let source = item(locallySent: 120)
        let plan = TransferReconciler.plan(
            item: source,
            server: TransferServerSnapshot(acceptedChunks: [0], state: .uploading),
            networkAvailable: true,
            userPaused: true
        )

        XCTAssertEqual(plan.displayState, .paused)
        XCTAssertEqual(source.locallySentByteCount, 120)
    }

    func testCellularGrantAppliesOnlyToTheExistingBatch() {
        var grant = CellularBatchGrant()
        let allowed = item()
        let newCapture = item(batchID: UUID())

        grant.grant(for: allowed.batchID)
        XCTAssertTrue(grant.allows(allowed))
        XCTAssertFalse(grant.allows(newCapture))
        grant.revoke()
        XCTAssertFalse(grant.allows(allowed))
    }

    func testInvalidLocalCountsAreClampedWithoutAffectingRemoteTruth() {
        let negative = TransferQueueItem(
            assetID: "negative",
            batchID: firstBatch,
            chunkCount: -2,
            byteCount: -1,
            locallySentByteCount: 99
        )
        let excessive = item(locallySent: 999)

        XCTAssertEqual(negative.chunkCount, 0)
        XCTAssertEqual(negative.byteCount, 0)
        XCTAssertEqual(negative.localByteProgress, 0)
        XCTAssertEqual(excessive.locallySentByteCount, excessive.byteCount)
        XCTAssertEqual(excessive.localByteProgress, 1)
    }
}
