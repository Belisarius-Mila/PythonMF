Nazev: VocabularyFR pro Janu - archiv oprav appky, obrazku a mappingu
Priorita: 2
Stav: archiv
Pripomenout pri startu: ne
Datum: 2026-06-07

Co se resilo:
- Jana pouziva VocabularyFR data ve sdilene iCloud slozce `PythonMF`.
- Po doplneni CSV, obrazku a mappingu aplikace nejdriv cast obrazku nevidela.
- Ukazalo se, ze macOS `.app` je PyInstaller build a musi hledat externi `PythonMF/Pict`.
- Nasledne zustalo mnoho fallbacku, protoze nove vygenerovane obrazky byly fyzicky v `Pict`, ale chybely mappingy.
- Nakonec byla odhalena zamenena dvojice `school.PNG` / hospital.

Co je hotove:
- Janin `VocabularyFR.csv` ma doplnene prikladove francouzske vety a ceske preklady u chybejicich radku.
- Chybejici obrazky z naseho `Pict` byly zkopirovane do Janina iCloud `PythonMF/Pict`.
- Vygenerovano a schvaleno 39 novych obrazku pro francouzska slovicka.
- Nove obrazky byly zkopirovane do naseho i Janina `Pict`.
- Janin `Pict/mapping.json` byl doplnen o existujici i nove mappingy.
- Finální audit po opravach:
  - CSV radku: 347
  - mapping zaznamu u Jany: 841
  - radku pres mapping: 320
  - radku pres presny nazev obrazku: 26
  - fallback pouze: 1
  - jediny zamerne ponechany fallback: `chez | u, k -> preposition`
  - mapping hodnot bez existujiciho obrazku: 0
- Opravena záměna `school.PNG`: aktualni `school.PNG` je skola; `hospital.png` zustava nemocnice.
- Commit + push:
  - `383fc22 Fix VocabularyFR external Pict lookup`
  - `e4202a6 Apply Jana VocabularyFR generated image mappings`
  - `253c6cd Fix Vocabulary school image mixup`

Co neni hotove:
- Neni potreba dalsi aktivni prace, pokud Jana nepotvrdi novy problem.
- iCloud synchronizace muze byt pomala; pri problemu nejdrive overit datumy souboru na Janine Macu.

Dalsi krok:
- Archivovat projekt mimo aktivni seznam.
- Pri navratu spustit audit:
  `.venv/bin/python scripts/audit_jana_vocabularyfr_pict_mapping.py`

Navrhovane dalsi kroky:
- Okamzite: zadny dalsi krok, jen nechat Janu znovu otevrit aplikaci po iCloud synchronizaci.
- Pri dalsim pozadavku: zacit read-only auditem CSV/mapping/Pict, ne generovanim.
- Volitelne pozdeji: uklidit pracovni `PictNew/generated/20260606_fr_jana_batch*` az po samostatnem potvrzeni, protoze jde o pracovni/generovane soubory mimo aktivni aplikaci.

Zmenene nebo relevantni soubory:
- `VocabularyFR/vocab_trainer_fr.py`
- `Pict/mapping.json`
- `Pict/school.PNG`
- `PictSource/school.PNG`
- `Samantha_Agent/scripts/audit_jana_vocabularyfr_pict_mapping.py`
- `Samantha_Agent/scripts/apply_jana_vocabularyfr_generated_mappings.py`
- Janina iCloud slozka: `PythonMF/VocabularyFR/`
- Janina iCloud obrazky: `PythonMF/Pict/`

Bezpecnost / neukladat:
- Neukladat do gitu Janina soukroma iCloud data ani runtime zalohy mimo git.
- Nemazat `PictNew/generated` ani backupy bez vyslovneho souhlasu.
