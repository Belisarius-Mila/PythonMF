# Dohlížitel — oprava spánku14.11.2026


## 2026-11-14 07:52 CET — Noční spánek a potvrzení trvajícího problému

Míla výslovně schválil opravu a bezprostřední Terra p+n v proudu
project-samantha-infrastructure. Předání používá centrální release_executor
a jediné app.communication.luna_release.submit_release(wait=True), bez
nativního pomocníka. Terra je schválená preferovaná role; při auditu musí
být vybraná právě gpt-6.1-terra/high, žádný tichý fallback na Lunu.

Příčina: Lokální LaunchAgent běží i při krátkých systémových DarkWake.
Před ranním otevřením Macu14.11. přijal Pushcut8 oznámení (10 agentových
událostí), hlavně starý heartbeat pošty a autosave. Záznam OS04:32:11
DarkWake a události04:32:14 dokazují časovou vazbu. Noční kontrola pošty
byla až za kontrolou stáří heartbeatu, takže záměrné neprovádění scanu
vytvářelo nové incidenty. Autosave má600s cyklus, který musí po spánku
dostat čas na skutečné obnovení. Vnější hlídač není nakonfigurovaný.

Oprava:
- Pošta23–07 Europe/Prague nejprve vyhodnotí outside_hours; starý/chybějící
  heartbeat ani nečerstvý scan samy v noci nevyhlásí závadu.
- Čtecí pmset -g systemstate rozliší plné probuzení (Graphics) od DarkWake;
  kern.waketime doplní čas probuzení. Žádná změna uspávání, sítě či víka.
  Při spánku/údržbě nebo neověřené power sondě neprobíhají síťové sondy
  a neodesílá se problém ani obnova. Panel stav viditelně označí Pozastaveno.
- Trvalá pěti­minutová ochrana po probuzení, prvním běhu nebo delší mezeře.
  Restart workeru ani opakovaný polling tuto lhůtu nezkrátí/neprodlužuje.
  Autosave má navíc až15 minut na svůj desetiminutový cyklus; skutečný
  čerstvý úspěch jej může vrátit dříve po společné pěti­minutové ochraně.
- Nové varování až po souvislém problému alespoň90s (při120s periodě dvě
  skutečné kontroly). Stejný čas/dvojí klik nestačí. Krátký výpadek nemá
  varování ani falešnou obnovu. Working/noční klid/spánek čítač přeruší.
- Otevřené incidenty se během spánku neuzavírají a nevytváří se obnova.
  Zachované identifikátory a accepted/delivery_unknown; neprovádí se resend.
  Pending před spánkem potřebuje čerstvé potvrzení po obnovení provozu.
- Nové pozastavené řádky se na disk zapisují jako dříve známé unknown/
  unavailable plus whitelisted pause_code. Starší běžící Cockpit je stále
  přečte; nový reader zobrazí přesný důvod. Žádná falešná zelená.

Ověření:71 cílených testů PASS, Node panel včetně Pozastaveno a redakce PASS.
Regrese zahrnují starý/noční/chybějící/budoucí heartbeat, DarkWake bez sond,
noční opakování, restart během grace, krátký spánek mezi dvěma tiky,
mezery, neověřený power stav, trvalý i krátký výpadek, ochranu autosave,
pending send a skutečnou obnovu. Živá nová OS sonda pouze čtecí: awake,
čas normálního otevření víka souhlasí s pmset logem. Testy používají vlastní
dočasné archivy a syntetického sendera; žádné ostré testovací Pushcut POST.
Konečná plná brána: 3876 testů/31 skip v izolaci (668.4s): pouze1 chyba nezměněného recovery CLI bootstrapu mimo kanonický projekt; stejný test v kanonickém prostředí PASS. Nové testy dohledu PASS; úplná kanonická publikační brána následuje u Terry.

Vývoj proběhl v samostatném vlastním worktree, Data se nemění. Při integraci
je použit existující worker zámek proti načtení neúplné sady souborů.
Definice LaunchAgentu ani nastavení Pushcutu se nemění; žádný bootstrap,
reinstalace, vypnutí sledovaných služeb či úprava soukromých incidentů ručně.
Všechny existující soubory a účtenky zůstávají zachované.

Další krok: Lokální commit a již schválené jediné Terra p+n; konečná provozní
účtenka je mimo Git v logs/agent_supervisor_sleep_release_20261114.log.
Po vydání ověřit GitHub SHA, health/nové UI, čerstvý scheduled tick a stejnou
vlastněnou službu/config. Další skutečná noc je fyzická přejímka; automaticky
Mac neuspávat. Bez samostatného pokynu nenastavovat žádný vnější dohled.

Technické zdroje: https://github.com/apple-oss-distributions/PowerManagement/blob/main/pmset/pmset.m
(System Capabilities) a https://github.com/apple-oss-distributions/xnu/blob/main/iokit/IOKit/pwr_mgt/IOPM.h
(Graphics0x02). Provozní cesta je lokální Mac; GitHub uchovává kód a Pushcut
doručuje oznámení.

Doplňující QA: Skutečná noční OS časová osa64 Sleep/DarkWake/Wake přechodů
přehraná do syntetických zdravých služeb a desetiminutového autosave:266
kontrol,203 pozastavených,0 falešných oznámení. Produkční incidenty/config
se neměnily,0 skutečných Pushcut POST. Doklad
logs/agent_supervisor_sleep_replay_20261114.log (nenahrazuje další fyzickou noc).

Omezení izolované brány: Jediný nezměněný test recovery CLI bootstrapu
v oddělené kopii vrátil attention/ValueError. Tentýž test v kanonickém
projektu bez úpravy kódu prošel; neobchází se žádná aktivace a nekopírují
se privátní data. Doklad logs/agent_supervisor_sleep_canonical_environment_test_20261114.log.
Plnou kanonickou bránu nad přesným commitem musí před push/deploy dokončit
registrovaná Terra; konečná provozní účtenka zůstává mimo Git.
