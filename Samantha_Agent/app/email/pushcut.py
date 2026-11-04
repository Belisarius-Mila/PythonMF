"""Static Pushcut notifications with durable attempts and no uncertain resend."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re
import ssl
from uuid import uuid4
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

import certifi

from app.file_persistence import FileLockTimeoutError, exclusive_file_lock
from .continuous_agent import ContinuousEmailAgent


NOTIFICATION_TEXT = "Zkontroluj e-maily v Cockpitu."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_url(value: str, *, webhook: bool = False) -> str:
    if not isinstance(value, str) or any(ord(c) < 33 for c in value):
        raise ValueError("Adresa nesmí obsahovat mezery ani řídicí znaky.")
    try:
        url = urlsplit(value)
        valid = (url.scheme == "https" and bool(url.hostname) and not url.username
                 and not url.password and not url.fragment and url.port in {None, 443})
        if webhook:
            valid = valid and url.hostname == "api.pushcut.io" and not url.query and bool(
                re.fullmatch(r"/[^/]+/notifications/[^/]+", url.path))
        else:
            valid = valid and url.hostname not in {"localhost", "127.0.0.1", "::1"} and url.path == "/emails-to-resolve/" and not url.query
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Zadej celou Pushcut adresu." if webhook else "Zadej HTTPS adresu E-mailů k řešení dostupnou z iPhonu.")
    return value


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def trigger_pushcut(webhook_url: str) -> dict:
    """Plain POST preserves the predefined free-tier text, sound and URL action."""
    _validate_url(webhook_url, webhook=True)
    opener = build_opener(_NoRedirect(), HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    try:
        with opener.open(Request(webhook_url, data=b"", method="POST"), timeout=15) as response:
            return {"status": "accepted" if response.status == 200 else "delivery_unknown"}
    except HTTPError as exc:
        # Never expose the exception URL, body or headers: the path is a credential.
        return {"status": "rejected" if 400 <= exc.code < 500 else "delivery_unknown", "error": f"http_{exc.code}"}
    except Exception:
        return {"status": "delivery_unknown", "error": "network_result_unknown"}


def pushcut_status(worker: ContinuousEmailAgent | None = None) -> dict:
    state = (worker or ContinuousEmailAgent()).status()
    config = state.get("pushcut", {})
    tests = state.get("pushcut_tests", {})
    matching = [test for test in tests.values() if test.get("revision") == config.get("revision")]
    last = max(matching, key=lambda test: test.get("created_at", ""), default={})
    return {"enabled": bool(config.get("enabled")), "configured": bool(config.get("webhook_url")),
            "cockpit_url": config.get("cockpit_url", ""),
            "counts": dict(Counter(event["status"] for event in state.get("notification_hours", {}).values())),
            "last_test_status": "delivery_unknown" if last.get("status") == "sending" else last.get("status", ""),
            "message": NOTIFICATION_TEXT}


class PushcutNotifier:
    def __init__(self, worker: ContinuousEmailAgent | None = None, *, sender=trigger_pushcut):
        self.worker = worker or ContinuousEmailAgent()
        self.sender = sender

    def configure(self, *, webhook_url: str, cockpit_url: str, enabled: bool) -> dict:
        if type(enabled) is not bool:
            raise ValueError("Neplatná volba upozornění.")
        _validate_url(cockpit_url)
        with exclusive_file_lock(self.worker.root / "pushcut_dispatch", timeout=0):
            def update(document):
                old = document.get("pushcut", {})
                url = webhook_url.strip() or old.get("webhook_url", "")
                if url:
                    _validate_url(url, webhook=True)
                elif enabled:
                    raise ValueError("Nejprve vlož adresu notifikace z Pushcutu.")
                changed = (old.get("enabled", False) != enabled or old.get("webhook_url", "") != url
                           or old.get("cockpit_url", "") != cockpit_url)
                if changed:
                    for event in document.get("notification_hours", {}).values():
                        if event["status"] == "pending":
                            event.update(status="skipped", reason="configuration_changed")
                revision = old.get("revision") if old.get("webhook_url") == url and old.get("cockpit_url") == cockpit_url else None
                document["pushcut"] = {"enabled": enabled, "webhook_url": url, "cockpit_url": cockpit_url,
                                       "revision": revision or uuid4().hex}
            self.worker._update(update)
        return pushcut_status(self.worker)

    def _send(self, section: str, key: str, url: str) -> dict:
        self.worker._update(lambda d: d[section][key].update(status="sending", attempted_at=_now()))
        try:
            outcome = self.sender(url)
        except Exception:
            outcome = {"status": "delivery_unknown", "error": "network_result_unknown"}
        status = outcome.get("status") if isinstance(outcome, dict) else "delivery_unknown"
        if status not in {"accepted", "rejected", "delivery_unknown"}:
            status = "delivery_unknown"
        # Store only our own bounded status, never a transport response or secret.
        self.worker._update(lambda d: d[section][key].update(status=status, finished_at=_now()))
        return {"status": status}

    def test(self, *, request_id: str, confirmed: bool) -> dict:
        if confirmed is not True or not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", request_id):
            raise ValueError("Testovací oznámení vyžaduje výslovné spuštění a identitu pokusu.")
        with exclusive_file_lock(self.worker.root / "pushcut_dispatch", timeout=0):
            state = self.worker.status()
            previous = state.get("pushcut_tests", {}).get(request_id)
            if previous:
                return {"status": "delivery_unknown" if previous["status"] == "sending" else previous["status"]}
            url = state.get("pushcut", {}).get("webhook_url", "")
            _validate_url(url, webhook=True)
            revision = state["pushcut"]["revision"]
            self.worker._update(lambda d: d.setdefault("pushcut_tests", {}).__setitem__(request_id, {
                "status": "pending", "created_at": _now(), "revision": revision}))
            return self._send("pushcut_tests", request_id, url)

    def drain(self) -> dict:
        try:
            with exclusive_file_lock(self.worker.root / "pushcut_dispatch", timeout=0):
                state = self.worker.status()
                config = state.get("pushcut", {})
                if not config.get("enabled"):
                    return {"status": "disabled", "accepted": 0}
                url = _validate_url(config.get("webhook_url", ""), webhook=True)
                accepted = 0
                for hour, event in state.get("notification_hours", {}).items():
                    if event["status"] == "sending":
                        self.worker._update(lambda d: d["notification_hours"][hour].update(status="delivery_unknown"))
                        continue
                    if event["status"] != "pending":
                        continue
                    current = self.worker.status()
                    def needs_review(item):
                        return (item.get("status") in {"awaiting_confirmation", "saving"}
                                or (item.get("status") == "archived" and item.get("proposal", {}).get("reply_draft")
                                    and item.get("reply", {}).get("status") != "smtp_sent"))
                    if not any(needs_review(current["items"].get(item_id, {})) for item_id in event["item_ids"]):
                        self.worker._update(lambda d: d["notification_hours"][hour].update(status="skipped", reason="already_reviewed"))
                        continue
                    outcome = self._send("notification_hours", hour, url)
                    accepted += outcome["status"] == "accepted"
                return {"status": "checked", "accepted": accepted}
        except FileLockTimeoutError:
            return {"status": "busy", "accepted": 0}
