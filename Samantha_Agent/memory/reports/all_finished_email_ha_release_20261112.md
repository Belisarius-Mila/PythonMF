# Společné vydání dokončené práce — 2026-11-12

Míla po dokončení vývoje výslovně zadal p+n všech nalezených dokončených
commitů včetně Datových a úklid repa. Projekt project-email-cases používá
společný runtime Cockpitu; jde o stejné nasazení pro e-mailové UI i Human–Adam.

## Integrovaný rozsah

- E-mailová etapa3:10555d48, přesné vazby, zdrojový důkaz a termíny.
- E-mailová etapa4:7b3ddbf3, citované návrhy, lidské převzetí/odmítnutí,
  rozhodnutí o vazbě, rezervovaný jediný pokus a obnova bez opakování modelu.
- Datův HA-05:b9ed2ad61b664e625578cdb981e6e964ee738121, živá karta,
  veřejný plán/commentary a čtecí obnova původní práce bez druhého odeslání.
- Úklid:e44a1b5a,28 místních a11 vzdálených plně integrovaných větví.
  Přesné tipy, záloha a postup v git_branch_archive.md a privátních účtenkách.

Při auditu Data současně pracuje na HA-06 ve vlastním worktree ebbd.
HA-06 není součástí nalezeného commitu b9ed2ad6; jeho nezapsané soubory
nejsou převzaté ani změněné. Aktivní Datova větev zůstává zachovaná.
Dva staré čisté pomocné worktrees jsou odpojené od dokončených větví,
všechny soubory včetně ignorovaných privátních podkladů zůstávají.

## Důkazy před vydáním

Finální e-mailový zdroj:587 cílených PASS /34,988s, statická brána PASS,
plná brána3709 testů /538,314s,31 SKIP. Kontrolované headless mobilní/desktop
UI, skutečné HTTP/Node a crash/obnova bez modelového retry. Žádný placený pilot.
Datův HA-05 má vlastní417 cílených a140 browser kontrol, plnou3648 /534,548s,
5 SKIP. Integrační kontrola společného kódu192 PASS /12,639s. Konflikt LL
vyřešen zachováním obou záznamů; společný quality gate obsahuje obě nové sady.
Plná publikační brána nad přesným konečným main je povinnou součástí p+n.

## Jediné předání a hranice

Request `email-ha-all-finished-20261112-v1`, očekávaný job `b794e9f91e021059c97a7851827e6160`.
Původní přesný approved_head a výsledek budou v
`data/private/all_finished_email_ha_release_20261112/release_plan.json`,
`release_receipt.json` a `verification.json`. Tento zápis před vydáním není
dokladem push/deploy. Při nejistotě ověřit stejnou účtenku, neopakovat submission.
Registrovaný submit_release(wait=True) s centrální rolí vybírá skutečný model;
žádné ruční přepínání rolí, nový vývojový agent ani modelový polling.

Hodinová kopie7f47a41f a výchozí vypnutý followup monitor zůstávají zachované.
P+n společného runtime nenahrazuje registrovaný upgrade této kopie, vědomé
zapnutí doplňku nebo skutečný modelový pilot s rozpočtem. Mac/iPhone a skutečný
modelový průchod zůstávají otevřené. Samostatný e-mailový TVBCP není dohodnutý;
Cockpit handoff/TVBCP kryjí UI/workflow, HA handoff/TVBCP vlastní komunikační proud.

Další krok: jediné schválené p+n a kontrola přesné účtenky/živého runtime.
Potom samostatná řízená přejímka a rozhodnutí o servisním upgradu/aktivaci.
