import Foundation

public enum TransferRemoteState: String, Codable, Sendable {
    case uploading
    case verifying
    case verified
    case verificationFailed = "verification_failed"
}

public enum TransferDisplayState: Equatable, Sendable {
    case paused
    case waitingForNetwork
    case uploading(acceptedChunks: Int, totalChunks: Int)
    case verifying
    case verifiedOnMac
    case needsAttention
}

public struct TransferQueueItem: Equatable, Sendable {
    public let assetID: String
    public let batchID: UUID
    public let chunkCount: Int
    public let byteCount: Int64
    public let locallySentByteCount: Int64

    public init(
        assetID: String,
        batchID: UUID,
        chunkCount: Int,
        byteCount: Int64,
        locallySentByteCount: Int64
    ) {
        self.assetID = assetID
        self.batchID = batchID
        self.chunkCount = max(0, chunkCount)
        self.byteCount = max(0, byteCount)
        self.locallySentByteCount = min(max(0, locallySentByteCount), self.byteCount)
    }

    public var localByteProgress: Double {
        guard byteCount > 0 else { return 0 }
        return Double(locallySentByteCount) / Double(byteCount)
    }
}

public struct TransferServerSnapshot: Equatable, Sendable {
    public let acceptedChunks: Set<Int>
    public let state: TransferRemoteState

    public init(acceptedChunks: Set<Int>, state: TransferRemoteState) {
        self.acceptedChunks = acceptedChunks
        self.state = state
    }
}

public struct TransferPlan: Equatable, Sendable {
    public let displayState: TransferDisplayState
    public let missingChunks: [Int]

    public init(displayState: TransferDisplayState, missingChunks: [Int]) {
        self.displayState = displayState
        self.missingChunks = missingChunks
    }
}

public enum TransferReconciler {
    /// The server snapshot is authoritative after relaunch. Local byte progress is
    /// informative only and can never produce `verifiedOnMac`.
    public static func plan(
        item: TransferQueueItem,
        server: TransferServerSnapshot?,
        networkAvailable: Bool,
        userPaused: Bool
    ) -> TransferPlan {
        let allChunks = Array(0..<item.chunkCount)
        if userPaused {
            return TransferPlan(displayState: .paused, missingChunks: allChunks)
        }
        guard networkAvailable else {
            return TransferPlan(displayState: .waitingForNetwork, missingChunks: allChunks)
        }
        guard let server else {
            return TransferPlan(
                displayState: .uploading(acceptedChunks: 0, totalChunks: item.chunkCount),
                missingChunks: allChunks
            )
        }

        let accepted = server.acceptedChunks.filter { allChunks.contains($0) }
        let missing = allChunks.filter { !accepted.contains($0) }
        switch server.state {
        case .verified:
            return TransferPlan(displayState: .verifiedOnMac, missingChunks: [])
        case .verificationFailed:
            return TransferPlan(displayState: .needsAttention, missingChunks: missing)
        case .verifying:
            return TransferPlan(displayState: .verifying, missingChunks: [])
        case .uploading where missing.isEmpty:
            return TransferPlan(displayState: .verifying, missingChunks: [])
        case .uploading:
            return TransferPlan(
                displayState: .uploading(
                    acceptedChunks: accepted.count,
                    totalChunks: item.chunkCount
                ),
                missingChunks: missing
            )
        }
    }
}

public struct CellularBatchGrant: Equatable, Sendable {
    public private(set) var batchID: UUID?

    public init(batchID: UUID? = nil) {
        self.batchID = batchID
    }

    public mutating func grant(for batchID: UUID) {
        self.batchID = batchID
    }

    public mutating func revoke() {
        batchID = nil
    }

    public func allows(_ item: TransferQueueItem) -> Bool {
        batchID == item.batchID
    }
}
