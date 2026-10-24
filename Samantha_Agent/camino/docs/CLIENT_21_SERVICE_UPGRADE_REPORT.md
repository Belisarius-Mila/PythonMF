# Camino 21 a aktualizace služby

Stav: 2026-10-24 19:48 CEST. Míla výslovně zadal novou IPA, aktualizaci
služby a stejné aplikace na iPhonu; před provedením potvrdil přesnou globální
brzdu pro tento servisní přechod. Služba je aktualizovaná, build 21 nainstalovaný.

## Instalační balíček a telefon

- `Camino-Projects-Trash-21-20261024.ipa`, verze 0.1.0 (21), bundle ID `cz.pythonmf.camino.app`.
- Podepsaný iOS archive/export, strict codesign čisté exportované aplikace, ZIP/CRC a `project_trash_v1` v binárce PASS.
- 1072250 B; SHA-256 `f307048f0cd33b85c91dbe5a6a5a776b7af95444f246000cb49270be40ae1e54`. Zdroj `e7f2c598e8b82646ddabba24474674d56a725e89`; funkční kód odpovídá ověřenému `0a18db30`.
- Profil platí do 2026-10-29 19:01:14 UTC a zahrnuje připojený iPhone. Podpisové identity, profil a identifikátor zařízení zůstávají mimo Git.
- Create-only kopie v Downloads a iCloud Drive/Dokumenty; oba hashe shodné. iCloud metadata uploaded=true, uploading=false. Starší IPA zachované.
- Přímá CoreDevice aktualizace téže aplikace z buildu 20 na 21 PASS; následný dotaz potvrdil verzi a stejné bundle ID. Odinstalace neproběhla.
- Před prvním spuštěním zůstalo všech sedm původních položek Application Support/Camino; velikosti i lastModDate metadata.sqlite, WAL a SHM přesně shodné. Nejde o úplný hashový audit všech telefonních dat ani fyzickou přejímku.
- Historická složka Sync-before obsahovala pouze prázdný technický journal bez položek media/metadata; nic se neuklízelo.
- Spuštění přes CoreDevice odmítl zamčený telefon (Locked). Míla musí telefon odemknout, otevřít Camino a potvrdit své původní záznamy.
- SideStore evidenci přímá instalace neověřila. Pro další obnovu použít novou IPA 21, zachovat stejnou identitu a neodinstalovávat; dosavadní nastavení Customize AppID zapnuté a Append Team ID vypnuté.

## Provedený servisní přechod

1. Read-only preflight, migrace kopie v RAM a izolovaný import ve skutečném venv služby PASS; requirements beze změny.
2. Pod lifecycle zámkem registrované zastavení a ověřené uvolnění služby.
3. Registrovaný upgrade na immutable release `f00fcb1311a77d4c4066cb1fa43e375df077f693`, zachovaná původní konfigurace a LaunchAgent definice. Funkční zdroje shodné s ověřenou verzí koše.
4. Čtyři místní SQLite snapshoty metadata/media/owner-auth/reader-auth ověřené pomocí SHA-256 a quick_check; všechny původní tabulky přesně shodné.
5. Registrovaný start a migrace 3→4; `project_trash_v1` potvrzené, nové tabulky koše při přejímce prázdné. Poslední registrovaný status owned/running=true a owner health PASS.

Po přechodu jsou všechny původní tabulky čtyř DB a archiv shodné:
921 přijatých operací, 132 Momentů, 4 cesty, všech 316 originálů /
2 379 212 189 B se shodnými SHA-256. Identity, epochs, cursor, granty,
exports/reconciliation flags false a Serve zachované. Žádná skutečná cesta
ani média se nemazaly.

Owner HTTP/HTTPS a autentizace PASS, anonymní přístup 401. Viewer katalog,
deník, mapa a map-data HTTPS 200; fotografie, audio a video Range 206
(ověřený krátký úsek každého média). Cockpit seznam projektového koše OK,
bez žádostí.

Při zápisu průběhové účtenky po stopu odmítl create-only writer přepsání
souboru. Upgrade ještě nezačal; pokračování vyšlo z ověřeného zastaveného
stavu a použilo nové append-only účtenky. Stop se neopakoval.
Finder přidal desktopové extrakci metadata odmítaná strict codesign;
instalace proto použila čistou extrakci ověřené IPA v privátním `/private/tmp`
a podpis ověřený bezprostředně před instalací (existující postup LL-037).
IPA ani zdrojový kód se kvůli tomu neměnily.

Externí šifrovaná záložní jednotka nebyla připojená. Čtyři ověřené místní DB
snapshoty a původní release/config umožňují servisní obnovu; snapshot na
stejném SSD nenahrazuje nezávislou externí zálohu.

## Rozsah ověření a další krok

Cockpit byl již vydaný Lunou `b75c48be083a1f26e8e7296ccf5997de` do
`0a18db30` (2232 testů PASS, smoke 5/5). Nynější samostatný servisní krok
aktualizoval službu a telefon; nový p+n ani push dokumentace neproběhl.
Závěrečná statická brána a git diff --check PASS; zdrojový kód beze změny.

První další krok: odemknout a otevřít Camino, potvrdit původní cesty a
záznamy. Fyzický tok koše na syntetické cestě/filmu, skutečná sedmidenní
lhůta a uvolnění místa zůstávají NEOVĚŘENO. Praktická editace textu,
historie nahrávek, jejich koš, MP3/WAV a český hlas zůstávají otevřené.

Technické účtenky `service-upgrade-final.json`, `viewer-upgrade-check.json`,
`viewer-media-upgrade-check.json`, `phone-install.json`, `phone-app-after.json`,
`phone-preservation-check.json` a `phone-launch.json` jsou jen v ignorovaném
private vývojovém adresáři. Do Gitu nepatří profily, IPA, tokeny ani databáze.
