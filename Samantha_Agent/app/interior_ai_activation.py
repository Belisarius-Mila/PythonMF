"""Price-reviewed interior pilot and activation after compatible Cockpit deployment."""
from __future__ import annotations

import hashlib
import ast
import json
from pathlib import Path
import re
import subprocess
import uuid

from app.communication import agent_roles
from app.communication.luna_release import http_call
from app.file_persistence import atomic_write_json, exclusive_file_lock
from app.email.service_control import EmailServiceController
from app.interior_ai import CodexInteriorDriver, InteriorAI, PROTOCOL, digest
from app.interior_atelier import AtelierError, InteriorAtelier, _now, _safe_path

PROJECT = Path(__file__).resolve().parents[1]
PROBES = PROJECT / "data/private/neuberk_interier_design/ai_probes"
PROBE_ID = re.compile(r"[0-9a-f]{32}")


def role_consumer_readiness(controller=None):
    """Read the owned hourly copy's parser constants without importing or changing it."""
    controller = controller or EmailServiceController()
    status = controller.status()
    if not status["installed"]:
        return {"ready": True, "email_service": "not_installed"}
    if not status["owned"]:
        return {"ready": False, "email_service": "ownership_unverified"}
    try:
        receipt = json.loads(controller.receipt_path.read_text())
        path = _safe_path(Path(receipt["runtime"]) / "app/communication/agent_roles.py")
        if path.stat().st_size > 100000:
            raise ValueError("parser size")
        tree = ast.parse(path.read_text())
        constants = {}
        known = set()
        for statement in tree.body:
            if not isinstance(statement, ast.Assign) or len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
                continue
            name, value = statement.targets[0].id, statement.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                constants[name] = value.value
            if (name == "KNOWN_ROLES" and isinstance(value, ast.Call) and isinstance(value.func, ast.Name)
                    and value.func.id == "frozenset" and len(value.args) == 1 and isinstance(value.args[0], ast.Set)):
                known = {constants.get(item.id) if isinstance(item, ast.Name) else item.value
                         for item in value.args[0].elts if isinstance(item, (ast.Name, ast.Constant))}
        ready = agent_roles.INTERIOR_ROLE in known
        return {"ready": ready, "email_service": "compatible" if ready else "registered_upgrade_required",
                "source_head": status["source_head"], "parser_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    except (OSError, ValueError, SyntaxError, KeyError, TypeError):
        return {"ready": False, "email_service": "parser_unverified"}


def source_digest():
    paths = ("app/interior_ai.py", "app/codex_appserver.py", "app/communication/agent_roles.py", "app/interior_atelier.py")
    return digest({path: hashlib.sha256((PROJECT / path).read_bytes()).hexdigest() for path in paths})


def _write(path, data):
    _safe_path(path)
    atomic_write_json(path, data)
    path.chmod(0o600)


def _proof(probe_id):
    if not isinstance(probe_id, str) or not PROBE_ID.fullmatch(probe_id):
        raise AtelierError("Neplatná identita pilotu.")
    path = _safe_path(PROBES / probe_id / "proof.json")
    if path.stat().st_size > 100000:
        raise AtelierError("Důkaz pilotu má nepovolenou velikost.")
    return path, json.loads(path.read_text())


def probe_candidate(*, model, reasoning_effort, cost_review, project_id, room_id, base_id="base",
                    include_image=False, confirmed=False, probe_id=None, store=None, client_factory=None):
    """At most one analysis and one image request, only after explicit pilot consent.

    The price-reviewed binding lives in the private probe, not in production config.
    Results use the normal room-scoped journal and immutable variant path. Repeating
    this probe identity returns its existing proof, never another model call.
    """
    if confirmed is not True:
        return {"state": "not_started", "reason": "Nejprve zvol model a rozsah cenově posouzeného pilotu."}
    if (not isinstance(model, str) or not agent_roles.MODEL_ID.fullmatch(model)
            or reasoning_effort not in agent_roles.EFFORTS or type(include_image) is not bool
            or not isinstance(cost_review, str) or not 8 <= len(cost_review) <= 240):
        raise AtelierError("Pilot nemá platnou volbu modelu a cenové posouzení.")
    store = store or InteriorAtelier()
    probe_id = probe_id or uuid.uuid4().hex
    if not PROBE_ID.fullmatch(probe_id):
        raise AtelierError("Pilot nemá platnou identitu.")
    home = _safe_path(PROBES / probe_id)
    fingerprint = digest([model, reasoning_effort, cost_review, project_id, room_id, base_id, include_image])
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    proof_path = home / "proof.json"
    with exclusive_file_lock(home / "pilot", timeout=0):
        if proof_path.exists():
            _, proof = _proof(probe_id)
            if proof["fingerprint"] != fingerprint:
                raise AtelierError("Stejný pilot už patří jinému zadání.")
            return {"probe_id": probe_id, "state": proof["state"], "chat_passed": proof.get("chat_passed", False),
                    "image_passed": proof.get("image_passed", False), "replayed": True}
        state = store._read()
        _, room = store._room(state, project_id, room_id)
        draft = store._draft(room, base_id)
        if not draft["source_ids"]:
            raise AtelierError("Nejprve v Ateliéru vyber podklady pro pilot.")
        relative = f"data/private/neuberk_interier_design/ai_probes/{probe_id}/proof.json"
        binding = {"label": "AI architekt interiérového Ateliéru", "preferred_model": model,
            "approved_models": [{"model": model, "reasoning_effort": reasoning_effort,
                "cost_review": cost_review, "dry_run_evidence": relative}]}
        config = home / "fixture/config/agent_roles.json"
        config.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        _write(config, {"schema": 1, "roles": {agent_roles.INTERIOR_ROLE: binding}})
        proof = {"schema": 1, "probe_id": probe_id, "fingerprint": fingerprint, "state": "running", "accepted": False,
            "model": model, "reasoning_effort": reasoning_effort, "include_image": include_image,
            "binding": binding, "code_digest": source_digest(), "created_at": _now(),
            "project_id": project_id, "room_id": room_id, "base_id": base_id, "jobs": {},
            "chat_passed": False, "image_passed": False,
            "release_policy_digest": agent_roles.load_role()["policy_digest"]}
        _write(proof_path, proof)
        driver = CodexInteriorDriver(roles_path=config, **({"client_factory": client_factory} if client_factory else {}))
        service = InteriorAI(store, driver=driver, launcher=lambda callback: callback(), require_activation=False)
        messages = {"chat": "Prohlédni všechny přiložené podklady. Stručně popiš místnost, navrhni tři praktická zlepšení a řekni, které rozměry nebo informace potřebuješ ověřit. Respektuj uložené zadání a pevné prvky.",
                    "image": "Vytvoř právě jednu realistickou koncepční variantu této místnosti podle pracovního obrázku a uloženého zadání. Zachovej stavební dispozici, pohled kamery a pevné prvky. Použij přiložené fotografie jako podklady. Vygeneruj jeden obrázek, žádné další varianty."}
        try:
            for mode in (["chat", "image"] if include_image else ["chat"]):
                result = service.start({"project_id": project_id, "room_id": room_id, "base_id": base_id,
                    "expected_revision": draft["revision"], "request_id": f"pilot-{mode}-{probe_id}",
                    "message": messages[mode], "mode": mode})
                job = store._room(store._read(), project_id, room_id)[1]["ai_requests"][result["request_id"]]
                proof["jobs"][mode] = result["request_id"]
                proof[mode + "_passed"] = job["status"] == "completed" and (mode == "chat" or bool(job["variant_id"]))
                _write(proof_path, proof)
                if not proof[mode + "_passed"]:
                    break
            proof["state"] = "review_required" if proof["chat_passed"] and (not include_image or proof["image_passed"]) else "attention"
        except Exception as error:
            proof.update(state="attention", error_type=type(error).__name__)
        _write(proof_path, proof)
        return {"probe_id": probe_id, "state": proof["state"], "chat_passed": proof["chat_passed"],
                "image_passed": proof["image_passed"], "replayed": False}


def accept_probe(probe_id, *, confirmed=False):
    """Main Adam records one review of the real result; this never calls the model."""
    if confirmed is not True:
        return {"state": "not_accepted"}
    path, proof = _proof(probe_id)
    if (proof["state"] not in {"review_required", "accepted"} or proof["code_digest"] != source_digest()
            or not proof["chat_passed"] or proof["include_image"] and not proof["image_passed"]):
        raise AtelierError("Pilot nemá přijatelný výsledek nebo se jeho zdroje změnily.")
    proof.update(state="accepted", accepted=True, accepted_at=_now())
    _write(path, proof)
    return {"state": "accepted", "probe_id": probe_id}


def activation_plan(probe_id, *, call=None):
    """New roles cannot be added before the running parser understands them."""
    _, proof = _proof(probe_id)
    call = call or http_call
    config = agent_roles.CONFIG_PATH
    if not proof["accepted"] or proof["code_digest"] != source_digest():
        raise AtelierError("Aktivace vyžaduje přijatý a nezměněný skutečný pilot.")
    if agent_roles.load_role()["policy_digest"] != proof["release_policy_digest"]:
        raise AtelierError("Role publikace se od pilotu změnila.")
    document = json.loads(config.read_bytes())
    old = document["roles"].get(agent_roles.INTERIOR_ROLE)
    if old is not None:
        if old == proof["binding"]:
            return {"state": "active", "probe_id": probe_id}
        raise AtelierError("Architekt už má jiné schválené nastavení.")
    runtime = call("/api/interior/ai/status")
    if (runtime.get("ok") is not True or runtime.get("protocol") != PROTOCOL
            or runtime.get("role_schema") != 1 or runtime.get("role") != agent_roles.INTERIOR_ROLE):
        raise AtelierError("Nejprve je nutné nasadit kompatibilní Cockpit s podporou role architekta.")
    consumers = role_consumer_readiness()
    if not consumers["ready"]:
        raise AtelierError("Před aktivací nové role je nutný registrovaný upgrade kompatibility samostatné e-mailové služby.")
    if subprocess.check_output(["git", "-C", str(PROJECT), "status", "--porcelain"], text=True).strip():
        raise AtelierError("Aktivace vyžaduje čistý checkpoint main.")
    if subprocess.check_output(["git", "-C", str(PROJECT), "branch", "--show-current"], text=True).strip() != "main":
        raise AtelierError("Aktivace patří na kanonický main.")
    return {"state": "ready", "probe_id": probe_id, "proof_digest": digest(proof),
            "config_digest": hashlib.sha256(config.read_bytes()).hexdigest(),
            "head": subprocess.check_output(["git", "-C", str(PROJECT), "rev-parse", "HEAD"], text=True).strip(),
            "role_consumers": consumers}


def activate(plan, *, confirmed=False):
    """One checked central policy edit; no Git, restart or publication."""
    if confirmed is not True or not isinstance(plan, dict) or plan.get("state") != "ready":
        return {"state": "not_applied"}
    current = activation_plan(plan["probe_id"])
    if current.get("state") == "active":
        return current
    if current != plan:
        raise AtelierError("Plán aktivace se změnil; nic nezapsáno.")
    _, proof = _proof(plan["probe_id"])
    document = json.loads(agent_roles.CONFIG_PATH.read_bytes())
    document["roles"][agent_roles.INTERIOR_ROLE] = proof["binding"]
    # Validate the exact new document with the same parser before the atomic edit.
    trial = _safe_path(PROBES / plan["probe_id"] / "activation_config.json")
    _write(trial, document)
    agent_roles.load_role(trial, role=agent_roles.INTERIOR_ROLE)
    if hashlib.sha256(agent_roles.CONFIG_PATH.read_bytes()).hexdigest() != plan["config_digest"]:
        raise AtelierError("Centrální nastavení se změnilo; nic nezapsáno.")
    atomic_write_json(agent_roles.CONFIG_PATH, document)
    return {"state": "active", "probe_id": plan["probe_id"], "model": proof["model"]}
