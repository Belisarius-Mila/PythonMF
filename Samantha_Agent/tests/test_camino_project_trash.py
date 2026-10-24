"""Synthetic lifecycle, space reclamation, exact retries and interrupted erasure."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from uuid import uuid4

import httpx

from app.camino_project_trash import project_trash_action
from app.camino_film_workshop import MacFilmProjectStore
from app.camino_film_editor import FilmEditor
from camino.api.v1 import CaminoV1Contract
from camino.domain.codec import wire
from camino.domain.model import Privacy
from camino.domain.project_lifecycle import lifecycle_lock
from camino.domain.project_removal import inventory, remove_planned
from camino.domain.project_trash import ProjectTrash, TrashError, RETENTION_MS, CONFIRMATION
from camino.domain.revision_store import StoreConflict, StoreNotFound
from camino.server.application import create_app
from camino.server.auth import RevocableTokenStore
from tests.camino_viewer_fixture import ViewerFixture, uid


class ProjectTrashTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/private/tmp')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        archive = self.root / 'archive'; archive.mkdir(mode=0o700)
        self.f = ViewerFixture(archive)
        self.asset = self.f.upload(30, 'photo', b'SYNTHETIC-ORIGINAL-TO-ERASE')
        self.other = self.f.add_project(100, name='Survivor')
        self.now = 1_000_000
        self.films = self.root / 'films'; self.phone_films = self.root / 'phone-films'
        self.viewer = self.root / 'viewer'; self.viewer.mkdir(mode=0o700)
        self.trash = ProjectTrash(self.f.store.path, self.f.media.database_path, self.f.media.root,
            film_roots=(self.films, self.phone_films), viewer_root=self.viewer, clock=lambda: self.now)
        self.request_id = str(uuid4())

    def request(self, request_id=None):
        state = self.f.store.state()
        return self.trash.request_trip({'request_id': request_id or self.request_id,
            'trip_id': self.f.trip.id, 'device_id': uid(90), 'server_id': state['server_id'],
            'epoch': state['epoch'], 'name': 'Zkušební cesta'})

    def confirm(self):
        return self.trash.confirm(self.request_id, self.trash.preview(self.request_id)['plan_token'], CONFIRMATION)

    def film_store(self):
        return MacFilmProjectStore(self.films, metadata_db=self.f.store.path,
            media_db=self.f.media.database_path, media_root=self.f.media.root, trip_id=self.f.trip.id)

    def test_request_hides_trip_and_blocks_late_upload_render_and_viewer_until_restore(self):
        store = self.film_store(); pid = store.close_mac_day(self.f.day.local_date, confirmed=True)['project_id']
        request = self.request()
        self.assertEqual(self.request(), request)
        self.assertEqual([r['id'] for r in self.f.store.projects()], [self.other.trip.id])
        self.assertEqual(self.f.store.viewer_projects(), [])
        with self.assertRaises(StoreNotFound): self.f.store.asset(self.asset['id'])
        with self.assertRaises(ValueError): FilmEditor(store).inputs(pid)
        with self.assertRaises(StoreConflict) as caught:
            self.f.send('set_trip_title', {'trip_id': self.f.trip.id, 'title': 'Late'})
        self.assertEqual(caught.exception.code, 'project_in_trash')
        self.trash.restore(self.request_id)
        self.assertEqual(self.f.store.asset(self.asset['id']), self.asset)
        self.assertTrue(FilmEditor(store).inputs(pid)[0].is_dir())
        self.assertEqual(len(self.f.store.projects()), 2)

    def test_exact_seven_days_phone_ack_and_no_false_offline_completion(self):
        self.request(); confirmed = self.confirm()
        self.assertEqual(confirmed['purge_ms'], self.now + RETENTION_MS)
        self.now = confirmed['purge_ms'] - 1
        self.assertEqual(self.trash.sweep(), 0)
        self.assertTrue(self.f.media.verified_source(self.asset['id']).is_file())
        self.assertTrue((self.f.media.objects / (self.asset['id'] + '.bin')).exists())
        self.now += 1
        self.trash.sweep()
        receipt = next(r for r in self.trash.listing() if r['request_id'] == self.request_id)
        self.assertTrue(receipt['waiting_for_phone'])
        with self.assertRaises(TrashError): self.trash.restore(self.request_id)
        with self.assertRaises(TrashError): self.trash.acknowledge(self.request_id, uid(91))
        result = self.trash.acknowledge(self.request_id, uid(90))
        self.assertFalse(result['waiting_for_phone'])
        self.assertEqual(self.trash.acknowledge(self.request_id, uid(90)), result)

    def test_all_managed_bytes_history_upload_remnants_and_two_film_roots_are_erased(self):
        pid = self.film_store().close_mac_day(self.f.day.local_date, confirmed=True)['project_id']
        for root in (self.films, self.phone_films):
            folder = root / pid; folder.mkdir(parents=True, exist_ok=True)
            (folder / 'manifest.json').write_text(json.dumps({'trip_id': self.f.trip.id}))
            (folder / 'private-take.wav').write_bytes(b'PRIVATE-VOICE')
        from camino.server.viewer_media import RECIPE
        a = self.asset
        key = hashlib.sha256(f"{RECIPE}:{a['id']}:{a['sha256']}:{a['media_kind']}".encode()).hexdigest()
        (self.viewer / key).mkdir(); (self.viewer / key / 'preview.jpg').write_bytes(b'copy')
        (self.viewer / ('pending-' + a['id'] + '-attempt')).mkdir()
        (self.f.media.quarantine / ('.' + a['id'] + '.0.failed')).write_bytes(b'failed')
        (self.f.media.staging / ('.' + a['id'] + '.0.incoming')).write_bytes(b'chunk')
        survivor = self.f.media.objects / (self.other.asset['id'] + '.bin')
        before = survivor.read_bytes()
        self.request(); self.confirm(); self.now += RETENTION_MS
        self.trash.sweep()
        self.assertEqual(survivor.read_bytes(), before)
        for root in (self.films, self.phone_films): self.assertFalse((root / pid).exists())
        self.assertEqual(list(self.viewer.iterdir()), [])
        self.assertEqual(list(self.f.media.staging.iterdir()), [])
        self.assertEqual(list(self.f.media.quarantine.iterdir()), [])
        with sqlite3.connect(self.f.media.database_path) as db:
            for table in ('upload_sessions', 'upload_chunks', 'verified_assets', 'finalization_journal', 'recovery_events'):
                self.assertFalse(db.execute(f'SELECT 1 FROM {table} WHERE asset_id=?', (a['id'],)).fetchone())
        with sqlite3.connect(self.f.store.path) as db:
            self.assertFalse(db.execute('PRAGMA foreign_key_check').fetchall())
            self.assertEqual(db.execute('SELECT COUNT(*) FROM moments').fetchone()[0], 1)
            erased = [json.loads(r[0]) for r in db.execute('SELECT request_body FROM accepted_operations')]
            self.assertTrue(any(r['kind'] == 'project_erased' for r in erased))
            self.assertFalse(any('TAJNA-VETA' in json.dumps(r) for r in erased))
        self.assertNotIn(b'TAJNA-VETA', self.f.store.path.read_bytes())
        self.assertNotIn(b'PRIVATE-VOICE', self.f.store.path.read_bytes())

    def test_interrupted_unlink_resumes_without_reopening_project(self):
        self.request(); self.confirm(); self.now += RETENTION_MS
        def crash(): raise RuntimeError('synthetic interruption')
        self.trash.fault = crash
        with self.assertRaises(RuntimeError): self.trash.sweep()
        self.assertEqual(self.trash.listing()[0]['state'], 'purging')
        with self.assertRaises(TrashError): self.trash.restore(self.request_id)
        self.trash.fault = lambda: None
        self.assertEqual(self.trash.sweep(), 1)
        self.assertEqual(self.trash.sweep(), 0)
        self.assertEqual(self.trash.listing()[0]['state'], 'purged')

    def test_old_backup_packets_are_consumed_without_resurrection_or_sequence_holes(self):
        with sqlite3.connect(self.f.store.path) as db:
            original = db.execute('SELECT request_body FROM accepted_operations WHERE device_sequence=1').fetchone()[0]
        self.request(); self.confirm(); self.now += RETENTION_MS; self.trash.sweep()
        self.assertEqual(self.f.store.apply(json.loads(original), original)['cursor'], 1)
        rejected = json.loads(original); rejected['payload']['name'] = 'ERASED-CONFLICT-CONTENT'
        with self.assertRaises(StoreConflict): self.f.store.apply(rejected, json.dumps(rejected).encode())
        with sqlite3.connect(self.f.store.path) as db:
            self.assertFalse(db.execute('SELECT 1 FROM conflict_candidates').fetchone())
        self.assertFalse(self.f.store.state()['exports_blocked'])
        self.f.send('create_trip', wire(self.f.trip))
        m = self.f.moment(500, Privacy.DIARY)
        self.f.text(m, 501, 'MUST-NOT-REAPPEAR')
        self.assertEqual([r['id'] for r in self.f.store.projects()], [self.other.trip.id])
        self.f.send('set_trip_title', {'trip_id': self.other.trip.id, 'title': 'Still works'}, expected=1)
        self.assertEqual(self.f.store.projects()[0]['name'], 'Still works')
        with sqlite3.connect(self.f.store.path) as db:
            self.assertNotIn('MUST-NOT-REAPPEAR', ''.join(str(r[0]) for r in db.execute('SELECT request_body FROM accepted_operations')))

    def test_confirmation_token_rechecks_scope_and_lease_excludes_active_work(self):
        store = self.film_store(); pid = store.close_mac_day(self.f.day.local_date, confirmed=True)['project_id']
        self.request(); plan = self.trash.preview(self.request_id)
        (self.films / pid / 'new-take.wav').write_bytes(b'late')
        with self.assertRaises(TrashError) as caught:
            self.trash.confirm(self.request_id, plan['plan_token'], CONFIRMATION)
        self.assertEqual(caught.exception.code, 'plan_changed')
        with self.assertRaises(TrashError): self.trash.confirm(self.request_id, plan['plan_token'], 'yes')
        with lifecycle_lock(self.f.store.path):
            with self.assertRaises(TrashError) as caught: self.confirm()
            self.assertEqual(caught.exception.code, 'project_busy')

    def test_film_only_restore_expiry_and_explicit_new_generation_preserve_originals(self):
        store = self.film_store(); pid = store.close_mac_day(self.f.day.local_date, confirmed=True)['project_id']
        self.trash.request_film(self.request_id, pid, self.f.trip.id)
        self.trash.restore(self.request_id)
        self.assertEqual(self.trash.request_film(self.request_id, pid, self.f.trip.id)['state'], 'restored')
        with self.assertRaises(TrashError): self.trash.request_film(self.request_id, pid, self.other.trip.id)
        self.assertTrue(FilmEditor(store).inputs(pid)[0].exists())
        self.request_id = str(uuid4())
        self.trash.request_film(self.request_id, pid, self.f.trip.id)
        self.confirm(); self.now += RETENTION_MS; self.trash.sweep()
        self.assertTrue(self.f.media.verified_source(self.asset['id']).is_file())
        replacement = store.close_mac_day(self.f.day.local_date, confirmed=True)['project_id']
        self.assertNotEqual(replacement, pid)
        self.assertEqual(store.close_mac_day(self.f.day.local_date, confirmed=True)['project_id'], replacement)
        self.assertEqual(len(self.f.store.projects()), 2)

    def test_guarded_plan_rejects_symlinks_cross_links_and_replacement_but_allows_internal_links(self):
        selected = self.root / 'selected'; selected.mkdir()
        a = selected / 'a'; a.write_bytes(b'a')
        b = selected / 'b'; os.link(a, b)
        plan = inventory([selected]); remove_planned(plan)
        self.assertFalse(selected.exists())
        selected.mkdir(); a.write_bytes(b'a'); outside = self.root / 'outside'; os.link(a, outside)
        with self.assertRaises(ValueError): inventory([selected])
        outside.unlink(); b.symlink_to(outside)
        with self.assertRaises(ValueError): inventory([selected])
        b.unlink(); plan = inventory([selected]); a.unlink(); a.write_bytes(b'different')
        with self.assertRaises(ValueError): remove_planned(plan)
        self.assertEqual(a.read_bytes(), b'different')

    def test_mac_controls_do_not_offer_whole_trip_initiation(self):
        self.assertFalse(project_trash_action({'operation': 'trip', 'trip_id': self.f.trip.id}, trash=self.trash)['ok'])
        self.assertEqual(project_trash_action({'operation': 'list'}, trash=self.trash), {'ok': True, 'requests': []})

    def test_restart_recovery_does_not_move_files_out_of_an_interrupted_purge_plan(self):
        from camino.server.media_store import MediaStore
        self.request(); self.confirm(); self.now += RETENTION_MS
        def crash(): raise RuntimeError('synthetic stop')
        self.trash.fault = crash
        with self.assertRaises(RuntimeError): self.trash.sweep()
        reopened = MediaStore(self.f.media.database_path, self.f.media.root,
            asset_lookup=self.f.store.asset, asset_blocked=self.f.store.asset_in_trash, reserve_bytes=0)
        self.assertEqual(reopened.recovery_report['files_quarantined'], 0)
        self.trash.fault = lambda: None
        self.assertEqual(self.trash.sweep(), 1)

    def test_legacy_unbound_private_cache_blocks_complete_erasure_instead_of_silent_leak(self):
        legacy = self.f.media.quarantine / '00000000.part.old-orphan.random'
        legacy.write_bytes(b'UNASSIGNED-PRIVATE-COPY')
        self.request()
        with self.assertRaises(TrashError) as caught: self.trash.preview(self.request_id)
        self.assertEqual(caught.exception.code, 'unbound_quarantine')
        legacy.unlink()  # synthetic fixture only
        (self.viewer / 'pending-old-unbound').mkdir()
        with self.assertRaises(TrashError) as caught: self.trash.preview(self.request_id)
        self.assertEqual(caught.exception.code, 'legacy_viewer_cache')

    def test_repaired_away_asset_projection_does_not_leave_original_or_upload_bytes_behind(self):
        with sqlite3.connect(self.f.store.path) as db:
            db.execute('DELETE FROM assets WHERE id=?', (self.asset['id'],))
        path = self.f.media.objects / (self.asset['id'] + '.bin')
        self.assertTrue(path.exists())
        self.request(); self.confirm(); self.now += RETENTION_MS; self.trash.sweep()
        self.assertFalse(path.exists())
        self.assertEqual(self.f.media.verified_source(self.other.asset['id']).read_bytes(), b'second-project-photo')

    def test_trip_purge_supersedes_an_existing_film_trash_without_leaving_an_unfinishable_row(self):
        store = self.film_store(); pid = store.close_mac_day(self.f.day.local_date, confirmed=True)['project_id']
        film_request = str(uuid4()); self.trash.request_film(film_request, pid, self.f.trip.id)
        self.request(); self.confirm(); self.now += RETENTION_MS; self.trash.sweep()
        self.assertTrue(all(r['state'] == 'purged' for r in self.trash.listing()))

    def test_failed_database_reclamation_never_authorizes_phone_purge_and_resumes_after_restart(self):
        self.request(); self.confirm(); self.now += RETENTION_MS
        compact = self.trash._compact
        def fail_metadata(db):
            if db.execute('PRAGMA database_list').fetchone()[2] == str(self.f.store.path):
                raise OSError('synthetic VACUUM interruption')
            compact(db)
        self.trash._compact = fail_metadata
        with self.assertRaises(OSError): self.trash.sweep()
        self.assertEqual(self.trash.listing()[0]['state'], 'compacting')
        with self.assertRaises(TrashError): self.trash.acknowledge(self.request_id, uid(90))
        with self.assertRaises(TrashError): self.trash.restore(self.request_id)
        self.trash._compact = compact
        self.assertEqual(self.trash.sweep(), 1)
        self.assertEqual(self.trash.listing()[0]['state'], 'purged')

    def test_service_cannot_silently_omit_a_confirmed_storage_root(self):
        self.request(); self.confirm(); self.now += RETENTION_MS
        incomplete = ProjectTrash(self.f.store.path, self.f.media.database_path, self.f.media.root,
            film_roots=(self.films,), viewer_root=self.viewer, clock=lambda: self.now)
        with self.assertRaises(TrashError) as caught: incomplete.sweep()
        self.assertEqual(caught.exception.code, 'scope_changed')
        self.assertEqual(self.trash.listing()[0]['state'], 'trashed')
        self.assertTrue((self.f.media.objects / (self.asset['id'] + '.bin')).exists())


class TrashHTTPTests(unittest.IsolatedAsyncioTestCase):
    async def test_phone_protocol_is_authenticated_idempotent_and_cannot_confirm_or_restore(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            root = Path(directory); f = ViewerFixture(root)
            late = f.upload(30, 'photo', b'late-upload', complete=False)
            f.media.create_session(late['id'])
            tokens = RevocableTokenStore(root / 'auth.sqlite')
            token = 'synthetic-trash-owner-token-long-enough'; tokens.add(token, label='synthetic')
            app = create_app(metadata_api=CaminoV1Contract(f.store, authenticate=tokens.authenticate),
                             media_store=f.media, token_store=tokens)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
                route = '/api/v1/project-trash'
                self.assertEqual((await client.get(route, params={'device_id': uid(90)})).status_code, 401)
                headers = {'Authorization': 'Bearer ' + token}
                state = (await client.get('/api/v1/state', headers=headers)).json()
                self.assertIn('project_trash_v1', state['features'])
                payload = {'request_id': str(uuid4()), 'trip_id': f.trip.id, 'device_id': uid(90),
                           'server_id': state['server_id'], 'epoch': state['epoch'], 'name': 'Synthetic'}
                first = await client.post(route, json=payload, headers=headers)
                self.assertEqual(first.status_code, 200, first.text)
                chunk = await client.put('/api/v1/assets/' + late['id'] + '/chunks/0', content=b'late-upload',
                    headers={**headers, 'Content-Type': 'application/octet-stream',
                             'X-Camino-Chunk-Sha256': late['sha256']})
                self.assertEqual(chunk.status_code, 404)
                self.assertFalse(list(f.media.staging.iterdir()))
                again = await client.post(route, json=payload, headers=headers)
                self.assertEqual(first.json()['request_id'], again.json()['request_id'])
                listing = (await client.get(route, params={'device_id': uid(90)}, headers=headers)).json()
                self.assertEqual(listing['server_id'], state['server_id'])
                self.assertEqual(len(listing['requests']), 1)
                self.assertEqual((await client.get(route, params={'device_id': uid(91)}, headers=headers)).json()['requests'], [])
                for action in ('confirm', 'restore'):
                    self.assertEqual((await client.post(route + '/' + action, json=payload, headers=headers)).status_code, 404)
                self.assertEqual((await client.post(route, json={**payload, 'name': 'Changed'}, headers=headers)).status_code, 409)
                self.assertEqual((await client.post(route + '/ack', json={'request_id': payload['request_id'], 'device_id': uid(90)}, headers=headers)).status_code, 409)
