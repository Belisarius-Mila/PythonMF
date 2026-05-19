# Git Checkpoint Protocol

Priorita: 1
Pripomenout pri startu: ano
Datum: 2026-05-20

## Ucel

Bezpecny postup pro checkpoint pred rizikovou praci, reconnect recovery nebo
dlouhou session.

## Pred rizikovym krokem

1. Zkontrolovat stav:

```bash
git status --short --branch
```

2. Pokud jsou zmeny, rozlisit:

- vlastni zmeny aktualniho ukolu,
- starsi zmeny uzivatele,
- generovane nebo docasne soubory,
- citliva data, ktera nesmi do gitu.

3. Nepouzivat `git add .`.

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

## Kdy checkpointovat

- Pred operaci, ktera prejmenovava nebo hromadne upravuje soubory.
- Pred spustenim workflow, ktere zapisuje do dat.
- Po dokonceni funkcniho mezikroku.
- Pred resenim reconnect/padove situace, pokud je workspace cisty nebo jasny.

## Zakazy

- Nepouzivat `git reset --hard` bez vyslovneho pokynu.
- Nepouzivat `git checkout --` na cizi zmeny.
- Nekommitovat `data/session_autosave/`.
- Nekommitovat tokeny, API klice, hesla ani cele citlive e-maily.
