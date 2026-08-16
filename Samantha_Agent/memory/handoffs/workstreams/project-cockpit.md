<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Stav znovu ověřen: 2026-08-16 08:17 CEST

### Hotovo
- Nový nezávislý audit `AuditCockpit56_2.txt` vyhodnotil současný Cockpit jako
  provozně zralý se silnou bezpečnostní a capability vrstvou.
- Capability audit eviduje 83/83 mapovaných agent tools a POST registry 88 akcí.
- Živý přednasazovací smoke prošel 5/5.

### Otevřeno
- Oprava autosave matematiky je v lokálním main, ale při auditu ještě nebyla v
  běžícím code stampu; její řízené nasazení je následující krok tohoto úkolu.
- Interaktivní vizuální audit nebyl v této relaci dostupný; ruční Mac/iPhone
  přejímka zůstává otevřená.

### Rizika
- Největší architektonické riziko je rozhodovací přetížení hlavní stránky a
  koncentrace frontendu i HTTP routingu do velkých souborů.
- Poslední úspěšná záloha byla při auditu starší než tři dny.

### Další krok
- Řízeně nasadit autosave WIP, ověřit code stamp a smoke 5/5; potom provést
  pouze dry-run bez mazání.

### Rozhodnutí
- Cockpit se nebude plošně přepisovat. Další vývoj má nejdřív zlepšit výběr a
  vysvětlení nejvýše tří skutečných dalších kroků a potom po malých doménách
  rozdělovat frontend a routing při zachování bezpečnostních kontraktů.

### Navrhované další kroky
- Decision Cockpit D4 jako read-only vrstva nad živými audity a pamětí.
- První modulární řez vést přes health/recovery/autosave.

### Technický stav checkpointu
- Před nasazením běžel code stamp `78a8f396027ad740`, aktuální main měl
  `2360eef3753bca5a`; rozdíl odpovídal čekajícímu WIP.
- Oprava autosave reportu má doloženou plnou bránu 1414/1414.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# Handoff pracovního proudu: Cockpit / hlavní architektura

Nazev: Cockpit / hlavní architektura
Pracovni proud: project-cockpit
Typ: Project
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ne

Co se resilo:
Kanonicky handoff byl zalozen prvnim potvrzenym checkpointem tohoto proudu.

Co je hotove:
- Viz chronologicke checkpointy nize.

Co neni hotove:
- Viz posledni checkpoint a jeho dalsi krok.

Dalsi krok:
Viz posledni chronologicky checkpoint.

Navrhovane dalsi kroky:
- Prubezne aktualizovat pouze potvrzenymi checkpointy tohoto proudu.

Zmenene nebo relevantni soubory:
- Viz jednotlive checkpointy.

Bezpecnost / neukladat:
- Neukladat hesla, tokeny, API klice ani soukromy obsah.

### Automatický checkpoint 2026-08-02 14:10 CEST

- Pracovní proud: `project-cockpit`
- Hotovo: Důležitá připomenutí lze doručit přímo přes Tailscale do soukromého Cockpitu; opakované doručení je idempotentní a iCloud zůstává záložní cestou.; Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.
- Otevřeno: Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.; Lokální commity čekají na samostatný denní GitHub balíček.
- Rizika: Žádné další doložené provozní riziko.
- Stav při vytvoření checkpointu: testy prošly; tento historický blok sám nepotvrzuje pozdější nasazení.
- Ověření: plná Cockpit brána: 1269 testů, 281.3 s, výsledek OK
- Změněné cesty před paměťovým zápisem (5): `Samantha_Agent/app/cockpit.py`, `Samantha_Agent/app/urgent_reminders.py`, `Samantha_Agent/tests/test_cockpit.py`, `Samantha_Agent/tests/test_urgent_reminders.py`, `Samantha_Agent/generated_shortcuts/Samantha_Dulezite_pripomenuti.xml`
- Commit: `Deliver urgent reminders directly to Cockpit`
- Další krok: Samostatně auditovat a potvrdit nasazení do Cockpitu; potom v iPhonové zkratce doplnit soukromou Tailscale adresu a provést jeden živý doručovací test.

### 2026-08-05 22:41 CEST – Falešné iCloud čekání odstraněno v kódu

Hotovo:
- Nezměněný iCloud placeholder, který je už úplně uložený v private indexu, se
  nepovažuje za nové čekající stažení.
- Nový, změněný nebo neúplný zdroj zůstává varováním.

Rozhodnutí:
- iCloud hydratace a doručení připomenutí jsou dva různé stavy.
- Přímá iPhonová Tailscale zkratka není součástí tohoto kroku.

Další krok:
- Lokálně commitnout a samostatně nasadit; potom zkontrolovat kartu v živém
  Cockpitu.

Navrhované další kroky:
- Dokončit konfiguraci přímé Tailscale zkratky a živý doručovací test.

Technický důkaz:
- Cíleně 14 testů; plná Cockpit Quality Gate 1311 testů, vše OK.

### 2026-08-07 13:59 CEST – Současný Cockpit a servisní orientace narovnány

Hotovo:
- Přímé zkratky připomenutí a Quick Notes jsou funkční.
- Lokální vstupy VocabularyFR, VocabularyIT a MultiLO jsou zapojené.
- Dokumentový trezor v Servisu ukazuje nejdřív aktuální stav a historii až po
  rozbalení.

Rozhodnutí:
- Historické servisní statistiky zůstávají dostupné, ale nejsou výchozím
  pracovním úkolem.

Další krok:
- Bez okamžité změny; sledovat konkrétní uživatelskou zkušenost.

Navrhované další kroky:
- Při dalším systémovém auditu ověřit stáří agregované projektové paměti.

Technický důkaz:
- Běžící Cockpit je serverově ověřený na `91dc700`; smoke 5/5.
