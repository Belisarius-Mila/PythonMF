# Camino střižna — první krok UI, 2026-10-25 20:28 CET

## Uživatelský výsledek

- Stavová lišta v záhlaví střižny zůstává při posouvání uvnitř okna dostupná přes sticky header. Rozlišuje Informace / Hotovo / Probíhá / Vyžaduje zásah / Chyba; dynamický text používá textContent a status/alert bez přesunu fokusu.
- Editor, zdrojové přehrávání, komentář, export, katalog i chyby koše předávají odezvu společnému panelu. Kanály oddělují uložení, fotografie, přehrávání, export a překážky zavření. Běžné uložení nepřekryje chybu fotografie; důležité zprávy zůstávají do zavření nebo vyřešení příslušné operace. Aktivní práce se sama neschová.
- Skutečný stav a procenta exportu se zobrazují nahoře, ne pouze v historii dole. Rutinní poll stejného zdroje znovu nepřepíše jeho upozornění. Dokončená operace s hlasem nezůstane označená jako běžící.
- U hlavních tlačítek ukládání/náhled/MP4 je konkrétní vysvětlení nedostupnosti, svázané přes aria-describedby. Zakázaná tlačítka nepředstírají kurzorem čekání; probíhající práce má vlastní aria-busy. Při chybějící původní nahrávce panel vysvětluje možnost čtení/importu.
- Při sestavení seznamu i návratu ze skryté karty se uchová poloha v okně, kotva záběru a otevřený panel fotografie. Ručně zavřený panel se znovu neotevře. Ovládací prvek se při rekonstrukci vrací bez vynuceného posunu; fotografie má vyhrazenou výšku proti pozdějšímu rozskoku při načtení.

## Hranice

Fotografie se v tomto kroku nadále otevírá v nové kartě; vlastní zvětšovací dialog a větší přestavba pracovní plochy patří do dalšího návrhu. Původní skrývání soukromých médií/textu po opuštění karty, ochrany opožděných odpovědí, neměnný zdrojový text, revize, identita požadavků a potvrzení mazání zachované. Backend/perzistence, API payloady, originály ani osobní střihy se tímto krokem nemění. Pouze prezentační stav pozice se drží v paměti karty; nové úložiště nevzniká.

## Ověření

- 102 Python testů PASS: editor 44, foto vrstvy 23, Mac filmy 15, frontend 20 (49,366 s).
- Uvnitř těchto kontraktů běží Node interakce editoru, foto komentářů, knihovny a nový panel odezvy. Ověřeny: simulovaný rozpad layoutu při odstranění skrytého DOM, návrat scrollu/otevřeného i zavřeného panelu, důvody nedostupného exportu, callback chyby uložení a podmínky delšího hlasu, stav exportu, priorita chyb a oddělené potvrzené zotavení, soukromí hlášek, obnova fokusu, staré GET po uložení, opakování stejného save ID, nepřipojení starého hlasu, původní text a mazací ochrany.
- Rychlá kanonická statická brána PASS, včetně složeného JavaScriptu a syntaxe. Očekávaný otisk složeného HTML a seznam modulů upravený pro skutečný nový asset.
- První průběžný test narazil na původní golden HTML a změnu souboru během dlouhého testu. Po stabilizaci kódu a aktualizaci kontraktu je celá výše uvedená sada zelená.
- Skutečný Safari/Chrome/iPhone proklik, překrytí hlášek a jejich viditelnost při scrollování: **NEOVĚŘENO**, prohlížeč nebyl v této relaci připojený. Syntetický DOM se za tuto přejímku nevydává.

## Další přejímka po samostatném p+n

1. Dlouhý seznam: otevřít fotografii uprostřed, vrátit se a zkontrolovat stejný záběr, posunutí a panel; zopakovat s ručně zavřeným panelem.
2. U dolní části seznamu spustit komentář/náhled; horní stav musí být skutečně vidět a nesmí ho překrýt jiný panel. Ověřit běžný Mac i úzkou obrazovku a dlouhý text hlášky.
3. Vyvolat nesplněnou podmínku a ověřit důvod i po automatickém uložení. Při síťové chybě musí zůstat jasný další krok a nesmí vzniknout automatický nový zápis.
4. Po dokončení práce zkontrolovat zmizení dočasné blokace a čitelné potvrzení; během ukládání otestovat dostupnost vysvětlení u náhledu/MP4.

Krok je lokální vývoj s dokumentací a commitem. Push, nasazení, restart služby, produkční export a zásah do iPhonu neproběhly. Předchozí p+n v této konverzaci dokončilo c9c3a5af; nové p+n vyžaduje samostatný pokyn. Další návrh je prostornější pracovní plocha a sjednocení hlavních akcí.


## Publikace — 2026-10-26 09:28 CET

Předchozí odstavec o místním stavu je historický: Míla 26. 10. výslovně zadal
p+n Lunou a UI bc1fe4ad je nyní na GitHubu i nasazené v Cockpitu.
Účtenka 1173a162fd7197d9f5281e76a0f9d400: completed, push/deployment confirmed,
jeden commit, project-camino, cíl Cockpit, gpt-6-luna/high.
Plná brána 2232 PASS / 345,9 s, smoke 5/5, protected_services_unchanged=true.
Adam jednou ověřil GitHub/main 0/0, připravené profily, health a HTTP 200
s přesnou shodou nového HTML; code_stamp 28c8f0a83e59bc1b.
Terminálový caller účtenku převzal; returned_to_adam=false neprokazuje
portálový automatický návrat. Vydání se neopakuje.

Fyzická browserová přejímka výše zůstává NEOVĚŘENO. Po uložení střihu
obnovit Cockpit a prověřit skutečnou viditelnost/překrytí a návrat z fotografie.
Tento výsledkový záznam tvoří následný lokální dokumentační checkpoint.


## Uživatelské přijetí — 2026-10-26 09:59 CET

Míla po vydání odpověděl „Funguje to skvěle!“ a schválil pokračování vývoje.
První UI krok má uživatelské přijetí; přesné zařízení/prohlížeč a úplná matice
šířek nejsou uvedené. Nová pracovní plocha UI 2 má samostatný lokální report
camino_film_workspace_20261026.md a samostatnou přejímku po vydání.
