import os
import shutil
import time


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


def _icloud_root_candidates():
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

    if os.path.isdir(mobile_docs_root):
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

    # Dynamic iOS app-group UUID paths (change across installs/devices).
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


def _best_candidate(candidates, app_dir_hints):
    if not candidates:
        return None
    ranked = []
    for c in candidates:
        backup_penalty = 1 if _is_backup_like_path(c) else 0
        hint_score = _hint_match_score(c, app_dir_hints)
        try:
            mtime = os.path.getmtime(c)
        except Exception:
            mtime = 0.0
        # backup_penalty first (0 is better), then higher hint score, then newer file.
        ranked.append(((backup_penalty, -hint_score, -mtime), c))
    ranked.sort(key=lambda x: x[0])
    return ranked[0][1]


def _find_source_file(filename, app_dir_hints, local_dir=None, strict=False):
    local_dir_abs = os.path.abspath(local_dir) if local_dir else None
    scanned_roots = []

    def _collect_exact(name_variants, rel_strict):
        exact_candidates = []
        for root in _icloud_root_candidates():
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
    picked = _best_candidate(_collect_exact([filename], strict), app_dir_hints)
    if picked:
        return picked, scanned_roots

    # Pass 1b: fallback to common filename aliases such as VocabularyFR-2.csv.
    aliases = _source_name_aliases(filename)
    if aliases:
        picked = _best_candidate(_collect_exact(aliases, strict), app_dir_hints)
        if picked:
            return picked, scanned_roots

    if strict:
        if not allow_recursive:
            return None, scanned_roots

        # Fallback 1: broaden relative dirs but still without recursion.
        picked = _best_candidate(_collect_exact([filename], False), app_dir_hints)
        if picked:
            return picked, scanned_roots

        if aliases:
            picked = _best_candidate(_collect_exact(aliases, False), app_dir_hints)
            if picked:
                return picked, scanned_roots

        # Fallback 2: recursive external search for robust on-device path variance.
        recursive_candidates = []
        for root in _icloud_root_candidates():
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
        picked = _best_candidate(recursive_candidates, app_dir_hints)
        if picked:
            return picked, scanned_roots
        return None, scanned_roots

    # Pass 2: recursive external search (still excluding local app dir).
    recursive_candidates = []
    for root in _icloud_root_candidates():
        if not os.path.isdir(root):
            continue
        if root not in scanned_roots:
            scanned_roots.append(root)
        for candidate_name in [filename] + aliases:
            recursive_candidates.extend(
                _find_source_file_recursive(root, candidate_name, exclude_prefix=local_dir_abs)
            )
    picked = _best_candidate(recursive_candidates, app_dir_hints)
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
):
    os.makedirs(local_dir, exist_ok=True)
    updated = []
    unchanged = []
    missing = []
    failed = []
    sources = {}
    diagnostics = {}
    source_overrides = source_overrides or {}

    for filename in filenames:
        dst = os.path.join(local_dir, filename)
        local_dir_abs = os.path.abspath(local_dir)
        max_attempts = 8
        all_scanned_roots = []
        done = False

        for attempt in range(max_attempts):
            # 0) First choice: user-pinned source path (stable and fast).
            pinned = source_overrides.get(filename)
            if pinned and os.path.exists(pinned):
                src = pinned
                scanned_roots = ["pinned-source"]
            else:
                src, scanned_roots = _find_source_file(
                    filename,
                    app_dir_hints,
                    local_dir=local_dir,
                    strict=strict,
                )

            for r in scanned_roots:
                if r not in all_scanned_roots:
                    all_scanned_roots.append(r)

            if not src:
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
                    done = True
                    break
                shutil.copy2(src, dst)
                updated.append(filename)
                sources[filename] = src
                diagnostics[filename] = all_scanned_roots
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

    return {
        "updated": updated,
        "unchanged": unchanged,
        "missing": missing,
        "failed": failed,
        "sources": sources,
        "diagnostics": diagnostics,
    }
