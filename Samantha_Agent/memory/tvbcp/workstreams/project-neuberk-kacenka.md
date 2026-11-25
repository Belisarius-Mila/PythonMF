# TVBCP: Interiérový architekt

Pracovní proud: `project-neuberk-kacenka`
Typ: `Project`
Režim: `active`
Priorita: 2
Založeno: 2026-11-25, výslovným souhlasem Míly s návrhem nového vymezení
a následným pokynem nejprve narovnat název a dokumentaci.

## Cíl a kanonická rozhodnutí

- Jeden projekt Interiérový architekt, vývojový směr Interior Architect 2.0.
  Kačenka a místnost z dnešního Ateliéru jsou jeho dvě rozpracované místnosti.
- Zachovat návrhy a ostatní dostupná data obou místností. Současný backend
  aplikace a UI se navrhnou znovu uvnitř existující Samanthy/Cockpitu.
- Stabilní ID proudu i kanonické cesty zůstávají, staré názvy jsou aliasy.
- Výchozím zadáním je sedmisouborový balíček v
  [reference/](../../projects/interior_architect/reference/). Jeho schéma
  místnosti je pouze příklad. Nejnovější rozhodnutí drží tento TVBCP.
- Po sjednocení názvu Míla zadal technický audit a návrh backendu, UI a převodu.
  Návrh je připraven k rozhodnutí o prvním implementačním milníku.

## Dokumentace a stav

- [Rozcestník](../../projects/interior_architect/README.md) obsahuje mapu
  dokumentů, původ zadání a hranice platnosti.
- [Projektová paměť](../../projects/neuberk_interier_design.md) má aktuální
  souhrn a ponechanou historii verze 1.
- [Handoff](../../handoffs/workstreams/project-neuberk-kacenka.md) určuje
  obnovu práce a další krok.
- [Audit](../../projects/interior_architect/AUDIT.md), [backend](../../projects/interior_architect/BACKEND.md),
  [UI](../../projects/interior_architect/UI.md) a [převod](../../projects/interior_architect/MIGRATION.md)
  společně tvoří návrh verze 2.0.

## Otevřené otázky a rizika

- K přijetí zbývá návrh prvního pracovního řezu. Druhá místnost může zatím používat současné jméno Koupelna dolní.
- Vyzkoušet skutečný import, kolize revizí, chybějící média a návrat po zápisu do v2 na oddělené kopii.
- Oba klienty ručně převzít na zařízení včetně lokálních draftů a výkonu editoru. Perspektiva bez ověřitelného podkladu zůstává neověřená.
- Případná pozdější volba 3D nebo placeného adaptéru vyžaduje doložení jeho konkrétních schopností.

## Chronologické záznamy

### 2026-11-25 20:51 CET — Jednotný název a nové vymezení projektu

Hotovo: Interiérový architekt má sjednocenou identitu, aktuální rozcestník,
kanonický handoff a nově dohodnutý TVBCP. Původní technické zadání je zachované
v sedmi beze změny převzatých dokumentech. Historie Kačenky i aplikace Ateliér
zůstává dostupná a nově je oddělená od cílové verze 2.0.

Rozhodnutí: Míla schválil návrh sjednocení a výslovně zadal nejdřív název
a dokumentaci. Jeden projekt zahrnuje dvě místnosti; ID ani soukromé úložiště
se nepřejmenovávají. Schválení zahrnuje založení tohoto TVBCP.

Další krok: Dokončit technický audit a návrh převodu obou místností spolu
s návrhem nového UI, zatím bez převodu skutečných dat.

Navrhované další kroky: Po auditu ověřit převod na kopii, potom postupovat
po funkčních milnících masek/kompozice, scene modelu/2D a následně 3D/adaptéru.

Technický důkaz: 43 existujících katalogových, vazebních, paměťových a výběrových
testů PASS. Registrovaná programová brána a konečné porovnání soukromých dat
jsou evidované v místní účtence a
`data/private/interior_project_reset_20261125/completion.json`. Backend/UI,
živé služby a modelové role se nemění; bez push/nasazení a placeného tahu.

### 2026-11-25 21:07 CET — Audit a návrh pracovního postupu pro obě místnosti

**Hotovo.** Míla může posoudit návrh výběru místností, úpravy fotografie, historie a převodu. Audit rozlišil 26 indexovaných výstupů Kačenky a 27 variant Koupelny dolní, z nichž 4 mají připojený obrázek.

**Rozhodnutí.** Pokyn zahrnoval audit a návrh. Volba úložiště a pořadí implementace jsou Adamovy návrhy k rozhodnutí.

**Další krok.** Převzít návrh prvního místního řezu nad syntetickou fotografií.

**Navrhované další kroky.** Po přijetí vyzkoušet editor masky a bezeztrátovou kompozici. Na funkčním jádře ověřit převod na kopii. Poté doplnit scénu, půdorys a sdílené 3D pohledy.

**Technický důkaz.** 146 regresních testů v1 prošlo. Stávající příjem přijal i jiný poměr stran. Lokální syntetická kompozice měla 0 změn chráněných pixelů po načtení PNG. Dva průchody inventurou měly shodnou mapu 180 klíčů. Rizikem zůstávají neověřená geometrie fotografie a drafty konkrétního prohlížeče.
