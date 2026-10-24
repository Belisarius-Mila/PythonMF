# Camino

Soukromý cestovní deník: offline záznam na iPhonu, ověřené originály na Macu,
soukromý Viewer a jednodenní film z povolených podkladů.

## Aktuální orientace — 24. 10. 2026

Místně doplněný **koš celých cest a filmů na 7 dní**: žádost na iPhonu,
kontrola a potvrzení ve střižně, obnovení do lhůty a následný výmaz
spravovaných dat včetně telefonu po jeho spojení. Samostatný film ponechá
originály cesty. [Postup, rozsah a hranice vydání](docs/PROJECT_TRASH_REPORT.md).
Ovládání ve střižně je nasazené v `0a18db30` (Luna `b75c48be`, 2232 PASS,
smoke 5/5). Celý koš ještě vyžaduje samostatný upgrade služby Camino
a instalaci iPhonu; tyto části běžné p+n neaktualizovalo.

Nově místně: původní text z iPhonu a upravitelná pracovní kopie u fotografie,
historie čtení, obnovitelný koš a import MP3/WAV.
[Pracovní cyklus komentáře](docs/COMMENTARY_WORKFLOW_REPORT.md).

Místní přepracování střižny přidává **Text a komentář** přímo u fotografie:
celý text, statický panel, plynulé okno a uložené české čtení. Hlas připojený
k fotografii se přesouvá s ní; prodloužení obrazu je výslovné.
[Postup, ověření a hranice vydání](docs/PHOTO_TEXT_COMMENT_REPORT.md).

Nový místní krok 4–5 přidává výběr povolených cest ve Vieweru a volbu cesty
před dnem/filmem ve střižně. V aplikaci se zobrazí období i rozlišení shodných
názvů; nový projekt začíná bez přístupu pro Janu.
[Ovládání, oprávnění a ověření](docs/MULTI_PROJECT_ACCESS_REPORT.md).
Jde o vývojový checkpoint; živé vydání a instalace jsou samostatné kroky.

Předchozí balíček do e11d949a byl 24. 10. ověřeně pushnutý a nasazený do
Cockpitu přes Lunu e47cdb394ec5441c5d25632f11c8c995 (plná brána 2186,
smoke 5/5). Původní neúspěšné předání c3aba030 je uzavřená historie.

Více cest/dovolených má společný datový základ a oddělení projektů (kroky
1–2, publikované v ffc933d5). Nový krok 3 doplňuje ovládání projektů,
termínů a archivace v telefonu; [rozsah a přejímka](docs/PROJECT_MANAGEMENT_UI_REPORT.md).
Instalace telefonu a aktualizace samostatné služby zůstávají oddělené.

Oprava velkých fotografií ve střižně je publikovaná/nasazená v 8bc31d07
přes Lunu 5b60714d658675cfedd05f1df1bafad7 (2185 testů, smoke 5/5, náhled
HTTP 200). Celý rám a originál jsou zachované; [limity](docs/LARGE_PHOTO_REPORT.md).
Celý film dne 14. 10. má samostatnou uživatelskou přejímku.

- **iPhone:** fotografie i video mají zoom gestem dvěma prsty a podporované
  volby 0,5× / 1× / 2×. Míla potvrdil funkčnost a tento rozsah mu zatím stačí.
  Poslední připravený balíček je 0.1.0 (20); potvrzení nenahrazuje úplný
  protokol jednotlivých telefonních scénářů.
- **Střižna v Cockpitu:** Moje filmy a výběr dne, uložené revize střihu,
  přímý náhled fotografií/videí, ruční střih a soukromý export 720p/1080p.
  Panel **Texty a komentáře** nabízí přijaté texty, titulky, samostatné
  textové karty a poslech/umístění původního hlasu.
- **Doložené funkční vydání panelu střižny:** `d8d16f1b`, účtenka Luny
  `4b1ed8c23af048f133e00971d0ad1038`, push a nasazení do Cockpitu potvrzené,
  plná brána PASS (2 174 testů v účtence), kontroly po restartu 5/5.
  Při aktualizaci této dokumentace byl nový panel znovu dostupný přes HTTP.
- **Otevřeno:** fyzická přejímka nového panelu na Macu/iPhonu, samostatný
  důkaz nových větví renderu textové karty a poslechové kopie. Spojování
  více dnů do společného filmu P2-F zůstává pozdější samostatný krok.

P+n pro tento proud nasazuje společný runtime Samanthy/Cockpitu. Aktualizace
aplikace na iPhonu a samostatné služby Camino jsou odlišné operace. Provozní
stav se ověřuje živým auditem a přesnou účtenkou; tento text je datovaný přehled.

## Návody

- [iPhone: záznam, zoom, text a přenos do Macu](app/README.md)
- [Filmová střižna: postup od výběru dne po MP4](film/README.md)
- [Zoom: rozsah, balíček a hranice telefonního potvrzení](docs/CAMERA_ZOOM_REPORT.md)
- [Texty a komentáře: ovládání, soukromí a důkaz nasazení](docs/FILM_TEXT_AUDIO_REPORT.md)
- [Editor a export: technický report a historie](docs/P2CD_EDITOR_MP4_REPORT.md)

## Základní pravidla

Originály a starší revize se nepřepisují. Jen pro mě, skryté a nejasně
povolené podklady nevstupují do Vieweru ani filmu. Do deníku je stále
soukromý obsah. Textový koncept se nejprve vědomě uloží, pak přenese;
prázdná fronta sama nedokládá úplnost filmových vstupů. Přepis ani film
nejsou záloha. Nic se automaticky veřejně nesdílí.

## Specifikace, paměť a historické etapy

Podklady v0.5 společně se závazným dodatkem U15 jsou autoritou zadání.
Starší etapové reporty zachycují tehdejší stav, nikoli současný běh služeb.
V Human–Adam se projekt jmenuje **Camino** (`project-camino`).

- [Podklady v0.5](CAMINO_podklady_v0.5/README_v0.5.md)
- [Funkční specifikace v0.5](CAMINO_podklady_v0.5/CAMINO_funkcni_specifikace_v0.5.md)
- [Závazný dodatek k soukromí](docs/V05_PRIVACY_AMENDMENT.md)
- [Postupné úkoly C00–C11](CAMINO_podklady_v0.5/CAMINO_Codex_v0.5.md)
- [Historické podklady v0.4](CAMINO_podklady_v0.4/README_v0.4.md)
- [Projektová paměť](../memory/projects/camino.md)
- [Handoff](../memory/handoffs/workstreams/project-camino.md)
- [TVBCP](../memory/tvbcp/workstreams/project-camino.md)

- [Audit prostředí C00](docs/ENVIRONMENT_AUDIT.md)
- [Připravenost Camino Vieweru](docs/VIEWER_READINESS.md)
- [Technická rozhodnutí](docs/DECISIONS.md)
- [Ověřená instalace Xcode](docs/XCODE_INSTALLATION.md)
- [Zadání C01a](tasks/C01a_AUDIO_PROTOTYPE.md)
- [Zadání C01b](tasks/C01b_BACKGROUND_AUDIO.md)
- [Report C01b](docs/C01b_BACKGROUND_AUDIO_REPORT.md)
- [Zadání C01c](tasks/C01c_RECOVERABLE_AUDIO.md)
- [Report C01c](docs/C01c_RECOVERABLE_AUDIO_REPORT.md)
- [Zadání C02a](tasks/C02a_SYNTHETIC_RECEIVER.md)
- [Report C02a](docs/C02a_SYNTHETIC_RECEIVER_REPORT.md)
- [Zadání C02b](tasks/C02b_CHUNK_TRANSFER_EXPERIMENT.md)
- [Report C02b](docs/C02b_CHUNK_TRANSFER_REPORT.md)
- [Zadání C05a](tasks/C05a_PRODUCTION_RECEIVER.md)
- [Report C05a](docs/C05a_PRODUCTION_RECEIVER_REPORT.md)
- [C05a mediální OpenAPI](docs/C05a_MEDIA_OPENAPI_V1.json)
- [C05a server](server/README.md)
- [Zadání C05b](tasks/C05b_IOS_SYNC_QUEUE.md)
- [Report C05b](docs/C05b_IOS_SYNC_REPORT.md)
- [Fyzický plán C05b](app/C05b_IPHONE_TEST_PLAN.md)
- [Zadání C05c](tasks/C05c_STATUS_AXES.md)
- [Report C05c](docs/C05c_STATUS_UX_REPORT.md)
- [Fyzický plán C05c](app/C05c_IPHONE_TEST_PLAN.md)
- [Audio prototyp](prototypes/audio/README.md)
- [Transfer harness C02b](prototypes/transfer/README.md)
- [První integrovaná iPhone aplikace C04a](app/README.md)
- [Historický report C01a a tehdejší překážky](docs/C01a_AUDIO_PROTOTYPE_REPORT.md)

Rozbalené podklady v0.4/v0.5 a jejich původní manifesty zůstávají zachované.
Původní ZIPy jsou lokální a ignorované Gitem; původní podklady se kvůli
novějším dodatkům nebo návodům nepřepisují.
