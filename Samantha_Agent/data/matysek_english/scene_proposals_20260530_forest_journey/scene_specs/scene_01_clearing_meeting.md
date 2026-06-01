# Scene 1 - Clearing Meeting

Český název: Paseka, kde se všichni poprvé potkají
Výukový cíl: pozdravy, představování, `I am`, první skupinové `we are`, `we are going`, `too`, `together`
Návaznost: po současné scéně Benji + Bunny a po skoku dveřmi do dalšího světa
Stav: pracovní scénář k odsouhlasení, zatím neprogramovat

## Popis scény česky

Benji a Bunny vyjdou z dveří na malou slunnou paseku. Na pasece už jsou s nimi v přátelském půlkruhu Bruno, Fiona a Sunny. Nejsou to nepřátelé, ale budoucí kamarádi. Někteří se znají, někteří ne. Scéna je milá, pomalá a má fungovat jako první „social English“ lekce.

Hlavní obrazová varianta je varianta A: paseka v lese, všechny postavy stojí v půlkruhu a jsou vidět od začátku. Benji a Bunny jsou vlevo, Bruno uprostřed, Fiona a Sunny s ostatními v kruhu podle hotového obrázku. Varianty s pódiem, třemi cestami nebo postupným fyzickým příchodem postav se pro tuto verzi nepoužijí.

## Cíl pro dítě

Matýsek nemusí číst. Má jen poslouchat, dívat se a klikat na postavu, na kterou ho navede anglická hlasová nápověda a blikající šipka.

Princip:

1. Scéna řekne anglicky, koho má Matýsek najít.
2. U správné postavy bliká šipka nebo jemný světelný ukazatel.
3. Matýsek klikne na postavu.
4. Postava řekne krátkou anglickou větu.
5. U postavy se objeví anglická bublina.
6. Po anglické větě následuje krátký mluvený český překlad.
7. Aktivuje se další postava.

## Hlavní nápověda přes mikrofon

Hlavní česká nápověda patří pod horní tlačítko mikrofonu, aby se neduplikovala s další ikonou v obraze.

```text
Celou scénu můžeš spustit znovu tlačítkem šipky v kruhu.
Doporučujeme scénu přehrát několikrát a několikrát si projít slovníček, to je ikona knihy.
```

Panel má být stručný, ne školní výklad. V obraze zůstává samostatně viditelná ikona knihy pro slovníček a po dokončení scény tlačítko šipky v kruhu pro opakování celé sekvence.

## Krátká startovní nápověda

Při prvním vstupu do scény má jednou zaznít původní krátká orientační nápověda:

```text
Poslouchej anglickou nápovědu.
Klikni na postavu, na kterou ukazuje šipka.
Postava řekne větu anglicky a potom česky.
Ikona knihy otevírá slovníček.
```

Tato krátká nápověda se po startu nemusí znovu opakovat. Horní mikrofon zůstává pro hlavní nápovědu k opakování scény a slovníčku.

## Start dialogu

Návrh bez složité režie:

1. Po příchodu do scény jednou zazní krátká česká orientační nápověda.
2. Automaticky se spustí první anglická nápověda: `Tap Benji.`
3. U Benjiho začne blikat šipka.
4. Pokud Matýsek neklikne, po několika sekundách se `Tap Benji.` zopakuje.
5. Po kliknutí Benji řekne svou větu a objeví se bublina.
6. Po doznění anglické věty zazní krátký český překlad. Český překlad se nezobrazuje jako další bublina.
7. Stejný rytmus pokračuje přes Bunny, Bruna, Fionu a Sunny.

Toto je programově zvládnutelné bez velkého rizika: jde o jednu scénu, jeden aktivní hotspot, jednoduchou animaci šipky, jednu bublinu a sekvenční dialog.

## Finální pracovní dialog A

Toto je aktuálně preferovaný hlavní dialog. Varianty B a C jsou pro tuto scénu odloženy.

```text
Benji: Hello! I am Benji.
CZ: Ahoj! Já jsem Benji.

Bunny: Hi! I am Bunny. We are friends.
CZ: Ahoj! Já jsem Bunny. Jsme kamarádi.
CZ výslovnost: Ahoj! Já jsem Bany. Jsme kamarádi.

Bruno: Hello. I am Bruno.
CZ: Ahoj. Já jsem Bruno.

Fiona: Hi. I am Fiona.
CZ: Ahoj. Já jsem Fiona.

Sunny: Hello! I am Sunny.
CZ: Ahoj! Já jsem Sunny.
CZ výslovnost: Ahoj! Já jsem Sany.

Fiona: We are friends too.
CZ: My jsme také kamarádi.

Bruno: We are going to the lake.
CZ: Jdeme k jezeru.

Benji: We are going to the lake too.
CZ: My jdeme k jezeru také.

Sunny: We can go together.
CZ: Můžeme jít společně.

Fiona: Now we are all friends!
CZ: Teď jsme všichni kamarádi!
```

## Poznámka k angličtině

Původní jednodušší návrh `We go to the lake` byl pro první dětskou scénu použitelný, protože je velmi krátký a dobře opakuje `we` + `go` + `lake`.

Pro finální pracovní dialog ale volíme přirozenější anglickou variantu:

```text
Bruno: We are going to the lake.
Benji: We are going to the lake too.
```

Nebo ještě dětsky a akčně: ... toto bychg nechal napozději.

```text
Bruno: Let's go to the lake.
Benji: Yes! Let's go too.
```

Tahle formulace je o trochu delší, ale zní přirozeněji a pořád je pro dítě dobře pochopitelná, protože se opakuje stejný rytmus `We are going...`.

## Slovníček přes ikonu knihy

U každé scény bude malá ikona knihy. Po kliknutí se otevře jednoduchý slovníček důležitých slov a frází ze scény.

Pro tuto scénu:

```text
Hello - ahoj
I am - já jsem
friends - kamarádi
we are - my jsme
too - také
going / go - jít / jdeme
lake - jezero
can - můžeme
together - společně
now - teď
all - všichni
```

Návrh chování slovníčku:

1. Ikona knihy je viditelná, ale neruší hlavní obraz.
2. Po kliknutí se otevře malý panel s boxíky pod sebou.
3. Každý boxík má formát `English - česky`.
4. Po kliknutí na boxík se přehraje anglické slovo a potom český význam.
5. Panel lze zavřít křížkem nebo opětovným kliknutím na knihu.

To je programově reálné a užitečné. Není nutné dělat z toho samostatnou minihru v první verzi.

## Interakce pro Matýska

První průchod:

1. Anglická nápověda: `Tap Benji.`
2. Šipka bliká u Benjiho.
3. Matýsek klikne na Benjiho.
4. Benji řekne: `Hello! I am Benji.`
5. Zazní nebo se zobrazí: `Ahoj! Já jsem Benji.`
6. Pokračuje Bunny, Bruno, Fiona, Sunny.

Mini kontrola po představení:

1. Anglická nápověda: `Who is Fiona?`
2. Šipka tentokrát nejdřív nemusí blikat, aby Matýsek zkusil najít Fionu podle obrázku.
3. Když neklikne nebo klikne vedle, šipka jemně pomůže.
4. Po správném kliknutí Fiona řekne: `Hi. I am Fiona.`

Opakované klikání:

- Po dokončení hlavní sekvence může Matýsek klikat na libovolnou postavu.
- Každá postava jen zopakuje své představení a nespustí další dialog.
- Tlačítko šipky v kruhu vpravo dole spustí celou sekvenci znovu.
- Horní mikrofon přehraje hlavní českou nápovědu ke scéně.

## Adamovy poznámky

Souhlasím s tím, že pro první implementaci necháme jen dialog A. Je přehledný, zapamatovatelný a dobře se převádí na sekvenční klikání.

Navrhuji držet první verzi technicky střídmě:

- jeden obraz pozadí,
- pět klikacích oblastí pro postavy,
- jedna aktivní blikající šipka,
- jedna řečová bublina,
- jednoduchý mluvený český překlad po anglické větě,
- český help panel vpravo nahoře,
- ikona knihy se slovníčkem,
- možnost po dokončení zopakovat celou sekvenci tlačítkem šipky v kruhu,
- možnost po dokončení kliknout na libovolnou postavu a přehrát jen její představení.

Tohle je hezké, ale pořád rozumně malé sousto. Vyhnul bych se zatím složitým animacím chůze, plynulému pohybu postav, lip-syncu, větveným rozhovorům nebo velké slovníkové minihře. Tyto věci můžeme přidat až po ověření, že základní scéna funguje a Matýska baví.

Moje doporučení před programováním:

1. Odsouhlasit přesné znění dialogu.
2. Počítat s tím, že český překlad bude jen mluvený, ne jako další textová bublina.
3. V implementačním checklistu počítat s finální pracovní variantou `We are going to the lake`.
4. Potom teprve vytvořit implementační checklist pro první scénu.

## Hlasový casting

Hlasové ukázky a finální hlasový lock jsou připravené zde:

```text
data/matysek_english/voice_casting_20260601_scene01_recast/
data/matysek_english/voice_casting_20260601_scene01_recast/VOICE_LOCK_20260601.md
```

Finální odsouhlasený výběr:

- Benji: `reference_benji_fable_i_am_benji.mp3`
- Bunny: `reference_bunny_echo_i_am_bunny.mp3`
- Bruno: `bruno_macos_daniel_01_hello_i_am_bruno.mp3`
- Fiona: `fiona_macos_karen_01_hi_i_am_fiona.mp3`
- Sunny: `sunny_young_coral_01_hello_i_am_sunny.mp3`

Predchozi volby Fiona=`shimmer`, Bruno=`onyx`, Sunny=`nova` jsou nahrazeny recastingem.
Teprve podle tohoto locku se ma pripravit finalni audio cele sceny.

Pravidlo pro stabilitu hlasů: každá postava musí mít konkrétní odsouhlasené MP3
jako kanonickou referenci. Během vývoje se nesmí spoléhat jen na název TTS hlasu,
protože pozdější generace stejného názvu může znít jinak. Finální audio se po
odsouhlasení uloží jako asset a už se neregeneruje bez výslovného recastu.

## Mílovy poznámky z tohoto kola

- Obrazová varianta A zůstává, varianty B a C ne.
- Sekce `Interakce pro Matýska` se líbí a má být základem.
- Dialog A má zůstat jako hlavní dialog a byl Mílou upraven.
- Dialog B a dialog C se pro první verzi nepoužijí.
- Dialog se musí nějak jasně spustit.
- Když zvířátko domluví anglicky, má následovat český překlad.
- Anglický text má být vidět jako bublina u úst nebo blízko mluvící postavy.
- Každá scéna by měla mít ikonu knihy pro slovníček důležitých neintuitivních slovíček.
- Slovníček má být jednoduchý: anglicky - česky, ideálně klikatelné boxíky s přehráním.
- Dokument může fungovat jako výměna návrhů: Mílovy poznámky a Adamovy poznámky se budou opakovaně doplňovat, dokud scénář nebude zralý na programování.
- Interakce a grafika mají být hezké, ale rozsah má zůstat realistický. Neprogramujeme hru 8K.

## Mílovy poznámky z nové

Český překlad jen mluvené slovo. Další menší poznámky v textu. Ještě třeba dořešit hlasy postav v angličtině. Benji a Bunny by zůstali z původních scén, třeba přidat mladý ženský hlas Fiona, hlubší mužský jezevec a mladý nejlépe dětský Sunny...

## Proč se scéna hodí

Scéna přirozeně zavádí osoby a skupinu:

- `I am` přes vlastní představení,
- `we are` přes kamarády,
- `too` přes připojení ke skupině,
- `going / lake / together` přes cíl další cesty.

Nemusí se nic vysvětlovat gramaticky. Dítě jen vidí, kdo mluví, a slyší krátké opakované věty.
