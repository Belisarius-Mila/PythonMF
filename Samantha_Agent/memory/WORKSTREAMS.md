# Registr pracovnich proudu

Kanonicky git-safe registr dlouhodobe prace vedene jako `Project`, `Tool`,
`Layer` nebo `Misc`.

Faze 4.1 zalozila validovany kodovy katalog v
`human_adam_workstream_catalog.py`. Po Milove rucni kontrole byla puvodni
technicka klasifikace opravena podle praktickeho pravidla: dlouhodoba oblast
prace je `Project`, konkretni opakovatelny vykonavatel je `Tool`, sdilena
infrastrukturni schopnost muze byt `Layer` a `Misc` je jen skutecne nezarazena
prace.

Katalog slucuje vsech 28 zivych oblasti z `ACTIVE_PROJECTS.md`, pridava
pozastavene projekty Vocabulary FR a Vocabulary IT a dva dohodnute vychozi
proudy `Misc`. Vysledkem je 29 proudu: 23 projektu, 4 tooly a 2 `Misc`.
Rezimy `paused` a `archived` jsou validni; tri projekty jsou nyni `paused`.

Markdown se za behu neparsuje a neni zdrojem UI, vlaken, workspace, semaforu
ani nasazovaci logiky. Faze 4.1 sama nic soukromeho nezaklada.

## Uplny katalog faze 4.1

| ID | Typ | Kanonicky nazev | Rezim | Priorita | Kanonicky zdroj / slouceni |
| --- | --- | --- | --- | --- | --- |
| `project-mmtx` | `Project` | MMTX | active | 1 | MMTX |
| `project-janicka-cockpit` | `Project` | Janička Cockpit | active | 1 | Janička Cockpit / používání a převzetí Samanthy |
| `project-r2-adam-janicka` | `Project` | R2-Adam / Janička | active | 2 | R2-Adam / Janička |
| `project-family-emergency-plan` | `Project` | Pozůstalost / rodinný nouzový balík | active | 1 | Pozustalost / rodinny nouzovy balik |
| `project-neuberk-kacenka` | `Project` | Neuberk interiér / Kačenka | active | 2 | Neuberk interier design / Kacenka |
| `project-samantha-agent-rag` | `Project` | Samantha Agent / RAG | active | 1 | Samantha Agent/RAG |
| `project-knowledge-library` | `Project` | Knihovna | active | 2 | Znalostni databaze / Knihovna clanku / Knowledge inbox |
| `project-document-vault` | `Project` | Správa dokumentů / private vault | active | 1 | Sprava dokumentu / private vault + Reminders / platebni SMS |
| `project-shopping-archive` | `Project` | Nákupní průzkum a archiv nákupů | active | 2 | Nakupni pruzkum a archiv nakupu |
| `project-email-cases` | `Project` | iCloud Mail / Email Cases | active | 1 | iCloud Mail read-only / Email Cases |
| `project-lekarna` | `Project` | Lékárna | active | 1 | Lekarna |
| `project-tomik-video` | `Project` | Tomík video / FamilyVideoOrganizer | active | 1 | Tomik video iMovie / FamilyVideoOrganizer |
| `project-family-memory-films` | `Project` | Family Memory Films / USA 2019 | active | 1 | Family Memory Films / USA 2019 |
| `project-multilo` | `Project` | MultiLO | active | 2 | MultiLO |
| `project-tax-2025` | `Project` | Daňové přiznání 2025 | active | 3 | Tax |
| `project-cockpit` | `Project` | Cockpit / hlavní architektura | active | 1 | Cockpit hlavni architektura + Recovery centrum + legacy VoiceBridge |
| `layer-human-adam-development` | `Project` | Human–Adam | active | 1 | App-server rozhrani / novy Adam; historicke ID je zachovano kvuli runtime kompatibilite. |
| `project-capability-catalog` | `Project` | Katalog projektů a schopností | active | 1 | Mapovani projektu a schopnosti |
| `project-samantha-infrastructure` | `Project` | Samantha Infrastructure | active | 1 | Samantha Infrastructure + Codex full access / Guard proti mazani |
| `project-mobile-input` | `Project` | iPhone Shortcuts / Mobile Input | paused | 2 | iPhone Shortcuts / Mobile Input Layer |
| `project-colors-and-numbers` | `Project` | ColorsAndNumbers / automatické úkoly | active | 1 | Automaticke opakujici se ukoly / ColorsAndNumbers |
| `project-vocabulary-fr` | `Project` | Vocabulary FR | paused | 2 | Potvrzeny kanonicky projekt v `project_capability_map.md`; lokalni a webova varianta patri dohromady. |
| `project-vocabulary-it` | `Project` | Vocabulary IT | paused | 2 | Potvrzeny kanonicky projekt v `project_capability_map.md`; lokalni a webova varianta patri dohromady. |
| `tool-backup-restore` | `Tool` | Záloha a obnova | active | 1 | Samantha external backup |
| `tool-media-image-resize` | `Tool` | Zmenšování obrázků | active | 1 | Media image resize utility |
| `tool-vocabulary-image-pipeline` | `Tool` | PictNew / obrázky ke slovíčkům | active | 2 | PictNew / Vocabulary image workflow |
| `tool-tts` | `Tool` | TTS | active | 1 | TTS / Adam Voice Remote Cockpit; jen obecny TTS vykonavatel. |
| `misc-brainstorm` | `Misc` | Brainstorm / nápady | active | 2 | Dohoda univerzalniho katalogu; bez projektoveho zdroje. |
| `misc-unclassified-development` | `Misc` | Miscellaneous / nezařazený vývoj | active | 2 | Dohoda univerzalniho katalogu; bez projektoveho zdroje. |

## Vysvetleni slouceni

- `Reminders / platebni SMS` je funkcni cast Spravy dokumentu, ne samostatny
  proud.
- `Cockpit Recovery centrum` a legacy VoiceBridge patri pod projekt Cockpit.
- Prime hlasove zadavani v Human–Adam patri pod projekt Human–Adam; obecne TTS
  zustava samostatnym toolem.
- `Codex full access / Guard proti mazani` patri pod Samantha Infrastructure.
- Webove varianty Vocabulary FR/IT nejsou samostatne projekty.
- `iPhone Shortcuts / Mobile Input` je jasne pojmenovany projekt, nikoli `Misc`,
  ale po drivejsim zmrazeni je veden jako `paused`.

## Stavajici runtime vazby

Faze 4.1 nezaklada vlakna ani profily. Runtime zustava navazany pouze na dva
drive overene proudy. Human–Adam si docasne ponechava historicky runtime typ
`Layer` a starsi nazev jako kompatibilni alias; katalog ho uz kanonicky vede
jako `Project` / `Human–Adam`.

| ID | Vlakno | TVBCP | Handoff |
| --- | --- | --- | --- |
| `layer-human-adam-development` | Stavajici oddelene vlakno Human–Adam; soukromy identifikator se do Gitu neuklada. | `tvbcp/architektura_komunikace_samantha.txt` | `handoffs/human_adam_layer_workstream_start_2026_07_20.md` |
| `project-knowledge-library` | Stavajici oddelene vlakno Knihovny; soukromy identifikator se do Gitu neuklada. | `tvbcp/knihovna_cockpit.txt` | `handoffs/knowledge_library_article_editing_2026_07_16.md` |

## Pravidla registru

- Jde o kanonicke identity existujicich oblasti, nikoli o duplicitni projekty.
- Typ pracovniho proudu je `Project`, `Tool`, `Layer` nebo `Misc`.
- Jeden proud muze sloucit vice starych radku `ACTIVE_PROJECTS.md`.
- Jeden historicky kombinovany radek muze byt pri vyjasneni rozdelen mezi
  projekt a tool; konkretne TTS zustava toolem a legacy VoiceBridge patri pod
  Cockpit.
- Test katalogu hlida, ze zadny zivy radek `ACTIVE_PROJECTS.md` nezmizel a ze
  dokumentacni i kodovy katalog maji stejna ID a poradi.
- Katalog neobsahuje soukrome identifikatory vlaken, profilu ani cestu k
  workspace.
- Zalozeni nebo prekvalifikovani zaznamu samo nemeni UI, API, Git workflow,
  nasazeni ani bezici relaci Human–Adam.
