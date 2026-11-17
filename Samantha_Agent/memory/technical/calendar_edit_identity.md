# Stabilní identita a viditelné odmítnutí kalendářové editace

Aktualizace 2026-11-17 09:00 CET. Proud project-cockpit; kanonický handoff a existující
TVBCP workstreams/project-cockpit.md. Navazuje na calendar_complete_edit_20261109
 a calendar_edit_alarm_order_recovery_20261110 v reports/.

## Projev a důkaz

Míla hlásil uložení bez výsledku z úvodní agendy, zatímco samostatný kalendář
fungoval. Obě stránky používají shared/calendar_actions.js a /api/calendar/edit.
Dnešní privátní žurnál obsahoval dvě changed a poté verified pro tutéž původní
událost s totožnými nativními ID; žádný text/ID se nekopíruje do Gitu.
Pět read-only native inspect vracelo dva různé otisky, calendar_writes=false.
Samotné běžné HTML uložení prošlo na obou stránkách v syntetickém prohlížeči.

Otisk identity zahrnoval neuspořádané pole EventKit alarmů. Změna pouhého
pořadí proto dokázala přerušit úpravu jako changed ještě před save. Dřívější
oprava LL-122 již normalizovala read-back po save, nikoli tento původní otisk.
Regrese s přesnou produkční Swift logikou obrátí alarmy mezi preview/apply a
před opravou selhala. Živý nový helper se po opravě bez dalšího schválení
nepřepínal; fyzická přejímka nové verze tak zůstává otevřená.

## Oprava a hranice

- identity() seřadí pouze přesné řetězce alarmů. Počet, duplicity, absolutní i
  relativní čas a všechna další pole včetně obou nativních ID zůstávají součástí
  ověření. Skutečně změněný alarm, poznámka nebo jiná událost stále blokují save.
- Odmítnutí changed/blocked zachová otevřený editor s chybou, vypnutým Uložit
  a tlačítkem Zavřít. Nepoužívá jen notice připojenou ke starému řádku agendy,
  který mohlo automatické obnovení vyměnit. Stejný konečný požadavek nelze
  znovu submitnout. Validace editovatelného času a unknown recovery beze změny.
- Sdílený JS editor nyní explicitně patří do validační kalendářové domény;
  budoucí samotná změna JS musí zahrnout i nativní/edit/agenda HTTP regrese.
- Historické markery, terminální účtenky, oprávnění a původní helper zůstávají.
  Neprovádí se automatický druhý save, create, oprava osobní události ani grant.

## Ověření a další krok

2 nové regrese FAIL→PASS;38 cílených testů PASS. Skutečný Edge se syntetickými
API a celým HTML obou stránek: po jednom update, žádné JS chyby. Při změně
řádku na pozadí zůstává odmítnutí v dialogu, další save nedostupný;390px snímek
viz privátní důkazy. Žádné produkční API mutace ani skutečný calendar save.
Oddělený SDK build + codesign verify deep/strict +7 self-test PASS bez EventKit
přístupu. První build na Ploše měl Finder metadata odmítaná codesign; podle
stávající LL přenesen pouze testovací build root do /private/tmp. Zdrojová ani
produkční metadata se nečistila. Podepsaný testovací helper se neaktivoval.

Konečná programová brána, přesné zdroje a lokální commit jsou v
private calendar_home_edit_20261117/completion.json; úspěch se netvrdí bez PASS.
Po samostatně schváleném p+n zvolit v UI Povolit úpravy na Macu, které sestaví
nový podpis/helper; macOS může chtít grant. Pak pouze Mílou zvolená fyzická
úprava a ověření. Živý podpis/grant nejsou součástí tohoto vývojového kroku.
