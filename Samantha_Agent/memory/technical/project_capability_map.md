# Project capability map

Zalozeno 2026-05-19.
Potvrzeno Milou 2026-05-19.

Tento dokument mapuje projekty v `PythonMF` na schopnosti, workflow a bezpecnostni
brany pro Samanthu. Cilem neni popsat vsechny soubory, ale rozhodnout, co ma byt
pro bezny lidsky pokyn registrovana schopnost a co zatim zustava jen rucni prace
Codexu.

## Potvrzene rozhodnuti

Mila potvrdil tuto taxonomii:

- jako projekty bereme jen kanonicke oblasti s vlastnim ucelem, zdroji a
  udrzbou,
- web, build, dataset, platformni odvozenina nebo historicky prototyp jsou
  varianta/vystup/podprojekt, ne automaticky novy projekt,
- asset knihovny, sdilene skripty, `build/`, `dist/`, `tmp/`, `output/` a
  stare zalohy nejsou samostatne projekty,
- `ACTIVE_PROJECTS.md` ma obsahovat jen aktualne zive nebo rozpracovane oblasti,
  ne kompletni katalog vsech slozek,
- memory karty se maji zakladat jen pro prijate projekty, ktere budou opravdu
  zive nebo se s nimi bude aktivne pracovat.

Prvni prakticke workflow kandidaty:

1. `PictNew` read-only audit.
2. `VocabularyEN` sync do `docs/`.

Oba maji jasny vstup, vystup a nizke riziko.

## Urovne pripravenosti

| Uroven | Vyklad |
| --- | --- |
| L0 | Jen memory nebo poznamka. Samantha umi najit kontext, ale nema specialni tool ani workflow. |
| L1 | Existuje lokalni skript nebo aplikace, ale neni registrovana jako Samantha workflow. |
| L2 | Existuje registrovany shell workflow v `app/workflows/commands.py`. |
| L3 | Existuje Samantha `function_tool` s bezpecnostnimi pravidly a testy. |
| L4 | Chybi lidsky workflow kolem hotoveho toolu, napr. navazani vice kroku nebo prace v browseru. |

## Globalni schopnosti Samanthy

| Oblast | Uroven | Aktualni schopnost | Bezpecnostni brana |
| --- | --- | --- | --- |
| Lokalni pamet | L3 | `search_memory`, `memory_status`; RAG-like vyhledavani v markdown pameti. | Necte e-maily ani tajemstvi; jen memory soubory. |
| Workflow registry | L3 | `list_workflow_commands`, `preview_workflow_command`, `run_workflow_command`. | Shell jen z presne registrovaneho `argv`; zapisujici prikaz dvoukrokove. |
| E-mail read-only | L3/L4 | Hlavicky, hledani hlavicek, cteni konkretniho UID po potvrzeni, action case, case vault, archive vault, reminders, RIXO case. | Samostatne potvrzeni pro telo, ulozeni, archivaci, plne URL a oznaceni pripominky jako hotove. Nic neodesilat, nemazat, nepresouvat, neoznacovat jako prectene. |
| Reminders | L3 | Vypsat otevrene pripominky, detail, ulozit potvrzeny email action case, oznacit jako hotove. | Ulozeni a dokončení vyzaduje potvrzeni; bez plnych URL a bez neredigovanych adres. |
| Backup a obnova | L2/L3 | Registrovany backup workflow; tooly pro snapshoty, preview obnovy a potvrzenou obnovu. | Recovery pouze do `/Volumes/SamanthaSecureBackup/SamanthaBackups`; obnova nejdriv preview, potom potvrzeni, citlive cesty vyzaduji slovo `citlive` nebo `recovery`. |

## Registrovane shell workflow

Aktualni registry je v `Samantha_Agent/app/workflows/commands.py`.

| command_id | Ucel | Stav |
| --- | --- | --- |
| `backup_project_recovery` | Ostra recovery zaloha PythonMF/Samantha do sifrovaneho externiho kontejneru. | Registrovano, zapisujici, vyzaduje preview a potvrzeni. |
| `backup_project_dry_run` | Dry-run recovery zalohy bez kopirovani. | Registrovano, read-only preview. |

Dalsi projektove shell postupy zatim nejsou registrovane. Pokud je Mila zada
bezne lidsky, Samantha je nesmi prevadet na ad hoc shell; ma rict, ze workflow
neni registrovane, nebo ho navrhnout jako novou kartu.

## Projekty s memory kartou

| Projekt | Lokace | Uroven | Aktualni schopnosti/workflow | Nejblizsi kandidat na registraci |
| --- | --- | --- | --- | --- |
| Samantha Agent/RAG | `Samantha_Agent/` | L3 | Agent nad OpenAI Agents SDK, memory startup kontext, `search_memory`, `memory_status`. | Live retest dotazu na RAG a e-mail read-only; pokud sumi, pridat filtr typu zdroje. |
| iCloud Mail / Email Cases | `Samantha_Agent/app/email/`, `data/email/` | L3/L4 | Bohata sada read-only e-mail toolu, case/action/reminder/archive vrstvy. | Rozmrazit az na Miluv pokyn; doplnit lidsky WorkMode nad ulozenym case/archivem a browser workflow pro potvrzene odkazy. |
| Backup/restore | `Samantha_Agent/scripts/`, `app/backup/`, `app/workflows/` | L2/L3 | Workflow backupu, snapshot list, preview restore, potvrzena obnova. | Provest dalsi dry-run/ostry test podle stavu sifrovaneho kontejneru. |
| macOS sit / Tailscale recovery | `NETWORK_RECOVERY_CARD.txt`, `scripts/network_recovery_card.sh` | L1 | Offline recovery karta a rucni diagnostika. | Registrovat read-only diagnosticky workflow nebo jen ponechat jako nouzovy manual. |
| MMTX | `MatysekANJ/MMTX.py`, `MatysekANJ/web_mmtx/`, `docs/` | L1 | Pygame/web vyukova aplikace, hotspoty, sceny, audio podklady. | Workflow pro sync webu do `docs/` a smoke test; pred zmenami cist MMTX memory a handoff. |
| Matysek English Game concept | `MatysekANJ/anglictina_matysek_V3.py` | L0/L1 | Koncept a starsi Pygame experimenty. | Nechat V3 stabilni; hlavni smer je MMTX. |
| MultiLO | `MultiLO/` | L1 | Desktop vyukova aplikace, testy `test_multilo_core.py`, `test_storage.py`, rucni retest checklist. | Registrovat read-only/test workflow pro `py_compile` a unit testy; zapisove zmeny delat jen po konkretni zadani. |
| PictNew / FR+IT obrazky | `pict_new_audit.py`, `pict_new_prepare.py`, `image_generator.py`, `Pict/`, `PictNew/`, `VocabularyFR/`, `VocabularyIT/` | L1 | Overeny rucni workflow: audit/request -> dry-run -> potvrzene placene batch generovani -> review -> kopie do `Pict/` -> mapping az po dalsim potvrzeni. Kanonicky postup je v `technical/vocabulary_image_generation_workflow.md`. | Registrovat PictNew workflow s oddelenymi kroky: prepare, dry-run, confirmed generate, copy approved, mapping preview/apply se zalohou. |
| VocabularyEN web cards | `VocabularyEN/`, `docs/vocabulary-en/`, `docs/data/` | L1 | Sync CSV do `docs`, learner web MVP, localStorage stav. | Registrovat sync workflow `VocabularyEN -> docs`; test pres lokalni HTTP server pri UI zmenach. |
| TTS edge audio | `scripts/generate_tts.py`, `scripts/tts_gui.py` | L1 | Davkove MP3 z CSV a rucni GUI pres `edge-tts`. | Registrovat davkove TTS workflow; GUI spoustet jen na Miluv pokyn a s vedomim, ze otevre okno. |
| Tax 2025 | `Tax/` | L0/L1 | Checklist a vypocet v memory; citlive podklady v projektu. | Zadne automaticke vypocty bez zadani; pripadny workflow jen pro kontrolu checklistu, bez ukladani rodneho cisla/adres. |
| Lekarna | `Samantha_Agent/data/lekarna/` | L0/L1 | Evidence domacich leku v CSV, bezpecnostni pravidla. | Python tool pro read-only dotazy nad evidenci podle symptomu; nikdy neodhadovat davkovani. |
| Vedecke clanky | `Samantha_Agent/data/vedecke_clanky/` | L0/L1 | Registry struktura a pravidlo ptat se pred internetem. | Tool/workflow pro pridani clanku do registry; internetove doplneni jen po dotazu. |
| Pohadkova knizka GPT+Canva | `Samantha_Agent/memory/stories/`, budoucí knizni slozka | L0 | Redakcni workflow, stylova bible, prompty, Canva sazba. | Strukturovany workflow pro jednu pilotni pohadku: raw -> redakce -> strankovani -> styl/postavy -> Canva podklady. |
| Fraska/Dante esej | memory only | L0 | Koncept pojmu a tematicke osy. | Textovy workflow pro redakci eseje, bez automatizace v shellu. |

## Repo oblasti bez samostatne memory karty

Tyto oblasti existuji v repozitari a jsou z velke casti popsane ve starsim
katalogu `PROJECTS.md`, ale nejsou zatim plne popsane v
`Samantha_Agent/memory/projects/`. Pred dulezitou praci je vhodne zalozit nebo
doplnit memory kartu.

| Oblast | Pozorovane soubory | Predbezny typ |
| --- | --- | --- |
| `Animals/` | `animal_quiz.py` | Vyukova aplikace / quiz. |
| `AnimalsFilmPY/` | `animals_film.py` | Vyukovy nebo filmovy Python projekt. |
| `ColorsAndNumbers/` | `colors_numbers.py`, `web_colors_numbers/` | Vyukova aplikace a web. |
| `MBSoft/` | FR/IT aplikace, launchery, sync skripty | Slovnikove aplikace pro mobil/iPhone workflow. |
| `RestauracePTKL/` | texty, postavy, `restaurace_lines.py`, web | Anglicky pribeh/restauracni vyukovy projekt. |
| `Sportka/` | navrhy a CSV losovani | Analyticky/hravy projekt pro Sportku. |
| `ToBeTraining/` | `tobe_trenink.py`, Pygame varianta, CSV | Anglictina, trenink slovesa to be. |
| `VocabularyES/` | CSV a `vocab_trainer_es.py` | Slovnikova desktop aplikace. |
| `VocabularyLA/` | CSV a `vocab_trainer_la.py` | Slovnikova desktop aplikace. |
| `ZalohyPY/` | stare kopie kodu a CSV | Lokalni archiv/stare zalohy; nepouzivat jako zdroj pravdy bez overeni. |
| `iOS/` | `VocabFRLockscreen/` | iOS/navazujici projekt, zatim nemapovany. |

## Mapovani `PROJECTS.md` na rozhodnuti

`PROJECTS.md` je katalog slozek a vystupu. Pro Samanthu je uzitecne rozlisit
kanonicky projekt od jeho vystupu, platformni varianty, asset knihovny a archivu.

### Prijmout jako kanonicke projekty

Tyto polozky maji vlastni ucel, zdrojove soubory a pravdepodobne budou mit vlastni
memory kartu nebo uz ji maji.

| Kanonicky projekt | Slozky/vystupy z `PROJECTS.md` | Poznamka |
| --- | --- | --- |
| Samantha Agent | `Samantha_Agent/` | Hlavni projekt agenta, pameti, toolu, workflow, backupu a e-mailu. |
| MMTX | `docs/`, `MatysekANJ/MMTX.py`, `MatysekANJ/web_mmtx/` | Jeden aktivni projekt; web a Pygame jsou varianty/vystupy, ne dva nezavisle projekty. |
| MultiLO | `MultiLO/` | Samostatna vetsi desktop aplikace s testy a buildem. |
| Vocabulary EN | `VocabularyEN/`, `docs/vocabulary-en/`, `docs/vocabulary-en83/` | Jeden projekt se dvema datovymi sadami a webovymi vystupy. |
| Vocabulary FR | `VocabularyFR/` | Samostatny slovnikovy projekt; `MBSoft FR` a iOS varianta jsou platformni odvozeniny, pokud se nerozhodne jinak. |
| Vocabulary IT | `VocabularyIT/` | Samostatny slovnikovy projekt; web/data export jsou vystupy. |
| Vocabulary ES | `VocabularyES/` | Mensi samostatny slovnikovy projekt, zatim bez memory karty. |
| Vocabulary LA | `VocabularyLA/` | Mensi samostatny slovnikovy projekt, zatim bez memory karty. |
| Colors and Numbers | `ColorsAndNumbers/`, `docs/colors-numbers/`, `assets/openmoji_numbers/` | Jeden projekt; web a desktop jsou varianty, `assets/` je sdileny zdroj. |
| To Be Training | `ToBeTraining/` | Samostatna vyukova aplikace/prototyp. |
| Animals Quiz | `Animals/` | Maly samostatny vyukovy projekt. |
| Animals Film | `AnimalsFilmPY/` | Samostatny sekvencni vyukovy projekt. |
| Restaurace PTKL | `RestauracePTKL/`, `docs/restaurace-ptkl/` | Jeden dialogovy projekt; web je vystup. |
| PictNew / vocabulary image pipeline | `pict_new_audit.py`, `PictNew/`, `Pict/`, `VocabularyFR/`, `VocabularyIT/` | Projekt/workflow nad sdilenou obrazkovou knihovnou. |
| Tax 2025 | `Tax/` | Samostatny citlivy dokumentovy projekt. |
| Lekarna | `Samantha_Agent/data/lekarna/` | Samostatny lokalni datovy projekt uvnitr Samanthy. |
| Vedecke clanky | `Samantha_Agent/data/vedecke_clanky/` | Samostatna lokalni knihovna uvnitr Samanthy. |
| Pohadkova knizka | `Samantha_Agent/memory/stories/`, budouci knizni slozka | Kreativni projekt nad ulozenymi pohadkami. |
| Sportka | `Sportka/` | Samostatny experiment/analyticky projekt, ale oznacit jako nizkou prioritu a bez praktickeho dopadu na sance. |

### Sloucit jako variantu nebo podprojekt

Tyto polozky z `PROJECTS.md` nepovazovat za novy hlavni projekt, pokud Mila
nevyslovne rekne, ze se z nich ma stat samostatna vetev.

| Polozka | Rozhodnuti |
| --- | --- |
| `MMTX Web` a `MMTX Pygame` | Sloucit pod jeden projekt `MMTX`; sledovat, co je zdroj pravdy pro web. |
| `Anglictina Matysek` | Historicka/prototypova vetev pod detskou anglictinu; hlavni smer je `MMTX`. |
| `Vocabulary EN83 web` | Datova sada/vystup v ramci `Vocabulary EN`, ne samostatny projekt. |
| `MBSoft FR/IT` | Platformni varianta slovniku FR/IT pro Pythonista/iOS styl; zalozit memory kartu az pri aktivni praci. |
| `VocabFR LockScreen` | Platformni odvozenina `Vocabulary FR`; samostatny projekt jen pokud se bude aktivne rozvijet. |
| Webove slozky v `docs/` | Verejne vystupy projektu, ne zdrojove projekty samy o sobe. Vyjimkou je prakticky webovy zdroj MMTX, ktery je zatim v `docs/`. |

### Nepovazovat za projekt

Tyto oblasti jsou komponenty, sdilene zdroje, build vystupy nebo archiv.

| Polozka | Duvod |
| --- | --- |
| `Pict/` | Sdilena asset knihovna a mapping pro slovniky; projekt je az workflow kolem ni (`PictNew`). |
| `PictSource/` | Zdrojova/zalohova asset knihovna; vhodna k uklidu, ne projekt. |
| `assets/` | Sdilene audio/obrazky pro vice projektu. |
| `scripts/generate_tts.py`, `scripts/tts_gui.py` | Sdilena schopnost/tooling `TTS`, ne samostatna uzivatelska aplikace, pokud ji tak Mila neurci. |
| `build/`, `dist/`, build slozky v podprojektech | Generovane vystupy. |
| `tmp/`, `output/` | Docasne/pracovni vystupy. |
| `ZalohyPY/` | Archiv starsich kopii, ne zdroj pravdy. |

## Doporučený další postup mapovani

1. Vytvorit jednoduchy stavovy katalog s kategoriemi:
   `kanonicky projekt`, `varianta/vystup`, `sdilena schopnost`, `asset knihovna`,
   `archiv/generovane`, `docasne`.
2. Zalozit memory karty jen pro prijate kanonicke projekty, ktere jeste kartu
   nemaji a budou se realne udrzovat: `VocabularyFR`, `VocabularyIT`,
   `VocabularyES`, `VocabularyLA`, `ColorsAndNumbers`, `RestauracePTKL`,
   `ToBeTraining`, `Animals`, `AnimalsFilmPY`, pripadne `Sportka`.
3. Do `ACTIVE_PROJECTS.md` davat jen aktivni nebo rozpracovane oblasti, ne vsechny
   existujici projekty. Archivni a hotove veci patri do `PROJECTS.md` nebo memory
   indexu, ne do aktivnich priorit.
4. Pro kazdy aktivni projekt vybrat nejmensi uzitecne workflow:
   read-only audit, sync, build/test nebo otevreni aplikace.
5. Teprve potom pridavat do `app/workflows/commands.py`; bez registrace Samantha
   nesmi z lidske vety spoustet ad hoc shell.

Stav po potvrzeni: bod 1 je koncepcne potvrzeny, bod 3 je potvrzene pravidlo.
Nejblizsi implementace ma jit pres body 4 a 5 pro `PictNew` a `VocabularyEN`.

## Doporučeny tvar nove schopnosti

Kazda nova schopnost nebo workflow karta ma mit:

- lidsky zamer a priklady vet,
- typ: Python tool nebo shell workflow,
- ctene cesty,
- zapisovane cesty,
- co je vyslovne zakazane,
- potvrzovaci pravidlo,
- test nebo minimalni overeni.

Pro shell postupy plati: nejdrive pridat presny `argv` do
`Samantha_Agent/app/workflows/commands.py`, potom testy, az potom routovat
bezny lidsky pokyn na tento prikaz.

## Prioritni kandidati

1. `PictNew` workflow jako prvni nebackupovy workflow kandidat: prepare request, dry-run, potvrzene generovani davky, kopie schvalenych obrazku a mapping preview/apply.
2. `VocabularyEN` sync do `docs/` jako jednoduchy read/write workflow s jasnym
   vystupem.
3. `MultiLO` test workflow pro `py_compile` a existujici unit testy.
4. `TTS` davkovy workflow pro CSV -> MP3.
5. `Lekarna` read-only Python tool pro dotazy nad domaci evidenci.

## Bezpecnostni poznamky

- E-mailovy projekt je funkcne nejdal, ale je pozastaveny a citlivy.
- `Tax/`, `.env`, `Samantha_Agent/data/email/`,
  `Samantha_Agent/data/reminders/` a `Samantha_Agent/data/session_autosave/`
  jsou citlive oblasti.
- `PictNew` a image generation nesmi ukladat API klice do repo souboru.
- U lekarny nejde o lekarske doporuceni; odpoved musi vzdy rozlisit evidenci od
  davkovani a kontraindikaci.
- U vedeckych clanku se internet pouzije jen po dotazu, i kdyz by mohl doplnit
  metadata.
