# GPS u nových okamžiků — lokální implementace

## Fyzická přejímka 27. 9. — aktualizováno 13:24 CEST

- **Import/spuštění nové verze a zachování dat PASS podle Míly**: původní
  Camino se otevře, obsahuje „Povolit / obnovit GPS“, všechna data fungují.
- **GPS1 PASS**: nový okamžik před povolením polohy ukazuje „GPS u tohoto
  okamžiku není uložená“. To není důkaz skutečného GPS bodu ani přenosu.
- SideStore snímek v 08:29 ukazoval Camino / Sideloaded / 7 DAYS a kolečko
  místo ikony. Samotné kolečko nebylo důkazem selhání: následovalo úspěšné
  otevření nové funkce. Přesné datum nového profilu nebylo odečteno.
- **GPS2 částečně PASS (27. 9. 13:24)**: Míla potvrzuje „GPS uložena“,
  hlášená přesnost ±8 m. Jde o odhad telefonu, ne geodetické ověření místa.
  Offline vytvoření, zachování po restartu a mediální větve zbývají.
  **GPS3/GPS4 NEOVĚŘENO**; přenos na Mac dosud nedoložen. Bez změny kódu/služeb.

### Historická příprava balíčku

Aktualizace 27. 9. 08:02 CEST: **Camino 0.1.0 (6)** ze zdroje `3fbf7232`
je připravené ve Stahování jako `Camino-GPS-6-20260927.ipa` (1 049 786 B).
Stejné ID `cz.pythonmf.camino.app`, stejný tým a pokrytí zařízení jako build 5;
GPS usage description přítomný, background režim pouze audio. Podepsaný
generic iOS build, strict codesign i ZIP integrita PASS, binární obsah IPA
shodný s ověřenou aplikací. SHA-256:
`e805f9866400897ddcd320632f370a9ece16ddfcf2d3d35c59ba09f189fa523c`.
Přiložený starý profil vyprší **27. 9. 12:10 CEST**: pouze pro **nový podpis
v SideStore**, ne přímou instalaci. Nová expirace bude známá až po importu.
Na iPhonu zatím nic neinstalováno; GPS1–GPS4 zůstávají NEOVĚŘENO.
Push, server, Viewer grant ani Serve/Funnel se tímto krokem nemění.

### Import buildu 6

1. Přenést nové IPA ze Stahování na Macu do **Souborů na iPhonu**, například
   AirDropem. Kabel není pro import SideStore potřeba.
2. Camino zavřít. Pro SideStore zapnout **LocalDevVPN**, ověřit zelené
   **Device Reachability**. Při červené postupovat podle LL-051; RemotePair
   port je proměnlivý, nepřebírat historickou hodnotu.
3. SideStore → My Apps → **+** → vybrat `Camino-GPS-6-20260927.ipa`.
   **Customize AppID** ponechat zapnuté. V dialogu tohoto konkrétního importu
   ověřit ID `cz.pythonmf.camino.app` a **odškrtnout Append Team ID**.
   Checkbox se může při každém importu znovu zaškrtnout. Nic neodinstalovávat.
4. Po dokončení otevřít původní Camino, ověřit stará data a novou položku
   **Povolit / obnovit GPS**. Zatím GPS nepovolovat: první krátký test GPS1
   ověřuje nepovolenou polohu. Odečíst novou platnost v SideStore.
5. Až pro přenos GPS3 odpojit LocalDevVPN a zapnout **Tailscale**. Nestřídat
   tokeny ani znovu párovat, pokud stávající Camino připojení funguje.

Rozhodnutí Míly 27. 9. 2026: mapu odložit, sběr a přenos GPS dokončit před
cestou. Starší záznamy se nedoplňují. Před odjezdem naváže jednoduchý odkaz
„Otevřít místo v mapě“ ve Vieweru pro Janu, ne vlastní mapa ani sledování trasy.

## Chování

- iPhone pořídí jednorázový bod přes Core Location; oprávnění pouze při
  používání. Na hlavní obrazovce je stav a **Povolit / obnovit GPS**.
- Po povolení se poloha připravuje při příchodu do popředí, otevření kamery,
  ruční obnově a při zachycení (výsledek tohoto posledního požadavku je až
  pro následující okamžik). Bez periodického měření, historie pohybu,
  oprávnění Always nebo background location. Po odchodu do pozadí se požadavek ruší.
- Zachycení nikdy nečeká na polohu. Použije se již dostupný bod nejvýše
  120 sekund starý a ne z budoucnosti; chybějící, neplatný a starý bod znamená
  `location=null`. Přesnost nad 100 m se označí jako přibližná.
- **Omezení:** první okamžik před dokončením měření nebo po delší nečinnosti
  může být bez GPS. Pokud je poloha důležitá, před zachycením ověřit
  „GPS připravená“, případně použít obnovu. Pozdní bod se nepřiřazuje zpětně.
  Jednorázový požadavek má limit 15 s; nejde o garanci získání GPS.
- Bod patří vzniku Momentu: marker, nové foto/video, komentář a úvaha.
  U audia/videa je uložen s počátečním intentem; dokončení či obnova používá
  původní bod. Připojené médium ani pokračování nahrávky jej nemění.
- Detail na telefonu ukáže přítomnost GPS, souřadnice a odhad přesnosti.
  Přenos používá dosavadní `create_moment.location`: latitude, longitude,
  measured_at_utc_ms, horizontal_accuracy_m. Bez nového API či migrace serveru.
- Lokálně jde o nový oddělený záznam v existujícím `SettingRecord`, uložený
  v téže transakci jako Moment/intent. Core Data model se nemění; staré
  záznamy a jejich synchronizační obálky mají nadále původní null.
- Souřadnice nejsou v logách, provozních stavech ani Gitu. Originály médií
  a GPS/EXIF očištění Viewer kopií se nemění. Viewer zatím polohu nevydává.

## Automatické ověření

- Swift sada: **44/44 PASS**, včetně 5 GPS testů (hranice stáří/platnosti,
  restart a staré záznamy, audio retry, foto/video a přílohy, stabilní JSON).
- Server API: **3/3 PASS**; jedna zkouška přijímá skutečné syntetické JSON
  obálky vygenerované Swift testem, nikoli jen ručně napodobený payload.
  Opakovaný POST a znovuotevření DB zachovají bod, legacy null a počet operací.
- Generic iOS unsigned build PASS; simulátor iPhone 14 Plus/iOS 26.3:
  **UI 1/1 PASS**, nepovolená GPS neblokuje marker a stav přežije restart.
  Snímek hlavní obrazovky vizuálně zkontrolovaný. Plná projektová brána:
  **1830/1830 PASS** (364,7 s), následná rychlá statická brána PASS.
  Fyzická GPS, nový SideStore podpis/instalace a přenos z iPhonu NEOVĚŘENO.

Opakovatelná syntetická zkouška (v žádném kroku nečte živý archiv):

```sh
CAMINO_GPS_WIRE_FIXTURE=/private/tmp/camino-gps-synthetic-wire.json swift test --package-path camino/app --scratch-path /private/tmp/camino-gps-tests
CAMINO_GPS_WIRE_FIXTURE=/private/tmp/camino-gps-synthetic-wire.json /private/tmp/camino-c05a-venv/bin/python -m unittest camino.server.tests.test_gps -v
```

API test vyžaduje existující izolované serverové prostředí s FastAPI/httpx;
projektová `.venv` je neobsahuje. Nic kvůli testu do ní neinstalovat.
Bez proměnné je volitelný přeshraniční test přeskočen, nikoli PASS.

## Jeden krátký fyzický průchod po samostatně schválené aktualizaci

Zachovat tutéž aplikaci, ID a data; neodinstalovávat. Pro SideStore použít
LL-051 (skutečný RemotePair port, Append Team ID off); pro přenos Tailscale
a aktuální owner token. Žádné souřadnice ani tokeny neposílat do chatu.

1. **GPS1 — bez oprávnění:** ve Zkoušce bez povolené polohy označit okamžik.
   Uložení nesmí čekat; detail poctivě říká, že GPS není uložená.
2. **GPS2 — venku/offline:** povolit při používání, počkat na „GPS připravená“.
   Bez internetového připojení vytvořit marker, foto a krátký komentář/video.
   Detail má skutečný bod a přesnost. Znovu otevřít aplikaci; bod zůstane.
   Dlouhé audio ani hovory se neopakují; GPS nezasahuje do audio driveru.
3. **GPS3 — Mac:** obnovit připojení/Tailscale a poslat malou dávku. Vlastnickou
   kontrolou porovnat všechny čtyři hodnoty GPS v telefonu a uloženém Momentu
   na Macu; do důkazu uvést pouze shoda=true/false a počet, ne souřadnice.
   Zopakovat synchronizaci: bez duplikátu. Staré záznamy zůstanou beze změny.
4. **GPS4 — nepřesná/nedostupná:** alespoň jednou ověřit odmítnutí polohy nebo
   vypnutou přesnou polohu; záznam funguje, bod buď chybí, nebo je podle
   skutečné přesnosti označen jako přibližný. Nedostupné varianty NEOVĚŘENO.

GPS1 **PASS**, GPS2 **částečně PASS** podle přejímky výše; GPS3/GPS4 **NEOVĚŘENO**. Syntetická API zkouška nedokládá fyzický GPS fix,
spotřebu ani skutečnou telefonní síť. Živý server, grant Vieweru, Serve/Funnel
a instalace telefonu nebyly v tomto kroku změněny.

## Následuje: odkaz pro Janu

Pouze aktuální povolený `diary` Moment s bodem, nikdy `Jen pro mě`, skrytý,
konfliktní či odvolaný zdroj. Odkaz otevře externí mapu až po kliknutí, bez
vložené mapy a bez automatického stahování dlaždic. Poskytovatel mapy pak
obdrží daný bod; nevkládat token ani obsah deníku do URL/referreru. Při
přijatém zámku odkaz zmizí; už otevřenou mapu nelze odvolat. Před implementací
doplnit projekční/HTML testy soukromí a pak ověřit kliknutí s Janou.

Platformní podklad: Apple [jednorázová poloha](https://developer.apple.com/documentation/corelocation/cllocationmanager/requestlocation())
a [oprávnění při používání](https://developer.apple.com/documentation/corelocation/cllocationmanager/requestwheninuseauthorization()).
Použité chování je ověřené kompilací proti místnímu SDK; fyzická přejímka zbývá.
