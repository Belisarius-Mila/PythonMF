<!-- SAMANTHA_CURRENT_STATUS_START -->
## Aktuální stav

- Obnoveno potvrzeným checkpointem: 2026-08-02 14:10 CEST

### Hotovo
- Důležitá připomenutí lze doručit přímo přes Tailscale do soukromého Cockpitu; opakované doručení je idempotentní a iCloud zůstává záložní cestou.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

### Otevřeno
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

### Rizika
- Žádné další doložené provozní riziko.

### Další krok
- Samostatně auditovat a potvrdit nasazení do Cockpitu; potom v iPhonové zkratce doplnit soukromou Tailscale adresu a provést jeden živý doručovací test.

### Rozhodnutí
- Přímé Tailscale doručení je primární cesta a iCloud soubory zůstávají bezpečným fallbackem.

### Navrhované další kroky
- Opravit recovery dokončovací účtenky také pro lazy pracovní proudy, aby se stejný WIP blok neopakoval.

### Technický stav checkpointu
- Změna je otestovaná (1269 testů).
- Git před checkpointem: lokální `main` na `af834d3ce909`; GitHub může být starší a čeká na denní balíček.
- Poslední serverově potvrzené nasazení: `af834d3ce909` · odpovídá ověřenému main před tímto checkpointem · 0 testů · smoke 5/5 · 2026-08-01T15:54:02+00:00.
- Read-only živý stav: main=`local_ahead`, deployment=`verified_current`, runtime=`disconnected`.
- Tento snapshot je součástí lokálního checkpointu; push na GitHub zůstává odložený do potvrzeného denního balíčku.
- Tato sekce nahrazuje pouze předchozí aktuální souhrn; chronologické bloky níže zůstávají historickými snapshoty.
<!-- SAMANTHA_CURRENT_STATUS_END -->

# TVBCP: Cockpit / hlavní architektura

Pracovni proud: `project-cockpit`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Tento git-safe TVBCP zachycuje pouze potvrzena rozhodnuti, dulezite milniky,
testy, rizika a dalsi kroky pracovniho proudu. Neni kopii chatu a nesmi
obsahovat hesla, tokeny, API klice ani soukromy obsah.

Nove chronologicke zaznamy uprednostni lidsky stav v poradi Hotovo,
Rozhodnuti, Dalsi krok a Navrhovane dalsi kroky. Technicky dukaz je az
posledni kratka sekce. Starsi zaznamy se zpetne neprepisuji.

## Chronologicke zaznamy

Prvni zaznam prida potvrzeny checkpoint nize.

### 2026-08-02 14:10 CEST – Důležitá připomenutí lze doručit přímo přes Tailscale do soukromého Cockpitu; opakované doručení je idempotentní a iCloud zůstává záložní cestou.

Hotovo:
- Důležitá připomenutí lze doručit přímo přes Tailscale do soukromého Cockpitu; opakované doručení je idempotentní a iCloud zůstává záložní cestou.
- Předchozí stav main byl před tímto checkpointem serverově nasazený a ověřený.

Otevřeno:
- Pozdější nasazení nového checkpointu zatím není tímto snapshotem doložené.
- Lokální commity čekají na samostatný denní GitHub balíček.

Rizika:
- Žádné další doložené provozní riziko.

Rozhodnutí:
- Přímé Tailscale doručení je primární cesta a iCloud soubory zůstávají bezpečným fallbackem.

Další krok:
- Samostatně auditovat a potvrdit nasazení do Cockpitu; potom v iPhonové zkratce doplnit soukromou Tailscale adresu a provést jeden živý doručovací test.

Navrhované další kroky:
- Opravit recovery dokončovací účtenky také pro lazy pracovní proudy, aby se stejný WIP blok neopakoval.

Technický důkaz:
- plná Cockpit brána: 1269 testů, 281.3 s, výsledek OK.
- Pracovní proud: `project-cockpit`.
- Read-only živý stav při checkpointu: main=`local_ahead`, deployment=`verified_current`, runtime=`disconnected`.
