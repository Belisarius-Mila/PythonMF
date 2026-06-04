# Recovery karta: nový Mac + GitHub + záloha

Toto je krátký nouzový návod pro situaci:

```text
Původní Mac je pryč nebo nejde zapnout.
Mám nový Mac.
Mám GitHub repo PythonMF.
Mám externí zálohu SamanthaSecureBackup.
```

Nejdůležitější pravidlo: **nic nemaž a nic nepřepisuj naslepo**. Když si nejsi
jistý, nech existující složku stranou a obnovuj do nové.

## Co přežije

- Kód, weby, memory a handoffy přežijí na GitHubu, pokud byly commitnuté a
  pushnuté.
- Soukromá data mimo git přežijí v recovery záloze na externím disku.
- Codex/Adam se dá znovu navázat podle `AGENTS.md`, `memory/MEMORY_INDEX.md` a
  handoffů.
- Přihlášení, tokeny a hesla se znovu nastavují ručně. `auth.json` se
  nekopíruje.

## Co nedělat

- Nekopírovat `~/.codex/auth.json`.
- Neposílat obsah `.env`, hesla, tokeny ani app-specific passwords do chatu.
- Nemazat snapshoty záloh.
- Nepřepisovat existující `~/Desktop/PythonMF`, pokud už na novém Macu existuje.
  Nejprve ho přejmenovat stranou.

## 1. Připrav nový Mac

V Terminalu:

```bash
xcode-select --install
python3 --version
git --version
```

Nainstaluj nebo zprovozni:

- Codex CLI,
- VS Code nebo jiný editor,
- Python 3.12 nebo kompatibilní Python 3.

Pak se znovu přihlas do Codexu:

```bash
codex login
```

## 2. Získej nejnovější kód z GitHubu

```bash
mkdir -p "$HOME/Desktop"
cd "$HOME/Desktop"
git clone https://github.com/Belisarius-Mila/PythonMF.git
cd "$HOME/Desktop/PythonMF/Samantha_Agent"
```

Přečti základní instrukce:

```bash
sed -n '1,220p' AGENTS.md
sed -n '1,220p' memory/MEMORY_INDEX.md
sed -n '1,220p' RECOVERY_CARD_NEW_MAC.md
```

## 3. Připoj externí zálohu

Připoj externí disk `Falta`.

Najdi a otevři šifrovaný kontejner:

```bash
open "/Volumes/Falta/SamanthaSecureBackup.sparsebundle"
```

Po zadání hesla má vzniknout svazek:

```text
/Volumes/SamanthaSecureBackup
```

Ověření:

```bash
ls -la "/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots"
```

Poslední známý úspěšný snapshot k 2026-06-04:

```text
20260603_175327
```

## 4. Najdi poslední recovery snapshot

```bash
SNAPSHOT="/Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots/$(ls -1 /Volumes/SamanthaSecureBackup/SamanthaBackups/snapshots | tail -1)"
echo "$SNAPSHOT"
cat "$SNAPSHOT/backup_manifest.txt"
```

V manifestu hledej:

```text
Profile: recovery
```

Pokud je tam `safe`, obnova nebude obsahovat všechna soukromá data.

## 5. Nejjednodušší obnova celé složky PythonMF

Pokud už na novém Macu existuje `~/Desktop/PythonMF`, nejdřív ji odlož:

```bash
mv "$HOME/Desktop/PythonMF" "$HOME/Desktop/PythonMF_before_restore_$(date +%Y%m%d_%H%M%S)"
```

Potom obnov celý projekt ze snapshotu:

```bash
rsync -a "$SNAPSHOT/PythonMF/" "$HOME/Desktop/PythonMF/"
```

Tím se obnoví i soukromá lokální data, pokud snapshot byl `recovery`.

## 6. Dostaň kód na nejnovější GitHub stav

Snapshot může být starší než poslední commit. Po obnově proto zkus:

```bash
cd "$HOME/Desktop/PythonMF"
git status --branch --short
git pull origin main
```

Pokud `git pull` hlásí konflikt nebo lokální změny, zastav se a napiš Codexu:

```text
Obnovuji Samanthu po ztrátě Macu. Jsem ve složce ~/Desktop/PythonMF.
Přečti Samantha_Agent/AGENTS.md, Samantha_Agent/memory/MEMORY_INDEX.md
a Samantha_Agent/RECOVERY_CARD_NEW_MAC.md. Nic nemaž a nepřepisuj bez potvrzení.
Pomoz mi bezpečně dokončit obnovu a vyřešit git status.
```

## 7. Obnov Codex pomocná data, ale ne přihlášení

Pokud snapshot obsahuje `codex_home/`:

```bash
mkdir -p "$HOME/.codex"
rsync -a "$SNAPSHOT/codex_home/" "$HOME/.codex/"
rm -f "$HOME/.codex/auth.json"
codex login
```

Pokud `codex_home/` chybí, nevadí. Codex se nastaví novým přihlášením.

## 8. Obnov Python prostředí

```bash
cd "$HOME/Desktop/PythonMF/Samantha_Agent"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Pokud `.env` chybí, vytvoř ho ručně:

```bash
cp .env.example .env
```

Potom ho doplň ručně. Obsah `.env` nepatří do chatu ani do gitu.

## 9. Ověř, že Samantha žije

```bash
cd "$HOME/Desktop/PythonMF/Samantha_Agent"
source .venv/bin/activate
.venv/bin/python scripts/backup_status.py
.venv/bin/python -m unittest tests.test_cockpit
```

Spusť Cockpit:

```bash
scripts/start_cockpit.sh
```

Otevři:

```text
http://127.0.0.1:8770
```

V Cockpitu zkontroluj:

- `Recovery centrum`,
- `Diagnostika`,
- `Dokumentový intake`,
- `Git`,
- `Záloha`.

## 10. Když nemáš externí zálohu

Pořád lze obnovit kód:

```bash
cd "$HOME/Desktop"
git clone https://github.com/Belisarius-Mila/PythonMF.git
```

Ale bez recovery zálohy budou chybět soukromá lokální data mimo git:

- `data/private/`,
- e-mailové lokální archivy,
- reminders,
- `.env`,
- případná data v `Tax/` a dalších ignorovaných složkách.

## 11. Po úspěšné obnově

Nejdřív ověř funkčnost. Teprve potom udělej novou recovery zálohu.

Bezpečný začátek je dry-run:

```bash
cd "$HOME/Desktop/PythonMF/Samantha_Agent"
.venv/bin/python scripts/backup_samantha_python.py --dry-run --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups
```

Ostrou zálohu spouštěj až po kontrole cíle a potvrzení:

```bash
.venv/bin/python scripts/backup_samantha_python.py --execute --profile recovery --target /Volumes/SamanthaSecureBackup/SamanthaBackups --progress-every 5000
```

## 12. Jedna věta pro nového Codexe

Když na novém Macu otevřeš Codex, napiš mu:

```text
Jsem Míla a obnovuji Samanthu po ztrátě Macu. Pracuj česky.
Jsme ve složce ~/Desktop/PythonMF/Samantha_Agent.
Nejprve přečti AGENTS.md, memory/MEMORY_INDEX.md,
RECOVERY_CARD_NEW_MAC.md a RECOVERY_FROM_BACKUP.md.
Nic nemaž, nic nepřepisuj bez potvrzení a nikdy neukládej hesla ani tokeny.
Pomoz mi zkontrolovat git, zálohu, Python prostředí a spustit Cockpit.
```
