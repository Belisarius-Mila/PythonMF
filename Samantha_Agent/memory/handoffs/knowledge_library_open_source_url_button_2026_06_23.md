Nazev: Knihovna / tlacitko Otevrit na webu
Priorita: 2
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-23

Co se resilo:
- Mila pri prochazeni Knihovny v Cockpitu upozornil, ze ulozene URL clanky sice maji lokalni archiv, ale z detailu clanku nejde pohodlne znovu otevrit puvodni web.
- Cilem bylo pridat v detailu Knihovny primou akci pro znovuotevreni puvodniho clanku na webu.

Co je hotove:
- V Cockpit modalnim okne `Knihovna` pribylo tlacitko `Otevřít na webu`.
- Tlacitko se aktivuje jen u polozek, ktere maji `canonical_url` nebo `source_url`.
- Otevirani povoluje jen `http` a `https` URL a pouziva novou zalozku s `noopener`.
- U rucne vlozenych textu bez URL zustava tlacitko vypnute.
- Mila rucne potvrdil, ze funkce v Cockpitu funguje.
- Lokální i Tailscale Cockpit byly po změně bezpečně restartované.

Co neni hotove:
- Nebyl delan samostatny Playwright/UI screenshot test.
- Pracovni strom obsahuje starsi nesouvisejici rozpracovane zmeny Lekarny a Pict manifestu, ktere nejsou soucasti teto zmeny.

Dalsi krok:
- Zadny nutny dalsi krok. Pri dalsim prochazeni Knihovny sledovat, jestli popup blocker nektere prohlizece neomezuje; fallback status vypise URL rucne.

Navrhovane dalsi kroky:
- Okamzite: nic.
- Volitelne pozdeji: pridat malou ikonu/indikator v seznamu polozek, ze dana karta ma puvodni webovou URL.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`
- `memory/handoffs/knowledge_library_open_source_url_button_2026_06_23.md`
- `memory/MEMORY_INDEX.md`
- `memory/ACTIVE_PROJECTS.md`

Bezpecnost / neukladat:
- Do handoffu nejsou opsane texty clanku ani plne soukrome URL z Knihovny.
- Nepracovalo se s `data/private/article_archive/`.
