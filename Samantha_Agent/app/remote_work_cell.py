"""Isolated, local workspace for a write-capable Codex app-server thread."""

from __future__ import annotations

import atexit
import json
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.codex_appserver import AppServerError, CodexAppServerClient
from app.codex_appserver_lab import AppServerLabService, DEFAULT_CODEX_BIN
from app.file_persistence import atomic_write_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_REPO_ROOT = PROJECT_ROOT.parent
DEFAULT_REMOTE_ROOT = PROJECT_ROOT / "data" / "private" / "appserver_remote"
DEFAULT_WORKSPACE_ROOT = DEFAULT_REMOTE_ROOT / "workspace"
DEFAULT_REMOTE_STATE_PATH = DEFAULT_REMOTE_ROOT / "state.json"
DEFAULT_WORKSPACE_META_PATH = DEFAULT_REMOTE_ROOT / "workspace_meta.json"
REMOTE_REASONING_EFFORT = "high"
REMOTE_SANDBOX_MODE = "workspace-write"
REMOTE_SANDBOX_POLICY: dict[str, Any] = {
    "type": "workspaceWrite",
    "networkAccess": False,
    "writableRoots": [],
}
REMOTE_APPROVAL_POLICY = "never"
REMOTE_DEVELOPER_INSTRUCTIONS = (
    "Jsi Adam Remote, plnohodnotny projektovy spolupracovnik Mily v izolovane lokalni kopii "
    "repozitare PythonMF. Odpovidej cesky, Mílovi tykej a pracuj vecne. Pred dulezitou praci "
    "si precti AGENTS.md, Samantha_Agent/AGENTS.md, Samantha_Agent/memory/MEMORY_INDEX.md a "
    "relevantni handoff. Smis cist a upravovat pouze tuto izolovanou pracovní kopii, pouzivat "
    "nastroje, spoustet testy a pripravovat skutecne zmeny. Nikdy nehledej ani nemen data mimo "
    "aktualni workspace, nepouzivej sit, neprovadej push, nemen git remote, nemaz soubory ani "
    "neprovadej destruktivni git operace. Pred zmenou zkontroluj stav, zachovej cizi upravy a po "
    "zmene uved zmenene soubory, testy, rizika a dalsi krok. Commit vytvari pouze potvrzene "
    "checkpoint tlacitko Cockpitu. TVBCP je strucny lidsky rozhodovaci protokol, ne kopie chatu."
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


def _status_rows(repo: Path) -> list[dict[str, str]]:
    completed = _run_git(repo, ["status", "--porcelain=v1", "--untracked-files=all"])
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise AppServerError(detail or "Git status Remote Work Cell selhal.")
    output = completed.stdout.rstrip("\r\n")
    rows: list[dict[str, str]] = []
    for raw in output.splitlines():
        if len(raw) < 4:
            continue
        rows.append({"status": raw[:2], "path": raw[3:]})
    return rows


class RemoteWorkspaceManager:
    """Create and inspect one non-destructive clone used only by Adam Remote."""

    def __init__(
        self,
        *,
        source_repo: Path = SOURCE_REPO_ROOT,
        workspace_root: Path = DEFAULT_WORKSPACE_ROOT,
        metadata_path: Path = DEFAULT_WORKSPACE_META_PATH,
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
                    "workspace_label": "Adam Remote – izolovaná lokální kopie",
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
                    "workspace_label": "Adam Remote – neúplná kopie",
                    "source_branch": source_branch,
                    "source_head": source_head,
                    "source_pending_changes": source_pending,
                    "dirty": False,
                    "changes": [],
                    "remotes": [],
                    "message": "Cílová složka existuje, ale není platnou Remote Work Cell; nic nepřepisuji.",
                }
            changes = _status_rows(self.workspace_root)
            head = _git_output(self.workspace_root, ["rev-parse", "HEAD"])
            branch = _git_output(self.workspace_root, ["branch", "--show-current"])
            remotes = [item for item in _git_output(self.workspace_root, ["remote"]).splitlines() if item]
            base_head = self._metadata_base_head()
            relation = "aligned"
            local_commit_count = 0
            if head != source_head:
                if base_head and base_head == source_head:
                    ancestor = _run_git(
                        self.workspace_root,
                        ["merge-base", "--is-ancestor", source_head, head],
                    )
                    if ancestor.returncode == 0:
                        relation = "local_ahead"
                        local_commit_count = int(
                            _git_output(
                                self.workspace_root,
                                ["rev-list", "--count", f"{source_head}..{head}"],
                            )
                            or 0
                        )
                    else:
                        relation = "diverged"
                elif base_head and head == base_head:
                    relation = "source_ahead"
                else:
                    relation = "diverged"
            source_update_available = relation == "source_ahead"
            local_checkpoint_ahead = relation == "local_ahead"
            if remotes:
                message = "Remote Work Cell má neočekávaný Git remote; pracovní turny jsou zablokované."
            elif relation == "source_ahead":
                message = "Remote Work Cell je čistá, ale její základ čeká na aktualizaci z main."
            elif relation == "local_ahead":
                message = "Remote Work Cell má lokální WIP checkpoint bez pushnutí."
            elif relation == "diverged":
                message = "Remote Work Cell a main se rozešly; automatický sync je zablokovaný."
            else:
                message = "Remote Work Cell je připravená, aktuální a nemá Git remote."
            return {
                "ok": not remotes,
                "prepared": True,
                "workspace_label": "Adam Remote – izolovaná lokální kopie",
                "source_branch": source_branch,
                "source_head": source_head,
                "source_pending_changes": source_pending,
                "branch": branch,
                "head": head,
                "base_head": base_head,
                "workspace_relation": relation,
                "local_checkpoint_ahead": local_checkpoint_ahead,
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

    def prepare(self) -> dict[str, Any]:
        with self._lock:
            existing = self.status()
            if self.workspace_root.exists():
                if existing.get("prepared") and existing.get("ok"):
                    return {**existing, "created": False}
                raise AppServerError(str(existing.get("message") or "Remote Work Cell nelze bezpečně použít."))
            source_branch = _git_output(self.source_repo, ["branch", "--show-current"])
            if source_branch != "main":
                raise AppServerError("Remote Work Cell lze připravit pouze z hlavní větve main.")
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
                raise AppServerError("Remote Work Cell není v bezpečném stavu pro aktualizaci.")
            if current.get("remotes"):
                raise AppServerError("Remote Work Cell má Git remote; aktualizace je zablokovaná.")
            if current.get("branch") != "main":
                raise AppServerError("Remote Work Cell lze aktualizovat pouze na větvi main.")
            if current.get("dirty"):
                raise AppServerError("Nejdřív zkontroluj a checkpointuj rozpracované změny; workspace není čistý.")
            if current.get("source_branch") != "main":
                raise AppServerError("Zdrojový projekt není na větvi main; aktualizace je zablokovaná.")

            old_head = str(current.get("head") or "")
            source_head = str(current.get("source_head") or "")
            if old_head == source_head:
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
            if any(self._blocked_checkpoint_path(path) for path in incoming_paths):
                raise AppServerError("Main obsahuje pro Remote Work Cell blokovaný private, env nebo mediální soubor.")

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

    def review(self) -> dict[str, Any]:
        """Return path-level work evidence without exposing file contents."""
        with self._lock:
            current = self.status()
            if not current.get("prepared") or not current.get("ok"):
                raise AppServerError("Remote Work Cell není v bezpečném stavu pro kontrolu změn.")
            checkpoint_changes: list[dict[str, str]] = []
            if current.get("local_checkpoint_ahead"):
                base_head = str(current.get("base_head") or "")
                diff_text = _git_output(
                    self.workspace_root,
                    ["diff", "--name-status", "--find-renames", f"{base_head}..HEAD"],
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
                "local_checkpoint_ahead": bool(current.get("local_checkpoint_ahead")),
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
                raise AppServerError("Remote Work Cell není v bezpečném stavu pro checkpoint.")
            changes = list(current.get("changes") or [])
            if not changes:
                return {**current, "checkpoint_created": False, "message": "Není co checkpointovat."}
            blocked = [row["path"] for row in changes if self._blocked_checkpoint_path(row["path"])]
            if blocked:
                raise AppServerError("Checkpoint obsahuje blokovaný private, env nebo mediální soubor.")
            _git_output(self.workspace_root, ["diff", "--check"])
            _git_output(self.workspace_root, ["add", "--all", "--", "."])
            staged = _git_output(self.workspace_root, ["diff", "--cached", "--name-only"])
            staged_paths = [item for item in staged.splitlines() if item]
            if not staged_paths or any(self._blocked_checkpoint_path(item) for item in staged_paths):
                raise AppServerError("Checkpoint safety check odmítl staged obsah.")
            safe_message = " ".join(str(message or "").split())[:120] or "WIP Remote Adam checkpoint"
            _git_output(self.workspace_root, ["commit", "-m", safe_message], timeout=60)
            result = self.status()
            return {
                **result,
                "checkpoint_created": True,
                "checkpoint_head": result.get("head", ""),
                "message": "Lokální WIP checkpoint byl vytvořen bez pushnutí.",
            }


def read_remote_runtime_profile(
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
        if REMOTE_REASONING_EFFORT not in efforts:
            raise AppServerError("Efektivní Codex model nepodporuje požadovaný reasoning high.")
        return {
            "model": model_name,
            "display_name": str(model.get("displayName") or model_name),
            "configured_reasoning_effort": str(config.get("model_reasoning_effort") or ""),
            "reasoning_effort": REMOTE_REASONING_EFFORT,
            "supported_reasoning_efforts": efforts,
            "sandbox_mode": REMOTE_SANDBOX_MODE,
            "sandbox_policy": dict(REMOTE_SANDBOX_POLICY),
            "approval_policy": REMOTE_APPROVAL_POLICY,
            "network_access": False,
        }
    finally:
        client.close()


class RemoteWorkCellService:
    """Facade joining the isolated clone and a write-capable app-server thread."""

    def __init__(
        self,
        *,
        workspace: RemoteWorkspaceManager | None = None,
        state_path: Path = DEFAULT_REMOTE_STATE_PATH,
        codex_binary: str = DEFAULT_CODEX_BIN,
        client_factory: Callable[..., CodexAppServerClient] = CodexAppServerClient,
        profile_getter: Callable[..., dict[str, Any]] = read_remote_runtime_profile,
    ):
        self.workspace = workspace or RemoteWorkspaceManager()
        self.state_path = Path(state_path)
        self.codex_binary = codex_binary
        self.client_factory = client_factory
        self.profile_getter = profile_getter
        self._profile: dict[str, Any] | None = None
        self._lab: AppServerLabService | None = None
        self._lock = threading.RLock()

    def _runtime_profile(self) -> dict[str, Any]:
        if self._profile is None:
            self._profile = self.profile_getter(
                cwd=self.workspace.project_root,
                codex_binary=self.codex_binary,
                client_factory=self.client_factory,
            )
        return dict(self._profile)

    def _service(self) -> AppServerLabService:
        workspace = self.workspace.status()
        if not workspace.get("prepared") or not workspace.get("ok") or workspace.get("remotes"):
            raise AppServerError("Remote Work Cell není připravená nebo nemá bezpečně odstraněný Git remote.")
        if self._lab is None:
            profile = self._runtime_profile()
            self._lab = AppServerLabService(
                state_path=self.state_path,
                project_root=self.workspace.project_root,
                client_factory=self.client_factory,
                codex_binary=self.codex_binary,
                developer_instructions=REMOTE_DEVELOPER_INSTRUCTIONS,
                sandbox_mode=REMOTE_SANDBOX_MODE,
                sandbox_policy=REMOTE_SANDBOX_POLICY,
                approval_policy=REMOTE_APPROVAL_POLICY,
                reasoning_effort=REMOTE_REASONING_EFFORT,
                model=str(profile["model"]),
                default_role="Adam Remote",
            )
        return self._lab

    def _merge_status(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        workspace = self.workspace.status()
        result = dict(payload or {})
        result.update(
            {
                "ok": bool(result.get("ok", True)) and bool(workspace.get("ok", True)),
                "remote_work_cell": True,
                "prepared": bool(workspace.get("prepared")),
                "workspace": workspace,
            }
        )
        if workspace.get("prepared") and workspace.get("ok"):
            result["runtime_profile"] = self._runtime_profile()
        return result

    def status(self) -> dict[str, Any]:
        with self._lock:
            workspace = self.workspace.status()
            if not workspace.get("prepared") or not workspace.get("ok"):
                return self._merge_status(
                    {
                        "ok": bool(workspace.get("ok", True)),
                        "connection_state": "disconnected",
                        "thread_ready": False,
                        "active_thread": None,
                        "threads": [],
                        "messages": [],
                        "lifecycle_events": [],
                        "message": workspace.get("message") or "Remote Work Cell zatím není připravená.",
                    }
                )
            return self._merge_status(self._service().status())

    def prepare(self) -> dict[str, Any]:
        with self._lock:
            prepared = self.workspace.prepare()
            result = self.status()
            result["created"] = bool(prepared.get("created"))
            result["message"] = (
                "Izolovaná Remote Work Cell byla vytvořena bez private dat a bez Git remote."
                if prepared.get("created")
                else "Remote Work Cell už byla bezpečně připravená."
            )
            return result

    def sync_from_main(self, *, confirmed: bool) -> dict[str, Any]:
        with self._lock:
            result = self.workspace.sync_from_main(confirmed=confirmed)
            lab_status = self._lab.status() if self._lab is not None else {}
            return self._merge_status({**lab_status, **result, "ok": True})

    def new_thread(self, *, label: str = "") -> dict[str, Any]:
        return self._merge_status(self._service().new_thread(label=label, role="Adam Remote"))

    def resume(self) -> dict[str, Any]:
        return self._merge_status(self._service().resume())

    def restart(self) -> dict[str, Any]:
        return self._merge_status(self._service().restart())

    def disconnect(self) -> dict[str, Any]:
        return self._merge_status(self._service().disconnect())

    def update_capsule(self, *, registry_id: str, capsule: dict[str, Any]) -> dict[str, Any]:
        return self._merge_status(
            self._service().update_capsule(registry_id=registry_id, capsule=capsule)
        )

    def send(self, *, text: str, client_message_id: str, client_sent_at: str = "") -> dict[str, Any]:
        with self._lock:
            result = self._service().send(
                text=text,
                client_message_id=client_message_id,
                client_sent_at=client_sent_at,
            )
            result["workspace"] = self.workspace.status()
            result["runtime_profile"] = self._runtime_profile()
            result["remote_work_cell"] = True
            return result

    def save_message_to_tvbcp(self, *, client_message_id: str) -> dict[str, Any]:
        return self._service().save_message_to_tvbcp(client_message_id=client_message_id)

    def checkpoint(self, *, confirmed: bool, message: str = "") -> dict[str, Any]:
        result = self.workspace.checkpoint(confirmed=confirmed, message=message)
        return self._merge_status({"ok": True, **result})

    def close(self) -> None:
        with self._lock:
            if self._lab is not None:
                self._lab.close()


REMOTE_WORK_CELL = RemoteWorkCellService()
atexit.register(REMOTE_WORK_CELL.close)
