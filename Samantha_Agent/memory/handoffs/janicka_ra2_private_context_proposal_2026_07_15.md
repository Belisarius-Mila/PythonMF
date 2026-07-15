Nazev: Janička R-A2 – vlastní vlákno a soukromý dlouhodobý kontext
Priorita: 2
Stav: ceka na rozhodnuti
Pripomenout pri startu: ne
Datum: 2026-07-15

Co se resilo:

Míla navrhl, aby budoucí komunikaci v Cockpitu Janička obsluhoval samostatný
R-A2. Měl by vlastní trvalé app-server vlákno a vlastní průběžnou paměť, díky
níž by Jana při navazujících rozhovorech nemusela znovu vysvětlovat, co už se
řešilo.

Co je hotove:

- Je odsouhlasený koncept odděleného vlákna R-A2 pro Janičku.
- R-A2 nemá sdílet Mílovo vlákno Human–Adam ani jeho vývojový workspace,
  checkpointy, projektové TVBCP nebo nasazení.
- Má znovu použít ověřené komunikační jádro Human–Adam: app-server, spolehlivé
  doručení, reconnect, vlastnictví jednoho tahu, časomíru a případně zvuk.
- Dlouhodobý kontext Janičky nemá být projektový TVBCP v Gitu. Má jít o
  samostatnou soukromou paměť mimo Git, protože může zachycovat osobní nebo
  rodinný kontext.
- Paměť nemá být kopií chatu. Má držet jen stručná témata, přijaté dohody,
  preference, otevřené otázky a další krok.

Co neni hotove:

- Není navržený datový formát ani konkrétní umístění soukromého kontextu.
- Není rozhodnuto, co přesně smí R-A2 ukládat automaticky a co vyžaduje
  potvrzení Jany nebo Míly.
- Není navržené UI pro informaci `Kontext aktualizován`, kontrolu paměti,
  opravu nebo vrácení posledního zápisu.
- Není vyřešená rotace dlouhého vlákna, kompakce a obnova po havárii.
- Nebyla provedena implementace ani test.

Dalsi krok:

Navázat až po dokončení Human–Adam a jeho nouzového failover testu. Nejprve
sepsat krátký kontrakt R-A2: hranice vlákna, soukromí, datový model kontextu,
pravidla automatického zápisu, opravy paměti a bezpečné schopnosti Janičky.

Navrhovane dalsi kroky:

1. Založit pro R-A2 samostatné persistované app-server vlákno a samostatný
   runtime profil, ne kopii Human–Adam historie.
2. Použít kompaktní soukromý `Janička kontext` mimo Git. Načítat jej při
   startu, resume, rotaci nebo kompaktaci, ne celý znovu před každou zprávou.
3. Po potvrzeně dokončené výměně vyhodnotit, zda vznikla nová trvalá informace.
   Nezapisovat provozní mezistavy ani plný text rozhovoru.
4. Automatický zápis opatřit datem a stručným původem, potlačit duplicity a
   umožnit zobrazit, opravit nebo vrátit poslední změnu.
5. Zachovat standardní bezpečnostní brány Cockpitu. Oddělení vývojového
   workspace je oddělením role a kontextu, nikoli umělým omezením Jany.
6. Připravit testy oddělení vláken, obnovy po restartu, správné kompakce,
   nezapsání citlivého textu a opravy chybného automatického souhrnu.

Zmenene nebo relevantni soubory:

- `projects/janicka_cockpit_takeover.md`
- `projects/janicka_cockpit_kucharka.md`
- `handoffs/janicka_light_samantha_bridge_checkpoint_2026_07_03.md`
- `tvbcp/architektura_komunikace_samantha.txt`

Bezpecnost / neukladat:

- Do Gitu ani automatického kontextu neukládat hesla, tokeny, recovery klíče,
  celé e-maily, celé přepisy rozhovorů, rodná čísla ani zbytečné zdravotní,
  finanční nebo jiné citlivé podrobnosti.
- Soukromý kontext nesmí být bez výslovného rozhodnutí dostupný v Mílově
  vývojovém vlákně ani v projektovém TVBCP.
- Chybný automatický souhrn nesmí být považován za nevratnou pravdu; návrh musí
  obsahovat kontrolu, opravu a obnovu předchozí verze.
