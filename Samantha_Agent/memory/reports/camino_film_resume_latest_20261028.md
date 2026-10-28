# Camino — při otevření nabídnout poslední rozpracovaný film

Stav 2026-10-28 15:14 CET: lokální oprava; bez nového push nebo nasazení
Cockpitu. Míla hlásil, že se po otevření nabízí starší film místo posledního
rozpracování.

## Příčina a výsledné chování

Knihovna upřednostňovala výběr ze sessionStorage nebo konfigurační výchozí
cestu. Katalog navíc řadil filmy podle dne jejich zdrojů, nikoli podle
posledního uložení střihu. Datum pořízení tedy zastupovalo čas práce.

Katalog nyní uvádí last_edited_ms z existujícího souboru poslední uložené
revize, u dosud neupravovaného filmu z project-r1.json. Seznam filmů řadí
podle této hodnoty. Čtení, přehrávání či dokončený export čas střihu nemění.
Nezavádí se nový trvalý ukazatel, migrace ani přepis starých revizí.

Owner API /api/camino/film/trips doplňuje resume_project: identitu cesty,
filmu, den a čas uložené revize. Nejprve porovná pouze metadata uložených
revizí; potom ověřuje kandidáty od nejnovějšího do nalezení platného filmu.
Neprochází exportní úlohy všech ostatních filmů. Platnost manifestu,
současná oprávnění, koš, zdroje a textové/hlasové vazby se dál ověřují.
Neověřitelný nebo nyní soukromý film se jako nabídka návratu nepoužije.

Při novém otevření má tento ověřený film přednost před starou volbou karty
i konfigurační výchozí cestou, také napříč cestami. Když už uživatel pracuje,
obnovení přehledu ponechá právě vybraný film. Po skutečném zavření se výběr
při dalším otevření znovu vyhodnotí. Dosavadní ochrany rozpracovaného střihu,
pozdních odpovědí a potvrzení vstupů zůstávají zachované.

Pokud žádný uložený platný film není, zůstává dosavadní volba cesty/dne.
Nejde o nové uzavření vstupů, vytvoření filmu nebo automatický render.

## Ověření

- Nové backendové regrese nejdřív na původním kódu reprodukovaly nesprávné
  řazení a chybějící nabídku návratu. Finálně 86 testů PASS / 31,137 s:
  test_camino_film_editor, test_camino_mac_film a test_cockpit_frontend.
- Ověřený starší den uložený později, přesun výchozí nabídky mezi dvěma
  cestami se stejnými názvy a dny, vynechání nyní soukromého filmu, prázdný
  archiv, zachované bajty/mtime, nezměněné časy po renderu a žádný scan
  cizích renderových úloh při hledání nabídky návratu.
- Node ověřuje přednost ověřené serverové nabídky před starým uloženým
  výběrem, ruční volbu a dirty střih při refreshi, nové vyhodnocení po
  zavření/otevření a odmítnutí nabídky mimo ověřený seznam cest. Původní
  regrese pozdních odpovědí a samostatných karet nadále procházejí.
- Kontrolní čtení aktuálních dat novým místním kódem našlo platný film;
  0,771 s první a 0,027 s opakované volání. Jde o serverovou čtecí operaci,
  nikoli čas celé stránky. Do tohoto zápisu se nekopírují soukromá jména,
  identifikátory, obsahy střihů ani jejich data.
- Očekávaný frontendový otisk aktualizovaný po kontrole skutečné změny:
  636202 znaků, 11945 řádků, SHA-256
  d9c0bb7bb6c2b68f2be5203add479324757d7795f7bce51b14c7537695ed776c.
- Skutečný browser/Safari/iPhone NEOVĚŘENO. CUA inventory nemá připojený
  prohlížeč. Existující osobní střihy a média se při opravě nepřepisovala.
- Rychlá statická brána PASS. Živý Cockpit stále podává původní HTML
  e9fdd86775febeaa2c24d4e1d9422af75f09cb4d58bae1664fdf85a4f57c0ee6
  při HTTP 200 a code_stamp b90aa847fa54ce76; nová oprava je zatím místní.

Další krok: samostatné p+n pro project-camino → Cockpit, potom po uloženém
střihu obnovit stránku a ověřit novou výchozí nabídku, ruční výběr jiného
filmu, refresh bez samovolného přepnutí a nové otevření. Datum zdrojů se
nemá vydávat za čas poslední práce. Nasazení ani fyzická přejímka se tímto
lokálním checkpointem nepotvrzují.
