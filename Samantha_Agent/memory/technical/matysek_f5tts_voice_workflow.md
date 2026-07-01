# Matysek English - F5-TTS voice workflow

## Ucel

Tento workflow slouzi jako lokalni tool pro generovani anglickych hlasovych kandidatu pres F5-TTS v projektu Matysek English / MMTX.

Hlavni pouceni z testu 2026-06-02:

- nepouzivat referencni audio delsi nez zhruba 12 sekund,
- `ref_text` musi presne odpovidat pouzitemu referencnimu audiu,
- spojena 20s Bunny reference se lokalne klipovala a vysledek byl spatny,
- 12s reference a puvodni kratka reference znely Mile kvalitativne podobne,
- prakticky baseline pro Bunnyho zustava 7.344s reference z vety `Yes. But we can train all colors in my house. Let's go.`

## Zamcene hlasy z 2026-06-03

Lokalni registr referencnich hlasu:

```text
data/matysek_english/voice_references/locked_forest_journey_20260603/
```

Manifest pro wrapper:

```text
data/matysek_english/voice_references/locked_forest_journey_20260603/voice_reference_manifest.json
```

Aktualni presety:

| Postava | Ref audio | Ref text | Poznamka |
| --- | --- | --- | --- |
| Benji | `benji_reference.mp3` | `Hello! I am Benji. We are going to the lake too.` | Prodlouzena scene 01 reference z existujicich `fable` MP3; 4.920 s. |
| Bunny | `bunny_reference.mp3` | `Yes. But we can train all colors in my house. Let's go.` | Aktualni F5 baseline po testech. |
| Bruno | `bruno_reference.mp3` | `Hello. I am Bruno. We are going to the lake.` | Zamcena uspokojiva `onyx` reference po poslechu; 4.920 s. |
| Fiona | `fiona_reference.mp3` | `Hi. I am Fiona. We are friends too.` | Prodlouzena scene 01 reference: Karen intro + Karen veta pres macOS `say`; 2.760 s. |
| Sunny | `sunny_reference.mp3` | `Hello! I am Sunny. We can go together.` | Zamcena `young_nova` reference po poslechu F5 testu; 3.864 s. |

Poznamka 2026-06-03: Benji, Bruno a Fiona uz nemaji puvodni velmi kratke reference. Bruno byl prepnuty z kovoveho `macOS Daniel` na `onyx`. Sunny byl po odmítnutí `Junior` a poslechu F5 testu zamknuty na `young_nova`.

## Edge Neural voice lock z 2026-06-30

Pro nove produkcni MP3 ve Forest Journey Mila rozhodl pouzit rychlejsi hotove
Edge Neural hlasy z drivejsi PTKL To Be / To Have castingove palety. Lokalni
F5-TTS zustava dulezity kontext a zalozni/specialni cesta, ale neni vychozi
pro kazdou novou vetu, protoze je na Macu Intel casove narocny.

Aktualni rozhodnuti:

| Postava | Hlas | Poznamka |
| --- | --- | --- |
| Bunny | `en-US-AnaNeural` | `cast_b_child_plus_clear`; jasny Bunny kandidat podle Mily. |
| Sunny | `en-US-MichelleNeural` | Z PTKL selected castu, puvodne Lucy. |
| Benji | `en-US-BrianNeural` / korekce Scene 3: `en-US-AndrewNeural` | Brian byl vybran v PTKL castingu, ale pri Scene 3 retestu znel prilis brucive / jako Bruno; v teto scene je nahrazen Andrewem. |
| Fiona | `en-US-JennyNeural` | Z PTKL selected castu, puvodne Kate. |
| Bruno | puvodni brucivy/F5 hlas | Bruno zustava vyjimka, drzet stary charakter. |

Pravidlo pro dalsi MP3:

- nejdrive generovat male davky pres Edge TTS podle teto tabulky,
- Bruno generovat nebo doplnovat opatrne podle puvodni brucive reference,
- pred prepisem produkcniho audia udelat kratky poslechovy balicek a nechat
  Mílu potvrdit.
- Brian nebrat jako definitivni Benji lock bez noveho poslechoveho potvrzeni;
  pro Scene 3 je aktualni prakticka korekce `en-US-AndrewNeural`.

Sunny recast historie:

- `data/matysek_english/voice_references/sunny_reference_young_nova_together_20260603.mp3` je aktualni zamceny zdroj pro `locked_forest_journey_20260603/sunny_reference.mp3`.
- `ref_text`: `Hello! I am Sunny. We can go together.`
- testovaci F5 vystup `sunny_young_nova_ready_to_go_need_20260603_01.mp3` podle Mily zni dobre.
- `Junior` znel zastřene/kovove a nepouzivat jako Sunny baseline.

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

Priklad pro zamceny Bunny preset:

```bash
.venv/bin/python scripts/matysek_f5tts_generate.py \
  --character bunny \
  --gen-text "Hello, I am Bunny. Benji and me we are friends. Are we going together to the lake?" \
  --output-file output_original_short_ref_lake_test_01.mp3
```

Priklad pro Benjiho:

```bash
.venv/bin/python scripts/matysek_f5tts_generate.py \
  --character benji \
  --gen-text "Hello, Bunny. We are going to the lake." \
  --output-file benji_lake_test_01.mp3
```

Overeni bez spusteni F5:

```bash
.venv/bin/python scripts/matysek_f5tts_generate.py \
  --character bunny \
  --gen-text "Hello, Benji." \
  --output-file bunny_dry_run_test.mp3 \
  --dry-run
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
