# TVBCP: Rodinný kalendář

Pracovni proud: `project-family-calendar`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-07-22 08:48 CEST – Čistý builder náhledu D-2/D-1 a cílené testy jsou hotové

Pracovní proud: `project-family-calendar`.

Milník: Čistý builder náhledu D-2/D-1 a cílené testy jsou hotové

Důkaz: plná Cockpit brána: 980 testů, 208.3 s, výsledek OK. Checkpoint backend připravuje jeden commit na lokální
profilové `main`; zdrojový `main` přebírá tentýž objekt pouze fast-forwardem.

Další krok: Potvrdit checkpoint tohoto kroku v Cockpitu

### 2026-07-22 11:03 CEST – Dokumentační uzavření builderu a doplnění CI triggeru

Implementační checkpoint je dokončen: commit `531ed75` je na `main` a
`origin/main`. Dřívější další krok „Potvrdit checkpoint“ tímto novějším
záznamem pozbývá platnosti.

Kanonická projektová paměť, aktivní registr a handoff nyní popisují hotový
čistý builder. GitHub Cockpit Quality Gate nově sleduje
`app/family_calendar.py` a `tests/test_family_calendar*.py` při pull requestu
i pushi. Změna nezasahuje aplikaci, soukromá data, odesílání ani persistence
doručení.

Ověření: 28 cílených testů prošlo. Plná lokální Cockpit Quality Gate prošla
s 980 testy za 208.0 s a zahrnula čistý `git diff --check`.

Další krok: navrhnout samostatné read-only zobrazení náhledu v Cockpitu,
stále bez odesílání a bez persistence doručení.
