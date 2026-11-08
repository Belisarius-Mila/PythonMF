# REC-06 — zastavení před modelem po změně main, nový manifest

2026-11-07, Data, vlastní worktree `data/parallel-20261104`.

Míla výslovně schválil úplnou revizi podle původní karty
`9a532089fab4299bbebfa9f7c2bf8a84b95253d5bf8456672ec1fdcb38ba0133`,
včetně navržené přijímací meze 200 Standard kreditů bez tvrdého fakturačního
stropu. Toto cenové a modelové oprávnění se znovu nevyžaduje pro stejný
rozsah a limit; změnil se ale konkrétní zdrojový manifest.

## Co zastavilo původní spuštění

Před rezervací úlohy kontrola vrátila `full_pilot_frozen_inputs_changed`.
Místní main se posunul z `2909ea5ace2e993edb5ace4875ec552f00a7e1e2` na
`4a33af2a1e570a3cb781f2253df440d82b25defb`: Willův krok zjednodušení
kalendářových karet a potvrzovaného vytváření přes EventKit. Týká se také
vybrané projektové dokumentace, nejde pouze o nesouvisející binární změnu.

Ověřené ostatní vstupy souhlasily: původní TXT, otisky kódu, předchozí
syntetická kalibrace i statický protokol. **Nevznikl attempt marker,
controller ani per-turn záznam. Nebyl založen thread nebo spuštěn turn.
Počet modelových tahů úplné revize je 0, spotřeba tohoto spuštění 0.**
Původní soukromá i veřejná karta zůstávají zachované; nejsou přepisované
za novější zdroje a jejich starý digest se nepoužije pro nový obsah.

## Bezpečné obnovení přípravy před prvním pokusem

`app.recovery_guide_full_pilot.prepare(project_only=False, refresh=True)`
je nový explicitní neplacený vstup pro tento případ:

- Vyžaduje původní kartu a stejný rozsah. Nezakládá novou modelovou úlohu.
- Odmítne obnovení při existenci attempt markeru, controlleru nebo turns,
  tedy i po nejasném či částečném pokusu. Nic nemaže, neodemyká a neresetuje.
- Nový manifest/cenu uloží create-only pod nový digest do `revisions/`.
  Původní karta zůstává beze změny; nová uvádí supersedes digest.
- Zachová předchozí kreditové limity. Pokud nový plán převyšuje původní
  schválenou mez, nevytvoří novou kartu pod vyšším implicitním rozpočtem.
- Všechny verze sdílejí **jediný job/request a attempt marker**. Jakmile
  jedna verze úlohu rezervuje, druhá ji nemůže znovu spustit. Stejná verze
  pak vrací původní účtenku i v jiném týdnu.
- `run(approved_digest=...)` otevře přesně odpovídající originální nebo
  verzovanou kartu. Neznámý hash, upravený packet a symlink jsou odmítnuté.
  Neprovádí automatické přijetí nového manifestu ani automatický modelový retry.

Nová veřejná projekce: `recovery_guide_rec06_full_card_20261107_v2.json`.
Výsledný počet dokumentů, digest a přepočet jsou v této kartě a v navazujícím
časovaném záznamu. Původní `full_card_20261107.json` zůstává historickým
schváleným podkladem pro starý main, nikoli oprávněním k jiným bajtům.

## Ověření

Šest nových regresních případů: zachování staré karty a rozpočtu, vlastní
nový digest, společný job bez dvojího spuštění, odmítnutí při attempt i
osamoceném controlleru, nepovolené navýšení rozpočtu a symlink revize.
Cílená sada revision/full pilot: **34 testů OK**. Plná brána: 2 605 testů OK, 5 skipped; závěrečná statická brána OK.
Testy jsou syntetické, bez živého modelu a změn původních TXT.

Zdrojový main, produkční klient, runtime, kalendář/e-mail, role JSON a
provozní kopie návodu se v tomto kroku nemění. Žádný push ani nasazení.
Nejde o opravu Willovy kalendářové práce; ta se pouze zahrne do nového
čtecího zdrojového podkladu.

## Další krok

Přijmout změněný konkrétní manifest v2, při zachování již schváleného
modelu, jednorázové úlohy a limitu 200 kreditů. Teprve potom jednou zavolat
run s jeho přesným digestem. Nový main po této přejímce znovu znamená
čtecí zastavení; neobchází se zmrazení zdrojů. Pro spuštění z izolovaného
Data worktree není potřeba nasazovat tento pilot do main.

## 2026-11-07 19:58 CET — konkrétní karta v2

- Zdrojový main: `4a33af2a1e570a3cb781f2253df440d82b25defb`.
- Snapshot: `90e85eb7e83abdb9bf4a57940081756cc1edbcc35de1ee57e4b4aff5f27ab8ad`.
- Nový approval digest: `09a6ed5becbe07e8d2a5703e29639b5f30aff9c3a40db4af7f2220bf999f4e0b`.
- Dokumenty: **530**, plus původní TXT; dohromady **6 290 890 bajtů**.
- Plán: **15 tahů**, rezerva **193,79845 Standard kreditu**, zachovaná mez **200**.
- Změny oproti starému manifestu: **1 přidaný, 5 změněných, 0 odstraněných**.

Přidané: `Samantha_Agent/memory/reports/calendar_simple_20261107.md`.

Změněné: `Samantha_Agent/memory/ACTIVE_PROJECTS.md`, `Samantha_Agent/memory/LESSONS_LEARNED.md`, `Samantha_Agent/memory/MEMORY_INDEX.md`, `Samantha_Agent/memory/handoffs/continuous_personal_agent_2026_11_04.md`, `Samantha_Agent/memory/projects/email_readonly_oauth.md`.

Karta v2 je připravená, ne automaticky přijatá modelem. Původní finanční
souhlas trvá; před spuštěním zbývá přijmout změnu konkrétních zdrojů.
