# Předání p+n celého balíčku Luně

Rozhodnutí Míly 2026-10-17: hlavní Adam dokončí vývoj a commity; po samostatném
p+n převezme Luna celý schválený balíček. Výsledek se vrací do stejné konverzace
hlavního Adama. První verze se vztahuje na `project-cockpit`.

## Technologie a rozsah

- Stávající Codex App Server, model `gpt-6-luna`, krátké nové dočasné vlákno.
  Nemění se výchozí model, konfigurace ani komunikační architektura.
- Luna dostává pouze projekt, koncové commity rozsahu, počet commitů, režim
  a názvy chráněných služeb. Nedostává celou historii, přihlašovací údaje,
  soukromá data ani oprávnění opravovat kód či systém.
- Jediný read-only modelový tah přebírá přesný cíl strukturovanou odpovědí.
  Stávající serverové Python postupy provádějí plnou publikační bránu,
  přesný GitHub batch push, přípravu nasazení, řízený restart a smoke 5/5.
- Celý rozsah mezi GitHub main a lokálním main je jeden balíček. Počet
  commitů není omezený na jeden. Prázdný balíček tato první verze nenasazuje.
- Soukromý záznam a oddělený proces přežijí restart Cockpitu i zavření karty.
  Každý požadavek má vlastní účtenku; předchozí se nepřepisují ani nemažou.

## Použití

1. Dokončit vývoj, ověření, paměťový zápis a lokální commity.
2. V proudu Cockpit použít `p+n`, `p*n`, `vše p+n` nebo tlačítko v Práci.
   Otázky obsahující p+n nejsou příkazem. Ostatní proudy zachovávají své postupy.
3. Read-only audit ověří čistotu a zarovnání profilů, aktuální GitHub rozsah,
   cílové nasazení a dostupnost původního vlákna Adama.
4. Uživatelské potvrzení se vztahuje na zobrazený přesný balíček. API navíc
   vyžaduje `POTVRZUJI PREDANI P+N LUNE`, oba auditované commity a request ID.
5. Výsledek je vidět ve stejné konverzaci. Po ostrém dokončení či překážce
   hlavní Adam dostane strojovou účtenku do původního vlákna. Jeho kontrolní
   tah má read-only sandbox bez sítě a nesmí opakovat vývoj ani publikování.

Zkouška bez publikování volá skutečnou Lunu a read-only ochranné kontroly;
nevolá push/deploy ani nový kontrolní tah hlavního Adama. Karta zobrazí výsledek.

V přímé terminálové/Codex relaci hlavní Adam deleguje krátké zadání pomocnému
agentovi `gpt-6-luna` bez kopírování celé historie. Ten použije registrované
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
- Závěrečná plná brána 1993/1993 PASS, bez přeskočení; unit část 267,315 s.
  `logs/luna_release_full_gate_20261017.log`.
- Ostré p+n a fyzická přejímka nejsou suchým během prokázané. První nasazení
  této funkce provede Adam dosavadní cestou po výslovném p+n, protože starý
  běžící Cockpit nové routy ještě nemá. Další balíčky už mohou využít Lunu.

Implementace: `app/communication/luna_release.py`, `luna_release_worker.py`,
nové registrované routy Cockpitu, úzké napojení chatu a návrat do session hubu.
Kanonický stav a důkazy patří do handoffu/TVBCP `project-cockpit`.
