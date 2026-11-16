"""Bounded recovery of the original editorial turn; never creates a thread/turn."""
from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.codex_appserver import final_agent_answer
from app.release_usage import normalize_usage, estimate_standard_credits
from app.science_news import digest, utc_now


def native_turn_usage(store, key, job, answer, *, sessions_root=None):
    """Validate final local usage for this one completed original turn only.

    No model calls, history export, inferred counters or partial usage. A second
    turn, mismatched final answer, changed context or unfinished log blocks it.
    """
    thread, turn = job.get('thread_id'), job.get('turn_id')
    if not isinstance(thread, str) or not re.fullmatch(r'[0-9a-f-]{36}', thread) or not turn:
        raise ValueError('Původní tah nemá ověřitelnou místní identitu.')
    root = Path(sessions_root) if sessions_root is not None else Path.home() / '.codex/sessions'
    paths = list(root.glob('*/*/*/*' + thread + '.jsonl'))
    if len(paths) != 1 or any(p.is_symlink() for p in (paths[0], *paths[0].parents)):
        raise ValueError('Původní místní záznam není jednoznačný.')
    path = paths[0]
    before = path.stat()
    if before.st_size > 2_000_000:
        raise ValueError('Původní místní záznam překročil limit.')
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError('Původní záznam se ještě mění.')
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    meta = [r['payload'] for r in rows if r.get('type') == 'session_meta']
    contexts = [r['payload'] for r in rows if r.get('type') == 'turn_context']
    events = [(n,r) for n,r in enumerate(rows) if r.get('type') == 'event_msg']
    starts = [(n,r) for n,r in events if r['payload'].get('type') == 'task_started']
    ends = [(n,r) for n,r in events if r['payload'].get('type') == 'task_complete']
    tokens = [(n,r) for n,r in events if r['payload'].get('type') == 'token_count']
    context = str((store.root / 'contexts' / digest(key)).resolve())
    if (len(meta) != 1 or meta[0].get('id') != thread or meta[0].get('cwd') != context
            or len(contexts) != 1 or len(starts) != 1 or len(ends) != 1 or not tokens):
        raise ValueError('Místní záznam nedokládá jediný původní tah.')
    c = contexts[0]; selected = job['executor']
    if (c.get('turn_id') != turn or c.get('cwd') != context or c.get('model') != selected['model']
            or c.get('effort') != selected['reasoning_effort'] or c.get('approval_policy') != 'never'
            or c.get('service_tier') not in (None,'standard')
            or c.get('sandbox_policy',{}).get('type') not in ('read-only','readOnly')
            or any(c.get('sandbox_policy',{}).get(k) is True for k in ('network_access','networkAccess'))):
        raise ValueError('Místní kontext původního tahu se neshoduje.')
    start_index, start = starts[0]; end_index, end = ends[0]; token_index, token = tokens[-1]
    if (not start_index < token_index < end_index or start['payload'].get('turn_id') != turn
            or end['payload'].get('turn_id') != turn
            or str(end['payload'].get('last_agent_message','')).strip() != answer.strip()):
        raise ValueError('Chybí dokončení a poslední spotřeba přesně původní odpovědi.')
    started = datetime.fromisoformat(start['timestamp'].replace('Z','+00:00'))
    observed = datetime.fromisoformat(token['timestamp'].replace('Z','+00:00'))
    completed = datetime.fromisoformat(end['timestamp'].replace('Z','+00:00'))
    if not datetime.fromisoformat(job['started_at']) <= started <= observed <= completed:
        raise ValueError('Časové doklady původní spotřeby se neshodují.')
    usage = None
    for _, row in tokens:
        current = normalize_usage((row['payload'].get('info') or {}).get('total_token_usage'))
        if current is None or (usage is not None and any(current[k] < usage[k] for k in current)):
            raise ValueError('Původní místní spotřeba není úplná nebo se vynulovala.')
        usage = current
    return usage, {'kind':'native_final_token_count','sha256':hashlib.sha256(raw).hexdigest(),
        'thread_id':thread,'turn_id':turn,'completed_at':end['timestamp'],'observed_at':token['timestamp']}


def complete_receipt_usage(store, key, job):
    proof = job.get('receipt', {})
    if proof.get('usage') is not None or job.get('usage_invalid') or job.get('guard_rejected'):
        return
    usage, provenance = native_turn_usage(store, key, job, proof.get('answer',''))
    with store.transaction() as state:
        current = state['jobs'][key]
        if current.get('receipt') != proof or current.get('usage_invalid') or current.get('guard_rejected'):
            raise ValueError('Původní doklad se při ověření změnil.')
        current['receipt']['usage'] = usage
        current['usage_provenance'] = provenance


def record_event(store, key, event):
    """Keep terminal proof and usage, never reasoning or a second prompt copy."""
    if event.get('method') not in ('thread/tokenUsage/updated', 'turn/completed'):
        return
    params = event.get('params', {})
    with store.transaction() as state:
        job = state['jobs'][key]
        turn = params.get('turn', {})
        if params.get('threadId') != job.get('thread_id'):
            return
        turn_id = params.get('turnId') or turn.get('id')
        if turn_id and turn_id != job.get('turn_id'):
            return
        if event.get('method') == 'thread/tokenUsage/updated':
            raw = params.get('tokenUsage', {})
            checked = normalize_usage(raw.get('total') if isinstance(raw,dict) else None, camel_case=True)
            previous = job.get('observed_usage')
            if checked is None or (previous is not None and any(checked[k] < previous[k] for k in checked)):
                job['usage_invalid'] = True
            job['observed_usage'] = checked if not job.get('usage_invalid') else None
        if event.get('method') == 'turn/completed':
            job['terminal_observed'] = turn.get('status')


def accept_result(store, key, approved):
    """Use only a persisted SDK receipt with delivery, usage and scope proof."""
    from app.science_news_model import ROLE, policy
    from app.communication import agent_roles
    job = store._read()['jobs'][key]
    if job.get('guard_rejected') or job.get('usage_invalid') or policy(store) != approved:
        raise ValueError('Rozsah nebo aktivace původního požadavku nejsou ověřené.')
    proof = job.get('receipt') or {}
    if (proof.get('delivered') is not True or proof.get('thread_id') != job.get('thread_id')
            or not isinstance(proof.get('answer'), str) or len(proof['answer']) > 200_000
            or proof.get('client_message_id') != job.get('client_message_id')
            or not proof.get('turn_id') or proof['turn_id'] != job.get('turn_id')):
        raise ValueError('Původní požadavek nemá úplný doklad doručení.')
    selected = job['executor']
    usage = normalize_usage(proof.get('usage'))
    if proof.get('measurement') is not None:
        from app.codex_usage import measurement_projection
        measured = measurement_projection(proof['measurement'])
        if (not measured or not measured['complete'] or measured['thread_id'] != job['thread_id']
                or measured['turn_id'] != job['turn_id'] or measured['usage'] != usage):
            raise ValueError('Měření původního požadavku není úplné.')
    cost = estimate_standard_credits(selected['model'], usage)
    limit = job.get('credit_limit', approved['max_job_credits'])
    output_limit = job.get('output_limit',16000)
    if type(output_limit) is not int or not 1 <= output_limit <= 16000:
        raise ValueError('Původní přejímací limit výstupu není ověřený.')
    if type(limit) not in (int,float) or not 0 < limit <= approved['max_job_credits']:
        raise ValueError('Původní rozpočet není ověřený.')
    if usage is None or cost is None or cost > limit or usage['output_tokens'] > output_limit or usage['total_tokens'] > 100_000:
        raise ValueError('Původní výsledek nemá přijatelný doklad spotřeby.')
    agent_roles.assert_current(selected, role=ROLE)
    answer = json.loads(proof['answer'])
    with store.transaction() as state:
        if job.get('budget_group'):
            parent = state['jobs'].get(job['budget_group'], {})
            keys = parent.get('part_keys', [])
            prior = keys[:keys.index(key)] if key in keys else []
            if (parent.get('kind') != 'translation_group' or parent.get('policy') != approved or key not in keys
                    or any(state['jobs'].get(k,{}).get('state') != 'completed' for k in prior)
                    or sum(state['jobs'][k]['estimated_credits'] for k in prior) + cost > parent['reserved_credits']):
                raise ValueError('Celá studie překračuje společný rozpočet.')
        state['jobs'][key].update(state='completed', answer=answer, usage=usage, estimated_credits=cost)
    return answer


def recover_model_result(store, key, payload, instructions, schema, *, client_factory=None):
    """Read precisely the original request, with no create/send/retry fallback."""
    from app.science_news_model import policy, ROLE, new_science_client
    from app.communication import agent_roles
    approved = policy(store)
    job = store._read()['jobs'].get(key)
    if not job:
        raise ValueError('Chybí původní modelový pokus.')
    if job.get('guard_rejected'):
        raise ValueError('Původní výstup porušil omezení; nelze jej automaticky přijmout.')
    if job.get('phase') == 'preflight' and not job.get('thread_id'):
        from app.science_news_model import call_model
        return call_model(store,key,payload,instructions,schema,client_factory=client_factory or new_science_client,
                          budget_group=job.get('budget_group'),output_limit=job.get('output_limit',16000))
    from app.science_news_model import model_fingerprint
    expected = model_fingerprint(payload, instructions, schema, approved, job.get('budget_group'),job.get('output_limit',16000))
    if job.get('fingerprint') != expected:
        raise ValueError('Otisk původního požadavku se změnil.')
    if job['state'] == 'completed':
        return job['answer']
    if job.get('receipt'):
        complete_receipt_usage(store, key, job)
        return accept_result(store, key, approved)
    if (not job.get('persistent') or not job.get('thread_id') or not job.get('client_message_id')
            or not job.get('executor')):
        raise ValueError('Starý dočasný pokus nemá obnovitelný doklad; žádné opakování.')
    selected = job['executor']
    agent_roles.assert_current(selected, role=ROLE)
    context = store.root / 'contexts' / digest(key)
    with (client_factory or new_science_client)() as client:
        # Resume attaches ONLY the pinned existing thread. It never starts work.
        client.resume_thread(job['thread_id'], cwd=context, model=selected['model'],
            developer_instructions=instructions, base_instructions=instructions,
            sandbox='read-only', approval_policy='never')
        page = client.transport.request('thread/turns/list', {'threadId': job['thread_id'],
                  'limit': 2, 'sortDirection': 'asc', 'itemsView': 'full'})
    turns = page.get('data')
    if page.get('nextCursor') or not isinstance(turns, list) or len(turns) != 1 or len(json.dumps(turns)) > 500_000:
        raise ValueError('Historie původního vlákna není jednoznačná.')
    turn = turns[0]
    if turn.get('status') != 'completed' or not turn.get('id') or (job.get('turn_id') and turn['id'] != job['turn_id']):
        raise ValueError('Původní tah není potvrzený jako dokončený.')
    items = turn.get('items', [])
    if not items or any(i.get('type') not in ('userMessage', 'agentMessage', 'reasoning', 'contextCompaction') for i in items):
        raise ValueError('Historie obsahuje neověřené použití nástroje.')
    users = [i for i in items if i['type'] == 'userMessage']
    if len(users) != 1 or users[0].get('clientId') != job['client_message_id']:
        raise ValueError('Historie neprokazuje původní uživatelský vstup.')
    answer = final_agent_answer([i for i in items if i['type'] == 'agentMessage'])
    if not answer or len(answer) > 200_000:
        raise ValueError('Chybí jednoznačná finální odpověď.')
    # Full usage is a fresh one-turn thread total, observed before disconnect.
    usage = job.get('observed_usage')
    with store.transaction() as state:
        state['jobs'][key].update(turn_id=turn['id'], raw_answer=answer,
            receipt={'answer': answer, 'thread_id': job['thread_id'], 'turn_id': turn['id'],
                     'client_message_id': job['client_message_id'], 'delivered': True, 'usage': usage},
            recovered_at=utc_now())
    complete_receipt_usage(store, key, store._read()['jobs'][key])
    return accept_result(store, key, approved)


def issue_closed(job):
    value = job.get('resolution')
    if not isinstance(value,dict) or value.get('state') != 'closed_without_output':
        return False
    try:
        return (isinstance(value['request_id'],str) and 8 <= len(value['request_id']) <= 120
                and isinstance(value['previous_fingerprint'],str) and len(value['previous_fingerprint']) == 64
                and all(c in '0123456789abcdef' for c in value['previous_fingerprint'])
                and datetime.fromisoformat(value['closed_at']).tzinfo is not None)
    except (KeyError,TypeError,ValueError):
        return False


def weekly_status(store, *, now=None, activated_at=None, enabled=True):
    """A safe UI projection; no recovery, writes, server or model calls."""
    from app.science_news_runner import slot
    now = now or datetime.now(ZoneInfo('Europe/Prague'))
    state = store._read(); jobs = state['jobs']
    due = slot(now); due_key = 'weekly_' + due.strftime('%Y%m%d')
    rows = [(k,j) for k,j in jobs.items() if k.startswith('weekly_')]
    unresolved = [(k,j) for k,j in rows if j.get('state') in ('started','attention') and not issue_closed(j)]
    key, job = sorted(unresolved)[0] if unresolved else (due_key,jobs.get(due_key,{}))
    if (not enabled or (activated_at is not None and due < activated_at)) and not unresolved:
        level, text = 'waiting', 'Příprava čeká na další schválený páteční termín.'
    elif unresolved:
        fresh = job.get('updated_at') and 0 <= (now-datetime.fromisoformat(job['updated_at'])).total_seconds() < 300
        level = 'preparing' if job.get('state') == 'started' and fresh else 'attention'
        text = ('Připravuji páteční výběr.' if level == 'preparing' else 'Příprava vědeckého výběru se přerušila. Výsledek není ověřený; automaticky jej neopakuji.')
    elif issue_closed(job):
        level, text = 'closed_without_output', 'Přerušené vydání bylo uzavřeno bez výsledku. Podklady zůstávají zachované; tento pokus se neopakuje.'
    elif job.get('state') == 'prepared':
        late = now >= due + timedelta(minutes=15)
        level = 'overdue' if late else 'prepared'
        text = ('Výběr je připravený, ale jeho zveřejnění se opozdilo. Čeká na nejbližší běh služby.'
                if late else 'Výběr je připravený a čeká na zveřejnění v pátek od 09:00.')
    elif not job and now >= due-timedelta(minutes=45):
        level, text = 'overdue', 'Páteční výběr zatím nebyl připraven. Čeká na nejbližší běh služby.'
    elif not job:
        level, text = 'waiting', 'Příprava čeká na nejbližší běh služby.'
    else:
        level, text = 'ok', 'Příprava vědeckých novinek nemá nevyřešenou chybu.'
    return {'state':level, 'attention':level in ('attention','overdue','closed_without_output'),
            'issue_date':key.removeprefix('weekly_'), 'message':text,
            'blocking':bool(unresolved), 'checked_at':now.isoformat()}


def close_interrupted_issue(store, key, *, expected_fingerprint, request_id, confirmed=False):
    """Retain unknown model state/budget and all data; never publish or resubmit."""
    if not confirmed or not isinstance(request_id,str) or not 8 <= len(request_id) <= 120:
        raise ValueError('Uzavření bez výsledku vyžaduje konkrétní souhlas a identitu.')
    from app.file_persistence import exclusive_file_lock
    with exclusive_file_lock(store.root / 'weekly_worker'):
        with store.transaction() as state:
            job = state['jobs'].get(key)
            if not key.startswith('weekly_') or not job or job.get('state') != 'attention':
                raise ValueError('Nejde o přerušené vydání.')
            if job.get('resolution'):
                if not issue_closed(job):
                    raise ValueError('Původní uzavření není platné.')
                if job['resolution'].get('request_id') != request_id:
                    raise ValueError('Vydání již uzavřel jiný požadavek.')
                return {'ok':True,'state':'closed_without_output','replayed':True}
            if digest(job) != expected_fingerprint:
                raise ValueError('Původní pokus se od auditu změnil.')
            job['resolution']={'state':'closed_without_output','request_id':request_id,
                               'closed_at':utc_now(),'previous_fingerprint':expected_fingerprint}
    return {'ok':True,'state':'closed_without_output','model_called':False}
