# Ateliér — společný půdorys a míry

Stav: místní vývoj, 2026-11-10 21:29 CET; bez p+n. Proud project-neuberk-kacenka, vlastní větev adam/interior-room-plan-20261110 z19703fdb. Na main souběžně probíhala cizí práce MMTX; její soubory a Data worktree se neměnily.

## Výsledek a hranice

Jeden základ pro každou místnost projektu: vybraný podklad typu plan, volitelný text skutečných měr a pevných bodů, vlastní revision. Základ se ukládá v Podkladech a přidává k automatickému výběru AI před variantovými referencemi. Duplicity se nepředávají dvakrát. Společný půdorys se už nevybírá zaškrtávátkem u každého návrhu. Souhrn před potvrzením ukazuje půdorys, jeho náhled a míry. Model je nesmí měnit; fotografie určuje pohled/vzhled a společný základ rozměrové podmínky. Nejde o přesný CAD/3D model a nebyla prokázána geometrická přesnost generování.

Staré místnosti mají čtecí prázdný základ, bez migrace či automatického zápisu. Nebyl vybrán žádný skutečný soukromý půdorys a nevymýšlely se skutečné míry. Výměna nebo odebrání vazby zachová soubory i uložené varianty. Trvalé smazání zůstává samostatně potvrzovaná operace.

## Kontrakt

- save_room_basis používá stávající registrovanou action trasu, media lock a repository transakci. expected_basis_revision chrání souběh, stabilní request_id přesný replay. Cizí místnost, fotografii místo plan a vadné hodnoty odmítá. Identický save nemění revizi.
- Neuložený základ je v browserové cache podle projektu/místnosti; platí napříč variantami. Nesplývá s otázkami a drafty jednotlivých variant. Novější serverové hodnoty lokální rozpracování nepřepíší; jsou vidět pro porovnání.
- Při neukončené AI úloze v místnosti se změna základu odmítne. Změna základu váže nový brief_basis/token a zneplatní předchozí souhrn. Starší potvrzení neodešle placený tah.
- context.room_basis nese zmrazené míry, revizi a číslo přiloženého půdorysu. Obě AI akce používají stejný effective_sources. Limit šesti obrázků zahrnuje půdorys; nic se tajně nezahazuje. Obrazový kontext dál neobsahuje historii ani volné poznámky.
- Mazací náhled označí room_plan. Po výslovném potvrzení se vazba odpojí, revize zvýší, míry zůstanou. Cleanup dohledá i joby, kde půdorys nebyl v draft.source_ids, a odstraní jejich obrazové pracovní kopie. Nejisté aktivní joby smazání blokují a recover již smazané obrázky nevrátí.
- Změněný zdroj/instrukce patří do otisků případného budoucího pilotu. Modelové role, architektura App Serveru a aktivační politika zůstávají stejné; žádný nový placený pilot neběžel.

## Ověření

130 cílených Python/HTTP/frontend kontrol PASS včetně 28 Node scénářů. Nově 11 serverových kontraktů + 1 HTTP regrese a 4 Node scénáře: čtecí kompatibilita, sdílení/restart, replay, konflikt revizí, cizí místnost, výměna bez smazání, automatický chat/image snapshot, deduplikace, starý token, aktivní job, maximum obrázků, smazání automatických snapshotů, zachování měr a cache napříč variantami.

Nativní Safari/CUA na vlastní syntetické místnosti: výběr jediného půdorysu, uložení skutečných testovacích měr, indikace automatického přikládání bez checkboxu, kontrolní náhled, chat a potvrzený obraz se stejnou revizí/základem, automatický základ i v nové variantě. Fake chat1/image1/paid0; snapshoty skutečně obsahují shodný room_basis a plan_image_number=2, obrazový kontext má prázdnou historii/poznámky. Testovací panel zavřený, vlastní server ukončený. Nejde o skutečné nasazení ani fyzickou přejímku nové funkce na privátní místnosti/iPhonu.

Plná brána PASS: 3469 testů, 0 chyb, 31 SKIP, 531,0 s.

Důkazy: data/private/interior_room_basis_20261110/ (qa.json, full_gate.log, chat_snapshot.json, approved_snapshot.json, browser_counts.json, preservation_before.json a následná kontrola). Projektový handoff, paměť a primární katalogový řádek aktualizované. Nový TVBCP nebyl výslovně dohodnutý; pro budoucí Human–Adam zůstává vazba otevřená.

## Další krok

Samostatně autorizované p+n a následně výběr vlastního půdorysu a zadání ověřených měr v Podkladech. Žádná skutečná data se tímto vývojem neměnila.
