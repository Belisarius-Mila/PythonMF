Nazev: Cockpit sprava managed Codex relaci
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-07-03

Co se resilo:
Po zprovozneni Janička light komunikace zacaly vedle hlavni Mílovy Codex relace
bezne bezet i spravovane relace `samantha_adam` a `samantha_janicka`. Stary
Cockpit pohled je pocital jako obycejne Codex relace, coz vedlo k matoucemu
varovani o vice relacich a mohlo by je nabizet k cleanupu.

Co je hotove:
- Voice bridge status rozlisuje bezne lidske Codex relace a spravovane relace.
- `samantha_adam` se zobrazuje jako `Adam managed`.
- `samantha_janicka` se zobrazuje jako `Janička light`.
- Limit jedne bezne hlasove/VS relace se pocita jen nad lidskymi relacemi.
- Cleanup starych relaci chrani nejen voice bridge cil, ale i managed relace.
- Cockpit UI popisuje managed relace oddelene a nenabizi je jako stare relace.
- Testy `tests.test_cockpit` prosly.

Co neni hotove:
- Neni doplnen samostatny velky panel „Sprava relaci“; zatim jde o opravu
  existujiciho Voice bridge panelu.

Dalsi krok:
Pri dalsim rucnim testu Cockpitu overit, ze panel Hlas / Voice bridge ukazuje
hlavni relaci zvlast a `Adam managed` / `Janička light` jako spravovane relace.

Navrhovane dalsi kroky:
Pokud se sprava relaci bude dal komplikovat, udelat samostatny prehled:
`Hlavni Adam`, `Janička light`, `legacy Adam`, `VS Code/Codex`, `SSH/screen`,
vcetne tlacitek start/stop jen pro managed sluzby.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `tests/test_cockpit.py`

Bezpecnost / neukladat:
Neukladat soukrome texty z relaci, tokeny ani cele prikazy obsahujici citliva
data. Cleanup relaci musi dal chranit aktivni hlasovy cil a managed sluzby.

## Provozni oprava 2026-07-10

- Backend celou dobu videl dve relace, ale hlavni shrnuti ukazovalo jen pocet
  beznych relaci. Nyni zobrazuje celkem / bezne / spravovane, tedy aktualne
  `2 / 1 / 1`, a Janičku dal nepovazuje za starou relaci k automatickemu uklidu.
- Tlacitko `Zastavit Janičku` zustava v textovem chatu, je aktivni jen kdyz
  relace bezi a backend po `screen quit` overi, ze relace skutecne zmizela.
  Pokud screen prezije, vrati pravdivy stav `stop_incomplete`.
- Managed relace uz nespousteji vlastni autosave watcher. Janička light zustala
  po nasazeni bezet, ale jeji nadbytecny watcher byl setrne ukoncen.
- Cockpit dashboard, detail Hlas, Recovery centrum a Autosave uklid nyni davaji
  dohromady viditelny prehled relaci a watcheru.
- Implementace je v commitu `67ba77e`; GitHub Actions Cockpit Quality Gate beh
  cislo 11 skoncil uspesne:
  `https://github.com/Belisarius-Mila/PythonMF/actions/runs/29119991977`.
