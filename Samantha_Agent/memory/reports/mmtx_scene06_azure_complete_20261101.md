# MMTX scéna 6: dokončené audio přes Azure

Datum: 2026-11-01
Pracovní proud: project-mmtx
Běh: 2026-11-01 22:17:32 až 22:28:07 CET

## Výsledek

- Míla přijal šest hlasových ukázek a výslovně zadal pokračování.
- Místně hotovo **144/144 stop**: 72 anglických a 72 českých. Chybí 0.
- Přibylo 128 Azure MP3, 128 úspěšných a unikátních požadavků; přesně 5 870 účtovaných znaků. Limit běhu 10 000 znaků, žádný automatický retry nebo přepnutí poskytovatele.
- Původních 16 MP3 i jejich účtenky zůstaly přesně shodné. Zachované jsou také všechny ostatní původní soubory scény kromě očekávaného rozšíření audio manifestu a vazeb.
- Každá stopa odpovídá původnímu textu, hlasu, tempu -10 % a SHA-256. Zdrojová scéna a mirror mají přesně shodnou množinu souborů a bajty.
- Klíč zůstává pouze v místní konfiguraci mimo Git a v transientním stdin konfigurace curl. Není ve webové aplikaci ani v projektovém zápisu.

## Ověření

- Offline `build_scene06_audio.py --check`: Audio 144/144; chybí 0, exit 0. Všech 144 MP3 dekódováno.
- Po generování 4 testy skutečného JavaScriptového stavového automatu scény, zrušení audia, telefonních rozměrů, mirroru a navigace PASS.
- Před během 24 cílených Azure/builder/scéna/workflow testů PASS.
- Plná brána změn: 2273 testů PASS, 0 chyb; unittest 539,599 s, celkem unit fáze 545,5 s. Brána běžela souběžně s generací; následná kontrola dat a čtyři testy scény ověřily hotovou sadu.
- Testy výběru ukázek a překročení rozpočtu nyní používají syntetická data a nezávisí na tom, kolik skutečných MP3 už existuje.
- Míla přijal šest hlasových ukázek. Celý fyzický proklik a poslech scény na Macu/iPhonu nadále NEOVĚŘENO.

## Registrovaný běh a důkazy

- Workflow `mmtx_scene06_azure_complete` používá přesné argv:
  `.venv/bin/python ../MatysekANJ/build_scene06_audio.py --apply --provider azure`.
- Log: `logs/mmtx_scene06_azure_complete_20261101.log`.
- Ukončený stav: `logs/mmtx_scene06_azure_complete_20261101_state.json`, status completed, exit 0, final_tracks 144.
- Brána: `logs/mmtx_scene06_azure_complete_full_gate_20261101.log`.
- Klíče, účtové identifikátory a soukromý obsah do důkazů nepatří.

## Další krok a hranice

- Prakticky projít a poslechnout celou scénu; pak samostatně autorizované p+n.
- V tomto kroku pouze místní soubory a commit, bez push, Pages publikace a nasazení Cockpitu. Poslední doložená veřejná verze do 46173ef9 je historický stav z 28. 10., nikoli dnešní živý audit.
- Limit je na jeden běh, skutečné vyúčtování určuje Azure. Pro tento běh se všechny požadavky úspěšně dokončily a nebyly opakované.
