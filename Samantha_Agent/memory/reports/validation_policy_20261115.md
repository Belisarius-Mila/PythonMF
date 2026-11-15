# Zrychlení ověření a vydání — 2026-11-15

Rozsah schválený Mílou: trvale programově vynucovat potřebné kontroly,
neopakovat úspěšné ověření totožného kódu a zachovat plnou ochranu rizikových změn.

Implementace sjednocuje terminál, checkpoint, GitHub batch a nasazení nad
`validation_policy.py`. Pevný seznam známých změn má pevné závislé testy;
ostatní změny mají plnou sadu. Podepsaná účtenka váže obsah, prostředí,
politiku a původní plný základ na nejvýše24 hodin. Kontrola probíhá i po běhu.
Model nemůže klientským přepínačem vypnout testy. Režim `targeted` rozumí
producent, release worker, čtenáři stavu i UI. Historické `quick` záznamy
zůstávají čitelné. Dokumentační zápis checkpointu vyvolá jen vlastní potřebné
testy, pokud je ostatní již ověřený obsah přesně shodný.

Regrese ověřují podvržení, expiraci a neprodlužování plného základu, obsahovou
změnu se stejným mtime/velikostí, změnu prostředí/politiky, starý načtený modul,
změnu během testů, rename i commit otestovaného smazání, souběžné atomické účtenky, nulu/selhání testů,
chybějící modul/základ, celý čekající balíček, starý skip přepínač,
checkpointové dokumenty a přenos cíleného důkazu přes release worker/UI.

Plná brána této rizikové změny je povinným krokem před lokálním commitem.
Její skutečný závěrečný výsledek, počty a měření převzetí budou uloženy pouze
v soukromé `data/private/validation_policy_20261115/completion.json` a podepsané
účtence v Git metadatech. Tento verzovaný popis se po závěrečné bráně nemění,
aby byl commit tvořen právě ověřenými vstupy. Stav PASS nelze odvozovat
z existence tohoto dokumentu; rozhoduje skutečný výsledek brány.

Omezení: běžící Cockpit se tímto místním vývojem neaktualizuje. Není provedený
push, deploy, restart ani živé p+n. Skutečná úspora celého vydání se převezme
při příštím samostatně povoleném p+n. GitHub CI dál používá plnou sadu.
Mediální soubory, Git historie, zálohy a aktivní Data zůstávají mimo zásah.
