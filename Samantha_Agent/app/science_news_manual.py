"""Explicit, separate weekly catch-up. Reuses the guarded one-attempt editor."""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

from app.file_persistence import FileLockTimeoutError, exclusive_file_lock
from app.science_news import ID, digest, identity, public_url, utc_now
from app.science_news_model import call_model, policy
from app.science_news_runner import INSTRUCTIONS, PRAGUE, SCHEMA, grounded_items


def run_manual(store, *, request_id, week_start, packet, confirmed=False):
    """Publish at most five fresh discoveries for one completed calendar week.

    packet contains reviewed public source excerpts, not instructions or private
    correspondence. Repeating this exact request only recovers its original
    model result. It never reopens a weekly job or clears its budget reservation.
    """
    if confirmed is not True or not isinstance(request_id, str) or not ID.fullmatch(request_id) or len(request_id) < 8:
        raise ValueError('Ruční vydání vyžaduje výslovný souhlas a stabilní request_id.')
    start_date = date.fromisoformat(week_start)
    start = datetime.combine(start_date, time(), PRAGUE)
    end = start + timedelta(days=7)
    if start_date.weekday() != 0 or end > datetime.now(PRAGUE):
        raise ValueError('Vyber dokončený kalendářní týden od pondělí.')
    if not isinstance(packet, dict) or not isinstance(packet.get('candidates'), list) or len(packet['candidates']) > 60:
        raise ValueError('Neplatné nebo příliš rozsáhlé veřejné podklady.')
    if not any(i.get('state') == 'ok' for i in packet.get('source_health', [])):
        raise ValueError('Žádný ověřený veřejný zdroj.')
    seen = set()
    for item in packet['candidates']:
        when = datetime.fromisoformat(item['published_at'])
        if when.tzinfo is None or not start <= when < end:
            raise ValueError('Podklad nepatří do vybraného týdne.')
        public_url(item['source_url'])
        if item['candidate_id'] in seen or not isinstance(item['source_excerpt'], str) or not 20 <= len(item['source_excerpt']) <= 10000:
            raise ValueError('Duplicitní nebo nedostatečný podklad.')
        seen.add(item['candidate_id'])
    policy(store)  # No journal or model before activation is verified.
    fingerprint = digest({'week_start': week_start, 'packet': packet})
    key = 'manual_' + digest(request_id)[:24]
    store.root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with exclusive_file_lock(store.root / (key + '_worker'), timeout=0):
            with store.transaction() as state:
                job = state['jobs'].get(key)
                if job and job['fingerprint'] != fingerprint:
                    raise ValueError('request_id již patří jiným podkladům nebo týdnu.')
                if job and job['state'] == 'published':
                    return {'ok': True, 'state': 'already_published', 'issue_id': key, 'item_count': len(job['items'])}
                if job is None:
                    frozen = json.loads(json.dumps(packet))
                    frozen['candidates'] = [i for i in frozen['candidates'] if identity(i) not in state['items']]
                    frozen['follows'] = [i for i in state['follows'].values() if i['active']]
                    calibration = json.loads((Path(__file__).resolve().parents[1] /
                        'memory/reports/science_news_calibration_20261108.json').read_text())
                    if not calibration.get('calibration_acceptance'):
                        raise ValueError('Filtr nemá přijatou kalibraci.')
                    frozen['calibration'] = [{'title': i['title_cs'], 'verdict': i['user_verdict'],
                        'reason': i['recommendation_reason']} for i in calibration['candidates']]
                    frozen['requested_period'] = {'start': start.isoformat(), 'end_exclusive': end.isoformat()}
                    job = {'state': 'started', 'fingerprint': fingerprint, 'request_id': request_id,
                        'packet': frozen, 'packet_digest': digest(frozen), 'available_at': utc_now(),
                        'week_start': week_start, 'updated_at': utc_now()}
                    state['jobs'][key] = job
            try:
                frozen = job['packet']
                if digest(frozen) != job['packet_digest']:
                    raise ValueError('Zmrazené podklady se změnily.')
                if 'items' not in job:
                    answer = job.get('raw_answer')
                    if answer is None:
                        answer = call_model(store, 'editor_' + key, frozen, INSTRUCTIONS, SCHEMA) if frozen['candidates'] else {'items': []}
                        with store.transaction() as state:
                            state['jobs'][key].update(raw_answer=answer, updated_at=utc_now())
                    items = grounded_items(answer, frozen, frozen['follows'])
                    with store.transaction() as state:
                        state['jobs'][key].update(items=items, state='prepared', updated_at=utc_now())
                job = store._read()['jobs'][key]
                store.publish(key, job['items'], available_at=job['available_at'], source_health=frozen['source_health'])
                with store.transaction() as state:
                    state['jobs'][key].update(state='published', updated_at=utc_now())
                return {'ok': True, 'state': 'published', 'issue_id': key, 'item_count': len(job['items'])}
            except Exception as error:
                with store.transaction() as state:
                    state['jobs'][key].update(state='attention', error_type=type(error).__name__, updated_at=utc_now())
                return {'ok': False, 'state': 'attention', 'issue_id': key,
                    'message': 'Výsledek vyžaduje ověření původní účtenky; nový placený pokus se nespouští.'}
    except FileLockTimeoutError:
        return {'ok': True, 'state': 'preparing', 'issue_id': key}
