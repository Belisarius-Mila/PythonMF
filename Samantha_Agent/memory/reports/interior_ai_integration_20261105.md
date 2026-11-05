# Ateliér — AI rozhovor a řízené obrazové varianty

Datum: 2026-11-05. Autor: Will. Proud: project-neuberk-kacenka.
Výchozí vydání: b9b59c7d (MPO oprava; CI 42083732254 success).

## Požadavek a aktuální výsledek

Míla po praktickém vyzkoušení zadal „Zapoj teď AI“. Je připravená lokální
implementace skutečného rozhovoru nad podklady a vytvoření jedné obrazové
varianty. Produkční modelová role není zapnutá; žádné skutečné fotografie
se při vývoji neposlaly modelu a neproběhl žádný placený pilot. Nebyl proveden
push, nasazení, změna e-mailové služby, instalace závislostí ani změna rolí.

## Uživatelský tok

- Pravý panel Architekt obsahuje otázku, volbu rozhovoru a samostatné
  vytvoření AI návrhu. Počet předávaných podkladů je viditelný. Když nejsou
  vybrané, lze explicitně použít nahrané podklady místnosti (nejvýše šest).
- Rozpracované zadání se před požadavkem uloží s kontrolou revize.
  Snapshot obsahuje vybrané náhledy, kreslené značky na pracovním obrázku,
  pevné prvky, dosavadní dokončený rozhovor a poznámky této varianty.
  Nadlimitní kontext se odmítne před placeným tahem; nikdy se tiše nekrátí.
- AI může popsat podklady, doporučit změny a ptát se. Obrazový požadavek
  vytvoří skutečnou ai_proposal variantu, s rodičem a původními referencemi.
  V galerii je odlišena od lidského zadání. Rozměry a stavební proveditelnost
  se nevydávají za ověřené z fotografie.
- Poznámky zůstávají samostatné a nejsou vydávané za odpovědi AI.

## Technická a bezpečnostní hranice

- Stejný Unix WebSocket App Server, bez migrace na SDK. Nový volitelný
  argument local_image_paths pouze doplní explicitní localImage vstupy.
  Původní textové volání, handshake, efektivní nastavení, final-answer
  a delivery_unknown kontrakt zůstávají ověřované původními testy.
- Každý požadavek je nejprve zapsaný do transakčního repository, má stabilní
  identitu/otisk, zmrazené nastavení modelu a neměnné obrazové snapshoty.
  Dvojklik či opakování HTTP se stejnou identitou nespustí další modelový tah.
  Novější rozepsané změny ani jiná místnost výsledek nepřevezmou.
- Pro model se předávají jen ověřené room-owned metadata-free náhledy.
  Žádná cesta z prohlížeče; omezený readOnly sandbox jen pro snapshot.
  MCP konektory, web, shell, view_image, paměti a delegace jsou vypnuté.
  Native image_generation je vypnuté v chat režimu a zapnuté jen pro obrazový
  požadavek. Podpora těchto přepínačů byla přečtena ze skutečného serveru.
- Výsledek se zachová v soukromém journalu před publikací varianty. Při
  chybě ukládání se může dokončit místně; při nejistém doručení se čte jen
  původní vlákno. Obnova nikdy nevolá thread/start, thread/resume nebo turn/start.
- Při chybě či restartu není automatický placený retry. Neověřený výsledek
  blokuje další požadavek v témže kontextu. Nulový nebo vícenásobný obrazový
  výstup se nevydává za jednu úspěšnou AI variantu.
- Standardní GET stavu nevrací interní journal, snapshoty, thread IDs ani
  syrové účtenky. Samostatné AI status API vrací jen příslušný rozhovor/stav.

## Ověření

- 145 cílených Python testů PASS: klientský multimodální kontrakt, izolace
  podkladů, změna zadání, idempotence, restart, jednorázový worker, skutečná
  varianta z obrazové fixture, zachování originálů a obnovitelné uložení.
- Nové Node DOM scénáře: dvojklik, dokončení bez přepsání rozepsaného textu,
  opožděná odpověď jiné místnosti, neověřené HTTP a kontrola původního
  požadavku bez dalšího placeného tahu. Zachovaných 8 původních Node scénářů.
- HTTP cesty, capability registry, přesný frontendový snapshot a syntaxe
  mají cílené kontroly. GitHub workflow nově zahrnuje backend a testy Ateliéru
  v push i pull_request filtrech; příští čistě backendová oprava už nevynechá CI.
- První plný běh provedl 2559 testů: jediná chyba byl zastaralý očekávaný
  počet rizikových schopností v test_capability_audit (29 → 31 po registraci AI).
  Aktualizovaný audit má 3 testy PASS. Závěrečný plný běh: 2559 testů,
  0 chyb, 31 přeskočených; testy 388,844 s, kanonická brána OK.
- Logy: interior_ai_client_contract_20261105.log, interior_ai_domain_20261105.log,
  interior_ai_frontend_20261105.log, interior_ai_http_20261105.log,
  interior_ai_verification_20261105.log, interior_ai_audit_verification_20261105.log,
  interior_ai_full_gate_20261105.log (první běh), interior_ai_full_gate_final_20261105.log.

## Živý pilot a nutná kompatibilita

Asynchronně je položená volba Terra/high: právě jeden rozbor vybraných
soukromých podkladů a volitelně jeden obrazový návrh. Odpověď zatím není.
Standard sazby ověřené 5. 11.: 25 vstup / 1,25 cached / 125 výstup kreditů
za milion tokenů. Nativní generování používá GPT-Image-2 a účtuje se navíc;
nebyl slíben pevný kreditový strop jednoho požadavku. Platí pouze explicitní
počet pilotních požadavků a žádné automatické opakování.

Centrální role interior_architect se nepřidává před skutečným přijatým pilotem
a kompatibilním živým runtime. Zkušební role existuje pouze v cenově schváleném
soukromém pilotním prostoru. Výsledek přitom může normální ověřenou cestou
patřit přímo do vybraného uživatelského projektu; produkční role se tím nezapíná.

**Potvrzený integrační blokátor:** hodinová e-mailová kopie ac9f3bed obsahuje
starší KNOWN_ROLES, které interior_architect neznají. Přidání role do sdíleného
JSON by zablokovalo i její čtení continuous_email. Čtecí AST audit vlastněné
kopie to ověřuje bez importu nebo spuštění jejího kódu. Aktivace se proto
zastaví, dokud není kompatibilní také tato samostatná služba.

Připravený postup po konkrétním souhlasu:

1. Schválený skutečný pilot přes probe_candidate, kontrola výsledku hlavním
   Adamem a accept_probe; opakovaná identita pilot nikdy nezopakuje.
2. Registrované Terra p+n nového kompatibilního Cockpitu, role zatím neaktivní.
3. Registrované pause/prepare/upgrade vlastní e-mailové kopie z čistého vydaného
   main se zachováním stavů a předchozího runtime. Upgrade vyžaduje přesnou
   globální potvrzovací větu podle service_control.py a global_safety_brake.md.
4. activation_plan ověří přijatý pilot, nezměněný zdroj, čistý main, kompatibilní
   živé API i skutečné další konzumenty role. activate změní jen centrální roli.
5. Checkpoint / odpovídající ověření a schválené závěrečné p+n politiky. Model
   se zpřístupní až po startu procesu s odpovídající politikou, nikoli uprostřed
   běžící relace po pouhém přepsání JSON.

K dnešku není oprávnění k tomuto novému p+n ani k systémovému upgrade doložené.
Nevznikl nový TVBCP; jeho dříve otevřená vazba zůstává viditelná v handoffu.
Fyzická přejímka skutečného AI rozhovoru a obrazového návrhu zůstává otevřená.

Oficiální podklady: [App Server](https://learn.chatgpt.com/docs/app-server),
[generování obrázků](https://learn.chatgpt.com/docs/image-generation),
[ceny a spotřeba](https://learn.chatgpt.com/docs/pricing).
