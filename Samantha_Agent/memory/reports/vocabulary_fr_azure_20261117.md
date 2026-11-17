# Vocabulary FR — schválená výroba Henri / Vlasta

Stav: výrobní základ připravený; spuštění a skutečný výsledek dokládá navazující
soukromá účtenka. Míla výslovně schválil celý přesný plán a Azure limit 2 USD
bez daně. Volba FR hlasu je Henri, CZ hlas zůstává Vlasta; oba při tempu −10 %.

- Převzatý přesný Willův patch adaptéru a syntetických testů; samotný adaptér
  má 11 testů PASS. Data nemění jeho návrh ani Willovu hlavní pracovní kopii.
- Soukromý plán obsahuje 1 664 nových klipů a zachovává 166 existujících českých
  MP3. Původní uzavřený obsahový balíček v001 se nepřepisuje.
- Čerstvý veřejný ceník i lokální region znovu odpovídají schválenému podkladu:
  15 USD / 1M účtovaných znaků, 88 682 znaků, odhad 1,33023 USD bez daně.
  Rezervovaný text zahrnuje SSML; nepředpokládá se kvóta zdarma ani sleva.
- Nový obsahový výrobní pomocník zpracuje jeden blok do 10 000 znaků, zároveň
  drží společný rozpočet přes všechny bloky. Před každým voláním trvale uloží
  rezervaci. Nejistý stav zastaví další přenos a automaticky se neopakuje.
- Kód, plán, schválení, zdrojový balíček a místní konfigurace jsou připnuté.
  Hotové zvuky se kontrolují podle otisku a nikdy se znovu nevyrábějí.
- První dva placené klipy jsou součástí schválené sady, ne dodatečná ukázka.
  Po ověření FR i CZ pokračuje zbytek devíti plánovaných pracovních bloků.
- Nová kompletní verze vzniká odděleně; zachová katalog, obrazy, osobní datovou
  revizi a již hotové soubory. Vzniknou úplné manifesty všech čtyř kanálů.
- Exporty, reálné texty, média, výrobní plán a účtenky zůstávají mimo Git a docs.
  Nový balíček zůstane private/publicPromotionApproved=false.

Will přebírá konkrétní balíček s otisky a klientskou integrační přejímku. Jako
jediný zapisovatel aktualizuje kanonický FR handoff/TVBCP/ACTIVE/INDEX a paměť.
Tento report je obsahový podklad; nedokládá nasazení nebo fyzický poslech.

[Veřejná sazba Azure](https://prices.azure.com/api/retail/prices?%24filter=meterName%20eq%20%27S1%20Neural%20Text%20To%20Speech%20Characters%27%20and%20armRegionName%20eq%20%27germanywestcentral%27)
