"""HA-09: read-only adapters for exact checkpoint/release receipts.

No status recovery, Git commands, dispatch, polling workers or receipt mutation.
The source stores validate private documents; this projection exposes IDs and
allowlisted phases only, never summaries, prompts, tokens or worker output.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

from app.communication.human_adam_work import operation_id, WorkError
from app.release_usage import normalize_usage

HEX = re.compile(r'[a-f0-9]{40}\Z')
JOB = re.compile(r'[a-f0-9]{32,64}\Z')
RELEASE_PHASES = {'handoff', 'protection', 'push_requested', 'validation',
                  'deploy_requested', 'publish_requested', 'verification', 'return', 'done'}


def _time(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except (ValueError, OverflowError):
        return None


def _parent(record, workstream):
    if not isinstance(record, dict) or not isinstance(record.get('scope'), dict):
        return None
    scope = record['scope']
    try:
        exact = operation_id(workstream, record.get('client_request_id', ''))
    except (ValueError, TypeError, WorkError):
        return None
    if (scope.get('workstream_id') != workstream or exact != record.get('operation_id')
            or not isinstance(scope.get('thread_id'), str) or not scope['thread_id']
            or scope.get('thread_id') != record.get('thread_id')
            or record.get('delivery_state') != 'confirmed'):
        return None
    return {'operation_id':exact, 'client_request_id':record['client_request_id'],
            'thread_id':scope['thread_id'], 'profile_id':scope.get('profile_id', '')}


def build_server_job_progress(*, workstream_id, thread_id, latest_client_id, observed_at,
                              records=(), completion_job=None,
                              releases=(), deployment=None, consistent=True, source_errors=(),
                              latest_received_at='', model_running=False):
    observed = _time(observed_at)
    parents = {}
    for record in records[:64]:
        parent = _parent(record, workstream_id)
        if parent:
            parents[parent['client_request_id']] = (parent, record)
    jobs = []
    invalid_source = False

    def add(kind, key, state, phase, created, updated, parent=None, **extra):
        start, end = _time(created), _time(updated)
        if (not isinstance(key, str) or not JOB.fullmatch(key) or not observed
                or not start or not end or not start <= end <= observed):
            return
        current = bool(parent and parent['thread_id'] == thread_id
                       and parent['client_request_id'] == latest_client_id)
        jobs.append({'job_id':key, 'kind':kind, 'state':state, 'phase':phase,
            'created_at':created, 'updated_at':updated, 'parent':parent,
            'current':current, 'reported_active':state in {'queued','running','retry_waiting'},
            'liveness':'not_checked', **extra})

    job = completion_job or {}
    if job.get('workstream_id') == workstream_id:
        pair = parents.get(job.get('client_message_id'))
        if pair and pair[0]['profile_id'] == job.get('profile_id'):
            parent, record = pair
            state = job.get('state')
            if state in {'queued','running','retry_waiting','completed','failed'}:
                verified = bool(state == 'completed' and HEX.fullmatch(job.get('checkpoint_head','')))
                add('checkpoint', job.get('idempotency_key'), 'attention' if state == 'completed' and not verified else state,
                    {'queued':'queued','running':'checkpoint_validation','retry_waiting':'retry_waiting',
                     'completed':'checkpoint_completed' if verified else 'attention','failed':'attention'}[state],
                    job.get('created_at'),job.get('updated_at'),parent,
                    outcome='checkpoint_verified' if verified else 'unverified',
                    verified_head=job['checkpoint_head'] if verified else '')
    # Persisted HA-04 terminal references remain useful after the global job slot
    # advances. Never turn a stale active reference into a live checkpoint.
    for parent, record in parents.values():
        reference = record.get('completion') or {}
        if (reference.get('kind') == 'completion' and reference.get('state') in {'completed','failed'}
                and not any(j['kind'] == 'checkpoint' and j['job_id'] == reference.get('job_id') for j in jobs)):
            done = reference['state'] == 'completed'
            add('checkpoint',reference.get('job_id'),reference['state'],
                'completion_completed' if done else 'attention',record.get('created_at'),
                record.get('updated_at'),parent,outcome='completion_confirmed' if done else 'unverified',verified_head='')

    for release in releases[:32]:
        if release.get('workstream_id') != workstream_id:
            continue
        target, head = release.get('deployment_target'), release.get('target_head')
        state, phase = release.get('state'), release.get('phase')
        if (target not in {'cockpit','github_pages'} or not isinstance(head,str) or not HEX.fullmatch(head)
                or state not in {'queued','running','completed','attention','dry_run_completed','returning'}
                or phase not in RELEASE_PHASES):
            invalid_source = True
            continue
        binding = release.get('parent_work')
        parent = None
        if isinstance(binding,dict):
            pair = parents.get(binding.get('client_request_id'))
            if pair and binding == pair[0] and release.get('parent_thread_id') == pair[0]['thread_id']:
                parent = pair[0]
        verification = release.get('verification')
        verification = verification if isinstance(verification,dict) else {}
        usage_proof = release.get('luna_proof')
        usage_proof = usage_proof if isinstance(usage_proof,dict) else {}
        verified = (release.get('dry_run') is False and verification.get('state') == 'deployed'
                    and verification.get('main_head') == head and verification.get('deployment_target') == target)
        if target == 'cockpit':
            verified = verified and verification.get('code_stamp') == release.get('expected_code_stamp') and verification.get('smoke_count') == 5
        else:
            verified = (verified and type(verification.get('deployment_id')) is int
                        and verification['deployment_id'] > 0 and verification.get('smoke_http_status') == 200)
        late = False
        proof = deployment or {}
        if (not verified and observed and target == 'cockpit' and release.get('dry_run') is False
                and proof.get('state') == 'deployed' and proof.get('workstream_id') == workstream_id
                and proof.get('main_head') == head and proof.get('expected_code_stamp') == release.get('expected_code_stamp')
                and proof.get('smoke_count') == 5 and _time(proof.get('deployed_at'))
                and _time(release.get('created_at'))
                and _time(release['created_at']) <= _time(proof['deployed_at']) <= observed):
            verified = late = True
        add('release',release.get('job_id'), 'running' if state == 'returning' else state, phase,
            release.get('created_at'),release.get('updated_at'),parent,
            deployment_target=target, target_head=head,
            push_state=release.get('push_state') if release.get('push_state') in {'not_started','requested','confirmed','already_aligned','uncertain'} else 'unverified',
            deployment_state=release.get('deployment_state') if release.get('deployment_state') in {'not_started','requested','confirmed','uncertain'} else 'unverified',
            outcome='deployment_verified' if verified else 'dry_run_completed' if state == 'dry_run_completed' and release.get('dry_run') is True else 'unverified',
            verified_head=head if verified else '', later_verified=late,
            dry_run=release.get('dry_run') is True,
            executor_usage=normalize_usage(usage_proof.get('token_usage')),
            request_origin='terminal' if release.get('return_channel') == 'caller' else 'portal')
        if (jobs and jobs[-1]['job_id'] == release.get('job_id') and parent is None
                and release.get('return_channel') == 'caller' and not model_running
                and _time(latest_received_at) and _time(release.get('created_at'))
                and _time(release['created_at']) >= _time(latest_received_at)):
            jobs[-1]['current'] = True
    jobs.sort(key=lambda row:(_time(row['created_at']),row['job_id']),reverse=True)
    jobs = jobs[:16]
    frontier, seen = [], set()
    for row in jobs:
        if not row['current']:
            continue
        family = (row['kind'],row.get('deployment_target','') if row['kind'] == 'release'
                  else (row.get('parent') or {}).get('operation_id',''))
        if family not in seen:
            frontier.append(row)
            seen.add(family)
    active = next((row for row in frontier if row['reported_active']
        or row['state'] in {'failed','attention'} and row['outcome'] == 'unverified'),None)
    # Terminal requests are independent project operations, never silently
    # attributed to the last model turn. They remain visible in history.
    healthy = bool(consistent and observed and not source_errors and not invalid_source)
    if not healthy:
        active = None
    value = {'schema_version':1,'read_only':True,'writes_performed':False,
        'scope':{'workstream_id':workstream_id,'thread_id':thread_id},
        'consistent':healthy,'jobs':jobs,'current_job_id':active['job_id'] if active else None,
        'source_unavailable':bool(source_errors or invalid_source),'actions':{'retry':False,'publish':False,'recover':False}}
    value['revision'] = hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    return value
