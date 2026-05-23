# E-mail read-only OAuth integrace

## Cil

Mila chce jit cestou bezpecne dlouhodobe integrace, ve ktere Samantha dokaze cist vybrane e-maily pres OAuth, ne pres Apple Mail GUI. Prvni verze ma byt read-only a bez moznosti odesilani, mazani nebo uprav zprav.

## Bezpecnostni pravidla

- Zacit pouze ctenim e-mailu, ne odesilanim.
- Nepouzivat trvaly pristup ke vsem akcim ve schrance, pokud staci uzsi opravneni.
- Tokeny, client secret, refresh tokeny ani skutecne adresy neschranovat v gitu ani v pameti.
- Tajemstvi patri pouze do lokalniho `.env`, macOS Keychainu nebo jineho lokalniho secret store.
- Do pameti se smi zapisovat jen architektura, rozhodnuti, obecne scope a provozni pravidla.
- Obsah e-mailu neukladat do dlouhodobe pameti automaticky; ukladat jen vyslovne schvalene shrnuti.
- Prvni implementace musi mit rucni potvrzeni Milou pred ulozenim jakehokoli poznatku z e-mailu do `memory/`.

## Doporuceny smer podle poskytovatele

### Gmail

Pro Gmail je potreba pocitat s tim, ze plny read-only scope `https://www.googleapis.com/auth/gmail.readonly` je podle oficialni dokumentace Google vedeny jako restricted scope. To je porad bezpecnejsi nez `https://mail.google.com/`, ale pro verejnou aplikaci by to mohlo znamenat verifikaci a dalsi pozadavky.

Pragmaticka prvni volba:

- Pro lokalni osobni prototyp pouzit OAuth klienta typu Desktop app.
- Scope drzet na `https://www.googleapis.com/auth/gmail.readonly`, pokud Samantha opravdu potrebuje telo zprav.
- Pokud staci jen hlavicky a metadata, zvazit `https://www.googleapis.com/auth/gmail.metadata`, protoze necte telo e-mailu.

### Outlook / Microsoft 365

Pro Microsoft Graph je vhodny delegovany uzivatelsky scope `Mail.Read`, ktery cte mailbox prihlaseneho uzivatele. Nezacinat application permissions, protoze ty typicky znamenaji pristup bez prihlaseneho uzivatele a mohou mit organizacni rozsah.

Pragmaticka prvni volba:

- Pouzit delegated OAuth flow.
- Scope: `Mail.Read`.
- Doplnek `offline_access` pouzit jen tehdy, pokud chceme obnovovat token bez opakovaneho prihlasovani.

## Navrh architektury v projektu

Minimalni struktura pro prvni verzi:

```text
app/email/
  __init__.py
  models.py          # normalizovany EmailSummary / EmailMessage
  provider_base.py   # spolecne rozhrani
  gmail_provider.py  # pozdeji Gmail API
  graph_provider.py  # pozdeji Microsoft Graph
scripts/
  email_oauth_login.py       # jednorazove prihlaseni a ulozeni tokenu mimo git
  email_list_recent.py       # test vypisu poslednich zprav bez ukladani obsahu
data/email/
  .gitkeep                   # lokalni cache jen pokud bude potreba
```

Prvni skript nema nic posilat do OpenAI ani zapisovat do pameti. Ma jen overit, ze OAuth funguje a ze lze vypsat napr. poslednich 10 predmetu, odesilatelu a casu.

## Hranice pro prvni implementaci

Prvni verze smi:

- vypsat posledni e-maily,
- hledat podle dotazu,
- nacist jeden konkretni e-mail po potvrzeni uzivatelem,
- vytvorit shrnuti v chatu.

Prvni verze nesmi:

- odesilat e-maily,
- mazat e-maily,
- oznacovat e-maily jako prectene,
- automaticky archivovat nebo stitkovat,
- automaticky zapisovat obsah nebo citlive detaily do pameti.

## Provozni pripominka: tydenni kontrola a zaloha

Mila chce, aby Samantha pri startu pripomnela e-mailovou udrzbu, pokud se dele
nez 7 dni neprovedla kontrola nebo zaloha dulezitych e-mailu.

Pravidlo:

- Pokud nebyla poslednich 7 dni spustena e-mailova triage, pripomenout:
  `Nebyly projity e-maily za poslednich 7 dni. Chces spustit Email Triage?`
- Pokud nebyla poslednich 7 dni provedena zaloha/archivace dulezitych e-mailu,
  pripomenout:
  `Dulezite e-maily nebyly poslednich 7 dni archivovany. Chces vybrat zpravy k zaloze?`
- Pripominka sama nesmi cist e-maily, stahovat prilohy, otevirat odkazy ani nic
  ukladat. Ma pouze upozornit a nabidnout dalsi krok.
- Technicky smer: pozdeji vest lokalni stav napr. v
  `data/email/activity_state.json` s poli `last_triage_at` a
  `last_archive_at`. Tento soubor patri do lokalnich dat, ne do memory.
- Do memory se nema zapisovat konkretni obsah e-mailu, UID, plne URL ani citlive
  udaje. Memory ma obsahovat jen toto obecne provozni pravidlo.

## iCloud Mail aktualni smer

Mila upresnil, ze hlavni ucet pro prvni prototyp je iCloud Mail pouzivany na iPhonu
a Macu. iPhone a Mac se maji chapat jako klienti; Samantha se nema napojovat na
lokalni aplikaci Mail jako primarni zdroj, ale na iCloud Mail server.

Pro iCloud Mail byl pripraven prvni read-only test:

- `scripts/icloud_list_recent.py`
- IMAP server: `imap.mail.me.com`
- port: `993`
- prihlaseni pres iCloud adresu a Apple app-specific password
- konfigurace v lokalnim `.env`
- vypis pouze poslednich hlavicek: datum, odesilatel, predmet
- bez cteni tela e-mailu
- bez zmeny stavu zprav diky `BODY.PEEK`

Konkretni iCloud adresa ani app-specific heslo se nesmi zapisovat do pameti. Adresa
smela byt pouzita pouze v lokalnim `.env`, ktery je ignorovany gitem.

Navazujici handoff k pokusu o nastaveni je v:

- `memory/handoffs/email_icloud_setup_conversation_2026_05_18.txt`

## Prakticky dalsi krok

Prvni poskytovatel je iCloud Mail. Nejblizsi krok je zprovoznit app-specific password
v lokalnim `.env` a spustit:

```bash
python3 /Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent/scripts/icloud_list_recent.py --limit 10
```

Az test projde, pridat normalizovane rozhrani do `app/email/` a teprve potom nastroj
pro Samanthu.

## Overene zdroje k 2026-05-18

- Google Gmail API scopes: `https://developers.google.cn/workspace/gmail/api/auth/scopes?hl=en`
- Microsoft Graph permissions reference: `https://learn.microsoft.com/en-us/graph/permissions-reference`
- Apple app-specific passwords: `https://support.apple.com/en-mide/102654`
- Apple iCloud Mail server settings: `https://support.apple.com/en-la/HT202304`

## Aktualni kanonicky stav 2026-05-23

Projekt je rozpracovany, ale zakladni read-only vrstvy uz existuji. Tento stav
prekryva starsi iCloud handoffy z 2026-05-18 a vetsinu implementacnich mezistavu
z 2026-05-19.

Hotove schopnosti:

- iCloud read-only workflow:
  - vypsat hlavicky,
  - hledat v hlavickach,
  - precist jedno konkretni telo podle UID az po potvrzeni,
  - fulltextove hledat v textu za rok bez vypisu tel,
  - vytvaret redigovane shrnuti a safe case.
- Email triage / case / archive vrstvy:
  - `run_email_triage_session`,
  - `save_selected_email_cases_from_uids`,
  - lokalni `EmailCaseVault`,
  - lokalni `EmailArchiveVault`,
  - samostatne potvrzene zobrazeni odkazu z archivu.
- Reminders napojeni:
  - z potvrzeneho e-mailoveho action case lze navrhovat a ukladat pripominky
    podle obecných pravidel reminders workflow.
- Seznam Mail:
  - `SeznamReadOnlyEmailProvider` existuje pro INBOX hlavicky a potvrzene cteni
    jednoho tela podle UID,
  - `list_recent_seznam_email_headers`,
  - `search_seznam_email_headers`,
  - `read_seznam_email_body_by_uid`,
  - `list_unified_email_headers` rozlisuje zdroj schranky.
- Lokalni Seznam `.env` je vyplneny mimo git a memory.
- Read-only Seznam smoke test hlavicek 2026-05-23 prosel:
  - provider se prihlasil,
  - nacetl 2 hlavicky,
  - do vystupu ani memory nebyly vypsany predmety, odesilatele, telo ani URL.
- Drivejsi Seznam pojistny worklist/prilohy existuji lokalne v
  `data/private/email_seznam/`:
  - 34 UID slozek priloh,
  - 129 lokalnich souboru priloh,
  - katalog podle metadat/nazvu priloh.

Aktualni dalsi krok:

- Sjednotit potvrzovaci formulace pro cteni tela podle zdroje schranky, napr.
  aby bylo vzdy jasne, zda jde o iCloud UID nebo Seznam UID.
- Seznam pojistne prilohy a dokumenty resit jen pres potvrzovane read-only nebo
  document-vault workflow.
- Neudelat automaticky fulltext, cteni tel, stahovani priloh, archivaci ani
  vypis plnych URL bez samostatneho potvrzeni.

Bezpecnostni hranice:

- Neukladat do memory ani gitu e-mailove adresy, hesla, app-specific passwords,
  tokeny, cela tela e-mailu, plne URL, prilohy ani privatni obsah.
- Lokalni citliva data zustavaji v `data/email/`, `data/private/email_seznam/`
  a `.env`; tyto soubory se necommituji.
- Vystupy do memory smi obsahovat jen architekturu, workflow, pocty a redigovany
  stav prace.

## Historicke handoffy

Tyto handoffy ponechat jako auditni historii, ale nepouzivat je jako aktivni
startovni stav projektu. Aktualni navazani je tento projektovy soubor a
`handoffs/email_seznam_readonly_provider_2026_05_22.md`.

Zaklad iCloud read-only:

- `handoffs/email_mail_permissions_2026_05_17.txt`
- `handoffs/email_icloud_setup_conversation_2026_05_18.txt`
- `handoffs/email_icloud_readonly_test_ok_2026_05_18.md`
- `handoffs/email_icloud_app_email_layer_2026_05_18.md`
- `handoffs/email_samantha_tool_headers_2026_05_18.md`
- `handoffs/email_samantha_e2e_headers_ok_2026_05_18.md`
- `handoffs/email_read_uid_test_ok_2026_05_18.md`
- `handoffs/email_samantha_read_body_tool_ok_2026_05_18.md`
- `handoffs/email_safe_workflow_confirmed_2026_05_18.md`
- `handoffs/email_readonly_workflow_handoff_2026_05_18.md`
- `handoffs/email_search_headers_ready_2026_05_18.md`

Case, odkazy, reminders a RIXO:

- `handoffs/email_case_workflow_ready_2026_05_19.md`
- `handoffs/email_samantha_headers_redacted_waiting_uid_2026_05_19.md`
- `handoffs/email_url_tool_e2e_ok_2026_05_19.md`
- `handoffs/email_rixo_insurance_phase1_ready_2026_05_19.md`
- `handoffs/email_rixo_insurance_phase1_implemented_2026_05_19.md`
- `handoffs/email_action_case_phase2_proposed_2026_05_19.md`
- `handoffs/email_action_case_phase2_core_done_2026_05_19.md`
- `handoffs/email_reminders_phase3b_done_2026_05_19.md`

Triage, case vault a archive vault:

- `handoffs/email_work_session_proposed_2026_05_19.md`
- `handoffs/email_triage_work_mode_proposed_2026_05_19.md`
- `handoffs/email_triage_work_mode_core_done_2026_05_19.md`
- `handoffs/email_triage_session_tool_done_2026_05_19.md`
- `handoffs/email_case_vault_save_tool_done_2026_05_19.md`
- `handoffs/email_activity_state_done_2026_05_19.md`
- `handoffs/email_archive_vault_proposed_2026_05_19.md`
- `handoffs/email_archive_vault_core_done_2026_05_19.md`
- `handoffs/email_archive_vault_tool_done_2026_05_19.md`
- `handoffs/email_archive_vault_no_urls_after_archive_2026_05_19.md`
- `handoffs/email_project_frozen_human_handoff_2026_05_19.md`

Pozdejsi rozsireni:

- `handoffs/email_fulltext_search_tool_2026_05_21.md`
- `handoffs/email_seznam_pojisteni_prilohy_2026_05_21.md`
- `handoffs/email_seznam_readonly_provider_2026_05_22.md`
