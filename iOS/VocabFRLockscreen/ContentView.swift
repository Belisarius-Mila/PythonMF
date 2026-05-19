import SwiftUI

struct ContentView: View {
    @StateObject private var vm = TrainerViewModel()

    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Toggle("HT only", isOn: $vm.filterHT)
                    .onChange(of: vm.filterHT) { _ in
                        vm.nextWord()
                    }
                Spacer()
                Text("Zbyva: \(vm.remainingCount)")
                    .font(.headline)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.yellow.opacity(0.6))
                    .cornerRadius(8)
            }

            RoundedRectangle(cornerRadius: 12)
                .fill(Color.gray.opacity(0.2))
                .frame(height: 150)
                .overlay(Text("Picture").foregroundColor(.gray))

            HStack {
                Text(vm.currentWord?.fr ?? "Hotovo")
                    .font(.system(size: 34, weight: .bold))
                Spacer()
                Button(action: vm.speakCurrentFR) {
                    Image(systemName: "speaker.wave.2.fill")
                        .font(.title2)
                }
            }
            .padding()
            .background(Color.white)
            .cornerRadius(12)

            Button(action: vm.revealTranslation) {
                Text(vm.showTranslation ? (vm.currentWord?.cz ?? "") : "UKAZAT PREKLAD")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(Color.blue)
                    .cornerRadius(12)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text(vm.showTranslation ? (vm.currentWord?.sentence ?? "") : "")
                    .font(.system(size: 18, weight: .bold))
                    .frame(maxWidth: .infinity, alignment: .leading)
                Text(vm.showTranslation ? (vm.currentWord?.sentenceT ?? "") : "")
                    .font(.system(size: 16))
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(12)
            .frame(maxWidth: .infinity, minHeight: 130, alignment: .topLeading)
            .background(Color.white)
            .cornerRadius(12)

            HStack {
                VStack(alignment: .leading, spacing: 10) {
                    Toggle("Nauceno", isOn: Binding(
                        get: { vm.currentWord?.learned ?? false },
                        set: { vm.toggleLearned($0) }
                    ))
                    Toggle("Tezky (HT)", isOn: Binding(
                        get: { vm.currentWord?.hard ?? false },
                        set: { vm.toggleHard($0) }
                    ))
                }
                Spacer()
                VStack(spacing: 8) {
                    Button("Auto") { vm.startAuto() }
                        .font(.system(size: 16, weight: .bold))
                        .frame(width: 84, height: 36)
                        .background(Color.orange)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                    Button("Fin") { vm.stopAuto() }
                        .font(.system(size: 16, weight: .bold))
                        .frame(width: 84, height: 36)
                        .background(Color.gray)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
            }

            Button(action: vm.nextWord) {
                Text("DALSI SLOVICKO")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .background(Color.green)
                    .cornerRadius(16)
            }
        }
        .padding()
        .background(Color(UIColor.systemGray6))
        .alert("Chyba", isPresented: Binding(
            get: { vm.errorMessage != nil },
            set: { if !$0 { vm.errorMessage = nil } }
        )) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(vm.errorMessage ?? "")
        }
    }
}
