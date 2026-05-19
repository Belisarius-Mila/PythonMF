import Foundation

struct Word: Identifiable, Equatable {
    let id = UUID()
    var fr: String
    var cz: String
    var sentence: String
    var sentenceT: String
    var learned: Bool
    var hard: Bool
}
