# Navrh: opakovatelny systemovy audit projektu, toolu a vrstev

Datum: 2026-06-23
Stav: implementováno; pojistka driftu projektové paměti doplněna 2026-08-07
Navazuje na: `memory/reports/systemovy_audit_projekty_tooly_vrstvy_2026_06_23.txt`

## Cil

Vytvorit opakovatelny report, ktery na jeden prikaz sestavi aktualni orientacni
mapu Samanthy:

- co je dnes priorita,
- kde je provozni riziko,
- ktere projekty/tooly/vrstvy jsou aktivni,
- kde jsou mezery v registry nebo workflow,
- jaky je nejmensi rozumny dalsi krok.

Report ma byt kratky lidsky itinerar, ne kompletni export pameti.

## Navrzeny nazev

Lidsky nazev:

```text
Systemovy audit projektu, toolu a vrstev
```

CLI:

```text
.venv/bin/python scripts/samantha_project_audit.py --mode quick
.venv/bin/python scripts/samantha_project_audit.py --mode full
.venv/bin/python scripts/samantha_project_audit.py --mode full --save
```

Samantha tool:

```text
samantha_project_audit(mode="quick", save=False)
```

Vystup pri `--save`:

```text
memory/reports/systemovy_audit_projekty_tooly_vrstvy_YYYY_MM_DD.txt
```

Pokud uz stejny den existuje report se zakladnim nazvem, generator ho nesmi
prepsat. Dalsi ulozeni dostane casovou priponu:

```text
memory/reports/systemovy_audit_projekty_tooly_vrstvy_YYYY_MM_DD_HHMMSS.txt
```

## Bezpecnostni hranice

Generator smi cist:

- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `memory/technical/project_capability_map.md`
- `memory/technical/system_reports.md`
- `app/system_reports.py`
- vystupy bezpecnych reportu: health, quantitative, capability, backup status
- git metadata pres `git status --short --branch`

Generator nesmi cist:

- `data/private/`
- cela tela e-mailu,
- soukrome dokumenty,
- fulltexty clanku v article archive,
- private ChatGPT exporty,
- tokeny, `.env`, app-specific passwords,
- soubory v `data/session_autosave/` krome agregovaneho stavu pres existujici
  autosave/status nastroj, pokud bude pozdeji pridany.

Generator nesmi delat:

- zadne presuny, mazani, importy, archivy, oznacovani hotovo,
- zadne automaticke commity,
- zadne cteni webu,
- zadne posilani e-mailu nebo zprav,
- zadne doplnovani soukromych detailu do reportu.

`--save` smi zapsat jen git-safe report do `memory/reports/`.

## MVP rozsah

Prvni verze ma byt deterministicka a jednoducha. Nebude pouzivat LLM k
vymysleni textu; jen parsuje existujici bezpecne soubory a sklada sablonovy
report.

MVP sekce:

1. Hlavicka
   - nazev, datum, mode, zdroje, bezpecnost.

2. Provozni stav
   - backup status,
   - git summary,
   - pocet aktivnich `[PRIPOMENOUT]`,
   - top health warnings,
   - capability gap count,
   - quantitative file/line summary.

3. Rychle doporuceni
   - 3 az 5 kratkych bodu podle pravidel:
     - dirty git nad prah -> git cleanup jako prvni,
     - backup starsi nez 3 dny -> backup jako prvni,
     - mnoho `[PRIPOMENOUT]` -> cleanup pameti,
     - capability gaps -> registry cleanup,
     - jinak prvni aktivni priority 1/A1 projekt.

4. Priorita 1
   - aktivni radky z `ACTIVE_PROJECTS.md` s prioritou `A1+`, `A1`, `1`,
     nebo textem `[PRIPOMENOUT]` v navazanem memory/handoff odkazu.
   - u kazde polozky: oblast, typ odhadnuty z nazvu, stav, dalsi krok.

5. Priorita 2
   - aktivni radky s prioritou `2` a vybrane paused polozky s jasnym dalsim
     krokem.

6. Priorita 3
   - priorita `3`, archivni udrzba, zastarale pripominky, historicke recovery
     veci.

7. Tooly a schopnosti
   - prebrat agregaci z `app.capability_audit.format_samantha_capability_audit()`,
     ale do reportu ulozit jen souhrn a mezery, ne dlouhou tabulku pri quick.

8. Vrstvy
   - staticka mapa vrstev v kodu:
     - lidska orientacni vrstva,
     - provozni/recovery vrstva,
     - Cockpit UI vrstva,
     - private data vrstva,
     - knowledge vrstva,
     - mobile/voice vrstva,
     - workflow registry vrstva,
     - kreativni/edukacni aplikacni vrstva.
   - u kazde vrstvy kratky stav odvozeny z dostupnych signalu.

9. Zaver
   - 3 silne stranky,
   - 3 rizika,
   - jeden nejmensi dalsi krok.

## Full mode

`--mode full` muze pridat:

- vsechny aktivni projekty z `ACTIVE_PROJECTS.md`,
- plne health warnings,
- plny seznam capability areas,
- seznam starych `[PRIPOMENOUT]` kandidatu k odsumeni,
- odkazy na relevantni handoffy bez cteni private obsahu.

Full mode stale nesmi cist private data.

## Datovy model v kodu

Navrzeny modul:

```text
app/project_audit_report.py
```

Navrzene datove struktury:

```python
@dataclass(frozen=True)
class ProjectAuditResult:
    created_at: str
    mode: str
    git_summary: str
    backup_summary: str
    reminder_count: int
    health_warnings: tuple[str, ...]
    quick_recommendations: tuple[str, ...]
    priority_1: tuple[ProjectAuditItem, ...]
    priority_2: tuple[ProjectAuditItem, ...]
    priority_3: tuple[ProjectAuditItem, ...]
    capability_summary: CapabilityAuditSummary
    layers: tuple[AuditLayer, ...]
    saved_path: Path | None

@dataclass(frozen=True)
class ProjectAuditItem:
    name: str
    priority: str
    lifecycle: str
    memory: str
    handoff: str
    status: str
    next_step: str
    inferred_type: str
```

Hlavni funkce:

```python
run_samantha_project_audit(mode="quick", save=False) -> ProjectAuditResult
format_samantha_project_audit(mode="quick", save=False) -> str
save_samantha_project_audit(result) -> Path
```

## Heuristiky priority

Zakladni razeni:

1. explicitni priorita `A1+`, `A1`, `1`,
2. provozni blokery: dirty git, stara zaloha, vysoky pocet `[PRIPOMENOUT]`,
3. projekty s aktualnim handoffem z poslednich 7 dni,
4. projekty s jasnym dalsim krokem,
5. paused/archive az nakonec.

Generator nema odhadovat procenta rozpracovanosti jako pravdu. Pokud se procenta
v reportu zachovaji, maji byt volitelna a rucne udrzovana v ACTIVE_PROJECTS
nebo oddelene konfiguraci. MVP je nebude pocitat.

## Kam zaregistrovat po schvaleni

Po schvaleni implementace pridat:

1. `app/project_audit_report.py`
2. `scripts/samantha_project_audit.py`
3. tool wrapper v `app/samantha_agent.py`
4. zaznam v `app/system_reports.py`
5. zaznam v `memory/technical/system_reports.md`
6. zaznam v `memory/technical/capability_routing_rules.md`
7. podle potreby zaznam ve `memory/technical/workflow_command_registry.md`
8. testy:
   - `tests/test_project_audit_report.py`
   - aktualizace `tests/test_system_reports.py`

## Testy

Minimalni testy:

1. Parser `ACTIVE_PROJECTS.md` rozpozna aktivni vs archivni radky.
2. Report v quick modu obsahuje provozni stav, priority, tool gap a vrstvy.
3. Report nevypisuje soukrome blokovane cesty typu `data/private`.
4. `save=True` vytvori soubor v `memory/reports/` s datem.
5. `save=False` nic nezapisuje.
6. Pokud uz stejny den existuje report, dalsi `save=True` ho neprepisuje a
   pouzije casovou priponu.
7. System report registry obsahuje novy report a ma unikatni nazvy.
8. Pri dirty git vznikne doporuceni na git cleanup.
9. Pri backup warningu vznikne doporuceni na backup.

## Prvni implementacni krok

Nejmensi uzitecny krok:

1. Vytvorit `app/project_audit_report.py` s parserem `ACTIVE_PROJECTS.md` a
   `MEMORY_INDEX.md`.
2. Vygenerovat quick report do stdout bez `--save`.
3. Pridat testy parseru a quick vystupu.

Az potom:

4. Pridat `--save`.
5. Zaregistrovat jako systemovy report.
6. Pridat Samantha tool.
7. Teprve nakonec resit full mode a Cockpit tlacitko.

## Co zatim nedelat

- Nedelat LLM sumarizaci soukromych souboru.
- Nedelat webove overovani.
- Nedelat automaticke prepisovani `ACTIVE_PROJECTS.md`.
- Nedelat automaticke ruseni `[PRIPOMENOUT]`.
- Nedelat commit/push jako vedlejsi efekt reportu.
- Nedelat Cockpit UI pred tim, nez CLI report projde testy.

## Navrzeny lidsky trigger

Bezny dotaz:

```text
Udelej aktualni systemovy audit.
```

Mapovani:

```text
samantha_project_audit(mode="quick", save=False)
```

Ulozeni:

```text
Uloz aktualni systemovy audit.
```

Mapovani:

```text
samantha_project_audit(mode="full", save=True)
```

Pred ulozenim neni potreba specialni potvrzeni, protoze jde o git-safe report
do `memory/reports/`. Potvrzeni bude potreba az u navazujicich akci, ktere by
menily data, commitovaly nebo spoustely shell workflow.

## Doplnění 2026-08-07: pojistka proti zastaralému agregátu

Audit 2026-08-07 ukázal, že automatické checkpointy aktualizují kanonický
handoff a TVBCP, ale ne vždy také souhrnný `ACTIVE_PROJECTS.md`. Terminálové
commity navíc nemusí aktualizovat žádnou projektovou paměť, pokud daný krok
výslovně neuzavírá projektový checkpoint. Systémový audit proto mohl převzít
starý řádek agregátu a vydat jej za dnešní stav.

Generátor nyní před sestavením reportu spouští read-only audit autority paměti.
Porovná poslední Git timestamp `ACTIVE_PROJECTS.md` s kanonickým handoffem a
TVBCP každého materializovaného proudu. Pokud je kanonická dvojice novější:

- report viditelně uvede počet a názvy dotčených proudů;
- doporučí nejprve synchronizovat `ACTIVE_PROJECTS.md`;
- starý agregovaný stav už nepředstaví bez varování jako spolehlivě aktuální.

Jde o diagnostickou pojistku, nikoli automatický přepis paměti. Audit stále nic
nemění, nemaže ani nezakládá TVBCP pro lazy proudy. Trvalým provozním pravidlem
je při významném projektovém checkpointu dorovnat v jednom kroku kanonický
handoff, TVBCP a odpovídající řádek `ACTIVE_PROJECTS.md`; uzavřeným historickým
handoffům současně odebrat `[PRIPOMENOUT]`.
