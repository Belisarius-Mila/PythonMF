Nazev: Matysek English - F5-TTS Bunny voice tool checkpoint
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-02

Co se resilo:
- Míla testoval lokalni F5-TTS generovani Bunnyho anglickeho hlasu pro Matysek English / MMTX.
- Puvodni problem byl pad CLI kvuli `torch.xpu` na lokalnim macOS Intel prostredi.
- Po lokalni oprave virtualenvu se generovani rozbehlo a porovnaly se tri Bunny reference: spojena 20s, zkracena 12s a puvodni kratka reference.
- Vznikl git-safe wrapper tool `scripts/matysek_f5tts_generate.py` a technicky workflow zapis `memory/technical/matysek_f5tts_voice_workflow.md`.

Co je hotove:
- Lokalni F5 CLI v `.venv_f5tts2` po docasne oprave `torch.xpu` chyby spousti `f5-tts_infer-cli`.
- Bylo overeno, ze F5 lokalne klipuje referencni audio nad zhruba 12 sekund.
- Spojena 20.136s reference dala spatny vysledek, protoze audio bylo klipnute a `ref_text` uz neodpovidal.
- Zkracena 11.064s reference probehla bez klipovani.
- Puvodni 7.344s reference i 12s reference podle Mily zni kvalitativne podobne; prakticky baseline zatim zustava puvodni kratka reference.
- Wrapper tool umi spustit generovani, nastavit lokalni cache, zmerit cas a odmita reference nad 12 sekund bez explicitniho `--allow-long-ref`.

Co neni hotove:
- Neni definitivne rozhodnuta dlouhodoba hlasova strategie Bunnyho pro vsechny nove Forest Journey sceny.
- Docasna oprava v `.venv_f5tts2` je jen lokalni virtualenv patch a neni zanesena jako reprodukovatelny setup.
- Vygenerovane MP3 jsou zatim pracovni kandidati, ne finalni produkcni assety.

Dalsi krok:
- Pro dalsi Bunny kandidaty pouzit wrapper `scripts/matysek_f5tts_generate.py` s puvodni kratkou referenci, generovat jen male davky vet a rozhodovat poslechem.

Navrhovane dalsi kroky:
- Okamzite: pripravit seznam vsech Bunny vet pro Forest Journey sceny 1-6 a generovat je po kratkych davkach.
- Potom: pokud bude hlas stale nestabilni, rozhodnout mezi zachovanim puvodnich existujicich MP3, precastovanim Bunnyho, nebo precastovanim cele kapitoly.
- Technicky: z docasneho virtualenv patche udelat opakovatelny setup/check skript, pokud se F5-TTS bude pouzivat pravidelne.

Zmenene nebo relevantni soubory:
- `scripts/matysek_f5tts_generate.py`
- `memory/technical/matysek_f5tts_voice_workflow.md`
- `data/matysek_english/voice_references/bunny_long_gifts_scene_we_can_train_all_colors_20260602.mp3`
- `data/matysek_english/voice_references/bunny_reference_12s_20260602.mp3`
- `data/matysek_english/voice_references/bunny_combined_reference_20260602.mp3`
- `data/matysek_english/voice_references/output_original_short_ref_lake_test_01.mp3`
- `data/matysek_english/voice_references/output_12s_ref_lake_test_01.mp3`
- `data/matysek_english/voice_references/output_combined_ref_lake_test_01.mp3`
- Lokalni virtualenv patch: `.venv_f5tts2/lib/python3.11/site-packages/f5_tts/infer/utils_infer.py`

Bezpecnost / neukladat:
- Necommitovat `.venv_f5tts/` ani `.venv_f5tts2/`.
- Necommitovat pracovni MP3 kandidaty bez vyslovneho rozhodnuti, ze patri do hry.
- Neukladat do pameti ani gitu zadne tokeny, API klice, hesla ani soukrome e-maily.
