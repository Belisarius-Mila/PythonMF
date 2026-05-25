Nazev: iPhone zkratky - zmrazeni Mobile Input Layer
Priorita: 2
Stav: zmrazeno / funkcni zaklad
Pripomenout pri startu: ne
Datum: 2026-05-25

## Co se resilo

Mila prosel tiskovy TXT k iPhone zkratkam a upozornil, ze v nem chybel zacatek
inspirace: jeste pred volbou `Najit auto` a `Rychla poznamka pro Samanthu`
videl obecne priklady zkratek z MacStories / Shortcuts Playground, ktere ho
privedly ke zkouseni ruznych smeru.

Puvodni odpoved byla dohledana v autosave:

```text
Samantha_Agent/data/session_autosave/session_20260523_222223.txt
```

Kontext v autosave obsahuje nasi pozdejsi odpoved na otazku:

- 2026-05-23 20:03:55 Mila: "ty zkratky jsou super. Vis o nejakych dalsich,
  ktere by pro nas davali smysl?"
- 2026-05-23 20:04:47 Adam odpovedel seznamem kandidatu.

Dodatecne bylo 2026-05-25 dohledano webove pozadi na MacStories:

- MacStories mini-site pro Shortcuts Playground uvadi konkretni ukazkove zkratky:
  `ParkedCar`, `DailyDigest`, `ActionItems`, `FlightBoard`, `LinkCleaner`,
  `MeetingNotes`, `NightMode`, `PasswordGen`.
- Uvodni clanek Federica Viticciho uvadi dalsi priklady:
  poslednich 5 screenshotu poslat kontaktu pres iMessage, ukazat cas do dalsi
  udalosti v kalendari, append text/obrazky do denni Notion poznamky, nacist
  dnesni Todoist ukoly a preplanovat je, nahrat audio a prepsat ho pres Gemini,
  vypsat cron joby na Macu, ovladat lokalni/Mac shell veci, pouzit Obsidian CLI
  nebo web/API research pred vytvorenim zkratky.

Tento handoff slouzi jako inteligentni zmrazeni cele vrstvy zkratek: neotevirat
dalsi vyvoj bez vyslovneho navratu, ale zachovat smer, backlog a hranice.

## Klasifikace

iPhone zkratky nejsou samostatny projekt.

Kanonicka klasifikace:

- `iPhone Shortcuts / Mobile Input Layer`
- typ: `Infrastructure capability`
- ucel: mobilni vstupni a akcni vrstva napric projekty
- stav: pouzitelny zaklad, dalsi rozvoj priorita 2

Jednotliva zkratka neni Samantha tool. Zkratka je mobilni vstup, tlacitko nebo
front-end. Samantha tool je az lokalni Python schopnost, ktera vstup bezpecne
zpracuje.

## Hotove zkratky / schopnosti

- `Najit auto v3.shortcut`
  - funguje u Mily i Jany,
  - robustni vetev pro navigaci je `Get Parked Car Location -> Get Maps Link -> Open URL`.
- `Lékárna Jana.shortcut`
  - Mila potvrdil, ze funguje.
- `Rychlá poznámka pro Samanthu.shortcut`
  - uklada poznamky do iCloud kontejneru Zkratek,
  - Samantha umi zobrazit ocislovany seznam a detail pres quick notes tooly.

## Externi inspirace z MacStories / Shortcuts Playground

Toto je cast, ktera v tiskovem TXT chybela a ktera Milu puvodne navedla
k experimentum. Neni to nas backlog, ale inspiracni katalog moznosti.

Zdroje pro tuto cast:

- `https://www.macstories.net/shortcuts-playground/`
- `https://www.macstories.net/stories/introducing-shortcuts-playground/`
- `https://www.macstories.net/shortcuts/`
- `https://github.com/viticci/shortcuts-playground-plugin`

### Ukazky na Shortcuts Playground mini-site

1. `ParkedCar` / `Najit zaparkovane auto`
   - originalni prompt: ulozit, kde jsem zaparkoval, a pozdeji me dovest zpet
     k autu,
   - popis: zkratka ulozi aktualni polohu jako polohu auta a pri pozdejsim
     spusteni otevre navigaci v Mapach,
   - relevance pro Samanthu: uz prakticky overeno jako `Najit auto v3`;
     dobry vzor pro rodinne, nizkorizikove, lokalni mobilni workflow.

2. `DailyDigest` / `Ranni prehled`
   - originalni prompt: rychly ranni digest s pocasim, kalendarem a
     pripominkami,
   - popis: zkratka posklada zakladni informace pro zacatek dne,
   - relevance pro Samanthu: kandidat na ranni rodinny/prepracovni prehled,
     ale pouze read-only; pozor na zahlceni a duplicitni rutiny.

3. `ActionItems` / `Akcni body ze zapisu`
   - originalni prompt: vzit neusporadanou meeting note, vycistit z ni action
     items a poslat je do Reminders,
   - popis: prevod chaotickeho textu na ukoly,
   - relevance pro Samanthu: velmi silny smer pro QN; muze byt zaklad
     workflow "z poznamky udelej ukoly", ale citlive akce musi zustat
     potvrzovane.

4. `FlightBoard` / `Letova tabule`
   - originalni prompt: zobrazit budouci lety z kalendare jako jednoduchou
     odletovou tabuli,
   - popis: specializovany pohled nad kalendarem pro cestovani,
   - relevance pro Samanthu: inspirace pro cestovni rezim; muze se hodit pri
     dovolene, pojisteni, ubytovani, letenkach a dokumentech.

5. `LinkCleaner` / `Cistic odkazu`
   - originalni prompt: vycistit URL a odstranit tracking pred sdilenim,
   - popis: prijme odkaz, odstrani sledovaci parametry a pripravi cistou URL,
   - relevance pro Samanthu: vhodne pro nakupni pruzkum, archiv zdroju,
     sdileni odkazu bez balastu a ochranu soukromi.

6. `MeetingNotes` / `Zapis ze schuzky`
   - originalni prompt: zalozit meeting note s agendou, diskusi, ukoly a
     dalsimi kroky,
   - popis: vytvori strukturovanou poznamku pro jednani,
   - relevance pro Samanthu: vzor pro strukturovane handoffy, QN triage,
     projektove zapisy a "co jsme domluvili".

7. `NightMode` / `Nocni rezim`
   - originalni prompt: prepnout telefon do nocniho rezimu s Dark Mode a Night
     Shift,
   - popis: jednoduche systemove prepnuti telefonu pred spankem,
   - relevance pro Samanthu: inspirace pro osobni rezimy, ale neni primarni
     pro nasi praci; muze patrit do kategorie zdravych hranic prace/odpocinku.

8. `PasswordGen` / `Generator hesla`
   - originalni prompt: vytvorit silne heslo a hned ho zkopirovat,
   - popis: vygeneruje heslo a ulozi ho do schranky,
   - relevance pro Samanthu: technicky uzitecne, ale bezpecnostne rizikove;
     pro nas pouze jako inspirace, ne jako automaticky workflow s ukladanim
     hesel.

### Dalsi konkretni priklady z uvodniho clanku

9. `Hello World` / `Zkusebni Hello World`
   - popis: jednoduchy az absurdni test, ze generator umi vytvorit fungujici
     zkratku z prirozeneho jazyka,
   - relevance: dobry smoke test instalace Shortcuts Playgroundu.

10. `Send Last 5 Screenshots` / `Poslat poslednich 5 screenshotu`
    - popis: vzit pet poslednich screenshotu a poslat je kontaktu pres
      iMessage,
    - relevance: inspirace pro sdileni obrazovych podkladu; pro Samanthu by
      bylo bezpecnejsi ukladat do inboxu nez posilat bez potvrzeni.

11. `Time Until Next Event` / `Cas do dalsi udalosti`
    - popis: zjisti dalsi udalost v kalendari a ukaze, kolik casu do ni zbyva,
    - relevance: vhodne pro lehky osobni status, ale neni klicove.

12. `Append to Notion Daily Note` / `Pridat do denni Notion poznamky`
    - popis: prida text nebo obrazky do denni poznamky v Notion,
    - relevance: primej vzor pro nas `Samantha inbox` nebo denni log, jen bez
      Notion zavislosti; u nas radeji lokalni private inbox.

13. `Todoist Today Rescheduler` / `Preplanovani dnesnich ukolu`
    - popis: nacte dnesni ukoly z Todoist, uzivatel vybere, ktere preplanovat,
      a zvoli nove datum,
    - relevance: silny vzor pro potvrzovane zpracovani ukolu; u nas az po
      ustaleni reminders/task workflow.

14. `Audio Transcription with Gemini` / `Nahrat a prepsat audio`
    - popis: nahraje audio, prepis ziska pres Gemini API a vlozi text do
      schranky,
    - relevance: velmi blizke QN hlasovemu vstupu; u nas resit pres lokalni
      inbox, jasne zachazeni s API klici a soukromim.

15. `List Cron Jobs` / `Vypsat cron ulohy na Macu`
    - popis: zkratka na Macu spusti shell a zobrazi bezici cron joby,
    - relevance: inspirace pro systemove reporty Samanthy, ale rizikove; musi
      byt read-only a registrovane jako schvaleny systemovy report/tool.

16. `Control Mac / Shell Things` / `Ovladani Macu ze Zkratek`
    - popis: zkratky mohou spoustet lokalni shell nebo ovladat lokalni aplikace,
    - relevance: vysoka sila i riziko; pouzivat jen pres capability registry,
      ne jako volne ad hoc prikazy.

17. `Obsidian CLI Local/SSH` / `Obsidian pres CLI nebo SSH`
    - popis: zkratka pracuje s Obsidian CLI lokalne nebo vzdalene pres SSH,
    - relevance: konceptualne podobne "mobilni vstup -> znalostni system";
      u nas zatim pouze jako inspirace, ne jako tichy SSH.

18. `API Research Before Building` / `Otestovat API pred tvorbou zkratky`
    - popis: agent si pred tvorbou zkratky dohleda dokumentaci a otestuje API,
    - relevance: presne odpovida nasemu smeru profesionalizace; pred citlivejsi
      automatizaci nejdriv test, pak shortcut, pak rucni overeni.

### Relevantni napady z MacStories Shortcuts Archive

MacStories Archive je sirsi katalog stovek zkratek. Neni ucel kopirovat vse,
ale tyto typy jsou pro Samanthu nejzajimavejsi:

19. `Take Screenshot and Share` / `Vyfotit obrazovku a sdilet`
    - relevance: rychle predani chyby nebo stavu aplikace do inboxu.

20. `MultiButton` / `Vicenasobne tlacitko`
    - relevance: jedno tlacitko muze podle kontextu spustit ruzne akce; vhodne
      pro budouci "Samantha akce" na Action Buttonu.

21. `Screenshot, Markup, and Share` / `Screenshot, anotace a sdileni`
    - relevance: uzitecne pro technickou podporu, bug reporty, navrhy UI a
      dokumentovani problemu.

22. `Run Shortcut From Folder` / `Spustit zkratku ze slozky`
    - relevance: muze pomoci s organizaci vetsiho mnozstvi zkratek.

23. `Blinds After 9` / `Zaluzie po devate`
    - relevance: ukazuje kombinaci HomeKit + podminky Wi-Fi + cas; pro nas
      vzor podmineneho domaciho workflow, ne priorita.

24. `Video Processor (Claude/Gemini)` / `Zpracovani videa pres AI`
    - relevance: mozny budouci smer pro rodinna videa, YouTube prepisy nebo
      znalostni intake; vyzaduje soukromi a cost kontrolu.

25. `Compress Dropbox Files` / `Zabalit vice souboru do ZIP`
    - relevance: obecne archivacni workflow; pro nas spise lokalni private
      document vault nez Dropbox.

26. `Extract Files from Zip Archive` / `Rozbalit archiv`
    - relevance: uzitecne pro budouci ChatGPT exporty, stazene baliky a velke
      podklady.

27. `Delete Old Files` / `Smazat stare soubory`
    - relevance: jen jako varovny priklad; u Samanthy mazani vzdy vyzaduje
      explicitni potvrzeni.

28. `Copy iCloud Drive Link` / `Zkopirovat iCloud Drive odkaz`
    - relevance: sdileni dokumentu rodine nebo sobe, ale pozor na soukromi a
      nahodne verejne odkazy.

29. `File Downloader` / `Stahnout soubor z URL`
    - relevance: podobne nasemu knowledge inboxu; vhodne az s kontrolou typu
      souboru, umisteni a zdroje.

30. `Extract All Files from Archive` / `Rozbalit vsechny soubory`
    - relevance: prakticke pro importy, exporty a archivaci.

31. `Share Dropbox Photo` / `Sdilet fotku pres Dropbox`
    - relevance: vzor pro foto/video workflow, ale u nas spise iCloud/Photos
      export do private inboxu.

32. `Rename and Save File` / `Prejmenovat a ulozit soubor`
    - relevance: silny vzor pro document intake: prijmout soubor, prejmenovat
      podle pravidel, ulozit do spravneho inboxu.

33. `Preview Folder Contents` / `Nahled obsahu slozky`
    - relevance: vhodne pro "co je v inboxu" nebo "co ceka ke zpracovani".

34. `Shortcuts Backup` / `Zaloha vsech zkratek`
    - relevance: dulezite pro stabilizaci nasi vrstvy zkratek; kandidat na
      budouci udrzbu po vetsim rozsireni zkratek.

Poznamka pro budouci praci:

- inspiracni seznam obsahuje i rizikove smerovani typu SSH, shell, API tokeny,
  hesla, mazani souboru a posilani zprav; pro nasi Samanthu to patri pouze do
  potvrzovaneho, auditovaneho workflow, ne do automaticky spustenych zkratek.
- jako nejtezitelnejsi smer se zatim jevi: `Samantha inbox`,
  `Quick Notes -> action items`, `document/faktura intake`, `link cleaner`,
  `folder preview/status`, `shortcuts backup` a read-only systemove reporty.

## Nasi puvodni kandidati na zkratky

Toto je nase pozdejsi odpoved v autosave. Neni to externi inspirace od autora,
ale navazujici lokalni shortlist pro Milu a Samanthu.

1. `Rychlá poznámka pro Samanthu`
   - nadiktovat text na iPhonu,
   - ulozit jako soubor do inboxu pro pozdejsi zpracovani,
   - zvolena jako prvni opravdu silna dalsi zkratka a realne implementovana.

2. `Dokument do trezoru`
   - vyfotit nebo naskenovat papir,
   - ulozit PDF do soukromeho document inboxu,
   - navazuje na private document vault.

3. `Faktura / nákup do archivu`
   - ze sdileni poslat PDF, e-mailovy vystrizek nebo fotku uctenky do nakupniho
     archivu,
   - navazuje na koncept `Nakupni pruzkum a archiv nakupu`,
   - vhodne pro Dolphin E20 / RobotWorld a podobne nakupy.

4. `Lékárna pro rodinu`
   - otevrit domaci Lekarnu,
   - pripadne rovnou konkretni rezim pro Janu / Milu / domaci leky,
   - cast pro Janu byla realne implementovana.

5. `Poslat polohu / navigace domů`
   - jednoduche rodinne zkratky,
   - poslat aktualni polohu Jane,
   - navigovat domu,
   - najit zaparkovane auto.

6. `Rychlá připomínka`
   - nadiktovat napr. "pripomen mi zitra zavolat technikovi",
   - ulozit pripominku bez dlouheho tukani,
   - vyzaduje jasnou hranici mezi lokalni poznamkou, reminders workflow a
     citlivymi akcemi.

7. `Samantha inbox`
   - univerzalni zkratka,
   - text, odkaz, fotka nebo PDF se ulozi do jednoho vstupniho adresare,
   - pozdeji se spolecne roztidi do projektu/toolu/archivu/pripominky.

## Quick Notes a strategicke smerovani

Po implementaci `Rychlá poznámka pro Samanthu` zacaly vznikat strategicke QN:

- QN #4 + #6: bezpecny akcni inbox, ale ne tichy SSH,
- QN #10: ziva znalostni databaze z velkych chat exportu,
- QN #13: mapa systemu Samanthy,
- QN #16: webovy kokpit,
- QN #17: cviceni pro Milu a Janu.

Dalsi QN z 2026-05-25:

- QN Matysek EN: revize hlasu Bunny/Beny/sova a navrh lesni skoly se sovou,
  predmety a odpovedmi ano/ne; patri do projektu `Matysek English / MMTX`, ne
  do vrstvy zkratek.
- QN inteligentni zpracovani emoci: patri k eseji / osobnimu systemu, ne ke
  zkratkam.
- QN remote Mac action: teoreticke spousteni Mac aplikace nebo infrastruktury
  z iPhonu; rizikove, pouze jako hlidany napad za bezpecnostni branou.
- QN Photo Inbox: z vybrane fotky ulozit kopii do soukromeho inboxu k
  pozdejsimu trideni do dovolene, vyletu, alba nebo rodinneho projektu; dobry
  budouci nizkorizikovy kandidat.

Samostatny feedback k top 3 informacnim smerum je ulozen v:

```text
Samantha_Agent/memory/handoffs/quick_notes_infsystem_top3_feedback_2026_05_24.md
```

## Bezpecnostni hranice

Zkratky mohou:

- zachytit text, odkaz, fotku nebo PDF,
- ulozit vstup do soukromeho inboxu,
- pripravit navrh ukolu,
- spustit nizkorizikovou lokalni iPhone akci.

Zkratky nesmi bez potvrzeni:

- posilat citlive e-maily,
- mazat soubory,
- commitovat nebo pushovat,
- objednavat nebo platit,
- pracovat s hesly, tokeny nebo API klici,
- menit systemove nastaveni,
- delat akce "tiche SSH" stylem.

Pro citlive veci zustava vzor:

```text
navrh -> potvrzeni -> provedeni -> zaznam
```

Kanonicka architektura:

```text
iPhone zkratky -> lokalni/private inbox -> Samantha tool -> potvrzeni/kokpit -> zaznam
```

Jedna veta:

```text
Zkratky jsou rychly mobilni vstup a lehky front-end, ne samostatny agent a ne
nekontrolovany vzdaleny ovladac Macu.
```

## Finalni rozhodnuti po zpracovani pracovniho TXT

Mila 2026-05-25 potvrdil tato pravidla:

1. Quick Notes se nemaji automaticky mazat ani precislovavat.
   - Cisla QN zustavaji stabilni.
   - Poznamky oznacene jako "vymazat" jsou jen kandidati na pozdejsi uklid.
   - Skutecne mazani vyzaduje samostatne potvrzeni.

2. Klasifikaci QN zatim nema resit vice tlacitek na iPhonu.
   - Zkratka ma zustat co nejjednodussi.
   - Adam pri zpracovani navrhne klasifikaci.
   - Mila pripadne potvrdi nebo opravi.

3. Zmrazeni neznamena konec vrstvy zkratek.
   - Znamena neotvirat dalsi implementacni vetve bez vyslovneho navratu.
   - Znamena drzet zkratky jako `Mobile Input Layer`.
   - Slozitejsi logika patri do Samantha toolu a casem do weboveho kokpitu.

Navrzene QN stavy / klasifikace:

- `idea`
- `reminder`
- `task_candidate`
- `sensitive_action`
- `archive_candidate`
- `project_candidate`
- `tool_candidate`
- `memory_candidate`
- `processed`
- `trash_candidate`
- `promoted_to_project`
- `promoted_to_tool`
- `promoted_to_memory`

## Co neni hotove

- `mark_quick_note_done`
- archivace / processed stav pro QN
- klasifikace QN: `idea`, `reminder`, `task_candidate`, `sensitive_action`,
  `archive_candidate`
- "z poznamky c. X udelej tool" jako workflow
- "z poznamky c. X udelej projekt" jako workflow
- Quick Notes status system report
- systemova mapa Samanthy
- bezpecny asynchronni akcni inbox s potvrzenim
- univerzalni `Samantha inbox`

## Backlog po zmrazeni

Priorita A - jadro vrstvy:

- Quick Notes status report.
- Processed/archive stav pro QN.
- QN #4/#6: bezpecny akcni inbox, ale bez ticheho SSH.

Priorita B - prakticke vstupni workflow:

- Dokument do trezoru.
- Faktura/nakup do archivu.
- Photo Inbox / dovolenkova fotka k vytezeni.

Priorita C - uzitecne, ale ne urgentni:

- LinkCleaner / cistic odkazu.
- Screenshot do inboxu.
- Preview Folder Contents / nahled obsahu slozky.
- Shortcuts Backup / zaloha zkratek.

Priorita D - rizikove nebo pozdejsi:

- Remote Mac Action.
- Shell/SSH ovladani Macu ze zkratky.
- Video Processor pres AI.
- Automaticke odesilani zprav/e-mailu bez potvrzeni.

## Rozhodnuti o zmrazeni

Zkratky maji velky potencial, ale nemaji ted spolknout hlavni pozornost.

Aktualni rozhodnuti:

- ponechat funkcni zaklad,
- neotvirat dalsi vetve bez vyslovneho navratu,
- brat zkratky jako `Mobile Input Layer`,
- backlog drzet v tomto handoffu,
- po navratu vybrat jen jeden maly dalsi krok.
- aktualni priorita po zmrazeni je prepnout na `Matysek English / MMTX`.

## Doporuceny dalsi krok pri navratu

Pokud se Mila vrati ke zkratkam, nejdriv:

1. Nacist:

```text
Samantha_Agent/memory/technical/iphone_shortcuts_playground.md
Samantha_Agent/memory/handoffs/iphone_shortcuts_freeze_infrastructure_layer_2026_05_25.md
Samantha_Agent/memory/handoffs/quick_notes_infsystem_top3_feedback_2026_05_24.md
```

2. Zobrazit kratky stav:

- hotove zkratky,
- pocet QN,
- poslednich 5 QN,
- rozpracovane kandidaty,
- doporuceny jeden dalsi krok.

3. Vybrat maximalne jednu vec:

- `Quick Notes status`,
- processed/archive stav QN,
- `Dokument do trezoru`,
- `Faktura / nakup do archivu`,
- `Photo Inbox`,
- nebo `Samantha inbox` jako opatrny intake bez automatickych akci.

## Doporuceny dalsi krok ted

Prepnout pozornost na `Matysek English / MMTX`, protoze Mila bude 5 dni s
Matyskem a chce obohatit aplikaci realnym obsahem k okamzitemu testovani.

## Zmenene nebo relevantni soubory

- `Samantha_Agent/memory/technical/iphone_shortcuts_playground.md`
- `Samantha_Agent/memory/handoffs/iphone_shortcuts_quick_notes_continue_2026_05_23.md`
- `Samantha_Agent/memory/handoffs/quick_notes_infsystem_top3_feedback_2026_05_24.md`
- `Samantha_Agent/app/quick_notes.py`
- `Samantha_Agent/scripts/samantha_quick_notes.py`
- `Samantha_Agent/tests/test_quick_notes.py`
- `Samantha_Agent/data/private/quick_notes/index.json` - soukrome, necommitovat
- `Samantha_Agent/data/private/quick_notes/shortcuts_chat_rekonstrukce_PRACOVNI_KOPIE_PRO_MILU_2026-05-25.txt`
  - soukrome, necommitovat; obsahuje Milovu pracovni anotovanou verzi
- `/Users/miloslavfalta/Documents/Shortcuts Playground/` - hotove `.shortcut`
  soubory mimo git

## Bezpecnost / neukladat

- Necommitovat skutecny obsah Quick Notes inboxu.
- Necommitovat `.shortcut` soubory ani private request drafty.
- Necommitovat soukroma data z iCloud Drive, dokumentu, faktur ani nakupniho
  archivu.
- Do memory ukladat jen workflow a shrnuti, ne citlivy obsah.
