# Ovládání více projektů — krok 3

Stav 23. 10. 2026: implementace ověřená, schválené p+n sleduj přes
účtenku c3aba0302d0661fbff03b131e65357a4. Tento checkpoint vzniká před jejím výsledkem. Samotné
p+n publikuje zdroje a společný runtime Cockpitu; neinstaluje iPhone ani
neaktualizuje samostatnou službu Camino.

## Používání

- První spuštění nabízí název nového projektu a volitelná data začátku/konce.
  Zkouška zůstává samostatnou výslovnou volbou.
- Nabídka → Projekty ukáže Probíhající a Archivované. Zaškrtnutý je právě
  vybraný projekt; jeho název a případné období jsou na hlavní obrazovce.
- Nový projekt lze založit bez termínů. Konec před začátkem se neuloží.
- Upravit projekt načte skutečný název, Zkoušku, termíny a archivaci.
  Uložit provede jednu transakci; Zrušit ponechá původní stav.
- Archivovaný projekt lze vybrat a číst. Nové foto/video/audio a označení
  okamžiku jsou vypnuté, dosavadní záznamy a přenosy zůstávají zachované.
  Vypnutím Archivovat projekt a uložením jej znovu otevřeš.
- Přepínání a správa čekají na dokončení přípravy záznamu, kamery, audia
  nebo importu. Projekt se nikdy nepřepisuje názvem jiné dovolené.

## Původ změny a integrace

Datová příprava Adamem v 176a6c66. První návrh Luny nebyl převzatý kvůli
chybně vymezenému zdrojovému úseku. Po Mílově výslovném potvrzení vznikl
nový registrovaný návrh c39307ba80c8e9e373149a9a7696c220, baseline a after
15/15 PASS. Adam zkontroloval diff a převzal jej přes accept s přesným
otiskem. Navíc doplnil validační stav zakládání a identifikátor přepínače
Zkoušky pro nezávislou UI přejímku. Kritické datové změny nejsou delegované.

## Ověření a omezení

- Datová příprava: Swift 82 PASS, plná společná brána 2185 PASS, iOS Debug
  build PASS. Původní identity i fronty zachované bez migrace schématu.
- Aktuální UI: rychlá statická brána PASS, generic iOS Release build PASS.
- Tři vybrané UI scénáře PASS: offline/soukromí/Moment 1/1; dva projekty,
  termíny, oddělené Momenty, archivace, blokování pořizování, znovuotevření
  a restart + přejmenování původní Zkoušky 2/2. Poslední běh TEST SUCCEEDED.
  První běh scénářů měl dvě selhání testovacího klikání na popisek přepínače;
  test nyní kliká na samotný ovladač a ověřuje jeho hodnotu. Aplikační kód
  se kvůli této opravě testu neměnil. Dokumentace: 4 soubory / 48 odkazů PASS.
- První simulátorový běh uvázl před testy a byl přerušen; druhý zablokoval
  CodeSign kvůli FinderInfo ve složce na Ploše. Pro další test použit čistý
  DerivedData v /private/tmp a místní ad-hoc podpis, bez změny týmů či účtů.
- Důkazy pouze data/private/camino_projects_ui_20261023/ a dočasné xcresult
  CaminoProjectsUI20261023Tests / CaminoProjectsUISwitchTests20261023.
  Žádná produkční média ani soukromé texty ve verzovaném reportu.

Před budoucí instalací stejné aplikace bez odinstalace je nutné samostatně
schválit a ověřit službu s project_details_v1 a zachování archivu/střihů.
Telefonní instalace, fyzické foto/video/mikrofon a přejímka přenosu nové
verze NEPROVEDENO. Termín je popis projektu, ne filtr záznamů. Krok 4
projektový Viewer/Mac a krok 5 výběr střižny navazují; neslibuje se automatické
sdílení nových dovolených ani společný vícedenní film.

## 2026-10-23 22:39 CEST — výsledek prvního p+n

Účtenka c3aba0302d0661fbff03b131e65357a4 skončila attention před pushem. Přímý živý
GitHub zůstal na 8bc31d07; nasazení nezačalo. Plná brána spustila 2185 testů,
jediný selhal na startovacím souběhu status probe / worker lock. Nový
telefonní kód tuto kolizi nezpůsobil. Původní běh se neopakuje.

Adam připravil úzkou opravu status probe ve stávající 30s lhůtě a regresní
test. 57 cílených testů PASS; plná brána 2186 PASS (333,492 s unit část), opakovaný souběh 10/10 PASS. Nový placený pokus
Luny až po konkrétním potvrzení; žádný ruční push či restart služeb.

## 2026-10-24 — navázání

Opravený balíček do e11d949a úspěšně pushnutý/nasazený do Cockpitu přes
účtenku e47cdb394ec5441c5d25632f11c8c995, plná brána 2186 a smoke 5/5.
Kroky 4–5 navazují [samostatným místním checkpointem](MULTI_PROJECT_ACCESS_REPORT.md),
včetně období a rozlišení shodných jmen v nabídce telefonu. iPhone se běžným
p+n neinstaloval; fyzická přejímka nové verze zůstává samostatná.
