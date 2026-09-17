import Foundation
import Network

struct BackgroundTaskSnapshot: Equatable, Sendable {
    let taskIdentifier: Int
    let description: String
    let state: URLSessionTask.State
}

enum BackgroundTransferEvent: Sendable {
    case progress(description: String, sent: Int64, expected: Int64)
    case completed(
        description: String,
        statusCode: Int?,
        responseBody: Data,
        errorCode: Int?
    )
    case finishedEvents
}

final class BackgroundTransferDriver: NSObject, URLSessionDataDelegate,
    URLSessionTaskDelegate, @unchecked Sendable
{
    static let identifier = "cz.pythonmf.camino.transfer.prototype.background.v1"

    private let eventHandler: @Sendable (BackgroundTransferEvent) -> Void
    private let lock = NSLock()
    private var responseBodies: [Int: Data] = [:]
    private var sessionStorage: URLSession!

    init(eventHandler: @escaping @Sendable (BackgroundTransferEvent) -> Void) {
        self.eventHandler = eventHandler
        super.init()
        let configuration = URLSessionConfiguration.background(withIdentifier: Self.identifier)
        configuration.sessionSendsLaunchEvents = true
        configuration.isDiscretionary = false
        configuration.waitsForConnectivity = true
        configuration.allowsCellularAccess = true
        configuration.allowsExpensiveNetworkAccess = true
        configuration.timeoutIntervalForResource = 24 * 60 * 60
        configuration.urlCache = nil
        sessionStorage = URLSession(
            configuration: configuration,
            delegate: self,
            delegateQueue: nil
        )
    }

    func scheduleUpload(
        request: URLRequest,
        fileURL: URL,
        description: String
    ) -> Int {
        let task = sessionStorage.uploadTask(with: request, fromFile: fileURL)
        task.taskDescription = description
        task.countOfBytesClientExpectsToSend = request.value(forHTTPHeaderField: "Content-Length")
            .flatMap(Int64.init) ?? NSURLSessionTransferSizeUnknown
        task.countOfBytesClientExpectsToReceive = 4096
        task.resume()
        return task.taskIdentifier
    }

    func taskSnapshots() async -> [BackgroundTaskSnapshot] {
        await sessionStorage.allTasks.compactMap { task in
            guard let description = task.taskDescription else { return nil }
            return BackgroundTaskSnapshot(
                taskIdentifier: task.taskIdentifier,
                description: description,
                state: task.state
            )
        }
    }

    func suspendAll() async {
        for task in await sessionStorage.allTasks { task.suspend() }
    }

    func resumeAll() async {
        for task in await sessionStorage.allTasks { task.resume() }
    }

    func cancelAll() async {
        for task in await sessionStorage.allTasks { task.cancel() }
    }

    func urlSession(
        _ session: URLSession,
        task: URLSessionTask,
        didSendBodyData bytesSent: Int64,
        totalBytesSent: Int64,
        totalBytesExpectedToSend: Int64
    ) {
        guard let description = task.taskDescription else { return }
        eventHandler(.progress(
            description: description,
            sent: totalBytesSent,
            expected: totalBytesExpectedToSend
        ))
    }

    func urlSession(
        _ session: URLSession,
        dataTask: URLSessionDataTask,
        didReceive data: Data
    ) {
        lock.lock()
        responseBodies[dataTask.taskIdentifier, default: Data()].append(data)
        lock.unlock()
    }

    func urlSession(
        _ session: URLSession,
        task: URLSessionTask,
        didCompleteWithError error: (any Error)?
    ) {
        lock.lock()
        let body = responseBodies.removeValue(forKey: task.taskIdentifier) ?? Data()
        lock.unlock()
        let code = (task.response as? HTTPURLResponse)?.statusCode
        let errorCode = (error as NSError?)?.code
        eventHandler(.completed(
            description: task.taskDescription ?? "",
            statusCode: code,
            responseBody: body,
            errorCode: errorCode
        ))
    }

    func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        eventHandler(.finishedEvents)
    }
}

struct NetworkPathState: Equatable, Sendable {
    let available: Bool
    let expensive: Bool
}

final class TransferNetworkMonitor: @unchecked Sendable {
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "cz.pythonmf.camino.transfer.network")
    private let handler: @Sendable (NetworkPathState) -> Void

    init(handler: @escaping @Sendable (NetworkPathState) -> Void) {
        self.handler = handler
        monitor.pathUpdateHandler = { path in
            handler(NetworkPathState(
                available: path.status == .satisfied,
                expensive: path.isExpensive
            ))
        }
    }

    func start() { monitor.start(queue: queue) }
    func cancel() { monitor.cancel() }
}
