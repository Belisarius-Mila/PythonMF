# Capability routing rules

Zalozeno 2026-05-19.

## Smysl

Samantha ma prijimat bezne lidske pokyny a prevadet je na bezpecne registrovane
schopnosti. Toto pravidlo plati pro vsechny soucasne i budouci projekty.

## Obecny postup

1. Pochopit zamer z bezne cestiny.
2. Pojmenovat, jak Samantha pokyn pochopila.
3. Vybrat registrovanou schopnost/tool/workflow.
4. Strucne rict bezpecnostni rozsah:
   - co bude cist,
   - co bude zapisovat,
   - co urcite nebude delat.
5. Pokud jde o zapis, obnovu, odesilani, mazani, citlive cteni nebo shellovy
   workflow prikaz, vyzadat potvrzeni podle pravidel dane schopnosti.
6. Spustit pouze registrovanou schopnost, ne ad hoc improvizovany prikaz.

## Volba miry rezie

Pred novym ukolem ma Samantha nebo Codex zvolit primerenou miru workflow rezie:

- maly, rychly a snadno opakovatelny ukol: primy krok bez manifestu,
- stredni ukol s vice soubory nebo vystupy: lehky manifest/log/summary,
- dlouhy, sitove citlivy, hromadny, drahy nebo soukromy ukol: plne
  checkpointovane workflow podle `memory/technical/session_recovery_rules.md`.

Cilem je nepretezovat male ukoly zbytecnou strukturou, ale u delsi prace mit
navazatelnost po reconnectu, padu Codexu nebo castecne chybe.

## Typy schopnosti

### Python tools

Pouzivat pro bezpecne aplikacni operace uvnitr Samanthy, napr. e-maily,
reminders, memory, lokalni vaulty a obnovu souboru.

Tool musi mit vlastni bezpecnostni pravidla a testy. Pokud pracuje s citlivymi
daty, musi mit potvrzovaci gate.

### System reports

Pouzivat pro kratke ad hoc systemove prehledy, ktere Mila potrebuje spustit
opakovaně a nechce si pamatovat jejich presne nazvy.

Aktualni registrovane reporty:

| Zamer v bezne reci | Registrovana schopnost | Bezpecnostni rozsah |
| --- | --- | --- |
| "Jaky je stav Samanthy?", "health check", "mame cisty stul?" | `samantha_health_check(mode="quick")` | cte memory index, aktivni projekty a git status; nezapisuje |
| "Kvantitativni status", "kolik mame souboru/radku?", "objemovy rust" | `samantha_quantitative_status(save=False)` | cte agregovane souborove statistiky mimo soukroma data; bez `save=True` nezapisuje |
| "Uloz kvantitativni snapshot" | `samantha_quantitative_status(save=True)` | ulozi jen agregovanou JSONL datovou vetu bez nazvu souboru a soukromeho obsahu |
| "Jake mame systemove reporty?" | `samantha_system_reports()` | vypise registr reportu; nezapisuje |
| "Co Samantha umi?", "audit schopnosti", "kde jsou workflow rezervy?" | `samantha_capability_audit()` | cte registr toolu a workflow; nezapisuje |
| "Udelej aktualni systemovy audit", "audit projektu/toolu/vrstev", "na cem dnes navazat?" | `samantha_project_audit(mode="quick", save=False)` | cte jen git-safe pametove registry a systemove reporty; necte private vault, e-maily ani soukrome dokumenty |
| "Uloz aktualni systemovy audit" | `samantha_project_audit(mode="full", save=True)` | zapise git-safe textovy report do `memory/reports/`; bez private obsahu |
| "Co je v knowledge inboxu?", "velke podklady", "archiv chatu k prostudovani" | `samantha_knowledge_inbox_inventory()` | vypise jen metadata souboru v private inboxu; necte obsah |
| "Co mam ve Stazenych pro knowledge inbox?", "najdi podklady v Downloads" | `samantha_downloads_inventory()` | vypise jen metadata top-level souboru ve Stazenych; necte obsah |
| "Prekopiruj vybrane soubory ze Stazenych do knowledge inboxu" | `copy_downloads_files_to_knowledge_inbox(...)` | kopiruje jen vybrane relativni soubory z Downloads do private inboxu az po potvrzeni |
| "Chci iPhone zkratku", "vytvor Apple Shortcut", "stav Shortcuts Playground" | `iphone_shortcuts_playground_status()` nebo `prepare_iphone_shortcut(...)` | status je read-only; private request draft se zapisuje az po potvrzeni a realny `.shortcut` se musi rucne overit |
| "Stav pameti", "priority", "pripomenuti" | `memory_status()` | cte jen bezpecnou lokalni memory diagnostiku; nezapisuje |

Kdyz pri praci vznikne novy opakovatelny ad hoc status, audit nebo report,
Samantha se ma zeptat: "Udelame z toho novy systemovy report?" Pokud Mila
souhlasi, pridat ho do `app/system_reports.py`, `memory/technical/system_reports.md`
a podle potreby do testu.

### Shell workflow registry

Pouzivat pro lokalni prikazy, ktere maji byt spoustene pres shell, napr. zaloha,
build, export, audit nebo davkovy projektovy skript.

Shell workflow musi byt registrovany v:

```text
Samantha_Agent/app/workflows/commands.py
```

Samantha smi spustit jen presne ulozene `argv`. Pred zapisujicim workflow ma
ukazat presny shell a cekat na potvrzeni.

## Priklady

Pokyn:

```text
Najdi e-maily za poslednich 7 dni.
```

Samantha ma odpovedet ve smyslu:

```text
Chapu to jako bezpecny vypis e-mailovych hlavicek za poslednich 7 dni.
Pouziji read-only e-mailovy tool. Prectu jen UID, datum, odesilatele a predmet.
Nebudu cist tela, otevirat odkazy, stahovat prilohy, mazat, presouvat ani
oznacovat jako prectene.
```

Pevny rychly vstup:

```text
Prosím přehled emailů za posledních 7 dní
```

Samantha ho ma mapovat na sjednoceny read-only prehled iCloud + Seznam za
poslednich 7 dni. Vychozi razeni: hlavne zpravy s PDF prilohami nebo signalem
dokumentu/prilohy; kategorie `faktury/e-shopy`, `pojisteni/smlouvy`,
`urady/dane`, `ostatni`; vystup jen hlavicky a kratky duvod dulezitosti.
Bez dalsiho potvrzeni necist cela tela, nestahovat prilohy, neotevirat odkazy,
neukladat PDF, nic neposilat, nemazat, nepresouvat ani neoznacovat jako prectene.

Pokyn:

```text
Zalohuj data projektu.
```

Samantha ma odpovedet ve smyslu:

```text
Chapu to jako recovery zalohu PythonMF/Samantha na externi disk.
Spustila bych tento presny shell prikaz: ...
Potvrzujes spusteni?
```

## Bezpecnostni pravidla

- Nikdy nemapovat lidsky pokyn primo na libovolny shell.
- Pokud neni zamer jasny, zeptat se kratce, misto spusteni.
- Pokud existuje vice kandidatu, vypsat je a nechat Milu vybrat.
- U e-mailu nerozsirovat rozsah cteni bez potvrzeni.
- U obnovy souboru vzdy nejdriv preview, potom potvrzeni.
- U backupu a jinych shell workflow nejdriv ukazat presny prikaz, potom cekat
  na potvrzeni.
- Nove projekty maji pri pridani automatizace dostat bud Python tool, nebo
  shell workflow kartu; ne skryty ad hoc postup.
