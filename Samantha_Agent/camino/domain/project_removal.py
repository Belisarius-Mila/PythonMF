"""Frozen, restartable unlink plans. No symlinks or links outside the selected set."""
from collections import Counter
import os
from pathlib import Path
import stat


def inventory(paths):
    result = []
    def scan(path, depth):
        if depth > 20 or len(result) >= 100000:
            raise ValueError('Rozsah mazání je příliš velký.')
        s = path.lstat()
        if path.resolve() != path or not (stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode)):
            raise ValueError('Mazání obsahuje nebezpečný odkaz.')
        result.append({'path': str(path), 'directory': stat.S_ISDIR(s.st_mode),
                       'device': s.st_dev, 'inode': s.st_ino, 'bytes': s.st_size,
                       'mtime_ns': s.st_mtime_ns, 'links': s.st_nlink,
                       'parent_device': path.parent.stat().st_dev, 'parent_inode': path.parent.stat().st_ino})
        if stat.S_ISDIR(s.st_mode):
            for p in sorted(path.iterdir()):
                scan(p, depth + 1)
    roots = sorted(set(Path(p) for p in paths))
    roots = [p for p in roots if not any(q != p and p.is_relative_to(q) for q in roots)]
    for p in roots:
        if p.exists() or p.is_symlink():
            scan(p, 0)
    counts = Counter((r['device'], r['inode']) for r in result if not r['directory'])
    if any(counts[(r['device'], r['inode'])] != r['links'] for r in result if not r['directory']):
        raise ValueError('Soubor má odkaz mimo potvrzený rozsah.')
    return result


def remove_planned(rows, *, fault=lambda: None):
    """Missing entries are a previously completed part of this same frozen plan."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directories = {r['path']: r for r in rows if r['directory']}
    remaining = Counter()
    for r in rows:
        p = Path(r['path'])
        if p.parent.resolve() != p.parent:
            raise ValueError('Nadřazená cesta se změnila.')
        if not r['directory'] and p.exists():
            remaining[(r['device'], r['inode'])] += 1
    for r in sorted(rows, key=lambda row: len(Path(row['path']).parts), reverse=True):
        p = Path(r['path'])
        if not p.exists() and not p.is_symlink():
            continue
        fd = os.open(p.parent, flags)
        try:
            ps = os.fstat(fd)
            if (ps.st_dev, ps.st_ino) != (r['parent_device'], r['parent_inode']):
                raise ValueError('Nadřazený adresář se změnil.')
            parent = directories.get(str(p.parent))
            if parent:
                s = os.fstat(fd)
                if (s.st_dev, s.st_ino) != (parent['device'], parent['inode']):
                    raise ValueError('Adresář se během mazání změnil.')
            s = os.stat(p.name, dir_fd=fd, follow_symlinks=False)
            if (s.st_dev, s.st_ino) != (r['device'], r['inode']):
                raise ValueError('Soubory se během mazání změnily.')
            if r['directory']:
                if not stat.S_ISDIR(s.st_mode):
                    raise ValueError('Adresář byl nahrazen.')
                os.rmdir(p.name, dir_fd=fd)
            else:
                key = (s.st_dev, s.st_ino)
                if (not stat.S_ISREG(s.st_mode) or (s.st_size, s.st_mtime_ns) != (r['bytes'], r['mtime_ns'])
                        or s.st_nlink != remaining[key]):
                    raise ValueError('Soubor nebo jeho odkazy se změnily.')
                os.unlink(p.name, dir_fd=fd)
                remaining[key] -= 1
            os.fsync(fd)
            fault()
        finally:
            os.close(fd)
