# Agenda kalendáře na úvodní stránce Cockpitu

Stav 2026-11-07 23:41 CET: vývoj lokálně hotový, bez push/nasazení.
Kanonický proud project-cockpit; existující handoff a TVBCP aktualizované.

Pod důležitými připomenutími jsou nejprve úkoly/termíny z kalendáře,
potom schůzky a další události v klouzavém období 30 dní, chronologicky.
Šest položek na skupinu, zbytek rozbalit. Čas Europe/Prague, celodenní
a vícedenní položky, u přechodu půlnoci také koncové datum.

## Obnova a typy

- GET vrátí privátní cache bez nativního čtení. Samostatné POST refresh
  zahájí pozadí; hlavní status na něm nezávisí. Viditelná stránka obnovuje
  při návratu a po 120 s; server má 60s cooldown a jediný běžící pokus
  i napříč instancemi. Čtecí stav je omezený 90s lease. UI pouze čte stav,
  neopakuje mutaci při timeoutu. Neaktuální/neúplný zdroj není úspěšná prázdná agenda.
- Pouze dříve vybrané kalendáře a existující podepsaná čtečka. Žádná nová
  OS žádost, žádný rebuild helperů, žádný model, žádná úprava událostí.
- Čtečka neposkytuje stabilní nativní ID ani obchodní typ. Využíváme pouze
  ověřené účtenky Samanthy a přesnou shodu kalendář/název/start/end/all_day
  s normalizací UTC. Konfliktní a duplicitní obsah se neodhaduje.
- Neznámé položky zůstávají ve Schůzky a další události. Přes Typ lze
  zvolit Termín, Schůzka či Automaticky. Jde o soukromé zobrazení, nikoli
  editaci macOS. Označení následuje přesný obsah; změna názvu/času vyžaduje
  nové označení. Žádná heuristika podle délky, názvu či názvu kalendáře.
- agenda_refresh.json a agenda_types.json v již privátním app support
  používají samostatné zámky, atomický zápis a kontrolu revizí. Čtení labelů
  po chybě nevede k jejich přepsání. GET bez nastavení nevytváří úložiště.
- HTTP Host/Origin ochrany zůstaly zachované, query parametry odmítnuté,
  obsah událostí vykreslený přes textContent. Citlivá data nejsou v Gitu.

## Ověření

- Plná brána: 2896 testů OK, 31 SKIP; logs/calendar_agenda_gate_20261107.log.
- Finální změny UI: 347 cílených PASS včetně Node VM a skutečných HTTP
  testů; logs/calendar_agenda_targeted_20261107.log. Statická brána
  logs/calendar_agenda_static_20261107.log.
- Živý fresh read: 4 vybrané kalendáře, 7 budoucích událostí, 1 známý typ
  Samanthy; žádný zápis ani modelový tah, původní signed reader i writer
  ověřené beze změny. logs/calendar_agenda_live_read_20261107.log.
- Nativní Safari na izolovaném syntetickém fixture s opravdovou novou
  sekcí/CSS/JS: layout, změna typu 1/8 → 2/7, zachování po Obnovit,
  rozbalení zbytku PASS. Vlastní QA tab i server uzavřené, soubory zachované.
  logs/calendar_agenda_browser_20261107.log.
- Živá data nebyla použita v UI fixture. Fyzická iPhone a produkční UI
  přejímka tohoto nového panelu neproběhla. Původní jednoduché zadávání
  a navigace již vydané v 0850e6f3 (release 1b8a9680c8b54bf7c48895a8267dc924,
  CI 42418270872 success); toto není nové oprávnění k p+n.

Další krok: samostatně schválit p+n agendy, pak Mílova přejímka.
