from __future__ import annotations

import io
import json
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from app.family_calendar_delivery_config import load_family_calendar_delivery_config
from app.family_calendar_delivery_config_transition import (
    DELIVERY_CONFIG_DRY_RUN_CONFIRMATION,
    DeliveryConfigTransitionError,
    apply_family_calendar_delivery_config_dry_run,
    plan_family_calendar_delivery_config_dry_run,
)
from app.file_persistence import lock_path_for
from scripts.family_calendar_delivery_config_enable_dry_run import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADDRESSES = (
    "one@example.invalid",
    "two@example.invalid",
    "three@example.invalid",
    "four@example.invalid",
)
SENDER_ADDRESS = "sender@example.invalid"


class FamilyCalendarDeliveryConfigTransitionTests(unittest.TestCase):
    def test_plan_is_read_only_redacted_and_changes_only_mode(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_config(Path(temp_dir))
            original = path.read_bytes()
            entries_before = tuple(sorted(path.parent.iterdir()))

            plan = plan_family_calendar_delivery_config_dry_run(path=path)

            self.assertEqual(plan.source_config.mode.value, "disabled")
            self.assertEqual(plan.target_config.mode.value, "dry_run")
            self.assertEqual(plan.source_config.smtp_provider, plan.target_config.smtp_provider)
            self.assertEqual(
                plan.source_config.sender_address,
                plan.target_config.sender_address,
            )
            self.assertEqual(plan.source_config.recipients, plan.target_config.recipients)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(tuple(sorted(path.parent.iterdir())), entries_before)
            self.assertEqual(
                plan.safe_document(),
                {
                    "status": "preview",
                    "schema": 2,
                    "from_mode": "disabled",
                    "to_mode": "dry_run",
                    "recipient_count": 4,
                },
            )
            _assert_redacted(self, repr(plan), path)

    def test_wrong_confirmation_changes_nothing_and_creates_no_lock(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_config(Path(temp_dir))
            original = path.read_bytes()
            plan = plan_family_calendar_delivery_config_dry_run(path=path)

            with self.assertRaisesRegex(DeliveryConfigTransitionError, "confirmation"):
                apply_family_calendar_delivery_config_dry_run(
                    plan,
                    confirmation="yes",
                )

            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(lock_path_for(path).exists())

    def test_exact_confirmation_atomically_enables_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_config(Path(temp_dir))
            plan = plan_family_calendar_delivery_config_dry_run(path=path)

            result = apply_family_calendar_delivery_config_dry_run(
                plan,
                confirmation=DELIVERY_CONFIG_DRY_RUN_CONFIRMATION,
            )
            config = load_family_calendar_delivery_config(path)

            self.assertEqual(result.config, config)
            self.assertEqual(config.mode.value, "dry_run")
            self.assertEqual(config.sender_address, SENDER_ADDRESS)
            self.assertEqual(
                tuple(recipient.address for recipient in config.recipients),
                ADDRESSES,
            )
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(lock_path_for(path).stat().st_mode), 0o600)
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])
            _assert_redacted(self, repr(result), path)

    def test_changed_source_is_not_overwritten_after_planning(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_config(Path(temp_dir))
            plan = plan_family_calendar_delivery_config_dry_run(path=path)
            changed = _document(mode="disabled")
            changed["sender_address"] = "changed@example.invalid"
            changed_text = json.dumps(changed)
            path.write_text(changed_text, encoding="utf-8")
            path.chmod(0o600)

            with self.assertRaisesRegex(DeliveryConfigTransitionError, "changed"):
                apply_family_calendar_delivery_config_dry_run(
                    plan,
                    confirmation=DELIVERY_CONFIG_DRY_RUN_CONFIRMATION,
                )

            self.assertEqual(path.read_text(encoding="utf-8"), changed_text)

    def test_already_dry_run_insecure_and_linked_configs_fail_closed(self) -> None:
        cases = ("already_dry_run", "unsafe_permissions", "symlink")
        for case in cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
                    root = Path(temp_dir)
                    private_source = None
                    if case == "symlink":
                        private_dir = root / "family"
                        private_dir.mkdir(mode=0o700)
                        private_source = root / "private-source.json"
                        private_source.write_text(
                            json.dumps(_document(mode="disabled")),
                            encoding="utf-8",
                        )
                        private_source.chmod(0o600)
                        path = private_dir / "notification_config.json"
                        path.symlink_to(private_source)
                    else:
                        path = _write_config(
                            root,
                            mode="dry_run" if case == "already_dry_run" else "disabled",
                        )
                    if case == "unsafe_permissions":
                        path.chmod(0o644)

                    with self.assertRaises(DeliveryConfigTransitionError) as raised:
                        plan_family_calendar_delivery_config_dry_run(path=path)

                    _assert_redacted(self, str(raised.exception), path)
                    self.assertFalse(lock_path_for(path).exists())
                    if private_source is not None:
                        self.assertTrue(path.is_symlink())
                        self.assertEqual(
                            json.loads(private_source.read_text(encoding="utf-8"))["mode"],
                            "disabled",
                        )

    def test_two_processes_apply_one_plan_exactly_once(self) -> None:
        script = """
import sys
import time
from pathlib import Path
from app.family_calendar_delivery_config_transition import (
    DELIVERY_CONFIG_DRY_RUN_CONFIRMATION,
    DeliveryConfigTransitionError,
    apply_family_calendar_delivery_config_dry_run,
    plan_family_calendar_delivery_config_dry_run,
)

path = Path(sys.argv[1])
ready = Path(sys.argv[2])
gate = Path(sys.argv[3])
plan = plan_family_calendar_delivery_config_dry_run(path=path)
ready.write_text("ready", encoding="utf-8")
while not gate.exists():
    time.sleep(0.01)
try:
    apply_family_calendar_delivery_config_dry_run(
        plan,
        confirmation=DELIVERY_CONFIG_DRY_RUN_CONFIRMATION,
    )
except DeliveryConfigTransitionError:
    print("failed")
else:
    print("applied")
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            path = _write_config(root)
            gate = root / "gate"
            ready_paths = (root / "ready-a", root / "ready-b")
            processes = [
                subprocess.Popen(
                    [sys.executable, "-c", script, str(path), str(ready), str(gate)],
                    cwd=PROJECT_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for ready in ready_paths
            ]
            deadline = time.monotonic() + 10
            while not all(ready.exists() for ready in ready_paths):
                if time.monotonic() >= deadline:
                    self.fail("Transition workers did not reach the apply gate.")
                time.sleep(0.01)
            gate.write_text("go", encoding="utf-8")
            outputs = [process.communicate(timeout=20) for process in processes]

            for process, (_stdout, stderr) in zip(processes, outputs, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(
                sorted(stdout.strip() for stdout, _stderr in outputs),
                ["applied", "failed"],
            )
            self.assertEqual(load_family_calendar_delivery_config(path).mode.value, "dry_run")

    def test_cli_previews_then_applies_with_redacted_output(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            path = _write_config(Path(temp_dir))
            original = path.read_bytes()
            preview_output = io.StringIO()

            preview_exit = main(
                ["--path", str(path)],
                output=preview_output,
            )

            self.assertEqual(preview_exit, 0)
            self.assertEqual(json.loads(preview_output.getvalue())["status"], "preview")
            self.assertEqual(path.read_bytes(), original)
            _assert_redacted(self, preview_output.getvalue(), path)

            apply_output = io.StringIO()
            apply_exit = main(
                [
                    "--path",
                    str(path),
                    "--apply",
                    "--confirmation",
                    DELIVERY_CONFIG_DRY_RUN_CONFIRMATION,
                ],
                output=apply_output,
            )

            self.assertEqual(apply_exit, 0)
            self.assertEqual(
                json.loads(apply_output.getvalue()),
                {
                    "status": "applied",
                    "schema": 2,
                    "mode": "dry_run",
                    "recipient_count": 4,
                },
            )
            _assert_redacted(self, apply_output.getvalue(), path)


def _document(*, mode: str) -> dict[str, object]:
    return {
        "schema_version": 2,
        "mode": mode,
        "smtp_provider": "icloud",
        "sender_address": SENDER_ADDRESS,
        "recipients": [
            {"recipient_id": f"recipient-{index}", "address": address}
            for index, address in enumerate(ADDRESSES, start=1)
        ],
    }


def _write_config(root: Path, *, mode: str = "disabled") -> Path:
    private_dir = root / "family"
    private_dir.mkdir(mode=0o700)
    path = private_dir / "notification_config.json"
    path.write_text(json.dumps(_document(mode=mode)), encoding="utf-8")
    path.chmod(0o600)
    return path


def _assert_redacted(
    test_case: unittest.TestCase,
    visible: str,
    path: Path,
) -> None:
    test_case.assertNotIn("@", visible)
    for value in (*ADDRESSES, SENDER_ADDRESS, "changed@example.invalid", str(path)):
        test_case.assertNotIn(value, visible)


if __name__ == "__main__":
    unittest.main()
