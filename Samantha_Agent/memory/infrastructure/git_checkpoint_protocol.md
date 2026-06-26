# Git Checkpoint Protocol

Priorita: 1
Pripomenout pri startu: ano
Datum: 2026-05-20

## Ucel

Bezpecny postup pro checkpoint pred rizikovou praci, reconnect recovery nebo
dlouhou session.

V koreni `PythonMF` muze existovat rychla lidska nouzova karticka:

```text
Samantha_GIT_PUSH.txt
```

Je tam schvalne kvuli tomu, aby ji Mila rychle nasel, kdyz se Codex nebo VS Code
seka a nechce dlouze hledat v memory. Kanonicka pravidla ale zustavaji zde:
root karticka ma byt jen kratka pripominka a nesmi obchazet bezpecne git
principy.

## Pred rizikovym krokem

1. Zkontrolovat stav:

```bash
git status --short --branch
```

2. Spustit rutinni safety check:

```bash
.venv/bin/python scripts/git_safety_check.py
```

Tento check hlida nejen staged private/autosave/env soubory a velke binarni
soubory, ale nově i branch guard: vypise aktualni vetev a vetve, ktere nejsou
sloucene do `main`. Pokud ukaze smesnou nebo neintegrovanou vetev, nepokracovat
s predpokladem, ze `main` obsahuje vsechnu hotovou praci; nejdriv udelat audit,
samostatny cherry-pick nebo archivacni rozhodnuti.

3. Pokud jsou zmeny, rozlisit:

- vlastni zmeny aktualniho ukolu,
- starsi zmeny uzivatele,
- generovane nebo docasne soubory,
- citliva data, ktera nesmi do gitu.

4. Nepouzivat `git add .`.

Vyjimka: `git add .` pouzit jen tehdy, kdyz byl tesne predtim zkontrolovan
`git status --short --untracked-files=all` a je jasne, ze workspace neobsahuje
citlive, docasne ani nesouvisejici soubory. U Samanthy je bezpecny default
pridavat jen konkretni cesty.

## Commit

Commitovat jen konkretni soubory:

```bash
git add <soubor1> <soubor2>
git commit -m "Strucny popis"
```

Push:

```bash
git push origin main
```

Od 2026-06-26 plati osobni low-friction pravidlo pro Mílu:

```text
push na main po commitu smi probehnout bez dalsiho dotazu, pokud projde guard.
```

Pred rutinnim pushem spustit:

```bash
.venv/bin/python scripts/git_push_guard.py
```

Kdyz guard hlasi `OK routine push allowed: git push origin main`, muze Codex pri
bezne hotove praci pushnout `origin main` bez dalsiho rucniho potvrzeni. Je to
zamerne osobni rychly rezim, ne firemni compliance: ma neotravovat u beznych
checkpointu a brzdit jen veci, ktere se spatne vraci zpet.

Push bez dalsiho dotazu je zakazany a je potreba se zeptat, kdyz:

- nejde o vetev `main`,
- upstream neni `origin/main`,
- working tree neni cisty po commitu,
- vetev je za upstreamem,
- bezi merge/rebase/cherry-pick/revert,
- existuji nevyresene neintegrovane vetve mimo `main`,
- posledni commit obsahuje `data/private/`, `data/session_autosave/`, `.env`
  nebo podobne zakazane cesty,
- jde o force push, mazani vetve/tagu nebo prepis historie.

## Kdy checkpointovat

- Pred operaci, ktera prejmenovava nebo hromadne upravuje soubory.
- Pred spustenim workflow, ktere zapisuje do dat.
- Po dokonceni funkcniho mezikroku.
- Pred resenim reconnect/padove situace, pokud je workspace cisty nebo jasny.
- Pred zmenou tematu, kdyz Mila chce odskocit na dulezitejsi problem nebo napad.

## Pred zmenou tematu

Kdyz Mila rekne neco jako `zaparkuj soucasnou praci`, `ted odskocime na...`,
`nejdriv vyresime neco jineho` nebo se zjevne meni oblast prace, spustit:

```bash
.venv/bin/python scripts/work_context_guard.py
```

Guard je read-only a od 2026-06-26 se spousti automaticky pri startu Samanthy:

- ve vnejsim launcheru `scripts/samantha_codex.sh` jeste pred pripojenim do
  existujici `screen` session,
- uvnitr nove Codex session pres `scripts/samantha_screen_entry.sh`.

Pokud vnejsi launcher najde rozpracovanou praci, v interaktivnim terminalu pred
attachnutim vypise varovani a nabidne session zastavit. Pokud vnitrek nove Codex
session najde rozpracovanou praci, jeho vystup se preda i jako startovni prompt
Codexu, aby nova session nezacala nove tema bez checkpointu.

Guard hleda:

- jinou vetev nez `main`,
- staged, unstaged nebo untracked zmeny,
- nepushnute nebo chybejici upstream commity,
- rozbehnuty merge/rebase/cherry-pick/revert,
- neintegrovane vetve mimo `main`.

Pokud guard nehlasi cisty stav, nejdriv udelat maly checkpoint: commit/push hotove
casti, WIP vetev pro rozpracovanou praci, nebo handoff s presnym dalsim krokem.
Teprve potom menit tema.

## Zakazy

- Nepouzivat `git reset --hard` bez vyslovneho pokynu.
- Nepouzivat `git checkout --` na cizi zmeny.
- Nekommitovat `data/session_autosave/`.
- Nekommitovat tokeny, API klice, hesla ani cele citlive e-maily.
