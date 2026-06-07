Nazev: Janička Cockpit / používání a převzetí Samanthy
Priorita: 1
Stav: historicky start, prekryto aktualnim projektovym souborem
Pripomenout pri startu: ano
Datum: 2026-06-06

Aktualizacni poznamka 2026-06-07:
- Tento handoff je historicky start projektu.
- Casti o tom, ze tlacitko `Janička` jeste neni implementovane, jsou prekryte
  aktualnim stavem v `memory/projects/janicka_cockpit_takeover.md`.
- Prvni git-safe kucharka je zalozena v
  `memory/projects/janicka_cockpit_kucharka.md`.

Co se resilo:
- Mila upresnil, ze `Janička` neni hracka ani omezeny uzivatelsky rezim.
- Cilem je vazny kontinuitni vstup do Samanthy pro Janu.
- Byly rozlisene dva rezimy:
  - Jana pouziva zivou Samanthu, kdyz Mila docasne nemuze;
  - Jana muze Samanthu plne prevzit pri Milove smrti.

Co je hotove:
- Zalozen git-safe projektovy memory soubor `memory/projects/janicka_cockpit_takeover.md`.
- Projekt je zapsany v `memory/ACTIVE_PROJECTS.md` jako priorita 1.
- Projekt je zapsany v `memory/MEMORY_INDEX.md` s pripomenutim.
- Zapsana shoda: Jana nema mit specialne omezeny pristup; bezpecnost ma byt obecna pro cely system.
- Zapsana hranice: `Janička Cockpit` je zivy prakticky vstup, zatimco pozustalost zustava samostatny nouzovy/vlastnicky plan.

Co nebylo hotove pri zalozeni 2026-06-06:
- Tlacitko `Janička` v Cockpitu jeste nebylo implementovane.
- Prvni kucharka pro Janu jeste nebyla hotova.
- Nebylo rozpracovane propojeni na private/sifrovany pozustalostni balik.

Aktualni stav 2026-06-07:
- Tlacitko `Janička` je v Cockpitu implementovane.
- Prvni git-safe kucharka pro Janu je zalozena.
- Propojeni na private/sifrovany pozustalostni balik zustava otevrena cast,
  ale bez citlivych udaju v gitu.

Historicky dalsi krok pri zalozeni:
- Po tehdejsi priorite Adam Voice / Cockpit read-only capability registry
  navrhnout MVP obrazovku `Janička` v Cockpitu.
- Soucasne zalozit prvni verzi kucharky pro Janu:
  - jak hledat dokumenty;
  - jak cist a tisknout;
  - jak pouzit Lekarnu;
  - jak otevrit pripravene rodinne projekty;
  - jak se zeptat Adama;
  - kdy prejit do nouzoveho prevzeti / pozustalosti.

Aktualni dalsi krok:
- Rucne projit obrazovku `Janička` z pohledu Jany a podle vysledku upravit
  texty UI nebo kucharku.

Navrhovane dalsi kroky:
- Navrhnout UI bez technicke reci a bez infantilniho pojeti.
- Udrzet tlacitko viditelne a laskave, ale dustojne.
- Nezavadet pro Janu zvlastni permissions vrstvu; destruktivni a citlive kroky chranit obecnymi systemovymi pravidly.

Zmenene nebo relevantni soubory:
- `memory/projects/janicka_cockpit_takeover.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do git-safe projektu neukladat hesla, tokeny, recovery klice, telefonni cisla, rodna cisla, cele e-maily ani citlive konkretni udaje.
- Citlive udaje patri jen do private/sifrovaneho pozustalostniho baliku mimo git.
