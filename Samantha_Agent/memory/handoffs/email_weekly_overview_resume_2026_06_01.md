Nazev: Email management - 7denni prehled hlavicek k navazani
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-01

Co se resilo:
- Mila spustil pevny vstup `Prosím přehled emailů za posledních 7 dní`.
- Byl proveden read-only prehled hlavicek za poslednich 7 dni.
- Vystup byl rozdelen na faktury/e-shopy, pojisteni/smlouvy, urady/dane a
  ostatni.
- Bezpecnostni rozsah byl dodrzen: necetla se cela tela, nestahovaly se prilohy,
  neoteviraly odkazy a nic se ve schrankach nemenilo.

Co je hotove:
- Git-safe pravidlo pevneho vstupu uz je v memory.
- Soukromy resume detail s UID a predmety je ulozen mimo git v:
  `data/private/email_session_handoffs/weekly_email_overview_2026_06_01_private.md`

Co neni hotove:
- Nebyl vybran konkretni e-mail k dalsimu zpracovani.
- Nebyly cteny konkretni e-maily a nebyla ukladana zadna PDF priloha.

Dalsi krok:
- Pri navazani precist soukromy resume soubor a zeptat se Mily, ktere UID chce
  zpracovat.
- Pravdepodobni kandidati jsou pojistne/smluvni e-maily a jedna Apple faktura,
  ale konkretni UID zustava jen v soukromem resume souboru.

Navrhovane dalsi kroky:
- Po Milove vyberu konkretniho UID vyzadat samostatne potvrzeni pro nacteni
  konkretniho e-mailu.
- Pokud e-mail obsahuje PDF, ulozeni do document vaultu delat az podle
  potvrzovaneho document-management workflow.

Zmenene nebo relevantni soubory:
- `data/private/email_session_handoffs/weekly_email_overview_2026_06_01_private.md`
- `memory/projects/email_readonly_oauth.md`
- `memory/technical/capability_routing_rules.md`

Bezpecnost / neukladat:
- Do git-safe memory neukladat konkretni UID, e-mailove adresy, cela tela,
  plne URL ani prilohy.
- Soukromy resume soubor je mimo git a smi slouzit jen pro navazani prace.
