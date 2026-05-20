# Webova aplikace Lekarna - hotovo, udrzba priorita 2

Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-05-20

## Co se resilo

- Uzavreni projektu webove aplikace Lekarna po uspesnem verejnem provozu.
- Aplikace je publikovana na GitHub Pages, pouziva sifrovany datovy balik a heslo se neuklada.
- Posledni ladeni ChatGPT fallbacku: na Macu muze prohlizec ignorovat otevreni nove zalozky, proto je v aplikaci kopirovaci fallback.

## Co je hotove

- Verejny web: `https://belisarius-mila.github.io/PythonMF/lekarna/`
- Cockpit stare lekarny, heslova brana/dešifrovani, tri krabicky, hadi dotaz a MP3 napoveda.
- Skutecna data, fotky a `PIL_Short` jsou v sifrovanem baliku `docs/lekarna/encrypted-data/lekarna.enc.json`.
- Nesifrovany export `docs/lekarna/private-data/` zustava ignorovany a necommitovany.
- ChatGPT fallback ma viditelny panel s pripravenym dotazem, tlacitko pro zkopirovani, obycejny odkaz na ChatGPT a instrukci pro `Cmd+klik` nebo prave tlacitko.
- Posledni commit/push verejne aplikace: `954b98b Add pharmacy GPT copy fallback`.

## Co neni hotove

- Zadny urgentni vyvoj neni otevreny.
- Budouci rozvoj je priorita 2, az bude cas nebo novy urgentni pozadavek.
- Pri zmene CSV/fotek je nutne znovu udelat export, sifrovani a cilene commitnout novy encrypted bundle.

## Dalsi krok

- Bez dalsiho aktivniho vyvoje.
- Pri novem pozadavku nejdrive precist tento handoff a `Samantha_Agent/memory/projects/lekarna_web_app.md`.
- Pokud se zmeni data, spustit lokalne:

```bash
cd /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent
.venv/bin/python scripts/export_lekarna_web_private_data.py
.venv/bin/python scripts/encrypt_lekarna_web_bundle.py
```

- Heslo zadat pouze do lokalniho skryteho promptu.
- Potom cilene commitnout `docs/lekarna/encrypted-data/lekarna.enc.json`.

## Zmenene nebo relevantni soubory

- `docs/lekarna/index.html`
- `docs/lekarna/styles.css`
- `docs/lekarna/app.js`
- `docs/lekarna/assets/lekarna-cockpit.png`
- `docs/lekarna/assets/ipl-short.png`
- `docs/lekarna/audio/lekarna-help-intro.mp3`
- `docs/lekarna/encrypted-data/lekarna.enc.json`
- `Samantha_Agent/memory/projects/lekarna_web_app.md`
- `Samantha_Agent/scripts/export_lekarna_web_private_data.py`
- `Samantha_Agent/scripts/encrypt_lekarna_web_bundle.py`

## Bezpecnost / neukladat

- Neukladat heslo do chatu, memory, dokumentace ani gitu.
- Neukladat hash hesla.
- Necommitovat `docs/lekarna/private-data/`.
- Necommitovat `Samantha_Agent/data/lekarna/`.
- Web nesmi radit davkovani ani nahrazovat lekare nebo lekarnu.
