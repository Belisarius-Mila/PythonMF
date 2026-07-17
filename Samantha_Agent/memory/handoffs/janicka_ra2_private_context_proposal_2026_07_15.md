Nazev: Janička R2-Adam – vlastní vlákno, soukromý kontext a TXT export
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ne
Datum: 2026-07-15; aktualizováno 2026-07-17

Co se resilo:

Míla navrhl, aby budoucí komunikaci v Cockpitu Janička obsluhoval samostatný
R2-Adam, původně pracovně označený R-A2. Měl by vlastní trvalé app-server vlákno
a vlastní průběžnou paměť, díky níž by Jana při navazujících rozhovorech nemusela
znovu vysvětlovat, co už se řešilo.

Dne 2026-07-17 byl R2-Adam založen jako samostatný projekt. Nová kanonická
hranice říká, že nesmí měnit ani mazat zdrojová data Samanthy, ale smí z
povolených dat vytvořit nový textový soubor a po samostatném potvrzení jej
odeslat na pevný soukromý kontakt Jany.

Co je hotove:

- Je odsouhlasený koncept odděleného vlákna R2-Adam pro Janičku.
- R2-Adam nemá sdílet Mílovo vlákno Human–Adam ani jeho vývojový workspace,
  checkpointy, projektové TVBCP nebo nasazení.
- Má znovu použít ověřené komunikační jádro Human–Adam: app-server, spolehlivé
  doručení, reconnect, vlastnictví jednoho tahu, časomíru a případně zvuk.
- Dlouhodobý kontext Janičky nemá být projektový TVBCP v Gitu. Má jít o
  samostatnou soukromou paměť mimo Git, protože může zachycovat osobní nebo
  rodinný kontext.
- Paměť nemá být kopií chatu. Má držet jen stručná témata, přijaté dohody,
  preference, otevřené otázky a další krok.
- R2-Adam je read-only vůči dokumentům, článkům, e-mailům, projektům,
  připomínkám, rodinným datům, Gitu a ostatním zdrojovým záznamům.
- Povolené zápisy jsou pouze jeho vlastní technický stav, verzovaný soukromý
  kontext, nový append-only TXT export, e-mailový draft a technická účtenka.
- TXT export smí vzniknout pouze z konkrétně povolených zdrojů, ukládá se mimo
  Git a nikdy nepřepisuje existující soubor.
- E-mailový příjemce je pevný lokální kontakt `Jana`; skutečná adresa se
  nezapisuje do Gitu ani modelového promptu.
- Odeslání je dvoukrokové: nejdřív export a draft s náhledem, potom samostatné
  potvrzení konkrétního draftu. Nejisté odeslání se automaticky neopakuje.

Co neni hotove:

- Není navržený datový formát ani konkrétní umístění soukromého kontextu.
- Není rozhodnuto, co přesně smí R2-Adam ukládat automaticky do vlastního
  kontextu a co vyžaduje potvrzení Jany nebo Míly.
- Není navržené UI pro informaci `Kontext aktualizován`, kontrolu paměti,
  opravu nebo vrácení posledního zápisu.
- Není vyřešená rotace dlouhého vlákna, kompakce a obnova po havárii.
- Není hotová matice povolených datových zdrojů, private export store, limity
  TXT souboru ani UI náhledu a potvrzení.
- Stávající outbound e-mail umí hlavně potvrzené přeposlání existujícího
  e-mailu; samostatná schopnost vytvořit nový TXT draft s přílohou neexistuje.
- Nebyla provedena implementace ani test.

Dalsi krok:

Neimplementovat další funkci naslepo. Nejprve uzavřít krátký kontrakt R2-Adam:
matici povolených read-only zdrojů, datový model soukromého kontextu, pravidla
automatického zápisu, append-only TXT export a dvoukrokové odeslání Janě.

Navrhovane dalsi kroky:

1. Založit pro R2-Adam samostatné persistované app-server vlákno a samostatný
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
7. Přidat testy, že R2-Adam nemění zdrojová data, nepřepisuje existující export,
   nečte tajemství, neposílá bez druhého potvrzení a neopakuje nejisté odeslání.
8. První exportní řez omezit na jeden bezpečný read-only zdroj, jeden UTF-8 TXT
   soubor a pevný kontakt Jany.

Zmenene nebo relevantni soubory:

- `projects/janicka_cockpit_takeover.md`
- `projects/janicka_r2_adam.md`
- `projects/janicka_cockpit_kucharka.md`
- `projects/email_readonly_oauth.md`
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
- Do exportu ani draftu automaticky nezahrnovat `.env`, hesla, tokeny, API a
  recovery klíče, autentizační konfiguraci nebo surové autosave/session logy.
- Skutečná adresa Jany, vytvořené TXT soubory, drafty a jejich obsah zůstávají
  pouze v soukromém úložišti mimo Git.
- R2-Adam nesmí dostat obecný zapisovací nebo mazací nástroj; pozdější úklid
  exportů musí být samostatný potvrzovaný servisní workflow.
