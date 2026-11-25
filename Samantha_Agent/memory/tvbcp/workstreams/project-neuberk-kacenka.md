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
- Současný krok zahrnuje pouze sjednocení názvu a dokumentace. Neimplementuje
  backend/UI 2.0, nepřevádí data a nemění runtime ani placené operace.

## Dokumentace a stav

- [Rozcestník](../../projects/interior_architect/README.md) obsahuje mapu
  dokumentů, původ zadání a hranice platnosti.
- [Projektová paměť](../../projects/neuberk_interier_design.md) má aktuální
  souhrn a ponechanou historii verze 1.
- [Handoff](../../handoffs/workstreams/project-neuberk-kacenka.md) určuje
  obnovu práce a další krok.
- [Úvodní audit](../../projects/interior_architect/AUDIT.md) není dokončenou
  technickou etapou 0. [Migrační plán](../../projects/interior_architect/MIGRATION.md)
  zatím neprovedl žádný převod.

## Otevřené otázky a rizika

- Budoucí zobrazovaný název druhé místnosti; současná soukromá evidence se nemění.
- Úplná inventura původových vazeb a baseline technické etapy 0.
- Jednotné schéma, ověřené míry a návrh nového pracovního UI.
- Schopnosti skutečného obrazového adaptéru: kreslené vodítko není maska.
  Pixelová integrita stejného pohledu nezaručuje geometrii generované oblasti.
- Výkon a licence případných nových závislostí nejsou tímto krokem ověřené.

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
