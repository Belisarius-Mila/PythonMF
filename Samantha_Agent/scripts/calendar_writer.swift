import AppKit
import EventKit
import Foundation
import CoreFoundation
import Darwin

// Creates only a new, explicitly confirmed event. No update/delete API.
enum WriterError: Error { case invalidRequest }
let iso = ISO8601DateFormatter()
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
func base(_ operation: String) -> [String: Any] {
    return ["schema": 1, "operation": operation, "authorization": authorization(),
            "calendar_writes": false, "parent_pid": Int(getppid()),
            "bundle_identifier": Bundle.main.bundleIdentifier ?? "unidentified",
            "observed_at": iso.string(from: Date())]
}
func text(_ value: [String: Any], _ key: String, _ limit: Int, required: Bool = false) throws -> String {
    guard let s = value[key] as? String, s.count <= limit, !s.contains("\0"),
          !required || !s.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw WriterError.invalidRequest }
    return s
}
func validate(_ e: [String: Any]) throws -> (Date, Date, TimeZone, [Int]) {
    guard Set(e.keys) == Set(["operation_id", "calendar_id", "title", "start", "end", "time_zone", "all_day", "location", "join_url", "reminders"]),
          UUID(uuidString: try text(e, "operation_id", 36, required: true)) != nil,
          let start = iso.date(from: try text(e, "start", 40, required: true)),
          let end = iso.date(from: try text(e, "end", 40, required: true)),
          end > start, end.timeIntervalSince(start) <= 7 * 86400,
          let zone = TimeZone(identifier: try text(e, "time_zone", 100, required: true)),
          let allDay = e["all_day"] as? NSNumber, CFGetTypeID(allDay) == CFBooleanGetTypeID(),
          let alarms = e["reminders"] as? [NSNumber], alarms.count <= 2,
          alarms.allSatisfy({ CFGetTypeID($0) != CFBooleanGetTypeID() && [60.0,1440.0].contains($0.doubleValue) }),
          Set(alarms.map { $0.intValue }).count == alarms.count else { throw WriterError.invalidRequest }
    _ = try text(e, "calendar_id", 512, required: true); _ = try text(e, "title", 1000, required: true)
    _ = try text(e, "location", 1000)
    let link = try text(e, "join_url", 1000)
    if !link.isEmpty {
        guard let url = URLComponents(string: link), ["http","https"].contains(url.scheme ?? ""),
              !(url.host ?? "").isEmpty, url.user == nil, url.password == nil else { throw WriterError.invalidRequest }
    }
    return (start, end, zone, alarms.map { $0.intValue }.sorted())
}
func serialized(_ value: [String: Any]) throws -> Data {
    return try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
}
func marker(_ event: [String: Any]) -> String { return "Samantha event: " + (event["operation_id"] as! String) }
func facts(_ event: EKEvent) -> [String: Any] {
    return ["event_id": event.eventIdentifier ?? "", "calendar_id": event.calendar.calendarIdentifier,
            "title": event.title ?? "", "start": iso.string(from: event.startDate), "end": iso.string(from: event.endDate),
            "time_zone": event.timeZone?.identifier ?? "", "all_day": event.isAllDay,
            "location": event.location ?? "", "join_url": event.url?.absoluteString ?? "",
            "reminders": (event.alarms ?? []).map { -$0.relativeOffset / 60 }.sorted(),
            "marker": event.notes ?? ""]
}
func matches(_ event: EKEvent, _ expected: [String: Any]) throws -> Bool {
    let (start, end, zone, alarms) = try validate(expected)
    return event.calendar.calendarIdentifier == expected["calendar_id"] as? String
        && event.title == expected["title"] as? String && event.startDate == start && event.endDate == end
        && event.timeZone?.identifier == zone.identifier && event.isAllDay == expected["all_day"] as? Bool
        && (event.location ?? "") == expected["location"] as? String
        && (event.url?.absoluteString ?? "") == expected["join_url"] as? String
        && event.notes == marker(expected) && !event.hasRecurrenceRules
        && (event.alarms ?? []).allSatisfy { $0.absoluteDate == nil }
        && (event.alarms ?? []).map { -$0.relativeOffset / 60 }.sorted() == alarms.map { Double($0) }
}
func find(_ e: [String: Any], id: String? = nil) throws -> EKEvent? {
    // A new store performs read-back rather than trusting the object passed to save.
    let store = EKEventStore(); let (start, end, _, _) = try validate(e)
    if let id = id, let event = store.event(withIdentifier: id), try matches(event, e) { return event }
    guard let calendar = store.calendar(withIdentifier: e["calendar_id"] as! String) else { return nil }
    let events = store.events(matching: store.predicateForEvents(withStart: start, end: end, calendars: [calendar]))
        .filter { $0.notes == marker(e) }
    guard events.count == 1, try matches(events[0], e) else { return nil }
    return events[0]
}
func transact(_ request: [String: Any], root: URL) throws -> [String: Any] {
    let operation = request["operation"] as! String
    guard let e = request["event"] as? [String: Any] else { throw WriterError.invalidRequest }
    let (start, end, zone, alarms) = try validate(e)
    var result = base(operation); result["operation_id"] = e["operation_id"]
    result["expected"] = e
    guard authorization() == "full_access" else { result["status"] = "authorization_required"; return result }
    let directory = root.appendingPathComponent("transactions")
    try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
    let journal = directory.appendingPathComponent((e["operation_id"] as! String) + ".json")
    let lockPath = journal.path + ".lock"
    guard journal.path == journal.resolvingSymlinksInPath().path,
          lockPath == URL(fileURLWithPath: lockPath).resolvingSymlinksInPath().path else { throw WriterError.invalidRequest }
    let fd = Darwin.open(lockPath, O_CREAT | O_RDWR | O_NOFOLLOW, S_IRUSR | S_IWUSR)
    guard fd >= 0 else { throw WriterError.invalidRequest }
    defer { Darwin.close(fd) }
    guard flock(fd, LOCK_EX | LOCK_NB) == 0 else { throw WriterError.invalidRequest }
    let exists = FileManager.default.fileExists(atPath: journal.path)
    if exists {
        let saved = try JSONSerialization.jsonObject(with: Data(contentsOf: journal)) as? [String: Any]
        guard let old = saved?["event"] as? [String: Any], try serialized(old) == serialized(e) else { throw WriterError.invalidRequest }
    }
    if let found = try find(e) {
        result["status"] = "saved_verified"; result["event"] = facts(found); return result
    }
    // A prior journal or a recovery request can NEVER invoke save again.
    if exists || operation == "recover" { result["status"] = "write_unknown"; return result }
    let store = EKEventStore()
    guard let calendar = store.calendar(withIdentifier: e["calendar_id"] as! String), calendar.allowsContentModifications else {
        result["status"] = "calendar_unavailable"; return result
    }
    let event = EKEvent(eventStore: store)
    event.calendar = calendar; event.title = e["title"] as? String
    event.startDate = start; event.endDate = end; event.timeZone = zone
    event.isAllDay = e["all_day"] as! Bool; event.location = e["location"] as? String
    let link = e["join_url"] as! String; event.url = link.isEmpty ? nil : URL(string: link)
    event.notes = marker(e); event.alarms = alarms.map { EKAlarm(relativeOffset: -Double($0) * 60) }
    // Atomic exclusive claim + fsync BEFORE the sole mutation call.
    try serialized(["event": e, "state": "save_started"]).write(to: journal, options: .withoutOverwriting)
    let journalFD = Darwin.open(journal.path, O_RDONLY | O_NOFOLLOW)
    guard journalFD >= 0 else { throw WriterError.invalidRequest }
    let synced = fsync(journalFD); Darwin.close(journalFD)
    guard synced == 0 else { throw WriterError.invalidRequest }
    let directoryFD = Darwin.open(directory.path, O_RDONLY | O_NOFOLLOW)
    guard directoryFD >= 0 else { throw WriterError.invalidRequest }
    let directorySynced = fsync(directoryFD); Darwin.close(directoryFD)
    guard directorySynced == 0 else { throw WriterError.invalidRequest }
    result["calendar_writes"] = true
    do { try store.save(event, span: .thisEvent, commit: true) }
    catch { result["status"] = "write_unknown"; return result }
    if let found = try find(e, id: event.eventIdentifier) {
        result["status"] = "saved_verified"; result["event"] = facts(found)
    } else { result["status"] = "write_unknown" }
    return result
}
func load(_ filename: String) throws -> (URL, URL, [String: Any]) {
    guard let configured = Bundle.main.object(forInfoDictionaryKey: "SamanthaPilotRoot") as? String else { throw WriterError.invalidRequest }
    let root = URL(fileURLWithPath: configured).standardizedFileURL
    let input = URL(fileURLWithPath: filename).standardizedFileURL
    let directory = input.deletingLastPathComponent()
    guard root.path == root.resolvingSymlinksInPath().path, input.path == input.resolvingSymlinksInPath().path,
          input.lastPathComponent == "request.json", directory.deletingLastPathComponent().path == root.appendingPathComponent("requests").path,
          UUID(uuidString: directory.lastPathComponent) != nil, (try Data(contentsOf: input)).count <= 32000,
          let value = try JSONSerialization.jsonObject(with: Data(contentsOf: input)) as? [String: Any],
          value["schema"] as? Int == 1, value["request_id"] as? String == directory.lastPathComponent,
          let operation = value["operation"] as? String, ["authorize","create","recover"].contains(operation),
          Set(value.keys) == Set(operation == "authorize" ? ["schema","operation","request_id","start","end"] : ["schema","operation","request_id","event"]) else { throw WriterError.invalidRequest }
    return (root, directory.appendingPathComponent("response.json"), value)
}
func emit(_ value: [String: Any], _ output: URL) throws {
    var result = value; result["request_id"] = output.deletingLastPathComponent().lastPathComponent
    try serialized(result).write(to: output, options: .withoutOverwriting)
}
do {
    let args = Array(CommandLine.arguments.dropFirst())
    if args == ["--status-json"] { print(String(decoding: try serialized(base("status")), as: UTF8.self)) }
    else if args == ["--self-test"] {
        let good: [String: Any] = ["operation_id":"00000000-0000-4000-8000-000000000001", "calendar_id":"synthetic", "title":"Test",
            "start":"2026-11-11T09:00:00Z", "end":"2026-11-11T10:00:00Z", "time_zone":"Europe/Prague", "all_day":false,
            "location":"", "join_url":"", "reminders":[1440,60]]
        _ = try validate(good); var count = 1
        for changes: [String: Any] in [["end":"2026-11-11T08:00:00Z"],["reminders":[true]],["all_day":1],["join_url":"file:///tmp/test"],["operation_id":"../other"]] {
            do { _ = try validate(good.merging(changes, uniquingKeysWith: { _, new in new })) }
            catch { count += 1 }
        }
        guard count == 6 else { throw WriterError.invalidRequest }
        print("{\"self_test\":true,\"checks\":6,\"calendar_accessed\":false}")
    } else if args.count == 1 {
        let (root, output, request) = try load(args[0])
        if request["operation"] as? String == "authorize" {
            if !["not_determined","write_only"].contains(authorization()) {
                var r = base("authorize"); r["status"] = "authorization_checked"; try emit(r, output)
            } else {
                let app = NSApplication.shared; app.setActivationPolicy(.accessory)
                EKEventStore().requestFullAccessToEvents { _, error in
                    DispatchQueue.main.async {
                        var r = base("authorize"); r["status"] = error == nil ? "authorization_checked" : "authorization_error"
                        do { try emit(r, output) } catch { fputs("writer_response_failed\n", stderr) }
                        app.terminate(nil)
                    }
                }
                app.run()
            }
        } else { try emit(transact(request, root: root), output) }
    } else { throw WriterError.invalidRequest }
} catch { fputs("calendar_writer_failed\n", stderr); exit(2) }
