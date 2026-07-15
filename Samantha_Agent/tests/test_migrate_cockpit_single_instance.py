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


TAILSCALE_STATUS = (
    '{"Self":{"DNSName":"samantha.example.ts.net."},'
    '"CertDomains":["samantha.example.ts.net"]}'
)


class MigrateCockpitSingleInstanceTests(unittest.TestCase):
    def test_same_cockpit_process_requires_pid_and_code_stamp_match(self) -> None:
        self.assertTrue(migration.same_cockpit_process(health(42), health(42)))
        self.assertFalse(migration.same_cockpit_process(health(42), health(43)))
        self.assertFalse(migration.same_cockpit_process(health(42), None))

    def test_https_health_uses_system_curl_and_requires_valid_json(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            return completed(args, stdout='{"ok":true,"server":{"pid":42,"code_stamp":"stamp-1"}}')

        result = migration.fetch_https_health("https://samantha.example.ts.net", runner=runner)
        self.assertEqual(result, health(42))
        self.assertEqual(commands[0][0], "/usr/bin/curl")
        self.assertIn("--fail", commands[0])
        self.assertEqual(commands[0][-1], "https://samantha.example.ts.net/api/server/health")

        invalid = migration.fetch_https_health(
            "https://samantha.example.ts.net",
            runner=lambda args: completed(args, stdout="not-json"),
        )
        self.assertIsNone(invalid)

    def test_migration_stops_legacy_service_and_configures_tcp_and_https_proxies(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            if args[-2:] == ["ip", "-4"]:
                return completed(args, stdout="100.64.0.1\n")
            if args[-2:] == ["status", "--json"]:
                return completed(args, stdout=TAILSCALE_STATUS)
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
        self.assertIn(
            ["/tailscale", "serve", "--bg", "--yes", "--https", "443", migration.LOCAL_BASE_URL],
            commands,
        )
        self.assertEqual(result["secure_base_url"], "https://samantha.example.ts.net")
        self.assertFalse(any("bootstrap" in command for command in commands))

    def test_failed_verification_rolls_back_to_preserved_launchd(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            if args[-2:] == ["ip", "-4"]:
                return completed(args, stdout="100.64.0.1\n")
            if args[-2:] == ["status", "--json"]:
                return completed(args, stdout=TAILSCALE_STATUS)
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
        self.assertIn(["/tailscale", "serve", "--https=443", "off"], commands)
        self.assertTrue(any(command[:2] == ["launchctl", "bootstrap"] for command in commands))
        self.assertTrue(any(command[:2] == ["launchctl", "kickstart"] for command in commands))

    def test_already_single_instance_adds_and_verifies_https_without_launchctl(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            if args[-2:] == ["status", "--json"]:
                return completed(args, stdout=TAILSCALE_STATUS)
            return completed(args, stdout="100.64.0.1\n")

        with patch.object(migration, "tailscale_binary", return_value=Path("/tailscale")):
            result = migration.migrate_to_single_instance(
                runner=runner,
                health_loader=lambda url: health(42),
                wait_loader=lambda _url: health(42),
            )

        self.assertEqual(result["status"], "already_single_https_ready")
        self.assertIn(
            ["/tailscale", "serve", "--bg", "--yes", "--https", "443", migration.LOCAL_BASE_URL],
            commands,
        )
        self.assertFalse(any(command and command[0] == "launchctl" for command in commands))

    def test_missing_tailscale_dns_name_fails_before_serve_changes(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            if args[-2:] == ["ip", "-4"]:
                return completed(args, stdout="100.64.0.1\n")
            if args[-2:] == ["status", "--json"]:
                return completed(args, stdout='{"Self":{}}')
            return completed(args)

        with patch.object(migration, "tailscale_binary", return_value=Path("/tailscale")):
            with self.assertRaisesRegex(migration.MigrationError, "DNS jméno"):
                migration.migrate_to_single_instance(runner=runner, health_loader=lambda _url: health(42))

        self.assertFalse(any("serve" in command for command in commands))

    def test_disabled_https_certificates_fail_before_serve_changes(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            if args[-2:] == ["ip", "-4"]:
                return completed(args, stdout="100.64.0.1\n")
            if args[-2:] == ["status", "--json"]:
                return completed(
                    args,
                    stdout='{"Self":{"DNSName":"samantha.example.ts.net."},"CertDomains":null}',
                )
            return completed(args)

        with patch.object(migration, "tailscale_binary", return_value=Path("/tailscale")):
            with self.assertRaisesRegex(migration.MigrationError, "nejsou v tailnetu povolené"):
                migration.migrate_to_single_instance(runner=runner, health_loader=lambda _url: health(42))

        self.assertFalse(any("serve" in command for command in commands))

    def test_existing_single_instance_removes_https_when_verification_fails(self) -> None:
        commands: list[list[str]] = []

        def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
            commands.append(args)
            if args[-2:] == ["ip", "-4"]:
                return completed(args, stdout="100.64.0.1\n")
            if args[-2:] == ["status", "--json"]:
                return completed(args, stdout=TAILSCALE_STATUS)
            return completed(args)

        with patch.object(migration, "tailscale_binary", return_value=Path("/tailscale")):
            with self.assertRaisesRegex(migration.MigrationError, "HTTPS Cockpit"):
                migration.migrate_to_single_instance(
                    runner=runner,
                    health_loader=lambda _url: health(42),
                    wait_loader=lambda _url: None,
                )

        self.assertIn(["/tailscale", "serve", "--https=443", "off"], commands)
        self.assertFalse(any(command and command[0] == "launchctl" for command in commands))


if __name__ == "__main__":
    unittest.main()
