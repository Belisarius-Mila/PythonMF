"""05/P1 offline experiment. Never imported by the production runtime.

The only executable peer this module can launch is our synthetic stdio fixture.
No Codex process, network connection, credentials or shared state are needed.
The small receipt guard is intentionally in-memory: it MUST NOT replace the
canonical session hub's persistent pending/delivery_unknown/recovery contract.
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class PilotContractError(RuntimeError):
    pass


def proxy_config(*, codex_binary: Path, socket_path: Path, cwd: Path):
    """Build, but NEVER start, a candidate shared-runtime connection.

    SDK 0.163 has no native Unix transport. CLI 0.166's `app-server proxy`
    can bridge stdio to an existing socket. Real interoperability, reconnect
    and server survival after proxy close still require a separate acceptance.
    """
    from openai_codex import CodexConfig

    if not all(path.is_absolute() for path in (codex_binary, socket_path, cwd)):
        raise PilotContractError("Executable, socket and cwd must be absolute")
    return CodexConfig(
        codex_bin=str(codex_binary),
        launch_args_override=(str(codex_binary), "app-server", "proxy", "--sock", str(socket_path)),
        cwd=str(cwd),
        client_name="samantha_p1_offline_pilot",
        experimental_api=False,
    )


def synthetic_config(scenario: str = "complete", *, cli_version: str = "0.166.0"):
    """A real SDK transport connected exclusively to a deterministic fixture."""
    from openai_codex import CodexConfig

    peer = Path(__file__).resolve().parents[1] / "scripts" / "codex_sdk_synthetic_peer.py"
    return CodexConfig(
        launch_args_override=(sys.executable, "-I", str(peer), scenario, cli_version),
        client_name="samantha_p1_offline_pilot",
        experimental_api=False,
    )


@contextmanager
def synthetic_codex(scenario: str = "complete", *, cli_version: str = "0.166.0"):
    """Close fixture pipes too: SDK 0.163.close leaves stdout/stderr open."""
    from openai_codex import Codex

    codex = Codex(synthetic_config(scenario, cli_version=cli_version))
    process = codex._client._proc
    try:
        yield codex
    finally:
        codex.close()
        if process is not None:
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()


def resume_existing(codex: Any, *, thread_id: str, cwd: Path, model: str, provider: str):
    """Only caller-resolved roles; never select or activate a replacement model."""
    from openai_codex import ApprovalMode, Sandbox

    if not thread_id or not model or not provider or not cwd.is_absolute():
        raise PilotContractError("Explicit thread, cwd, approved model and saved provider required")
    thread = codex.thread_resume(
        thread_id,
        cwd=str(cwd),
        model=model,
        model_provider=provider,
        sandbox=Sandbox.read_only,
        approval_mode=ApprovalMode.deny_all,
        include_turns=False,
    )
    if thread.id != thread_id:
        raise PilotContractError("Resumed thread differs; do not create or resend")
    return thread


def history_pages(request: Callable[..., Any], *, method: str, thread_id: str, max_pages: int = 10):
    """Bounded read-only pagination. Never fall back to unbounded thread/read."""
    if method not in {"thread/turns/list", "thread/items/list"} or not thread_id or max_pages < 1:
        raise PilotContractError("Invalid history request")
    cursor = None
    seen: set[str] = set()
    rows = []
    for _ in range(max_pages):
        params = {"threadId": thread_id, "limit": 20, "sortDirection": "asc"}
        if method == "thread/turns/list":
            params["itemsView"] = "notLoaded"
        if cursor is not None:
            params["cursor"] = cursor
        page = request(method, params)
        if not isinstance(page, dict) or not isinstance(page.get("data"), list):
            raise PilotContractError("Invalid history page")
        rows.extend(page["data"])
        cursor = page.get("nextCursor")
        if cursor is None:
            return rows
        if not isinstance(cursor, str) or not cursor or cursor in seen:
            raise PilotContractError("Invalid or repeated history cursor")
        seen.add(cursor)
    raise PilotContractError("History page budget exceeded; no automatic fallback")


@dataclass(frozen=True)
class Delivery:
    state: str
    answer: str | None = None
    error: dict[str, Any] | None = None


def evaluate_events(events: list[dict[str, Any]], *, thread_id: str, turn_id: str,
                    client_id: str, allow_legacy_phase: bool = False) -> Delivery:
    """Reference acceptance contract, using synthetic wire messages only.

    A final answer alone is not delivery proof. Require started + exactly one
    correlated user item + completed. Duplicate IDs are deduplicated, conflicting
    IDs/content fail closed. Preserve structured errors without interpreting a
    retry hint as permission to repeat an action.
    """
    started = False
    users: dict[str, dict[str, Any]] = {}
    answers: dict[str, dict[str, Any]] = {}
    terminal = None
    error = None
    conflict = False
    for event in events:
        params = event.get("params", {})
        if not isinstance(params, dict):
            continue
        turn = params.get("turn", {})
        if not isinstance(turn, dict):
            return Delivery("delivery_unknown")
        if params.get("threadId") != thread_id or params.get("turnId", turn.get("id")) != turn_id:
            continue
        method = event.get("method")
        if terminal is not None and method in {"turn/completed", "item/completed", "turn/started"}:
            conflict = True
        if method == "turn/started":
            started = True
        if method == "error":
            error = {"error": params.get("error"), "willRetry": params.get("willRetry")}
        if method == "item/completed":
            item = params.get("item", {})
            target = users if item.get("type") == "userMessage" else answers
            if item.get("type") in {"userMessage", "agentMessage"}:
                key = item.get("id")
                if not isinstance(key, str) or not key or (key in target and target[key] != item):
                    conflict = True
                else:
                    target[key] = item
        if method == "turn/completed":
            terminal = turn
            final_users = [i for i in turn.get("items", []) if i.get("type") == "userMessage"]
            if final_users:
                # Final input proof is authoritative, including mismatching client IDs.
                users = {str(n): item for n, item in enumerate(final_users)}
            final_agents = [i for i in turn.get("items", []) if i.get("type") == "agentMessage"]
            if final_agents:
                answers = {str(n): item for n, item in enumerate(final_agents)}
            if turn.get("error"):
                error = {"error": turn["error"], "willRetry": False}
    if terminal is None or conflict:
        return Delivery("delivery_unknown", error=error)
    if terminal.get("status") != "completed":
        return Delivery(str(terminal.get("status") or "delivery_unknown"), error=error)
    finals = [i.get("text") for i in answers.values() if i.get("phase") == "final_answer"]
    if not finals and allow_legacy_phase:
        finals = [i.get("text") for i in answers.values() if i.get("phase") is None]
    if (not started or len(users) != 1 or next(iter(users.values())).get("clientId") != client_id
            or len(finals) != 1 or not isinstance(finals[0], str) or not finals[0].strip()):
        return Delivery("delivery_unknown", error=error)
    return Delivery("completed", finals[0], error)


def attempt_once(ledger: dict[str, str], client_id: str, action: Callable[[], Any]) -> Any:
    """Demonstrate reservation-before-send; caller owns persistence/locking."""
    if not client_id or client_id in ledger:
        raise PilotContractError("Already reserved; reconcile evidence, never resend")
    ledger[client_id] = "pending"
    try:
        result = action()
    except BaseException:
        ledger[client_id] = "delivery_unknown"
        raise
    ledger[client_id] = "observed_result"  # NOT a canonical delivery receipt.
    return result


def main() -> None:
    from importlib.metadata import version
    from openai_codex import ApprovalMode, Sandbox

    ledger: dict[str, str] = {}
    with synthetic_codex() as codex:
        thread = resume_existing(codex, thread_id="synthetic-thread", cwd=Path.cwd().resolve(),
                                 model="synthetic-approved-model", provider="openai")
        result = attempt_once(ledger, "synthetic-request", lambda: thread.run(
            "SYNTHETIC ONLY", model="synthetic-approved-model", effort="low",
            sandbox=Sandbox.read_only, approval_mode=ApprovalMode.deny_all,
            output_schema={"type": "object", "properties": {"ok": {"type": "boolean"}},
                           "required": ["ok"], "additionalProperties": False},
        ))
        if result.status.value != "completed" or json.loads(result.final_response or "null") != {"ok": True}:
            raise PilotContractError("Synthetic result differs from the acceptance contract")
        print(json.dumps({"sdk": version("openai-codex"), "peer": "synthetic_stdio",
                          "thread": thread.id, "status": result.status.value,
                          "final_response": result.final_response, "paid_turns": 0}))


if __name__ == "__main__":
    main()
