"""Deterministic stdio fixture for 05/P1. No sockets, model or project imports."""

import json
import sys


def emit(value):
    print(json.dumps(value), flush=True)


def main():
    scenario, cli_version = sys.argv[1:3]
    thread_id = "synthetic-thread"
    turn_id = "synthetic-turn"
    for line in sys.stdin:
        message = json.loads(line)
        method = message.get("method")
        params = message.get("params") or {}
        if "id" not in message:
            continue
        request_id = message["id"]
        if method == "initialize":
            result = {"userAgent": f"codex/{cli_version}", "platformFamily": "unix",
                      "platformOs": "macos", "serverInfo": {"name": "synthetic", "version": cli_version}}
        elif method == "thread/resume":
            if scenario == "rpc_error":
                emit({"id": request_id, "error": {"code": -32001, "message": "synthetic overload",
                      "data": {"codexErrorInfo": "server_overloaded", "retryAfterMs": 25}}})
                continue
            if params.get("excludeTurns") is not True or params.get("approvalPolicy") != "never":
                emit({"id": request_id, "error": {"code": -32602, "message": "missing explicit safety/history policy"}})
                continue
            result = {"thread": {"id": "wrong-thread" if scenario == "wrong_thread" else thread_id,
                      "cliVersion": cli_version, "createdAt": 1, "updatedAt": 1,
                      "cwd": params["cwd"], "ephemeral": False, "modelProvider": "openai",
                      "preview": "", "sessionId": "synthetic-session", "source": "cli",
                      "status": {"type": "idle"}, "turns": [], "projectId": None},
                      "cwd": params["cwd"], "model": params.get("model", "synthetic-approved-model"),
                      "modelProvider": "openai", "approvalPolicy": "never", "approvalsReviewer": "user",
                      "sandbox": {"type": "readOnly"}}
        elif method == "turn/start":
            if scenario == "disconnect_before_ack":
                return
            result = {"turn": {"id": turn_id, "status": "inProgress", "items": []}}
        elif method in {"thread/turns/list", "thread/items/list"}:
            second = params.get("cursor") == "synthetic-next"
            item_id = "second" if second else "first"
            row = ({"id": item_id, "status": "completed", "items": [], "itemsView": "notLoaded"}
                   if method == "thread/turns/list" else
                   {"turnId": turn_id, "item": {"type": "userMessage", "id": item_id,
                                                "content": [], "clientId": None}})
            result = {"data": [row], "nextCursor": None if second else "synthetic-next"}
        else:
            emit({"id": request_id, "error": {"code": -32601, "message": "not supported by synthetic fixture"}})
            continue
        emit({"id": request_id, "result": result})
        if method != "turn/start":
            continue
        emit({"method": "turn/started", "params": {"threadId": thread_id, "turn": result["turn"]}})
        if scenario == "disconnect_after_ack":
            return
        user = {"type": "userMessage", "id": "synthetic-user", "content": [],
                "clientId": params.get("clientUserMessageId")}
        commentary = {"type": "agentMessage", "id": "synthetic-commentary", "text": "Working",
                      "phase": "commentary"}
        final = {"type": "agentMessage", "id": "synthetic-final", "text": '{"ok":true}',
                 "phase": None if scenario == "legacy_phase" else "final_answer"}
        items = [user, final, commentary]  # commentary deliberately arrives AFTER the final answer.
        if scenario == "commentary_only":
            items = [user, commentary]
        for item in items:
            payload = {"threadId": thread_id, "turnId": turn_id, "item": item, "completedAtMs": 1000}
            if scenario == "malformed_item":
                payload.pop("completedAtMs")
            emit({"method": "item/completed", "params": payload})
        if scenario == "lost_completion":
            return
        status = "interrupted" if scenario == "interrupted" else "completed"
        turn = {"id": turn_id, "status": status, "items": items}
        if scenario == "failed":
            turn.update(status="failed", error={"message": "synthetic failure",
                        "codexErrorInfo": {"httpConnectionFailed": {"httpStatusCode": 503}},
                        "additionalDetails": "synthetic detail"})
        emit({"method": "turn/completed", "params": {"threadId": thread_id, "turn": turn}})


if __name__ == "__main__":
    main()
