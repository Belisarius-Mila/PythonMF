# Společný provozní rozhovor Samanthy

Aktualizace: 2026-11-16 21:32 CET. Kanonický proud project-cockpit; existující handoff a
TVBCP ve workstreams/project-cockpit.md. Nejde o nový vývojový profil.

## Schválený rozsah a použití

První balíček propojuje iPhone, Cockpit a Mint. Na monitoru tlačítko Samantha
otevře /samantha/. Zahájit rozhovor vytvoří prázdnou historii bez modelového
volání. Připojit telefon zobrazí jednorázový šestimístný kód na deset minut.
Na telefonu stejný vstup, zadat kód. Psát / diktovat zde převezme rozepsaný text;
iPhone používá mikrofon vlastní klávesnice. Na Mintu lze psaní převzít a text
opravit. Odeslat spustí jednu otázku, obě zařízení vidí tutéž odpověď. Ctrl/Cmd
+Enter odpovídá výslovnému Odeslat. Obnovit stav je pouze čtení.

Celý schválený plán je v Downloads/Samantha_iPhone_Cockpit_Mint_plan_vyvoje_2026-11-16.txt.
Další balíčky: knihovní hledání a karty; ukládání článků/receptů/míst a evidence
návštěv; kalendářové formuláře; browser rozšíření pro ovládání monitoru.
Současný chat tyto akce neslibuje a nemá jejich nástroje.

## Stav a spolehlivost

- app/shared_chat.py používá kanonický data/private/shared_chat/, nikoli kopii
  izolovaného vývojového profilu. JsonWorkRepository: atomické transakce a
  sdílený zámek. Soukromá data, kódy a přístupové údaje nepatří do Gitu.
- Spárované zařízení má vlastní náhodný přístupový klíč, pouze v lokálním
  browser storage a API těle/hlavičce. Nikdy v URL. Host/Origin kontroly Cockpitu
  zůstávají závazné. Neúspěšné pokusy o kód mají omezení; kód je jednorázový.
- Rozepsaný text má revizi, vlastníka psaní a120sekundovou obnovovanou lease.
  Převzetí je výslovné, pozdní zápis hlídá compare-and-set. Konfliktní místní
  text zůstává v sessionStorage a lze ho vědomě převzít. Stav po výpadku je
  viditelně neověřený; nové odeslání je do obnovení spojení nedostupné.
- Před POST se uchová původní identita zprávy. Server nejdřív atomicky přijme
  přesný draft, teprve pak spouští worker. Souběžné POST, ztracená odpověď ani
  reload nespustí další tah. Polling, připojení a psaní model nevolají.
- Odpovědi a původní doručení vlastní samostatný CanonicalSessionHub. Restart
  pokračuje v uloženém threadu; pokud dokončení není doložené, ukazuje
  delivery_unknown a novou kopii blokuje. Automatické znovuodeslání neexistuje.
  U restartu během nedokončeného tahu není v prvním balíčku operátorská
  rekonciliace; zachovat původní účtenky, neposílat stejnou otázku do nového chatu.
- app/shared_chat_runtime.py přebírá stávající human-chat model/effort; nezasahuje
  do config/agent_roles.json ani do vývojových profilů. Oddělený workspace,
  read-only sandbox bez sítě, nástroje/MCP/aplikace vypnuté. Použití textového
  modelu začne jen výslovným Odeslat. Mobilní diktování neposílá audio Samanthě.
- Změnit připojení mění pouze toto zařízení; historii na Macu nemaže. Běžné
  zavření stránky a návrat používají stejnou identitu. Výpadek Macu znamená
  nedostupný backend, Tailscale samotný jej nenahrazuje ani nebudí.

## Ověření a meze

335 cílených testů PASS: doména, runtime, skutečné HTTP, dva skuteční JS klienti,
CAS konflikt, souběžný send, ztracená HTTP odpověď, reload, pozdní GET,
offline/online, dosavadní Cockpit a registry. Živý App Server přijal oddělené
připojení s nulou modelových tahů. Uložený runtime_probe.json není důkazem
skutečné modelové odpovědi. Fyzický telefon/Mint a Safari náhled neověřené.
Vlastní validační doména shared_chat propojuje také HTML/CSS/JS a Node fixture
s reálným HTTP testem dvou klientů; změna frontendu nesmí skončit jen obecnými
serverovými kontrolami. První integrační brána1529 PASS; po posledním rozdílu
rozhoduje finální účtenka, přerušený následný meziběh není důkaz.
Konečná programová brána a lokální commit: private shared_chat_20261116/completion.json.
Vývoj sám není push nebo nasazení do běžícího Cockpitu.

Přejímka po samostatně schváleném p+n: na Mintu založit rozhovor, připojit
telefon kódem, převzít/diktovat otázku, převzít/opravit na Mintu, odeslat jednou,
ověřit odpověď na obou, obnovit stránky a krátce přerušit síť bez další otázky.
