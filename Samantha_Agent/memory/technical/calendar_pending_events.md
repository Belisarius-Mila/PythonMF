# Nevyřízené události po termínu

Aktualizováno 27. 11. 2026. Proud project-cockpit.
Nasazeno v dca28fe8, push a deployment potvrzené 27.11. Provozní kontrola 5/5
a živé API prošly. Následuje uživatelská přejímka.

Úvodní agenda zobrazuje nadcházejících 30 dní a dříve načtené nevyřízené
události. Po termínu jsou označené „Po termínu · čeká na potvrzení Splněno“.
Zůstanou přes obnovení a restart až do vyřízení konkrétního výskytu.

## Uložení a hranice

CalendarOverview při zápisových operacích ukládá prošlé načtené záznamy do
retained_events v soukromém overview.json pod stejným zámkem a atomickým
writerem jako běžnou cache. Čtení snapshotu úložiště nezapisuje ani nevolá
nativní kalendář. Záznamy zachovají duplicitní skupiny, výběr kalendářů a
původní časy. Celodenní hranice používá již existující kanonickou půlnoc.

Agenda spojuje aktuální řádky se zachovanými podle stejného obsahového klíče.
Typ a Splněno zůstávají v revizovaném agenda_types.json. Jednoznačný prošlý
záznam lze místně vyřídit i při neaktuálním čtení, s kontrolou obou revizí.
Práce s nativním kalendářem dál vyžaduje aktuální zdroj a ověřenou identitu.
Ověřená editace přenese zachovanou položku na nový obsah. Ověřené výslovné
smazání vyřídí i odpovídající místní připomínku.

Kolizní kontroly dál používají původní events a své živé čtecí intervaly.
Zachovaná historie se do množiny kolizí nepřimíchává. Každý opakovaný výskyt
má vlastní obsahový klíč. Duplicity stejného obsahu zůstávají nejednoznačné.
Zpětné uchování vychází z dosud dostupné cache. Již přepsané starší přehledy
se automaticky nerekonstruují.

## Ověření

Regrese tests.test_calendar_agenda, tests.test_calendar_overview,
tests.test_cockpit_calendar_agenda a kalendářové edit/delete sady včetně
jejich skutečných HTTP a Node scénářů. Testy používají syntetické události
a ověřují přesné počty nativních volání. Důkazy jsou v soukromé složce
data/private/calendar_retained_20261127/.

## Další krok

Uživatelská přejímka prošlé položky v hlavním Cockpitu po obnovení stránky.
Účtenka vydání a živé ověření jsou v data/private/calendar_retained_20261127/release/.
