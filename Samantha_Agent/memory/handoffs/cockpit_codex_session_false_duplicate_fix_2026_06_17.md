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

Co neni hotove:
- Bežici Cockpit muze mit stary Python kod nacteny v pameti; aby se oprava
  projevila v UI, je potreba bezpecny restart Cockpitu.
- Cursorova testovaci CSS zmena v `MatysekANJ/web_mmtx/styles_intro_v2.css`
  zustava mimo tento commit a mimo tento handoff.

Dalsi krok:
Po commitu/pushi udelat bezpecny restart Cockpitu a v UI zkontrolovat, ze radek
voice bridge ukazuje `Codex relace: 1 (limit 1)` bez varovani.

Navrhovane dalsi kroky:
Okamzity:
- Restartovat Cockpit pres existujici bezpecny restart workflow.

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
