Nazev: VocabularyFR Web Trainer pro Janu - checkpoint prototypu
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-06-04

## Co se resilo

Mila chce z desktopove Python/Tkinter aplikace `VocabularyFR/vocab_trainer_fr.py`
udelat pouzitelnou verzi pro Janu bez instalovaneho Pythonu. Jana si denne
pridava nova francouzska slovicka a ma take iPhone/Pythonista workflow, proto
nestaci jen staticka cteci stranka.

## Co je hotove

Webovy MVP prototyp vznikl v:

```text
VocabularyFR/web/
```

Spusteni lokalne:

```text
cd /Users/miloslavfalta/Desktop/PythonMF/VocabularyFR/web
python3 -m http.server 8788 --bind 127.0.0.1
```

URL:

```text
http://127.0.0.1:8788
```

Hotove funkce:

- CSV load/edit/export nad `VocabularyFR.csv`.
- Primy zapis do CSV v Chrome/Edge pres File System Access API, Safari fallback
  export.
- Vyhledavani, filtry, razeni.
- Treninkova karta FR/CZ s preklapenim.
- Lokalni audio cache pro francouzske slovo a cast vet.
- Obrazky pres `Pict/mapping.json` a fallbacky podle puvodni desktop logiky.
- Auto smycka: Start/Stop, nahodne/postupne, interval, slovo nebo slovo + veta.

Generator audia:

```text
VocabularyFR/generate_web_audio.py
```

Generator obrazku:

```text
VocabularyFR/prepare_web_pict_assets.py
```

Aktualni asset stav:

- `VocabularyFR/web/audio/fr_words/`: 193 `.m4a`, pokryva vsechna aktualni FR
  slovicka.
- `VocabularyFR/web/audio/fr_sentences/`: 127 `.m4a`.
- `VocabularyFR/web/pict/images/`: 174 obrazku.
- `VocabularyFR/web/pict/manifest.json`: mapping a seznam obrazku.
- Velikost `VocabularyFR/web/`: cca 39 MB.

Overeno:

```text
node --check ../VocabularyFR/web/app.js
CSV round-trip nad realnym VocabularyFR.csv: 206 rows
curl -I http://127.0.0.1:8788/app.js
curl -I http://127.0.0.1:8788/pict/manifest.json
curl -I http://127.0.0.1:8788/pict/images/plate.png
curl -I http://127.0.0.1:8788/audio/fr_words/assiette.m4a
```

Mila potvrdil:

- zakladni CSV funguje,
- audio koncept je v poradku, pokud funguje podle planu,
- obrazky se nacitaji,
- auto smycka funguje.

## Co neni hotove

- Staticky web neumí sam generovat kvalitni audio pro nove slovo/vetu.
- Prohlizecovy Web Speech hlas byl otestovan jako nepouzitelny fallback.
- Neni vyresene denni doplnovani novych slovicek Janou v zahranici bez servisniho
  zasahu Mily.
- Neni vyreseny iPhone/Pythonista sync.
- Neni rozhodnuto, jestli cil bude staticky web, macOS `.app`/helper, nebo
  server pres Tailscale.

## Navrhovane cesty reseni

### 1. Staticky web + servis u Mily

Jana dostane celou slozku `VocabularyFR/web/`. Pri novych slovech/vetach Mila
obcas vezme aktualni CSV a spusti:

```text
python3 VocabularyFR/generate_web_audio.py
python3 VocabularyFR/prepare_web_pict_assets.py
```

Vyhoda: jednoduche a uz rozpracovane.
Nevyhoda: neni idealni pro denni pridavani slov v zahranici.

### 2. Mala macOS aplikace bez Pythonu

Zabalit webove UI a lokalni helper tak, aby Jana nemusela mit Python, ale aplikace
umela lokalne volat macOS `say`/`afconvert` a dogenerovat audio hned pri pridani
slova/vety.

To je aktualne nejlepsi kandidat pro Janin Mac.

### 3. Samantha server / Tailscale

Jana by pouzivala web pres zabezpeceny pristup k Milovu Macu/serveru. Server by
ukladal CSV, generoval audio a spravoval obrazky.

Vyhoda: automaticke.
Nevyhoda: zavislost na dostupnem serveru a bezpecnem pristupu.

### 4. iPhone / Pythonista 3

iPhone verze by pravdepodobne mela zustat Pythonista aplikace nad stejnym CSV,
audio a obrazky by byly v Pythonista iCloud slozce.

Vikendovy test s Janou:

1. V Pythonista iCloud vytvorit `samantha_test.txt`.
2. Overit Files na iPhonu.
3. Overit Janin Mac.
4. Pripadne nasdilet Milovi.
5. Potom resit, zda jde spolecne pouzivat `VocabularyFR.csv`.

Pozor na iCloud konflikty pri soucasne editaci z Macu a iPhonu.

## Dalsi krok

Nejblizsi prakticky krok:

1. Dodelat maly deploy/checklist pro predani `VocabularyFR/web/` Jane.
2. Rozhodnout, zda dalsi technicka prace bude:
   - macOS `.app`/helper pro automaticke audio generovani bez Pythonu,
   - nebo Pythonista/iCloud test o vikendu.

## Zmenene nebo relevantni soubory

```text
VocabularyFR/web/index.html
VocabularyFR/web/styles.css
VocabularyFR/web/app.js
VocabularyFR/web/audio/
VocabularyFR/web/pict/
VocabularyFR/generate_web_audio.py
VocabularyFR/prepare_web_pict_assets.py
Samantha_Agent/memory/projects/vocabularyfr_web_trainer.md
Samantha_Agent/memory/handoffs/vocabularyfr_web_trainer_checkpoint_2026_06_04.md
```

## Bezpecnost / neukladat

- Necommitovat soukrome Janino pripadne budouci osobni CSV, pokud by obsahovalo
  citlive poznamky.
- Pred servisnim zasahem do Janina CSV delat zalohu.
- Nepribalovat nesouvisejici rozpracovane zmeny v Samantha memory/scripts.
