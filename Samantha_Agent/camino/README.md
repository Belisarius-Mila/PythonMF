# Camino

Soukromý cestovní deník: offline záznam na iPhonu, soukromé zpracování na Macu
a pozdější film z povolených zdrojů.

**Stav: autoritativní podklady v0.5 + U15. C01a, C01b, C01c a C02a jsou přijaty v prototypovém rozsahu. C02b má druhý lokální checkpoint: receiver, trvalá fronta a samostatný iOS URLSession harness jsou připravené k instalaci, ale fyzické T043/T047–T050 ještě neproběhly. Trvalá služba ani veřejná cesta nejsou aktivní. Camino Viewer je P0, ale podle etap se implementuje až v C08c–C08f.**

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
- [Audio prototyp](prototypes/audio/README.md)
- [Transfer harness C02b](prototypes/transfer/README.md)
- [Aktuální report a překážky](docs/C01a_AUDIO_PROTOTYPE_REPORT.md)

C02b má lokálně sestavený samostatný iOS `URLSession` harness pro syntetickou
96MiB dávku, trvalý journal a nejvýše dvě připravené 8MiB části. Další krok je
podpis, instalace na iPhone a řízené fyzické T043/T047–T050; žádný z nich zatím
není PASS. C02a/C02b receiver není produkční upload server.

Rozbalené podklady v0.4 a v0.5 jsou verzované včetně manifestů. Původní ZIPy
jsou zachované lokálně a ignorované Gitem; profilové workspaces přebírají
dokumenty. Původní v0.5 se kvůli dodatku nepřepisuje.
