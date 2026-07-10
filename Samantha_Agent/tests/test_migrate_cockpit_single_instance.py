from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import migrate_cockpit_single_instance as migration


def completed(args: list[str], returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr=stderr)


def health(pid: int) -> dict[str, object]:
    return {"ok": True, "server": {"pid": pid, "code_stamp": "stamp-1"}}


class MigrateCockpitSingleInstanceTests(unittest.TestCase):
    def test_same_cockpit_process_requires_pid_and_code_stamp_match(self) -> None:
        self.assertTrue(migration.same_cockpit_process(health(42), health(42)))
        self.assertFalse(migration.same_cockpit_process(health(42), health(43)))
        self.assertFalse(migration.same_cockpit_process(health(42), None))

    def test_migration_stops_legacy_service_and_configures_tcp_proxy(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            if args[-2:] == ["ip", "-4"]:
                return completed(args, stdout="100.64.0.1\n")
            return completed(args)

        with patch.object(migration, "tailscale_binary", return_value=Path("/tailscale")):
            result = migration.migrate_to_single_instance(
                runner=runner,
                health_loader=lambda url: health(42) if url == migration.LOCAL_BASE_URL else health(99),
                wait_loader=lambda url: health(42),
            )

        self.assertEqual(result["status"], "single_instance")
        self.assertTrue(any(command[:2] == ["launchctl", "bootout"] for command in commands))
        self.assertIn(
            ["/tailscale", "serve", "--bg", "--yes", "--tcp", "8770", "tcp://127.0.0.1:8770"],
            commands,
        )
        self.assertFalse(any("bootstrap" in command for command in commands))

    def test_failed_verification_rolls_back_to_preserved_launchd(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            if args[-2:] == ["ip", "-4"]:
                return completed(args, stdout="100.64.0.1\n")
            return completed(args)

        with (
            patch.object(migration, "tailscale_binary", return_value=Path("/tailscale")),
            patch("pathlib.Path.exists", return_value=True),
        ):
            with self.assertRaises(migration.MigrationError):
                migration.migrate_to_single_instance(
                    runner=runner,
                    health_loader=lambda url: health(42) if url == migration.LOCAL_BASE_URL else health(99),
                    wait_loader=lambda url: None,
                )

        self.assertIn(["/tailscale", "serve", "--tcp=8770", "off"], commands)
        self.assertTrue(any(command[:2] == ["launchctl", "bootstrap"] for command in commands))
        self.assertTrue(any(command[:2] == ["launchctl", "kickstart"] for command in commands))

    def test_already_single_instance_is_noop(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            return completed(args, stdout="100.64.0.1\n")

        with patch.object(migration, "tailscale_binary", return_value=Path("/tailscale")):
            result = migration.migrate_to_single_instance(
                runner=runner,
                health_loader=lambda url: health(42),
            )

        self.assertEqual(result["status"], "already_single")
        self.assertFalse(any(command and command[0] == "launchctl" for command in commands))


if __name__ == "__main__":
    unittest.main()
