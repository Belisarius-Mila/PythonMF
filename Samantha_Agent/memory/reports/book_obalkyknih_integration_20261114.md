# Napojení online obálek Obálkyknih.cz — 14.11.2026

Nová místní verze zobrazuje online obálku v rychlém ISBN formuláři i u knihy
v seznamu, pokud nemá vlastní fotografii nebo uloženou miniaturu. Po uložení
knihy bez místní miniatury náhled zůstane dostupný. Obrázek otevírá detail
zdroje; samostatný název knihy otevírá naši kartu.

Prohlížeč přímo načítá cache3.obalkyknih.cz s povinným keywords=ISBN
a Referrer-Policy origin jen na tomto img. Globální zásada ostatních
požadavků zůstává zachovaná, CSP se rozšiřuje jen o tento host a jen pro
obrázky hlavního dokumentu. Ostatní dva frontend servery se nepoužívají,
protože jejich oprávnění při předchozí kontrole nebyla potvrzená.

Žádná nová backendová síťová operace, nové přihlašovací údaje ani úprava
živých knih. Stávající book_cover_url zůstává pevnou Open Library ISBN
identitou a náhradním zdrojem. Backendový downloader Open Library, jeho
validace, rezervace, transakce a replay se neměnily. Trvalé ukládání obsahu
Obálkyknih není součástí této změny. Obálka je odvozený online náhled.

Při chybě, prázdném obrázku nebo po5s v rychlém náhledu následuje Open Library.
Selhání obou zdrojů neblokuje Uložit. Stará načtení a časovače po změně ISBN
nepřepíšou novou knihu či místní přílohu. Lazy řádky mají viditelný box,
časový limit nepoužívají před načtením mimo viewport.

Ověření:49 inventura/miniatury/HTTP bezpečnost +39 frontend/ISBN testů PASS;
po závěrečné úpravě nápovědy znovu23 frontend PASS. Skutečný prohlížeč
z registrovaného HTTPS originu načetl reálnou obálku170×240, správný odkaz
a minimální Referer. Izolovaný archiv:2 testovací knihy,0 produkčních POST.
Chyba/1×1/timeout/oba zdroje nedostupné, místní priorita, změna knihy a lazy
scroll ověřené;390/1280 bez přetékání,0 neodchycených výjimek.
Finální statická brána v logs/obalkyknih_static_gate_20261114.log.

Stav: lokální vývoj a ověření; bez push, nasazení a fyzické iPhone přejímky.
Další krok: samostatně potvrzené p+n project-knowledge-library / Cockpit.
Dohodnuté obory, žánry a dynamické filtry zůstávají navazujícím krokem.

Zdroje:
- https://docs.google.com/document/d/1b2iw31p5Izs0cHyDmErETQSp4KppBVm05BBCkiw67kI/edit
- https://www.obalkyknih.cz/about
- https://github.com/cbvk/obalkyknih/wiki/Dokumentace-procesu-rizeni-prav-pristupu
