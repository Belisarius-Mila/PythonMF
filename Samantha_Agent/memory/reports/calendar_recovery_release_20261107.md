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

## 2026-11-07 14:33 CET — Will: převzetí dodatečně dokončeného REC-05

Hotovo: První balíček 135f46e7 je potvrzeně pushnutý a nasazený (Terra job
10fcd19ea7f50889a1f1424679e70b9b, 2781 testů, smoke 5/5). Během jeho běhu
Data commitnul aa18a6e7. Will podle Mílova pokynu všechny commity přebírá i tento
REC-05 do navazujícího přesného vydání. Celý kalendář/REC-01 až REC-04 zůstává.
Nový plánovač má pouze sandboxové callbacky a produkční run/tick jsou stále
activation_required. Žádná role, služba, skutečný návod ani modelový pilot se
neaktivují. REC-06 má samostatné dosud otevřené předpoklady a oprávnění.

Hotovo: Zachovaná launcher X_OK kontrola. Fixture mají vlastní spustitelný
wrapper k aktuálnímu interpretu a odkaz na skutečný CLI pro minimal-PATH test;
žádná závislost na .venv izolovaného publikačního profilu. Validace produkce
není oslabená. 199 cílených testů PASS; skutečný read-only environment preview
v hlavním checkoutu PASS (bez launchd/auth přejímky, bez služby/modelu).
LL-100 z nového proudu přeznačen na LL-110, historické záznamy zachované.

Rozhodnutí: pokračuje původní výslovné p+n všech hotových commitů, nikoli
aktivace automatického běhu. Datův worktree zůstává oddělený.


Další krok: navazující Terra p+n, nová přesná účtenka a nejnovější GitHub CI.
Autorita výsledku logs/calendar_recovery_rec05_release_20261107.log a
logs/calendar_recovery_verified_20261107.log. Důkazy předání předchozího balíčku
zůstávají calendar_recovery_release_v2_20261107.log a *_verified_phase1_*.log.
Technický důkaz: logs/calendar_rec05_targeted_20261107.log a
calendar_rec05_environment_20261107.log. Plná brána posledního balíčku je
povinná u registrovaného workeru. Bez změny hodinové kopie, výběru kalendářů,
produkčních TXT/iCloud kopií nebo aktivace plánovače.
