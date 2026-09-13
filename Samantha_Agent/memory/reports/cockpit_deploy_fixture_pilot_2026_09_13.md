# Cockpit — menší náklady přípravy testů nasazení

Pilot z 13. 9. 2026 navazuje na měření v commitu `0d1b24f1`.
Změna se týká pouze pomocného kódu testů. Produkční Cockpit, synchronizace,
kontroly nasazení, manifest brány a časové limity zůstaly beze změny.

## Zjištění a provedená změna

V prvním měření dva nejpomalejší testy spustily 285 a 274 Git procesů.
Jejich trvání tvořilo přibližně 98 % času; společná příprava prostředí
`prepare_clean_main` zabrala přibližně třetinu celého testu. Zbytek připadal
hlavně na Git dotazy během vlastního scénáře. Nejde tedy jen o pomalý setUp.

Příprava nejprve vytvořila origin a primární kopii, pak přidala testovací
bránu druhým commitem, znovu pushnula do dočasného originu a synchronizovala
primární kopii. Teprve poté vytvořila druhý profil.

Nyní se syntetická brána doplní před prvním push a vytvořením obou kopií.
Pomocná funkce `prepare_with_origin` přijímá volitelnou konfiguraci zdroje;
bez ní zůstává její původní postup. Výchozí stav má nadále dva commity,
stejný obsah, čistý source/origin/oba profily a profily bez remote.
Každé volání vytváří vlastní skutečné repozitáře od nuly, bez sdílené cache.
Změní se historie reflogu a odpadne údaj o nadbytečné úvodní synchronizaci;
žádný scénář na těchto vedlejších údajích nestaví. Vlastní sync/audit/prepare/
verify uvnitř testů zůstávají vykonávané v původním pořadí se stejnými kontrolami.

## Měření před a po

Dva vzorky každé varianty každého původního testu, tedy osm úspěšných běhů.
Tabulka ukazuje rozsah obou vzorků, nikoli garantovaný výkon. Při kontrolním
kole bylo obrácené pořadí variant prvního testu; souběžně neběžela plná sada.

| Scénář | Celý test před / po (s) | Příprava před / po (s) | Git procesy před / po |
| --- | --- | --- | --- |
| Lokální main napřed, rychlé nasazení | 11,39–12,55 / 10,06–10,48 | 3,68–3,90 / 2,30–2,49 | 285 / 251 |
| Čistý profil pozadu, audit a dorovnání | 11,07–13,55 / 9,81–11,02 | 3,67–4,68 / 2,32–2,52 | 274 / 240 |

Samotná společná příprava v každém běhu klesla z **87 na 53 Git procesů**,
tedy o 34 (39 %). Počty příkazů ve vlastních fázích scénářů se nezměnily.
Časová úspora přípravy v těchto vzorcích je přibližně 1,3–2,2 s;
není to slib stejné úspory na každém počítači ani přímé měření celé brány.
Nový regresní test nezávislosti navíc něco stojí, takže se úspory jednotlivých
volání nesmějí prostě násobit a vydávat za celkový výsledek.

## Metodika a hranice

Dočasný měřicí obal spouštěl původní metody přes unittest. `perf_counter`
odděloval `prepare_clean_main`, veřejný audit, přípravu nasazení a ověření;
zbytek zahrnuje vytvoření konkrétní situace, dodatečné status dotazy,
asserty, úklid a režii runneru. Importy do těchto časů nepatří.
Obal nad `subprocess.run` vykonal původní procesy beze změny a sčítal jejich
počet/dobu podle fáze. Časy Git jsou obsažené v časech fází, nesčítají se s nimi.
Baseline při kontrolním kole použil původní tělo `prepare_clean_main` z
`0d1b24f1`; vlastní testové metody i produkční moduly byly stejné.

Sousední JSON obsahuje všech osm měření, statické názvy testů, fáze, počty,
časy a výsledky. Neukládá argumenty, výstupy příkazů, místní cesty ani obsah
souborů. Jednorázový obal není součástí release brány. Časy nelze přímo
porovnávat s dřívějším úplným během na jinak zatíženém Macu.

## Ověření a další postup

- Osm původních pilotních běhů prošlo.
- Nový test ověřil dva nezávislé soubory repozitářů: shodný výchozí head,
  dvoucommitovou historii, bránu v obou profilech, čistotu a chybějící remote.
  Commit v jednom profilu nezměnil source, origin, jeho peer ani druhý soubor
  repozitářů. Cílený běh prošel.
- AST porovnání potvrzuje zachování všech 17 původních metod testů nasazení.
- Plná brána po změně: **1650/1650**, žádné chyby, selhání ani skip; unit
  **455,340 s**, celý testovací podproces 460,0 s. Skupina deploy má nyní
  18 testů za **84,487 s** (dřívější vzorek 17 testů / 97,494 s).
- Celá brána v tomto běhu proti dřívějším 426,384 s nezrychlila. Mimo upravenou
  skupinu se časy také změnily; příčinu tohoto kolísání pilot neurčuje.
  Přímým důkazem změny jsou opakovaná dílčí měření a stabilně nižší počty
  Git procesů, nikoli prostý rozdíl dvou celých běhů.

Tento malý pilot je plnou bránou uzavřený. Další zrychlování produkčních
status/preflight kontrol by vyžadovalo samostatný rozbor časových hranic a
změn stavu; zde se žádné čtení nevynechává. Další strukturální řez volit podle
konkrétní HTTP/doménové vazby v roadmapě. Společný push/nasazení čeká na pokyn.
