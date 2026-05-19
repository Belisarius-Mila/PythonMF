import Foundation
import AVFoundation

@MainActor
final class TrainerViewModel: NSObject, ObservableObject {
    @Published var words: [Word] = []
    @Published var currentWord: Word?
    @Published var currentIndex: Int?
    @Published var filterHT = false
    @Published var showTranslation = false
    @Published var remainingCount = 0
    @Published var autoRunning = false
    @Published var errorMessage: String?

    private let store = CSVStore()
    private let speaker = AVSpeechSynthesizer()
    private var shownInSelection = Set<Int>()
    private var selectionSignature = ""
    private var phase: AutoPhase = .idle

    private enum AutoPhase {
        case idle
        case speakingFR
        case speakingCZ
    }

    override init() {
        super.init()
        speaker.delegate = self
        configureAudioSession()
        load()
        nextWord()
    }

    func load() {
        do {
            words = try store.loadWords()
            recalcRemaining()
        } catch {
            errorMessage = "Naceni CSV selhalo: \(error.localizedDescription)"
        }
    }

    func nextWord() {
        stopAuto()
        advanceWord(speakFR: true)
    }

    func revealTranslation() {
        showTranslation = true
        guard let w = currentWord else { return }
        speak(text: w.sentence, lang: "fr-FR")
    }

    func toggleLearned(_ value: Bool) {
        guard let i = currentIndex, i < words.count else { return }
        words[i].learned = value
        save()
        recalcRemaining()
    }

    func toggleHard(_ value: Bool) {
        guard let i = currentIndex, i < words.count else { return }
        words[i].hard = value
        save()
        recalcRemaining()
    }

    func startAuto() {
        guard !autoRunning else { return }
        autoRunning = true
        phase = .idle
        runAutoStep()
    }

    func stopAuto() {
        autoRunning = false
        phase = .idle
        speaker.stopSpeaking(at: .immediate)
    }

    func speakCurrentFR() {
        guard let fr = currentWord?.fr else { return }
        speak(text: fr, lang: "fr-FR")
    }

    private func runAutoStep() {
        guard autoRunning else { return }
        advanceWord(speakFR: false)
        guard let w = currentWord else {
            stopAuto()
            return
        }
        showTranslation = false
        phase = .speakingFR
        speak(text: w.fr, lang: "fr-FR")
    }

    private func advanceWord(speakFR: Bool) {
        let indices = activeIndices()
        if indices.isEmpty {
            currentWord = nil
            currentIndex = nil
            remainingCount = 0
            return
        }

        let sig = "\(filterHT)|" + indices.map(String.init).joined(separator: ",")
        if sig != selectionSignature {
            selectionSignature = sig
            shownInSelection.removeAll()
        }

        var available = indices.filter { !shownInSelection.contains($0) }
        if available.isEmpty {
            shownInSelection.removeAll()
            available = indices
        }

        guard let chosen = available.randomElement() else { return }
        shownInSelection.insert(chosen)
        currentIndex = chosen
        currentWord = words[chosen]
        showTranslation = false
        recalcRemaining()

        if speakFR {
            speak(text: words[chosen].fr, lang: "fr-FR")
        }
    }

    private func recalcRemaining() {
        let indices = activeIndices()
        let total = indices.count
        if total == 0 {
            remainingCount = 0
            return
        }
        let seen = shownInSelection.filter { indices.contains($0) }.count
        remainingCount = seen >= total ? 0 : max(0, total - seen + 1)
    }

    private func activeIndices() -> [Int] {
        let base = words.indices.filter { !filterHT || words[$0].hard }
        let unlearned = base.filter { !words[$0].learned }
        return unlearned.isEmpty ? base : unlearned
    }

    private func save() {
        do {
            try store.saveWords(words)
        } catch {
            errorMessage = "Ulozeni CSV selhalo: \(error.localizedDescription)"
        }
    }

    private func speak(text: String, lang: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        let utterance = AVSpeechUtterance(string: trimmed)
        utterance.voice = AVSpeechSynthesisVoice(language: lang)
        utterance.rate = 0.46
        speaker.speak(utterance)
    }

    private func configureAudioSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playback, mode: .spokenAudio, options: [.mixWithOthers, .allowBluetooth])
            try session.setActive(true)
        } catch {
            errorMessage = "Audio session error: \(error.localizedDescription)"
        }
    }
}

extension TrainerViewModel: AVSpeechSynthesizerDelegate {
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in
            guard autoRunning else { return }
            guard let w = currentWord else { return }
            switch phase {
            case .speakingFR:
                phase = .speakingCZ
                showTranslation = true
                speak(text: w.cz, lang: "cs-CZ")
            case .speakingCZ:
                phase = .idle
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) { [weak self] in
                    guard let self = self else { return }
                    self.runAutoStep()
                }
            case .idle:
                break
            }
        }
    }
}
