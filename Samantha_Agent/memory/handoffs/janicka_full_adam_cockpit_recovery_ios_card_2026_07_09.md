Nazev: Janicka nouzova zaloha: plny Adam, Cockpit launchery a iPhone karta
Priorita: 1
Stav: ceka na kratky rucni retest s Janou
Pripomenout pri startu: ano
Datum: 2026-07-09

## Co se resilo

Po realnem testu `Janička -> Zeptat se Adama` bez VS Code se ukazalo, ze light
režim je uzitecny pro bezne odpovedi, ale pri slozitejsi praci muze narazit na
timeout nebo omezeny rozsah. Cilem bylo dat Jane viditelnou, netechnickou
zalozni cestu k plnemu Adamovi bez nutnosti spoustet VS Code nebo znat Codex
syntaxi.

## Co je hotove

- V Cockpitu je v Janičce jako prvni karta tlacitko `Když Adam light nestačí`
  / `Otevřít plného Adama`.
- Backend endpoint `/api/janicka/full-adam/open` otevre Terminal.app s primym
  interaktivnim `codex --no-alt-screen -C ...` a startovnim promptem pro Janu.
- Startovni prompt rika, ze Jana pise normalni vetou, nemusi znat prikazy a ze
  bez potvrzeni se nema nic posilat, mazat, presouvat, platit ani menit.
- Cockpit UI zobrazuje i rucni fallback: otevrit Terminal, prejit do projektu
  a spustit `codex --no-alt-screen`.
- Na Macu jsou mimo git pripravene viditelne launchery pro otevreni Cockpitu:
  desktop `.command`, desktop aplikace a aplikace v `/Applications`.
- Je pripravena podepsana iPhone zkratka `Janička SOS.shortcut` na Plose Macu;
  zobrazi Jane kartu s postupem, kde na Macu najit aplikaci a jak otevrit
  Janičku/plneho Adama.
- Testy Cockpitu pokryvaji pritomnost tlacitka, endpointu a pevneho Terminal
  prikazu pro plneho Adama.

## Co neni hotove

- Zkratka jeste neni nasdilena/importovana na Janin iPhone.
- Neni hotovy spolecny rucni test cele cesty s Janou:
  iPhone karta -> Mac `Aplikace` -> `JANIČKA OTEVŘÍT COCKPIT` -> `Janička`
  -> `Otevřít plného Adama`.
- Běžný light chat je funkcni, ale posledni realny test nebyl stoprocentni:
  pri slozitejsim e-mailovem pozadavku se objevil timeout/fallback a je vhodne
  jeste otestovat 2-3 navazujici jednoduche dotazy.

## Dalsi krok

Nasdilet/importovat `Janička SOS.shortcut` na Janin iPhone, pridat ji na
viditelne misto a spolecne projit celou nouzovou cestu. Po tom jeste kratce
otestovat bezny `Zeptat se Adama` light chat na 2-3 navazujicich dotazech.

## Navrhovane dalsi kroky

Okamzity:
- S Janou otevrit iPhone zkratku a podle ni spustit Cockpit a plneho Adama.

Volitelne pozdeji:
- Udelat jednoduchou tisknutelnou kartu se stejnymi kroky.
- Zviditelnit launcher v Docku/Finderu podle toho, co Jana realne najde
  nejsnadneji.
- Rozhodnout, jestli ma Janička SOS karta obsahovat i kontakt na technickou
  pomoc.

## Zmenene nebo relevantni soubory

- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/projects/janicka_cockpit_takeover.md`
- `memory/projects/janicka_cockpit_kucharka.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Mimo git / soukrome nebo lokalni artefakty:
- `/Users/miloslavfalta/Desktop/JANA - OTEVRIT COCKPIT.command`
- `/Users/miloslavfalta/Desktop/JANA COCKPIT.app`
- `/Applications/JANA COCKPIT.app`
- `/Users/miloslavfalta/Desktop/Janička SOS.shortcut`
- `data/private/shortcuts/janicka_sos.xml`
- `data/private/shortcuts/output/Janička SOS.shortcut`

## Overeni

- Cilene i cele `tests.test_cockpit` prosly po oprave JavaScript stringu.
- iPhone Shortcut XML proslo validaci Shortcuts Playground validatoru.
- Podepsany `.shortcut` vznikl s vystupem `mode anyone`.
- Desktop `.command` byl otestovan neinteraktivnim spustenim a otevrel Cockpit.
- Mila rucne potvrdil, ze aplikacni launchery pro Cockpit funguji.

## Rizika

- Terminal/Codex launcher zavisi na lokalni instalaci `codex`, shell prostredi a
  macOS Terminal.app.
- Pokud spadne nebo nejde spustit Cockpit, desktop/app launcher pomaha jen do
  miry, do jake funguje `scripts/start_cockpit.sh`.
- iPhone karta sama nespousti Mac na dalku; je to navigacni karta pro Janu.
- Light Janička chat zustava uzitecny, ale neni jedina zachranna cesta pro
  slozitejsi praci.

## Bezpecnost / neukladat

- Neukladat do gitu cele e-maily, obsah archivovanych zprav, hesla, tokeny,
  recovery klice, rodna cisla ani jina citliva data.
- Soukrome zkratky, lokalni launchery a private vystupy zustavaji mimo git,
  pokud Mila vyslovne nerozhodne jinak.
