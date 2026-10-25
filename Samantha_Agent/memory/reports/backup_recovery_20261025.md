# Recovery záloha — 2026-10-25 14:53 CET

- Projektový snapshot: `20261025_142837` na šifrovaném svazku SamanthaSecureBackup.
- Zdrojový Git head: `e368753a1b069e7e21a59cfadddc458749a0ec8d`; zachycuje zdroje před tímto následným evidenčním zápisem.
- 63 143 souborů: 17 050 nově kopírovaných, 46 092 hardlinků, 1 symlink, 0 přeskočených; 4 309 588 279 nových B projektové části. Existující snapshoty zachované.
- Samostatné živé Camino: `20261025_143650-abf7e7e5`, 1 647 souborů / 5 167 041 733 B, čtyři SQLite databáze, přesný provozní release a soukromá konfigurace.
- Archiv Camina: 921 operací, 132 Momentů, 4 cesty a 316 originálů / 2379212189 B. Registrovaný běh ověřil všechny soubory SHA-256, databáze a mediální účtenky i shodu zmrazeného zdroje.
- Závěrečná kontrola: šifrovaný skutečně připojený cíl, manifesty a recovery karta PASS; čtyři DB quick_check PASS. Čtyři vybrané projektové SHA-256 shodné a tytéž soubory skutečně zrekonstruované do nového dočasného adresáře bez přepsání originálů.
- Obnovené testovací soubory: AGENTS.md, memory/MEMORY_INDEX.md, config/agent_roles.json a camino/app/Core/CaminoLocalStore.swift. Soukromá .env ověřená pouze shodou; žádné tajemství ani jeho hash se do tohoto zápisu nevypisuje.
- Codex auth.json a nouzové data/session_autosave ve snapshotu nejsou. Recovery obsahuje projekty a podporovaný rozsah Codex konfigurace/relací; nejde o obraz celého Macu, Klíčenky ani instalovaných aplikací.
- Camino znovu běží, owner HTTP/HTTPS PASS. Config a Serve otisky před/po shodné; Cockpit PID a code_stamp zachované. Zdrojová data, oprávnění a síť se zálohou neměnily.
- activity_state a backup_status potvrzují 2026-10-25; zpožděné upozornění je vyřešené. Na šifrovaném svazku po běhu přibližně 406 GiB volných.

## Obnova a hranice

Vyber dokončený projektový snapshot `20261025_142837` a jeho
backup_manifest.txt; ten odkazuje na odpovídající Camino supplement
`20261025_143650-abf7e7e5`. Podrobný TXT návod 1.2 obsahuje i starší
příklady 18./19. října; pro tuto zálohu mají přednost aktuální manifesty.
Nový projektový snapshot už obsahuje historii/kód až do e368753a,
samostatný starší doplněk kódu z 19. 10. kvůli němu není potřebný.

Zkouška souborové obnovy a kontrola databází prošly. Kompletní instalace
a fyzická přejímka náhradního Macu zůstávají samostatné. Soukromé manifesty,
inventáře, tokeny a databáze patří pouze do šifrovaného backupu; tento souhrn
je Git-safe. Zdrojový kód zálohování se neměnil, nové testy/publikace se
nespouštěly. Zápis výsledku tvoří následný lokální dokumentační checkpoint.
