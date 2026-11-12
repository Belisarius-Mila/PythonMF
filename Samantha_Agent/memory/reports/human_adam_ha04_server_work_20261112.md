# HA-04 — serverově vlastněná dlouhá práce a obnova

Datum: 2026-11-12 12:07 CET
Kanonický proud: layer-human-adam-development.
Výchozí vydaný main: 5e3ae99ff2816510437159b084bf8eccc4948fa2.
Původní plán: Human_Adam_hluboka_analyza_a_plan_monitoringu_2026-11-11.txt, HA-04/7.2/7.3.
Míla schválil vývoj a potom výslovně rovnou p+n. Vykonavatel vývoje Adam.

## HA-04 — serverově vlastněná práce, 2026-11-12 12:07 CET

Lokálně implementované trvalé přijetí jedné modelové práce, operation_id,
serverový worker a čtecí snímek/omezená historie s cursorem. Staré /send čeká
nad stejnou serverovou prací; nový /work/start vrací202. GET /work dohledává
práci podle scope a operation_id/client_message_id, včetně nového server_generation.

Reload nebo ztracená HTTP odpověď nevytvářejí další turn/start. Worker používá
původní profilový lock a cross-process lease; nemění model/sandbox/oprávnění.
Trvalá dispatch bariéra předchází RPC, scope vlákna se znovu ověří před send.
Po restartu se nic automaticky nespouští. Výslovný recover ověří pouze původní
cached session/completion doklad, jinak vrátí neověřenost. Child job ID je pevné;
modelová odpověď může být potvrzená, zatímco checkpoint ještě běží či je neověřený.

Metadata observer využívá HA-03, před přesným ACK bufferuje jen bezpečné typy
událostí, nikdy raw text/nástrojové argumenty/reasoning.128 událostí na práci,
64 položek přehledu,64 metadat před ACK, nejvýše8 workerů a2 staré RAM odpovědi.
Staré identitní soubory zůstávají jako idempotentní doklady. Cursor mezera
vyžaduje jednorázový resync; terminální stav ani cizí generace se nepřepisují.

325 cílených testů PASS, statická brána PASS. Ověřen skutečný pád vlastního
syntetického procesu po dispatch a HTTP odpojení/dva klienti, bez druhého
provedení. Finální plná lokální brána PASS: 3635 testů / 573,186 s, 31 SKIP; finální zdroj včetně child-job ochrany a oprav registrů.
Finální zpevnění přesné child-job vazby je součástí325 cílených kontrol;
povinná publikační plná brána znovu ověří celý přesný finální commit.
Žádný placený vývojový pilot, živý modelový HA-04 test, skutečná mutace
uživatelského workspace, změna rolí, instalace služby či nový daemon.

Míla schválil i bezprostřední Terra p+n. Request `human-adam-ha04-20261112-v1`,
job `832a2e708b8016039f5547df141d8fe4`; autorita výsledku v původní účtence a
`data/private/ha04_20261112/release_receipt.json`. Tento snapshot je před vydáním.
HA-05 zůstává živá karta/UI kanál; současný klient zachovává starý čekající
protokol a nepřidává ukládání rozepsaných draftů. Steer/interrupt/usage a
rozšířené adaptéry dalších jobů zůstávají HA-06 ažHA-09. Fyzická Mac/iPhone
přejímka a skutečný živý reconnect dlouhé modelové práce zůstávají otevřené.
Report `reports/human_adam_ha04_server_work_20261112.md`.

## Kontrakt a autority

WorkStore/Controller vlastní private metadata přijetí; původní SessionHub/Client
zůstávají autoritou modelového doručení. Stávající completion job je autoritou
checkpointu. Žádná automatická repríza, další role nebo obecný agentní proces.
Worker drží původní profilový zámek, jednorázový write_intent a cross-process
lease. Mechanická extrakce původního send těla byla ověřena AST proti baseline;
postup modelového vstupu, bezpečnostních kontrol a dokončování se nemění.

operation_id je deterministické z workstream+client_message_id. Otisk textu,
write_intent a klientských metadat odmítne jiné zadání pod stejnou identitou.
Serverový code stamp není nová uživatelská identita při pozdějším readbacku.
Nezápis úložiště nebo nemožnost získat vlastnictví nespustí model. Accepted
před durable dispatch bariérou lze při obnově pod volnou lease prokázat jako
not_dispatched; za bariérou bez důkazu zůstává unverified. Nikdy se z toho
samo nevytvoří nový send. File lease není zabíjení procesu a nezavádí službu.

Jeden wire reader z HA-03 dál směruje RPC a notifikace. Observer má vlastní
bounded subscription, bufferuje jen malé whitelistované druhy do přesného
ACK a filtruje cizí turn/thread/generaci. Nezapisuje text plánu/odpovědi,
reasoning, argumenty nástroje ani cesty. Subscriber se při konci bounded
čekáním pokusí dočíst terminální metadata; nedočtení/overflow znamená gap.
Poslední potvrzený výsledek zůstává u původního vlastníka, metadata observer
nemůže smazat doručení nebo vyvolat druhý RPC. Terminální journal je absorbující.

Dokončená modelová odpověď a navazující kontrola mají oddělený stav. Výpadek
completion readeru ponechá delivery=confirmed a celek unverified. Přesný
child-job odkaz se po navázání nepřesměruje na novější/cizí job stejného projektu.
Worker sleduje jen již vytvořený původní job, nepouští nový. Obecné adaptéry
a celý přehled dalších druhů práce patří HA-09.

## Retence a soukromí

Privátní per-operation záznam drží přijatý text, nikoli rozepsaný browserový
draft. Po terminálním potvrzeném doručení jej odstraní z duplicitní cache; canonical chat
jeho vlastní historii zachová. Přehled má64 identit; staré terminalní záznamy
se kompaktně uchovají jako doklady identity/otisku, bez původního textu.
Neukončené identity se nevyřazují, plný přehled neověřených prací odmítne
nové přijetí.128 událostí/operaci; prázdný/chybějící cursor vrací snímek,
starý/budoucí cursor vyžaduje resync. Gap marker vyžaduje resync jen klientům
před jeho cursorem. Nejvýše8 běžících workerů a2 staré odpovědi v RAM.
Čtecí API nepřenáší user text, odpověď, soukromý vstup, root nebo raw chybu.

Restart nové instance nic nedispatchuje. Staré aktivní záznamy mají neověřenou
projekci a novou server_generation. Výslovný recover využívá pouze původní
cached canonical session a přesnou completion identitu; neprovádí App Server
resend/reconnect, nevyrábí pozitivní důkaz z absence položky a nemění originální
receipt. Původní delivery_unknown/ruční obnovovací brány zůstávají zachované.

## Ověření

325 cílených testů PASS v targeted_final.log. Obsahují původní ProfileManager,
Hub, službu, dispatcher, client, HTTP ochrany i nové kontrakty. Skutečný vlastní
syntetický Python proces je ukončen po jediné simulované modelové dispatch;
nový Controller obnoví stejné ID neověřeně a počet volání zůstane1. HTTP legacy
spojení se během práce zavře; server pokračuje a druhý klient čte stejnou práci.
Testované dvě stránky, dvojklik, chybný fingerprint/oprávnění/project/thread,
CSRF/foreign-origin, storage/start/shutdown, retence, cursor/gap, ztracené ACK
pozorování, bezpečné payloady, potvrzené doručení při výpadku telemetrie a
pozdější cizí child job. Žádná fixture nepoužívá skutečný model.

Finální plná lokální brána PASS: 3635 testů / 573,186 s, 31 SKIP; finální zdroj včetně child-job ochrany a oprav registrů.
První plný běh: 3634 testů / 558,103 s, 2 selhání a 31 skip. Opraveno přesné
pořadí nových cest v POST registru a očekávaný počet rizikových schopností
auditního testu (36 včetně nového start). Následně 270 testů registrů a Cockpitu
PASS / 3,248 s. Finální plná sada obsahuje i poslední ochranu přesné child-job
identity; povinná publikační brána znovu ověří celý finální commit před pushem.
Statická brána, py_compile a git diff --check PASS; po finálním doplnění se
statická brána znovu prošla před commitem. Soukromé fixture/logy mimo Git:
`data/private/ha04_20261112/`.

Primární protokolová dokumentace byla načtena přes OpenAI Docs:
[App Server lifecycle](https://learn.chatgpt.com/docs/app-server#lifecycle-overview).
Jde o referenci protokolu, nikoli důkaz živého HA-04 modelového pilotu.

## Vydání a přejímka

Jedno registrované submit_release(wait=True), request `human-adam-ha04-20261112-v1`,
job `832a2e708b8016039f5547df141d8fe4`; přesný schválený SHA až po lokálním commitu.
Program sám zmrazí origin/cíl/model podle centrální role Terra. Root nedoplňuje
ručně další model ani pomocného agenta. Konečná autorita:
`data/private/ha04_20261112/release_receipt.json` a původní privátní job.
Při timeoutu/nejistotě se dohledává totéž ID, neprovádí se nové předání.

UI/livecard/automatický browserový čtecí kanál je HA-05. Současný klient
zůstává na kompatibilním čekajícím send. Tento krok nedokládá živý reconnect
rozpracovaného placeného modelu, iPhone ergonomii ani úplnou práci dalších
HA-06/07/08/09. Nevznikl placený vývojový pilot ani oprávnění jej opakovat.
Vlastní hodinová poštovní kopie, modelové role a jiné chráněné služby se
neupgradují. Po p+n následuje obvyklá jednorázová kontrola původní účtenky,
GitHubu, živého kódu a registrace lehkého čtecího endpointu bez skutečného send.
