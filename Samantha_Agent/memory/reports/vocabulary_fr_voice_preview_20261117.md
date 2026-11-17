# Vocabulary FR — ukázka ženského a mužského hlasu

Stav: ukázka hotová, čeká výběr hlasu uživatelem. Navazuje na obsahový checkpoint
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

Podklad pro další výrobu, nikoli souhlas s placenými voláními:

- Ve zmrazeném balíčku chybí 904 různých FR klipů a 760 různých CZ klipů.
  Původních 166 existujících českých MP3 je zachovaných.
- Pro oba jazyky dohromady jde o 88 682 odhadovaných účtovaných znaků včetně
  zvolených SSML prosody tagů. Samotná francouzština má 47 737 těchto znaků.
- Čerstvý veřejný ceník Azure pro germanywestcentral: 15 USD / 1M znaků.
  Odhad před daní a bez předpokladu bezplatné kvóty či slev je 1,33023 USD
  za vše chybějící, případně 0,716055 USD jen za FR. Nejde o vyúčtování účtu.
- Azure adaptér dosud nepovoluje FR hlasy; společnou úpravu vlastní Will.
  Žádná placená výroba ani automatická náhrada poskytovatele zde neproběhla.

Další krok: uživatel vybere hlas podle ukázky. Pak připravit konkrétní výrobní
postup a odsouhlasit cenu celé zbývající knihovny; zachovat hotové MP3, identitu
textů a pravidlo bez automatického opakování nejasného požadavku.

Ověřené veřejné podklady:

- [Podporované hlasy Microsoftu](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Způsob účtování znaků](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech)
- [Veřejná cenová odpověď Azure](https://prices.azure.com/api/retail/prices?%24filter=meterName%20eq%20%27S1%20Neural%20Text%20To%20Speech%20Characters%27%20and%20armRegionName%20eq%20%27germanywestcentral%27)
