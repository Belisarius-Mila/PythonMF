# Samantha system reports

Kanonicky prehled systemovych reportu je v kodovem registru
`app/system_reports.py`. Na dotaz typu "jake mame systemove reporty" ma
Samantha pouzit tool `samantha_system_reports`.

## Aktualni reporty

| Report | Ucel | Spusteni |
| --- | --- | --- |
| Health check | Rychla kontrola rozpracovanosti, git stavu, pending bodu a varovani. | `.venv/bin/python scripts/samantha_health_check.py --mode quick` |
| Kvantitativni status | Objemovy rust Samanthy: soubory, radky, lokalni stav vs git tracked. | `.venv/bin/python scripts/samantha_quantitative_status.py` |
| Capability audit | Prehled registrovanych schopnosti, toolu, workflow a hlavních rezerv. | `.venv/bin/python scripts/samantha_capability_audit.py` |
| Systemovy audit projektu, toolu a vrstev | Aktualni lidsky itinerar podobny rucnimu auditu: projekty, provozni rizika, tooly, vrstvy a nejmensi dalsi krok. | `.venv/bin/python scripts/samantha_project_audit.py --mode quick` |
| Knowledge inbox inventory | Bezpecny inventar velkych podkladu ve private knowledge inboxu bez cteni obsahu. | `.venv/bin/python scripts/samantha_knowledge_inbox.py` |
| Downloads inventory | Bezpecny inventar top-level souboru ve Stazenych pred kopirovanim do knowledge inboxu. | `.venv/bin/python scripts/samantha_downloads_to_knowledge_inbox.py --list` |
| iPhone shortcuts status | Kontrola pripravenosti MacStories Shortcuts Playground pro tvorbu iPhone zkratek. | `.venv/bin/python scripts/samantha_iphone_shortcuts.py --status` |
| Rodinny kalendar readiness | Redigovana read-only kontrola rezimu, lokalniho planovace, Keychain reference, persistence a recovery blokeru bez cteni hesla, zapisu nebo odeslani. | `.venv/bin/python scripts/family_calendar_delivery_readiness.py` |
| Memory status | Stav lokalni pameti, startup kontextu, priorit a pripomenuti. | pres Samanthu tool `memory_status` |

## Pravidla

- Reporty maji byt kratke, ad hoc a bezpecne.
- Reporty nesmi cist ani vypisovat soukroma data, e-maily, tokeny nebo tajemstvi.
- Pokud report uklada data, musi jit o agregovanou datovou vetu bez nazvu
  souboru a bez soukromeho obsahu.
- Systemovy audit projektu smi pri `--save` ulozit jen git-safe textovy report
  do `memory/reports/`; nesmi cist private vault, e-maily, soukrome dokumenty
  ani fulltexty clanku.
- Kdyz pri praci vznikne novy opakovatelny ad hoc status, audit nebo report,
  Samantha se ma zeptat: "Udelame z toho novy systemovy report?"
- Novy systemovy report pridej nejdriv do `app/system_reports.py`, potom do
  tohoto dokumentu a podle potreby do testu.
