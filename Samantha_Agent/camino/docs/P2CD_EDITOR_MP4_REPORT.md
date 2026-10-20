# Camino P2-C/D — editor a MP4 z uzavřeného dne

Stav k 20. 10. 21:23 CEST: oprava mazání `84336632` je nasazená a Mílou
přijatá, MP4 dnů 6 a 7 hotová. Po přesném úklidu čtyř osiřelých video metadat
projde 8. říjen validací se 44 zdroji; projekt tohoto dne zatím znovu neuložený.
Míla 12. 10. výslovně zadal pokračování editorem a MP4 nad potvrzenou Mac
sadou 6. 10. Telefon, běžící Camino, jeho archiv a síť se nemění.
Míla potvrdil „ok p+n cockpit“; přesný `7c9547fc` je na GitHubu a nasazený pouze Cockpit. Hotové MP4 se znovu nevyráběly.

## Trvalé smazání jedné varianty — 20. 10. 2026

Míla vyzkoušel vytvoření MP4 druhého dne a výslovně požaduje nevyhovující
varianty trvale odstranit kvůli místu. To mění původní zachovávání všech exportů.
U hotového filmu, dílčího náhledu a neúspěšného pokusu přibylo „Smazat natrvalo“.
Před potvrzením se zobrazí přesný profil/revize/časový úsek a celkový počet
a velikost souborů dané varianty. Seznam dílčích náhledů uvádí i jejich časy.

Smažou se všechny její pracovní pokusy: finální MP4, neúplná videa, segmenty,
PNG a ostatní pracovní soubory. Žádný koš, archivní přesun ani nová mediální
kopie. V původním adresáři úlohy zůstanou jen request, malý stav smazání
a nulový soubor zámku. Tato technická metadata neobsahují média a brání
tomu, aby starý request ID znovu vytvořil smazaný výstup.

Přesná potvrzovací věta je vyžadovaná podle `global_safety_brake.md` pro
mazání adresářů a více souborů. Potvrzení je vázané na serverový plán konkrétní
varianty; změněné soubory vyžadují nové ověření. Originály, uložené revize
střihu, jiné varianty a zdrojové náhledy se touto akcí nemažou.

Zámek chrání před souběhem s renderem a ostatními zápisy stejné střižny. Aktivní
render a čekající varianta se odmítají; symbolické odkazy, pevné odkazy mimo
vybranou variantu a jiný disk se neprocházejí. Pracuje se pouze přes ověřené adresáře a jejich
deskriptory. Před prvním odstraněním se atomicky uloží stav `delete_pending`
s identitami potvrzených souborů bez jejich obsahu. Pád tak neobnoví výdej
nebo render; „Dokončit smazání“ odstraní zbývající členy téže sady.
Úspěšně smazaná varianta se už nenabízí a starý GET/HEAD/Range vrací 404.
Příliš velký záznam pro obnovu se odmítne ještě před prvním odstraněním;
editor musí umět svůj stav mazání po pádu znovu načíst.

Místní přehrávání vybrané varianty se zastaví před odstraněním. Jiný již
otevřený přehrávač/stahování může držet bloky do zavření souboru. Při mazání
se nevytváří kopie; existující stažené soubory, externí/iCloud zálohy a APFS
snapshoty jsou mimo tuto operaci. Nejde o bezpečný přepis SSD.

Původní implementace: 71 cílených a 2 146 plných testů PASS, nasazení `3b129ded`
potvrzené. Následná fyzická zkouška mazání FAIL; oprava viz poslední záznam níže.
Produkční varianty se během vývoje nemažou. Důkazy `camino_export_delete_*_20261020.log`.

## Moje filmy a výběr dnů — 20. 10. 2026

Po Mílově přijetí prvního filmu/střihu přibylo otevření dříve uloženého
projektu a výběr dalšího Mac dne. Jde o více samostatných jednodenních filmů;
společný vícedenní film, kapitoly a prolog/epilog P2-F zůstávají další etapou.

Přehled nabízí jen aktuálně ověřené projekty nakonfigurované cesty. U každého
uvádí den, revizi a počet hotových filmových exportů; zdrojové náhledy se do
počtu nezahrnují. Seznam Mac dnů vychází z povolených obrazových zdrojů,
vynechá soukromé/skryté dny a není potvrzením dokončeného přenosu.
Nový projekt vznikne teprve po výslovném potvrzení konečnosti vybraného dne,
úplné validaci jeho inventáře, originálů a účtenek. Originály se nemění.

Výběr má každá karta vlastní, připomene si jej v `sessionStorage`; server nemá
globální aktivní den. Editor, uložení, zdrojový náhled, worker a výdej MP4
používají konkrétní projektové ID. Nepovolené parametry a nesoulad dne s ID
jsou odmítnuté. Původní cesty bez parametru zůstávají kompatibilní s 6. 10.

Přepnutí blokuje probíhající nebo nepotvrzené uložení. Při výpadku spojení
editor skryje staré zdroje a zachová koncept v kartě; po obnovení lze úpravy
uložit. Pozdní odpověď starého projektu ani jiná karta nemění nový výběr.
Koncept není trvalá záloha po násilném zavření karty; uložené revize jsou
trvalé. Aktuální soukromí a integrita se ověřují i při otevření a výdeji.

Ověření: 60 cílených testů PASS, včetně dvou syntetických dnů s oddělenými
revizemi a exporty, workeru druhého dne, odmítnutí cizích zdrojů/výstupů,
read-only přehledu, změny soukromí, HTTP Origin/parametrů a UI závodů.
Plná brána 2 137/2 137 PASS (415,624 s testů). Produkční film zůstává v revizi 5,
osm původních JSON souborů a šest hotových výstupů má shodné SHA-256.
Žádný produkční projekt ani render nevznikl. Logy `camino_film_library_*_20261020.log`.

Po samostatném nasazení pouze Cockpitu přejímka:

1. Otevřít Camino film a v „Moje filmy“ původní den; ověřit poslední střih
   a přehrání stávajícího exportu.
2. Zvolit jiný den. Až když jsou jeho Mac data konečná, potvrdit uložení
   nového projektu. Neúplné či změněné zdroje musí vznik projektu zablokovat.
3. Upravit jednu délku fotografie nebo ruční úsek videa, vyčkat na uloženou
   revizi, obnovit stránku a zkontrolovat změnu. Náhled/export zadat vědomě.
4. Vrátit se k původnímu projektu: jeho střih, revize i starší exporty musí
   zůstat dostupné a shodné. Dvě karty musí držet nezávislý výběr.

Fyzický retest nového přehledu na Macu/iPhonu nebyl proveden; nástrojový
prohlížeč není dostupný. Mílovo hodnocení prvního filmu je uživatelský důkaz,
nikoli samostatný PASS každého staršího P2-C/E přejímacího úkonu.

## Editor

Film Camino zachovává původní projekt a nabízí všechny jeho povolené zdroje.
Záběry lze řadit, výslovně vyřadit, upravit titulek, délku fotografie,
ruční in/out videa a hlasitost. Vyřazení nikdy nemaže původní médium.
Výchozí videa jsou celá. Každý platný střih se automaticky ukládá do nové
create-only revize; původní návrh a všechny uložené úpravy zůstávají.
Optimistická kontrola revize zabrání přepsání z jiného okna. Retry stejného
požadavku neduplikuje uloženou revizi.

Povolené zvukové části se nabízejí celé, vypnuté do výslovného umístění.
Uživatel volí čas ve filmu, in/out i hlasitost. Překrytí více komentářů
nebo přesah za obraz se odmítne s vysvětlením; je třeba vědomě upravit
umístění nebo prodloužit obraz. Zvuk videa se při komentáři ztiší na
uživatelův poměr, výchozí 0,2. Žádná generovaná řeč, hudba ani AI.

## Export a obnova

Náhled 720p, finále 1080p/16:9 a dílčí pracovní úsek používají přesnou
uloženou revizi a manifest. Starší výsledek je označený svou revizí.
Soukromá fronta je trvalá, idempotentní a serializovaná systémovým zámkem.
Po vědomém zadání exportu běží samostatný místní proces; změna stránky či
restart Cockpitu ho neukončí. Neinstaluje se služba ani LaunchAgent.
Přerušený export se opakuje od začátku v novém adresáři. Starší hotové
výsledky i neúplné pokusy zůstávají zachované do výslovného trvalého smazání
jedné varianty popsaného výše; automatický úklid není zapnutý.

FFmpeg běží s nice 10, dvěma vlákny a jedním filtrovacím vláknem. Záběry se
normalizují postupně. Fotografie mají pracovní PNG hlavního obrazu, EXIF
otočení a případný ICC převod do sRGB, bez metadat; vícevrstvé MPO se nesmí
přímo smyčkovat jako video. [Pillow dokumentace MPO](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#mpo)
popisuje hlavní obraz a další vrstvy. Videa respektují vlastní rotační
matici a celý rám bez automatického ořezu. HDR video se nyní bezpečně
odmítá; tento den má ověřené SDR video zdroje. HDR gain map fotografií se
neaplikuje; výsledkem je jejich standardní hlavní SDR obraz.

Po spojení pracovních segmentů dostane audio časovou bázi 48 kHz a
souvislé PTS podle počtu vzorků (`asettb=1/48000,asetpts=N/SR/TB`), podle
[oficiální dokumentace FFmpeg](https://ffmpeg.org/ffmpeg-filters.html#setpts_002c-asetpts).
Tím se odstraní malá překrytí milisekundových časů mezi PCM segmenty.
Kontroluje se počet video snímků, délka obou stop, H.264/AAC, rozměry,
celé dekódování i hash. Zdrojové soukromí, integrita a neměnnost revize se
ověřují před renderem, mezi záběry a před publikací. MP4 se zpřístupní až
po úplné validaci; každý GET/HEAD/Range znovu kontroluje aktuální povolenost.
Originály se nikdy nevydávají novou filmovou HTTP cestou.

První reálný pokus odhalil PCM timestamp kolizi a MPO vedlejší vrstvy,
které běžný smyčkový dekodér zaměňoval za další obrazy. Oba neplatné výstupy
byly správně zadrženy. Opravy mají syntetické regresní testy pro mnoho
zlomkových střihů a otočené dvouvrstvé MPO, včetně posledního snímku.

## Hranice první verze

Jeden uzavřený den, nejvýše 256 zdrojů a 60 minut obrazu, fotografie do
300 sekund, 16 rozpracovaných exportů. Žádné automatické doplňování
nehybného závěru, automatický výběr kratšího obsahu ani změny P0.
Filmové soubory jsou mimo Git a archiv. Browser/Safari a celý lidský
poslech jsou samostatná fyzická přejímka; decode/hash nejsou lidský PASS.
Staženou cizí kopii nelze pozdější změnou soukromí odvolat.

## Důkaz skutečného dne

Oba profily vycházejí z revize 1 a stejného edit/manifest otisku. Zahrnují
25 záběrů: 11 foto a 14 celých videí. Pět samostatných hlasových částí
zůstává k výslovnému umístění, první sestavení zachovává zvuk videí.
Časová osa 200 475 ms, skutečné video 200 465 ms / audio 200 466 ms;
6014 snímků v obou MP4. Všechny záběry náhledu byly vizuálně prohlédnuté.

| Profil | Rozměr | MP4 bajtů | Render sekund | Špička pracovního adresáře, alokované B |
| --- | --- | ---: | ---: | ---: |
| Náhled | 1280×720 | 25 617 860 | 135.034 | 101150720 |
| Finále | 1920×1080 | 115 011 021 | 181.017 | 291872768 |

Špičky jsou 50ms měření jednoho pracovního adresáře, nikoli celého APFS.
Neúplné starší pokusy zůstávají v historii a nevydávají se. Hash náhledu:
`2e979374f63ba8dbeb3a1171a6142679d7167414e65604aaf0f265d328b766f4`.
Hash finále:
`3013f072f34d6e7654c17e44955fec5de950811629bb62e4c33a5a09a3c542ee`.

Izolovaný skutečný Cockpit HTTP: root/editor 200, revize 1, 25 obrazových
a 5 zvukových nabídek, oba MP4 Range 206 a HEAD 200. Čerstvý audit Camina:
owner HTTP/HTTPS zdravé, Viewer/mapa/map-data 200, foto/audio/video Range 206,
anonymní Viewer 401. Archiv před/po přesně shodný: 624 operací, 82 Momentů,
216 originálů, 1 673 901 399 B, stejné identity/tripy a všechny SHA-256.
Serve otisk beze změny, Funnel off. Telefon a Camino služba se neměnily.
Po autorizovaném nasazení běží pouze nový Cockpit PID 35526/otisk
`4f1f0c17ac72659f`, účtenka `deployed`, smoke 5/5. Camino zůstává PID 67017
a release `e95568b7999e`. Živý HTTP/HTTPS root/editor 200 a oba MP4
HEAD 200 / Range 206; všechny odpovědi mají přesné bajty původních výstupů.
Celé 1080p finále stažené přes HTTPS má shodný SHA-256 uvedený výše.
Zopakovaný audit všech 216 originálů, identity/tripů a Serve je přesně
shodný; nevznikl nový render a žádná Camino/síťová změna.

Cílené testy editoru, HTTP, JS, souběhu, obnovy, soukromí a skutečných
renderů PASS. Závěrečná plná brána **1907/1907 PASS** (319,041 s testů).
Nová sada editoru má 19/19 testů PASS, včetně skutečného renderu
720p/1080p, zlomkových střihů a MPO/EXIF/ICC. Nový editor je publikovaný a nasazený pouze do Cockpitu.
Míla 12. 10. oznámil první hodnocení filmu OK a ocenil strukturu editoru;
ovládání vyzkouší 13. 10. Jeho zařízení, profil a rozsah poslechu nejsou
uvedené. Podrobná P2-E přejímka ovládání a ručního komentáře čeká.
Nástrojová browser QA neměla dostupný prohlížeč.

## Publikační ověření

[GitHub brána 38285925799](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38285925799) nasazeného `7c9547fc` má success: 1907 testů OK, 13 podmíněně přeskočených, 203,452 s. Skutečné render testy a všech 19 editor testů prošly místně bez přeskočení.

## 2026-10-12 20:14 CEST — uživatelské hodnocení a předání

Míla 12. 10. hodnotí první skutečný film „na první dobrou ok“ a strukturu editoru dobře. Ovládání vyzkouší 13. 10.; není hlášená chyba vyžadující dnešní opravu.

13. 10. ověřit ovládání: změnit pořadí dvou záběrů a délku jedné fotky, vyčkat uložení, obnovit stránku a přehrát dílčí náhled. PASS: pořadí i délka zůstanou uložené a náhled odpovídá střihu.


## 2026-10-15 19:40 CEST — živý návrat ke střižně a doporučení dalšího kroku

Míla po přijetí opravy přenosu požádal o prohlídku střižny a návrh dalšího
vývojového kroku. Registrovaný Mac film status a běžící editor potvrdily
platný projekt 6. 10., revizi 1, 25 obrazových záběrů (11 foto/14 videí),
pět samostatných hlasových nabídek, z nichž žádná není zapnutá, a stopáž
200 475 ms. Oba hotové 720p/1080p MP4 jsou přes HTTP i soukromé HTTPS
dostupné HEAD 200 / Range 206, se stejnými velikostmi 25 617 860 B
a 115 011 021 B. Nový projekt, úprava ani render se nespustily.

P2-C/E ruční ovládání na iPhonu a první vlastní uložený střih stále čekají
na přejímku. Zdroj `film_editor.js` nabízí in/out číselně a tlačítko
náhledu záběru zadává dílčí render; API neposkytuje přímý zdrojový přehrávač.
Nejde o nástrojový browser klik ani fyzickou Safari přejímku.

Doporučený malý krok k rozhodnutí: přímý náhled vybraného videa ve střižně,
posun po záznamu a tlačítka „Tady začít“ / „Tady skončit“, pak přehrání
vybraného úseku bez nového renderování celého filmu. Číselné hodnoty
zůstanou dostupné pro upřesnění. Výchozí video zůstává celé, ruční trim
je výslovný, ukládá se nová revize. První přejímka nad dnem 6. 10.:
zvolit úsek, uložit/reload, ověřit odpovídající náhled/MP4 a zachovaný
celý originál i revizi 1. Později také dosavadní změna pořadí/délky fotky.

Návrh je pouze doporučení, dnešní zadání není implementační autorizace.
Při realizaci použít chráněné odvozené náhledy nad stejným uzavřeným
manifestem, kontrolovat aktuální soukromí a nevydávat originály novou
HTTP cestou. Rozsah má být uvnitř filmové střižny v Cockpitu bez změn
telefonní aplikace a přenosové služby. P2-F vícedenní film zůstává později.
Důkaz `logs/camino_film_return_audit_20261015.log`; pouze zápisy, bez renderu.

## 2026-10-15 20:09 CEST — přímý náhled videa a ruční označení střihu

Hotovo:
- Ve střižně je místně připravené otevření celého videa, posun v přehrávači, „Tady začít“, „Tady skončit“ a „Přehrát výběr“. Číselné upřesnění zůstává; změny používají dosavadní automatické ukládání nových revizí.
- Chráněný 720p náhled zdroje se připraví jednou v dosavadní sériové frontě a při dalším otevření se znovu použije. Výběr se přehrává bez renderování filmu. Náhled zdroje neobsahuje titulek ani samostatný hlas; ty patří do renderovaného střihu.
- Originály, uložené revize a výchozí celé video jsou zachované. Živý audit v 19:58 CEST: přesná shoda archivu s podkladem před vývojem, všech 300 originálů / 2 316 799 213 B SHA-256 PASS, 883 operací, flags false a stejný Serve; Camino stále běží na `f60a33c98fd5`. Skutečný film 6. 10. zůstal v revizi 1, bez nového produkčního renderu či změny střihu.

Rozhodnutí:
- Míla „ok, jdeme na to!“ výslovně schválil realizaci navrženého přímého náhledu a ručního trimu v Cockpitu. Rozsah neobsahuje nový telefonní build, změnu přenosové služby, push ani nasazení.

Další krok:
- Po samostatném pokynu nasadit pouze Cockpit a na iPhonu vybrat úsek jednoho videa ze 6. 10., uložit/reload a porovnat s náhledem výsledného filmu.

Navrhované další kroky:
- Dokončit P2-C/E fyzickou přejímku: ruční úsek, pořadí záběrů a délka fotografie; původní revize i celé video musí zůstat dostupné.
- P2-F vícedenní film až po přijetí ovládání prvního dne.

Technický důkaz:
- 23/23 cílených editorových testů PASS, včetně skutečné odvozeniny celého videa a renderu ručního úseku: barvy/snímky, délka, svislý celý obraz, odstranění soukromých metadat, nezměněný SHA originálu. Node test ověřuje tlačítka, čísla, uložení/reload, konec přehrání, chybu média, pozdní odpověď a odvolání soukromí. Plná brána 1940/1940 PASS.
- Registrovaný POST `/api/camino/film/source` připravuje jen odvozeninu; dosavadní chráněný output kontroluje manifest, aktuální soukromí a hash pro GET/HEAD/Range. Originál se nevydává. Ověřeno odmítnutí cizího Origin, soukromého/cizího zdroje, poškozeného náhledu a změny soukromí během renderu i před výdejem.
- Důkazy: `logs/camino_film_trim_final_tests_20261015.log`, `logs/camino_film_trim_gate_final_20261015.log`, `logs/camino_film_trim_live_audit_20261015.log`, `logs/camino_film_trim_smoke_20261015.log`; report `camino/docs/P2CD_EDITOR_MP4_REPORT.md`. Nástrojový prohlížeč není dostupný; fyzická Safari/iPhone přejímka neprovedena.

Implementační kontrakt:
- POST `/api/camino/film/source` přijímá jen `project_id`, `asset_id`, `request_id`; vyžaduje video z ověřeného uzavřeného manifestu a stejné přístupové/Origin kontroly jako ostatní zápisy editoru.
- Interní pracovní draft obsahuje jediný celý vybraný zdroj bez titulku a samostatných hlasů, odvozený z neměnné revize 1. Nevzniká uložená edit revize. Zdrojové úlohy jsou v API odlišené `source_asset_id` a nezobrazují se jako výsledné filmy.
- Stejný renderer, soukromé adresáře, sériový worker, kontrola místa, celé dekódování a hash. Staré výstupy i neúplné pokusy zůstávají zachované. Opětovné otevření používá hotový ověřený náhled, po poškození se vytvoří nový pokus.
- Kontrola konce přehrávání přes čas videa a krátký časovač; čísla v milisekundách, výstup kvantovaný na dosavadních 30 fps. Tlačítka zachovávají úsek alespoň 0,1 s, konec za začátkem a v délce média.
- Ovládání se povolí po načtení metadat. Pozdní odpověď předchozího výběru ani zavřeného okna neobnoví staré video. Chyba média, skrytí stránky, odvolání soukromí nebo zavření vyčistí přehrávač.

Aktualizovaný kontrolní otisk stránky odpovídá přidaným ovládacím prvkům; 18/18 frontendových kontraktních testů PASS. Závěrečná plná brána 1940/1940 PASS (326,925 s testů). Žádný push ani nasazení v tomto kroku.

## 2026-10-15 20:26 CEST — p+n, skutečný náhled a prostředí filmového workeru

Hotovo:
- Schválená dávka čtyř commitů je na GitHubu, `298b6dc2` má úspěšnou vzdálenou bránu. Cockpit byl řízeně přepnutý, nový proces ověřený a smoke 5/5.
- Skutečný pokus o zdrojový náhled zachytil rozdíl oproti terminálu: launchd nemá v PATH místní FFmpeg/FFprobe. Neúspěšný pokus zůstal zachovaný, nic se nevydalo.
- Místní oprava rozšiřuje PATH výhradně novému filmovému workeru o známé instalační adresáře, dosavadní výběr nástroje má přednost. Nemění rodičovský proces, macOS konfiguraci, přenosovou službu ani síť. Pod omezeným PATH už skutečný samostatný worker vytvořil ověřený celý náhled 6 732 ms / 988 097 B; revize 1 a střih zůstaly shodné.

Rozhodnutí:
- Mílovo „ok p+n“ schvaluje push a nasazení pouze Cockpitu včetně nutné opravy nalezené při živém ověření. iPhone IPA ani služba Camino se nepřepínají.

Další krok:
- Dokončit bránu opravy, push a druhé řízené nasazení Cockpitu; potom ověřit nové video přes HTTP/HTTPS a zachování archivu.

Navrhované další kroky:
- Po úspěšném nasazení fyzická přejímka iPhone úsek/save/reload/náhled. P2-F až později.

Technický důkaz:
- 24/24 cílených testů PASS, včetně dohledání mediálních nástrojů při službovém PATH bez změny rodiče. Plná brána 1941/1941 PASS.
- První nasazení `298b6dc2`: PID 70357, stamp `9b76cb02cb956175`, receipt deployed a smoke 5/5. [GitHub brána 38784392159](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38784392159) success. Skutečný omezený worker: úplné dekódování a SHA-256 `70aa61e3ab27a85078bf20adf33ee86e94e0814f58f415f04ef56d339b8b4ab6` PASS; nejde o fyzický poslech.
- Archiv před/po prvním nasazení přesně shodný: 883 operací, 123 Momentů, 300 originálů / 2 316 799 213 B SHA-256 PASS, flags false. Camino stále `f60a33c98fd5`, PID 47332, konfigurace i Serve shodné, Funnel off. Produkční střih revize 1 a oba hotové filmy zůstávají zachované. Důkazy `logs/camino_film_trim_predeploy_20261015.log`, `logs/camino_film_trim_postdeploy_20261015.log`, `logs/camino_film_trim_worker_live_20261015.log` a worker test/gate logy.

## 2026-10-15 20:29 CEST — dokončené p+n střižny a skutečný náhled z Cockpitu

Hotovo:
- Nové ovládání střižny je pushnuté a nasazené pouze do Cockpitu, včetně opravy prostředí filmového workeru. Řízený restart doložil nový proces a povinný smoke 5/5.
- Běžící Cockpit přes nový POST připravil další dosud nenachystané celé video: 8 763 ms / 1 484 481 B, celé dekódované a hash ověřený. Je tak ověřené skutečné spuštění workeru z macOS služby, ne jen terminálový render.
- Oba původní filmy a nový zdrojový náhled: HTTP i soukromé HTTPS HEAD 200 / Range 206, ověřené TLS. Revize 1 a celý střih před/po shodné; žádný nový render celého filmu. Jeden původní neúspěšný zdrojový pokus i dva hotové odvozené náhledy zůstávají zachované.
- Závěrečný audit: 883 operací, 123 Momentů a všech 300 originálů / 2 316 799 213 B se shodnými SHA-256; flags false, stejný server `f60a33c98fd5`, PID 47332, konfigurace i Serve přesně shodné, Funnel off. Owner API HTTP/HTTPS i anonymní odmítnutí PASS. Telefonní IPA a přenosová služba se nepřepínaly.

Rozhodnutí:
- Dokončeno Mílovo „ok p+n“ pro střižnu v Cockpitu. Nutná PATH oprava se omezuje na nový filmový worker, bez systémových změn.

Další krok:
- Na iPhonu obnovit Cockpit, otevřít Film Camino, u videa „Otevřít video pro střih“, posunout/označit začátek a konec, přehrát výběr, vyčkat uložení a ověřit zachování po reloadu. Potom porovnat renderovaný náhled s ručním střihem.

Navrhované další kroky:
- Dokončit P2-C/E fyzickou přejímku také pořadím dvou záběrů a délkou fotografie. P2-F vícedenní film až potom.

Technický důkaz:
- Kód `ff87ee2d`, runtime otisk `ba5bfa185ffd57b9`, receipt deployed, nový proces potvrzený, smoke 5/5. Plná místní brána 1941/1941 PASS (331,381 s testů), cílené testy 24/24 PASS; při nasazení opakovaná statická brána nad shodným kódem.
- Skutečný nový náhled SHA-256 `53170d49201fb43ec7d381124e9a2644c65d26903f5c9f5a125962cc1a27f173`. Důkazy `logs/camino_film_trim_worker_deployed_20261015.log`, `logs/camino_film_trim_final_preview_20261015.log`, `logs/camino_film_trim_final_archive_20261015.log`. Předchozí `298b6dc2` má vzdálenou bránu success; nová [GitHub brána 38785696792](https://github.com/Belisarius-Mila/PythonMF/actions/runs/38785696792) při zápisu ještě běží, její případné nahrazení dalším dokumentačním pushem není výsledek testů.
- HTTP/API/render důkaz nenahrazuje fyzické ovládání a poslech na iPhonu. Nová telefonní přejímka zatím neprovedená; celá videa, uzavřený manifest a starší revize zachované.


### 2026-10-20 17:51 CEST — Oprava mazání skutečných filmových výstupů

Hotovo:
- Dohledaná příčina Mílova neúspěšného mazání po nasazení: ochrana odmítla
  dva interní názvy téhož MP4 vytvořené samotným rendererem. Produkční mazání
  nezačalo; restart nemohl varianty odstranit.
- Místní oprava uznává pouze plně vnitřní pevné odkazy a zahrnuje pracovní
  podadresáře. Před každým odstraněním znovu kontroluje identitu a zbývající
  počet odkazů; přerušení mezi názvy lze bezpečně dokončit.
- 42 cílených testů PASS, včetně skutečného render → smazání. Všech 10 živých
  variant projde pouze čtecím inventářem; 570 původních souborů shodných.

Rozhodnutí:
- Bez změny rozsahu: konkrétní varianta, potvrzený plán a globální brzda.
  Žádné produkční mazání během opravy, nové kopie ani automatický p+n.

Další krok:
- Po samostatném p+n pouze Cockpitu zopakovat skutečné smazání nepotřebného
  náhledu a ověřit zmizení po reloadu při zachování ostatních variant.

Navrhované další kroky:
- Další připomínky střihu druhého dne, společný vícedenní film P2-F až později.

Technický důkaz:
- Plná brána opravy 2 151/2 151 PASS (323,406 s testů), `camino_export_delete_fix_gate_20261020.log`.
- Logy `camino_export_delete_fix_reproduction_20261020.log`,
  `camino_export_delete_fix_targeted_20261020.log`,
  `camino_export_delete_fix_production_readonly_20261020.log`.
- Původní vydání `3b129ded` potvrzené účtenkou `cb5a8c476ff62f035fbf48241bccafe4`,
  2 146 plných testů a smoke 5/5. Oprava je samostatný místní krok.

Implementační doplnění:
- Inventář připouští pevné odkazy pouze při shodě počtu všech názvů inode uvnitř
  varianty se skutečným st_nlink. Při unlink se tento počet snižuje a ověřuje.
  Zbývající inventář po přerušení musí být podmnožinou původně potvrzené sady.
- Podadresáře pracovních pokusů mají limit hloubky 8 a 4 096 položek;
  obnovovací JSON zůstává omezený na 950 kB. Symlinky, jiná zařízení a neznámé
  položky v kořeni úlohy jsou odmítnuté; žádné obecné rm/rmtree.
- Uváděná velikost je logický součet souborových jmen, včetně interních
  hardlinků; není to měření fyzicky uvolněného APFS místa.


### 2026-10-20 21:23 CEST — Odstranění osiřelých záznamů čtyř videí z 8. října

Hotovo:
- Osmý den znovu projde ověřením pro založení filmu: 24 fotografií,
  14 videí a 6 zvuků. Odstraněny právě čtyři záznamy videí, která Míla po
  přenosu metadat, ale před přenosem souborů smazal na telefonu.
- Ostatních 304 originálů, 894 přijatých operací, 124 Momentů, synchronizační
  identita/kurzor, ostatní tabulky a všechny existující filmové soubory zachované.
- Původní Camino služba obnovená a zdravá přes HTTPS; konfigurace a síť shodné.
- Míla již potvrdil funkční mazání variant po nasazení `84336632` a má MP4 dnů 6 a 7.

Rozhodnutí:
- Míla přesnou větou globální brzdy potvrdil tento konkrétní úklid čtyř osiřelých
  položek. Pouze živý Asset inventář, historické synchronizační obálky zachované.
- Žádné další mazání telefonu, originálů, filmů ani obecná změna serverového kontraktu.

Další krok:
- V Cockpitu znovu uložit projekt 8. října a pokračovat střihem/MP4.

Navrhované další kroky:
- Při dalším běžném kontaktu ověřit synchronizaci telefonu; P2-F později.

Technický důkaz:
- Kopie v paměti před potvrzením PASS; ostrý offline SQL zásah až po snapshotu,
  přesném porovnání plánu a uzamčení filmových zápisů. 4 řádky odstraněné,
  304 zůstaly, 10 ostatních metadata tabulek a celá media DB shodné.
- FK/quick_check PASS; všech 304 originálů / 2 339 685 533 B SHA-256 PASS,
  797 filmových souborů beze změny; původní projekty 6 a 7 platné, den 8 validní.
- HTTPS owner health 200, Cockpit katalog OK. Další fyzický kontakt telefonu
  neověřený. Log `logs/camino_metadata_cleanup_20261020.log`, detail a snapshot private.

## 2026-10-20 22:23 CEST — Otevření fotografií ve střižně

Fotografie mají lokálně Otevřít fotografii v nové kartě a nemají renderovaný náhled záběru. Read-only PNG bez EXIF/GPS a bez diskové kopie; správné natočení/ICC, aktuální projekt/soukromí/hash a kontrola po dekódování. Video ovládání zachované. Funkční kód skutečně vytvořila Luna, Adam zkontroloval a převzal; opravil pouze citaci old, testové literály, úklid testserveru a složený frontendový otisk.

Skutečný model gpt-6-luna/high; původní job d67ea8e3a4c26b3c088fd33a821194e8, přijatá kontrola 393b9e1a2d6920d7ed27d41c74473cea, 4 původní FAIL → 4 PASS. Další modelový pokus neproběhl, původní odhad 0,161725 Standard, kontrola 0. Node PASS; integrační běh 69 testů, po opravě jediného fixture rozměru původních 68 PASS + konkrétní 1 PASS. Statická brána PASS. Důkazy logs/luna_photo_accepted_20261020.log, luna_photo_integration_tests_20261020.log, luna_photo_frontend_contract_final_20261020.log.

Ověřit finální účtenku schváleného p+n 92b4b7704c6503fb8b2ed300b600c7f9 a živý audit. Při completed navázat fyzickou přejímkou fotografie v Cockpitu na Macu/iPhonu; p+n slepě neopakovat. Tento Git checkpoint zachycuje stav před vydáním; výsledek publikace/nasazení je v přesné účtence a logs/luna_photo_release_20261020.log.
