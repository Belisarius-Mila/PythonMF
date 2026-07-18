Nazev: Human–Adam – zachovaný WIP při rozvětvení workspace
Priorita: 1
Stav: čeká na retest
Pripomenout pri startu: ano
Datum: 2026-07-18

Co se resilo:

- Současný vývoj z terminálu a z iPhonu způsobil, že WIP checkpoint Human–Adam
  vznikl nad starším `main`, zatímco živý `main` se později posunul.
- Backend správně označil workspace jako `diverged`, ale UI z hodnoty
  `local_checkpoint_ahead=false` chybně odvodilo, že žádný WIP neexistuje.

Co je hotove:

- Původní TVBCP commit byl nalezen neporušený a bezeztrátově zachován v
  ochranných Git referencích izolovaného workspace.
- Bez rebase, resetu a mazání byl z aktuálního `main` vytvořen nový pracovní
  checkpoint `ebd47b9 Doplnění TVBCP - layout`; původní obsah zůstal zachovaný.
- Audit nového checkpointu prošel jako přesný jednocommitový fast-forward a Míla
  jej následně úspěšně nasadil.
- `main`, `origin/main` a Human–Adam workspace jsou po nasazení zarovnané na
  `ebd47b9`, čisté a bez Git remote v izolovaném workspace.
- Backend nyní odděluje dva stavy:
  - `local_checkpoint_ahead`: WIP je přímo auditovatelný a nasaditelný;
  - `local_checkpoint_preserved`: WIP existuje, ale po rozvětvení vyžaduje
    bezpečnou obnovu.
- Při rozvětvení se počet zachovaných commitů a změněné cesty počítají vůči
  poslednímu ověřenému základu workspace.
- Stavová hlavička a panel Práce zobrazí `WIP zachován · nutná obnova` místo
  zavádějícího tvrzení o čistém workspace nebo chybějícím WIP.
- Audit i automatický sync zůstávají ve stavu recovery fail-closed.
- Cílené testy včetně přesné simulace incidentu prošly.
- Plná Cockpit quality gate prošla: 766 testů, Python/JavaScript/shell syntaxe a
  `git diff --check` jsou v pořádku.

Co neni hotove:

- Nová UI/backend oprava zachovaného WIP ještě nebyla restartem načtena do
  běžícího Cockpitu ani vizuálně ověřena.
- Automatická obnova rozvětveného WIP z UI záměrně nevznikla; recovery zůstává
  servisní, protože může vyžadovat posouzení konfliktů.

Dalsi krok:

- Po checkpointu a pushi bezpečně restartovat Cockpit a ověřit normální stav
  `Workspace čistý` na Macu nebo iPhonu.
- Nové recovery upozornění ověřit při příštím přirozeném souběhu; nevytvářet
  záměrně rozvětvení v živém workspace jen kvůli vizuálnímu testu.

Navrhovane dalsi kroky:

- Pokud se souběh bude opakovat, zvážit samostatný potvrzovaný recovery workflow
  s preview společného základu a změněných cest. Automatický merge nepřidávat.

Zmenene nebo relevantni soubory:

- `human_adam_workspace.py`
- `human_adam_service.py`
- `human_adam_ui.py`
- `test_human_adam_workspace.py`
- `test_human_adam_service.py`
- `test_human_adam_ui.py`

Bezpecnost / neukladat:

- Neukládat obsah TVBCP mimo jeho kanonický soubor, celý chat, thread ID,
  soukromé cesty ani private data do diagnostiky nebo Git handoffu.
- Při rozvětvení neprovádět automatický rebase, reset, merge ani přepis WIP.
- Recovery vždy nejdřív ochrání původní commit samostatnou referencí.
