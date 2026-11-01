# MMTX scéna 6: Azure a poslechové ukázky

Datum: 2026-11-01
Ukázka vytvořená: 2026-11-01 21:32 CET
Pracovní proud: project-mmtx

## Výsledek

- Generátor má výslovnou volbu `--provider azure`; dosavadní Edge zůstává výchozí. Účet se nepřepíná a jiný poskytovatel se při chybě nevolá.
- Azure klíč a region se načítají pouze z místní konfigurace. Klíč jde do curl přes stdin, nikoli do argumentů procesu, logu nebo webové aplikace.
- Zachované původní texty, hlasová ID a tempo -10 %. SSML se escapuje bez krácení nebo normalizace textu.
- Před odesláním se ověří celý plán a před každým požadavkem se rezervují účtované znaky. Maximum 10 000 znaků na jeden spuštěný běh; timeout ani nejasná chyba rezervaci nevrací a požadavek se automaticky neopakuje.
- Vzniklo šest samostatných MP3 a spojený poslech 22.488 s. Ukázky: Jenny, Vlasta, Andrew, Ana, Michelle, Guy. Celkem 274 účtovaných znaků, šest úspěšných požadavků.
- Ukázky zůstávají oddělené v ignorovaném projektovém prostoru `data/private/mmtx/scene06_azure_preview/20261101T203248563646Z/`. Poslech: `listen_all.mp3`; účtenka: `preview.json`.
- Kanonické audio zůstává 16/144; zbývá 128 stop. SHA-256 všech souborů obou kopií scény před/po přesně shodné. Ukázky se do scény nevkládaly.

## Ověření

- 44 cílených testů PASS: Azure transport, SSML, rozpočet, redakce chyb, žádný retry, zachování MP3, izolovaná ukázka, scéna, registry a workflow.
- Šest MP3 dekódováno; vazby na text, hlas, tempo a SHA-256 PASS. Spojený MP3 také dekódován a přehrán přes afplay.
- Plná projektová brána PASS: 2273 testů, 0 chyb (514,733 s unittest; 520,7 s včetně běhu). Log mmtx_scene06_azure_full_gate_20261101.log.
- Původní Edge, nová Azure ukázka i spojený poslech: MP3 mono 24 kHz / 48 kb/s.
- Lidské přijetí zvuku Mac/iPhone: NEOVĚŘENO.

## Registrovaný postup

`mmtx_scene06_azure_preview`:
`.venv/bin/python ../MatysekANJ/build_scene06_audio.py --preview --provider azure`

Pozdější výslovné doplnění:
`.venv/bin/python ../MatysekANJ/build_scene06_audio.py --apply --provider azure`

Offline kontrola:
`.venv/bin/python ../MatysekANJ/build_scene06_audio.py --check`
Při 16/144 je očekávaný exit 1 kvůli neúplnému audiu, nikoli neplatným souborům.

## Další krok a rizika

- Míla poslechne ukázky a rozhodne o doplnění zbývajících 128 stop. Skutečný proklik celé scény a fyzický poslech Mac/iPhone zůstávají otevřené.
- Limit platí pro jeden běh, nikoli pro jiné aplikace nebo samostatně znovu spuštěné běhy. Skutečné vyúčtování určuje Azure; místní účtenka eviduje rezervované znaky.
- Při chybě se zachovají hotové soubory a zbytek se negeneruje automaticky. Existující text/hlas/tempo/hash musí nadále odpovídat, jinak se výstup zachová a běh skončí.
- Bez push, Pages publikace, nasazení Cockpitu nebo změny jiných hlasových cest.
