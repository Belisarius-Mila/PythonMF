"""Private, separately authorized day-of-event SMS alongside calendar email."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import json
import re
import stat
from zoneinfo import ZoneInfo

from app.family_calendar import DEFAULT_FAMILY_CALENDAR_PATH, load_family_people, upcoming_family_events
from app.file_persistence import (atomic_create_bytes, atomic_write_json, exclusive_file_lock,
                                  FileLockTimeoutError)
from app.work_repository import JsonWorkRepository, RepositoryMutation
from app.family_calendar_sms_transport import MessagesSMS, SMSOutcome

ROOT = Path(__file__).resolve().parents[1] / 'data/private/family_calendar/sms'
TZ = ZoneInfo('Europe/Prague')
TEST_CONFIRMATION = 'POTVRZUJI JEDNU ZKUSEBNI SMS RODINNEHO KALENDARE'
ENABLE_CONFIRMATION = 'POTVRZUJI AUTOMATICKE SMS RODINNEHO KALENDARE'
STATES = {'sending', 'sent', 'delivered', 'not_sent', 'unknown', 'failed'}
SMS_TEMPLATE = 'Speciálně pro Vás {salutation}: Dnes má {event_label} {person}.'
TEST_TEMPLATE = 'Speciálně pro Vás {salutation}: Zkušební upozornění rodinného kalendáře.'


class SMSAttemptError(RuntimeError):
    """The durable attempt could not be completed; never replay blindly."""

    def __init__(self, message, *, transport_called=True):
        super().__init__(message)
        self.transport_called = transport_called


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def policy(config):
    return {**{key: config[key] for key in ('schema', 'recipient_id', 'phone', 'salutation', 'hour', 'timezone', 'service')},
            'template': SMS_TEMPLATE, 'test_template': TEST_TEMPLATE}


def validate_config(value):
    fields = {'schema', 'recipient_id', 'phone', 'salutation', 'hour', 'timezone', 'service', 'enabled', 'authorization'}
    if (not isinstance(value, dict) or set(value) != fields or type(value['schema']) is not int or value['schema'] != 1
            or value['recipient_id'] != 'calendar-sms-1' or type(value['enabled']) is not bool
            or type(value['hour']) is not int or value['hour'] != 9 or value['timezone'] != 'Europe/Prague'
            or value['service'] != 'SMS' or not isinstance(value['phone'], str)
            or not re.fullmatch(r'\+[1-9][0-9]{7,14}', value['phone'])
            or not isinstance(value['salutation'], str) or not 1 <= len(value['salutation']) <= 80
            or value['salutation'] != value['salutation'].strip() or any(ord(c) < 32 for c in value['salutation'])
            or not isinstance(value['authorization'], str)):
        raise ValueError('Soukromé SMS pravidlo nelze ověřit.')
    if value['enabled'] and value['authorization'] != digest(policy(value)):
        raise ValueError('SMS pravidlo neodpovídá schválenému příjemci a textu.')
    return value


def message_for(config, event=None):
    if event is None:
        return TEST_TEMPLATE.format(salutation=config['salutation'])
    if event.event_type not in ('birthday', 'name_day') or event.days_until != 0:
        raise ValueError('SMS patří jen dnešnímu svátku nebo narozeninám.')
    kind = 'narozeniny' if event.event_type == 'birthday' else 'svátek'
    relation = f' ({event.relation})' if event.relation else ''
    text = SMS_TEMPLATE.format(salutation=config['salutation'], event_label=kind, person=event.display_name+relation)
    if len(text) > 500 or any(ord(c) < 32 for c in text):
        raise ValueError('Text SMS nelze bezpečně připravit.')
    return text


class CalendarSMS:
    def __init__(self, root=ROOT, *, people_path=DEFAULT_FAMILY_CALENDAR_PATH, adapter=None,
                 clock=lambda: datetime.now(TZ)):
        self.root, self.people_path, self.adapter, self.clock = Path(root), Path(people_path), adapter, clock
        self.config_path = self.root / 'config.json'
        self.repo = JsonWorkRepository(self.root/'delivery.json')

    def _private(self, path):
        if path.resolve() != path or path.is_symlink() or not path.is_file():
            raise ValueError('Soukromý SMS soubor nelze ověřit.')
        if stat.S_IMODE(path.stat().st_mode) != 0o600 or stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
            raise ValueError('SMS data nemají soukromá oprávnění.')

    def _config(self):
        self._private(self.config_path)
        return validate_config(json.loads(self.config_path.read_text()))

    def _now(self):
        value = self.clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ValueError('Čas SMS musí obsahovat časové pásmo.')
        return value.astimezone(TZ)

    def _ledger(self):
        self._private(self.repo.path)
        value = self.repo.read()
        if value.get('schema') != 1 or not isinstance(value.get('records'), dict):
            raise ValueError('Doručovací evidenci SMS nelze ověřit.')
        for key, record in value['records'].items():
            if (not re.fullmatch('[0-9a-f]{64}', key) or not isinstance(record, dict)
                    or record.get('state') not in STATES or type(record.get('attempt')) is not int
                    or not 1 <= record['attempt'] <= 24 or record.get('kind') not in ('event', 'test')
                    or not isinstance(record.get('event_key'), str)
                    or key != digest(['calendar-sms-1', record['event_key']])
                    or not isinstance(record.get('phone'), str) or not re.fullmatch(r'\+[1-9][0-9]{7,14}', record['phone'])
                    or not isinstance(record.get('text'), str) or not 1 <= len(record['text']) <= 500
                    or not isinstance(record.get('policy'), str) or not re.fullmatch('[0-9a-f]{64}', record['policy'])
                    or datetime.fromisoformat(record['at']).tzinfo is None):
                raise ValueError('Doručovací evidenci SMS nelze ověřit.')
        return value

    def prepare(self, *, phone, salutation):
        """Create-only disabled private draft; never overwrite existing consent/history."""
        config = validate_config({'schema': 1, 'recipient_id': 'calendar-sms-1', 'phone': phone,
            'salutation': salutation, 'hour': 9, 'timezone': 'Europe/Prague', 'service': 'SMS',
            'enabled': False, 'authorization': ''})
        if self.root.resolve() != self.root:
            raise ValueError('SMS root nesmí být symbolický odkaz.')
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if stat.S_IMODE(self.root.stat().st_mode) != 0o700:
            raise ValueError('SMS adresář není soukromý.')
        with exclusive_file_lock(self.root/'worker', timeout=0):
            if self.config_path.exists() or self.repo.path.exists():
                raise ValueError('SMS pravidlo již existuje; původní data se nepřepisují.')
            atomic_create_bytes(self.repo.path, json.dumps({'schema': 1, 'records': {}}).encode())
            atomic_create_bytes(self.config_path, json.dumps(config, ensure_ascii=False).encode())
        return self.status()

    def _events(self, now):
        self._private(self.people_path)
        people = load_family_people(self.people_path, today=now.date())
        return [e for e in upcoming_family_events(people, today=now.date(), lookahead_days=0) if e.notification_due]

    def preview(self):
        config, now = self._config(), self._now()
        records = self._ledger()['records']
        verified = any(r.get('kind') == 'test' and r['state'] in ('sent', 'delivered')
                       and r.get('policy') == digest(policy(config))
                       and timedelta(0) <= now - datetime.fromisoformat(r['at']) <= timedelta(days=7)
                       for r in records.values())
        test_attention = any(r.get('kind') == 'test' and r.get('policy') == digest(policy(config))
                             and r['state'] in ('sending', 'unknown', 'failed') for r in records.values())
        return {'configured': True, 'enabled': config['enabled'], 'fingerprint': digest(policy(config)),
                'hour': 9, 'timezone': 'Europe/Prague', 'today_count': len(self._events(now)),
                'test_verified': verified and not test_attention, 'test_attention': test_attention,
                'test_confirmation': TEST_CONFIRMATION,
                'enable_confirmation': ENABLE_CONFIRMATION, 'writes_performed': False,
                'transport_called': False, 'redacted': True}

    def status(self):
        if not self.config_path.exists():
            return {'status': 'not_configured', 'enabled': False, 'writes_performed': False, 'transport_called': False, 'redacted': True}
        try:
            config = self._config(); records = self._ledger()['records']
            counts = {state: sum(r['state'] == state for r in records.values()) for state in sorted(STATES)}
            return {'status': 'active' if config['enabled'] else 'disabled', 'enabled': config['enabled'],
                    'hour': 9, 'timezone': 'Europe/Prague', 'counts': counts,
                    'attention_count': sum(counts[s] for s in ('sending', 'unknown', 'failed', 'not_sent')),
                    'writes_performed': False, 'transport_called': False, 'redacted': True}
        except Exception:
            return {'status': 'unverified', 'enabled': False, 'writes_performed': False, 'transport_called': False, 'redacted': True}

    def enable(self, *, fingerprint, confirmation):
        if confirmation != ENABLE_CONFIRMATION:
            raise ValueError('Chybí výslovné potvrzení automatických SMS.')
        with exclusive_file_lock(self.root/'worker', timeout=0):
            config = self._config(); preview = self.preview()
            if fingerprint != preview['fingerprint'] or not preview['test_verified']:
                raise ValueError('Nejdřív ověř jednu zkušební SMS pro přesné pravidlo.')
            from app.family_calendar_delivery_hourly import hourly_schedule_active
            if not hourly_schedule_active():
                raise ValueError('Hodinový plán rodinného kalendáře není aktivní.')
            from app.communication.luna_release import http_call
            audit = http_call('/api/human-adam/deploy-audit'); health = http_call('/api/server/health')
            if not audit.get('ready') or audit.get('expected_code_stamp') != health.get('server', {}).get('code_stamp'):
                raise ValueError('Nejdřív nasaď kompatibilní runtime SMS pravidla.')
            config.update(enabled=True, authorization=fingerprint)
            atomic_write_json(self.config_path, config)
        return self.status()

    def test(self, *, fingerprint, confirmation, request_id):
        if confirmation != TEST_CONFIRMATION or not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,80}', request_id):
            raise ValueError('Zkušební SMS vyžaduje přesný souhlas a stabilní identitu.')
        with exclusive_file_lock(self.root/'worker', timeout=0):
            config = self._config()
            if fingerprint != digest(policy(config)):
                raise ValueError('Příjemce nebo text se od potvrzení změnil.')
            if any(r.get('kind') == 'test' and r.get('policy') == fingerprint and r['state'] in ('sending', 'unknown', 'failed')
                   for r in self._ledger()['records'].values()):
                raise ValueError('Nejdřív ověř původní zkušební SMS; nová identita ji neopakuje.')
            attempt = self._attempt(config, 'test:'+request_id, message_for(config), self._now(), kind='test')
        return {**self.status(), **attempt}

    def disable(self, *, confirmed):
        if confirmed is not True:
            raise ValueError('Vypnutí SMS nebylo potvrzené.')
        with exclusive_file_lock(self.root/'worker', timeout=0):
            config = self._config(); config['enabled'] = False
            atomic_write_json(self.config_path, config)
        return self.status()

    def _attempt(self, config, event_key, text, now, *, kind='event'):
        unchanged = {'transport_called': False, 'writes_performed': False}
        def eligible():
            current = self._now()
            return kind != 'event' or (current.date() == now.date() and current.hour >= 9)
        if not eligible():
            return unchanged
        key = digest([config['recipient_id'], event_key])
        previous = self._ledger()['records'].get(key)
        if previous:
            if (previous['state'] != 'not_sent' or previous['attempt'] >= 24 or kind == 'test'
                    or now < datetime.fromisoformat(previous['at']) + timedelta(hours=1)):
                return unchanged
        record = {'state': 'not_sent', 'kind': kind, 'attempt': previous['attempt'] + 1 if previous else 1,
                  'at': now.isoformat(), 'policy': digest(policy(config)), 'phone': config['phone'],
                  'text': text, 'event_key': event_key}
        def store():
            def update(document):
                document['records'][key] = record
                return RepositoryMutation(document)
            self.repo.transact(update)
        adapter = self.adapter or MessagesSMS()
        try:
            anchor = adapter.preflight()
            if type(anchor) is not int or anchor < 0:
                raise ValueError()
        except Exception:
            store()  # Proven no transport call; a later hourly check may retry.
            return {'transport_called': False, 'writes_performed': True}
        if not eligible():
            return unchanged
        record.update(state='sending', anchor=anchor)
        store()  # Durable intent must succeed before sending.
        if not eligible():
            record['state'] = 'not_sent'
            try:
                store()
            except Exception as error:
                raise SMSAttemptError('Přerušený záměr SMS vyžaduje kontrolu.', transport_called=False) from error
            return {'transport_called': False, 'writes_performed': True}
        try:
            outcome = adapter.send(config['phone'], text, anchor)
            if not isinstance(outcome, SMSOutcome) or outcome.state not in ('sent', 'delivered', 'failed', 'unknown'):
                raise ValueError()
            if outcome.state != 'unknown' and (type(outcome.row_id) is not int or outcome.row_id <= anchor):
                raise ValueError()
            record.update(state=outcome.state, row_id=outcome.row_id)
        except Exception:
            record['state'] = 'unknown'
        try:
            store()  # A failed completion leaves sending in the original ledger.
        except Exception as error:
            raise SMSAttemptError('Stav původní SMS není ověřený; znovu ji neposílej.') from error
        return {'transport_called': True, 'writes_performed': True}

    def tick(self):
        """Called only by the owned hourly dispatcher; disabled means zero writes."""
        called = written = False
        try:
            config = self._config() if self.config_path.exists() else None
            if not config or not config['enabled']:
                return self.status()
            now = self._now()
            if now.hour < 9:
                return {'status': 'before_09', 'transport_called': False, 'redacted': True}
            with exclusive_file_lock(self.root/'worker', timeout=0):
                config = self._config()
                if not config['enabled']:
                    return self.status()
                events = self._events(now)
                for event in events:
                    attempt = self._attempt(config, event.event_key, message_for(config, event), now)
                    called |= attempt['transport_called']; written |= attempt['writes_performed']
            return {**self.status(), 'candidate_count': len(events), 'transport_called': called, 'writes_performed': written}
        except FileLockTimeoutError:
            return {'status': 'busy', 'transport_called': False, 'redacted': True}
        except SMSAttemptError as error:
            return {'status': 'unverified', 'transport_called': called or error.transport_called,
                    'writes_performed': True, 'redacted': True}
        except Exception:
            return {'status': 'unverified', 'transport_called': called, 'writes_performed': written, 'redacted': True}


def run_calendar_sms():
    return CalendarSMS().tick()
