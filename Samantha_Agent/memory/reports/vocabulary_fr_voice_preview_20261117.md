# Vocabulary FR — ukázka ženského a mužského hlasu

Stav: Míla vybral Henriho, fr-FR-HenriNeural, tempo −10 %. Následně schválil
Azure výrobu do 2 USD bez daně; celá knihovna je hotová a soukromě ověřená.
Dokončení dokládá reports/vocabulary_fr_azure_20261117.md. Navazuje na obsahový checkpoint
`a119e84f`; uzavřený obsahový balíček v001 se nemění. Kanonické FR dokumenty
nadále spravuje Will, tento redigovaný report je obsahový podklad k předání.

Hotovo:

- Dva syntetické francouzské hlasy: Denise a Henri, stejné tempo −10 % a přesně
  stejný vlastní necitlivý demonstrační text o 206 znacích. Neodesílala se Janina
  soukromá slovní zásoba ani její osobní příznaky.
- Dva úspěšné požadavky přes stávající registrovaný Edge generátor; žádná změna
  endpointu, nový poskytovatel, opakování nejistého požadavku ani Azure syntéza.
- MP3 trvají 25,920 s a 25,488 s. Obě byly plně dekódované bez chyby a mají
  připnuté SHA-256. Zachované samostatně mimo již předaný balíček.
- Lokální porovnávací stránka se dvěma přehrávači v Downloads. Média jsou
  relativní, bez autoplay a bez síťové závislosti při poslechu. Při přehrání
  jednoho hlasu stránka pozastaví druhý. Struktura a soubory jsou ověřené;
  fyzická přejímka v Safari a vlastní poslech patří uživateli.
- Soukromá účtenka zachycuje explicitní autorizaci ukázky, text/hlasy/tempo,
  stavy před požadavkem, výsledné soubory a otisky. Do Gitu patří jen tento report.

Původní cenový podklad před schválením výroby:

- Ve výchozím zmrazeném balíčku chybělo 904 různých FR klipů a 760 různých CZ klipů.
  Původních 166 existujících českých MP3 je zachovaných.
- Pro oba jazyky dohromady jde o 88 682 odhadovaných účtovaných znaků včetně
  zvolených SSML prosody tagů. Samotná francouzština má 47 737 těchto znaků.
- Čerstvý veřejný ceník Azure pro germanywestcentral: 15 USD / 1M znaků.
  Odhad před daní a bez předpokladu bezplatné kvóty či slev je 1,33023 USD
  za vše chybějící, případně 0,716055 USD jen za FR. Nejde o vyúčtování účtu.
- Při přípravě ukázky Azure adaptér FR hlasy nepovoloval; doplnění následně
  dokončil Will. Samotná hlasová ukázka placenou Azure syntézu nepoužila.

Aktuální další krok: Will převezme nový uzavřený soukromý balíček v003, provede
klientskou integrační přejímku a aktualizuje kanonické FR dokumenty. Publikace
a fyzická přejímka jsou samostatné otevřené kroky.

Ověřené veřejné podklady:

- [Podporované hlasy Microsoftu](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Způsob účtování znaků](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech)
- [Veřejná cenová odpověď Azure](https://prices.azure.com/api/retail/prices?%24filter=meterName%20eq%20%27S1%20Neural%20Text%20To%20Speech%20Characters%27%20and%20armRegionName%20eq%20%27germanywestcentral%27)

## Rozhodnutí a příprava výroby — 2026-11-17

- Míla po hlasové ukázce výslovně zvolil Henriho. Volba se uložila samostatně,
  původní uzavřený obsahový balíček ani ukázky se nepřepisují.
- Připravený konkrétní soukromý výrobní plán: 1 664 nových klipů, reference všech
  karet a kanálů, připnuté texty/hlasy/tempo, 166 zachovávaných MP3 s otisky,
  9 pracovních bloků do 10 000 účtovaných znaků. Plán nebyl odeslaný.
- Plán je vázaný na původní bundle digest; změna vstupů vyžaduje nový plán.
  Původní návrh celkového limitu byl 2 USD bez daně. Míla jej následně
  výslovně schválil spolu s přesným plánem. Cenový odhad zůstává 1,33023 USD za vše chybějící.
- V okamžiku volby hlasu Azure adaptér FR nepovoloval. Následný Willův přesný
  patch Data převzal beze změny; společný adaptér znovu nenavrhoval.
- V okamžiku volby hlasu celá výroba ještě neběžela. Následné dokončení je
  uvedené v samostatném Azure reportu; push/publikace/nasazení Data neprováděl.
