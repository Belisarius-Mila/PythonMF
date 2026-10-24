# Cesty a filmy: společný sedmidenní koš

Schválené zadání Míly 24. 10. 2026. Tento kontrakt popisuje vyvíjenou změnu;
není potvrzením nasazení, instalace ani výmazu skutečných dat.

## Význam akcí

- Smazat filmový projekt odstraní pouze jeho střih, revize, komentáře,
  importované hlasy, náhledy a všechny exporty/pracovní pokusy. Zdrojová
  cesta, její originály a jiné filmy zůstávají zachované.
- Smazat celou cestu všude začíná v iPhonu. Telefon cestu skryje a zastaví
  její další přenosy. Mac přijme idempotentní žádost s přesnou identitou.
  Vlastník na Macu zkontroluje rozsah a potvrdí přesun do koše na sedm dní.
- Po potvrzení Macu běží jedna lhůta od serverového UTC času. Do jejího
  uplynutí lze na Macu obnovit celou cestu nebo film. Žádné druhé kopie médií
  při přesunu do koše nevznikají. Koš místo neuvolňuje.
- Po lhůtě samostatná služba Camino dokončí trvalé odstranění na Macu.
  Telefon odstraňuje místní kopii až podle autentizovaného výsledku Macu,
  nikoli podle posunutých místních hodin. Offline zařízení zůstane viditelně
  nedokončené; úplné dokončení vyžaduje potvrzení výmazu z iPhonu.
- Obsah zůstává jednosměrný iPhone → Mac. Zpět chodí pouze stav žádosti,
  termín a potvrzení. Mazání cesty nelze nově zahájit z Macu.

## Synchronizace a soukromí

- Žádost nesmí ztratit ani přečíslovat již zmrazenou operaci. Před odesláním
  žádosti se doručí již přidělené obálky; další nepřidělená práce této cesty
  se pozastaví. Ostatní cesty smějí pokračovat a obnova žádosti práci vrátí.
- Po trvalém výmazu se odstraní i přijaté texty a osobní obsah původních
  synchronizačních obálek, konflikty, rozpracované uploady, jejich karantény,
  Viewer kopie a všechny filmové projekty této cesty v obou filmových kořenech.
- Zůstane pouze malý technický záznam identit a výsledku výmazu. Starý
  paket či obnovená fronta nesmějí smazanou cestu znovu vytvořit. Kontinuita
  kurzoru a přesný opakovaný požadavek ostatních cest zůstanou zachované.
- Koš je vlastnické rozhraní; Viewer, původní URL a filmové zdroje z něj nic
  nevydávají. Obnovení obnoví původní oprávnění, nevytvoří nový grant.
- Přenos, převod, render a výmaz používají společný souborový zámek.
  Nedokončený výmaz je trvalý stav a po restartu dokončí jen schválené cesty.
  Potvrzené kořeny dat musí odpovídat službě; výsledek pro iPhone vzniká až
  po úspěšném uvolnění databází. Přerušená kompaktace je obnovitelný stav.
  Cizí soubory, symlinky a odkazy mimo vybraný rozsah se odmítají.
- Starší externí/iCloud zálohy a ručně exportované cizí kopie nejsou živé
  spravované úložiště; jejich odstranění ani nemožnost obnovy z nich tato
  funkce neslibuje. Koš nevytváří skrytou druhou zálohu.

## Přejímka

Syntetické dva projekty se stejným názvem a datem: offline žádost, restart,
ztracená odpověď, pozastavená fronta, obnova, sedmidenní hranice, výmaz všech
typů médií a odvozenin, zmenšení databází, odmítnutí starých URL a paketů,
pozdní upload/Viewer/render, zachování druhé cesty a telefonní potvrzení.
Samostatně celý filmový projekt versus celá cesta. Skutečný iPhone/Safari
a fyzické uvolnění místa jsou samostatná přejímka po instalaci/nasazení.
