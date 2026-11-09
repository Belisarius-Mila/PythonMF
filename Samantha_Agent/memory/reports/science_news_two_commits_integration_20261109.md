# Převzetí dvou Datových ScienceNews commitů

Stav: 2026-11-09 23:38 CET. Míla výslovně schválil převzetí obou nových commitů a následné p+n.

## Rozsah a předchozí vydání

- Převzaty přesně `9abeb7970d4a266f819bcc7c23c1ade6cd84f9b0` a `3ba4d06312ee362853e54090a01d3a7cd56e89e8` nad již vydaným `32c4ed20`.
- Předchozí vydání `32c4ed20` je potvrzené účtenkou `243f9c9c6ccb7086cdf28acca2f13117`: 3 commity pushed/deployed, plná brána 3370, smoke 5/5, chráněné služby beze změny; GitHub CI 42705522900 success. Starší attention bd828212 je historické přerušení, ne aktuální stav vydání.
- UI nově vysvětluje nedostupný překlad a vypne tlačítko při neaktivní službě. Hotový uložený překlad lze otevřít dál bez nového modelového tahu; tři rozhodovací volby jsou zachované.
- Součástí jsou zmrazené podklady jednorázového pilotu a redigovaný report jeho provedení Datou. Vývojový pilot již proběhl: tento integrační krok ho neopakuje a nemění žádnou jeho účtenku.

## Integrace a ověření

- Pět konfliktů vyřešeno: aktuální stav používá novější Datův report, obě chronologické historie se zachovaly, kontrolní otisk odpovídá současnému Cockpitu včetně kalendáře/Archivu. Nová lekce přejmenována z kolidujícího LL-114 na LL-121; původní main LL-114 zůstává.
- 116 cílených Python testů PASS, včetně Node scénářů skutečného ScienceNews modulu: neaktivní tlačítko neotevře okno ani neodešle překlad, uložený překlad je dostupný a zpráva zůstává nevyřízená. Log `logs/science_news_two_commits_targeted_20261109.log`.
- Plná integrační brána PASS: 3381 testů / 31 SKIP (492,622 s); log: `logs/science_news_two_commits_full_gate_20261109.log`.
- Role JSON, parser a registrované p+n, ochrana automatického restartu i kalendářový/archivní kód zůstávají přesně ze současného main. Datův worktree se nemění.

## Hranice a další krok

Žádný další modelový překlad, přenos hotového překladu do živé karty, import dat, aktivace role nebo plánovače. Soukromé zdroje/paket/překlad/účtenky zůstávají v Datově private worktree, jejich text nebyl kvůli převzetí čten ani kopírován. Zmrazený přípravný JSON se nemění; jeho historický stav prepared/0 paid je překryt výsledkovým reportem, nikoli upraven. Pilot je svázaný i s původními závislostmi; integrace jeho historické otisky nepřepočítává a nedává oprávnění zkoušku spouštět z nového main.

Po bráně dokončit jeden merge checkpoint, zarovnat pouze čisté profily a provést již schválené Terra p+n pro `project-knowledge-library` přes `submit_release(wait=True)`. Účtenka nového vydání bude v `logs/science_news_two_commits_release_20261109.log`; tento předpublikační zápis výsledek nepředjímá. Mílova čtenářská přejímka překladu, fyzická UI přejímka, připojení hotového textu a případná automatika jsou další samostatné kroky.
