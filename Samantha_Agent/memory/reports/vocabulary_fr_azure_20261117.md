# Vocabulary FR — kompletní soukromé audio Henri / Vlasta

Stav: `ready_for_integration`, hotový uzavřený soukromý balíček v003.
Míla schválil přesný plán a Azure limit 2 USD bez daně. Výrobní kód je připnutý
checkpointem `49432092`; konečná soukromá účtenka dokládá také závěrečný zápis.

Hotovo:

- 1 664 nových úspěšných Azure požadavků: 440 různých FR slovních klipů,
  464 FR vět, 303 CZ slovních klipů a 457 CZ vět. Původních 166 českých MP3
  je zachovaných bajtově. Henri / Vlasta, oba při tempu −10 %.
- Všech 464 karet má všechny čtyři zvukové kanály: 1 856 odkazů, 1 830 různých
  MP3. Manifesty words/sentences i audioStatus jsou complete.
- Všech 1 830 MP3 plně dekódováno v uzavřené v002. Finální v003 má všechny
  mediální soubory přesně bajtově shodné; shoda doložená úplnými SHA manifesty.
- Rezervovaných 88 682 účtovaných znaků včetně SSML, odhad spotřeby
  1,33023 USD bez daně při ověřené sazbě 15 USD/1M. Pod limitem 2 USD;
  nejde o ověřené konečné vyúčtování účtu. Žádný neúspěšný nebo opakovaný
  požadavek, žádné automatické přepnutí poskytovatele.
- Dva úvodní placené klipy byly součástí stejného plánu. Poté devět pracovních
  bloků do 10 000 znaků; společná účtenka držela celý rozpočet napříč běhy.
- Zachované všechny texty, UID, obrazy a 898 obrazových vazeb u 464 vět.
  Původní Janin CSV zůstal hashově nezměněný. Osobní stav v payload není.
- Při ověření proti Willovu klientovi byla opravena příliš přísná značka
  sound:colors u pěti barevných karet. Oprava je výhradně v nové katalogové
  revizi a konfliktech procvičování; žádný text, hlas nebo MP3 se kvůli ní
  neměnil ani znovu negeneroval. Verze v001 a v002 zůstaly zachované.
- Čistě datová přejímka se zmrazenými model.js/practice.js od Willa přijala
  všech 1 856 zvukových odkazů, 464 záznamů procvičování a 898 obrazových
  vazeb. Pro všech 464 karet se sestavily čtyři vzájemně slučitelné možnosti.
  Nejde o tvrzení, že proběhl fyzický proklik nebo poslech v Safari/iPhonu.

Technický a bezpečnostní důkaz:

- Převzatý přesný Willův patch Henriho; adaptér má 11 syntetických testů PASS.
  Výrobní nástroj a související obsahové testy mají dohromady 45 testů PASS.
- Programová validation-v3 brána výrobního checkpointu: 152 testů PASS,
  shoda zdrojů po commitu ověřená převzetím podepsané účtenky. Finální reporty
  projdou navazující programovou branou před závěrečným checkpointem.
- Každá rezervace trvale uložená před POST. Nejistý stav blokuje další přenos;
  hotové soubory se nikdy automaticky nevyrábějí znovu. Kód, souhlas, plán,
  zdrojový balíček a konfigurace byly během jednotlivých běhů připnuté.
- Výstupy jsou výhradně mimo Git a docs. Balíček v003 má vlastní soupis
  souborů s SHA/velikostí, katalogový a obsahový digest, kódový commit,
  výrobní plán/souhlas/účtenku a explicitní redakční změnu pěti konfliktů.
- publicPromotionApproved=false. Data nic nepushoval, nepublikoval, nenasazoval
  ani nerestartoval. Skutečné texty, média a podrobné účtenky nejsou v commitu.

Další krok: Will převezme konkrétní v003 a kódové checkpointy podle nového TXT,
provede soukromou klientskou integrační přejímku a jako jediný zapisovatel
aktualizuje kanonický FR handoff, stávající TVBCP, ACTIVE/INDEX a projektovou
paměť. Potom fyzický poslech/proklik a případné samostatně schválené zveřejnění.

[Veřejná sazba Azure](https://prices.azure.com/api/retail/prices?%24filter=meterName%20eq%20%27S1%20Neural%20Text%20To%20Speech%20Characters%27%20and%20armRegionName%20eq%20%27germanywestcentral%27)
