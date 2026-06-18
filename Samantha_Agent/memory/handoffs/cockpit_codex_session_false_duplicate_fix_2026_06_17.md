Nazev: Cockpit - oprava falesne druhe Codex relace
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-17

Co se resilo:
Cockpit hlasil `Codex relace: 2 (limit 1)`, i kdyz skutecne bezela jen jedna
Samantha/Codex relace ve `screen` na `ttys000`. Mila spravne upozornil, ze vcera
jednu relaci zavrel a jednu otevrel, ale Cockpit porad ukazoval varovani.

Co je hotove:
- Read-only kontrola ukazala jednu realnou Codex relaci na `ttys000`.
- Procesy `node /usr/local/bin/codex` a vnorena binarka `vendor/.../codex` patri
  ke stejne relaci.
- Bug byl v detekci `discover_codex_ttys`: kdyz child Codex proces nasel TTY,
  ktere uz bylo v seznamu, pokracoval po rodicich az ke `screen` procesu na
  `ttys003` a vytvoril falesnou druhou relaci.
- Oprava zastavi hledani rodicu vzdy po nalezeni platneho TTY; pokud uz TTY
  bylo pridane, jen se neprida podruhe.
- Doplnen regresni test pro kombinaci `screen` + wrapper `node codex` + child
  `vendor/bin/codex`.
- Ziva kontrola po oprave vratila `ttys=['ttys000']`, `codex_tty_count=1` a
  voice bridge `status=ok`.
- Commit `c61c259 Fix false duplicate Codex session detection` byl pushnut na
  `origin/main`.
- Po restartu Codexu varovani v Cockpitu stale zustavalo, protoze bezici Cockpit
  server mel nacteny stary Python kod.
- Bezpecne byly restartovane obe Cockpit instance: lokalni `127.0.0.1:8770` i
  Tailscale `100.89.150.6:8770`.
- Po restartu obe `/api/status` kontroly hlasily `status=ok`,
  `codex_ttys=['ttys000']` a `Codex relace: 1 (limit 1)`.
- Mila nasledne potvrdil v UI: "Uz je to ok."

Co neni hotove:
- Cursorova testovaci CSS zmena v `MatysekANJ/web_mmtx/styles_intro_v2.css`
  zustava mimo tento commit a mimo tento handoff.

Dalsi krok:
Zadne dalsi kroky k tomuto incidentu nejsou potreba. Pri pristim podobnem
varovani nejdrive rozlisit restart Codexu od restartu Cockpit serveru.

Navrhovane dalsi kroky:
Okamzity:
- Pokracovat v rozdelane praci; stav voice bridge je potvrzeny jako OK.

Volitelne:
- Sjednotit Cockpit status i read-only panel `Codex relace` na jednu sdilenou
  presnou detekci, aby se podobne rozdily mezi rychlym a detailnim reportem
  nevracely.

Zmenene nebo relevantni soubory:
- `app/speech/terminal_bridge.py`
- `tests/test_terminal_bridge.py`
- `memory/handoffs/cockpit_codex_session_false_duplicate_fix_2026_06_17.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Neukladat do gitu zadny obsah `data/private/voice_inbox/`.
- Pri kontrole procesu pouzivat read-only vypisy; ukoncovani relaci jen pres
  potvrzovane workflow a nikdy neukoncovat aktualni `effective_tty`.
