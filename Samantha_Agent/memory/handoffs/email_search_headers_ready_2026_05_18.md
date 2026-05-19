# Handoff: E-mail header search ready

Nazev: Read-only vyhledavani e-mailovych hlavicek
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Byl doplnen dalsi read-only krok pro iCloud Mail: vyhledavani v e-mailovych
hlavickach bez cteni tel zprav.

## Co je hotove

Read-only vyhledavani e-mailovych hlavicek bylo navrzeno a rucni test pres
`scripts/email_search_headers.py` prosel.

Pribyl skript:

- `scripts/email_search_headers.py`

Doplneny Samantha tool:

- `search_email_headers`

Provider ma metodu:

- `ICloudReadOnlyEmailProvider.search_headers(query, limit, scan_limit)`

Vlastnosti:

- bez dotazu vraci posledni hlavicky podle `--limit`,
- s dotazem pouziva server-side IMAP search nad poli `From` a `Subject`,
- vysledky radi podle UID sestupne, aby vracely nejnovejsi nalezene hlavicky,
- lokalni scan-limit zustava jen jako fallback, kdyz server-side hledani nic nevrati,
- hleda pouze v hlavickach, ne v tele zpravy,
- vraci pouze UID, datum, odesilatele a predmet,
- necte tela e-mailu,
- nic neposila, nemaze, nepresouva ani neoznacuje jako prectene,
- prilohy a odkazy se zatim neresi,
- nic neuklada do memory.

## Overeni

Probehl py_compile pro upravene soubory.

Registrace nastroju v Samantha agentovi potvrdila:

```text
['search_memory', 'list_recent_email_headers', 'search_email_headers', 'read_email_body_by_uid']
```

Realny read-only test mimo Codex sandbox pres:

```bash
.venv/bin/python scripts/email_search_headers.py --limit 10
```

probehl OK. Konkretni vysledky se do memory neukladaji.

Pozdeji byl overen i dotaz:

```bash
.venv/bin/python scripts/email_search_headers.py --query Apple --limit 20 --scan-limit 500
```

Puvodni lokalni scan 500 hlavicek byl prilis pomaly. Implementace byla upravena na
server-side IMAP search nad `From` a `Subject` a nasledne bylo opraveno numericke
razeni UID. Rychly test s `--query Apple --limit 5` probehl OK.

## Co neni hotove

Zatim neni hotove:

- end-to-end test hledani pres Samanthu,
- presnejsi filtrovani podle pole `From` nebo `Subject`,
- hledani podle data nebo flags,
- ulozeni redigovaneho shrnuti do memory po vyslovnem souhlasu.

## Dalsi krok

Pripojit `search_email_headers` jako Samantha tool, pokud uz neni pripojeny, a
otestovat pres Samanthu dotazy typu:

- najdi neprectene e-maily,
- najdi dulezite e-maily,
- najdi e-maily od konkretniho odesilatele,
- najdi e-maily s klicovym slovem v predmetu nebo odesilateli.

Samantha ma pouzit `search_email_headers` a vratit pouze UID, datum, odesilatele,
predmet a flags. Telo e-mailu se smi cist az po vyberu UID a vyslovnem potvrzeni
Mily.

## Bezpecnost / neukladat

Do memory ani gitu neukladat:

- UID konkretni realne zpravy,
- app-specific password,
- iCloud adresu v plnem zneni,
- obsah e-mailu,
- konkretni hlavicky z realne schranky,
- cele e-maily,
- tokeny,
- hesla,
- citlive osobni udaje.
