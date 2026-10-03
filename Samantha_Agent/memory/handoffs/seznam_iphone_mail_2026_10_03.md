# Seznam v Apple Mailu na iPhonu — pokračovat zítra

Stav: rozpracovane, na zadost Mily preruseno do zitra
Pripomenout pri startu: ano
Datum: 2026-10-03 21:48 WEST
Priorita nebyla uzivatelem urcena; nevznika novy projekt ani TVBCP.

## Co se resilo

Apple Mail hlasi nespravne heslo k IMAP uctu Seznam. Bez cteni obsahu
zprav, bez zkouseni hesel agentem a bez zasahu do nastaveni uctu.

## Co je hotove

- Snimek chyby overen v Downloads; soukromy obsah z pozadi neprepisovat.
- Mila uvadi, ze pristup do stejne schranky na webu funguje.
- Dvoufazove overeni podle Mily neni nastavene; hypoteza nutneho hesla
  pro aplikace se nepotvrdila.
- Mila potvrdil imap.seznam.cz a odpovidajici uzivatelskou adresu.
- Na dotaz na SSL zapnuto / port 993 odpovedel, ze ma takove hodnoty;
  novy snimek nastaveni nebyl v Downloads, jde o uzivatelske potvrzeni.
- Mobilni data misto Wi-Fi pri zapnutem Tailscale: Mail stale chce heslo.
- Agent nemenil heslo, ucet, sit ani telefon a nic neodesilal.

## Co neni hotove

Pricina neni urcena. Test s vypnutym Tailscale nebyl uzivatelem potvrzen.
Neni rozliseno, zda webove prihlaseni probehlo rucnim zadanim hesla,
pres automaticke vyplneni nebo existujici relaci. Neprohlasovat VPN,
slabe zabezpeceni Wi-Fi ani heslo za prokazanou pricinu.

## Dalsi krok

Navazat poslednim navrzenym kratkym testem: na mobilnich datech docasne
vypnout Tailscale, v Mailu overit zname webove heslo, potom Tailscale zase
zapnout. Po dobu vypnuti nebude dostupny soukromy Cockpit/Camino server.
Nezadavat heslo do chatu. Pokud potiz trva, upresnit skutecne nove webove
prihlaseni a presne zneni chyby; nevracet se automaticky k jiz overenym bodum.

## Navrhovane dalsi kroky

Zadne dalsi zmeny zatim nejsou schvalene. Ucet neodstranovat a neresetovat.

## Zmenene nebo relevantni soubory

Tento handoff, MEMORY_INDEX.md a ACTIVE_PROJECTS.md. Soukromy snimek
zustava mimo Git. Camino p+n pred timto handoffem bylo dokoncene na
c670c8d9, 1847/1847, smoke 5/5, Git 0/0; build 15 a prenos 14s videa
Mila fyzicky potvrdil. Jde o casovy zaznam, nikoli dalsi zivy audit.

## Bezpecnost / neukladat

Zadna hesla, e-mailove adresy, texty zprav, kontakty ani obsah snimku.
Pouze rucni handoff; zadna casovana uloha ani dalsi push/deploy.

## Overene verejne podklady

- https://o-seznam.cz/napoveda/email/mohlo-by-se-hodit/postovni-programy-a-aplikace/
- https://o-seznam.cz/napoveda/ucet/dvoufazove-overeni/postovni-programy/
- https://o-seznam.cz/napoveda/email/mohlo-by-se-hodit/postovni-programy-a-aplikace/ukonceni-podpory-nezabezpeceneho-pripojeni/
- https://tailscale.com/kb/1103/exit-nodes
