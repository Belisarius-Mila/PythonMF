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

Push ani nové nasazení zatím nejsou potvrzené. Registrované publikační brány
vyžadují čistý celý pracovní strom. Nesouvisející nesledovaná složka s audio
podklady v kořeni Git repozitáře zůstává zachovaná a není součástí commitu.
Míla dostal konkrétní návrh přesunu celé složky mimo Git bez změny obsahu;
provedení čeká na jeho rozhodnutí. Samotný souhlas s p+n platí dál.

Po vyřešení překážky: čistě zarovnat profilové workspaces, provést registrovaný
GitHub batch s plnou branou a řízené nasazení. Ověřit nový proces, přesný head,
smoke 5/5 a shodu skutečně servírovaného HTML s lokálním frontendem.

Příští vývoj: **U07 — Servis podle účelu**, sloučení duplicit, detaily na
vyžádání, pravdivé health štítky a intervaly podle konfigurace. Zachovat
dostupnost obnovy screenu, restartu, auditu a zálohy i jejich ochranné podmínky.

Fyzická Safari/iPhone/VoiceOver přejímka čeká. Drafty žijí jen v aktuální
kartě; potvrzený reload nebo ukončení prohlížeče je může ztratit. Přímý odkaz
obnovuje hlavní oblast, nikoli přesný vnořený dialog. Záloha zůstává odložená
kvůli nedostupnému disku; žádná záloha nebyla spuštěna.
