# Více projektů — Viewer, Mac a filmová střižna (kroky 4–5)

Stav 24. 10. 2026: místní implementace a ověření, bez nového p+n,
aktualizace samostatné služby nebo instalace iPhonu. Navazuje na datový
základ a telefonní ovládání v [krocích 1–3](MULTI_PROJECT_FOUNDATION.md).

## Používání

- Aplikace ukazuje v nabídce Projekty také období. Stejně pojmenované
  projekty mají krátké rozlišení identity. Nový projekt začíná s Viewerem
  vypnutým; tuto hranici připomíná text při zakládání.
- Ve Vieweru odkaz Projekty otevře Cesty a dovolené, rozdělené na Probíhající
  a Archivované. Jsou zde pouze výslovně povolené projekty, bez názvů,
  identit nebo počtů neveřejných cest a owner-only Momentů.
- Vybraný projekt má vlastní odkazy deníku, dnů, mapy, bodů a médií.
  Původní přímé odkazy /viewer/ dál ukazují cestu z konfigurace. Přepnutí
  telefonu ani jiné karty prohlížeče nemění cizí již otevřený projekt.
- Ve Film Camino nejprve vyber Cesta nebo dovolená, pak uložený film nebo
  Den na Macu. Dva projekty mohou mít stejné datum i jméno. Archivované
  cesty lze číst a zpracovat ve filmu, nemění se tím pořizování v telefonu.
- Rozpracované uložení/úpravy blokují přepnutí. Výběr cesty, dne a filmu
  si pamatuje konkrétní karta; i prázdná cesta zůstává vybraná po obnovení.
- Nový film stále vyžaduje vědomé potvrzení konečných Mac dat vybrané cesty
  a dne. Celá videa jsou výchozí, zkracování je ruční.

## Oprávnění

Čtecí přihlášení Jany zůstává oddělené od owner API a od grantů projektů.
Výchozí grant nových telefonních projektů je vypnutý. Čtenář nedostává
owner katalog. Katalog Vieweru, HTML, mapa i GET/HEAD/Range médií znovu
ověřují serverem známé povolení. Odvolaná cesta zmizí i ze starých URL;
ostatní povolené cesty a přihlášení zůstanou použitelné. Obnova/konflikt
zavře katalog i přípravu médií. Již uloženou cizí kopii nelze odvolat.

Registrovaný servisní program umí nad zastavenou službou změnit pouze grant
jednoho existujícího projektu; vyžaduje vlastní výslovné potvrzení a pro
nový grant již zřízené samostatné čtecí přihlášení. Příklady budoucí správy:

```bash
.venv/bin/python scripts/camino_service_control.py enable-viewer --trip-id UUID_PROJEKTU --confirm
.venv/bin/python scripts/camino_service_control.py disable-viewer --trip-id UUID_PROJEKTU --confirm
```

Při explicitním --trip-id se čtecí tokeny nevytvářejí ani neodvolávají.
Prázdné/neplatné/neexistující ID se odmítá. Bez --trip-id zůstává původní
význam globálního enable/disable (disable odvolá všechny čtecí tokeny).
Spouštěč nabídne Viewer i při povolené jiné cestě než konfigurační výchozí.
V tomto vývojovém kroku nebyl změněn žádný skutečný grant nebo token.

## Datové vazby a kompatibilita

trip_id označuje cestu; project_id označuje uzavřenou sadu pro jeden film.
Katalog filmu a potvrzení Mac dne dostávají explicitní trip_id. Uložený film,
render worker, fotografie i hotový export vybírají archivní kontext ze
svého neměnného manifestu, nezávisle na pozdějším výběru v UI. Neshoda
cesty, dne, zdroje nebo manifestu se odmítne. Jedna konfigurační cesta je
pouze výchozí volba starých klientů, nikoli celý archiv.

Filmový strom, identity starších projektů, originály a uložené střihy
zůstávají na původních místech. Katalog Macu používá SQLite mode=ro,
neinicializuje RevisionStore a nespouští migraci. Beze změny DB schématu.
Povolení Vieweru samo nevytváří film; owner film nepotřebuje grant pro Janu,
ale nadále odmítá owner-only/skryté zdroje. Termíny cest jsou popis, ne filtr.

## Ověření

- 34 cílených integračních testů PASS: grant/revoke jednotlivých cest bez
  přepisu původních operací a bez rotace čtenáře, HTML/JSON/mapa/Range/HEAD,
  proxy prefix, souběžné odvolání při převodu, blokace obnovou, archivy.
- Dva stejné názvy i dny: různé manifesty, zdroje a filmové UUID. Cizí asset
  ve střihu a cizí job odmítnuté; worker/CLI vyberou správný manifest.
  Syntetické exporty ověřují vazby a bajty, nikoli fyzický poslech videa.
- Node scénáře střižny PASS: různé karty, stejné dny, pozdní odpověď,
  chybně označená cesta, neuložený střih, reload a prázdný projekt.
- Izolovaný HTTP server a dvě skutečné syntetické JPEG → PNG 1024×768:
  dekódování obou odlišných obrazů, bez EXIF, cizí asset HTTP 404 PASS.
- iOS Release generic build PASS; podpis, IPA a instalace nové verze neprovedené.
- plná brána 2193 PASS (453,570 s unit část), závěrečné 3 testy dispatcheru PASS.
- Browser není v tomto prostředí registrovaný. Skutečný browser/Safari,
  iPhone a celkový přenos nové verze jsou NEOVĚŘENO; Node ani HTTP nejsou
  jejich náhradní fyzická přejímka.

Důkazy jsou pouze data/private/camino_projects_20261024/ a syntetická
úložiště v /private/tmp. Žádná reálná média ani soukromé texty v Gitu.

## Další krok

Samostatně schválené p+n Cockpitu; pro novou telefonní verzi nejprve
odpovídající samostatná aktualizace služby s project_details_v1 a potom
stejné aplikace bez odinstalace. Před živými změnami ověřit zálohu/otisky
archivu a střihů. Krok 6: fyzicky projít dvě cesty a celý přenos/Viewer/film.
Společný vícedenní film zůstává další samostatná etapa.
