# Francouzština Jana — soukromé pexeso pro dva hráče

Vývoj schválený 24. 11. 2026. Pracovní proud `project-vocabulary-fr`, existující
handoff a TVBCP. Jde o samostatnou herní službu s lokálně ověřovaným klientem;
stav skutečného nasazení určuje soukromá účtenka, nikoli tento návod.

## Uživatelský tok

V Janině pexesu vybere zakladatel slovíčka a použije „Hrát spolu na dálku“.
Do další stránky přechází pouze 12 vybraných UID, nikoli celý osobní seznam.
Každý hráč zadá krátké jméno a výslovně zapne zvuk. Zazní francouzská ukázka.
Zakladatel sdílí pozvánku; po připojení druhého hráče zahájí partii.

Oba mají tentýž plán 6×4, hráče na tahu, skóre a výsledek. Otočení přehraje
FR a zobrazí na 2 s CZ; server čeká na oba skutečně dokončené poslechy.
Shoda se započte jednou, nechá hráče pokračovat a zobrazí 2s velkou FR kartu
bez CZ s opakovaným FR zvukem. Velký obrázek se přednačítá při otočení
kartičky. Delší zvuk dál blokuje další tah. Poslední
odměna předchází výsledku. Sbírky lze na konci přehrávat samostatně.

Při přerušení spojení se tahy zamknou. Po 15 s bez heartbeat nebo při
výslovném odchodu se společná fáze pozastaví. Návrat ve stejném prohlížeči
použije jeho soukromý hráčský přístup. Reload a návrat po skrytí stránky
vyžadují znovu kliknout na „Pokračovat a zapnout zvuk“. Chyba poslechu nabízí
opakování nebo výslovné pokračování bez zvuku; francouzštinu nenahrazuje CZ.

## Oddělení a protokol

- `app/vocabulary_fr_multiplayer.py`: standardní Python HTTP server, SQLite
  transakce a autoritativní herní stav. Neimportuje Cockpit ani App Server,
  nezpřístupňuje jejich routy a nevyžaduje modely, mikrofon ani nové audio.
- `online.html`, `online.js`, `online.css`: stejný FR model, existující
  výběr 12 kompatibilních významů a existující veřejná média. Jeden explicitně
  odemknutý Audio element se znovu používá pro vzdálené události.
- Klient dotazuje vlastní službu přibližně po 0,6 s; při síťové chybě po
  1,6 s. Server řídí fáze a každý mutující požadavek má jedinečnou identitu
  a očekávané kolo/fázi. Pozdní klik ani opakovaná odpověď nepřidá další bod.
- Čekací fáze: waiting, choose, reveal, compare, reward, finished. reveal
  čeká nejméně 2 s a na obě potvrzení poslechu; compare trvá nejméně 1 s;
  reward nejméně 2 s a dohrání obou zvuků. Obnovení zachová stejnou fázi.
- Plán zamíchá server. Klient před otočením nedostává UID skrytých míst.
- API `/api/vocabulary-fr/rooms`: create; `/{room}/join`, sync, ready,
  leave, start, flip, heard, rematch, restart. Všechny operace s místností po join
  používají hráčský Bearer token. `GET /health` vrací protokol a otisk katalogu.
- Každá pozvánka a hráčský token má 256 bitů náhody. Tokeny jsou v databázi
  hashované, pozvánka je v URL fragmentu a po vstupu se z adresy odstraní.
  Host může pozvat pouze jednoho dalšího hráče; jeho token nelze nahradit
  dalším návštěvníkem. Soukromý hráčský přístup zůstává v sessionStorage.
- Nové databáze mají oprávnění 0600. Úložiště je pod `data/private/`, mimo
  Git a veřejné soubory. Automatický úklid databáze soubory nemaže.
- Místnost platí nejvýše 24 hodin, bez aktivity nejvýše 2 hodiny. Výchozí
  kapacita je 64 současných místností; create/join jsou omezené počtem
  požadavků. Tělo JSON je omezené na 32 KiB, síťové čtení na 15 s.
- Přísná kontrola Host a Origin; žádné cookies ani CORS. CSP omezuje zdroje
  na vlastní původ. Služba podává pouze veřejného FR klienta a FR média,
  nikoli obecný repozitář, ostatní aplikace, soukromé soubory nebo symlinky ven.
- Obsah katalogu a jeho obrazová/audio metadata mají společný otisk. Po
  změně katalogu se stará místnost odmítne, místo aby hrála s jinými významy.

## Místní spuštění

Z adresáře Samantha_Agent:

    .venv/bin/python -m app.vocabulary_fr_multiplayer --port 8791

Náhled je na `http://127.0.0.1:8791/vocabulary-fr/`. Výchozí databáze je
`data/private/vocabulary-fr-online/rooms.sqlite3`; přepínač `--database`
umožňuje oddělenou testovací databázi. CLI dovoluje jen loopback bind.
Tento příkaz službu neinstaluje do launchd ani nepublikuje na internet.

## Co je potřeba pro Německo ↔ domov

Samotné GitHub Pages provozovat herní server neumějí. Před skutečnou
přejímkou se musí určit a samostatně schválit cílová HTTPS adresa, hosting,
provozní vlastník a registrovaný způsob nasazení této služby. Běžné FR
Pages p+n samo backend nenainstaluje. Stávající Cockpit/Tailscale konfigurace
se tímto vývojem nemění a nelze ji automaticky rozšířit.

Služba očekává HTTPS reverzní proxy před loopback HTTP serverem. Parametr
`--public-origin` musí odpovídat schválené HTTPS adrese bez cesty. Proxy musí
zachovat veřejný Host a prohlížečový Origin; přístup klienta a API je na
stejném původu. Služba nedůvěřuje libovolným forwarded hlavičkám.

Pro první pilot je klient podáván touto samostatnou službou. Při případné
změně původu webu se prohlížečová osobní označení automaticky nepřenesou.
Zachovat původní data; případný přenos provést existujícím výslovným
exportem/importem. Výběr provozní adresy a napojení původního veřejného
vstupu musí být součástí konkrétního návrhu nasazení.

## Přejímka

Automatické testy: `tests.test_vocabularyfr_multiplayer` a původní
`tests.test_vocabularyfr_web_gallery`. Skutečný rozsah vybírá registrovaná
doménová brána; nové soubory mají vlastníka v `validation_domains.py`.

Na dvou zařízeních ověřit: založení, pozvání, oba poslechy, neshodu, shodu,
2s odměnu, skutečně delší zvuk, obě skóre, zablokované kliknutí mimo tah,
odpojení během poslechu i odměny, ruční návrat po reloadu a dokončení hry.
Soukromý testovací scénář a důkazy jsou v `data/private/vocabulary_fr_online_20261124/`.
Lokální HTTP, syntetické prohlížeče a úspěšná brána nedokládají přejímku na
dvou fyzických Macích přes skutečné připojení Německo–domov.

Podklad k odemykání zvuku v Safari:
https://webkit.org/blog/7734/auto-play-policy-changes-for-macos/

## Dočasný večerní HTTPS pilot — 24. 11. 2026

Registrované `vocabulary_fr_hosting_prepare/status/start/stop` používají
`app.vocabulary_fr_hosting.Pilot`. Prepare přijímá celý schválený SHA čistého
main a ověřenou projektovou binárku cloudflared s přesným SHA256. Export je
pouze veřejná FR část z Gitu a samostatný Python server, bez .git či soukromých
souborů. Stav, logy, databáze a exporty zůstávají v data/private/vocabulary-fr-hosting.

Start vyžaduje current scoped consent a request_id. Nepotvrzený či nejasný
předchozí start se neopakuje. Status je čtecí, stop ukončí jen procesy s přesně
shodnou totožností a nic nemaže. Není zde žádná instalace, launchd, nový účet,
změna Tailscale, Funnel, DNS záznamů, firewallu ani Cockpitu/Camina.

Quick Tunnel vytvoří náhodnou dočasnou HTTPS adresu. Herní pozvánka zůstává
soukromá a hra má dva chráněné sloty; samotný veřejný FR klient je přes tuto
adresu dostupný. Prohlížeč, média a API jsou na stejném původu. Po skončení
tunelu adresa přestane fungovat, při novém spuštění se změní. Mac musí zůstat
zapnutý, online a neuspaný. Nejde o trvalou produkční adresu ani automatickou
službu po restartu Macu. Další rozšíření vyžaduje konkrétní provozní rozhodnutí.

Oficiální omezení: https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/
Provozní URL a finální důkazy pouze v private vocabulary_fr_hosting_20261124/completion.json
a v předaném TXT Downloads; soukromé adresy nepatří do Gitu.

HTTP podávání médií podporuje jednoduché byte Range, otevřený i koncový rozsah,
206/Content-Range, neplatné rozsahy416 a odpovídající HEAD. To je potřeba
pro kompatibilitu přehrávání v Safari; soubory MP3 se nemění. Testy ověřují
přesné bajty a délku. Podklad Apple:
https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/CreatingVideoforSafarioniPhone/CreatingVideoforSafarioniPhone.html

## Přímý vstup z Cockpitu — místně připraveno 24. 11. 2026

`web_apps_catalog()` mění pouze dynamický odkaz „Francouzština Jana“. Základní
WEB_APP_CATALOG, Pages původ, ostatní aplikace i desktopový FR trainer zůstávají.
`cockpit_french_url()` čte existující Pilot.status; nic nevytváří ani nespouští.
Pouze při skutečně běžících vlastněných procesech a platné HTTPS Quick Tunnel
adrese připojí onlineOrigin do URL fragmentu. Žádné PID, tokeny či herní data
se nepředávají a konkrétní dočasný hostname se nedostane do Gitu ani do Pages GET.

FR memory.js zachytí adresu před změnou interního routování a případně ji drží
v odděleném sessionStorage klíči vocabulary-fr.online-origin.v1. Povoluje jen
HTTPS původ odpovídající Quick Tunnel bez přihlašovacích údajů, portu, cesty,
query či fragmentu. Nový vstup z Cockpitu nahradí předchozí dočasnou adresu.
Blokované úložiště neblokuje použití platného vstupu v právě otevřené stránce.

Tlačítko Hrát spolu na dálku otevírá oddělenou kartu s noopener/noreferrer.
Předává pouze12 UID z již platného výběru ve fragmentu words. Osobní localStorage,
filtry a původní stránka zůstávají na původní adrese, bez migrace a exportu dat.
Samostatná hra nadále funguje svým dosavadním místním vstupem. Při neověřené
službě se katalog vrací k původnímu běžnému odkazu, nezkouší automatický start.

Pro živé zapojení je potřeba samostatně schválené registrované p+n FR Pages
(aktualizovaný klient) a Cockpitu (dynamický katalog). Samotná lokální změna
není publikace; stávající dočasný herní backend není potřeba restartovat.

Katalogová kontrola PID si pro ps vynutí C locale a systémové časové pásmo
bez změny prostředí rodiče. Porovnání normalizuje starší české i anglické
datum narození procesu a jen známý přechod Python launcheru; nadále musí
souhlasit čas vzniku, PID a všechny argumenty. To dovoluje stejnou původní
partii rozpoznat i z launchd/UTC prostředí, bez nového tunelu či restartu.

## Další partie ve stejné místnosti — 24. 11. 2026

Po dokončení může zakladatel použít „Další partie s jinými slovíčky“. V místnosti
vybere veřejný okruh a zkontroluje návrh12 významů. Návrh vynechá všech12 UID
z dokončené partie; pokud okruh nestačí, zahájení je vypnuté a nabídne širší
výběr. „Změnit výběr“ znovu losuje; „Zrušit výběr“ zachová výsledek. Soukromé
osobní filtry původní Francouzštiny zůstávají v původním panelu.

Rematch přijímá volitelná uids (12 kompatibilních veřejných významů). Bez uids
platí původní rematch se stejnými slovy. Jen zakladatel po finished a za
přítomnosti obou hráčů může změnu provést; requestId/expectedRound/expectedStage
zabraňují opakování a opožděnému restartu. Místnost, pozvánka, oba tokeny a
jména se zachovají, kolo se zvýší a skóre/tahy/plán se obnoví. Spoluhráč zůstává
v panelu a nové kolo načte běžným sync. Po nejisté odpovědi klient nejprve
načte autoritativní stav, žádný create/join/rematch neopakuje automaticky.

Registrované vocabulary_fr_hosting_upgrade → Pilot.upgrade aktualizuje jen
přesně vlastněný server na stávajícím konektoru. Vyžaduje explicitní aktuální
souhlas, čistý schválený SHA, expected_running_head a trvalé request_id, předem
připravený neměnný export se stejným katalogem/audio/quiz i konektorem. Před
SIGTERM serveru zapisuje soukromou účtenku. Počká na zánik původního procesu,
ověří volný loopback port, spustí jediný server na stejné databázi/původu a
ověří jeho health/katalog i oba PID. Konektor se neukončuje, žádný nový tunel
nevzniká. Nejasný výsledek je attention a stejný požadavek se pouze přečte;
žádný automatický druhý start. Soubory, hry a staré exporty se nemažou.

Aktualizace není tímto návodem schválená ani provedená. Po skutečném nasazení
stačí oběma obnovit stávající herní panel a kliknout na pokračování se zvukem.
SessionStorage ve stejném panelu/původu zachová soukromý přístup. Nová pozvánka
není nutná; časová platnost místnosti24h/2h bez aktivity zůstává.

## Trvalý cloud — příprava 24. 11. 2026

Míla zadal přípravu trvalého hostingu. Nasazovací podklad, cenu, provoz a
přejímku drží deploy/vocabulary-fr/README.md a render.yaml. Placená aktivace
čeká na potvrzení účtu a ceny. Registrované vocabulary_fr_cloud_prepare
exportuje pouze committed veřejnou FR část; vocabulary_fr_cloud_backup
vytváří konzistentní soukromou SQLite kopii bez přepisu/mazání či uploadu.

Online-hosting.json v docs/vocabulary-fr má schemaVersion1 a origin:null.
Po ověřeném nasazení se aktivuje pouze konkrétní HTTPS původ onrender.com
přidělený vlastněné službě. Klient i Cockpit jej používají před případným
starým tunelem. Fragment ani sessionStorage nemohou povolit libovolný Render
hostname. Osobní Pages původ/filtry zůstávají; hra se otevírá zvlášť se12 UID.
První přechod původu vyžaduje novou místnost. Databáze Macu se neexportuje.

## Bezplatný soukromý Tailscale — aktuální volba 24. 11. 2026

Míla odmítl placenou aktivaci a potvrdil zapnutý Mac i fungující Tailscale/
Cockpit u Jany. Aktuální připravený cíl je soukromý Serve8443→127.0.0.1:8792.
Render zůstává neaktivní podklad. Žádný Funnel, veřejný vstup, ACL změna,
sdílení zařízení ani platba nejsou součástí této varianty.

Registrované vocabulary_fr_tailnet_prepare/status/activate/verify vlastní
PrivateGame v app/vocabulary_fr_tailnet.py. Prepare freeze: čistý přesný
commit, veřejný export, aktuální vlastní node/DNS, původní Serve/Funnel a
LaunchAgent com.samantha.vocabulary-fr. Aktivace vyžaduje přesnou globální
frázi a otisk plánu. Jediný intent před bootstrap/Serve; nejistý výsledek
se neopakuje. Verify pouze doloží původní fungující proces a trasu proti
původnímu snímku; nikdy nespustí druhou aktivaci ani neresetuje síť.

Vlastní GUI-user LaunchAgent startuje loopback-only server po přihlášení.
Privátní soubory/manifesty/DB jsou pod data/private/vocabulary-fr-tailnet.
Ostatní443/8770 posluchače i Camino se kontrolují beze změny; cizí8443/8792
nebo systémový soubor blokuje. Nový endpoint není důkaz přístupu z Janina
Macu: po aktivaci je nutná skutečná HTTPS/přístupová přejímka a ověření
obou hráčů. Případné ACL omezení vyžaduje nový samostatný návrh.

Cockpit předá pouze živě ověřenou soukromou adresu přes fragment. Klient
povoluje pouze kanonický HTTPS ts.net původ na8443, žádné credentials,
cesty, query/fragment nebo jiné porty. Osobní Pages původ/filtry a12 UID
zůstávají. Konkrétní privátní hostname nikdy do Git konfigurace.

Podklady: https://tailscale.com/docs/features/tailscale-serve a
https://tailscale.com/docs/reference/tailscale-cli/serve . Původní Host
u nainstalované1.104.7 zachovává TCP proxy podle
https://github.com/tailscale/tailscale/blob/v1.104.7/ipn/ipnlocal/serve.go .

## Změna filtru rozehrané i dokončené hry — 25. 11. 2026

Zakladatel mění filtr uvnitř online místnosti, bez navigace na přehled.
Nabídka obsahuje okruh, slovní druh, obtížnost, typ výrazu, posledních20/50
nebo FR/CZ hledání a náhled12 kompatibilních slov. Zrušení nic neodesílá.
Potvrzený restart rozehrané partie vyžaduje výslovné potvrzení vynulování;
dokončená hra může začít s novým filtrem přímo. Místnost se nevytváří znovu.

Akce restart vyžaduje zakladatele, již zahájenou hru, oba připojené hráče,
validní12 UID a aktuální expectedRound/expectedStage. V jediné transakci
vymění plán, vynuluje skóre/tahy/poslechy a zvýší kolo; tokeny, pozvánka,
jména a expirace zůstávají. Duplicitní requestId vrátí původní výsledek,
starý klik/poslech nemůže zasáhnout nové kolo. Klient při novém kole ukončí
předchozí zvuk i odměnu a dál používá stejnou sessionStorage identitu.
Původní rematch zůstává omezený na dokončenou hru.

Tento krok je místní. Vydání vyžaduje kromě Pages také samostatný aktualizovaný
herní export/server. Neměnit stávající databázi a nepřidávat nové síťové granty.
Publikace a změna běžící služby potřebují odpovídající autorizaci; historické
potvrzení předchozí aktivace se nevztahuje na nový plán služby.

## Poslechový duel pro dva — 26. 11. 2026

Místně doplněný druhý herní režim. V pexesu je „Poslechový duel na dálku“;
otevře `duel.html` na stejném ověřeném herním původu. Předá celou zásobu
veřejných UID z aktuálního filtru (například posledních 50), nikoli jen
12 karet ani soukromé osobní značky. Původní karta a její data zůstanou.
Zásoba musí umožnit alespoň 12 vzájemně odlišných obrázků s oběma zvuky.

Jedna hra má 12 náhodných, neopakovaných zadání. Před každým kolem se
nejméně 3 s ukazuje „Začíná nové kolo“ / „Další kolo“ a přehraje české slovo.
Příprava čeká na dohrání a načtení všech 12 náhledů u obou hráčů. Server
potom naplánuje společné otevření s krátkým předstihem pro doručení stavu.
Do kartiček se přesunou již dekódované obrazové elementy bez nového načítání;
stejně tak velká odpověď před zahájením FR zvuku a dvousekundové ukázky.
Oba mají stejné 4×3 kartičky. Zakladatel dvěma krátkými menu volí text
2/3/4 s a obrázek 1/2 s; výchozí nastavení zůstává 2 + 1 s.
Nejprve ukazují pouze velký FR zápis přes plochu karty, potom se
objeví již připravený obrázek nad zmenšeným textem. Přechod používá čas od
stejného společného otevření; polling ani kliknutí ho nespouští znovu.
Kliknout lze v obou částech okna a první odpověď zůstává zamčená i po
odhalení obrázků. Nabídka se skryje po součtu obou délek (3–6 s).
Server při přípravě otázky zmrazí délky tohoto kola; pozdější změna menu
platí až pro další kolo a nikdy neobnoví běžící časovač ani odpověď.
Nastavení patří místnosti, přežije restart služby, další hru i změnu filtru.
Zakladatel jej může uložit i před připojením spoluhráče. Druhý hráč menu
nevidí a server jeho pokus o změnu odmítne. Zůstávají přístupy, skóre a pozvánka.
Nový klient proti starší službě zachová původní 2 + 1 s, ale menu zablokuje
s vysvětlením. Po vydání je potřeba obnovit stránku u obou hráčů.
Každý má jedinou uzamčenou odpověď; rychlost nepřidává body. Oba mohou
získat 1 bod, chyba nebo chybějící odpověď dává 0. Použité zadání se v této
hře neopakuje, pomocné kartičky se mohou opakovat z původní zásoby.

Po skrytí kartiček oba klienty potvrdí uzavření výběru. Teprve pak server
jednou započte body, odhalí odpovědi a oba uvidí velký správný obrázek,
FR zápis a přehraje se FR slovo. Vyhodnocení trvá nejméně 2 s a dohrání
obou poslechů. Následující kolo zahájí vyzyvatel tlačítkem „Další kolo“.
Průběžné skóre zůstává dole. Na konci lze zahájit hru se stejnou konkrétní
zásobou nebo změnit filtr; reset skóre a 12 kol zachová místnost, obě
identity, přístupy i pozvánku. Změna filtru během hry vyžaduje potvrzení resetu,
zrušení výběru nemění serverový stav.

Autoritou časového limitu je server; klient odvozuje čas od serverového
času a monotónních hodin, nikoli od nastavení data na počítači. Kartičky
se skryjí i bez další síťové odpovědi. Příliš pozdní doručení okna vyžaduje
ruční návrat a nové celé okno. Odchod, skrytí stránky či chyba spojení
zastaví lokální časovače a zvuk. Návrat do nezapočítaného výběru zopakuje
stejné zadání, vymaže jeho nevyhodnocené odpovědi a změní číslo fáze.
Již vyhodnocené body se neopakují. Chyba obrázků zastaví přípravu; chybu
zvuku lze opakovat nebo výslovně přeskočit, nikdy se nenahradí jiným jazykem.

Služba zachovává pexesový protokol1; nový `mode=duel` přidává akce
`answer`, `closed`, `next`, `timing` a vlastní fáze `duel_intro`, `duel_choose`,
`duel_result`, `duel_between`. Akce obou režimů se nemíchají. Budoucí otázky
a cizí odpověď před vyhodnocením server klientovi nepředává. Klient má
oddělený klíč `vocabulary-fr.duel-session.v1`. Health zveřejňuje podporované
`games`; starší služba bez duelu způsobí jasnou zprávu místo založení pexesa.
Používají se pouze existující veřejná FR/CZ média.

Přejímka: `tests.test_vocabularyfr_multiplayer` spouští i skutečný JS duel
nad dvěma nezávislými syntetickými prohlížeči; HTTP test používá skutečný
server a dvě identity. Stejná sada ověřuje všech 12 kol, časové hranice,
zálohu stavu v SQLite, skryté odpovědi, idempotenci, návrat a změnu filtru.
Vstup z galerie kryje `tests.test_vocabularyfr_web_gallery`. Vizuální a
akustická přejímka na fyzických zařízeních zůstává samostatná. Před živým
použitím je nutné vydat klienta a zvlášť aktualizovat export/server herní
služby. Tento vývoj neaktivuje síť ani neaktualizuje běžící server.

Při obnovení přerušené otázky se zachovává její roundTextSeconds a roundImageSeconds; čekající nastavení se převezme až pro další otázku. Starší místnosti bez těchto polí používají při opakování původní 2 + 1 s.
