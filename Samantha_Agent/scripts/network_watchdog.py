from __future__ import annotations

import argparse
import csv
import json
import re
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_DIR / "logs" / "network_watchdog"
VPN_PROCESS_NAMES = ("Tailscale", "WireGuard", "OpenVPN", "NEIKEv2Provider")


@dataclass
class Probe:
    timestamp: str
    elapsed_s: float
    wifi_device: str
    wifi_ipv4: str
    default_interface: str
    default_gateway: str
    utun_count: int
    vpn_processes: str
    dns_nameservers: str
    gateway_ping_ok: bool
    gateway_ping_ms: float | None
    ip_ping_ok: bool
    ip_ping_ms: float | None
    dns_resolve_ok: bool
    dns_resolve_ms: float | None
    openai_https_ok: bool
    openai_http_code: int | None
    openai_connect_ms: float | None
    openai_tls_ms: float | None
    openai_https_ms: float | None
    chatgpt_https_ok: bool
    chatgpt_http_code: int | None
    chatgpt_connect_ms: float | None
    chatgpt_tls_ms: float | None
    chatgpt_https_ms: float | None
    verdict: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Log macOS network stability for Codex/ChatGPT reconnect diagnosis."
    )
    parser.add_argument("--duration", type=int, default=900, help="Run time in seconds.")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between probes.")
    parser.add_argument("--out-dir", type=Path, default=LOG_DIR, help="Directory for logs.")
    parser.add_argument("--once", action="store_true", help="Run a single probe.")
    return parser.parse_args()


def run(command: list[str], timeout: float = 5.0) -> tuple[int, str, str, float]:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        return completed.returncode, completed.stdout.strip(), completed.stderr.strip(), elapsed_ms
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        stdout = (exc.stdout or "").strip() if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "timeout"
        return 124, stdout, stderr, elapsed_ms


def detect_wifi_device() -> str:
    code, stdout, _stderr, _ms = run(["networksetup", "-listallhardwareports"], timeout=3)
    if code == 0:
        lines = stdout.splitlines()
        for pos, line in enumerate(lines):
            if line.strip() in {"Hardware Port: Wi-Fi", "Hardware Port: AirPort"}:
                for follow in lines[pos + 1 : pos + 4]:
                    match = re.match(r"Device:\s*(\S+)", follow.strip())
                    if match:
                        return match.group(1)
    return "en0"


def detect_ipv4(device: str) -> str:
    code, stdout, _stderr, _ms = run(["ipconfig", "getifaddr", device], timeout=2)
    if code == 0 and stdout:
        return stdout.splitlines()[0].strip()

    code, stdout, _stderr, _ms = run(["ifconfig", device], timeout=2)
    if code == 0:
        match = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)\b", stdout)
        if match:
            return match.group(1)
    return ""


def default_route() -> tuple[str, str]:
    code, stdout, _stderr, _ms = run(["route", "-n", "get", "default"], timeout=3)
    if code != 0:
        return "", ""
    gateway = ""
    interface = ""
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("gateway:"):
            gateway = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("interface:"):
            interface = stripped.split(":", 1)[1].strip()
    return interface, gateway


def utun_count() -> int:
    code, stdout, _stderr, _ms = run(["ifconfig"], timeout=3)
    if code != 0:
        return -1
    return sum(1 for line in stdout.splitlines() if line.startswith("utun"))


def active_vpn_processes() -> str:
    active: list[str] = []
    for name in VPN_PROCESS_NAMES:
        code, _stdout, _stderr, _ms = run(["pgrep", "-x", name], timeout=1)
        if code == 0:
            active.append(name)
    return ",".join(active)


def dns_nameservers() -> str:
    code, stdout, _stderr, _ms = run(["scutil", "--dns"], timeout=3)
    if code != 0 or not stdout:
        return ""
    values: list[str] = []
    for line in stdout.splitlines():
        match = re.search(r"nameserver\[\d+\]\s*:\s*(\S+)", line)
        if match and match.group(1) not in values:
            values.append(match.group(1))
    return ",".join(values[:6])


def ping_host(host: str) -> tuple[bool, float | None]:
    code, stdout, stderr, _ms = run(["ping", "-c", "1", "-W", "1000", host], timeout=3)
    text = stdout + "\n" + stderr
    match = re.search(r"time[=<]([0-9.]+)\s*ms", text)
    ping_ms = float(match.group(1)) if match else None
    return code == 0, ping_ms


def resolve_dns() -> tuple[bool, float | None]:
    start = time.monotonic()
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(3.0)
    try:
        socket.getaddrinfo("status.openai.com", 443)
        elapsed_ms = (time.monotonic() - start) * 1000
        return True, elapsed_ms
    except OSError:
        elapsed_ms = (time.monotonic() - start) * 1000
        return False, elapsed_ms
    finally:
        socket.setdefaulttimeout(old_timeout)


def curl_head(url: str) -> tuple[bool, int | None, float | None, float | None, float | None]:
    command = [
        "curl",
        "--ipv4",
        "--head",
        "--silent",
        "--show-error",
        "--max-time",
        "12",
        "--connect-timeout",
        "5",
        "--output",
        "/dev/null",
        "--write-out",
        "%{http_code} %{time_connect} %{time_appconnect} %{time_total}",
        url,
    ]
    code, stdout, _stderr, elapsed_ms = run(command, timeout=14)
    http_code: int | None = None
    connect_ms: float | None = None
    tls_ms: float | None = None
    total_ms: float | None = None
    parts = stdout.split()
    if len(parts) == 4:
        try:
            http_code = int(parts[0])
            connect_ms = float(parts[1]) * 1000
            tls_ms = float(parts[2]) * 1000
            total_ms = float(parts[3]) * 1000
        except ValueError:
            pass
    if total_ms is None:
        total_ms = elapsed_ms
    return code == 0 and http_code is not None and http_code < 500, http_code, connect_ms, tls_ms, total_ms


def classify(
    wifi_ipv4: str,
    ip_ping_ok: bool,
    dns_resolve_ok: bool,
    openai_https_ok: bool,
    chatgpt_https_ok: bool,
) -> str:
    if not wifi_ipv4:
        return "NO_WIFI_IPV4"
    if not ip_ping_ok:
        return "NO_IP_CONNECTIVITY"
    if not dns_resolve_ok:
        return "DNS_FAILURE"
    if not openai_https_ok and not chatgpt_https_ok:
        return "HTTPS_FAILURE"
    if not openai_https_ok:
        return "OPENAI_STATUS_HTTPS_FAILURE"
    if not chatgpt_https_ok:
        return "CHATGPT_HTTPS_FAILURE"
    return "OK"


def collect_probe(start_time: float, wifi_device: str) -> Probe:
    timestamp = datetime.now().isoformat(timespec="seconds")
    elapsed_s = time.monotonic() - start_time
    wifi_ipv4 = detect_ipv4(wifi_device)
    default_interface, default_gateway = default_route()
    current_utun_count = utun_count()
    vpn_processes = active_vpn_processes()
    nameservers = dns_nameservers()
    gateway_ok, gateway_ms = ping_host(default_gateway) if default_gateway else (False, None)
    ip_ok, ip_ms = ping_host("1.1.1.1")
    dns_ok, dns_ms = resolve_dns()
    openai_ok, openai_code, openai_connect_ms, openai_tls_ms, openai_ms = curl_head(
        "https://status.openai.com/"
    )
    chatgpt_ok, chatgpt_code, chatgpt_connect_ms, chatgpt_tls_ms, chatgpt_ms = curl_head(
        "https://chatgpt.com/"
    )
    verdict = classify(wifi_ipv4, ip_ok, dns_ok, openai_ok, chatgpt_ok)
    return Probe(
        timestamp=timestamp,
        elapsed_s=round(elapsed_s, 3),
        wifi_device=wifi_device,
        wifi_ipv4=wifi_ipv4,
        default_interface=default_interface,
        default_gateway=default_gateway,
        utun_count=current_utun_count,
        vpn_processes=vpn_processes,
        dns_nameservers=nameservers,
        gateway_ping_ok=gateway_ok,
        gateway_ping_ms=gateway_ms,
        ip_ping_ok=ip_ok,
        ip_ping_ms=ip_ms,
        dns_resolve_ok=dns_ok,
        dns_resolve_ms=round(dns_ms, 1) if dns_ms is not None else None,
        openai_https_ok=openai_ok,
        openai_http_code=openai_code,
        openai_connect_ms=round(openai_connect_ms, 1) if openai_connect_ms is not None else None,
        openai_tls_ms=round(openai_tls_ms, 1) if openai_tls_ms is not None else None,
        openai_https_ms=round(openai_ms, 1) if openai_ms is not None else None,
        chatgpt_https_ok=chatgpt_ok,
        chatgpt_http_code=chatgpt_code,
        chatgpt_connect_ms=round(chatgpt_connect_ms, 1) if chatgpt_connect_ms is not None else None,
        chatgpt_tls_ms=round(chatgpt_tls_ms, 1) if chatgpt_tls_ms is not None else None,
        chatgpt_https_ms=round(chatgpt_ms, 1) if chatgpt_ms is not None else None,
        verdict=verdict,
    )


def append_csv(path: Path, probe: Probe, write_header: bool) -> None:
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(probe).keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(asdict(probe))


def append_jsonl(path: Path, probe: Probe) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(probe), ensure_ascii=False) + "\n")


def summarize(probes: list[Probe], summary_path: Path) -> None:
    verdict_counts: dict[str, int] = {}
    transitions: list[str] = []
    previous = ""
    for probe in probes:
        verdict_counts[probe.verdict] = verdict_counts.get(probe.verdict, 0) + 1
        if probe.verdict != previous:
            transitions.append(f"- {probe.timestamp}: {previous or 'START'} -> {probe.verdict}")
            previous = probe.verdict

    bad = [probe for probe in probes if probe.verdict != "OK"]
    lines = [
        "# Network watchdog summary",
        "",
        f"Started: {probes[0].timestamp if probes else ''}",
        f"Finished: {probes[-1].timestamp if probes else ''}",
        f"Probes: {len(probes)}",
        "",
        "## Verdict counts",
        "",
    ]
    for verdict, count in sorted(verdict_counts.items()):
        lines.append(f"- {verdict}: {count}")
    lines.extend(["", "## Transitions", ""])
    lines.extend(transitions or ["- No probes collected."])
    lines.extend(["", "## First non-OK probes", ""])
    for probe in bad[:20]:
        lines.append(
            "- "
            f"{probe.timestamp} {probe.verdict} "
            f"ipv4={bool(probe.wifi_ipv4)} "
            f"gateway_ping={probe.gateway_ping_ok} "
            f"ip_ping={probe.ip_ping_ok} "
            f"dns={probe.dns_resolve_ok} "
            f"openai={probe.openai_https_ok}/{probe.openai_http_code}/{probe.openai_https_ms}ms "
            f"chatgpt={probe.chatgpt_https_ok}/{probe.chatgpt_http_code}/{probe.chatgpt_https_ms}ms "
            f"utun={probe.utun_count} vpn={probe.vpn_processes or '-'}"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = args.out_dir / f"network_watchdog_{stamp}.csv"
    jsonl_path = args.out_dir / f"network_watchdog_{stamp}.jsonl"
    summary_path = args.out_dir / f"network_watchdog_{stamp}_summary.md"

    wifi_device = detect_wifi_device()
    start = time.monotonic()
    deadline = start + (0 if args.once else args.duration)
    probes: list[Probe] = []

    print(f"watchdog_csv={csv_path}")
    print(f"watchdog_jsonl={jsonl_path}")
    print(f"watchdog_summary={summary_path}")
    print(f"wifi_device={wifi_device}")

    write_header = True
    while True:
        probe = collect_probe(start, wifi_device)
        probes.append(probe)
        append_csv(csv_path, probe, write_header)
        append_jsonl(jsonl_path, probe)
        write_header = False
        print(
            f"{probe.timestamp} {probe.verdict} "
            f"ip={probe.wifi_ipv4 or '-'} "
            f"gw={probe.gateway_ping_ok}"
            f"{'' if probe.gateway_ping_ms is None else f'/{probe.gateway_ping_ms:.0f}ms'} "
            f"ping={probe.ip_ping_ok}"
            f"{'' if probe.ip_ping_ms is None else f'/{probe.ip_ping_ms:.0f}ms'} "
            f"dns={probe.dns_resolve_ok} "
            f"openai={probe.openai_https_ok}/{probe.openai_http_code}/{probe.openai_https_ms}ms "
            f"chatgpt={probe.chatgpt_https_ok}/{probe.chatgpt_http_code}/{probe.chatgpt_https_ms}ms "
            f"utun={probe.utun_count} vpn={probe.vpn_processes or '-'}",
            flush=True,
        )

        if args.once or time.monotonic() >= deadline:
            break
        sleep_for = max(0.0, min(args.interval, deadline - time.monotonic()))
        time.sleep(sleep_for)

    summarize(probes, summary_path)
    return 0 if all(probe.verdict == "OK" for probe in probes) else 2


if __name__ == "__main__":
    sys.exit(main())
