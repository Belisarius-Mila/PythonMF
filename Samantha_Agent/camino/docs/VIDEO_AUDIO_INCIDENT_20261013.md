# Camino — obnova spouštění videa se zvukem, 13. 10. 2026

Aktualizováno: 2026-10-13 18:11 CEST. Stav: uživatel hlásí obnovené spouštění; přesná
příčina není potvrzená. Žádný nový build, instalace, render ani nasazení.

## Pozorování na telefonu podle Míly

- Ráno přestalo natáčení videa v Caminu fungovat; restart iPhonu nepomohl.
  Uživatel nehlásí změnu nastavení.
- Běžný Fotoaparát: fotografie a video fungují.
- Camino video se zvukem zůstávalo na „Povol mikrofon pro video se zvukem…“.
- Mikrofon pro Camino je v Nastavení povolený.
- Výslovně tiché video v Caminu se natočilo normálně.
- Samostatný Komentář v Caminu funguje normálně.
- Bluetooth byl zapnutý; sluchátka podle uživatele nebyla připojená, byla
  v boxu. Po vypnutí Bluetooth přes Nastavení a novém otevření kamery
  se video se zvukem spustilo. Uživatel si není jistý, zda stejný krok
  zkoušel i dříve během dne.
- Po opětovném zapnutí Bluetooth video se zvukem dál běží.

Nejnovější uživatelský výrok potvrzuje spuštění. Ukončení, uložení a
slyšitelný zvuk posledního klipu nejsou samostatně potvrzené. Aktuální
instalovaný build, iOS, stav zvukových tras a přímý telefonní log nejsou
k dispozici. Nevydává se úplný fyzický PASS ani potvrzená kořenová příčina.

## Co z toho plyne

Pozorování zužují závadu na přípravu zvuku pro video. Samostatný mikrofon
a tiché video fungují; vypnuté oprávnění není doložená příčina. Samotné
zapnuté Bluetooth není dostatečnou podmínkou závady, protože poslední
pokus funguje i s ním. Pracovní hypotéza je dočasně zaseknutá příprava
zvukového vstupu či zachytávací relace. Série změnila více podmínek:
Komentář/přehrávání, nové otevření kamery, tiché video a Bluetooth.
Nelze určit, který krok obnovu způsobil, ani vyloučit Bluetooth jako
případný spouštěč v dřívějším odlišném stavu.

## Čtení kódu

`CameraCaptureController.prepareVideoSound` nastaví uvedenou hlášku před
`AVCaptureDevice.requestAccess(for: .audio)`. Při úspěšném oprávnění ji
nepřepíše během zastavení relace, přidání zvukového vstupu a nového
spuštění; text proto neurčuje přesné místo čekání. Zamítnutí oprávnění
a nedostupný mikrofon mají jiné výslovné hlášky.

Komentář používá `IOSAudioDriver` se sdílenou `AVAudioSession`, režimem
`playAndRecord` a `allowBluetoothHFP`; přehrávání nastavuje `playback`.
Otevření kamery zastaví přehrávání a deaktivuje zvukovou relaci. To je
kódový kontext pro hypotézu, nikoli reprodukce konkrétního selhání.
Lokální zdroje telefonní aplikace se od včerejšího nasazení Cockpitu
nezměnily a během dnešního auditu nebyly upravené.

Apple rozlišuje odpojení Bluetooth v Ovládacím centru a úplné vypnutí
v Nastavení; po odpojení může dostupnost příslušenství obnovit i restart
či 5:00. Není doložené, kterou variantu Míla použil při dřívějším pokusu.
[Oficiální postup Apple](https://support.apple.com/en-us/102412).

## Další krok

Ukončit a uložit nynější klip a přehrát jej se slyšitelným zvukem.
Při potvrzeném výsledku pokračovat běžným používáním. Pokud se závada
vrátí, zachytit přesnou hlášku, poslední činnost před selháním a stav
připojeného zvuku dříve než provést další změny. Bez těchto důkazů se
nepřipravuje spekulativní oprava ani nová instalace.

Čtení kódu a uživatelské testy jsou důkazem tohoto kroku; nový build,
automatická reprodukce a zařízení dostupné z Macu NEPROVEDENO. Kód původní
aplikace, konfigurace Mac archivu, síť a služby nebyly při diagnostice
měněné. Testy vytvořily zkušební záznamy; žádné mazání ani přepis
původních souborů se neprováděl.
