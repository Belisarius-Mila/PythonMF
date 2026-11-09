# Propojení archivu hodinového agenta — 2026-11-09

Stav: lokálně připraveno, bez push/nasazení. Kanonická UI evidence: handoff a TVBCP `project-cockpit`; e-mailový kontext v `email_readonly_oauth.md` a existujícím kontinuálním handoffu. Nový TVBCP nevzniká.

## Příčina a změna

Potvrzená archivace agentem ukládá do samostatného soukromého archivu. Stránka Archiv četla jen klasický archiv, proto správně uložená zpráva nebyla vidět. Reader nyní ve výchozím nastavení čte oba pevné kořeny. Výslovně dodané jiné kořeny zůstávají izolované.

Seznam, hledání, detail, text zprávy, originál a vložené přílohy používají společné rozlišení. Klasické reference se nemění; agent má oddělený namespace. Kolize ID se odmítají, metadata se před čtením kontrolují proti symlinkům a povolenému kořeni. Přílohy agenta pocházejí z uloženého EML; historické externí dokumenty se nepřipojují pouze podle UID schránky.

Writer, uložené zprávy, účtenky, stav hodinového agenta a Pushcut se nemění. Žádná migrace, opakované ukládání nebo nové odesílání.

## Ověření

- 30 cílených testů PASS: původní kontrakty, dvě úložiště, chybějící klasický kořen, izolovaný vlastní kořen, společné řazení/limit/hledání, stabilita starých odkazů, kolize, ochrana cest a symlinků, oddělení UID a nezměněné soubory.
- Syntetický HTTP test přes skutečné routy: seznam obou zdrojů → detail → PDF a originál, správné typy a soukromé bezpečnostní hlavičky.
- Skutečné již uložené vyúčtování: nalezené v novém společném seznamu, text detailu dostupný, jedna vložená PDF příloha čitelná. Otisky všech souborů jeho archivu před/po shodné. Bez výpisu obsahu, identifikátorů či adres.
- Závěrečná statická brána PASS: `logs/email_archive_bridge_static_20261109.log`.
- Cílený log: `logs/email_archive_bridge_targeted_20261109.log`.
- Plná brána: 3296 testů OK (31 SKIP), 587,906 s unit testů; `logs/email_archive_bridge_full_gate_20261109.log`.

## Rizika a další krok

Lokální ověření není nasazení. Běžící Cockpit opravu dosud neobsahuje; další krok je samostatně autorizované p+n, následně ověřit zobrazení a otevření PDF na Macu/iPhonu. Samotná archivace zprávy nenahrazuje samostatný import PDF do knihovny Dokumenty.

Dřívější read-only kontrola Pushcut našla přijetí oznámení poskytovatelem HTTP 200; zobrazení na telefonu tím není potvrzené. Další hodinový souhrn neměl důležitou zprávu a upozornění záměrně nevytvořil. Žádný nový test ani resend neproběhl.
