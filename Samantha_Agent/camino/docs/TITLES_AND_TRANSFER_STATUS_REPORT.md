# Názvy z telefonu a stav mobilní dávky — B01/B02

27. 9. 2026. Lokální implementace na výslovný pokyn Míly. Nasazení serveru,
push, nový podpis a fyzická aktualizace telefonu jsou samostatné kroky.

## Nasazení serveru 27. 9. 20:35 CEST — připraveno k importu IPA

Míla schválil pokračování nasazením, podpisem a instalací a následně potvrdil
novou přesnou globální brzdu. Registrovaný stop/upgrade/start dokončený;
server release 403180320849 obsahuje implementaci B01/B02 z 7dcee1c8.
Živý HTTPS API stav potvrzuje moment_title_v1, Viewer a všech 6 denních stránek
HTTP 200. Anonymní přístup a záměna owner/reader odmítnuté HTTP 401.
Před/po shodná metadata, serverová identita i owner/reader tokeny. Zachováno
51 Momentů / 155 operací / 58 hashově ověřených médií (263 578 290 B),
oba recovery flagy=false. Upgrade uchoval DB snapshoty a starou konfiguraci.
Soukromá HTTPS trasa zdravá, Funnel off; Tailscale ani Cockpit se nepřepínaly.

Camino 0.1.0 (7), zdroj 7dcee1c8, podepsaný generic iOS build PASS.
Strict codesign PASS, stejné ID cz.pythonmf.camino.app, stejný tým a pokrytí
zařízení jako build 6. Profil do 4. 10. 2026 18:07 CEST. Pro zvolenou instalaci
přes SideStore se podepisuje znovu; jeho výslednou expiraci je třeba odečíst
po importu, nejde o záruku provozu do 17. 10.

Ve Stahování: Camino-Names-7-20260927.ipa, 1 065 916 B, SHA-256
`8837340d63fcc3caecb095a07a39a1ef46ebcaa04d00613f8bbe794b6c413a87`.
ZIP integrita a přesná shoda všech 5 souborů s podepsanou app PASS.
První zabalení přidalo AppleDouble metadata; finální balíček vznikl bez nich
a prošel úplnou kontrolou. Původní build 6 IPA se neměnil.

**Server je připravený; nyní lze importovat.**
SideStore: LocalDevVPN, zelené Device Reachability, import buildu 7,
Customize AppID ponechat zapnuté; pro tento import zkontrolovat původní ID
a odškrtnout Append Team ID. Žádná odinstalace. Po importu kontrola starých
dat a Přidat/Upravit název; pro přenos přepnout na Tailscale.
Import a fyzický přenos názvu stále NEPROVEDENO. Žádný push.

## Rozsah a rozhodnutí

- Jeden nepovinný název celého Momentu: označený okamžik, samostatná fotografie,
  video, komentář i úvaha. Připojená média patří pod tento název; samostatné
  přejmenování každého souboru/úseku nahrávky nyní neimplementujeme.
- V detailu Přidat/Upravit název, jeden řádek do 160 Unicode skalárů,
  Uložit/Zrušit, prázdné pole název odstraní. Ukládání funguje offline,
  nezdržuje pořízení. Seznam i detail zobrazí název, původní čas/typ zůstávají.
- Tok je **iPhone → Mac → Viewer**, bez přenosu oprav z Macu do telefonu.
  Jana je nadále jen čtenář. Webový editor teď nevzniká.
- Adamova volba pro případné pozdější dokončení: malý owner editor na Macu,
  oddělený od čtecího přístupu Jany. Jeho ruční název bude lokální přepis
  zobrazení s předností před telefonním názvem; další příjem z telefonu jej
  nesmaže. Možnost vrátit se k názvu telefonu. Implementace až podle času/kreditů.

## Uložení a kompatibilita

- Telefon přidává volitelná pole do existujícího JSON journalu v SettingRecord,
  nikoli atributy Core Data. Starý journal chybějící název chápe jako prázdný.
- Uložení vytvoří atomickou metadata operaci title a novou revizi. Retry
  stejného ID je idempotentní; jiné tělo pod stejným ID a stará revize selžou.
  Smazání názvu je další revize, originály ani GPS se nemění.
- Původní create_moment payload zůstává nezměněný i po pojmenování. Dříve
  uložené přesné obálky se nepřegenerují. Server umí historický objekt bez
  title; prázdný title do wire nepřidává, aby se nerozbilo porovnání identit.
- Server oznamuje moment_title_v1. Telefon před odesláním čekajícího názvu
  vyžaduje podporu a na starém serveru srozumitelně žádá aktualizaci Macu;
  názvy zůstávají lokálně. **Nejdříve nasadit server, potom aktualizovat telefon.**
- Viewer vydává jen povolené názvy přes existující diary/nonhidden projekci,
  escapuje HTML; zámek či skrytí odstraní i název. Reader nesmí zapisovat.
- Návrat na starší aplikaci po vytvoření title operací není podporovaný:
  starý dekodér tuto operaci nezná. Pro případ obnovy zachovat existující kopie;
  nikdy neodinstalovávat aplikaci kvůli aktualizaci.

## B01 — pravdivý stav po mobilním přenosu

Po ověření posledního média se grant správně ruší. Dosavadní synchronize
i networkChanged potom bez kontroly práce hlásily čekání na Wi-Fi.
Nová společná rozhodovací funkce zachová dříve potvrzenou kopii jen při
známé identitě serveru, úplném pokrytí místních Momentů, nulové čekající práci,
bez chybějících audio metadat a bez recovery flagu. Nejde o nové živé spojení.
Nové médium/pending metadata, ztracená účtenka či obnova nejsou zelené;
další dávka nezdědí mobilní souhlas. Hlášení čekání uvádí počty čekající práce.

## Ověření

- Swift jádro: 47/47 PASS, včetně názvu po znovuotevření, retry, vymazání,
  odmítnutí neplatného názvu/revize, stabilního create payloadu a mobilního stavu.
- Python doména/projekce: 21/21 PASS, včetně historické identity, revizí a soukromí.
- Izolované HTTP Viewer testy: 14/14 PASS, včetně escaping a zákazu reader zápisu.
- Skutečné Swift obálky → izolované ASGI API → znovuotevření DB → Viewer:
  1/1 PASS, včetně opakovaného odeslání a druhého názvu.
- Simulátor iPhone 14 Plus: 1/1 UI test PASS (53,6 s): zadání, uložení,
  ukončení/znovuotevření, kontrola názvu a jeho vymazání.
- Generic iOS Debug build 0.1.0 (7) PASS, CODE_SIGNING_ALLOWED=NO.
  Výstup v /private/tmp/camino-names-device-derived; není podepsanou instalací.
- Plná projektová brána: **1836/1836 PASS**, jednotková sada 445,116 s.
  Logy: /private/tmp/camino-names-full-gate.log, camino-names-swift.log,
  camino-names-http.log, camino-title-wire.log, camino-names-ui.log
  a camino-names-device-build.log (všechny ve stejném dočasném adresáři).
- Fyzický iPhone/import, živý přenos názvu a skutečná mobilní regrese:
  **NEPROVEDENO**. Server nasazený a ověřený výše, telefon se zatím nezměnil.

## Krátká fyzická přejímka po nasazení

1. Aktualizovat tutéž aplikaci bez odinstalace; stará data jsou dostupná.
2. Offline pojmenovat jeden okamžik, změnit název, zavřít/otevřít aplikaci.
3. Malou dávku povolit přes mobilní data a odeslat: úplná kopie potvrzená Macem,
   žádné falešné Čeká na Wi-Fi; název správně ve Vieweru.
4. Další nový záznam bez nového souhlasu čeká. Soukromý název do Vieweru nejde;
   po doručení zámku zmizí i dříve zobrazený název. Vymazání názvu vrátí typ/čas.
5. Bez dostupného Macu nesmí nový název ani médium vypadat jako potvrzené.

Žádná nová matice mikrofonu/hovorů: recorder se neměnil. M3/M4 zůstávají.
