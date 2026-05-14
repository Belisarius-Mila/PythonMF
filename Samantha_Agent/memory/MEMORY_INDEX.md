# Memory Index

Tento soubor je rozcestnik dlouhodobe pameti pro Samantha Agent.

## Core

- `samantha_core.md` - zakladni kontext: kdo je Mila, co je Samantha Agent, aktualni stav prostredi a dlouhodoby cil.

## Projects

- `projects/tax_priznani_2025.md` - daňové přiznání 2025, výpočty, checklist formuláře a pravidlo neukládat citlivé údaje.
- `projects/pictnew_vocabulary_image_pipeline.md` - opakovatelný audit a generování obrázků ke slovíčkům FR/IT přes `mapping.json`, `Pict/` a `PictNew/`.
- `projects/tts_edge_audio_tools.md` - české TTS/MP3 nástroje přes edge-tts, dávkový CSV režim a ruční GUI.
- `projects/matysek_english_game_concept.md` - koncept anglické hry pro pětiletého Matýska bez čtení, se scénami, hlasem a příběhem.
- `projects/mmtx_story_hotspot_app.md` - nový směr MMTX: příběhová Pygame hotspot aplikace s houbami, barvami a dynamickým číslováním.
- `projects/multilo_stabilization_cleanup.md` - stabilizace MultiLO návratu do kokpitu, cleanup screenů, pending after callbacky a `tk.Entry` v psacích režimech.

## Handoffs

- `handoffs/chatgpt_handoff_2026_05_14.md` - kompaktní předání po dlouhém ChatGPT vlákně, včetně promptu pro Codex a promptu pro nový ChatGPT chat.
- `handoffs/mmtx_web_handoff_2026_05_14.md` - handoff k webové verzi MMTX v `docs/`, hotovým scénám OwlGarden a HouseBunny, audio strategii a mirroru.

## Technical Rules

- `technical/naming_conventions.md` - názvosloví: Samantha je běžný ChatGPT, Codex je pracovní agent v projektu, Codex CLI je terminálový nástroj.

## Aktualni stav

- Mila buduje osobniho AI agenta Samantha.
- Codex CLI uz funguje v projektu `PythonMF`.
- Node.js, npm, Python 3.12 a OpenAI API key jsou pripravene.
- Skutecne API klice ani jine citlive udaje se do pameti ani do gitu nezapisuji.

## Planovany smer

1. Vytvorit lokalni pamet pro Samantha Agent.
2. Postavit prvni verzi agenta nad OpenAI Agents SDK.
3. Pozdeji pridat RAG nad exporty z ChatGPT.
