"""Bounded read-only probes, returning no mailbox contents, credentials or logs."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
import subprocess
import urllib.request

from app.agent_supervisor import PROJECT, LABELS


def power_probe(*, runner=subprocess.run):
    """Read-only OS capabilities distinguish full wake from maintenance DarkWake."""
    capabilities = runner(["/usr/bin/pmset", "-g", "systemstate"],
        capture_output=True, text=True, timeout=3, check=False)
    match = re.search(r"^Current System Capabilities are: ([A-Za-z ]+)\s*$", capabilities.stdout[:4096], re.MULTILINE)
    if capabilities.returncode or not match:
        return {"state": "unknown"}
    tokens = set(match[1].split())
    if not tokens or tokens - {"CPU", "Graphics", "Audio", "Network", "None"}:
        return {"state": "unknown"}
    state = "awake" if "Graphics" in tokens else "sleeping"
    wake_at = ""
    try:
        wake = runner(["/usr/sbin/sysctl", "-n", "kern.waketime"],
            capture_output=True, text=True, timeout=3, check=False)
        stamp = re.search(r"\bsec\s*=\s*([0-9]{1,12})\s*,", wake.stdout[:1024])
        if wake.returncode == 0 and stamp:
            wake_at = datetime.fromtimestamp(int(stamp[1]), timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError, subprocess.SubprocessError):
        pass  # The persistent transition/gap check also provides a wake grace period.
    return {"state": state, "wake_at": wake_at}


def email_probe():
    from app.email.service_control import EmailServiceController
    from app.email.service import load_settings
    from app.email.continuous_source import IMAPAgentSource
    control = EmailServiceController()
    settings = load_settings(control.settings_path)
    if not settings.enabled:
        return {"enabled": False}
    state = control.status()
    document = control.worker.status()
    sources = []
    for provider in settings.providers:
        key = IMAPAgentSource(provider).key  # configuration only; never scan/login
        source = document.get("sources", {}).get(key, {})
        sources.append({k: source.get(k) for k in ("health", "error", "uidvalidity", "followup_scan")})
    health = state.get("health", {})
    running = False
    pid = health.get("pid")
    if health.get("status") == "running" and type(pid) is int and pid > 0:
        process = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "command="],
            capture_output=True, text=True, timeout=3, check=False)
        running = (process.returncode == 0 and "scripts/continuous_email_agent.py tick" in process.stdout)
    return {**{k: state.get(k) for k in ("enabled", "installed", "owned", "loaded")},
            "sources": sources, "worker_running": running,
            "health": {k: health.get(k) for k in ("status", "started_at", "finished_at")}}


def cockpit_probe():
    # Fixed loopback endpoint; no redirects, caller URL or private business APIs.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open("http://127.0.0.1:8770/api/server/health", timeout=3) as response:
        data = response.read(8193)
        if response.status != 200 or len(data) > 8192:
            return {"reachable": False}
    payload = json.loads(data)
    return {"reachable": payload.get("ok") is True and type(payload.get("server", {}).get("pid")) is int}


def appserver_probe():
    from app.communication.local_runtime import DEFAULT_SOCKET_PATH
    from app.codex_appserver import CodexAppServerClient, UnixSocketAppServerTransport
    from functools import partial
    # Connect/init/model-list only. No process controller, thread/turn or retry.
    factory = partial(UnixSocketAppServerTransport, socket_path=DEFAULT_SOCKET_PATH, timeout=3)
    with CodexAppServerClient(transport_factory=factory, timeout=3) as client:
        models = client.list_models()
    return {"reachable": bool(models)}


def autosave_probe():
    from scripts.autosave_status import autosave_status
    status = autosave_status()
    return {"watcher_count": status.watcher_count, "latest_modified_at": status.latest_modified_at,
            "last_error": bool(status.last_error)}


def storage_probe():
    import shutil
    return {"free_gib": shutil.disk_usage(PROJECT).free / 1024**3}


PROBES = {"email": email_probe, "cockpit": cockpit_probe, "appserver": appserver_probe,
          "autosave": autosave_probe, "storage": storage_probe, "power": power_probe}


def collect(*, probes=None):
    result = {}
    selected = PROBES if probes is None else probes
    if "power" in selected:
        try:
            result["power"] = selected["power"]()
        except Exception:
            result["power"] = {"state": "unknown"}
        if result["power"].get("state") != "awake":
            return result  # No network probes or sends during maintenance wake/uncertainty.
    for identity in LABELS:
        try:
            result[identity] = selected[identity]()
        except Exception:
            # Exception messages may contain secrets, URLs or process arguments.
            result[identity] = {"probe_failed": True}
    return result
