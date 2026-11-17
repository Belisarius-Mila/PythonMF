# Samantha — oprava přenosu textu po spárování

Míla nahlásil, že se po připojení kódem nic nepřenáší. Čtecí kontrola
oddělila úspěšné párování od dosud neuloženého draftu; obsah skutečných
soukromých zpráv ani přístupové údaje se nevypisoval a rozhovor se neměnil.

Příčina je reprodukovaná v nativním Safari: klient si uložil globální
setTimeout/clearTimeout do vlastností instance. Volání this.clearTimer nebo
this.setTimer tím předalo jako receiver klienta. Safari vyžaduje Window
(TypeError: Can only call Window.clearTimeout on instances of Window).
Selhal automatický debounce i ruční flush. Párovací a claim API časovače
používaly jinak, proto připojení vypadalo úspěšně. Běžný polling navíc mohl
přepsat přechodnou chybu, přestože lokální text dál čekal na přenos.

Oprava zachovává testovou injekci a výchozí časovače obaluje uzávěry volajícími
přímo správné Window. Vedle editoru je trvalá informace o dosud nepřeneseném
nebo uloženém draftu a o nutnosti převzít psaní. Není změněná persistence,
párovací protokol, scope/oprávnění, historie nebo pravidla jediného send.
Lokální recovery zůstává explicitní, otázky se automaticky neopakují.

Ověření:
- Nová brand-check regrese před opravou FAIL, po opravě PASS. Ověří správný
  receiver, nahrazování debounce, lokální recovery a zrušení při disconnect.
- Další prohlížečový test provede přímo automatický debounce → jedno uložení
  draftu přes HTTP adaptér; žádný modelový send. Přítomnost nové JS regrese
  pokrývá stejná doména shared_chat a stávající HTTP Python modul.
-51 cílených Python kontrol PASS, včetně skutečného HTTP toku dvou JS klientů,
  souběhu/nejistého send a validačních kontraktů. Izolované HTTP testy nyní
  mockují provozní logger; odmítnutí cizího Origin dál ověřují bez znečištění
  skutečného bezpečnostního logu testovací událostí.
- Nativní Safari: dva originy téže localhost fixture pro dvě nezávislá
  úložiště. Po reloadu opraveného klienta explicitní obnova zachovaného
  testovacího textu; párování, automatický přenos v obou směrech, převzetí
  na monitorovém klientu, ruční oprava, jeden send do syntetického modelu,
  tatáž odpověď v obou klientech a reload bez další zprávy. Soukromá testovací
  místnost obsahuje právě jednu dokončenou, potvrzenou zprávu. Nula placených
  modelových tahů. Vlastní okno/server uzavřené, původní Safari zachované.

Finální programovou bránu nad celým čekajícím balíčkem, zmrazené otisky a
lokální commit určuje data/private/shared_chat_transfer_fix_20261117/completion.json.
Zdrojový main zahrnuje také dřívější lokální FR klient eafc8161; úzké důkazy
Mint opravy nenahrazují potřebné pokrytí této čekající registrace.

Oprava je místní, běžící Cockpit nebyl restartovaný ani nasazený. Další krok
je samostatně autorizované p+n a Mílova fyzická přejímka iPhone/Mint.
Při obnovení skutečné stránky použít případně „Použít zachovaný text“;
neodesílat novou kopii nejisté otázky. Přímé řízení browseru/kalendáře zůstává
další vývojový balíček, toto je oprava prvního sdíleného rozhovoru.

První společná brána dokončila1353 testů s jediným TimeoutExpired při startu
syntetického CLI v test_cockpit_https_entry. Test ověřuje předání prostředí,
nikoli rychlost nově vytvořeného procesu pod zatížením. Testovací runner nyní
povolí této fixture10s; samostatný kontrakt stále vyžaduje produkční timeout2s.
Produkční read_serve_status ani nastavení Tailscale se nemění. Následných51
cílených kontrol včetně HTTPS modulu PASS; konečná společná účtenka rozhoduje
podle completion.json, první neúspěšný běh není důkaz PASS.
