"""Minimal standalone chat surface for Janička's non-development R2-Adam."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.codex_appserver import AppServerError
from app.communication.human_adam_service import HumanAdamService, MAX_MESSAGE_CHARS
from app.communication.human_adam_workspace import HUMAN_ADAM_SANDBOX_POLICY
from app.communication.janicka_r2_backend import JanickaR2Backend
from app.communication.janicka_r2_documents import R2_DOCUMENTS_RELATIVE_ROOT
from app.communication.session_hub import (
    SessionBusyError,
    SessionDeliveryUnknownError,
    SessionHubError,
)


R2_CHAT_PROFILE_ID = "janicka_r2_chat"
R2_CHAT_SESSION_RELATIVE_PATH = (
    Path("communication")
    / "workstreams"
    / "project-r2-adam-janicka"
    / "r2_chat_session.json"
)
R2_CHAT_DEVELOPER_INSTRUCTIONS = (
    "Jsi R2-Adam v jednoduchem chatu Janicky. S Janou nebo Milou mluv cesky, "
    "srozumitelne a bez technicke omacky. Nejsi vyvojovy Adam: nikdy nevyvijej, "
    "nemen projektovy kod, testy, Git, memory, handoff, TVBCP ani pracovni proudy. "
    "Zdrojova uzivatelska data Samanthy pouze cti pres registrovane read-only "
    "schopnosti a jen v rozsahu konkretniho lidskeho zadani. Nevypisuj tajemstvi "
    "ani systemove autentizacni udaje. Jediny zapis uzivatelskeho obsahu je prace "
    "s vlastnimi TXT dokumenty pres JanickaR2DocumentStore v povolenem adresari. "
    "Novy dokument vytvor jen na jasne zadani a ukaz jeho obsah v chatu ke kontrole. "
    "Tisk ani e-mail nikdy neproved bez samostatne registrovane schopnosti, nahledu "
    "a vyslovneho potvrzeni konkretni akce; dokud schopnost neni dostupna, otevrene "
    "rekni, ze akci zatim nelze dokoncit."
)
_PUBLIC_MESSAGE_FIELDS = (
    "client_message_id",
    "client_sent_at",
    "received_at",
    "completed_at",
    "status",
    "user_text",
    "answer",
    "delivery_confirmed",
    "recovery_required",
)


def _public_session(value: object) -> dict[str, Any]:
    session = value if isinstance(value, dict) else {}
    raw_messages = session.get("messages")
    messages: list[dict[str, Any]] = []
    if isinstance(raw_messages, list):
        for item in raw_messages:
            if not isinstance(item, dict):
                continue
            messages.append(
                {
                    key: item.get(key)
                    for key in _PUBLIC_MESSAGE_FIELDS
                    if key in item
                }
            )
    active_turn = session.get("active_turn")
    public_active_turn = (
        {
            "client_message_id": str(active_turn.get("client_message_id") or ""),
            "started_at": str(active_turn.get("started_at") or ""),
        }
        if isinstance(active_turn, dict)
        else None
    )
    return {
        "connected": bool(session.get("connected")),
        "connection_state": str(session.get("connection_state") or "disconnected"),
        "turn_busy": bool(session.get("turn_busy")),
        "active_turn": public_active_turn,
        "messages": messages,
    }


@dataclass(frozen=True)
class JanickaR2ChatAdapter:
    """Own one persistent R2 conversation without Human-Adam development controls."""

    service: Any
    backend: JanickaR2Backend

    @classmethod
    def bind(
        cls,
        *,
        base_service: HumanAdamService,
        state_path: Path | None = None,
    ) -> "JanickaR2ChatAdapter":
        if not isinstance(base_service, HumanAdamService):
            raise TypeError("R2 chat nema platny zaklad sdileneho app-serveru.")
        private_root = base_service.workspace.canonical_private_root.resolve()
        document_root = (private_root / R2_DOCUMENTS_RELATIVE_ROOT).resolve()
        backend = JanickaR2Backend.bind(
            canonical_private_root=private_root,
            document_root=document_root,
        )
        chat_service = HumanAdamService(
            runtime=base_service.runtime,
            workspace=base_service.workspace,
            state_path=Path(
                state_path or private_root / R2_CHAT_SESSION_RELATIVE_PATH
            ),
            work_profile_id=R2_CHAT_PROFILE_ID,
            codex_binary=base_service.codex_binary,
            profile_getter=base_service.profile_getter,
            developer_instructions=(
                R2_CHAT_DEVELOPER_INSTRUCTIONS
                + backend.developer_instructions()
            ),
            sandbox_policy={
                **HUMAN_ADAM_SANDBOX_POLICY,
                "networkAccess": False,
                "writableRoots": [str(document_root)],
            },
            private_capability_backend=backend,
        )
        return cls(service=chat_service, backend=backend)

    def _control_block(self) -> str:
        lines = [
            "[DEVELOPMENT_CONTROL]",
            "source=janicka_r2_chat_policy",
            f"profile_id={R2_CHAT_PROFILE_ID}",
            "workspace_writable=false",
            "canonical_private_access=read_only",
            f"canonical_private_root={self.backend.canonical_private_root}",
            "canonical_private_confirmation_required=none",
            "rule=R2-Adam is not a development agent. Never change project files, "
            "tests, Git, memory, handoff, TVBCP or workstreams.",
            *self.backend.development_control_lines(),
            "[/DEVELOPMENT_CONTROL]",
        ]
        return "\n".join(lines)

    @staticmethod
    def _public_payload(value: object) -> dict[str, Any]:
        payload = value if isinstance(value, dict) else {}
        runtime = payload.get("runtime")
        return {
            "ok": payload.get("ok") is True,
            "status": str(payload.get("status") or ""),
            "message": str(payload.get("message") or ""),
            "runtime": {
                "reachable": bool(
                    isinstance(runtime, dict) and runtime.get("reachable")
                )
            },
            "session": _public_session(payload.get("session")),
        }

    def status(self) -> dict[str, Any]:
        return self._public_payload(self.service.status())

    def connect(self) -> dict[str, Any]:
        return self._public_payload(self.service.connect())

    def send(self, payload: object) -> dict[str, Any]:
        body = payload if isinstance(payload, dict) else {}
        text = str(body.get("message") or "").strip()
        if not text:
            raise SessionHubError("Napiš nejdřív zprávu pro R2-Adama.")
        if len(text) > MAX_MESSAGE_CHARS:
            raise SessionHubError(
                f"Zpráva může mít nejvýše {MAX_MESSAGE_CHARS} znaků."
            )
        result = self.service.send(
            text=text,
            client_message_id=str(body.get("client_message_id") or ""),
            client_sent_at=str(body.get("client_sent_at") or ""),
            development_control_block=self._control_block(),
            write_intent=False,
        )
        return {
            "ok": result.get("ok") is True,
            "duplicate_prevented": result.get("duplicate_prevented") is True,
            "session": _public_session(
                result.get("session") or self.service.hub.snapshot()
            ),
        }


def janicka_r2_chat_status_action(
    *,
    adapter: JanickaR2ChatAdapter,
) -> dict[str, Any]:
    try:
        return adapter.status()
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {
            "ok": False,
            "status": "r2_chat_status_failed",
            "message": str(exc),
            "runtime": {"reachable": False},
            "session": _public_session({}),
        }


def janicka_r2_chat_connect_action(
    *,
    adapter: JanickaR2ChatAdapter,
) -> dict[str, Any]:
    try:
        return adapter.connect()
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {
            "ok": False,
            "status": "r2_chat_connect_failed",
            "message": str(exc),
            "runtime": {"reachable": False},
            "session": _public_session({}),
        }


def janicka_r2_chat_send_action(
    payload: object,
    *,
    adapter: JanickaR2ChatAdapter,
) -> dict[str, Any]:
    try:
        return adapter.send(payload)
    except SessionBusyError as exc:
        return {"ok": False, "status": "r2_chat_busy", "message": str(exc)}
    except SessionDeliveryUnknownError as exc:
        return {"ok": False, "status": "delivery_unknown", "message": str(exc)}
    except (AppServerError, SessionHubError, OSError, ValueError) as exc:
        return {"ok": False, "status": "r2_chat_send_failed", "message": str(exc)}


R2_ADAM_CHAT_HTML = r"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>R2-Adam</title>
  <style>
    :root { color-scheme:light; --ink:#172033; --muted:#64748b; --line:#dbe3ee; --blue:#2563eb; --soft:#f3f6fb; --ok:#16803c; --warn:#b45309; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; background:#eef2f7; color:var(--ink); font:16px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    main { width:min(920px,100%); min-height:100vh; margin:0 auto; background:#fff; display:flex; flex-direction:column; }
    header { position:sticky; top:0; z-index:2; padding:14px max(16px,env(safe-area-inset-left)); border-bottom:1px solid var(--line); background:rgba(255,255,255,.96); }
    .head { display:grid; grid-template-columns:minmax(80px,1fr) auto minmax(80px,1fr); align-items:center; gap:10px; }
    h1 { grid-column:2; margin:0; font-size:21px; text-align:center; }
    .back { justify-self:start; border:1px solid var(--line); border-radius:11px; padding:9px 12px; background:#fff; color:var(--ink); font-weight:700; text-decoration:none; }
    .badge { justify-self:end; padding:5px 9px; border-radius:999px; background:var(--soft); color:var(--muted); font-size:13px; white-space:nowrap; }
    .badge.ok { color:var(--ok); background:#ecfdf3; }
    .badge.warn { color:var(--warn); background:#fff7ed; }
    #activity { margin:8px 0 0; color:var(--warn); font-size:13px; font-weight:700; text-align:center; }
    #activity[hidden] { display:none; }
    #notice { min-height:34px; padding:8px 18px 0; color:var(--muted); font-size:14px; }
    #chat { flex:1; padding:14px 18px 150px; display:flex; flex-direction:column; gap:14px; }
    .exchange { display:grid; gap:8px; }
    .bubble { max-width:86%; padding:12px 14px; border-radius:16px; white-space:pre-wrap; overflow-wrap:anywhere; }
    .human { justify-self:end; background:#dbeafe; border-bottom-right-radius:5px; }
    .adam { justify-self:start; background:var(--soft); border-bottom-left-radius:5px; }
    .meta { display:block; margin-top:6px; color:var(--muted); font-size:12px; }
    .empty { color:var(--muted); text-align:center; margin:30px 0; }
    .composer { position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:min(920px,100%); padding:12px max(16px,env(safe-area-inset-right)) calc(12px + env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left)); border-top:1px solid var(--line); background:rgba(255,255,255,.98); }
    textarea { width:100%; min-height:76px; max-height:230px; resize:vertical; border:1px solid #bac7d8; border-radius:13px; padding:12px; font:inherit; color:var(--ink); }
    .compose-actions { display:flex; justify-content:flex-end; margin-top:8px; }
    button { border:1px solid var(--blue); border-radius:11px; padding:10px 15px; background:var(--blue); color:#fff; font:inherit; font-weight:700; cursor:pointer; }
    button:disabled { opacity:.55; cursor:wait; }
    @media (max-width:620px) {
      .head { grid-template-columns:minmax(72px,1fr) auto minmax(72px,1fr); }
      .back { padding:8px 10px; }
      .badge { max-width:105px; overflow:hidden; text-overflow:ellipsis; }
      .bubble { max-width:94%; }
      #chat { padding-left:12px; padding-right:12px; }
    }
  </style>
</head>
<body>
<main>
  <header>
    <div class="head">
      <a class="back" href="/">← Cockpit</a>
      <h1>R2-Adam</h1>
      <span class="badge warn" id="connectionBadge">Připojuji…</span>
    </div>
    <div id="activity" role="status" aria-live="polite" hidden>R2-Adam pracuje…</div>
  </header>
  <div id="notice" role="status" aria-live="polite"></div>
  <section id="chat" aria-label="Konverzace R2-Adam"></section>
  <form class="composer" id="composer" autocomplete="off">
    <textarea id="messageInput" maxlength="12000" autocomplete="off" placeholder="Napiš R2-Adamovi…" aria-label="Zpráva pro R2-Adama"></textarea>
    <div class="compose-actions">
      <button id="sendBtn" type="submit" disabled>Odeslat</button>
    </div>
  </form>
</main>
<script>
  const STATUS_PATH = "/api/r2-adam/status";
  const CONNECT_PATH = "/api/r2-adam/connect";
  const SEND_PATH = "/api/r2-adam/send";
  const connectionBadge = document.getElementById("connectionBadge");
  const activity = document.getElementById("activity");
  const notice = document.getElementById("notice");
  const chat = document.getElementById("chat");
  const composer = document.getElementById("composer");
  const input = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  let connected = false;
  let turnBusy = false;
  let sendInFlight = false;
  let lastMessagesFingerprint = "";

  async function api(path, options={}) {
    const response = await fetch(path, {
      headers: {"Content-Type":"application/json"},
      ...options
    });
    return await response.json();
  }

  function newMessageId() {
    if (window.crypto && crypto.randomUUID) return `r2-adam-${crypto.randomUUID()}`;
    return `r2-adam-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function formatTime(value) {
    const date = new Date(value || "");
    return Number.isNaN(date.getTime())
      ? ""
      : date.toLocaleTimeString("cs-CZ", {hour:"2-digit", minute:"2-digit"});
  }

  function bubble(text, className, meta) {
    const node = document.createElement("article");
    node.className = `bubble ${className}`;
    node.textContent = text || "";
    const small = document.createElement("span");
    small.className = "meta";
    small.textContent = meta || "";
    node.appendChild(small);
    return node;
  }

  function renderMessages(messages) {
    const rows = Array.isArray(messages) ? messages : [];
    const fingerprint = JSON.stringify(rows);
    if (fingerprint === lastMessagesFingerprint) return;
    lastMessagesFingerprint = fingerprint;
    chat.replaceChildren();
    for (const item of rows) {
      const exchange = document.createElement("div");
      exchange.className = "exchange";
      exchange.appendChild(
        bubble(item.user_text, "human", `Odesláno ${formatTime(item.client_sent_at || item.received_at)}`)
      );
      if (item.answer) {
        exchange.appendChild(
          bubble(item.answer, "adam", `R2-Adam · ${formatTime(item.completed_at)}`)
        );
      } else {
        const pending = item.status === "pending"
          ? "R2-Adam pracuje…"
          : "Výsledek doručení je nejistý. Zprávu neposílej automaticky znovu.";
        exchange.appendChild(bubble(pending, "adam", formatTime(item.received_at)));
      }
      chat.appendChild(exchange);
    }
    if (!rows.length) {
      const empty = document.createElement("p");
      empty.className = "empty";
      empty.textContent = "Zatím tu není žádná zpráva. Napiš R2-Adamovi, co potřebuješ.";
      chat.appendChild(empty);
    }
    window.scrollTo({top:document.body.scrollHeight, behavior:"smooth"});
  }

  function render(payload) {
    const session = payload && payload.session ? payload.session : {};
    const runtime = payload && payload.runtime ? payload.runtime : {};
    connected = Boolean(payload && payload.ok && runtime.reachable && session.connected);
    turnBusy = Boolean(session.turn_busy || session.active_turn);
    connectionBadge.textContent = connected ? "Připojeno" : "Odpojeno";
    connectionBadge.className = `badge ${connected ? "ok" : "warn"}`;
    activity.hidden = !turnBusy;
    sendBtn.disabled = !connected || turnBusy || sendInFlight;
    renderMessages(session.messages);
  }

  async function refreshStatus({quiet=false}={}) {
    try {
      const payload = await api(STATUS_PATH);
      render(payload);
      if (!payload.ok && !quiet) notice.textContent = payload.message || "R2-Adam zatím není připravený.";
      return payload;
    } catch (_error) {
      connected = false;
      connectionBadge.textContent = "Nedostupné";
      connectionBadge.className = "badge warn";
      sendBtn.disabled = true;
      if (!quiet) notice.textContent = "Stav R2-Adama se nepodařilo načíst.";
      return null;
    }
  }

  async function ensureConnected() {
    const status = await refreshStatus({quiet:true});
    if (status && status.ok && status.session && status.session.connected) return true;
    connectionBadge.textContent = "Připojuji…";
    try {
      const payload = await api(CONNECT_PATH, {method:"POST", body:"{}"});
      render(payload);
      notice.textContent = payload.ok ? "" : (payload.message || "R2-Adama se nepodařilo připojit.");
      return Boolean(payload.ok && payload.session && payload.session.connected);
    } catch (_error) {
      connected = false;
      connectionBadge.textContent = "Nedostupné";
      connectionBadge.className = "badge warn";
      notice.textContent = "R2-Adama se nepodařilo připojit.";
      sendBtn.disabled = true;
      return false;
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || sendInFlight || turnBusy) return;
    if (!connected && !(await ensureConnected())) return;
    const clientMessageId = newMessageId();
    sendInFlight = true;
    sendBtn.disabled = true;
    notice.textContent = "Zpráva byla předána R2-Adamovi.";
    input.value = "";
    try {
      const payload = await api(SEND_PATH, {
        method:"POST",
        body:JSON.stringify({
          message,
          client_message_id:clientMessageId,
          client_sent_at:new Date().toISOString()
        })
      });
      if (!payload.ok) {
        notice.textContent = payload.status === "delivery_unknown"
          ? "Výsledek doručení je nejistý. Stejnou zprávu neposílej automaticky znovu."
          : (payload.message || "R2-Adam zprávu nedokončil.");
      } else {
        notice.textContent = "";
      }
    } catch (_error) {
      notice.textContent = "Spojení se přerušilo. Než zprávu zopakuješ, počkej na obnovení stavu.";
    } finally {
      sendInFlight = false;
      await refreshStatus({quiet:true});
      input.focus();
    }
  }

  composer.addEventListener("submit", sendMessage);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      composer.requestSubmit();
    }
  });
  ensureConnected();
  window.setInterval(() => refreshStatus({quiet:true}), 4000);
</script>
</body>
</html>
"""
