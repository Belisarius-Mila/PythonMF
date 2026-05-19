#!/bin/zsh
set -euo pipefail

DISK_ROOT="${SAMANTHA_EXTERNAL_DISK:-/Volumes/Falta}"
IMAGE_PATH="$DISK_ROOT/SamanthaSecureBackup.sparsebundle"
VOLUME_NAME="SamanthaSecureBackup"
SIZE="${SAMANTHA_SECURE_BACKUP_SIZE:-500g}"

echo "Samantha secure backup container setup"
echo "Disk: $DISK_ROOT"
echo "Container: $IMAGE_PATH"
echo "Max size: $SIZE"
echo

if [ ! -d "$DISK_ROOT" ]; then
  echo "Chyba: externi disk neni pripojeny: $DISK_ROOT" >&2
  echo "Dostupne svazky:" >&2
  ls /Volumes >&2
  exit 1
fi

if [ -e "$IMAGE_PATH" ]; then
  echo "Chyba: kontejner uz existuje: $IMAGE_PATH" >&2
  echo "Nebudu ho prepisovat." >&2
  exit 1
fi

echo "Zadej nove heslo pro sifrovany kontejner."
echo "Heslo se nebude zobrazovat, neulozi se do souboru a neposilej ho do chatu."
printf "Heslo: "
stty -echo
read -r PASS1
stty echo
printf "\nHeslo znovu: "
stty -echo
read -r PASS2
stty echo
printf "\n"

if [ -z "$PASS1" ]; then
  echo "Chyba: heslo nesmi byt prazdne." >&2
  exit 1
fi

if [ "$PASS1" != "$PASS2" ]; then
  echo "Chyba: hesla se neshoduji." >&2
  exit 1
fi

echo
echo "Vytvarim sifrovany sparsebundle kontejner..."
umask 077
printf "%s" "$PASS1" | hdiutil create \
  -type SPARSEBUNDLE \
  -size "$SIZE" \
  -fs APFS \
  -volname "$VOLUME_NAME" \
  -encryption AES-256 \
  -stdinpass \
  "$IMAGE_PATH"

echo
echo "Pripojuji kontejner..."
printf "%s" "$PASS1" | hdiutil attach -stdinpass "$IMAGE_PATH"

unset PASS1
unset PASS2

echo
echo "Hotovo."
echo "Ocekavany pripojeny svazek: /Volumes/$VOLUME_NAME"
echo
echo "Dalsi krok pro kontrolu bez kopirovani:"
echo "  cd \"$HOME/Desktop/PythonMF\""
echo "  Samantha_Agent/scripts/backup_samantha.command --dry-run --profile recovery"
echo
echo "Ostra zaloha az po kontrole:"
echo "  Samantha_Agent/scripts/backup_samantha.command --execute --profile recovery"
echo
echo "Po zaloze vysun kontejner:"
echo "  hdiutil detach \"/Volumes/$VOLUME_NAME\""
echo
read -r "REPLY?Stiskni Enter pro zavreni okna..."
