import AppKit
import EventKit
import Foundation
import CryptoKit
import CoreFoundation
import Darwin

// Separate from the deployed reader/create-only writer. Always .thisEvent.
enum DeleteError: Error { case invalid }
let iso = ISO8601DateFormatter()
func encode(_ value: [String: Any]) throws -> Data { try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]) }
func auth() -> String {
    switch EKEventStore.authorizationStatus(for: .event) {
    case .notDetermined: return "not_determined"
    case .restricted: return "restricted"
    case .denied: return "denied"
    case .fullAccess: return "full_access"
    case .writeOnly: return "write_only"
    @unknown default: return "unknown"
    }
}
func base(_ op: String) -> [String: Any] {
    ["schema":1,"operation":op,"authorization":auth(),"calendar_writes":false,
     "parent_pid":Int(getppid()),"bundle_identifier":Bundle.main.bundleIdentifier ?? "unidentified",
     "observed_at":iso.string(from:Date())]
}
func string(_ value: [String: Any], _ key: String, _ max: Int) throws -> String {
    guard let s=value[key] as? String, !s.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty,
          s.count<=max, !s.unicodeScalars.contains(where: { $0.value<32 && !(key=="title" && [9,10,13].contains($0.value)) }) else { throw DeleteError.invalid }
    return s
}
func validate(_ e: [String: Any]) throws -> (Date,Date) {
    guard Set(e.keys)==Set(["calendar_id","title","start","end","all_day"]),
          let a=iso.date(from:try string(e,"start",40)), let b=iso.date(from:try string(e,"end",40)),
          b>a, b.timeIntervalSince(a)<=31*86400,
          let flag=e["all_day"] as? NSNumber, CFGetTypeID(flag)==CFBooleanGetTypeID() else { throw DeleteError.invalid }
    _=try string(e,"calendar_id",512); _=try string(e,"title",400)
    return (a,b)
}
func validateIdentity(_ identity: [String: Any]) throws {
    guard Set(identity.keys)==Set(["event_id","item_id","fingerprint","recurring"]),
          let hash=identity["fingerprint"] as? String, hash.range(of:"^[a-f0-9]{64}$",options:.regularExpression) != nil,
          let flag=identity["recurring"] as? NSNumber, CFGetTypeID(flag)==CFBooleanGetTypeID() else { throw DeleteError.invalid }
    _=try string(identity,"event_id",1024); _=try string(identity,"item_id",1024)
}
func isSame(_ event: EKEvent, _ expected: [String: Any]) throws -> Bool {
    let (a,b)=try validate(expected)
    return event.calendar.calendarIdentifier==expected["calendar_id"] as? String && event.title==expected["title"] as? String
        && event.startDate==a && event.endDate==b && event.isAllDay==expected["all_day"] as? Bool
}
func identity(_ event: EKEvent) throws -> [String: Any] {
    let recurring=event.hasRecurrenceRules || event.isDetached || event.occurrenceDate != nil
    let facts: [String: Any] = ["calendar_id":event.calendar.calendarIdentifier,"event_id":event.eventIdentifier ?? "",
        "item_id":event.calendarItemIdentifier,"title":event.title ?? "","start":iso.string(from:event.startDate),
        "end":iso.string(from:event.endDate),"all_day":event.isAllDay,"location":event.location ?? "",
        "notes":event.notes ?? "","url":event.url?.absoluteString ?? "","zone":event.timeZone?.identifier ?? "",
        "modified":event.lastModifiedDate?.timeIntervalSince1970 ?? -1,"created":event.creationDate?.timeIntervalSince1970 ?? -1,
        "occurrence":event.occurrenceDate?.timeIntervalSince1970 ?? -1,"recurrence":(event.recurrenceRules ?? []).map { rule -> [String: Any] in
            ["frequency":rule.frequency.rawValue,"interval":rule.interval,"first_day":rule.firstDayOfTheWeek,
             "weekdays":(rule.daysOfTheWeek ?? []).map { [$0.dayOfTheWeek.rawValue,$0.weekNumber] },
             "monthdays":rule.daysOfTheMonth ?? [],"months":rule.monthsOfTheYear ?? [],"weeks":rule.weeksOfTheYear ?? [],
             "yeardays":rule.daysOfTheYear ?? [],"positions":rule.setPositions ?? [],
             "until":rule.recurrenceEnd?.endDate?.timeIntervalSince1970 ?? -1,"count":rule.recurrenceEnd?.occurrenceCount ?? 0]
        },
        "alarms":(event.alarms ?? []).map { "\($0.relativeOffset):\($0.absoluteDate?.timeIntervalSince1970 ?? -1)" },
        "attendees":event.hasAttendees,"organizer":event.organizer != nil,"status":event.status.rawValue]
    let hash=SHA256.hash(data:try encode(facts)).map { String(format:"%02x",$0) }.joined()
    let value: [String: Any] = ["event_id":event.eventIdentifier ?? "","item_id":event.calendarItemIdentifier,"fingerprint":hash,"recurring":recurring]
    try validateIdentity(value); return value
}
func candidates(_ store: EKEventStore, _ calendar: EKCalendar, _ expected: [String: Any]) throws -> [EKEvent] {
    let (a,b)=try validate(expected)
    return try store.events(matching:store.predicateForEvents(withStart:a,end:b,calendars:[calendar])).filter { try isSame($0,expected) }
}
func persist(_ value: [String: Any], _ path: URL, first: Bool) throws {
    try encode(value).write(to:path,options:first ? .withoutOverwriting : .atomic)
    for url in [path,path.deletingLastPathComponent()] {
        let fd=Darwin.open(url.path,O_RDONLY|O_NOFOLLOW);guard fd>=0 else { throw DeleteError.invalid }
        let result=fsync(fd);Darwin.close(fd);guard result==0 else { throw DeleteError.invalid }
    }
}
func transact(_ request: [String: Any], _ root: URL) throws -> [String: Any] {
    let op=request["operation"] as! String, expected=request["event"] as! [String: Any]
    _=try validate(expected)
    var result=base(op);result["expected"]=expected;result["operation_id"]=request["operation_id"]
    result["identity"]=request["identity"]
    guard auth()=="full_access" else { result["status"]="authorization_required";return result }
    let store=EKEventStore()
    guard let calendar=store.calendar(withIdentifier:expected["calendar_id"] as! String),calendar.allowsContentModifications else {
        result["status"]="calendar_unavailable";return result
    }
    if op=="inspect" {
        let found=try candidates(store,calendar,expected)
        guard found.count==1 else { result["status"]="changed";return result }
        guard !found[0].hasAttendees && found[0].organizer==nil else { result["status"]="unsupported";return result }
        let day=DateFormatter();day.calendar=Calendar(identifier:.gregorian);day.locale=Locale(identifier:"en_US_POSIX")
        day.timeZone=found[0].timeZone ?? TimeZone.current;day.dateFormat="yyyy-MM-dd"
        result["start_day"]=day.string(from:found[0].startDate);result["calendar_title"]=String(calendar.title.prefix(200))
        result["identity"]=try identity(found[0]);result["status"]="preview";return result
    }
    let frozen=request["identity"] as! [String: Any];try validateIdentity(frozen)
    let operationID=try string(request,"operation_id",32)
    guard operationID.range(of:"^[a-f0-9]{32}$",options:.regularExpression) != nil else { throw DeleteError.invalid }
    let directory=root.appendingPathComponent("transactions")
    try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
    // Claim the native target, not just the UI request: another tab/new preview
    // can never retry an uncertain removal of the same frozen occurrence.
    // Scope is stable even if a provider changes notes/lastModified while a
    // previous remove is uncertain. Such a change cannot create a retry slot.
    let scope: [String: Any] = ["calendar_id":expected["calendar_id"]!,"event_id":frozen["event_id"]!,
                               "item_id":frozen["item_id"]!,"start":iso.string(from:(try validate(expected)).0)]
    let targetKey=SHA256.hash(data:try encode(scope)).map { String(format:"%02x",$0) }.joined()
    let journal=directory.appendingPathComponent(targetKey+".json"),lock=directory.appendingPathComponent(targetKey+".lock")
    guard journal.path==journal.resolvingSymlinksInPath().path,lock.path==lock.resolvingSymlinksInPath().path else { throw DeleteError.invalid }
    let fd=Darwin.open(lock.path,O_CREAT|O_RDWR|O_NOFOLLOW,S_IRUSR|S_IWUSR);guard fd>=0 else { throw DeleteError.invalid }
    defer { Darwin.close(fd) };guard flock(fd,LOCK_EX|LOCK_NB)==0 else { throw DeleteError.invalid }
    var prior: [String: Any]?=nil
    if FileManager.default.fileExists(atPath:journal.path) {
        guard let value=try JSONSerialization.jsonObject(with:Data(contentsOf:journal)) as? [String: Any],
              let old=value["event"] as? [String: Any],let oldID=value["identity"] as? [String: Any],
              try encode(old)==encode(expected),try encode(oldID)==encode(frozen) else { throw DeleteError.invalid }
        prior=value
    }
    // Recovery and duplicate calls can only inspect the journal, never remove.
    if prior != nil || op=="recover_delete" {
        result["status"]=(prior?["operation_id"] as? String==operationID && prior?["state"] as? String=="deleted_verified") ? "deleted_verified" : "delete_unknown"
        return result
    }
    let found=try candidates(store,calendar,expected)
    guard found.count==1,try encode(identity(found[0]))==encode(frozen) else { result["status"]="changed";return result }
    guard !found[0].hasAttendees && found[0].organizer==nil else { result["status"]="unsupported";return result }
    var record: [String: Any] = ["event":expected,"identity":frozen,"operation_id":operationID,"state":"delete_started"]
    try persist(record,journal,first:true) // fsynced durable claim before the only mutation.
    result["calendar_writes"]=true
    do { try store.remove(found[0],span:.thisEvent,commit:true) }
    catch { result["status"]="delete_unknown";return result }
    // A new store verifies the exact occurrence is gone. Identical other events
    // are never removed; ID + occurrence is checked, not just its title.
    let fresh=EKEventStore()
    guard let freshCalendar=fresh.calendar(withIdentifier:expected["calendar_id"] as! String) else { result["status"]="delete_unknown";return result }
    let remains=try candidates(fresh,freshCalendar,expected).contains {
        $0.eventIdentifier==frozen["event_id"] as? String && $0.calendarItemIdentifier==frozen["item_id"] as? String
    }
    guard !remains else { result["status"]="delete_unknown";return result }
    record["state"]="deleted_verified";try persist(record,journal,first:false)
    result["status"]="deleted_verified";return result
}
func load(_ filename: String) throws -> (URL,URL,[String: Any]) {
    guard let configured=Bundle.main.object(forInfoDictionaryKey:"SamanthaPilotRoot") as? String else { throw DeleteError.invalid }
    let root=URL(fileURLWithPath:configured).standardizedFileURL,input=URL(fileURLWithPath:filename).standardizedFileURL
    let directory=input.deletingLastPathComponent()
    guard root.path==root.resolvingSymlinksInPath().path,input.path==input.resolvingSymlinksInPath().path,
          input.lastPathComponent=="request.json",directory.deletingLastPathComponent().path==root.appendingPathComponent("requests").path,
          UUID(uuidString:directory.lastPathComponent) != nil,(try Data(contentsOf:input)).count<=16000,
          let value=try JSONSerialization.jsonObject(with:Data(contentsOf:input)) as? [String: Any],
          value["schema"] as? Int==1,value["request_id"] as? String==directory.lastPathComponent,
          let op=value["operation"] as? String,["authorize","inspect","delete","recover_delete"].contains(op),
          Set(value.keys)==Set(op=="authorize" ? ["schema","operation","request_id","start","end"] : ["schema","operation","request_id","event","operation_id","identity"]) else { throw DeleteError.invalid }
    if op != "authorize" {
        guard let e=value["event"] as? [String: Any],let id=value["identity"] as? [String: Any] else { throw DeleteError.invalid }
        _=try validate(e)
        if op=="inspect" { guard id.isEmpty,value["operation_id"] as? String=="" else { throw DeleteError.invalid } }
        else { try validateIdentity(id) }
    }
    return (root,directory.appendingPathComponent("response.json"),value)
}
func emit(_ value: [String: Any], _ path: URL) throws {
    var result=value;result["request_id"]=path.deletingLastPathComponent().lastPathComponent
    try encode(result).write(to:path,options:.withoutOverwriting)
}
do {
    let args=Array(CommandLine.arguments.dropFirst())
    if args==["--status-json"] { print(String(decoding:try encode(base("status")),as:UTF8.self)) }
    else if args==["--self-test"] {
        let good: [String: Any] = ["calendar_id":"synthetic","title":"Test","start":"2026-11-11T09:00:00Z","end":"2026-11-11T10:00:00Z","all_day":false]
        _=try validate(good);var count=1
        for change: [String: Any] in [["end":"2026-11-11T08:00:00Z"],["all_day":1],["title":""],["calendar_id":"\u{0}"],["extra":true]] {
            do { _=try validate(good.merging(change,uniquingKeysWith:{_,new in new})) } catch { count+=1 }
        }
        do { try validateIdentity(["event_id":"x","item_id":"y","fingerprint":"bad","recurring":false]) } catch { count+=1 }
        guard count==7 else { throw DeleteError.invalid };print("{\"self_test\":true,\"checks\":7,\"calendar_accessed\":false}")
    } else if args.count==1 {
        let (root,output,request)=try load(args[0])
        if request["operation"] as? String=="authorize" {
            if !["not_determined","write_only"].contains(auth()) { var result=base("authorize");result["status"]="authorization_checked";try emit(result,output) }
            else {
                let app=NSApplication.shared;app.setActivationPolicy(.accessory)
                EKEventStore().requestFullAccessToEvents { _,error in DispatchQueue.main.async {
                    var result=base("authorize");result["status"]=error==nil ? "authorization_checked" : "authorization_error"
                    do { try emit(result,output) } catch { fputs("calendar_delete_response_failed\n",stderr) };app.terminate(nil)
                }};app.run()
            }
        } else { try emit(transact(request,root),output) }
    } else { throw DeleteError.invalid }
} catch { fputs("calendar_delete_failed\n",stderr);exit(2) }
