"""One explicitly requested complete study, bounded parts and one shared budget."""
from __future__ import annotations

from datetime import datetime

from app.communication.agent_roles import load_role
from app.file_persistence import exclusive_file_lock, FileLockTimeoutError
from app.science_news import digest, utc_now
from app.science_news_model import (ROLE, ScienceBudgetError, call_model, monthly_charged,
    policy, TRANSLATION_INSTRUCTIONS, TRANSLATION_SCHEMA)
from app.science_news_runner import PRAGUE

MAX_SOURCE = 300_000
PART_SIZE = 20_000


class TranslationBusy(ValueError):
    pass


def split_source(text):
    if not isinstance(text, str) or not 200 <= len(text) <= MAX_SOURCE:
        raise ValueError('Celý zdroj překročil povolený rozsah překladu.')
    parts = []
    while len(text) > PART_SIZE:
        boundary = text.rfind('\n', PART_SIZE // 2, PART_SIZE)
        if boundary < 0:
            boundary = text.rfind(' ', PART_SIZE // 2, PART_SIZE)
        boundary = boundary + 1 if boundary >= 0 else PART_SIZE
        parts.append(text[:boundary])
        text = text[boundary:]
    if text:
        parts.append(text)
    return parts


def translate_study(store, item, *, model=call_model):
    """Only an explicit POST starts/resumes work; GET never calls this function."""
    try:
        with exclusive_file_lock(store.root / ('translation_worker_' + digest(item['id'])), timeout=0):
            return _translate_locked(store, item, model=model)
    except FileLockTimeoutError as error:
        raise TranslationBusy('Původní překlad stále běží.') from error


def _translate_locked(store, item, *, model):
    approved = policy(store)
    binding = load_role(role=ROLE)
    source = item['source_text']
    if item.get('translation_permission') not in ('cc-by', 'cc-by-sa', 'cc0', 'public-domain', 'user-provided'):
        raise ValueError('Zdroj nemá ověřené oprávnění k překladu.')
    parts = split_source(source)
    payloads = [{'source_text': part, 'part_index': index + 1, 'part_count': len(parts)}
                for index, part in enumerate(parts)]
    key = 'translation_' + item['id']
    part_keys = ['model_translation_' + item['id'] + '_part_' + str(index + 1) for index in range(len(parts))]
    fingerprint = digest({'source': source, 'url': item['source_url'], 'policy': approved,
                          'role': binding['policy_digest'], 'parts': payloads})
    month = datetime.now(PRAGUE).strftime('%Y-%m')
    with store.transaction() as state:
        old = state['jobs'].get(key, {})
        if old.get('kind') == 'translation_group':
            if old.get('fingerprint') != fingerprint:
                raise ValueError('Původní studie, role nebo rozpočet se změnily.')
        else:
            # Legacy uncertain single-turn attempts can never become a new batch.
            if state['jobs'].get('model_translation_' + item['id']):
                raise ValueError('Nejprve ověř původní nedělený překlad.')
            state['jobs'][key] = {'kind': 'translation_group', 'fingerprint': fingerprint,
                'policy': approved, 'role_policy_digest': binding['policy_digest'], 'month': month,
                'reserved_credits': 0, 'part_keys': part_keys, 'parts': payloads,
                'translations': {}, 'completed_parts': 0, 'part_count': len(parts), 'started_at': utc_now()}
        parent = state['jobs'][key]
        no_budget = (parent['reserved_credits'] == 0 and
            monthly_charged(state, month, exclude=key) + approved['max_job_credits'] > approved['max_month_credits'])
        if no_budget:
            parent.update(state='attention', message='Měsíční rozpočet nemá rezervu pro celou studii. Žádný modelový tah nezačal.', updated_at=utc_now())
        else:
            parent.update(reserved_credits=approved['max_job_credits'], state='running',
                          message='Překládám celou studii včetně metod…', updated_at=utc_now())
    if no_budget:
        raise ScienceBudgetError('Měsíční rozpočet nemá rezervu pro celou studii.')
    try:
        for index, payload in enumerate(payloads):
            current_item = store.item(item['id'])
            if (digest(current_item.get('source_text')) != digest(source) or current_item['source_url'] != item['source_url']
                    or current_item.get('translation_permission') != item['translation_permission']):
                raise ValueError('Zdroj nebo oprávnění se během překladu změnily.')
            current = store._read()['jobs'][key]
            if str(index) in current['translations']:
                continue
            answer = model(store, part_keys[index], payload, TRANSLATION_INSTRUCTIONS,
                           TRANSLATION_SCHEMA, budget_group=key)
            text = answer.get('translation', '')
            if (set(answer) != {'translation', 'complete'} or answer['complete'] is not True
                    or not isinstance(text, str) or not .3 * len(payload['source_text']) <= len(text) <= 4 * len(payload['source_text'])):
                raise ValueError('Část překladu není úplná.')
            with store.transaction() as state:
                state['jobs'][key]['translations'][str(index)] = text
                state['jobs'][key].update(completed_parts=index+1, updated_at=utc_now())
        if policy(store) != approved or load_role(role=ROLE)['policy_digest'] != binding['policy_digest']:
            raise ValueError('Schválená role nebo rozpočet se během překladu změnily.')
        with store.transaction() as state:
            parent = state['jobs'][key]
            current = state['items'][item['id']]
            if (digest(current.get('source_text')) != digest(source) or current['source_url'] != item['source_url']
                    or current.get('translation_permission') != item['translation_permission']):
                raise ValueError('Zdrojová studie se během překladu změnila.')
            children = [state['jobs'].get(k, {}) for k in part_keys]
            if any(j.get('state') != 'completed' or j.get('budget_group') != key for j in children):
                raise ValueError('Části nemají úplné původní účtenky.')
            cost = sum(j['estimated_credits'] for j in children)
            if cost > approved['max_job_credits']:
                raise ScienceBudgetError('Celá studie překročila schválený rozpočet.')
            current['translation'] = '\n\n'.join(parent['translations'][str(i)] for i in range(len(parts)))
            parent.update(state='completed', estimated_credits=cost, updated_at=utc_now(), message='Celá studie je přeložená.')
    except Exception as error:
        with store.transaction() as state:
            parent = state['jobs'][key]
            message = ('Schválený rozpočet celé studie nestačí na zbývající části. Hotové části jsou zachované; limit automaticky nezvyšuji.'
                       if isinstance(error, ScienceBudgetError) else
                       'Překlad se přerušil; hotové části jsou zachované. Pokračovat lze jen ověřením původních účtenek, bez opakování nejisté části.')
            parent.update(state='attention', message=message, error_type=type(error).__name__, updated_at=utc_now())
        raise
