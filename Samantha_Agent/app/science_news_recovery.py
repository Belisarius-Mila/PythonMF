"""Bounded recovery of the original editorial turn; never creates a thread/turn."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.codex_appserver import final_agent_answer
from app.release_usage import normalize_usage, estimate_standard_credits
from app.science_news import digest, utc_now


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
    if type(limit) not in (int,float) or not 0 < limit <= approved['max_job_credits']:
        raise ValueError('Původní rozpočet není ověřený.')
    if usage is None or cost is None or cost > limit or usage['output_tokens'] > 16_000 or usage['total_tokens'] > 100_000:
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
    from app.science_news_model import policy, ROLE
    from app.communication import agent_roles
    from app.communication.luna_release import new_luna_client
    approved = policy(store)
    job = store._read()['jobs'].get(key)
    if not job:
        raise ValueError('Chybí původní modelový pokus.')
    if job.get('guard_rejected'):
        raise ValueError('Původní výstup porušil omezení; nelze jej automaticky přijmout.')
    if job.get('phase') == 'preflight' and not job.get('thread_id'):
        from app.science_news_model import call_model
        return call_model(store,key,payload,instructions,schema,client_factory=client_factory or new_luna_client,
                          budget_group=job.get('budget_group'))
    from app.science_news_model import model_fingerprint
    expected = model_fingerprint(payload, instructions, schema, approved, job.get('budget_group'))
    if job.get('fingerprint') != expected:
        raise ValueError('Otisk původního požadavku se změnil.')
    if job['state'] == 'completed':
        return job['answer']
    if job.get('receipt'):
        return accept_result(store, key, approved)
    if (not job.get('persistent') or not job.get('thread_id') or not job.get('client_message_id')
            or not job.get('executor')):
        raise ValueError('Starý dočasný pokus nemá obnovitelný doklad; žádné opakování.')
    selected = job['executor']
    agent_roles.assert_current(selected, role=ROLE)
    context = store.root / 'contexts' / digest(key)
    with (client_factory or new_luna_client)() as client:
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
