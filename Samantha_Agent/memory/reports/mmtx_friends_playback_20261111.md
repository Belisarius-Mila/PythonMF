# MMTX — jednotný přehrávač Přátel1–4

Přátelé nyní místně používají tři stejné režimy jako Cesta k jezeru: CZ vypnuto (pouze anglický text/zvuk), CZ text (český překlad bez českého zvuku), CZ text+hlas (po angličtině následuje čeština). Každá příběhová replika čeká na ruční Next. Repeat zopakuje právě aktuální repliku. Tři režimy se uchovají mezi čtyřmi kapitolami; optional localStorage nesmí přehrávač zablokovat.

## Čtyři části a herní chování

1. Benji/Bunny: devět původních replik jednotlivě, každá s CZ textem a původní EN/CS MP3. Po Review zůstává slovníček a možnost dalšího obrazu.
2. Sova: tři úvodní repliky jednotlivě, potom původní počítání. Jednotlivé kliknutí na objekty/čísla a palec spouští jednu EN/CS hlášku; při mluvení je herní vstup blokovaný. Český text čísel má správné tvary pro jablka, slunečnice a prasátka. Nápověda a závěrečný pokyn mají EN/CZ text a ruční Next.
3. Rozhovor po počítání: dvě původní repliky jednotlivě s pevnými stopami. Na terč se přejde až po Next za poslední replikou.
4. Barvy: dva přeložené úvodní pokyny jednotlivě, potom původní hra. Barevné zadání a Try again jsou jednou hláškou po uživatelově herním kliknutí. Excellent i závěrečné Great job čekají na Next; teprve potom pokračuje původní vizuální výsledek a další zadání. Tři HouseBunny snímky zůstávají animací jedné hry.

Slovníčky respektují režim i při vyslovení slovíčka. V EN-only režimu ukazují anglická hesla, při zapnuté češtině i překlad. Původní nasčítané bubliny nahrazuje jedna aktuální replika pod obrazem. Lesní škola, houby, Cesta k jezeru a ostatní portály zachovávají svůj dosavadní běh.

## Audio a bezpečné přehrávání

Nový friends_player.js používá jednu aktivní zvukovou cestu, token generace a samostatné čekání na Next. Návrat zastaví Audio/speechSynthesis, odpojí callbacky a ukončí pending promise jako zrušenou. Chyba angličtiny neodemkne Next ani se neobejde českým přepínačem; Repeat umožňuje nový lokální pokus. Vypnutí češtiny zastaví probíhající CS a pokračuje až po dokončené angličtině. Není autoplay další repliky.

Původní MP3 se negenerují ani nepřepisují: 27 pevných audio vazeb základních dialogů/návodů a čtyři původní české soubory soví nápovědy. Sova EN, slovíčka a hra s barvami nadále používají browser speechSynthesis tam, kde není pevná stopa; nové české herní texty používají stejnou systémovou cestu. Aplikace nevolá nové placené cloudové TTS API a nepotřebuje nový API klíč ani službu. Skutečný hlas závisí na hlasové výbavě prohlížeče/zařízení; není tvrzením, že jsou všechny systémové hlasy totožné s Azure hlasy šestky.

## Rozložení a ověření

Přehrávač je pod obrazem. Při aktivních Přátelích má celá karta výšku100svh, zmenšitelnou oblast obrazu a automatickou oblast titulků/ovládání. Obrazová oblast zachovává poměr1407/768, takže procentní hotspoty zůstávají souhlasné s původní ilustrací. Nová story-viewport vrstva mimo Přátele zachovává původní blokové rozložení.

40 cílených testů OK / 4,798 s a rychlá statická brána OK. Nové testy kontrolují všechny režimy, EN→CS, stop během CZ, EN/CS chyby a Repeat, opožděný callback, zrušení pending Next, hlas prohlížeče, nedostupné localStorage a celý průchod čtyřmi kapitolami s původními hrami. Dva nové unittesty jsou zahrnuté v kanonické plné bráně.

Skutečné místní Safari ukázalo první repliku1/9 v EN-only režimu a potom CZ text, dostupný Next a stav5/9 s překladem. Screenshot potvrdil celý obraz i všechny prvky ovládání v okně. Uživatel mezitím ovládal tutéž kartu, proto další automatické klikání nebylo vynucované. Nejde o výslovnou lidskou hlasovou přejímku, veřejné nasazení nebo fyzický iPhone test.

Plná místní brána: 2991 testů OK (5 SKIP), testy 618,242 s / jednotkový krok 624,1 s. Po zahájení této brány byla doplněna izolovaná pojistka Repeat/jazykového přepínače během vítězné fanfáry a zachován původní slovníček Cesty k jezeru; po těchto drobnostech znovu prošlo všech 40 cílených testů a rychlá statická brána. Všechny čtyři webové soubory (HTML, hlavní JS, nový player, CSS) mají bajtově shodný mirror. Původní obrázky a audio beze změny.

Změna zůstává pouze v Datově worktree data/parallel-20261104. Main a služby nedotčené, nové p+n nezadané. Další krok po místním checkpointu: Mílova přejímka ovládání/hlasů a případná samostatně schválená publikace.

## Servisní brána a oprava testu

První účtenka 504e36351eba4bb2b6f6b53e90977f22 skončila attention / push_state=uncertain / deployment_state=not_started. Read-only git ls-remote potvrdilo GitHub f6770814, main d35e81a6 zůstal čistý a neodeslaný.

Rozhodnutí: Plná servisní brána3487 testů /607,383 s měla právě jednu chybu: nový Friends test hledal Node jen v PATH služby. Používá nyní existující scripts.cockpit_quality_gate.node_binary() a sám vynucuje systémový PATH. Žádná instalace, restart, změna přehrávače ani vyřazení testu. Původní job/účtenka se neopakuje; po opravě a přesném novém auditu bude nové předání se suffixem v2 v již schváleném rozsahu p+n.

Další krok: Dokončit cílenou kontrolu se servisním PATH a statickou bránu, uložit opravu, zarovnat čisté profily a předat nový přesný balíček jednou přes submit_release(wait=True).

Navrhované další kroky: Po nové konečné účtence ověřit GitHub/Pages a veřejné bajty; fyzická hlasová a iPhone přejímka samostatně.

Technický důkaz: Po opravě 40 cílených testů se systémovým PATH OK /5,417 s, Data2/2 OK /0,366 s, obě statické brány OK. Původní soukromý gate log zachovaný; veřejná bezpečná účtenka v mmtx_friends_playback_release_attempt1_20261111.json. MMTX zdroje a původní MP3/obrázky se opravou testu nemění.

## Konečný veřejný výsledek

### 2026-11-11 20:46 CET — Veřejné vydání ověřené po neurčité účtence

Hotovo: Dva main commity d35e81a6 a2106bead jsou odeslané; Přátelé1–4 se třemi režimy a ručním Next/Repeat jsou veřejně nasazené. Původní hry, MP3 i ilustrace zachované, oba webové kořeny shodné.

Rozhodnutí: Původní job504e3635 skončil na servisním Node/PATH testu před pushem; po přesné opravě a novém auditu vznikl nový request data-mmtx-friends-playback-44bfbb5f-20261111-v2, jobae8ee1749c0399f64e2941459ca4bda3. Ten potvrdil push a plnou bránu, ale uzavřel se attention s deployment_state=uncertain ještě za běžícího Pages workflow. Žádný další release/push/dispatch se nespouštěl. Adam pouze read-only počkal na přesný běh43090037585 a ověřil jeho úspěch, deployment a veřejné bajty. Původní strojové účtenky se nepřepisují ani nevydávají za completed.

Další krok: Mílova přejímka veřejného ovládání a hlasů ve čtyřech částech Přátel.

Navrhované další kroky: Fyzický iPhone samostatně. Předčasný návrat Pages publisheru zůstává procesním rizikem pro budoucí vydání; tato změna ho neopravuje ani neprovádí nové vydání.

Technický důkaz: Centrální Terra6.1/high, 2 commity, push_state=confirmed, plná publikační brána3487 PASS /639,7 s. Přesný workflow43090037585 completed/success, head2106beadf0d10afdc53993c7f40a7868da9b34be; deployment7719962425 success v19:45:38Z. HTTP4/4 exact: HTML8557 B, hlavní JS116987 B, CSS34879 B, player7592 B; celkem168015 B. HTTPS kontrola s ověřovaným certifi CA; žádné vypínání TLS ověřování. Registrované GitHub/deploy audity potvrdily main/origin aligned, 0 čekajících commitů, oba profily aligned a čisté. Main zůstává čistý, konečný doklad se ukládá jen v Data. Žádný restart Cockpitu ani nový placený obrazový/TTS/vývojový pokus. Před/po snapshot chráněných služeb v dokončené účtence chybí, netvrdit tuto formální přejímku. Safari fyzický proklik po vydání ani hlasová/iPhone přejímka nebyly provedené. Reporty mmtx_friends_playback_release_attempt1_20261111.json, mmtx_friends_playback_release_v2_20261111.json a mmtx_friends_playback_public_20261111.json.

Veřejná verze: https://belisarius-mila.github.io/PythonMF/index.html?scene=intro4&release=2106bead
