"""M2c offline proof: synthetic SQLite only, never launchctl, Tailscale or clipboard."""

import hashlib
import json
import os
import plistlib
import sqlite3
import sys
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from camino.domain.revision_store import RevisionStore, SCHEMA_VERSION
from camino.server.auth import RevocableTokenStore
from camino.server.service_safety import database_lock, private_write, readonly, snapshot
from scripts import camino_service_control as service
from scripts import camino_service_prepare as preparation
from tests.camino_viewer_fixture import ViewerFixture, uid


class CaminoServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.f = ViewerFixture(self.root)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.copies = self.root / "copies"
        self.copies.mkdir(mode=0o700)
        self.auth = RevocableTokenStore(self.root / "owners.sqlite")
        self.auth.add("SYNTHETIC-OWNER-" * 4, label="fixture")
        state = self.f.store.state()
        self.config = dict(metadata_db=str(self.f.store.path), auth_db=str(self.auth.path),
                           media_db=str(self.root / "media.sqlite"), media_root=str(self.root / "originals"),
                           viewer_media_root=str(self.copies), python=sys.executable, code_root=str(service.PROJECT_ROOT),
                           trip_id=self.f.trip.id, server_id=state["server_id"], epoch=state["epoch"])
        private_write(self.runtime / "config.json", json.dumps(self.config).encode())
        self.agents = self.root / "agents"
        self.commands = []

    def runner(self, argv):
        self.commands.append(argv)
        if argv[0] == service.TAILSCALE:
            return SimpleNamespace(returncode=0, stdout="{}", stderr="")
        code = 1 if argv[0] == "/usr/sbin/lsof" or argv[1] == "print" else 0
        return SimpleNamespace(returncode=code, stdout="", stderr="")

    def control(self, action):
        return service.control(action, self.runtime, runner=self.runner, agents=self.agents)

    def test_missing_configuration_is_read_only(self):
        root = self.root / "absent"
        self.assertEqual(service.control("status", root), {"configured": False, "live_checked": False})
        self.assertFalse(root.exists())

    def test_install_is_disabled_create_only_and_idempotent(self):
        self.assertFalse(self.control("install")["started"])
        definition = plistlib.loads((self.agents / (service.LABEL + ".plist")).read_bytes())
        self.assertTrue(definition["KeepAlive"])
        self.assertEqual(definition["ExitTimeOut"], 330)
        self.assertEqual(definition["Umask"], 0o077)
        self.control("install")
        self.assertFalse(any("bootstrap" in x or "enable" in x for x in self.commands))
        self.assertFalse((self.runtime / "readers.sqlite").exists())

    def test_foreign_definition_cannot_be_overwritten_or_stopped(self):
        self.agents.mkdir()
        path = self.agents / (service.LABEL + ".plist")
        private_write(path, b"foreign")
        for action in ("install", "start", "stop"):
            with self.assertRaises(ValueError):
                self.control(action)
        self.assertEqual(path.read_bytes(), b"foreign")
        self.assertFalse(any("bootout" in x for x in self.commands))

    def test_exact_legacy_definition_is_preserved_and_upgraded(self):
        self.agents.mkdir()
        config = service.load_config(self.runtime)
        legacy = plistlib.loads(service.service_plist(self.runtime, config))
        legacy["EnvironmentVariables"].pop("TERM")
        original = plistlib.dumps(legacy, sort_keys=True)
        path = self.agents / (service.LABEL + ".plist")
        private_write(path, original)
        self.control("install")
        self.assertEqual((self.runtime / "launchagent-before-term.plist").read_bytes(), original)
        self.assertEqual(plistlib.loads(path.read_bytes())["EnvironmentVariables"]["TERM"], "dumb")
        self.control("install")
        self.assertFalse(any("bootstrap" in x for x in self.commands))

    def test_identity_path_privacy_and_alias_checks(self):
        for updates in ({"epoch": uid(999)}, {"auth_db": self.config["metadata_db"]},
                        {"viewer_media_root": self.config["media_root"]}, {"python": "/private/tmp/no-python"}):
            with patch.object(service.json, "loads", return_value={**self.config, **updates}):
                with self.assertRaises((ValueError, OSError)):
                    service.load_config(self.runtime)
        os.chmod(self.runtime / "config.json", 0o644)
        with self.assertRaises(ValueError):
            self.control("status")

    def test_busy_legacy_writer_and_loaded_service_prevent_mutation(self):
        def busy(argv):
            return SimpleNamespace(returncode=0, stdout="1234", stderr="")
        with self.assertRaises(ValueError):
            service.control("enable-viewer", self.runtime, runner=busy, agents=self.agents)
        self.assertFalse((self.runtime / "readers.sqlite").exists())
        def open_db(argv):
            return SimpleNamespace(returncode=0 if argv[0].endswith("lsof") else 1, stdout="", stderr="")
        with self.assertRaises(ValueError):
            service.control("enable-viewer", self.runtime, runner=open_db, agents=self.agents)

    def test_single_writer_lock_and_no_symlink_follow(self):
        with database_lock(self.f.store.path):
            with self.assertRaises(BlockingIOError):
                with database_lock(self.f.store.path):
                    self.fail("second lock acquired")
        path = self.root / "other.sqlite"
        path.with_suffix(".sqlite.service-lock").symlink_to(self.f.store.path)
        with self.assertRaises(OSError):
            with database_lock(path):
                self.fail("followed symlink")

    def test_snapshot_contains_committed_wal_and_verified_receipt(self):
        connection = sqlite3.connect(self.f.store.path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE wal_proof (value TEXT)")
        connection.execute("INSERT INTO wal_proof VALUES ('synthetic')")
        connection.commit()
        try:
            target = snapshot(self.f.store.path, self.root / "snapshots")
            copy = readonly(target)
            try:
                self.assertEqual(copy.execute("SELECT value FROM wal_proof").fetchone(), ("synthetic",))
            finally:
                copy.close()
            receipt = json.loads(target.with_suffix(".receipt.json").read_text())
            self.assertEqual(receipt["sha256"], hashlib.sha256(target.read_bytes()).hexdigest())
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        finally:
            connection.close()

    def test_upgrade_snapshot_precedes_schema_change_and_preserves_identity(self):
        with self.f.store._connection() as connection:
            connection.execute("DROP TABLE viewer_permissions")
            connection.execute("PRAGMA user_version=1")
        before = self.f.store.state()
        self.control("enable-viewer")
        copies = list((self.root / "pre-upgrade-snapshots").glob("*.sqlite"))
        self.assertEqual(len(copies), 1)
        copy = readonly(copies[0])
        try:
            self.assertEqual(copy.execute("PRAGMA user_version").fetchone()[0], 1)
        finally:
            copy.close()
        self.assertEqual(self.f.store.state(), before)
        with self.f.store._connection() as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)

    def test_failed_snapshot_does_not_upgrade_or_grant(self):
        with self.f.store._connection() as connection:
            connection.execute("PRAGMA user_version=1")
        with patch.object(service, "snapshot_before_upgrade", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.control("enable-viewer")
        self.assertFalse((self.runtime / "readers.sqlite").exists())
        with self.f.store._connection() as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_explicit_grant_revoke_regrant_no_immutable_rewrite_or_secret_report(self):
        with self.f.store._connection() as connection:
            original = connection.execute("SELECT body FROM trips").fetchall()
            requests = connection.execute("SELECT request_body FROM accepted_operations").fetchall()
        result = self.control("enable-viewer")
        token = service.active_reader(self.runtime)
        self.assertIsNotNone(token)
        self.assertNotIn(token, json.dumps(result))
        self.assertFalse(self.auth.authenticate("Bearer " + token))
        readers = RevocableTokenStore(self.runtime / "readers.sqlite")
        self.assertTrue(readers.authenticate("Bearer " + token))
        self.assertEqual(len(self.f.store.viewer_snapshot(self.f.trip.id)["moments"]), 1)
        self.control("disable-viewer")
        self.assertFalse(readers.authenticate("Bearer " + token))
        self.assertEqual(self.f.store.viewer_snapshot(self.f.trip.id)["moments"], [])
        self.assertEqual(self.f.store.viewer_safe_ids(self.f.trip.id), ())
        self.control("enable-viewer")
        self.assertNotEqual(service.active_reader(self.runtime), token)
        self.assertFalse(readers.authenticate("Bearer " + token))
        self.assertEqual(len(list(self.runtime.glob("reader-token-*.txt"))), 2)
        with self.f.store._connection() as connection:
            self.assertEqual(connection.execute("SELECT body FROM trips").fetchall(), original)
            self.assertEqual(connection.execute("SELECT request_body FROM accepted_operations").fetchall(), requests)
        self.f.lock()
        self.assertEqual(self.f.store.viewer_snapshot(self.f.trip.id)["moments"], [])

    def test_unknown_trip_and_nonboolean_permission_fail(self):
        with self.assertRaises(Exception):
            self.f.store.set_viewer_permission(uid(999), enabled=True)
        with self.assertRaises(ValueError):
            self.f.store.set_viewer_permission(self.f.trip.id, enabled="yes")

    def test_failure_during_token_creation_keeps_trip_closed(self):
        with patch.object(RevocableTokenStore, "add", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.control("enable-viewer")
        self.assertEqual(self.f.store.viewer_safe_ids(self.f.trip.id), ())

    def test_start_stop_are_exact_and_do_not_change_network_or_credentials(self):
        self.control("install")
        with patch.object(service.socket, "socket"):
            self.assertTrue(self.control("start")["start_requested"])
        self.control("stop")
        self.assertTrue(any("bootstrap" in command for command in self.commands))
        network = [c for c in self.commands if c[0] == service.TAILSCALE]
        self.assertTrue(network)
        self.assertTrue(all(c[2:] == ["status", "--json"] for c in network))
        self.assertFalse((self.runtime / "readers.sqlite").exists())

    def test_unknown_network_or_funnel_blocks_start_before_migration(self):
        self.control("install")
        for value in ('{"AllowFunnel":{"mac:443":true}}', "[]", "invalid"):
            def runner(argv):
                if argv[0] == service.TAILSCALE:
                    return SimpleNamespace(returncode=0, stdout=value, stderr="")
                return self.runner(argv)
            with patch.object(service, "prepare_metadata") as prepare:
                with self.assertRaises(ValueError):
                    service.control("start", self.runtime, runner=runner, agents=self.agents)
                prepare.assert_not_called()

    def test_runtime_needs_explicit_grant_even_if_imported_trip_is_enabled(self):
        config = service.load_config(self.runtime)
        self.assertFalse(service.viewer_granted(config))
        self.control("enable-viewer")
        self.assertTrue(service.viewer_granted(config))
        self.control("disable-viewer")
        self.assertFalse(service.viewer_granted(config))

    def test_registry_uses_confirmation_and_status_is_read_only(self):
        from app.workflows.commands import WORKFLOW_COMMANDS
        commands = [c for c in WORKFLOW_COMMANDS if c.command_id.startswith("camino_service_")]
        self.assertEqual(len(commands), 11)
        for command in commands:
            writes = command.command_id not in ("camino_service_status", "camino_service_network_status")
            self.assertEqual(command.requires_confirmation, writes)
            self.assertEqual("--confirm" in command.argv, writes)

    def test_foreign_loaded_job_is_not_stopped_even_with_matching_disk_plist(self):
        self.control("install")
        calls = []
        def runner(argv):
            calls.append(argv)
            return SimpleNamespace(returncode=0, stdout="path = /foreign/service.plist\nstate = running", stderr="")
        with self.assertRaises(ValueError):
            service.control("stop", self.runtime, runner=runner, agents=self.agents)
        self.assertEqual(len(calls), 1)
        self.assertFalse(service.control("status", self.runtime, runner=runner, agents=self.agents)["running"])

    def preparation_state(self):
        return {**self.config, "phase": "stopped", "token_path": str(self.root / "archived-token.txt")}

    def test_archive_audit_hashes_media_without_migration_or_private_content(self):
        self.f.upload(30, "audio", b"synthetic audio")
        before = self.f.store.path.read_bytes()
        result = preparation.archive_evidence(self.preparation_state())
        self.assertEqual(result["verified_assets"], 1)
        self.assertEqual(result["verified_bytes"], 15)
        self.assertNotIn("TAJNA", json.dumps(result))
        self.assertEqual(self.f.store.path.read_bytes(), before)
        path = self.root / "originals/objects" / (uid(30) + ".bin")
        path.write_bytes(b"wrong")
        with self.assertRaises(ValueError):
            preparation.archive_evidence(self.preparation_state())

    def test_archive_audit_does_not_guess_between_two_populated_trips(self):
        with self.f.store._connection() as db:
            db.execute("INSERT INTO trips VALUES (?,?)", (uid(80), "{}"))
            db.execute("UPDATE moments SET trip_id=? WHERE id=?", (uid(80), self.f.private.id))
        with self.assertRaises(ValueError):
            preparation.archive_evidence(self.preparation_state())

    def test_prepare_preserves_restore_flags_and_creates_no_reader_or_listener(self):
        destination = self.root / "prepared-service"
        with self.auth._open() as db:
            db.execute("UPDATE owner_tokens SET revoked_at='synthetic-revocation'")
        self.f.store.rotate_epoch_for_restore()
        before = self.f.store.state()
        code = self.root / "release-code"
        (code / "scripts").mkdir(parents=True)
        (code / "scripts/camino_service_control.py").write_text("# synthetic")
        def environment(path):
            (path / "bin").mkdir(parents=True)
            (path / "bin/python").symlink_to(sys.executable)
        with patch.object(preparation, "_load_state", return_value=self.preparation_state()), \
             patch.object(preparation, "_validate_state_paths"), \
             patch.object(service, "require_private_network"), \
             patch.object(service, "offline", return_value=nullcontext()), \
             patch.object(preparation, "release_checkout", return_value=code), \
             patch.object(preparation.venv, "EnvBuilder") as builder, \
             patch.object(preparation.subprocess, "run") as command:
            builder.return_value.create.side_effect = environment
            result = preparation.prepare(root=destination)
        self.assertTrue(result["prepared"])
        self.assertTrue(result["exports_blocked"])
        self.assertFalse(result["installed"])
        self.assertEqual(self.f.store.state(), before)
        self.assertEqual(len(list((destination / "preparation-snapshots").glob("*/*.receipt.json"))), 3)
        self.assertFalse((destination / "readers.sqlite").exists())
        self.assertTrue(self.auth.authenticate("Bearer " + (destination / "owner-token.txt").read_text()))
        self.assertNotIn((destination / "owner-token.txt").read_text(), json.dumps(result))
        self.assertEqual(command.call_count, 2)
        self.assertTrue(all(call.args[0][1:3] == ["-m", "pip"] for call in command.call_args_list))


if __name__ == "__main__":
    unittest.main()
