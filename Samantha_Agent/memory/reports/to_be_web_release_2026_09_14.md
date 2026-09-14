# ToBeToHave — web a návrat katalogu do hlavního menu

Datum: 2026-09-14 21:44 CEST

- Míla potvrdil lokální prototyp. Publikace používá stávající GitHub Pages.
- Cíl: https://belisarius-mila.github.io/PythonMF/to-be-to-have/
- Zdroj `ToBeTraining/web/`; veřejná kopie `docs/to-be-to-have/` — 236/236 shodných souborů.
- 107 otázek, 24 skládání vět, 184 MP3 a 47 WebP; žádná změna výukového obsahu.
- Katalog se v U06 přesunul do Servisu. Jediné tlačítko `webAppsBtn` je nyní znovu
  v hlavní hlavičce; původní dialog, fokus, návraty a samostatné okno zůstávají.
- Dlaždice `to-be-to-have` má HTTPS URL a nespouští desktopový launcher.
- 14/14 JS testů trenažéru; 22/22 cílených Cockpit testů včetně návratů/dialogů.
- 184/184 MP3 ověřeno ffprobe, 47/47 WebP dekódováno; největší 256 386 B.
- Regresní test porovnává celý manifest veřejné kopie a odmítá další soubory mimo aplikaci.
- Rychlá statická brána Python/JS/shell a whitespace OK.
- 236/236 HTTP odpovědí pod `/to-be-to-have/` odpovídá zdrojovým hashům.
- Zastaralý souhrnný řádek ToBeToHave (KPTL) opraven; KPTL historie v handoffu zůstává.
- Tento zápis předchází plné publikační bráně, push, Pages a nasazení Cockpitu.
  Finální důkaz poskytuje GitHub deployment daného headu, veřejné hash kontroly
  a živá nasazovací účtenka Cockpitu. Nejde o nasazení nové služby nebo Camina.
- Fyzický iPhone a systémová audio politika Safari po veřejném vydání NEOVĚŘENO.
