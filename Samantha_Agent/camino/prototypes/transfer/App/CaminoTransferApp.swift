import SwiftUI
import UIKit

@main struct CaminoTransferApp: App {
    @UIApplicationDelegateAdaptor(TransferAppDelegate.self) private var appDelegate
    @StateObject private var model = TransferViewModel.shared
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            TransferScreen(model: model)
                .onChange(of: scenePhase) { _, phase in
                    if phase == .active { model.applicationBecameActive() }
                }
        }
    }
}

final class TransferAppDelegate: NSObject, UIApplicationDelegate {
    @MainActor private static var backgroundCompletionHandler: (() -> Void)?

    func application(
        _ application: UIApplication,
        handleEventsForBackgroundURLSession identifier: String,
        completionHandler: @escaping () -> Void
    ) {
        Self.backgroundCompletionHandler = completionHandler
        TransferViewModel.shared.reconnectBackgroundSession(identifier: identifier)
    }

    @MainActor static func finishBackgroundEvents() {
        let handler = backgroundCompletionHandler
        backgroundCompletionHandler = nil
        handler?()
    }
}

struct TransferScreen: View {
    @ObservedObject var model: TransferViewModel

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Label("Pouze syntetický test", systemImage: "lock.shield.fill")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Text("Camino Transfer C02b")
                        .font(.title2.bold())
                    Text("Samostatná testovací aplikace. Nečte Camino Audio, Fotky ani osobní média.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    configurationCard
                    transferCard
                    explanationCard
                }
                .padding()
            }
            .navigationTitle("Camino Transfer")
            .background(Color(.systemGroupedBackground))
        }
    }

    private var configurationCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Soukromý přijímač").font(.headline)
            TextField("https://…/camino-c02b", text: $model.serverURL)
                .textInputAutocapitalization(.never)
                .keyboardType(.URL)
                .textContentType(.URL)
                .autocorrectionDisabled()
                .accessibilityIdentifier("serverURL")
            SecureField(
                model.tokenStored ? "Token je uložen v Keychain" : "Bearer token",
                text: $model.tokenInput
            )
            .textContentType(.password)
            .accessibilityIdentifier("bearerToken")
            Button("Uložit soukromou konfiguraci") { model.saveConfiguration() }
                .buttonStyle(.bordered)
                .accessibilityIdentifier("saveConfiguration")
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18))
    }

    private var transferCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(model.statusText)
                .font(.title3.bold())
                .accessibilityIdentifier("transferStatus")
            Text(model.detailText)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .accessibilityIdentifier("transferDetail")
            if let journal = model.journal {
                ProgressView(value: model.progress)
                    .accessibilityIdentifier("transferProgress")
                    .accessibilityLabel("Odesláno \(Int(model.progress * 100)) procent bytů")
                Text("\(Int(model.progress * 100)) % bytů · části \(journal.acceptedChunks.count)/\(journal.chunkCount) · připraveno \(model.preparedCount)/2")
                    .font(.system(.caption, design: .monospaced))
                Toggle(
                    "Povolit mobilní data jen této dávce",
                    isOn: Binding(
                        get: { model.cellularAllowed },
                        set: { value in Task { await model.setCellularAllowed(value) } }
                    )
                )
                .disabled(journal.phase == .verified)
                .accessibilityIdentifier("cellularBatchGrant")
            }

            Button("Vytvořit novou syntetickou dávku 96 MiB") {
                Task { await model.createSyntheticBatch() }
            }
            .buttonStyle(.borderedProminent)
            .disabled(!model.canCreateBatch)
            .accessibilityIdentifier("createSyntheticBatch")

            if model.canSynchronize {
                Button("Synchronizovat nyní", systemImage: "arrow.triangle.2.circlepath") {
                    Task { await model.synchronize() }
                }
                .buttonStyle(.borderedProminent)
                .accessibilityIdentifier("synchronizeNow")
            }
            if model.canPause {
                Button("Pozastavit") { Task { await model.pause() } }
                    .buttonStyle(.bordered)
                    .accessibilityIdentifier("pauseTransfer")
            } else if model.canResume {
                Button("Pokračovat") { Task { await model.resume() } }
                    .buttonStyle(.borderedProminent)
                    .accessibilityIdentifier("resumeTransfer")
            }
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18))
    }

    private var explanationCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Pravdivé stavy").font(.headline)
            Text("100 % bytů znamená Ověřuji. Ověřeno na Macu se ukáže až po serverové kontrole celkové délky a SHA-256.")
            Text("Po nuceném ukončení aplikace se nic neslibuje: po dalším otevření se fronta znovu porovná se serverem.")
            Text("Při nedostupném tailnetu aplikace čeká. Veřejný alternativní upload není k dispozici.")
        }
        .font(.footnote)
        .foregroundStyle(.secondary)
    }
}
