# Camino — datum a čas vytvoření hotového videa

Datum: 2026-10-28 12:42 CET. Proud project-camino. Stav: publikované a nasazené do 668321f8 přes Terru 6.1/high; fyzická přejímka čeká.

Míla potřebuje místo samotného čísla revize vidět čas vytvoření videa. V seznamu hotových MP4 1080p a náhledů 720p je proto před revizí text Vytvořeno s datem a časem včetně sekund. Technická vazba revize zůstává dostupná.

Nový worker zapíše completed_at v UTC do status.json společně s ready až po dokončení a opětovné validaci výstupu. API pro hotové výstupy vrací created_at a created_at_estimated. Nezměněný/idempotentní požadavek ani čtení uložený čas neposouvají; nejde o čas zadání renderu nebo pořízení originálů.

Starší exporty bez tohoto údaje používají mtime status.json pouze ke čtení a UI výslovně uvádí Vytvořeno přibližně. Původní přesný čas z historických metadat nelze vždy prokázat; žádná migrace ani přepis starých souborů se neprovádí. Chybějící či neplatný čas se zobrazí jako Čas vytvoření není k dispozici, bez propisu surové neplatné hodnoty.

Formát cs-CZ, výslovná zóna Europe/Prague, sekundy a korektní zimní/letní posun. Informace je vykreslená jako text, nikoli HTML. Řazení, volba přehrávaného výsledku, identity požadavků, fingerprinty střihu a mazání se nemění. Soukromé skutečné projekty nebyly při vývoji měněné.

Ověření: 69 cílených kontrol PASS / 41,071 s (test_camino_film_editor + test_cockpit_frontend). Nové backendové regrese ověřují přesný čas, opakovaný GET/idempotentní enqueue a historický fallback bez změny bajtů či mtime. Node ověřuje českou zimu/léto, pořadí před revizí, označení přibližného času a neplatný/chybějící údaj. Plná brána 2260 testů PASS (494,814 s unit část, 501,4 s fáze); log logs/camino_export_created_time_gate_20261028.log.

Fyzická Safari přejímka NEOVĚŘENO. Po obnovení Cockpitu ověřit datum u existujícího výstupu a nově dokončeného exportu; po obnovení stránky musí přesný čas zůstat stejný. Nový skutečný export se při tomto vývoji nevytvářel. Nasazený základ f336fd47 přes Terru, aktuální změna je nasazená ve 668321f8.


## 2026-10-28 13:03 CET — Výsledek p+n

Registrovaný submit_release(wait=True), přesný head a Terra 6.1/high zmrazené auditem; bez změny modelu, nativního pomocného agenta nebo retry. Účtenka 8e735788255921fdc8bbd83f491714fa completed, push/deployment confirmed, 2 commity do 668321f8446fad749a00d1adefc95e149f1cd867, project-camino → Cockpit. Plná publikační brána 2260 PASS / 439,8 s, smoke 5/5, protected_services_unchanged=true, code stamp b90aa847fa54ce76.

Jedna Adamova kontrola: GitHub main přesně vydaný head; health a stránka HTTP 200, HTML přesně odpovídá místnímu COCKPIT_HTML, SHA-256 e9fdd86775febeaa2c24d4e1d9422af75f09cb4d58bae1664fdf85a4f57c0ee6, exportCreatedLabel/Vytvořeno přítomné. Nativní caller účtenku převzal, returned_to_adam=false je portálový příznak a nevyvolává retry.

Samotné předání: 26514 input, 0 cached, 78 output (z toho 14 reasoning), celkem 26592 tokenů; při již schválených Standard sazbách orientačně 0,6726 kreditu za tento tah. Nejde o fakturu ani cenu Adama/celé práce.

Fyzická Safari přejímka NEOVĚŘENO. Soukromé skutečné projekty, zdrojové texty, média a souhlasy Orusu nebyly během tohoto p+n měněné; žádný nový skutečný render nebyl spouštěný. Závěrečný zápis je místní dokumentační checkpoint pro příští balíček, bez nového p+n.
