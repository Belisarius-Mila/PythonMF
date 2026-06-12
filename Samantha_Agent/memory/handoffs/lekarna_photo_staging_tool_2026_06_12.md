Nazev: Lekarna photo staging tool
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-12

Co se resilo:
- Mila mel ve Stazenych dve nove fotky pripravku Dr.Max Zinek/Zinok Forte 25 mg
  a Dr.Max Vitamin B12 500 mcg.
- Dosavadni foto import umel dobre `prepare/apply`, ale neumel pohodlne vzit
  fotky primo z externiho umisteni typu `~/Downloads`.

Co je hotove:
- Vznikl novy Samantha tool `stage_lekarna_photo_import`.
- Tool kopiruje vybrane zdrojove fotky do soukrome slozky
  `data/lekarna/Leky_v_Krabickach/` a vytvori CSV manifest v
  `data/lekarna/photo_imports/`.
- CLI ma novy prikaz:
  `.venv/bin/python scripts/lekarna_photo_import.py stage --source <fotka>`.
- Hlavni agent `app/samantha_agent.py` novy tool importuje, registruje a ma
  instrukce, kdy pouzit `stage`, `prepare`, `apply` a `validate`.
- Capability audit vidi Lekarnu jako `8/8` toolu bez unmapped gapu.
- Dnesni dve fotky byly potvrzene importovane do soukrome evidence; evidence ma
  po importu 69 polozek. Soukroma data/fotky nejsou v gitu.

Co neni hotove:
- Zatim neni automaticke OCR/vision cteni metadat z fotky; metadata se stale
  doplnuji kontrolovane pres manifest.
- Webovy/encrypted export Lekarny nebyl po dnesni zmene soukromych dat znovu
  generovan.

Dalsi krok:
- Pri dalsich fotkach ze Stazenych pouzit `stage_lekarna_photo_import`, potom
  zkontrolovat/doplnit manifest a teprve po vete
  `Potvrzuji import fotek lekarna` spustit `apply_lekarna_photo_import`.

Navrhovane dalsi kroky:
- Okamzity: neni potreba zadna dalsi akce, pokud Mila nechce aktualizovat webovy
  encrypted bundle Lekarny.
- Volitelne: pozdeji doplnit Cockpit tlacitko pro vyber fotek a zobrazeni
  manifestu k revizi.
- Volitelne: doplnit image/OCR navrh metadat, ale ponechat potvrzovaci apply
  branu.

Zmenene nebo relevantni soubory:
- `app/lekarna/photo_import.py`
- `app/lekarna/tools.py`
- `app/lekarna/__init__.py`
- `scripts/lekarna_photo_import.py`
- `tests/test_lekarna_service.py`
- `app/samantha_agent.py`
- `app/capability_audit.py`
- `memory/projects/lekarna_domaci_leky.md`

Bezpecnost / neukladat:
- `data/lekarna/` obsahuje soukroma domaci zdravotni data a fotky; necommitovat.
- Neuvadet davkovani jako doporuceni; u novych polozek drzet
  `nutno_overit=ano`, `overeno_z_letaku=ne` a `expirace=nezjisteno`, pokud neni
  expirace jasne overena.
