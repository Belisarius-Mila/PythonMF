# Hodinová služba a vědomé zapnutí hlídání

## Příprava zapnutí hlídání a upgradu služby — 2026-11-12

Míla výslovně schválil upgrade vlastní hodinové služby i vědomé zapnutí
followup monitoru. Předchozí p+n je dokončené:37292ecb, Terra,
job b794e9f91e021059c97a7851827e6160,3722 testů, smoke5/5; oba živé HTML
odpovídaly zdroji, GitHub/main zarovnané. Zde nejde o opakování tohoto vydání.

Doplněn registrovaný configure_followups: potvrzený boolean a přesný
instalovaný SHA, vlastněná načtená aktivní služba a bytewise shoda čtyř
kritických modulů s commitem. Zápis serializovaný s instalací/workerem,
idempotentní opakování bez zápisu. Nepouští model, scan ani kickstart.
Po změně příznaku neoznačuje starý heartbeat za novou kontrolu; resetuje
technickou identitu slotu i při zapnutí ve stejné hodině. Ruční evidence,
kurzory, role, SMTP a kalendář se tím nemění. Vypnutí funguje i při rozbité instalaci.

67 cílených PASS /16,235s. Plná finální brána viz report
reports/email_followups_activation_20261112.md. Původní překonaná sada byla
záměrně ukončená exit143 a není dokladem úspěchu. Provozní výsledek se ukládá
odděleně v data/private/email_followups_activation_20261112/.
Další krok: dokončit checkpoint, registrované pause/prepare/upgrade, ověření
instalované kopie, configure_followups a přirozený nový heartbeat.
Samostatný e-mailový TVBCP stále není dohodnutý; existující Cockpit dokumenty
kryjí jen své UI/workflow. Skutečný reply/modelový průchod a Mac/iPhone jsou zvlášť.

## Provozní přejímka

Před zásahy ověřit vlastní enabled/owned/loaded službu7f47a41f a uložit
privátní otisky stavu/nastavení/rolí. Upgrade používá přesný schválený commit
s přijatou branou; stará kopie i servisní záloha zůstávají. Při neúspěchu
využít původní registrovanou obnovu, žádný ruční přepis LaunchAgentu.

Ověřit celý instalovaný manifest a readiness přímo novým interpretem
v instalované kopii. Zapnutí samo není doklad dokončeného workeru;
počkat na nový launchd heartbeat a živé API configured/worker_recent.
Dokončený hodinový slot se nevrací zpět a žádné staré posouzení se neopakuje.
Starší jediný aktivní zdroj byl přesně ověřen registrovaným verify_source
přes původní UID/epochu/digest. Výsledek verified_headers; všechny původní
zprávy, kurzory a ruční pole shodné, bez historického scanu či modelu. Důkaz
source_verification_result.json v privátní složce.
Neúplný zdrojový scan zůstává v UI neověřený až do přirozeného dalšího scanu.
Nevyvozovat 'bez odpovědi' jen z dostupného heartbeat.

Ostré účtenky/otisky a výsledky pouze v privátní složce výše. Do Gitu se
neukládají texty/identita korespondence, adresy, nastavení přihlašování ani tokeny.
Nový placený pilot a SMTP/kalendář nejsou součástí této servisní operace.
Aktivační příkaz má vlastní checkpoint. Po skutečné aktivaci a provozním zápisu
následuje dokončení Mílova již zadaného p+n všech commitů a úklidu jedním
novým registrovaným požadavkem nad novým přesným SHA. Předchozí dokončený job
b794e9f91e021059c97a7851827e6160 se neopakuje ani nepřepisuje.

## Finální lokální přejímka

67 cílených PASS /16,235s; finální plná brána3730 testů /525,585s,31 SKIP,
Cockpit quality gate OK. Finální otisky service_control/registry/testů zachované
v tested_sources.json. Statická checkpoint brána následně před commitem.
