#!/usr/bin/env python3
"""Build a Jana Mac release in a NEW directory; never install or overwrite data.

The private JSON request supplies input_dir, output_dir and python (build venv).
Without --execute this only validates and prints the build plan.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "VocabularyFR"
DEFAULT_REQUEST = ROOT / "Samantha_Agent/data/private/vocabularyfr_jana_release/request.json"
CODE = ("vocab_trainer_fr.py", "vocabulary_csv_store.py", "verb_training.py",
        "verb_training_screen.py", "jana_launcher.py", "bundle_check.py")
CONTENT = ("VerbeTraining.csv", "VerbeSentences.csv", "verb_training_pictures.json")
DATA = ("VocabularyFR.csv", "VerbeFR.csv", "FR_Pict.csv")
IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_request(request):
    paths = {name: Path(request[name]).expanduser().absolute()
             for name in ("input_dir", "output_dir", "python")}
    if os.path.lexists(paths["output_dir"]):
        raise ValueError("Výstupní adresář už existuje; použij nový název vydání.")
    if not paths["python"].is_file():
        raise ValueError("Chybí Python sestavovacího prostředí.")
    for name in DATA:
        path = paths["input_dir"] / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Chybí bezpečný vstupní soubor {name}.")
    with (paths["input_dir"] / DATA[0]).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"FR", "CZ", "Sentence", "SentenceT"}.issubset(reader.fieldnames or ()):
            raise ValueError("Slovník nemá potřebné sloupce.")
        rows = list(reader)
    if not rows or any(not row.get(key, "").strip() for row in rows
                       for key in ("Sentence", "SentenceT")):
        raise ValueError("Slovník musí mít všechny věty i překlady.")
    return paths, len(rows)


def build(request):
    paths, count = validate_request(request)
    out = paths["output_dir"]
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    source = out / "source"
    source.mkdir()
    hashes = {}
    for name in CODE + CONTENT:
        shutil.copyfile(SOURCE / name, source / name)
        hashes[name] = digest(source / name)
    for name in DATA:
        shutil.copyfile(paths["input_dir"] / name, source / name)
        hashes[name] = digest(source / name)
    shutil.copytree(SOURCE / "training_images", source / "training_images")
    pictures = source / "Pict"
    pictures.mkdir()
    for path in (ROOT / "Pict").iterdir():
        if path.is_file() and (path.suffix.lower() in IMAGES or path.name == "mapping.json"):
            shutil.copyfile(path, pictures / path.name)
    args = [str(paths["python"]), "-m", "PyInstaller", "--onedir", "--windowed",
            "--name", "VocabularyFR", "--osx-bundle-identifier", "cz.pythonmf.vocabularyfr.jana",
            "--target-arch", "x86_64", "--distpath", str(out / "dist"),
            "--workpath", str(out / "build"), "--specpath", str(source)]
    for name in CONTENT + DATA + ("training_images", "Pict"):
        destination = name if name in ("training_images", "Pict") else "."
        args.extend(["--add-data", f"{source / name}:{destination}"])
    args.append(str(source / "jana_launcher.py"))
    with (out / "build.log").open("w") as log:
        subprocess.run(args, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=True)
    app = out / "dist/VocabularyFR.app"
    # Only the freshly generated bundle: Finder may attach metadata while building.
    subprocess.run(["/usr/bin/xattr", "-cr", str(app)], check=True)
    subprocess.run(["/usr/bin/codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)
    subprocess.run(["/usr/bin/codesign", "--verify", "--deep", str(app)], check=True)
    strict = subprocess.run(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)],
                            capture_output=True, text=True)
    if strict.returncode and "resource fork, Finder information, or similar detritus" not in strict.stderr:
        raise ValueError("Podpis balíčku neprošel striktní kontrolou: " + strict.stderr)
    report = out / "bundle_check.json"
    with (out / "bundle_check.log").open("w") as log:
        subprocess.run([str(app / "Contents/MacOS/VocabularyFR"), "--check-bundle", str(report)],
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=90)
    checked = json.loads(report.read_text(encoding="utf-8"))
    if checked["rows"] != count or checked["verbs"] != checked["images_loaded"]:
        raise ValueError("Zabalená aplikace neprošla kontrolou dat a obrázků.")
    portable = out / "VocabularyFR"
    portable.mkdir()
    # ditto retains the framework links and permissions inside the macOS bundle.
    subprocess.run(["/usr/bin/ditto", str(app), str(portable / app.name)], check=True)
    for name in DATA:
        shutil.copyfile(source / name, portable / name)
    shutil.copyfile(SOURCE / "JANA_CTI_ME.txt", portable / "CTI_ME.txt")
    archive = out / "VocabularyFR_Jana.zip"
    subprocess.run(["/usr/bin/ditto", "-c", "-k", "--keepParent", str(portable), str(archive)], check=True)
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise ValueError("Poškozený distribuční ZIP.")
    manifest = {"rows": count, "source_sha256": hashes, "zip_sha256": digest(archive),
                "python": subprocess.check_output([str(paths["python"]), "--version"], text=True).strip(),
                "pyinstaller": subprocess.check_output([str(paths["python"]), "-m", "PyInstaller", "--version"], text=True).strip(),
                "codesign_deep": "OK", "codesign_strict": "Finder metadata" if strict.returncode else "OK",
                "architecture": "x86_64", "data_authority": "CSV beside app, explicit --data-dir"}
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    paths, count = validate_request(request)
    if args.execute:
        print(json.dumps(build(request), indent=2))
    else:
        print(json.dumps({"rows": count, "output": str(paths["output_dir"]),
                          "execute": False, "writes_live_data": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
