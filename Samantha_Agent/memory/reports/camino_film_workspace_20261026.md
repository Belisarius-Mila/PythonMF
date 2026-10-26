# Camino — pracovní plocha střižny, 2026-10-26 09:59 CET

## Přijetí předchozího kroku

Míla po nasazení bc1fe4ad uvedl „Funguje to skvěle!“ a požádal o pokračování.
To je uživatelské přijetí prvního UI kroku (hlášky, důvody blokací a návrat od
fotografie). Konkrétní zařízení/prohlížeč tím není určený; nelze z toho vyvodit
samostatné přijetí ostatních funkcí Camina nebo úplné matice šířek.

## Nové ovládání

- Okno využívá větší část obrazovky. Na širokém displeji má seznam záběrů vlevo, zdrojový náhled uprostřed a nastavení vybraného záběru vpravo. Střední a úzké šířky mají postupné skládání panelů; min-width/min-height a box-sizing brání přetékání gridu/okna.
- Záběr v seznamu má číslo, typ, popisek, délku, stav zařazení a u fotografie soukromou miniaturu. Viditelné je nastavení jediného záběru; výběr je označený i přes aria-current. Vedle zůstává počet zařazených záběrů a délka filmu včetně karet.
- Výběr je čistě pohled: nevytváří revizi, nespustí render ani přípravu videa, nevyřazuje záběry. Vyřazený záběr lze stále vybrat a upravit. Video se začne připravovat až po jeho ručním otevření. Zdrojová fotografie je označená jako zdroj; text/zvuk se posuzují ve skutečném náhledu filmu.
- Sticky záhlaví obsahuje uložení, přehrání hotového výsledku, vytvoření náhledu a export MP4. Dosavadní hlášky a důvody nedostupnosti zůstávají součástí záhlaví i na úzkém displeji.
- Přehrát výsledek používá jen bezpečný výstup aktuální uložené revize, celé délky a stavu ready. Starší revize, částečné náhledy a source proxy tento ovladač nezpřístupní. Dřívější výsledky jsou dál dostupné v označené historii. Přehrání nezadává nový export; výsledek otevře v přehrávači.
- Projekty/zdroje, textové nástroje, náhledy/hotové filmy a vědomé obnovení střihu mají vlastní sbalitelné sekce. Při chybějícím filmu nebo chybě se výběr projektů otevře, aby zůstal dostupný další krok.

## Zachované hranice

Backend, API payloady, originály, uložené revize a mazací potvrzení se nemění.
Neexistuje nové trvalé UI úložiště. Výběr/posunutí žijí v paměti karty a jsou
vázané na projekt a stabilní Asset ID. Změny rozepsané u jiného záběru zůstávají
v pracovním draftu; automatické ukládání a ochrany opožděných GET zůstávají.
Po skrytí se odstraní i nové miniatury a centrální foto URL. Nové asynchronní
přehrání používá epochu/generaci; pozdní odmítnutí se nezobrazí v jiném filmu.
Při běžném psaní se přepisují pouze popisky, nikoli celé miniatury.

## Ověření

- 103 cílených Python testů PASS / 47,818 s: editor 44, foto vrstvy 23, Mac filmy 15 a frontend 21. Poté závěrečné Node interakce a 21 frontendových kontraktů znovu PASS / 2,216 s po poslední úpravě stylů/ochrany přehrávání. Nejde o 124 různých testů.
- Node regrese: toolbar mimo kořen editoru, výběr záběru bez zápisu/renderu/proxy, rozepsaný text, identita po přesunu, obnova vybraného videa ze skryté karty, odstranění nových soukromých URL, přehrání bez nové úlohy, vyloučení částečného/staršího výsledku, stale play rejection a zachování miniatur při psaní. Původní kontrakty foto textu/hlasů/koše a opožděných odpovědí prošly.
- HTML má vyvážené značky a jedinečná ID/data-film ovladače. Golden kontrakt aktualizovaný po zkontrolované změně HTML/CSS/JS. Rychlá kanonická statická brána PASS.
- Skutečné rozložení, klikání a viditelnost při scrollu na Macu a iPhonu: **NEOVĚŘENO**. CUA inventory nemá prohlížeč ani aplikaci. Syntetický DOM a CSS kontrakt nejsou fyzickou přejímkou.

## Přejímka po samostatném vydání

1. Dlouhý film otevřít na širokém Macu a úzkém displeji. Ověřit čitelnost seznamu/náhledu/nastavení, žádné vodorovné přetékání, dostupné hlášky a hlavní akce.
2. Rozepsat text u fotografie, přepnout na jiný záběr a zpět; text se musí zachovat. Přesunout záběr a ověřit, že výběr zůstane na stejném obsahu, ne na původním pořadovém čísle.
3. Procházet videa bez otevření: nesmí vzniknout nové source/render úlohy. Teprve ručně otevřít video a zkontrolovat střih celé původní délky.
4. Přehrát uložený výsledek: nesmí vzniknout nový export. Po změně revize nebo jen s částečným/starším výsledkem má ovladač vysvětlit nedostupnost.
5. Otevřít a sbalit projekty/nástroje/historii; přepnout kartu a vrátit se. Kontrolovat stejný výběr, hlášky a návrat od fotografie podle přijatého prvního kroku.

Jen místní vývoj, bez push, nasazení nebo produkčního renderu. Na poslední
vydané UI bc1fe4ad nový krok nemá vliv do samostatného p+n. Příjemnější český
hlas a další praktická přejímka nahrávek/importu zůstávají samostatné.


## Publikace — 2026-10-26 10:28 CET

Předchozí místní stav je historie: po výslovném p+n Lunou je UI 2 v 41ac2e1d
na GitHubu i nasazené v Cockpitu. Účtenka aedb878e354d3771056c54fa12acc909:
completed, push/deployment confirmed, dva commity, project-camino, Cockpit,
release_executor gpt-6-luna/high. Plná brána 2233 PASS / 350,9 s, smoke 5/5,
protected_services_unchanged=true.

Adam jednou převzal účtenku a ověřil GitHub/main 0/0, profily ready, health OK
a HTTP 200 s přesnou shodou nového frontendového HTML včetně pracovní plochy
a toolbaru. Code stamp 28c8f0a83e59bc1b; skutečné nové UI ověřuje shoda HTML.
Return caller účtenku obdržel; returned_to_adam=false neprokazuje portálový
návrat a není důvodem opakovat úspěšné vydání.

Vizuální browserová přejímka UI 2 výše zůstává NEOVĚŘENO. První UI krok má
Mílovo uživatelské přijetí, které se automaticky nepřenáší na nové rozložení.
Tento výsledkový zápis je následný lokální dokumentační checkpoint.
