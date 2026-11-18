# Společný provozní rozhovor Samanthy
<!-- SAMANTHA_CURRENT_STATUS_START -->
## 2026-11-18 12:43 CET — Potvrzené ukládání z rozhovoru

Hotovo — Samantha připraví uložení článku, receptu nebo místa z jednoznačného
odkazu či textu předchozí odpovědi. Konkrétní odkaz lze vybrat i tlačítkem.
Obě zařízení vidí společný návrh, zdroj, kategorii, text a případný stav
místa. Vybraný text s URL se zachová přesně; samotná URL po potvrzení stáhne
stránku a uloží dostupný text i originál zdroje. Zápis vyžaduje tlačítko.

Rozhodnutí — Nejasný výběr žádá určení zdroje. Duplicita se kontroluje podle
shodné normalizované URL nebo shodného normalizovaného textu, nikoli významu.
Funkční parametry URL zůstávají, běžné sledovací parametry se ignorují.
Dokončený výsledek i stav nejistého pokusu jsou viditelné v rozhovoru.

Další krok — Po samostatně schváleném p+n fyzicky přejmout na iPhonu a Mintu
výběr, náhled, potvrzení, duplicitu a otevření uložené položky v Knihovně.

Navrhované další kroky — Vyhrazená webová záložka na Mintu podle bodu7.
Kalendář zůstává samostatným bodem6.

Technický důkaz — Cílené testy zahrnují dvě zařízení, souběh a konfliktní
návrh, přesný úryvek s URL, různé parametry, duplicitu po kanonické URL,
pád po zápisu a ověření původního ID bez nového zápisu. Před fyzickou
přejímkou prošla také syntetická HTTP/JS integrace. Reálný veřejný zdroj
example.com byl uložen do odděleného testovacího archivu, druhý pokus našel
stejnou položku a samostatný úryvek zachoval text, URL a stav místa.
Důkaz v soukromém dočasném adresáři samantha-save-final-4_zhtoy8.
Programová brána je doložena podepsanou soukromou účtenkou.

Rizika — Nejasný výběr zůstává k ručnímu určení. Po přerušení před zápisem
registru může být výsledek neověřený a původní zdroj se automaticky neopakuje.
Fyzické ověření na iPhonu/Mintu a nové nasazení dosud neproběhly.

## 2026-11-18 11:35 CET — Stav návštěvy míst ve společném rozhovoru

Hotovo — Otevřené místo ve společném rozhovoru umožňuje uložit stav Neurčeno,
Navštíveno, Chceme navštívit nebo Tip. Starší záznamy se čtou jako Neurčeno.
Doporučení míst s explicitním dotazem vynechá označené navštívené položky.
Všichni spárovaní účastníci vidí společný stav.

Rozhodnutí — Změna stavu vyžaduje výslovné tlačítko a kontrolu původní hodnoty.
Při nesouladu se stav nepřepíše. Nové položky se z tohoto kroku zatím neukládají.

Další krok — Dokončit návrh a potvrzené ukládání článku, receptu či místa
z rozhovoru včetně kontroly duplicit a uchování zdrojového URL a obsahu.

Navrhované další kroky — Přejmout funkci na iPhonu a Mintu po samostatném p+n,
poté navázat ovládáním webové záložky.

Technický důkaz — 66 cílených kontrol a programová brána737 PASS. Testy
zahrnují staré záznamy, nepřípustnou kategorii, změnu druhým zařízením a
vynechání navštíveného místa. Vizuální fyzická přejímka nebyla provedena.
Stav návštěvy má jedinou autoritu v atomicky zapisovaném registru. Běžná
editace místa jej zachovává.

## 2026-11-18 09:52 CET — Internetové hledání ve společném rozhovoru

Hotovo — Samantha má místně připojené živé webové hledání ve stejném
modelovém tahu. Nalezené zdroje zobrazuje jako klikatelné názvy s celou
adresou. Telefon a monitor dostávají stejnou odpověď i odkazy.

Rozhodnutí — Míla schválil čtecí hledání jako první krok ovládání internetu.
Použije se stávající model a App Server. Instrukce zakazují vkládat soukromé
knihovní podklady a historii do webových dotazů. Toto omezení je instrukční.
Knihovní hledání nadále používá stávající místní čtečku.

Další krok — Samostatně schválené p+n do Cockpitu a fyzická přejímka
jednoho internetového dotazu na iPhonu a Mintu.

Navrhované další kroky — Vyhrazená záložka Firefoxu na Mintu podle kroku7
uloženého plánu, následně potvrzené ukládání vybrané stránky.

Technický důkaz — 33 cílených kontrol a programová doménová brána458 PASS.
Jediný oddělený živý test vrátil oficiální web Českého rozhlasu Vltava.
App Server doložil item/started i item/completed typu webSearch a potvrzené
dokončení původního tahu. Odkazy používají textové uzly a existující HTTP(S)
validátor bez přihlašovacích údajů. Nová regrese pokrývá HTML injekci,
adresu s query/fragmentem a závorkami i odmítnutí URL s heslem.
Zdrojové p+n čtecí Knihovny z de12f383 je už dokončené podle předchozího
předání a Mílova potvrzení. Nové webové hledání je místní, fyzická přejímka
čeká. Živý test je v dočasné soukromé složce samantha-web-smoke-t87in85r.
<!-- SAMANTHA_CURRENT_STATUS_END -->
## 2026-11-17 21:11 CET — Samantha, čtecí Knihovna jako první část druhého balíčku

Hotovo: Míla nyní potvrzuje, že propojení iPhone–Mint celkem funguje, a zadal
pokračování. Samantha místně dostala hledání knih, článků, receptů a míst nad
celým kanonickým katalogem, sdílené výsledkové karty a čtečku uloženého textu.
Telefon může otevřít výsledek a monitor uvidí stejnou položku. Přirozené odkazy
„Otevři druhý“/„Otevři ten recept“ používají předchozí výsledky; nejasný výběr
se přizná. Na monitoru lze hledání a výběr kdykoli doladit ručně.
Rozhodnutí: Čtecí část uloženého druhého balíčku (krok4). Míla vývoj schválil;
nové p+n tím nezadal. Používá stejnou Knihovnu a stávající model/App Server,
bez nové modelové role, placeného hlasu nebo druhého modelového průchodu.
Server připojí dohledané zdroje k jediné původní otázce; zobrazovaný user_text
zůstává původní. Reconnect, polling a knihovní tlačítka model nevolají.
Další krok: Po samostatném p+n fyzicky přejmout dotaz z iPhonu, výsledky
na Mintu, hlasové otevření konkrétní položky a ruční otevření v čtečce.
Navrhované další kroky: Potom krok5 — potvrzené ukládání z rozhovoru a evidence
Navštíveno/Chceme navštívit/Tip/Neurčeno. Kalendář a webové rozšíření jsou dál.
Technický důkaz:33 cílených Python kontrol PASS včetně dvou skutečných HTTP/JS
klientů a3 nových JS případů čtečky (pozdní odpověď, stránkování/retry, URL).
Skutečný čtecí audit:145 položek,3 dotazy lokálně0,04–0,21s,0 zápisů/modelových
volání. Testy zahrnují školní i skutečný tvar Konspektových skupin, nové položky,
poškozený katalog, cestu/symlink mimo archiv, cizí room, CAS výběru a jediný send.
Safari CUA opakovaně odmítlo ovládání při změně aktivního okna; žádná nativní
vizuální přejímka se netvrdí. Vlastní syntetický server ukončený, původní okno
zachované. Fyzický Mint/iPhone a skutečná modelová odpověď nového kroku čekají.
Meze: Lokální vyhledávání je podle slov a prefixů s tolerancí diakritiky,
nejvýše12 karet; nejde o sémantický index. Knihy poskytují uloženou anotaci/
poznámky, ne automaticky plnou knihu. Uložený text lze číst celý po20000 znacích
s kontrolním otiskem; model dostává omezené výňatky3500 znaků nebo otevřený
text do120000 znaků a pravdivé text_truncated. Katalog/textový cache je jen RAM.
Citlivý obsah/podklady zůstávají mimo Git. Žádné uložení do archivu, inference
návštěv, kalendářový zápis nebo řízení webové záložky.
Finální doménová brána, head a stav: private shared_chat_library_20261117/
completion.json; targeted_tests.log, live_readonly.json a safari_verification.json.


## 2026-11-17 — Průběžný diktát a stálý vstup iPhone–Mint

Hotovo: Diktát se průběžně ukládá nejvýše jedním požadavkem;150ms časovač
se každou klávesou neodkládá. Pomalá síť slučuje mezilehlé změny, nevyrábí
frontu starých snapshotů. Aktivní stránky kontrolují stav po400ms; skryté po5s,
offline po2s. Jedno čtení současně, okamžitý návrat po pageshow/online/viditelnosti.
Klepnutí do otázky synchronně otevře editaci/fokus před čekáním na HTTP.
Po odeslání zůstává původní zařízení vlastníkem psaní, i když otázku odešle
monitor. Fokus zůstane při kliknutí na Odeslat. Aktivní pole bezpečně obnovuje
120s oprávnění po30s, vždy bez automatického převzetí cizího zařízení.
Rozhodnutí: Míla potvrdil první skutečné spojení, ale rychlost a opakované
mačkání přebírání/obnovy hodnotil jako nepoužitelné; schválil tento malý balíček.
Původní CAS/revize, zachování konfliktního textu, párování a jediná identita
odeslání zůstávají. Nový text během nejistého sendu se drží místně; pouze
čtecí ověření nezahájí další otázku. Model, sandbox ani hlasová služba se nemění.
Důkaz:23 cílených Python kontrol včetně skutečných dvou HTTP/JS klientů;
9 nových deterministických JS scénářů (souvislý diktát, pomalá síť, pozdní GET,
fokus, obnova vlastního oprávnění, žádné převzetí cizího, nejistý send a bfcache).
První text druhý klient lokálně zobrazil za410ms během pokračujícího diktátu.
Nativní Safari se dvěma oddělenými origins ověřilo klepnutí do pole, zachovaný
fokus/editaci po jednom syntetickém sendu, druhou otázku bez přebírání a ruční
opravu z monitoru bez přebíracího tlačítka. Původní okno zachované, vlastní
okno/server ukončené;0 skutečných modelových volání, žádná skutečná konverzace.
Rizika:410ms je lokální fixture, nikoli naměřená rychlost fyzického iPhonu
přes Tailscale. Fyzický mikrofon/klávesnice a latence iPhone/Mint čekají
na přejímku až po samostatném p+n. Odpověď modelu se zatím zobrazí celá.
Další krok: Programová doménová brána a lokální commit; pak samostatné p+n
včetně dřívějšího Henriho f75c17f9. Toto zadání neprovádí nasazení/restart.
Finální důkaz/head: private shared_chat_responsive_20261117/completion.json;
real_http_frontend.log, safari_verification.json, targeted_tests.log a final_gate.log.


## 2026-11-17 — Společná integrace FR a opravy přenosu Samanthy

Hotovo: Oprava Window časovačů a viditelného stavu sdíleného draftu185d225b
je připravená ve společném balíčku s FR klientem a Datovým a119e84f.
Rozhodnutí: Míla výslovně zadal p+n všech čekajících commitů po Datově checkpointu.
Další krok: Registrované p+n a přesná kontrola živého /samantha/ proti zdroji;
finální účtenky/head a stav v private fr_mint_release_20261117/completion.json.
Rizika: Fyzické iPhone/Mint přepárování a přenos textu musí potvrdit Míla.
Předchozí dva Safari klienti ověřili syntetický rozhovor bez placeného modelu;
skutečný rozhovor se tímto vydáním neodesílá ani neopakuje.


Aktualizace: 2026-11-17 15:35 CET. Kanonický proud project-cockpit; existující handoff a
TVBCP ve workstreams/project-cockpit.md. Nejde o nový vývojový profil.

## 2026-11-17 15:35 CET — Oprava přenosu rozepsaného textu Samanthy

Hotovo: Opravený klient po spárování skutečně automaticky ukládá rozepsaný
text. Safari odmítalo Window.clearTimeout/setTimeout volané přes instanci
klienta; párování a převzetí psaní prošly, ale debounce ani následný flush
neproběhly. Výchozí časovače nyní volá uzávěr přes správné Window.
UI navíc trvale rozlišuje neuložený a sdílený draft i pokyn k převzetí psaní.
Rozhodnutí: Míla nahlásil, že po spárování kódem se nic nepřenáší. Oprava
řeší reprodukovaný prohlížečový problém; nemění párování, síť, oprávnění,
uložené rozhovory ani pravidla jediného odeslání. Vývoj není nové p+n.
Další krok: Samostatně autorizované p+n opravy a pak Mílova fyzická přejímka
telefon → rozepsaný text na Mintu → ruční oprava → jedna otázka/odpověď.
Navrhované další kroky: Pokud po reloadu zůstane lokálně zachovaný text,
použít explicitní „Použít zachovaný text“. Novou kopii nejisté otázky neposílat.
Technický důkaz:51 cílených Python kontrol PASS, nová Window-brand regrese
FAIL→PASS, skutečný automatický debounce uloží právě jeden draft bez otázky.
Dva nativní Safari klienti s oddělenými úložišti prošli párováním, obnovou
původně neuloženého testovacího textu, obousměrným automatickým přenosem,
převzetím/ruční opravou, jedním syntetickým send a společnou odpovědí. Reload
neodeslal nic znovu. Soukromá fixture, žádný placený model ani změna skutečného
rozhovoru. Vlastní okno/server ukončené, původní Safari okno zachované.
Finální programovou bránu, přesné otisky a commit určuje pouze
private shared_chat_transfer_fix_20261117/completion.json. Fyzický iPhone/Mint
zůstává samostatnou přejímkou; běžící Cockpit dosud používá starší klient.
Předchozí kalendářová chyba zůstává uživatelem přijatá. FR klient eafc8161
je samostatný čekající lokální krok; skutečný Janin obsah zůstává mimo Git/docs.

## Schválený rozsah a použití

První balíček propojuje iPhone, Cockpit a Mint. Na monitoru tlačítko Samantha
otevře /samantha/. Zahájit rozhovor vytvoří prázdnou historii bez modelového
volání. Připojit telefon zobrazí jednorázový šestimístný kód na deset minut.
Na telefonu stejný vstup, zadat kód. Psát / diktovat zde převezme rozepsaný text;
iPhone používá mikrofon vlastní klávesnice. Na Mintu lze psaní převzít a text
opravit. Odeslat spustí jednu otázku, obě zařízení vidí tutéž odpověď. Ctrl/Cmd
+Enter odpovídá výslovnému Odeslat. Obnovit stav je pouze čtení.

Celý schválený plán je v Downloads/Samantha_iPhone_Cockpit_Mint_plan_vyvoje_2026-11-16.txt.
Další balíčky: knihovní hledání a karty; ukládání článků/receptů/míst a evidence
návštěv; kalendářové formuláře; browser rozšíření pro ovládání monitoru.
Současný chat tyto akce neslibuje a nemá jejich nástroje.

## Stav a spolehlivost

- app/shared_chat.py používá kanonický data/private/shared_chat/, nikoli kopii
  izolovaného vývojového profilu. JsonWorkRepository: atomické transakce a
  sdílený zámek. Soukromá data, kódy a přístupové údaje nepatří do Gitu.
- Spárované zařízení má vlastní náhodný přístupový klíč, pouze v lokálním
  browser storage a API těle/hlavičce. Nikdy v URL. Host/Origin kontroly Cockpitu
  zůstávají závazné. Neúspěšné pokusy o kód mají omezení; kód je jednorázový.
- Rozepsaný text má revizi, vlastníka psaní a120sekundovou obnovovanou lease.
  Převzetí je výslovné, pozdní zápis hlídá compare-and-set. Konfliktní místní
  text zůstává v sessionStorage a lze ho vědomě převzít. Stav po výpadku je
  viditelně neověřený; nové odeslání je do obnovení spojení nedostupné.
- Před POST se uchová původní identita zprávy. Server nejdřív atomicky přijme
  přesný draft, teprve pak spouští worker. Souběžné POST, ztracená odpověď ani
  reload nespustí další tah. Polling, připojení a psaní model nevolají.
- Odpovědi a původní doručení vlastní samostatný CanonicalSessionHub. Restart
  pokračuje v uloženém threadu; pokud dokončení není doložené, ukazuje
  delivery_unknown a novou kopii blokuje. Automatické znovuodeslání neexistuje.
  U restartu během nedokončeného tahu není v prvním balíčku operátorská
  rekonciliace; zachovat původní účtenky, neposílat stejnou otázku do nového chatu.
- app/shared_chat_runtime.py přebírá stávající human-chat model/effort; nezasahuje
  do config/agent_roles.json ani do vývojových profilů. Oddělený workspace,
  read-only sandbox bez sítě, nástroje/MCP/aplikace vypnuté. Použití textového
  modelu začne jen výslovným Odeslat. Mobilní diktování neposílá audio Samanthě.
- Změnit připojení mění pouze toto zařízení; historii na Macu nemaže. Běžné
  zavření stránky a návrat používají stejnou identitu. Výpadek Macu znamená
  nedostupný backend, Tailscale samotný jej nenahrazuje ani nebudí.

## Ověření a meze

335 cílených testů PASS: doména, runtime, skutečné HTTP, dva skuteční JS klienti,
CAS konflikt, souběžný send, ztracená HTTP odpověď, reload, pozdní GET,
offline/online, dosavadní Cockpit a registry. Živý App Server přijal oddělené
připojení s nulou modelových tahů. Uložený runtime_probe.json není důkazem
skutečné modelové odpovědi. Fyzický telefon/Mint zůstává neověřený; syntetická nativní Safari přejímka17.11. je doložená výše.
Vlastní validační doména shared_chat propojuje také HTML/CSS/JS a Node fixture
s reálným HTTP testem dvou klientů; změna frontendu nesmí skončit jen obecnými
serverovými kontrolami. První integrační brána1529 PASS; po posledním rozdílu
rozhoduje finální účtenka, přerušený následný meziběh není důkaz.
Konečná programová brána a lokální commit: private shared_chat_20261116/completion.json.
Vývoj sám není push nebo nasazení do běžícího Cockpitu.

Přejímka po samostatně schváleném p+n: na Mintu založit rozhovor, připojit
telefon kódem, převzít/diktovat otázku, převzít/opravit na Mintu, odeslat jednou,
ověřit odpověď na obou, obnovit stránky a krátce přerušit síť bez další otázky.
