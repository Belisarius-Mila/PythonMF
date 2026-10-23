# Camino — první krok zoomu fotoaparátu

Stav dokumentace: 23. 10. 2026. Zoom má Mílovo obecné potvrzení funkčnosti
„funguje, zatím to stačí“. Jednotlivé scénáře níže nejsou tímto potvrzením
samostatně přijaté; přesná instalovaná verze ani postup instalace nebyly
v potvrzení doložené. Poslední připravený Release je 0.1.0 (20).

Zdroj zoomu `07109721` byl pushnutý v balíčku přes registrovanou Lunu,
účtenka `698ae54bb9df52516cd35c2821f88f4c`: push/deploy potvrzené,
plná brána PASS (2 174 testů v účtence), kontroly Cockpitu 5/5. Toto p+n
neinstalovalo klienta do iPhonu. [Praktický návod](../app/README.md).

## Rozsah

- Fotografie i video: přiblížení dvěma prsty, aktuální hodnota a podporované
  rychlé volby 0,5× / 1× / 2×. Tlačítka přecházejí plynule; gesto mění zoom přímo.
- Přednostně zadní triple/dual-wide/dual camera, potom základní wide camera.
  Přední kamera zůstává podporovaná. Každá kamera se otevírá v normálním 1×
  záběru, pokud jej aktuální konfigurace dovoluje.
- iOS 18+ používá systémový displayVideoZoomFactorMultiplier; iOS 17 odvozuje
  měřítko ultra-wide virtuální kamery z prvního přepínacího faktoru.
- Nastavuje se skutečný videoZoomFactor zařízení pod lockForConfiguration.
  Převod a limity kontroluje LocalCameraZoomScale; neplatné číselné hodnoty se odmítají.
- KVO aktualizuje hodnotu, rozsah i rychlé volby. Změna zoomu nepřestavuje
  capture session. Je povolená v ready/recording, zakázaná při ukládání a dokončování.
- Při návratu z pozadí se obnoví stav ovladačů. Chyba nastavení zoomu ponechá
  režim nahrávání a zvuku beze změny. Při nedostupné nové kameře se vrací původní input.
- Vyšší digitální zoom může snížit kvalitu; volba 2× není označená jako optická.

Ostření dotykem, expozice a blesk nejsou v tomto kroku implementované.
Datové schéma, soukromí, ukládání originálů a synchronizační kontrakt se nemění.

## Ověření a balíček

- Swift XCTest: 79/79 PASS, z toho pět nových testů měřítka, mezí a neplatných vstupů.
- Arm64 iOS Debug a Release: BUILD SUCCEEDED, Xcode 26.3, SDK iOS 26.2.
- Release balíček 0.1.0 (20), bundle ID `cz.pythonmf.camino.app`, arm64.
- `Camino-Zoom-20-20261023-unsigned.ipa`, 1 289 562 B, ZIP/CRC PASS.
- SHA-256: `b2c6eaab20343f569a87c4b6203f3078f83a881ec56d31efa6b5730d707bb031`.
- Kopie ve Stahování má shodný hash. Balíček nemá podpis/profil pro zařízení;
  při instalaci jej musí podepsat SideStore při zachování identity stávající aplikace.
- Sestavení nepředstavuje fyzické ověření kamery. Push a nasazení společného
  runtime jsou již doložené účtenkou výše; telefonní instalace je samostatná.
  Mílovo potvrzení funkčnosti není dokladem každého bodu podrobného plánu.
- Logy, manifest a technický archiv Gitu: `data/private/camino_zoom_20261023/`.

## Podrobná fyzická přejímka — jednotlivé scénáře NEOVĚŘENO

1. Před aktualizací ověřit dostupnost původních dat. Aktualizovat stejnou
   aplikaci bez odinstalace; po spuštění zkontrolovat zachování záznamů.
2. Zadní fotografie: výchozí 1×, podporované 0,5×/1×/2×, pinch k oběma mezím.
   Uložený snímek musí odrážet zvolený zoom, bez chyby či pádu.
3. Video se zvukem: během jednoho klipu postupně měnit zoom, nahlas počítat,
   bezpečně ukončit a přehrát celý klip. Ověřit plynulost a souvislý zvuk.
4. Zopakovat tiché video; výslovná volba Bez zvuku musí zůstat zachovaná.
5. Přední kamera: podporované meze, žádné falešné ultra-wide tlačítko, návrat
   na zadní kameru a normální 1×. Přepínání kamer během záznamu zůstává blokované.
6. Portrét i krajina: ovladače, orientace a uložený obraz bez otočení či ořezu navíc.
7. Pozadí během náhledu i videa: dosavadní bezpečné přerušení, žádný automatický
   restart záznamu; po návratu opět použitelné ovladače.
8. Nové foto/video připojit ke správnému Momentu a ověřit dosavadní ukládání
   a přenos. Nepovažovat úspěšné sestavení za důkaz zachování zvuku nebo dat na telefonu.

## Technické podklady

- [Apple: Zoom](https://developer.apple.com/documentation/avfoundation/capture-device-zoom)
- [Apple: displayVideoZoomFactorMultiplier](https://developer.apple.com/documentation/avfoundation/avcapturedevice/displayvideozoomfactormultiplier)
- [Apple: virtualDeviceSwitchOverVideoZoomFactors](https://developer.apple.com/documentation/avfoundation/avcapturedevice/virtualdeviceswitchovervideozoomfactors)
