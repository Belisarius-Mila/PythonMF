# Týdenní správce obnovovacího návodu — neaktivní pilot

Implementační etapa 2026-11-07, proud `project-samantha-infrastructure`.
Schválený plán REC-01 až REC-06 je v `projects/samantha_external_backup.md`.
Tento dokument popisuje vývojový základ, nikoli zapnutého týdenního agenta.

## Co je připravené

- `app/recovery_guide_sources.py`: nejprve celý původní TXT, potom celé
  vybrané dokumenty; zmrazený Git HEAD, SHA-256, explicitní rozsah a počty
  vynechaných textů. Žádné zkracování souborů. Pracovní změna dokumentu
  inventuru zastaví. Nové necommitované soubory nejsou součástí manifestu.
- `app/recovery_guide_maintainer.py`: dávky celých souborů a syntéza,
  vkládaný tokenizer a transport, kontrola citací, kapitol a rozsahu,
  rezervace rozpočtu bez slibované cache, měsíční součet rezervací,
  trvalá účtenka, zámek a jeden společný slot pro ruční i plánovaný běh.
- App Server adaptér používá samostatné ephemeral read-only vlákno pro
  každou dávku, bez nástrojů/sítě/MCP/skills/plugins/hooks a historie projektu.
  Nemění globální konfiguraci ani původní App Server transport.
  Vyžaduje přesný Sol/medium a kontrolu centrální role před i po tahu.
  Explicitní Fast/flex/priority či neznámá preference jej zastaví.
- `app/recovery_guide_publish.py`: připnuté identity cílů včetně známých
  aliasů, původní verze, kandidát, žurnál, dva jednotlivé atomické zápisy,
  kontrola změny od převzetí a dokončení přesně stejných bajtů po přerušení.
- `scripts/recovery_guide.py`: registrovaný náhled/stav a záměrně blokované
  `run`/`tick`. `scripts/recovery_guide_launchd.py` pouze vypíše návrh plist.
  Neobsahuje instalaci, bootstrap, restart, placený tah ani publikování TXT.
- Parser centrálních rolí zná nový název `recovery_document_maintainer`;
  v `config/agent_roles.json` role přidaná **není**.

Původní text je zachován i v soukromém stavu syntetického/pilotního běhu,
každá dávka má otisk vstupu, důkaz pokrytí a číselnou spotřebu. První návrh
vždy skončí `review`: nutná je obsahová přejímka, ne automatická publikace.

## Registrované neplacené vstupy

Z adresáře Samantha_Agent, jeho vlastním Pythonem:

```text
.venv/bin/python scripts/recovery_guide.py preview
.venv/bin/python scripts/recovery_guide.py status
.venv/bin/python scripts/recovery_guide.py run
.venv/bin/python scripts/recovery_guide_launchd.py
```

Workflow ID: `recovery_guide_preview`, `recovery_guide_status`,
`recovery_guide_run`. První vypisuje manifest bez textů, druhý poslední
účtenku splatného týdne. `run`/`tick` vrátí `activation_required`, exit 2,
nula modelových volání a zápisů. Plist jde jen na stdout; nepřesměrovávat jej
do LaunchAgents ani nespouštět, dokud neproběhne samostatná aktivace.

`preview` při necommitované změně dokumentace vrátí attention. Neobchází se
to stashem či čtením starého HEAD místo nové dokumentace: nejprve dokončit
lokální checkpoint, potom přijmout konkrétní nový manifest.

## Korpus a platnost důkazů

Výchozí návrh rozsahu zahrnuje Samantha `memory/`, `docs/`, `camino/`,
README/AGENTS připojených částí repozitáře, PythonMF `docs/`,
`MatysekANJ/docs/` a `iOS/`. Soubor musí být sledovaný, UTF-8 a bez symlinku.
Soukromé oblasti, session logy/transkripty a přístupové údaje se nečtou.
Manifest uvádí i počet ostatních vynechaných textů. To je **návrh rozsahu**,
nikoli tvrzení, že každá dokumentace všech aplikací již byla nalezena.
Před prvním modelem doplnit/odsouhlasit seznam připojených částí a manifest.
Změna rozsahu mění otisk a vyžaduje nové přijetí.

Stav dokumentace je `documented_not_live`, historické či smíšené dokumenty
`historical_or_mixed`. Git HEAD nedokazuje nasazení. Zatím nejsou připojené
živé audity aplikací, konfigurací ani ručně ověřená nastavení telefonu.
Tyto informace se před pilotem doplní jen bezpečnými registrovanými audity
a explicitními allowlisty polí; žádné celé konfigurace s tajnými hodnotami.

## Dva cíle a skutečný nález

Kanonický provozní TXT má být `PythonMF/OBNOVA_SAMANTHY_NOVY_MAC.txt`,
druhý v iCloud Drive → Dokumenty se stejným názvem. Konkrétní uživatelské
cesty ukazuje `preview`; writer je nepřebírá z modelového výstupu.

Čtecí audit 2026-11-07: oba nové cílové soubory chybějí. Nezměněné TXT 1.2
jsou na Ploše, v kořeni iCloud Drive a také ve sledovaném kořeni
Samantha_Agent. Všechny tři mají SHA-256
`a3659d9cf61ccd9d1c04737060f215ec4b6547da1eb877aa92b793f97e936935`.
Staré kopie se nyní nemění ani nemažou; způsob jejich archivního označení
zůstává součástí prvního migračního kroku.

`CloudDocs/Documents` je známý symlink do `~/Documents`. Foundation na
samotném symlinku vrací `ubiquitous=false`; na skutečném cíli po resolve
vrací `ubiquitous=true, uploaded=true, uploading=false`, bez chyby uploadu.
Stejný kladný výsledek má původní TXT v kořeni iCloudu. Identita aliasu se
proto nejprve připne a zkontroluje, metadata se následně čtou z jeho
skutečného cíle. To potvrzuje dostupnost synchronizované cílové složky,
nikoli upload nového TXT, který zatím nebyl vytvořen. Nastavení se neměnilo.

Metadata se čtou přes systémovou Foundation/JXA bez instalace PyObjC.
JXA musí pole NSURL klíčů přemostit na NSArray; NSNumber 0/1 převádí na
bool. Chybějící hodnota, chyba či timeout nikdy nepotvrdí upload.
Přejímka v aplikaci Soubory na iPhonu se dokládá samostatně.

## Přerušení a ukládání

Řadič zapíše `in_flight` před každým možným placeným odesláním. Restart
vrátí původní účtenku i při `attention` či `in_flight`; nepokračuje další
dávkou ani znovu neodesílá. Vyřešení nejisté účtenky je ruční servisní krok.
Syntéza je předem plánovaná část jedné úlohy, nikoli retry.

Writer rozlišuje `prepared`, `local_saved`, `both_local_saved`,
`pending_icloud`, `uploaded` a `attention`. Žádná atomická transakce přes
dva disky/cloud se neslibuje. Po selhání druhého zápisu obnoví existující
první verzi, pokud ji mezitím nezměnil někdo jiný. Nově vytvořený soubor
nemaže; zůstane pozorovatelný stav k dokončení. Opakovaný přenos používá
stejné request ID, otisk kandidáta a připnuté cíle, nikdy další model.

Zámky koordinují vlastní procesy. Kontroly hashů před výměnou a po ní nejsou
univerzální filesystem CAS proti cizímu editoru píšícímu ve stejné mikrosekundě.
Při migraci proto nejprve ukončit souběžnou ruční editaci obou cílových TXT.
Stav/historie patří do vlastního soukromého adresáře; ne do Gitu. Retence
s mazáním není implementovaná ani schválená.

## Co ještě brání skutečnému provozu

1. Přijmout úplný zdrojový manifest a doplnit bezpečné doklady nastavení.
   Vybrat a ověřit přesný tokenizer daného modelu. V testech je počítadlo
   syntetické, nikoli měření skutečných tokenů. Izolovaný tiktoken 0.14.0
   přesný Sol nezná; referenční o200k_base jej nenahrazuje. Cena skutečného
   týdenního čtení dosud není změřená.
2. Schválit konkrétní nepublikující cenový pilot a limity, připojit živý
   adaptér k příslušnému povolenému vstupu. Nynější CLI run/tick je uzavřený.
   Před trialem znovu ověřit model, Standard režim a spotřebu. Výstupní
   rezervace/časový limit jsou přijímací a předběžné kontroly; současný
   transport nemá v tomto adaptéru tvrdý fakturační ani výstupní strop.
3. Přijmout konkrétní celý návrh a zdroje změn. Validátor prokáže citace,
   některé známé zrušené identifikátory, zachování kapitol/rozsahu a úzké
   signatury tajemství. **Neprokáže významovou správnost všech příkazů,
   neodhalí každé tajemství ani všechny možné rozpory.** Proto tento pilot
   nikdy sám neschválí publikaci či bezobslužnou týdenní revizi.
4. Provést první migraci a přejímku obou
   kopií včetně skutečného uploadu/iPhonu. Před aktivací odvodit publikaci
   jen z validované a obsahově přijaté účtenky, nikoli z volného argumentu
   knihovní funkce writeru. Automatické propojení řadiče a writeru zatím není.

Připravený slot je neděle 09:00 Europe/Prague, stále jen návrh. Patnáctiminutový
neplacený tick a RunAtLoad mají později vybrat jeden poslední splatný týden,
nikoli dohánět všechny minulé týdny. Bez schválení času, rozpočtu, přijatého
pilotního TXT a funkčního iCloud cíle se služba neinstaluje.

## Git, záloha a předání Willovi

Pro nový provozní soubor navrhuje integrační krok přesné pravidlo v kořenovém
PythonMF `.gitignore`: `/OBNOVA_SAMANTHY_NOVY_MAC.txt`. Nyní se nepřidávalo;
starý sledovaný Samantha_Agent TXT se tím nemění. Writer sám Git neovládá.
Recovery backup chodí po filesystemu, nepoužívá Git ignore. Test potvrzuje,
že jeho aktuální ALWAYS_FILTER nový TXT nevylučuje. Nová skutečná záloha
se neprováděla; její manifest ověřit při skutečné první migraci.

Will má převzít tento izolovaný vývoj do aktuálního main, zachovat své
novější role a práci a **sjednotit množinu známých rolí**, nepřepsat svůj
parser starší kopií. Nejdřív kompatibilní kód, až po další schválené přejímce
nová centrální role; v této etapě žádná aktivace JSON, služby nebo modelu.
Po převzetí znovu vytvořit neplacený manifest nad čistým skutečným main.
Nejbližší krok je uzavření rozsahu/metadata cílů a tokenizační preflight;
teprve z konkrétního náhledu požadovat souhlas s cenovým pilotem.

## REC-06: samostatná syntetická kalibrace

Aktuálně 2026-11-07 16:18 CET: Míla schválil přesnou původní kartu a jediná
skutečná zkouška **prošla**. Jeden dokončený tah, všech pět klasifikací/citací
správně, bez zaznamenaných nástrojových položek. Input 5 248, output 188,
total 5 436 tokenů, čas 6 646 ms; odhad **0,3094 Standard kreditu**. Doklad:
`reports/recovery_guide_rec06_result_20261107.json`. Nejde o celý čtecí pilot
REC-02 ani o publikaci/aktivaci. Původní trvalá účtenka brání dalšímu pokusu.
Referenční počet 500 tokenů nevystihuje skutečný input a nenahrazuje přesný
tokenizer; samotný poměr není spolehlivá extrapolace ceny celého korpusu.

Navazující úplný čtecí pilot má nový oddělený vstup
`app.recovery_guide_full_pilot.prepare/run`. Příprava čte přímo Git bloby
připnutého main bez přepínání pracovních kopií; celá plná varianta má 529
dokumentů a 15 tahů. Marže 1,25 textového počtu a 8 000 tokenů na tah dává
plán 193,61315 Standard kreditu, navržená přijímací mez 200. Marže není
prokázaný horní odhad ani tvrdý fakturační strop; přesné Sol mapování a
skutečný kontext serveru zůstávají nedoložené. Tato karta se musí přijmout
samostatně; původní souhlas s jedinou syntetickou kalibrací ji nepovoluje.

Úloha má vlastní pevný request, trvalou rezervaci a známé turn účtenky;
opakovaný vstup po výpadku nebo v dalším týdnu nevolá model. Kandidát je
pouze ve vlastní .venv, bez writeru, změn centrální role či plánovače.
Mac/iPhone důkazy a úplná aplikační přejímka nejsou tvrzené jako hotové.
Podrobnosti a konkrétní manifest v REC-06 full pilot reportu a cenové kartě.

Po výslovném souhlasu Míly bylo původní spuštění zastaveno ještě před
attempt markerem: Willův main nově obsahoval kalendářový krok 4a33af2a.
Úplná revize proto zatím neprovedla žádný placený tah. Explicitní neplacené
`prepare(refresh=True)` smí zachovat starou kartu a připravit nový manifest
pouze před jakýmkoli attempt/controller/turns. Nezvyšuje starý limit a všechny
verze sdílejí jediný job. Nový konkrétní manifest vyžaduje přijetí; dosavadní
schválený model/limit se zachovávají. Nejde o obnovení po nejistém placeném tahu.
Detaily v recovery_guide_rec06_source_refresh_20261107.md a kartě v2.

Manifest v2 byl Mílou přijat. První skutečný SDK tah dorazil se všemi
36 přesnými citacemi a jedním přesným original_guide navíc. Controller
zastavil pokrytí na 0 kvůli očekávané délce pole; known receipt má jasné
doručení a spotřebu 10,44505 Standard kreditu. Úzká normalizace původní řádek
vyjme pouze při úplném přesném pokrytí a zachová raw odpověď i notes.

`app.recovery_guide_receipt_recovery` pak může pod původním souhlasem v2
převzít známý první výsledek lokálně a SDK pokračovat až další původně
schválenou dávkou. Stejný job, jediný další marker, žádný reset/refresh,
žádné opakování tahu 1; unknown delivery nebo neznámá spotřeba jsou odmítnuté.
První známá cena se účtuje v navazujícím součtu jen jednou, celkový limit
zůstává 200. Konkrétní důkaz/checkpoint v REC-06 run reportu a JSON.

`app.recovery_guide_trial.prepare()` vytvoří pevnou neplacenou kartu pro
jeden Sol/medium tah se Standardem připnutým pouze na tento tah. Nečte
obnovovací TXT ani projektový korpus, neaktivuje centrální roli a nepublikuje.
`app.recovery_guide_trial.run(approved_digest=...)` vyžaduje konkrétní souhlas
s původní kartou. Není připojený k produkčnímu run/tick. Trvalý jeden slot
blokuje opakování při chybě, výpadku i restartu; zkouška nemá reset/retry.

Pilot používá pouze vlastní `.venv/recovery_rec06_trial`; žádný výstup se
nepřenese do iCloudu. Statický protokol pochází z oficiálního .163.0 balíčku
ve vlastní `.venv/recovery_rec06_cli`, nikoli ze změny globálního Codexu.
Při změně peeru, socketu, implementace nebo schématu je nutná nová kontrola.

Karta odděluje referenční počet tokenů od nepodporovaného přesného mapování
Solu, přijímací rozpočet od tvrdého fakturačního limitu a vypnuté vystavení
shellu od povinně zapnutého backendu unified_exec. Příprava karty není živý
důkaz izolace. Detaily a další oddělené přejímky v REC-06 reportu.

## Ověření a podklady

Testy: `tests.test_recovery_guide`; společně s routine_tasks, agent_roles a
workflow_commands. Plná projektová brána zahrnuje nový modul i kompilaci.
Testy používají pouze syntetické dokumenty, dočasné cíle a falešný transport.
Žádná živá služba, přepis provozního TXT ani placený tah není jejich součástí.

Oficiální podklady plánu: [model Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[Standard kredity](https://learn.chatgpt.com/docs/pricing#token-rates),
[konfigurace Fast](https://learn.chatgpt.com/docs/agent-configuration/speed#fast-mode).
Sazby jsou podklad pro předběžnou rezervaci, nikoli fakturační účtenka.


### Výsledek vývojového ověření 2026-11-07

- 37 nových syntetických testů; cílená sada s původními rolemi, workflow a
  rutinním kontrolorem: 65/65 OK.
- Plná projektová brána: 2 413 testů, OK, 5 skipped. Po následném zpřesnění
  Foundation aliasu a přidání jeho regresního testu znovu 65/65 cíleně a
  statická brána OK. Ostatní nezměněné testy se zbytečně neopakovaly.
- Reálná Foundation kontrola pouze četla metadata složky a původního TXT.
  Žádný modelový tah, zápis provozního TXT, push ani nasazení.

### Soubory vývojového balíčku

Nové: `app/recovery_guide_sources.py`, `app/recovery_guide_maintainer.py`,
`app/recovery_guide_publish.py`, `scripts/recovery_guide.py`,
`scripts/recovery_guide_launchd.py`, `tests/test_recovery_guide.py`, tento návod.

Upravené: `app/communication/agent_roles.py` (jen kompatibilita názvu role),
`app/routine_tasks.py` (přísnější omezení sdíleného čtecího helperu),
`app/workflows/commands.py`, `scripts/cockpit_quality_gate.py`,
`memory/ACTIVE_PROJECTS.md`, `memory/MEMORY_INDEX.md`, `memory/LESSONS_LEARNED.md`,
`memory/projects/samantha_external_backup.md` a kanonický handoff/TVBCP
`project-samantha-infrastructure.md`. Celkem 17 souborů.

## 2026-11-07 12:39 CET — doplnění REC-02

Přidané neplacené `preflight` a `runtime`, jejich workflow registry a
samostatná rezerva inspekce/syntézy. Tiktoken je pouze v izolovaném prostředí,
projektové závislosti ani role se neměnily. Kompletní zmrazený číselný plán
viz `../reports/recovery_guide_rec02_20261107.json`, praktická interpretace
viz `../reports/recovery_guide_rec02_20261107.md`.

Korpus 509 dokumentů: 10 dávek + syntéza, referenčně 139,1392 Standard kreditů.
Upstream mapování pro Sol chybí; běžící server 0.163.0 a nevyhovující
Standard preference se nesmí zaměnit za nové provozní ověření. Živý pilot
neproběhl, REC-02 není celá uzavřená. CLI run/tick i role stále neaktivované.
Další krok je doložení izolovaného Standard kontraktu ve Willově aktuálním
runtime a konkrétní přijetí kalibračního/cenového pilotu. Žádný restart zde.

## 2026-11-07 13:03 CET — REC-03, přejímka kvality

Povinný core validator přesměrovaný do recovery_guide_quality.validate.
Bezpečné kódy chyb jsou v quality_issue; chybná syntéza se neukládá ani
neopakuje. Navíc samostatné review nad explicitně schválenou inventurou
aplikací, Mac/iPhone checklistem a důvěryhodnými datovanými doklady.
Výchozí produkční inventura je prázdná a neschválená; žádné hádané role/aplikace.

Základní kontrola je zapojená do pilotního řadiče. Úplné review/checklist
je samostatné knihovní API a testy; existující modelový kontrakt jej zatím
sám nevytváří. REC-04 musí jeho účtenku a konkrétní přijetí Mílou svázat
s přesným kandidátem/kontextem/checklistem/cíli. Ani review není povolení
publikace. Podrobná specifikace a známé meze jsou v REC-03 reportu.

Cold-reader balíček byl čten novým izolovaným procesem bez projektové
historie; lidská/modelová přejímka skutečného návrhu ještě neproběhla.
Dosavadní REC-02 blokátory zůstávají, bez nového modelu/služby či zápisu TXT.

## 2026-11-07 13:33 CET — REC-04, přijetí a převod na testovacích cílech

Veřejná hranice je PublicationStore; nízkoúrovňový _publish_candidate je
interní a váže žurnál na hash přijetí. Zmrazený paket propojuje kandidáta,
kontext/checklist, kvalitativní doklady, validátor i identity obou cílů.
Přijetí má neměnný manifest a vzniká poslední. Původní verze se nemažou.

Přenos má společný zámek/aktivní marker, přesné stavy kopií a written flagy.
Pád nevede k dalšímu modelu ani opakování hotové výměny. Metadata auditu se
ověřují samostatně a po nich znovu oba hashe. Ruční změna/vrácení se nepřepíše.
Podrobný kontrakt i omezení jsou v REC-04 reportu.

Tento veřejný vstup je zatím pouze sandboxový: vlastní .venv/temp podadresář,
žádný produkční režim či implicitní cíle. Testovací uploaded je simulované,
nikoli skutečný cloudový důkaz. CLI run/tick a role zůstávají neaktivované.
Další REC-05 připraví trvalý plánovač; produkční aktivace zůstává REC-06.

## 2026-11-07 14:16 CET — REC-05, plánovač a dohled

WeeklyScheduler má trvalý týdenní záznam a oddělené fáze analysis/acceptance/
delivery. Rozpracované doručení řeší před novým týdnem. Nejistá analýza se
neopakuje ani příští týden; lze připojit jen skutečně známou místní účtenku.
No-change větev znovu ověřuje aktuální kopie po celé revizi.

Registrované schedule-preview/status a launchd/environment preview.
Připravený plist se pouze vypisuje, neinstaluje; bootstrap CLI s minimálním
PATH prošel, skutečný launchd/auth kontext ještě není ověřený. Den/čas a
rozpočty zůstávají neschválené, run/tick a centrální role neaktivované.

Vývojový plánovač pracuje výhradně se sandboxovými neplacenými callbacky.
Produkční adapter musí při REC-06 převzít přesné společné slot/request ID,
aktuální centrální roli a autentizovanou úzkou autoritu, ne používat druhý
odvozený týden nebo modelové potvrzení. Podrobnosti a otevřené předpoklady
jsou v REC-05 reportu. Skutečný REC-02 pilot i iPhone přejímka stále čekají.

## 2026-11-07 21:44 CET — konečný výsledek živého v2 pilotu

Druhý tah dorazil se všemi 65 zdroji, ale dva raw quote řetězce měnily první
písmeno oproti doslovnému zdroji. Controller proto zastavil další SDK kroky.
Celkem dva jedinečné tahy, 387 928 tokenů a odhad 21,013 Standard kreditu;
první cena je v pokračování zahrnutá jednou, nesčítat historické ledgery.
Žádný celý kandidát nevznikl, dalších 13 tahů/syntéza neprovedené.

Zachovat raw citace a přísný gate; další návrh je programový source/anchor
ID resolver pro inspect i synthesis. Není implementovaný ani modelově
ověřený. Nový placený trial nevzniká automaticky z nevyužité rezervy tohoto
uzavřeného běhu. Zdrojové/účetní důkazy v REC-06 run reportu a full_result JSON.

## 2026-11-07 — offline source/anchor protokol

Nové samostatné `recovery_guide_anchors.py`, `recovery_guide_anchor_protocol.py`
a čtecí `recovery_guide_anchor_audit.py` nevolají SDK. Modelový kontrakt vybírá
source/anchor ID; přesný text vrací program z katalogu celého snapshotu.
Inspect vyžaduje pevné pokrytí všech dokumentů, synthesis všechny dávky právě
jednou a pouze předané evidence (plus celý original). Nezměněný quality gate
nadále kontroluje přesné citace, historii i neschválené příkazy.

Offline regrese: 24 testů, 530 dokumentů + original zachovaných beze zkrácení,
14 requestů, 101 fixture dokumentů včetně dvou doložených kapitalizací.
Není to živá modelová přejímka ani nové přijetí starých notes. Uzavřený v2 job,
raw účtenky a původních 21,013 Standard kreditu se nemění; žádný placený tah.

Katalog/request hashe nejsou autorizace. Prázdné zdroje nejsou podporované,
max 996 zdrojů/schema. Chybí živý adapter a nové tokenové/cenové posouzení
(včetně celých řádků, metadat, schémat a syntézy). Další krok je nový izolovaný
trial a konkrétní neplacená karta, poté samostatně přijatý malý živý test.
Doklad a přesný návrh: reports/recovery_guide_anchors_20261107.md a
reports/recovery_guide_anchors_offline_20261107.json. REC-06 zůstává otevřená.

## 2026-11-07 — malý živý adapter připraven, zatím nespouštěn

Nové `recovery_guide_anchor_trial.prepare/run`, `recovery_guide_anchor_transport`
a `recovery_guide_anchor_costing`: oddělený pevný job pro dva malé modelové
kroky (inspect + synthesis), nikoli pokračování uzavřeného v2 či celý korpus.
Celý původní TXT + dva známé citační dokumenty, 75 100 bytů. Karta
566899e7…ddd8cb3 připíná main 0850e6f3, kód, manifest, peer/socket, konkrétní
inspect schema a pravidlo deterministické syntézy ze skutečné odpovědi.

Plán 14,72415 Standard kreditu; návrh přijímací meze 15 za oba tahy. Reference
není přesné Sol mapování a meze nejsou tvrdý účetní/output/časový strop.
Podrobnosti v reports/recovery_guide_anchor_trial_20261107.md a samostatné
card/offline JSON. Přesný nový lidský souhlas zatím chybí: žádný placený tah.
26 nových testů, 50 cílených OK; zdrojová fixture prošla inspect i synthesis,
není však skutečným modelovým výsledkem. Původní job/raw účtenky beze změny.
Při driftu před jakýmkoli pokusem lze neplaceně připravit explicitní revizi;
po rezervaci zůstává jen původní receipt, žádný retry ani reset. Další kroky:
malá samostatně přijatá živá zkouška, pak nová karta celého korpusu; žádná
produkční aktivace rolí, služeb, zápis TXT/iCloud nebo publikování v této etapě.

## 2026-11-07 — známý výsledek malé živé anchor zkoušky

Karta 566899e7…ddd8cb3 výslovně přijata a run zavolán jednou. Dva doručené
completed tahy; inspect 9,008 s a synthesis 400,240 s. Obsahově prošly oba
kontrakty i původní quality gate, original zachován doslovně včetně vnějšího
whitespace, obě přesné source/anchor evidence a dva unverified dodatky.
Syntéza byla obsahově znovu ověřena offline z raw, bez nového modelu.

Cena 8,50485 Standard kreditu je odhad ze skutečných tokenů; pod mezí 15.
Přesto celý job zůstává attention / accepted=false kvůli času >300 s.
Limit/state se nepřepisoval, žádný retry/reset/refresh/třetí tah. Starý úplný
v2 job beze změny. Příští run tohoto slotu smí pouze vrátit známou účtenku.

Důkaz: reports/recovery_guide_anchor_trial_run_20261107.md a *_result_20261107.json.
Nejbližší návrh je samostatný úplný anchor pilot s neplacenou kartou, aktuálními
zdroji a realistickým fázovým časovým plánem podle měření; nový celý modelový
pokus musí být konkrétně přijat. Celý korpus ani Mac/iPhone nastavení zatím
nebyly přezkoumané, žádný provozní návod či týdenní aktivace nevznikly.

## 2026-11-08 — celý neplacený anchor plán

Nový samostatný `recovery_guide_anchor_full_plan.py` nabízí prepare/measure
s offline inspection/validate_inspection/synthesis helpery, **nemá run**.
Plán dcfb8b2a…c6f805d nad main 6d5b576b: 531 dokumentů + original, celé
texty 6 314 979 B, 20 čtecích dávek + 1 syntéza, bez opakovaného čtení dokumentů.
Návrh 243,50895 / přijímací mez 250 Standard kreditů; o200k_base není přesné
Sol mapování, není to tvrdý billing/context/output cap ani schválená cena.

Synthesis rezervuje až 771 evidence rows a všechna bounded findings; každý
přesný evidence row <=160 reference tokenů, nejvýše 6 findings/dávku se dvěma
odkazy a celkem <=1000 reference tokenů. 782 dlouhých řádků nelze citovat,
ale plné texty se nekrátí. Žádný zdroj nebyl vynechán. Nová obálka ještě
není modelově ověřená; aktuální stav je plán s explicitně chybějícím adapterem.

Pro další kartu návrh 300 s inspect / 900 s synthesis (měření 400,240 s,
output-scaled rezerva 807,058 s); starý malý job zůstává attention při 300 s.
18 nových / 68 cílených testů OK a úplná offline zdrojová fixture, žádný model.
Doklad reports/recovery_guide_anchor_full_plan_20261108.md/JSON a offline JSON.
Příští vývoj musí připojit přesný plan digest k samostatnému trvalému běhovému
jobu, ověřit peer/socket/účet/role, vynutit meze a no-retry a až potom vytvořit
novou exekuční kartu. Souhlas s placením se v této plánovací etapě nežádá.

## 2026-11-08 — celý běhový adapter dokončen, čeká přesný souhlas

Nové `recovery_guide_anchor_full_pilot.prepare(plan_digest=...)/status/run` a
čistý isolated `recovery_guide_anchor_full_worker` jsou registrované odděleně
od starých jobů a produkčního CLI run/tick. Karta 4b22ea9e…4cce1d1 nad plánem
dcfb8b2a…c6f805d: 531 dokumentů + original, nejvýše 21 Sol/medium Standard
tahů, plán 243,50895 / přijímací mez 250 kreditů (ne hard cap), 300/900 s.

Přesný peer/socket/účet/model, kód/tokenizer a zdroje se připínají a kontrolují
před akcemi; trvalý marker před wire, raw receipts před přejímkou, jeden job
napříč předběžnými kartami, žádný reset/resume/retry. `status` pouze čte receipt
bez připojení. Structured error data zůstávají privátní, willRetry neopravňuje
nový tah, usage bez terminální události zůstane pouze pozorovaná. Přijatý
kandidát patří pouze do vlastní .venv; není to publication/activation grant.

Původní quality gate se nemění: nové příkazy bez allowlist a živé Mac/iPhone
claims bez důkazů jsou nepodporované. Celá aplikační inventura není prokázaná.
43 nových / 111 cílených testů OK; úplná 20+1 skutečná zdrojová fixture
bez modelu zachovala všechna findings, žádný starý job/plán nebyl přepsán.
Příprava nespustila žádný thread/turn. Souhlas s placením musí přijmout novou
kartu zvlášť; neplatí dosavadní souhlas s malým testem ani návrh rozpočtu.
Doklad reports/recovery_guide_anchor_full_pilot_20261108.md a card/offline JSON.

## 2026-11-08 — celý pilot skončil na nevydaném coverage ID

Schválený celý run karty 4b22ea9e…4cce1d1 byl zavolán jednou. První tah je
completed/delivered; 27 dokumentů, 6 findings, 9,58995 Standard kreditu.
Model zvolil covered.d0001 = l131111 pro AGENTS.md s 26 řádky. Toto ID není
vydané; dalších 38 referencí platných. Scope, findings 721/1000 reference
tokenů, evidence row meze, bezpečnost textů a input/output/time meze prošly.

Resolver odmítl celou dávku: attention / accepted=false, 0 přijatých dávek,
zbývajících 20 tahů ani syntéza neodeslané. Raw se neupravoval, žádný retry
či přijetí notes. Schema zatím omezuje anchor pouze vzorem l + číslo, takže
samo zabrání špatnému formátu, nikoli nevydanému číslu. Další návrh je čistě
offline zpřísnění na skutečně vydaná ID se znovu ověřenou velikostí/cenou,
nikoli oprava této odpovědi nebo pokračování původního uzavřeného slotu.
Doklad reports/recovery_guide_anchor_full_pilot_run_20261108.md a result JSON.
Staré joby/plán beze změny; žádný provozní návod, role, služba ani publikace.

## 2026-11-08 — offline přesný číselný index citací

Nové samostatné exact_schema/exact_plan nemění uzavřený executor ani staré
raw. Source_citation_index_v1 vydává pro každý request/zdroj právě 1…N
povolených referencí. Integer bounds a skupiny anyOf vážou source/domain;
internal decoder mapuje do původních lN a používá stejný resolver/quality gate.
Vstupní text se nekrátí, prázdné/nadlimitní řádky mají null index. Numeric
index není fyzický řádek a nesmí se přenášet mezi requesty.

21 schémat a 8683 probes nezávislým Draft202012Validator, 99874 mapování,
19 nových / 130 cílených testů OK. Protipříklad 131111 pro AGENTS.md odmítnut
max21; fixture není opravená modelová odpověď ani přijetí starého jobu.
Původní raw 6177159d…505b55a / job attention / 9,58995 zachovaný beze změny.

Plán a59c80c4…516c070 nad main6d5b576b: 531 dokumentů + original, 20+1,
237,43795 Standard kreditu, návrh meze240 (ne billing cap), syntéza234859
input. Nová reprezentace je offline, nebyla modelově ověřena a není zapojená
do běhového adapteru. Neexistuje nová exekuční karta či placený souhlas.
Doklad reports/recovery_guide_anchor_exact_20261108.md a plan/offline JSON.
Další krok samostatná integrace/dekodér/worker a nový konkrétní postup;
žádný automatický model, retry, publikace či aktivace. Starý job neopakovat.

## 2026-11-08 12:07 CET — přesný číselný protokol ve skutečném adapteru

Nové recovery_guide_anchor_exact_pilot.prepare/run/status a exact_worker
perform/dispatch jsou registrované. Worker vždy reprodukuje request-local
mapu a ověřuje wire/schema/index SHA, celou historii i raw; do původního
resolveru předává pouze nový interní decode. Staré raw ani job se nepřepisují.
Executor používá vlastní pevný job, připojení ke sdílenému socketu, vlastní
read-only ephemeral thread pro každou fázi a přesný Sol/medium/Standard.
Původní produkční klient/runtime, role a služba zůstaly beze změny.

Čerstvá karta 741e71da…492f570 / plán586cdf96…f3a3add, main6c610287:
532 dokumentů + celý original, 20+1, plán237,88715 / návrh meze240,
syntéza input235090/output32000, časy300/900s a run6900s. Nejde o tvrdý
billing/output/wall-clock cap. Runtime preflight pouze čtecí, peer0.163.0,
local CLI0.166.0; samotný nový wire není živě modelově ověřený.

Nový job not_started / nula modelových pokusů. K novému placenému běhu je
nutné přijetí této konkrétní karty; dřívější jediný souhlas nepřenášet.
Bez reset/resume/retry; při nejistotě status, ne nový send. Status nic
nevytváří a nepřipojuje. Výsledek pouze soukromý kandidát, publication false.
Nové příkazy bez allowlist a živé Mac/iPhone facts bez důkazů nepodporované.
Týdenní produkční agent a provozní kopie/upload nejsou tímto aktivované.
Důkaz: reports/recovery_guide_anchor_exact_execution_20261108.md a JSON.

Celokorpusová fixture přijata 20+1: všech 532 dokumentů přesně jednou,
celý original v každé fázi, všech 20 findings v syntéze. Syntetický wire,
skutečný izolovaný tokenizer, žádný model ani skutečné runtime spojení.
Status/replay bez spojení, status zachoval bajty i mtime. 46 nových testů,
plná kanonická brána 2794 testů / 5 skipped OK (539,094 s).
