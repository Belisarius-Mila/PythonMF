import Foundation

/// Control receipts only; a server deadline never authorizes a local-clock purge.
public struct LocalProjectTrash: Codable, Equatable, Identifiable, Sendable {
    public let id: UUID
    public let tripID: UUID
    public var name: String
    public var state: String
    public var serverID: UUID?
    public var epoch: UUID?
    public var purgeMilliseconds: Int64?
    public var momentIDs: Set<UUID>
    public var files: [CaminoErasureEntry]?

    public init(id: UUID = UUID(), tripID: UUID, name: String, state: String = "local_request",
                momentIDs: Set<UUID> = []) {
        self.id = id; self.tripID = tripID; self.name = name; self.state = state
        self.momentIDs = momentIDs
    }

    public var blocksProject: Bool { state != "restored" }
    public var statusText: String {
        switch state {
        case "local_request": "Čeká na spojení s Macem a potvrzení ve střižně."
        case "requested": "Čeká na tvoje potvrzení ve střižně na Macu."
        case "trashed": "Koš na 7 dní. Obnovení je možné ve střižně na Macu."
        case "purging", "compacting": "Mac dokončuje výmaz a uvolnění místa. Telefon zatím data uchovává."
        case "purged": "Mac potvrdil výmaz. Čeká na bezpečné dokončení v telefonu."
        case "phone_deleted": "Telefon smazán. Čeká na doručení potvrzení Macu."
        case "phone_ack": "Výmaz na Macu i v telefonu potvrzen."
        case "restored": "Obnoveno na Macu."
        default: "Stav výmazu vyžaduje ověření."
        }
    }
}

/// A persisted, restartable inventory within the application's own container.
public struct CaminoErasureEntry: Codable, Equatable, Sendable {
    public let relativePath: String
    public let directory: Bool
    public let device: UInt64
    public let inode: UInt64
    public let size: UInt64
    public let modified: Date
    public let links: UInt64

    private static func safe(_ relative: String, root: URL) throws -> URL {
        let result = root.appendingPathComponent(relative).standardizedFileURL
        let expected = root.resolvingSymlinksInPath().appendingPathComponent(relative).standardizedFileURL
        guard !relative.hasPrefix("/"), !relative.split(separator: "/").contains(".."),
              result.path.hasPrefix(root.standardizedFileURL.path + "/"),
              result.resolvingSymlinksInPath() == expected else { throw LocalStoreError.inconsistentStore }
        return result
    }

    private static func attributes(_ url: URL) throws -> [FileAttributeKey: Any]? {
        do { return try FileManager.default.attributesOfItem(atPath: url.path) }
        catch {
            let value = error as NSError
            if value.domain == NSCocoaErrorDomain && [NSFileNoSuchFileError, NSFileReadNoSuchFileError].contains(value.code) { return nil }
            throw error
        }
    }

    public static func inventory(root: URL, paths: [String]) throws -> [Self] {
        let fm = FileManager.default
        var result: [Self] = []
        func scan(_ relative: String, depth: Int) throws {
            guard depth <= 20, result.count < 100_000 else { throw LocalStoreError.inconsistentStore }
            let url = try safe(relative, root: root)
            guard let a = try attributes(url) else { return }
            let directory = a[.type] as? FileAttributeType == .typeDirectory
            guard directory || a[.type] as? FileAttributeType == .typeRegular,
                  let dev = a[.systemNumber] as? NSNumber, let ino = a[.systemFileNumber] as? NSNumber,
                  let size = a[.size] as? NSNumber, let date = a[.modificationDate] as? Date,
                  let links = a[.referenceCount] as? NSNumber else { throw LocalStoreError.inconsistentStore }
            result.append(Self(relativePath: relative, directory: directory, device: dev.uint64Value,
                inode: ino.uint64Value, size: size.uint64Value, modified: date, links: links.uint64Value))
            if directory {
                for name in try fm.contentsOfDirectory(atPath: url.path).sorted() {
                    try scan(relative + "/" + name, depth: depth + 1)
                }
            }
        }
        let roots = Set(paths)
        for path in roots.sorted() where !roots.contains(where: { path.hasPrefix($0 + "/") }) {
            try scan(path, depth: 0)
        }
        var counts: [String: UInt64] = [:]
        for item in result where !item.directory {
            counts["\(item.device):\(item.inode)", default: 0] += 1
        }
        for item in result where !item.directory {
            guard counts["\(item.device):\(item.inode)"] == item.links
            else { throw LocalStoreError.inconsistentStore }
        }
        return result
    }

    public static func remove(root: URL, entries: [Self]) throws {
        let fm = FileManager.default
        var remaining: [String: Int] = [:]
        for item in entries where !item.directory {
            let url = try safe(item.relativePath, root: root)
            if try attributes(url) != nil {
                remaining["\(item.device):\(item.inode)", default: 0] += 1
            }
        }
        for item in entries.sorted(by: { $0.relativePath.split(separator: "/").count > $1.relativePath.split(separator: "/").count }) {
            let url = try safe(item.relativePath, root: root)
            guard let a = try attributes(url) else { continue }
            guard (a[.systemNumber] as? NSNumber)?.uint64Value == item.device,
                  (a[.systemFileNumber] as? NSNumber)?.uint64Value == item.inode else {
                throw LocalStoreError.inconsistentStore
            }
            if item.directory {
                guard a[.type] as? FileAttributeType == .typeDirectory,
                      try fm.contentsOfDirectory(atPath: url.path).isEmpty else { throw LocalStoreError.inconsistentStore }
            } else {
                guard a[.type] as? FileAttributeType == .typeRegular,
                      (a[.size] as? NSNumber)?.uint64Value == item.size,
                      a[.modificationDate] as? Date == item.modified,
                      (a[.referenceCount] as? NSNumber)?.intValue == remaining["\(item.device):\(item.inode)"] else { throw LocalStoreError.inconsistentStore }
            }
            try fm.removeItem(at: url)
            if !item.directory { remaining["\(item.device):\(item.inode)", default: 0] -= 1 }
        }
    }
}
