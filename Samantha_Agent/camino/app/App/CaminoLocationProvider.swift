import Combine
import CoreLocation
import Foundation

/// One-shot foreground fixes only; no track, background mode, geocoder or logs.
// CLLocationManager is created on the main run loop; its delegate uses that queue.
@MainActor final class CaminoLocationProvider: NSObject, ObservableObject, @preconcurrency CLLocationManagerDelegate {
    @Published private(set) var fix: LocalLocationFix?
    @Published private(set) var requesting = false
    @Published private(set) var authorization: CLAuthorizationStatus = .notDetermined
    private let manager = CLLocationManager()
    private var foreground = false
    private var timeout: Task<Void, Never>?

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
        authorization = manager.authorizationStatus
    }

    func setForeground(_ active: Bool) {
        foreground = active
        if active { refresh() }
        else { stopRequest() }
    }

    func enableOrRefresh() {
        guard foreground else { return }
        if manager.authorizationStatus == .notDetermined {
            manager.requestWhenInUseAuthorization()
        } else { refresh() }
    }

    func refresh() {
        authorization = manager.authorizationStatus
        guard foreground, authorized else { fix = nil; return }
        guard !requesting else { return }
        requesting = true
        manager.requestLocation()
        timeout = Task { [weak self] in
            try? await Task.sleep(for: .seconds(15))
            guard !Task.isCancelled else { return }
            self?.stopRequest()
        }
    }

    /// Capture never waits. A late fix is for a later Moment, never a backfill.
    func snapshot(at date: Date) -> LocalLocationFix? {
        authorization = manager.authorizationStatus
        let result = authorized ? usableFix(at: date) : nil
        refresh()
        return result
    }

    func status(at date: Date) -> String {
        switch authorization {
        case .notDetermined: return "GPS není zapnutá · záznam funguje i bez ní"
        case .denied, .restricted: return "GPS není povolená · povol ji v Nastavení iPhonu"
        default: break
        }
        if let fix = usableFix(at: date) {
            return fix.approximate ? "GPS připravená · přibližná poloha" : "GPS připravená"
        }
        return requesting ? "Zjišťuji GPS · záznam na ni nečeká" : "GPS není dostupná · obnov polohu"
    }

    private var authorized: Bool {
        authorization == .authorizedWhenInUse || authorization == .authorizedAlways
    }

    private func usableFix(at date: Date) -> LocalLocationFix? {
        guard let fix, fix.usable(at: Int64(date.timeIntervalSince1970 * 1_000)) else { return nil }
        return fix
    }

    private func stopRequest() {
        timeout?.cancel()
        timeout = nil
        manager.stopUpdatingLocation()
        requesting = false
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorization = manager.authorizationStatus
        if !authorized { fix = nil; stopRequest() }
        else if foreground { refresh() }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard foreground, requesting, authorized else { return }
        let now = Int64(Date().timeIntervalSince1970 * 1_000)
        fix = locations.reversed().compactMap { value -> LocalLocationFix? in
            let point = LocalLocationFix(latitude: value.coordinate.latitude,
                longitude: value.coordinate.longitude,
                measuredAtUTCMilliseconds: Int64(value.timestamp.timeIntervalSince1970 * 1_000),
                horizontalAccuracyMeters: value.horizontalAccuracy)
            return point.usable(at: now) ? point : nil
        }.first
        stopRequest()
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        stopRequest() // No private coordinates or raw platform errors in logs/UI.
    }
}
