"""One Messages SMS attempt, correlated by new row, exact recipient and text."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import quote

from app.messages.outbound import DEFAULT_MESSAGES_DB_PATH, send_via_messages_app


@dataclass(frozen=True)
class SMSOutcome:
    state: str
    row_id: int = 0


class MessagesSMS:
    def __init__(self, db_path=DEFAULT_MESSAGES_DB_PATH, *, sender=send_via_messages_app,
                 attempts=8, pause=time.sleep):
        self.db_path, self.sender, self.attempts, self.pause = Path(db_path), sender, attempts, pause

    def _connect(self):
        return sqlite3.connect('file:' + quote(str(self.db_path)) + '?mode=ro', uri=True, timeout=3)

    def preflight(self):
        with self._connect() as db:
            db.execute('SELECT text, is_sent, is_delivered, error, service, handle_id, is_from_me FROM message LIMIT 0')
            db.execute('SELECT id FROM handle LIMIT 0')
            return int(db.execute('SELECT COALESCE(MAX(ROWID), 0) FROM message').fetchone()[0])

    def send(self, phone, text, anchor):
        # The caller must have persisted sending before crossing this boundary.
        self.sender(phone, text, 'SMS')
        for attempt in range(self.attempts):
            with self._connect() as db:
                rows = db.execute('''SELECT m.ROWID, h.id, m.service, m.is_sent, m.is_delivered, m.error
                    FROM message m JOIN handle h ON h.ROWID=m.handle_id
                    WHERE m.ROWID > ? AND m.is_from_me=1 AND m.text=?''', (anchor, text)).fetchall()
            exact = [row for row in rows if re.sub(r'\D', '', row[1] or '') == phone.removeprefix('+')]
            if len(exact) > 1:
                return SMSOutcome('unknown')
            if exact:
                row, _, service, sent, delivered, error = exact[0]
                if str(service).upper() != 'SMS':
                    return SMSOutcome('unknown', row)
                if error:
                    return SMSOutcome('failed', row)
                if delivered:
                    return SMSOutcome('delivered', row)
                if sent:
                    return SMSOutcome('sent', row)
            if attempt + 1 < self.attempts:
                self.pause(1.5)
        return SMSOutcome('unknown')
