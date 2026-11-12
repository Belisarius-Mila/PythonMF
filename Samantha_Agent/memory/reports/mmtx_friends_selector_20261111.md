# MMTX — Přátelé: čtyři číslované části

**Vydané na GitHub Pages:** main a445cb4338a88df4858e3d8a7ea524e73b3d57c2, Terra job aad89ff92930ad5b96ddc677e44fb736 completed, push/deployment confirmed. Plná brána3482 PASS / 531,1 s, Pages run43048031652 / deployment7714069369. Veřejné HTML/JS/CSS3/3 byte/SHA exact, potvrzené čtyři části a samostatná škola.

Míla výslovně upřesnil, že Přátelé mají jen čtyři části. Tlačítko Friends / Přátelé otevře okno s čísly 1–4 v mřížce 2×2. Lesní škola zůstává pod vlastní ikonou a v nabídce Přátel není. Toto rozhodnutí nahrazuje původní pracovní odhad pěti kapitol z cff31d75.

| Číslo | Část | Obraz / runtime |
| --- | --- | --- |
| 1 | Benji a Bunny | BenjiBunnyScene.png / benjiBunny |
| 2 | Počítání se sovou | MeetingOul1.PNG / owlGarden |
| 3 | Rozhovor u sovy | MeetingOul2.PNG / owlGarden outro |
| 4 | Hra s barvami | HouseBunny1–3.PNG / houseBunny |

Trojka má přímý vstup do původního rozhovoru a pokračování do barev bez opakování počítání. Používá cleanup a sequenceId. Tři fáze terče tvoří jedinou čtvrtou část. Dialog má nativní fokus, křížek a Escape. Odstraněn pátý button i jeho přepínání, čísla mimo1–4 se odmítnou. CSS používá vlastní dvousloupcový friends-scenes bez změny rozložení nabídky Cesta k jezeru1–6.

Ověření: 20 cílených testů a rychlá statická brána OK. Oba HTML/JS/CSS kořeny shodné, git diff --check OK. Skutečné místní Safari zobrazilo čtyři tlačítka2×2, zavření a funkční samostatnou ikonu Lesní školy. Předchozí přejímka všech čtyř vstupů zůstává platná; mapování1–4 se opravou neměnilo. Obrázky/audio/texty příběhu zachované, existující testy jen aktualizují cache verzi. Bez nových obrazových/TTS či placených vývojových volání.

Míla výslovně autorizoval commit a p+n Terrou. Tento přípravný Data checkpoint ještě nedokládá publikaci; následuje bezpečná integrace do čistého main a jedno registrované submit_release(wait=True), project-mmtx→GitHub Pages. Žádný restart Cockpitu v cíli Pages. Fyzická iPhone a veřejná přejímka po vydání zůstávají samostatné.

## Výsledek p+n

Jediné předání submit_release(wait=True), request data-mmtx-friends-four-07488254-20261111-v1, cílový project-mmtx→Pages a centrální Terra6.1/high. Jeden integrovaný main commit po čistém8255ff9c, který byl předem aligned s origin. Žádný nativní pomocný agent, nové TTS/obrázky ani opakování publikace. Oba čisté profily byly zarovnané na a445cb43.

Main20 cílených testů OK / 0,463 s a rychlá statická brána OK. Povinná publikační brána3482 PASS / 531,1 s. Pages deployment7714069369 z run43048031652 potvrzuje přesný a445cb43 a HTTP200, chráněné služby beze změny. Následná veřejná kontrola3/3 porovnala HTML7737 B, JS115943 B a CSS33207 B, celkem156887 B, přesné bajty a SHA-256. Parsování veřejného HTML potvrdilo čísla1,2,3,4, žádnou pětku ve friendsScenes a vlastní forestSchoolPortalButton; veřejné CSS potvrdilo2×2.

Skutečné Safari bylo vizuálně ověřené místně před publikací. Po publikaci GUI nebylo dostupné(cgWindowNotFound), takže produkční fyzický proklik a iPhone zůstávají Mílovi. Závěrečné záznamy jsou pouze místní Data checkpoint pro další balíček, vydaný main se nepřepisuje.

Produkce: https://belisarius-mila.github.io/PythonMF/index.html?scene=intro4&release=a445cb43

Konečný registrovaný GitHub audit: main/origin aligned na a445cb43, main čistý a 0 čekajících commitů. Human–Adam i Knihovna čisté a aligned na stejném headu.
