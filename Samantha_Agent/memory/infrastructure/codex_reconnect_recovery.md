# Codex Reconnect Recovery

Priorita: 1
Pripomenout pri startu: ano
Datum: 2026-05-20

## Ucel

Postup pro navazani prace po vypadku SSH, reconnect loopu, padu Codexu nebo
zaseknuti streamu.

Detailni pravidla jsou v:

```text
memory/technical/session_recovery_rules.md
```

## Zakladni pravidlo

Nejdriv zjistit, co je realne rozpracovane:

```bash
git status --short --branch
git --no-pager log -3 --oneline --decorate
```

Pak cist relevantni memory:

```text
memory/MEMORY_INDEX.md
memory/ACTIVE_PROJECTS.md
memory/handoffs/
```

## Po vypadku SSH

Pouzit:

```bash
samantha
```

Pokud prikaz neni znamy:

```bash
source ~/.zshrc
samantha
```

Rucne:

```bash
screen -ls
screen -r samantha_codex
```

## Po padu Codexu

Pouzit:

```bash
codex resume --last
```

nebo konkretni session ID:

```bash
codex resume <SESSION_ID>
```

## Pri zaseknutem nastroji

- Zkontrolovat, zda stale bezi proces, ktery Codex spustil.
- Ukoncit jen vlastni diagnosticky proces, ne uzivatelske aplikace.
- Nepouzivat destruktivni git prikazy.
- Pred dalsi praci shrnout, co je rozpracovane a co bylo overeno.

## Bezpecnost

Autosave v `data/session_autosave/` je nouzovy log a nesmi se commitovat.
