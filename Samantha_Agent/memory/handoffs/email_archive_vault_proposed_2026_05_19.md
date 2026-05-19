Nazev: EmailArchiveVault - navrh kompletni lokalni zalohy e-mailu
Priorita: 1
Stav: ceka na implementaci
Pripomenout pri startu: ano
Datum: 2026-05-19

Co se resilo:
- Navrhl se samostatny `EmailArchiveVault` vedle existujiciho bezpecneho `EmailCaseVault`.
- Cil je po vyslovnem potvrzeni pro konkretni UID ulozit kompletni lokalni kopii duleziteho e-mailu pro pripad, ze e-mail z iCloudu zmizi.
- Dulezity rozdil:
  - `EmailCaseVault` je bezpecny pracovni case bez celeho tela, plnych URL a neredigovanych e-mailu.
  - `EmailArchiveVault` je citlivy lokalni archiv, muze obsahovat cele telo, HTML, plne URL a raw EML.

Co je hotove:
- Pouze navrh architektury a bezpecnostnich pravidel.
- Navrzena cilova slozka `data/email/archive/`.
- Navrzena struktura archivu napr. `data/email/archive/email-UID-slug/`.
- Navrzene soubory:
  - `metadata.json`,
  - `body.txt`,
  - `body.html`, pokud existuje,
  - `links.json` s plnymi URL,
  - `attachments/attachments.json`,
  - pozdeji soubory priloh,
  - idealne `original.eml`, pokud provider umi ziskat raw zpravu.
- Navrzene samostatne potvrzeni pro archivaci konkretniho UID.
- Navrzena budouci provider metoda typu `read_message_for_archive` nebo `read_raw_message_by_uid`.
- Navrzene budouci moduly:
  - `app/email/archive_models.py`,
  - `app/email/archive_service.py`,
  - `app/email/archive_tools.py`,
  - `tests/test_email_archive_service.py`,
  - `tests/test_email_archive_tools.py`.

Co neni hotove:
- Nic se zatim neimplementovalo.
- Neni vytvoren `EmailArchiveVault` service.
- Neni vytvoren Samantha tool pro archivaci.
- Neni doplnen provider raw read-only vystup.
- Neni upraven `.gitignore` pro `data/email/archive/`.
- Neni workflow pro pozdejsi stazeni konkretnich priloh.

Dalsi krok:
- Implementovat nejdrive cisty `EmailArchiveVault` service nad fake e-mailem bez IMAPu:
  - ulozit `metadata.json`,
  - ulozit `body.txt`,
  - ulozit `body.html`,
  - ulozit `links.json`,
  - ulozit `attachments/attachments.json`,
  - pridat testy nad temporary directory.
- Soucasne pridat `.gitignore` pravidlo pro `data/email/archive/`.
- Az potom doplnit read-only provider metodu a samostatne potvrzovany Samantha tool.

Zmenene nebo relevantni soubory:
- Zatim zadne implementacni soubory pro `EmailArchiveVault`.
- Relevantni existujici soubory:
  - `app/email/case_vault.py`,
  - `app/email/case_vault_tools.py`,
  - `app/email/icloud_provider.py`,
  - `app/email/models.py`,
  - `app/samantha_agent.py`,
  - `memory/handoffs/email_case_vault_save_tool_done_2026_05_19.md`.

Bezpecnost / neukladat:
- `EmailArchiveVault` je citlivy lokalni archiv, ne memory.
- Archiv se nikdy nema zapisovat do memory.
- Archiv se nikdy nema commitovat do gitu.
- Nutne pridat do `.gitignore`: `Samantha_Agent/data/email/archive/` nebo odpovidajici relativni cestu.
- Archivace nesmi byt automaticky napojena na triage.
- Archivace musi vyzadovat samostatne vyslovne potvrzeni s konkretnim UID.
- Tool nesmi otevirat odkazy.
- Tool nesmi spoustet ani automaticky stahovat prilohy.
- Tool nesmi nic odesilat, mazat, presouvat ani oznacovat jako prectene.
- Stahovani souboru priloh ma byt az dalsi samostatne potvrzovany krok.
- Cteni archivu zpet do chatu ma byt samostatny workflow s potvrzenim.
