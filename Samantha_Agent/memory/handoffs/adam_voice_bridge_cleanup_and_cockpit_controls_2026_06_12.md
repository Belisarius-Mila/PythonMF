Nazev: Adam Voice Bridge cleanup a Cockpit ovladani relaci
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ano
Datum: 2026-06-12

Co se resilo:
Stabilizace hlasoveho bridge mezi Cockpitem, Macem, iPhonem a aktualni Codex relaci.
Mila pracuje pres VS Code a nekdy otevira dalsi Codex relace pro vedlejsi ukoly;
po zavreni okna krizkem nebo po SSH navazani mohly zustat bezici stare relace
na dalsich TTY. To matlo stav voice bridge a mohlo zpusobit tiche nedoruceni
hlasoveho pokynu do aktualni relace.

Co je hotove:
- Mac Cockpit pres Tailscale uz smi pouzit lokalni systemovy hlasovy fallback,
  pokud nejde o mobilni klient. iPhone zustava browser-first a pouziva otevreny
  audiokanal.
- Restart Cockpitu ma ochranu proti zavodu s launchd: po ukonceni serveru nejdriv
  ceka, zda ho launchd znovu nezvedne, a nespousti druhou instanci, pokud uz
  endpoint odpovida.
- Hlasovy pokyn, ktery se ulozi do inboxu, ale nedoruci se do Codexu nebo je
  doruceni neoverene, uz nemlci: Cockpit zapise pending stav a posledni odpoved
  s duvodem.
- Do soukromeho runtime souboru `data/private/voice_inbox/delivery_attempts.jsonl`
  se zapisuje audit dorucovacich pokusu bez plneho textu pokynu.
- Voice bridge bere vice nez jednu aktivni Codex relaci jako varovani; vychozi
  limit je 1.
- Panel `Technicke nastaveni` / `Voice bridge cil` v Cockpitu ma tlacitko
  `Ukoncit stare relace`, ktere po potvrzeni ukonci jen stare Codex relace mimo
  aktualni `effective_tty`.
- Byly ukonceny zbytky starych testovacich relaci `ttys003` a `ttys005`; zustala
  jen aktualni relace `ttys001` a voice bridge hlasi `ok`.
- Zaverencny rucni test po commitu/pushi probehl OK: Mac hlasovy pokyn prosel
  do Codexu, iPhone pokyn prosel do Codexu, po otevreni audiokanalu se odpoved
  prehrala na iPhonu a test otevreni nove Codex relace, zavreni krizkem a uklid
  stare relace z Cockpitu probehl ve vsech fazich.

Co neni hotove:
- Voice bridge je pro aktualni provoz uzavreny jako funkcni.
- Pravidla pro bezny provoz vice paralelnich Codex relaci jsou domluvena, ale
  nejsou jeste samostatne rozpracovana do uzivatelske kucharky; neni to blokujici.

Dalsi krok:
Prejit na dokumentovy vault podle ranniho planu. Voice bridge pri dalsi praci
drzet v idealnim stavu `Codex relace: 1`; pokud Cockpit ukaze vice relaci, pouzit
`Ukoncit stare relace`.

Navrhovane dalsi kroky:
Okamzity:
- Zacit dokumenty read-only kontrolou stavu: dokumentovy vault, inboxy a kandidati
  k revizi bez mazani, presunu nebo tisku.

Volitelne:
- Dopsat kratkou kucharku pro Milu: jak bezpecne ukoncovat Codex (`Ctrl-C`,
  potom `exit`), jak pracovat s vedlejsi relaci a jak postupovat pri SSH.
- Casem rozlisit v UI hlavni relaci, vedlejsi relace a SSH relace lidstejsimi
  popisky nez jen TTY.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `scripts/restart_cockpit.py`
- `tests/test_cockpit.py`
- `tests/test_restart_cockpit.py`
- `memory/projects/tts_edge_audio_tools.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- `data/private/voice_inbox/` je runtime soukromy inbox, neni urcen ke commitu.

Bezpecnost / neukladat:
- Neukladat do gitu obsah hlasoveho inboxu, cele hlasove prepisy, tokeny, hesla
  ani osobni citlive texty.
- Tlačítko pro ukonceni starych relaci nikdy nema bez potvrzeni ukoncovat aktualni
  `effective_tty`; pokud neni chraneny cil jednoznacny, backend musi akci odmitnout.
