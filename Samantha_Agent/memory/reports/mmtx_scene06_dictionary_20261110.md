# MMTX — závěrečný slovníček nové šestky

Po poslední replice desátého obrazu je dostupná ikona knihy. Otevře dvousloupcový,
posuvný slovníček ve stejném stylu jako scéna 5. Obsahuje 77 nových hesel a spojení,
nikoli opakování slovníčků předchozích scén. Tato změna vzniká lokálně v Datově
větvi; poslední publikovaná verze f7a4ab58 zatím nový slovníček neobsahuje.

## Výběr slov

Audit vychází z pěti anglických audio manifestů a pěti JS zdrojů: dialogy,
anglické pokyny a slovníčky scén 1–5. U sdíleného úvodního skriptu se bere jen
scéna 1 na mýtině, nikoli jiné lekce v témže souboru. Všech deset vstupů bylo
bajtově ověřených proti skutečně vydanému commitu f7a4ab58.

Jde o 450 textových úseků, 191 známých základních tvarů. Tvary se mapují výslovně,
například trees → tree, coming → come, better → good. Vlastní jména, členy,
osobní a přivlastňovací zájmena i gramatické kontrakce nejsou samostatná slovníčková hesla. Nová slovesa,
podstatná jména, přídavná jména a užitečná spojení mají kurátorský český překlad.
Každé heslo má doložený výskyt ve skutečné šestce a žádné nemá starý základní
tvar nebo celé spojení v porovnávaném korpusu. U spojení se kontroluje celý významový celek, například look like nebo find out,
nikoli jen jednotlivá slova.

Základní tvar cloud se dokládá přes clouds, ear přes ears, practise přes practising.
Smaller zůstává ve skutečném příběhovém tvaru s lemmatem small. Lead je ponechané
v kontextu lead our team, aby samostatné slovo nemátlo významem nebo výslovností.
Přesné zdroje, jejich SHA-256, mapování tvarů a výskyty všech 77 hesel jsou
v mmtx_scene06_dictionary_audit_20261110.json.

## Ovládání a přehrávání

- Ikona knihy se objeví až po dokončení poslední věty, v režimu s hlasem až po
  angličtině i češtině. Samotné načtení desátého obrazu ji neodemkne.
- Každá karta ukazuje emoji a anglické heslo. Režim CZ: text navíc ukáže český
  význam, CZ: text + hlas přehraje po angličtině i češtinu. CZ: vypnuto čte jen EN.
- Během čtení nelze spustit další kartu. Zavření slovníčku nebo vypnutí českého
  čtení příslušnou řeč zastaví a zneplatní pozdní callbacky. Po chybě lze znovu
  klepnout na heslo. Chyba slovíčka nepoškodí stav dokončené lekce.
- Zavírací křížek a Escape vrací do desátého obrazu; focus se vrací ikoně knihy.
  Again zavře slovníček a na začátku příběhu ikonu znovu skryje.
- Historie prohlížeče sama zvuk nespouští. Tichý devátý obraz zůstává tichý.
- Slovníček je nezávislý na vnějším slovníkovém webu: všechny potřebné MP3 jsou
  přímo ve složce šestky a v jejím mirroru.

## Audio a zachování podkladů

154 slovníčkových MP3: 77 anglických (Andrew) a 77 českých (Vlasta), tempo −10 %.
20 českých nahrávek bylo převzatých z VocabularyEN, s přesně stejným textem,
hlasem a tempem; identita názvu je odvozená z těchto vstupů a kontroluje se také
SHA-256 a dekódování. Zdrojové soubory, CSV a obecný slovník se nemění.

134 nových unikátních Azure požadavků, 4964 SSML znaků z limitu 5000, žádný retry.
Celkem 1597824 B slovníčkových MP3. Nové audio má vlastní trvalou účtenku a
oddělené manifesty nově vytvořených a všech převzatých/vytvořených aktiv.
Před prvním transportem se ověří celý rozpočet, novost hesel i všechny převzaté
nahrávky; nejistý transport blokuje opakování. Skutečná výroba se pro testy neopakovala.

167 původních materiálů šestky a 10 dřívějších EN/CS raw účtenek mají stále shodné
SHA-256 proti předchozímu Git checkpointu. Původních 134 dialogových MP3, texty,
ilustrace ani vazba z pětky se nepřepisují. Po rozšíření šestka obsahuje 288 MP3.
Lokální HTTP vrátilo 327/327 skutečných veřejných souborů s přesnými bajty.
Pomocné .lock zůstávají ignorované, soukromé účtenky a klíče nejsou v Gitu.

## Ověření a stav

- 74 cílených testů PASS; po doplnění přístupných EN/CZ názvů ještě samostatný
  JS průchod PASS. Pokrývá i slovníček, všech 77 EN→CS dvojic, odemykání až po
  konci, textové režimy, chybu/nový klik, zavření za běhu, Escape, historii a Again.
- Audit zablokoval záměrně vložené staré heslo trees před jakýmkoli transportem.
  Syntetická výroba ověřila celý rozpočet, zachování předchozích podkladů a
  dokončený opakovaný běh bez nových požadavků. Převzatá MP3 s jiným textem
  nebo otiskem se odmítne. Všech 154 slovníčkových MP3 prošlo dekódováním.
- Plná místní brána slovníčku: 2989 testů OK (5 SKIP), 625,637 s; rychlá statická brána také OK.
- Skutečné Safari dokončilo obraz 10 / 6/6, zobrazilo ikonu knihy a otevřelo čitelný posuvný dvousloupcový seznam. Kliknutí na beautiful načetlo EN i CS MP3 (HTTP 200 ve správném pořadí).
- Fyzický iPhone a Mílova jazyková/hlasová přejímka zůstávají otevřené.

Nové p+n nebylo zadané ani spuštěné. Další krok je místní přejímka a poté vydání
slovníčku podle samostatného Mílova pokynu.

## Hesla

| EN | CZ |
| --- | --- |
| beautiful | krásný |
| blue | modrý |
| cloud | mrak |
| ear | ucho |
| sky | obloha |
| four | čtyři |
| hear | slyšet |
| look like | vypadat jako |
| shout | křičet |
| fish | ryba |
| net | podběrák |
| dinner | večeře |
| food | jídlo |
| meeting | sněm |
| where | kde |
| other side | druhá strana |
| morning | ráno |
| boat | loď |
| fishing hut | rybářská chatrč |
| beside | vedle |
| follow | následovat |
| enjoy | užít si |
| splash | šplouchnutí |
| smaller | menší |
| practise | trénovat |
| frog | žabák |
| race | závod |
| dry | suchý |
| sleep | spát |
| tonight | dnes v noci |
| before | před |
| warm | teplý |
| fire | oheň |
| like | líbit se |
| call | svolat |
| stag | jelen |
| party | oslava |
| bring | přinést |
| every | každý |
| animal | zvíře |
| ask | požádat |
| something | něco |
| think | myslet si |
| wrong | špatně |
| soon | brzy |
| find out | zjistit |
| sick | nemocný |
| people | lidé |
| cut down | pokácet |
| whole | celý |
| healthy | zdravý |
| home | domov |
| anyone | někdo |
| idea | nápad |
| woodpecker | datel |
| check | prohlédnout |
| beaver | bobr |
| leave | nechat |
| must | muset |
| take away | odvézt |
| shore | břeh |
| everyone | všichni |
| hard work | těžká práce |
| lead our team | vést náš tým |
| team | tým |
| plan | plán |
| show | ukázat |
| start | začít |
| see you there | uvidíme se tam |
| many | mnoho |
| may | možná |
| please | prosím |
| just | jen |
| even | dokonce |
| place | místo |
| find | najít |
| next time | příště |
