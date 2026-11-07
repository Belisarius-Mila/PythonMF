# REC-04 — přijetí kandidáta a bezpečný převod dvou kopií

2026-11-07, Data worktree, proud `project-samantha-infrastructure`.
Míla schválil čtvrtou vývojovou etapu. Zápis byl zkoušen pouze na dočasných
syntetických souborech. Skutečné provozní TXT, iCloud a služby se neměnily.

## Výsledek a hranice

`PublicationStore` v `app/recovery_guide_publication.py` spojuje přejímku
REC-03, konkrétní text, checklist, zdrojové doklady a dvě pevné cílové cesty.
Přijetí pouhého SHA textu již není veřejné writer API. Starý nízkoúrovňový
byte writer se jmenuje `_publish_candidate` a používá jej interní převod.

Nový veřejný vstup má v této verzi **pouze sandbox režim**. Stav i oba cíle
musejí být v explicitním izolovaném podadresáři vlastní `.venv` nebo
systémového dočasného adresáře; samotný obecný temp kořen ani celý domovský
adresář není povolený. Režim production je výslovně odmítnutý. Výchozí
provozní cesty ani automatická instalace nejsou součástí tohoto API.

To je vývojový a přejímací základ REC-04, nikoli provedená migrace do
PythonMF/iCloud Dokumentů. Produkční autorizovaný vstup s přesnými cestami
a skutečnými doklady musí projít samostatnou aktivací REC-06. Soukromá
Python funkce sama není bezpečnostní bariéra proti vlastnímu správci stroje;
smyslem je, že žádný registrovaný modelový/provozní vstup neobchází přijetí.

## Kontrakt přijetí

1. Důvěryhodný řadič/operátor vytvoří `PublicationStore` s pevným sandboxem,
   stavem a přesnými dvěma cíli. Model tyto hodnoty ani schválení neurčuje.
2. `prepare` znovu provede plnou kvalitativní přejímku. Zmrazí odpověď,
   původní návod, celý snapshot, checklist, kontext, verzi validátoru a
   identitu cílů do neměnného JSON paketu. Vstupní slovníky již nemůže
   následná změna volajícího nepozorovaně přepsat.
3. `preview` ukáže přesný binding, otisk kandidáta a důkazů i oba cíle;
   `candidate_text` poskytne konkrétní TXT ke čtení. Tyto operace nezapisují.
4. `accept` vyžaduje explicitní potvrzení přesného bindingu důvěryhodným
   operátorem. V této verzi je jeho autorita označená `sandbox_confirmation`;
   syntetické testy nepředstírají skutečnou Mílovu přejímku nového návodu.
5. Kandidát, původní návod, paket a kvalitativní účtenka se ukládají
   create-only do soukromého stavu. Neměnný schvalovací manifest vznikne
   až poslední. Přerušení před ním není přijetí. Stejné ID lze dokončit
   jen stejnými bajty; jiné vstupy pod stejným ID se odmítnou.

Potvrzení bez správného bindingu, kandidát s blokovanou kvalitou nebo změna
jediného uloženého artefaktu nemůže projít. Opakované přijetí již stejné
identity vrátí stejnou původní účtenku bez nové žádosti či nového souhlasu.

Datum přijetí používá Europe/Prague; první převod znovu ověří čerstvost
dokladů a důvěryhodný callback aktuálnosti vstupů. Callback v provozní
integraci musí porovnat skutečný aktuální snapshot, ne vracet konstantu.
V testech jde o výslovný syntetický důkaz. Model callback nevytváří.

## Provádění a návrat po přerušení

`execute` vyžaduje přesné ID a hash neměnného přijetí. Kandidát se načte
z již přijatého paketu, ne z nového modelového výsledku. Před uložením se
ověří všechny jeho artefakty, rodiče cílů, známé aliasy a aktuální obsah.
Předchozí obsah obou cílů i původní zdrojový TXT zůstávají zachované.
Archivace a návrat zachovávají i původní CRLF bajty.

Jeden zámek řadí všechny žádosti daného store. Trvalý aktivní marker
zabraňuje tomu, aby starší žádost později přepsala novější vydání. Další
kandidát čeká, pokud předchozí doručení ještě není uzavřené. Pád mezi
aktivním markerem a záznamem provádění neobnoví starého vlastníka.

Nízkoúrovňový žurnál je navázaný na **hash přijetí**, kandidáta a připnuté
cíle. Rozlišuje přípravu, místní uložení, dvě místní kopie, čekající upload,
potvrzený upload a attention. Stav navíc popisuje skutečně pozorované kopie:
candidate, baseline, changed nebo unavailable. Selhání rollbacku je viditelné.
Samostatné trvalé příznaky written rozlišují již dokončené kopie od dosud
rozpracovaných. Ruční návrat dokončené kopie ke zcela stejným původním
bajtům se tak nesplete s povoleným dokončením původního zápisu. Vlastní
rollback má před změnou bajtů trvalý záznam záměru.

Po zahájení žurnálovaného převodu lze dokončit stejné již přijaté bajty bez
nové analýzy a modelu, i když se mezitím vyvíjí další dokumentace. Jde o
dokončení konkrétní schválené verze, nikoli o tvrzení, že obsah sleduje novější
HEAD. Nový přijatý kandidát potřebuje nový snapshot/přijetí. Ruční změna
samotných cílových bajtů se nepřepíše; přenos skončí attention.

Po potvrzení obou lokálních kopií se metadata uploadu čtou samostatně.
Shodný místní hash sám nestačí. Výpadek metadata auditu vrátí pending_icloud,
ne falešný úspěch. Po auditu se znovu kontrolují oba hashe, aby se zachytila
ruční změna během čekání. Opakovaná kontrola uploadu nezapisuje znovu již
shodné kopie a nemá žádný modelový tah.

`status` vrací poslední uložené pozorování; není novým živým iCloud auditem.
Otevření souboru na iPhonu zůstává samostatnou fyzickou přejímkou.

## Ověřené scénáře

| Situace | Výsledek |
| --- | --- |
| Pouhý náhled nebo nepotvrzený binding | žádný zápis cíle ani stavového store |
| Kandidát bez přijetí, změna artefaktu/cesty/validátoru | odmítnutí |
| Změna zdrojů nebo zestárlý doklad před prvním převodem | žádný cílový zápis |
| Přerušení přijetí před manifestem | není schváleno; dokončit jen stejný paket |
| Pád po první nebo druhé výměně souboru | dokončení stejné verze bez opakování hotové výměny |
| Selhání druhého cíle | bezpečný návrat první staré verze, pokud zůstala naše |
| Ruční změna první kopie při selhání druhé | ruční obsah zachován |
| Neúspěšný rollback | attention s přesnými stavy kopií, pozdější bezpečné dokončení |
| Nová první kopie původně neexistovala | při selhání se nemaže; zůstane kandidát a attention |
| Chyba/timeout metadata auditu nebo nepotvrzený upload | pending_icloud, žádný model/rewrite |
| Nesynchronizovaná cílová složka | před prvním cílovým zápisem attention |
| Ruční změna během metadata auditu | attention, nikoli uploaded |
| Ruční návrat hotové kopie k původním bajtům | attention, bez opětovného přepsání |
| Starý požadavek po novějším vydání | superseded, žádné přepsání |
| Nový kandidát při starém čekajícím přenosu | waiting_previous_delivery |
| Změněný alias/poškozený archiv/slabá oprávnění stavu | odmítnutí |
| Souběžný proces | společný zámek, žádný dvojí writer |

Všechny cloudové odpovědi v těchto testech jsou syntetické. Označení
uploaded v testu znamená přijetí simulovaných metadat, **nikoli skutečný
upload provozního TXT**. Strojově čitelný příklad je v
`recovery_guide_rec04_example_20261107.json`; neobsahuje skutečné uživatelské
cesty ani soukromý obsah. Testovací adresáře se uklízí běžným unit-test
cleanupem; provozní retenční mazání writer neobsahuje.

## Ověření

38 nových REC-04 testů; cílená sada 152/152 OK. Závěrečná plná projektová brána nad poslední verzí writeru: 2 501 testů OK, 5 skipped. Dřívější mezibrána 2 498 OK; po zpřesnění written/manifest se plná brána opakovala.

Samostatná přejímací sada v této pracovní kopii:

```text
OPENAI_AGENTS_DISABLE_TRACING=1 .venv/bin/python -m unittest tests.test_recovery_guide_publication
```

## Praktické limity a další krok

Zámek koordinuje vlastní procesy. Hash před/po zápisu není univerzální
filesystem CAS proti libovolnému cizímu editoru v poslední mikrosekundě.
Ani dva atomické souborové zápisy a iCloud netvoří jednu atomickou transakci.
Proto se při skutečné migraci musí ukončit souběžné ruční úpravy TXT.
Poškozený store se automaticky neopravuje ani nemaže; výsledek zůstane
odmítnutý/attention pro operátora.
Paket přijetí má limit 32 MB; větší se odmítne celý, nikdy se tiše nekrátí.

REC-05: připojit registrované preview/run/status k trvalému plánovači,
zachovat čekající doručení před novou analýzou a připravit aktivaci.
Budoucí běžný týdenní provoz má používat jednorázově schválený úzký rozsah
autonomie a jeho limity; nemá vyžadovat nový ruční souhlas každý týden.
Současné konkrétní sandboxové potvrzení tuto provozní autoritu nenahrazuje.
Živý REC-02 pilot, úplný produkční korpus/aplikace, přijetí skutečného TXT,
pevné provozní cíle, skutečný iCloud/iPhone důkaz a oprávnění k nasazení
zůstávají otevřené předpoklady REC-06. Data nyní nic nepublikuje ani neaktivuje.


### Soubory této etapy

Nové: `app/recovery_guide_publication.py`, `tests/test_recovery_guide_publication.py`,
tento report a redigovaný syntetický příklad `recovery_guide_rec04_example_20261107.json`.
Upravené: `app/recovery_guide_publish.py`, `tests/test_recovery_guide.py`
(základní IO testy používají interní byte writer), `scripts/cockpit_quality_gate.py`,
`memory/ACTIVE_PROJECTS.md`, `memory/MEMORY_INDEX.md`, `memory/LESSONS_LEARNED.md`,
`memory/projects/samantha_external_backup.md`, `memory/technical/recovery_guide_maintainer.md`
a kanonický handoff/TVBCP `project-samantha-infrastructure.md`. Celkem 14 souborů.
