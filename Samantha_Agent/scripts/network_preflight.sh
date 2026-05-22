#!/bin/zsh
set -u

PROJECT_DIR="${PROJECT_DIR:-$HOME/Desktop/PythonMF/Samantha_Agent}"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/network_preflight.log"

mkdir -p "$LOG_DIR" 2>/dev/null || true

timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

log() {
  local message="$1"
  print -r -- "[$(timestamp)] $message" >> "$LOG_FILE" 2>/dev/null || true
}

say() {
  print -r -- "$1"
  log "$1"
}

run_quiet() {
  "$@" >/dev/null 2>&1
}

section() {
  say ""
  say "== $1 =="
}

detect_wifi_device() {
  local device
  device="$(networksetup -listallhardwareports 2>/dev/null | awk '
    /Hardware Port: Wi-Fi|Hardware Port: AirPort/ { found=1; next }
    found && /Device:/ { print $2; exit }
  ')"
  if [[ -z "$device" ]]; then
    device="en0"
  fi
  print -r -- "$device"
}

detect_ipv4() {
  local device="$1"
  local ip_addr
  ip_addr="$(ipconfig getifaddr "$device" 2>/dev/null || true)"
  if [[ -n "$ip_addr" ]]; then
    print -r -- "$ip_addr"
    return 0
  fi

  ip_addr="$(ifconfig "$device" 2>/dev/null | awk '/^[[:space:]]*inet / { print $2; exit }')"
  if [[ -n "$ip_addr" ]]; then
    print -r -- "$ip_addr"
    return 0
  fi

  return 1
}

detect_process() {
  local name="$1"
  if command -v pgrep >/dev/null 2>&1 && pgrep -x "$name" >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

kill_process_if_requested() {
  local name="$1"
  if detect_process "$name"; then
    say "VPN proces bezi: $name"
    if [[ "${SAMANTHA_DISABLE_VPN:-0}" == "1" ]]; then
      if run_quiet killall "$name"; then
        say "Ukonceno: $name"
      else
        say "Nepodarilo se ukoncit bez sudo: $name"
      fi
    fi
  fi
}

ping_check() {
  local label="$1"
  local target="$2"
  if run_quiet ping -c 1 -W 1000 "$target"; then
    say "OK ping $label ($target)"
    return 0
  fi
  say "FAIL ping $label ($target)"
  return 1
}

https_check() {
  local label="$1"
  local target="$2"
  if ! command -v curl >/dev/null 2>&1; then
    say "SKIP HTTPS $label: curl neni dostupny"
    return 1
  fi
  if run_quiet curl --head --silent --show-error --max-time 5 "$target"; then
    say "OK HTTPS $label ($target)"
    return 0
  fi
  say "FAIL HTTPS $label ($target)"
  return 1
}

main() {
  if [[ "${SAMANTHA_PREFLIGHT:-1}" == "0" ]]; then
    exit 0
  fi

  local wifi_device
  wifi_device="$(detect_wifi_device)"

  say "Samantha network preflight: $(timestamp)"

  section "VPN / tunely"
  kill_process_if_requested "Tailscale"
  kill_process_if_requested "WireGuard"
  kill_process_if_requested "OpenVPN"
  kill_process_if_requested "NEIKEv2Provider"

  if [[ "${SAMANTHA_DISABLE_VPN:-0}" == "1" ]]; then
    say "SAMANTHA_DISABLE_VPN=1: pokus o ukonceni znamych VPN procesu probehl."
  else
    say "Bezpecny rezim: VPN/Tailscale pouze detekuji, automaticky je neukoncuji."
  fi

  local utun_count
  utun_count="$(ifconfig 2>/dev/null | grep -c '^utun' || true)"
  say "Aktivni utun rozhrani: $utun_count"

  section "Wi-Fi / IP"
  say "Wi-Fi device: $wifi_device"

  local ip_addr
  ip_addr="$(detect_ipv4 "$wifi_device" || true)"
  if [[ -n "$ip_addr" ]]; then
    say "IP adresa na $wifi_device: $ip_addr"
  else
    say "VAROVANI: $wifi_device nema IPv4 adresu z DHCP."
  fi

  section "Konektivita"
  local net_ok=0
  local dns_ok=0
  ping_check "Cloudflare DNS" "1.1.1.1" && net_ok=1
  ping_check "google.com" "google.com" && dns_ok=1
  https_check "Apple" "https://www.apple.com/" && net_ok=1 && dns_ok=1

  if [[ "$net_ok" == "1" && "$dns_ok" == "1" ]]; then
    say "Vysledek: zakladni internet i DNS vypadaji funkcne."
  elif [[ "$net_ok" == "1" && "$dns_ok" == "0" ]]; then
    say "Vysledek: internet pravdepodobne funguje, problem muze byt DNS."
  else
    say "Vysledek: sit je nestabilni nebo nedostupna. Zkus vypnout VPN/Tailscale, obnovit Wi-Fi/DHCP, pripadne pouzit recovery kartu."
  fi

  say "Log: $LOG_FILE"
}

main "$@"
