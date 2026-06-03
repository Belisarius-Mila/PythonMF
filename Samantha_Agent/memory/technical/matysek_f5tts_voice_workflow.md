# Matysek English - F5-TTS voice workflow

## Ucel

Tento workflow slouzi jako lokalni tool pro generovani anglickych Bunny/Benji kandidatu pres F5-TTS v projektu Matysek English / MMTX.

Hlavni pouceni z testu 2026-06-02:

- nepouzivat referencni audio delsi nez zhruba 12 sekund,
- `ref_text` musi presne odpovidat pouzitemu referencnimu audiu,
- spojena 20s Bunny reference se lokalne klipovala a vysledek byl spatny,
- 12s reference a puvodni kratka reference znely Mile kvalitativne podobne,
- prakticky baseline pro Bunnyho zatim zustava puvodni kratka reference.

## Lokalni prostredi

Aktualni testovane prostredi:

```text
Samantha_Agent/.venv_f5tts2/
```

CLI:

```text
Samantha_Agent/.venv_f5tts2/bin/f5-tts_infer-cli
```

Na Macu Intel je generovani pres CPU pomale. Testovaci veta kolem 9 sekund vystupu trvala radove 6 az 9 minut.

## Wrapper tool

Repo obsahuje wrapper:

```bash
scripts/matysek_f5tts_generate.py
```

Priklad pro puvodni kratkou Bunny referenci:

```bash
.venv/bin/python scripts/matysek_f5tts_generate.py \
  --gen-text "Hello, I am Bunny. Benji and me we are friends. Are we going together to the lake?" \
  --output-file output_original_short_ref_lake_test_01.mp3
```

Wrapper nastavuje lokalni cache:

```text
MPLCONFIGDIR=/private/tmp/matplotlib-f5tts
XDG_CACHE_HOME=/private/tmp/f5tts-cache
```

A pred spustenim odmita referenci nad 12 sekund, pokud neni vedome pouzito `--allow-long-ref`.

## Reference a vysledky z 2026-06-02

Referencni soubory v `data/matysek_english/voice_references/`:

- `bunny_long_gifts_scene_we_can_train_all_colors_20260602.mp3` - puvodni kratka Bunny reference, 7.344 s.
- `bunny_combined_reference_20260602.mp3` - spojena 20.136s reference, F5 ji klipuje; nepouzivat jako baseline.
- `bunny_reference_12s_20260602.mp3` - zkracena 11.064s reference bez klipovani.

Porovnavaci vystupy:

- `output_combined_ref_lake_test_01.mp3` - spatny vysledek kvuli klipovani reference, cas 356.17 s.
- `output_12s_ref_lake_test_01.mp3` - pouzitelny, ale podle Mily kvalita podobna jako original, cas 562.86 s.
- `output_original_short_ref_lake_test_01.mp3` - pouzitelny baseline, cas 401.05 s.

Testovana veta:

```text
Hello, I am Bunny. Benji and me we are friends. Are we going together to the lake?
```

## Zname problemy

Na `torch 2.2.2` lokalni F5-TTS narazil na:

```text
AttributeError: module 'torch' has no attribute 'xpu'
```

Docasna lokalni oprava byla provedena jen v `.venv_f5tts2`:

```text
hasattr(torch, "xpu") and torch.xpu.is_available()
```

Tato uprava je uvnitr virtualenvu a nema se commitovat. Pokud se prostredi obnovi, je lepsi opravu zopakovat instalacnim/setup krokem nebo najit kompatibilni verzi F5-TTS pro macOS Intel.

## Pravidla pouziti

- Nekombinovat ruzne postavy do jedne reference.
- Nepouzivat referenci nad 12 sekund bez vedomeho testu.
- U kazde reference ulozit nebo znat presny `ref_text`.
- Pro finalni herni MP3 delat poslechovy vyber, ne brat prvni generaci automaticky.
- Vygenerovane MP3 v `data/matysek_english/voice_references/` jsou lokalni pracovni vystupy; commitovat jen po vyslovnem rozhodnuti, ze patri do hry.
