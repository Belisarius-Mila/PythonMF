"""REC-04 acceptance boundary; production requires private runtime activation.

No model, service, Git, production-path default or installation. The trusted
operator supplies ReviewContext and confirmation; neither is model authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import tempfile
from typing import Callable
from zoneinfo import ZoneInfo

from app.file_persistence import atomic_create_text, atomic_write_json, exclusive_file_lock
from app import recovery_guide_quality as quality
from app.recovery_guide_sources import Source, Snapshot, canonical_json, digest
from app.recovery_guide_publish import Target, _publish_candidate, icloud_metadata


@dataclass(frozen=True)
class PublicationDraft:
    packet_json: str  # Immutable copy of all inputs, never a mutable model dict.

    @property
    def sha256(self) -> str:
        return digest(self.packet_json)


def _hydrate(packet: dict):
    raw = packet["snapshot"]
    snapshot = Snapshot(raw["head"], Source(**raw["original"]), tuple(Source(**s) for s in raw["sources"]),
                        tuple(raw["scopes"]), raw["excluded_text_files"])
    raw = dict(packet["context"])
    raw["checked_on"] = date.fromisoformat(raw["checked_on"])
    raw["facts"] = tuple(quality.SourceFact(**f) for f in raw["facts"])
    raw["workflows"] = tuple(tuple(w) for w in raw["workflows"])
    raw["applications"] = tuple(raw["applications"])
    raw["unresolved_conflicts"] = tuple(raw["unresolved_conflicts"])
    context = quality.ReviewContext(**raw)
    targets = []
    for row in packet["targets"]:
        row = dict(row)
        row["aliases"] = tuple(tuple(a) for a in row["aliases"])
        targets.append(Target(**row))
    return snapshot, context, tuple(targets)


class PublicationStore:
    """One owner, fixed targets, shared lock and immutable acceptance manifests.

    Sandbox remains the default. Production requires a current private
    activation, fixed destinations and the integrated format acceptance route.
    """
    def __init__(self, state_dir: Path, *, sandbox_root: Path,
                 destinations: tuple[Path, Path], mode: str = "sandbox", activation=None):
        self.activation = activation
        if mode != "sandbox":
            from app.recovery_guide_runtime_config import RuntimeConfig
            if mode != "production" or not isinstance(activation, RuntimeConfig):
                raise ValueError("production_publication_disabled")
            activation.permits(state_dir, destinations)
        self.scope = "production" if mode == "production" else "sandbox_only"
        if not sandbox_root.is_absolute() or sandbox_root.is_symlink():
            raise ValueError("invalid_sandbox")
        self.sandbox = sandbox_root.resolve(strict=True)
        allowed = (Path(__file__).resolve().parents[1] / ".venv", Path(tempfile.gettempdir()).resolve())
        if mode == "sandbox" and not any(self.sandbox != base and self.sandbox.is_relative_to(base) for base in allowed):
            raise ValueError("sandbox_root_not_isolated")
        self.root = state_dir.absolute()
        self.destinations = tuple(p.absolute() for p in destinations)
        if len(self.destinations) != 2 or self.destinations[0].resolve() == self.destinations[1].resolve():
            raise ValueError("two_distinct_destinations_required")
        for path in (self.root, *self.destinations):
            if (path == self.root or mode == "sandbox") and (not path.resolve().is_relative_to(self.sandbox) or ".." in path.parts):
                raise ValueError("outside_sandbox")
        if any(p.resolve().is_relative_to(self.root.resolve()) for p in self.destinations):
            raise ValueError("destination_inside_state")
        stat = self.sandbox.stat()
        self.root_identity = (stat.st_dev, stat.st_ino)
        self.identity = digest(canonical_json({"sandbox": str(self.sandbox), "root": str(self.root),
            "root_identity": self.root_identity, "destinations": [str(p) for p in self.destinations]}))
        self._guard()

    def _guard(self):
        if self.activation is not None:self.activation.permits(self.root, self.destinations)
        stat = self.sandbox.stat()
        if (stat.st_dev, stat.st_ino) != self.root_identity:
            raise ValueError("sandbox_identity_changed")
        if any(p.is_symlink() for p in (self.root, *self.root.parents)):
            raise ValueError("state_alias_refused")
        if self.root.exists() and self.root.stat().st_mode & 0o077:
            raise ValueError("state_directory_not_private")
        for path in self.destinations:
            if self.scope == "sandbox_only" and not path.resolve().is_relative_to(self.sandbox):
                raise ValueError("destination_left_sandbox")
        for path in (self.root / "store.lock", self.root / "active.json", self.root / "requests", self.root / "writes"):
            if path.is_symlink():
                raise ValueError("state_alias_refused")

    def _directory(self, request_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", request_id):
            raise ValueError("invalid_request_id")
        self._guard()
        directory = self.root / "requests" / request_id
        if directory.is_symlink():
            raise ValueError("request_alias_refused")
        return directory

    @staticmethod
    def _read(path: Path) -> bytes:
        if path.is_symlink() or not path.is_file():
            raise ValueError("artifact_unavailable")
        return path.read_bytes()

    def _once(self, path: Path, text: str):
        if path.exists() or path.is_symlink():
            if self._read(path) != text.encode("utf-8"):
                raise ValueError("immutable_artifact_conflict")
        else:
            atomic_create_text(path, text)

    def _evaluate(self, draft: PublicationDraft):
        if len(draft.packet_json.encode("utf-8")) > 32_000_000:
            raise ValueError("packet_too_large")
        packet = json.loads(draft.packet_json)
        required = {"schema", "store_identity", "validator_version", "snapshot", "context", "targets", "answer", "dossier"}
        integrated = packet.get("schema") == 2
        if (set(packet) != required | ({"format_request"} if integrated else set())
                or packet["schema"] not in {1,2} or packet["store_identity"] != self.identity
                or packet["validator_version"] != quality.VALIDATOR_VERSION):
            raise ValueError("publication_scope_or_validator_changed")
        if self.scope == "production" and not integrated:
            raise ValueError("runtime_integrated_format_required")
        snapshot, context, targets = _hydrate(packet)
        if len(targets) != 2 or tuple(t.path for t in targets) != tuple(str(p) for p in self.destinations):
            raise ValueError("destinations_changed")
        for target in targets:
            target.check()
        from app import recovery_guide_consolidation as consolidation
        request = consolidation.Request(packet["format_request"]) if integrated else None
        receipt = quality.review(packet["answer"], snapshot, packet["dossier"], context, format_request=request)
        if receipt["state"] != "review" or receipt["publication_authorized"] is not False:
            raise ValueError("quality_gate_blocked")
        candidate = (consolidation.validate(packet["answer"], snapshot, request, context=context)["candidate"]
                     if integrated else quality.validate(packet["answer"], snapshot, context=context))
        return packet, snapshot, context, targets, receipt, candidate

    def prepare(self, answer: dict, snapshot: Snapshot, dossier: dict,
                context: quality.ReviewContext, *, format_request=None) -> PublicationDraft:
        self._guard()
        raw_context = asdict(context) | {"checked_on": context.checked_on.isoformat()}
        packet = {"schema": 1, "store_identity": self.identity, "validator_version": quality.VALIDATOR_VERSION,
                  "snapshot": asdict(snapshot), "context": raw_context, "answer": answer, "dossier": dossier,
                  "targets": [asdict(Target.pin(p)) for p in self.destinations]}
        if format_request is not None:
            packet.update(schema=2, format_request=format_request.envelope)
        draft = PublicationDraft(canonical_json(packet))
        self._evaluate(draft)
        return draft

    def preview(self, draft: PublicationDraft) -> dict:
        _, snapshot, _, targets, receipt, candidate = self._evaluate(draft)
        return {"state": "confirmation_required", "scope": self.scope, "binding_sha256": draft.sha256,
                "candidate_sha256": digest(candidate), "original_sha256": snapshot.original.sha256,
                "quality_sha256": digest(canonical_json(receipt)), "targets": [asdict(t) for t in targets],
                "model_calls": 0, "writes": False}

    def candidate_text(self, draft: PublicationDraft) -> str:
        return self._evaluate(draft)[-1]

    def accept(self, draft: PublicationDraft, *, request_id: str, confirmed_binding: str,
               confirmed: bool = False, now: datetime | None = None) -> dict:
        """Called by trusted operator, never by a free model confirmation field."""
        directory = self._directory(request_id)
        if confirmed_binding != draft.sha256:
            raise ValueError("confirmation_binding_mismatch")
        if not (directory / "approval.json").exists() and confirmed is not True:
            return self.preview(draft)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.stat().st_mode & 0o077:
            raise ValueError("state_directory_not_private")
        with exclusive_file_lock(self.root / "store", timeout=0):
            if (directory / "approval.json").exists():
                manifest, _, _, _ = self._load(request_id)
                if manifest["binding_sha256"] != draft.sha256:
                    raise ValueError("request_identity_conflict")
                return self.status(request_id)
            if confirmed is not True:
                return self.preview(draft)
            packet, snapshot, context, targets, receipt, candidate = self._evaluate(draft)
            now = now or datetime.now(timezone.utc)
            if now.tzinfo is None or now.astimezone(ZoneInfo("Europe/Prague")).date() != context.checked_on:
                raise ValueError("fresh_confirmation_review_required")
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            self._once(directory / "packet.json", draft.packet_json)
            self._once(directory / "candidate.txt", candidate)
            self._once(directory / "source-original.txt", snapshot.original.text)
            self._once(directory / "quality.json", canonical_json(receipt))
            manifest = {"schema": 1, "store_identity": self.identity, "request_id": request_id,
                "binding_sha256": draft.sha256, "candidate_sha256": digest(candidate),
                "original_sha256": snapshot.original.sha256, "quality_sha256": digest(canonical_json(receipt)),
                "targets": packet["targets"], "authority": "runtime_confirmation" if self.scope == "production" else "sandbox_confirmation", "accepted_at": now.isoformat()}
            # Approval commits last. Interrupted preparation can finish only with
            # the same immutable bytes; it is never mistaken for acceptance.
            self._once(directory / "approval.json", canonical_json(manifest))
            return self.status(request_id)

    def _load(self, request_id: str):
        directory = self._directory(request_id)
        raw_manifest = self._read(directory / "approval.json")
        manifest = json.loads(raw_manifest)
        expected = {"schema", "store_identity", "request_id", "binding_sha256", "candidate_sha256",
                    "original_sha256", "quality_sha256", "targets", "authority", "accepted_at"}
        if (set(manifest) != expected or raw_manifest != canonical_json(manifest).encode("utf-8")
                or manifest.get("schema") != 1 or manifest.get("store_identity") != self.identity
                or manifest.get("request_id") != request_id or manifest.get("authority") != ("runtime_confirmation" if self.scope == "production" else "sandbox_confirmation")):
            raise ValueError("invalid_acceptance_manifest")
        draft = PublicationDraft(self._read(directory / "packet.json").decode("utf-8"))
        packet, snapshot, context, targets, receipt, candidate = self._evaluate(draft)
        if (manifest["binding_sha256"] != draft.sha256 or manifest["targets"] != packet["targets"]
                or manifest["candidate_sha256"] != digest(candidate)
                or self._read(directory / "candidate.txt") != candidate.encode("utf-8")
                or manifest["original_sha256"] != snapshot.original.sha256
                or self._read(directory / "source-original.txt") != snapshot.original.text.encode("utf-8")
                or manifest["quality_sha256"] != digest(canonical_json(receipt))
                or self._read(directory / "quality.json") != canonical_json(receipt).encode("utf-8")):
            raise ValueError("accepted_artifact_changed")
        return manifest, (packet, snapshot, context, targets, receipt, candidate), draft, digest(canonical_json(manifest))

    def status(self, request_id: str) -> dict:
        directory = self._directory(request_id)
        if not (directory / "approval.json").exists():
            return {"state": "not_accepted", "request_id": request_id, "model_calls": 0}
        manifest, loaded, _, approval_sha = self._load(request_id)
        path = directory / "execution.json"
        result = json.loads(self._read(path)) if path.exists() else {"state": "accepted"}
        active = self.root / "active.json"
        if active.exists() and json.loads(self._read(active))["request_id"] != request_id:
            previous_id = json.loads(self._read(active))["request_id"]
            previous_path = self._directory(previous_id) / "execution.json"
            # A newly accepted integrated week may follow a completed delivery.
            # Its exact pinned baselines must still match both current copies.
            from app.recovery_guide_publish import file_hash
            forward = (loaded[0]["schema"] == 2 and not path.exists() and previous_path.exists()
                and json.loads(self._read(previous_path)).get("state") == "uploaded"
                and all(file_hash(t.check()) == t.baseline for t in loaded[3]))
            if not forward:
                result = {**result, "state": "superseded_or_waiting", "observed_state": result["state"]}
        return {**result, "request_id": request_id, "approval_sha256": approval_sha,
                "snapshot_sha256": loaded[4]["snapshot_sha256"], "quality_sha256": manifest["quality_sha256"],
                "candidate_sha256": manifest["candidate_sha256"], "scope": self.scope, "model_calls": 0,
                "physical_iphone_acceptance": "not_verified", "live_status_audit": False}

    def execute(self, request_id: str, *, approval_sha256: str,
                current_inputs: Callable[[dict], bool], cloud_audit=icloud_metadata,
                now: datetime | None = None) -> dict:
        directory = self._directory(request_id)
        self._load(request_id)  # Refuse unaccepted work before creating any lock.
        with exclusive_file_lock(self.root / "store", timeout=0):
            manifest, loaded, _, actual_approval = self._load(request_id)
            if actual_approval != approval_sha256:
                raise ValueError("acceptance_hash_mismatch")
            packet, snapshot, context, targets, receipt, candidate = loaded
            active = self.root / "active.json"
            if active.exists():
                previous_id = json.loads(self._read(active))["request_id"]
                if previous_id != request_id:
                    # Never resume an old approved guide over a newer version.
                    if (directory / "execution.json").exists():
                        return {**self.status(request_id), "state": "superseded"}
                    previous_path = self._directory(previous_id) / "execution.json"
                    if not previous_path.exists():
                        return {**self.status(request_id), "state": "waiting_previous_delivery"}
                    previous = json.loads(self._read(previous_path))
                    if previous["state"] != "uploaded":
                        return {**self.status(request_id), "state": "waiting_previous_delivery"}
            execution = directory / "execution.json"
            prior = json.loads(self._read(execution)) if execution.exists() else {}
            journal = self.root / "writes" / f"{request_id}.json"
            continuing = prior.get("inputs_verified") is True and journal.exists()
            if not continuing:
                now = now or datetime.now(timezone.utc)
                if now.tzinfo is None:
                    raise ValueError("timezone_required")
                from app.recovery_guide_consolidation import Request
                request = Request(packet["format_request"]) if packet["schema"] == 2 else None
                fresh = quality.review(packet["answer"], snapshot, packet["dossier"],
                    replace(context, checked_on=now.astimezone(ZoneInfo("Europe/Prague")).date()), format_request=request)
                if fresh["state"] != "review" or current_inputs(manifest) is not True:
                    return {**self.status(request_id), "state": "inputs_changed_or_stale"}
            atomic_write_json(active, {"request_id": request_id})
            atomic_write_json(execution, {"state": "applying", "inputs_verified": True})
            try:
                result = _publish_candidate(candidate, validation_sha256=manifest["candidate_sha256"],
                    authorization_sha256=actual_approval, targets=targets, state_dir=self.root / "writes",
                    request_id=request_id, cloud_audit=cloud_audit)
            except (OSError, ValueError):
                result = {"state": "attention", "reason": "publication_not_verified"}
            atomic_write_json(execution, {**result, "inputs_verified": True})
            return self.status(request_id)
