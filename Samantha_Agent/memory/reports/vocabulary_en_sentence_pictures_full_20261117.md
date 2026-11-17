# Vocabulary EN — úplná mapa obrazových pojmů ve větách

Stav2026-11-17: lokální vývoj analogický Datově italštině. Vydaný pilot
d4c986ec zůstává výchozím bodem; nové p+n není součástí tohoto kroku.

Všech512 aktivních vět (492 Slovíček/20 Interakcí) má dohromady1255 vazeb
na512 stávajících významů. Počet vět podle délky mapy:1 pojem62,2 pojmy210,
3 pojmy191,4 pojmy45,5 pojmů4. Neaktivních10 karet se neaktivuje.
Původních20 pilotů včetně redakčních poznámek zůstává přesně zachovaných.

Každá další věta byla významově revidovaná. Tvar ve větě je svázaný s přesným
UID a EN/CZ významem; samotná shoda řetězce nestačí. Rozlišují se například
orange/ovoce a barva, drink/sloveso a nápoj, right/směr/správný/pravá strana,
open/sloveso a přídavné jméno. Ustálené výrazy se nedělí na nesouvisející
významy. U otázky What do you want to do? je do navázané na druhý, plnovýznamový
výskyt. Nedoplňují se falešné vazby runs/řeka→běhat, looks happy→dívat se,
catch the bus→chytat míč nebo little water→malý. Shodné obrázky deep/valley
nejsou v jedné větě zdvojené. Přesné rozhodnutí pro jednotlivé věty zůstává
v soukromém redakčním přehledu, veřejná metadata nesou jen ověřené vazby.

Builder navíc odmítne neúplné pokrytí aktivního katalogu. Zachovává dosavadní
kontroly aktuálního znění EN/CZ, referencí, doslovných tvarů, UTF16 pozic,
pořadí, jedinečnosti a existence skutečných obrázků. Nová aktivní karta tedy
vyžaduje i revidovanou mapu své věty. Stávající runtime funguje beze změny:
ve větné fázi1–5 miniatur s EN názvy, ve slovní původní velká karta, stejný
přehrávač a nejvýše10 přednačtených náhledů. Osobní filtry a ruční učení
zůstávají zachované. Nejsou nové obrázky, náhledy, TTS, věty ani jejich změny.

Ověření:28 cílených Python testů PASS, včetně spuštění skutečného JS
controlleru. Nové regrese pokrývají chybějící aktivní větu, přesný hash20 pilotů,
významové výjimky a návrat nově pokryté juice věty na původní slovní kartu
se stejným Audio přehrávačem. Export má512 vět/1255 vazeb. Finální programovou
doménovou bránu, otisky a lokální commit určuje výhradně
`data/private/vocabulary_en_sentence_pictures_full_20261117/completion.json`.
Plná testová sada se nespouští. Fyzická telefonní a obsahová/akustická přejímka
zůstávají otevřené; automatické testy ji nenahrazují.

Datův aktivní IT worktree nebyl změněný ani integrovaný. Aktualizován kanonický
handoff, projektová paměť, index/ACTIVE a existující obecný TVBCP. Nový EN TVBCP
nevzniká. Další krok je samostatně autorizované p+n úplné anglické mapy.
