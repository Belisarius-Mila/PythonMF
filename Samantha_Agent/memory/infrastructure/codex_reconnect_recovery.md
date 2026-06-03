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

## Network preflight pri startu

`scripts/samantha_codex.sh` spousti `scripts/network_preflight.sh` pred pripojenim
ke `screen` relaci. Preflight kontroluje:

- bezici zname VPN/Tailscale procesy,
- pocet `utun` tunelovych rozhrani,
- IPv4 adresu na Wi-Fi rozhrani,
- zakladni ping na IP a DNS jmeno.

Vychozi rezim jen diagnostikuje a nic nevypina.

Pro pokus o ukonceni znamych VPN procesu pred startem lze pouzit:

```bash
source ~/.zshrc
SAMANTHA_DISABLE_VPN=1 samantha
```

nebo primo:

```bash
~/Desktop/PythonMF/Samantha_Agent/scripts/samantha_clean.sh
```

Preflight lze nouzove preskocit:

```bash
SAMANTHA_PREFLIGHT=0 samantha
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

## [PRIPOMENOUT] Cockpit Recovery centrum

Priorita 1 pro pristi praci na Cockpitu: pridat read-only Recovery centrum pro
navazani po padu Samanthy/Codexu. Cilem je, aby Mila nemusel lovit terminalovy
postup v pameti.

Minimalni obsah:

- posledni autosave timestamp z `data/session_autosave/` bez vypisu citliveho
  obsahu logu,
- kratke git status summary,
- posledni relevantni handoff nebo odkaz na `MEMORY_INDEX.md`,
- doporuceny dalsi prikaz: `samantha`, pripadne `codex resume --last`,
- jasne upozorneni, ze recovery panel je read-only a nic neprepisuje.

Kanonicky handoff:

```text
memory/handoffs/cockpit_recovery_center_priority_2026_06_03.md
```

## Pravidlo pro dlouhe ukoly pri nestabilnim spojeni

Pri opakovanych reconnectech nepokracovat dlouhymi interaktivnimi tool cally.
Dlouhe prace spoustet jako samostatne skripty s logem a stavovym vystupem.

Konkretne:

- pred dlouhym ukolem spustit `samantha` nebo pri problemech `SAMANTHA_DISABLE_VPN=1 samantha`,
- dlouhe davky psat do skriptu v `scripts/` nebo projektove lokalni slozce,
- prubeh zapisovat do `logs/` nebo soukrome pracovni slozky,
- vystupy delat navazovatelne a opakovatelne,
- po reconnectu nejdriv precist vystupni soubor/log a az potom pokracovat.

To plati hlavne pro videa, media importy, exporty, sifrovani balicku a hromadne
operace nad soubory.

## Bezpecnost

Autosave v `data/session_autosave/` je nouzovy log a nesmi se commitovat.
