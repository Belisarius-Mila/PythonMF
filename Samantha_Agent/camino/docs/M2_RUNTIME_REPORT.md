# M2a — místní příprava provozu a odkazu z Cockpitu

2026-09-25. Hotový lokální kód, nikoli dokončená M2 nebo nasazení.
Míla potvrdil, že syntetický M1 náhled funguje, a povolil pokračování.
Zařízení/prohlížeč ani jednotlivé mediální zkoušky ve zprávě nerozepisoval;
z potvrzení nevzniká vzdálený RT3 PASS ani test Janiných zařízení.

## Výsledek

- Existující server lze explicitně spustit s Viewerem a oddělenou čtecí
  databází; výchozí nastavení zůstává vypnuté. Chybné nastavení se odmítne,
  nikdy se nepoužije owner oprávnění jako náhrada. Token se nevydává sám.
- Jeden worker běží mimo obsluhu HTTP, sériově po startu a pak s intervalem
  60 s po dokončení předchozí dávky. Žádná fronta nového frameworku ani AI.
  Worker patří životnímu cyklu aplikace; při zastavení nezačíná další médium.
  Probíhající FFmpeg příkaz má limit 300 s a může zdržet ukončení. Čtení disku
  nemá tvrdou časovou garanci; výkon velké dávky se musí změřit v provozu.
- Nová média se objeví po převodu a obnovení stránky. HTML ukazuje kontrolu,
  přípravu, čekání nebo chybu bez soukromých diagnostických detailů. Pád dávky
  se zkusí znovu v dalším cyklu; jeden vadný převod má nejvýše tři pokusy za
  život procesu. Potom čeká na opravu/restart, aby nehromadil další soubory.
- Existující hotové kopie se znovu nepřevádějí. Originály a metadatové revize
  se nemění, neúplné kopie se nevydávají ani automaticky nemažou. Zámky a U15
  zůstávají vynucené při každém HTTP výdeji včetně starých mediálních adres.
- Soukromý prefix `/camino-api` funguje také v odkazech na dny a média.
  Root prefix je pevná konfigurace, ne libovolná hlavička od klienta.
- Cockpit dostal samostatný odkaz **Otevřít Camino** ve skupině Rodina a
  konfigurační stav v Servisu. Bez platné adresy je odkaz skrytý. Přijme jen
  HTTPS adresu zařízení v `*.ts.net` na `/viewer/` či `/camino-api/viewer/`,
  bez hesla, query nebo fragmentu. Stejná kontrola probíhá i ve frontendové
  vrstvě. Neplatná změna odstraní staré `href`.
- Cockpit nečte média/tokeny, neproxyuje ani nespouští Camino. Odkaz je
  přímý a fungování Vieweru nezávisí na běhu Cockpitu. „Odkaz nastavený“
  úmyslně neznamená „služba běží“ ani „Funnel vypnutý“ — to vyžaduje audit.
- Historický C05b acceptance spouštěč explicitně drží Viewer vypnutý i při
  zděděné proměnné prostředí. Neměníme jeho původní privátní testovací scope.

## Konfigurace pro později schválené nasazení

K existujícím `CAMINO_C05A_*` cestám přidat až ve schváleném provozním kroku:

| Proměnná/volba | Význam |
| --- | --- |
| `CAMINO_VIEWER_ENABLED=1` | Explicitní aktivace; jinak vypnuto |
| `CAMINO_VIEWER_AUTH_DB` | Existující soukromá DB s alespoň jedním čtecím tokenem, jiná než owner DB |
| `CAMINO_VIEWER_TRIP_ID` | Přesná UUID povolené cesty, bez automatického přepínání soukromí |
| `CAMINO_VIEWER_MEDIA_ROOT` | Soukromý adresář obnovitelných kopií mimo Git |
| `CAMINO_VIEWER_INTERVAL_SECONDS` | Volitelně 1–3600 s; výchozí 60 s |
| `--root-path /camino-api` | Prefix pro budoucí privátní proxy; port nekolidující se ScanDocu |
| `CAMINO_VIEWER_URL` v Cockpitu | Přímá soukromá URL bez tokenu; pouze konfiguruje odkaz |

Je potřeba dostupný FFmpeg v PATH služby. `main` drží loopback, jeden proces
a vypnuté access logy. Samotné tyto volby neinstalují launchd, HTTPS, Serve,
ACL ani nezapínají `Trip.viewer_enabled`. Žádná skutečná konfigurace ani nové
přístupové údaje v tomto kroku nevznikly. Návod není povolení k nasazení.

## Ověření

- 5/5 nových rychlých testů: bezpečná URL, chování odkazu v JavaScriptu,
  serialita/stop/restart workeru, retry bez úniku chyby a limity intervalu.
- 6/6 nových izolovaných serverových testů: opt-in, odmítnutí vadné konfigurace,
  předání runtime voleb bez listeneru, omezení vadných převodů, skutečné
  syntetické médium doručené po startu, prefix, staré URL po zámku a opětovný
  vstup/výstup aplikačního lifecycle. Owner HTTP odpovídá i během pozastavené
  dávky workeru. Není to launchd/process-crash nebo zátěžová zkouška.
- 7/7 M1 HTTP/mediálních regresí a 5/5 původních FastAPI testů PASS.
  17/17 runtime/C05b-control/Cockpit-status a 18/18 frontend testů PASS.
  Cílené sady se překrývají; počty nesčítat jako unikátní testy.
- Plná projektová brána PASS: 1 781/1 781 testů (229,798 s); Python,
  JavaScript a shell syntaxe i whitespace OK. Závěrečný limit vadných převodů
  a test souběžného HTTP jsou navíc ověřené cílenou izolovanou sadou.
- Nové nasazené UI ani síťový průchod na Safari NEPROVEDENO. Žádný nový
  iOS build, instalace, přenos osobních dat, live worker, Serve/Funnel,
  launchd instalace, push ani deployment.

## Další krok

M2b: doplnit minimální přenos pořadí a mezer audiočástí z iPhonu a jeho použití
ve Vieweru; současné UUID/pořadí přijetí nejsou časová osa. Nezasahovat do
samotného recorderu. Potom připravit registrovaný provozní start/status/stop,
vědomé povolení cesty a čtecí přístup, samostatně schválit nasazení a provést
jeden společný iPhone → Mac → Jana průchod. M3 záloha a M4 freeze zůstávají.

Implementační reference: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
a [privátní proxy prefix](https://fastapi.tiangolo.com/advanced/behind-a-proxy/).
