# REC: sjednocený formát zapojený do týdenního běhu

2026-11-08 15:35 CET; Data, vlastní worktree a větev data/parallel-20261104.
Míla schválil integraci do běhu. Neaktivoval se plánovač, role ani model;
žádný placený tah, push, nasazení nebo změna provozních dat.

## Výsledek

RecoveryRuntime nyní propojuje WeeklyScheduler → maintainer.run → obsahovou
přejímku PublicationStore → existující dvoucílový writer. Produkční režimy
mají explicitní privátní aktivační autoritu; bez ní jsou dál zablokované.
CLI run/tick jsou na tuto cestu skutečně připojené. Status nic nevytváří.

Další týden čte poslední přijatý doručený návod a kontroluje obě SHA kopií.
Bootstrap je povolený pouze prvnímu běhu a jen podle přijatého otisku.
Neplatný či nejistý výsledek blokuje i další týdny; nikdy nevytvoří náhradní
modelovou akci. Při pending iCloud nebo pádu mezi kopiemi pokračuje stejný
přijatý request/candidate/approval bez modelu. Ruční změna kopií se nezahodí
návratem ke starému originálu. Změna aktivační konfigurace zastaví pending job.

Nový formát je povinný i v produkční přejímce; původní aplikační checklist,
macOS, čerstvost faktů a konkrétní trusted confirmation se neobcházejí.
Dokončení přenosu není automatická obsahová přejímka ani fyzická kontrola iPhonu.
Syntetická zkouška odhalila a opravila nesprávné označení nově přijaté verze
za superseded za předchozím dokončeným přenosem. Průchod je dovolen jen při
shodě obou aktuálních kopií s připnutými baselines; staré formáty se nemění.

## Transport a účtenky

Běhové spojení používá existující sdílený socket a oddělená ephemeral
read-only vlákna bez nástrojů. Guard předá explicitní Standard na každý turn,
kontroluje model/effort/role i změnu zdrojů těsně před placeným odesláním.
Trvalý unknown marker je před wire; po výpadku zachová thread/turn a známou
telemetrii. Úplná raw odpověď se uloží před obsahovým přijetím. Výjimky se
nevypisují s potenciálně soukromým obsahem do veřejného statusu.

Tento týdenní kontrakt používá source/quote citace výchozího maintaineru.
Historické exact-index piloty a jejich raw zůstávají oddělené a uzavřené,
nejde o jejich retry ani fallback. Nové schema/obálka vyžadují nové neplacené
nacenění a samostatné přijetí skutečného běhu; starý placený souhlas se nepřenáší.
Přijímací limity nejsou tvrdý fakturační/output cap. Reference tokenizer není
přesné mapování modelu ani přesný úplný App Server prompt.

## Ověření

- 39 nových testů první běhové sady běhu/konfigurace/transportu a tři následné
  zkoušky registru a nezávislosti přenosu na App Serveru; celkem 42.
- 272 cílených testů před závěrečnou změnou registru PASS.
- Plná brána 2 863 testů OK (5 skipped). Po závěrečném doplnění oprávnění
  a oddělení delivery readiness následovala cílená regrese 161 testů OK;
  všechny nově změněné moduly i registry znovu ověřené. Statická brána a diff check OK.
- Produkční větev kódu (simulation=false), ale fake callback a všechny cesty
  v dočasných adresářích: dva týdny dokončené se shodnými kopiemi. Druhý
  source_original_sha256 == první candidate_sha256. Čtyři stub volání,
  nula placených modelových tahů; podrobné bezpečné agregace v přiloženém JSON.
- Samostatný syntetický RPC test přes stávající klient prokázal explicitní
  Standard, readonly/ephemeral, odmítnutí reuse vlákna a zachování unknown
  thread/turn po výpadku. Není to provider acceptance nového kontraktu.
- Pád mezi kopiemi, pending iCloud přes nový týden, restart a delivery unknown,
  změna vstupů/aktivace, neplatné přijetí i legacy fallback jsou pokryté.
- 48 původních JSON artefaktů starých jobů beze změny. Skutečná aktivační
  konfigurace ve worktree chybí; čtecí status vrací activation_required.

## Změněné soubory

Nové recovery_guide_runtime.py, recovery_guide_runtime_config.py,
recovery_guide_runtime_live.py a test_recovery_guide_runtime.py.
Nutné návaznosti: recovery_guide_maintainer.py, recovery_guide_quality.py,
recovery_guide_publication.py, recovery_guide_scheduler.py, recovery_guide.py,
cockpit_quality_gate.py a registr app/workflows/commands.py.
Projektové zápisy: tento report a JSON, recovery_guide_maintainer.md,
capability_routing_rules.md, samantha_external_backup.md, ACTIVE_PROJECTS.md,
MEMORY_INDEX.md, LESSONS_LEARNED.md a kanonický handoff/TVBCP infrastruktury.

## Další provozní krok

Po Willově převzetí není potřeba znovu psát propojení. Je nutné samostatně
přijmout aktuální čtenářský text/dossier a konkrétní aktivační podklady:
rozsah, časový plán, cenové meze, tokenizer s přijatou nejistotou, ověřený
kontext/verzi/protokol a kompatibilní centrální roli. Teprve schválená
privátní aktivace umožní run/tick; tento vývoj ji nevytváří ani nezapíná.
Přijetí konkrétního kandidáta jde přes prepare_acceptance/accept s bindingem
plus identitou jobu. Další tick přenáší stejné bajty. Skutečné provozní
kopie, upload, služba a iPhone vyžadují vlastní oprávnění a důkaz.
