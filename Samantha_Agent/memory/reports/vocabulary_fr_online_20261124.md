## 2026-11-24 13:20 CET — Místní první verze pexesa na dálku pro dva hráče

Hotovo: Francouzština Jana má vstup „Hrát spolu na dálku“ ze současného
výběru pexesa. Samostatná herní služba spojuje dva klienty soukromou
pozvánkou bez účtů: stejných 24 míst 6×4, 12 dvojic, krátká jména, společné
tahy a skóre. Shoda ponechá hráče a dvě šedá místa. Oba musí dokončit FR
poslech a krátkou 2s CZ nápovědu. Po shodě se na 2 s ukáže velká FR karta
s opakovaným FR poslechem bez CZ; delší zvuk dál zamyká tah. Obrázek se
přednačítá již při otočení. Poslední odměna předchází výsledku.
Při odpojení se fáze pozastaví; ruční návrat zachová stav bez nového bodu.
Ztracená odpověď se ověří čtením stavu, neposílá se znovu další klik.

Rozhodnutí: Míla schválil vývoj jedné partie Jana v Německu ↔ Míla doma,
první rozsah dva hráči a soukromý odkaz. Klient vybírá pouze 12 UID;
osobní označení, původní lokální pexeso pro 1–4 hráče, obsah a všechna média
zůstávají zachované. Backend je izolovaný od Cockpitu/App Serveru,
SQLite transakce drží jednu autoritu. Pozvánka je jen ve fragmentu adresy,
hráčské tokeny v sessionStorage/Bearer a hashované v privátní databázi;
skrytý plán se klientům nepředává. Host/Origin, souběh, identita požadavku,
očekávané kolo/fáze, limity a odmítnutí třetího hráče mají vlastní testy.
Žádná nová výroba médií, modelové volání ani zásah do živé služby.

Další krok: Určit a samostatně schválit konkrétní HTTPS adresu, hosting
a způsob nasazení izolované služby; poté fyzická přejímka obou Maců.
Pouhé FR Pages p+n backend nezprovozní. Při změně původu se osobní data
nepřenášejí automaticky; řešit je existujícím výslovným exportem/importem.
Navrhované další kroky: Projít připravený scénář Německo–domov včetně
výpadku, zvuku, poslední dvojice a další partie. Zde není nové p+n.

Technický důkaz: 23 cílených Python kontrol PASS; 16 nových online JS a 55 FR
JS včetně 2 nových kontrol předání výběru. Dva nezávislé klienty ověřují
oba poslechy, nižší druhé číslo, přednačtení obrázku, 2s odměnu/delší zvuk,
chybu/retry/skip, reload, síťový timeout i ztracenou odpověď bez další mutace.
Serverové zkoušky pokrývají celou partii s 12 dvojicemi, skóre, opakování,
restart DB, souběhy, přístupy a oddělení HTTP cest. 54/54 místních HTTP souborů
bajtově přesných; 25 původních klientských/datových souborů zachovaných.
GUI Safari nebylo dostupné: cgWindowNotFound, browser access host unavailable.
Není to fyzická ani přeshraniční přejímka. Finální brána a commit jsou
autoritativně v private vocabulary_fr_online_20261124/completion.json.
Návod: technical/vocabulary_fr_online.md; přejímací TXT v Downloads.
