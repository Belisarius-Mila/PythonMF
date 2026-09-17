import SwiftUI
import AVFAudio

@main struct CaminoAudioApp: App {
    var body: some Scene { WindowGroup { AudioScreen() } }
}

struct AudioScreen: View {
    @StateObject private var model = AudioViewModel()
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    Label("Jen v tomto telefonu", systemImage: "lock.fill")
                        .font(.subheadline).foregroundStyle(.secondary)
                    Text("Audio prototyp C01c")
                        .font(.title2.bold())
                    Text("Spusť nahrávání před zamčením. Camino průběžně uzavírá obnovitelné části; při hovoru, změně mikrofonu nebo pádu se samo znovu nerozběhne.")
                        .font(.subheadline).foregroundStyle(.secondary)
                    if let c = model.controller {
                        Picker("Typ nahrávky", selection: $model.kind) {
                            ForEach(RecordingKind.allCases, id: \.self) { Text($0.rawValue).tag($0) }
                        }
                        .pickerStyle(.segmented).disabled(!c.canStart)
                        VStack(alignment: .leading, spacing: 14) {
                            Text(c.message).font(.headline)
                                .accessibilityIdentifier("captureStatus")
                            if c.phase == .playing {
                                Text("\(duration(c.playbackElapsed)) / \(duration(c.playbackDuration))")
                                    .font(.system(.title, design: .monospaced).bold())
                                    .accessibilityIdentifier("playbackTime")
                                    .accessibilityLabel("Přehráno \(duration(c.playbackElapsed)) z \(duration(c.playbackDuration))")
                                ProgressView(value: c.playbackProgress)
                                    .tint(.blue)
                                    .accessibilityIdentifier("playbackProgress")
                                    .accessibilityLabel("Průběh přehrávání")
                            } else {
                                Text(duration(c.elapsed)).font(.system(.largeTitle, design: .monospaced).bold())
                                    .accessibilityLabel("Délka aktuální části \(duration(c.elapsed))")
                                Text("Aktuální část").font(.caption).foregroundStyle(.secondary)
                                Text(c.input).font(.subheadline)
                                ProgressView(value: meter(c.power))
                                    .tint(c.phase == .recording ? .red : .secondary)
                                    .accessibilityLabel("Úroveň mikrofonu")
                            }
                            if c.canStop {
                                Button { Task { await c.stop() } } label: {
                                    Label("Ukončit a uložit", systemImage: "stop.fill")
                                        .frame(maxWidth: .infinity).padding(.vertical, 12)
                                }.buttonStyle(.borderedProminent).tint(.red)
                            } else if c.phase == .interrupted {
                                Button("Pokračovat", systemImage: "mic.fill") {
                                    Task { await c.continueRecording() }
                                }.buttonStyle(.borderedProminent).disabled(!c.canContinue)
                                Button("Ukončit nahrávání") { c.endInterruptedSession() }
                                    .buttonStyle(.bordered)
                            } else if c.phase == .playing {
                                Button("Zastavit přehrávání", systemImage: "stop.fill") { c.stopPlayback() }
                                    .buttonStyle(.borderedProminent)
                            } else {
                                Button { Task { await c.start(kind: model.kind) } } label: {
                                    Label("Start", systemImage: "mic.fill")
                                        .frame(maxWidth: .infinity).padding(.vertical, 12)
                                }.buttonStyle(.borderedProminent).disabled(!c.canStart)
                            }
                            if c.microphoneDenied {
                                Button("Otevřít nastavení aplikace") {
                                    if let url = URL(string: UIApplication.openSettingsURLString) {
                                        UIApplication.shared.open(url)
                                    }
                                }
                            }
                        }.padding().background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20))

                        Text("Uložené nahrávky").font(.title3.bold())
                        if c.library.clips.isEmpty {
                            Text("První krátký záznam se objeví tady.").foregroundStyle(.secondary)
                        }
                        if c.library.unfinishedCount > 0 {
                            Label("Neověřené nebo neúplné záznamy: \(c.library.unfinishedCount). Zůstaly zachované.",
                                  systemImage: "exclamationmark.triangle")
                                .font(.subheadline).foregroundStyle(.orange)
                        }
                        ForEach(c.library.sessions) { session in
                            VStack(alignment: .leading, spacing: 8) {
                              if let first = session.parts.first {
                                Text(first.draft.kind.rawValue).font(.headline)
                                Text(first.draft.startedAt, format: .dateTime.day().month().hour().minute())
                                    .font(.subheadline).foregroundStyle(.secondary)
                              }
                              ForEach(Array(session.parts.enumerated()), id: \.element.id) { index, clip in
                                if session.parts.count > 1 { Text("Část \(index + 1)").font(.subheadline.bold()) }
                                if let continuation = clip.draft.continuation {
                                    Text(continuation.gapSeconds.map { "Pauza před pokračováním: přibližně \(duration($0))" }
                                         ?? "Pauza před pokračováním: délka neznámá")
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                                if clip.recovery?.recoveredAfterCrash == true {
                                    Label("Obnovená částečná nahrávka · konec může chybět",
                                          systemImage: "exclamationmark.triangle.fill")
                                        .font(.subheadline).foregroundStyle(.orange)
                                }
                                if let segments = clip.segments, segments.count > 1 {
                                    Text("Obnovitelné části: \(segments.count)")
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                                if clip.segments?.contains(where: { $0.discontinuityBefore }) == true {
                                    Text("Mezi zachovanými částmi je neověřená mezera.")
                                        .font(.caption).foregroundStyle(.orange)
                                }
                                Text("\(duration(clip.audio.duration)) · \(clip.recovery != nil ? "Zachovaný přehratelný rozsah" : (clip.interrupted ? "Přerušený záznam" : "Uloženo v telefonu"))")
                                    .font(.subheadline)
                                Button("Přehrát", systemImage: "play.fill") { c.play(clip) }
                                    .buttonStyle(.bordered).disabled(!c.canPlay)
                              }
                            }.frame(maxWidth: .infinity, alignment: .leading)
                                .padding().background(.quaternary, in: RoundedRectangle(cornerRadius: 16))
                        }
                    } else { Text(model.startupError ?? "Úložiště není dostupné.").foregroundStyle(.red) }
                }.padding()
            }.navigationTitle("Camino Audio")
                .background(Color(.systemGroupedBackground))
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active { model.controller?.enterForeground() }
            else { model.controller?.leaveForeground() }
        }
    }

    private func duration(_ value: Double) -> String {
        let seconds = value.isFinite ? max(0, Int(value)) : 0
        return String(format: "%02d:%02d", seconds / 60, seconds % 60)
    }
    private func meter(_ power: Float) -> Double { min(1, max(0, Double((power + 60) / 60))) }
}
