Nazev: VoiceBridge full-access test a e-mail confirmation uzavreny
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-29

Co se resilo:
- Navazani po vypnuti Codex sandboxu a prakticky audit Cockpit oddilu VoiceBridge.
- Cilem bylo overit stabilni tok Cockpit/iPhone/Mac -> hlasovy inbox -> Codex -> odpoved do Cockpitu -> browser audio.
- Soucasti testu bylo i rizikovejsi workflow: priprava e-mailoveho draftu a skutecne odeslani az po samostatne presne tokenove potvrzovaci vete.

Co je hotove:
- Cockpit tlacitko `Otevrit audiokanal` automaticky kontroluje/spousti Adam Voice Mode watcher.
- Mezistav `Zprava vlozena do chatu a zahajeno zpracovani.` se zapisuje textove pres `scripts/adam_voice_reply.py --processing-started`.
- Finalni odpoved se zapisuje pres `scripts/adam_voice_reply.py --latest-command` a Cockpit ji pri otevrenem audiokanalu umi precist v browseru.
- Terminal/VS Code GUI bridge uz nehlasi jiste doruceni, pokud ho neumi overit; neovereny transport zustava jako pending/inbox stav.
- Start watcheru v Cockpitu detekuje rychly pad procesu a nehlasi falesne zeleny stav.
- Potvrzovaci karta `Codex ceka na potvrzeni` umi zobrazit tokenovou potvrzovaci vetu a po dokonceni se cisti.
- Realne probehly testy neodeslaneho draftu i potvrzeneho odeslani kratkych testovacich e-mailu; kopie odeslanych zprav se ulozily do iCloud Odeslanych.
- Mila po Testu 24 oznacil audit Cockpitu v oddilu VoiceBridge za zatim uzavreny a uspokojivy.

Co neni hotove:
- Neni zalozen ani implementovan samostatny Guard proti mazani po vypnuti sandboxu.
- Celkovy audit Cockpitu pokracuje jindy; uzavren je jen blok VoiceBridge.
- Pokud by se v normalnim provozu znovu objevily duplicity hlasovych pokynu nebo zpozdene potvrzovaci karty mezi Mac/iPhone, resit jako samostatny bug s konkretnim prikladem.

Dalsi krok:
- Pred Guardem muze Mila chtit jeste hledat nejake informace.
- Potom zalozit a implementovat Guard proti mazani pro full-access rezim.

Navrhovane dalsi kroky:
- Guard proti mazani zacit nejmensim uzitecnym krokem: centralni bezpecnostni wrapper nebo detekcni pravidla pro `rm -rf`, `git clean`, `git reset --hard`, force push a hromadne mazani/presuny.
- Zachovat plynulou praci pro read-only diagnostiku, testy, commit/push a bezne upravy; brzdit jen destruktivni nebo hromadne akce.
- Po Guardu se vratit k dalsim blokum Cockpit auditu podle potreby.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/adam_voice_mode.py`
- `app/speech/terminal_bridge.py`
- `app/email/outbound.py`
- `app/email/outbound_tools.py`
- `app/samantha_agent.py`
- `app/capabilities/registry.py`
- `tests/test_cockpit.py`
- `tests/test_adam_voice_mode.py`
- `tests/test_terminal_bridge.py`
- `tests/test_email_outbound_tools.py`
- `tests/test_capability_registry.py`
- `memory/projects/email_readonly_oauth.md`
- `memory/technical/codex_remote_approval_notice.md`

Overeni:
- Proslo `.venv/bin/python -m unittest tests.test_terminal_bridge tests.test_adam_voice_mode tests.test_cockpit tests.test_email_outbound_tools` s vysledkem 256 testu OK.
- Lokalni i Tailscale Cockpit prosly smoke checkem.
- Adam Voice Mode watcher po restartu bezel samostatne a Cockpit servery bezely lokalne i pres Tailscale.

Bezpecnost / neukladat:
- Do memory ani gitu neukladat e-mailove adresy, potvrzovaci tokeny, plne texty e-mailu, obsah soukromych dokumentu ani hesla.
- `data/email/outbox_drafts/`, `data/private/` a `data/session_autosave/` necommitovat.
- Skutecne odesilani e-mailu/SMS zustava dvoukrokove: draft/navrh a potom samostatna presna potvrzovaci veta.
