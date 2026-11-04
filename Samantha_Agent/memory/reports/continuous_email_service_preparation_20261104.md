# Příprava hodinové e-mailové služby

## Výsledek

Samostatný jednorázový vstup `tick` používá existující hodinový plánovač
7–22 v Europe/Prague, celý IMAP/MIME vstup a návrhy v Cockpitu. Budoucí
macOS LaunchAgent jej může vyvolávat po minutě; dokončená hodina už
poštu/model znovu nevolá. Náhled pouze vrací definici, nic neinstaluje.
Mechanismus intervalového spouštění vychází z
[dokumentace Apple](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html).

`service.json` v existujícím private kořeni musí být výslovně připravený
a povolený. Vzor je vypnutý, obsahuje iCloud a Seznam a navržený limit
20 modelových posouzení za pražský den. Tento limit není schválené provozní
nastavení ani finanční strop; celé zprávy se dál předávají bez zkracování.
Po dosažení limitu další zprávy počkají na další den nebo výslovné zvýšení
limitu. Před aktivací je třeba vybrat limit podle požadovaného provozu.

Každý modelový pokus se před voláním trvale započítá v soukromém repository,
včetně pokusu s nejistým výsledkem. Restart počítadlo nevymaže a nejisté
posouzení se samo neopakuje. Při vypnutí konfigurace se dokončí právě
běžící posouzení; další zpráva zůstane před kurzorem. Změna výběru účtů
také zastaví původní dávku. Souběžný proces narazí na provozní zámek.

Role `continuous_email` je nyní rozpoznávaná parserem, ale v centrální
konfiguraci není aktivovaná. Nevyužívá se náhradou role p+n ani vývojáře.
Bez vlastní role se vstup zastaví před katalogovým připojením. Budoucí
výběr ověří katalog a otisk schválení; automatický přechod na jiný model
je zakázaný. Zvolená Terra a její úsilí se převezmou až ze schválené role.

Změna UIDVALIDITY nyní zastaví zdroj před SEARCH/FETCH. Původní pozice
zůstane zachovaná a je vidět `MailboxEpochChanged`. Dřívější chování
začínalo bez dalšího rozhodnutí znovu od celé historie. Obnovení pozice
po takové změně zůstává samostatný explicitní servisní krok.

## Registrované ovládání

- `continuous_email_agent_status`: agregovaný stav; aktivaci bez důkazu
  označuje jako `not_verified`, nikoli napevno „nenainstalováno“.
- `continuous_email_agent_readiness`: pouze místní konfigurace, schválení,
  výchozí pozice a existence socketu. Bez IMAP či spojení s modelem.
- `continuous_email_agent_service_preview`: definice LaunchAgentu a
  vypnutý konfigurační vzor. Bez zápisu do systému či startu procesu.
- `continuous_email_agent_tick`: potvrzovaný jednorázový živý cyklus,
  který navíc vyžaduje povolenou konfiguraci a vlastní schválenou roli.
  V této etapě se živě nespouštěl.

## Čerstvé ověření 2026-11-04 22:39 CET

- iCloud má výchozí pozici; Seznam ji zatím nemá. Existující iCloud pozici
  při budoucí aktivaci zachovat, nepřesouvat automaticky na „teď“.
- Soukromá provozní konfigurace chybí, služba je vypnutá a vlastní modelová
  role ještě není schválená. Socket existuje; nejde o důkaz funkčního modelu.
- Původní čtyři položky zůstávají vyřazené/ignorované, nové nebyly vytvořené.
- Finální cílená sada 112 scénářů PASS, včetně role/workflow a dosavadního
  SMTP/editoru. Plná Cockpit brána 2366 testů PASS (498,4 s); po doplnění
  dvou dalších scénářů samostatně ověřeno všech 15 servisních testů i celá
  cílená sada. Finální statická brána PASS. Plná brána se po čistě
  diagnostickém přejmenování pole náhledu a doplnění testů neopakovala.
- Reprodukce změny identifikace schránky doložila FAIL před opravou,
  následná regrese ověřila zastavení bez SEARCH/FETCH a zachování kurzoru.
- Důkazy: `logs/continuous_email_service_targeted_20261104.log`,
  `logs/continuous_email_service_final_targeted_20261104.log`,
  `logs/continuous_email_service_readiness_20261104.log`,
  `logs/continuous_email_service_gate_20261104.log`.

## Další krok a hranice

Nejprve samostatné p+n tohoto kompatibilního runtime; až potom aktivovat
novou roli v centrálním JSON. Starší běžící parser novou roli ještě nezná.
Připravit schválený profil Terry a provozní počet/rozpočet, výchozí pozici
Seznamu a řízenou instalaci s ověřením po restartu. Náhled není instalátor;
LaunchAgent se ještě nezapisoval ani nenačítal. Změny v LaunchAgents mají
samostatnou systémovou bránu podle `global_safety_brake.md`.

Příště nedůležité je od předchozího p+n již nasazené (592d247b, potvrzené
vydání a zelené GitHub CI); starší zápisy „pouze lokálně“ jsou překonané.
Jeho fyzická přejímka, potvrzená archivace/metadatová přejímka, notifikace
a CalDAV zůstávají otevřené. Tento krok nic neodeslal ani nearchivoval,
nezměnil modelovou konfiguraci ani živé služby a neprovedl p+n.
