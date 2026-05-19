#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
AUDIO_DIR="$ROOT_DIR/audio"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$AUDIO_DIR"

make_sample() {
  local filename="$1"
  local rate="$2"
  local text="$3"
  local aiff_path="$TMP_DIR/${filename%.m4a}.aiff"
  local out_path="$AUDIO_DIR/$filename"

  say -v Zuzana -r "$rate" -o "$aiff_path" "$text"
  afconvert -f m4af -d aac "$aiff_path" "$out_path"
}

make_sample "01_short_prompt_slow.m4a" 145 "Jestli me uz znas, jdeme objevovat, tak klikni na lupu."
make_sample "02_short_prompt_medium.m4a" 165 "Jestli me uz znas, jdeme objevovat, tak klikni na lupu."
make_sample "03_short_prompt_warm.m4a" 152 "Ahoj, jestli me uz znas, klikni na lupu a jdeme objevovat."
make_sample "04_long_intro_slow.m4a" 145 "Ahoj, ja jsem Benzi. Tvuj dedecek je muj pritel a pozadal me, abych ti pomohl objevovat novy svet. Svet, kde se mluvi anglicky. Pojdme na to."
make_sample "05_long_intro_shorter.m4a" 158 "Ahoj, ja jsem Benzi. Tvuj dedecek me pozadal, abych ti pomohl objevovat svet anglictiny. Pojdme na to."
make_sample "06_forest_line_slow.m4a" 148 "Zacneme v mem rodnem lese."
make_sample "07_forest_line_medium.m4a" 164 "Zacneme v mem rodnem lese."
make_sample "08_exit_line_warm.m4a" 150 "Pojd, ukazu ti cestu."

echo "Hotovo: ukazky jsou v $AUDIO_DIR"
