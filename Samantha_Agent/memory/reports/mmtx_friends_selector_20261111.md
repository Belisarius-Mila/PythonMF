# MMTX — Přátelé: čtyři číslované části

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
