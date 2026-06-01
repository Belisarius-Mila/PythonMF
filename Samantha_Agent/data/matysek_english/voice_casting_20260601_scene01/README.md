# Voice casting - Scene 1 Clearing Meeting

Datum: 2026-06-01
Stav: poslechove ukazky k odsouhlaseni, ne finalni produkcni audio

## Cíl

Vybrat hlasy pro novou petici postav pred programovanim prvni forest journey sceny.

## Pravidlo pro zamknuti hlasu

Nazev TTS hlasu typu `echo`, `fable`, `shimmer` atd. nestaci jako pevna identita
postavy. Stejny nazev hlasu muze pri pozdejsi generaci znit jinak. Proto se hlas
postavy zamyka az konkretni odsouhlasenou MP3 nahravkou.

Pravidlo:

1. Pro kazdou postavu vybrat konkretni referencni MP3.
2. Tuto MP3 oznacit jako kanonickou referenci postavy.
3. Pro finalni dialogy generovat nebo vybirat audio tak dlouho, dokud odpovida
   kanonicke referenci.
4. Po odsouhlaseni finalni MP3 soubory ulozit do projektu a uz je neregenerovat.
5. Pri dalsim vyvoji prehravat ulozene MP3, ne volat TTS znovu podle nazvu hlasu.
6. Novy hlas nebo recast postavy delat jen po vyslovnem odsouhlaseni.

Stavajici hlasy:

- Benji: `fable`; kanonicka reference je existujici produkcni Benji audio
- Bunny: kanonicka reference je `reference_bunny_echo_i_am_bunny.mp3`; nebrat
  dnesni `echo` generace jako automaticky stejny hlas

Navrh pro nove postavy:

- Fiona: mladsi zensky hlas, mily a trochu sikovny
- Bruno: hlubsi klidny muzsky hlas
- Sunny: mladsi, lehky, hravy hlas; pokud nebude pusobit dost detsky, hledat dalsi variantu

## Aktuální kontrola po Mílově poslechu

- Tento prvni casting je nahrazen recastingem:
  `../voice_casting_20260601_scene01_recast/VOICE_LOCK_20260601.md`.
- Benji je potvrzen podle `reference_benji_fable_i_am_benji.mp3`.
- Bunny je potvrzeny podle `reference_bunny_echo_i_am_bunny.mp3`; tento konkretni soubor je spravna kanonicka reference.
- Důležité zjištění: `reference_bunny_echo_i_am_bunny.mp3` je správný Bunny hlas ze starého produkčního audia, ale nově vygenerované `echo` ukázky znějí jinak. Proto pro Bunnyho nebrat dnešní `echo` automaticky jako stejnou postavu; starý produkční soubor je kanonická reference.
- Bruno: nove potvrzeny konkretni referencni soubor `bruno_macos_daniel_01_hello_i_am_bruno.mp3`.
- Fiona: nove potvrzeny konkretni referencni soubor `fiona_macos_karen_01_hi_i_am_fiona.mp3`.
- Sunny: nove potvrzeny konkretni referencni soubor `sunny_young_coral_01_hello_i_am_sunny.mp3`.

## Nahrazene predchozi prvni prirazeni

- Fiona=`shimmer`, Bruno=`onyx`, Sunny=`nova` uz nebrat jako finalni volbu.
- Platny vyber je v recast `VOICE_LOCK_20260601.md`.

## Referenční původní hlasy

- `reference_benji_fable_i_am_benji.mp3`
- `reference_bunny_echo_i_am_bunny.mp3`

## Nové ukázky

Bunny k opětovnému porovnání:

- `current_echo_i_am_bunny_control.mp3` - dnešní kontrolní generace stejného textu `I am Bunny.`; může znít jinak než stará reference
- `bunny_echo_hi_i_am_bunny_we_are_friends.mp3`
- `bunny_shimmer_hi_i_am_bunny_we_are_friends.mp3`
- `bunny_ash_hi_i_am_bunny_we_are_friends.mp3`
- `bunny_nova_hi_i_am_bunny_we_are_friends.mp3`

Starší Bunny testy z předchozího castingu:

- `old_test_bunny_intro_echo.mp3`
- `old_test_bunny_intro_shimmer.mp3`
- `old_test_bunny_intro_ash.mp3`
- `old_test_bunny_intro_onyx.mp3`
- `old_test_bunny_count_shimmer.mp3`

Fiona:

- `fiona_shimmer_hi_i_am_fiona.mp3`
- `fiona_shimmer_we_are_friends_too.mp3` - puvodni kandidat, nahrazeno recastingem
- `fiona_nova_hi_i_am_fiona.mp3`
- `fiona_coral_hi_i_am_fiona.mp3`

Bruno:

- `bruno_onyx_hello_i_am_bruno.mp3` - puvodni kandidat, nahrazeno recastingem
- `bruno_onyx_we_are_going_to_the_lake.mp3`
- `bruno_ash_hello_i_am_bruno.mp3`

Sunny:

- `sunny_young_coral_01_hello_i_am_sunny.mp3`
- `sunny_young_coral_02_we_can_go_together.mp3`
- `sunny_young_coral_03_look_benji_the_lake_is_close.mp3` - ad hoc overeni kandidata `sunny_young_coral_01`
- `sunny_young_coral_04_can_you_help_me_find_the_path.mp3` - ad hoc overeni kandidata `sunny_young_coral_01`
- `sunny_young_nova_01_hello_i_am_sunny.mp3` - puvodni kandidat, nahrazeno recastingem
- `sunny_young_nova_02_we_can_go_together.mp3`
- `sunny_young_shimmer_01_hello_i_am_sunny.mp3`
- `sunny_young_shimmer_02_we_can_go_together.mp3`
- `sunny_young_alloy_01_hello_i_am_sunny.mp3`
- `sunny_young_alloy_02_we_can_go_together.mp3`
- `sunny_ash_hello_i_am_sunny.mp3`
- `sunny_ash_we_can_go_together.mp3`
- `sunny_nova_hello_i_am_sunny.mp3`
- `sunny_coral_hello_i_am_sunny.mp3`
- `sunny_shimmer_hello_i_am_sunny.mp3`
- `sunny_echo_hello_i_am_sunny.mp3`
- `sunny_alloy_hello_i_am_sunny.mp3`
- `sunny_sage_hello_i_am_sunny.mp3`
- `sunny_ballad_hello_i_am_sunny.mp3`

## Co rozhodnout

1. Potvrdit, ze Benji zustava `fable`.
2. Bunny je potvrzeny podle kanonicke reference `reference_bunny_echo_i_am_bunny.mp3`.
3. Fiona je po recastingu potvrzena podle `fiona_macos_karen_01_hi_i_am_fiona.mp3`.
4. Bruno je po recastingu potvrzen podle `bruno_macos_daniel_01_hello_i_am_bruno.mp3`.
5. Sunny je po recastingu potvrzena podle `sunny_young_coral_01_hello_i_am_sunny.mp3`.

Po odsouhlaseni se ma mapa hlasu zapsat do scenare a az potom generovat finalni audio cele sceny. Finalni MP3 soubory se po schvaleni zamknou jako assety a nebudou se pregenerovavat.

## Sunny - macOS lokální hlasy

Tyto ukázky vznikly lokálně přes macOS `say`, bez placené služby a bez OpenAI generování. Jsou vhodné hlavně pro rychlé hledání mladšího/dívčího směru.

Doporučené pořadí poslechu:

1. `sunny_macos_flo_us_01_hello_i_am_sunny.mp3`
2. `sunny_macos_flo_us_02_we_can_go_together.mp3`
3. `sunny_macos_sandy_us_01_hello_i_am_sunny.mp3`
4. `sunny_macos_sandy_us_02_we_can_go_together.mp3`
5. `sunny_macos_shelley_us_01_hello_i_am_sunny.mp3`
6. `sunny_macos_shelley_us_02_we_can_go_together.mp3`
7. `sunny_macos_junior_01_hello_i_am_sunny.mp3`
8. `sunny_macos_kathy_01_hello_i_am_sunny.mp3`

Další varianty ve složce:

- `sunny_macos_flo_gb_*.mp3`
- `sunny_macos_sandy_gb_*.mp3`
- `sunny_macos_shelley_gb_*.mp3`

Pokud některý macOS hlas vyhoví, zamknout konkrétní MP3 jako kanonickou referenci Sunny. Před veřejným nasazením ještě ověřit licenční vhodnost macOS hlasového výstupu; pro soukromé rodinné testování je to praktická rychlá cesta.
