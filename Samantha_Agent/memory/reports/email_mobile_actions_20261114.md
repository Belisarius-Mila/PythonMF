# Mobilní tlačítka poštovního agenta

Stav: místně opravené, dosud bez push/nasazení. 2026-11-14 20:48 CET.

Při čtecím browserovém auditu celé e-mailové stránky se šest tlačítek na
390px namačkalo na46px šířky a256px výšky. Text se lámal po písmenech.
Jediné mobilní CSS pravidlo pro přímá tlačítka akčního řádku v#cards
nastavuje flex základ9rem.390px má dva sloupce154px, výška44–58px;
320px jeden sloupec246×44px.1280px zachovává původní rozměry.

Pořadí, názvy, handlery, potvrzení odeslání, dialogy, metadata a služby se
nemění. Editor odpovědi má před/po597px. Celá příprava a browser používají
pouze syntetickou zprávu a odchyt všech síťových požadavků; žádný produkční POST.

Ověření:26 frontendových testů PASS (včetně původních Node průchodů odeslání,
nejasného výsledku, refresh a hlídání). Skutečný browser320/390/1280 PASS,
žádné přetékání ani neodchycená výjimka; screenshot390 vizuálně prohlédnutý.
Finální statická brána před commitem. Důkazy data/private/email_mobile_ui_20261114/,
log email_mobile_actions_targeted_20261114.log. Asset kontrakt upraven jen
pro skutečně změněnou e-mailovou stránku. Nové zrcadlové CSS unit testy nevznikly.

Knihovna64e9897a byla před tímto vývojem vydaná samostatným jobem
3f40788ac09e6a1b24ada757ef6534c1:3918 PASS, push/deploy confirmed,smoke5/5,
živý HTTPS shodný se zdrojem a606 skupin API. Toto potvrzení se nevztahuje
na následnou místní UI úpravu. Širší UI preference Míla zatím neupřesnil;
po UI navazuje A+C. Fyzická iPhone přejímka a nové p+n UI zůstávají samostatné.
UI pokrývá Cockpit handoff/TVBCP; nový e-mailový TVBCP není založený.
