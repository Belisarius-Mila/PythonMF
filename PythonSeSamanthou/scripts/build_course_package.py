"""Build one content-only course ZIP from its validated manifest; never overwrite a release."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from course_loader import load_course, local_file, valid_id


def build(course_directory, destination):
    root = Path(course_directory).resolve()
    load_course(root / 'kurz.json')  # Validation only: does not execute lesson code.
    if not valid_id(root.name):
        raise ValueError('Název složky balíčku musí být jednoduchý místní identifikátor.')
    manifest = json.loads((root / 'kurz.json').read_text(encoding='utf-8'))
    files = {root / 'kurz.json', local_file(root, 'README.md')}
    for relative in manifest['lessons']:
        meta = local_file(root, relative)
        files.add(meta)
        lesson = json.loads(meta.read_text(encoding='utf-8'))
        for field in ('explanation_file', 'starter_file', 'solution_file'):
            files.add(local_file(meta.parent, lesson[field]))
    if any(p.suffix not in {'.md', '.json', '.py'} for p in files):
        raise ValueError('Distribuce smí obsahovat pouze Markdown, JSON a Python lekcí.')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            info = zipfile.ZipInfo(str(Path(root.name) / path.relative_to(root)), (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    raw = buffer.getvalue()
    # Verify that archived paths still resolve through the manifest (including symlink aliases).
    with tempfile.TemporaryDirectory(prefix='samantha-package-check-') as temp:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            archive.extractall(temp)
        load_course(Path(temp) / root.name / 'kurz.json')
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open('xb') as handle:
            handle.write(raw)
    except FileExistsError:
        if destination.read_bytes() != raw:
            raise FileExistsError('Cílový soubor už obsahuje jiný balíček; zvol nový název.') from None
    print(f'{destination.name}: {len(files)} souborů, {len(raw)} B, SHA-256 {hashlib.sha256(raw).hexdigest()}')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('course_directory', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    build(args.course_directory, args.destination)
