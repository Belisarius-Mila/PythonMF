# Scene 02 — pevná audio knihovna

Scéna přehrává pouze předem připravená MP3 uvedená v `../audio_manifest.js`.
Systémový ani prohlížečový hlas se nepoužívá.

## Pravidla

1. `audio_manifest.js` mapuje každý skutečně mluvený text na jedno MP3.
2. Existující kvalitní MP3 se při opakovaném buildu nepřepisují.
3. Chybějící české stopy používají hlas `cs-CZ-VlastaNeural`.
4. Chybějící anglické slovníkové stopy používají hlas `en-US-JennyNeural`.
5. Žádné API klíče ani citlivá data nejsou součástí scény.

## Struktura

```text
audio/
  english/   — dialog, instrukce, reakce (EN)
  czech/     — nápovědy pro rodiče (CZ)
```

## Rozsah

- 9 dvojjazyčných dialogových vět,
- 12 dvojjazyčných položek slovníčku,
- anglické i české pokyny a nápovědy,
- celkem 55 pevných zvukových referencí.

## English — zachované dialogy

| Soubor | Text |
|--------|------|
| `scene02_01_sunny_no_nuts_en.mp3` | Oh no! I don't have my nuts! |
| `scene02_02_fiona_benji_nuts_en.mp3` | Benji, do you have nuts? |
| `scene02_03_benji_map_en.mp3` | No. I have a map. |
| `scene02_04_fiona_bunny_nuts_en.mp3` | Bunny, do you have nuts? |
| `scene02_05_bunny_carrot_en.mp3` | No. I have a carrot. |
| `scene02_06_bruno_bag_wait_second_en_fix1.mp3` | Wait a second. I have a bag. |
| `scene02_07_bruno_look_inside_friends_en_fix3_balanced.mp3` | It is big. Look inside, friends! |
| `scene02_08_sunny_my_nuts_en_fix1_balanced.mp3` | My nuts! I am so happy! |
| `scene02_09_fiona_ready_en.mp3` | Good. Now we are ready. |

## English — instrukce a nápovědy

| Soubor | Text |
|--------|------|
| `scene02_prompt_tap_benji_en.mp3` | Tap Benji. Does he have nuts? |
| `scene02_prompt_tap_bunny_en.mp3` | Tap Bunny. Does he have nuts? |
| `scene02_prompt_tap_bag_en.mp3` | Tap the bag. |
| `scene02_try_again_en.mp3` | Try again. |
| `scene02_not_yet_tap_benji_en.mp3` | Not yet. Tap Benji. |
| `scene02_not_yet_tap_bunny_en.mp3` | Not yet. Tap Bunny. |
| `scene02_look_at_bag_en.mp3` | Look at the bag. |

## English — slovníček

| Soubor | Text |
|--------|------|
| `scene02_vocab_nuts_en.mp3` | nuts |
| `scene02_vocab_map_en.mp3` | map |
| `scene02_vocab_carrot_en.mp3` | carrot |
| `scene02_vocab_bag_en.mp3` | bag |
| `scene02_vocab_i_have_en.mp3` | I have |
| `scene02_vocab_i_dont_have_en.mp3` | I don't have |
| `scene02_vocab_do_you_have_en.mp3` | Do you have? |
| `scene02_vocab_does_he_have_en.mp3` | Does he have? |
| `scene02_vocab_look_inside_en.mp3` | Look inside |
| `scene02_vocab_ready_en.mp3` | ready |
| `scene02_vocab_wait_en.mp3` | wait |
| `scene02_vocab_happy_en.mp3` | happy |

## Czech — help pro rodiče

| Soubor | Text |
|--------|------|
| `scene02_help_tap_benji_cz.mp3` | Klepni na Benjiho. Má oříšky? |
| `scene02_help_tap_bunny_cz.mp3` | Klepni na Bunny. Má oříšky? |
| `scene02_help_tap_bag_cz.mp3` | Klepni na brašnu. |
| `scene02_dictionary_help_cz.mp3` | Slovníček. Klepni na slovo a uslyšíš ho anglicky. |

## Reprodukovatelný build a kontrola

Z kořene repozitáře:

```bash
python3 MatysekANJ/build_scene02_audio.py
python3 MatysekANJ/build_scene02_audio.py --check
```

První příkaz je bezpečný dry-run. Přepínač `--apply` používá schválenou
projektovou audio capability a vytvoří pouze chybějící MP3; běžný vývojový krok
jej používá jen v povoleném zapisovacím režimu.
