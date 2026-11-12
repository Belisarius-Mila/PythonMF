# E-mailové hlídání — etapa 3: vazby zpráv a termíny

Datum: 2026-11-12 13:26 CET
Proud: project-email-cases; UI/workflow ve stávajícím Cockpit handoffu/TVBCP.
Výchozí main: 72e1015cf89a0b6c3623712d2912d18b33f6d369.
Zdrojový plán: Samantha_hlidani_zalezitosti_navrh_vyvoje_2026-11-11.txt, etapa3.
Míla zadal pokračování e-mailové práce; HA-05 zůstává Datovi.

## Hlídání e-mailů — lokální etapa 3, 2026-11-12 13:26 CET

Etapy1/2 včetně ručního UI jsou vydané v původním balíčku4242cf7f5bdb6b88724e635cde31b443.
Na Mílův pokyn navázal Adam etapou3; HA-05 zůstává Datovi. Lokálně hotové
konzervativní vazby příchozích zpráv a termínové kontroly ve stávajícím service_tick.
Jiný účet, chybějící/duplicitní ID, nový účastník a rozporné aktivní/uzavřené věci
se nespojí automaticky. Podnět i původní obsah související zprávy přežijí chybu
posouzení; hlídání drží jen identitu/digest, nepřepisuje ruční cíl ani lifecycle.
Kontrola běží i nad hotovým mailovým slotem bez dalšího posouzení. Negativní
výsledek vyžaduje úplný zdroj, shodnou epochu a čerstvý scan zahájený až po termínu.
Zdrojový čas se neposouvá pozdním dokončením modelu. Jeden aktuální podnět na věc.

UI čte ověřený stav, časy a související zprávy; starší zdroj lze výslovně ověřit
přesným UID/epochou/digestem, bez resetu kurzoru či zpětného průchodu schránkou.
Kompatibilní worker musí doložit monitor_version1 a čerstvý heartbeat; stará kopie
ani rollback nesmějí tvrdit běžící monitor. Výchozí doplněk je vypnutý v samostatném
privátním namespace; ServiceSettings a modelové role beze změny.
Finální478 cílených testů PASS; statická brána PASS. Plná regrese PASS:3670 testů /572,074s,31 SKIP; finální čtecí zpřesnění následně478 cílených PASS /32,772s, viz report.
Bez nového p+n, aktivace, servisního upgradu, skutečného modelového tahu nebo odeslání.
Instalovaná hodinová kopie zůstává7f47a41f; živá automatická schopnost byla čtecím
auditem vypnutá. Další: etapa4 — doložené obsahové návrhy v jednom běžném posouzení.
Celý samostatný e-mailový TVBCP není dohodnutý; existující Cockpit dokumenty kryjí
jen své UI/workflow. Report reports/email_followups_monitor_20261112.md.


## Doložené vazby

Header-only index je svázaný se skutečným EML content_digest. Message-ID má
normalizovanou doménu a zachovanou lokální část, stejně konzervativně účastníci.
In-Reply-To/References a stejný zdrojový účet musejí ukázat na jedinou věc;
nový účastník/CC, neznámý přímý rodič, duplicita nebo konflikt s uzavřenou věcí
vyžadují ruční ověření. Shodný předmět je pouze kandidát, ne automatická vazba.
Hlavičky neprokazují obsah, splnění cíle ani doručení příjemci. Nejasná vazba
se v této etapě eviduje a zobrazuje jako návrh k ověření; editor jejího výslovného
potvrzení/odmítnutí před ostrou aktivací zůstává navazující integrační krok.

Příjem atomicky uloží novou položku, fakt vazby a aktuální generaci před modelem
či posunem UID. Nejisté posouzení se neopakuje. Vztah neovlivňuje viditelnostní
filtr. Související tělo je v původním agentním itemu i při important=false nebo
chybě modelu; followups obsahuje jen ID/digest a odkaz. Ruční cíl, další krok,
check_at a active/completed se automaticky nemění. Vyřízená věc nepřijímá nové
podněty; po znovuotevření se staré generace nepřehrávají.

Starší karta bez indexu má potvrzený verify_source. Nejprve ověřená cache,
jinak jeden konkrétní read_item původního UID/epochy; přesný digest je povinný.
Před i po čtení CAS. Opožděný read neotevře vyřízenou věc. Trvalá doménová
účtenka přežije generic-cache eviction; reload pouze čte původní operaci.

## Zdrojový důkaz a termín

Původní hodinová služba/okno07–22 zůstávají jediné. Nový scan předem zneplatní
starou úplnost. Scheduler zaznamená complete pouze po úplném dočtení; dosažený
limit, pause nebo error jsou incomplete. as_of je začátek posledního zdrojového
scanu, verified_at jeho konec před modelovým posouzením. Pomalý model neposune
snapshot za deadline. Pro negativní podnět musí platit shodná epocha, health=ok,
complete, scan as_of nejméně od check_at a stáří nejvýše75min (hodina +15min
rezerva). Jinak explicitně neověřeno, nikoli tvrzení o nepřišlé odpovědi.

finish kontroluje hlídání i při already_completed, zero mail, pauze či limitu;
mailové posuzování se kvůli tomu neopakuje. Nastavení/zdroj/model nedostupné
znamenají neověřenost. V noci bez nového podnětu, ráno pouze současný stav,
bez přehrání každého zameškaného slotu. Jeden aktuální notice_id na věc,
generaci, ruční termín a poslední relevantní zprávu; další hodina jej aktualizuje.

## Kompatibilita a aktivace

Žádný nový klíč ServiceSettings; stará strict instalovaná kopie zůstává čitelná.
Privátní monitor konfigurace version1/enabled je standardně off a v této etapě
nemá aktivační setter/UI. Testy ji zapínají pouze v dočasné fixture.
Schopnost Běží vyžaduje čerstvý vlastní monitor průchod i kompatibilní heartbeat
s followup_monitor_version1. Starý worker/rollback s jiným heartbeat ji zneplatní.
Readiness dokládá podporovanou verzi, nikoli aktivaci či skutečnou přejímku.
Existující registrovaný servisní manifest zahrne nové moduly až při budoucím
schváleném prepare/upgrade přesného commitu. Dnešní7f47a41f se neupgradovala.

## Ověření a meze

454 cílených testů PASS /28,272s, včetně původních doménových, HTTP, Node,
service/scheduler, capability a Cockpit regresí. Nové scénáře zahrnují přesnou
změnu předmětu, účty/UID/epochu, nové účastníky, duplicitní/rozporné aktivní
či uzavřené věci, dvě instance, restart, atomic admission failure, vyřízení
během modelu/zdrojového čtení, backlog, no mail/already_completed, pause,
source/model setup error, pomalý model přes deadline, CAS/readback a rollback.
Statická brána PASS; Plná regrese PASS:3670 testů /572,074s,31 SKIP; finální čtecí zpřesnění následně478 cílených PASS /32,772s, viz report.
První plný běh byl záměrně zastaven před dokončením kvůli nalezené a opravené
hranici aktivní/uzavřené věci. Není dokladem úspěchu. Následující plný běh provedl3670 testů /558,013s
s jediným selháním starého asset kontraktu e-mailové stránky (31 SKIP).
Produkční kód prošel; zkontrolovaný nový HTML kontrakt59386 znaků/911 řádků
a SHA256 f574029924dcebdb7b7fa16d4ba4f2c1d29190532823d6d4ef12ce8ffd8fba24
je aktualizovaný.66 testů celého dotčeného frontendu/monitoru/HTTP následně
PASS /8,775s; navazující plná brána je doložená níže.
Důkazy: data/private/email_followups_step3_20261112/, mimo Git.

Čtecí provozní audit na začátku: služba enabled/owned/loaded, instalovaný head
7f47a41fec3ddf3d29bb3e6ff197236f3c61ce01; poslední check already_completed,
automatická schopnost false. Citlivý obsah se neopisuje. Při vývoji nebyl spuštěn
živý IMAP/SMTP/model/kalendářový zápis, Pushcut, upgrade nebo aktivace.
Žádná nová fyzická/živá browser přejímka, pouze deterministické DOM/HTTP fixture.
Samostatný e-mailový TVBCP zůstává nedohodnutý; existující Cockpit dokument
kryje pouze své UI/workflow a nenahrazuje jej. Etapa4 obsahových návrhů,
p+n, servisní integrace a skutečné malé případy jsou otevřené kroky.


## Finální úroveň ověření

Plná brána po opravě asset kontraktu PASS:3670 testů /572,074s,31 SKIP.
V průběhu tohoto běhu byl ještě zpřísněný pouze čtecí příznak worker_recent:
kompatibilní čerstvý heartbeat navíc musí mít completed/already_completed/incomplete;
paused/disabled/failed/outside_hours/busy/needs_initialization ani chybějící stav
neprokazují běžící kontroly. Persistence, párování, intake, termíny ani odchozí
workflow se tím neměnily. Finální dotčené moduly včetně celé frontend sady
znovu PASS:478 testů /32,772s. Jde o cílenou přejímku poslední čtecí změny,
nikoli nový plný běh3671 testů. Finální statická brána před commitem PASS.
