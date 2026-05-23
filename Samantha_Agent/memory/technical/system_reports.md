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
| Knowledge inbox inventory | Bezpecny inventar velkych podkladu ve private knowledge inboxu bez cteni obsahu. | `.venv/bin/python scripts/samantha_knowledge_inbox.py` |
| Memory status | Stav lokalni pameti, startup kontextu, priorit a pripomenuti. | pres Samanthu tool `memory_status` |

## Pravidla

- Reporty maji byt kratke, ad hoc a bezpecne.
- Reporty nesmi cist ani vypisovat soukroma data, e-maily, tokeny nebo tajemstvi.
- Pokud report uklada data, musi jit o agregovanou datovou vetu bez nazvu
  souboru a bez soukromeho obsahu.
- Kdyz pri praci vznikne novy opakovatelny ad hoc status, audit nebo report,
  Samantha se ma zeptat: "Udelame z toho novy systemovy report?"
- Novy systemovy report pridej nejdriv do `app/system_reports.py`, potom do
  tohoto dokumentu a podle potreby do testu.
