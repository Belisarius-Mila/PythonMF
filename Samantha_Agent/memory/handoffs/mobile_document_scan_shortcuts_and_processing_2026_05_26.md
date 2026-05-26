Nazev: Mobilni sken dokumentu pres iPhone zkratky a priprava zpracovani
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-26

Co se resilo:
- Mila chce rychle ukladat vice dokumentu pres iPhone: zkratka vyfoti jednu nebo
  vice stran, stranky patri pod jeden technicky identifikator a na konci se ulozi
  lidsky nazev dokumentu.
- Druha zkratka ma zalozit request pro Samanthu, aby davkove zpracovala obsah
  mobilniho inboxu.
- Resilo se odliseni technickeho identifikatoru batchu, lidskeho nazvu dokumentu
  a budouciho `case_id` pro vecne souvisejici dokumenty.

Co je hotove:
- Otestovana a Milou potvrzena iPhone zkratka
  `Skenovat dokument pro Samanthu v4.shortcut`.
  - Je ulozena mimo repo v
    `/Users/miloslavfalta/Documents/Shortcuts Playground/`.
  - Uklada do spravneho iCloud inboxu `SamanthaDocumentInbox`.
  - Foti opakovane stranky a pta se `Dalsi strana dokumentu? Ano / Ne`.
  - Kratky kod na zacatku je technicky identifikator souboru.
  - Lidsky nazev dokumentu se uklada do manifestu jako `document_title`.
- Otestovana druha zkratka `Zpracovat dokumenty pro Samanthu.shortcut`.
  - Vytvari `SamanthaDocumentInbox/process_request.json`.
  - Mila potvrdil, ze request soubor je na miste.
- V kodu dokumentoveho vaultu jsou pridane tooly:
  - `scan_mobile_document_inbox` jako read-only kontrola iCloud inboxu;
  - `prepare_mobile_document_batch` jako write-safe priprava batchu.
- Realny test batchu `scan_B` prosel:
  - nalezen manifest a 2 stranky;
  - pripraven pracovni adresar
    `data/private/documents/mobile_inbox/processing/scan_b/`;
  - vytvoren PDF soubor `scan_b.pdf`;
  - zdrojove fotky v iCloud inboxu zustaly beze zmeny;
  - `prepare_document_import` nad pracovnim PDF probehl.

Co neni hotove:
- Neni jeste hotovy finalni potvrzovany import z pripravenych mobilnich PDF do
  private vaultu.
- Neni jeste doladena klasifikace pro testovaci dokumenty tak, aby Samantha
  rozlisila technicky test zkratky od realneho auto dokumentu.
- Neni jeste implementovane automaticke spojeni vecne souvisejicich dokumentu
  pres `case_id`; zatim je domluveny koncept.
- Doautomatizovani smazani docasneho adresare ma prijit az po potvrzenem importu
  a kontrole, ne v teto prvni bezpecne fazi.

Dalsi krok:
- Navazat kontrolnim importnim krokem: vzit pripraveny
  `data/private/documents/mobile_inbox/processing/scan_b/scan_b.pdf`,
  ukazat Milovi navrhovana metadata a az po potvrzeni ulozit do vaultu.

Navrhovane dalsi kroky:
- Okamzite: pridat potvrzovany tool pro finalni import pripravenych mobilnich
  batchu do vaultu.
- Potom: pridat lepsi pravidla pro `case_id`, aby vice samostatnych dokumentu
  mohlo byt svazano do jednoho pripadu bez míchani stran jednoho PDF.
- Pozdeji: po importu archivovat nebo presunout zpracovane soubory z iCloud
  inboxu jen po samostatnem potvrzeni Mily.

Zmenene nebo relevantni soubory:
- `app/documents/vault.py`
- `app/documents/tools.py`
- `app/documents/__init__.py`
- `app/samantha_agent.py`
- `tests/test_document_vault_tools.py`
- `memory/projects/document_management_private_vault.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`
- iCloud inbox mimo repo:
  `/Users/miloslavfalta/Library/Mobile Documents/iCloud~is~workflow~my~workflows/Documents/SamanthaDocumentInbox`
- Shortcuts vystupy mimo repo:
  `/Users/miloslavfalta/Documents/Shortcuts Playground/`

Bezpecnost / neukladat:
- Necommitovat `data/private/documents/mobile_inbox/processing/...`.
- Necommitovat fotky, PDF ani extrahovany plny text soukromych dokumentu.
- Necommitovat obsah iCloud inboxu ani `.shortcut` soubory bez samostatneho
  rozhodnuti.
- Do memory neukladat plny obsah dokumentu, rodna cisla, adresy, castky ani jine
  citlive udaje.
