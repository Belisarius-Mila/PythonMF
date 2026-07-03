Nazev: Janička light Samantha bridge checkpoint
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-07-03

Co se resilo:
Janička Cockpit mel opakovany problem, kdy prvni textovy dotaz do Adama prosel
a odpoved se vratila, ale druhy dotaz uz se nedorucil. Projevy byly hlavne:
screen command probehl bez viditelneho request ID v relaci, macOS odmitl prime
TTY vlozeni s `Operation not permitted` a pri fallbacku z Cockpit serveru chybel
`node` v PATH.

Co je hotove:
- `app/adam_service.py` ma samostatnou light relaci `samantha_janicka`.
- Start light relace predava startovni prompt bez navrhu prace: precist pravidla,
  relevantni memory a cekat na dotazy z Janičky.
- Doruceni do screen relace overuje, ze se `Request ID` opravdu objevi v hardcopy
  vystupu relace.
- Pri neoverenem screen doruceni se zkousi prime doruceni do managed Codex TTY.
- Pokud macOS prime TTY doruceni odmitne, Janička prejde na read-only
  `codex exec` fallback, ktery odpoved zapise zpet do request/reply store.
- `codex exec` fallback doplnuje PATH prefixy `/usr/local/bin`,
  `/opt/homebrew/bin`, `/usr/bin`, `/bin`, `/usr/sbin`, `/sbin`, aby Cockpit
  server nasel `node`.
- Cockpit ma nove servisni endpointy a UI ovladani pro light relaci:
  `/api/janicka/light/status`, `/api/janicka/light/start`,
  `/api/janicka/light/stop`.
- Testy `tests.test_adam_service` a `tests.test_cockpit` prosly.

Co neni hotove:
- Chybi delsi rucni retest z Janička Cockpitu po cistem restartu Cockpitu a/nebo
  Macu.
- Neni rozhodnuto, jestli po stabilizaci zustane `samantha_adam` jako historicky
  fallback, nebo se Janička chat natrvalo sjednoti na `samantha_janicka` +
  `codex exec` fallback.

Dalsi krok:
Rucne v Cockpitu otestovat z okna `Janička` alespon tri navazujici textove dotazy
po sobe. Overit, ze se odpovedi vraci i po druhem a tretim dotazu, a ze pripadny
fallback pres read-only worker odpovi bez potreby rucniho startu Codexu.

Navrhovane dalsi kroky:
Okamzity dalsi krok je rucni retest vice dotazu v realnem Janička okne.
Volitelne po uspesnem retestu zjednodusit UI texty tak, aby Jana nevidela rozdil
mezi screen relaci, TTY a `codex exec` fallbackem.

Zmenene nebo relevantni soubory:
- `app/adam_service.py`
- `app/cockpit.py`
- `tests/test_adam_service.py`
- `tests/test_cockpit.py`
- `memory/projects/janicka_cockpit_takeover.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
Do gitu neukladat soukrome texty z Janička chatu, cele e-maily, tokeny,
hesla, recovery klice ani konkretni citlive rodinne nebo dokumentove udaje.
