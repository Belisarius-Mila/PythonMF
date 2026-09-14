# Předání UI Cockpitu U01–U06 — 14. 9. 2026

Míla schválil push a nasazení celého čekajícího balíčku. U07 se má řešit až
při příštím pokračování; dnešní krok jej nezahajuje.

## Dokončený vývoj

| Krok | Výsledek | Commit |
| --- | --- | --- |
| Audit | 22 nálezů a roadmapa U01–U11, původní strukturální audit zachovaný | `80e5994c` |
| U01 | Společná viditelná odezva akcí včetně dialogů a Servisu | `2f6306bb` |
| U02 | Hlavička bez překryvů a návraty z dokumentových čteček | `04a4d372` |
| U03 | Kompaktní Dokumenty, rozbalovací pracovní karty, viditelné problémy | `05c9994f` |
| U04 | Stránkování hledání a zachování hledání při návratu ze čtečky | `a180d6f6` |
| U05 | Jedna prioritní fronta, oddělené úkoly a provozní varování | `3192e621` |
| U06 | Šest oblastí navigace, 16 dialogů, návrat fokusu a rozepsaných formulářů | `2bbdcfc7` |

Podrobné důkazy jednotlivých kroků jsou v `cockpit_ui_u01_2026_09_14.json`
až `cockpit_ui_u06_2026_09_14.json`. Jde o automatizované testy a syntetické
browser scénáře, nikoli fyzickou přejímku Mílova Safari/iPhonu.

## Ověření před předáním

- První plná brána: 1680 testů, jedna chyba ve starém testu, který vymezoval
  `renderDashboard` pomocí již odstraněné `renderDashboardMorningSentence`.
- Oprava používá aktuální následující funkci `renderDecisionCards`; původní
  kontrola, že průběžný status neotevírá Dokumenty, zůstala zachovaná.
- Opravený cílený test prošel. Opakovaná plná brána dokončena 2026-09-14 20:19 CEST:
  **1680/1680 testů OK**, testy 318,932 s; statické kontroly také prošly.
- Všech šest JSON reportů je čitelných; kontrola cest čekajícího balíčku
  nenašla zakázané private, autosave ani klíčové cesty.

## Publikace a otevřené kroky

Funkční balíček U01–U06 nasazen: `980aed7a66426665b2e809b097522fba2910dc8c`. Ověřeno
`2026-09-14T18:23:41+00:00`: nový proces potvrzen, otisk `55373c8c1c4da728`,
smoke **5/5** a shoda podávaného HTML s lokálním frontendem.

Míla schválil přesun nesouvisejících audio podkladů. Celá složka byla
přesunuta vedle repozitáře do `PythonMF_local_artifacts`; všech 35 souborů,
521 757 bajtů, stejné SHA-256 a oprávnění. Podklady nejsou v Gitu.
Publikační i nasazovací audit po přesunu prošly, oba profilové workspaces
jsou čistě zarovnané s lokálním main.

Tento uzavírací zápis vzniká po ověřeném funkčním nasazení a před společným
GitHub balíčkem včetně zápisu. Ten provede povinnou plnou bránu; po push se
řízeně nasadí a ověří finální head. Aktuální odeslání a finální head poskytují
registrované `github-batch-audit`, `deploy-audit` a `deploy-verification`;
tento zápis sám není důkaz dokončeného push.

Příští vývoj: **U07 — Servis podle účelu**, sloučení duplicit, detaily na
vyžádání, pravdivé health štítky a intervaly podle konfigurace. Zachovat
dostupnost obnovy screenu, restartu, auditu a zálohy i jejich ochranné podmínky.

Fyzická Safari/iPhone/VoiceOver přejímka čeká. Drafty žijí jen v aktuální
kartě; potvrzený reload nebo ukončení prohlížeče je může ztratit. Přímý odkaz
obnovuje hlavní oblast, nikoli přesný vnořený dialog. Záloha zůstává odložená
kvůli nedostupnému disku; žádná záloha nebyla spuštěna.
