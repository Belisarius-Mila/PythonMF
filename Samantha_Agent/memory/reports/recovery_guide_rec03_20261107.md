# REC-03 — důkazy a kvalita obnovovacího návodu

2026-11-07, Data worktree, proud `project-samantha-infrastructure`.
Míla schválil třetí etapu. Připravené automatické kontroly a syntetická
přejímka; žádný placený model, skutečný nový návrh TXT ani publikace.
Otevřené podmínky živého REC-02 pilotu zůstávají beze změny.

## Výsledek

`app/recovery_guide_quality.py` rozlišuje dvě vrstvy:

1. `validate`: povinná kontrola modelové syntézy před uložením kandidáta.
   Je přímo zapojená přes `validate_candidate` do existujícího pilotního
   řadiče. Neplatná syntéza skončí attention, bez kandidáta a bez dalšího
   modelového pokusu při opakovaném spuštění stejného slotu. Účtenka obsahuje
   pouze bezpečný kód `quality_issue`, nikdy odmítnutý obsah.
2. `review`: samostatná přejímka s explicitním schváleným seznamem aplikací,
   důkazy z důvěryhodného řadiče a checklistem nastavení. Výstup je vždy
   `blocked` nebo `review`, **nikdy povolení publikace**. Neúplný či
   neschválený produkční seznam aplikací nelze nahradit sedmi příklady z testů.

Řadič ani model nesmějí zaměnit tyto dvě vrstvy. Přijetí syntaxe/obsahu
modelové odpovědi není dokončená přejímka aplikací a není oprávnění writeru.
Plná přejímka, schválení konkrétního TXT a propojení její účtenky s writerem
patří do integračního kroku REC-04. Produkční modelový kontrakt zatím
samostatný aplikační checklist neprodukuje; ten nyní ověřuje knihovní API
a syntetické testy. Automatické zajištění důvěryhodných auditních dokladů
a skutečně úplného seznamu aplikací stále vyžaduje REC-01/REC-02 podklady.

## Povinná kontrola syntézy

- SHA-256 skutečného textu všech podkladů a nepřítomnost duplicitních zdrojů.
- Platný tvar odstavců a citací; `unchanged` opravdu pochází z původního TXT.
- Zachování pořadí a jedinečnosti původních kapitol, alespoň 75 % rozsahu
  každé jednotlivé kapitoly, úvodních instrukcí i celého textu. Je to hrubá
  pojistka proti vynechání, nikoli důkaz zachování každého významového kroku.
  Větší oprávněné zkrácení se musí ručně přezkoumat místo obejití brány.
- Cesty, URL a ID modelů musejí být přesně v citované části podkladu.
  Výskyt jinde v dlouhém dokumentu ani podobný prefix cesty nestačí.
- Rozpoznané nové shellové příkazy vyžadují přesnou citaci i důvěryhodně
  předaný schválený workflow katalog. Kontrola příkaz nikdy nespouští.
  Bez kontextu katalogu zůstane nový příkaz zablokovaný; stejná kontrola
  platí i pro příkazy v aplikačním checklistu.
- Historický/plánovaný důkaz se nesmí prohlásit za současnou konfiguraci.
  Neověřený odstavec dostane přímo v TXT viditelný štítek `[Neověřeno]`.
- Nové tvrzení o aktuálním ověření/deploy či telefonu vyžaduje čerstvý
  doložený audit/ruční doklad, včetně otisku přesné citace; samotné slovo
  `documented`, současné datum ani starý log nestačí.
- Známé identifikátory zrušeného placeného hlasového runtime se odmítají
  i při převzetí beze změny z původního návodu. Ostatní audio se neodstraňuje.
- Kontrola UTF-8, skrytých řídicích/bidi znaků, známých klíčů a podezřelých
  přiřazení hesel/tokenů v textu i citacích. Do chyb jde jen kód, ne obsah.
- Pouhá změna data je odmítnutá. Beze změny se vrací přesně původní bajty,
  bez umělého přidání koncového newline nebo posunu obsahového data.

Skutečný stávající TXT 1.2 byl místně pouze přečten. Touto základní kontrolou
prošel a zůstal bajtově shodný: 62 778 B. Nejde o přijetí jeho aktuálnosti,
test příkazů, obnovu počítače ani nový návrh vytvořený Solem.

## Přijímací checklist aplikací a nastavení

`ReviewContext` pochází z důvěryhodného operátora/řadiče, ne z odpovědi
modelu. Je svázaný s celým snapshotem. Výchozí seznam aplikací je prázdný
a neschválený. Skutečný rozsah musí zahrnout i další zapojené aplikace,
prohlížeče a iPhone nástroje podle uzavřené inventury; nenahrazuje se odhadem.

Pro každou aplikaci jsou povinné položky:

| Oblast | Pole |
| --- | --- |
| Smysl a potřeba | purpose, requirement |
| Instalace a verze | installation, version |
| Obnova konfigurace a dat | configuration, data |
| Přihlášení a oprávnění | sign_in, permissions |
| Spouštění a kontrola | start, verification |
| Vazba telefonu | mac_connection, iphone_installation, iphone_permissions, iphone_verification |

Každé pole rozlišuje dokumentované, ručně ověřené, neověřené nebo doloženě
nepoužitelné. `unverified` smí obsahovat pouze `neověřeno`, ne skryté tvrzení
o nějakém nastavení. Dokumentovaná hodnota musí být přímo v citaci a ve
stejné větě jako jméno příslušné aplikace; široká citace dvou aplikací
nesmí přesunout hodnotu z jedné do druhé.

`SourceFact` svazuje zdroj a jeho otisk s autoritou a datem. Ruční/live důkaz
navíc váže otisk přesné citace. Datum je platné ISO, nesmí být budoucí a musí
splnit schválenou čerstvost (výchozí 90 dní). Model si tyto doklady nemůže
sám schválit. Nová/neověřená verze macOS nebo přetrvávající kritický rozpor
přejímku blokují. Pro testy se používá výslovně fiktivní TestOS 1/2.

Účtenka obsahuje verzi validátoru, otisky kandidáta, kontextu i checklistu a zdrojové kotvy:
SHA-256 souboru/citace, rozsah řádků, autoritu a počet výskytů citace.
Více výskytů citace se nezamlčuje; významovou jednoznačnost posoudí člověk.

## Nezávislé čtení bez soukromé historie

`cold_reader_bundle` vydá pouze kontrolovaný návod, jeho aplikační checklist,
účtenku a instrukci číst bez provádění příkazů. Checklist se při sestavení
kopíruje, jeho pozdější mutace nezmění již zkontrolovaný balíček.

Syntetický příklad je v `recovery_guide_rec03_example_20261107.json`.
Všechny skutečné aplikace/nastavení v něm jsou neověřené; produkční rozsah
není schválený. Test nový balíček předal novému procesu `python -I` přes
stdin, s prázdným pracovním adresářem a bez projektové historie/prostředí.
Proces rozpoznal návod, sedm syntetických aplikací a 98 neověřených polí.

To dokládá samostatnost datového přenosu, **nikoli lidské porozumění**.
Zkouška novým člověkem nebo novým modelovým čtenářem skutečného přijatého
návrhu ještě neproběhla. Nevznikl žádný další placený agent ani modelový tah.

## Přejímací scénáře

| Scénář | Požadovaný výsledek |
| --- | --- |
| Přidaná aplikace bez kompletního Mac/iPhone checklistu | blokace |
| Změna cesty nebo role mimo přesnou citaci | blokace |
| Nové oprávnění/ověření telefonu pouze podle dokumentace | blokace ručního ověření |
| Starý/plánovaný log vydaný za současné nastavení | blokace |
| Zrušený hlas zachovaný jako údajně unchanged | blokace |
| Zachované nadpisy, ale vynechané kroky kapitoly/úvodu | blokace |
| Chybějící podklad nebo nesouhlasící SHA | blokace |
| Nesprávný/neznámý příkaz | blokace, žádné spuštění |
| Vložené instrukce v podkladu | pouze data; bez nástrojů, historické syntetické izolace zachované |
| Příliš velký soubor nebo změna během běhu | dosavadní REC-01/02 brány, žádné tiché zkrácení/retry |
| Datum bez věcné změny | blokace změny; plná revize patří do účtenky |
| Chybná syntéza a opětovný stejný slot | attention, žádný kandidát ani nový tah |

## Ověření a hranice

38 nových REC-03 testů; závěrečná cílená sada 114/114 OK. Plná projektová brána: 2 459 testů OK, 5 skipped. Po závěrečných zpřesněních znovu cílená sada a statická brána OK; nezměněné testy se zbytečně neopakovaly.

Regexy a poměr délky nejsou úplný sémantický analyzátor ani univerzální
detektor tajemství. Kontext důkazů je důvěryhodná hranice: kdyby jej někdo
naplnil nepravdivým auditem, kontrola sama fyzický telefon neprověří.
Znalost témat v textu také nedokazuje, že kroky fungují na náhradním Macu.
Proto i zcela vyplněný strojový výsledek zůstává `review` a publication false.
To odpovídá také [omezení Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs):
platný tvar JSON nezaručuje věcně správnou odpověď.

## Další krok a předání

REC-04: připnout úplnou schválenou inventuru a důvěryhodné doklady,
svázat tuto přejímací účtenku/konkrétní přijetí Mílou s přesným kandidátem,
oběma pevnými cíli a writerem. Dále testovat přerušení a současné změny.
Skutečné ukládání, živý REC-02 modelový pilot, push/deploy a aktivace služby
mají nadále samostatné podmínky. Will zachová novější main/role při převzetí;
Data nyní mění pouze vlastní worktree a lokální commit.


### Soubory této etapy

Nové: `app/recovery_guide_quality.py`, `tests/test_recovery_guide_quality.py`,
tento report a syntetický příklad `recovery_guide_rec03_example_20261107.json`.
Upravené: `app/recovery_guide_maintainer.py`, `tests/test_recovery_guide.py`
(konzistentní hash syntetického injektovaného zdroje),
`scripts/cockpit_quality_gate.py`, `memory/ACTIVE_PROJECTS.md`,
`memory/MEMORY_INDEX.md`, `memory/LESSONS_LEARNED.md`,
`memory/projects/samantha_external_backup.md`,
`memory/technical/recovery_guide_maintainer.md` a kanonický handoff/TVBCP
`project-samantha-infrastructure.md`. Celkem 14 souborů.
