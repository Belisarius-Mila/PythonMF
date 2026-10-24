"""Cross-process exclusion between project work and owner-approved erasure."""
from contextlib import contextmanager
from functools import wraps
import fcntl
import os
from pathlib import Path


@contextmanager
def lifecycle_lock(database: Path, *, exclusive=False, blocking=True):
    path = Path(database).parent / '.project-lifecycle.lock'
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
                    | (0 if blocking else fcntl.LOCK_NB))
        yield
    finally:
        os.close(fd)


def has_trash_schema(db):
    return db.execute("SELECT 1 FROM sqlite_master WHERE name='project_trash'").fetchone() is not None


def project_blocked(db, trip_id):
    if not has_trash_schema(db):
        return False
    return db.execute("SELECT 1 FROM project_trash WHERE target_kind='trip' AND trip_id=? "
                      "AND state!='restored' LIMIT 1", (trip_id,)).fetchone() is not None


def film_blocked(db, project_id):
    if not has_trash_schema(db):
        return False
    return db.execute("SELECT 1 FROM project_trash WHERE target_kind='film' AND target_id=? "
                      "AND state!='restored' LIMIT 1", (project_id,)).fetchone() is not None


def shared(database):
    """Hold the lifecycle lease through an entire synchronous operation."""
    def decorate(method):
        @wraps(method)
        def run(self, *args, **kwargs):
            with lifecycle_lock(database(self)):
                return method(self, *args, **kwargs)
        return run
    return decorate
