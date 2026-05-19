# Handoff: iCloud Mail read by UID test OK

Nazev: iCloud Mail read-only cteni konkretniho e-mailu podle UID
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-05-18

## Co se resilo

Po potvrzeni Mily probehl test read-only nacteni jednoho konkretniho e-mailu podle
UID pres iCloud IMAP.

## Co je hotove

Byl doplnen skript:

- `scripts/email_read_uid.py`

Skript pouziva:

- `imap.select("INBOX", readonly=True)`,
- `BODY.PEEK[]`,
- limit velikosti zpravy,
- limit vypisu pres `--max-chars`,
- ignorovani priloh,
- defaultni redigovani e-mailovych adres v tele zpravy.

Realny test mimo Codex sandbox probehl OK. E-mail byl nacten jako read-only a
zprava nebyla mazana, odesilana, presouvana ani oznacovana jako prectena.

## Co neni hotove

Zatim neni hotove:

- zapojeni cteni tela e-mailu jako Samantha tool,
- workflow vyzadujici potvrzeni pred ctenim tela konkretni zpravy,
- shrnuti konkretniho e-mailu v chatu,
- rucne schvalene ulozeni vybraneho shrnuti do memory.

## Dalsi krok

Navrhnout Samantha tool pro cteni konkretniho e-mailu podle UID tak, aby pred
ctenim tela vyzadoval jasne potvrzeni Mily a aby ve vystupu redigoval citlive
udaje, minimalne e-mailove adresy.

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
