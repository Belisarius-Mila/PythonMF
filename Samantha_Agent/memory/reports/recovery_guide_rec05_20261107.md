# REC-05 — trvalý plánovač a dohled, zatím neaktivní

2026-11-07, Data worktree, proud `project-samantha-infrastructure`.
Míla schválil pátou vývojovou etapu. Plánovač ověřen se syntetickými
callbacky a skutečným sandboxovým writerem z REC-04; žádný placený model,
skutečný iCloud zápis, instalace LaunchAgentu ani restart služby.

## Výsledek

`WeeklyScheduler` v `app/recovery_guide_scheduler.py` má trvalé soukromé
účtenky pro ISO týdny, společný zámek a oddělené fáze analýzy, přijetí
a doručení. Registrované CLI náhledy/stav zpřístupňují plán a metadata.
LaunchAgent má absolutní cesty, minimální PATH a umask 077; pouze se vypisuje.

Aktivace produkce není součástí REC-05. Knihovní plánovač má pouze explicitní
sandbox režim v izolovaném podadresáři vlastní .venv nebo systémového temp.
Jeho callbacky jsou důvěryhodný neplacený simulátor, nikoli modelová oprávnění.
Předání živého backendu jim nebylo povolené. Veřejné CLI `run` a `tick`
nadále vrací activation_required s nulou modelových volání a zápisů.

## Týden, hodiny a výpadek Macu

- Neděle 09:00 Europe/Prague je stále **návrh**, nikoli schválený termín.
  Výchozí policy má enabled/schedule_approved/budget_approved false a nulové
  rozpočty. Neexistuje skrytá aktivní konfigurace ani náhradní model.
- Ruční i časované spuštění sdílí přesné ID `recovery-YYYY-Www`. Není force
  parametr, který by obnovil nový placený tah již zpracovaného týdne.
- Po odstávce se vybírá jeden poslední splatný týden, nikdy seznam všech
  minulých týdnů. Před hranicí schválené aktivace se zpětně nespouští nic.
- Při návratu hodin zpět se starší dosud nespouštěný slot nepřidá za novější.
  ISO přelom roku i Praha DST jsou otestované. Opakovaná podzimní hodina má
  jeden slot; neexistující jarní hodina se posune na první odpovídající okamžik
  po mezeře. Navržená devátá hodina takovou nejednoznačnost vůbec nemá.
- Syntetický pád procesu neztratí identitu týdne. Po návratu nejdřív přijde
  rozpracovaná úloha, až dalším tickem nejnovější splatný týden.

## Přechody a bezpečnost před modelem

| Stav | Další krok |
| --- | --- |
| nesplněné preconditions | čekat před analýzou, žádný model |
| analysis_in_flight před callbackem | trvalý marker a rezervace před možným odesláním |
| nejasný/chybný výsledek analýzy | attention, žádný další model ani příští týden |
| awaiting_acceptance | čekat na již skutečně přijatou REC-04 účtenku |
| delivery_ready / delivery_in_flight | ověřit přijetí a dokončit přesně tytéž bajty |
| pending_icloud | zkontrolovat/dokončit cloud bez nové analýzy |
| completed | dvě schválené kopie a potvrzený upload podle writeru |
| completed_no_change | úplná revize + čerstvé závěrečné ověření obou dosavadních kopií |

Před novou analýzou vyžaduje řadič důvěryhodné potvrzení dostupnosti Macu,
uživatelské session, sítě, Codex/iCloud přihlášení, nezměněné centrální role,
Standard režimu, kontextu a zdrojového rozsahu. Chybějící důkaz je false,
nikoli předpoklad dostupnosti. FileVault ani přihlášení se neobchází.

Plán obsahuje předem celý počet zdrojů/tahů a rezervaci nákladů. Limity na
jednotlivý běh a měsíc se kontrolují před callbackem; známá skutečná spotřeba
se zachová i při překročení limitu nebo neplatném návratovém payloadu.
Měsíc konzervativně účtuje vyšší z rezervace a známé spotřeby. Chybějící
telemetrie, neúplné pokrytí, jiný snapshot/model/role, nadlimitní tahy či čas
zastaví pokračování před doručením. To nejsou tvrdé fakturační ani rušící
limity běžícího transportu. Časový práh kontroluje dokončení analýzy;
jednotlivé síťové timeouty musí zajistit adapter.

Role se zde nevolí ani nepřepínají. Plánovač porovnává receipt s očekávaným
centrálním otiskem role a s požadovaným Sol/medium; `config/agent_roles.json`
zůstává jedinou autoritou výběru a v této etapě se neměnil. Živý katalog,
izolaci a skutečný Standard běh tato simulace nenahrazuje.

## Obnova bez opakování akce

Nejistou analýzu žádný další tick nezavolá znovu. `reconcile_analysis` umí
po explicitním potvrzení důvěryhodného operátora připojit **známou místní
účtenku stejné identity**, pokud se vejde do původního kontraktu. Neprovádí
nové generování, nesnižuje známou spotřebu/počet tahů a nepřijímá soukromé
prompty do plánovače. Neznámý výsledek nelze vydávat za hotový. Jiný případ
attention/poškození či změna policy zůstává servisním rozhodnutím; žádný
automatický reset nebo mazání historie není implementovaný.

`attach_publication` váže již přijatý REC-04 request/hash ke známému kandidátu.
Model tím nemůže sám potvrdit přijetí. Přenos kontroluje shodu request ID,
kandidáta, snapshotu, přijetí a sandbox scope před i po volání writeru.
Uploaded/pending metadata bez důkazu obou kandidátních kopií nejsou úspěch.
Pending cloud může pokračovat bez Codex auth, protože nevzniká modelový tah;
vyžaduje však Mac/session/síť/iCloud a stále platnou policy.

Pokud obsah zůstal stejný, modelové čtení celé dokumentace se nepřeskakuje.
Před i **po** něm musí být ověřeny aktuální kopie a snapshot. Pouze tak lze
skončit bez změny. Není-li kopie dosud zavedená, shodný text není důvod
předstírat dokončenou migraci. Datum TXT se při revizi samo neposouvá.

## Registrované náhledy a dohled

Z této pracovní kopie, bez placeného tahu:

```text
.venv/bin/python scripts/recovery_guide.py schedule-preview
.venv/bin/python scripts/recovery_guide.py status
.venv/bin/python scripts/recovery_guide_launchd.py
.venv/bin/python scripts/recovery_guide_launchd.py --check-environment
```

Workflow ID: `recovery_guide_schedule_preview`, `recovery_guide_status`,
`recovery_guide_launchd_preview`, `recovery_guide_environment_preview`.
Dosavadní inventory/preflight/runtime a blokovaný run zůstávají registrované.
Žádný z těchto vstupů neinstaluje ani neaktivuje plánovač. Plist je pouze
stdout, nepřesměrovávat jej do LaunchAgents před REC-06 přejímkou.

`status` přidává poslední plánovačový běh, zdrojové pokrytí, kandidátní otisk,
spotřebu, očekávanou roli, pending úlohy a stav kopií. Čte místní účtenky;
nejde o nový živý audit. Návratová JSON účtenka pracovního proudu zajišťuje
dohled bez zásahu do produkčního Cockpitu. Žádné externí zprávy/e-maily.
Čekání před vznikem modelové úlohy je popsáno ve výsledku ticku, nikoli jako
fiktivní dokončený běh v historii. Historie úloh se nemaže.

Náklady a modelové tahy v sandboxu jsou výslovně simulované. `model_calls:0`
znamená, že tato implementace/test nevolá živý model; `reported_model_turns`
je testovaný údaj kontrolního kontraktu. Příklad v REC-05 JSON není skutečná
cena budoucí revize ani schválení testovacích limitů pro produkci.

## LaunchAgent a prostředí

Připravený plist má absolutní venv Python/script/CWD/logy, minimální PATH,
umask 077, StartInterval 900 a RunAtLoad. Neobsahuje KeepAlive, který by
nečekaně opakoval drahou práci; zámek a účtenky platí i při souběhu ručního
spuštění. Přihlášení a dostupný Mac zůstávají nutné. Nevzniká cloudový host.

Zkouška `--check-environment` spustila jen čtecí CLI status pod navrženým
minimálním prostředím. Ověřila bootstrap/importy, nikoli skutečný launchd
GUI/auth kontext. Výstup výslovně uvádí launchd_session_verified a
authentication_verified false, service_installed false. Skutečnou session,
přihlášení, mount/síť a jeden plánovaný slot musí doložit až povolená aktivace.
E-mailový agent ani jiný LaunchAgent nebyl upravený/restartovaný.

## Ověření

42 nových REC-05 scénářů; cílená sada 194/194 OK. Finální plná projektová brána nad posledním kódem: 2 543 testů OK, 5 skipped. Čtecí CLI bootstrap pod minimálním PATH OK; skutečná launchd/auth session a produkční model zůstávají neověřené.

Samostatná přejímka plánovače:

```text
OPENAI_AGENTS_DISABLE_TRACING=1 .venv/bin/python -m unittest tests.test_recovery_guide_scheduler
```

Testy zahrnují restart, ruční/timer souběh, hodiny/DST/ISO rok, jednu nejnovější
doháněnou úlohu, limity, změnu role/policy, nedostupné přihlášení, neúplné
pokrytí, nejasné analýzy i přenos, ruční připojení známé účtenky, immutable
writer a návratové metadata. E2E test použil skutečné dočasné soubory a
REC-04 writer s falešným iCloud auditem. Po čekání na cloud se byte kopie
nezapsaly znovu a analytický callback neběžel podruhé.

## Přesný další krok: REC-06

Will převezme lokální balíček do aktuálního main při zachování jeho rolí/práce.
Před aktivací nutno uzavřít:

1. Skutečný REC-02 runtime/Standard/tokenizer či přijatý odhad+kalibraci,
   konkrétní cenu a jeden zvlášť schválený čtecí pilot. Dosavadní provozní
   zjištění jsou pouze datovaný REC-02 snapshot, nikoli nové ověření služby.
2. Úplný schválený korpus/aplikace, bezpečné registrované doklady, přijatý
   skutečný návrh TXT a pravidla jednorázově schválené automatické údržby.
   Budoucí týdenní běh v tomto rozsahu nemá čekat na nový ruční souhlas.
3. Produkční adapter modelu, auditů a writeru s autentizovanou úzkou autoritou.
   Musí převzít **stejný scheduler slot/request**, ne odvozovat druhý týden
   jinými defaulty v modelovém pilotu. Simulované callbacky se nesmějí vydat
   za živou integraci; stávající `run`/`tick` ji záměrně ještě nespouštějí.
4. Přesné dva provozní cíle, reálnou migraci, skutečný Foundation upload
   a otevření TXT na iPhonu. Potom samostatně povolený release/instalaci,
   schválený den/čas/rozpočet a zkoušku jednoho slotu i bezpečného catch-up.


### Soubory této etapy

Nové: `app/recovery_guide_scheduler.py`, `tests/test_recovery_guide_scheduler.py`,
tento report a redigovaný syntetický `recovery_guide_rec05_example_20261107.json`.
Upravené: `app/recovery_guide_publication.py` (metadata již přijatého snapshotu),
`app/workflows/commands.py`, `scripts/recovery_guide.py`, `scripts/recovery_guide_launchd.py`,
`scripts/cockpit_quality_gate.py`, `memory/ACTIVE_PROJECTS.md`, `memory/MEMORY_INDEX.md`,
`memory/LESSONS_LEARNED.md`, `memory/projects/samantha_external_backup.md`,
`memory/technical/recovery_guide_maintainer.md` a kanonický handoff/TVBCP
`project-samantha-infrastructure.md`. Celkem 16 souborů.
