"""Owner-confirmed seven-day erasure of one trip or one complete film project.

The ledger is in the authoritative metadata DB, and stores no media copies.
All byte removal uses a frozen journal; a crash never reopens a deleted source.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from uuid import UUID

from .project_lifecycle import lifecycle_lock, has_trash_schema, project_blocked, film_blocked
from .project_removal import inventory, remove_planned

RETENTION_MS = 7 * 24 * 60 * 60 * 1000
CONFIRMATION = 'Potvrzuji globální brzdu: rozumím riziku a chci pokračovat.'


class TrashError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def canonical(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise TrashError('invalid_id', 'Neplatná identita projektu.')
    return value


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def fingerprint(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def initialize_schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS project_trash ('
               'request_id TEXT PRIMARY KEY,target_kind TEXT NOT NULL,target_id TEXT NOT NULL,'
               'trip_id TEXT NOT NULL,device_id TEXT,state TEXT NOT NULL,requested_ms INTEGER NOT NULL,'
               'confirmed_ms INTEGER,purge_ms INTEGER,phone_purged_ms INTEGER,'
               'request_sha256 TEXT NOT NULL,body TEXT NOT NULL,plan TEXT)')
    db.execute('CREATE INDEX IF NOT EXISTS project_trash_target ON project_trash(target_kind,target_id)')
    db.execute('CREATE TABLE IF NOT EXISTS purged_project_objects ('
               'kind TEXT NOT NULL,id TEXT NOT NULL,trip_id TEXT NOT NULL,PRIMARY KEY(kind,id))')


def object_trip(db, kind, identifier):
    tables = {'trip': ('trips', 'id'), 'day': ('days', 'id'), 'moment': ('moments', 'id'),
              'asset': ('assets', 'id'), 'text': ('text_revisions', 'id'),
              'layout': ('audio_layouts', 'id')}
    if kind == 'trip':
        row = db.execute('SELECT id FROM trips WHERE id=?', (identifier,)).fetchone()
    elif kind in ('day', 'moment'):
        row = db.execute(f'SELECT trip_id FROM {tables[kind][0]} WHERE id=?', (identifier,)).fetchone()
    else:
        row = db.execute(f'SELECT m.trip_id FROM {tables[kind][0]} a JOIN moments m '
                         f'ON m.id=a.moment_id WHERE a.{tables[kind][1]}=?', (identifier,)).fetchone()
    if row:
        return row[0]
    if has_trash_schema(db):
        row = db.execute('SELECT trip_id FROM purged_project_objects WHERE kind=? AND id=?',
                         (kind, identifier)).fetchone()
        return row[0] if row else None
    return None


def operation_trip(db, envelope):
    p, kind = envelope['payload'], envelope['kind']
    if kind in ('create_trip', 'create_day', 'create_moment', 'set_trip_title', 'set_project_details'):
        value = p.get('id' if kind == 'create_trip' else 'trip_id')
        try:
            return canonical(value)
        except (ValueError, TypeError, AttributeError):
            return None  # The normal typed contract reports the invalid field.
    return object_trip(db, 'moment', p.get('moment_id')) if isinstance(p.get('moment_id'), str) else None


def operation_identity(envelope):
    kind, p = envelope['kind'], envelope['payload']
    if kind in ('create_trip', 'create_day', 'create_moment', 'create_asset'):
        return kind[7:], canonical(p.get('id'))
    if kind in ('set_trip_title', 'set_project_details'):
        return 'trip', canonical(p.get('trip_id'))
    if kind == 'append_text':
        return 'text', canonical(p.get('id'))
    if kind == 'create_audio_layout':
        return 'layout', canonical(p.get('clip_id'))
    return 'moment', canonical(p.get('moment_id'))


def erased_envelope(envelope, trip_id):
    return {**{k: envelope[k] for k in ('contract_version', 'epoch', 'operation_id',
             'device_sequence', 'device_id')}, 'kind': 'project_erased',
            'expected_revision': None, 'payload': {'trip_id': trip_id}}


class ProjectTrash:
    def __init__(self, metadata_db, media_db, media_root, *, film_roots=(), viewer_root=None,
                 clock=lambda: int(time.time() * 1000), fault=lambda: None):
        self.metadata_db, self.media_db = Path(metadata_db), Path(media_db)
        self.media_root = Path(media_root)
        self.film_roots = tuple(dict.fromkeys(Path(p) for p in film_roots))
        self.viewer_root = Path(viewer_root) if viewer_root is not None else None
        self.clock, self.fault = clock, fault
        for p in (self.metadata_db, self.media_db, self.media_root, *self.film_roots,
                  *((self.viewer_root,) if self.viewer_root else ())):
            if p.is_symlink() or p.resolve() != p:
                raise TrashError('unsafe_store', 'Úložiště má nebezpečnou cestu.')
        with self.db() as db:
            if not has_trash_schema(db):
                raise TrashError('upgrade_required', 'Nejdřív aktualizuj službu Camino.')

    @contextmanager
    def db(self, path=None):
        path = Path(path or self.metadata_db)
        if path.is_symlink() or path.resolve() != path or not path.is_file():
            raise TrashError('unsafe_store', 'Databáze nemá původní bezpečnou cestu.')
        db = sqlite3.connect(path.as_uri() + '?mode=rw', uri=True, isolation_level=None, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA secure_delete=ON')
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def control(self):
        try:
            with lifecycle_lock(self.metadata_db, exclusive=True, blocking=False):
                yield
        except BlockingIOError:
            raise TrashError('project_busy', 'Probíhá přenos nebo zpracování. Zkus to znovu.') from None

    def _row(self, db, request_id):
        row = db.execute('SELECT * FROM project_trash WHERE request_id=?', (canonical(request_id),)).fetchone()
        if row is None:
            raise TrashError('request_missing', 'Požadavek na smazání není dostupný.')
        return row

    def _public(self, row):
        body = json.loads(row['body'])
        return {k: row[k] for k in ('request_id', 'target_kind', 'target_id', 'trip_id', 'device_id',
                'state', 'requested_ms', 'confirmed_ms', 'purge_ms', 'phone_purged_ms')} | {
                    'name': body.get('name', ''), 'server_now_ms': self.clock(),
                    'waiting_for_phone': row['target_kind'] == 'trip' and row['state'] == 'purged'
                                         and row['phone_purged_ms'] is None}

    def listing(self, *, device_id=None):
        with lifecycle_lock(self.metadata_db), self.db() as db:
            rows = db.execute('SELECT * FROM project_trash ORDER BY requested_ms DESC').fetchall()
            return [self._public(r) for r in rows if device_id is None or r['device_id'] == device_id]

    def identity(self):
        with self.db() as db:
            row = db.execute('SELECT server_id,epoch FROM meta WHERE singleton=1').fetchone()
            return dict(row)

    def request_trip(self, payload):
        expected = {'request_id', 'trip_id', 'device_id', 'server_id', 'epoch', 'name'}
        if not isinstance(payload, dict) or set(payload) != expected:
            raise TrashError('invalid_request', 'Požadavek má neplatná pole.')
        for k in expected - {'name'}:
            canonical(payload[k])
        name = payload['name']
        if not isinstance(name, str) or not name.strip() or len(name) > 160 or any(ord(c) < 32 for c in name):
            raise TrashError('invalid_name', 'Neplatný název cesty.')
        digest = fingerprint(payload)
        with self.control(), self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            meta = db.execute('SELECT * FROM meta WHERE singleton=1').fetchone()
            if (meta['server_id'], meta['epoch']) != (payload['server_id'], payload['epoch']):
                raise TrashError('server_mismatch', 'Identita Macu se změnila; nejdřív ověř obnovu.')
            if meta['exports_blocked'] or meta['reconciliation_required']:
                raise TrashError('archive_blocked', 'Archiv vyžaduje ověření obnovy.')
            if meta['writer_device_id'] not in (None, payload['device_id']):
                raise TrashError('writer_mismatch', 'Žádost může vytvořit jen hlavní iPhone.')
            old = db.execute('SELECT * FROM project_trash WHERE request_id=?', (payload['request_id'],)).fetchone()
            if old:
                if old['request_sha256'] != digest:
                    raise TrashError('request_conflict', 'Stejné ID označuje jiný požadavek.')
                return self._public(old)
            if project_blocked(db, payload['trip_id']):
                raise TrashError('request_exists', 'Cesta už má požadavek na smazání.')
            db.execute('INSERT INTO project_trash VALUES (?,?,?,?,?,?,?,NULL,NULL,NULL,?,?,NULL)',
                       (payload['request_id'], 'trip', payload['trip_id'], payload['trip_id'],
                        payload['device_id'], 'requested', self.clock(), digest, encoded({'name': name})))
            if meta['writer_device_id'] is None:
                db.execute('UPDATE meta SET writer_device_id=? WHERE singleton=1', (payload['device_id'],))
            db.commit()
            return self._public(self._row(db, payload['request_id']))

    def _film_directories(self, trip_id, project_id=None):
        result = []
        for root in self.film_roots:
            if root.is_symlink() or root.resolve() != root:
                raise TrashError('unsafe_store', 'Filmové úložiště se změnilo.')
            if not root.exists():
                continue
            for folder in root.iterdir():
                folder_id = folder.name.removeprefix('.pending-')
                try:
                    canonical(folder_id)
                except (ValueError, TypeError):
                    continue
                if folder.is_symlink() or not folder.is_dir():
                    raise TrashError('unsafe_store', 'Filmový projekt má nebezpečný odkaz.')
                path = folder / 'manifest.json'
                if not path.exists() and folder.name.startswith('.pending-'):
                    path = folder / 'mac-confirmation.json'
                if path.is_symlink() or not path.is_file():
                    raise TrashError('invalid_manifest', 'Filmový manifest vyžaduje kontrolu.')
                manifest = json.loads(path.read_text())
                if manifest.get('trip_id') == trip_id and (project_id is None or folder_id == project_id):
                    result.append(folder)
        return result

    def _scope(self):
        roots = sorted(set((self.media_root, *self.film_roots,
                            *((self.viewer_root,) if self.viewer_root else ()))))
        identities = {}
        for path in roots:
            if path.is_symlink() or path.resolve() != path or (path.exists() and not path.is_dir()):
                raise TrashError('unsafe_store', 'Kořen spravovaných dat se změnil.')
            identities[str(path)] = [path.stat().st_dev, path.stat().st_ino] if path.exists() else None
        return {'metadata_db': str(self.metadata_db), 'media_db': str(self.media_db),
                'media_root': str(self.media_root), 'film_roots': sorted(str(p) for p in self.film_roots),
                'viewer_root': str(self.viewer_root) if self.viewer_root else None, 'roots': identities}

    def _check_scope(self, expected):
        actual = self._scope()
        if not isinstance(expected, dict) or any(actual[k] != expected.get(k) for k in actual if k != 'roots'):
            raise TrashError('scope_changed', 'Služba nemá stejná úložiště jako potvrzený přehled. Výmaz čeká na kontrolu.')
        if any(value is not None and actual['roots'].get(path) != value for path, value in expected['roots'].items()):
            raise TrashError('scope_changed', 'Potvrzený kořen dat byl přesunut nebo nahrazen. Výmaz čeká na kontrolu.')

    def _snapshot(self, db, row):
        trip = row['trip_id']
        identities = {'trip': [trip], 'day': [], 'moment': [], 'asset': [], 'text': [], 'layout': []}
        assets = []
        if row['target_kind'] == 'trip':
            identities['day'] = [r[0] for r in db.execute('SELECT id FROM days WHERE trip_id=?', (trip,))]
            identities['moment'] = [r[0] for r in db.execute('SELECT id FROM moments WHERE trip_id=?', (trip,))]
            for kind, table in [('asset', 'assets'), ('text', 'text_revisions'), ('layout', 'audio_layouts')]:
                key = 'id'
                for r in db.execute(f'SELECT a.* FROM {table} a JOIN moments m ON m.id=a.moment_id WHERE m.trip_id=?', (trip,)):
                    identities[kind].append(r[key])
                    if kind == 'asset':
                        assets.append(json.loads(r['body']))
        operations = []
        if row['target_kind'] == 'trip':
            # Include accepted manifests whose projection was removed by an
            # earlier repair. Their upload/quarantine bytes still belong here.
            by_id = {a['id']: a for a in assets}
            for op in db.execute('SELECT id,request_body FROM accepted_operations'):
                body = json.loads(op['request_body'])
                if body.get('kind') != 'project_erased' and operation_trip(db, body) == trip:
                    operations.append(op['id'])
                    if body['kind'] == 'create_asset':
                        by_id.setdefault(body['payload']['id'], body['payload'])
            with self.db(self.media_db) as media:
                for session in media.execute('SELECT asset_id,moment_id,media_kind,sha256 FROM upload_sessions'):
                    if session['moment_id'] in identities['moment']:
                        by_id.setdefault(session['asset_id'], {'id': session['asset_id'],
                            'media_kind': session['media_kind'], 'sha256': session['sha256']})
            assets = list(by_id.values())
            identities['asset'] = sorted(by_id)
        paths = self._film_directories(trip, row['target_id'] if row['target_kind'] == 'film' else None)
        if row['target_kind'] == 'film' and not paths:
            raise TrashError('film_missing', 'Filmový projekt není dostupný.')
        if row['target_kind'] == 'trip':
            from camino.server.viewer_media import RECIPE
            quarantine = self.media_root / 'quarantine'
            with self.db(self.media_db) as media:
                known_assets = {r[0] for r in media.execute('SELECT asset_id FROM upload_sessions')}
            known_assets.update(r[0] for r in db.execute('SELECT id FROM assets'))
            known_assets.update(identities['asset'])
            known_assets.update(r[0] for r in db.execute("SELECT id FROM purged_project_objects WHERE kind='asset'"))
            if quarantine.exists() and any(not known_assets.intersection(p.name.split('.')) for p in quarantine.iterdir()):
                raise TrashError('unbound_quarantine', 'Některé pracovní kopie médií nemají ověřené přiřazení. Nejdřív zkontroluj karanténu.')
            if self.viewer_root and self.viewer_root.exists():
                # Old conversions had no ownership identity in their name.
                # Do not silently declare complete erasure while such bytes
                # remain unclassified; an owner audit must resolve them first.
                for pending in self.viewer_root.glob('pending-*'):
                    try:
                        canonical(pending.name[8:44])
                    except ValueError:
                        raise TrashError('legacy_viewer_cache', 'Starší pracovní kopie Vieweru vyžadují kontrolu přiřazení před výmazem.') from None
            for a in assets:
                aid = canonical(a['id'])
                paths += [self.media_root / 'objects' / (aid + '.bin'), self.media_root / 'sessions' / aid]
                for directory in (self.media_root / '.staging', self.media_root / 'quarantine'):
                    if directory.exists():
                        paths += [p for p in directory.iterdir() if aid in p.name.split('.')]
                if self.viewer_root:
                    key = hashlib.sha256(f"{RECIPE}:{aid}:{a['sha256']}:{a['media_kind']}".encode()).hexdigest()
                    paths.append(self.viewer_root / key)
                    paths += list(self.viewer_root.glob('pending-' + aid + '-*'))
            with self.db(self.media_db) as media:
                for r in media.execute('SELECT asset_id,staging_name FROM finalization_journal'):
                    if r['asset_id'] in identities['asset'] and r['staging_name']:
                        p = self.media_root / '.staging' / r['staging_name']
                        if p.parent != self.media_root / '.staging':
                            raise TrashError('unsafe_store', 'Neplatná pracovní cesta média.')
                        paths.append(p)
        files = inventory(paths)
        return {'identities': identities, 'operations': operations, 'files': files, 'scope': self._scope(),
                'film_count': len(self._film_directories(trip, row['target_id'] if row['target_kind'] == 'film' else None))}

    def preview(self, request_id):
        with self.control(), self.db() as db:
            row = self._row(db, request_id)
            if row['state'] in ('purging', 'compacting', 'purged', 'restored'):
                return self._public(row)
            snap = self._snapshot(db, row)
            return {**self._public(row), 'plan_token': fingerprint(snap),
                    'bytes': sum({(r['device'], r['inode']): r['bytes'] for r in snap['files'] if not r['directory']}.values()),
                    'file_count': sum(not r['directory'] for r in snap['files']),
                    'moment_count': len(snap['identities']['moment']),
                    'asset_count': len(snap['identities']['asset']), 'film_count': snap['film_count']}

    def confirm(self, request_id, token, confirmation):
        if confirmation != CONFIRMATION:
            raise TrashError('confirmation_required', 'Přesun do sedmidenního koše vyžaduje přesné potvrzení.')
        with self.control(), self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, request_id)
            if row['state'] == 'trashed':
                return self._public(row)
            if row['state'] != 'requested':
                raise TrashError('invalid_state', 'Žádost už nelze potvrdit.')
            snapshot = self._snapshot(db, row)
            if token != fingerprint(snapshot):
                raise TrashError('plan_changed', 'Rozsah se změnil. Znovu zkontroluj přehled.')
            now = self.clock()
            body = json.loads(row['body']); body['confirmed_scope'] = snapshot['scope']
            db.execute("UPDATE project_trash SET state='trashed',confirmed_ms=?,purge_ms=?,body=? WHERE request_id=?",
                       (now, now + RETENTION_MS, encoded(body), request_id))
            db.commit()
            return self._public(self._row(db, request_id))

    def request_film(self, request_id, project_id, trip_id):
        for value in (request_id, project_id, trip_id):
            canonical(value)
        with self.control(), self.db() as db:
            old = db.execute('SELECT * FROM project_trash WHERE request_id=?', (request_id,)).fetchone()
            if old:
                if old['target_kind'] != 'film' or old['target_id'] != project_id or old['trip_id'] != trip_id:
                    raise TrashError('request_conflict', 'Stejné ID označuje jiný požadavek.')
                return self._public(old)
            if project_blocked(db, trip_id) or film_blocked(db, project_id):
                raise TrashError('request_exists', 'Projekt už má požadavek na smazání.')
            folders = self._film_directories(trip_id, project_id)
            if not folders:
                raise TrashError('film_missing', 'Filmový projekt není dostupný.')
            name = json.loads((folders[0] / 'manifest.json').read_text()).get('local_date', 'Film')
            db.execute('INSERT INTO project_trash VALUES (?,?,?,?,NULL,?,?,NULL,NULL,NULL,?,?,NULL)',
                       (request_id, 'film', project_id, trip_id, 'requested', self.clock(),
                        fingerprint([project_id, trip_id]), encoded({'name': name})))
            return self._public(self._row(db, request_id))

    def restore(self, request_id):
        with self.control(), self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, request_id)
            if row['state'] == 'restored':
                return self._public(row)
            if row['target_kind'] == 'film' and project_blocked(db, row['trip_id']):
                raise TrashError('parent_in_trash', 'Nejdřív obnov celou cestu; samostatný film ji z koše nevrátí.')
            if row['state'] not in ('requested', 'trashed') or (row['purge_ms'] is not None and self.clock() >= row['purge_ms']):
                raise TrashError('expired', 'Lhůta pro obnovení už skončila.')
            db.execute("UPDATE project_trash SET state='restored',body='{}',plan=NULL WHERE request_id=?", (request_id,))
            db.commit()
            return self._public(self._row(db, request_id))

    def acknowledge(self, request_id, device_id):
        with self.control(), self.db() as db:
            row = self._row(db, request_id)
            if row['target_kind'] != 'trip' or row['device_id'] != canonical(device_id) or row['state'] != 'purged':
                raise TrashError('invalid_ack', 'Výmaz telefonu neodpovídá žádosti.')
            db.execute('UPDATE project_trash SET phone_purged_ms=COALESCE(phone_purged_ms,?) WHERE request_id=?',
                       (self.clock(), request_id))
            return self._public(self._row(db, request_id))

    def _erase_metadata(self, db, row, plan):
        trip, ids = row['trip_id'], plan['identities']
        for kind, values in ids.items():
            db.executemany('INSERT OR IGNORE INTO purged_project_objects VALUES (?,?,?)',
                           [(kind, i, trip) for i in values])
        for oid in plan['operations']:
            old = db.execute('SELECT request_body FROM accepted_operations WHERE id=?', (oid,)).fetchone()
            if old:
                db.execute('UPDATE accepted_operations SET request_body=? WHERE id=?',
                           (encoded(erased_envelope(json.loads(old[0]), trip)).encode(), oid))
        for conflict in db.execute('SELECT operation_id,request_sha256,request_body FROM conflict_candidates').fetchall():
            try:
                belongs = operation_trip(db, json.loads(conflict['request_body'])) == trip
            except (ValueError, KeyError, TypeError):
                belongs = conflict['operation_id'] in plan['operations']
            if belongs:
                db.execute('DELETE FROM conflict_candidates WHERE operation_id=? AND request_sha256=?',
                           (conflict['operation_id'], conflict['request_sha256']))
        for table in ('audio_layouts', 'text_revisions', 'assets', 'moment_revisions'):
            db.execute(f'DELETE FROM {table} WHERE moment_id IN (SELECT id FROM moments WHERE trip_id=?)', (trip,))
        for table in ('moments', 'days', 'viewer_permissions'):
            db.execute(f'DELETE FROM {table} WHERE trip_id=?', (trip,))
        db.execute('DELETE FROM trips WHERE id=?', (trip,))

    @staticmethod
    def _compact(db):
        if db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0]:
            raise TrashError('database_busy', 'Databáze má otevřené čtení. Uvolnění místa se dokončí při dalším pokusu.')
        db.execute('VACUUM')
        if db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()[0]:
            raise TrashError('database_busy', 'Databáze ještě neuvolnila pracovní soubor. Výmaz zatím není dokončený.')

    def _finish(self, db, row):
        # Do not tell the phone to erase its final copy before durable SQL
        # reclamation succeeds. A failed VACUUM resumes from `compacting`.
        self._compact(db)
        db.execute('BEGIN IMMEDIATE')
        db.execute("UPDATE project_trash SET state='purged' WHERE request_id=?", (row['request_id'],))
        if row['target_kind'] == 'trip':
            db.execute("UPDATE project_trash SET state='purged' "
                       "WHERE target_kind='film' AND trip_id=? AND state!='restored'", (row['trip_id'],))
        db.commit()

    def sweep(self):
        """Only a confirmed expired request can enter this restartable purge."""
        with self.control(), self.db() as db:
            rows = db.execute("SELECT * FROM project_trash WHERE state IN ('purging','compacting') OR "
                              "(state='trashed' AND purge_ms<=?)", (self.clock(),)).fetchall()
            for row in rows:
                row = self._row(db, row['request_id'])
                if row['state'] == 'purged':
                    continue
                if row['state'] == 'compacting':
                    self._finish(db, row)
                    continue
                self._check_scope(json.loads(row['body']).get('confirmed_scope'))
                plan = json.loads(row['plan']) if row['plan'] else self._snapshot(db, row)
                if row['state'] != 'purging':
                    db.execute("UPDATE project_trash SET state='purging',plan=? WHERE request_id=?",
                               (encoded(plan), row['request_id']))
                remove_planned(plan['files'], fault=self.fault)
                if row['target_kind'] == 'trip':
                    with self.db(self.media_db) as media:
                        media.execute('BEGIN IMMEDIATE')
                        for aid in plan['identities']['asset']:
                            for table in ('verified_assets', 'finalization_journal', 'upload_chunks', 'recovery_events', 'upload_sessions'):
                                media.execute(f'DELETE FROM {table} WHERE asset_id=?', (aid,))
                        media.commit()
                        self._compact(media)
                    db.execute('BEGIN IMMEDIATE')
                    self._erase_metadata(db, row, plan)
                    db.execute("UPDATE project_trash SET state='compacting',body='{}',plan=NULL "
                               "WHERE target_kind='film' AND trip_id=? AND state!='restored'", (row['trip_id'],))
                else:
                    db.execute('BEGIN IMMEDIATE')
                db.execute("UPDATE project_trash SET state='compacting',body='{}',plan=NULL WHERE request_id=?", (row['request_id'],))
                db.commit()
                self._finish(db, row)
            return len(rows)
