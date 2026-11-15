// Production writer logic against an in-memory EventKit substitute only.
enum EKAuthorizationStatus { case notDetermined, restricted, denied, fullAccess, writeOnly }
enum EKEntityType { case event }
enum EKSpan { case thisEvent }
class EKAlarm {
    var relativeOffset: Double; var absoluteDate: Date? = nil
    init(relativeOffset: Double) { self.relativeOffset = relativeOffset }
}
class EKCalendar { var calendarIdentifier = "synthetic"; var allowsContentModifications = true }
class EKEvent {
    var calendar = EKCalendar(); var eventIdentifier: String? = "native-event"
    var title: String?; var startDate = Date(); var endDate = Date()
    var timeZone: TimeZone?; var isAllDay = false; var location: String?
    var url: URL?; var notes: String?; var alarms: [EKAlarm]?
    var hasRecurrenceRules = false
    init(eventStore: EKEventStore) {}
}
struct EventQuery { let start: Date; let end: Date; let calendars: [EKCalendar] }
class EKEventStore {
    static var pool = [EKEvent](); static var saves = 0; static var inclusive = true
    static var destination = EKCalendar()
    static func authorizationStatus(for type: EKEntityType) -> EKAuthorizationStatus { .fullAccess }
    func event(withIdentifier id: String) -> EKEvent? { Self.pool.first { $0.eventIdentifier == id } }
    func calendar(withIdentifier id: String) -> EKCalendar? { id == "synthetic" ? Self.destination : nil }
    func predicateForEvents(withStart start: Date, end: Date, calendars: [EKCalendar]) -> EventQuery {
        EventQuery(start: start, end: end, calendars: calendars)
    }
    func events(matching query: EventQuery) -> [EKEvent] {
        Self.pool.filter { event in event.startDate < query.end && event.endDate > query.start
            && query.calendars.contains { $0.calendarIdentifier == event.calendar.calendarIdentifier } }
    }
    func save(_ event: EKEvent, span: EKSpan, commit: Bool) throws {
        Self.saves += 1
        if event.isAllDay && Self.inclusive { event.endDate = event.endDate.addingTimeInterval(-1) }
        Self.pool.append(event)
    }
}
func runCalendarWriterHarness(_ root: URL) throws {
    func check(_ condition: Bool, _ message: String) {
        if !condition { fputs("native_assertion_failed: \(message)\n", stderr); exit(1) }
    }
    func fixture(_ start: String, _ end: String, allDay: Bool = true, modern: Bool = true) throws -> (URL, [String: Any]) {
        let directory = root.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        EKEventStore.pool = []; EKEventStore.saves = 0; EKEventStore.inclusive = modern
        let event: [String: Any] = ["operation_id": UUID().uuidString, "calendar_id": "synthetic", "title": "Synthetic event",
            "start": start, "end": end, "all_day": allDay, "time_zone": "Europe/Prague", "location": "", "join_url": "", "reminders": [1440, 60]]
        return (directory.resolvingSymlinksInPath(), event)
    }
    func request(_ op: String, _ event: [String: Any]) -> [String: Any] { ["operation": op, "event": event] }
    var count = 0
    // Same-day, multiday, DST-short and DST-long periods; old and modern EventKit.
    for modern in [true, false] {
        for (start, end) in [("2026-11-11T23:00:00Z", "2026-11-12T23:00:00Z"),
                             ("2026-11-11T23:00:00Z", "2026-11-14T23:00:00Z"),
                             ("2026-03-27T23:00:00Z", "2026-03-29T22:00:00Z"),
                             ("2026-10-23T22:00:00Z", "2026-10-25T23:00:00Z")] {
            let (dir, event) = try fixture(start, end, modern: modern)
            let created = try transact(request("create", event), root: dir)
            check(created["status"] as? String == "saved_verified", "all-day create verification")
            check(EKEventStore.saves == 1, "create count")
            let observed = created["event"] as! [String: Any]
            let expectedEnd = iso.date(from: end)!.addingTimeInterval(modern ? -1 : 0)
            check(iso.date(from: observed["end"] as! String) == expectedEnd, "keep raw native identity")
            for operation in ["recover", "create"] {
                let recovered = try transact(request(operation, event), root: dir)
                check(recovered["status"] as? String == "saved_verified", "existing identity recovery")
                check(recovered["calendar_writes"] as? Bool == false && EKEventStore.saves == 1, "recovery created again")
            }
            count += 1
        }
    }
    // A one-second difference is accepted only at the inclusive all-day boundary.
    for (allDay, delta) in [(false, -1.0), (true, -2.0), (true, 1.0), (true, -1.5)] {
        let (dir, event) = try fixture("2026-11-11T23:00:00Z", "2026-11-12T23:00:00Z", allDay: allDay, modern: false)
        _ = try transact(request("create", event), root: dir)
        EKEventStore.pool[0].endDate = EKEventStore.pool[0].endDate.addingTimeInterval(delta)
        let result = try transact(request("recover", event), root: dir)
        check(result["status"] as? String == "write_unknown" && EKEventStore.saves == 1, "loose end tolerance")
        count += 1
    }
    for changed in ["title", "marker", "start", "alarms", "calendar", "zone", "all_day", "duplicate"] {
        let (dir, event) = try fixture("2026-11-11T23:00:00Z", "2026-11-12T23:00:00Z")
        _ = try transact(request("create", event), root: dir)
        let actual = EKEventStore.pool[0]
        switch changed {
        case "title": actual.title = "Changed"
        case "marker": actual.notes = "Other operation"
        case "start": actual.startDate = actual.startDate.addingTimeInterval(1)
        case "alarms": actual.alarms = [EKAlarm(relativeOffset: -3600)]
        case "calendar": actual.calendar = EKCalendar(); actual.calendar.calendarIdentifier = "other"
        case "zone": actual.timeZone = TimeZone(identifier: "UTC")
        case "all_day": actual.isAllDay = false
        default: EKEventStore.pool.append(actual)
        }
        let result = try transact(request("recover", event), root: dir)
        check(result["status"] as? String == "write_unknown" && EKEventStore.saves == 1, "identity mismatch: " + changed)
        count += 1
    }
    // A missing original event with an existing durable claim never grants retry.
    do {
        let (dir, event) = try fixture("2026-11-11T23:00:00Z", "2026-11-12T23:00:00Z")
        _ = try transact(request("create", event), root: dir); EKEventStore.pool = []
        let result = try transact(request("create", event), root: dir)
        check(result["status"] as? String == "write_unknown" && EKEventStore.saves == 1, "missing event retry")
        count += 1
    }
    print("calendar writer native: \(count) PASS; real calendar access: false")
}
