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
- Dalsi krok je rucne zkontrolovat kratky vyber, importovat jej do iMovie a
  strihat podle ciselneho poradi souboru a storyboardu.
