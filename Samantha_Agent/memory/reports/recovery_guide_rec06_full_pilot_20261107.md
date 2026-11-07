# REC-06 — úplný zdrojový manifest a připravený čtecí pilot

Navazující stav: Míla tuto cenovou kartu schválil. Před prvním modelem ale
nový kalendářový main zneplatnil konkrétní zdroje; žádný paid turn neproběhl.
Aktuální podklad je `recovery_guide_rec06_source_refresh_20261107.md` a
`recovery_guide_rec06_full_card_20261107_v2.json`. Následující původní
manifest/cena se zachovávají jako historie schválené staré karty.

2026-11-07, Data, vlastní větev `data/parallel-20261104`.
Stav: **připraveno k přijetí konkrétního rozsahu a ceny, žádný další placený tah**.
REC-06 jako celek pokračuje; tento krok nepovoluje publikaci ani týdenní provoz.

## Zdrojový rozsah

- Původní návod se čte celý jako první, ze schváleného Desktop TXT. SHA-256
  `a3659d9cf61ccd9d1c04737060f215ec4b6547da1eb877aa92b793f97e936935`.
- Dokumentace se čte přímo z Git objektů připnutého místního `main`:
  `2909ea5ace2e993edb5ace4875ec552f00a7e1e2`. Žádný checkout, merge, rebase,
  čtení Willových pracovních změn ani spuštění kódu tohoto commitu.
- Plný navržený rozsah: **529 dokumentů**, **6 281 401 UTF-8 bajtů**
  včetně původního TXT. Explicitní oblasti: Samantha memory/docs/camino,
  připojené PythonMF docs, MatysekANJ docs a iOS; dále vybrané AGENTS/README.
  **114 ostatních textových cest je vynecháno** podle deklarovaných pravidel.
- Plný snapshot SHA-256:
  `7b08aba87f1956e9d4587a13421d91d6c556c506db59a33dd19a70badec0072b`.
  Každý soubor má samostatný hash a autoritu; soubory se nezkracují.
  Handoffy/reporty/TVBCP zůstávají historické či smíšené důkazy.
- Texty jsou pouze sledované, regulární UTF-8 Git bloby. Symlink v Git stromu,
  neplatné UTF-8, známá signatura tajemství či změněný původní TXT přípravu
  zastaví. Vynechávají se private/session/autosave oblasti. Filtr neprokazuje
  absenci všech možných tajemství; osobní zdroje ani celá konfigurace nejsou
  automaticky přidané. Neukládá se obsah soukromých e-mailů, auth ani Keychain.

Nový `collect_revision()` umožňuje zkontrolovat přesný committed main bez
zásahu do jiné pracovní kopie. Varianta `project_only=True` umí výslovně
užší projektový rozsah; žádná taková změna není automatický cenový fallback.
Po dobu přípravy je Mílovi nabídnuta volba rozsahu. Bez jiné volby se připraví
původní úplný návrh, který se stále musí přijmout s konkrétní cenou.

## Cena a meze

| Položka | Plný navržený pilot |
| --- | --- |
| Model | přesný gpt-6.1-sol / medium, bez náhrady |
| Počet tahů | **14 čtecích dávek + 1 syntéza**, celkem 15 |
| Každá dávka | celý původní návod a celé přiřazené dokumenty |
| Syntéza | celý původní návod a ověřená zjištění ze všech dávek |
| Referenční cena bez nové marže | 144,8141 Standard kreditu |
| Plán s marží | **193,61315 Standard kreditu** |
| Navržená přijímací mez jedné úlohy | **200 Standard kreditů** |
| Plánovaný input s marží | 3 152 263 tokenů součtem všech kontextů |
| Rezervovaný output | 144 000 tokenů součtem všech tahů |
| Jeden kontext | plánovací mez 250 000, kontrola celých souborů |
| Výstup | kontrola nejvýše 8 000 tokenů na dávku / 32 000 na syntézu |
| Čas | 30 minut na úlohu; vlastní připojení čeká 90 s na zprávu |
| Publikování / role / služba | žádné |

Marže je **1,25 × referenční textový počet + rezerva 8 000 tokenů na každý
tah**. Tato rezerva není prokázaný horní odhad. Vychází z opatrného plánu
po syntetické kalibraci: 500 referenčních textových tokenů vs 5 248 skutečného
inputu. Rozdíl nerozkládáme na tokenizaci a serverové rámování; poměr nelze
mechanicky přenést na celý korpus.

Upstream tiktoken 0.14.0 stále nezná přesný Sol. `o200k_base` zůstává
referencí, nikoli přidaným mapováním modelu. Publikovaný výchozí kontext Codex /
ChatGPT Work je 500K; skutečný limit konkrétního připojeného serveru dosud není
číselně doložen. Plán proto nepoužívá API maximum jako důkaz běžícího runtime.

Sazby ověřené z OpenAI Docs: 50 input / 2,5 cached input / 250 output
Standard kreditů na 1M tokenů. Cache se předem nepředpokládá. Není to API
dolarová cena ani fakturační účtenka. **200 kreditů není tvrdý fakturační strop**:
transport neumí vynutit max output; po nadlimitním či nejistém tahu se
zachová skutečná známá spotřeba a další tah se nespustí. I neúspěšný nebo
obsahově nepřijatý návrh může stát kredity. Stejný model se automaticky neopakuje.

## Spustitelný izolovaný vstup

Nové `app.recovery_guide_full_pilot.py` poskytuje:

- `prepare(project_only=False)`: neplacený manifest, rozpočet a původní karta
  ve vlastní `.venv/recovery_rec06_full_pilot`. Žádný thread/start ani turn/start.
- `run(approved_digest=...)`: pouze po lidském přijetí přesné karty jeden
  úplný pilot; výsledek je privátní kandidát pro obsahovou přejímku.

`prepare` připne celý snapshot, výpočet rozpočtu, úspěšnou původní kalibraci,
socket/peer, relevantní implementaci a nezměněný centrální konfigurační soubor.
Plná soukromá karta je neměnná; její veřejná projekce s cenou a hashi zdrojů
je `recovery_guide_rec06_full_card_20261107.json`. Existence karty není souhlas.

Připravený approval digest:
`9a532089fab4299bbebfa9f7c2bf8a84b95253d5bf8456672ec1fdcb38ba0133`.

Před připojením se trvale rezervuje jedno job ID. Controller z REC-01 ukládá
in_flight před každou možnou placenou akcí, eviduje pokrytí a součet skutečné
spotřeby. Adaptér navíc uloží per-turn marker před wire, známou identitu tahu
a dokončenou účtenku před parsováním/validací. Chybný JSON či nástrojový typ
nezmažou známé tokeny. Opakovaný run i v jiném týdnu vrátí původní účtenku.
Není reset, retry, automatická náhrada modelu nebo rozšíření source scope.

Přísný kvalitativní validátor může návrh odmítnout, například při nových
příkazech bez registrovaného kontextu. Dorazí-li syntéza, celý původní JSON
zůstane v soukromé per-turn účtence k posouzení stejného výsledku bez dalšího
modelu. Automatické obejití validátoru nebo publikování tím není povolené.

Každá čtecí dávka musí odpovídat připnutému payload hashi a pořadí. Syntéza
smí přijít až po všech dávkách. Každý tah má čerstvé ephemeral vlákno,
readOnly bez sítě, never approval, prázdný cwd a per-turn Standard. Vypíná se
stejných 30 funkcí jako při úspěšné kalibraci, všechny nakonfigurované MCP a
nalezené skills. Původní produkční klient, runtime a role se nemění.
Backend unified_exec zůstává samostatně nevypnutelný; vypnuté je vystavení
shellového nástroje. Událostní audit není sám o sobě preventivní sandbox.

Před další dávkou se znovu ověří main head, původní TXT, otisky kódu,
kalibrace a runtime. Souběžný nový main proto může pilot zastavit; placené
dokončené dávky se neopakují a částečná účtenka zůstane k ručnímu posouzení.
Pilot je výslovná zkouška kandidáta modelu, nikoli aktivace centrální role.

Pro spuštění z Data worktree **není potřeba nasazovat tento nový pilot**.
Připravená karta se má provést nad uvedeným main před jeho další změnou;
po převzetí nového commitu do main by bylo potřeba nejprve připravit novou
kartu nad novým zdrojovým stavem. Pro celý běh počítat s klidovým oknem až
30 minut bez změny main a původního návodu. Toto omezení je viditelné,
nikoli obcházené přegenerováním zdrojů po schválení ceny.

## Mac / iPhone: co je a není ověřené

Čtecí připojení znovu potvrdilo peer .163.0, spravovaný účet chatgpt a přesný
Sol/medium. Stávající Cockpit `/api/server/health` vrátil ok true a jeho
čtecí `/api/web-apps` vrací 12 katalogových položek. **Katalog není úplná
inventura všech aplikací ani důkaz funkčnosti každé z nich.** Neověřovalo se
nasazení každého blobu main, nastavení telefonu, přihlášení do všech služeb
ani celá instalace Macu. Karta tyto mezery výslovně obsahuje.

Pro následnou přejímku celého návrhu je třeba samostatně doplnit:

- odsouhlasený seznam aplikací/integrací a pro každou účel, instalaci,
  verzi, bezpečné nastavení, datové cesty, přihlášení bez hodnot tajemství,
  oprávnění, start a ověřovací postup;
- Mac: aktuální OS baseline, skutečné prostředí služeb/PATH, aplikace,
  Tailscale/HTTPS, centrální role, zálohy a datové kopie;
- iPhone: konkrétní používaný prohlížeč, Tailscale, uložený vstup do Cockpitu,
  aplikaci Camino, případné zkratky a oprávnění; stav se nesmí odhadnout;
- první skutečné dvě kopie TXT, metadata uploadu a otevření přes Soubory.

Dokumentované nastavení smí být v návrhu uvedeno jako dokumentované;
neověřené se musí přiznat. Automatická publikace je i po modelovém výsledku
zakázaná. Plná aplikační kontrola REC-03 a ruční obsahová přejímka následují.

## Ověření a předání

28 nových neplacených testů: neměnné Git bloby i při novém/dirty worktree,
scope/alias/UTF-8/secrets, explicitní cena s marží, per-turn Standard,
oprávnění, pořadí/payload, neznámá spotřeba, zachování markeru/turn ID,
pád před a po odeslání, opakování i další týden bez nové akce. Testovací
controller používá syntetické zdroje a transport, nikoli živý model.
Plná projektová brána: 2 599 testů OK, 5 skipped; závěrečná statická brána OK.

Změny: tři nové app moduly (`recovery_guide_revision`, `recovery_guide_costing`,
`recovery_guide_full_pilot`), dva testové moduly, seznamy quality gate,
registrace Python vstupů a tento projektový zápis/karta. Žádné závislosti,
produkční klient/runtime/Cockpit/e-mail, role JSON ani provozní TXT se neměnily.
Původní syntetická účtenka zůstává zachovaná. Výsledek pro Willa se předává
kanonickým handoffem/TVBCP, bez zprávy, merge, push nebo nasazení Datou.

Nejbližší krok po přijetí karty: jednou spustit přesný full pilot, posoudit
skutečnou spotřebu a celý kandidát. Nejasný výsledek se neodesílá znovu.
Teprve po obsahové přejímce povolený produkční adapter, dvě kopie, iPhone
a samostatně autorizovaná aktivace týdenního slotu. Samotné nasazení kódu
nepovoluje placené čtení, publikaci návodu ani běh na pozadí.

## Primární zdroje

- [OpenAI Docs: Standard kredity](https://learn.chatgpt.com/docs/pricing#token-rates)
  — aktuální sazby a oddělení API-key účtování.
- [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
  — úsilí medium a výchozí Codex/Work kontext, nikoli důkaz konkrétního serveru.
- [App Server: start a turn](https://learn.chatgpt.com/docs/app-server#start-a-turn)
  — per-turn Standard doložené navíc přesným schématem .163.0 z kalibrace.
