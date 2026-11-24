"""No live connector or system configuration is used by hosting regressions."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch, MagicMock

from app.vocabulary_fr_hosting import Pilot, PUBLIC, SERVER, _sha, _write
from app.vocabulary_fr_hosting import cockpit_french_url
from urllib.parse import parse_qs, urlsplit


class HostingTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.DEVNULL, text=True).strip()
        self.git = git
        git("init", "-b", "main");git("config", "user.name", "Fixture");git("config", "user.email", "fixture@example.test")
        for name in (SERVER, *PUBLIC):
            path = self.repo / name
            if not path.suffix:
                path = path / ("online.html" if name.endswith("vocabulary-fr") else "sample.webp")
            path.parent.mkdir(parents=True, exist_ok=True);path.write_text("public fixture")
        (self.repo / "Samantha_Agent/.env").write_text("PRIVATE FIXTURE")
        git("add", "--", SERVER, *PUBLIC);git("commit", "-m", "fixture")
        (self.repo / ".git/info/exclude").write_text("Samantha_Agent/data/\nSamantha_Agent/.env\n")
        self.head = git("rev-parse", "HEAD");self.pilot = Pilot(self.repo)
        self.binary = self.repo / "Samantha_Agent/data/private/connector"
        self.binary.parent.mkdir(parents=True);self.binary.write_text("verified connector fixture")

    def prepare(self):
        return self.pilot.prepare(expected_head=self.head, connector=self.binary, connector_sha256=_sha(self.binary))

    def upgrade_fixture(self, *, change_catalog=False):
        old = self.prepare()
        (self.pilot.root / "rooms.sqlite3").write_bytes(b"preserved private room and player fixture")
        state = {"state": "started", "head": self.head, "requestId": "fixture-original-start", "origin": "https://fixture-first-second-third.trycloudflare.com",
                 "processes": {"connector": {"pid": 100, "identity": "connector-owned"}, "server": {"pid": 101, "identity": "server-old"}}}
        _write(self.pilot.root / "active.json", state)
        (self.repo / SERVER).write_text("updated public server fixture")
        if change_catalog:
            (self.repo / "docs/data/vocabulary-fr-v2.json").write_text("different catalog fixture")
        self.git("add", "--", SERVER, "docs/data/vocabulary-fr-v2.json");self.git("commit", "-m", "updated fixture")
        self.head = self.git("rev-parse", "HEAD")
        self.prepare()
        self.upgrade_git = {command: self.git(*command) for command in [("rev-parse", "HEAD"), ("status", "--porcelain"), ("branch", "--show-current")]}
        args = {"expected_head": self.head, "expected_running_head": old["head"], "request_id": "fixture-upgrade-0001", "confirmed": True}
        return state, args

    def test_export_contains_only_committed_public_fr_and_no_repository_or_secrets(self):
        prepared = self.prepare();release = Path(prepared["release"])
        self.assertFalse((release / ".git").exists());self.assertFalse((release / "Samantha_Agent/.env").exists())
        self.assertIn(SERVER, prepared["files"]);self.assertIn("docs/vocabulary-fr/online.html", prepared["files"])
        self.assertEqual(self.prepare(), prepared)

    def test_dirty_or_wrong_head_and_unverified_connector_cannot_prepare(self):
        for head, digest in [("a" * 40, _sha(self.binary)), (self.head, "f" * 64)]:
            with self.assertRaises(ValueError):
                self.pilot.prepare(expected_head=head, connector=self.binary, connector_sha256=digest)
        (self.repo / SERVER).write_text("uncommitted")
        with self.assertRaises(ValueError):self.prepare()

    def test_modified_release_or_connector_cannot_start(self):
        prepared = self.prepare();(Path(prepared["release"]) / SERVER).write_text("modified")
        with self.assertRaises(ValueError):self.pilot.start(expected_head=self.head, request_id="fixture-change-01", confirmed=True)
        self.assertEqual(self.pilot.status()["state"], "not_started")

    def test_archive_symlink_cannot_export_private_source(self):
        link = self.repo / "docs/vocabulary-fr/private-link";link.symlink_to(self.repo / "Samantha_Agent/.env")
        self.git("add", "--", str(link));self.git("commit", "-m", "unsafe fixture");self.head = self.git("rev-parse", "HEAD")
        with self.assertRaises(ValueError):self.prepare()

    def test_one_request_starts_once_uses_empty_config_and_ignores_inherited_tunnel_secrets(self):
        self.prepare();calls=[]
        def launch(args, **kwargs):
            calls.append((args,kwargs));kwargs["stdout"].write(b"https://fixture-first-second-third.trycloudflare.com\n");kwargs["stdout"].flush()
            process=MagicMock();process.pid=100+len(calls);process.poll.return_value=None;return process
        with patch("app.vocabulary_fr_hosting.socket.socket"), patch("app.vocabulary_fr_hosting.subprocess.Popen",side_effect=launch), patch.object(self.pilot,"_identity",side_effect=lambda pid:f"owned-{pid}"),patch.dict("os.environ",{"TUNNEL_TOKEN":"secret","TUNNEL_LOGLEVEL":"debug","PYTHONPATH":"bad"}):
            first=self.pilot.start(expected_head=self.head,request_id="fixture-start-001",confirmed=True)
            second=self.pilot.start(expected_head=self.head,request_id="fixture-start-001",confirmed=True)
            self.assertTrue(first["running"]);self.assertTrue(second["running"]);self.assertEqual(len(calls),2)
            connector=calls[0];self.assertNotIn("TUNNEL_TOKEN",connector[1]["env"]);self.assertNotIn("PYTHONPATH",connector[1]["env"])
            config=connector[0][connector[0].index("--config")+1];self.assertEqual(Path(config).read_text(),"{}\n")
            self.assertIn("127.0.0.1:8791", " ".join(connector[0]));self.assertIn(first["origin"], calls[1][0])
            with self.assertRaises(ValueError):self.pilot.start(expected_head=self.head,request_id="fixture-start-002",confirmed=True)

    def test_dead_uncertain_or_reused_pid_never_restarts_or_kills_a_foreign_process(self):
        self.pilot.root.mkdir(parents=True)
        _write(self.pilot.root/"active.json",{"state":"attention","head":self.head,"requestId":"fixture-unknown-01","processes":{"connector":{"pid":123,"identity":"original"}}})
        with patch.object(self.pilot,"_identity",return_value="foreign"),patch("app.vocabulary_fr_hosting.os.kill") as kill:
            self.assertFalse(self.pilot.status()["running"])
            with self.assertRaises(ValueError):self.pilot.start(expected_head=self.head,request_id="fixture-unknown-02",confirmed=True)
            self.pilot.stop(request_id="fixture-unknown-01",confirmed=True);kill.assert_not_called()

    def test_current_confirmation_is_required_for_start_and_stop(self):
        with self.assertRaises(ValueError):self.pilot.start(expected_head=self.head,request_id="fixture-start-001",confirmed=False)
        with self.assertRaises(ValueError):self.pilot.stop(request_id="fixture-start-001",confirmed=False)

    def test_partial_start_is_recorded_and_same_request_never_creates_a_second_connector(self):
        self.prepare();calls=[]
        def launch(args,**kwargs):
            calls.append(args)
            if len(calls)==2:raise OSError("server fixture failure")
            kwargs["stdout"].write(b"https://fixture-first-second-third.trycloudflare.com\n");kwargs["stdout"].flush()
            process=MagicMock();process.pid=101;return process
        with patch("app.vocabulary_fr_hosting.socket.socket"),patch("app.vocabulary_fr_hosting.subprocess.Popen",side_effect=launch),patch.object(self.pilot,"_identity",return_value="owned"):
            with self.assertRaises(OSError):self.pilot.start(expected_head=self.head,request_id="fixture-partial-01",confirmed=True)
            result=self.pilot.start(expected_head=self.head,request_id="fixture-partial-01",confirmed=True)
            self.assertEqual(result["state"],"attention");self.assertEqual(len(calls),2)

    def test_stop_terminates_only_owned_processes_and_keeps_games_and_release(self):
        prepared=self.prepare();database=self.pilot.root/"rooms.sqlite3";database.write_bytes(b"preserved game fixture")
        _write(self.pilot.root/"active.json",{"state":"started","requestId":"fixture-stop-0001","processes":{"connector":{"pid":100,"identity":"owned"},"server":{"pid":101,"identity":"owned"}}})
        with patch.object(self.pilot,"_identity",return_value="owned"),patch("app.vocabulary_fr_hosting.os.kill") as kill:
            result=self.pilot.stop(request_id="fixture-stop-0001",confirmed=True)
            self.assertEqual(result["state"],"stopped");self.assertEqual([call.args[0] for call in kill.call_args_list],[100,101])
        self.assertEqual(database.read_bytes(),b"preserved game fixture");self.assertTrue(Path(prepared["release"]).exists())

    def test_registered_start_is_explicit_and_status_does_not_mutate(self):
        from app.capabilities import get_capability, ConfirmationPolicy, RiskLevel
        start=get_capability("vocabulary_fr_hosting_start")
        self.assertTrue(start.requires_confirmation)
        self.assertEqual(start.confirmation_policy,ConfirmationPolicy.EXACT_CURRENT_MESSAGE)
        upgrade=get_capability("vocabulary_fr_hosting_upgrade")
        self.assertTrue(upgrade.requires_confirmation)
        self.assertEqual(upgrade.confirmation_policy,ConfirmationPolicy.EXACT_CURRENT_MESSAGE)
        self.assertEqual(get_capability("vocabulary_fr_hosting_status").risk,RiskLevel.READ_ONLY)
        self.assertEqual(self.pilot.status(),{"state":"not_started"})
        self.assertFalse(self.pilot.root.exists())

    def test_upgrade_replaces_only_backend_once_preserving_origin_connector_and_database(self):
        before, args = self.upgrade_fixture()
        identities = {100: "connector-owned", 101: "server-old", 201: "server-new"}
        def stopped(pid, sig):
            operation = json.loads((self.pilot.root / "upgrades" / (args["request_id"] + ".json")).read_text())
            self.assertEqual(operation["state"], "upgrading")
            self.assertEqual(pid, 101)
            identities[pid] = ""
        process = MagicMock(pid=201)
        with patch("app.vocabulary_fr_hosting._git", side_effect=lambda repo, *command: self.upgrade_git[command]), \
             patch.object(self.pilot, "_identity", side_effect=lambda pid: identities.get(pid, "")), \
             patch("app.vocabulary_fr_hosting.os.kill", side_effect=stopped) as kill, \
             patch("app.vocabulary_fr_hosting.subprocess.Popen", return_value=process) as launch, \
             patch("app.vocabulary_fr_hosting.socket.socket"), patch.object(self.pilot, "_wait_for_server") as health, \
             patch.dict("os.environ", {"TUNNEL_TOKEN": "secret", "PYTHONPATH": "bad"}):
            result = self.pilot.upgrade(**args)
            self.assertTrue(result["running"]);self.assertEqual(result["upgrade"]["state"], "completed")
            self.assertEqual(result["origin"], before["origin"])
            self.assertEqual(result["requestId"], before["requestId"])
            self.assertEqual(result["processes"]["connector"], before["processes"]["connector"])
            self.assertEqual(result["processes"]["server"]["pid"], 201)
            self.assertEqual(result["head"], args["expected_head"])
            health.assert_called_once();self.assertEqual(self.pilot.upgrade(**args), result)
            self.assertEqual(kill.call_count, 1);self.assertEqual(launch.call_count, 1)
            command = launch.call_args.args[0]
            self.assertIn(before["origin"], command);self.assertIn(str(self.pilot.root / "rooms.sqlite3"), command)
            self.assertIn(args["expected_head"], " ".join(command))
            self.assertNotIn("TUNNEL_TOKEN", launch.call_args.kwargs["env"])
            self.assertNotIn("PYTHONPATH", launch.call_args.kwargs["env"])
            with self.assertRaises(ValueError):self.pilot.upgrade(**{**args, "expected_running_head": "a" * 40})
        self.assertEqual((self.pilot.root / "rooms.sqlite3").read_bytes(), b"preserved private room and player fixture")
        self.assertTrue((self.pilot.root / "releases" / args["expected_running_head"]).exists())

    def test_upgrade_rejects_unapproved_stale_foreign_or_changed_catalog_before_stop(self):
        _, args = self.upgrade_fixture(change_catalog=True)
        with patch("app.vocabulary_fr_hosting._git", side_effect=lambda repo, *command: self.upgrade_git[command]), \
             patch.object(self.pilot, "_identity", side_effect=lambda pid: {100: "connector-owned", 101: "server-old"}.get(pid, "")), \
             patch("app.vocabulary_fr_hosting.os.kill") as kill, patch("app.vocabulary_fr_hosting.subprocess.Popen") as launch:
            for values in [{**args, "confirmed": False}, {**args, "expected_running_head": "f" * 40}, args]:
                with self.assertRaises(ValueError):self.pilot.upgrade(**values)
            kill.assert_not_called();launch.assert_not_called()
        with patch.object(self.pilot, "_identity", return_value="reused-foreign"), patch("app.vocabulary_fr_hosting.os.kill") as kill:
            with self.assertRaises(ValueError):self.pilot.upgrade(**args)
            kill.assert_not_called()

    def test_failed_upgrade_keeps_tunnel_and_never_replays_uncertain_start(self):
        before, args = self.upgrade_fixture()
        identities = {100: "connector-owned", 101: "server-old"}
        def stop(pid, sig):identities[pid] = ""
        with patch("app.vocabulary_fr_hosting._git", side_effect=lambda repo, *command: self.upgrade_git[command]), \
             patch.object(self.pilot, "_identity", side_effect=lambda pid: identities.get(pid, "")), \
             patch("app.vocabulary_fr_hosting.os.kill", side_effect=stop) as kill, patch("app.vocabulary_fr_hosting.socket.socket"), \
             patch("app.vocabulary_fr_hosting.subprocess.Popen", side_effect=OSError("fixture start uncertain")) as launch:
            with self.assertRaises(OSError):self.pilot.upgrade(**args)
            result = self.pilot.upgrade(**args)
            self.assertEqual(result["state"], "attention");self.assertEqual(result["upgrade"]["state"], "attention")
            self.assertTrue(result["alive"]["connector"])
            self.assertEqual(result["origin"], before["origin"])
            self.assertEqual(kill.call_count, 1);self.assertEqual(launch.call_count, 1)
            with self.assertRaises(ValueError):self.pilot.upgrade(**{**args, "request_id": "fixture-upgrade-0002"})

    def test_upgrade_does_not_start_replacement_while_original_server_still_lives(self):
        _, args = self.upgrade_fixture()
        with patch("app.vocabulary_fr_hosting._git", side_effect=lambda repo, *command: self.upgrade_git[command]), \
             patch.object(self.pilot, "_identity", side_effect=lambda pid: {100: "connector-owned", 101: "server-old"}.get(pid, "")), \
             patch("app.vocabulary_fr_hosting.os.kill") as kill, patch("app.vocabulary_fr_hosting.subprocess.Popen") as launch, \
             patch("app.vocabulary_fr_hosting.time.monotonic", side_effect=[0, 31]):
            with self.assertRaisesRegex(RuntimeError, "not exited"):self.pilot.upgrade(**args)
            self.assertEqual(kill.call_count, 1);launch.assert_not_called()
            self.assertEqual(self.pilot.upgrade(**args)["upgrade"]["state"], "attention")

    def test_upgrade_records_new_process_but_does_not_report_success_after_failed_health(self):
        _, args = self.upgrade_fixture()
        identities = {100: "connector-owned", 101: "server-old", 201: "server-new"}
        def stop(pid, sig):identities[pid] = ""
        with patch("app.vocabulary_fr_hosting._git", side_effect=lambda repo, *command: self.upgrade_git[command]), \
             patch.object(self.pilot, "_identity", side_effect=lambda pid: identities.get(pid, "")), \
             patch("app.vocabulary_fr_hosting.os.kill", side_effect=stop) as kill, patch("app.vocabulary_fr_hosting.socket.socket"), \
             patch("app.vocabulary_fr_hosting.subprocess.Popen", return_value=MagicMock(pid=201)) as launch, \
             patch.object(self.pilot, "_wait_for_server", side_effect=RuntimeError("health not confirmed")):
            with self.assertRaisesRegex(RuntimeError, "health"):self.pilot.upgrade(**args)
            result = self.pilot.upgrade(**args)
            self.assertFalse(result["running"]);self.assertEqual(result["state"], "attention")
            self.assertEqual(result["processes"]["server"]["pid"], 201)
            self.assertTrue(result["alive"]["connector"])
            self.assertEqual(kill.call_count, 1);self.assertEqual(launch.call_count, 1)

    def test_macos_launcher_transition_keeps_exact_pid_birth_and_server_arguments(self):
        args=' -I /release/Samantha_Agent/app/vocabulary_fr_multiplayer.py --port 8791 --database /private/rooms.sqlite3'
        before='Tue Nov 24 14:23:33 2026 '+sys.executable+args
        after='Tue Nov 24 14:23:33 2026 '+str(Path(sys.base_prefix)/'Resources/Python.app/Contents/MacOS/Python')+args
        self.assertEqual(Pilot._stable_identity(before),Pilot._stable_identity(after))
        self.assertNotEqual(Pilot._stable_identity(before),Pilot._stable_identity(after.replace('14:23:33','14:23:34')))
        self.assertNotEqual(Pilot._stable_identity(before),Pilot._stable_identity(after.replace('8791','8770')))
        self.assertNotEqual(Pilot._stable_identity(before),Pilot._stable_identity(after.replace(str(Path(sys.base_prefix)/'Resources/Python.app/Contents/MacOS/Python'),'/foreign/python')))

    def test_cockpit_launch_retains_pages_origin_and_attaches_only_live_game_origin(self):
        original='https://belisarius-mila.github.io/PythonMF/vocabulary-fr/#personalHard=true'
        origin='https://fixture-friendly-family-game.trycloudflare.com'
        with patch.object(Pilot,'status',return_value={'running':True,'origin':origin,'processes':{'private':'never expose'},'token':'never expose'}):
            result=cockpit_french_url(original,self.repo)
        url=urlsplit(result);params=parse_qs(url.fragment)
        self.assertEqual(url.netloc,'belisarius-mila.github.io');self.assertEqual(url.path,'/PythonMF/vocabulary-fr/')
        self.assertEqual(params,{'personalHard':['true'],'onlineOrigin':[origin]})
        self.assertNotIn('never',result);self.assertFalse(self.pilot.root.exists())

    def test_legacy_czech_birth_dates_match_english_process_output_for_server_and_connector(self):
        for command in ['/private/connector --url http://127.0.0.1:8791',sys.executable+' -I /release/Samantha_Agent/app/vocabulary_fr_multiplayer.py --port 8791']:
            old='út 24 lis 14:23:33 2026 '+command
            fresh='Tue Nov 24 14:23:33 2026 '+command
            self.assertEqual(Pilot._stable_identity(old),Pilot._stable_identity(fresh))
            self.assertNotEqual(Pilot._stable_identity(old),Pilot._stable_identity(fresh.replace('14:23:33','14:23:34')))

    def test_permanent_game_origin_is_available_in_cockpit_without_a_local_mac_pilot(self):
        path=self.repo/'docs/vocabulary-fr/online-hosting.json'
        path.write_text(json.dumps({'schemaVersion':1,'origin':'https://fixture-fr.onrender.com'}))
        with patch.object(Pilot,'status',side_effect=AssertionError('Local pilot must not be needed')):
            linked=cockpit_french_url('https://belisarius-mila.github.io/PythonMF/vocabulary-fr/#personalHard=true',self.repo)
        self.assertEqual(parse_qs(urlsplit(linked).fragment),{'personalHard':['true'],'onlineOrigin':['https://fixture-fr.onrender.com']})
        for config in [{'schemaVersion':2,'origin':'https://fixture-fr.onrender.com'}, {'schemaVersion':1,'origin':'https://foreign.example'}, {'schemaVersion':1,'origin':'https://fixture-fr.onrender.com/path'}, None]:
            path.write_text(json.dumps(config))
            with patch.object(Pilot,'status',return_value={'running':False}):
                self.assertEqual(cockpit_french_url('https://example.test/fr/',self.repo),'https://example.test/fr/')

    def test_process_query_is_independent_of_a_caller_locale_and_utc_environment(self):
        response=subprocess.CompletedProcess([],0,'Tue Nov 24 14:23:33 2026 /private/connector --url local\n','')
        with patch.dict('os.environ',{'LC_ALL':'cs_CZ.UTF-8','LANG':'cs_CZ.UTF-8','TZ':'UTC'}),patch('app.vocabulary_fr_hosting.subprocess.run',return_value=response) as run:
            self.assertTrue(Pilot._identity(123))
            environment=run.call_args.kwargs['env'];self.assertEqual(environment['LC_ALL'],'C');self.assertEqual(environment['LANG'],'C');self.assertNotIn('TZ',environment)

    def test_stopped_or_malformed_pilot_cannot_redirect_cockpit_to_foreign_content(self):
        original='https://belisarius-mila.github.io/PythonMF/vocabulary-fr/'
        for state in [{'running':False,'origin':'https://fixture-friendly-family-game.trycloudflare.com'},
                      {'running':True,'origin':'https://untrusted.example'},
                      {'running':True,'origin':'https://fixture-friendly-family-game.trycloudflare.com/path'},
                      {'running':True,'origin':None}]:
            with self.subTest(state=state),patch.object(Pilot,'status',return_value=state):
                self.assertEqual(cockpit_french_url(original,self.repo),original)
        for error in [ValueError('bad receipt'),AttributeError('malformed receipt')]:
            with patch.object(Pilot,'status',side_effect=error):
                self.assertEqual(cockpit_french_url(original,self.repo),original)


if __name__ == "__main__":unittest.main()
