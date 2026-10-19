"""Verified encrypted Camino bundles; quiesce only the owned service and film writes."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import plistlib
import shutil
import sqlite3
import stat
import subprocess
import time
import urllib.request
from contextlib import ExitStack, closing, contextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from camino.server.service_safety import readonly
from scripts import camino_service_control as service
from scripts.camino_service_prepare import archive_evidence

BACKUP_ROOT = Path('/Volumes/SamanthaSecureBackup/SamanthaBackups')
DB_KEYS = ('metadata_db', 'media_db', 'auth_db')
SKIP_DIRS = {'venv', '.venv', '__pycache__', '.git'}


def service_command(argv):
    environment = os.environ.copy()
    if argv[0] == service.TAILSCALE:
        environment['TAILSCALE_BE_CLI'] = '1'
    # The owned plist allows 330 seconds for an in-flight upload to drain.
    timeout = 360 if argv[:2] == ['/bin/launchctl', 'bootout'] else 30
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                          check=False, env=environment)


class RuntimeController:
    ROOT, SCHEMA_VERSION = service.ROOT, service.SCHEMA_VERSION
    load_config, target = staticmethod(service.load_config), staticmethod(service.target)

    @staticmethod
    def control(action, root):
        return service.control(action, root, runner=service_command)

    @staticmethod
    def offline(config):
        return service.offline(config, runner=service_command)

    @staticmethod
    def checked(argv):
        return service.checked(argv, runner=service_command)


def encrypted_target(root: Path) -> None:
    """A directory named like a volume is not proof of a mounted encrypted image."""
    mount = BACKUP_ROOT.parent
    if root != BACKUP_ROOT or root.resolve() != root or not os.path.ismount(mount):
        raise ValueError('mounted secure backup target required')
    result = subprocess.run(['hdiutil', 'info', '-plist'], capture_output=True, check=True, timeout=15)
    images = plistlib.loads(result.stdout).get('images', [])
    matches = [im for im in images if any(e.get('mount-point') == str(mount)
                                         for e in im.get('system-entities', []))]
    if len(matches) != 1:
        raise ValueError('encrypted image identity unavailable')
    result = subprocess.run(['hdiutil', 'isencrypted', matches[0]['image-path']],
                            capture_output=True, text=True, check=True, timeout=15)
    if 'encrypted: YES' not in result.stdout:
        raise ValueError('encrypted image required')


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8') as stream:
        os.chmod(path, 0o600)
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def lock(path: Path):
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(descriptor)


def inventory(root: Path) -> dict[Path, tuple[int, int]]:
    """Never follow symlinks or silently skip unknown source file types."""
    files = {}
    for folder, directories, names in os.walk(root, followlinks=False):
        base = Path(folder)
        for name in list(directories):
            path = base / name
            if name in SKIP_DIRS:
                directories.remove(name)
            elif path.is_symlink():
                raise ValueError('source directory symlink refused')
        for name in names:
            if (name.endswith(('-wal', '-shm', '.service-lock', '.pyc'))
                    or name in ('.closure-lock', '.render-worker', 'service.log')):
                continue
            path = base / name
            mode = path.lstat()
            if not stat.S_ISREG(mode.st_mode):
                raise ValueError('source must contain regular files only')
            files[path.relative_to(root)] = (mode.st_size, mode.st_mtime_ns)
    return files


def logical_digest(connection: sqlite3.Connection) -> str:
    value = hashlib.sha256()
    for line in connection.iterdump():
        value.update(line.encode('utf-8'))
        value.update(b'\n')
    return value.hexdigest()


def copy_database(source: Path, target: Path) -> None:
    """Include committed WAL through SQLite's backup API, never raw live DB copies."""
    with target.open('xb'):
        os.chmod(target, 0o600)
    original, copied = readonly(source), sqlite3.connect(target)
    try:
        deadline = time.monotonic() + 60
        def progress(_status, _remaining, _total):
            if time.monotonic() > deadline:
                raise TimeoutError('database backup timed out')
        original.backup(copied, pages=256, progress=progress)
        if (copied.execute('PRAGMA quick_check').fetchall() != [('ok',)]
                or logical_digest(original) != logical_digest(copied)):
            raise ValueError('database backup differs logically')
    finally:
        original.close()
        copied.close()
    with target.open('rb') as stream:
        os.fsync(stream.fileno())


def copy_files(source: Path, target: Path, files: dict, databases: set[Path]) -> dict:
    entries = {}
    target.mkdir(parents=True, mode=0o700)
    for relative in files:
        original, destination = source / relative, target / relative
        destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if original in databases:
            copy_database(original, destination)
        else:
            with original.open('rb') as src, destination.open('xb') as dst:
                os.chmod(destination, 0o700 if original.stat().st_mode & 0o100 else 0o600)
                shutil.copyfileobj(src, dst, 1024 * 1024)
                dst.flush()
                os.fsync(dst.fileno())
            if digest(original) != digest(destination):
                raise ValueError('copied file hash mismatch')
        entries[relative.as_posix()] = {'bytes': destination.stat().st_size,
                                       'sha256': digest(destination)}
    return entries


def wait_stopped(controller, root: Path, timeout: float = 360) -> None:
    """bootout can return while launchd is still draining the owned job."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = controller.control('status', root)
        if not current.get('owned_definition'):
            raise RuntimeError('service ownership changed while stopping')
        if not current.get('loaded'):
            return
        time.sleep(.25)
    raise TimeoutError('owned service is still stopping; inspect its state')


def health(root: Path, timeout: float = 90) -> None:
    token = (root / 'owner-token.txt').read_text().strip()
    config = json.loads((root / 'config.json').read_text())
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        request = urllib.request.Request('http://127.0.0.1:8767/healthz',
                                         headers={'Authorization': 'Bearer ' + token})
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                if response.status != 200 or json.load(response).get('scope') != 'c05a_private_owner':
                    raise OSError('unexpected service health')
            request = urllib.request.Request('http://127.0.0.1:8767/api/v1/state',
                                             headers={'Authorization': 'Bearer ' + token})
            with urllib.request.urlopen(request, timeout=2) as response:
                state = json.load(response)
            if all(state.get(k) == config[k] for k in ('server_id', 'epoch')):
                return
        except OSError:
            pass
        time.sleep(.25)
    raise RuntimeError('owned service did not return healthy')


def verify_bundle(bundle: Path, manifest: dict | None = None) -> dict:
    """Read back every byte/hash and all DB integrity checks, without starting a service."""
    if bundle.is_symlink():
        raise ValueError('backup directory symlink refused')
    bundle = bundle.resolve()
    manifest = manifest or json.loads((bundle / 'backup_manifest.json').read_text())
    if manifest.get('schema') != 1 or manifest.get('scope') != 'camino-recovery':
        raise ValueError('unknown Camino backup manifest')
    for relative, evidence in manifest['files'].items():
        path = bundle / relative
        if (Path(relative).is_absolute() or '..' in Path(relative).parts
                or path.resolve() != path or not path.is_file()
                or path.stat().st_size != evidence['bytes'] or digest(path) != evidence['sha256']):
            raise ValueError('backup file verification failed')
    references = [*manifest['layout'].values(), *manifest['databases']]
    for relative in references:
        path = bundle / relative
        if (Path(relative).is_absolute() or '..' in Path(relative).parts
                or path.resolve() != path or not path.exists()):
            raise ValueError('backup layout reference is unsafe or missing')
    mapped = {key: bundle / relative for key, relative in manifest['layout'].items()}
    config = json.loads((bundle / 'Camino/Service/config.json').read_text())
    mapped['trip_id'] = config['trip_id']
    for relative in manifest['databases']:
        connection = readonly(bundle / relative)
        try:
            if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                raise ValueError('backup database integrity failed')
        finally:
            connection.close()
    result = archive_evidence(mapped)
    if result != manifest['archive']:
        raise ValueError('restored archive differs')
    return {'verified': True, 'files': len(manifest['files']),
            'databases': len(manifest['databases']), **result}


def backup_camino(*, backup_root: Path = BACKUP_ROOT, mode: str = 'dry-run',
                  root: Path | None = None, controller=None, health_check=health) -> dict:
    """Create a separate immutable supplement, also called by regular recovery backups."""
    if mode not in ('dry-run', 'execute'):
        raise ValueError('unknown backup mode')
    controller = controller or RuntimeController()
    root = root or controller.ROOT
    if not root.exists():
        return {'state': 'not_configured', 'copied': False}
    config = controller.load_config(root)
    with closing(readonly(config['metadata_db'])) as connection:
        if connection.execute('PRAGMA user_version').fetchone()[0] != controller.SCHEMA_VERSION:
            raise ValueError('restart would require a schema change; backup refused')
    release = config['code_root']
    if (not release.is_relative_to(root.parent / 'Releases')
            or not all(config[key].is_relative_to(root) for key in
                       (*DB_KEYS, 'media_root', 'viewer_media_root'))):
        raise ValueError('archive paths outside supported recovery layout')
    encrypted_target(backup_root)
    target_device = backup_root.stat().st_dev
    before = controller.control('status', root)
    if (not before.get('owned_definition')
            or (before.get('loaded') and not before.get('running'))):
        raise ValueError('unowned or transitioning service refused')
    if isinstance(controller, RuntimeController):
        service.require_private_network(runner=service_command)
    source_files, release_files = inventory(root), inventory(release)
    needed = sum(size for size, _ in (*source_files.values(), *release_files.values()))
    if shutil.disk_usage(backup_root).free < needed + 1024**3:
        raise ValueError('insufficient backup space')
    if mode == 'dry-run':
        return {'state': 'preview', 'files': len(source_files) + len(release_files),
                'bytes': needed, 'will_pause_service': before['loaded'], 'copied': False}
    bundle = backup_root / 'camino_snapshots' / (datetime.now().strftime('%Y%m%d_%H%M%S') + '-' + uuid4().hex[:8])
    attempted_stop = False
    manifest = None
    with ExitStack() as stack:
        stack.enter_context(lock(backup_root / '.camino-backup.lock'))
        film = root / 'film-projects'
        if film.exists():
            stack.enter_context(lock(film / '.closure-lock'))
        try:
            if before['loaded']:
                attempted_stop = True
                controller.control('stop', root)
                wait_stopped(controller, root)
            with controller.offline(config):
                # All supported writers are now excluded. Inventory only this frozen interval.
                source_files, release_files = inventory(root), inventory(release)
                archive = archive_evidence(config)
                if (bundle.parent.is_symlink() or bundle.parent.resolve() != bundle.parent
                        or (bundle.parent.exists() and bundle.parent.stat().st_mode & 0o077)):
                    raise ValueError('private backup parent required')
                bundle.parent.mkdir(exist_ok=True, mode=0o700)
                bundle.mkdir(mode=0o700)
                databases = {config[key] for key in DB_KEYS}
                readers = root / 'readers.sqlite'
                if readers.exists():
                    databases.add(readers)
                files = copy_files(root, bundle / 'Camino/Service', source_files, databases)
                for key in ('media_root', 'viewer_media_root'):
                    (bundle / 'Camino/Service' / config[key].relative_to(root)).mkdir(
                        parents=True, exist_ok=True, mode=0o700)
                if film.exists():
                    (bundle / 'Camino/Service/film-projects').mkdir(exist_ok=True, mode=0o700)
                release_target = Path('Camino/Releases') / release.parent.name / release.name
                release_entries = copy_files(release, bundle / release_target, release_files, set())
                entries = {'Camino/Service/' + name: value for name, value in files.items()}
                entries.update({str(release_target / name): value for name, value in release_entries.items()})
                layout = {key: str(Path('Camino/Service') / config[key].relative_to(root))
                          for key in (*DB_KEYS, 'media_root', 'viewer_media_root')}
                layout['code_root'] = str(release_target)
                manifest = {'schema': 1, 'scope': 'camino-recovery', 'files': entries,
                            'layout': layout, 'archive': archive,
                            'databases': [str(Path('Camino/Service') / p.relative_to(root))
                                          for p in sorted(databases)],
                            'source_home': str(Path.home()), 'service_was_running': before['loaded']}
                verify_bundle(bundle, manifest)
                if (inventory(root) != source_files or inventory(release) != release_files
                        or archive_evidence(config) != archive):
                    raise ValueError('source changed during frozen backup')
        finally:
            if attempted_stop:
                current = controller.control('status', root)
                if not current.get('owned_definition'):
                    raise RuntimeError('service ownership changed; automatic restart refused')
                if current.get('loaded'):
                    # A failed/timed-out stop can still have an asynchronous bootout
                    # in progress. Re-enabling alone would not restore that job.
                    try:
                        wait_stopped(controller, root)
                    except TimeoutError:
                        controller.checked(['/bin/launchctl', 'enable', controller.target()])
                        health_check(root)
                        raise
                controller.control('start', root)
                health_check(root)
        # A failed copy or restart never earns a completed backup manifest.
        encrypted_target(backup_root)
        if backup_root.stat().st_dev != target_device:
            raise ValueError('backup volume changed during copy')
        write_json(bundle / 'backup_manifest.json', manifest)
    result = verify_bundle(bundle)
    result.update(state='completed', snapshot_id=bundle.name,
                  service_running_restored=bool(before['loaded']))
    return result
