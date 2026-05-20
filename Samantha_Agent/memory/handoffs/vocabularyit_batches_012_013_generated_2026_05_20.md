Nazev: VocabularyIT PictNew - batche 012 a 013 vygenerovane
Priorita: 2
Stav: obrazky zkopirovane do Pict, ceka na mapping
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Mila potvrdil placene API generovani obrazku pro VocabularyIT batche 012 a 013.
- Rozsah potvrzeni: generovat pouze batche 012 a 013.
- Zakazano: presouvat obrazky do `Pict/`, mazat existujici obrazky, pokracovat po selhani batchu.

Co je hotove:
- Batch 012 je kompletni: 10/10 obrazku, `generation_report.json` a `review.html`.
- Batch 013 je kompletni: 5/5 obrazku, `generation_report.json` a `review.html`.
- Kontrola reportu potvrdila u obou batchu status `generated` pro vsechny polozky.
- Nejvetsi soubory podle reportu:
  - batch 012: cca 230.2 kB,
  - batch 013: cca 246.6 kB.
- Request `PictNew/NewPicturesRequest20052026.json` ma 125 polozek a batch 013 byl posledni batch.
- Po Milove vizualnim potvrzeni byly vsechny vygenerovane `.webp` soubory z batchu 001 az 013 zkopirovany do `Pict/`.
- Kontrola po kopirovani potvrdila, ze v `Pict/` existuje 125/125 cilovych souboru.

Co neni hotove:
- Nebyl upraven `Pict/mapping.json`.

Dalsi krok:
- Aktualizovat `Pict/mapping.json` az po dalsim vyslovnem potvrzeni a pred zmenou vytvorit zalohu.

Zmenene nebo relevantni soubory:
- `PictNew/NewPicturesRequest20052026.json`
- `PictNew/generated/20260520_it_batch012/`
- `PictNew/generated/20260520_it_batch013/`
- `Pict/` - nove zkopirovane `.webp` soubory z batchu 001 az 013.

Bezpecnost / neukladat:
- Neukladat API klice, tokeny ani jina tajemstvi.
- Neupravovat `Pict/mapping.json` bez samostatneho potvrzeni.
- Nemazat existujici obrazky bez vyslovneho souhlasu.
