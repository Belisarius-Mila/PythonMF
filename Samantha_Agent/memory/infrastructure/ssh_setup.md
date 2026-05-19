# SSH Setup

Priorita: 2
Pripomenout pri startu: ne
Datum: 2026-05-20

## Ucel

Kratky operacni kontext pro praci pres SSH na Macu, hlavne pri navazovani Codex
session z iPhonu nebo jineho klienta.

## Zakladni workflow

- Pro navazani Codex prace pouzit prikaz `samantha`.
- `samantha` se ma pripojit do `screen` session `samantha_codex`.
- Pri vypadku SSH nemusi padnout bezici Codex; nejdrive zkusit znovu `samantha`.

Detailni pravidla:

```text
memory/technical/session_recovery_rules.md
```

## Rucni prikazy

```bash
screen -ls
screen -r samantha_codex
```

Odpojeni bez ukonceni:

```text
Ctrl+A, potom D
```

## Bezpecnost

Do memory neukladat privatni SSH klice, hesla, tokeny ani plnou citlivou SSH
konfiguraci.
