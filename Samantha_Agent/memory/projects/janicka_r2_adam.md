# R2-Adam / Janička

Priorita: 2
Stav: samostatný aktivní projekt, návrh před implementací
Založeno: 2026-07-17
Historický pracovní název: R-A2

## Cíl

R2-Adam bude samostatný dlouhodobý Adam v Cockpitu Janička. Má Janě poskytovat
praktickou práci nad existujícími daty Samanthy bez sdílení Mílova Human–Adam
vlákna, vývojového workspace, checkpointů nebo projektového TVBCP.

Má mít vlastní trvalé app-server vlákno a soukromý kompaktní kontext mimo Git,
aby Jana při navazujících rozhovorech nemusela znovu vysvětlovat dříve přijaté
dohody, preference a otevřené kroky.

## Kanonická oprávnění

R2-Adam je read-only vůči zdrojovým uživatelským datům Samanthy:

- nesmí mazat ani měnit dokumenty, články, e-maily, projekty, připomínky,
  rodinná data, Git, TVBCP nebo jiné zdrojové záznamy;
- data čte pouze přes existující registrované schopnosti a jejich bezpečnostní
  hranice, ne libovolným průchodem celého filesystemu;
- výraz `libovolná data Samanthy` znamená uživatelský obsah, ke kterému má Jana
  oprávněný přístup, nikoli tajemství nebo systémovou autentizační vrstvu.

Povolené zápisy jsou úzké výjimky nutné pro jeho funkci:

- vlastní technický stav trvalého vlákna;
- vlastní soukromý kompaktní kontext s kontrolou, opravou a návratem poslední
  verze;
- nový odvozený textový export, e-mailový draft a technická účtenka odeslání.

Tyto zápisy nikdy nesmějí přepsat zdrojová data. Export se vždy vytváří jako
nový soubor a první verze nic automaticky nemaže ani neuklízí.

## Textový export pro Janu

R2-Adam má umět z povolených dat Samanthy sestavit nový UTF-8 textový soubor:

- výstupní formát první verze je pouze `.txt`;
- soubor se ukládá do soukromé složky mimo Git;
- název je bezpečně normalizovaný a existující soubor se nepřepisuje;
- export nese stručný název, datum a přehled použitých typů zdrojů;
- soukromý obsah se nevypisuje do Gitu, memory ani technických logů;
- před e-mailem se ukáže rozsah, velikost a přiměřený náhled výsledku.

## Odeslání e-mailem

Příjemce je pevný soukromý kontakt `Jana`, nikoli libovolně zadaná e-mailová
adresa. Skutečná adresa zůstává mimo Git a načte se lokálně z povoleného
kontaktního úložiště.

Odeslání je dvoukrokové:

1. R2-Adam vytvoří TXT export a lokální e-mailový draft, ale nic neodešle.
2. Jana nebo Míla zkontrolují příjemce, název, zdroje, velikost a náhled a
   samostatně potvrdí odeslání konkrétního draftu.

Po SMTP odeslání se má uložit best-effort kopie do Odeslaných a technická
účtenka bez obsahu: ID exportu/draftu, čas, velikost, stav SMTP a stav kopie v
Odeslaných. Nejistý výsledek se nesmí automaticky opakovat.

Stávající e-mailová vrstva má dvoukrokové potvrzení, SMTP a kopii v Odeslaných,
ale dnes připravuje hlavně přeposlání existujícího e-mailu. Samostatná schopnost
pro nový TXT export je budoucí úzký vývojový krok, nikoli současná funkce.

## Zakázaný obsah

R2-Adam nesmí do exportu, svého kontextu ani e-mailového draftu automaticky
zahrnout:

- `.env`, hesla, tokeny, API klíče a app-specific passwords;
- recovery klíče, SSH klíče a autentizační konfiguraci;
- surové autosave/session logy a interní technické identity;
- celý obsah e-mailové schránky nebo private úložiště bez konkrétního lidského
  zadání a povoleného zdrojového workflow.

Citlivý zdravotní, finanční, právní nebo rodinný obsah se smí použít pouze při
konkrétním zadání, v nezbytném rozsahu a s jasným náhledem před odesláním.

## Architektura

- Samostatné app-server vlákno a runtime profil.
- Žádné sdílení Human–Adam vlákna ani izolovaného vývojového workspace.
- Znovupoužití ověřeného Session Hub kontraktu: jeden tah, reconnect,
  idempotence, `delivery_unknown`, časomíra a případný zvuk.
- Soukromý kompaktní kontext mimo Git; není kopií chatu ani projektovým TVBCP.
- Registrované read-only zdroje a jediná úzká exportní/outbound schopnost.

## Otevřené kroky před implementací

1. Sepsat přesnou matici povolených zdrojů a citlivých kategorií.
2. Zvolit private umístění, schéma a verzování Janiččina kontextu.
3. Navrhnout append-only TXT export store, limity velikosti a názvosloví.
4. Navrhnout pevný kontakt `Jana`, preview a dvoukrokový draft/send kontrakt.
5. Rozhodnout UI pro kontrolu a vrácení poslední změny soukromého kontextu.
6. Připravit testy oddělení vláken, zákazu změn zdrojů, nepřepsání exportu,
   blokace tajemství, potvrzení odeslání, sent-copy a nejistého doručení.
7. Teprve potom implementovat nejmenší vertikální řez nad jedním bezpečným
   read-only zdrojem a jedním TXT exportem.

## Bezpečnost

- Do Gitového projektu nepatří skutečná adresa Jany ani obsah exportů a draftů.
- R2-Adam nesmí dostat obecný zapisovací nebo mazací tool jen kvůli pohodlí.
- Automatické mazání exportů se v první verzi nepovoluje; případný úklid bude
  samostatný potvrzovaný servisní workflow.
- Odeslání je externí akce a vždy zůstává za samostatným potvrzením.
