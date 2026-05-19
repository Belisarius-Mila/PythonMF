# Handoff: Email Case workflow ready

Nazev: iCloud Mail read-only Email Case workflow
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-19

## Co se resilo

Navazovalo se na iCloud Mail read-only workflow. Po overenem hledani hlavicek
a potvrzenem cteni konkretniho UID byla pridana bezpecna vrstva pracovnich
e-mailovych pripadu.

Cil vrstvy:

- po vyhledani hlavicek a vyslovnem potvrzeni konkretniho UID nacist telo
  read-only,
- vytvorit redigovany pracovni pripad,
- urcit typ e-mailu, prioritu a deadline,
- vytahnout akcni kroky,
- vytahnout odkazy jen jako metadata,
- vytahnout prilohy jen jako metadata,
- pripravit navrh odpovedi bez odeslani,
- nic automaticky neukladat do memory.

## Co je hotove

Pribyly soubory:

- `app/email/case_models.py`
- `app/email/case_service.py`
- `app/email/case_tools.py`
- `app/email/safety.py`
- `scripts/email_case_from_uid.py`
- `tests/test_email_case_service.py`

Upravene soubory:

- `app/email/models.py`
- `app/email/icloud_provider.py`
- `app/email/tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`

Pribyl Samantha tool:

- `build_email_case_from_uid`

Registrovane Samantha tools jsou:

```text
['search_memory', 'list_recent_email_headers', 'search_email_headers', 'read_email_body_by_uid', 'build_email_case_from_uid']
```

Email Case model umi:

- `email_type` (`newsletter`, `transactional`, `message`),
- `priority`,
- `deadline`,
- `action_items`,
- `links` jako metadata,
- `attachments` jako metadata,
- `reply_draft`,
- `summary_redacted`.

Bezpecnostni potvrzeni je sdilene v:

- `app/email/safety.py`

Tool i case workflow vyzaduji, aby aktualni Milova zprava obsahovala konkretni
UID i jasny souhlas. Bez toho se provider nesmi zavolat.

## Overeni

Probehl lokalni test bez IMAPu nad umelymi e-maily:

```text
Ran 9 tests in 0.002s
OK
```

Probehl i realny read-only CLI test pracovního pripadu na potvrzenem marketingovem
newsletteru. Vysledek:

- e-mail byl klasifikovan jako `newsletter`,
- priorita `low`,
- deadline nenalezen,
- akcni kroky nenalezeny,
- prilohy nenalezeny,
- odkazy byly zobrazeny jen souhrnne podle domeny,
- odpoved se u newsletteru nenavrhuje.

Do memory se neulozilo konkretni UID, plny odesilatel, predmet, telo, odkazy ani
obsah e-mailu.

## Dulezite opravy z realneho testu

Realny HTML newsletter odhalil, ze parser puvodne do shrnuti propoustel CSS
a neviditelne vyplnove znaky. Bylo opraveno:

- ignorovani `head`, `style`, `script`, `noscript`,
- cisteni neviditelnych filler znaku,
- vytazeni `href` odkazu jako metadata bez otevreni,
- filtrovani falesnych deadline hodnot typu CSS decimal,
- zkraceni link sekce na souhrn domen a poctu odkazu.

## Co neni hotove

Zatim neni hotove:

- end-to-end test `build_email_case_from_uid` primo pres Samanthu v prirozenem
  dialogu,
- samostatny tool pro zobrazeni plnych URL jen na vyslovne vyzadani,
- lepsi ceske shrnovani newsletteru bez modeloveho LLM kroku,
- perzistence redigovaneho case shrnuti do memory po vyslovnem potvrzeni,
- workflow pro prilohy: zatim jen metadata, zadne stahovani.

## Dalsi krok

Nejblizsi prakticky krok:

1. Otestovat `build_email_case_from_uid` pres Samanthu v prirozenem dialogu.
2. Zachovat pravidlo: konkretni UID a jasne potvrzeni musi byt v aktualni Milove
   zprave.
3. Pokud vystup bude dobry, pridat dalsi bezpecny tool:
   `show_email_case_links(uid, confirmation_text, user_confirmed)` nebo podobny,
   ktery zobrazi plne URL pouze na vyslovne vyzadani a bez jejich otevreni.
4. Teprve potom resit ulozeni redigovaneho shrnuti do memory po samostatnem
   vyslovnem souhlasu.

## Zmenene nebo relevantni soubory

- `app/email/case_models.py`
- `app/email/case_service.py`
- `app/email/case_tools.py`
- `app/email/safety.py`
- `app/email/models.py`
- `app/email/icloud_provider.py`
- `app/email/tools.py`
- `app/email/__init__.py`
- `app/samantha_agent.py`
- `scripts/email_case_from_uid.py`
- `tests/test_email_case_service.py`
- `memory/handoffs/email_case_workflow_ready_2026_05_19.md`

## Bezpecnost / neukladat

Do memory ani gitu neukladat:

- UID konkretni realne zpravy,
- plne hlavicky realnych zprav,
- plny predmet nebo odesilatele realne zpravy, pokud to neni vyslovne schvalene,
- obsah e-mailu,
- plne URL z e-mailu,
- prilohy,
- tokeny,
- app-specific password,
- iCloud adresu,
- hesla,
- citlive osobni udaje.

Workflow stale nesmi:

- odesilat e-maily,
- mazat e-maily,
- presouvat e-maily,
- oznacovat e-maily jako prectene,
- otevirat odkazy,
- stahovat prilohy bez potvrzeni,
- ukladat obsah e-mailu do memory bez vyslovneho souhlasu.

