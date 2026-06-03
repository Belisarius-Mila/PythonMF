Nazev: Matysek Forest Journey - scena 1 Sunny hlas a zaverecny prompt
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-06-03

Co se resilo:
- Prvni scena Forest Journey / cesta k jezeru (`clearingMeeting`) v Matysek webu.
- Lock hlasu Sunnyho po neuspesnych kandidátech; finalni reference je mlady `young_nova`.
- Pregenerovani dvou Sunny replik pro produkcni web:
  - `Hello! I am Sunny.`
  - `We can go together.`
- Uprava zaverecneho promptu po dobehnuti prvni sceny.

Co je hotove:
- Sunny reference je zafixovana v lokalni ignorovane slozce:
  - `data/matysek_english/voice_references/locked_forest_journey_20260603/sunny_reference.mp3`
  - referencni text: `Hello! I am Sunny. We can go together.`
- Testovaci Sunny MP3 `I am ready to go. Do we have all what we need?` znela Mile dobre.
- Produkcni Sunny MP3 byly nahrazeny v `docs/` i mirroru `MatysekANJ/web_mmtx/`:
  - `audio/english/scene01_05_sunny_hello_i_am_sunny_en.mp3`
  - `audio/english/scene01_09_sunny_we_can_go_together_en.mp3`
- Cache suffix pro tyto dve Sunny repliky je `?v=20260603sunny-nova`.
- Zaverecny anglicky prompt je:
  - `Great. Open the door or run again.`
- Velka ceska napoveda zustala puvodni.
- Samostatna zaverecna ceska veta je doplnena jen do finale sceny:
  - `Dveřmi vstoupíš do další scény nebo si přehraj vše znovu.`
- Tato ceska veta se zobrazi pod zaverecnou anglickou vetou a precte se po anglicke TTS vete.
- Overeni probehlo:
  - `node --check docs/script_intro_v2.js`
  - `node --check MatysekANJ/web_mmtx/script_intro_v2.js`
  - kontrola shody MP3 mezi `docs/` a mirror kopii pres `cmp`
- Relevantni commity jsou pushnute na `origin/main`:
  - `29ddc3f Lock Sunny F5 voice reference`
  - `a74ef18 Update Sunny voice in Matysek lake scene`
  - `b465279 Update Matysek lake scene ending prompt`
  - `7d2904a Fix Matysek lake scene final Czech hint`

Co neni hotove:
- Mila jeste musi rucne zkontrolovat produkci v prohlizeci.
- Je potreba poslechnout, zda Sunny v kontextu prvni sceny sedi s Benjim, Bunny, Brunem a Fionou.
- Pokud bude Sunny v produkci stale problem, vratit se ke castingu Sunnyho hlasu.
- Dalsi sceny Forest Journey zatim nejsou navazane na novy hlasovy postup.

Dalsi krok:
- Otevrit produkcni web, pustit `clearingMeeting` / cestu k jezeru a zkontrolovat:
  - Sunny repliky,
  - cache refresh,
  - zaverecny text `Great. Open the door or run again.`,
  - zaverecnou ceskou vetu,
  - ze velka napoveda stale obsahuje puvodni delsi text.

Navrhovane dalsi kroky:
- Okamzity krok: rucni produkcni retest prvni sceny.
- Potom: podle poslechu bud Sunnyho potvrdit pro dalsi sceny, nebo udelat jeste jeden kratky casting.
- Nasledne: pripravit dalsi scenu Forest Journey a generovat repliky malymi davkami pres `scripts/matysek_f5tts_generate.py`.

Zmenene nebo relevantni soubory:
- `docs/script_intro_v2.js`
- `MatysekANJ/web_mmtx/script_intro_v2.js`
- `docs/audio/english/scene01_05_sunny_hello_i_am_sunny_en.mp3`
- `docs/audio/english/scene01_09_sunny_we_can_go_together_en.mp3`
- `MatysekANJ/web_mmtx/audio/english/scene01_05_sunny_hello_i_am_sunny_en.mp3`
- `MatysekANJ/web_mmtx/audio/english/scene01_09_sunny_we_can_go_together_en.mp3`
- `scripts/matysek_f5tts_generate.py`
- `memory/technical/matysek_f5tts_voice_workflow.md`
- Lokalne, ignorovane a necommitovane reference:
  - `data/matysek_english/voice_references/locked_forest_journey_20260603/`

Bezpecnost / neukladat:
- Do gitu neukladat `data/private/`.
- Do gitu neukladat `data/session_autosave/`.
- Lokálni hlasove reference v `data/matysek_english/voice_references/` jsou pracovni/ignorovane; commitovat jen dokumentaci a produkcni webove assety podle konkretniho zadani.
- Nepouzivat `git add .`; commitovat jen presne vybrane soubory.
