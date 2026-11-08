# Sjednocený obnovovací návod — 8. listopadu 2026

Míla určil čtenářský formát: změny integrovat do původních tematických kapitol,
jediné datum aktualizace, odstranění historicky zastaralých poznámek o zálohách.
Data podle tohoto směru připravil novou souvislou pracovní verzi bez modelu.

## Dodaný soubor

`OBNOVA_SAMANTHY_NOVY_MAC_AKTUALIZOVANY_08112026.txt` v Downloads a ve vlastní
soukromé pracovní kopii. Obě pracovní kopie mají 75 415 B a SHA-256
`381963c3e2d24f2624caf4af1a79bb130f321fa5bc75d4ffb020f9fda82543c8`.
Záhlaví: **Nejnovější update dokumentu z 08112026**.
Plný text není v Gitu. Předchozí redakční soubor a originály se nepřepisují.
Tyto dvě pracovní kopie nejsou provozní cíle PythonMF + iCloud Dokumenty.

## Změny pro čtenáře

- Jeden text17 kapitol, změny přímo v odpovídajících podkapitolách; žádné
  bloky DOPLNĚNÍ, které opravují předchozí soupeřící instrukci.
- Zastaralé dvojice záloh, jejich počty a velikosti, staré testovací záznamy,
  čísla buildů a prošlé podpisy nejsou předkládané jako současný stav.
- Snapshoty se vybírají podle dokončených manifestů a skutečné vazby projektu
  na doplněk Camina. Zástupnou cestu musí člověk před použitím vyplnit;
  žádný starý konkrétní snapshot není výchozí hodnotou příkazu.
- Volitelný Git bundle je obecný ověřovaný postup, nikoli povinný starý balík.
- Potřebné app/data oblasti, oprávnění Mac/iPhone, role, media, fronty a bezpečné
  chování při nejasném výsledku zůstávají součástí odpovídajících kapitol.
- Pravidlo epochy Camina vychází z implementovaného `identical_recovery_v1`:
  shodný archiv, žádná rotace epochy ani slučování. Odlišný inventář vyžaduje
  zastavení a samostatný skutečně implementovaný recovery postup, nikoli
  ruční aplikaci historické architektonické specifikace.
- Ověřovací Python zálohy má přímo kopírovatelný heredoc. Odsazení prezentace
  nesmí rozbít Python nebo ukončovací shellový delimiter.

Instalační příkaz Codexu přes Homebrew zůstává doložený
[oficiálním Homebrew caskem](https://formulae.brew.sh/cask/codex).
Dvojitý alternativní instalační recept a starý konkrétní CLI pin odstraněné;
pravidla pro skutečnou verzi klienta a serveru zůstávají. Referenční odkazy
nejsou prohlášení, že všechny externí stránky prošly novým úplným auditem.

## Ověření a hranice

- 17 kapitol jednou a ve správném pořadí;47 zdrojových částí má soukromou mapu
  na cílové kapitoly. Hlavní datové/bezpečnostní oblasti zachované.
- V textu nejsou stará konkrétní snapshotID ani vrstvy DOPLNĚNÍ.
- 31 odkazovaných relativních projektových cest existuje v této pracovní kopii.
- Kontrolní Python: AST PASS, logika shodná s podkladem po odebrání
  prezentačního odsazení. Zsh -n heredocu PASS; žádný obnovovací příkaz se nespouštěl.
- Kontrola UTF-8 a úzkých signatur tajemství PASS, kopie v Downloads shodná.
- 24 finančních artefaktů uzavřeného pilotu a předchozí redakční podklad mají
  původní SHA. Žádný nový model, cena ani změna původního přijetí/limitů.
- Kód, role, služby, projektové závislosti ani provozní TXT/iCloud se nemění.
  Původní placený job zůstává attention; tato redakční forma jej neopravuje.
- Starý gate s požadavkem zachování75% historické kapitoly se neměnil a jeho
  úspěšný průchod se pro nový konsolidovaný text netvrdí. Uživatelova nová forma
  vyžaduje příští odpovídající kontrolu témat, kroků, zdrojů a oprávněných změn.

Jde o dokončený sjednocený pracovní text k obsahové přejímce, nikoli o důkaz
instalace na novém Macu nebo fyzické funkčnosti telefonu. Plná sémantická
přejímka a případná publikace zůstávají oddělené. Nový výstup se automaticky
nepřenáší do obou provozních cílů ani neaktivuje plánovač.

## Další aktualizace

Vždy aktualizovat kapitoly v jediném platném čtenářském textu a datum
v záhlaví. Udržovat potřebné kroky, odstraněné neplatné instrukce doložit
mimo dokument; historii, citace a minulé verze ponechat v odděleném auditu.
Datum návodu nikdy nevydávat za stáří nebo úplnost zálohy. Aktivační změny
rendereru, validátoru a publikátoru nejsou součástí tohoto redakčního kroku.

Statická brána a git diff --check OK. Kód se neměnil; plná unit sada se
pro samotnou redakci textu znovu nespouštěla.

Git-safe změněné soubory: tento report a jeho JSON, ACTIVE_PROJECTS.md,
MEMORY_INDEX.md, LESSONS_LEARNED.md, samantha_external_backup.md,
recovery_guide_maintainer.md a kanonický handoff/TVBCP infrastruktury.
Plný soukromý TXT ani generátor pracovního textu nejsou v Gitu.
