from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from app.family_calendar_delivery_config import DELIVERY_CONFIG_SCHEMA_VERSION
from app.family_calendar_delivery_runner import run_configured_family_calendar_delivery


EVENT_KEY = "person-example:birthday:2026-12-19"
PRIVATE_ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
RECIPIENT_IDS = ("recipient-1", "recipient-2", "recipient-3", "recipient-4")


class FamilyCalendarDeliveryRunnerTests(unittest.TestCase):
    def test_disabled_config_returns_redacted_noop_without_runtime_effects(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_private_config(root)
            state_path, worker_path = _runtime_paths(root)
            calls = {"coordinator": 0, "transport": 0}

            def transport(_record):
                calls["transport"] += 1
                raise AssertionError("disabled runner must not call transport")

            def coordinator(**_kwargs):
                calls["coordinator"] += 1
                transport(None)
                raise AssertionError("disabled runner must not call coordinator")

            for offset in ("D-2", "D-1"):
                with self.subTest(offset=offset):
                    result = run_configured_family_calendar_delivery(
                        event_key=EVENT_KEY,
                        offset=offset,
                        transport=transport,
                        config_path=config_path,
                        state_path=state_path,
                        worker_path=worker_path,
                        coordinator=coordinator,
                    )

                    self.assertEqual(result.status, "disabled")
                    self.assertEqual(result.recipient_count, 4)
                    self.assertFalse(result.attempt_eligible)
                    self.assertFalse(result.coordinator_called)
                    self.assertFalse(result.transport_called)
            self.assertEqual(calls, {"coordinator": 0, "transport": 0})
            self.assertFalse(state_path.exists())
            self.assertFalse(worker_path.exists())
            self.assertFalse(Path(f"{worker_path}.lock").exists())
            self.assertFalse(state_path.parent.exists())

    def test_missing_config_returns_config_error_without_creating_paths(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = root / "config" / "notification_config.json"
            state_path, worker_path = _runtime_paths(root)
            calls = {"coordinator": 0, "transport": 0}

            def transport(_record):
                calls["transport"] += 1
                raise AssertionError("config error must not call transport")

            def coordinator(**_kwargs):
                calls["coordinator"] += 1
                raise AssertionError("config error must not call coordinator")

            result = run_configured_family_calendar_delivery(
                event_key=EVENT_KEY,
                offset="D-1",
                transport=transport,
                config_path=config_path,
                state_path=state_path,
                worker_path=worker_path,
                coordinator=coordinator,
            )

            self.assertEqual(result.status, "config_error")
            self.assertEqual(result.recipient_count, 0)
            self.assertFalse(result.attempt_eligible)
            self.assertEqual(calls, {"coordinator": 0, "transport": 0})
            self.assertFalse(config_path.parent.exists())
            self.assertFalse(state_path.parent.exists())

    def test_corrupt_and_insecure_configs_fail_closed_without_private_values(self) -> None:
        for case in ("corrupt", "insecure"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    root = Path(temp_dir)
                    if case == "corrupt":
                        config_path = _write_private_text(root, "private@example.invalid {not-json")
                    else:
                        config_path = _write_private_config(root)
                        config_path.chmod(0o644)
                    state_path, worker_path = _runtime_paths(root)

                    result = run_configured_family_calendar_delivery(
                        event_key=EVENT_KEY,
                        offset="D-2",
                        transport=_unexpected_transport,
                        config_path=config_path,
                        state_path=state_path,
                        worker_path=worker_path,
                        coordinator=_unexpected_coordinator,
                    )

                    serialized = json.dumps(asdict(result), sort_keys=True)
                    visible = f"{result!r} {serialized}"
                    self.assertEqual(result.status, "config_error")
                    self.assertFalse(result.attempt_eligible)
                    self.assertFalse(result.coordinator_called)
                    self.assertFalse(result.transport_called)
                    self.assertNotIn("@", visible)
                    for private_value in (*PRIVATE_ADDRESSES, *RECIPIENT_IDS, EVENT_KEY):
                        self.assertNotIn(private_value, visible)
                    self.assertFalse(state_path.exists())
                    self.assertFalse(worker_path.exists())
                    self.assertFalse(state_path.parent.exists())

    def test_disabled_result_does_not_expose_addresses_ids_or_message_content(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            result = run_configured_family_calendar_delivery(
                event_key=EVENT_KEY,
                offset="D-2",
                transport=_unexpected_transport,
                config_path=_write_private_config(root),
                state_path=_runtime_paths(root)[0],
                worker_path=_runtime_paths(root)[1],
                coordinator=_unexpected_coordinator,
            )

        visible = f"{result!r} {json.dumps(asdict(result), sort_keys=True)}"
        self.assertNotIn("@", visible)
        for private_value in (*PRIVATE_ADDRESSES, *RECIPIENT_IDS, EVENT_KEY, "subject", "body"):
            self.assertNotIn(private_value, visible)

    def test_dry_run_validates_d2_and_d1_without_runtime_effects(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_private_config(root, mode="dry_run")
            state_path, worker_path = _runtime_paths(root)
            calls = {"coordinator": 0, "transport": 0}

            def transport(_record):
                calls["transport"] += 1
                raise AssertionError("dry run must not call transport")

            def coordinator(**_kwargs):
                calls["coordinator"] += 1
                raise AssertionError("dry run must not call coordinator")

            for offset in ("D-2", "D-1"):
                with self.subTest(offset=offset):
                    result = run_configured_family_calendar_delivery(
                        event_key=EVENT_KEY,
                        offset=offset,
                        transport=transport,
                        config_path=config_path,
                        state_path=state_path,
                        worker_path=worker_path,
                        coordinator=coordinator,
                    )

                    self.assertEqual(result.status, "dry_run")
                    self.assertEqual(result.recipient_count, 4)
                    self.assertTrue(result.attempt_eligible)
                    self.assertFalse(result.coordinator_called)
                    self.assertFalse(result.transport_called)
                    visible = f"{result!r} {json.dumps(asdict(result), sort_keys=True)}"
                    self.assertNotIn("@", visible)
                    for private_value in (*PRIVATE_ADDRESSES, *RECIPIENT_IDS, EVENT_KEY):
                        self.assertNotIn(private_value, visible)

            self.assertEqual(calls, {"coordinator": 0, "transport": 0})
            self.assertFalse(state_path.parent.exists())
            self.assertFalse(Path(f"{worker_path}.lock").exists())

    def test_dry_run_invalid_input_fails_closed_and_stays_redacted(self) -> None:
        private_event_key = "private-person@example.invalid\ninvalid"
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            config_path = _write_private_config(root, mode="dry_run")
            state_path, worker_path = _runtime_paths(root)

            for event_key, offset in ((private_event_key, "D-2"), (EVENT_KEY, "D-3")):
                with self.subTest(event_key=event_key, offset=offset):
                    result = run_configured_family_calendar_delivery(
                        event_key=event_key,
                        offset=offset,
                        transport=_unexpected_transport,
                        config_path=config_path,
                        state_path=state_path,
                        worker_path=worker_path,
                        coordinator=_unexpected_coordinator,
                    )

                    visible = f"{result!r} {json.dumps(asdict(result), sort_keys=True)}"
                    self.assertEqual(result.status, "input_error")
                    self.assertEqual(result.recipient_count, 0)
                    self.assertFalse(result.attempt_eligible)
                    self.assertFalse(result.coordinator_called)
                    self.assertFalse(result.transport_called)
                    self.assertNotIn("@", visible)
                    self.assertNotIn("private-person", visible)
                    self.assertNotIn(EVENT_KEY, visible)

            self.assertFalse(state_path.parent.exists())


def _valid_document(*, mode: str = "disabled") -> dict:
    return {
        "schema_version": DELIVERY_CONFIG_SCHEMA_VERSION,
        "mode": mode,
        "smtp_provider": "icloud",
        "sender_address": "sender@example.invalid",
        "recipients": [
            {"recipient_id": recipient_id, "address": address}
            for recipient_id, address in zip(RECIPIENT_IDS, PRIVATE_ADDRESSES, strict=True)
        ],
    }


def _write_private_config(root: Path, *, mode: str = "disabled") -> Path:
    return _write_private_text(root, json.dumps(_valid_document(mode=mode)))


def _write_private_text(root: Path, content: str) -> Path:
    private_dir = root / "config"
    private_dir.mkdir(mode=0o700)
    path = private_dir / "notification_config.json"
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)
    return path


def _runtime_paths(root: Path) -> tuple[Path, Path]:
    runtime_dir = root / "runtime"
    return runtime_dir / "delivery_state.json", runtime_dir / "delivery_worker"


def _unexpected_transport(_record):
    raise AssertionError("runner must not call transport in this phase")


def _unexpected_coordinator(**_kwargs):
    raise AssertionError("runner must not call coordinator in this phase")


if __name__ == "__main__":
    unittest.main()
