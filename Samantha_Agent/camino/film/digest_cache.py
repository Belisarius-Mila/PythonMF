"""Bounded RAM-only digest reuse for read-only film browsing, never permissions."""
from collections import OrderedDict
import hashlib
import hmac
import os
import stat
import threading
import time


_CACHE = OrderedDict()
_LOCK = threading.Lock()
_LIMIT = 1024
_TTL = 30.0
_clock = time.monotonic


def _signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def verified_digest(path, expected):
    """Reuse only a matching hash of an unchanged regular file for at most 30s.

    Callers must still check the current archive, privacy, inventory and receipts.
    Never stores media, metadata permissions or an open descriptor. Full render,
    save and closure validation do not use this read-only optimization.
    """
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise OSError("not a regular film source")
        signature = _signature(before)
        key = (str(path), signature, expected)
        # Coalesce concurrent first reads as well as repeated HTTP requests.
        with _LOCK:
            cached = _CACHE.get(key)
            reused = cached is not None and _clock() - cached < _TTL
            if reused:
                actual = expected
                _CACHE.move_to_end(key)
            else:
                _CACHE.pop(key, None)
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            after = os.fstat(stream.fileno())
            current = os.stat(path, follow_symlinks=False)
            if (_signature(after) != signature or _signature(current) != signature
                    or not stat.S_ISREG(current.st_mode)):
                _CACHE.pop(key, None)
                raise OSError("film source changed during validation")
            if hmac.compare_digest(actual, expected):
                # A hit must not extend the age of the original byte check.
                if not reused:
                    _CACHE[key] = _clock()
                while len(_CACHE) > _LIMIT:
                    _CACHE.popitem(last=False)
            return actual
