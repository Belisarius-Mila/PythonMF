Nazev: Adam Voice Mode / terminal bridge checkpoint
Priorita: 1
Stav: hotovo, ceka na dalsi realny test
Pripomenout pri startu: ne
Datum: 2026-06-05

Co se resilo:
- Cockpit hlasovy vstup uz umi ulozit prepis do private inboxu a Adam Voice Mode ho umi zpracovat pres lokalni watcher.
- Navazne vznikla snaha poslat bezpecne, read-only hlasove pokyny primo do beziciho Codex terminalu.
- Pri realnem testu se ukazalo, ze hlaska micha dohromady bezpecnostni blok a technickou chybu AppleScriptu.

Co je hotove:
- Commit `abf80ee Add Adam voice history bridge` pridal historii hlasovych odpovedi a zpetny zapis Adamovy odpovedi.
- Commit `e5b16fd Add Adam voice terminal bridge` pridal terminalovy bridge pro vkladani bezpecnych hlasovych pokynu do Codex terminalu.
- Commit `b595cab Improve Adam voice terminal fallback` opravil fallback a hledani terminaloveho tabu:
  - technicka chyba se uz nehlasi jako bezpecnostni odmitnuti,
  - bridge hleda Codex terminal nejen podle procesu v Terminal tabu, ale i podle TTY bezicich Codex procesu,
  - pri technickem selhani zustane pokyn pripraveny v private hlasovem inboxu.
- Realny dotaz z pending inboxu byl rucne zpracovan a odpoved byla zapsana do hlasove historie pres `scripts/adam_voice_reply.py`.
- Testy po posledni uprave prosly: `457 tests OK`.
- Po restartu hlasovy watcher bezel s terminal bridge zapnutym.

Co neni hotove:
- Neni jeste dlouhodobe overene, ze AppleScript vlozi dalsi hlasovy pokyn do spravneho Codex terminalu pri vice otevrenych tabech/relacich.
- Hlasovy watcher sam neni plnohodnotny agent: pokud se pokyn nedostane do Codex terminalu, umi ho bezpecne ponechat v inboxu, ale sam neprovede repo analyzu nebo slozitou praci.
- Pro rizikove nebo destruktivni pokyny zustava spravne chovani: nevkladat automaticky a vyzadat rucni presnou formulaci v Codex terminalu.

Dalsi krok:
- Pri dalsim hlasovem testu overit, zda se read-only pokyn skutecne objevi v aktivnim Codex terminalu.
- Pokud se znovu neobjevi, zkontrolovat macOS Accessibility/System Events opravneni a vypsat `target_ttys` z bridge vysledku.

Navrhovane dalsi kroky:
- Okamzite: udelat jeden jednoduchy read-only hlasovy test, napriklad dotaz na stav repa nebo pocet dnesnich Python radku.
- Navazujici: zvazit specialni "terminal voice mode" jen pro read-only pokyny a samostatne potvrzovaci brany pro vse, co zapisuje, maze, odesila nebo cte citlive soukrome soubory.
- Volitelne: doplnit Cockpit diagnostiku, ktera ukaze posledni terminal bridge status, `target_ttys`, posledni technickou chybu a cas posledniho prijateho pokynu.

Zmenene nebo relevantni soubory:
- `app/speech/terminal_bridge.py`
- `app/speech/adam_voice_mode.py`
- `tests/test_terminal_bridge.py`
- `tests/test_adam_voice_mode.py`
- `scripts/adam_voice_reply.py`
- `data/private/voice_inbox/` je runtime/private oblast mimo git.

Bezpecnost / neukladat:
- Do memory ani gitu neukladat plne private hlasove inboxy, citlive pokyny, tokeny, API klice ani soukrome rodinne/media detaily.
- Automaticke predani do terminalu smi byt jen pro bezpecne, read-only pokyny; ostatni pokyny maji zustat v inboxu a vyzadovat rucni potvrzeni.
