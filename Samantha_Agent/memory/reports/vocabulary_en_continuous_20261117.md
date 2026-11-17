# Vocabulary EN — kontinuální procvičování

Stav 2026-11-17 09:15 CET: místní vývoj, bez push/nasazení.

Na velké kartě nabídka Smyčka se dvěma režimy. Slovíčka vždy ukazuje a čte EN
heslo a pod ním zobrazí CZ význam. Věta + slovíčko nejprve ukáže/čte celou EN
větu s CZ překladem, po dočtení a prodlevě ji nahradí EN heslem/CZ významem a
přečte heslo. Po další pauze přejde na další obrázek. Poslední vede na první.
Používá se skutečná posloupnost z aktuálního filtru včetně A–D/obtížných/N.
Výslovně zamíchaná posloupnost se v dalších průchodech sama nepřehazuje.

Ovládání Spustit/Pozastavit/Pokračovat/Ukončit; prodleva1/2/4/6 sekund, default2.
Pokračovat opakuje přerušený úsek od začátku. Stávající ruční Slovíčko/Věta a
jazykový směr se nemění. Návrat zvýrazní poslední miniaturu; filtrovaný přímý
odkaz se vrací do přesné odpovídající galerie, opraveno proti512 místo42.

## Zvuk a přerušení

Další úsek nevychází z odhadnuté délky. Čeká skutečný ended a plnou prodlevu.
Jediný výslovně odemknutý Audio element mění src a volá load pro každý úsek,
i opakování stejného hesla. Tím se nevrací na konec dříve seekovaného souboru.
Per-element autoplay doporučení primárního [WebKit podkladu](https://webkit.org/blog/7734/auto-play-policy-changes-for-macos/).
Staré ended události ignorované, dokud aktuální resource není opravdu ended;
všechny pokračující handlery váže generační token. Timeout90 s chybu pozastaví.
Chybějící/nesouhlasné metadata nebo MP3, play rejection a chyba rovněž zastaví
smyčku na dotčené kartě. Žádný automatický retry/přeskočení ani TTS fallback.
Odchod, historie, nastavení/hra, jiný osobní výběr a bfcache zruší čekání/zvuk.
URL, sessionStorage ani reload smyčku nespouštějí automaticky. Po návratu je
nutné výslovné spuštění. Osobní PINy ani uložená zásoba se nepřepisují.

## Ověření a další krok

12 nových JS scénářů skutečného modulu. Pokrývají filtry a smyčku se3/2/1 kartou,
obě fáze a viditelné překlady, dlouhý zvuk, přesnou prodlevu, opakovaný load,
pause/resume/exit, staré callbacks, historii, nastavení/hru, bfcache/reload,
chybějící metadata/zamítnutí/error/timeout, shuffle a změnu profilu z jiné karty.
Nový test návratu z přímého odkazu nejprve FAIL, po opravě PASS. První revize
odhalila i chybějící explicitní pause při play rejection; opraveno a regresně
ověřeno. Finální programově vybrané důkazy určuje completion.json, nikoli tento
průběžný text. Původní slova/věty, oba audio manifesty i všechny assety zachované.

Safari na samostatném localhost původu skutečně pokračovalo cat→cow→crocodile→crow,
ukázalo větu dog/český překlad a potom dog/pes. Pause/stop zafungovalo. Po opravě
návrat do galerie42 karet místo512, fokus crocodile. Vlastní okno/server zavřené,
původní produkční okno park zachované. Fyzický telefon a akustické posouzení
Mílou tímto potvrzené nejsou. Další krok: samostatně schválené EN p+n.

Samostatný projektový TVBCP nebyl dohodnutý; pokračuje stávající obecný záznam
v architektura_komunikace_samantha.txt a kanonický EN handoff. IT se nemění.
- Finální funkční kandidát prošel programovou bránou115 PASS (validation-v3), včetně všech80 JS scénářů galerie a samostatných kontrol profilů. Dodatečný zápis důkazu projde dokumentační bránou; přesnou shodu zdrojů po commitu doloží completion.json.
