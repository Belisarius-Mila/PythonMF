# Handoff: iCloud Mail Samantha Email Case E2E OK a URL tool připraven

Nazev: iCloud Mail read-only - Samantha Email Case end-to-end prošel a URL tool připraven
Priorita: 1
Stav: ceka na dalsi rozhodnuti
Pripomenout pri startu: ano
Datum: 2026-05-19

## Co se resilo

Navázalo se na iCloud Mail read-only Email Case workflow. Cílem bylo posunout
chybějící end-to-end test přes Samanthu v přirozeném dialogu a ověřit bezpečnostní
bránu před čtením těla e-mailu.

## Co je hotove

- Lokální testy email case vrstvy prošly.
- Samantha úspěšně vypsala poslední e-mailové hlavičky read-only.
- Byl ověřen bezpečnostní scénář bez potvrzení: při požadavku na pracovní případ
  podle UID bez výslovného souhlasu Samantha odmítla číst tělo a vyžádala si
  potvrzení.
- Byla upravena hlavičková vrstva, aby ve výstupu redigovala e-mailovou adresu
  odesílatele.
- Byl přidán test, který kontroluje, že formátování hlaviček nepropustí plnou
  e-mailovou adresu.
- Po úpravě testy znovu prošly.
- Opakovaný průchod přes Samanthu potvrdil, že hlavičky se dál vypisují, ale
  adresa odesílatele je redigovaná.
- Po Milově aktuálním výslovném potvrzení s konkrétním UID prošel end-to-end test
  `build_email_case_from_uid` přes Samanthu.
- Výsledek byl bezpečný: e-mail byl rozpoznán jako newsletter, s nízkou prioritou,
  bez deadlinu a bez akčních kroků; odkazy byly ponechány jen jako metadata a nic
  se neotevíralo.
- Byl přidán samostatný tool `show_email_case_links` pro vypsání plných URL jen
  po aktuálním výslovném potvrzení s konkrétním UID a zmínkou o URL/odkazech.
- Tool je registrovaný v Samanthě a lokální testy prošly.
- Přes Samanthu byl ověřen odmítací průchod: bez přesného potvrzení si Samantha
  vyžádá potvrzovací větu a e-mail nečte.

## Co neni hotove

- Po samostatném Milově potvrzení s konkrétním UID a výslovnou žádostí o plné
  URL/odkazy prošel i reálný test `show_email_case_links` přes Samanthu.
- Tool vypsal plné URL a potvrdil bezpečnostní hranice: odkazy nebyly otevřeny,
  nic se nestahovalo a nic se neuložilo do memory.
- Perzistence redigovaného case shrnutí do memory po samostatném výslovném
  souhlasu zatím není hotová.

## Dalsi krok

Další praktický krok je rozhodnout, jestli se má přidat pohodlnější prezentace
odkazů, například seskupení podle domény, pojmenování podle okolního textu nebo
kopírovatelný blok. Plné URL stále neukládat do memory.

## Zmenene nebo relevantni soubory

- `app/email/tools.py`
- `tests/test_email_case_service.py`
- `app/samantha_agent.py`
- `app/email/case_tools.py`
- `app/email/link_tools.py`
- `app/email/safety.py`

## Bezpecnost / neukladat

Do memory ani gitu neukládat:

- konkrétní reálná UID,
- plné hlavičky reálných zpráv,
- plné e-mailové adresy,
- celé předměty reálných zpráv,
- obsah e-mailů,
- plné URL,
- přílohy,
- tokeny,
- app-specific password,
- iCloud adresu,
- hesla.

Workflow stále nesmí odesílat, mazat, přesouvat, označovat jako přečtené,
otevírat odkazy, stahovat přílohy ani ukládat obsah e-mailů do memory bez
výslovného souhlasu.
