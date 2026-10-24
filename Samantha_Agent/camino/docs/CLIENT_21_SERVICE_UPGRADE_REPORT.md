# Camino 21 a příprava aktualizace služby

Stav: 2026-10-24 19:24 CEST. Míla výslovně zadal dokončit novou IPA a aktualizaci služby.

## Hotový instalační balíček

- `Camino-Projects-Trash-21-20261024.ipa`, verze 0.1.0 (21), bundle ID `cz.pythonmf.camino.app`.
- Podepsaný iOS archive i export PASS; strict codesign exportované aplikace, ZIP/CRC a přítomnost `project_trash_v1` v binárce PASS.
- 1072250 B; SHA-256 `f307048f0cd33b85c91dbe5a6a5a776b7af95444f246000cb49270be40ae1e54`. Zdroj `e7f2c598e8b82646ddabba24474674d56a725e89`; žádná změna kódu nebo datového modelu oproti ověřenému koši.
- Profil platí do 2026-10-29 19:01:14 UTC. Podpisové identity, profil a zařízení zůstávají mimo Git.
- Create-only kopie v Downloads a iCloud Drive/Dokumenty; oba hashe shodné. iCloud metadata potvrzují uploaded=true, uploading=false. Starší IPA zachované.
- iPhone se po navázání spojení stal dostupným, potvrzená instalovaná verze 0.1.0 (20) se stejným bundle ID. Nová verze 21 nebyla instalovaná. Zachovat stávající aplikaci/data, neodinstalovávat; SideStore postup zachovává Customize AppID zapnuté a Append Team ID vypnuté.

## Připravený servisní krok

- Vlastněná služba je dostupná, owner HTTP 200, anonymní 401. Stávající schéma 3, projektový koš zatím nepodporuje. Exports/reconciliation flags false.
- Quick_check/FK a úplná kontrola SHA všech 316 originálů / 2 379 212 189 B PASS. Stav: 921 přijatých operací, 132 Momentů, 4 cesty. Soukromé identity a texty se neuvádějí.
- Přechod 3→4 na SQLite kopii v paměti PASS: všechny původní tabulky obsahově shodné, nové tabulky koše prázdné, quick_check/FK PASS. Živá databáze se neměnila.
- Izolovaný import aktuálního registrovaného release balíčku ve skutečném Pythonu služby PASS; requirements jsou byte-for-byte shodné. Serve a konfigurace mají uložené soukromé výchozí otisky.
- Externí šifrovaná záložní jednotka nyní není připojená. Před změnou se registrovaným upgradem po zastavení vytvoří ověřené místní SQLite snapshoty metadat, médií, owner auth a reader auth. Snapshot na stejném SSD nenahrazuje nezávislou externí zálohu.

## Čekající potvrzení a přesný další krok

Aktualizace služby přepíná její vlastněnou LaunchAgent definici. Podle
`memory/technical/global_safety_brake.md` vyžadují změny LaunchAgents přesnou
potvrzovací větu. Dřívější věta v tomto rozhovoru platila pro úklid SSD, ne
pro nynější servisní přechod. Živé stop/upgrade/start zatím neproběhly.

Po odpovídajícím potvrzení: registrovaný stop a vyčkání na uvolnění DB →
upgrade s ověřenými čtyřmi DB snapshoty a zachováním definice/config-before
→ start a migrace 3→4 → owner HTTP/HTTPS + auth + Viewer kontroly, shodné
původní řádky/identity/316 SHA a Serve → aktualizace stejné aplikace na
iPhonu bez odinstalace, ověření buildu 21 a zachování dat.

Novou IPA instalovat až po ověření kompatibilní služby. Celý fyzický tok
koše a ověření osobních záznamů v telefonu zůstávají NEOVĚŘENO.

Důkazy a podpisové soubory jsou pouze v ignorovaném private vývojovém
adresáři; do Gitu nepatří profily, IPA, tokeny ani soukromé databáze.
