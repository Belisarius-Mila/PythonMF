var editSaves=0,editFail=false,changeID=false
extension EKEventStore {
    func save(_ event: EKEvent,span: EKSpan,commit: Bool) throws {
        editSaves+=1;Self.spans.append(span)
        if editFail { throw FakeError.fail }
        if changeID { event.eventIdentifier="new-detached-id";event.calendarItemIdentifier="new-detached-item" }
    }
}
func runCalendarEditHarness(_ root: URL) throws {
    try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
    func check(_ value: Bool) throws { if !value { throw FakeError.fail } }
    func summary(_ event: EKEvent) -> [String: Any] {
        ["calendar_id":event.calendar.calendarIdentifier,"title":event.title!,"start":iso.string(from:event.startDate),"end":iso.string(from:event.endDate),"all_day":event.isAllDay]
    }
    func setup(_ n: String) throws -> (EKEvent,URL,[String: Any],[String: Any]) {
        let event=EKEvent();event.notes="Keep notes";event.location="Keep place";event.alarms=[EKAlarm()]
        EKEventStore.pool=[event];EKEventStore.spans=[];editSaves=0;editFail=false;changeID=false
        let directory=root.appendingPathComponent(n);try FileManager.default.createDirectory(at:directory,withIntermediateDirectories:true)
        let old=summary(event);var target=old;target["title"]="Changed";target["start"]=iso.string(from:event.startDate.addingTimeInterval(86400));target["end"]=iso.string(from:event.endDate.addingTimeInterval(86400))
        return (event,directory.resolvingSymlinksInPath(),old,target)
    }
    func request(_ op: String,_ old: [String: Any],_ target: [String: Any],_ id: [String: Any],_ operation: String) -> [String: Any] {
        ["operation":op,"event":old,"replacement":target,"identity":id,"operation_id":operation]
    }
    let operation=String(repeating:"a",count:32)
    // Real production code: one update, unchanged fields, duplicate and recovery read-only.
    do {
        let (e,dir,old,target)=try setup("verified");let id=try identity(e)
        let v=try transact(request("update",old,target,id,operation),dir)
        try check(v["status"] as? String=="edited_verified" && editSaves==1 && e.notes=="Keep notes" && e.location=="Keep place" && e.alarms?.count==1)
        for op in ["update","recover_update"] { let v=try transact(request(op,old,target,id,operation),dir);try check(v["status"] as? String=="edited_verified" && v["calendar_writes"] as? Bool==false) }
        try check(editSaves==1 && EKEventStore.spans.allSatisfy { if case .thisEvent=$0 { return true };return false })
        // A later legitimate edit can proceed; earlier receipts remain recoverable.
        let old2=summary(e);var target2=old2;target2["title"]="Changed twice"
        let v2=try transact(request("update",old2,target2,try identity(e),String(repeating:"b",count:32)),dir)
        try check(v2["status"] as? String=="edited_verified" && editSaves==2)
        let recovered=try transact(request("recover_update",old,target,id,operation),dir);try check(recovered["status"] as? String=="edited_verified" && editSaves==2)
    }
    // Changed provider fields between preview and apply are never overwritten.
    do {
        let (e,dir,old,target)=try setup("changed");let id=try identity(e);e.notes="Externally changed"
        let v=try transact(request("update",old,target,id,operation),dir);try check(v["status"] as? String=="changed" && editSaves==0)
    }
    // Invitations are never modified or sent.
    do {
        let (e,dir,old,target)=try setup("attendee");e.hasAttendees=true
        let v=try transact(request("update",old,target,try identity(e),operation),dir);try check(v["status"] as? String=="unsupported" && editSaves==0)
    }
    // A failed/unknown save blocks any new operation, including a moved item.
    do {
        let (e,dir,old,target)=try setup("unknown");let id=try identity(e);editFail=true
        let v=try transact(request("update",old,target,id,operation),dir);try check(v["status"] as? String=="edit_unknown" && editSaves==1)
        editFail=false
        // This case models a save that failed without committing to the store.
        e.title=old["title"] as? String;e.startDate=iso.date(from:old["start"] as! String)!;e.endDate=iso.date(from:old["end"] as! String)!
        let r=try transact(request("recover_update",old,target,id,operation),dir);try check(r["status"] as? String=="edit_unknown" && editSaves==1)
        let current=summary(e);var other=current;other["title"]="Another edit"
        let second=try transact(request("update",current,other,try identity(e),String(repeating:"b",count:32)),dir)
        try check(second["status"] as? String=="edit_unknown" && editSaves==1)
    }
    do {
        let (e,dir,old,target)=try setup("late");let id=try identity(e);editFail=true
        let v=try transact(request("update",old,target,id,operation),dir);try check(v["status"] as? String=="edit_unknown")
        editFail=false
        let recovered=try transact(request("recover_update",old,target,id,operation),dir)
        try check(recovered["status"] as? String=="edited_verified" && editSaves==1 && recovered["calendar_writes"] as? Bool==false)
    }
    // Recurrence saves only this occurrence; new detached IDs are verified.
    do {
        let (e,dir,old,target)=try setup("recurring");e.recurrenceRules=[EKRecurrenceRule()];changeID=true
        let sibling=EKEvent();sibling.startDate=e.startDate.addingTimeInterval(7*86400);sibling.endDate=e.endDate.addingTimeInterval(7*86400);EKEventStore.pool.append(sibling)
        let v=try transact(request("update",old,target,try identity(e),operation),dir)
        try check(v["status"] as? String=="edited_verified" && editSaves==1 && e.eventIdentifier=="new-detached-id" && sibling.title=="Káva")
    }
    // Read-only recovery without a journal must never save.
    do {
        let (e,dir,old,target)=try setup("missing");let v=try transact(request("recover_update",old,target,try identity(e),operation),dir)
        try check(v["status"] as? String=="edit_unknown" && editSaves==0)
    }
    print("calendar edit native: PASS; real calendar access: false")
}
