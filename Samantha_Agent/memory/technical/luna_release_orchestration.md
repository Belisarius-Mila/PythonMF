# Předání p+n celého balíčku Luně

Rozhodnutí Míly 2026-10-17: hlavní Adam dokončí vývoj a commity; po samostatném
p+n převezme Luna celý schválený balíček. Výsledek se vrací do stejné konverzace
hlavního Adama. Rozšíření téhož dne platí pro všechny kanonické vývojové
proudy portálu (aktuálně 33), včetně přímé terminálové relace.

## Technologie a rozsah

- Stávající Codex App Server, model `gpt-6-luna`, krátké nové dočasné vlákno.
  Nemění se výchozí model, konfigurace ani komunikační architektura.
- Luna dostává pouze projekt, koncové commity rozsahu, počet commitů, režim
  a názvy chráněných služeb. Nedostává celou historii, přihlašovací údaje,
  soukromá data ani oprávnění opravovat kód či systém.
- Jediný read-only modelový tah přebírá přesný cíl strukturovanou odpovědí.
  Stávající serverové Python postupy provádějí plnou publikační bránu,
  přesný GitHub batch push a registrované nasazení: běžící runtime Samanthy
  s restartem a smoke 5/5, nebo společný Pages publisher s přesným deployment
  SHA a HTTP 200 konkrétní webové aplikace.
- Celý rozsah mezi GitHub main a lokálním main je jeden balíček. Počet
  commitů není omezený na jeden. Je-li main již přesně na GitHubu, proběhne
  plná brána a registrované nasazení bez dalšího push.
- Soukromý záznam a oddělený proces přežijí restart Cockpitu i zavření karty.
  Každý požadavek má vlastní účtenku; předchozí se nepřepisují ani nemažou.

## Použití

1. Dokončit vývoj, ověření, paměťový zápis a lokální commity.
2. Ve vybraném vývojovém proudu použít `p+n`, `p*n`, `vše p+n` nebo tlačítko
   v Práci. Otázky obsahující p+n nejsou příkazem. Archivovaný proud nelze
   použít k novému vývojovému předání.
3. Read-only audit ověří čistotu a zarovnání profilů, aktuální GitHub rozsah,
   cílové nasazení a dostupnost původního vlákna Adama.
4. Uživatelské potvrzení se vztahuje na zobrazený přesný balíček. API navíc
   vyžaduje `POTVRZUJI PREDANI P+N LUNE`, oba auditované commity,
   `expected_workstream_id`, `expected_deployment_target` a request ID.
   Stejný commit nelze po potvrzení přesměrovat na jiný projekt nebo cíl.
5. Výsledek je vidět ve stejné konverzaci. Po ostrém dokončení či překážce
   hlavní Adam dostane strojovou účtenku do původního vlákna. Jeho kontrolní
   tah má read-only sandbox bez sítě a nesmí opakovat vývoj ani publikování.

Zkouška bez publikování volá skutečnou Lunu a read-only ochranné kontroly;
nevolá push/deploy ani nový kontrolní tah hlavního Adama. Karta zobrazí výsledek.

V přímé terminálové/Codex relaci hlavní Adam deleguje krátké zadání pomocnému
agentovi `gpt-6-luna` bez kopírování celé historie. Předá i zamýšlené ID
projektu. Pomocník použije `audit_release()` bez argumentu `service`,
porovná projekt s předáním a při rozdílu se zastaví. Potom použije registrované
`start_terminal_release`, sleduje soukromou účtenku a výsledek vrátí původnímu
volajícímu agentovi. Pro čekání a závěrečný důkaz používá pouze
`LunaReleaseStore().status()` a jeho bezpečnou projekci `job.gate` /
`job.verification`; nikdy nevypisuje celý interní záznam z `load()` ani token.
Stejný serverový postup provede publikování, ale žádná
zpráva se neposílá do jiné konverzace Cockpitu. Způsob návratu nelze přepnout
uživatelským HTTP payloadem. Hlavní Adam poté ověří účtenku a odpoví v původní
relaci. Během p+n zůstává společný main bez dalších vývojových změn.

GitHub HTTPS push může jednorázově použít již ověřené přihlášení GitHub CLI
podle LL-060; bez změny globální konfigurace, nového přihlášení, tokenu v argv
nebo opakování push. Ostatní remotes zachovávají dosavadní transport.

## Registrované cíle

- Běžné proudy používají stávající společné nasazení runtime Samanthy/Cockpitu.
  To zahrnuje například infrastrukturu, Human–Adam, Knihovnu i editor filmu.
- `project-mmtx`, `project-to-be-to-have` a `project-colors-and-numbers`
  používají společný existující PythonMF Pages publisher. Poslední dva mají
  vlastní HTTP smoke cesty `to-be-to-have/` a `colors-numbers/`.
- Zdrojem jsou serverový katalog a registrované vazby `PAGES_PROJECT_PATHS`.
  Nový běžný proud nepotřebuje zvláštní seznam povolených ID; nový druh
  produkčního cíle musí mít registrovaný adapter. Neznámý cíl se zastaví.
- Nejde o univerzální vydávání samostatných klientů, instalaci na zařízení
  nebo aktualizaci služby Camino. Jejich specifické vydání zůstává samostatnou
  operací s vlastním oprávněním; běžné p+n tyto služby nepřepíná.
- Pravidla projektu, handoff/TVBCP a jeho cílené kontroly plní hlavní Adam
  před commitem. Luna přebírá hotový rozsah a server vynutí plnou publikační bránu.

## Ochrany

- Jen kanonický Cockpit. Uživatelské payloady nemohou měnit cíl služby,
  cestu workspace, model, callback URL ani cestu soukromé účtenky.
- Během předání jsou další Human–Adam mutace a samostatný restart zablokované.
  Interní kroky autorizuje soukromý token svázaný s úlohou a přesnou fází;
  veřejný stav token nikdy nevrací.
- Cíl nasazení pochází ze zmrazené účtenky, ne z nového obsahu main ani
  klientského payloadu. Původní brány odmítnou změnu před i během operace.
- Před/po se čtou vlastněný Camino proces, hash konfigurace a Serve,
  jediný čerstvý trvalý autosave a jeho nastavení. Žádná změna těchto služeb,
  originálů, filmů, záloh nebo sítí není součástí tohoto workflow.
- Stejné request ID nespustí druhou úlohu. Cross-process lease povolí právě
  jednoho vykonavatele. Při nejistém push se automaticky nepokračuje; po
  přerušení HTTP při restartu se pouze ověří nový proces, restart se neopakuje.
- `requested`/`uncertain` nejsou důkaz neprovedení. Push a nasazení mají
  samostatné potvrzené stavy. Chyba se vrací Adamovi se zachovanou účtenkou,
  bezpečným důvodem a fází; hlídání přerušeného procesu nepřepisuje souběžně
  dokončený výsledek.
- Návrat nezakládá nové vlákno a nesmí se znovu odeslat při nejistém doručení.
  Při chybě obnovy zůstává viditelný stav vyžadující ověření.

## Ověření a zavedení

- Skutečná Luna přijala syntetický sedmicommitový balíček a přesný SHA;
  samostatný suchý běh celého vykonavatele prošel i skutečnými read-only
  ochranami Camino/autosave. Bez publikování nebo změny hlavního modelu.
- Důkazy: `logs/luna_release_live_probe_20261017.log`,
  `logs/luna_release_live_dry_run_20261017.log` a testové logy.
- Skutečný návrat přes App Server prošel v oddělené syntetické konverzaci:
  stejný thread, potvrzené doručení, zachovaný testovací model a read-only tah;
  provozní konverzace se nezměnila. `logs/luna_release_live_return_20261017.log`.
- Testy pokrývají více commitů, změnu SHA, nonce/fáze, souběh, nejistý push,
  přerušení restartem, zachování původního vlákna, read-only návrat a souběžné
  dokončení při kontrole přerušeného procesu. Závěrečná regresní sada 27 testů
  PASS: `logs/luna_release_race_targeted_20261017.log`.
- První verze pro Cockpit: plná brána 1993/1993 PASS, bez přeskočení; unit část 267,315 s.
  `logs/luna_release_full_gate_20261017.log`.
- Obecné rozšíření: 286 cílených integračních testů PASS, včetně všech 33
  vývojových proudů, potvrzeného projektu/cíle, již odeslaného main,
  Pages bez restartu, HTTP cesty konkrétní aplikace a starého MMTX kontraktu.
  `logs/luna_general_integration_20261017.log`.
- Skutečná Luna a skutečné read-only ochrany prošly v oddělených syntetických
  suchých bězích pro `misc-unclassified-development` (5,29 s) a `project-mmtx`
  (5,19 s), po 7 commitech. Žádná produkční úloha ani publikace nevznikla.
  `logs/luna_general_live_dry_run_20261017.log`.
- Závěrečná plná brána obecného rozšíření: 2011/2011 PASS, bez přeskočení,
  unit část 263,223 s. `logs/luna_general_full_gate_20261017.log`.
- Ostré p+n a fyzická přejímka nejsou suchým během prokázané. První nasazení
  této funkce provede Adam dosavadní cestou po výslovném p+n, protože starý
  běžící Cockpit nové routy ještě nemá. Další balíčky už mohou využít Lunu.

Implementace: `app/communication/luna_release.py`, `luna_release_worker.py`,
nové registrované routy Cockpitu, úzké napojení chatu a návrat do session hubu.
Kanonický stav a důkazy patří do handoffu/TVBCP `project-cockpit`.
