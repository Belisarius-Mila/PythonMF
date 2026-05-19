import Foundation

final class CSVStore {
    private let filename = "VocabularyFR.csv"

    func loadWords() throws -> [Word] {
        try ensureSeededCSV()
        let url = try documentsCSVURL()
        let data = try Data(contentsOf: url)
        guard let text = String(data: data, encoding: .utf8) ?? String(data: data, encoding: .windowsCP1250) else {
            return []
        }
        return parseCSV(text)
    }

    func saveWords(_ words: [Word]) throws {
        let header = ["FR", "CZ", "Order", "Sentence", "SentenceT", "L", "HT"]
        var lines = [header.joined(separator: ",")]
        for (i, w) in words.enumerated() {
            let row = [
                csvEscape(w.fr),
                csvEscape(w.cz),
                "\(i + 1)",
                csvEscape(w.sentence),
                csvEscape(w.sentenceT),
                w.learned ? "True" : "False",
                w.hard ? "True" : "False"
            ]
            lines.append(row.joined(separator: ","))
        }
        let out = lines.joined(separator: "\n")
        try out.write(to: documentsCSVURL(), atomically: true, encoding: .utf8)
    }

    private func ensureSeededCSV() throws {
        let target = try documentsCSVURL()
        if FileManager.default.fileExists(atPath: target.path) {
            return
        }
        guard let bundled = Bundle.main.url(forResource: "VocabularyFR", withExtension: "csv") else {
            let header = "FR,CZ,Order,Sentence,SentenceT,L,HT\n"
            try header.write(to: target, atomically: true, encoding: .utf8)
            return
        }
        try FileManager.default.copyItem(at: bundled, to: target)
    }

    private func documentsCSVURL() throws -> URL {
        let docs = try FileManager.default.url(
            for: .documentDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        return docs.appendingPathComponent(filename)
    }

    private func parseCSV(_ text: String) -> [Word] {
        let rows = parseCSVRows(text)
        guard !rows.isEmpty else { return [] }
        let header = rows[0]
        var ix: [String: Int] = [:]
        for (i, h) in header.enumerated() {
            ix[h.trimmingCharacters(in: .whitespacesAndNewlines)] = i
        }

        func field(_ row: [String], _ key: String) -> String {
            guard let i = ix[key], i < row.count else { return "" }
            return row[i]
        }

        return rows.dropFirst().map { row in
            Word(
                fr: field(row, "FR"),
                cz: field(row, "CZ"),
                sentence: field(row, "Sentence"),
                sentenceT: field(row, "SentenceT"),
                learned: isTrue(field(row, "L")),
                hard: isTrue(field(row, "HT"))
            )
        }
    }

    private func parseCSVRows(_ text: String) -> [[String]] {
        var rows: [[String]] = []
        var row: [String] = []
        var field = ""
        var inQuotes = false
        var i = text.startIndex

        while i < text.endIndex {
            let c = text[i]
            if c == "\"" {
                let next = text.index(after: i)
                if inQuotes, next < text.endIndex, text[next] == "\"" {
                    field.append("\"")
                    i = next
                } else {
                    inQuotes.toggle()
                }
            } else if c == ",", !inQuotes {
                row.append(field)
                field = ""
            } else if (c == "\n" || c == "\r"), !inQuotes {
                if c == "\r" {
                    let next = text.index(after: i)
                    if next < text.endIndex, text[next] == "\n" {
                        i = next
                    }
                }
                row.append(field)
                field = ""
                if !(row.count == 1 && row[0].isEmpty) {
                    rows.append(row)
                }
                row = []
            } else {
                field.append(c)
            }
            i = text.index(after: i)
        }

        if !field.isEmpty || !row.isEmpty {
            row.append(field)
            rows.append(row)
        }
        return rows
    }

    private func isTrue(_ s: String) -> Bool {
        let v = s.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        return v == "true" || v == "1" || v == "yes" || v == "ano"
    }

    private func csvEscape(_ s: String) -> String {
        if s.contains(",") || s.contains("\"") || s.contains("\n") || s.contains("\r") {
            return "\"" + s.replacingOccurrences(of: "\"", with: "\"\"") + "\""
        }
        return s
    }
}
