"""Standalone responsive Human–Adam text interface."""

from __future__ import annotations


HUMAN_ADAM_HTML = r"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Human–Adam</title>
  <style>
    :root { color-scheme: light; --ink:#172033; --muted:#64748b; --line:#dbe3ee; --blue:#2563eb; --soft:#f3f6fb; --ok:#16803c; --warn:#b45309; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; background:#eef2f7; color:var(--ink); font:16px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    main { width:min(920px,100%); min-height:100vh; margin:0 auto; background:#fff; display:flex; flex-direction:column; }
    header { position:sticky; top:0; z-index:2; padding:14px max(16px,env(safe-area-inset-left)); border-bottom:1px solid var(--line); background:rgba(255,255,255,.96); }
    .head { display:flex; align-items:center; gap:10px; }
    h1 { margin:0; font-size:21px; flex:1; }
    button,.back { border:1px solid var(--line); border-radius:11px; padding:10px 13px; background:#fff; color:var(--ink); font:inherit; font-weight:700; text-decoration:none; cursor:pointer; }
    button.primary { background:var(--blue); color:#fff; border-color:var(--blue); }
    button:disabled { opacity:.55; cursor:wait; }
    .statusline { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; color:var(--muted); font-size:13px; }
    .badge { padding:4px 8px; border-radius:999px; background:var(--soft); }
    .badge.ok { color:var(--ok); background:#ecfdf3; }
    .badge.warn { color:var(--warn); background:#fff7ed; }
    #notice { min-height:24px; padding:8px 18px 0; color:var(--muted); font-size:14px; }
    #chat { flex:1; padding:14px 18px 180px; display:flex; flex-direction:column; gap:14px; }
    .exchange { display:grid; gap:8px; }
    .bubble { max-width:86%; padding:12px 14px; border-radius:16px; white-space:pre-wrap; overflow-wrap:anywhere; }
    .human { justify-self:end; background:#dbeafe; border-bottom-right-radius:5px; }
    .adam { justify-self:start; background:var(--soft); border-bottom-left-radius:5px; }
    .meta { display:block; margin-top:6px; color:var(--muted); font-size:12px; }
    .composer { position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:min(920px,100%); padding:12px max(16px,env(safe-area-inset-right)) calc(12px + env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left)); border-top:1px solid var(--line); background:rgba(255,255,255,.98); }
    textarea { width:100%; min-height:86px; max-height:230px; resize:vertical; border:1px solid #bac7d8; border-radius:13px; padding:12px; font:inherit; color:var(--ink); }
    .compose-actions { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:8px; }
    .hint { color:var(--muted); font-size:12px; }
    .tvbcp-panel { position:fixed; z-index:5; inset:0 0 0 auto; width:min(680px,100%); display:flex; flex-direction:column; background:#fff; border-left:1px solid var(--line); box-shadow:-12px 0 40px rgba(15,23,42,.18); }
    .tvbcp-panel[hidden] { display:none; }
    .tvbcp-head { display:flex; align-items:center; gap:8px; padding:14px max(16px,env(safe-area-inset-right)) 14px 16px; border-bottom:1px solid var(--line); }
    .tvbcp-head h2 { flex:1; margin:0; font-size:18px; }
    #tvbcpMeta { padding:10px 16px; color:var(--muted); font-size:13px; border-bottom:1px solid var(--line); }
    #tvbcpContent { flex:1; overflow:auto; margin:0; padding:16px max(16px,env(safe-area-inset-right)) calc(16px + env(safe-area-inset-bottom)) 16px; white-space:pre-wrap; overflow-wrap:anywhere; font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }
    #workMeta { padding:10px 16px; color:var(--muted); font-size:13px; border-bottom:1px solid var(--line); }
    #workChanges { flex:1; overflow:auto; margin:0; padding:16px 34px; }
    #workChanges li { margin-bottom:8px; overflow-wrap:anywhere; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:14px; }
    .checkpoint-box { padding:12px 16px calc(12px + env(safe-area-inset-bottom)); border-top:1px solid var(--line); display:grid; gap:8px; }
    .checkpoint-box input { width:100%; border:1px solid #bac7d8; border-radius:11px; padding:10px 12px; font:inherit; }
    @media (max-width:620px) { .back { padding:8px 10px; } .bubble { max-width:94%; } .hint { display:none; } #chat { padding-left:12px; padding-right:12px; } }
  </style>
</head>
<body>
<main>
  <header>
    <div class="head">
      <a class="back" href="/">← Cockpit</a>
      <h1>Human–Adam</h1>
      <button id="tvbcpOpenBtn" type="button">TVBCP</button>
      <button id="workOpenBtn" type="button">Práce</button>
      <button id="refreshBtn" type="button">Stav</button>
      <button class="primary" id="connectBtn" type="button">Připojit</button>
    </div>
    <div class="statusline">
      <span class="badge warn" id="connectionBadge">Odpojeno</span>
      <span class="badge" id="threadBadge">Relace: —</span>
      <span class="badge" id="workspaceBadge">Izolovaný workspace</span>
    </div>
  </header>
  <div id="notice" role="status" aria-live="polite"></div>
  <section id="chat" aria-label="Konverzace Human–Adam"></section>
  <form class="composer" id="composer">
    <textarea id="messageInput" maxlength="12000" placeholder="Napiš Adamovi…" aria-label="Zpráva pro Adama"></textarea>
    <div class="compose-actions">
      <span class="hint">⌘/Ctrl + Enter odešle · Enter píše nový řádek</span>
      <button class="primary" id="sendBtn" type="submit">Odeslat</button>
    </div>
  </form>
  <aside class="tvbcp-panel" id="tvbcpPanel" hidden aria-label="Projektový TVBCP">
    <div class="tvbcp-head">
      <h2 id="tvbcpTitle">Projektový TVBCP</h2>
      <button id="tvbcpRefreshBtn" type="button">Obnovit</button>
      <button id="tvbcpCloseBtn" type="button">Zavřít</button>
    </div>
    <div id="tvbcpMeta">TVBCP se načte až po otevření.</div>
    <pre id="tvbcpContent"></pre>
  </aside>
  <aside class="tvbcp-panel" id="workPanel" hidden aria-label="Pracovní změny">
    <div class="tvbcp-head">
      <h2>Pracovní změny</h2>
      <button id="workRefreshBtn" type="button">Obnovit</button>
      <button id="workCloseBtn" type="button">Zavřít</button>
    </div>
    <div id="workMeta">Stav se načte až po otevření.</div>
    <ul id="workChanges"></ul>
    <div class="checkpoint-box">
      <input id="checkpointMessage" maxlength="120" placeholder="Krátký popis WIP checkpointu">
      <button class="primary" id="checkpointBtn" type="button" disabled>Checkpoint bez pushnutí</button>
    </div>
  </aside>
</main>
<script>
  const chat = document.getElementById("chat");
  const notice = document.getElementById("notice");
  const connectionBadge = document.getElementById("connectionBadge");
  const threadBadge = document.getElementById("threadBadge");
  const workspaceBadge = document.getElementById("workspaceBadge");
  const connectBtn = document.getElementById("connectBtn");
  const refreshBtn = document.getElementById("refreshBtn");
  const composer = document.getElementById("composer");
  const input = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const tvbcpOpenBtn = document.getElementById("tvbcpOpenBtn");
  const tvbcpPanel = document.getElementById("tvbcpPanel");
  const tvbcpCloseBtn = document.getElementById("tvbcpCloseBtn");
  const tvbcpRefreshBtn = document.getElementById("tvbcpRefreshBtn");
  const tvbcpTitle = document.getElementById("tvbcpTitle");
  const tvbcpMeta = document.getElementById("tvbcpMeta");
  const tvbcpContent = document.getElementById("tvbcpContent");
  const workOpenBtn = document.getElementById("workOpenBtn");
  const workPanel = document.getElementById("workPanel");
  const workCloseBtn = document.getElementById("workCloseBtn");
  const workRefreshBtn = document.getElementById("workRefreshBtn");
  const workMeta = document.getElementById("workMeta");
  const workChanges = document.getElementById("workChanges");
  const checkpointMessage = document.getElementById("checkpointMessage");
  const checkpointBtn = document.getElementById("checkpointBtn");
  let busy = false;
  let lastSession = null;

  function messageId() {
    if (window.crypto && crypto.randomUUID) return `human-adam-${crypto.randomUUID()}`;
    return `human-adam-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function formatTime(value) {
    if (!value) return "čas neuveden";
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("cs-CZ", {hour:"2-digit",minute:"2-digit",second:"2-digit",day:"2-digit",month:"2-digit"});
  }

  function setBusy(value, text="") {
    busy = value;
    connectBtn.disabled = value;
    refreshBtn.disabled = value;
    sendBtn.disabled = value;
    if (text) notice.textContent = text;
  }

  function bubble(text, className, meta) {
    const node = document.createElement("article");
    node.className = `bubble ${className}`;
    node.textContent = text;
    const small = document.createElement("span");
    small.className = "meta";
    small.textContent = meta;
    node.appendChild(small);
    return node;
  }

  function renderSession(session) {
    lastSession = session || null;
    chat.replaceChildren();
    const messages = session && Array.isArray(session.messages) ? session.messages : [];
    for (const item of messages) {
      const exchange = document.createElement("div");
      exchange.className = "exchange";
      exchange.appendChild(bubble(item.user_text || "", "human", `Odesláno ${formatTime(item.client_sent_at || item.received_at)}`));
      const confirmed = item.delivery_confirmed ? "Doručení potvrzeno" : (item.status === "delivery_unknown" ? "Doručení nejisté – neposílat automaticky znovu" : "Zpracování nedokončeno");
      if (item.answer) exchange.appendChild(bubble(item.answer, "adam", `Adam · ${formatTime(item.completed_at)} · ${confirmed}`));
      else exchange.appendChild(bubble(item.status === "pending" ? "Adam pracuje…" : confirmed, "adam", formatTime(item.received_at)));
      chat.appendChild(exchange);
    }
    if (!messages.length) {
      const empty = document.createElement("p");
      empty.textContent = "Zatím tu není žádná výměna. Připoj relaci a pošli první zprávu.";
      empty.style.color = "var(--muted)";
      chat.appendChild(empty);
    }
    window.scrollTo({top:document.body.scrollHeight,behavior:"smooth"});
  }

  function renderStatus(payload) {
    const session = payload && payload.session ? payload.session : null;
    const connected = Boolean(session && session.connected && payload.runtime && payload.runtime.reachable);
    connectionBadge.textContent = connected ? "Připojeno" : "Odpojeno";
    connectionBadge.className = connected ? "badge ok" : "badge warn";
    const thread = session && session.thread_id ? session.thread_id : "";
    threadBadge.textContent = `Relace: ${thread ? thread.slice(0,8) : "—"}`;
    const workspace = payload && payload.workspace ? payload.workspace : {};
    workspaceBadge.textContent = workspace.has_git_remote ? "POZOR: Git remote" : (workspace.sync_available ? "Workspace čeká na sync" : (workspace.dirty ? `Workspace: ${workspace.change_count} změn` : (workspace.local_checkpoint_ahead ? `WIP checkpoint: ${workspace.local_commit_count}` : "Workspace čistý")));
    workspaceBadge.className = workspace.has_git_remote || workspace.sync_available || workspace.dirty || workspace.local_checkpoint_ahead ? "badge warn" : "badge";
    renderSession(session);
  }

  async function api(path, options={}) {
    const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || "HTTP požadavek selhal.");
    return payload;
  }

  async function loadStatus() {
    if (busy) return;
    setBusy(true, "Načítám stav…");
    try {
      const payload = await api("/api/human-adam/status");
      renderStatus(payload);
      notice.textContent = payload.ok ? "" : (payload.message || "Human–Adam zatím není připravený.");
    } catch (error) { notice.textContent = `Stav nelze načíst: ${error.message}`; }
    finally { setBusy(false); }
  }

  async function connect() {
    if (busy) return;
    setBusy(true, "Připojuji kanonickou relaci…");
    try {
      const payload = await api("/api/human-adam/connect", {method:"POST", body:"{}"});
      if (!payload.ok) throw new Error(payload.message || "Připojení selhalo.");
      renderStatus(payload);
      notice.textContent = "Kanonická relace je připravená.";
      input.focus();
    } catch (error) { notice.textContent = `Připojení selhalo: ${error.message}`; }
    finally { setBusy(false); }
  }

  async function loadTvbcp() {
    tvbcpRefreshBtn.disabled = true;
    tvbcpMeta.textContent = "Načítám pracovní TVBCP…";
    try {
      const payload = await api("/api/human-adam/tvbcp");
      if (!payload.ok) throw new Error(payload.message || "TVBCP nelze načíst.");
      tvbcpTitle.textContent = payload.title || "Projektový TVBCP";
      tvbcpContent.textContent = payload.content || "";
      const workState = payload.workspace_dirty ? `pracovní kopie má ${payload.workspace_change_count} změn` : "pracovní kopie je čistá";
      const syncState = payload.sync_available ? " · čeká na aktualizaci z main" : "";
      tvbcpMeta.textContent = `Pracovní TVBCP · ${workState}${syncState} · změněno ${formatTime(payload.modified_at)}`;
      tvbcpContent.scrollTop = 0;
    } catch (error) {
      tvbcpContent.textContent = "";
      tvbcpMeta.textContent = `TVBCP nelze načíst: ${error.message}`;
    } finally { tvbcpRefreshBtn.disabled = false; }
  }

  function openTvbcp() {
    workPanel.hidden = true;
    tvbcpPanel.hidden = false;
    loadTvbcp();
  }

  function closeTvbcp() {
    tvbcpPanel.hidden = true;
  }

  function renderWork(payload) {
    workChanges.replaceChildren();
    const pending = Array.isArray(payload.changes) ? payload.changes : [];
    const checkpointed = Array.isArray(payload.checkpoint_changes) ? payload.checkpoint_changes : [];
    const rows = pending.length ? pending : checkpointed;
    for (const item of rows) {
      const row = document.createElement("li");
      row.textContent = `${item.status || "?"} · ${item.path || ""}`;
      workChanges.appendChild(row);
    }
    if (!rows.length) {
      const row = document.createElement("li");
      row.textContent = "Žádné pracovní změny.";
      workChanges.appendChild(row);
    }
    if (payload.dirty) workMeta.textContent = `Necheckpointované změny: ${payload.change_count}`;
    else if (payload.local_checkpoint_ahead) workMeta.textContent = `Lokální WIP checkpoint: ${payload.local_commit_count} commitů · ${payload.checkpoint_change_count} souborů · bez pushnutí`;
    else workMeta.textContent = "Workspace je čistý a odpovídá main.";
    checkpointBtn.disabled = !payload.dirty;
  }

  async function loadWork() {
    workRefreshBtn.disabled = true;
    workMeta.textContent = "Načítám pracovní stav…";
    try {
      const payload = await api("/api/human-adam/workspace");
      if (!payload.ok) throw new Error(payload.message || "Pracovní stav nelze načíst.");
      renderWork(payload);
    } catch (error) {
      workChanges.replaceChildren();
      workMeta.textContent = `Pracovní stav nelze načíst: ${error.message}`;
      checkpointBtn.disabled = true;
    } finally { workRefreshBtn.disabled = false; }
  }

  function openWork() {
    tvbcpPanel.hidden = true;
    workPanel.hidden = false;
    loadWork();
  }

  function closeWork() {
    workPanel.hidden = true;
  }

  async function createCheckpoint() {
    if (checkpointBtn.disabled) return;
    if (!window.confirm("Vytvořit lokální WIP checkpoint v izolované kopii bez pushnutí?")) return;
    checkpointBtn.disabled = true;
    workMeta.textContent = "Vytvářím bezpečný lokální checkpoint…";
    let failure = "";
    try {
      const payload = await api("/api/human-adam/checkpoint", {method:"POST", body:JSON.stringify({confirmed:true,message:checkpointMessage.value.trim()})});
      if (!payload.ok) throw new Error(payload.message || "Checkpoint selhal.");
      checkpointMessage.value = "";
      renderWork(payload.work);
      renderStatus(payload.status);
    } catch (error) {
      failure = `Checkpoint selhal: ${error.message}`;
      await loadWork();
    }
    if (failure) workMeta.textContent = failure;
  }

  async function sendMessage(event) {
    event.preventDefault();
    if (busy) return;
    const text = input.value.trim();
    if (!text) { notice.textContent = "Napiš nejdřív zprávu."; return; }
    const sentAt = new Date().toISOString();
    const clientId = messageId();
    const optimistic = lastSession ? {...lastSession, messages:[...(lastSession.messages || []), {user_text:text,client_sent_at:sentAt,received_at:sentAt,status:"pending",answer:""}]} : {messages:[{user_text:text,client_sent_at:sentAt,received_at:sentAt,status:"pending",answer:""}]};
    renderSession(optimistic);
    setBusy(true, `Odesláno ${formatTime(sentAt)} · Adam pracuje…`);
    let failure = "";
    try {
      const payload = await api("/api/human-adam/send", {method:"POST", body:JSON.stringify({message:text,client_message_id:clientId,client_sent_at:sentAt})});
      if (!payload.ok) throw new Error(payload.message || "Odeslání selhalo.");
      input.value = "";
      renderSession(payload.session);
      notice.textContent = "Odpověď doručena a potvrzena.";
    } catch (error) {
      failure = `Odeslání není potvrzené: ${error.message}`;
    } finally { setBusy(false); }
    await loadStatus();
    if (failure) notice.textContent = failure;
  }

  connectBtn.addEventListener("click", connect);
  refreshBtn.addEventListener("click", loadStatus);
  tvbcpOpenBtn.addEventListener("click", openTvbcp);
  tvbcpCloseBtn.addEventListener("click", closeTvbcp);
  tvbcpRefreshBtn.addEventListener("click", loadTvbcp);
  workOpenBtn.addEventListener("click", openWork);
  workCloseBtn.addEventListener("click", closeWork);
  workRefreshBtn.addEventListener("click", loadWork);
  checkpointBtn.addEventListener("click", createCheckpoint);
  composer.addEventListener("submit", sendMessage);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) sendMessage(event);
  });
  loadStatus();
</script>
</body>
</html>
"""
