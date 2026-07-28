# Registr pracovnich proudu

Kanonicky git-safe registr dlouhodobe prace vedene jako `Project`, `Tool`,
`Layer` nebo `Misc`.

Faze 4.1 zalozila validovany kodovy katalog v
`human_adam_workstream_catalog.py`. Po Milove rucni kontrole byla puvodni
technicka klasifikace opravena podle praktickeho pravidla: dlouhodoba oblast
prace je `Project`, konkretni opakovatelny vykonavatel je `Tool`, sdilena
infrastrukturni schopnost muze byt `Layer` a `Misc` je jen skutecne nezarazena
prace.

Katalog slucuje vsech 29 zivych oblasti z `ACTIVE_PROJECTS.md`, pridava
pozastavene projekty Vocabulary FR a Vocabulary IT a dva dohodnute vychozi
proudy `Misc`. Vysledkem je 30 proudu: 24 projektu, 4 tooly a 2 `Misc`.
Rezimy `paused` a `archived` jsou validni; tri projekty jsou nyni `paused`.

Markdown se za behu neparsuje a neni zdrojem UI, vlaken, workspace, semaforu
ani nasazovaci logiky. Faze 4.1 sama nic soukromeho nezaklada.

Faze 4.2 pridala neverejny soukromy lazy backend vlaken. Katalog pri nacteni
nevytvari adresare, klienty ani Codex vlakna. Teprve potvrzene otevreni jednoho
konkretniho proudu zalozi nebo obnovi jeho vlastni persistentni stav a pritom
znovu pouzije jeden sdileny cisty workspace a jeden app-server runtime. Aktivni
muze byt jen jeden lazy proud; prepnuti je fail-closed pri aktivnim tahu,
nejistem doruceni nebo necistem ci nesynchronnim workspace.

Faze 4.3 pridala kanonickou git-safe pametovou vazbu tehdejsich 29 proudu. Human–Adam
a Knihovna zachovavaji sve dva drive potvrzene handoff/TVBCP pary. Ostatni
proudy maji jedine stabilni cesty pod `memory/handoffs/workstreams/` a
`memory/tvbcp/workstreams/`, ale soubory se nevytvareji hromadne. Prvni
potvrzeny checkpoint konkretniho proudu po zelene brane transakcne zalozi obe
kostry, doplni chronologicky zaznam a zahrne je do stejneho commitu. Selhani
brany nebo commitu nenecha nepravdivy castecny pametovy par.

Faze 4.5g-d2 doplnila drive dohodnuty, ale opomenuty samostatny projekt
Rodinny kalendar. Ma lazy vlakno, stabilni dosud nematerializovane pametove
cesty a explicitne povolenou jednorazovou direct-main autorizaci. Nadale se
nesmi smesovat s Knihovnou clanku.

## Uplny kanonicky katalog

| ID | Typ | Kanonicky nazev | Rezim | Priorita | Kanonicky zdroj / slouceni |
| --- | --- | --- | --- | --- | --- |
| `project-mmtx` | `Project` | MMTX | active | 1 | MMTX |
| `project-janicka-cockpit` | `Project` | Janička Cockpit | active | 1 | Janička Cockpit / používání a převzetí Samanthy |
| `project-r2-adam-janicka` | `Project` | R2-Adam / Janička | active | 2 | R2-Adam / Janička |
| `project-family-emergency-plan` | `Project` | Pozůstalost / rodinný nouzový balík | active | 1 | Pozustalost / rodinny nouzovy balik |
| `project-neuberk-kacenka` | `Project` | Neuberk interiér / Kačenka | active | 2 | Neuberk interier design / Kacenka |
| `project-samantha-agent-rag` | `Project` | Samantha Agent / RAG | active | 1 | Samantha Agent/RAG |
| `project-knowledge-library` | `Project` | Knihovna | active | 2 | Znalostni databaze / Knihovna clanku / Knowledge inbox |
| `project-family-calendar` | `Project` | Rodinný kalendář | active | 1 | Rodinný kalendář |
| `project-document-vault` | `Project` | Správa dokumentů / private vault | active | 1 | Sprava dokumentu / private vault + Reminders / platebni SMS |
| `project-shopping-archive` | `Project` | Nákupní průzkum a archiv nákupů | active | 2 | Nakupni pruzkum a archiv nakupu |
| `project-email-cases` | `Project` | iCloud Mail / Email Cases | active | 1 | iCloud Mail read-only / Email Cases |
| `project-lekarna` | `Project` | Lékárna | active | 1 | Lekarna |
| `project-tomik-video` | `Project` | Tomík video / FamilyVideoOrganizer | active | 1 | Tomik video iMovie / FamilyVideoOrganizer |
| `project-family-memory-films` | `Project` | Family Memory Films / USA 2019 | active | 1 | Family Memory Films / USA 2019 |
| `project-multilo` | `Project` | MultiLO | active | 2 | MultiLO |
| `project-tax-2025` | `Project` | Daňové přiznání 2025 | active | 3 | Tax |
| `project-cockpit` | `Project` | Cockpit / hlavní architektura | active | 1 | Cockpit hlavni architektura + Recovery centrum; stará komunikační větev je vyřazená |
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
| `tool-tts` | `Tool` | TTS | active | 1 | TTS / české audio nástroje; jen obecný TTS vykonavatel. |
| `misc-brainstorm` | `Misc` | Brainstorm / nápady | active | 2 | Dohoda univerzalniho katalogu; bez projektoveho zdroje. |
| `misc-unclassified-development` | `Misc` | Miscellaneous / nezařazený vývoj | active | 2 | Dohoda univerzalniho katalogu; bez projektoveho zdroje. |

## Vysvetleni slouceni

- `Reminders / platebni SMS` je funkcni cast Spravy dokumentu, ne samostatny
  proud.
- Historická komunikační větev patřila pod projekt Cockpit a po svém vyřazení
  netvoří samostatný aktivní proud.
- Prime hlasove zadavani v Human–Adam patri pod projekt Human–Adam; obecne TTS
  zustava samostatnym toolem.
- `Codex full access / Guard proti mazani` patri pod Samantha Infrastructure.
- Webove varianty Vocabulary FR/IT nejsou samostatne projekty.
- `iPhone Shortcuts / Mobile Input` je jasne pojmenovany projekt, nikoli `Misc`,
  ale po drivejsim zmrazeni je veden jako `paused`.

## Stavajici runtime vazby

Faze 4.2 zachovava oba drive overene proudy jako rezervovane legacy vazby, aby
pred migraci nevzniklo druhe vlakno Human–Adam ani Knihovny. Zbyvajicich 27
proudu melo pripraveny lazy soukromy slot; po doplneni Rodinneho kalendare je
lazy proudu 28. Zadny se nezaklada pri startu
Cockpitu. Human–Adam si docasne ponechava historicky runtime typ `Layer` a
starsi nazev jako kompatibilni alias; katalog ho uz kanonicky vede jako
`Project` / `Human–Adam`.

| ID | Vlakno | TVBCP | Handoff |
| --- | --- | --- | --- |
| `layer-human-adam-development` | Stavajici oddelene vlakno Human–Adam; soukromy identifikator se do Gitu neuklada. | `tvbcp/architektura_komunikace_samantha.txt` | `handoffs/human_adam_layer_workstream_start_2026_07_20.md` |
| `project-knowledge-library` | Stavajici oddelene vlakno Knihovny; soukromy identifikator se do Gitu neuklada. | `tvbcp/knihovna_cockpit.txt` | `handoffs/knowledge_library_article_editing_2026_07_16.md` |

Kanonicke handoff/TVBCP vazby vsech proudu vlastni
`human_adam_workstream_memory.py`. Status vystavuje pouze pripravenost dokumentu,
nikoli soukrome vlakno nebo private cestu. Pri startu jsou materializovane jen
dva zachovane legacy pary; dalsi vzniknou az prvnim skutecnym checkpointem.

## Pravidla registru

- Jde o kanonicke identity existujicich oblasti, nikoli o duplicitni projekty.
- Typ pracovniho proudu je `Project`, `Tool`, `Layer` nebo `Misc`.
- Jeden proud muze sloucit vice starych radku `ACTIVE_PROJECTS.md`.
- Jeden historicky kombinovany radek muze byt pri vyjasneni rozdelen mezi
  projekt a tool; konkretne TTS zustava toolem a vyřazená komunikační větev
  zůstává pouze historií projektu Cockpit.
- Test katalogu hlida, ze zadny zivy radek `ACTIVE_PROJECTS.md` nezmizel a ze
  dokumentacni i kodovy katalog maji stejna ID a poradi.
- Katalog neobsahuje soukrome identifikatory vlaken, profilu ani cestu k
  workspace.
- Soukromy lazy backend smi vystavit jen redigovany stav bez ID vlakna a bez
  private cesty.
- Kazdy proud ma prave jeden kanonicky handoff a jeden kanonicky TVBCP; dva
  proudy nesmeji sdilet stejnou cestu.
- Chybejici proudove dokumenty se zakladaji pouze uvnitr potvrzeneho
  checkpointu po zelene brane a pri selhani commitu se transakcne vrati zpet.
- Otevreni proudu vyzaduje potvrzeni, cisty synchronni workspace, dokonceny tah
  a vyresene doruceni; archivni proud se neotevira.
- Zalozeni nebo prekvalifikovani zaznamu samo nemeni UI, API, Git workflow,
  nasazeni ani bezici relaci Human–Adam.
