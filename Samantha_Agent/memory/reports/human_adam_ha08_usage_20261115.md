# HA-08 — Čas a spotřeba práce


## 2026-11-15 20:13 CET — HA-08: čas a doložená spotřeba práce, místně

Hotovo: V Práce / Probíhá je přehled spotřeby s rozpadem na Adama a přesně
přiřazená registrovaná předání pomocníkům. Zachovává vstup, cache, výstup,
uvažování, výchozí a konečné počítadlo vlákna, čas modelového průchodu
včetně čekání na pomocníka a dobu od přijetí do dokončení serverové práce.
Opakované události a čtení účtenky spotřebu nenavyšují. Uložené měření
přežije reload; obnova používá důkaz stejného původního tahu.
Rozhodnutí: Míla zadal nejprve samostatný HA-08 commit. P+n ani živý placený
pilot tím nezadal. Cenový odhad je volitelný; bez ověřené verze cen zůstává
částka i verze cen null. Historickou kreditní tabulku nevydáváme za dnešní
cenu ani vyúčtování. Nezavádíme nový řídicí endpoint či modelovou roli.
Další krok: Po cílené programové bráně samostatný lokální commit HA-08;
potom případné p+n na další výslovný pokyn.
Navrhované další kroky: Omezená živá přejímka Mac/iPhone a HA-09 — adaptéry
serverových úloh/checkpointu/vydání podle původního plánu.
Technický důkaz: Čerstvé thread/start poskytuje nulový základ. Pokračující
stejný klient používá poslední potvrzené kumulativní počítadlo se shodným
modelem, effort a service tier. Resume, neznámý základ, změna nastavení,
pokles čítače, vadná telemetrie nebo nejistý konec nedají falešnou úplnou
deltu. Cached input a reasoning zůstávají podmnožinami vstupu/výstupu.
Původní příjemce tahu předává pouze číselnou projekci, ne reasoning,
prompty či nástrojové argumenty. Frontend nepřebírá nekonzistentní součet.
Soukromý finální důkaz a přesné počty: data/private/ha08_usage_20261115/completion.json.
Rizika: Úplnost znamená evidovaný modelový tah a registrovaná předání přes
vývojový portál, nikoli účetní spotřebu účtu či libovolný vnější proces.
Samostatný vydávací job bude navázán v HA-09; necitujeme globální poslední
job. První tah po resume má bez základu neznámou deltu; další může použít
nově ověřený konec. Časy pomocníků se překrývají s průchodem Adama a nesčítají
se. Doba od přijetí končí serverovým potvrzením; při havarijní obnově může
zahrnout čekání na ověření původního výsledku. Syntetické testy a headless
prohlížeč nenahrazují skutečnou modelovou ani fyzickou iPhone přejímku.

Datový kontrakt: TurnReceipt.token_measurement → kanonická relace a HA-04
owned_work; GET /api/human-adam/work vrací usage_summary s číselnými
components, recorded_usage, complete, elapsed_ms/elapsed_final a price.
Modelová delta používá total, nikoli součet průběžných last. Podrobnosti
předání se zapisují před pokusem a po účtence pod stabilním otiskem úkolu
v rámci původního workstream/client_message/thread. Kontrola kotev a accept
nevytvářejí další modelový komponent. Odhad ceny není zapnutý.

Sada test_human_adam_usage pokrývá kumulativní duplicity/coalescing,
reset/malformed počítadla, změnu modelu/effort/tier, resume, neznámý model,
přerušení, výpadek zápisu telemetrie, cizí parent, deduplikaci pomocníka,
reload a kanonickou obnovu bez opakovaného modelu. HTTP smlouva u klienta
bez telemetrie vrací unknown/null. Node prověřuje rozpad a neúplné stavy.

Doplněné ověření HA-08: kolize zámku telemetrie nečeká na původním
příjemci. Volitelný zápis pomocníka má paměťovou zálohu do povinné
terminální transakce; ztracená telemetrie nezmění neznámou spotřebu v nulu.
Úplnost celého evidovaného průchodu se potvrdí až při serverovém dokončení.
