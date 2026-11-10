"""Prepare a bounded runtime activation; exact safety phrase installs the agent.

No role is written here. Will must first deploy the reviewed role and runtime.
An uncertain launch is inspected under the same receipt and never bootstrapped twice.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import urllib.request
from zoneinfo import ZoneInfo

from app.communication.agent_roles import load_role
from app.file_persistence import atomic_create_text, atomic_write_json, exclusive_file_lock

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'data/private/science_news_activation'
CONFIRMATION = 'Potvrzuji globální brzdu: rozumím riziku a chci pokračovat.'
LABEL = 'com.samantha.science-news'
CODE = ('app/science_news.py', 'app/science_news_sources.py', 'app/science_news_runner.py',
        'app/science_news_model.py', 'app/routine_tasks.py', 'app/codex_appserver.py',
        'app/release_usage.py', 'app/file_persistence.py', 'scripts/science_news.py',
        'app/cockpit_science_news.py', 'app/frontend/cockpit/science_news.js')
ROLE_PROBE = '''import json
from app.communication.agent_roles import load_role, AgentRoleError, KNOWN_ROLES
try:
 b=load_role(role="science_news_editor")
 print(json.dumps({"known":True,"policy_digest":b["policy_digest"]}))
except AgentRoleError:
 print(json.dumps({"known":"science_news_editor" in KNOWN_ROLES,"policy_digest":None}))
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def safe(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Aktivace nesmí použít symlink.')
    return path


def expected_role():
    binding = load_role(role='science_news_editor')
    candidates = binding['approved_models']
    if (binding['preferred_model'] != 'gpt-6.1-sol' or len(candidates) != 1
            or candidates[0]['model'] != 'gpt-6.1-sol' or candidates[0]['reasoning_effort'] != 'medium'):
        raise ValueError('Aktivace má jiného kandidáta než schválená zkouška.')
    return binding['policy_digest']


def probe_role(runtime, runner=subprocess.run):
    result = runner([str(runtime / '.venv/bin/python'), '-c', ROLE_PROBE], cwd=str(runtime),
        capture_output=True, text=True, check=False, timeout=20)
    if result.returncode != 0:
        raise ValueError('Provozní parser rolí nelze ověřit.')
    return json.loads(result.stdout)


def first_due(now):
    local = now.astimezone(ZoneInfo('Europe/Prague'))
    day = local.date() + timedelta(days=(4 - local.weekday()) % 7)
    due = datetime(day.year, day.month, day.day, 9, tzinfo=ZoneInfo('Europe/Prague'))
    return due if due > local else due + timedelta(days=7)


def probe_serving(runtime):
    """Read-only binding to the local Cockpit and its actually served save guard."""
    try:
        listing = subprocess.run(['lsof','-nP','-iTCP@127.0.0.1:8770','-sTCP:LISTEN','-Fp'],
            capture_output=True, text=True, check=False, timeout=5).stdout
        pids = [line[1:] for line in listing.splitlines() if re.fullmatch(r'p\d+',line)]
        if len(pids) != 1:
            return False
        cwd = subprocess.run(['lsof','-a','-p',pids[0],'-d','cwd','-Fn'],
            capture_output=True, text=True, check=False, timeout=5).stdout
        if 'n'+str(runtime) not in cwd.splitlines():
            return False
        with urllib.request.urlopen('http://127.0.0.1:8770/',timeout=5) as response:
            page = response.read(2000000).decode()
        return 'button.disabled = action === "save" && !item.translation_available;' in page
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


def readiness(proposal, role_probe=probe_role, serving_probe=probe_serving):
    runtime = safe(Path(proposal['runtime_root']))
    code_ok = all(sha(safe(runtime / name).read_bytes()) == value for name, value in proposal['runtime_code'].items())
    role = role_probe(runtime)
    return {'code_ready': code_ok, 'role_ready': role.get('known') is True
        and role.get('policy_digest') == proposal['role_policy_digest'],
        'served_save_guard': serving_probe(runtime)}


def prepare(*, runtime_root, home=None, now=None, role_probe=probe_role, serving_probe=probe_serving):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aktivace potřebuje časové pásmo.')
    runtime = safe(Path(runtime_root).absolute())
    home = safe(Path(home or Path.home()).absolute())
    state = runtime / 'data/private/science_news'
    safe(state)
    agent = safe(home / 'Library/LaunchAgents' / (LABEL + '.plist'))
    if not (runtime / '.venv/bin/python').is_file():
        raise ValueError('Provozní Python není dostupný.')
    hashes = {name: sha(safe(runtime / name).read_bytes()) for name in CODE}
    # This new guard must be deployed before activation. Unrelated current runtime
    # dependencies are pinned as observed, rather than overwritten from Data.
    for name in ('app/science_news_model.py','app/cockpit_science_news.py','app/frontend/cockpit/science_news.js'):
        hashes[name] = sha((ROOT / name).read_bytes())
    definition = {'Label': LABEL, 'ProgramArguments': [str(runtime / '.venv/bin/python'),
        str(runtime / 'scripts/science_news.py'), 'tick'], 'WorkingDirectory': str(runtime),
        'StartInterval': 60, 'RunAtLoad': True,
        'StandardOutPath': str(state / 'scheduler.stdout.log'), 'StandardErrorPath': str(state / 'scheduler.stderr.log')}
    proposal = {'schema': 1, 'runtime_root': str(runtime), 'home': str(home), 'agent_path': str(agent),
        'first_due': first_due(now).isoformat(), 'max_job_credits': 15, 'max_month_credits': 100,
        'role_policy_digest': expected_role(), 'runtime_code': hashes,
        'activation_code_sha256': sha(Path(__file__).read_bytes()),
        'plist': plistlib.dumps(definition, sort_keys=True).decode()}
    encoded = canonical(proposal)
    fingerprint = sha(encoded.encode())
    safe(STATE).mkdir(parents=True, exist_ok=True)
    path = safe(STATE / ('proposal_' + fingerprint + '.json'))
    if not path.exists():
        atomic_create_text(path, encoded)
    elif path.read_text() != encoded:
        raise ValueError('Existující návrh se změnil.')
    return {'proposal_sha256': fingerprint, 'first_due': proposal['first_due'],
        'max_job_credits': 15, 'max_month_credits': 100, 'installation_performed': False,
        'paid_model_calls': 0, **readiness(proposal, role_probe, serving_probe)}


def activate(*, proposal_sha256, confirmation, runner=subprocess.run, role_probe=probe_role,
             serving_probe=probe_serving, now=None):
    if confirmation != CONFIRMATION:
        raise ValueError('Instalace LaunchAgentu vyžaduje přesnou větu globální brzdy.')
    if not re.fullmatch('[a-f0-9]{64}', str(proposal_sha256)):
        raise ValueError('Aktivace vyžaduje přesný otisk návrhu.')
    proposal_path = safe(STATE / ('proposal_' + proposal_sha256 + '.json'))
    raw = proposal_path.read_bytes()
    proposal = json.loads(raw)
    if (sha(raw) != proposal_sha256 or proposal['activation_code_sha256'] != sha(Path(__file__).read_bytes())
            or proposal['role_policy_digest'] != expected_role()):
        raise ValueError('Aktivační návrh se změnil.')
    ready = readiness(proposal, role_probe, serving_probe)
    if not all(ready.values()):
        raise ValueError('Nejprve je nutné nasadit schválený runtime a roli.')
    runtime = safe(Path(proposal['runtime_root']))
    state = safe(runtime / 'data/private/science_news')
    config = safe(state / 'activation.json')
    agent = safe(Path(proposal['agent_path']))
    receipt_path = safe(STATE / ('receipt_' + proposal_sha256 + '.json'))
    safe(receipt_path.with_name(receipt_path.name + '.lock'))
    operation_lock = safe(STATE / ('operation_' + proposal_sha256))
    safe(operation_lock.with_name(operation_lock.name + '.lock'))
    domain = 'gui/' + str(os.getuid())
    label = domain + '/' + LABEL
    def loaded():
        result = runner(['/bin/launchctl', 'print', label], capture_output=True, text=True, check=False, timeout=20)
        return result.returncode == 0, result.stdout
    def matches(listing):
        rows = {line.strip().strip('"') for line in listing.splitlines()}
        return all(arg in rows for arg in plistlib.loads(proposal['plist'].encode())['ProgramArguments'])
    with exclusive_file_lock(operation_lock):
        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
        now = now or datetime.now(timezone.utc)
        if receipt is None:
            if now.tzinfo is None or datetime.fromisoformat(proposal['first_due']) <= now:
                raise ValueError('První schválený pátek už uplynul; obnov neplacený návrh.')
            receipt = {'state': 'prepared', 'launch_attempted': False, 'activated_at': now.isoformat(),
                'proposal_sha256': proposal_sha256, 'first_due': proposal['first_due'], 'paid_model_calls': 0}
        activation = {'enabled': True, 'approval_ref': 'science-news-' + proposal_sha256,
            'activated_at': receipt['activated_at'], 'max_job_credits': 15, 'max_month_credits': 100,
            'proposal_sha256': proposal_sha256}
        present, listing = loaded()
        if agent.exists() and agent.read_text() != proposal['plist']:
            raise ValueError('Existující LaunchAgent patří jinému nastavení.')
        if config.exists() and json.loads(config.read_text()) != activation:
            raise ValueError('Existující aktivace se změnila; nepřepisuji ji.')
        if present:
            if not receipt['launch_attempted'] or not agent.exists() or not config.exists() or not matches(listing):
                raise ValueError('Běžící službu nelze přiřadit ke stejné účtence.')
            receipt['state'] = 'active'
            atomic_write_json(receipt_path, receipt)
            return receipt
        if receipt['launch_attempted']:
            raise ValueError('Spuštění už bylo odesláno; bootstrap neopakuji. Ověř stejnou účtenku.')
        atomic_write_json(receipt_path, receipt)
        state.mkdir(parents=True, exist_ok=True)
        agent.parent.mkdir(parents=True, exist_ok=True)
        if not config.exists():
            atomic_create_text(config, canonical(activation))
        if not agent.exists():
            atomic_create_text(agent, proposal['plist'])
        receipt.update(state='launch_unknown', launch_attempted=True)
        atomic_write_json(receipt_path, receipt)
        result = runner(['/bin/launchctl', 'bootstrap', domain, str(agent)],
            capture_output=True, text=True, check=False, timeout=30)
        present, listing = loaded()
        receipt['launch_returncode'] = result.returncode
        receipt['state'] = 'active' if present and matches(listing) else 'attention'
        atomic_write_json(receipt_path, receipt)
        if receipt['state'] != 'active':
            raise ValueError('Spuštění není ověřené; žádný druhý bootstrap.')
        return receipt
