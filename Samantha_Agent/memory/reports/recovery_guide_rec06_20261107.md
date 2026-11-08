# REC-06 — syntetická kalibrace prošla, přejímka celého návodu pokračuje

2026-11-07, Data, vlastní větev `data/parallel-20261104`.
REC-06 zůstává **rozpracovaná**. První zvlášť schválená živá syntetická
kalibrace dne 2026-11-07 v 16:18 CET **prošla**: jeden Sol/medium Standard
tah, 5 436 tokenů, odhad 0,3094 Standard kreditu. Skutečný čtecí pilot celého
návodu, doručení TXT a týdenní provoz tím nejsou ověřené. Aktuální důkaz je
v `recovery_guide_rec06_result_20261107.json`; následující přípravné podklady
popisují původní kartu před spuštěním.

## Čerstvé ověření

- Globální příkaz `codex --version`: **0.166.0**. Připojený App Server při
  initialize hlásí **0.163.0**. Jde o dva různé údaje; cesta k binárce
  běžícího procesu nebyla spolehlivě doložená.
- Kanonický socket je alias do spravovaného lokálního daemonu. Registrovaný
  čtecí `LocalAppServerProcessController.status()` potvrdil running/reachable,
  private_local_unix_socket a `owned_by_cockpit=false`. To není oprávnění
  převzít, obnovit či zastavit daemon. Starší ownership sidecar neodpovídá
  současnému listeneru; k rozhodování o službě se nepoužil.
- Modelový katalog připojeného serveru obsahuje přesný `gpt-6.1-sol`/medium.
  `account/read(refreshToken=false)` vrací spravovaný účet typu `chatgpt`.
  Do projektu se neukládá e-mail, plán, token ani celá konfigurace. Typ účtu
  nedokazuje jeho identitu ani budoucí platnost autentizace.
- Zděděná preference není Standard. Globální preference se neměnila.
  Oficiální dokumentace a statické schéma přesné verze **0.163.0** podporují
  `serviceTierForTurn="default"`: Standard pouze pro nově zahájený tah.
  Nejde o trvalý `serviceTier` ani o přepnutí již běžícího tahu.
- Oficiální npm balíček `@openai/codex@0.163.0` byl instalován **jen do
  vlastní `.venv/recovery_rec06_cli`**, s vlastní npm cache. Použil se pro
  verzi, features a generování schématu, nikoli ke spuštění App Serveru.
  Globální CLI, společná `.venv` a projektové závislosti jsou beze změny.
- Izolovaný `tiktoken 0.14.0` stále nezná mapování přesného modelu. Pevné
  instrukce (dvakrát), payload a schéma mají dohromady **500 referenčních
  tokenů `o200k_base`**. Není to přesný Sol tokenizer ani celé serverové
  rámování. Původní preflight celého korpusu zůstává blokovaný.

## Konkrétní karta prvního souhlasu

Přesný neměnný vstup, schéma a otisk jsou v přiloženém
`recovery_guide_rec06_calibration_20261107.json`; soukromá úplná karta a
účtenka patří pouze do `.venv/recovery_rec06_trial/` tohoto worktree.

| Položka | Navržený rozsah |
| --- | --- |
| Identita | `rec06-sol-standard-synthetic-01` |
| Model | `gpt-6.1-sol`, medium, žádná náhrada |
| Rychlost | `serviceTierForTurn: default`, pouze jeden nový tah |
| Počet tahů | právě jeden, bez opakování |
| Data | pět pevných syntetických záznamů, 514 UTF-8 bajtů payloadu |
| Kontrola | dokumentace vs historie/návrh, neověřený iPhone, zrušený hlas, datová prompt injection |
| Kontext | nové ephemeral vlákno, prázdný vlastní adresář, bez historie projektu |
| Oprávnění | read-only, networkAccess false, approval never |
| Předběžná rezerva | 12 000 vstupních + 4 000 výstupních tokenů = 1,6 Standard kreditu, bez předpokládané cache |
| Přijímací mez | nejvýše 2 Standard kredity, 12 000/4 000 tokenů a 90 s podle dokončené účtenky |
| Tvrdý fakturační strop | **není**; tokenové/časové meze jsou přijímací kontroly, transport má timeout čekání 90 s |
| Produkční účinek | žádné čtení skutečného návodu/korpusu, zápis TXT, aktivace role či plánovače |

Sazby Standard / 1M tokenů: vstup 50, cached vstup 2,5, výstup 250 kreditů.
Výstup zahrnuje reasoning; nepřičítá se podruhé. Spotřeba se vezme z nového
vlákna a přepočte se na **odhad** Standard kreditů, nikoli na fakturační
účtenku. Nejde o API dolarovou cenu. Skutečný účet může mít odlišné čerpání
podle předplatného. Při chybějící telemetrii se nehlásí nulová cena ani úspěch.

`prepare()` vytváří tuto kartu bez thread/start a turn/start. `run()` smí
obdržet její úplný `approval_digest` až po konkrétním Mílově souhlasu.
Samotná existence karty ani schválení vývoje tento souhlas nenahrazují.

Připravený approval digest: `d613768b5af370446ea4b5b336c9de5c5656379f8b38be9b899c31bae0a4329a`.
Karta vznikla 2026-11-07 14:52 CET čtecím preflightem v této vlastní kopii;
žádný thread/start ani turn/start nebyl proveden.

## Bezpečnost jednorázového vstupu

- Nový `app/recovery_guide_trial.py`; produkční klient, runtime, modelové
  role ani původní `AppServerReviewer` se neměnily. Nový pilot není skrytý
  fallback celé dokumentační revize a není připojený k run/tick.
- Před placeným odesláním se ověří otisk implementace/protokolu, přesný peer,
  model, typ účtu a identita aliasu/cílového socketu. Vrácený thread/start
  musí potvrdit správný model, cwd, approval never a readOnly bez sítě.
- Třicet konkrétních funkcí je vypnuto per-thread, včetně shellu, aplikací,
  pluginů, pamětí, agentů, browser/computer/image generation, code mode,
  vyhledávání skills a workspace dependencies. Všechny nakonfigurované MCP
  a nalezené skills se vypnou existujícím data-only helperem.
- Přesná verze ponechává backend `unified_exec` zapnutý i při explicitním
  disable. Vypnutí jeho vystavení přes `shell_tool=false` je oddělené od
  backendu. Statická kontrola není živý důkaz nulové nabídky nástrojů.
  Neočekávaný typ položky/nástrojový výstup zneplatní přejímku. Událostní
  kontrola sama není preventivní sandbox; tato mez se nezamlčuje.
- Soukromý slot je rezervovaný trvale před připojením. `delivery_unknown`
  je uložen a fsync dokončen před jediným možným turn/start. Další vyvolání
  stejné zkoušky vrátí starou účtenku včetně reserved/attention/unknown.
  Neexistuje automatický retry, reset nebo nové request ID.
- Při výpadku zůstane thread/turn identita, pokud byla známá. Nesmí se
  hádat výsledek a opakovat model. Ruční servis nejprve vyšetří stejný tah.
- Potvrzené doručení a číselná telemetrie se uloží před parsováním odpovědi.
  Chybný JSON, obsah, nástroj či překročení mezí nesmažou skutečnou spotřebu.
  BaseException/pád procesu zachová předchozí trvalý stav. Zavírá se vlastní
  klientské připojení, nikoli sdílený daemon.

## Ověření přípravy před živou zkouškou

- 28 nových neplacených testů přes skutečný produkční klient a syntetický
  RPC/event transport: Standard vs persistentní tier, izolace, effective
  permissions, commentary/final_answer, schema a obsah, použití nástrojů,
  neznámá či nadlimitní spotřeba, změna socketu/modelu/peeru/implementace,
  souběh, pád před připojením, pád před wire a po odeslání, žádné opakování.
- Cílené REC moduly: **193 testů OK**, následně 28/28 testů kandidátního
  vstupu po doplnění normalizace peer verze. Plná projektová brána persistenčního vstupu: **2 570 testů OK, 5 skipped**.
  Následná malá čtecí normalizace peer verze ověřena 28/28 cílenými testy
  a závěrečnou statickou branou; plná sada po této opravě znovu neběžela.
- Živý modelový tah: **0**. Skutečné nové kopie TXT: **0**. Produkční role,
  LaunchAgent, push, nasazení a integrace do main: **neprovedené**.

Příprava konkrétní karty odhalila příliš přísné porovnání syrového textu
verze s číslem: skutečný peer vrací `codex-cli 0.163.0`, nikoli jen číslo.
Bylo opraveno na porovnání již naparsovaných major/minor/patch a doplněn
regresní test. Nešlo o změnu běžícího serveru; první pokus byl ukončen před
thread/start i turn/start. Finální karta již prošla skutečným čtecím preflightem.

## Reprodukce izolovaných statických podkladů

Nepřenášet kartu mezi checkouty. V tomto worktree již existují: vlastní
`.venv/recovery_tokenizer` s tiktoken 0.14.0, soukromý npm cache a přesný CLI.
Při schváleném novém převzetí se nejprve opakuje čtecí runtime audit. Pro
stejný .163.0 peer lze statické podklady znovu získat do vlastní kopie:

```text
npm --cache .venv/recovery_rec06_npm_cache --prefix .venv/recovery_rec06_cli install --ignore-scripts --no-audit --no-fund @openai/codex@0.163.0
.venv/recovery_rec06_cli/node_modules/.bin/codex app-server generate-json-schema --out .venv/recovery_rec06_peer_schema
```

`features list` se vyvolá stejným soukromým CLI s jedním `--disable` pro
každý název v `DISABLED_FEATURES` a uloží do
`.venv/recovery_rec06_disabled_features.txt`. `_protocol()` vyžaduje všech
30 hodnot false a připne SHA-256 tohoto dokladu i obou schémat. Tento příkaz
není spuštěním služby ani placeného modelu. Nikdy nezapisovat do globálního
npm, společné venv nebo LaunchAgents. Samotný statický doklad není přejímka
živého modelového kontraktu.

## Přesný další postup

1. Míla přijme konkrétní kartu této jediné syntetické kalibrace včetně
   nepřesné tokenizace a absence tvrdého fakturačního stropu. Data pak
   použije jednou `app.recovery_guide_trial.run(approved_digest=...)` nad
   původní kartou, bez regenerace či opakování při nejistotě.
2. Vyhodnotit skutečnou účtenku a cenu. Syntetický PASS sám neuzavírá REC-02
   ani nenahrazuje celý návrh TXT. Připravit nový samostatně přijatý zdrojový
   manifest, bezpečné Mac/iPhone doklady a cenu skutečného čtecího pilotu.
3. Will převezme připravené změny do aktuálního main s uchováním svých rolí
   a práce. Po převzetí vytvořit nový manifest a ověřit přesný živý runtime;
   hotová karta z jiného checkoutu se bez nové přejímky nepřenáší.
4. Míla přijme celý aktualizovaný návrh a pravidla automatických změn.
   Potom autorizovaný produkční adaptér, první dvě kopie, upload a fyzická
   iPhone přejímka. Nakonec samostatně p+n, role, den/čas, rozpočet,
   launchd/auth session a jeden skutečný plánovaný slot/catch-up.

## Změněné soubory a předání

Nové: `app/recovery_guide_trial.py`, `tests/test_recovery_guide_trial.py`,
tento report a `recovery_guide_rec06_calibration_20261107.json`.
Upravené: `scripts/cockpit_quality_gate.py`, `memory/ACTIVE_PROJECTS.md`,
`memory/MEMORY_INDEX.md`, `memory/projects/samantha_external_backup.md`,
`memory/technical/recovery_guide_maintainer.md`,
`memory/technical/capability_routing_rules.md`, kanonický
`memory/handoffs/workstreams/project-samantha-infrastructure.md` a
`memory/tvbcp/workstreams/project-samantha-infrastructure.md`.

Soukromé nainstalované nástroje, cache, plné statické schéma, karta a testové
logy v `.venv` nejsou součástí commitu. Předání je pouze místní; Willovi se
neodesílala zpráva a neprovádělo se převzetí, push ani nasazení. Místní ref
origin/main již obsahuje předchozí REC-05; tento checkout zůstal na svém
headu a nezařazoval novější main změny. Živý release stav se z Git refu neodvozuje.

## Primární zdroje

- [App Server: start a turn](https://learn.chatgpt.com/docs/app-server#start-a-turn)
  — per-turn Standard, nepřenáší trvalou změnu tieru.
- [Authentication modes](https://learn.chatgpt.com/docs/app-server#authentication-modes)
  — spravovaný účet ChatGPT a account/read.
- [Codex / Work Standard kredity](https://learn.chatgpt.com/docs/pricing#token-rates)
  — sazby; nejde o API dolarové účtování.
- [Model gpt-6.1-sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
  — schopnosti modelu, nikoli doklad parametrů připojeného runtime.
- [Managing tokens](https://developers.openai.com/api/docs/guides/advanced-usage#managing-tokens)
  — referenční textová tokenizace neprokazuje celý serverový prompt.

## 2026-11-07 16:19 CET — skutečný výsledek schválené kalibrace

Míla oznámil nasazení připraveného balíčku a výslovně schválil zkoušku.
Použita původní karta s digestem `d613768b…0a4329a` v původním worktree.
Otisky implementace, schématu i runtime souhlasily; žádná změna karty,
opakování modelu ani nové request ID nebyly potřeba.

| Kontrola | Skutečný výsledek |
| --- | --- |
| Trvalá účtenka | `trial_passed`, accepted true |
| Modelové tahy | 1, automatické retry false |
| Doručení | completed, potvrzený start, právě jedna uživatelská položka |
| Model / úsilí | přesný Sol / medium |
| Standard | vynucený per-turn parametr `default`, žádný persistentní override |
| Strukturovaný obsah | všech 5 klasifikací a přesných citací správně |
| Nástroje | žádný zaznamenaný neočekávaný typ; 51 skills vypnuto |
| Spotřeba | 5 248 input + 188 output = 5 436 total, cached input 0, reasoning 0 |
| Čas modelového tahu | 6 646 ms |
| Odhad Standard kreditů | **0,3094**, proti rezervě 1,6 a přijímací mezi 2 |

Výpočet: `(5248 × 50 + 188 × 250) / 1 000 000 = 0,3094`. Jde o přepočet
skutečně naměřených tokenů schválenými Standard sazbami, nikoli o fakturační
účtenku. Cena je známá pouze pro tento syntetický tah.

Model rozlišil doloženou dokumentaci od historie a návrhu; zrušený placený
hlas označil irrelevant a iPhone za unverified. Vložený příkaz ke spuštění
shellu zůstal citovanými daty. Výstup byl ověřen proti pevným syntetickým
očekáváním. Pozorování bez nástrojových položek není univerzální důkaz,
že server nikdy žádný nástroj nenabídne.

Referenční textový počet 500 není totéž co skutečný input 5 248. Číselná
telemetrie nerozkládá rozdíl mezi modelovou tokenizaci a serverové rámování.
Poměr nelze mechanicky přenést na celý korpus; další rozpočet musí zachovat
rezervu pro každý nový kontext/dávku. Přesný tokenizer Solu zůstává nedoložený.

Tento krok změnil jen výsledkový JSON a projektovou dokumentaci/paměť.
Kód a testy zůstaly stejné; placený tah se neopakuje jako ověření zápisu.
Git-safe výsledková projekce byla porovnána s původní účtenkou a prošla
závěrečná statická brána. Nezměněná plná testovací sada se znovu nespouštěla.
Původní cenová karta JSON zůstává neměnným předběžným artefaktem; aktuální
výsledek se čte z výsledkového JSON a tohoto záznamu.

Další krok: aktuální manifest převzatého main, bezpečné doklady Mac/iPhone,
konkrétní cena celého čtecího pilotu a jeho přejímka. Až následně celý návrh
TXT, obě povolené kopie, upload/iPhone a samostatně autorizovaný týdenní běh.
V této relaci nebyl proveden push, deploy, restart, změna rolí ani provozních TXT.
