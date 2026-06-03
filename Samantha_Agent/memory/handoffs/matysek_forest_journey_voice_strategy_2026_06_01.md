Nazev: Matysek Forest Journey - hlasova strategie pro Bunnyho a dalsi sceny
Priorita: 1
Stav: ceka na rozhodnuti
Pripomenout pri startu: ano
Datum: 2026-06-01

Co se resilo:
- Prvni scena Forest Journey `Clearing Meeting` je funkcni a hlasove castingu postav se venovala velka pozornost.
- Míla spravne identifikoval zasadni problem: Bunny musi ve scene rict `We are friends.`, ale schvaleny stary Bunny hlas z puvodni sceny Benji+Bunny umi jen existujici MP3 vety.
- Pokus vlozit `We are friends` z noveho kandidata rozbil hlasovou konzistenci Bunnyho. Commit s timto resenim byl revertovan a pushnut:
  - chybny commit: `5a9818f Add Bunny friendship line to clearing scene`
  - opravny revert: `30c92b5 Revert "Add Bunny friendship line to clearing scene"`
- Aktualni produkce je zpet v hlasove cistem stavu:
  - Bunny ve `clearingMeeting` rika schvalenym starym hlasem `Hello. I am Bunny.`
  - Fiona rika `We are friends too.`
  - cache je zpet `20260601bunnylock1`.

Co je hotove:
- Odsouhlasene vizualy a story bible Forest Journey.
- Prvni implementacni pruchod `clearingMeeting` existuje v `docs/` i mirroru `MatysekANJ/web_mmtx/`.
- Stary Benji/Bunny uvodni hlas byl napojen pro Benjiho a Bunnyho predstaveni.
- Recast hlasove reference pro ostatni postavy jsou ulozene v:
  - `data/matysek_english/voice_casting_20260601_scene01_recast/`
- Byly vytvoreny zkusebni kandidati pouze pro Bunny vetu `We are friends.`:
  - `data/matysek_english/voice_casting_20260601_bunny_we_are_friends/`
  - Míla je posoudil jako nepouzitelne: nic z toho ani vzdalene nesedelo ke schvalenemu Bunny hlasu.

Co neni hotove:
- Neni vyresena dlouhodoba hlasova strategie pro Bunnyho v cele Forest Journey.
- Neni bezpecne pokracovat v dalsich scenach s predpokladem, ze stary Bunny hlas bude umet nove vety.
- Neni finalne rozhodnuto, zda:
  1. precastovat Bunnyho pro celou novou kapitolu,
  2. precastovat vsechny postavy pro celou Forest Journey,
  3. hledat stabilni lidsky nebo externi hlas,
  4. upravit dialogy tak, aby se pouzivaly jen existujici schvalene MP3.

Dalsi krok:
- Zitra nejdriv rozhodnout hlasovou strategii pro celou Forest Journey, nez se bude pokracovat v programovani dalsich scen nebo finalnim MP3 napojeni.
- Prakticky prvni krok: pripravit seznam vsech vet, ktere Bunny potrebuje ve scenach 1-6, a podle toho rozhodnout, jestli stary hlas vubec muze byt nosny.

Navrhovane dalsi kroky:
- Okamzite:
  - Neprogramovat dalsi hlasy naslepo.
  - Nesazet na novy OpenAI `echo` jako nahradu stareho Bunnyho, protoze aktualni generace netrefuje puvodni charakter.
  - Udelat kratky voice-strategy dokument pro Forest Journey: postava -> existujici schvalena reference -> budouci vety -> riziko konzistence.
- Volitelne po rozhodnuti:
  - Pokud se bude precastovat Bunny, vygenerovat ne jednu vetu, ale mini sadu 8-12 budoucich Bunny vet a schvalovat charakter na cele sade.
  - Pokud se bude precastovat cela kapitola, zamknout `VOICE_LOCK_FOREST_JOURNEY` pro vsech 5 postav a teprve potom generovat sceny.
  - Pokud se zustane u starych MP3, prepsat scenar tak, aby Bunny nepouzival nove neexistujici fraze; toto ale Míla vnima jako dlouhodobe spatnou cestu.

Zmenene nebo relevantni soubory:
- `docs/script_intro_v2.js`
- `docs/index.html`
- `MatysekANJ/web_mmtx/script_intro_v2.js`
- `MatysekANJ/web_mmtx/index.html`
- `MatysekANJ/benji_bunny_dialogue.json`
- `data/matysek_english/voice_casting_20260601_scene01_recast/`
- `data/matysek_english/voice_casting_20260601_bunny_we_are_friends/`
- `data/matysek_english/scene_proposals_20260530_forest_journey/`

Bezpecnost / neukladat:
- Neukladat API klice, tokeny ani soukrome udaje.
- Necommitovat `data/session_autosave/`.
- Neprovadet dalsi produkcni zmeny hlasu bez Mílova poslechu a explicitniho schvaleni.
- Pri git commitu nepridavat cizi zmeny a nepouzivat `git add .`.
