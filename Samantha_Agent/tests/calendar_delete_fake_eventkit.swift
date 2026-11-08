// Test-only in-memory EventKit replacement. Production Swift logic is compiled
// unchanged against these types; no EventKit import, database or OS grant.
enum EKAuthorizationStatus { case notDetermined, restricted, denied, fullAccess, writeOnly }
enum EKSpan { case thisEvent, futureEvents }
enum EKEventStatus: Int { case none=0 }
enum EKRecurrenceFrequency: Int { case daily=0 }
enum EKWeekday: Int { case monday=2 }
class EKRecurrenceDayOfWeek { var dayOfTheWeek=EKWeekday.monday;var weekNumber=0 }
class EKRecurrenceEnd { var endDate: Date?=nil;var occurrenceCount=0 }
class EKRecurrenceRule {
    var frequency=EKRecurrenceFrequency.daily;var interval=1;var firstDayOfTheWeek=2
    var daysOfTheWeek: [EKRecurrenceDayOfWeek]?=nil
    var daysOfTheMonth: [NSNumber]?=nil;var monthsOfTheYear: [NSNumber]?=nil
    var weeksOfTheYear: [NSNumber]?=nil;var daysOfTheYear: [NSNumber]?=nil;var setPositions: [NSNumber]?=nil
    var recurrenceEnd: EKRecurrenceEnd?=nil
}
class EKAlarm { var relativeOffset=Double(-3600);var absoluteDate: Date?=nil }
class EKCalendar { var calendarIdentifier="private";var allowsContentModifications=true;var title="Osobní" }
class EKEvent {
    var calendar=EKCalendar();var eventIdentifier: String?="native-event";var calendarItemIdentifier="native-item"
    var title: String?="Káva";var startDate=Date(timeIntervalSince1970:1794387600);var endDate=Date(timeIntervalSince1970:1794391200)
    var isAllDay=false;var location: String?=nil;var notes: String?=nil;var url: URL?=nil;var timeZone: TimeZone?=nil
    var lastModifiedDate: Date?=Date(timeIntervalSince1970:1);var creationDate: Date?=Date(timeIntervalSince1970:1)
    var occurrenceDate: Date?=nil;var recurrenceRules: [EKRecurrenceRule]?=nil;var alarms: [EKAlarm]?=nil
    var hasAttendees=false;var organizer: String?=nil;var status=EKEventStatus.none;var isDetached=false
    var hasRecurrenceRules: Bool { !(recurrenceRules ?? []).isEmpty }
}
struct EventQuery { let start: Date;let end: Date;let calendars: [EKCalendar] }
enum FakeError: Error { case fail }
class EKEventStore {
    static var pool=[EKEvent]();static var removes=0;static var spans=[EKSpan]();static var fail=false
    static var calendar=EKCalendar()
    static func authorizationStatus(for kind: FakeKind) -> EKAuthorizationStatus { .fullAccess }
    enum FakeKind { case event }
    func requestFullAccessToEvents(completion: (Bool,Error?)->Void) { completion(true,nil) }
    func calendar(withIdentifier id: String) -> EKCalendar? { id==Self.calendar.calendarIdentifier ? Self.calendar : nil }
    func predicateForEvents(withStart start: Date,end: Date,calendars: [EKCalendar]) -> EventQuery { EventQuery(start:start,end:end,calendars:calendars) }
    func events(matching query: EventQuery) -> [EKEvent] {
        Self.pool.filter { event in event.startDate<query.end && event.endDate>query.start && query.calendars.contains { $0.calendarIdentifier==event.calendar.calendarIdentifier } }
    }
    func remove(_ event: EKEvent,span: EKSpan,commit: Bool) throws {
        Self.removes+=1;Self.spans.append(span)
        if Self.fail { throw FakeError.fail }
        Self.pool.removeAll { $0 === event }
    }
}

func runCalendarDeleteHarness(_ root: URL) throws {
    var passed=0
    func fixture() throws -> (URL,EKEvent,[String: Any]) {
        let dir=root.appendingPathComponent(UUID().uuidString);try FileManager.default.createDirectory(at:dir,withIntermediateDirectories:true)
        let event=EKEvent();EKEventStore.pool=[event];EKEventStore.calendar=event.calendar;EKEventStore.removes=0;EKEventStore.spans=[];EKEventStore.fail=false
        let summary: [String: Any] = ["calendar_id":"private","title":event.title!,"start":iso.string(from:event.startDate),"end":iso.string(from:event.endDate),"all_day":false]
        // Foundation canonicalizes an existing /private/var test folder to
        // /var. Use its canonical spelling just like the real helper's loader.
        return (dir.resolvingSymlinksInPath(),event,summary)
    }
    func request(_ op: String,_ event: [String: Any],_ frozen: [String: Any]=[:],_ id: String=String(repeating:"a",count:32)) -> [String: Any] {
        ["operation":op,"event":event,"identity":frozen,"operation_id":op=="inspect" ? "" : id]
    }
    func check(_ condition: Bool,_ message: String) { if !condition { fatalError(message) } }
    // Exact identity, single remove, same/different request replay, read-only recovery.
    do {
        let (dir,_,event)=try fixture();let p=try transact(request("inspect",event),dir);check(p["status"] as? String=="preview","preview")
        let id=p["identity"] as! [String: Any];check(EKEventStore.removes==0,"inspect mutated")
        let done=try transact(request("delete",event,id),dir);check(done["status"] as? String=="deleted_verified","delete")
        check(EKEventStore.removes==1 && EKEventStore.spans==[.thisEvent],"span")
        for op in ["delete","recover_delete"] {
            let replay=try transact(request(op,event,id),dir);check(replay["status"] as? String=="deleted_verified","replay")
            check(replay["calendar_writes"] as? Bool==false,"replay writes")
        }
        let other=try transact(request("delete",event,id,String(repeating:"b",count:32)),dir)
        check(other["status"] as? String=="delete_unknown" && EKEventStore.removes==1,"new request retried target");passed+=1
    }
    // Changes in hidden details must invalidate a previously confirmed preview.
    for change in ["notes","modified","alarm","recurrence","id","title","time"] {
        let (dir,event,summary)=try fixture();let p=try transact(request("inspect",summary),dir);let frozen=p["identity"] as! [String: Any]
        switch change {
        case "notes":event.notes="changed"
        case "modified":event.lastModifiedDate=Date()
        case "alarm":event.alarms=[EKAlarm()]
        case "recurrence":event.recurrenceRules=[EKRecurrenceRule()]
        case "id":event.eventIdentifier="foreign"
        case "title":event.title="other"
        default:event.startDate=event.startDate.addingTimeInterval(60)
        }
        let result=try transact(request("delete",summary,frozen),dir)
        check(result["status"] as? String=="changed" && EKEventStore.removes==0,"changed "+change);passed+=1
    }
    do {
        let (dir,event,summary)=try fixture();let other=EKEvent();other.eventIdentifier="duplicate";EKEventStore.pool=[event,other]
        check(try transact(request("inspect",summary),dir)["status"] as? String=="changed","duplicates");check(EKEventStore.removes==0,"duplicate removal");passed+=1
    }
    for invited in [true,false] {
        let (dir,event,summary)=try fixture();if invited { event.hasAttendees=true } else { event.organizer="other" }
        check(try transact(request("inspect",summary),dir)["status"] as? String=="unsupported","invitation")
        check(EKEventStore.removes==0,"invite remove");passed+=1
    }
    do {
        let (dir,event,summary)=try fixture();event.recurrenceRules=[EKRecurrenceRule()];event.occurrenceDate=event.startDate
        let future=EKEvent();future.startDate=event.startDate.addingTimeInterval(86400);future.endDate=event.endDate.addingTimeInterval(86400)
        EKEventStore.pool=[event,future];let p=try transact(request("inspect",summary),dir);let frozen=p["identity"] as! [String: Any]
        check(frozen["recurring"] as? Bool==true,"recurrence flag")
        check(try transact(request("delete",summary,frozen),dir)["status"] as? String=="deleted_verified","recurring remove")
        check(EKEventStore.pool.count==1 && EKEventStore.pool[0] === future && EKEventStore.spans==[.thisEvent],"future removed");passed+=1
    }
    do {
        let (dir,_,summary)=try fixture();let p=try transact(request("inspect",summary),dir);let frozen=p["identity"] as! [String: Any]
        check(try transact(request("recover_delete",summary,frozen),dir)["status"] as? String=="delete_unknown","recover missing")
        check(EKEventStore.removes==0,"recover removed");EKEventStore.fail=true
        check(try transact(request("delete",summary,frozen),dir)["status"] as? String=="delete_unknown","failed remove")
        for op in ["delete","recover_delete"] { _=try transact(request(op,summary,frozen),dir) }
        _=try transact(request("delete",summary,frozen,String(repeating:"b",count:32)),dir)
        check(EKEventStore.removes==1,"uncertain remove retried");passed+=1
    }
    do {
        let (dir,event,summary)=try fixture();let p=try transact(request("inspect",summary),dir);let frozen=p["identity"] as! [String: Any]
        EKEventStore.fail=true;_=try transact(request("delete",summary,frozen),dir)
        event.notes="provider update while unknown";let newer=try transact(request("inspect",summary),dir)
        var blocked=false
        do { _=try transact(request("delete",summary,newer["identity"] as! [String: Any],String(repeating:"b",count:32)),dir) }
        catch { blocked=true }
        check(blocked && EKEventStore.removes==1,"changed fingerprint reopened unknown target");passed+=1
    }
    do {
        let (dir,event,summary)=try fixture();let p=try transact(request("inspect",summary),dir);event.calendar.allowsContentModifications=false
        check(try transact(request("delete",summary,p["identity"] as! [String: Any]),dir)["status"] as? String=="calendar_unavailable","read only")
        check(EKEventStore.removes==0,"readonly remove");passed+=1
    }
    print("Calendar delete native transaction scenarios: \(passed) PASS; real calendar access: false")
}
