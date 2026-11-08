# Hodinové kalendářové návrhy — lokální doplněk

Datum: 2026-11-08 18:22 CET
Pracovní proud: project-email-cases; stávající UI kontrakt project-cockpit.
E-mailový kanonický handoff: continuous_personal_agent_2026_11_04.md.
Samostatný e-mailový TVBCP není domluvený a nevzniká; UI rozhodnutí jsou
v existujícím project-cockpit. Toto není uzavření chybějící e-mailové TVBCP vazby.

Mílova podmínka: zachovat již implementované fungující chování.
Rozsah: lokální vývoj bez aktivace, placeného pilotu, push a nasazení.

## Výsledek

- Nový přepínač ServiceSettings.calendar_suggestions má výchozí false.
  Bez něj se používá původní výstupní schéma, modelový prompt i EmailProposal.
  SDK větev se nerozšiřuje. Živá instalovaná kopie zůstává f2d6ef79.
- Zapnutá větev přidává do jediného strukturovaného posouzení calendar_candidate.
  E-mailová pole i podpis se validují jako dosud. Candidate má stejné evidence,
  materialize a následnou validaci jako ručně připravený kalendářový návrh.
- Soukromý doplněk calendar_suggestion je uložený atomicky vedle proposal,
  nikoli uvnitř editovaného/archivovaného e-mailového kontraktu.
  Je vázaný na původní content_digest; invalid citace nezahodí e-mailový návrh.
- Relevantní schůzka/termín zůstane viditelnou důležitou kartou i při chybné
  important=false klasifikaci modelu. Bez relevantního návrhu se klasifikace nemění.
- Přehled předává jen stav doplňku, nikoli duplicitní zdroj/candidate/usage.
  Tlačítko Do kalendáře, editor a čtyři editovatelná pole zůstávají stejné.
- Explicitní prepare převezme připravený návrh jednou atomickou transakcí,
  bez IMAP/modelu, s výchozími alarmy a původním revizním/kolizním protokolem.
  GET jen čte. Existující pokus, rozepsané hodnoty i write marker mají přednost.
- Ruční příprava u starých a nepřipravených karet zůstává beze změny.
  Formální pozvánka/recurrence se nikdy nepromění v automatický create.
- Původní funkce source_context přemístěná do společného modulu beze změny AST;
  import app.email.calendar_draft.source_context zůstává kompatibilní.

## Ověření

- Cílená sada: 214 testů PASS; log logs/calendar_hourly_targeted_20261108.log.
- Nový modul: 20 scénářů, samostatný nový HTTP scénář ve stávající sadě.
- E-mailový i kalendářový Node browser kontrakt PASS. Zachování starých karet,
  konceptů, formuláře odpovědi, polling, ruční archivace/odesílání a kolize
  pokryté existujícími regresními testy.
- První plný běh: 3199 testů / 31 SKIP; jediné selhání byla stará délka/hash email_agent assetu po záměrné změně. Opravená pouze očekávaná délka, počet řádků a SHA této stránky; 23 frontendových testů následně PASS. Původní neúspěšný log zachovaný jako calendar_hourly_full_gate_20261108.log.
- Závěrečná plná Cockpit brána: 3199 testů OK (31 SKIP), 604,272 s unit část; logs/calendar_hourly_full_gate_v2_20261108.log.

## Provozní hranice a další přejímka

- Běžící Cockpit zůstává f51f3412 / otisk 2c6f32d804c8a870, ikony c14f2524
  nepublikované. Žádná změna service.json, modelové role, instalace, helperů,
  kalendářového výběru nebo Datova worktree. Obnovovací TXT beze změny.
- Přepínač nyní nezapínat ve staré službě: její strict parser nový klíč nezná.
  Nejprve samostatné autorizované p+n kompatibilního Cockpitu a registrovaný
  upgrade vlastní hodinové kopie, pak teprve samostatné povolení nové funkce.
  Návrat ke staré kopii nesmí nechat nový klíč ve starém strict nastavení.
- Přijatá událost se nezapisuje na pozadí; konkrétní zápis stále vyžaduje
  lidský klik po čerstvé kontrole. Testy používají jen dočasná syntetická data.
- Zapnutý návrh přidává prompt/schema a výstupní tokeny. Privátní doplněk
  uchovává známou duration/usage posouzení, chybějící usage je None.
  Stejný počet tahů není důkaz stejné ceny; skutečné měření teprve při přijatém pilotu.
- Modelová sémantická správnost a Mac/iPhone přejímka nejsou doložené syntetikou.
  Neřeší se tím původní samostatné P0 SMS a CLI tracing body.
