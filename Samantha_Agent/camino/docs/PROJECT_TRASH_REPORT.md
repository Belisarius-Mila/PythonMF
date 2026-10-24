# Sedmidenní koš celé cesty a filmového projektu

Vývoj 24. 10. 2026 podle Mílova schválení. Jde o místní změnu zdrojů;
push, nasazení Cockpitu, aktualizace služby Camino, instalace iPhonu ani
mazání skutečných projektů nejsou součástí tohoto kroku.

## Následné p+n — 2026-10-24 17:56 CEST

Pět schválených commitů do `0a18db30` je publikovaných a Cockpit nasazený
přes jedinou Lunu. Účtenka `b75c48be083a1f26e8e7296ccf5997de`: completed,
push/deploy confirmed, plná brána 2232 PASS, smoke 5/5. Živě ověřený stamp
`7ae887842f089e5c`, GitHub/main shodné; chráněné služby nezměněné.
Automatický portálový návrat je nepotvrzený (`returned_to_adam=false`);
účtenku zde převzal a ověřil terminálový Adam.

Toto p+n aktualizovalo pouze společný runtime/Cockpit. Následně po samostatném
schválení a přesné globální větě proběhl upgrade služby na schéma 4 a stejné
iPhone aplikace na build 21 bez odinstalace. Původní archiv/316 SHA a Viewer
PASS, kontejner telefonu zachovaný. Míla později potvrdil spuštění 21 a
žádost o smazání; odhalený chybějící návrat je opravený v připravené IPA 22
([ověření](PROJECT_TRASH_NAVIGATION_REPORT.md)). Fyzický tok koše dosud
nepřijatý. Při servisním přechodu se skutečná data nemazala.
[Podrobnosti samostatného vydání](CLIENT_21_SERVICE_UPGRADE_REPORT.md).

## Používání po samostatném vydání

1. Na iPhonu otevři **Projekty → Upravit projekt → Požádat o smazání celé
   cesty**. Potvrzená žádost cestu skryje. Její nové přenosy se zastaví;
   přesné opakování již přidělených metadat se nejdřív bezpečně dokončí.
   Offline žádost zůstává uložená do dalšího povoleného spojení.
2. Na Macu otevři **Film Camino → Koš projektů a žádosti z iPhonu**.
   **Zkontrolovat rozsah** ukáže originály, záznamy, filmy a soubory na Macu.
   Telefon může obsahovat další nepřenesená data. Přesun do koše potvrdíš
   přesnou větou globální brzdy zobrazenou u žádosti.
3. Od potvrzení běží jedna sedmidenní lhůta podle UTC času Macu. Tlačítko
   **Obnovit projekt** vrátí práci před jejím koncem. U nepotvrzené žádosti
   lze rovnou zrušit žádost. Telefon převezme obnovení při příštím spojení.
4. Po lhůtě samostatný worker služby Camino trvale smaže spravovaná data
   Macu. Telefon maže až po autentizovaném potvrzení tohoto výsledku,
   dokončí místní výmaz a odešle ACK. Offline telefon zůstává viditelně
   nedokončený; nestačí posunout jeho hodiny nebo vypršet místnímu termínu.

Samostatný **Smazat celý film…** u uloženého filmu připraví žádost jen pro
film: všechny střihy, revize, importované a syntetické hlasy, pracovní
pokusy, náhledy a exporty. Následuje stejná kontrola a sedmidenní koš.
Zdrojová cesta a originály na iPhonu/Macu zůstávají. Nové výslovné založení
filmu po jeho výmazu používá novou identitu; staré URL/requesty jej neoživí.

## Co výmaz pokrývá

- Originály a upload sessions/chunks/staging/karantény příslušné cesty,
  včetně médií, jejichž projekci dříve odstranila oprava archivu.
- Viewer kopie a přiřazené nedokončené převody; oba filmové kořeny,
  včetně přiřazených nedokončených projektů.
- Trip/Day/Moment, všechny revize a texty, audio layouts, Viewer grant,
  konflikty a osobní obsah přijatých synchronizačních obálek.
- V iPhonu také nedokončené foto/video záměry, všechny audio pokusy vlastních
  sessions, dříve jednotlivě smazané záznamy, textové koncepty/historie,
  lokální GPS, přijatá historie fronty a připravená upload kopie.
- SQLite výmaz a kompakce na Macu i v telefonu; Core Data se znovu otevře
  podporovanou volbou VACUUM. ACK následuje až po úspěšné kompaktaci.

Zůstanou malé technické záznamy UUID, kurzoru, otisků přesných retry a výsledku
výmazu. Neobsahují původní názvy ani texty. Zabrání opětovnému vytvoření
projektu ze staré fronty/obnoveného telefonu a zachovají pořadí dalších cest.
Obsah putuje iPhone → Mac; opačně pouze řízení koše a potvrzení.

Koš nevytváří kopii médií a během sedmi dnů místo neuvolňuje. Starší zálohy,
Fotky/iCloud Photos a ruční exporty mimo spravované kořeny jsou samostatné.
Tato funkce je nemaže a neslibuje vymazání historických záloh/snapshotů.

## Ochrany a návaznost vydání

- Výmaz má uložený neměnný inventář a trvalé stavy `purging` a `compacting`; po přerušení
  pokračuje ve stejném rozsahu. Symlinky, nahrazené soubory a hardlinky mimo
  vybraný rozsah odmítá. Interní hardlinky exportů se počítají a odstraňují
  společně, předpokládané bajty se neduplikují za každý odkaz.
- Potvrzený rozsah váže skutečné kořeny dat. Služba s jinou konfigurací nebo
  nahrazeným kořenem nesmí tiše vynechat část potvrzených dat. Výsledek
  `purged` vznikne až po úspěšné kompaktaci; selhání VACUUM se znovu dokončí
  ze stavu `compacting` a iPhone zatím uchovává svoji kopii.
- Přenosy, Viewer převody a filmové zápisy/rendery drží společný zámek proti
  potvrzení/výmazu. Recovery po restartu nepřesouvá soubory z rozpracovaného
  výmazu do jiné karantény. Staré pakety se po výmazu obsahově nepersistují.
- Starší pracovní kopie bez ověřitelného přiřazení výmaz zastaví k ručnímu
  auditu. Nevymazávají se odhadem a výsledek se neoznačí jako dokončený.
- Metadata schéma přechází z 3 na 4. Starší služba schéma 4 odmítne;
  při vydání je nutný registrovaný upgrade služby včetně předchozího
  snapshotu. Cockpit samotný archiv nemigruje; bez nového schématu koš
  vrací požadavek na aktualizaci. Nový iPhone vyžaduje `project_trash_v1`.
- Samostatně autorizovaný upgrade služby a instalace buildu 21 jsou hotové;
  navazuje syntetická fyzická přejímka. Samotné p+n společného runtime
  tyto kroky nenahrazuje.

## Ověření

Syntetický kontrakt: 16 Python testů PASS, včetně HTTP autentizace, pozdního
uploadu, hranice sedmi dnů, restartu po částečném unlinku, obou filmových
kořenů, obnovení, ACK, staré fronty a zachování druhé cesty. DOM scénář
ověřuje rozsah, přesnou potvrzovací větu, obnovení a samostatný film.
Swift/Core Data: 87 testů PASS, včetně odstranění textu z SQLite/WAL,
reálného zmenšení databáze a zachování pořadí fronty.

Finální plná projektová brána PASS: 2232 testů, unit část
381,487 s. iOS Release build pro skutečný iPhone target PASS bez podpisu
a instalace. Finální cílená přejímka 20 PASS včetně DOM a route kontraktů.
Fyzický iPhone, Safari, skutečná sedmidenní produkční lhůta a uvolnění místa
živého projektu NEOVĚŘENO; vyžadují příslušné vydání a samostatnou přejímku.
