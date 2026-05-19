# Info.plist additions

Do `Info.plist` pridej:

1. Klic `UIBackgroundModes` (Array)
- polozka `audio`

V Xcode to vypada jako:
- `Required background modes`
  - `App plays audio`

To je nutne pro prehravani TTS pri zamcene obrazovce.

## Doporuceni
- Testuj na fyzickem iPhonu, ne na simulatoru.
- V `Signing & Capabilities` neni treba zvlastni entitlement, staci `UIBackgroundModes`.
