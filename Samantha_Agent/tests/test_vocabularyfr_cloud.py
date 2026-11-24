"""Cloud preparation tests use isolated Git repositories and loopback only."""
import http.client
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import time
import unittest

from app import vocabulary_fr_cloud as cloud
from app.vocabulary_fr_hosting import PUBLIC, CLOUD_ORIGIN

PROJECT = Path(__file__).resolve().parents[1]
ORIGIN = "https://fixture-french-pairs.onrender.com"


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo";self.repo.mkdir()
        self.output = Path(self.temp.name) / "release"
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True, stderr=subprocess.DEVNULL).strip()
        self.git = git
        git("init", "-b", "main");git("config", "user.name", "Fixture");git("config", "user.email", "fixture@example.test")
        for name in (cloud.SERVER, cloud.CLOUD, *PUBLIC):
            target = self.repo / name
            if not target.suffix:
                target = target / ("online.html" if name.endswith("vocabulary-fr") else "sample.webp")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("committed public fixture")
        for name in ["Samantha_Agent/.env", "Samantha_Agent/data/private/rooms.sqlite3", "docs/vocabulary-en/index.html"]:
            target = self.repo / name;target.parent.mkdir(parents=True, exist_ok=True);target.write_text("PRIVATE OR UNRELATED")
        git("add", "--", cloud.SERVER, cloud.CLOUD, *PUBLIC);git("commit", "-m", "fixture")
        self.head = git("rev-parse", "HEAD")

    def prepare(self):
        return cloud.prepare_release(repo=self.repo, output=self.output, expected_head=self.head)

    def test_only_committed_allowlist_is_exported_and_reused_without_copying_private_inputs(self):
        self.assertEqual(cloud.PUBLIC, PUBLIC)
        (self.repo / cloud.SERVER).write_text("unapproved working copy")
        value = self.prepare()
        self.assertEqual((self.output / cloud.SERVER).read_text(), "committed public fixture")
        self.assertEqual(self.prepare(), value)
        self.assertFalse((self.output / ".git").exists())
        self.assertFalse((self.output / "Samantha_Agent/.env").exists())
        self.assertFalse((self.output / "Samantha_Agent/data").exists())
        self.assertFalse((self.output / "docs/vocabulary-en").exists())

    def test_unapproved_head_modified_release_and_git_metadata_destination_are_rejected(self):
        with self.assertRaises(ValueError):cloud.prepare_release(repo=self.repo, output=self.output, expected_head="a" * 40)
        with self.assertRaises(ValueError):cloud.prepare_release(repo=self.repo, output=self.repo / ".git/export", expected_head=self.head)
        self.prepare();(self.output / cloud.SERVER).write_text("modified")
        with self.assertRaises(ValueError):self.prepare()

    def test_symlink_in_public_git_tree_cannot_export_a_private_file(self):
        target = self.repo / "docs/vocabulary-fr/private-link";target.symlink_to(self.repo / "Samantha_Agent/.env")
        self.git("add", "--", str(target));self.git("commit", "-m", "unsafe fixture");self.head = self.git("rev-parse", "HEAD")
        with self.assertRaises(ValueError):self.prepare()
        self.assertFalse((self.output / "docs/vocabulary-fr/private-link").exists())

    def test_blueprint_is_paid_single_instance_persistent_manual_and_uses_immutable_export(self):
        # The Blueprint uses JSON syntax, a YAML subset, without another dependency.
        spec = json.loads((PROJECT / "deploy/vocabulary-fr/render.yaml").read_text())["services"][0]
        self.assertEqual(spec["plan"], "0.5c-512mb");self.assertEqual(spec["region"], "frankfurt")
        self.assertEqual(spec["numInstances"], 1);self.assertEqual(spec["autoDeployTrigger"], "off")
        self.assertEqual(spec["disk"], {"name": "vocabulary-fr-games", "mountPath": "/var/data", "sizeGB": 1})
        self.assertIn("$RENDER_GIT_COMMIT", spec["buildCommand"]);self.assertIn("$RENDER_GIT_COMMIT", spec["startCommand"])
        self.assertEqual(spec["healthCheckPath"], "/api/vocabulary-fr/rooms/health")

    def test_reused_export_rejects_injected_files_and_a_truncated_manifest(self):
        value=self.prepare();(self.output/"injected.txt").write_text("unlisted")
        with self.assertRaises(ValueError):self.prepare()
        value['files']={"docs/vocabulary-fr/online.html":value['files']["docs/vocabulary-fr/online.html"]}
        (self.output/'manifest.json').write_text(json.dumps(value))
        with self.assertRaises(ValueError):self.prepare()


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.env = {"RENDER": "true", "RENDER_EXTERNAL_URL": ORIGIN, "PORT": "10000", "VOCABULARY_FR_DATA_DIR": str(self.directory)}

    def test_runtime_configuration_requires_assigned_https_origin_and_existing_persistent_directory(self):
        value = cloud.configuration(self.env)
        self.assertEqual(value, {"origin": ORIGIN, "port": 10000, "directory": self.directory})
        self.assertTrue(CLOUD_ORIGIN.fullmatch(ORIGIN))
        for change in [{"RENDER": "false"}, {"PORT": "0"}, {"PORT": "443"}, {"PORT": "10000;bad"},
                       {"VOCABULARY_FR_DATA_DIR": "relative"}, {"VOCABULARY_FR_DATA_DIR": str(self.directory / "missing")},
                       *[{"RENDER_EXTERNAL_URL": x} for x in ["http://fixture.onrender.com", "https://other.example", ORIGIN + "/", ORIGIN + ":443", ORIGIN + "?x=1", "https://user@fixture.onrender.com"]]]:
            with self.subTest(change=change), self.assertRaises(ValueError):cloud.configuration({**self.env, **change})

    def request(self, port, path, host=None):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        try:
            connection.request("GET", path, headers={"Host": host or ORIGIN.split("//")[1]})
            response = connection.getresponse()
            return response.status, response.read()
        finally:connection.close()

    def test_health_checks_database_and_keeps_host_and_private_route_boundaries(self):
        settings = {**cloud.configuration(self.env), "port": 0}
        server = cloud.create_server(settings, bind="127.0.0.1")
        thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        try:
            port = server.server_port
            status, body = self.request(port, "/api/vocabulary-fr/rooms/health")
            self.assertEqual(status, 200);self.assertEqual(json.loads(body)["protocol"], 1)
            self.assertEqual(self.request(port, "/api/vocabulary-fr/rooms/health", host="foreign.example")[0], 403)
            self.assertEqual(self.request(port, "/api/server/health")[0], 404)
            self.assertEqual(self.request(port, "/.env")[0], 404)
            (self.directory / "rooms.sqlite3").write_bytes(b"corrupt fixture")
            self.assertEqual(self.request(port, "/api/vocabulary-fr/rooms/health")[0], 503)
        finally:server.shutdown();thread.join(3);server.server_close()

    def test_consistent_backup_preserves_active_database_and_never_overwrites_snapshots(self):
        source = self.directory / "rooms.sqlite3"
        with sqlite3.connect(source) as conn:
            conn.execute("CREATE TABLE rooms (id TEXT, body TEXT)")
            conn.execute("INSERT INTO rooms VALUES (?,?)", ("fixture-room", "private fixture access"))
        first = cloud.backup_database(directory=self.directory)
        second = cloud.backup_database(directory=self.directory)
        self.assertNotEqual(first, second);self.assertEqual(first.stat().st_mode & 0o777, 0o600)
        for path in [source, first, second]:
            with sqlite3.connect(path) as conn:self.assertEqual(conn.execute("SELECT * FROM rooms").fetchall(), [("fixture-room", "private fixture access")])

    def test_backup_refuses_a_symlink_destination_without_touching_other_files(self):
        with sqlite3.connect(self.directory / "rooms.sqlite3") as conn:conn.execute("CREATE TABLE rooms (id TEXT)")
        foreign = self.directory / "elsewhere";foreign.mkdir()
        (self.directory / "backups").symlink_to(foreign, target_is_directory=True)
        with self.assertRaises(ValueError):cloud.backup_database(directory=self.directory)
        self.assertEqual(list(foreign.iterdir()), [])

    def test_sigterm_and_restart_keep_database_and_private_access(self):
        with socket.socket() as probe:probe.bind(("127.0.0.1", 0));port = probe.getsockname()[1]
        env = {**os.environ, **self.env, "PORT": str(port)}
        code = "from app import vocabulary_fr_cloud as c; original=c.create_server; c.create_server=lambda settings: original(settings,bind='127.0.0.1'); c.main()"
        def start():
            process = subprocess.Popen([sys.executable, "-c", code, "serve"], cwd=PROJECT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.addCleanup(lambda: process.poll() is None and process.terminate())
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if process.poll() is not None:self.fail(process.communicate()[1].decode())
                try:
                    if self.request(port, "/api/vocabulary-fr/rooms/health")[0] == 200:return process
                except OSError:pass
                time.sleep(.05)
            self.fail("Cloud fixture did not start")
        first = start()
        with sqlite3.connect(self.directory / "rooms.sqlite3") as conn:conn.execute("INSERT INTO rooms VALUES (?,?,?)", ("room-fixture", "request-fixture", "private access fixture"))
        first.terminate();first.wait(5);first.communicate()
        second = start()
        try:
            with sqlite3.connect(self.directory / "rooms.sqlite3") as conn:self.assertEqual(conn.execute("SELECT body FROM rooms WHERE id='room-fixture'").fetchone(), ("private access fixture",))
        finally:second.terminate();second.wait(5);second.communicate()


if __name__ == "__main__":unittest.main()
