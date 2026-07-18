Nazev: Cockpit - pamatovacek klicovych prikazu
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-07-18

Co se resilo:
Mila chtel bezpecny a snadno dostupny seznam nekolika klicovych prikazu pro
navrat k Adamovi, Cockpit, Git diagnostiku a zalohu. Pamatovacek ma byt dostupny
primo z Cockpitu, ale nesmi prikazy spoustet ani menit.

Co je hotove:
- Vznikl jediny git-safe Markdown zdroj rozdeleny do ctyr praktickych skupin.
- V Cockpitu je read-only modal dostupny ze sekce Servis a odkazem z Recovery
  centra.
- Backend cte jen pevne urceny soubor, parser selhava uzavrene a do rozhrani
  nepropousti cestu ani HTML.
- Frontend vykresluje prikazy a popisy pres `textContent`; nema tlacitko pro
  spusteni, upravu ani kopirovani.
- Pamatovacek je dohledatelny z MEMORY_INDEX.
- Cilene testy, Python kompilace, JavaScript syntaxe, kontrola diffu a plna
  Cockpit brana prosly; plna brana mela 776 uspesnych testu.

Co neni hotove:
- Bezi jeste predchozi instance Cockpitu, proto nova polozka nebyla vizualne
  overena v zivem rozhrani na Macu ani iPhonu.

Dalsi krok:
Rizene restartovat Cockpit a vizualne overit `Servis -> Pamatovacek` i odkaz z
Recovery centra. Zkontrolovat ctyri skupiny, zavreni modalniho okna a citelnost
na uzkem iPhone displeji.

Navrhovane dalsi kroky:
- Pokud budou prikazy pribyvat, menit jen kanonicky Markdown zdroj a zachovat
  read-only charakter rozhrani.
- Nepridavat dynamickou cestu k souboru ani spousteni prikazu z prohlizece.

Zmenene nebo relevantni soubory:
- `app/command_cheatsheet.py`
- `app/cockpit.py`
- `memory/infrastructure/klicove_prikazy_pamatovacek.md`
- `memory/MEMORY_INDEX.md`
- `scripts/cockpit_quality_gate.py`
- `tests/test_command_cheatsheet.py`
- `tests/test_cockpit.py`
- `tests/test_cockpit_http_security.py`
- `tests/test_cockpit_quality_gate.py`

Bezpecnost / neukladat:
Do pamatovacku nepatri hesla, tokeny, cele e-mailove adresy, soukrome cesty ani
prikazy obsahujici tajemstvi. Cockpit ma zustat pouze read-only prohlizecem.
