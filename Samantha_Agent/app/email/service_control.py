"""Prepare a committed runtime; install only after the exact system confirmation."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import subprocess
import tarfile
import time
from uuid import uuid4

from app.communication.agent_roles import EMAIL_ROLE, load_role
from app.file_persistence import atomic_write_text, exclusive_file_lock, FileLockTimeoutError
from app.work_repository import JsonWorkRepository, RepositoryMutation
from .continuous_agent import ContinuousEmailAgent
from .continuous_source import IMAPAgentSource, MailboxEpochChanged
from .pushcut import pushcut_status
from .service import PROJECT_ROOT, DEFAULT_ROOT, LABEL, ServiceSettings, load_settings, launch_agent_preview, approved_selection


CONFIRMATION = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
SUPPORT_ROOT = Path.home() / "Library/Application Support/SamanthaEmailAgent"


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _write(path: Path, value) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2))


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class EmailServiceController:
    def __init__(self, *, project: Path = PROJECT_ROOT, root: Path = DEFAULT_ROOT,
                 support: Path = SUPPORT_ROOT, agents: Path | None = None,
                 runner=subprocess.run, selector=approved_selection, source_factory=IMAPAgentSource):
        self.project, self.root, self.support = Path(project).resolve(), Path(root), Path(support)
        self.target = (agents or Path.home() / "Library/LaunchAgents") / (LABEL + ".plist")
        self.plan_path, self.receipt_path = self.root / "installation_plan.json", self.root / "installation.json"
        self.settings_path = self.root / "service.json"
        self.runner, self.selector, self.source_factory = runner, selector, source_factory
        self.worker = ContinuousEmailAgent(self.root)
        self.job = f"gui/{os.getuid()}/{LABEL}"

    def _git(self, *args) -> str:
        result = self.runner(["git", "-C", str(self.project), *args], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError("Nelze ověřit schválený zdroj služby.")
        return result.stdout.strip()

    def _launchctl(self, *args, check=True):
        result = self.runner(["/bin/launchctl", *args], capture_output=True, text=True, timeout=30)
        if check and result.returncode:
            raise RuntimeError("Operace vlastní hodinové služby nebyla potvrzená.")
        return result

    def _role(self):
        return load_role(self.project / "config/agent_roles.json", role=EMAIL_ROLE)

    def status(self) -> dict:
        receipt = JsonWorkRepository(self.receipt_path).read()
        health = JsonWorkRepository(self.root / "service_health.json").read()
        result = self._launchctl("print", self.job, check=False)
        installed = self.target.exists()
        owned = False
        if installed and not self.target.is_symlink() and receipt.get("plist_sha256"):
            owned = hashlib.sha256(self.target.read_bytes()).hexdigest() == receipt["plist_sha256"]
        enabled = load_settings(self.settings_path).enabled if self.settings_path.exists() else False
        return {"installed": installed, "owned": owned, "loaded": result.returncode == 0,
                "enabled": enabled, "health": health, "source_head": receipt.get("source_head", ""),
                "label": LABEL, "one_shot": True}

    def prepare(self) -> dict:
        if self._git("status", "--porcelain") or self._git("branch", "--show-current") != "main":
            raise ValueError("Příprava vyžaduje čistý commitnutý main.")
        head = self._git("rev-parse", "HEAD")
        role = self._role()
        push = pushcut_status(self.worker)
        if not (push["configured"] and push["enabled"] and push["last_test_status"] == "accepted"):
            raise ValueError("Nejprve připoj a otestuj Pushcut.")
        settings = load_settings(self.settings_path) if self.settings_path.exists() else ServiceSettings()
        if settings.enabled:
            raise ValueError("Před přípravou instalace službu pozastav.")
        if not os.access(self.project / ".venv/bin/python", os.X_OK):
            raise ValueError("Projektový Python není spustitelný.")
        # Model selection may bootstrap the shared server. Reject invalid
        # local preparation before that operational side effect.
        selected = self.selector()
        if selected["policy_digest"] != role["policy_digest"] or selected.get("fallback"):
            raise ValueError("Provozní model neodpovídá schválené roli.")
        source = self.runner(["git", "-C", str(self.project), "archive", head, "app", "scripts/continuous_email_agent.py"],
                             capture_output=True, timeout=60)
        if source.returncode:
            raise ValueError("Nelze připravit zdrojovou kopii.")
        stage = self.root / "service_staging" / (head + "-" + uuid4().hex[:8])
        stage.mkdir(parents=True, exist_ok=False)
        manifest = {}
        with tarfile.open(fileobj=io.BytesIO(source.stdout)) as archive:
            for member in archive.getmembers():
                name = member.name
                path = PurePosixPath(name)
                if not member.isfile() or not name.endswith(".py"):
                    continue
                if path.is_absolute() or ".." in path.parts or not (name.startswith("app/") or name == "scripts/continuous_email_agent.py"):
                    raise ValueError("Zdrojová kopie má nepovolenou cestu.")
                content = archive.extractfile(member).read()
                destination = stage / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                manifest[name] = hashlib.sha256(content).hexdigest()
        for relative, target in {".env": self.project / ".env", "data/private": self.project / "data/private",
                                 "config/agent_roles.json": self.project / "config/agent_roles.json"}.items():
            link = stage / relative
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(target)
        _write(stage / "runtime_manifest.json", manifest)
        runtime = self.support / "releases" / head
        spec = launch_agent_preview(project=runtime, python=self.project / ".venv/bin/python")
        spec["StandardOutPath"] = str(self.project / "logs/continuous_email_service.out.log")
        spec["StandardErrorPath"] = str(self.project / "logs/continuous_email_service.err.log")
        plan = {"schema": 1, "source_head": head, "stage": str(stage), "runtime": str(runtime),
                "manifest": manifest, "role_digest": role["policy_digest"], "settings": settings.model_dump(),
                "plist": spec, "prepared_at": _stamp()}
        plan["digest"] = _digest(plan)
        _write(self.plan_path, plan)
        if not self.settings_path.exists():
            _write(self.settings_path, settings.model_dump())
        return {"ok": True, "prepared_only": True, "plan_digest": plan["digest"], "source_head": head,
                "target": str(self.target), "runtime": str(runtime), "model": selected["model"],
                "effort": selected["reasoning_effort"], "settings": settings.model_dump(), "hours": "07–22 Europe/Prague"}

    def _plan(self, expected_digest: str) -> dict:
        plan = json.loads(self.plan_path.read_text())
        digest = plan.pop("digest")
        if digest != expected_digest or digest != _digest(plan):
            raise ValueError("Instalační plán se změnil.")
        if self._git("status", "--porcelain") or self._git("rev-parse", "HEAD") != plan["source_head"]:
            raise ValueError("Schválený zdroj služby se změnil.")
        if self._role()["policy_digest"] != plan["role_digest"]:
            raise ValueError("Schválený modelový profil se změnil.")
        if load_settings(self.settings_path).model_dump() != plan["settings"]:
            raise ValueError("Nastavení služby se od přípravy změnilo.")
        stage = Path(plan["stage"])
        if not stage.is_relative_to(self.root / "service_staging") or Path(plan["runtime"]) != self.support / "releases" / plan["source_head"]:
            raise ValueError("Instalační plán má cizí cíl.")
        for name, digest in plan["manifest"].items():
            if hashlib.sha256((stage / name).read_bytes()).hexdigest() != digest:
                raise ValueError("Zdrojová kopie se změnila.")
        if {str(path.relative_to(stage)) for path in stage.rglob("*.py")} != set(plan["manifest"]):
            raise ValueError("Zdrojová kopie obsahuje další kód.")
        for relative, target in {".env": self.project / ".env", "data/private": self.project / "data/private",
                                 "config/agent_roles.json": self.project / "config/agent_roles.json"}.items():
            if not (stage / relative).is_symlink() or os.readlink(stage / relative) != str(target):
                raise ValueError("Odkazy na společný stav se změnily.")
        return plan

    def _initialize(self, providers):
        for provider in providers:
            source = self.source_factory(provider)
            baseline = source.baseline_cursor()  # metadata only, never historical bodies
            old = self.worker.status()["sources"].get(source.key)
            if old and old.get("uidvalidity") != baseline["uidvalidity"]:
                raise MailboxEpochChanged("Výchozí identifikace schránky se změnila.")
            if not old:
                self.worker._update(lambda d: d["sources"].__setitem__(source.key, baseline))

    def _wait_check(self, started: str, *, timeout=90) -> dict:
        deadline = time.monotonic() + timeout
        grace = time.monotonic() + 10
        while time.monotonic() < deadline:
            health = JsonWorkRepository(self.root / "service_health.json").read()
            if health.get("started_at", "") >= started and health.get("status") in {"outside_hours", "completed", "already_completed", "incomplete"}:
                return health
            if health.get("started_at", "") >= started and health.get("status") == "failed":
                raise RuntimeError("První kontrola služby selhala.")
            if health.get("started_at", "") >= started and health.get("status") == "running" and time.monotonic() >= grace:
                return {**health, "startup_confirmed_only": True}
            time.sleep(.2)
        raise RuntimeError("První dokončená kontrola služby nebyla potvrzená.")

    def install(self, *, confirmation: str, plan_digest: str, verifier=None) -> dict:
        if confirmation != CONFIRMATION:
            raise ValueError("Instalace LaunchAgentu vyžaduje přesnou větu globální brzdy.")
        with exclusive_file_lock(self.root / "installation", timeout=0):
            plan = self._plan(plan_digest)
            if self.target.exists() or self.target.is_symlink() or self._launchctl("print", self.job, check=False).returncode == 0:
                raise ValueError("Cíl už existuje; první instalace nesmí přepsat cizí ani běžící službu.")
            self.selector()  # current availability, no paid turn
            self._initialize(plan["settings"]["providers"])
            runtime = Path(plan["runtime"])
            if runtime.exists() or runtime.is_symlink() or self.support.is_symlink() or runtime.parent.is_symlink():
                raise ValueError("Cílová kopie už existuje; zachovaná data vyžadují servisní kontrolu.")
            runtime.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(plan["stage"], runtime, symlinks=True)
            self.target.parent.mkdir(parents=True, exist_ok=True)
            content = plistlib.dumps(plan["plist"])
            staged = self.target.parent / ("." + LABEL + "." + uuid4().hex + ".pending")
            with staged.open("xb") as handle:
                os.chmod(staged, 0o600)
                handle.write(content); handle.flush(); os.fsync(handle.fileno())
            os.link(staged, self.target)  # create-only; keep the owned pending copy as recovery evidence
            receipt = {"source_head": plan["source_head"], "plan_digest": plan_digest, "runtime": str(runtime),
                       "plist_sha256": hashlib.sha256(content).hexdigest(), "status": "installing"}
            _write(self.receipt_path, receipt)
            started = _stamp()
            try:
                _write(self.settings_path, {**plan["settings"], "enabled": True})
                self._launchctl("bootstrap", f"gui/{os.getuid()}", str(self.target))
                self._launchctl("enable", self.job)
                self._launchctl("kickstart", self.job)
                health = (verifier or self._wait_check)(started)
                receipt.update(status="installed", verified_at=_stamp(), first_check=health)
                _write(self.receipt_path, receipt)
            except Exception:
                _write(self.settings_path, {**plan["settings"], "enabled": False})
                self._launchctl("bootout", self.job, check=False)
                receipt.update(status="failed_disabled", failed_at=_stamp())
                _write(self.receipt_path, receipt)
                raise
            return {"ok": True, "installed": True, "first_check": health, "source_head": plan["source_head"]}

    def upgrade(self, *, confirmation: str, plan_digest: str, verifier=None) -> dict:
        """Switch only the owned paused job; retain both releases and rollback data."""
        if confirmation != CONFIRMATION:
            raise ValueError("Aktualizace LaunchAgentu vyžaduje přesnou větu globální brzdy.")
        with exclusive_file_lock(self.root / "installation", timeout=0):
            plan = self._plan(plan_digest)
            current = self.status()
            if not current["owned"] or plan["settings"]["enabled"]:
                raise ValueError("Aktualizovat lze jen vlastní pozastavenou službu.")
            old = JsonWorkRepository(self.receipt_path).read()
            if old["source_head"] == plan["source_head"]:
                raise ValueError("Tento kód je již nainstalovaný; použij obnovení služby.")
            old_xml = self.target.read_text()
            new_xml = plistlib.dumps(plan["plist"]).decode()
            new_hash = hashlib.sha256(new_xml.encode()).hexdigest()
            receipt = {**old, "source_head": plan["source_head"], "plan_digest": plan_digest,
                       "runtime": plan["runtime"], "plist_sha256": new_hash,
                       "previous_source_head": old["source_head"], "status": "upgrading"}

            def restore():
                _write(self.settings_path, {**plan["settings"], "enabled": False})
                if (self.target.is_symlink() or not self.target.exists()
                        or hashlib.sha256(self.target.read_bytes()).hexdigest() not in {old["plist_sha256"], new_hash}):
                    _write(self.receipt_path, {**receipt, "status": "upgrade_attention_disabled"})
                    raise ValueError("Cizí změnu systémového souboru nelze přepsat při obnově.")
                self._launchctl("bootout", self.job, check=False)
                atomic_write_text(self.target, old_xml)
                _write(self.receipt_path, {**old, "status": "upgrade_failed_disabled", "failed_at": _stamp()})
                if current["loaded"]:
                    self._launchctl("bootstrap", f"gui/{os.getuid()}", str(self.target), check=False)

            # A busy worker must fail before copying/replacing any system files.
            with exclusive_file_lock(self.root / "service_check", timeout=0):
                self.selector()
                runtime = Path(plan["runtime"])
                if runtime.exists() or runtime.is_symlink() or self.support.is_symlink() or runtime.parent.is_symlink():
                    raise ValueError("Cílová kopie už existuje; zachovaná data vyžadují servisní kontrolu.")
                backup = self.root / "service_backups" / (uuid4().hex + ".json")
                _write(backup, {"receipt": old, "plist_xml": old_xml, "saved_at": _stamp()})
                runtime.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(plan["stage"], runtime, symlinks=True)
                try:
                    # Recheck ownership immediately before the atomic replacement.
                    if not self.status()["owned"]:
                        raise ValueError("Vlastnictví služby se během přípravy změnilo.")
                    if current["loaded"]:
                        self._launchctl("bootout", self.job)
                    atomic_write_text(self.target, new_xml)
                    _write(self.receipt_path, receipt)
                    _write(self.settings_path, {**plan["settings"], "enabled": True})
                    self._launchctl("bootstrap", f"gui/{os.getuid()}", str(self.target))
                    self._launchctl("enable", self.job)
                except Exception:
                    restore()
                    raise
            started = _stamp()
            try:
                self._launchctl("kickstart", self.job)
                health = (verifier or self._wait_check)(started)
            except Exception:
                _write(self.settings_path, {**plan["settings"], "enabled": False})
                try:
                    with exclusive_file_lock(self.root / "service_check", timeout=0):
                        restore()
                except FileLockTimeoutError:
                    # Preserve an active assessment; pause stops the next message.
                    _write(self.receipt_path, {**receipt, "status": "upgrade_attention_disabled"})
                raise
            receipt.update(status="installed", verified_at=_stamp(), upgrade_check=health)
            _write(self.receipt_path, receipt)
            return {"ok": True, "upgraded": True, "source_head": plan["source_head"],
                    "previous_source_head": old["source_head"], "health": health}

    def pause(self, *, confirmed: bool) -> dict:
        if confirmed is not True:
            raise ValueError("Pozastavení vyžaduje výslovný pokyn.")
        with exclusive_file_lock(self.root / "installation", timeout=0):
            settings = load_settings(self.settings_path)
            _write(self.settings_path, {**settings.model_dump(), "enabled": False})
        return {"ok": True, "paused": True, "current_assessment_may_finish": True}

    def configure_followups(self, *, enabled: bool, confirmed: bool, expected_source_head: str) -> dict:
        """Explicit local opt-in; never scans mail, starts a model or kicks the job."""
        from .followup_monitor import configuration, VERSION
        from .followups import _space
        if (confirmed is not True or type(enabled) is not bool
                or not isinstance(expected_source_head, str)
                or not re.fullmatch(r"[0-9a-f]{40}", expected_source_head)):
            raise ValueError("Změna hlídání vyžaduje výslovné potvrzení a přesný schválený zdroj.")
        with exclusive_file_lock(self.root / "installation", timeout=0):
            with exclusive_file_lock(self.root / "service_check", timeout=0):
                status = self.status()
                if enabled:
                    receipt = JsonWorkRepository(self.receipt_path).read()
                    runtime = self.support / "releases" / expected_source_head
                    if (not all(status.get(k) for k in ("owned", "loaded", "enabled"))
                            or status["source_head"] != expected_source_head
                            or receipt.get("status") != "installed"
                            or receipt.get("runtime") != str(runtime)
                            or runtime.is_symlink() or self.support.is_symlink()
                            or runtime.parent.is_symlink()):
                        raise ValueError("Zapnutí vyžaduje vlastní aktivní kompatibilní instalaci.")
                    prefix = self._git("rev-parse", "--show-prefix")
                    for name in ("app/email/service.py", "app/email/followup_monitor.py",
                                 "app/email/followup_assessment.py", "app/email/codex_proposer.py"):
                        path = runtime / name
                        source = self.runner(["git", "-C", str(self.project), "show",
                            expected_source_head + ":" + prefix + name], capture_output=True, timeout=30)
                        if source.returncode or path.is_symlink() or path.read_bytes() != source.stdout:
                            raise ValueError("Instalovaná podpora hlídání neodpovídá schválenému zdroji.")
                def mutate(document):
                    old = configuration(document)
                    result = {"ok": True, "enabled": enabled, "source_head": expected_source_head,
                              "worker_verified": False, "model_started": False}
                    if old["enabled"] == enabled:
                        return RepositoryMutation(document, {**result, "changed": False}, changed=False)
                    _space(document, create=True)["monitor"] = {**old, "version": VERSION,
                        "enabled": enabled, "changed_at": _stamp(), "source_head": expected_source_head,
                        "previous_last_run_at": old.get("last_run_at", ""), "last_run_at": "", "last_slot": "",
                        "last_run_status": "awaiting_worker" if enabled else "disabled"}
                    return RepositoryMutation(document, {**result, "changed": True})
                return self.worker.repository.transact(mutate).result

    def resume(self, *, confirmed: bool) -> dict:
        if confirmed is not True:
            raise ValueError("Obnovení vyžaduje výslovný pokyn.")
        with exclusive_file_lock(self.root / "installation", timeout=0):
            status = self.status()
            if not (status["owned"] and status["loaded"]):
                raise ValueError("Obnovení vyžaduje vlastní nainstalovanou službu.")
            self.selector()
            self._initialize(load_settings(self.settings_path).providers)
            settings = load_settings(self.settings_path)
            _write(self.settings_path, {**settings.model_dump(), "enabled": True})
        return {"ok": True, "resumed": True}

    def verify_restart(self, *, confirmation: str, verifier=None) -> dict:
        if confirmation != CONFIRMATION:
            raise ValueError("Obnova systémové služby vyžaduje přesnou větu globální brzdy.")
        with exclusive_file_lock(self.root / "installation", timeout=0):
            status = self.status()
            if not (status["owned"] and status["loaded"]):
                raise ValueError("Obnovit lze pouze vlastní načtenou službu.")
            receipt = JsonWorkRepository(self.receipt_path).read()
            with exclusive_file_lock(self.root / "service_check", timeout=0):
                try:
                    self._launchctl("bootout", self.job)
                    self._launchctl("bootstrap", f"gui/{os.getuid()}", str(self.target))
                    self._launchctl("enable", self.job)
                except Exception:
                    settings = load_settings(self.settings_path)
                    _write(self.settings_path, {**settings.model_dump(), "enabled": False})
                    receipt.update(status="restart_failed_disabled", failed_at=_stamp())
                    _write(self.receipt_path, receipt)
                    raise
            started = _stamp()
            try:
                self._launchctl("kickstart", self.job)
                health = (verifier or self._wait_check)(started)
            except Exception:
                settings = load_settings(self.settings_path)
                _write(self.settings_path, {**settings.model_dump(), "enabled": False})
                receipt.update(status="restart_failed_disabled", failed_at=_stamp())
                _write(self.receipt_path, receipt)
                raise
            receipt.update(restart_verified_at=_stamp(), restart_check=health)
            _write(self.receipt_path, receipt)
            return {"ok": True, "restart_verified": True, "health": health}
