"""Preserve owned recovery-service state inside the encrypted-backup source.

New private files only. Never edits/installs a service or restores old paths.
"""
from pathlib import Path
import json,os,plistlib,re,sqlite3
from app.file_persistence import atomic_create_text,exclusive_file_lock
from app.recovery_guide_sources import canonical_json,digest
from app.recovery_guide_revalidation import owned_configuration
from app.vocabulary_fr_cloud import backup_database

ROOT=Path(__file__).resolve().parents[1]
MAX_BYTES=300*1024*1024


def sources():
    config,_=owned_configuration();home=Path.home();rows=[]
    for label in ('com.samantha.recovery-guide','com.samantha.vocabulary-fr'):
        path=home/'Library/LaunchAgents'/(label+'.plist')
        if path.exists():
            if path.is_symlink() or plistlib.loads(path.read_bytes()).get('Label')!=label:raise ValueError('archive_foreign_agent')
            rows.append((path,'launchagents/'+path.name))
    for path in sorted(config.root.rglob('*')):
        if path.is_symlink():raise ValueError('archive_source_alias')
        if path.is_file():rows.append((path,'recovery-runtime/'+path.relative_to(config.root).as_posix()))
    bootstrap=Path(config.payload['bootstrap']['path']);rows.append((bootstrap,'recovery-bootstrap.txt'))
    for name in ('.venv/recovery_rec06_peer_schema/v2/TurnStartParams.json','.venv/recovery_rec06_peer_schema/v2/ThreadStartResponse.json','.venv/recovery_rec06_cli/node_modules/@openai/codex/package.json','.venv/recovery_rec06_disabled_features.txt'):
        rows.append((config.project/name,'reviewed-proof/'+('protocol-package.json' if name.endswith('package.json') else 'disabled-features.txt' if name.endswith('disabled_features.txt') else Path(name).name)))
    game=ROOT/'data/private/vocabulary-fr-tailnet'
    if (game/'rooms.sqlite3').is_file():rows.append((backup_database(directory=game),'vocabulary-fr/rooms.sqlite3'))
    return rows


def verify(path):
    manifest=json.loads((path/'manifest.json').read_text())
    if manifest.get('state')!='complete':raise ValueError('archive_incomplete')
    for row in manifest['files']:
        name=Path(row['relative'])
        if name.is_absolute() or '..' in name.parts:raise ValueError('archive_path_escape')
        target=path/name
        if any(p.is_symlink() for p in (target,*target.parents)) or digest(target.read_bytes())!=row['sha256']:raise ValueError('archive_bytes_changed')
    database=path/'vocabulary-fr/rooms.sqlite3'
    if database.exists():
        with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as connection:
            if connection.execute('PRAGMA integrity_check').fetchone()!=('ok',):raise ValueError('archive_database_integrity')
    return manifest


def preserve(*,request_id):
    if not re.fullmatch('[a-zA-Z0-9_-]{12,80}',request_id):raise ValueError('archive_request_id')
    path=ROOT/'data/private/recovery-service-archives'/request_id
    if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('archive_destination_alias')
    path.mkdir(parents=True,mode=0o700,exist_ok=True)
    with exclusive_file_lock(path/'operation'):
        if (path/'manifest.json').exists():return verify(path)
        rows=sources();size=sum(source.stat().st_size for source,_ in rows)
        if size>MAX_BYTES:raise ValueError('archive_scope_requires_review')
        manifest=[]
        for source,relative in rows:
            if any(p.is_symlink() for p in (source,*source.parents)) or not source.is_file() or source.stat().st_uid!=os.getuid():raise ValueError('archive_source_not_owned')
            raw=source.read_bytes();target=path/relative;target.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
            with target.open('xb') as stream:os.chmod(target,0o600);stream.write(raw);stream.flush();os.fsync(stream.fileno())
            manifest.append({'relative':relative,'sha256':digest(raw),'bytes':len(raw)})
        for (source,_),row in zip(rows,manifest):
            if digest(source.read_bytes())!=row['sha256']:raise ValueError('archive_source_changed')
        result={'state':'complete','request_id':request_id,'files':manifest,'bytes':size,
            'restore_policy':'Review new paths, runtime proof and permissions; never auto-install captured LaunchAgents.'}
        atomic_create_text(path/'manifest.json',canonical_json(result));return verify(path)
