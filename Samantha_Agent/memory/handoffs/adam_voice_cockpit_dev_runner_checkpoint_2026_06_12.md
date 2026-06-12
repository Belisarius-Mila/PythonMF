Nazev: Adam Voice / Cockpit approval visibility and Dev runner checkpoint
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-12

Co se resilo:
- Vzdaleny iPhone/SSH provoz narazel na to, ze Codex muze cekat na systemove
  potvrzeni mimo sandbox, ale Mila to z Cockpitu nevidel a nemohl pohodlne
  pokracovat.
- Nejde jen o read-only stavove kontroly; hlavni problem je vyvojova smycka:
  navrhovani toolu, upravy kodu, testy, syntax check, restart Cockpitu, endpoint
  smoke testy a opakovane ladeni.
- Interni Codex approval tlacitko zatim Cockpit neumi zmacknout, takze reseni je
  minimalizovat situace, kdy se Codex approval vubec objevi, a presunout caste
  bezpecne kroky do pevne povolenych Cockpit akci.

Co je hotove:
- Cockpit zobrazuje runtime kartu `Codex čeká na potvrzení` z
  `data/private/voice_inbox/codex_approval_request.json`.
- Karta ma nove tlacitko `Vyčistit kartu` a backend endpoint
  `/api/voice-mode/codex-approval/clear`.
- Vycištění karty je jen uklid runtime stavu po rucnim vyreseni nebo zruseni;
  neklika za Milu na interni Codex systemove povoleni.
- V sekci `Hlas -> Technické nastavení` je panel `Bezpečné kontroly` s pevnym
  read-only allowlistem:
  - `Codex relace`
  - `Voice bridge`
  - `Git stav`
  - `Záloha`
- Backend endpointy:
  - `GET /api/voice-mode/safe-readonly`
  - `POST /api/voice-mode/safe-readonly/run`
- V sekci `Servis` je novy panel `Vývojový runner` pro opakovane vyvojove kroky
  bez volneho shellu:
  - `Testy Cockpit + voice`
  - `Python syntax`
  - `Diff check`
- Backend endpointy:
  - `GET /api/dev-runner/actions`
  - `POST /api/dev-runner/run`
- Dev runner spousti jen registrovana ID z allowlistu, ne prijaty shell text.
- Lokální i Tailscale Cockpit byly restartovane a live endpointy otestovane.
- Live testy:
  - `Codex relace` pres lokalni i Tailscale Cockpit vratily jednu relaci
    `ttys000` a efektivni voice bridge cil `ttys000`.
  - `Diff check` pres lokalni i Tailscale Dev runner prosel.
  - `Python syntax` pres Dev runner prosel; ukazuje jen stary znamy
    `SyntaxWarning` v HTML stringu.
- Cílene testy po implementaci prosly: `185 tests OK`.

Co neni hotove:
- Cockpit stale neumi zmacknout interni Codex systemove approval tlacitko.
- Dev runner zatim neumi commit/push workflow; to ma byt samostatna specialni
  kategorie s prehledem staged souboru a potvrzenim.
- Dev runner zatim nema job historii ani dlouhe logovani mimo odpoved endpointu.
- Neni jeste samostatny UI prehled poslednich behu Dev runneru.
- Neni jeste pridana sada pro dalsi projekty mimo Cockpit/voice.

Dalsi krok:
- Rucne v iPhone/Tailscale Cockpitu otevrit `Servis -> Vývojový runner` a
  kliknout `Diff check`, `Python syntax` a podle potreby `Testy Cockpit + voice`.
- Pokud se v praxi osvedci, doplnit dalsi pevne akce pro beznou ladici smycku:
  endpoint smoke check, cockpit status snapshot, pripadne commit/push preview.

Navrhovane dalsi kroky:
- Okamzite: commitnout a pushnout aktualni checkpoint.
- Pak: doplnit Dev runner akci pro `tests.test_cockpit` samostatne nebo pro
  rychly smoke test endpointu, pokud `Testy Cockpit + voice` bude na iPhonu moc
  pomale.
- Potom: navrhnout specialni `Commit + push` workflow jako L2 akci: zobrazit
  presne staged soubory, commit message a vyzadovat potvrzeni.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/technical/codex_remote_approval_notice.md`
- `scripts/codex_approval_notice.py`

Bezpecnost / neukladat:
- Runtime soubor `data/private/voice_inbox/codex_approval_request.json` je mimo
  git a nema se commitovat.
- Dev runner nesmi prijimat volny shell prikaz z UI.
- Read-only allowlist nesmi cist tajemstvi, cele private dokumenty ani e-maily.
- Commit/push je povazovan za samostatnou L2 kategorii, ne obycejny read-only
  krok.
