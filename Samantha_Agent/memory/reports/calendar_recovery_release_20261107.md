# Společné vydání kalendáře a obnovovacího návodu

## 2026-11-07 14:04 CET — Will: společné schválené Terra p+n

Hotovo: Do hlavního checkoutu převzatý Datův commitovaný REC-01 až REC-04
rozsah 29de7f05, dc528b45, d8b3d066, e8bb4b12, d5651110 nad kalendářovým
9f7ce93e. Rozpracovaný REC-05 v Datově vlastním worktree zůstává zachovaný.
Konflikty zachovávají všechny současné role (Email/Ateliér) i přidaný parser
RECOVERY_ROLE, oba seznamy workflow a všechny testy. Centrální JSON beze změny:
recovery_document_maintainer není aktivovaný. Sdílený helper zachovává named
profile/disabled_features a doplňuje Datovo vypnutí plugins/skills. LL nového
REC proudu přeznačené na 106–108, aby nepřekryly existující záznamy.

Rozhodnutí: Míla výslovně zadal všechny hotové Willovy i Datovy commity pro
Terra p+n. Jde o společný runtime Cockpitu, předání project-email-cases; nový
plánovač, placený REC pilot, produkční TXT/iCloud publikace a nová role se
neaktivují. REC-04 writer zůstává jen pro izolované testovací kopie.

Další krok: jediný registrovaný submit_release(wait=True), zmrazený společný
merge head a Terra z centrálního auditu. Výsledek publikace se neodvozuje z
tohoto předběžného zápisu: autorita logs/calendar_recovery_release_20261107.log
a logs/calendar_recovery_verified_20261107.log a přesná runtime účtenka.

Navrhované další kroky: kalendářový bod 5 (jediný zápis včetně alarmů) až jako
další vývoj; REC-05/06 v Datově samostatném proudu, původní přejímky zachované.

Technický důkaz: 198 cílených integračních testů PASS. Plná společná brána,
smoke, přesné nasazení a CI jsou podmínkou vydání; zajišťuje registrovaný worker
a následná kontrola Willa. Žádná změna hodinové kopie, produkčního návodu,
iCloud cílů, služeb Camina či autosave mimo standardní chráněné vydání Cockpitu.

## 2026-11-07 14:18 CET — oprava přenositelnosti testu po publikační bráně

Hotovo: Test návrhu plist používá vlastní TemporaryDirectory s připraveným
interpretem a skriptem. Ověřuje pouze vytvoření specifikace bez změn fixture;
nový negativní scénář zachovává odmítnutí chybějícího Pythonu nebo skriptu.
Produkční launcher ani služby se nemění. 125 REC testů PASS.

Rozhodnutí: Původní přesná účtenka d525499100547f133a7214951cc661dd zůstává
zachovaná v attention/push_state=uncertain. Diagnostika doložila jedinou chybu
v plné bráně (2780 testů, 49 SKIP): lokální .venv chybí v izolovaném profilu.
GitHub živě stále 9730a662. V github_batch.py brána vyhazuje výjimku před
_push_exact_head, tedy tento pokus žádný Git push neprovedl; nasazení nezačalo.
Nejde o opakování nejasného síťového push. Po opravě vzniká nový commit a nový
přesný balíček podle stále platného Mílova p+n.

Další krok: nové registrované předání v2; autorita aktuálního vydání
logs/calendar_recovery_release_v2_20261107.log a calendar_recovery_verified_20261107.log.
Technický důkaz selhání: logs/calendar_recovery_gate_failed_fixture_20261107.log;
oprava: logs/calendar_recovery_fixture_fix_20261107.log. Produkční REC aktivace
zůstává vypnutá a Datův REC-05 ve vlastním worktree zachovaný.
