# Podklady obnovy Samanthy — 25. 11. 2026

Tento dokument je netajný podklad pro sjednocený obnovovací návod. Stav je
časově omezený na níže popsaný čtecí audit; není to důkaz fyzické obnovy Macu.

## Správce návodu a současný způsob práce

Agent Samantha používá Codex App Server, hlavní checkout a oddělené pracovní
kopie. Historické pojmenování Agent SDK není pokyn k migraci architektury.
Role a jejich schválené modely spravuje config/agent_roles.json. Po obnově
nepřebírat model ani rozpočet z paměti; ověřit skutečný aktuální stav repozitáře.

Hlavní provozní návod je OBNOVA_SAMANTHY_NOVY_MAC.txt v kořeni PythonMF,
druhá provozní kopie je v iCloud Dokumentech. Kopie na Ploše a starší soubor
v Downloads nejsou automaticky autoritou. Při auditu byly provozní kopie
shodné a měly datum 8. listopadu. Datum nové redakce není datum externí zálohy.

Týdenní správce má label com.samantha.recovery-guide, interval kontroly900s
s výběrem nejnovějšího splatného nedělního slotu od09:00 Europe/Prague.
Nejde o placené spuštění každých15 minut. Má vlastní privátní aktivaci,
stav a schválenou roli recovery_document_maintainer, Sol/medium Standard,
mez200 kreditů/běh a1000/měsíc. Při auditu neměl dokončený týdenní slot:
čekal na runtime proof pro0.163.0, zatímco sdílený server byl0.169.0.
Revalidace runtime je samostatný přesný syntetický pokus; bez důkazu
nepřepisovat runtime_evidence ani nevypínat ochrannou bránu.

Registrovaný recovery_service_archive_preserve vytváří pouze nový soukromý
archiv v Samantha_Agent/data/private/recovery-service-archives. Obsahuje
konfiguraci a žurnály správce, bootstrap návod, protokolové důkazy pro
Standard, dvě vlastněné definice LaunchAgentů a konzistentní databázi FR.
Dokončený manifest ověřuje SHA všech souborů; změna zdroje, symlink nebo
překročení rozsahu zastaví dokončení. Nejde o instalaci zachycených plistů.
Pro obnovu vybrat dokončený archiv obsažený ve skutečném recovery snapshotu,
ověřit jeho manifest a upravit cesty až podle nového vlastněného zařízení.

Aktivní správce původně běžel ze stálé Data pracovní kopie mimo hlavní
PythonMF. Samotná recovery hlavního checkoutu proto nezaručuje zachování
jeho soukromé aktivace a žurnálů. Po ztrátě Macu určit umístění z ověřeného
servisního doplňku, obnovit stavy a sestavit novou definici pro nové cesty.
Neobnovovat starý plist slepě a nespouštět druhý správce. Bez kompletního
ověřeného runtime proofu, limitů, přijatého návodu a historie nejistých pokusů
musí zůstat nová aktivace vypnutá.

## Francouzština Jana a společné pexeso

Od24.11. je přijatý bezplatný soukromý provoz na zapnutém Macu přes Tailscale
Serve. Samostatná služba com.samantha.vocabulary-fr používá soukromé HTTPS8443
na loopback8792. Soukromý hostname se při obnově odvozuje z nového vlastněného
zařízení a schválené sítě; není správné kopírovat jméno zaniklého Macu.
Funnel se nezapíná, nepřidávat granty ani neměnit Cockpit/Camino trasy.

Kód služby je app/vocabulary_fr_tailnet.py a app/vocabulary_fr_multiplayer.py.
Veřejný klient je docs/vocabulary-fr; hlavní vstup Francouzština Jana
v Cockpitu zachovává původní Pages původ osobního učení a do fragmentu
předává ověřenou adresu živé soukromé herní služby. Samotné Pages nejsou
herní server. Dočasné Cloudflare adresy nejsou trvalou obnovovací adresou.

Soukromé herní stavy, rooms.sqlite3, konzistentní SQLite zálohy, neměnné
exporty a účtenky plánů jsou v Samantha_Agent/data/private/vocabulary-fr-tailnet.
Zdrojový GitHub nenahrazuje tuto databázi ani ostatní ignorovaná data.
Pro recovery zvolit dokončenou konzistentní zálohu databáze a ověřit její
integritu. Nemíchat soubory živé SQLite z různých okamžiků. Místnosti mají
běžnou expiraci24h /2h bez aktivity; kopie databáze tuto platnost neprodlužuje.

Po obnově zdrojů a Python prostředí použít registrovaný PrivateGame.prepare
pro přesný čistý commit a nové schválené soukromé zařízení. Před zapnutím
zkontrolovat plán, existující služby, porty a původní síť. Aktivace je
samostatná systémová akce s přesnou globální potvrzovací větou. Nevytvářet
obecnou veřejnou proxy, nepřebírat cizí PID/label a nic automaticky nemazat.

Aktualizace25.11. zachovává při změně filtru místnost a hráčské přístupy:
zakladatel rozehrané i dokončené hry mění filtr uvnitř místnosti. Zrušení
vrátí původní hru, potvrzení vymění24 karet a vynuluje skóre. Server zvýší
kolo a odmítá opožděné kliky/poslechy. Vydání klienta nestačí; samostatný
server musí odpovídat schválenému exportu. Po obnově oba hráči odemknou zvuk
ve svých prohlížečích. HTTP test není důkaz slyšitelného zvuku u Jany.

## Záloha a hranice obnovitelnosti

Poslední doložená recovery v auditované evidenci byla15.11.2026. Nová záloha
je úkol této opravy, nikoli hotový výsledek tohoto dokumentu. Výběr snapshotu
vždy řídit dokončeným manifestem a skutečným doplňkem Camina; žádné pevné
historické ID ani datum tohoto dokumentu nenahrazuje manifest.

Recovery provádět jen na připojený a ověřený šifrovaný svazek
/Volumes/SamanthaSecureBackup/SamanthaBackups. Samotný připojený Falta nestačí.
Před kopírováním preflight/dry-run a ověření místa; po něm0 skipped, manifest,
reprezentativní SHA shody, zkušební obnova a evidence poslední dokončené zálohy.
Auth.json a data/session_autosave jsou vyloučené; přihlášení se provádí znovu.
Obnovený konfigurační soubor není důkaz platného přihlášení nebo systémového
oprávnění. Hesla, Keychain, SSH, externí data a chybějící soukromé runtime
kopie je nutné určit zvlášť; kompletní novou instalaci Macu prokáže až
samostatná fyzická zkouška. Žádné tvrzení o úplné obnově všech osobních dat.

## Druhý blokátor a připravený návrh limitů

Neplacený inventář zmrazil682 podkladů, celkem3331261 referenčních tokenů
s přijatou bezpečnostní přirážkou; jde o plánování, nikoli účetní spotřebu.
Původní konfigurace nemá oddělenou inspection_output_tokens, a proto
rezervuje celých32000 výstupních tokenů i pro každou kontrolní dávku.
Takový plán překročí20 kroků a po samotném přepnutí runtime nezačne.

Návrh zachová úplný korpus a limit20 kroků, finální návod32000 tokenů,
čas, roli, Standard i měsíční mez1000 kreditů. Pro poznámky z kontrolní
dávky zavede samostatnou rezervu3000 tokenů a navrhuje přijímací mez250
kreditů za celý běh. Naměřená celková rezervace před konečným commitem
byla232,02615 kreditu,20 kroků. Není to uskutečněná spotřeba ani tvrdý
upstream billing cap. Plán250 je po výslovném přijetí schválený, dosud však není zapnutý.

Volitelný refresh_budget v přesném revalidačním plánu obsahuje celý otisk
korpusu, jeho Git head, skutečný rozpad rezervace a konkrétní dvě změny
limitů. Převzetí bez této položky rozpočty vůbec nemění. Při změně zdrojů
se před placeným tahem i před změnou aktivace odmítne původní plán.
Přesné přijetí rozpočtového plánu musí navíc předcházet aktivaci.

Standard sazby programu pro Sol50/2,5/250 kreditů za1M input/cache/output
byly při přípravě25.11. potvrzené proti oficiálnímu ceníku:
https://learn.chatgpt.com/docs/pricing#token-rates
Ceny a limity zkontrolovat znovu při budoucí změně; nerozšiřovat rozpočet
jen podle ceny nástupnického modelu. Model role se zde nemění.

## 2026-11-25 — Přijatý plán, nejistý původní pokus a ruční aktualizace

Míla výslovně přijal nákladový plán: jeden syntetický pokus s mezí15,
oddělené poznámky3000 a250 za revizi při zachování1000 měsíčně.
Původní pokus byl odeslán právě jednou. RPC chyba po značce před odesláním
neposkytla potvrzený tah ani spotřebu; jeho účtenka zůstává delivery_unknown.
Dočasné vlákno není dostupné. Žádné opakování ani změna runtime proofu,
limitů či automatického OS baseline se neprovedly. Další placený pokus
vyžaduje nové informované přijetí, původní rezervace se neuvolňuje.

Doplněné kontroly uchovávají strukturovanou RPC chybu pro budoucí pokus.
Pozorovaný macOS15.8.3 se liší od schváleného15.8.2; volitelná navržená
baseline v novém plánu vyžaduje výslovnou kontrolu a nesmí driftovat.
Nejde o aktualizaci operačního systému.26 cílených testů PASS.

Nezávislá dokončovací cesta je cílená ruční redakce provozních TXT přes
PublicationStore, potvrzený upload obou kopií a registrované převzetí pouze
bootstrap SHA před prvním týdenním jobem. Nepředstírá úplnou modelovou revizi
ani neruší historii. Servisní archiv uchovává protocol-package.json v ploché
cestě reviewed-proof, aby jej nevyloučil filtr node_modules v externí záloze.
Následuje ověření archivu, šifrovaná recovery a izolovaná zkouška obnovy.

Živý konečný stav, brána, commit a provozní účtenky jsou v soukromém
 data/private/recovery_maintainer_repair_20261125/completion.json.
Tento tematický krok nezahrnuje push, restart ani nasazení Cockpitu.

## 2026-11-25 — Provozní návod uploadován, návrh21 kroků bez aktivace

Hotovo: Cílená ruční redakce sjednoceného TXT prošla PublicationStore;
obě pevné kopie mají shodné SHA,80726B a iCloud potvrdil uploaded.
Návod uvádí omezení ruční redakce, nikoli úspěch automatické revize.
Registrované převzetí změnilo pouze bootstrap a zachovalo předchozí aktivaci.
Servisní archiv ověřený:45 souborů včetně konzistentní FR SQLite a čtyř
protokolových podkladů. Hlavní opravný commit073abf6a, brána1269 PASS.

Po rozšíření provozního originálu úplné nové plánování odmítlo20 kroků.
Připravuje se proto výslovný call_limit_refresh z20 na21; všechny zdroje
zůstávají celé, kredity250/běh a1000/měsíc se nezvyšují. Nová volba je
v neměnném plánu, ověřuje scheduler i limits a nepřechází do aktivace bez
úspěšné přesně přijaté revalidace. Samotná příprava není placený pokus.
Nový skutečný pokus navíc k původní nejisté účtence vyžaduje nové přijetí.

Stav: Automatický správce je stále blokovaný; důkaz0.163, mez200 a základ
macOS15.8.2 nebyly přepnuté. První pokus má delivery_unknown, neopakovat.
Nový plán navrhne i přezkoumanou publikační baseline pozorovaného15.8.3,
nikoli aktualizaci OS. Záloha a izolovaná zkouška obnovy se dokončují
nezávisle. Aktuální konečné důkazy, snapshot a další krok jsou v soukromém
 data/private/recovery_maintainer_repair_20261125/completion.json.
Push, nasazení Cockpitu ani nový model nejsou součástí tohoto kroku.

## 2026-11-25 — Limit znaků před tokenovou bránou

Míla přijal doplňkový plán15/250/1000,21 kroků a publikační baseline15.8.3.
Jeho jeden RPC pokus byl odmítnut turn/start -32602: syntetická zpráva měla
1340529 znaků proti serverovému maximu1048576. Přesný zdroj rust-v0.169.0
potvrzuje odmítnutí před submit_core_op; soukromý oddělený disposition uchovává
SHA nezměněné účtenky a oficiálního zdroje. Nejde o přijetí testu ani runtime
proof. Původní starší účtenka bez podrobné RPC chyby zůstává nejistá.

Oprava: syntetický obsah s vyšší hustotou tokenů, dvojí omezení tokenů i
Unicode znaků v přípravě, guard před předodesílací značkou a síťovým RPC.
Dávkování zachovává celé zdroje, zohledňuje oba limity a skutečná finální
syntéza se znovu kontroluje před označením dalšího placeného tahu.
73 cílených testů PASS včetně tokenově vyhovujícího nadlimitního textu,
celých souborů a Unicode hranice, která není počtem bajtů.

Další krok: doménová brána a místní commit; zmrazit opravené přesné vstupy
při stejných schválených omezeních. Žádná automatická smyčka retry, změna
role, deployment či navýšení rozpočtu. Automatický správce se nezapnul.
Ruční provozní TXT a šifrovaná recovery20261125_175722 se zkouškou obnovy
zůstávají platné. Konečný důkaz a opravené vstupy mají soukromou autoritu
 data/private/recovery_maintainer_repair_20261125/completion.json.

Zdroj protokolu:
https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/app-server/src/request_processors/turn_processor.rs#L588-L595

## 2026-11-25 20:28 CET — Obnova: runtime ověřen, úplná revize zastavená na schématu

### Hotovo
Provozní návod po cílené ruční redakci zůstává v PythonMF i iCloud Dokumentech
shodný a uploadovaný. Skutečná kalibrace přijala runtime0.169.0, oddělené
rezervy poznámek a původně schválené250/běh,1000/měsíc,21 kroků; publikační
baseline15.8.3 byla přezkoumaná bez instalace operačního systému.
První šifrovaná recovery se zkouškou obnovy je ověřená. Závěrečný servisní
archiv je připravený; aktualizovaný snapshot má zachovat také nové účtenky. Jejich přesný
výsledek má private/recovery_maintainer_repair_20261125/completion.json.

### Rozhodnutí
Úplná automatická revize není dokončená. Dvě dokončené čtecí dávky pokryly
102 z683 zdrojů a byly převzaté místně bez opětovného placeného čtení.
Třetí tah provider odmítl invalid_json_schema kvůli novému řádku v pevném
řetězci. Zachované jsou všechny původní záznamy, attention i RPC odmítnutí;
žádný marker se neresetoval a po této chybě nebyl další modelový tah.
Známá spotřeba kalibrace a dvou čtení je30,96955 kreditu. Starší nejistý
pokus a odmítnutý tah bez usage nedostaly vymyšlenou nulovou cenu.

### Další krok
Dokončit závěrečné ověření šifrované zálohy a před dalším modelovým pokusem
přijmout nový konkrétní plán pokračování. Původní hranice21 pokusů se tiše
nezvyšuje. Žádné další placené čtení není součástí tohoto dokončení.

### Navrhované další kroky
- Případné pokračování musí doložit původní102 nezměněné zdroje, známé usage
  a explicitní dispozici odmítnutého schématu; nejistý tah se neopakuje.
- Úplnou instalaci náhradního Macu a otevření návodu na fyzickém iPhonu ověřit
  samostatně. Nesouvisející necommitovaná Data práce není servisním archivem.

### Technický důkaz
Brána813 PASS pro předchozí kód; závěrečná brána a commit jsou v soukromé
účtence. Oprava výběru citací je offline ověřená na všech683 zdrojích:
exact substring, žádné uvozovky ani nový řádek v enum literálu. Doplňkové
regrese ověřují zachování strukturované chyby bez retry. Živá přejímka
opraveného schématu zatím chybí. Kód opravy není nainstalovaný do aktivní
Data služby; její definice, role, síť a dosavadní historie jsou zachované.
Push, restart ani nasazení Cockpitu nebyly zadány.
