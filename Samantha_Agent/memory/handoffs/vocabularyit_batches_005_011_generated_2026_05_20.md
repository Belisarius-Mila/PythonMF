Nazev: VocabularyIT PictNew - batche 005 az 011 vygenerovane
Priorita: 2
Stav: ceka na vizualni kontrolu
Pripomenout pri startu: ano
Datum: 2026-05-20

Co se resilo:
- Mila potvrdil placene API generovani obrazku pro VocabularyIT batche 005 az 011.
- Rozsah potvrzeni: generovat pouze batche 005, 006, 007, 008, 009, 010 a 011.
- Zakazano: presouvat obrazky do `Pict/`, mazat existujici obrazky, pokracovat po selhani batchu.

Co je hotove:
- Batche 005 az 011 jsou ve slozce `PictNew/generated/` kompletni.
- Kazdy batch ma `generation_report.json`, `review.html` a 10 souboru `.webp`.
- Kontrola reportu potvrdila u vsech batchu status `generated` pro 10/10 polozek.
- Kontrola proti planu z `PictNew/NewPicturesRequest20052026.json` nenasla chybejici ani nadbytecne `.webp` soubory.
- Nejvetsi soubory podle reportu:
  - batch 005: cca 208.2 kB,
  - batch 006: cca 282.6 kB,
  - batch 007: cca 241.7 kB,
  - batch 008: cca 220.5 kB,
  - batch 009: cca 234.2 kB,
  - batch 010: cca 262.8 kB,
  - batch 011: cca 217.5 kB.

Co neni hotove:
- Nebyla provedena vizualni kontrola obrazku.
- Obrazky nebyly presunuty do `Pict/`.
- Nebyl upraven `Pict/mapping.json`.

Dalsi krok:
- Otevrit a vizualne zkontrolovat review soubory:
  - `PictNew/generated/20260520_it_batch005/review.html`
  - `PictNew/generated/20260520_it_batch006/review.html`
  - `PictNew/generated/20260520_it_batch007/review.html`
  - `PictNew/generated/20260520_it_batch008/review.html`
  - `PictNew/generated/20260520_it_batch009/review.html`
  - `PictNew/generated/20260520_it_batch010/review.html`
  - `PictNew/generated/20260520_it_batch011/review.html`
- Batch 012 ani presun do `Pict/` nespoustet bez dalsiho vyslovneho potvrzeni.

Zmenene nebo relevantni soubory:
- `PictNew/NewPicturesRequest20052026.json`
- `PictNew/generated/20260520_it_batch005/`
- `PictNew/generated/20260520_it_batch006/`
- `PictNew/generated/20260520_it_batch007/`
- `PictNew/generated/20260520_it_batch008/`
- `PictNew/generated/20260520_it_batch009/`
- `PictNew/generated/20260520_it_batch010/`
- `PictNew/generated/20260520_it_batch011/`

Bezpecnost / neukladat:
- Neukladat API klice, tokeny ani jina tajemstvi.
- Nepresouvat obrazky do `Pict/` bez samostatneho potvrzeni.
- Nemazat existujici obrazky bez vyslovneho souhlasu.
