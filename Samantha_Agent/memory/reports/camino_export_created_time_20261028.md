# Camino — datum a čas vytvoření hotového videa

Datum: 2026-10-28 12:42 CET. Proud project-camino. Stav: místní vývoj, bez nového p+n.

Míla potřebuje místo samotného čísla revize vidět čas vytvoření videa. V seznamu hotových MP4 1080p a náhledů 720p je proto před revizí text Vytvořeno s datem a časem včetně sekund. Technická vazba revize zůstává dostupná.

Nový worker zapíše completed_at v UTC do status.json společně s ready až po dokončení a opětovné validaci výstupu. API pro hotové výstupy vrací created_at a created_at_estimated. Nezměněný/idempotentní požadavek ani čtení uložený čas neposouvají; nejde o čas zadání renderu nebo pořízení originálů.

Starší exporty bez tohoto údaje používají mtime status.json pouze ke čtení a UI výslovně uvádí Vytvořeno přibližně. Původní přesný čas z historických metadat nelze vždy prokázat; žádná migrace ani přepis starých souborů se neprovádí. Chybějící či neplatný čas se zobrazí jako Čas vytvoření není k dispozici, bez propisu surové neplatné hodnoty.

Formát cs-CZ, výslovná zóna Europe/Prague, sekundy a korektní zimní/letní posun. Informace je vykreslená jako text, nikoli HTML. Řazení, volba přehrávaného výsledku, identity požadavků, fingerprinty střihu a mazání se nemění. Soukromé skutečné projekty nebyly při vývoji měněné.

Ověření: 69 cílených kontrol PASS / 41,071 s (test_camino_film_editor + test_cockpit_frontend). Nové backendové regrese ověřují přesný čas, opakovaný GET/idempotentní enqueue a historický fallback bez změny bajtů či mtime. Node ověřuje českou zimu/léto, pořadí před revizí, označení přibližného času a neplatný/chybějící údaj. Plná brána 2260 testů PASS (494,814 s unit část, 501,4 s fáze); log logs/camino_export_created_time_gate_20261028.log.

Fyzická Safari přejímka NEOVĚŘENO. Po samostatném p+n ověřit datum u existujícího výstupu a nově dokončeného exportu; po obnovení stránky musí přesný čas zůstat stejný. Nový skutečný export se při tomto vývoji nevytvářel. Nasazený základ f336fd47 přes Terru, aktuální změna zatím není nasazená.
