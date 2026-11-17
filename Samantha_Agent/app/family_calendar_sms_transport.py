"""One Messages SMS attempt, correlated by new row, exact recipient and text."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import json
import re
import sqlite3
import subprocess
import time
from urllib.parse import quote

from app.messages.outbound import DEFAULT_MESSAGES_DB_PATH, send_via_messages_app


@dataclass(frozen=True)
class SMSOutcome:
    state: str
    row_id: int = 0
    service: str = ''


def decode_attributed_body(blob):
    """Decode the Mac's own archived attributed text, without activating an app."""
    if not isinstance(blob, bytes) or not 0 < len(blob) <= 2_000_000:
        return None
    script = '''ObjC.import('Foundation');
function run() {
    const input = $.NSFileHandle.fileHandleWithStandardInput.readDataToEndOfFile;
    const encoded = $.NSString.alloc.initWithDataEncoding(input, $.NSUTF8StringEncoding).js;
    const data = $.NSData.alloc.initWithBase64EncodedStringOptions(encoded, 0);
    const value = $.NSUnarchiver.unarchiveObjectWithData(data);
    return JSON.stringify({text: ObjC.unwrap(value.string)});
}'''
    result = subprocess.run(['/usr/bin/osascript', '-l', 'JavaScript', '-e', script],
        input=base64.b64encode(blob).decode('ascii'), capture_output=True, text=True, check=True, timeout=5)
    value = json.loads(result.stdout).get('text')
    return value if isinstance(value, str) else None


class MessagesSMS:
    def __init__(self, db_path=DEFAULT_MESSAGES_DB_PATH, *, sender=send_via_messages_app,
                 attempts=8, pause=time.sleep, decoder=decode_attributed_body):
        self.db_path, self.sender, self.attempts, self.pause = Path(db_path), sender, attempts, pause
        self.decoder = decoder

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
        return self.verify(phone, text, anchor)

    def verify(self, phone, text, anchor, *, attempts=None):
        """Inspect only the original attempt; never invoke the sender."""
        attempts = self.attempts if attempts is None else attempts
        decoded = {}
        for attempt in range(attempts):
            with self._connect() as db:
                columns = {row[1] for row in db.execute('PRAGMA table_info(message)')}
                body = 'm.attributedBody' if 'attributedBody' in columns else 'NULL'
                rows = db.execute(f'''SELECT m.ROWID, h.id, m.service, m.is_sent, m.is_delivered, m.error, m.text, {body}
                    FROM message m JOIN handle h ON h.ROWID=m.handle_id
                    WHERE m.ROWID > ? AND m.is_from_me=1''', (anchor,)).fetchall()
            exact = []
            for row in rows:
                if re.sub(r'\D', '', row[1] or '') != phone.removeprefix('+'):
                    continue
                plain = row[6]
                if plain is None and isinstance(row[7], bytes):
                    cache_key = (row[0], row[7])
                    if cache_key not in decoded:
                        try:
                            decoded[cache_key] = self.decoder(row[7])
                        except Exception:
                            decoded[cache_key] = None
                    plain = decoded[cache_key]
                if plain == text:
                    exact.append(row)
            if len(exact) > 1:
                return SMSOutcome('unknown')
            if exact:
                row, _, service, sent, delivered, error, _, _ = exact[0]
                service = str(service).upper()
                if service not in ('SMS', 'RCS'):
                    return SMSOutcome('unknown', row)
                if error:
                    return SMSOutcome('failed', row, service)
                if delivered:
                    return SMSOutcome('delivered', row, service)
                if sent:
                    return SMSOutcome('sent', row, service)
            if attempt + 1 < attempts:
                self.pause(1.5)
        return SMSOutcome('unknown')
