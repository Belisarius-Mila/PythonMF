# Vocabulary EN — obrazové pojmy ve větách

Stav 2026-11-17 11:00 CET: pilot hotový místně, bez nového push/nasazení.

Míla schválil pilot20 vět s maximálně5 existujícími obrázky nad větou. Metadata
jsou připravená předem a významově zkontrolovaná; prohlížeč nic neodvozuje.
Pilot má51 vazeb na35 různých významových karet. Všechny obrázky, náhledy,
slovníkové věty a nahrávky pocházejí z dosavadní aplikace.522 UID/512 aktivních
karet a18 okruhů beze změny; žádná generace obrázků ani placené TTS.

Ve smyčce Věta + slovíčko se všechny miniatury s EN hesly ukážou společně nad
EN větou a CZ překladem. Po dočtení a nastavené pauze zmizí a obnoví se velká
karta cílového slova s EN/CZ a jeho výslovností. Na desktopu až5 vedle sebe,
v úzkém rozložení více řádků. Obrázky nejsou ovládací prvky. Pod popiskem je
základní heslo (sing), celá věta zachovává svůj tvar (sings).

Filtr stále vybírá cílové karty; ilustrující významy mohou být i mimo osobní
A–D a vybrané téma. Profily, obtížná a PIN se nemění. Ruční režim vět zůstává
se skrytou odpovědí. Bez metadata pro větu pokračuje původní zobrazení.

## Významová mapa pilotu

| Cílové heslo | EN věta | Obrazové pojmy v pořadí |
|---|---|---|
| cat | The cat sleeps on the chair all afternoon. | cat, sleep, chair |
| dog | The dog waits by the door for a walk. | dog, wait, door |
| tree | A bird is building a nest in the tree. | bird, tree |
| school | I walk to school with my friend. | walk, school, friend |
| apple | I eat an apple on my way to work. | eat, apple |
| mother | My mother keeps old photos in a small box. | mother, old, small, box |
| table | We ask for a table for two by the window. | table, two, window |
| window | Open the window and let in fresh air. | open, window |
| bread | We buy fresh bread in the morning. | bread, morning |
| bird | A small bird sings on the window in the morning. | small, bird, sing, window, morning |
| chair | The wooden chair stands beside the table. | chair, table |
| bed | The cat is sleeping under the bed. | cat, sleep, bed |
| car | Our car is parked in front of the house. | car, house |
| train | The train arrives at the station on time. | train |
| bus | The yellow bus stops near the school. | yellow, bus, stop, school |
| key | This small key opens the front door. | small, key, open, door |
| hand | I wash my hands. | hand |
| sleep | We sleep in the hut. | sleep, hut |
| wait | Please wait for me by the door. | wait, door |
| help | Can you help me? | help |

Sporné významy byly vyřešené ručně: open/otevřít místo open/otevřený,
help/pomáhat místo help/pomoc, sleeps/sleeping→sleep. Parked nemá vazbu na
podstatné jméno park. A walk nemá vazbu na sloveso chodit. On time se neváže
na obecný čas. Chybějící pojmy (např. nest/photos) zůstaly bez ilustrace.

## Export a odolnost

Nový samostatný builder kontroluje přesnou identitu cíle/věty i pojmů,
aktivní UID,1–5 unikátních významů/obrázků, doslovný výraz s hranicemi slov,
pořadí/nezacházení přes sebe, existující bezpečné místní assety a UTF16 indexy.
Při změně významu či věty prohlížeč starou mapu nepoužije. Neznámý záznam nebo
chybný tvar se odmítne jako celek. Neprobíhá automatické domýšlení významu.

Nejvýše10 držených přednačtených náhledů pro aktuální a další větu. Zvuk ani
přechod fáze na obrázek nečekají. Selhání odstraní pouze vadnou dlaždici;
při ztrátě všech se obnoví původní velký obraz. Pozdní chyba staré dlaždice
nesmí změnit jinou větu ani slovní fázi. Pozdní metadata nemění právě běžící
větu; projeví se při další větné fázi. Žádný další Audio element ani změna
dosavadního časování smyčky.

## Ověření a předání

6 nových Python kontrol v existujícím registrovaném testovacím modulu prošlo,
včetně přesného exportu, všech obrazových souborů a UTF16.9 nových skutečně
vykonávaných JS scénářů prošlo:20 map, chybné/stará metadata, správné fáze,
filtr A bez zápisu členství, image error/all-failed, pozdní callback, pozdní
metadata a původní ruční věta. Finální programem vybranou bránu, přesné zdroje
a lokální checkpoint určuje private/vocabulary_en_sentence_pictures_20261117/completion.json.

Safari Mac na samostatném localhost původu ukázalo u bird všech5 obrázků
small/bird/sing/window/morning nad celou EN větou a CZ překladem a potom
skutečně přešlo na velkou bird/pták kartu. Smyčka byla ukončená, vlastní okno
a server zavřené, původní uživatelské okno zachované. Telefon a Mílovo
akustické posouzení nejsou tímto potvrzené. Kontaktní náhled všech vybraných
pojmových obrázků byl vizuálně prohlédnut; nové ilustrace se nevyráběly.

Předchozí smyčka2d7e34a6 byla integrovaná do main jako b2b6710b. Jediné dříve
schválené p+n mělo job0d4eb5c10e0cbe94bbba96e31a06e551 attention, push uncertain,
deployment not_started; nezávislý audit tehdy prokázal nezměněný origin.
Míla nyní výslovně nechal p+n a servis pravidel Willovi. Žádný retry, restart
Cockpitu ani další release submit se v tomto vývoji neprovádí. Historický
stav není tvrzení o nynější produkci; veřejný stav zde znovu neauditujeme.

Další krok: Willova integrace/vydání a Mílova přejímka pilotu. Zbývajících492
aktivních vět zatím nemá novou mapu. Rozšíření pokrytí a případný port do IT
jsou další samostatné kroky. Bez dohody nevzniká vlastní EN TVBCP; nový zápis
je ve stávajícím architektura_komunikace_samantha.txt.

Finální funkční kandidát: validation-v3 161 PASS, režim targeted. Po doplnění tohoto důkazu a zachování úplné historie handoffu následuje dokumentační brána; přesnou shodu finálního commitu potvrzuje privátní completion.json.
