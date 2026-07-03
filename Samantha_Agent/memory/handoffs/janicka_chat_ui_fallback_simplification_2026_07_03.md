Nazev: Janička chat UI fallback simplification
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-07-03

Co se resilo:
Okno `Janička` ukazovalo vedle sebe starý managed Adam (`samantha_adam`) a novou
light relaci (`samantha_janicka`) podobným jazykem. Vypadalo to jako dvě rovnocenné
cesty a mátlo to při testování.

Co je hotove:
- Hlavní viditelný stav je teď `Janička chat`.
- Tlačítka hlavní cesty jsou `Spustit Janičku` a `Zastavit Janičku`.
- Starý `samantha_adam` je přesunutý pod rozbalovací `Servisní fallback`.
- Fallback tlačítka jsou přejmenovaná na `Spustit fallback`, `Restartovat fallback`,
  `Zastavit fallback`.
- Stav fallbacku říká `Starý Adam fallback` a staré pending dotazy označuje jako
  `Starých nevyřízených dotazů`.
- `Hlasový marker` je v fallback statusu přejmenovaný na `Mílův hlasový bridge`,
  aby bylo jasné, že nejde o Janinu relaci.
- Test `tests.test_cockpit` prošel.

Co neni hotove:
- Neni resen cleanup starých pending requestů v `samantha_adam`; UI je jen jasně
  označuje jako starý fallback stav.

Dalsi krok:
Ručně otevřít `Janička` -> `Zeptat se Adama` a ověřit, že Jana/Míla vidí primárně
jen `Janička chat` a fallback zůstává schovaný pod servisem.

Bezpecnost / neukladat:
Do handoffu neukladat obsah konkrétních dotazů ani odpovědí z Janička chatu.
