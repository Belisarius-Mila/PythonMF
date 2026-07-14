Nazev: Externí recovery disk – USB zařízení se neenumeruje
Priorita: 1
Stav: ceka na fyzicky retest
Pripomenout pri startu: ano
Datum: 2026-07-14

Co se resilo:

- Před plánovanou recovery zálohou se externí disk nepřipojil a macOS předtím
  zobrazil varování o odpojování USB zařízení.

Co je hotove:

- Read-only kontrola nepotvrdila žádný externí fyzický ani virtuální disk.
- Ve `/Volumes` je jen systémový disk.
- USB strom ukázal pouze interní T2 zařízení; externí USB mass storage ani
  Thunderbolt zařízení se neenumerovalo.
- Nebyl spuštěn mount, First Aid, oprava souborového systému ani zápis na disk.
- Poslední úspěšná recovery záloha zůstává z 2026-07-09 a je starší než 3 dny.

Co neni hotove:

- Není rozlišeno, zda je příčinou kabel, hub, port, napájení nebo samotný disk.
- Nová záloha zatím nemohla proběhnout.

Dalsi krok:

- Disk i hub nechat krátce odpojené, Mac ponechat na napájení a disk připojit
  přímo jiným datovým kabelem do jiného portu. U disku s adaptérem restartovat i
  jeho napájení. Potom znovu read-only ověřit USB enumeraci a `diskutil list`.

Navrhovane dalsi kroky:

1. Pokud se zařízení objeví jako disk, teprve potom řešit mount a stav svazku.
2. Pokud se stále neenumeruje, provést úplné vypnutí Macu s odpojenými USB
   zařízeními a retest po startu.
3. Při pokračujícím problému ověřit disk jiným kabelem nebo na jiném počítači.
4. First Aid nebo jiné zásahy do dat provádět až po detekci zařízení a novém
   rozhodnutí Míly.

Zmenene nebo relevantni soubory:

- `scripts/backup_status.py`
- `memory/handoffs/external_backup_disk_usb_not_detected_2026_07_14.md`

Bezpecnost / neukladat:

- Neukládat sériová čísla zařízení ani obsah zálohy.
- Neformátovat, neinicializovat a neopravovat disk bez výslovného rozhodnutí.
