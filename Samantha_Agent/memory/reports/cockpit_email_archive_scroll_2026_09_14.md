# Archiv e-mailů: oprava desktopového posouvání — 14. 9. 2026

Míla při přejímce potvrdil ostatní funkce jako zdánlivě v pořádku a nahlásil
nefunkční posouvání seznamu pouze na Macu. Na iPhonu mu posouvání funguje.
Samostatný audit UI zůstává odložený.

Příčina: desktopové grid panely `.message-pane` a `.reader-pane` neměly
`min-height: 0`. Panel roztáhl řádek na výšku obsahu, seznam neměl vlastní
přetečení a `body { overflow: hidden }` skryl zbytek. Mobil již minimum nula měl.
Oprava přidává přesně tyto dvě deklarace do společných pravidel; mobilní
výsledné styly, JavaScript, API i datové operace zůstávají stejné.

## Ověření před/po

Místní headless Edge na Macu, 160 syntetických zpráv, dlouhý syntetický detail,
všechny síťové požadavky zachycené testem; žádná živá soukromá data.
Vestavěný Browser nebylo možné připojit (nedostupný native bridge).

- 1440×900: před opravou seznam clientHeight=scrollHeight=15775 a posun 0;
  po opravě clientHeight=720, posun 15055, poslední zpráva viditelná a otevřitelná.
- 1024×768: před opravou stejné selhání; po opravě clientHeight=588,
  posun 15187, poslední zpráva viditelná a otevřitelná.
- 390×844: před/po stejné rozměry a posun 15149; poslední zpráva otevřená,
  návrat na seznam zachovává dolní pozici. Jde o emulaci, ne nový Safari test.
- Dlouhý detail se po opravě posouvá ve všech třech velikostech. Bez JS chyb
  a bez POST. Desktopový snímek vizuálně zkontrolován.
- 24 cílených frontendových/HTTP testů prošlo. Aktualizovaný očekávaný otisk
  archivní stránky odpovídá pouze dvěma CSS deklaracím.

## Dokončení a přejímka

Oprava navazuje na schválené p+n a hlášenou chybu při přejímce. Tento zápis
vzniká před opravným balíčkem; jeho plnou bránu, push a nasazení doloží
registrované živé audity. Zápis sám jejich úspěch nepředjímá.
Po nasazení na Macu obnovit archiv Cmd+R, dát kurzor nad seznam a rolovat
kolečkem/dvěma prsty až dolů. Otevřít dolní zprávu a zkusit posun dlouhého textu
v pravém panelu. Na iPhonu jen krátce zopakovat dosavadní funkční posouvání.
Širší audit UI až samostatně. Archiv nadále načítá nejvýše 160 výsledků;
opravou se nemění stránkování ani tento existující limit.
