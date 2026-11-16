"""Preview and explicitly apply the owned hourly calendar schedule."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess

from app.family_calendar_delivery_config import load_family_calendar_delivery_config, DeliveryConfigMode
from app.family_calendar_delivery_readiness import (
    DEFAULT_FAMILY_CALENDAR_PLANNER_PATH, DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
    FAMILY_CALENDAR_PLANNER_LABEL, _planner_document_matches,
)
from app.family_calendar_delivery_coordinator import DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH
from app.file_persistence import atomic_create_bytes, atomic_replace_text_under_external_lock, atomic_write_json, exclusive_file_lock

GLOBAL_CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
HOURLY_CONFIRMATION = "POTVRZUJI HODINOVOU KONTROLU RODINNEHO KALENDARE"
PROJECT = Path(__file__).resolve().parents[1]


def hourly_schedule_active():
    path = PROJECT / 'data/private/family_calendar/hourly_schedule/policy.json'
    try:
        return (path.resolve() == path and json.loads(path.read_text())
                == {'version': 1, 'enabled': True})
    except (OSError, ValueError):
        return False


def hourly_planner_document(document):
    """Preserve interpreter and owned entry point; schedule hourly from 08:00."""
    result = dict(document)
    result.update(StartCalendarInterval=[{"Hour": hour, "Minute": 0} for hour in range(8, 24)], RunAtLoad=True)
    return result


def _snapshot(planner_path, runner_path):
    path = Path(planner_path)
    if path.is_symlink() or path.parent.resolve() != path.parent or path.name != FAMILY_CALENDAR_PLANNER_LABEL + '.plist':
        raise ValueError('Planner path is not the owned calendar agent')
    s = path.stat()
    parent = path.parent.stat()
    if (s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) != 0o600 or not stat.S_ISREG(s.st_mode)
            or parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) & 0o022 or s.st_size > 64_000):
        raise ValueError('Planner ownership or permissions changed')
    payload = path.read_bytes()
    document = plistlib.loads(payload)
    if (not _planner_document_matches(document, runner_path) or document.get('ProcessType') != 'Background'
            or type(document.get('RunAtLoad')) is not bool):
        raise ValueError('Existing planner contract is not supported')
    target = plistlib.dumps(hourly_planner_document(document))
    return payload, target


def preview_hourly_schedule(*, planner_path=DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
                            runner_path=DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH):
    before, after = _snapshot(planner_path, runner_path)
    fingerprint = hashlib.sha256(before + b'\0' + after + b'\0' + str(Path(planner_path)).encode()).hexdigest()
    return {'status': 'already_hourly' if before == after else 'preview', 'fingerprint': fingerprint,
            'hours': list(range(8, 24)), 'minute': 0, 'run_at_load': True,
            'before_08_no_send': True, 'event_day_catch_up': True,
            'may_start_automatic_runner_on_apply': True,
            'requires_confirmation': HOURLY_CONFIRMATION, 'writes_performed': False,
            'transport_called': False, 'redacted': True}


def _launchctl(*args):
    return subprocess.run(['/bin/launchctl', *args], capture_output=True, timeout=20)


def _runtime_ready():
    from app.communication.luna_release import http_call
    audit = http_call('/api/human-adam/deploy-audit')
    health = http_call('/api/server/health')
    return bool(audit.get('ready') and audit.get('expected_code_stamp')
                == health.get('server', {}).get('code_stamp'))


def apply_hourly_schedule(*, fingerprint, confirmation, global_confirmation,
                          planner_path=DEFAULT_FAMILY_CALENDAR_PLANNER_PATH,
                          runner_path=DEFAULT_FAMILY_CALENDAR_PLANNER_RUNNER_PATH,
                          worker_path=DEFAULT_FAMILY_CALENDAR_DELIVERY_WORKER_PATH,
                          store_root=None, command=_launchctl, runtime_ready=_runtime_ready):
    """One owned replacement, with durable intent and no retry on uncertain bootstrap.

    Runtime readers must be updated before the scheduler may persist D-0/retry
    records. The confirmation is separate from code publication.
    """
    if confirmation != HOURLY_CONFIRMATION or global_confirmation != GLOBAL_CONFIRMATION:
        raise ValueError('Hourly scheduling needs the exact approved scope and safety acknowledgement')
    root = Path(store_root or PROJECT / 'data/private/family_calendar/hourly_schedule')
    if root.resolve() != root:
        raise ValueError('Schedule receipts cannot use symlinks')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with exclusive_file_lock(root / 'operation'):
        preview = preview_hourly_schedule(planner_path=planner_path, runner_path=runner_path)
        if fingerprint != preview['fingerprint']:
            raise ValueError('Planner changed since preview')
        if preview['status'] == 'already_hourly':
            if not (root / 'policy.json').exists():
                raise ValueError('Hourly planner has no completed activation receipt; inspect it first')
            return preview
        attempt_path = root / (fingerprint + '.json')
        if attempt_path.exists():
            raise ValueError('Inspect the original schedule attempt; do not repeat it')
        if not runtime_ready():
            raise ValueError('Deploy the compatible calendar reader before enabling hourly checks')
        config = load_family_calendar_delivery_config()
        if config.mode is not DeliveryConfigMode.ENABLED:
            raise ValueError('Existing calendar automation must already be enabled')
        before, after = _snapshot(planner_path, runner_path)
        service = f'gui/{os.getuid()}/{FAMILY_CALENDAR_PLANNER_LABEL}'
        if command('print', service).returncode:
            raise ValueError('Existing calendar planner is not loaded')
        receipt = {'state': 'requested', 'stage': 'unload', 'fingerprint': fingerprint,
                   'transport_called': False, 'redacted': True}
        atomic_create_bytes(root / (fingerprint + '.previous.plist'), before)
        atomic_write_json(attempt_path, receipt)
        with exclusive_file_lock(worker_path):
            try:
                if command('bootout', service).returncode:
                    raise ValueError('Planner unload not confirmed')
                if command('print', service).returncode != 113:
                    raise ValueError('Planner absence not confirmed')
                receipt['stage'] = 'replace'; atomic_write_json(attempt_path, receipt)
                if _snapshot(planner_path, runner_path)[0] != before:
                    raise ValueError('Planner changed during transition')
                atomic_replace_text_under_external_lock(Path(planner_path), after.decode())
                receipt['stage'] = 'bootstrap'; atomic_write_json(attempt_path, receipt)
                # Persist authorization before RunAtLoad can start the worker.
                atomic_write_json(root / 'policy.json', {'version': 1, 'enabled': True})
                if command('bootstrap', f'gui/{os.getuid()}', str(planner_path)).returncode:
                    raise ValueError('Planner load not confirmed')
                receipt['stage'] = 'verify'; atomic_write_json(attempt_path, receipt)
                if command('print', service).returncode or Path(planner_path).read_bytes() != after:
                    raise ValueError('Hourly planner verification failed')
                receipt.update(state='completed', stage='verified', writes_performed=True)
            except Exception as error:
                # A started worker may already be sending. Never boot it out or
                # automatically repeat bootstrap after an uncertain result.
                receipt.update(state='attention', failure_type=type(error).__name__, writes_performed=True)
            atomic_write_json(attempt_path, receipt)
        return receipt


def hourly_schedule_tool(*, apply=False, fingerprint='', confirmation='', global_confirmation=''):
    try:
        result = (apply_hourly_schedule(fingerprint=fingerprint, confirmation=confirmation,
                   global_confirmation=global_confirmation) if apply else preview_hourly_schedule())
    except Exception as error:
        result = {'status': 'blocked', 'failure_type': type(error).__name__, 'redacted': True}
    return json.dumps(result, ensure_ascii=False)
