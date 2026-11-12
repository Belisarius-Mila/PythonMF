# Hlídání e-mailů — etapa 4: návrhy a lidská rozhodnutí

Datum: 2026-11-12 14:27 CET
Proud: project-email-cases. Výchozí main10555d48e05490e9aa0f312ed49c0c8c70445ce5.
Míla schválil pokračování vývoje před p+n; HA-05 zůstává Datovi.
Plán: Samantha_hlidani_zalezitosti_navrh_vyvoje_2026-11-11.txt, etapa4 + dokončení ručních rozhodnutí etapy3.

## Hlídání e-mailů — lokální etapa 4, 2026-11-12 14:27 CET

Na Mílův pokyn pokračoval Adam po checkpointu10555d48; HA-05 zůstává Datovi.
Lokálně hotové doložené návrhy dalšího kroku v jediném běžném posouzení zprávy
a výslovné potvrzení/odmítnutí nejasných vazeb. Před posouzením se atomicky
zmrazí konkrétní zdroj, cíl, uživatelský základ, generace a identita pokusu.
Výsledek po ruční změně, vyřízení/znovuotevření, výměně zdroje či vypnutí doplňku
zůstane u původního pokusu jako neaktuální; nová záležitost se nepřepíše.

Citace musejí odpovídat skutečnému textu/předmětu/HTML. Neplatný volitelný
výstup nesmaže běžný e-mailový návrh. Převzetí mění jen next_step/waiting_on;
cíl, čas kontroly a active/completed mění dál uživatel zvlášť. Ruční přiřazení
po posouzení nevytváří druhý modelový tah; existující dvě věci se neslučují.
Jeden společný tah podporuje současně kalendář i hlídání, bez změny EmailProposal,
rolí, ServiceSettings a režimu odesílání. Výchozí monitor zůstává vypnutý.

587 cílených PASS /34,988s, statická brána PASS. Skutečný headless Edge:
390×844 náhled/úprava a1280×1000 převzetí/vazba PASS, bez přetékání a opakovaného
POST/modelu; mobilní tlačítka po vizuální opravě zkontrolovaná. Finální plná brána PASS:3709 testů /538,314s,31 SKIP.
Syntetický vstup358→981B, instrukce3192→4555B, schéma1181→2548B; tah1→1.
Skutečné tokeny, cena, kvalita odpovědí živého modelu a fyzický iPhone nejsou ověřené.
Další: samostatně schválené p+n etapy3+4, registrovaný upgrade hodinové kopie,
vědomé zapnutí a omezený test. Placený pilot vyžaduje konkrétní rozsah/rozpočet.
Míla následně výslovně zadal p+n všech dokončených commitů včetně Datových a úklid repa. Servisní upgrade ani aktivace doplňku tím nejsou provedené.
Samostatný e-mailový TVBCP není dohodnutý; existující Cockpit TVBCP kryje své UI/workflow.
Report reports/email_followups_assessment_20261112.md, důkazy mimo Git
v data/private/email_followups_step4_20261112/.


## Jeden přijatý pokus, stejné modelové rozhraní

Intake transakce uloží nový item, vazbu a jediný volitelný followup_attempt
před modelem/kurzorem. Kontext obsahuje jen jednu aktivní záležitost: ID,
generaci, uživatelský cíl/krok/termín a jejich zmrazený základ. Neobsahuje druhou
kopii mailu ani celou historii, má limit16KiB. Současné nové EML/text/HTML se
předává původním úplným způsobem. Výchozí vypnutý monitor kontext nepřidává.

CodexEmailProposer využívá jednu původní start_thread/send_text dvojici,
stávající model/effort a silný receipt.delivered. Volitelný followup_candidate
je oddělený od EmailProposal. Existuje původní schema, kalendářové, followup
nebo společné; všechny mají required/additionalProperties kontrakt. Kalendář
a hlídání nevyvolají dva tahy. Starý EmailProposal/koncepty zůstávají čitelné.

Výsledek je přijatý pouze pro původní attempt_id/input_digest/source_digest.
Porovnává se aktuální cache identity, generace, poslední relevantní zpráva,
uživatelský základ a povolení doplňku. Technický monitor_check otisk cíle
nemění; ruční změna včetně změny zpět ano. Stará generace nebo zdrojový drift
ponechá pouze stálý stale doklad u původního itemu. Chyba/nejistota či chybějící
volitelný výsledek neplánují retry; neplatný kandidát zachová platný původní
mailový návrh. Neprokazuje se obsah úkonů mimo sledované zdroje.

## Citace a skutečný význam návrhu

Pydantic kandidát dovoluje next_step/review_completion/manual_required/no_change,
jen přesný followup_id a vymezená pole. Nejvýše3 citace po400 znacích,
nejvýše8 nejistot po500 znacích. Citace musí souhlasit s body/subject/HTML
po normalizaci bílých znaků a mezery před interpunkcí. Neznámý zdroj,
vymyšlená citace, cizí věc či další operační pole znamenají invalid bez ztráty
EmailProposal. Text se renderuje přes textContent, nikoli HTML.

Doložení krátké citace není strojový důkaz splnění celého cíle. Interpretace
modelu zůstává označeným návrhem. Částečná odpověď, 'ozvu se', příloha,
webové podání a vložená instrukce mají syntetické bezpečnostní kontrakty;
skutečnou kvalitu inference dosud placený pilot nedoložil. Metadata přílohy
nejsou jejím přečteným obsahem. Podnět review_completion sám neuzavírá věc.

## Ruční rozhodnutí

Stejný validovaný endpoint POST followups, přesný operation_id a CAS.
Převzetí doloženého návrhu mění pouze next_step/waiting_on. Lze jej předem
upravit v původním editoru nebo odmítnout; cíl/check_at/lifecycle se nepřepisují.
Vyřízeno je původní zvláštní uživatelské přepnutí. Neaktuální návrh nelze převzít.

resolve_binding kontroluje konkrétní příchozí item, původní scope/digest,
aktivní generaci a dosud otevřenou review vazbu. Přijme/odmítne ji bez modelu.
Přijetí nemůže přiřadit zprávu, která už vlastní jinou záležitost. Ostatní aktivní
nejisté vazby stejné zprávy atomicky dostanou assigned_elsewhere; neproběhne merge
ani znovuotevření. Výslovně přijatý jednoznačný Message-ID může rozšířit známé
vlákno a schválené účastníky; nejednoznačné ID zůstává jen jednotlivou lidskou vazbou.
Zpráva přiřazená až po posouzení dostane manual_review, nikoli druhý modelový pokus.

Trvalá doménová účtenka přežije obecnou cache. Dvojklik/ztracená odpověď/reload
ověřují stejnou operaci; zápis jiné revize nebo stejné ID s jiným rozhodnutím
se odmítne. Atomické selhání nepřijme půlku rozhodnutí nad dvěma věcmi.

## Ověření a měření

587 finálních cílených PASS /34,988s: doména, original reply/calendar/visibility,
service/scheduler, registr, skutečné HTTP/CSRF a Node UI. Nové kontrakty:
jediný tah/strict schema/plný konec velkého mailu, špatné citace a cizí otisky,
stale source/basis/generation, technický check během modelu, vypnutí během
modelu, žádné retry, explicitní lidské rozhodnutí a zachovaná ruční pole.
Statická brána PASS; Finální plná brána PASS:3709 testů /538,314s,31 SKIP.

Skutečný vlastní headless Edge + dočasný HTTP backend:390×844 náhled návrhu,
editor a rozměry tlačítek;1280×1000 převzetí dalšího kroku a ruční přiřazení.
Oba průchody PASS, posts=2 a žádné nové fake modelové posouzení při UI akcích.
Mobilní tlačítka byla nejprve vizuálně příliš úzká, následná cílená oprava
scopovaného CSS a nová rozměrová kontrola PASS. Finální screenshoty prohlédnuté.
Nejde o fyzický iPhone, živou službu ani skutečný placený model. Browser má
vlastní izolovaný profil; po zkoušce byly vlastní testovací procesy ukončené.

Reprodukovatelné syntetické měření: payload358→981 UTF8B, instrukce3192→4555B,
schéma1181→2548B, turn_count1→1. Skutečné tokeny/cena nezměřené; mock usage
nejsou účetní data. Záznam nese actual_cost_measured=false. Případný skutečný
srovnávací pilot musí mít konkrétní případy a rozpočet, žádný nebyl spuštěn.

## Vydání, služba a otevřené kroky

Nové čtečky/heartbeat/readiness rozumějí followup_assessment_version1. Nevznikl
nový ServiceSettings klíč, role ani aktivační setter. Monitor defaultoff;
aktivní původní hodinová kopie7f47a41f se v tomto kroku nemění. Placený živý
pilot, registrovaný servisní upgrade a vědomé zapnutí mají vlastní souhlas. Míla následně výslovně zadal společné p+n všech hotových commitů a úklid repa.
Další krok je společné p+n lokálních etap3+4 a samostatná řízená servisní/přejímací
sekvence. Samostatný e-mailový TVBCP je dokumentačně nedohodnutý; existující
Cockpit TVBCP kryje své UI/workflow, nenahrazuje celý tento proud. Citlivý obsah
z reálné pošty se do zprávy ani Gitu nekopíruje. Důkazy/logy/screenshoty:
`data/private/email_followups_step4_20261112/`, mimo Git.


## Kanonická validace převzatého kroku

Závěrečná kontrola odhalila možnost předat next_step s řídicím znakem, který
původní doména nepovoluje. Dvě regrese před opravou FAIL. Kandidát i přijetí
nyní používají původní _text validátor; neplatný výstup je invalid, původní
EmailProposal i ruční stav zůstávají čitelné. Finální cílená sada587 PASS /34,988s
a statická brána PASS. Obě překonané plné sady (full_gate.log a full_gate_final.log)
byly záměrně ukončené exit143; nejsou dokladem úspěchu. Finální full_gate_complete.log
zahrnuje také níže uvedenou opravu obnovy. Browser/asset kontrakt a měření
vstupních bytes se opravami nezměnily.

## Pád po přijetí pokusu

Simulovaný pád procesu po trvalé rezervaci a před výsledkem odhalil neuzavřený
stav reserved (regrese před opravou FAIL). Obnova původního analyzing nyní
atomicky uloží analysis_interrupted i neověřený followup pokus. Nevytváří nový
modelový tah; původní běžné rozhodnutí zůstává dohledatelné. Finální cílená sada
587 PASS /34,988s, statická brána PASS.
