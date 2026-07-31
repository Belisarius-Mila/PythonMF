import csv
import filecmp
import os
import shutil
import time


DATAFRESH_API_VERSION = 2

_CLOUD_FOLDER_NAMES = (
    "Desktop",
    "Documents",
    "Downloads",
    "Plocha",
    "Dokumenty",
    "Stazene",
    "Dokumente",
    "Schreibtisch",
)


def _source_name_aliases(filename):
    stem, ext = os.path.splitext(filename)
    aliases = []
    if ext.lower() == ".csv":
        aliases.extend(
            [
                f"{stem}-2{ext}",
                f"{stem}_2{ext}",
                f"{stem} 2{ext}",
            ]
        )
    ordered = []
    seen = {filename.lower()}
    for name in aliases:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(name)
    return ordered


def _icloud_root_candidates(fast=False):
    docs = os.path.expanduser("~/Documents")
    container = os.path.abspath(os.path.join(docs, ".."))
    appgroup_root = "/private/var/mobile/Containers/Shared/AppGroup"
    mobile_docs_root = "/private/var/mobile/Library/Mobile Documents"
    mobile_docs = "/private/var/mobile/Library/Mobile Documents/com~apple~CloudDocs"
    legacy_base = os.path.expanduser(
        "~/Documents/../Shared/AppGroup/com.apple.FileProvider.Storage/File Provider Storage"
    )
    candidates = [
        docs,
        container,
        os.path.join(container, "External Files"),
        os.path.join(docs, "PythonMF"),
        os.path.join(docs, "External Files"),
        legacy_base,
        os.path.expanduser("~/Library/Mobile Documents"),
        mobile_docs_root,
        os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs"),
        mobile_docs,
        os.path.join(mobile_docs, "PythonMF"),
        appgroup_root,
    ]
    for folder_name in _CLOUD_FOLDER_NAMES:
        candidates.append(os.path.join(legacy_base, folder_name))
        candidates.append(os.path.join(mobile_docs, folder_name))

    if not fast and os.path.isdir(mobile_docs_root):
        try:
            for entry in os.listdir(mobile_docs_root):
                entry_dir = os.path.join(mobile_docs_root, entry)
                if not os.path.isdir(entry_dir):
                    continue
                candidates.extend([entry_dir, os.path.join(entry_dir, "PythonMF")])
                for folder_name in _CLOUD_FOLDER_NAMES:
                    candidates.append(os.path.join(entry_dir, folder_name))
        except Exception:
            pass

    # Dynamic iOS app-group UUID paths change across installs/devices.  Include
    # their shallow File Provider roots even in fast mode; exact path checks are
    # cheap and avoid silently keeping an old local CSV after an iOS update.
    if os.path.isdir(appgroup_root):
        try:
            for entry in os.listdir(appgroup_root):
                grp = os.path.join(appgroup_root, entry)
                if not os.path.isdir(grp):
                    continue
                py_root = os.path.join(grp, "Pythonista3")
                py_docs = os.path.join(py_root, "Documents")
                ext_files = os.path.join(py_docs, "External Files")
                fp_root = os.path.join(grp, "File Provider Storage")

                candidates.extend(
                    [
                        grp,
                        py_root,
                        py_docs,
                        ext_files,
                        os.path.join(py_docs, "PythonMF"),
                        fp_root,
                    ]
                )
                for folder_name in _CLOUD_FOLDER_NAMES:
                    candidates.append(os.path.join(py_docs, folder_name))

                # iCloud mirrored folders can live under many provider subfolders.
                if os.path.isdir(fp_root):
                    for provider in os.listdir(fp_root):
                        provider_dir = os.path.join(fp_root, provider)
                        if not os.path.isdir(provider_dir):
                            continue
                        candidates.extend([provider_dir, os.path.join(provider_dir, "PythonMF")])
                        for folder_name in _CLOUD_FOLDER_NAMES:
                            candidates.append(os.path.join(provider_dir, folder_name))
        except Exception:
            pass

    # Keep order, remove duplicates.
    ordered = []
    seen = set()
    for c in candidates:
        c_abs = os.path.abspath(c)
        if c_abs in seen:
            continue
        seen.add(c_abs)
        ordered.append(c_abs)
    return ordered


def _relative_dir_candidates(app_dir_hints, strict=False):
    if strict:
        ordered = []
        seen = set()
        for rel in list(app_dir_hints or []):
            if rel in seen:
                continue
            seen.add(rel)
            ordered.append(rel)
        return ordered
    defaults = [
        "VocabularyFR",
        "VocabularyIT",
        "FrancouzstinaApp",
        "ItalstinaApp",
        "PythonMF/VocabularyFR",
        "PythonMF/VocabularyIT",
        "PythonMF/FrancouzstinaApp",
        "PythonMF/ItalstinaApp",
        "PythonMF/MBSoft",
        "PythonMF",
        "",
    ]
    ordered = []
    seen = set()
    for rel in list(app_dir_hints or []) + defaults:
        if rel in seen:
            continue
        seen.add(rel)
        ordered.append(rel)
    return ordered


def _normalize_path(path):
    return os.path.abspath(path).replace("\\", "/").lower()


def _is_backup_like_path(path):
    p = _normalize_path(path)
    markers = (
        "/backup/",
        "/backups/",
        "/zalo",
        "/archive/",
        "/archiv/",
        "/old/",
        "/trash/",
        "/.trash/",
    )
    return any(m in p for m in markers)


def _hint_match_score(path, app_dir_hints):
    p = _normalize_path(path)
    score = 0
    for i, hint in enumerate(app_dir_hints or ()):
        hint_norm = "/" + hint.replace("\\", "/").strip("/").lower() + "/"
        if hint_norm in p:
            score += 100 - i
    return score


def _csv_profile(path):
    try:
        with open(path, mode="r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = [
                str(header or "").replace("\ufeff", "").strip()
                for header in (reader.fieldnames or [])
            ]
            row_count = sum(1 for _row in reader)
        return {
            "ok": bool(headers),
            "row_count": row_count,
            "headers": headers,
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "row_count": 0,
            "headers": [],
            "error": str(exc),
        }


def _best_candidate(candidates, app_dir_hints, prefer_larger_csv=False):
    if not candidates:
        return None
    ranked = []
    for c in candidates:
        backup_penalty = 1 if _is_backup_like_path(c) else 0
        hint_score = _hint_match_score(c, app_dir_hints)
        csv_rows = 0
        invalid_csv_penalty = 0
        if prefer_larger_csv and os.path.splitext(c)[1].lower() == ".csv":
            profile = _csv_profile(c)
            csv_rows = profile["row_count"] if profile["ok"] else -1
            invalid_csv_penalty = 0 if profile["ok"] else 1
        try:
            mtime = os.path.getmtime(c)
        except Exception:
            mtime = 0.0
        # Prefer canonical non-backup locations.  For equivalent CSV locations,
        # prefer the complete dataset before relying on timestamps copied by
        # iCloud/File Provider.
        ranked.append(
            (
                (
                    backup_penalty,
                    invalid_csv_penalty,
                    -hint_score,
                    -csv_rows,
                    -mtime,
                ),
                c,
            )
        )
    ranked.sort(key=lambda x: x[0])
    return ranked[0][1]


def _find_source_file(
    filename,
    app_dir_hints,
    local_dir=None,
    strict=False,
    allow_recursive=True,
    fast=False,
):
    local_dir_abs = os.path.abspath(local_dir) if local_dir else None
    scanned_roots = []

    def _collect_exact(name_variants, rel_strict):
        exact_candidates = []
        for root in _icloud_root_candidates(fast=fast):
            if not os.path.isdir(root):
                continue
            if root not in scanned_roots:
                scanned_roots.append(root)
            for rel in _relative_dir_candidates(app_dir_hints, strict=rel_strict):
                for candidate_name in name_variants:
                    source = os.path.join(root, rel, candidate_name) if rel else os.path.join(root, candidate_name)
                    if not os.path.exists(source):
                        continue
                    if local_dir_abs and os.path.abspath(source).startswith(local_dir_abs + os.sep):
                        continue
                    exact_candidates.append(source)
        return exact_candidates

    # Pass 1: prefer exact filename from external sources (not inside local app dir).
    prefer_larger_csv = os.path.splitext(filename)[1].lower() == ".csv"
    picked = _best_candidate(
        _collect_exact([filename], strict),
        app_dir_hints,
        prefer_larger_csv=prefer_larger_csv,
    )
    if picked:
        return picked, scanned_roots

    # Pass 1b: fallback to common filename aliases such as VocabularyFR-2.csv.
    aliases = _source_name_aliases(filename)
    if aliases:
        picked = _best_candidate(
            _collect_exact(aliases, strict),
            app_dir_hints,
            prefer_larger_csv=prefer_larger_csv,
        )
        if picked:
            return picked, scanned_roots

    if strict:
        if not allow_recursive:
            return None, scanned_roots

        # Fallback 1: broaden relative dirs but still without recursion.
        picked = _best_candidate(
            _collect_exact([filename], False),
            app_dir_hints,
            prefer_larger_csv=prefer_larger_csv,
        )
        if picked:
            return picked, scanned_roots

        if aliases:
            picked = _best_candidate(
                _collect_exact(aliases, False),
                app_dir_hints,
                prefer_larger_csv=prefer_larger_csv,
            )
            if picked:
                return picked, scanned_roots

        if not allow_recursive:
            return None, scanned_roots

        # Fallback 2: recursive external search for robust on-device path variance.
        recursive_candidates = []
        for root in _icloud_root_candidates(fast=fast):
            if not os.path.isdir(root):
                continue
            for candidate_name in [filename] + aliases:
                recursive_candidates.extend(
                    _find_source_file_recursive(
                        root,
                        candidate_name,
                        max_depth=14,
                        exclude_prefix=local_dir_abs,
                    )
                )
        picked = _best_candidate(
            recursive_candidates,
            app_dir_hints,
            prefer_larger_csv=prefer_larger_csv,
        )
        if picked:
            return picked, scanned_roots
        return None, scanned_roots

    if not allow_recursive:
        return None, scanned_roots

    # Pass 2: recursive external search (still excluding local app dir).
    recursive_candidates = []
    for root in _icloud_root_candidates(fast=fast):
        if not os.path.isdir(root):
            continue
        if root not in scanned_roots:
            scanned_roots.append(root)
        for candidate_name in [filename] + aliases:
            recursive_candidates.extend(
                _find_source_file_recursive(root, candidate_name, exclude_prefix=local_dir_abs)
            )
    picked = _best_candidate(
        recursive_candidates,
        app_dir_hints,
        prefer_larger_csv=prefer_larger_csv,
    )
    if picked:
        return picked, scanned_roots

    # No local fallback: source must come from external/iCloud location.
    return None, scanned_roots


def _find_source_file_recursive(root, filename, max_depth=14, exclude_prefix=None):
    root = os.path.abspath(root)
    root_parts = root.rstrip(os.sep).split(os.sep)
    root_depth = len(root_parts)
    exclude_prefix = os.path.abspath(exclude_prefix) if exclude_prefix else None
    found_paths = []
    for current_root, dirs, files in os.walk(root, followlinks=True):
        # Skip heavy/system folders when scanning Documents recursively.
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".Trash", ".git", ".svn")]
        current_depth = len(current_root.rstrip(os.sep).split(os.sep))
        if (current_depth - root_depth) >= max_depth:
            dirs[:] = []
            continue
        if filename in files:
            found = os.path.join(current_root, filename)
            if exclude_prefix and os.path.abspath(found).startswith(exclude_prefix + os.sep):
                continue
            found_paths.append(found)
    return found_paths


def refresh_files_from_icloud(
    local_dir,
    filenames,
    app_dir_hints=(),
    source_overrides=None,
    strict=False,
    manual_only=False,
    allow_recursive=True,
    fast=False,
    max_attempts=8,
    required_csv_columns=None,
):
    os.makedirs(local_dir, exist_ok=True)
    updated = []
    unchanged = []
    missing = []
    failed = []
    sources = {}
    diagnostics = {}
    source_rows = {}
    local_rows = {}
    ignored_overrides = []
    source_overrides = source_overrides or {}
    required_csv_columns = required_csv_columns or {}

    for filename in filenames:
        dst = os.path.join(local_dir, filename)
        local_dir_abs = os.path.abspath(local_dir)
        all_scanned_roots = []
        done = False

        for attempt in range(max_attempts):
            pinned = source_overrides.get(filename)
            pinned_exists = bool(pinned and os.path.exists(pinned))
            if manual_only:
                src = pinned if pinned_exists else None
                scanned_roots = ["pinned-source"] if src else ["manual-only-no-pinned-source"]
            else:
                automatic_src, scanned_roots = _find_source_file(
                    filename,
                    app_dir_hints,
                    local_dir=local_dir,
                    strict=strict,
                    allow_recursive=allow_recursive,
                    fast=fast,
                )
                candidates = [
                    candidate
                    for candidate in (pinned if pinned_exists else None, automatic_src)
                    if candidate
                ]
                src = _best_candidate(
                    candidates,
                    app_dir_hints,
                    prefer_larger_csv=os.path.splitext(filename)[1].lower() == ".csv",
                )
                if pinned_exists and src and os.path.abspath(src) != os.path.abspath(pinned):
                    ignored_overrides.append(filename)

            if not src and manual_only:
                src = None

            for r in scanned_roots:
                if r not in all_scanned_roots:
                    all_scanned_roots.append(r)

            if not src:
                if manual_only:
                    missing.append(filename)
                    diagnostics[filename] = all_scanned_roots
                    done = True
                    break
                if attempt < (max_attempts - 1):
                    time.sleep(min(0.5 * (attempt + 1), 2.0))
                    continue
                missing.append(filename)
                diagnostics[filename] = all_scanned_roots
                done = True
                break
            try:
                if os.path.abspath(src).startswith(local_dir_abs + os.sep):
                    if attempt < (max_attempts - 1):
                        time.sleep(min(0.5 * (attempt + 1), 2.0))
                        continue
                    missing.append(filename)
                    diagnostics[filename] = all_scanned_roots
                    done = True
                    break
                if os.path.abspath(src) == os.path.abspath(dst):
                    unchanged.append(filename)
                    sources[filename] = src
                    diagnostics[filename] = all_scanned_roots
                    if os.path.splitext(src)[1].lower() == ".csv":
                        profile = _csv_profile(src)
                        source_rows[filename] = profile["row_count"]
                        local_rows[filename] = profile["row_count"]
                    done = True
                    break
                if os.path.splitext(src)[1].lower() == ".csv":
                    profile = _csv_profile(src)
                    required = {
                        str(column or "").replace("\ufeff", "").strip()
                        for column in required_csv_columns.get(filename, ())
                        if str(column or "").strip()
                    }
                    headers = set(profile["headers"])
                    missing_columns = sorted(required - headers)
                    if not profile["ok"] or missing_columns:
                        detail = profile["error"] or (
                            "chybi sloupce " + ", ".join(missing_columns)
                        )
                        failed.append(f"{filename}: neplatny CSV zdroj ({detail})")
                        sources[filename] = src
                        diagnostics[filename] = all_scanned_roots
                        done = True
                        break
                    source_rows[filename] = profile["row_count"]
                if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
                    unchanged.append(filename)
                    sources[filename] = src
                    diagnostics[filename] = all_scanned_roots
                    if filename in source_rows:
                        local_rows[filename] = source_rows[filename]
                    done = True
                    break
                shutil.copy2(src, dst)
                updated.append(filename)
                sources[filename] = src
                diagnostics[filename] = all_scanned_roots
                if os.path.splitext(dst)[1].lower() == ".csv":
                    local_profile = _csv_profile(dst)
                    local_rows[filename] = local_profile["row_count"]
                done = True
                break
            except Exception as exc:
                if attempt < (max_attempts - 1):
                    time.sleep(min(0.5 * (attempt + 1), 2.0))
                    continue
                failed.append(f"{filename}: {exc}")
                diagnostics[filename] = all_scanned_roots
                done = True
                break

        if not done:
            diagnostics[filename] = all_scanned_roots
        if filename not in local_rows and os.path.exists(dst):
            if os.path.splitext(dst)[1].lower() == ".csv":
                local_rows[filename] = _csv_profile(dst)["row_count"]

    return {
        "updated": updated,
        "unchanged": unchanged,
        "missing": missing,
        "failed": failed,
        "sources": sources,
        "diagnostics": diagnostics,
        "source_rows": source_rows,
        "local_rows": local_rows,
        "ignored_overrides": list(dict.fromkeys(ignored_overrides)),
    }


def refresh_result_succeeded(result, filename):
    return filename in (result.get("updated") or []) or filename in (
        result.get("unchanged") or []
    )


def datafresh_status_text(result, filename, loaded_rows):
    failed = result.get("failed") or []
    if failed:
        return "✗ DataFresh chyba: " + " | ".join(str(item) for item in failed)
    if filename in (result.get("missing") or []):
        return f"✗ DataFresh nenasel iCloud zdroj {filename}"
    if not refresh_result_succeeded(result, filename):
        return f"✗ DataFresh nedokoncil aktualizaci {filename}"

    source_rows = (result.get("source_rows") or {}).get(filename)
    if isinstance(source_rows, int) and source_rows != int(loaded_rows or 0):
        return (
            f"✗ DataFresh nesoulad: zdroj {source_rows}, "
            f"nacteno {int(loaded_rows or 0)}"
        )
    state = "Aktualizovano" if filename in (result.get("updated") or []) else "Aktualni"
    if isinstance(source_rows, int):
        return f"✓ {state}: {int(loaded_rows or 0)} slovicek (zdroj {source_rows})"
    return f"✓ {state}: {int(loaded_rows or 0)} slovicek"
