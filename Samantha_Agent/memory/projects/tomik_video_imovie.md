# Projekt: Tomik video iMovie

Datum zalozeni: 2026-05-21
Priorita: 1

## Cil

Pomoci Mile pripravit rodinne video z malych klipu od dcery, tema: vnuk Tomik -
druhy rok. Skladani bude prakticky probihat v iMovie, Codex/Samantha ma pomahat
s organizaci, vyberem, storyboardem, strukturou, popisky, hudbou a exportnim
checklistem.

## Bezpecnost a soukromi

- Rodinna videa, fotky a finalni exporty nepatri do gitu ani do memory.
- Do memory ukladat jen workflow, rozhodnuti, strukturu projektu a anonymizovane
  poznamky; neukladat soukrome detaily z videi.
- Pokud vzniknou pracovni soubory nebo seznamy klipu, drzet je mimo verejne repo
  nebo v lokalni ignorovane slozce.

## Navrzeny workflow

1. Vytvorit jednu lokalni slozku mimo git, napr. `~/Movies/Tomik_rok_2/`.
2. Do ni rozdelit klipy:
   - `01_inbox_originaly/` - nedotcene originaly,
   - `02_vybrane/` - klipy vybrane do filmu,
   - `03_audio_hudba/` - hudba, zvuky, namluva,
   - `04_exporty/` - testovaci a finalni exporty.
3. Originaly nemazat ani neprejmenovavat destruktivne.
4. Udelat rychly index klipu: datum, delka, co je na videu, kvalita, jestli patri
   do finalniho strihu.
5. Navrhnout jednoduchou strukturu filmu:
   - zacatek s titulkem,
   - 4 az 8 tematickych kapitol,
   - kratke prechody,
   - zaver s nejlepsim momentem nebo rodinnym titulkem.
6. V iMovie importovat jen vybrane kopie nebo vybrane originaly, seradit podle
   storyboardu, zkratit hluche zacatky/konce, sjednotit hlasitost a pridat titulky.
7. Exportovat test, projit na TV/telefonu a az potom udelat finalni export.

## Jak muze Codex pomoct

- Navrhnout strukturu filmu podle seznamu klipu.
- Vytvorit checklist pro iMovie.
- Pomoci s nazvy kapitol a texty titulků.
- Navrhnout delku finalniho videa a rytmus strihu.
- Pripravit prikazy pro read-only audit slozky s videi, pokud Mila poskytne cestu.
- Navrhnout bezpečný postup konverze/komprese pres `ffmpeg`, pokud bude potreba;
  zapisujici operace delat jen po potvrzeni a se zalohou.

## Prvni rozhodnuti

- Projekt ma prioritu 1, protoze jde o konkretni rodinny vystup a iMovie prace se
  dela rucne s okamzitou praktickou hodnotou.
- Vstupni slozka byla nalezena jako `~/Downloads/Rok 2`.
- Pracovni lokalni slozka v projektu je `data/private/tomik_rok_2/`; cela je
  ignorovana gitem pres `data/private/`.
- Stav k 2026-05-21: 217 videi bylo zkopirovano do `01_originaly/`, vznikly
  nahledy, kontaktni listy, audit CSV, strucne popisy a chronologicky pojmenovana
  sada v `04_chronologicky_pojmenovane/`.
- Stav po navazani 2026-05-21: existuje navazovatelny skript
  `scripts/tomik_video_select_imovie.py`, kratky vyber 35 klipu v
  `05_imovie_vyber_short/`, rodinny vyber 82 klipu v `06_imovie_vyber_family/`
  a storyboardy `storyboard_short.md` + `storyboard_family.md`.
- Tento iMovie/PDF smer je prekryty novejsim smerem `FamilyVideoOrganizer`.

## Aktualni kanonicky stav 2026-05-23

Projekt zustava priorita 1, ale aktualni prakticky smer je lokalni webova
aplikace `FamilyVideoOrganizer`, ne dalsi PDF ani okamzity import do iMovie.

Hotove:

- 217 videi je zauditovano v soukrome slozce `data/private/tomik_rok_2/`.
- Existuji short/family vybery:
  - `05_imovie_vyber_short/` - 35 klipu,
  - `06_imovie_vyber_family/` - 82 klipu.
- Existuji PDF/review podklady pro rozhodovani s dcerou.
- V gitu je prvni UI prototyp v `docs/family-video-organizer/`:
  - tabulka videi,
  - filtry,
  - preview panel,
  - modal pro prehrani videa,
  - autosave do `localStorage`,
  - import draftu,
  - export rozhodnuti do JSON.
- Bug se zaviranim video modalu byl opraven.

Aktualni dalsi krok:

- Vygenerovat soukromy realny datovy balicek mimo git:
  `data/private/tomik_rok_2/family_video_organizer_package/`.
- Pripravit `videos-data.js` s realnymi 217 zaznamy a cestami k nahledum.
- Otestovat lokalne nacitani 217 zaznamu, nahledy, autosave, export JSON a
  prehrani videa podle puvodniho nazvu.
- Jakykoli import dcerina JSON rozhodnuti zpet do short/family vyberu musi byt
  samostatny potvrzovany krok.

## Historicke handoffy

Tyto handoffy ponechat jako auditni historii, ale nepouzivat je jako aktivni
startovni stav projektu. Aktualni navazani je tento projektovy soubor a
`handoffs/family_video_organizer_ui_prototype_2026_05_22.md`.

- `handoffs/tomik_video_imovie_start_2026_05_21.md` - zalozeni projektu a
  zakladni pravidla soukromi.
- `handoffs/tomik_video_imovie_audit_hotov_navrh_pokracovani_2026_05_21.md` -
  audit 217 videi, nahledy, kontaktni listy a chronologicky katalog.
- `handoffs/tomik_video_imovie_selection_ready_2026_05_21.md` - vytvoreni
  short/family iMovie vyberu a storyboardu.
- `handoffs/tomik_video_imovie_pause_waiting_daughter_2026_05_21.md` - pauza
  pred odsouhlasenim s dcerou, HTML/PDF review vystupy.
- `handoffs/tomik_video_review_pdfs_done_editable_next_2026_05_22.md` - velke
  PDF katalogy a uvaha o editovatelnem rozhodovacim listu; prekryto smerem
  FamilyVideoOrganizer.
