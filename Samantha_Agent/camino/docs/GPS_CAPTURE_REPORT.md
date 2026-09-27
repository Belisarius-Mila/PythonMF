# GPS u nových okamžiků — lokální implementace

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
  Fyzická GPS, podpis/instalace a přenos z iPhonu NEOVĚŘENO.

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

GPS1–GPS4 zatím **NEOVĚŘENO**. Syntetická API zkouška nedokládá fyzický GPS fix,
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
