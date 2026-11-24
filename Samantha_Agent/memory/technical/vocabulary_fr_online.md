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
  leave, start, flip, heard, rematch. Všechny operace s místností po join
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
