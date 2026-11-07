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
   syntetické, nikoli měření skutečných tokenů. Nic nebylo do prostředí
   doinstalované a cena skutečného týdenního čtení dosud není změřená.
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
