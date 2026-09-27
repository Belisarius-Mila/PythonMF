import SwiftUI

struct CaminoLocationStatusView: View {
    @ObservedObject var location: CaminoLocationProvider

    var body: some View {
        TimelineView(.periodic(from: .now, by: 5)) { context in
            VStack(alignment: .leading, spacing: 6) {
                Label(location.status(at: context.date), systemImage: "location")
                    .font(.footnote)
                Button("Povolit / obnovit GPS") { location.enableOrRefresh() }
                    .disabled(location.requesting)
                    .accessibilityIdentifier("refreshLocation")
            }
        }
    }
}
