"""Real candidate probe and guarded, one-time activation after runtime upgrade."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

from app import simple_development as development
from app.communication import agent_roles as roles
from app.communication.luna_release import http_call, new_luna_client
from app.file_persistence import atomic_write_json

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORE = PROJECT_ROOT / 'data/private/simple_development_probes'
PROTOCOL = 1
_ID = re.compile(r'[0-9a-f]{32}')
_SOURCE = 'def normalize_label(value):\n    text = str(value)\n    text = text.strip()\n    return text\n'
_TEST = '''import unittest
from app.labels import normalize_label
class LabelTests(unittest.TestCase):
    def test_spaces(self):
        self.assertEqual(normalize_label("  Ahoj   Mílo "), "ahoj mílo")
    def test_tabs(self):
        self.assertEqual(normalize_label("\\tŽLUŤOUČKÝ\\n KŮŇ "), "žluťoučký kůň")
    def test_empty(self):
        self.assertEqual(normalize_label(" \\t"), "")
'''
_REQUEST = {'goal': 'Ořízni okraje, sbal libovolné bílé znaky na jednu mezeru a použij casefold.',
            'path': 'app/labels.py', 'function': 'normalize_label', 'test_modules': ['tests.test_labels']}


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def capabilities():
    """Served by the running Cockpit, never inferred from files on disk."""
    try:
        roles.load_role(role=roles.DEVELOPMENT_ROLE)
        enabled = True
    except roles.AgentRoleError:
        enabled = False
    return {'ok': True, 'protocol': PROTOCOL, 'role_schema': 2,
            'role': roles.DEVELOPMENT_ROLE, 'enabled': enabled,
            'supported_task_kinds': ['pure_python_function']}


def probe_candidate(model, reasoning_effort, *, cost_review, confirmed=False, client_factory=new_luna_client):
    """One explicitly price-reviewed synthetic development turn; no production role edit."""
    if confirmed is not True:
        return {'state': 'not_started', 'reason': 'Zkouška vyžaduje schválené cenové posouzení.'}
    if (not isinstance(model, str) or not roles.MODEL_ID.fullmatch(model)
            or reasoning_effort not in roles.EFFORTS or not isinstance(cost_review, str)
            or not 8 <= len(cost_review) <= 240 or any(ord(c) < 32 for c in cost_review)):
        return {'state': 'attention', 'reason': 'Neplatné cenové posouzení nebo kandidát.'}
    probe_id = uuid.uuid4().hex
    home = development._private_dir(STORE / probe_id)
    fixture = development._private_dir(home / 'fixture')
    role_path = fixture / 'config/agent_roles.json'
    binding = {'label': 'Pomocník pro jednu čistou Python funkci', 'preferred_model': model,
               'approved_models': [{'model': model, 'reasoning_effort': reasoning_effort,
                                    'cost_review': cost_review,
                                    'dry_run_evidence': f'data/private/simple_development_probes/{probe_id}/proof.json'}]}
    release_digest = roles.load_role(PROJECT_ROOT / 'config/agent_roles.json')['policy_digest']
    for relative, text in {'app/__init__.py': '', 'tests/__init__.py': '',
                           'app/labels.py': _SOURCE, 'tests/test_labels.py': _TEST}.items():
        target = fixture / relative
        development._private_dir(target.parent)
        development._write(target, text.encode())
    development._private_dir(role_path.parent)
    development._write(role_path, json.dumps({'schema': 1, 'roles': {roles.DEVELOPMENT_ROLE: binding}}).encode())
    for command in (['init', '-q'], ['add', '--', 'app', 'tests', 'config/agent_roles.json'],
                    ['-c', 'user.name=Development probe', '-c', 'user.email=probe@invalid',
                     '-c', 'core.hooksPath=/dev/null', 'commit', '-q', '-m', 'Synthetic failing function']):
        subprocess.run(['git', '-C', str(fixture), *command], check=True, capture_output=True, timeout=30)
    result = development.run(_REQUEST, root=fixture, confirmed=True, roles_path=role_path,
                             store_root=home / 'jobs', client_factory=client_factory)
    proof = {'probe_id': probe_id, 'binding': binding, 'release_policy_digest': release_digest,
             'fixture': str(fixture), 'result': result}
    # A probe presents the same candidate for one main-Adam review as a normal task.
    atomic_write_json(home / 'proof.json', proof)
    (home / 'proof.json').chmod(0o600)
    return {'probe_id': probe_id, **result}


def accept_probe(probe_id, candidate_digest, *, confirmed=False):
    """Record the reviewed synthetic result; no production source/configuration edit."""
    if confirmed is not True:
        return {'state': 'not_applied'}
    home, proof = _proof(probe_id)
    result = development.accept(proof['result']['job_id'], candidate_digest,
                                root=Path(proof['fixture']), confirmed=True,
                                store_root=home / 'jobs', roles_path=Path(proof['fixture']) / 'config/agent_roles.json')
    if result.get('state') == 'applied':
        proof['result'] = result
        atomic_write_json(home / 'proof.json', proof)
        (home / 'proof.json').chmod(0o600)
    return {'probe_id': probe_id, **result}


def _proof(probe_id):
    if not isinstance(probe_id, str) or not _ID.fullmatch(probe_id):
        raise ValueError('Neplatná zkouška.')
    home = STORE / probe_id
    path = home / 'proof.json'
    if any(p.is_symlink() for p in (path, *path.parents)) or path.stat().st_size > 64000:
        raise ValueError('Neplatný soukromý důkaz.')
    proof = json.loads(path.read_bytes())
    if proof['probe_id'] != probe_id or proof['fixture'] != str(home / 'fixture'):
        raise ValueError('Důkaz nepatří k této zkoušce.')
    return home, proof


def activation_plan(probe_id):
    """Read-only: require a deployed compatible runtime plus an accepted real probe."""
    try:
        home, proof = _proof(probe_id)
        result = proof['result']
        saved = json.loads(development._read(home / 'jobs' / result['job_id'] / 'receipt.json'))
        binding = proof['binding']
        if (result['state'] != 'applied' or result != development._public(saved)
                or result['executor']['policy_digest'] != _digest(binding)
                or result['baseline']['exit_code'] != 1 or result['after']['exit_code'] != 0
                or result['baseline']['test_count'] != 3 or result['after']['test_count'] != 3
                or hashlib.sha256(development._read(home / 'fixture/app/labels.py')).hexdigest() != result['candidate_digest']):
            raise ValueError('Zkouška není uzavřená nebo se změnila.')
        config = PROJECT_ROOT / 'config/agent_roles.json'
        if roles.load_role(config)['policy_digest'] != proof['release_policy_digest']:
            raise ValueError('Role p+n se změnila.')
        document = json.loads(config.read_bytes())
        if roles.DEVELOPMENT_ROLE in document['roles']:
            if document['roles'][roles.DEVELOPMENT_ROLE] != binding:
                raise ValueError('Vývojová role už má jiné schválení.')
            return {'state': 'active', 'probe_id': probe_id}
        runtime = http_call('/api/human-adam/simple-development/capabilities')
        if (runtime.get('ok') is not True or runtime.get('protocol') != PROTOCOL
                or runtime.get('role_schema') != 2 or runtime.get('role') != roles.DEVELOPMENT_ROLE):
            raise ValueError('Nejprve je nutné nasadit kompatibilní Cockpit.')
        development._clean(PROJECT_ROOT)
        if development._git(PROJECT_ROOT, 'branch', '--show-current').decode().strip() != 'main':
            raise ValueError('Aktivace patří pouze na čistý kanonický main.')
        return {'state': 'ready', 'probe_id': probe_id, 'proof_digest': _digest(proof),
                'config_digest': hashlib.sha256(config.read_bytes()).hexdigest(),
                'source_head': development._head(PROJECT_ROOT), 'binding_digest': _digest(binding)}
    except Exception:
        return {'state': 'blocked', 'reason': 'Aktivace vyžaduje nezměněnou přijatou zkoušku, čistý main a již nasazený kompatibilní Cockpit.'}


def activate(plan, *, confirmed=False):
    """One local central-config edit; no service restart, Git or publication."""
    if confirmed is not True:
        return {'state': 'not_applied'}
    if not isinstance(plan, dict) or plan.get('state') != 'ready':
        return {'state': 'blocked', 'reason': 'Chybí přesný plán aktivace.'}
    current = activation_plan(plan.get('probe_id'))
    if current != plan:
        return {'state': 'blocked', 'reason': 'Plán aktivace se změnil; nic nezapsáno.'}
    _, proof = _proof(plan['probe_id'])
    config = PROJECT_ROOT / 'config/agent_roles.json'
    document = json.loads(config.read_bytes())
    document['roles'][roles.DEVELOPMENT_ROLE] = proof['binding']
    atomic_write_json(config, document)
    roles.load_role(config, role=roles.DEVELOPMENT_ROLE)
    return {'state': 'activated_locally', 'role': roles.DEVELOPMENT_ROLE,
            'binding_digest': plan['binding_digest'], 'next': 'Zkontrolovat a commitnout pouze centrální konfiguraci; publikace má vlastní oprávnění.'}
