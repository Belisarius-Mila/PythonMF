# Camino

Soukromý cestovní deník: offline záznam na iPhonu, soukromé zpracování na Macu
a pozdější film z povolených zdrojů.

**Stav: autoritativní podklady v0.5 + U15. C01a a C01b přijaty v prototypovém rozsahu. C01c 0.3.0 (3) je rozpracované pro segmentový journal a obnovu po pádu; fyzické T022/T023 čekají. Camino Viewer je P0, ale podle etap se implementuje až v C08c–C08f.**

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
- [Audio prototyp](prototypes/audio/README.md)
- [Aktuální report a překážky](docs/C01a_AUDIO_PROTOTYPE_REPORT.md)

Provést T022 na nainstalované verzi 0.3.0 (3); podle výsledku pokračovat T023,
nebo nejdřív opravit C01c.

Rozbalené podklady v0.4 a v0.5 jsou verzované včetně manifestů. Původní ZIPy
jsou zachované lokálně a ignorované Gitem; profilové workspaces přebírají
dokumenty. Původní v0.5 se kvůli dodatku nepřepisuje.
