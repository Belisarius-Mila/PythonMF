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

## Příprava autorizovaného vydání

2026-11-11 20:18 CET: Míla zadal Terra p+n. Data44bfbb5f integrována do čistého main po f6770814, původní změny zachované. Request data-mmtx-friends-playback-44bfbb5f-20261111-v1; jeden submit_release(wait=True) až po commitu a kontrolách. Tato sekce ještě není účtenkou push/nasazení.

Main integrační kontrola: 40 cílených testů OK / 6,460 s a rychlá statická brána OK. Přesné 8 webových souborů z Data44bfbb5f, přidání jediného testového modulu do současné main brány zachovalo všechny její ostatní moduly.
