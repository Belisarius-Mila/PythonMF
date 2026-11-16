# Vocabulary IT — zvukové přechody

2026-11-16 14:10 CET. Proud project-vocabulary-it. Vývoj proti f07dce0a, nové p+n nezadané.

## Nález a změna

Uživatel na produkci popsal nepravidelné/doříznuté čtení velké karty a ticho
po správném napsání. Kód skutečně povoloval Další ihned po správném obrázku,
pokud bylo Psaní vypnuté. Další volalo cancel/stop a mohlo nedočtenou nahrávku
ukončit. Replay šlo znovu spustit během aktuálního poslechu. Ukončení psaní
pouze obnovilo kartu a Další; nové play v této větvi vůbec nebylo.

Tři nové reprodukce na původní verzi selhaly, původních38 testů prošlo.
Třetí reprodukce simuluje přehrávač, jehož návrat currentTime=0 se projeví
až později: starý kód volal play ještě na koncové pozici. To prokazuje mezeru
ve stavovém modelu; nejde o důkaz přesné příčiny každého uživatelova výpadku.

Nově se Další/replay odemknou po skutečném ended a250ms oddechu. Přepínač
psaní audio ani tuto pauzu neobejde. Po600ms zeleného potvrzení textu se
zavře pole, obnoví karta a spustí další italské čtení; až po něm lze dál.
Vypnutí Psaní během potvrzení už závěrečný poslech nezruší. Během rozepsání
zůstává replay možný, draft zachovaný. Odchod vždy zruší zvuk i staré callbacky.

Každý herní poslech používá vlastní čerstvý Audio element, začíná na nule
a nečeká na rewind předchozího skončeného elementu. URL se přednačte už při
přípravě otázky; běžné Učení/Poslech používají původní cache. Čerstvé elementy
se po konci nepřidávají do cache. Jediný společný currentAudio/token zůstává,
žádné překrývání přehrávání. Nahrávky, manifesty, CSV, obrázky ani A–D se nemění.

Při chybě a20s timeoutu je dostupný replay/pokračování, aby člověk nezůstal
uvězněný v dočítání. Nejde o úspěšný poslech. Přímý ruční replay se spouští
bez časové prodlevy; autoplay odmítnutí má viditelnou zprávu.

## Důkazy a omezení

45 JS scénářů PASS: původních38 s novým očekáváním zvukové brány +7 regresí.
Nové reprodukce před opravou38 PASS/3 FAIL, po opravě45 PASS. Zkoušené dlouhé
zvuky/rychlé Next+replay, opožděný rewind a starý ended, přepínače během
pending/trailing/green, nové čtení po správném textu, jeho chyba/timeout/retry,
odchod a pozdní callback. Do skutečného bfcache a profilu se nepřidává stav.

Ve vlastním Safari okně: congratulazione bez Psaní — velká karta s blokovaným
replay a Další, odemknutí po konci; zapnutí psaní na dočtené kartě, draft
congratula, replay bez ztráty textu, dopsání zione, správné potvrzení, karta,
úspěšný konec dalšího audia a fokus Další. Navazující Di niente. se špatným
pak správným obrázkem, psaním a finálním čtením skončilo stejně. Produkční
okno mano17/497 zůstalo zachované. Vlastní okno a HTTP preview server uzavřené.
Tento QA dokládá UI a skutečné browserové media dokončení; nebyl zaznamenaný
akustický výstup a nelze tvrdit přijetí slyšitelného začátku na všech zařízeních.
Telefon/VoiceOver a Mílův skutečný poslech zůstávají přejímkou po vydání.

Finální gate/otisk/checkpoint: private/vocabulary_it_timing_20261116.
Oprava pouze místní; běžící Cockpit ani web se v tomto kroku nemění.

Referenční význam media událostí: [play()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/play)
potvrzuje zahájení; [ended](https://developer.mozilla.org/en-US/docs/Web/API/HTMLMediaElement/ended_event)
se používá pro dokončení. Nezaměňovat start Promise za konec nahrávky.
