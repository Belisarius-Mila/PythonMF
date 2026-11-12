# Hlídání záležitostí — ruční UI etapy 2

Datum: 2026-11-12 10:37 CET
Proud: project-email-cases, společná e-mailová stránka Cockpitu.
Výchozí main: efc16b97cdb4ab04f88a98b630adb512d1bb9cfb.

## Výsledek a rozsah

## Hlídání záležitostí — ruční UI etapy 2, 2026-11-12 10:37 CET

Lokálně dokončený formulář Hlídat tuto záležitost, přepínač Hlídání/Vyřízeno,
úprava cíle/kroku/času, obnovení stejné identity a přehled Aktivní/Vyřízené.
Historie i zdrojový text zůstávají dostupné po skrytí původní e-mailové karty.
Detail čte výhradně uložený zdroj se shodnou identitou a content_digest,
bez IMAP a další kopie těla v evidenci hlídání. Nejasný/chybějící zdroj se nenahrazuje.

Ruční evidence není automatický monitor: automatic_monitoring=false a thread_binding=pending.
Datum se zadává výslovně v Praze; žádný tichý výchozí termín. Formulář zachová
rozepsané údaje při konfliktu. Nejistý zápis blokuje opakování, po reloadu se
ověřuje čtením původního operation_id v historii. SessionStorage obsahuje jen
identitu pokusu a zdroje/záležitosti, ne text e-mailu ani formulář.
Použitý stávající třicetisekundový refresh, bez dalšího timeru.

Ověřené Node průchody a30 doménových/HTTP testů PASS. Skutečný headless Edge:
390×844 formulář bez horizontálního přetékání;1280×1000 založení, vyřízení,
obnovení stejného ID/generace3, skrytí karty a čtení původního zdroje PASS.
Fyzická iPhone přejímka otevřená. Plná brána PASS: 3529 testů /31 SKIP (516,847 s).
Pouze lokální vývoj; nové p+n ani aktivace nejsou součástí tohoto kroku.
Samostatný e-mailový TVBCP dál není dohodnutý; je viditelným dokumentačním
blokátorem uzavření celého proudu. UI zapsané v existujícím Cockpit handoffu/TVBCP.
Další vývoj: etapa3 — přesné vazby odpovědí a časové kontroly i bez nové pošty.
Report: reports/email_followups_ui_20261112.md.

## Převzetí a implementace

Zachované commity8f64dca7 a9d89446b na adam/email-followups-ui-20261111
obsahovaly přijímací kontrakty, časový helper a hooky, nikoli hotový formulář.
Větev zůstala zachovaná. Převzaté testy a základ helperu doplnil Adam přímo
nad současným main; žádný placený pokus se neopakoval. Původní Luna role,
modelový JSON a vydávací mechanismus se nemění.

Nový followups.js obsluhuje pouze registrovaný endpoint /api/email-agent/followups.
Create/update/set_state používají stabilní operation_id a očekávanou revizi.
Na nejasný výsledek se neposílá druhý POST; původní identita je zachovaná.
409 ponechá formulář i text a zablokuje opakování staré revize, dokud uživatel
vědomě neotevře aktuální záležitost. Bez změny polí se update neodesílá.
Pozdní GET ani starší revize nemohou vrátit dokončenou věc mezi aktivní.
Při výpadku čtení zůstává poslední seznam, nové zápisy jsou zablokované.

Datum je explicitní datetime-local v Europe/Prague. Převod ověřuje skutečný
zimní/letní offset; neexistující nebo dvojznačná DST hodina je odmítnutá.
Při obnovení se mění pouze nový čas a lifecycle, nikoli cíl či historie.
Tato evidence neposílá upozornění a nevytváří kalendářovou událost.

Výslovný detail má přídavné source_message z již uložené zprávy. Identita se
ověřuje proti vazbě; neexistující originál není nahrazovaný jinou zprávou.
Text se nevkládá do HTML a nekopíruje do doménové evidence. Read-only test
ověřil beze změny souborové bajty i po skrytí zdrojové karty.

## Důkazy a meze

- Původní UI kontrakt FAIL před přidáním followups.js; po implementaci PASS.
- Node: založení, zrušení bez POST, úpravy, lifecycle, reload, souběh,
  konflikt,503/síťová nejistota, selhání tab storage, stará GET, bezpečný text,
  source read a chybějící source, původní editor odpovědí/kalendáře/předvolby PASS.
-30 doménových/HTTP testů v source_tests.log PASS. Přidány2 doménové a1 HTTP
  regrese konkrétně pro dostupnost zdroje po skrytí a odmítnutí jiné identity.
- Skutečný Edge headless přes CDP: mobilní formulář390×844 bez přetékání;
  desktop1280×1000: create→completed→active stejné ID/generace3,
  skrytí původní karty a následné zobrazení původního zdroje PASS.
- Vizuálně prohlédnuté mobile.png a desktop.png. Jde o syntetickou lokální
  fixture, nikoli živý Cockpit nebo fyzický iPhone. CUA host byl nedostupný,
  použit samostatný headless profil bez zásahu do uživatelova prohlížeče.
- Statická brána a git diff --check podle static_gate.log.
- Plná brána PASS: 3529 testů /31 SKIP (516,847 s).
- Soukromé syntetické důkazy: data/private/email_followups_ui_20261112/.
  Do Gitu nepatří browser profily, screenshoty, testovací stav ani logy.

Při neověřeném zápisu zůstává původní intent blokovaný; nepřeklápí se na
nový pokus. Nezapsaná nebo v historii nepotvrzená operace vyžaduje dohledání
původní doménové účtenky, nikoli automatické opakování. Automatická služba
etapy3, chytré další kroky etapy4, p+n, servisní upgrade a fyzická přejímka
zůstávají dalšími kroky. Samostatný e-mailový TVBCP nebyl dohodnutý a je
viditelně otevřený; aktualizovaný existující Cockpit handoff/TVBCP kryje UI,
nikoli nahrazení dokumentu celého e-mailového proudu.
