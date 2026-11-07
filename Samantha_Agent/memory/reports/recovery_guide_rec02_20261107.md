# REC-02 — neplacený preflight a připravenost cenového pilotu

Stav 2026-11-07. Proud `project-samantha-infrastructure`, vlastní Data worktree.
Míla požádal pokračovat fází 2. Připravený neplacený výpočet a kontroly;
**živý čtecí pilot se Solem zatím neproběhl**. Fáze REC-02 proto není celá
uzavřená. Provozní TXT, modelové role, služby, push ani nasazení se neměnily.

## Reprodukovatelný vstup

Doprovodný `recovery_guide_rec02_20261107.json` obsahuje přesný manifest
s otisky všech zdrojů, navržené dávky, jejich otisky a čtecí runtime audit.
Neobsahuje původní TXT, texty zdrojů, modelové prompty ani tajné konfigurace.
Jde o zmrazený důkaz konkrétního preflightu, ne oprávnění spustit model.

- HEAD dokumentace: `dc528b4588336bb8af45c9fd72127cca4a122b47`.
- Snapshot: `dccc12e5c3eeae52eae111672c37fcdb6b6d8c514e2b7445f45cec18cbb2cdcc`.
- Celý původní návod byl načten první; SHA-256
  `a3659d9cf61ccd9d1c04737060f215ec4b6547da1eb877aa92b793f97e936935`.
- 509 celých dokumentů, celkem s původním návodem 5 921 126 B;
  114 ostatních textů mimo navržený rozsah. Výčet není přijatý korpus.
- Naplánováno 10 dávek + 1 syntéza, každý zdroj právě jednou v dávkách.
  Původní návod se předává každé dávce a syntéze. Žádný soubor se nekrátil.
- Referenční plán: `ff9fe0098fa4a8f9c5e0bc077e4f4482f7b4315387f70ce1c4ca84853641f53d`.

Nové zápisy vzniklé po tomto měření do uvedeného snapshotu nepatří. Před
skutečným pilotem znovu zmrazit celý přijatý korpus nad čistým cílovým HEAD;
nepředstírat, že historický snapshot zahrnuje pozdější dokumentaci.

## Tokeny a cena: co bylo skutečně změřené

Do samostatného prostředí `.venv/recovery_tokenizer` instalovaný pouze
`tiktoken 0.14.0` a jeho závislosti. Společná `.venv` ani závislosti projektu
se neměnily. Žádná instalace do globálního Pythonu nebo změna Codexu.

Upstream `encoding_for_model("gpt-6.1-sol")` vrací KeyError. Kód z toho
nedělá náhradu za jiný model, nepřidává vlastní neověřené mapování. Přesný
čítač pro živý pilot zůstává zablokovaný. Samostatný referenční výpočet
výslovně používá `o200k_base`; to **není doložený tokenizer Solu**.

| Referenční metrika | Výsledek |
| --- | ---: |
| Původní celý návod | 18 540 tokenů |
| Celá zvolená dokumentace | 1 802 609 tokenů |
| Plánované vstupy včetně opakovaného návodu, instrukcí a syntézy | 2 222 784 tokenů |
| Rezervované výstupy: 10 × 8 000 + 32 000 syntéza | 112 000 tokenů |
| Standard výpočet bez cache | 139,1392 kreditů |

Výpočet: vstup × 50 / milion + výstup × 250 / milion. Při stejném objemu
4 revize představují referenčně 556,56 a 5 revizí 695,70 kreditů. Nejde
o peněžní cenu, počet úloh v předplatném, zaručenou fakturaci ani tvrdý strop.
Položky 500 kreditů/běh a 2 500/měsíc v diagnostické specifikaci jsou
**neschválené vstupní parametry preflightu**, nikoli nastavený provozní limit
nebo požadavek na útratu. Skutečný přijatelný rozpočet ještě dohodnout.

Počet BPE tokenů textu ani při známém mapování neprokazuje celý modelový
prompt App Serveru. Framing, efektivní instrukce a skutečnou spotřebu je
nutné ověřit telemetrií jediného schváleného syntetického tahu. Předběžné
rezervace/citlivost počítání nikdy nevydávat za přesné měření fakturace.

## Runtime audit bez modelového tahu

Připojení pouze k existujícímu sdílenému Unix socketu, `initialize`,
`model/list` a `config/read`; žádný nový proces, thread/start ani turn/start.
Vynechány texty systémových instrukcí, celé konfigurace a soukromé údaje.

- Lokální příkaz `codex`: `0.166.0`.
- Připojený App Server: `0.163.0`; verze procesu se nesmí odhadnout z
  nynějšího binárního souboru nebo starého handoffu.
- `gpt-6.1-sol` s medium je v připojeném katalogu nabízený. To není placená
  zkouška přístupu ani důkaz izolace.
- Efektivní preference nevyhovuje kontrole Standard (`None`/`default`).
  Zdědit ji a účtovat odhad za Standard by bylo nesprávné. Kód ji neměnil.
- Připojený katalog nedoložil kontextové okno. Offline bundled katalog
  místní CLI uvádí 272 000, dokumentace uvádí 500K pro Codex/ChatGPT Work;
  tyto údaje nejsou důkazem kontextu právě běžícího serveru. Diagnostický
  plán používá konzervativnější 250K, ale pilot tím nezpřístupní.
- Typ autentizace/fakturační základ a živá účinnost všech omezení neověřené.

Oficiální App Server nyní dokumentuje `serviceTierForTurn: "default"` pro
jeden tah. Současný projektový klient tento parametr nevystavuje a nelze
předpokládat, že běžící starší server má stejný kontrakt. V této etapě se
produkční klient, globální preference ani služba kvůli tomu neměnily.

## Co změnil kód

`recovery_guide_preflight.py` přidává striktní tokenizer probe, blokující
přesný čítač, oddělenou referenční inventuru a redigovaný čtecí audit runtime.
CLI/workflow má nové neplacené `preflight` a `runtime`; run/tick dále
vracejí activation_required bez placeného volání.

Řadič má samostatnou výstupní rezervu pro inspekci a syntézu. I při
nadlimitním známém výstupu zachová skutečnou telemetrii/cenu v účtence;
měsíční součet používá vyšší ze známé ceny a původní rezervace. Nejde o
automatický retry ani tvrdý fakturační limit.

Příkazy pro reprodukci bez modelu:

```text
.venv/recovery_tokenizer/bin/python scripts/recovery_guide.py preflight
.venv/bin/python scripts/recovery_guide.py runtime
.venv/bin/python scripts/recovery_guide.py status
```

Preflight vrací záměrně exit 2 a `blocked_for_live_pilot`, přestože měření
referenčního plánu dokončil. Výstup je JSON bez textů. Síťový tokenizer
soubor se po prvním načtení ukládá do izolované cache tokenizeru pod `.venv`
(první diagnostika použila standardní dočasnou cache); žádný projektový
obsah se kvůli tokenizaci neodesílá. Runtime audit může bez
spuštění náhradního serveru vrátit `unavailable`.

## Přesný další integrační krok

Will nejprve převezme lokální vývojové commity do svého aktuálního main
s uchováním jeho novějších rolí a práce. Pak samostatným registrovaným
read-only auditem doloží skutečný runtime/kontext, možnost izolovaného
Standard tahu a kompatibilitu omezení bez změny globálních rolí/preferencí.
Pokud je nutný restart či release, vyžádá se jeho samostatné oprávnění.

Potom uzavřít mapování tokenizeru (nebo s Mílou výslovně změnit přísný
požadavek na předběžně přesný počet na doložený odhad + živou kalibraci),
odsouhlasit úplný manifest a konkrétní rozpočet syntetického kandidátního
pilotního tahu. Teprve poté jeden pevný syntetický Sol/medium tah, trvalý
marker před odesláním, bez retry, bez skutečné dokumentace a publikace.
Po zkoušce schválit rozsah/cenu čtení celého korpusu. Žádné samovolné
rozšíření tohoto předběžného souhlasu na týdenní službu nebo writer.

## Ověření

Plná projektová brána: 2 423 testů OK, 5 skipped; po doplnění Fast a měsíčního regresního případu znovu 76 cílených testů OK (11 nových v REC-02), závěrečná statická brána OK

## Primární podklady

- [Sol a modelové limity](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
- [Počítání tokenů a omezení předběžného počtu](https://developers.openai.com/api/docs/guides/advanced-usage#managing-tokens).
- [Standard kredity](https://learn.chatgpt.com/docs/pricing#token-rates).
- [App Server a tier jednoho tahu](https://learn.chatgpt.com/docs/app-server#start-a-turn).


### Soubory této etapy

Nové: `app/recovery_guide_preflight.py`, `tests/test_recovery_guide_preflight.py`,
tento report a jeho JSON evidence.

Upravené: `app/recovery_guide_maintainer.py`, `scripts/recovery_guide.py`,
`app/workflows/commands.py`, `scripts/cockpit_quality_gate.py`,
`memory/ACTIVE_PROJECTS.md`, `memory/MEMORY_INDEX.md`,
`memory/projects/samantha_external_backup.md`,
`memory/technical/recovery_guide_maintainer.md` a kanonický handoff/TVBCP
`project-samantha-infrastructure.md`. Celkem 14 souborů.
