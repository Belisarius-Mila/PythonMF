import AppKit
import EventKit
import Foundation
import Darwin

// This pilot deliberately contains no EventKit mutation API.
func authorization() -> String {
    switch EKEventStore.authorizationStatus(for: .event) {
    case .notDetermined: return "not_determined"
    case .restricted: return "restricted"
    case .denied: return "denied"
    case .fullAccess: return "full_access"
    case .writeOnly: return "write_only"
    @unknown default: return "unknown"
    }
}

enum PilotError: Error { case invalidRequest }

func interval(_ request: [String: Any]) throws -> (Date, Date) {
    let formatter = ISO8601DateFormatter()
    guard let a = request["start"] as? String, let b = request["end"] as? String,
          let start = formatter.date(from: a), let end = formatter.date(from: b),
          end > start, end.timeIntervalSince(start) <= 31 * 86400 else {
        throw PilotError.invalidRequest
    }
    return (start, end)
}

func base(_ operation: String) -> [String: Any] {
    return ["schema": 1, "operation": operation, "authorization": authorization(),
            "calendar_writes": false, "parent_pid": Int(getppid()),
            "bundle_identifier": Bundle.main.bundleIdentifier ?? "unidentified",
            "observed_at": ISO8601DateFormatter().string(from: Date())]
}

func probe(_ request: [String: Any]) throws -> [String: Any] {
    let (start, end) = try interval(request)
    var result = base("probe")
    guard authorization() == "full_access" else {
        result["status"] = "authorization_required"
        return result
    }
    let store = EKEventStore()
    let calendars = store.calendars(for: .event)
    guard calendars.count <= 512 else { throw PilotError.invalidRequest }
    // Inventory is local and private. Event bodies, titles, locations and notes
    // are never exported, even into this private response.
    result["calendars"] = calendars.map { calendar in
        ["id": calendar.calendarIdentifier, "title": calendar.title,
         "source_title": calendar.source.title,
         "source_type": calendar.source.sourceType.rawValue,
         "writable": calendar.allowsContentModifications] as [String: Any]
    }
    let selected = calendars.filter {
        $0.source.sourceType == .calDAV && $0.source.title.lowercased() == "icloud"
    }
    result["calendar_count"] = calendars.count
    result["icloud_calendar_count"] = selected.count
    result["status"] = selected.isEmpty ? "icloud_source_not_found" : "read_verified"
    result["start"] = request["start"]
    result["end"] = request["end"]
    if !selected.isEmpty {
        let predicate = store.predicateForEvents(withStart: start, end: end, calendars: selected)
        result["event_count"] = store.events(matching: predicate).count
    }
    return result
}

func loadRequest(_ filename: String) throws -> (URL, [String: Any]) {
    let input = URL(fileURLWithPath: filename).standardizedFileURL
    guard let configured = Bundle.main.object(forInfoDictionaryKey: "SamanthaPilotRoot") as? String else {
        throw PilotError.invalidRequest
    }
    let root = URL(fileURLWithPath: configured).standardizedFileURL
    let directory = input.deletingLastPathComponent()
    guard input.path == input.resolvingSymlinksInPath().path,
          root.path == root.resolvingSymlinksInPath().path,
          input.lastPathComponent == "request.json",
          directory.deletingLastPathComponent().path == root.appendingPathComponent("requests").path,
          UUID(uuidString: directory.lastPathComponent) != nil,
          let value = try JSONSerialization.jsonObject(with: Data(contentsOf: input)) as? [String: Any],
          Set(value.keys) == Set(["schema", "operation", "request_id", "start", "end"]),
          value["schema"] as? Int == 1,
          value["request_id"] as? String == directory.lastPathComponent,
          let operation = value["operation"] as? String,
          ["authorize", "probe"].contains(operation) else { throw PilotError.invalidRequest }
    _ = try interval(value)
    return (directory.appendingPathComponent("response.json"), value)
}

func emit(_ value: [String: Any], to output: URL) {
    do {
        var result = value
        result["request_id"] = output.deletingLastPathComponent().lastPathComponent
        let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
        try data.write(to: output, options: .withoutOverwriting)
    } catch {
        fputs("calendar_pilot_response_failed\n", stderr)
        exit(2)
    }
}

do {
    let args = Array(CommandLine.arguments.dropFirst())
    if args == ["--status-json"] {
        let data = try JSONSerialization.data(withJSONObject: base("status"), options: [.sortedKeys])
        print(String(decoding: data, as: UTF8.self))
    } else if args == ["--self-test"] {
        _ = try interval(["start": "2026-11-06T00:00:00Z", "end": "2026-11-07T00:00:00Z"])
        var rejected = 0
        for value in [["start": "bad", "end": "bad"],
                      ["start": "2026-11-07T00:00:00Z", "end": "2026-11-06T00:00:00Z"],
                      ["start": "2026-11-06T00:00:00Z", "end": "2027-01-01T00:00:00Z"]] {
            do { _ = try interval(value) } catch { rejected += 1 }
        }
        guard rejected == 3 else { throw PilotError.invalidRequest }
        print("{\"self_test\":true,\"checks\":4,\"calendar_accessed\":false}")
    } else if args.count == 1 {
        let (output, request) = try loadRequest(args[0])
        if request["operation"] as? String == "authorize" {
            if !["not_determined", "write_only"].contains(authorization()) {
                var result = base("authorize"); result["status"] = "authorization_checked"
                emit(result, to: output)
            } else {
                let app = NSApplication.shared
                app.setActivationPolicy(.accessory)
                let store = EKEventStore()
                store.requestFullAccessToEvents { _, error in
                    DispatchQueue.main.async {
                        var result = base("authorize")
                        result["status"] = error == nil ? "authorization_checked" : "authorization_error"
                        emit(result, to: output)
                        app.terminate(nil)
                    }
                }
                app.run()
            }
        } else {
            emit(try probe(request), to: output)
        }
    } else { throw PilotError.invalidRequest }
} catch {
    fputs("calendar_pilot_invalid_request\n", stderr)
    exit(2)
}
