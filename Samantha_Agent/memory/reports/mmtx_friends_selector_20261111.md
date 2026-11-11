# MMTX — číselná nabídka Přátelé

Tlačítko Friends / Přátelé otevírá modální okno ve stejném stylu jako Cesta k jezeru. Čísla spouštějí:

| Číslo | Kapitola | Původní obraz / runtime |
| --- | --- | --- |
| 1 | Benji a Bunny | BenjiBunnyScene.png / benjiBunny |
| 2 | Počítání se sovou | MeetingOul1.PNG / owlGarden |
| 3 | Rozhovor u sovy | MeetingOul2.PNG / owlGarden outro |
| 4 | Hra s barvami | HouseBunny1–3.PNG / houseBunny |
| 5 | Lesní škola | ForestSchool1.PNG / forestSchool (12 lekcí) |

Míla odhadoval pět scén, ve skutečnosti existuje více jednotlivých obrázků a některé jsou přechodové fáze jedné hry. Proto jde o pět smysluplných kapitol; pátá navazuje na Lesní školu, která zůstává dostupná i vlastním tlačítkem. Odeslaná upřesňující otázka zůstala bez odpovědi a po přiměřeném čekání byl tento předpoklad výslovně oznámen. Nejde o potvrzené nové obsahové rozhodnutí.

Trojka používá volitelný parametr owlOutro v existujícím setScene, zachovává cleanup/sequenceId a spustí původní rozhovor s jeho pokračováním do barev; nezačne znovu počítání. Ostatní vstupy používají původní reset a start funkce. Čísla fungují jen nad otevřeným dialogem a rozcestím, takže opakovaný klik ani pozdní odemčení audia nepřepne jinou právě otevřenou scénu. Dialog má nativní fokus, zavírací křížek a Escape.

Změněny jen index.html/script_intro_v2.js v docs a shodném mirroru; využívá se původní CSS. Aktualizovaná cache verze HTML/JS a odpovídající tři starší testové reference. Žádný přepis obrázků, audia, textů příběhu nebo systémových služeb. Hlavní checkout se nemění.

Ověření: 20 cílených testů OK / 0,498 s; rychlá statická brána OK a git diff --check OK. Skutečné Safari přes místní file URL zobrazilo čitelnou nabídku a prokliklo všech pět odpovídajících obrazů, všechny návraty, Escape a znovuotevření. Nabídka zůstala otevřená pro Mílu. Místní HTTP server nebyl dostupný a nebyl znovu spouštěn; toto není HTTP/produkční ani iPhone přejímka. Žádné modelové, audio ani jiné placené volání.

Toto je místní vývojový checkpoint Data na data/parallel-20261104. Nové p+n nebylo zadané ani spuštěné. Další krok: Mílova přejímka rozdělení a nabídky; případná publikace samostatně.
