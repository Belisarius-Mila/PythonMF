"""Create a portable source ZIP from an explicit allowlist; never include user progress."""
import argparse
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
RELEASE_NAME = 'PythonSeSamanthou_1_1_20260906.zip'


def build(output_dir):
    files = [ROOT / name for name in ('README.md', 'python_se_samanthou.py',
             'assessment.py', 'course_loader.py', 'progress_store.py', 'build_release.py',
             'reference/python_se_samanthou_v1.py', 'tests/test_classroom.py', 'tests/gui_smoke.py')]
    files.extend(p for p in (ROOT / 'kurzy').rglob('*') if p.is_file()
                 and p.suffix in {'.json', '.md', '.py'} and '__pycache__' not in p.parts)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            entry = zipfile.ZipInfo(str(Path('PythonSeSamanthou') / path.relative_to(ROOT)),
                                   date_time=(2026, 9, 6, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    raw = stream.getvalue()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / RELEASE_NAME
    try:
        with destination.open('xb') as handle:
            handle.write(raw)
    except FileExistsError:
        if destination.read_bytes() != raw:
            raise FileExistsError('Cílový ZIP už obsahuje jinou verzi; zvol jinou výstupní složku.') from None
    print(f'{destination.name}: {len(files)} souborů, {len(raw)} B, SHA-256 {hashlib.sha256(raw).hexdigest()}')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output_dir', type=Path)
    build(parser.parse_args().output_dir)
