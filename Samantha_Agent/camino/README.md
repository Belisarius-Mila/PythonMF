# Camino

Soukromý cestovní deník: offline záznam na iPhonu, soukromé zpracování na Macu
a pozdější film z povolených zdrojů.

**Stav: autoritativní podklady v0.5 + U15. C04d je fyzicky přijaté v dostupném lokálním rozsahu. C05a serverový základ prošel loopback smoke. C05b má lokálně implementovaný trvalý iOS journal, privátní C03b/C05a klient, pause a jednorázovou mobilní dávku; Swift 27/27, cílený UI test a registrovaný provozní obal prošly. Push, privátní Serve, instalace a fyzické T047–T053/T058 se dokládají samostatně; do té doby nejsou PASS. Funnel zůstává vypnutý. Viewer patří C08c–C08f.**

- [Podklady v0.5](CAMINO_podklady_v0.5/README_v0.5.md)
- [Funkční specifikace v0.5](CAMINO_podklady_v0.5/CAMINO_funkcni_specifikace_v0.5.md)
- [Závazný dodatek k soukromí](docs/V05_PRIVACY_AMENDMENT.md)
- [Postupné úkoly C00–C11](CAMINO_podklady_v0.5/CAMINO_Codex_v0.5.md)
- [Historické podklady v0.4](CAMINO_podklady_v0.4/README_v0.4.md)
- [Projektová paměť](../memory/projects/camino.md)
- [Handoff](../memory/handoffs/workstreams/project-camino.md)
- [TVBCP](../memory/tvbcp/workstreams/project-camino.md)

V Human–Adam se projekt jmenuje **Camino** (`project-camino`).

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
- [Audio prototyp](prototypes/audio/README.md)
- [Transfer harness C02b](prototypes/transfer/README.md)
- [První integrovaná iPhone aplikace C04a](app/README.md)
- [Aktuální report a překážky](docs/C01a_AUDIO_PROTOTYPE_REPORT.md)

C05b používá přijatý C03b manifest jako autoritu a C05a serverovou finalizaci
jako jediný důkaz hotového média. Přenos je alespoň-jednou: po zámku, relaunchi
nebo síťové chybě se nejdřív porovná stav a odešlou se jen chybějící části.
Session-owned privátní služba pro fyzické přijetí není C06a trvalé nasazení;
nemá párovací UI, `launchd` dohled ani druhou zálohu.

Rozbalené podklady v0.4 a v0.5 jsou verzované včetně manifestů. Původní ZIPy
jsou zachované lokálně a ignorované Gitem; profilové workspaces přebírají
dokumenty. Původní v0.5 se kvůli dodatku nepřepisuje.
