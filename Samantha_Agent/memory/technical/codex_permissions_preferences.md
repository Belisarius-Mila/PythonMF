# Codex: preference pro povolovani prikazu

## Kontext

Mila chce pri rutinnich ukolech omezit opakovane dotazy na povoleni, hlavne pri praci na webovych aplikacich v repozitari `PythonMF`.

Tento soubor neni technicke oprávneni samo o sobe. Skutecna povoleni uklada a vynucuje Codex CLI / Codex UI. Pamet slouzi jen jako pripominka, jaka povoleni ma Codex navrhovat pri dotazech na potvrzeni.

## Doporuceny start Codexu

Pro ukoly nad vice podslozkami repozitare spoustet Codex z korene:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF
codex
```

Tim se omezi dotazy na zapis mimo `Samantha_Agent`, protoze `docs/`, `ColorsAndNumbers/` a dalsi projektove slozky budou v pracovnim prostoru.

## Bezpecne rutinni prikazy k navrzeni pro Always allow

Pri vhodne prilezitosti navrhnout trvale povoleni pro:

```text
python3 -m edge_tts
git -C /Users/miloslavfalta/Desktop/PythonMF add
git -C /Users/miloslavfalta/Desktop/PythonMF commit -m
git -C /Users/miloslavfalta/Desktop/PythonMF push origin main
```

Pouziti:

- `python3 -m edge_tts` pro generovani ceskych MP3 audii.
- `git add`, `git commit`, `git push` pro standardni publikaci hotovych zmen.

## Co automaticky nepovolovat

Nenavrhovat trvale povoleni pro destruktivni nebo prilis siroke prikazy:

```text
rm
git reset
git checkout -- ...
python3
python
```

Mazani souboru, reset historie a podobne kroky ma Mila potvrzovat vzdy rucne.

## Poznamka ke GitHub push

Pokud `git push` selze chybou macOS keychainu typu:

```text
failed to get: -25308
fatal: could not read Username for 'https://github.com': Device not configured
```

nejde o chybejici Codex povoleni, ale o problem s GitHub prihlasenim v lokalnim credential helperu. Prakticky dalsi krok je spustit push z normalniho Terminalu nebo opravit GitHub prihlaseni.
