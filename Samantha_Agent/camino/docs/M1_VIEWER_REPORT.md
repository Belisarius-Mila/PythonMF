# M1 — lokální minimalistický Viewer

Datum: 2026-09-25. Stav: implementace a syntetické testy hotové;
vizuální/browser přejímka otevřená. Bez nasazení a skutečných médií.

## Výsledek

- Volitelný read-only Viewer v existující FastAPI aplikaci: `/viewer/`,
  `/viewer/days/{datum}` a povolené mediální URL. Výchozí server se nezměnil:
  bez explicitního předání `viewer=` žádné Viewer routy nevzniknou.
- `RevisionStore.viewer_snapshot()` čte konzistentní transakční snapshot.
  Před šablonou vyřadí soukromé, skryté, neznámé či konfliktní zdroje,
  vypnutou cestu a režim obnovy. Nevrací GPS, soukromé vazby ani jejich počty.
  Text s nedoloženými/soukromými zdroji nevydá; lidská revize má přednost.
- Český HTML index/detail dne, escapované texty, úsporné foto a standardní
  audio/video ovládání. Bez externích zdrojů, frameworku, AI a JavaScriptu.
- Samostatná odvolatelná čtecí autorizace: prohlížečový Basic dialog,
  uživatel `jana`, vysokonáhodný čtecí token jako heslo. Tokeny spravované
  mimo HTTP v jiné databázi než owner; žádné tokeny v URL. Pro nasazení M2
  nutné soukromé HTTPS a samostatně vydané oprávnění, které zde nevzniklo.
- GET/HEAD včetně Range vždy ověřují současný výběr a čtecí token. Stará
  adresa po přijatém zámku nefunguje. Již vydané bajty nelze vzít zpět.
  Odpovědi mají no-store, nosniff, CSP a zákaz vložení do cizího rámce.
- Explicitní `build_pending()` vytváří jen kopie ověřených povolených médií:
  JPEG preview, H.264/AAC MP4+poster, AAC M4A. FFmpeg bez síťových vstupů,
  odstranění metadat/kapitol, neměnné originály. Hotová sada s hashovým
  manifestem se aktivuje atomickým přejmenováním soukromého adresáře.
  Neúplné výstupy se nevydávají ani automaticky nemažou.

## Ověření

- 29/29 cílených projekčních/C03b/media-store testů PASS (z toho 6 nových
  rychlých projekčních scénářů bez FastAPI).
- 7/7 nových HTTP/mediálních testů PASS v odděleném Camino prostředí.
  Stávajících 5/5 FastAPI testů také prošlo. Testy vytvářejí jen obrazový
  testovací vzor a tón, nikoli osobní fotografie/hlas.
- Doložené: odmítnutí neautorizovaného a owner přístupu do Vieweru, zákaz
  zápisu, odvolání tokenu, tajná věta, HTML escaping, provenance, zámek/skrytí,
  stará mediální URL včetně HEAD/Range, restore, neúplný upload, vadný převod,
  změněná cache, symlink, kontrolní součty původních bajtů beze změny.
- Skutečné deriváty prošly ffprobe, odstraněním vložené testovací polohy
  a komentáře a HTTP 200/206. První kontrola tagů falešně zaměnila technické
  `chroma_location` za GPS; kontrola byla zpřesněna na metadata tags a prošla.
- Plná projektová brána PASS: 1 776/1 776 testů (330,889 s), kontroly
  Python/JavaScript/shell syntaxe OK. Po závěrečném zúžení FFmpeg vstupních
  formátů znovu 7/7 HTTP/mediálních testů PASS (2,909 s).
- Prohlížečový smoke NEPROVEDEN: připojený browser provider nemá dostupný
  prohlížeč (`listBrowsers=[]`). Připraven samostatný syntetický HTML náhled
  k otevření Mílou; media jsou vložená do souboru. Není to produkční export
  ani důkaz Safari/Jana/privátní sítě. Zdroje pro opakování:
  `camino/server/tests/viewer_preview.py`. Předaný soubor ve Stažených:
  `Camino-M1-preview-20260925.html`.

## Hranice a další krok

- M1 není plně přijaté bez krátkého otevření náhledu v prohlížeči. Další krok:
  zkontrolovat zobrazení a spustit jedno audio/video. Neopakovat C04/C05b.
- Vícedílné audio: současný iPhone registruje Assety podle UUID a v API chybí
  pořadí session/částí a mezery (`CaminoSync.swift`, `CaminoSyncCoordinator.swift`).
  Proto Viewer nabízí samostatná média v pořadí přijetí s výslovným upozorněním,
  nikoli falešně souvislou nahrávku. Před ostrým nasazením dlouhých komentářů
  je třeba v navazujícím kroku doplnit minimální přenos pořadí; nelze jej
  spolehlivě odhadnout z UUID ani z délky. iOS ani wire kontrakt se v M1 neměnily.
- M2 přidá provozní registraci/správu, plánování derivátů, privátní HTTPS,
  reálnou čtecí autorizaci, odkaz z Cockpitu a test Jany. Při aktuální bráně
  `viewer_enabled=false` se nic samo nepublikuje; povolení cesty zůstává
  samostatná vědomá operace. Žádný živý server/Serve/Funnel zde nebyl změněn.
- M3 záloha stále chybí. Přijaté krátké výpadky ani tento Viewer nejsou záloha.
- Výkon velkých archivů není změřený: při výdeji se ověřuje hash derivátu,
  stránka se skládá aktuálně, ne z trvale publikovaného HTML. Běžný batch
  přeskočí již připravené kopie bez opakovaného čtení velkých originálů.
  Poškozená dokončená cache se neobnovuje přes existující adresář automaticky.
  To jsou známé limity lokálního M1, nikoli důkaz dlouhodobé odolnosti.

Technické reference: [FFmpeg — volby mapování a metadat](https://ffmpeg.org/ffmpeg.html).
Range byl ověřen přímo proti instalované Starlette 1.7.0; bez nových závislostí.
