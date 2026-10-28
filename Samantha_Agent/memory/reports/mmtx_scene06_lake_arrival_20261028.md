# MMTX — scéna 6: Příchod k jezeru

Stav 2026-10-28 13:35 CET: místní pracovní náhled, audio blokované externí
službou. Scénář a implementaci na výslovný pokyn Míly připravila Terra 6.1;
Adam zkontroloval integraci. Žádný nový push, Pages deployment ani nasazení
Cockpitu. Předchozí místní dokumentační commit Camina e8375e7e zachovaný.

## Rozsah

Vychází z Mílou schváleného TXT
MMTX_Cesta_k_jezeru_scena_06_Prichod_k_jezeru_scenar_20261028.txt v Downloads.
Bez options znamená bez čtyř volitelných setkání Tilly/Pip/Lulu/Momo, bez
zahrádky s jejich výběrem a bez jejich varianty závěrečného vtipu.

Hlavní cesta má 72 EN/CZ replik: loučení s Loganem, příchod k jezeru,
obláčková ouška, Daisy, Freddie s listovým bubínkem, Dotty, Ollie s mušlemi,
čtyři zvukové bublinky, krátká melodie a zakončení. Přechod na scénu 6 se
objeví až po dokončení mostu ve scéně 5. Návrat do 5 funguje i před
spuštěním audio brány; odkaz na neexistující scénu 7 nepřibyl.

Ovládání zachovává EN / EN + CZ, Repeat a Next po jedné replice. Next
nepřeskakuje povinný dotyk. Změna karty nebo odchod ruší právě běžící audio
a zvukové efekty. Chyba řeči nezamkne průchod. Manifest odkazuje jen na
existující MP3, takže známé chybějící stopy nevyvolávají desítky HTTP 404.

## Ilustrace a meze zpracování

Čtyři nové široké ilustrace jsou ve složce scene06_lake_arrival jako
arrival.webp, duckfrog.webp, flyotter.webp a final.webp. Vestavěný ImageGen
použil referenci závěrečného loučení z páté scény. Adam všechny čtyři obrazy
vizuálně zkontroloval: pět původních postav, oblečení a Brunova lampa jsou
zachované; Logan u jezera není. Nová zvířátka jsou viditelná a odpovídají
hlavní cestě. Přesné konečné prompty, reference a cílové soubory jsou
zapsané v image_prompts.txt v obou kopiích aplikace. Použitá dovednost:
imagegen; režim built-in, bez CLI/API fallbacku.

Obrazy jsou statické. Nejsou rozanimovaná všechna komická gesta ze scénáře;
samostatná volitelná animace odrazu také není implementovaná. Písnička je
krátká místní syntetická melodie s postupným rozsvícením čtyř bublin,
ne hotová vokální hudební produkce ani přirozené zvuky všech zvířátek.

## Blokátor audia

Existují pouze EN stopy 000 a 001; obě dekódoval FFmpeg. Očekávaný celkový
počet je 144 (72 EN a 72 CZ), chybí 142. První dávka Edge TTS skončila
NoAudioReceived. Jediná další, sériová ověřovací generace s již doloženým
kompatibilním endpointem vrátila HTTP 429. Další síťové pokusy neprobíhají.

Původní postavy zachovávají přiřazení podle bezprostředně předcházející
scény 5, včetně Bruna/Guy. Omylem vzniklý nevybraný Daniel není součástí
veřejných souborů ani manifestu. Nová zvířátka mají navržené přiřazení
Daisy/Ana, Freddie/Guy, Dotty/Jenny, Ollie/Andrew; CZ používá Vlastu.
Náhrada původních hlasů nebyla potvrzená ani provedena.

build_scene06_audio.py obsahuje pouze výslovné --apply a offline --check.
Před sítí kontroluje dostupnost FFmpeg a všechny existující vazby zvuku
na text, hlas, tempo a SHA-256; nesoulad zastaví zpracování bez přepisu.
Generuje sériově a při selhání skončí bez automatického opakování. Úspěšné
nové stopy synchronizuje do mirroru. --check v nynějším stavu správně končí
exit 1 a zprávou „Audio 2/144; chybí 142“; nejde o úspěšnou audio přejímku.

Tento náhled nelze označit za dokončenou hlasovou hru pro dítě, které neumí
číst. Míla dostal volbu zachovat původní hlasy do odblokování služby, nebo
pro první přejímku potvrdit dočasné místní hlasy. Do odpovědi se zachovávají
původní hlasy a žádná další generace neběží.

## Ověření a místní průchod

- Všech 71 testů test_mmtx*.py PASS, 2,384 s. Nová sada má čtyři testy:
  skutečný JS stavový průchod s řízeným DOM/audiem, přerušení a chyba audia,
  offline chování builderu a odmítnutí změněného vstupu, mirror/navigace
  a pomocný konzervativní výpočet dotykové geometrie.
- Node kontrola syntaxe PASS. Obrázky a dvě existující MP3 jsou načitatelné;
  docs a MatysekANJ/web_mmtx mají byteově shodnou scénu 6.
- Rychlá kanonická statická brána PASS po projektovém zápisu. První
  whitespace kontrola zachytila nadbytečné prázdné řádky na konci tří
  dokumentů; byly opravené před úspěšným závěrečným během.
- Na místním loopback HTTP serveru 8802 vrací všech 13 kontrolovaných
  zdrojů HTTP 200 a přesné bajty z workspace, včetně návaznosti a médií.
- Skutečný browser/Safari/iPhone, vizuální geometrie rozhraní a lidský
  poslech NEOVĚŘENO. CUA inventory neobsahuje prohlížeč a vytvoření IAB
  vrátilo „Browser is not available: iab“. Model DOM ani výpočet geometrie
  nejsou důkazem skutečného browserového prokliku.

Náhled na Macu: http://127.0.0.1:8802/scene06_lake_arrival/

Pro opětovné spuštění ze Samantha_Agent:

```sh
.venv/bin/python -m http.server 8802 --bind 127.0.0.1 --directory ../docs
```

Přejímka: zpět ještě před startem; začít klepnutím; přepnout jazyk a Repeat;
projít šest povinných dotyků až do poslední repliky, získat právě čtyři
bublinky a zopakovat závěrečnou melodii. Ověřit přechod 5 → 6 až po dokončení
a návrat 6 → 5. Bez volitelných postav a bez dveří do scény 7.

Bezprostřední další krok: Mílův první obrazový/textový průchod a rozhodnutí
o hlasech. Po doplnění všech stop následuje samostatná hlasová a fyzická
přejímka; případné zveřejnění vyžaduje samostatný pokyn.
