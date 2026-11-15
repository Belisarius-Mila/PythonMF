"""Server-owned validation selection and authenticated, exact-input receipts.

Changed domains and consumer contracts run before release; full regression is
nightly/manual. No full-suite baseline is required. Receipts live in
private Git metadata, outside model workspaces and the versioned source tree.
"""
from __future__ import annotations

import ast
import hashlib
import hmac
import importlib.metadata
import json
import os
import platform
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable

from app.communication.git_runtime import GIT_EXECUTABLE
from app.communication.validation_domains import (BOUNDARY_TESTS, CONTRACT_SCOPES, CORE_TESTS, FALLBACK_TESTS,
    LOADED_SOURCE_HASH, modules_for_scopes, scopes_for_path)
from app.file_persistence import FilePersistenceError, atomic_create_bytes, atomic_write_json

POLICY_VERSION = "validation-v3"
MAX_RECEIPT_AGE_SECONDS = 24 * 60 * 60
_LOADED_POLICY_SOURCE = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_DOMAIN_SOURCE = Path(__file__).with_name('validation_domains.py')
_LOADED_DOMAIN_SOURCE = LOADED_SOURCE_HASH
DOC_TESTS = ("tests.test_human_adam_workstream_memory", "tests.test_memory_truth_audit")
FRONTEND_TESTS = ("tests.test_cockpit_frontend", "tests.test_article_archive",
                  "tests.test_book_cover", "tests.test_library_photos", "tests.test_cockpit_pwa")
_DOC_NAMES = frozenset({"Samantha_Agent/memory/ACTIVE_PROJECTS.md",
                        "Samantha_Agent/memory/MEMORY_INDEX.md",
                        "Samantha_Agent/memory/LESSONS_LEARNED.md"})
_DOC_PREFIXES = tuple("Samantha_Agent/memory/" + name + "/"
                      for name in ("handoffs", "projects", "reports", "tvbcp"))


class ValidationPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidationPlan:
    mode: str
    modules: tuple[str, ...] = ()
    reason: str = "unknown_or_sensitive_change"
    domains: tuple[str, ...] = ()

    @property
    def recipe(self) -> str:
        return _digest({"policy": POLICY_VERSION, "mode": self.mode, "modules": self.modules})


def _encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def _digest(value) -> str:
    return hashlib.sha256(_encoded(value)).hexdigest()


def select_validation_plan(paths: Iterable[str], *, repo: Path | None = None,
                           base: str | None = None) -> ValidationPlan:
    if (_file_hash(Path(__file__)) != _LOADED_POLICY_SOURCE
            or _file_hash(_DOMAIN_SOURCE) != _LOADED_DOMAIN_SOURCE
            or not _registry_is_current()):
        return contract_plan('policy_runtime_requires_reload')
    modules: set[str] = set(CORE_TESTS)
    domains: set[str] = set()
    names = []
    seen = False
    for raw in paths:
        seen = True
        name = str(raw)
        if name.startswith("/") or ".." in name.split("/") or "\\" in name:
            raise ValidationPolicyError('Invalid change path.')
        if (name.startswith('Samantha_Agent/tests/test_') and name.endswith('.py')
                and name.removeprefix('Samantha_Agent/')[:-3].replace('/', '.') not in _registry()):
            raise ValidationPolicyError('Changed test must be added to the canonical test registry.')
        names.append(name)
        selected = _modules_for_path(name)
        if selected is None:
            modules.update(FALLBACK_TESTS)
            domains.add('unassigned')
            continue
        modules.update(selected)
        domains.update(_scopes(name))
    if not seen:
        return contract_plan('no_new_scope_requires_existing_proof')
    if repo is not None:
        try:
            # New code uses the same domain/consumer checks, never a hidden
            # full-suite bootstrap. Compile changed Python even outside the
            # static gate's long-standing source manifest.
            for name in names:
                path = repo / name
                if path.suffix == '.py' and path.is_file():
                    ast.parse(path.read_text(encoding='utf-8'), filename=name)
            extra, reached = _dependent_tests(repo, names)
            modules.update(extra)
            domains.update(reached)
        except ValidationPolicyError as exc:
            modules.update(FALLBACK_TESTS)
            return ValidationPlan('targeted', tuple(sorted(modules)), str(exc), tuple(sorted(domains)))
        except (OSError, SyntaxError, UnicodeError):
            raise ValidationPolicyError('Changed source or dependency graph cannot be parsed.')
    return ValidationPlan("targeted", tuple(sorted(modules)), "reviewed_domains", tuple(sorted(domains)))


def contract_plan(reason: str) -> ValidationPlan:
    return ValidationPlan('targeted', tuple(sorted(FALLBACK_TESTS)), reason)


def covers(body: dict, plan: ValidationPlan) -> bool:
    return body.get('mode') == 'full' or (plan.mode == 'targeted'
        and set(plan.modules).issubset(body.get('covered_modules', body.get('modules', ()))))


def _registry():
    from scripts.cockpit_quality_gate import TEST_MODULES
    return TEST_MODULES


def _registry_is_current():
    from scripts import cockpit_quality_gate as gate
    return _file_hash(Path(gate.__file__)) == gate.LOADED_SOURCE_HASH


def _scopes(name):
    relative = name.removeprefix('Samantha_Agent/')
    return scopes_for_path(relative, _registry())


def _modules_for_path(name: str) -> tuple[str, ...] | None:
    if name in _DOC_NAMES or (name.startswith(_DOC_PREFIXES)
                              and Path(name).suffix.lower() in {".md", ".txt", ".json"}):
        return DOC_TESTS
    relative = name.removeprefix('Samantha_Agent/')
    if relative.startswith('tests/') and relative.endswith('.py'):
        module = relative[:-3].replace('/', '.')
        if module in _registry():
            # Editing an assertion does not change every production module in
            # its domain. Actual fixture users expand through reverse imports.
            return (module,)
    scopes = _scopes(name)
    if scopes:
        return tuple(sorted(modules_for_scopes(scopes, _registry())))
    return None


def _dependent_tests(repo: Path, changed: list[str]) -> tuple[set[str], set[str]]:
    """Reverse static imports, with reviewed composition/consumer contracts.

    Unknown/dynamic consumers add contract checks; parse failures are explicit
    errors. Swift/JS/runtime protocol edges belong to the explicit domain map.
    """
    def module_name(name):
        return name[:-3].replace('/', '.').removesuffix('.__init__')
    seeds = {module_name(n.removeprefix('Samantha_Agent/')) for n in changed
             if n.startswith(('Samantha_Agent/app/', 'Samantha_Agent/tests/')) and n.endswith('.py')}
    if not seeds:
        return set(), set()
    selected, scopes = set(), set()
    # Shared primitives have explicit contract suites. Following every user of
    # atomic_write_json would recreate the entire project-wide regression.
    for seed in tuple(seeds):
        owned = _scopes('Samantha_Agent/' + seed.replace('.', '/') + '.py')
        if seed.startswith('app.') and owned & CONTRACT_SCOPES:
            selected.update(modules_for_scopes(owned, _registry()))
            scopes.update(owned)
            seeds.remove(seed)
    if not seeds:
        return selected, scopes
    project = repo / 'Samantha_Agent'
    paths = [p for folder in ('app', 'tests') for p in (project/folder).rglob('*.py')]
    modules = {module_name(p.relative_to(project).as_posix()): p for p in paths}
    sources = tuple((name, path.name == '__init__.py', path.read_text(encoding='utf-8'))
                    for name, path in sorted(modules.items()))
    reverse, dynamic = _import_graph(sources)
    if {n for n in seeds if not n.startswith('tests.')} & dynamic:
        raise ValidationPolicyError('dynamic_dependency_requires_full')
    seen = set(seeds)
    pending = list(seeds)
    while pending:
        current = pending.pop()
        for consumer in reverse.get(current, ()):
            if consumer in seen:
                continue
            seen.add(consumer)
            if consumer in BOUNDARY_TESTS:
                selected.update(BOUNDARY_TESTS[consumer])
                continue
            if consumer.startswith('tests.'):
                if consumer not in _registry():
                    selected.update(FALLBACK_TESTS)
                    continue
                selected.add(consumer)
                # Changing a fixture expands all fixture users. Merely running
                # a test does not change fixtures exported by that test module.
                if current.startswith('tests.'):
                    pending.append(consumer)
                continue
            path = 'Samantha_Agent/' + modules[consumer].relative_to(project).as_posix()
            owned = _scopes(path)
            if not owned:
                selected.update(FALLBACK_TESTS)
                scopes.add('unassigned')
                pending.append(consumer)
                continue
            scopes.update(owned)
            selected.update(modules_for_scopes(owned, _registry()))
            if not owned & CONTRACT_SCOPES:
                pending.append(consumer)
    return selected, scopes


@lru_cache(maxsize=1)
def _import_graph(sources):
    """Cache by actual source text, never mtime; no stale dependency edges."""
    reverse, dynamic = {}, set()
    for name, is_package, source in sources:
        tree = ast.parse(source)
        package = name.split('.') if is_package else name.split('.')[:-1]
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and (
                    isinstance(node.func, ast.Name) and node.func.id in {'__import__','exec','eval'}
                    or isinstance(node.func, ast.Attribute)
                    and node.func.attr in {'import_module','__import__','exec','eval'}):
                dynamic.add(name)
            imports = []
            if isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
                if any(alias.name.split('.')[0] in {'importlib','runpy'} for alias in node.names):
                    dynamic.add(name)
            elif isinstance(node, ast.ImportFrom):
                prefix = package[:len(package)-node.level+1] if node.level else []
                base = '.'.join([*prefix, *([node.module] if node.module else [])])
                imports = [base, *[base+'.'+alias.name for alias in node.names]]
                if base.split('.')[0] in {'importlib','runpy'} or (
                        base == 'builtins' and any(a.name in {'__import__','exec','eval'} for a in node.names)):
                    dynamic.add(name)
            for imported in imports:
                reverse.setdefault(imported, set()).add(name)
    return reverse, dynamic


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run([GIT_EXECUTABLE, "--no-optional-locks", "-C", str(repo), *args],
                            capture_output=True, timeout=60, check=False)
    if result.returncode:
        raise ValidationPolicyError("Validation Git input could not be read.")
    return result.stdout


def changed_paths(repo: Path, base_ref: str | None = None) -> tuple[str, tuple[str, ...]]:
    if base_ref is None:
        try:
            base_ref = git(repo, "rev-parse", "--verify", "origin/main").decode().strip()
        except ValidationPolicyError:
            base_ref = "HEAD"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", base_ref):
        raise ValidationPolicyError("Invalid validation base.")
    base = git(repo, "rev-parse", "--verify", base_ref + "^{commit}").decode().strip()
    git(repo, "merge-base", "--is-ancestor", base, "HEAD")
    # --no-renames exposes both the old and new path; staged and unstaged
    # changes are compared to the immutable base, not a caller's path list.
    paths = git(repo, "diff", "--no-renames", "--name-only", "-z", base, "--")
    paths += git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    return base, tuple(sorted({os.fsdecode(p) for p in paths.split(b"\0") if p}))


def _file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@lru_cache(maxsize=64)
def _binary_hash(path: str, signature: tuple[int, ...]) -> str:
    return _file_hash(Path(path))


@lru_cache(maxsize=32768)
def _input_hash(path: str, signature: tuple[int, ...]) -> str:
    """Reuse bytes only while inode/device/size/mtime/ctime remain unchanged.

    Restoring mtime after a same-size write changes ctime and misses this cache.
    Symlinks are deliberately not cached by their own metadata.
    """
    return _file_hash(Path(path))


def validation_environment() -> dict[str, str]:
    """Run terminal and service gates with the same tools/imports/locale.

    These overrides are passed to the child, never installed in the server's
    process environment. Explicit Node/Xcode selection remains fingerprinted.
    PYTHONPATH is relative to the gate's tested project, including private clones.
    """
    environment = dict(os.environ)
    environment.update(
        PATH=os.pathsep.join(dict.fromkeys((str(Path(sys.executable).absolute().parent),
            '/opt/homebrew/bin', '/usr/local/bin', '/usr/bin', '/bin', '/usr/sbin', '/sbin'))),
        PYTHONPATH='.', PYTHONHASHSEED='0', PYTHONWARNINGS='', PYTHONUTF8='1',
        TZ='UTC', LC_ALL='C', LANG='C',
    )
    return environment


def environment_fingerprint() -> str:
    from scripts.cockpit_quality_gate import node_binary
    environment = validation_environment()
    tools = {}
    for name in ("python", "git", "node", "ffmpeg", "ffprobe", "swift", "xcrun"):
        found = (sys.executable if name == "python" else GIT_EXECUTABLE if name == "git"
                 else shutil.which(name, path=environment['PATH']))
        if name == "node":
            try:
                found = node_binary(environment=environment)
            except SystemExit:
                found = None
        if found:
            path = Path(found).resolve()
            info = path.stat()
            signature = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
            tools[name] = {"path": str(path), "sha256": _binary_hash(str(path), signature)}
        else:
            tools[name] = None
    dependencies = sorted((str(d.metadata.get("Name", "")), d.version,
                           hashlib.sha256((d.read_text("RECORD") or "").encode()).hexdigest())
                          for d in importlib.metadata.distributions())
    return _digest({"python": sys.version, "executable": str(Path(sys.executable).resolve()),
                    "prefix": sys.prefix, "platform": platform.platform(), "tools": tools,
                    "dependencies": dependencies,
                    "environment": {name: environment.get(name, "") for name in
                                    ("DEVELOPER_DIR", "PYTHONPATH", "PYTHONHASHSEED", "PYTHONWARNINGS",
                                     "PYTHONUTF8", "TZ", "LC_ALL", "LANG", "NODE_BINARY")}})


@dataclass(frozen=True)
class ValidationInputs:
    digest: str
    environment: str
    head: str
    clean: bool
    protected_digest: str = ""
    scope: tuple[tuple[str, str], ...] = ()


def capture_inputs(repo: Path, *, environment: str | None = None) -> ValidationInputs:
    names = git(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    rows = []
    resolved_repo = repo.resolve()
    for name in sorted({os.fsdecode(p) for p in names.split(b"\0") if p}):
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValidationPolicyError("Unsafe validation input.")
        path = repo / relative
        try:
            info = path.lstat()
        except FileNotFoundError:
            # A removed tracked file and its subsequently committed deletion
            # have identical test inputs. Git index membership is not content.
            continue
        if not path.resolve().is_relative_to(resolved_repo):
            raise ValidationPolicyError("External symlink input cannot be cached.")
        if stat.S_ISLNK(info.st_mode):
            if not path.is_file():
                raise ValidationPolicyError("Directory symlink input cannot be cached.")
            rows.append((name, "symlink", os.readlink(path), _file_hash(path)))
        elif stat.S_ISREG(info.st_mode):
            before = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
            sha = _input_hash(str(path), before)
            after = path.stat()
            if before != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise ValidationPolicyError("Validation input changed while hashing.")
            # A private clone may tighten group/other access (0644 -> 0600,
            # 0755 -> 0700). For the same owner these bits do not affect tests.
            # Preserve owner access, special bits, ownership and all foreign
            # file permissions; do not chmod or expose private workspace files.
            owned = info.st_uid == os.geteuid()
            mode = stat.S_IMODE(info.st_mode) & (~0o077 if owned else 0o7777)
            rows.append((name, "file", info.st_uid, None if owned else info.st_gid, mode, sha))
        else:
            raise ValidationPolicyError("Unsupported validation input.")
    env = environment if environment is not None else environment_fingerprint()
    protected, scope = [], []
    for row in rows:
        if _modules_for_path(row[0]) is not None:
            scope.append((row[0], _digest(row)))
        else:
            protected.append(row)
    return ValidationInputs(_digest({"files": rows, "environment": env, "policy": POLICY_VERSION}),
                            env, git(repo, "rev-parse", "HEAD").decode().strip(),
                            not bool(git(repo, "status", "--porcelain=v1", "--untracked-files=all").strip()),
                            _digest({"files": protected, "environment": env, "policy": POLICY_VERSION}),
                            tuple(scope))


class ValidationReceiptStore:
    def __init__(self, source_repo: Path, *, clock: Callable[[], float] = time.time):
        common = Path(os.fsdecode(git(source_repo, "rev-parse", "--git-common-dir")).strip())
        self.root = (source_repo / common).resolve() / "samantha-validation"
        self.clock = clock

    def _key(self, *, create: bool = False) -> bytes | None:
        path = self.root / "receipt-key"
        if create:
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
            if self.root.is_symlink() or self.root.stat().st_mode & 0o077:
                raise ValidationPolicyError("Validation receipt store must remain private.")
            if not path.exists():
                try:
                    atomic_create_bytes(path, secrets.token_bytes(32))
                except FilePersistenceError:
                    if not path.is_file():
                        raise
        try:
            if (self.root.is_symlink() or self.root.stat().st_mode & 0o077
                    or path.is_symlink() or path.stat().st_mode & 0o077
                    or path.stat().st_uid != os.getuid()):
                return None
            value = path.read_bytes()
            return value if len(value) == 32 else None
        except FileNotFoundError:
            return None

    def _load(self, name: str, environment: str) -> dict | None:
        key = self._key()
        if key is None:
            return None
        try:
            path = self.root / (name + ".json")
            if path.is_symlink() or path.stat().st_mode & 0o077:
                return None
            signed = json.loads(path.read_text())
            body, signature = signed["body"], signed["signature"]
            if not hmac.compare_digest(hmac.digest(key, _encoded(body), "sha256").hex(), signature):
                return None
            now = self.clock()
            if (body["policy"] != POLICY_VERSION or body["environment"] != environment
                    or not 0 <= now - body["issued_at"] <= MAX_RECEIPT_AGE_SECONDS
                    or type(body["test_count"]) is not int or body["test_count"] < 1
                    or body["mode"] not in {"full", "targeted"}):
                return None
            return body
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def baseline(self, head: str, environment: str) -> dict | None:
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            return None
        body = self._load("commit-" + head, environment)
        return body if body and body.get("head") == head else None

    def compatible_baseline(self, inputs: ValidationInputs) -> dict | None:
        """Reuse tested code when checkpoint journals changed after its gate.

        Every file outside the explicit targeted allowlist must have identical
        bytes/mode. The signed allowlisted manifest determines the new tests.
        """
        if not inputs.protected_digest:
            return None
        body = self._load("scope-" + inputs.protected_digest, inputs.environment)
        return body if body and body.get("protected_inputs") == inputs.protected_digest else None

    def find(self, inputs: ValidationInputs, plan: ValidationPlan, *, allow_bound: bool = False) -> dict | None:
        candidates = ["full-" + inputs.digest]
        if plan.mode == "targeted":
            candidates.append(plan.recipe + "-" + inputs.digest)
        if allow_bound and inputs.clean:
            candidates.append("commit-" + inputs.head)
        for name in candidates:
            body = self._load(name, inputs.environment)
            if (body and body["inputs"] == inputs.digest and
                    (covers(body, plan)
                     or (allow_bound and inputs.clean and body.get("head") == inputs.head))):
                return body
        return None

    def _write(self, name: str, body: dict) -> None:
        key = self._key(create=True)
        if key is None:
            raise ValidationPolicyError("Validation signing key is unavailable.")
        atomic_write_json(self.root / (name + ".json"),
                          {"body": body, "signature": hmac.digest(key, _encoded(body), "sha256").hex()})

    def record(self, inputs: ValidationInputs, plan: ValidationPlan, *, test_count: int,
               duration_seconds: float, baseline: dict | None = None) -> dict:
        if plan.mode not in {"full", "targeted"} or type(test_count) is not int or test_count < 1:
            raise ValidationPolicyError("Only a successful test-bearing gate can be attested.")
        if plan.mode == 'targeted' and (not plan.modules or not set(plan.modules).issubset(_registry())):
            raise ValidationPolicyError('Targeted validation requires registered test modules.')
        now = self.clock()
        coverage = set(_registry() if plan.mode == 'full' else plan.modules)
        if (baseline and baseline.get('protected_inputs') == inputs.protected_digest
                and baseline.get('environment') == inputs.environment):
            coverage.update(baseline.get('covered_modules', baseline.get('modules', ())))
        body = {"policy": POLICY_VERSION, "inputs": inputs.digest, "environment": inputs.environment,
                "head": inputs.head if inputs.clean else None, "mode": plan.mode, "recipe": plan.recipe,
                "modules": list(plan.modules), "test_count": test_count, "duration_seconds": duration_seconds,
                "protected_inputs": inputs.protected_digest, "scope_inputs": list(inputs.scope),
                "issued_at": now, "covered_modules": sorted(coverage)}
        name = ("full" if plan.mode == "full" else plan.recipe) + "-" + inputs.digest
        self._write(name, body)
        if inputs.protected_digest:
            self._write("scope-" + inputs.protected_digest, body)
        if inputs.clean:
            self._write("commit-" + inputs.head, body)
        return body

    def bind(self, inputs: ValidationInputs, body: dict) -> None:
        if inputs.clean and body["inputs"] == inputs.digest:
            self._write("commit-" + inputs.head, {**body, "head": inputs.head})
