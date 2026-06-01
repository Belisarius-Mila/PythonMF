import Carbon
import Foundation

@_silgen_name("RunApplicationEventLoop")
func RunApplicationEventLoop() -> OSStatus

let projectDir = "/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent"
let scriptPath = "\(projectDir)/scripts/start_cockpit.sh"
let logPath = "\(projectDir)/data/private/cockpit/hotkey_agent.log"
let hotKeySignature = fourCharCode("SCHK")
let hotKeyId = UInt32(1)

func fourCharCode(_ value: String) -> OSType {
    var result: UInt32 = 0
    for scalar in value.unicodeScalars.prefix(4) {
        result = (result << 8) + UInt32(scalar.value)
    }
    return OSType(result)
}

func log(_ message: String) {
    let line = "\(Date()) \(message)\n"
    guard let data = line.data(using: .utf8) else {
        return
    }

    let url = URL(fileURLWithPath: logPath)
    if FileManager.default.fileExists(atPath: logPath),
       let handle = try? FileHandle(forWritingTo: url) {
        defer { try? handle.close() }
        try? handle.seekToEnd()
        try? handle.write(contentsOf: data)
    } else {
        try? data.write(to: url, options: .atomic)
    }
}

func openCockpit() {
    log("hotkey pressed; launching \(scriptPath)")
    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/bin/zsh")
    process.arguments = [scriptPath]
    process.currentDirectoryURL = URL(fileURLWithPath: projectDir)

    do {
        try process.run()
    } catch {
        log("launch failed: \(error)")
        fputs("Samantha Cockpit hotkey failed: \(error)\n", stderr)
    }
}

let handler: EventHandlerUPP = { _, event, _ in
    var eventHotKeyId = EventHotKeyID()
    let status = GetEventParameter(
        event,
        EventParamName(kEventParamDirectObject),
        EventParamType(typeEventHotKeyID),
        nil,
        MemoryLayout<EventHotKeyID>.size,
        nil,
        &eventHotKeyId
    )

    if status == noErr,
       eventHotKeyId.signature == hotKeySignature,
       eventHotKeyId.id == hotKeyId {
        openCockpit()
        return noErr
    }

    return OSStatus(eventNotHandledErr)
}

var eventType = EventTypeSpec(
    eventClass: OSType(kEventClassKeyboard),
    eventKind: UInt32(kEventHotKeyPressed)
)

let installStatus = InstallEventHandler(
    GetApplicationEventTarget(),
    handler,
    1,
    &eventType,
    nil,
    nil
)

if installStatus != noErr {
    log("handler install failed: \(installStatus)")
    fputs("Samantha Cockpit hotkey handler install failed: \(installStatus)\n", stderr)
    exit(1)
}

var hotKeyRef: EventHotKeyRef?
var eventHotKeyId = EventHotKeyID(signature: hotKeySignature, id: hotKeyId)
let registerStatus = RegisterEventHotKey(
    UInt32(kVK_ANSI_C),
    UInt32(controlKey | optionKey | cmdKey),
    eventHotKeyId,
    GetApplicationEventTarget(),
    0,
    &hotKeyRef
)

if registerStatus != noErr {
    log("hotkey registration failed: \(registerStatus)")
    fputs("Samantha Cockpit hotkey registration failed: \(registerStatus)\n", stderr)
    exit(1)
}

log("agent started; hotkey Ctrl+Option+Cmd+C registered")
print("Samantha Cockpit hotkey agent is running: Ctrl+Option+Cmd+C")
let loopStatus = RunApplicationEventLoop()
log("application event loop exited: \(loopStatus)")
