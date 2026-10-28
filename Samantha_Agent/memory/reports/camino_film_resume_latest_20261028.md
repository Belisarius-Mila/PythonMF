# Camino — při otevření nabídnout poslední rozpracovaný film

Stav 2026-10-28 15:37 CET: publikované a nasazené do 03b9047f přes Terru;
fyzická přejímka výchozího výběru zůstává otevřená. Míla hlásil, že se po otevření nabízí starší film místo posledního
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
- Předpublikační kontrola v 15:14 CET: rychlá statická brána PASS, Cockpit
  tehdy podával původní HTML
  e9fdd86775febeaa2c24d4e1d9422af75f09cb4d58bae1664fdf85a4f57c0ee6
  při HTTP 200 a code_stamp b90aa847fa54ce76; oprava byla v té chvíli místní.

Další krok po dokončeném p+n pro project-camino → Cockpit: po uloženém
střihu obnovit stránku a ověřit novou výchozí nabídku, ruční výběr jiného
filmu, refresh bez samovolného přepnutí a nové otevření. Datum zdrojů se
nemá vydávat za čas poslední práce. Nasazení potvrzuje účtenka níže;
fyzická přejímka zůstává samostatná.

### 2026-10-28 15:37 CET — Terra p+n posledního rozpracovaného filmu dokončené

Hotovo:
- Cockpit podává opravenou střižnu s nabídkou posledního uloženého rozpracování napříč cestami. Aktuální HTML i serverová nabídka jsou živě ověřené; fyzická přejímka v prohlížeči zůstává otevřená.

Rozhodnutí:
- Míla výslovně zadal „Ok, terra p+n.“ Jeden registrovaný submit_release(wait=True) předal přesné dva commity a centrálně schválenou Terru 6.1/high; bez nativního pomocného agenta, změny modelu nebo retry.

Další krok:
- Po uloženém střihu obnovit Cockpit a ověřit poslední film po otevření, ruční volbu a opakované otevření.

Navrhované další kroky:
- Zachované dříve otevřené přejímky komentářů/importu a času vytvoření exportů.

Technický důkaz:
- Účtenka df3e2ff061892d509ed9a09c354af6d6 completed, push_state/deployment_state=confirmed, dva commity do 03b9047fb81a4c610fb097d7f8bad7f6e8cf18f2. Plná brána 2262 PASS / 381,8 s, smoke 5/5, protected_services_unchanged=true.
- Jedna kontrola Adama: GitHub/main 0/0 na vydaném headu před zápisem, health/HTML HTTP 200 a přesná shoda HTML SHA-256 d9c0bb7bb6c2b68f2be5203add479324757d7795f7bce51b14c7537695ed776c, code_stamp 693ef47d90d9a288. Živé resume_project patří povolené cestě a ověřenému filmovému katalogu; osobní identifikátory ani data nejsou v zápisu.
- Caller účtenku převzal; returned_to_adam=false nepotvrzuje automatický portálový návrat a není důvodem opakování. Předchozí 86 cílených testů PASS; browser/Safari/iPhone proklik NEOVĚŘENO. Následuje jen lokální výsledkový checkpoint, žádná další publikace.
