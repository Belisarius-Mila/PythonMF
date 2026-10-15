# Camino P2-C/D — editor a MP4 z uzavřeného dne

Stav: editor nasazený v Cockpitu; skutečný náhled 720p a finále 1080p jsou ověřené a dostupné.
Míla 12. 10. výslovně zadal pokračování editorem a MP4 nad potvrzenou Mac
sadou 6. 10. Telefon, běžící Camino, jeho archiv a síť se nemění.
Míla potvrdil „ok p+n cockpit“; přesný `7c9547fc` je na GitHubu a nasazený pouze Cockpit. Hotové MP4 se znovu nevyráběly.

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
výsledky i neúplné pokusy zůstávají zachované; žádný úklid ani mazání.

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
