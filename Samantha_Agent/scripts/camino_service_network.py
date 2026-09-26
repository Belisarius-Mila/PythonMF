#!/usr/bin/env python3
"""Owned private Serve route for the managed Camino archive; no Funnel or grants."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import camino_service_control as service
from scripts import camino_c02b_t043_control as network
from scripts.camino_c05b_private_control import _cockpit_root_healthy
from camino.server.service_safety import private_write

ROUTE = "/camino-api"
PROXY = f"http://127.0.0.1:{service.PORT}"


def state(kind, runner):
    result = runner([service.TAILSCALE, kind, "status", "--json"])
    if result.returncode:
        raise ValueError("network status unavailable")
    value = json.loads(result.stdout)
    if not isinstance(value, dict) or network._funnel_enabled(value):
        raise ValueError("private network verification failed")
    return value


def route_state(value, endpoint):
    # Existing Cockpit endpoint is required. Never create or alter its TLS/TCP.
    handlers = value["Web"][endpoint]["Handlers"]
    if "/" not in handlers:
        raise ValueError("existing Cockpit root required")
    for name, web in value["Web"].items():
        for path in web.get("Handlers", {}):
            if path.rstrip("/") == ROUTE or path.startswith(ROUTE + "/"):
                if name != endpoint or path != ROUTE:
                    raise ValueError("ambiguous Camino route")
    route = handlers.get(ROUTE)
    if route is not None and route != {"Proxy": PROXY}:
        raise ValueError("foreign Camino route")
    return route is not None


def without_route(value, endpoint):
    result = copy.deepcopy(value)
    result["Web"][endpoint]["Handlers"].pop(ROUTE, None)
    return result


def verify_api(base, token, config, http):
    code, health = http(base + "/healthz", token)
    if code != 200 or health.get("scope") != "c05a_private_owner":
        raise ValueError("owner health failed")
    code, remote = http(base + "/api/v1/state", token)
    if code != 200 or any(remote.get(k) != config[k] for k in ("server_id", "epoch")):
        raise ValueError("archive identity differs")
    if http(base + "/healthz", "")[0] != 401:
        raise ValueError("unauthorized access is not rejected")


def control(action, root=service.ROOT, *, runner=service.run_command,
            http=network._http_json, cockpit=_cockpit_root_healthy):
    config = service.load_config(root)
    status = service.control("status", root, runner=runner)
    if not status.get("owned_definition"):
        raise ValueError("owned service required")
    tail = runner([service.TAILSCALE, "status", "--json"])
    if tail.returncode:
        raise ValueError("tailnet unavailable")
    dns = network._dns_name(json.loads(tail.stdout))
    endpoint = dns + ":443"
    before = state("serve", runner)
    state("funnel", runner)
    present = route_state(before, endpoint)
    receipt_path = service.private_path(root / "serve-owner.json")
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    owned = receipt == {"endpoint": endpoint, "proxy": PROXY, "route": ROUTE}
    if present and not owned:
        raise ValueError("route has no matching ownership receipt")
    if action == "enable":
        if not status.get("running"):
            raise ValueError("running service required")
        token = service.private_path(root / "owner-token.txt").read_text().strip()
        verify_api(PROXY, token, config, http)
        if not cockpit(dns):
            raise ValueError("Cockpit root is not healthy")
        if not present:
            if receipt is not None and not owned:
                raise ValueError("foreign ownership receipt")
            private_write(root / ("serve-before-" + uuid4().hex + ".json"), json.dumps(before).encode())
            if receipt is None:
                private_write(receipt_path, json.dumps({"endpoint": endpoint, "proxy": PROXY, "route": ROUTE}).encode())
            service.checked([service.TAILSCALE, "serve", "--yes", "--bg", "--https=443",
                             "--set-path=" + ROUTE, PROXY], runner)
    elif action == "disable" and present:
        service.checked([service.TAILSCALE, "serve", "--yes", "--https=443",
                         "--set-path=" + ROUTE, "off"], runner)
    after = state("serve", runner)
    state("funnel", runner)
    present = route_state(after, endpoint)
    if without_route(before, endpoint) != without_route(after, endpoint):
        raise ValueError("unrelated Serve configuration changed; inspect preserved receipt")
    if (action == "enable" and not present) or (action == "disable" and present):
        raise ValueError("route change not confirmed")
    healthy = False
    if present:
        token = service.private_path(root / "owner-token.txt").read_text().strip()
        verify_api("https://" + dns + ROUTE, token, config, http)
        healthy = True
    if not cockpit(dns):
        raise ValueError("Cockpit root health failed")
    return {"route_present": present, "private_https_checked": healthy,
            "cockpit_healthy": True, "unrelated_routes_preserved": True,
            "funnel_enabled": False, "viewer_granted": status["viewer_granted"],
            "phone_delivery_checked": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "enable", "disable"))
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    if args.action != "status" and not args.confirm:
        parser.error("network changes require explicit confirmation")
    try:
        print(json.dumps(control(args.action), sort_keys=True))
        return 0
    except Exception as error:
        print(json.dumps({"ok": False, "error": type(error).__name__,
                          "next": "Inspect owned service and preserved Serve receipt; never reset Tailscale."}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
