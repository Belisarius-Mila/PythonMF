"""Private service lifecycle is tested with synthetic Tailscale and launchd only."""
import copy
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app import vocabulary_fr_tailnet as t
from app.vocabulary_fr_cloud import PUBLIC, SERVER, CLOUD

DNS = "fixture-mac.fixture-tail.ts.net"
ENDPOINT = DNS + ":8443"


class Runner:
    def __init__(self):
        self.serve = {"TCP": {"443": {"HTTPS": True}, "8770": {"TCPForward": "127.0.0.1:8770"}},
                      "Web": {DNS + ":443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8770"},
                                "/camino-api": {"Proxy": "http://127.0.0.1:8767"}}}}}
        self.actions = [];self.loaded = False;self.fail_bootstrap = False;self.alter_protected = False;self.foreign_path = False;self.lose_serve_reply = False

    def __call__(self, args):
        value = None;code = 0
        if args == [t.TAILSCALE, "status", "--json"]:
            value = {"BackendState": "Running", "Self": {"DNSName": DNS + ".", "ID": "fixture-owned-node"}}
        elif args in ([t.TAILSCALE, "serve", "status", "--json"], [t.TAILSCALE, "funnel", "status", "--json"]):value = self.serve
        elif args[:2] == ["/bin/launchctl", "print"]:
            if not self.loaded:code = 113;value = "absent"
            else:value = "path = " + ("/foreign.plist" if self.foreign_path else str(self.service.agent)) + "\npid = 12345\nstate = running\n"
        elif args[:2] == ["/bin/launchctl", "bootstrap"]:
            self.actions.append(args)
            receipt = json.loads(next((self.service.root / "requests").glob("*.json")).read_text())
            assert receipt["state"] in ("activating", "completed")
            definition = plistlib.loads(self.service.agent.read_bytes())
            assert definition["Label"] == t.LABEL and definition["KeepAlive"]
            assert "127.0.0.1" not in definition["ProgramArguments"]  # Uses the unchanged loopback default.
            if self.fail_bootstrap:raise RuntimeError("uncertain fixture bootstrap")
            self.loaded = True;value = ""
        elif args[:2] == ["/bin/launchctl", "bootout"]:
            self.actions.append(args);self.loaded = False;value = ""
        elif args == [t.TAILSCALE, "serve", "--yes", "--bg", "--https=8443", t.PROXY]:
            self.actions.append(args)
            self.serve["TCP"]["8443"] = {"HTTPS": True}
            self.serve["Web"][ENDPOINT] = {"Handlers": {"/": {"Proxy": t.PROXY}}}
            if self.alter_protected:self.serve["Web"][DNS + ":443"]["Handlers"]["/camino-api"] = {"Proxy": "http://foreign"}
            if self.lose_serve_reply:raise RuntimeError("fixture lost reply after Serve applied")
            value = ""
        else:raise AssertionError("Unexpected system action: " + str(args))
        return subprocess.CompletedProcess(args, code, value if isinstance(value, str) else json.dumps(value), "")


class TailnetTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo";self.repo.mkdir()
        def git(*args):return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True, stderr=subprocess.DEVNULL).strip()
        self.git = git;git("init", "-b", "main");git("config", "user.name", "Fixture");git("config", "user.email", "fixture@example.test")
        for name in (SERVER, CLOUD, *PUBLIC):
            path = self.repo / name
            if not path.suffix:path = path / ("online.html" if name.endswith("vocabulary-fr") else "fixture.webp")
            path.parent.mkdir(parents=True, exist_ok=True);path.write_text("public fixture")
        git("add", "--", SERVER, CLOUD, *PUBLIC);git("commit", "-m", "fixture")
        (self.repo / ".git/info/exclude").write_text("Samantha_Agent/data/\n")
        self.head = git("rev-parse", "HEAD");self.runner = Runner()
        self.service = t.PrivateGame(self.repo, home=Path(self.temp.name) / "home", runner=self.runner);self.runner.service = self.service
        names = ("vocabulary-fr-v2.json", "vocabulary-fr-audio.json", "vocabulary-fr-quiz.json")
        self.catalog = hashlib.sha256(b"\0".join((self.repo / "docs/data" / n).read_bytes() for n in names)).hexdigest()
        self.health = patch.object(self.service, "_health", side_effect=lambda origin: {"protocol": 1, "catalog": self.catalog} if self.runner.loaded else None)
        self.health.start();self.addCleanup(self.health.stop)
        self.socket = patch("app.vocabulary_fr_tailnet.socket.socket");self.socket.start();self.addCleanup(self.socket.stop)

    def prepare(self, request="fixture-tailnet-0001"):
        return self.service.prepare(expected_head=self.head, request_id=request)

    def activate(self, envelope, request="fixture-tailnet-0001", **extra):
        return self.service.activate(request_id=request, plan_digest=envelope["digest"], confirmation=t.CONFIRMATION, **extra)

    def test_preparation_only_freezes_private_plan_and_does_not_install_or_change_network(self):
        before = copy.deepcopy(self.runner.serve);value = self.prepare()
        self.assertEqual(value, self.prepare());self.assertFalse(self.service.agent.exists());self.assertEqual(self.runner.actions, [])
        self.assertEqual(self.runner.serve, before);self.assertEqual(value["plan"]["origin"], "https://" + ENDPOINT)
        self.assertIn("8792", value["plan"]["definition"]["ProgramArguments"])
        self.assertEqual(value["digest"], t._digest(value["plan"]))

    def test_global_phrase_and_exact_plan_are_required_before_any_system_change(self):
        envelope = self.prepare()
        for phrase, digest in [("ano", envelope["digest"]), (t.CONFIRMATION, "a" * 64)]:
            with self.assertRaises(ValueError):self.service.activate(request_id="fixture-tailnet-0001", plan_digest=digest, confirmation=phrase)
        self.assertFalse(self.service.agent.exists());self.assertEqual(self.runner.actions, [])

    def test_activation_preserves_cockpit_camino_and_private_scope_and_is_never_replayed(self):
        envelope = self.prepare();before = copy.deepcopy(self.runner.serve)
        result = self.activate(envelope)
        self.assertTrue(result["running"]);self.assertEqual(result["operation"]["state"], "completed")
        self.assertEqual(t._without_game(self.runner.serve, ENDPOINT), t._without_game(before, ENDPOINT))
        self.assertFalse(any(self.runner.serve.get("AllowFunnel", {}).values()))
        self.assertEqual(self.service.agent.stat().st_mode & 0o777, 0o600)
        actions = list(self.runner.actions);self.assertTrue(self.activate(envelope)["running"]);self.assertEqual(self.runner.actions, actions)
        self.assertEqual(len(actions), 2)

    def test_source_or_network_changes_reject_the_old_plan_without_system_mutations(self):
        envelope = self.prepare();self.runner.serve["Web"][DNS + ":443"]["Handlers"]["/other"] = {"Proxy": "http://fixture"}
        with self.assertRaises(ValueError):self.activate(envelope)
        self.assertEqual(self.runner.actions, [])

    def test_changed_commit_rejects_activation(self):
        envelope = self.prepare();(self.repo / SERVER).write_text("updated fixture")
        self.git("add", "--", SERVER);self.git("commit", "-m", "new fixture")
        with self.assertRaises(ValueError):self.activate(envelope)
        self.assertEqual(self.runner.actions, [])

    def test_release_manifest_is_bound_to_the_plan_before_any_system_change(self):
        envelope=self.prepare();release=self.service.root/'releases'/envelope['plan']['head']
        manifest=release/'manifest.json';manifest.write_text(manifest.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'manifest changed'):self.activate(envelope)
        self.assertEqual(self.runner.actions,[])

    def test_foreign_route_launchagent_or_service_label_is_preserved(self):
        self.runner.serve["TCP"]["8443"] = {"HTTPS": True}
        with self.assertRaises(ValueError):self.prepare()
        self.runner.serve["TCP"].pop("8443")
        self.runner.loaded = True
        with self.assertRaises(ValueError):self.prepare()
        self.runner.loaded = False;self.service.agent.parent.mkdir(parents=True);self.service.agent.write_bytes(b"foreign fixture")
        with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(self.service.agent.read_bytes(), b"foreign fixture");self.assertEqual(self.runner.actions, [])

    def test_funnel_enabled_anywhere_blocks_preparation(self):
        self.runner.serve["AllowFunnel"] = {DNS + ":10000": True}
        with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(self.runner.actions, [])

    def test_a_late_foreign_launchagent_is_not_overwritten(self):
        envelope = self.prepare()
        original_socket = self.service.runner
        def runner(args):
            result = original_socket(args)
            if args == ["/bin/launchctl", "print", self.service.target] and (self.service.root / "active.json").exists() and not self.service.agent.exists():
                self.service.agent.parent.mkdir(parents=True,exist_ok=True);self.service.agent.write_bytes(b"late foreign fixture")
            return result
        self.service.runner=runner
        with self.assertRaises(FileExistsError):self.activate(envelope)
        self.assertEqual(self.service.agent.read_bytes(),b"late foreign fixture")
        self.assertEqual(self.runner.actions,[])

    def test_uncertain_bootstrap_stays_attention_without_retrying_launch_or_network(self):
        envelope = self.prepare();self.runner.fail_bootstrap = True
        with self.assertRaises(RuntimeError):self.activate(envelope)
        before = list(self.runner.actions);result = self.activate(envelope)
        self.assertEqual(result["state"], "attention");self.assertEqual(result["operation"]["state"], "attention")
        self.assertEqual(self.runner.actions, before);self.assertNotIn("8443", self.runner.serve["TCP"])
        with self.assertRaises(ValueError):self.prepare("fixture-tailnet-second")

    def test_lost_activation_reply_is_resolved_by_original_live_proof_without_replay(self):
        envelope=self.prepare();self.runner.lose_serve_reply=True
        with self.assertRaises(RuntimeError):self.activate(envelope)
        before=list(self.runner.actions)
        result=self.service.verify(request_id='fixture-tailnet-0001',plan_digest=envelope['digest'])
        self.assertEqual(result['operation']['state'],'completed');self.assertTrue(result['running'])
        self.assertEqual(self.runner.actions,before)

    def test_protected_route_change_is_not_hidden_or_automatically_reset(self):
        envelope = self.prepare();self.runner.alter_protected = True
        with self.assertRaises(RuntimeError):self.activate(envelope)
        self.assertEqual(self.service.status()["state"], "attention")
        self.assertEqual(self.runner.serve["Web"][DNS + ":443"]["Handlers"]["/camino-api"], {"Proxy": "http://foreign"})
        self.assertFalse(any("reset" in action for action in self.runner.actions))

    def test_owned_update_preserves_database_and_previous_definition(self):
        first = self.prepare();self.activate(first)
        database = self.service.root / "rooms.sqlite3";database.write_bytes(b"private room fixture")
        previous = self.service.agent.read_bytes();(self.repo / SERVER).write_text("new server fixture")
        self.git("add", "--", SERVER);self.git("commit", "-m", "new release");self.head = self.git("rev-parse", "HEAD")
        second = self.prepare("fixture-tailnet-update")
        result = self.activate(second, "fixture-tailnet-update")
        self.assertTrue(result["running"]);self.assertEqual(result["head"], self.head)
        self.assertEqual(database.read_bytes(), b"private room fixture")
        self.assertEqual((self.service.root / "requests/fixture-tailnet-update-previous.plist").read_bytes(), previous)
        self.assertEqual(sum(action[:2] == ["/bin/launchctl", "bootstrap"] for action in self.runner.actions), 2)

    def test_status_rejects_a_reused_service_label_with_another_definition_path(self):
        value = self.prepare();self.activate(value);self.runner.foreign_path = True
        self.assertFalse(self.service.status()["running"])


if __name__ == "__main__":unittest.main()


class CompatibleCatalogMigrationTests(unittest.TestCase):
    def setUp(self):
        import sqlite3
        self.tmp = TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name);self.database = self.root / 'rooms.sqlite3'
        with sqlite3.connect(self.database) as c:
            c.execute('CREATE TABLE rooms (id TEXT PRIMARY KEY, request TEXT UNIQUE, body TEXT NOT NULL)')
        self.transition = {'from':'old-catalog','to':'new-catalog','uids':['vfr-0001','vfr-0002']}

    def write_room(self, uid, **extra):
        import sqlite3
        room = {'id':uid,'catalog':'old-catalog','deck':['vfr-0001','vfr-0002']*12,
                'players':[{'name':'A','tokenHash':'private-hash'},None],
                'inviteHash':'private-invite','expires':9999999999,'revision':7,
                'scores':[2,1],'owners':{'vfr-0001':0},'round':3,**extra}
        with sqlite3.connect(self.database) as c:
            c.execute('INSERT INTO rooms VALUES (?,?,?)',(uid,'request-'+uid,json.dumps(room)))
        return room

    def read_rooms(self):
        import sqlite3
        with sqlite3.connect(self.database) as c:
            return {uid:json.loads(body) for uid,body in c.execute('SELECT id,body FROM rooms')}

    def test_transaction_preserves_invites_access_scores_and_both_game_modes(self):
        a=self.write_room('pairs');b=self.write_room('duel',mode='duel',pool=['vfr-0001','vfr-0002'],questions=[{'target':'vfr-0001','choices':['vfr-0001','vfr-0002']}])
        result=t._migrate_rooms(self.root,self.transition)
        self.assertEqual(result['rooms'],2);self.assertTrue(Path(result['backup']).is_file())
        for uid,old in [('pairs',a),('duel',b)]:
            self.assertEqual(self.read_rooms()[uid],{**old,'catalog':'new-catalog'})
        self.assertEqual(t._migrate_rooms(self.root,self.transition)['rooms'],0)

    def test_unknown_uid_rolls_back_all_rooms_and_keeps_backup(self):
        self.write_room('first');self.write_room('second',deck=['vfr-9999'])
        before=self.read_rooms()
        with self.assertRaisesRegex(ValueError,'unknown meaning'):t._migrate_rooms(self.root,self.transition)
        self.assertEqual(self.read_rooms(),before)
        self.assertEqual(len(list((self.root/'backups').glob('*.sqlite3'))),1)

    def test_other_catalog_versions_are_never_relabelled(self):
        old=self.write_room('unrelated',catalog='different-version')
        self.assertEqual(t._migrate_rooms(self.root,self.transition)['rooms'],0)
        self.assertEqual(self.read_rooms()['unrelated'],old)

    def test_only_identical_old_meanings_and_quiz_metadata_allow_extension(self):
        from types import SimpleNamespace
        previous=self.root/'previous';current=self.root/'current'
        for base,value in [(previous,'old'),(current,'new')]:
            (base/'docs/data').mkdir(parents=True)
            for name in ('vocabulary-fr-v2.json','vocabulary-fr-audio.json','vocabulary-fr-quiz.json'):(base/'docs/data'/name).write_text(value)
        old=SimpleNamespace(revision='old-catalog',items={'vfr-0001':{'fr':'fixture'}},metadata={'vfr-0001':{'conflicts':[]}})
        new=copy.deepcopy(old);new.revision='new-catalog';new.items['vfr-0002']={'fr':'new fixture'};new.metadata['vfr-0002']={'conflicts':[]}
        with patch.object(t,'Catalog',side_effect=[old,new]):
            value=t._catalog_transition(previous,current,self.database)
        self.assertEqual(value,{'from':'old-catalog','to':'new-catalog','uids':['vfr-0001']})
        new.metadata['vfr-0001']['conflicts'].append('changed')
        with patch.object(t,'Catalog',side_effect=[old,new]), self.assertRaisesRegex(ValueError,'Existing vocabulary changed'):
            t._catalog_transition(previous,current,self.database)
