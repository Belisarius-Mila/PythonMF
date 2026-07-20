"""Isolated, local Git workspace used by the canonical Human–Adam session."""

from __future__ import annotations

import json
import re
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.codex_appserver import AppServerError, CodexAppServerClient, DEFAULT_CODEX_BIN
from app.file_persistence import atomic_write_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_REPO_ROOT = PROJECT_ROOT.parent
DEFAULT_HUMAN_ADAM_ROOT = PROJECT_ROOT / "data" / "private" / "appserver_remote"
DEFAULT_HUMAN_ADAM_WORKSPACE_ROOT = DEFAULT_HUMAN_ADAM_ROOT / "workspace"
DEFAULT_HUMAN_ADAM_WORKSPACE_META_PATH = DEFAULT_HUMAN_ADAM_ROOT / "workspace_meta.json"
HUMAN_ADAM_REASONING_EFFORT = "high"
HUMAN_ADAM_SANDBOX_MODE = "workspace-write"
HUMAN_ADAM_SANDBOX_POLICY: dict[str, Any] = {
    "type": "workspaceWrite",
    "networkAccess": False,
    "writableRoots": [],
}
HUMAN_ADAM_APPROVAL_POLICY = "never"
HUMAN_ADAM_WORKSPACE_DEVELOPER_INSTRUCTIONS = (
    "Jsi Adam v kanonicke relaci pracovniho rozhrani Human–Adam, plnohodnotny projektovy spolupracovnik Mily "
    "v izolovane lokalni kopii "
    "repozitare PythonMF. Odpovidej cesky, Mílovi tykej a pracuj vecne. Pred dulezitou praci "
    "si precti AGENTS.md, Samantha_Agent/AGENTS.md, Samantha_Agent/memory/MEMORY_INDEX.md a "
    "relevantni handoff. Smis cist a upravovat pouze tuto izolovanou pracovní kopii, pouzivat "
    "nastroje, spoustet testy a pripravovat skutecne zmeny. Nikdy nehledej ani nemen data mimo "
    "aktualni workspace, nepouzivej sit, neprovadej push, nemen git remote, nemaz soubory ani "
    "neprovadej destruktivni git operace. Pred zmenou zkontroluj stav, zachovej cizi upravy a po "
    "zmene uved zmenene soubory, testy, rizika a dalsi krok. Sam nikdy nespoustej git add, "
    "git commit, checkpoint, prevzeti do main, push ani nasazeni. Tyto operace spousti vyhradne "
    "Mila samostatnymi potvrzenymi ovladacimi prvky Cockpitu. TVBCP je strucny lidsky "
    "rozhodovaci protokol, ne kopie chatu."
)
BLOCKED_CHECKPOINT_PARTS = (
    "/data/private/",
    "/data/session_autosave/",
)
BLOCKED_CHECKPOINT_NAMES = {".env", ".env.local", ".env.production"}
BLOCKED_CHECKPOINT_SUFFIXES = {
    ".aac",
    ".aif",
    ".aiff",
    ".dmg",
    ".doc",
    ".docx",
    ".heic",
    ".jpeg",
    ".jpg",
    ".m4a",
    ".mov",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".wav",
    ".webp",
    ".zip",
}
PUBLIC_SOURCE_MEDIA_PREFIXES = (
    "ColorsAndNumbers/web_colors_numbers/",
    "docs/colors-numbers/",
)
MAX_PUBLIC_SOURCE_MEDIA_BYTES = 8 * 1024 * 1024


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _run_git(
    cwd: Path,
    args: list[str],
    *,
    timeout: float = 60.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/usr/bin/git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _git_output(cwd: Path, args: list[str], *, timeout: float = 30.0) -> str:
    completed = _run_git(cwd, args, timeout=timeout)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise AppServerError(detail or f"Git operace selhala: {' '.join(args)}")
    return completed.stdout.strip()


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    if not ancestor or not descendant:
        return False
    completed = _run_git(
        repo,
        ["merge-base", "--is-ancestor", ancestor, descendant],
    )
    return completed.returncode == 0


def _status_rows(repo: Path) -> list[dict[str, str]]:
    completed = _run_git(repo, ["status", "--porcelain=v1", "--untracked-files=all"])
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise AppServerError(detail or "Git status izolovaného Human–Adam workspace selhal.")
    output = completed.stdout.rstrip("\r\n")
    rows: list[dict[str, str]] = []
    for raw in output.splitlines():
        if len(raw) < 4:
            continue
        rows.append({"status": raw[:2], "path": raw[3:]})
    return rows


class HumanAdamWorkspaceManager:
    """Create and inspect the non-destructive clone used by Human–Adam."""

    def __init__(
        self,
        *,
        source_repo: Path = SOURCE_REPO_ROOT,
        workspace_root: Path = DEFAULT_HUMAN_ADAM_WORKSPACE_ROOT,
        metadata_path: Path = DEFAULT_HUMAN_ADAM_WORKSPACE_META_PATH,
        project_dir_name: str = PROJECT_ROOT.name,
    ):
        self.source_repo = Path(source_repo).resolve()
        self.workspace_root = Path(workspace_root).resolve()
        self.metadata_path = Path(metadata_path).resolve()
        self.project_dir_name = project_dir_name
        self._lock = threading.RLock()

    @property
    def project_root(self) -> Path:
        return self.workspace_root / self.project_dir_name

    def _valid_workspace(self) -> bool:
        return (
            (self.workspace_root / ".git").exists()
            and (self.project_root / "AGENTS.md").is_file()
            and (self.project_root / "memory" / "MEMORY_INDEX.md").is_file()
        )

    def status(self) -> dict[str, Any]:
        with self._lock:
            source_head = _git_output(self.source_repo, ["rev-parse", "HEAD"])
            source_branch = _git_output(self.source_repo, ["branch", "--show-current"])
            source_pending = len(_status_rows(self.source_repo))
            if not self.workspace_root.exists():
                return {
                    "ok": True,
                    "prepared": False,
                    "workspace_label": "Human–Adam – izolovaná lokální kopie",
                    "source_branch": source_branch,
                    "source_head": source_head,
                    "source_pending_changes": source_pending,
                    "dirty": False,
                    "changes": [],
                    "remotes": [],
                }
            if not self._valid_workspace():
                return {
                    "ok": False,
                    "prepared": False,
                    "workspace_label": "Human–Adam – neúplná kopie",
                    "source_branch": source_branch,
                    "source_head": source_head,
                    "source_pending_changes": source_pending,
                    "dirty": False,
                    "changes": [],
                    "remotes": [],
                    "message": "Cílová složka existuje, ale není platným Human–Adam workspace; nic nepřepisuji.",
                }
            changes = _status_rows(self.workspace_root)
            head = _git_output(self.workspace_root, ["rev-parse", "HEAD"])
            branch = _git_output(self.workspace_root, ["branch", "--show-current"])
            remotes = [item for item in _git_output(self.workspace_root, ["remote"]).splitlines() if item]
            base_head = self._metadata_base_head()
            relation = "aligned"
            local_commit_count = 0
            local_checkpoint_preserved = False
            if head != source_head:
                if _is_ancestor(self.workspace_root, source_head, head):
                    relation = "local_ahead"
                    local_commit_count = int(
                        _git_output(
                            self.workspace_root,
                            ["rev-list", "--count", f"{source_head}..{head}"],
                        )
                        or 0
                    )
                elif _is_ancestor(self.source_repo, head, source_head):
                    relation = "source_ahead"
                else:
                    relation = "diverged"
                    if (
                        re.fullmatch(r"[0-9a-f]{40}", base_head)
                        and _is_ancestor(self.workspace_root, base_head, head)
                    ):
                        local_commit_count = int(
                            _git_output(
                                self.workspace_root,
                                ["rev-list", "--count", f"{base_head}..{head}"],
                            )
                            or 0
                        )
                        local_checkpoint_preserved = local_commit_count > 0
            source_update_available = relation == "source_ahead"
            local_checkpoint_ahead = relation == "local_ahead"
            if remotes:
                message = "Human–Adam workspace má neočekávaný Git remote; pracovní turny jsou zablokované."
            elif relation == "source_ahead":
                message = "Human–Adam workspace je čistý, ale jeho základ čeká na aktualizaci z main."
            elif relation == "local_ahead":
                message = "Human–Adam workspace má lokální WIP checkpoint bez pushnutí."
            elif relation == "diverged":
                message = (
                    "Human–Adam workspace má zachovaný lokální WIP checkpoint, ale main se mezitím změnil; "
                    "audit a automatický sync jsou zablokované."
                    if local_checkpoint_preserved
                    else "Human–Adam workspace a main se rozešly; automatický sync je zablokovaný."
                )
            else:
                message = "Human–Adam workspace je připravený, aktuální a nemá Git remote."
            return {
                "ok": not remotes,
                "prepared": True,
                "workspace_label": "Human–Adam – izolovaná lokální kopie",
                "source_branch": source_branch,
                "source_head": source_head,
                "source_pending_changes": source_pending,
                "branch": branch,
                "head": head,
                "base_head": base_head,
                "workspace_relation": relation,
                "local_checkpoint_ahead": local_checkpoint_ahead,
                "local_checkpoint_preserved": local_checkpoint_preserved,
                "local_commit_count": local_commit_count,
                "source_update_available": source_update_available,
                "sync_available": source_update_available,
                "sync_allowed": bool(
                    source_update_available
                    and branch == "main"
                    and not changes
                    and not remotes
                ),
                "dirty": bool(changes),
                "changes": changes[:80],
                "change_count": len(changes),
                "remotes": remotes,
                "project_ready": self.project_root.is_dir(),
                "message": message,
            }

    def _metadata(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return dict(raw) if isinstance(raw, dict) else {}

    def _metadata_base_head(self) -> str:
        return str(self._metadata().get("base_head") or "")

    def _write_metadata(self, values: dict[str, Any]) -> None:
        atomic_write_json(
            self.metadata_path,
            values,
            ensure_ascii=False,
            indent=2,
        )

    def _ensure_local_commit_identity(self) -> None:
        """Copy missing repo-local Git identity without relying on hostname discovery."""
        identity: dict[str, str] = {}
        for key in ("user.name", "user.email"):
            source_value = _run_git(
                self.source_repo,
                ["config", "--local", "--get", key],
            )
            value = source_value.stdout.strip()
            if source_value.returncode != 0 or not value:
                raise AppServerError(
                    "Hlavní repozitář nemá úplnou lokální Git identitu; checkpoint nic nepřipravil."
                )
            identity[key] = value

        for key, value in identity.items():
            current = _run_git(
                self.workspace_root,
                ["config", "--local", "--get", key],
            )
            if current.returncode == 0 and current.stdout.strip():
                continue
            configured = _run_git(
                self.workspace_root,
                ["config", "--local", key, value],
            )
            if configured.returncode != 0:
                raise AppServerError(
                    "Lokální Git identitu izolovaného workspace se nepodařilo bezpečně nastavit."
                )

    def prepare(self) -> dict[str, Any]:
        with self._lock:
            existing = self.status()
            if self.workspace_root.exists():
                if existing.get("prepared") and existing.get("ok"):
                    self._ensure_local_commit_identity()
                    return {**self.status(), "created": False}
                raise AppServerError(str(existing.get("message") or "Human–Adam workspace nelze bezpečně použít."))
            source_branch = _git_output(self.source_repo, ["branch", "--show-current"])
            if source_branch != "main":
                raise AppServerError("Human–Adam workspace lze připravit pouze z hlavní větve main.")
            base_head = _git_output(self.source_repo, ["rev-parse", "HEAD"])
            self.workspace_root.parent.mkdir(parents=True, exist_ok=True)
            completed = subprocess.run(
                [
                    "/usr/bin/git",
                    "clone",
                    "--local",
                    "--no-hardlinks",
                    "--no-tags",
                    "--single-branch",
                    "--branch",
                    "main",
                    str(self.source_repo),
                    str(self.workspace_root),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout).strip()
                raise AppServerError(detail or "Izolovanou lokální kopii se nepodařilo vytvořit.")
            _git_output(self.workspace_root, ["remote", "remove", "origin"])
            if _git_output(self.workspace_root, ["remote"]):
                raise AppServerError("Git remote se z pracovní kopie nepodařilo odstranit.")
            self._ensure_local_commit_identity()
            self._write_metadata(
                {
                    "schema_version": 1,
                    "created_at": _now(),
                    "base_head": base_head,
                    "source_branch": source_branch,
                    "project_dir_name": self.project_dir_name,
                }
            )
            result = self.status()
            return {**result, "created": True}

    def sync_from_main(self, *, confirmed: bool) -> dict[str, Any]:
        """Fast-forward a clean isolated clone from committed local main only."""
        with self._lock:
            if not confirmed:
                raise AppServerError("Aktualizace z main vyžaduje výslovné potvrzení v Cockpitu.")
            current = self.status()
            if not current.get("prepared") or not current.get("ok"):
                raise AppServerError("Human–Adam workspace není v bezpečném stavu pro aktualizaci.")
            if current.get("remotes"):
                raise AppServerError("Human–Adam workspace má Git remote; aktualizace je zablokovaná.")
            if current.get("branch") != "main":
                raise AppServerError("Human–Adam workspace lze aktualizovat pouze na větvi main.")
            if current.get("dirty"):
                raise AppServerError("Nejdřív zkontroluj a checkpointuj rozpracované změny; workspace není čistý.")
            if current.get("source_branch") != "main":
                raise AppServerError("Zdrojový projekt není na větvi main; aktualizace je zablokovaná.")

            old_head = str(current.get("head") or "")
            source_head = str(current.get("source_head") or "")
            if old_head == source_head:
                metadata = self._metadata()
                metadata.update(
                    {
                        "schema_version": 1,
                        "base_head": source_head,
                        "source_branch": "main",
                        "project_dir_name": self.project_dir_name,
                        "last_synced_at": _now(),
                    }
                )
                self._write_metadata(metadata)
                current = self.status()
                return {
                    **current,
                    "synced": False,
                    "from_head": old_head,
                    "to_head": source_head,
                    "incoming_change_count": 0,
                    "message": "Izolovaný workspace už odpovídá aktuálnímu commitnutému main.",
                }

            _git_output(
                self.workspace_root,
                ["fetch", "--no-tags", str(self.source_repo), "refs/heads/main"],
                timeout=120,
            )
            if _git_output(self.workspace_root, ["remote"]):
                raise AppServerError("Lokální fetch neočekávaně vytvořil Git remote; nic neaktualizuji.")
            fetched_head = _git_output(self.workspace_root, ["rev-parse", "FETCH_HEAD"])
            source_head_after_fetch = _git_output(self.source_repo, ["rev-parse", "HEAD"])
            source_branch_after_fetch = _git_output(self.source_repo, ["branch", "--show-current"])
            if fetched_head != source_head or source_head_after_fetch != source_head:
                raise AppServerError("Main se během přípravy změnil; aktualizaci zopakuj nad stabilním stavem.")
            if source_branch_after_fetch != "main":
                raise AppServerError("Zdrojový projekt během přípravy opustil main; nic neaktualizuji.")

            ancestor = _run_git(
                self.workspace_root,
                ["merge-base", "--is-ancestor", "HEAD", "FETCH_HEAD"],
            )
            if ancestor.returncode != 0:
                raise AppServerError(
                    "Izolovaný workspace a main se rozešly; automatický merge ani přepis nejsou povolené."
                )

            incoming_text = _git_output(
                self.workspace_root,
                ["diff", "--name-status", "--find-renames", "HEAD", "FETCH_HEAD"],
            )
            incoming_rows: list[tuple[str, list[str]]] = []
            for line in incoming_text.splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    incoming_rows.append((parts[0], parts[1:]))
            unsafe_types = [status for status, _ in incoming_rows if status[:1] not in {"A", "M"}]
            if unsafe_types:
                raise AppServerError(
                    "Main obsahuje mazání, přejmenování nebo netypickou změnu; automatický update je odmítnutý."
                )
            incoming_paths = [path for _, paths in incoming_rows for path in paths]
            if any(
                not self._source_sync_path_allowed(path, fetched_head=fetched_head)
                for path in incoming_paths
            ):
                raise AppServerError("Main obsahuje pro Human–Adam blokovaný private, env nebo mediální soubor.")

            _git_output(self.workspace_root, ["diff", "--check", "HEAD", "FETCH_HEAD"])
            _git_output(
                self.workspace_root,
                ["merge", "--ff-only", "--no-edit", "FETCH_HEAD"],
                timeout=120,
            )
            result = self.status()
            if result.get("head") != source_head or result.get("dirty") or result.get("remotes"):
                raise AppServerError("Kontrola po aktualizaci nepotvrdila čistý workspace bez Git remote.")
            metadata = self._metadata()
            metadata.update(
                {
                    "schema_version": 1,
                    "base_head": source_head,
                    "source_branch": "main",
                    "project_dir_name": self.project_dir_name,
                    "last_synced_at": _now(),
                }
            )
            self._write_metadata(metadata)
            result = self.status()
            return {
                **result,
                "synced": True,
                "from_head": old_head,
                "to_head": source_head,
                "incoming_change_count": len(incoming_rows),
                "message": "Izolovaný workspace byl bezpečně fast-forwardován z lokálního main.",
            }

    @staticmethod
    def _blocked_checkpoint_path(path_text: str) -> bool:
        normalized = "/" + path_text.replace("\\", "/").strip('"')
        path = Path(path_text.strip('"'))
        return (
            path.name in BLOCKED_CHECKPOINT_NAMES
            or path.suffix.lower() in BLOCKED_CHECKPOINT_SUFFIXES
            or any(part in normalized for part in BLOCKED_CHECKPOINT_PARTS)
        )

    def checkpoint_path_allowed(self, path_text: str) -> bool:
        """Return the existing checkpoint path policy without exposing contents."""
        return not self._blocked_checkpoint_path(path_text)

    def _source_sync_path_allowed(self, path_text: str, *, fetched_head: str) -> bool:
        if not self._blocked_checkpoint_path(path_text):
            return True
        normalized = path_text.replace("\\", "/").strip('"')
        path = Path(normalized)
        if (
            path.suffix.lower() not in BLOCKED_CHECKPOINT_SUFFIXES
            or not any(normalized.startswith(prefix) for prefix in PUBLIC_SOURCE_MEDIA_PREFIXES)
        ):
            return False
        try:
            size = int(
                _git_output(
                    self.workspace_root,
                    ["cat-file", "-s", f"{fetched_head}:{normalized}"],
                )
            )
        except (AppServerError, ValueError):
            return False
        return 0 <= size <= MAX_PUBLIC_SOURCE_MEDIA_BYTES

    def review(self) -> dict[str, Any]:
        """Return path-level work evidence without exposing file contents."""
        with self._lock:
            current = self.status()
            if not current.get("prepared") or not current.get("ok"):
                raise AppServerError("Human–Adam workspace není v bezpečném stavu pro kontrolu změn.")
            checkpoint_changes: list[dict[str, str]] = []
            checkpoint_base_head = ""
            checkpoint_head = ""
            checkpoint_subject = ""
            checkpoint_visible = bool(
                current.get("local_checkpoint_ahead") or current.get("local_checkpoint_preserved")
            )
            if checkpoint_visible:
                checkpoint_head = str(current.get("head") or "")
                checkpoint_subject = " ".join(
                    _git_output(self.workspace_root, ["log", "-1", "--format=%s"]).split()
                )[:120]
                checkpoint_base_value = (
                    current.get("source_head")
                    if current.get("local_checkpoint_ahead")
                    else current.get("base_head")
                )
                checkpoint_base_head = str(checkpoint_base_value or "")
                if not checkpoint_base_head:
                    raise AppServerError("Human–Adam checkpoint nemá ověřitelný Git základ.")
                diff_text = _git_output(
                    self.workspace_root,
                    ["diff", "--name-status", "--find-renames", f"{checkpoint_base_head}..HEAD"],
                )
                for line in diff_text.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        checkpoint_changes.append(
                            {
                                "status": parts[0],
                                "path": " → ".join(parts[1:]),
                            }
                        )
            return {
                "ok": True,
                "dirty": bool(current.get("dirty")),
                "changes": list(current.get("changes") or []),
                "change_count": int(current.get("change_count") or 0),
                "checkpoint_changes": checkpoint_changes[:120],
                "checkpoint_change_count": len(checkpoint_changes),
                "checkpoint_base_head": checkpoint_base_head,
                "checkpoint_head": checkpoint_head,
                "checkpoint_subject": checkpoint_subject,
                "local_checkpoint_ahead": bool(current.get("local_checkpoint_ahead")),
                "local_checkpoint_preserved": bool(current.get("local_checkpoint_preserved")),
                "local_commit_count": int(current.get("local_commit_count") or 0),
                "workspace_relation": str(current.get("workspace_relation") or "unknown"),
                "source_update_available": bool(current.get("source_update_available")),
                "has_git_remote": bool(current.get("remotes")),
            }

    def checkpoint(self, *, confirmed: bool, message: str = "") -> dict[str, Any]:
        with self._lock:
            if not confirmed:
                raise AppServerError("Checkpoint vyžaduje výslovné potvrzení v Cockpitu.")
            current = self.status()
            if not current.get("prepared") or not current.get("ok"):
                raise AppServerError("Human–Adam workspace není v bezpečném stavu pro checkpoint.")
            changes = list(current.get("changes") or [])
            if not changes:
                return {**current, "checkpoint_created": False, "message": "Není co checkpointovat."}
            blocked = [row["path"] for row in changes if self._blocked_checkpoint_path(row["path"])]
            if blocked:
                raise AppServerError("Checkpoint obsahuje blokovaný private, env nebo mediální soubor.")
            self._ensure_local_commit_identity()
            _git_output(self.workspace_root, ["diff", "--check"])
            _git_output(self.workspace_root, ["add", "--all", "--", "."])
            staged = _git_output(self.workspace_root, ["diff", "--cached", "--name-only"])
            staged_paths = [item for item in staged.splitlines() if item]
            if not staged_paths or any(self._blocked_checkpoint_path(item) for item in staged_paths):
                raise AppServerError("Checkpoint safety check odmítl staged obsah.")
            safe_message = " ".join(str(message or "").split())[:120] or "WIP Human-Adam checkpoint"
            _git_output(self.workspace_root, ["commit", "-m", safe_message], timeout=60)
            result = self.status()
            return {
                **result,
                "checkpoint_created": True,
                "checkpoint_head": result.get("head", ""),
                "message": "Lokální WIP checkpoint byl vytvořen bez pushnutí.",
            }


def read_human_adam_runtime_profile(
    *,
    cwd: Path,
    codex_binary: str = DEFAULT_CODEX_BIN,
    client_factory: Callable[..., CodexAppServerClient] = CodexAppServerClient,
) -> dict[str, Any]:
    client = client_factory(codex_binary=codex_binary)
    try:
        config = client.read_effective_config(cwd=cwd)
        model_name = str(config.get("model") or "")
        if not model_name:
            raise AppServerError("Codex efektivní konfigurace neobsahuje model.")
        matching = [
            item
            for item in client.list_models(include_hidden=True)
            if item.get("id") == model_name or item.get("model") == model_name
        ]
        if not matching:
            raise AppServerError("Efektivní Codex model není v runtime katalogu.")
        model = matching[0]
        efforts = [
            str(item.get("reasoningEffort") or "")
            for item in model.get("supportedReasoningEfforts") or []
            if isinstance(item, dict)
        ]
        if HUMAN_ADAM_REASONING_EFFORT not in efforts:
            raise AppServerError("Efektivní Codex model nepodporuje požadovaný reasoning high.")
        return {
            "model": model_name,
            "display_name": str(model.get("displayName") or model_name),
            "configured_reasoning_effort": str(config.get("model_reasoning_effort") or ""),
            "reasoning_effort": HUMAN_ADAM_REASONING_EFFORT,
            "supported_reasoning_efforts": efforts,
            "sandbox_mode": HUMAN_ADAM_SANDBOX_MODE,
            "sandbox_policy": dict(HUMAN_ADAM_SANDBOX_POLICY),
            "approval_policy": HUMAN_ADAM_APPROVAL_POLICY,
            "network_access": False,
        }
    finally:
        client.close()
