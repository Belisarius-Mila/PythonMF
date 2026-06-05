Nazev: Adam Voice Bridge - iPhone text fallback a macOS Accessibility checkpoint
Priorita: 1
Stav: rozpracovane / funkcni po opravnenech, ceka na finalni smoke test
Pripomenout pri startu: ano
Datum: 2026-06-06

Co se resilo:
- iPhone/Safari v Cockpitu hlasil, ze prohlizec nepodporuje nahravani z mikrofonu.
- Mac a iPhone videly jinou verzi Cockpitu, protoze bezely dve instance: lokalni `127.0.0.1:8770` a Tailscale `100.89.150.6:8770`.
- Hlasovy pokyn se z iPhonu dostal do private inboxu, ale bridge nejdrive selhal na predani do Codex terminalu.
- Diagnostika ukazala macOS omezeni:
  - prime TTY vlozeni vracelo `Operation not permitted`,
  - VS Code fallback pres `osascript` nemel povolene posilani klaves,
  - `System Events` nemel asistenční pristup.

Co je hotove:
- Cockpit ma textovy fallback pro iPhone:
  - nove tlacitko `Odeslat přepis Adamovi` v hornim radku panelu `Hlasový pokyn`,
  - novy endpoint `/api/speech/voice-text`,
  - backend uklada nadiktovany/textovy pokyn stejnou cestou do `data/private/voice_inbox/` jako audio prepis.
- Hlasovy panel nově navadi na diktovani do pole `Přepis`, kdyz prohlizec neumi prime nahravani.
- Tailscale Cockpit byl restartovan samostatne a iPhone uz nove tlacitko vidi.
- Terminal bridge diagnostika nově vraci detailni duvody, kdyz selze marker TTY i VS Code fallback.
- Mila povolil macOS Accessibility/System Events tak, ze VS Code fallback zacal fungovat.
- Realny read-only test z Cockpitu se dostal do Codex chatu:
  - pokyn na zjisteni poctu Codex procesu,
  - pokyn na spocitani otevrenych oken,
  - pokyn na soucet pridaných radku kodu za poslednich 24 hodin.
- Hlasove cteni vysledku pres `scripts/speak_edge_open.py` fungovalo po spusteni s povolenou siti/open MP3 cestou.

Co neni hotove:
- Stale je potreba finalni smoke test primo z iPhonu po cerstvém otevreni Cockpitu:
  1. nadiktovat text do `Přepis`,
  2. klepnout `Odeslat přepis Adamovi`,
  3. overit, ze se pokyn sam vlozi do Codex chatu bez rucniho Enteru,
  4. overit, ze Adam odpovi a precte strucny vysledek.
- V Cockpitu mohou bezet dve instance (`127.0.0.1` a Tailscale). Pri budoucich UI zmenach restartovat obe nebo pouzit primo Tailscale endpoint.
- Aktualni Codex relaci bezi vice paralelne; pri dalsim restartu/novem terminalu muze byt potreba znovu oznacit aktualni TTY marker.

Dalsi krok:
- Udelat finalni realny smoke test z iPhonu s formulaci bez slov jako `napiš`, `ulož`, `změň`, protoze ta slova zamerne spousteji rucni brzdu terminal bridge.

Navrhovane dalsi kroky:
- Okamzite:
  - z iPhonu otestovat jednoduchy read-only pokyn typu `Adame přes příkazovou řádku zjisti kolik běží Codex procesů`.
- Volitelne navazujici:
  - zprehlednit v Cockpitu stav dvou instanci: lokalni vs. Tailscale.
  - pridat provozni poznamku, ze po macOS/TCC zmenach je potreba povolit Accessibility pro aplikaci/proces, ktery spousti `osascript`.
  - pridat lehky cleanup/diagnostiku vice soucasnych Codex relaci.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/terminal_bridge.py`
- `tests/test_cockpit.py`
- `tests/test_terminal_bridge.py`
- `data/private/voice_inbox/` relevantni pro runtime testy, ale zustava mimo git.

Overeni:
- `python -m unittest tests.test_terminal_bridge tests.test_adam_voice_mode` proslo: 33 tests OK.
- `python -m unittest tests.test_cockpit` proslo: 89 tests OK.
- Prakticky test:
  - VS Code fallback bez Enteru po Accessibility oprávnění vratil `delivered_vscode`.
  - Read-only hlasovy pokyn se dostal do Codex chatu a byl zpracovan.

Bezpecnost / neukladat:
- Neukladat obsah soukromych hlasovych inboxu, cele prepisy citlivych pokynu ani runtime JSON z `data/private/voice_inbox/` do gitu.
- Hlasovy bridge smi automaticky posilat jen nizkorizikove read-only pokyny.
- Pokyny obsahujici mazani, zmeny dat, odesilani, commit, push, platby, tokeny, hesla nebo podobne citlive formulace zustavaji na rucni potvrzeni.
