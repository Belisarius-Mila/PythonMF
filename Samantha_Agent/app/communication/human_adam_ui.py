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
    .head-tools { display:flex; align-items:center; gap:10px; }
    .profile-tools { display:flex; align-items:center; gap:8px; margin-top:10px; }
    .profile-tools label { color:var(--muted); font-size:13px; font-weight:700; }
    .profile-tools select { min-width:170px; border:1px solid #bac7d8; border-radius:10px; padding:8px 10px; background:#fff; color:var(--ink); font:inherit; }
    h1 { margin:0; font-size:21px; flex:1; }
    button,.back { border:1px solid var(--line); border-radius:11px; padding:10px 13px; background:#fff; color:var(--ink); font:inherit; font-weight:700; text-decoration:none; cursor:pointer; }
    button.primary { background:var(--blue); color:#fff; border-color:var(--blue); }
    button.audit-action { background:#fbbf24; color:#422006; border-color:#d97706; }
    button.audit-action.deployment-current:disabled { opacity:1; cursor:default; color:var(--ok); border-color:#86efac; background:#ecfdf3; }
    button.deploy-action { background:var(--ok); color:#fff; border-color:var(--ok); }
    button:disabled { opacity:.55; cursor:wait; }
    #workOpenBtn.work-clean { color:var(--ok); border-color:#86efac; background:#ecfdf3; }
    #workOpenBtn.work-attention { color:var(--warn); border-color:#fdba74; background:#fff7ed; }
    .statusline { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; color:var(--muted); font-size:13px; }
    #mobileStatusSummary { display:none; width:100%; margin-top:10px; padding:8px 10px; align-items:center; justify-content:space-between; gap:10px; text-align:left; color:var(--muted); background:var(--soft); }
    #mobileStatusSummary.warn { color:var(--warn); background:#fff7ed; }
    #mobileStatusSummary.ok { color:var(--ok); background:#ecfdf3; }
    #mobileStatusText { min-width:0; overflow-wrap:anywhere; }
    #mobileStatusToggleText { flex:0 0 auto; font-size:12px; font-weight:600; }
    .badge { padding:4px 8px; border-radius:999px; background:var(--soft); }
    button.sound-badge { padding:4px 8px; color:var(--muted); font-size:13px; font-weight:600; }
    .badge.ok { color:var(--ok); background:#ecfdf3; }
    .badge.warn { color:var(--warn); background:#fff7ed; }
    #turnActivity { margin:8px 0 0; padding:6px 10px; border-radius:10px; color:var(--warn); background:#fff7ed; font-size:13px; font-weight:700; }
    #turnActivity[hidden] { display:none; }
    #notice { min-height:24px; padding:8px 18px 0; color:var(--muted); font-size:14px; }
    #deploymentReceipt { margin:8px 0 0; padding:6px 10px; border-radius:10px; color:var(--ok); background:#ecfdf3; font-size:13px; }
    #deploymentReceipt.stale { color:var(--warn); background:#fff7ed; }
    #deploymentReceipt[hidden] { display:none; }
    #stepCompletionReceipt { margin:8px 0 0; padding:6px 10px; border-radius:10px; color:var(--ok); background:#ecfdf3; font-size:13px; font-weight:700; }
    #stepCompletionReceipt.running { color:#1d4ed8; background:#eff6ff; }
    #stepCompletionReceipt.warn { color:var(--warn); background:#fff7ed; }
    #stepCompletionReceipt[hidden] { display:none; }
    #chat { flex:1; padding:14px 18px 180px; display:flex; flex-direction:column; gap:14px; }
    .exchange { display:grid; gap:8px; }
    .bubble { max-width:86%; padding:12px 14px; border-radius:16px; white-space:pre-wrap; overflow-wrap:anywhere; }
    .human { justify-self:end; background:#dbeafe; border-bottom-right-radius:5px; }
    .adam { justify-self:start; background:var(--soft); border-bottom-left-radius:5px; }
    .meta { display:block; margin-top:6px; color:var(--muted); font-size:12px; }
    .reply-actions { display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
    .reply-speech,.reply-copy { padding:6px 9px; font-size:12px; white-space:nowrap; }
    .image-candidate-card { width:min(520px,100%); margin-top:10px; padding:12px; border:1px solid #bfdbfe; border-radius:13px; display:grid; gap:9px; background:#fff; white-space:normal; }
    .image-candidate-card[data-status="approved"] { border-color:#86efac; background:#f0fdf4; }
    .image-candidate-card[data-status="rejected"] { border-color:#fca5a5; background:#fef2f2; }
    .image-candidate-card h3 { margin:0; font-size:15px; }
    .image-candidate-preview { width:100%; max-height:280px; object-fit:contain; border:1px solid var(--line); border-radius:10px; background:var(--soft); }
    .image-candidate-placeholder { padding:18px 12px; border:1px dashed #93c5fd; border-radius:10px; color:var(--muted); background:#eff6ff; text-align:center; }
    .image-candidate-prompt { margin:0; padding:9px; border-radius:9px; color:var(--ink); background:var(--soft); white-space:pre-wrap; overflow-wrap:anywhere; font-size:13px; }
    .image-candidate-meta { margin:0; color:var(--muted); font-size:12px; overflow-wrap:anywhere; }
    .image-candidate-actions { display:flex; flex-wrap:wrap; gap:8px; }
    .image-candidate-actions button,.image-candidate-actions a { padding:7px 10px; font-size:12px; }
    .image-candidate-actions .approve { color:var(--ok); border-color:#86efac; background:#ecfdf3; }
    .image-candidate-actions .reject { color:#991b1b; border-color:#fca5a5; background:#fef2f2; }
    .composer { position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:min(920px,100%); padding:12px max(16px,env(safe-area-inset-right)) calc(12px + env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left)); border-top:1px solid var(--line); background:rgba(255,255,255,.98); }
    textarea { width:100%; min-height:86px; max-height:230px; resize:vertical; border:1px solid #bac7d8; border-radius:13px; padding:12px; font:inherit; color:var(--ink); }
    .voice-controls { display:flex; align-items:center; gap:8px; min-width:0; }
    #voiceRecordBtn.recording { color:#991b1b; border-color:#ef4444; background:#fef2f2; }
    #voiceStatus { min-width:0; overflow:hidden; color:var(--muted); font-size:12px; text-align:center; text-overflow:ellipsis; white-space:nowrap; }
    .compose-actions { display:grid; grid-template-columns:auto minmax(0,1fr) auto; align-items:center; gap:10px; margin-top:8px; }
    .send-controls { display:flex; align-items:center; gap:8px; }
    #writeIntentBtn.armed { color:#fff; border-color:#b45309; background:#b45309; }
    .tvbcp-panel { position:fixed; z-index:5; inset:0 0 0 auto; width:min(680px,100%); display:flex; flex-direction:column; background:#fff; border-left:1px solid var(--line); box-shadow:-12px 0 40px rgba(15,23,42,.18); }
    .tvbcp-panel[hidden] { display:none; }
    .tvbcp-head { display:flex; align-items:center; gap:8px; padding:14px max(16px,env(safe-area-inset-right)) 14px 16px; border-bottom:1px solid var(--line); }
    .tvbcp-head h2 { flex:1; margin:0; font-size:18px; }
    #tvbcpMeta { padding:10px 16px; color:var(--muted); font-size:13px; border-bottom:1px solid var(--line); }
    #tvbcpScroll { flex:1; min-height:0; overflow:auto; }
    #tvbcpContent { margin:0; padding:16px max(16px,env(safe-area-inset-right)) calc(16px + env(safe-area-inset-bottom)) 16px; white-space:pre-wrap; overflow-wrap:anywhere; font:14px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }
    #tvbcpEnd { height:1px; }
    #workMeta { padding:10px 16px; color:var(--muted); font-size:13px; border-bottom:1px solid var(--line); }
    #workChanges { flex:1; overflow:auto; margin:0; padding:16px 34px; }
    #workChanges li { margin-bottom:8px; overflow-wrap:anywhere; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:14px; }
    .development-semaphore-box { padding:12px 16px; border-bottom:1px solid var(--line); display:grid; gap:8px; background:#f8fafc; }
    .development-semaphore-box h3 { margin:0; font-size:15px; }
    .development-semaphore-box p { margin:0; color:var(--muted); font-size:13px; overflow-wrap:anywhere; }
    .development-semaphore-box input { width:100%; border:1px solid #bac7d8; border-radius:11px; padding:10px 12px; font:inherit; }
    .development-binding-fields { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:8px; }
    .development-binding-fields label { display:grid; gap:4px; color:var(--muted); font-size:12px; font-weight:700; }
    .development-binding-fields select { width:100%; min-width:0; border:1px solid #bac7d8; border-radius:11px; padding:9px 10px; background:#fff; color:var(--ink); font:inherit; }
    .development-semaphore-actions { display:flex; gap:8px; flex-wrap:wrap; }
    .project-continuity-box { padding:12px 16px; border-bottom:1px solid var(--line); display:grid; gap:8px; background:#fff; }
    .project-continuity-head { display:flex; align-items:center; gap:8px; }
    .project-continuity-head h3 { flex:1; margin:0; font-size:15px; }
    #projectContinuityMeta { margin:0; color:var(--muted); font-size:13px; overflow-wrap:anywhere; }
    #projectContinuityReasons { margin:0; padding-left:22px; color:var(--muted); font-size:13px; }
    .integration-audit-box { margin:12px 16px; padding:14px; border:1px solid #93c5fd; border-radius:13px; display:grid; gap:8px; background:#eff6ff; }
    .integration-audit-box[hidden] { display:none; }
    .integration-audit-box.ready { border-color:#86efac; background:#f0fdf4; }
    .integration-audit-box.warn { border-color:#fbbf24; background:#fffbeb; }
    .integration-audit-box.blocked { border-color:#fca5a5; background:#fef2f2; }
    .integration-audit-box h3 { margin:0; font-size:15px; }
    .integration-audit-box input { width:100%; border:1px solid #bac7d8; border-radius:11px; padding:10px 12px; font:inherit; }
    .integration-recovery-fields { display:grid; gap:8px; }
    .integration-recovery-fields[hidden] { display:none; }
    .integration-recovery-fields label { display:grid; gap:4px; color:var(--muted); font-size:12px; }
    #integrationAuditMeta { margin:0; color:var(--muted); font-size:13px; line-height:1.45; overflow-wrap:anywhere; }
    #integrationAuditPaths { margin:0; padding-left:22px; font:13px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace; overflow-wrap:anywhere; }
    .handoff-proposal-box { margin:12px 16px; padding:14px; border:1px solid #93c5fd; border-radius:13px; display:grid; gap:8px; background:#eff6ff; }
    .handoff-proposal-box h3 { margin:0; font-size:15px; }
    #handoffProposalMeta { margin:0; color:var(--muted); font-size:13px; overflow-wrap:anywhere; }
    #handoffProposalDraft { margin:0; padding:12px; border:1px solid #bfdbfe; border-radius:10px; background:#fff; white-space:pre-wrap; overflow-wrap:anywhere; font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }
    .checkpoint-box { padding:12px 16px calc(12px + env(safe-area-inset-bottom)); border-top:1px solid var(--line); display:grid; gap:8px; }
    .checkpoint-box input { width:100%; border:1px solid #bac7d8; border-radius:11px; padding:10px 12px; font:inherit; }
    #deployMeta { color:var(--muted); font-size:13px; line-height:1.4; }
    #handoffTakeoverCheck { padding:10px 12px; border:1px solid #f59e0b; border-radius:11px; background:#fffbeb; color:#92400e; font-size:13px; line-height:1.45; overflow-wrap:anywhere; }
    #handoffTakeoverCheck.verified { border-color:#86efac; background:#f0fdf4; color:#166534; }
    .thread-rotation-panel-body { flex:1; min-height:0; overflow:auto; padding:16px; display:flex; flex-direction:column; gap:10px; }
    .thread-rotation-help { margin:0; color:var(--muted); font-size:13px; line-height:1.45; }
    .work-panel-body { flex:1; min-height:0; overflow:auto; display:flex; flex-direction:column; }
    .workflow-help-trigger { width:38px; min-width:38px; padding:8px 0; border-radius:50%; font-weight:700; }
    .workflow-help-panel { padding:14px; border:1px solid #c9d6e5; border-radius:13px; background:#f8fafc; color:var(--ink); }
    .workflow-help-head { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
    .workflow-help-head h3 { flex:1; margin:0; font-size:16px; }
    .workflow-help-panel h4 { margin:14px 0 5px; font-size:14px; }
    .workflow-help-panel p { margin:0; color:var(--muted); font-size:13px; line-height:1.45; }
    .workflow-help-panel ol,.workflow-help-panel ul { margin:4px 0 0; padding-left:23px; }
    .workflow-help-panel li { margin:5px 0; line-height:1.4; }
    .workflow-help-safety { margin-top:14px !important; padding:9px 11px; border-radius:10px; background:#ecfdf3; color:var(--ok) !important; }
    .legacy-work-control { display:none !important; }
    .work-help-panel { flex:0 0 auto; margin:12px 16px; }
    .batch-workflow-box { margin:0 16px 14px; padding:14px; border:1px solid #bfdbfe; border-radius:13px; background:#eff6ff; }
    .batch-workflow-box h3 { margin:0 0 5px; font-size:15px; }
    .batch-workflow-box p { margin:0; color:var(--blue); font-size:14px; font-weight:700; }
    .batch-workflow-box ol { margin:9px 0 0; padding-left:23px; }
    .batch-workflow-box li { margin:5px 0; line-height:1.4; }
    .live-work-status-box { margin:0 0 14px; padding:12px; border:1px solid #dbe3ee; border-radius:12px; background:#f8fafc; }
    .live-work-status-box[data-state="current"],.live-work-status-box[data-state="current_runtime_disconnected"] { border-color:#bbf7d0; background:#f0fdf4; }
    .live-work-status-box[data-state="attention_required"],.live-work-status-box[data-state="unverified"] { border-color:#fed7aa; background:#fff7ed; }
    .live-work-status-box h3 { margin:0 0 5px; font-size:15px; }
    .live-work-status-box p { margin:0; color:var(--muted); font-size:13px; }
    .live-work-status-box input { width:100%; margin-top:8px; border:1px solid #bac7d8; border-radius:11px; padding:10px 12px; font:inherit; }
    .live-work-status-box ul { margin:8px 0 0; padding-left:22px; }
    .live-work-status-box li { margin:4px 0; line-height:1.35; }
    .thread-rotation-box { margin-top:14px; padding-top:12px; border-top:1px solid #dbe3ee; display:grid; gap:8px; }
    .thread-rotation-box h3 { margin:0; font-size:15px; }
    .thread-rotation-actions { display:flex; gap:8px; flex-wrap:wrap; }
    #threadRotationConfirmation { width:100%; min-width:0; }
    @media (max-width:620px) { .head { display:grid; grid-template-columns:auto minmax(0,1fr) auto; } .head h1 { text-align:center; } .head-tools { grid-column:1/-1; grid-row:2; justify-content:center; } .profile-tools { display:grid; grid-template-columns:auto minmax(0,1fr) auto; } .profile-tools select { min-width:0; width:100%; } .back { padding:8px 10px; } #mobileStatusSummary { display:flex; } .status-details { display:none; } .status-details.expanded { display:block; } .bubble { max-width:94%; } #chat { padding-left:12px; padding-right:12px; } }
    @media (max-width:620px) {
      .tvbcp-panel { width:100%; max-width:100vw; min-width:0; overflow-x:hidden; }
      .tvbcp-head,.thread-rotation-panel-body { min-width:0; max-width:100%; }
      .thread-rotation-help { overflow-wrap:anywhere; }
      .thread-rotation-actions > button { flex:1 1 100%; min-width:0; white-space:normal; }
      .development-semaphore-actions > button { flex:1 1 100%; min-width:0; white-space:normal; }
      .development-binding-fields { grid-template-columns:1fr; }
      .workflow-help-panel { padding:12px; }
      .workflow-help-head { align-items:flex-start; }
      .work-help-panel { margin:10px 12px; }
    }
  </style>
</head>
<body>
<main>
  <header>
    <div class="head">
      <button class="primary" id="connectBtn" type="button">Připojit</button>
      <h1>Human–Adam</h1>
      <div class="head-tools">
        <button id="threadRotationOpenBtn" type="button">Vlákno</button>
        <button id="tvbcpOpenBtn" type="button">TVBCP</button>
        <button id="workOpenBtn" type="button">Práce: stav</button>
        <button id="refreshBtn" type="button">Stav</button>
      </div>
      <a class="back" href="/">← Cockpit</a>
    </div>
    <div class="profile-tools">
      <label for="profileSelect">Pracovní proud</label>
      <select id="profileSelect" aria-label="Pracovní proud Human–Adam"></select>
      <button id="profileSwitchBtn" type="button" disabled>Přepnout</button>
    </div>
    <button id="mobileStatusSummary" type="button" aria-expanded="false" aria-controls="statusDetails">
      <span id="mobileStatusText" role="status" aria-live="polite">Odpojeno · Izolovaný workspace · Adam není připojen</span>
      <span id="mobileStatusToggleText">Podrobnosti</span>
    </button>
    <div class="status-details" id="statusDetails">
      <div class="statusline">
        <span class="badge warn" id="connectionBadge">Odpojeno</span>
        <span class="badge" id="profileBadge">Proud: Human–Adam</span>
        <span class="badge" id="threadBadge">Relace: —</span>
        <span class="badge" id="workspaceBadge">Izolovaný workspace</span>
        <span class="badge warn legacy-work-control" id="developmentBadge">Vývoj: neověřen</span>
        <button class="badge sound-badge warn" id="mediaSoundTestBtn" type="button">Zvuk odpovědi: vyzkoušet</button>
        <audio id="completionMediaAudio" preload="auto" playsinline hidden></audio>
      </div>
      <div id="turnActivity" role="status" aria-live="polite" hidden></div>
    </div>
    <div id="stepCompletionReceipt" role="status" aria-live="polite" hidden></div>
    <div id="deploymentReceipt" role="status" aria-live="polite" hidden></div>
  </header>
  <div id="notice" role="status" aria-live="polite"></div>
  <section id="chat" aria-label="Konverzace Human–Adam"></section>
  <form class="composer" id="composer" autocomplete="off">
    <textarea id="messageInput" maxlength="12000" autocomplete="off" placeholder="Napiš Adamovi…" aria-label="Zpráva pro Adama"></textarea>
    <div class="compose-actions">
      <div class="voice-controls">
        <button id="voiceRecordBtn" type="button">Nahrát pokyn</button>
        <button id="voiceStopBtn" type="button" hidden disabled>Ukončit záznam</button>
      </div>
      <span id="voiceStatus" role="status" aria-live="polite">Přepis se vloží do pole a sám se neodešle.</span>
      <div class="send-controls">
        <button id="writeIntentBtn" type="button" aria-pressed="false">Zahájit vývoj</button>
        <button class="primary" id="sendBtn" type="submit">Odeslat</button>
      </div>
    </div>
  </form>
  <aside class="tvbcp-panel" id="tvbcpPanel" hidden aria-label="Projektový TVBCP">
    <div class="tvbcp-head">
      <h2 id="tvbcpTitle">Projektový TVBCP</h2>
      <button id="tvbcpRefreshBtn" type="button">Obnovit</button>
      <button id="tvbcpCloseBtn" type="button">Zavřít</button>
    </div>
    <div id="tvbcpMeta">TVBCP se načte až po otevření.</div>
    <div id="tvbcpScroll" data-scroll-mode="end-anchor-v3">
      <pre id="tvbcpContent"></pre>
      <div id="tvbcpEnd" aria-hidden="true"></div>
    </div>
  </aside>
  <aside class="tvbcp-panel" id="threadRotationPanel" hidden aria-label="Bezpečná rotace profilového vlákna">
    <div class="tvbcp-head">
      <h2>Nové profilové vlákno</h2>
      <button id="threadRotationCloseBtn" type="button">Zavřít</button>
    </div>
    <div class="thread-rotation-panel-body">
      <p class="thread-rotation-help">Rotaci použij, když je dosavadní vlákno příliš dlouhé nebo začíná nová ucelená etapa stejného pracovního proudu. Nejdřív dokonči aktivní tah, spusť kontrolu a použij přesnou nabídnutou potvrzovací větu. Staré vlákno zůstane zachované a nearchivované; kontinuita pokračuje z handoffu, TVBCP a krátkého aktuálního kontextu.</p>
      <section class="thread-rotation-box" aria-label="Bezpečná rotace profilového vlákna">
        <p id="threadRotationMeta">Spusť kontrolu připravenosti. Staré vlákno se nemaže ani nearchivuje.</p>
        <input id="threadRotationConfirmation" maxlength="80" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" placeholder="Po kontrole sem vlož potvrzovací větu" hidden disabled>
        <div class="thread-rotation-actions">
          <button id="threadRotationAuditBtn" type="button">Prověřit nové vlákno</button>
          <button class="primary" id="threadRotationBtn" type="button" hidden disabled>Přejít do nového vlákna</button>
        </div>
      </section>
    </div>
  </aside>
  <aside class="tvbcp-panel" id="workPanel" hidden aria-label="Pracovní změny">
    <div class="tvbcp-head">
      <h2>Pracovní změny</h2>
      <button class="workflow-help-trigger" id="workHelpBtn" type="button" aria-label="Nápověda k jednoduchému vývoji a nasazení" aria-expanded="false" aria-controls="workHelpPanel" title="Jak pracovat a nasazovat">?</button>
      <button id="workRefreshBtn" type="button">Obnovit</button>
      <button id="workCloseBtn" type="button">Zavřít</button>
    </div>
    <div class="work-panel-body">
    <section class="workflow-help-panel work-help-panel" id="workHelpPanel" aria-labelledby="workHelpTitle" tabindex="-1" hidden>
      <div class="workflow-help-head">
        <h3 id="workHelpTitle">Jak pracovat a nasazovat</h3>
        <button id="workHelpCloseBtn" type="button">Zavřít návod</button>
      </div>
      <div class="simple-work-help">
        <p>Toto je pouze nápověda. Jejím otevřením se nic nemění, necommitne ani nenasadí.</p>

        <h4>1. Běžný vývoj</h4>
        <ol>
          <li>Vyber správný pracovní proud a klikni na <strong>Připojit</strong>.</li>
          <li>Před změnou kódu nebo projektových souborů klikni na <strong>Zahájit vývoj</strong> a potvrď jednorázové oprávnění. Platí pouze pro následující odeslaný pokyn; bez něj Adam zůstává pro workspace a Git read-only.</li>
          <li id="privateArchiveHelp" hidden><strong>Soukromý archiv aktivního proudu:</strong> čtení, diagnostiku a jednu jasně zadanou běžnou nedestruktivní úpravu pošli přímo bez tlačítka Zahájit vývoj. Samostatné potvrzení zůstává pro mazání, hromadné změny, odesílání ven a systémové zásahy.</li>
          <li>Vývojový úkol napiš přímo Adamovi do textového pole. Nový projekt, tool nebo layer se zakládá pouze v terminálovém dialogu s Adamem.</li>
          <li>Po úspěšné změně Adam spustí odpovídající testy, vytvoří samostatný lokální commit přímo v <code>main</code> a synchronizuje čisté profily. Nic tím ještě neposílá na GitHub ani nenačítá do běžícího Cockpitu.</li>
          <li>Pokud panel ukazuje čistý stav, můžeš hned zadat další vývoj. Lokální commity se přes den bezpečně skládají do denního balíčku.</li>
        </ol>

        <h4>2. Nasazení do Cockpitu</h4>
        <p><strong>Lokální commit není nasazení.</strong> Nasazuj jen tehdy, když má nový kód změnit běžící rozhraní nebo backend Cockpitu. Dokumentační změna ani další běžný vývoj nasazení nepotřebují.</p>
        <ol>
          <li>V okně <strong>Práce</strong> jednou stiskni <strong>Audit nasazení do Cockpitu</strong>.</li>
          <li>Vlož zobrazenou přesnou větu a jednou stiskni <strong>Nasadit aktuální main do Cockpitu</strong>.</li>
          <li>Počkej na řízený restart a potvrzení <strong>Běžící Cockpit ověřen</strong>.</li>
        </ol>
        <p>Nasazení nespouštěj současně z Cockpitu a z terminálového Adama. Stavový řádek vždy rozlišuje lokální <code>Git/main</code> od kódu načteného v běžícím Cockpitu.</p>

        <h4>3. Denní GitHub balíček</h4>
        <p>GitHub běžný vývoj nezdržuje. Až budeš chtít uzavřít denní balíček, otevři <strong>Práce</strong>, zkontroluj seznam čekajících commitů a vlož přesnou potvrzovací větu. Cockpit potom jednou spustí úplnou bránu a jedním pushem odešle celý balíček.</p>

        <h4>Když něco nejde</h4>
        <ul>
          <li><strong>Workspace je za <code>main</code>:</strong> při čistém profilu klikni na Připojit.</li>
          <li><strong>GitHub je před lokálním <code>main</code>:</strong> denní balíček se bezpečně zastaví. Audit nabídne tlačítko <strong>Dorovnat main s GitHubem</strong> pouze při čistém jednoznačném fast-forwardu. Při divergenci rozhodne servis; žádný merge, rebase ani force push se nespustí automaticky.</li>
          <li><strong>Čekající integrace:</strong> přečti read-only audit. Pokud je <code>main</code> čistý, nezměněný a private ownership marker odpovídá přesnému WIP, vlož nabídnutou potvrzovací větu a klikni na <strong>Převzít přesný WIP do main</strong>. Když model zapomene dokončovací účtenku, marker vytvořený před tahem zachová původ změn a panel nabídne <strong>Dokončit vlastněný WIP</strong> po doplnění git-safe popisu. Při posunu <code>main</code>, cizím WIP, divergenci nebo neshodě markeru nic nezačleňuj a vyžádej servisní rozhodnutí; totéž platí při nejistém doručení.</li>
          <li><strong>Audit nebo nasazení do Cockpitu selže:</strong> nic neopakuj naslepo; obnov stav a předej Adamovi přesnou chybu.</li>
          <li><strong>Čekání na nový Cockpit dosáhne limitu:</strong> neznamená to automaticky neúspěšné nasazení. Nasazení neopakuj, nejdřív obnov stav a zkontroluj serverovou účtenku. Terminálový fallback použij pouze tehdy, když Cockpit skutečně neodpovídá.</li>
          <li><strong>Repo není čisté:</strong> nenasazuj a nech Adama zjistit, co zůstalo rozpracované.</li>
        </ul>

        <p class="workflow-help-safety"><strong>Nouzový postup:</strong> nic nemaž, nepoužívej reset, rebase ani force push. Požádej Adama o read-only kontrolu.</p>
      </div>
    </section>
    <section class="batch-workflow-box" id="batchWorkflowBox" aria-label="Dnešní jednoduchý vývojový režim" hidden>
      <h3>Dnešní jednoduchý režim</h3>
      <p id="batchWorkflowNext" role="status">Načítám doporučený další krok.</p>
      <ol>
        <li id="batchWorkflowLocal">Vývoj: stav se načítá.</li>
        <li id="batchWorkflowDeploy">Cockpit: stav se načítá.</li>
        <li id="batchWorkflowGithub">GitHub: stav se načítá.</li>
      </ol>
    </section>
    <section class="development-semaphore-box legacy-work-control" aria-label="Historický globální vývojový semafor">
      <h3>Vývojový semafor</h3>
      <p id="developmentSemaphoreMeta">Stav vlastníka vývoje se načte společně s pracovním stavem.</p>
      <div class="development-binding-fields">
        <label>Projekt
          <select id="developmentProject" aria-label="Projekt vývoje"><option value="">Načítám projekty…</option></select>
        </label>
        <label>Aktuální handoff
          <select id="developmentHandoff" aria-label="Aktuální handoff projektu" disabled><option value="">Nejdřív vyber projekt</option></select>
        </label>
      </div>
      <input id="developmentTopic" maxlength="120" autocomplete="off" placeholder="Krátké téma vývoje">
      <div class="development-semaphore-actions">
        <button class="primary" id="developmentAcquireProfileBtn" type="button">Převzít pro tento profil</button>
        <button id="developmentAcquireTerminalBtn" type="button">Převzít pro terminál</button>
        <button id="developmentPauseBtn" type="button" hidden>Pozastavit</button>
        <button id="developmentResumeBtn" type="button" hidden>Obnovit</button>
        <button id="developmentReleaseBtn" type="button" hidden>Uvolnit</button>
      </div>
    </section>
    <section class="project-continuity-box legacy-work-control" aria-label="Historická aktuálnost projektového handoffu">
      <div class="project-continuity-head">
        <h3>Kontinuita projektu</h3>
        <button id="projectContinuityAuditBtn" type="button">Prověřit handoff</button>
      </div>
      <p id="projectContinuityMeta">Audit je pouze read-only a zatím nic neblokuje.</p>
      <ul id="projectContinuityReasons" hidden></ul>
    </section>
    <section class="live-work-status-box" id="liveWorkStatusBox" data-state="unverified" aria-label="Read-only živý stav pracovního proudu">
      <h3>Živý stav</h3>
      <p id="liveWorkStatusMeta" role="status">Stav se načte až po otevření panelu Práce.</p>
      <ul id="liveWorkStatusAxes"></ul>
    </section>
    <section class="live-work-status-box" id="trustedExternalGenerationBox" data-state="unverified" aria-label="Trvalý souhlas s externím generováním">
      <h3>Externí generování</h3>
      <p id="trustedExternalGenerationMeta" role="status">Stav trvalého souhlasu se načítá.</p>
      <p id="trustedExternalGenerationConfirmation"></p>
      <input id="trustedExternalGenerationInput" maxlength="700" autocomplete="off" spellcheck="false" placeholder="Vlož přesnou potvrzovací větu">
      <button id="trustedExternalGenerationBtn" type="button" disabled>Načítám…</button>
    </section>
    <div id="workMeta">Stav se načte až po otevření.</div>
    <ul id="workChanges"></ul>
    <section class="integration-audit-box" id="integrationAuditBox" aria-label="Audit a potvrzovaná brána čekající integrace" hidden>
      <h3>Čekající integrace</h3>
      <p id="integrationAuditMeta">Audit se načte společně s pracovním stavem.</p>
      <ul id="integrationAuditPaths" hidden></ul>
      <div class="integration-recovery-fields" id="integrationRecoveryFields" hidden>
        <label>Název commitu
          <input id="integrationRecoveryCommit" maxlength="120" autocomplete="off" placeholder="Krátký git-safe název">
        </label>
        <label>Co je hotové
          <input id="integrationRecoverySummary" maxlength="400" autocomplete="off" placeholder="Stručný redigovaný výsledek">
        </label>
        <label>Další krok
          <input id="integrationRecoveryNextStep" maxlength="500" autocomplete="off" placeholder="Praktický následující krok">
        </label>
      </div>
      <input id="integrationConfirmation" maxlength="80" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" placeholder="Potvrzovací věta" hidden disabled>
      <button class="deploy-action" id="integrationBtn" type="button" hidden disabled>Převzít přesný WIP do main</button>
      <button class="deploy-action" id="integrationRecoveryBtn" type="button" hidden disabled>Dokončit vlastněný WIP</button>
    </section>
    <section class="handoff-proposal-box legacy-work-control" id="handoffProposalBox" aria-label="Read-only návrh aktualizace handoffu" hidden>
      <h3>Návrh handoffu po checkpointu</h3>
      <p id="handoffProposalMeta">Návrh zatím není připravený.</p>
      <pre id="handoffProposalDraft" hidden></pre>
    </section>
    <div class="checkpoint-box">
      <input class="legacy-work-control" id="checkpointMessage" maxlength="120" placeholder="Historický lokální checkpoint">
      <button class="primary legacy-work-control" id="checkpointBtn" type="button" disabled>Historický lokální checkpoint</button>
      <div id="deployMeta">Nasazení je dostupné až po lokálním WIP checkpointu.</div>
      <section class="integration-audit-box" id="mainSyncBox" aria-label="Ruční dorovnání lokálního main s GitHubem" hidden>
        <h3>Dorovnání main s GitHubem</h3>
        <p id="mainSyncMeta">Nejdřív spusť audit nasazení.</p>
        <ul id="mainSyncChanges" hidden></ul>
        <button class="audit-action" id="mainSyncBtn" type="button" disabled>Dorovnat main s GitHubem</button>
      </section>
      <div class="legacy-work-control" id="handoffTakeoverCheck" role="status" hidden></div>
      <button class="audit-action" id="deployAuditBtn" type="button" disabled>Audit nasazení do Cockpitu</button>
      <input id="deployConfirmation" maxlength="80" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" placeholder="Po auditu sem vlož potvrzovací větu" hidden disabled>
      <button class="deploy-action" id="deployBtn" type="button" disabled>Nasadit aktuální main do Cockpitu</button>
      <section class="integration-audit-box" id="githubBatchBox" aria-label="Denní GitHub balíček" hidden>
        <h3>Denní GitHub balíček</h3>
        <p id="githubBatchMeta">Stav se prověří při otevření panelu Práce.</p>
        <ul id="githubBatchCommits" hidden></ul>
        <input id="githubBatchConfirmation" maxlength="80" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" placeholder="Po auditu sem vlož potvrzovací větu" hidden disabled>
        <button class="deploy-action" id="githubBatchBtn" type="button" hidden disabled>Odeslat denní balíček na GitHub</button>
      </section>
    </div>
    </div>
  </aside>
</main>
<script>
  const chat = document.getElementById("chat");
  const notice = document.getElementById("notice");
  const stepCompletionReceipt = document.getElementById("stepCompletionReceipt");
  const deploymentReceipt = document.getElementById("deploymentReceipt");
  const mobileStatusSummary = document.getElementById("mobileStatusSummary");
  const mobileStatusText = document.getElementById("mobileStatusText");
  const mobileStatusToggleText = document.getElementById("mobileStatusToggleText");
  const statusDetails = document.getElementById("statusDetails");
  const connectionBadge = document.getElementById("connectionBadge");
  const profileBadge = document.getElementById("profileBadge");
  const threadBadge = document.getElementById("threadBadge");
  const workspaceBadge = document.getElementById("workspaceBadge");
  const developmentBadge = document.getElementById("developmentBadge");
  const mediaSoundTestBtn = document.getElementById("mediaSoundTestBtn");
  const completionMediaAudio = document.getElementById("completionMediaAudio");
  const turnActivity = document.getElementById("turnActivity");
  const connectBtn = document.getElementById("connectBtn");
  const profileSelect = document.getElementById("profileSelect");
  const profileSwitchBtn = document.getElementById("profileSwitchBtn");
  const refreshBtn = document.getElementById("refreshBtn");
  const threadRotationOpenBtn = document.getElementById("threadRotationOpenBtn");
  const threadRotationPanel = document.getElementById("threadRotationPanel");
  const threadRotationCloseBtn = document.getElementById("threadRotationCloseBtn");
  const threadRotationMeta = document.getElementById("threadRotationMeta");
  const threadRotationConfirmation = document.getElementById("threadRotationConfirmation");
  const threadRotationAuditBtn = document.getElementById("threadRotationAuditBtn");
  const threadRotationBtn = document.getElementById("threadRotationBtn");
  const composer = document.getElementById("composer");
  const input = document.getElementById("messageInput");
  const writeIntentBtn = document.getElementById("writeIntentBtn");
  const sendBtn = document.getElementById("sendBtn");
  const voiceRecordBtn = document.getElementById("voiceRecordBtn");
  const voiceStopBtn = document.getElementById("voiceStopBtn");
  const voiceStatus = document.getElementById("voiceStatus");
  const tvbcpOpenBtn = document.getElementById("tvbcpOpenBtn");
  const tvbcpPanel = document.getElementById("tvbcpPanel");
  const tvbcpCloseBtn = document.getElementById("tvbcpCloseBtn");
  const tvbcpRefreshBtn = document.getElementById("tvbcpRefreshBtn");
  const tvbcpTitle = document.getElementById("tvbcpTitle");
  const tvbcpMeta = document.getElementById("tvbcpMeta");
  const tvbcpScroll = document.getElementById("tvbcpScroll");
  const tvbcpContent = document.getElementById("tvbcpContent");
  const tvbcpEnd = document.getElementById("tvbcpEnd");
  const workOpenBtn = document.getElementById("workOpenBtn");
  const workPanel = document.getElementById("workPanel");
  const workCloseBtn = document.getElementById("workCloseBtn");
  const workRefreshBtn = document.getElementById("workRefreshBtn");
  const workHelpBtn = document.getElementById("workHelpBtn");
  const workHelpPanel = document.getElementById("workHelpPanel");
  const workHelpCloseBtn = document.getElementById("workHelpCloseBtn");
  const privateArchiveHelp = document.getElementById("privateArchiveHelp");
  const batchWorkflowBox = document.getElementById("batchWorkflowBox");
  const batchWorkflowNext = document.getElementById("batchWorkflowNext");
  const batchWorkflowLocal = document.getElementById("batchWorkflowLocal");
  const batchWorkflowDeploy = document.getElementById("batchWorkflowDeploy");
  const batchWorkflowGithub = document.getElementById("batchWorkflowGithub");
  const liveWorkStatusBox = document.getElementById("liveWorkStatusBox");
  const liveWorkStatusMeta = document.getElementById("liveWorkStatusMeta");
  const liveWorkStatusAxes = document.getElementById("liveWorkStatusAxes");
  const workMeta = document.getElementById("workMeta");
  const workChanges = document.getElementById("workChanges");
  const integrationAuditBox = document.getElementById("integrationAuditBox");
  const integrationAuditMeta = document.getElementById("integrationAuditMeta");
  const integrationAuditPaths = document.getElementById("integrationAuditPaths");
  const integrationRecoveryFields = document.getElementById("integrationRecoveryFields");
  const integrationRecoveryCommit = document.getElementById("integrationRecoveryCommit");
  const integrationRecoverySummary = document.getElementById("integrationRecoverySummary");
  const integrationRecoveryNextStep = document.getElementById("integrationRecoveryNextStep");
  const integrationConfirmation = document.getElementById("integrationConfirmation");
  const integrationBtn = document.getElementById("integrationBtn");
  const integrationRecoveryBtn = document.getElementById("integrationRecoveryBtn");
  const handoffProposalBox = document.getElementById("handoffProposalBox");
  const handoffProposalMeta = document.getElementById("handoffProposalMeta");
  const handoffProposalDraft = document.getElementById("handoffProposalDraft");
  const developmentSemaphoreMeta = document.getElementById("developmentSemaphoreMeta");
  const developmentProject = document.getElementById("developmentProject");
  const developmentHandoff = document.getElementById("developmentHandoff");
  const developmentTopic = document.getElementById("developmentTopic");
  const developmentAcquireProfileBtn = document.getElementById("developmentAcquireProfileBtn");
  const developmentAcquireTerminalBtn = document.getElementById("developmentAcquireTerminalBtn");
  const developmentPauseBtn = document.getElementById("developmentPauseBtn");
  const developmentResumeBtn = document.getElementById("developmentResumeBtn");
  const developmentReleaseBtn = document.getElementById("developmentReleaseBtn");
  const projectContinuityAuditBtn = document.getElementById("projectContinuityAuditBtn");
  const projectContinuityMeta = document.getElementById("projectContinuityMeta");
  const projectContinuityReasons = document.getElementById("projectContinuityReasons");
  const trustedExternalGenerationBox = document.getElementById("trustedExternalGenerationBox");
  const trustedExternalGenerationMeta = document.getElementById("trustedExternalGenerationMeta");
  const trustedExternalGenerationConfirmation = document.getElementById("trustedExternalGenerationConfirmation");
  const trustedExternalGenerationInput = document.getElementById("trustedExternalGenerationInput");
  const trustedExternalGenerationBtn = document.getElementById("trustedExternalGenerationBtn");
  const checkpointMessage = document.getElementById("checkpointMessage");
  const checkpointBtn = document.getElementById("checkpointBtn");
  const deployMeta = document.getElementById("deployMeta");
  const mainSyncBox = document.getElementById("mainSyncBox");
  const mainSyncMeta = document.getElementById("mainSyncMeta");
  const mainSyncChanges = document.getElementById("mainSyncChanges");
  const mainSyncBtn = document.getElementById("mainSyncBtn");
  const githubBatchBox = document.getElementById("githubBatchBox");
  const githubBatchMeta = document.getElementById("githubBatchMeta");
  const githubBatchCommits = document.getElementById("githubBatchCommits");
  const githubBatchConfirmation = document.getElementById("githubBatchConfirmation");
  const githubBatchBtn = document.getElementById("githubBatchBtn");
  const handoffTakeoverCheck = document.getElementById("handoffTakeoverCheck");
  const deployAuditBtn = document.getElementById("deployAuditBtn");
  const deployConfirmation = document.getElementById("deployConfirmation");
  const deployBtn = document.getElementById("deployBtn");
  let busy = false;
  let sendInFlight = false;
  let sessionTurnBusy = false;
  let voiceRecorder = null;
  let voiceStream = null;
  let voiceChunks = [];
  let voiceStarting = false;
  let voiceRecording = false;
  let voiceTranscribing = false;
  let turnTimerId = null;
  let activeTurnStartedAt = "";
  let resultWatchTimerId = null;
  let resultWatchActive = false;
  let resultWatchClientMessageId = "";
  let resultWatchAttempt = 0;
  let lastSession = null;
  let sessionConnected = false;
  let activeWorkstreamId = "";
  let activeWorkstreamBackend = "compatibility_adapter";
  let activeWorkstreamLabel = "Human–Adam";
  let workstreamDevelopmentEnabled = true;
  let workstreamDeploymentEnabled = true;
  let writeIntentArmed = false;
  let deliveryUncertain = false;
  let deploymentAudit = null;
  let mainRemoteSyncAudit = null;
  let githubBatchAudit = null;
  let githubBatchModeEnabled = false;
  let pendingIntegrationAudit = null;
  let pendingIntegrationRecovery = null;
  let currentWorkstreamLiveStatus = null;
  const verifiedDeploymentStorageKey = "human-adam:verified-deployment:v1";
  const verifiedDeploymentSeenStorageKey = "human-adam:verified-deployment-seen:v1";
  const verifiedDeploymentMaxAgeMs = 15 * 60 * 1000;
  const deploymentReturnMaxAttempts = 120;
  let developmentSemaphore = null;
  let projectContinuity = null;
  let completionMediaUrl = "";
  let activeSpeechButton = null;
  let activeSpeechUtterance = null;
  let threadRotationAudit = null;
  let imageCandidatesByMessage = new Map();
  let imageCandidatesLoading = false;
  let imageGenerationEnabled = false;
  let trustedExternalGenerationEnabled = false;
  let trustedExternalGenerationGrantText = "";
  let trustedExternalGenerationRevokeText = "";
  const HUMAN_ADAM_SEND_PATH = "/api/human-adam/send";
  const RESULT_WATCH_MAX_ATTEMPTS = 60;
  const RESULT_WATCH_MAX_DELAY_MS = 30000;

  function messageId() {
    if (window.crypto && crypto.randomUUID) return `human-adam-${crypto.randomUUID()}`;
    return `human-adam-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function formatTime(value) {
    if (!value) return "čas neuveden";
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("cs-CZ", {hour:"2-digit",minute:"2-digit",second:"2-digit",day:"2-digit",month:"2-digit"});
  }

  function configureCompletionAudioSession() {
    if (typeof navigator === "undefined" || !("audioSession" in navigator) || !navigator.audioSession) return false;
    try {
      navigator.audioSession.type = "playback";
      return navigator.audioSession.type === "playback";
    } catch (_error) {
      return false;
    }
  }

  function writeWavText(view, offset, text) {
    for (let index = 0; index < text.length; index += 1) view.setUint8(offset + index, text.charCodeAt(index));
  }

  function completionMediaWavUrl() {
    if (completionMediaUrl) return completionMediaUrl;
    if (!window.URL || typeof window.URL.createObjectURL !== "function" || typeof Blob === "undefined") return "";
    const sampleRate = 22050;
    const frameCount = Math.ceil(sampleRate * 0.55);
    const dataLength = frameCount * 2;
    const buffer = new ArrayBuffer(44 + dataLength);
    const view = new DataView(buffer);
    writeWavText(view, 0, "RIFF");
    view.setUint32(4, 36 + dataLength, true);
    writeWavText(view, 8, "WAVE");
    writeWavText(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeWavText(view, 36, "data");
    view.setUint32(40, dataLength, true);
    const notes = [
      {frequency:740, start:0.02, duration:0.16},
      {frequency:988, start:0.22, duration:0.24},
    ];
    for (let frame = 0; frame < frameCount; frame += 1) {
      const time = frame / sampleRate;
      let sample = 0;
      for (const note of notes) {
        const localTime = time - note.start;
        if (localTime < 0 || localTime >= note.duration) continue;
        const attack = Math.min(1, localTime / 0.015);
        const release = Math.min(1, (note.duration - localTime) / 0.04);
        sample += Math.sin(2 * Math.PI * note.frequency * localTime) * 0.48 * Math.min(attack, release);
      }
      view.setInt16(44 + frame * 2, Math.round(Math.max(-1, Math.min(1, sample)) * 32767), true);
    }
    completionMediaUrl = window.URL.createObjectURL(new Blob([buffer], {type:"audio/wav"}));
    return completionMediaUrl;
  }

  function stopCompletionMediaSound() {
    completionMediaAudio.pause();
    try { completionMediaAudio.currentTime = 0; } catch (_error) {}
  }

  function prepareCompletionMediaSound() {
    configureCompletionAudioSession();
    const source = completionMediaWavUrl();
    if (!source) throw new Error("Mediální zvuk není podporovaný.");
    stopCompletionMediaSound();
    if (completionMediaAudio.src !== source) {
      completionMediaAudio.src = source;
      completionMediaAudio.load();
    }
    completionMediaAudio.volume = 1;
  }

  function updateCompletionMediaSoundUi(ready) {
    mediaSoundTestBtn.textContent = ready ? "Zvuk odpovědi: připraven" : "Zvuk odpovědi: vyzkoušet";
    mediaSoundTestBtn.className = ready ? "badge sound-badge ok" : "badge sound-badge warn";
  }

  async function primeCompletionMediaSound() {
    try {
      prepareCompletionMediaSound();
      completionMediaAudio.muted = true;
      const playback = completionMediaAudio.play();
      const started = playback && typeof playback.then === "function"
        ? await Promise.race([
          playback.then(() => true).catch(() => false),
          new Promise((resolve) => window.setTimeout(() => resolve(false), 500)),
        ])
        : true;
      if (!started) throw new Error("Mediální zvuk se nepodařilo připravit.");
      stopCompletionMediaSound();
      updateCompletionMediaSoundUi(true);
      return true;
    } catch (_error) {
      updateCompletionMediaSoundUi(false);
      return false;
    } finally {
      completionMediaAudio.muted = false;
    }
  }

  async function playCompletionMediaSound() {
    try {
      prepareCompletionMediaSound();
      completionMediaAudio.muted = false;
      const playback = completionMediaAudio.play();
      if (playback && typeof playback.then === "function") await playback;
      updateCompletionMediaSoundUi(true);
      return true;
    } catch (_error) {
      // Zvuk je pouze doplňkový; nesmí změnit potvrzený stav dokončeného tahu.
      updateCompletionMediaSoundUi(false);
      return false;
    }
  }

  async function testCompletionMediaSound() {
    mediaSoundTestBtn.disabled = true;
    try {
      await playCompletionMediaSound();
    } finally {
      mediaSoundTestBtn.disabled = false;
    }
  }

  function syncControls() {
    const rotationBlocked = busy || sendInFlight || sessionTurnBusy;
    connectBtn.disabled = busy;
    profileSelect.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing;
    profileSwitchBtn.disabled = profileSelect.disabled || !profileSelect.value || profileSelect.value === activeWorkstreamId;
    refreshBtn.disabled = busy || resultWatchActive;
    workOpenBtn.disabled = busy;
    refreshBtn.textContent = resultWatchActive ? "Čekám na výsledek…" : "Stav";
    sendBtn.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing;
    writeIntentBtn.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing || !sessionConnected || !workstreamDevelopmentEnabled;
    writeIntentBtn.classList.toggle("armed", writeIntentArmed);
    writeIntentBtn.setAttribute("aria-pressed", writeIntentArmed ? "true" : "false");
    writeIntentBtn.textContent = writeIntentArmed ? "Vývoj připraven" : "Zahájit vývoj";
    voiceRecordBtn.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing;
    voiceRecordBtn.classList.toggle("recording", voiceRecording);
    voiceRecordBtn.textContent = voiceRecording ? "Nahrávám…" : "Nahrát pokyn";
    voiceStopBtn.hidden = !voiceRecording;
    voiceStopBtn.disabled = !voiceRecording;
    threadRotationAuditBtn.disabled = rotationBlocked || !sessionConnected;
    const rotationRequired = threadRotationAudit ? String(threadRotationAudit.confirmation_text || "") : "";
    threadRotationConfirmation.disabled = rotationBlocked || !threadRotationAudit || threadRotationAudit.ready !== true;
    threadRotationBtn.disabled = threadRotationConfirmation.disabled || !rotationRequired || threadRotationConfirmation.value.trim() !== rotationRequired;
    const semaphoreValid = developmentSemaphore && developmentSemaphore.ok === true;
    const semaphoreActive = Boolean(semaphoreValid && developmentSemaphore.active);
    developmentTopic.disabled = busy || semaphoreActive;
    developmentProject.disabled = busy || semaphoreActive || !projectContinuity || projectContinuity.ok !== true;
    developmentHandoff.disabled = developmentProject.disabled || !developmentProject.value;
    developmentAcquireProfileBtn.disabled = busy || !semaphoreValid || developmentSemaphore.can_acquire_profile !== true;
    developmentAcquireTerminalBtn.disabled = busy || !semaphoreValid || developmentSemaphore.can_acquire_terminal !== true;
    developmentPauseBtn.disabled = busy || !semaphoreValid || developmentSemaphore.can_pause !== true;
    developmentResumeBtn.disabled = busy || !semaphoreValid || developmentSemaphore.can_resume !== true;
    developmentReleaseBtn.disabled = busy || !semaphoreValid || developmentSemaphore.can_release !== true;
    projectContinuityAuditBtn.disabled = busy;
  }

  function setBusy(value, text="") {
    busy = value;
    syncControls();
    if (text) notice.textContent = text;
  }

  function setWriteIntentArmed(value) {
    writeIntentArmed = Boolean(value);
    syncControls();
  }

  function armWriteIntent() {
    if (writeIntentBtn.disabled || writeIntentArmed) return;
    const confirmed = window.confirm("Jednorázově povolit zápis pouze pro následující pokyn?\n\nServer před odesláním ověří čistý main a všechny vývojové workspaces. Oprávnění se po jednom pokusu zruší.");
    if (!confirmed) return;
    setWriteIntentArmed(true);
    notice.textContent = "Jednorázový vývoj je připravený pro následující odeslaný pokyn.";
    input.focus();
  }

  function setMobileStatusDetails(expanded) {
    const showDetails = Boolean(expanded);
    statusDetails.classList.toggle("expanded", showDetails);
    mobileStatusSummary.setAttribute("aria-expanded", showDetails ? "true" : "false");
    mobileStatusToggleText.textContent = showDetails ? "Skrýt" : "Podrobnosti";
  }

  function updateMobileStatusSummary() {
    let text = "";
    let tone = "";
    if (sessionTurnBusy) {
      text = turnActivity.textContent || "Adam pracuje · čas neznámý · pokyn neposílej znovu";
      tone = "warn";
    } else if (deliveryUncertain) {
      text = "Stav doručení je nejistý · obnov stav · pokyn neposílej znovu";
      tone = "warn";
    } else {
      const connectionText = connectionBadge.textContent || "Odpojeno";
      const workspaceText = workspaceBadge.textContent || "Izolovaný workspace";
      const adamText = sessionConnected ? "Adam čeká" : "Adam není připojen";
      text = `${activeWorkstreamLabel} · ${connectionText} · ${workspaceText} · ${adamText}`;
      tone = sessionConnected && !workspaceBadge.classList.contains("warn") ? "ok" : "warn";
    }
    mobileStatusText.textContent = text;
    mobileStatusSummary.classList.toggle("ok", tone === "ok");
    mobileStatusSummary.classList.toggle("warn", tone === "warn");
  }

  function elapsedClock(startedAt) {
    const startedMs = new Date(startedAt).getTime();
    if (!Number.isFinite(startedMs)) return "čas neznámý";
    const elapsedSeconds = Math.max(0, Math.floor((Date.now() - startedMs) / 1000));
    const minutes = String(Math.floor(elapsedSeconds / 60)).padStart(2, "0");
    const seconds = String(elapsedSeconds % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  function stopTurnTimer() {
    if (turnTimerId !== null) window.clearTimeout(turnTimerId);
    turnTimerId = null;
    activeTurnStartedAt = "";
  }

  function updateTurnTimer() {
    if (!activeTurnStartedAt) return;
    turnActivity.textContent = `Adam pracuje · ${elapsedClock(activeTurnStartedAt)} · pokyn neposílej znovu`;
    updateMobileStatusSummary();
    turnTimerId = window.setTimeout(updateTurnTimer, 1000);
  }

  function startTurnTimer(startedAt) {
    const parsed = new Date(startedAt);
    const normalized = Number.isNaN(parsed.getTime()) ? "" : parsed.toISOString();
    if (!normalized) {
      stopTurnTimer();
      turnActivity.textContent = "Adam pracuje · čas neznámý · pokyn neposílej znovu";
      return;
    }
    if (activeTurnStartedAt === normalized && turnTimerId !== null) return;
    stopTurnTimer();
    activeTurnStartedAt = normalized;
    updateTurnTimer();
  }

  function renderTurnState(session) {
    const messages = session && Array.isArray(session.messages) ? session.messages : [];
    const latest = messages.length ? messages[messages.length - 1] : null;
    sessionTurnBusy = Boolean(session && session.turn_busy);
    if (sessionTurnBusy) {
      deliveryUncertain = false;
      const activeTurn = session && session.active_turn ? session.active_turn : {};
      startTurnTimer(activeTurn.started_at || "");
      turnActivity.hidden = false;
    } else {
      stopTurnTimer();
      deliveryUncertain = Boolean(latest && latest.status === "delivery_unknown");
      turnActivity.textContent = deliveryUncertain
        ? "Stav doručení je nejistý · obnov stav · pokyn neposílej znovu"
        : "";
      turnActivity.hidden = !deliveryUncertain;
    }
    updateMobileStatusSummary();
    syncControls();
  }

  function clearMessageInput() {
    input.value = "";
    input.defaultValue = "";
  }

  function runSendUiBestEffort(action) {
    try {
      action();
    } catch (_error) {
      // Zobrazení je pomocné; nesmí zablokovat ani změnit výsledek transportu.
    }
  }

  function restoreRejectedMessage(text) {
    if (input.value) return;
    input.value = String(text || "").slice(0, Number(input.maxLength) || 12000);
    input.defaultValue = "";
    input.focus();
  }

  function preferredVoiceMimeType() {
    if (!window.MediaRecorder || typeof window.MediaRecorder.isTypeSupported !== "function") return "";
    const candidates = ["audio/mp4", "audio/webm;codecs=opus", "audio/webm"];
    return candidates.find((candidate) => window.MediaRecorder.isTypeSupported(candidate)) || "";
  }

  function releaseVoiceStream() {
    if (voiceStream) voiceStream.getTracks().forEach((track) => track.stop());
    voiceStream = null;
  }

  function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.addEventListener("load", () => {
        const dataUrl = String(reader.result || "");
        resolve(dataUrl.includes(",") ? dataUrl.split(",", 2)[1] : dataUrl);
      }, {once:true});
      reader.addEventListener("error", () => reject(new Error("Nahrávku nelze načíst.")), {once:true});
      reader.readAsDataURL(blob);
    });
  }

  function insertTranscriptForReview(text) {
    const transcript = String(text || "").trim();
    if (!transcript) throw new Error("Přepis je prázdný.");
    const existing = input.value;
    const separator = existing && !/\s$/.test(existing) ? "\n" : "";
    const combined = `${existing}${separator}${transcript}`;
    if (input.maxLength > 0 && combined.length > input.maxLength) {
      throw new Error("Přepis se nevejde do textového pole; zkrať rozepsaný text.");
    }
    input.value = combined;
    input.focus();
  }

  function isIOSDevice() {
    const userAgent = String(navigator.userAgent || "");
    return /iPad|iPhone|iPod/.test(userAgent)
      || (navigator.platform === "MacIntel" && Number(navigator.maxTouchPoints || 0) > 1);
  }

  async function startVoiceRecording() {
    if (busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing) return;
    if (isIOSDevice()) {
      input.focus();
      voiceStatus.textContent = "Kurzor je v poli; použij mikrofon klávesnice iPhonu a text před odesláním zkontroluj.";
      return;
    }
    if (!window.isSecureContext) {
      voiceStatus.textContent = "Mikrofon je na iPhonu dostupný jen přes HTTPS adresu Cockpitu; tato stránka běží přes HTTP.";
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
      voiceStatus.textContent = "Tento prohlížeč nebo jeho oprávnění nepodporují nahrávání mikrofonu.";
      return;
    }
    try {
      voiceStarting = true;
      syncControls();
      voiceStream = await navigator.mediaDevices.getUserMedia({audio:true});
      voiceStarting = false;
      if (sendInFlight || sessionTurnBusy) {
        releaseVoiceStream();
        voiceStatus.textContent = "Adam právě pracuje; nový záznam teď nelze zahájit.";
        syncControls();
        return;
      }
      voiceChunks = [];
      const mimeType = preferredVoiceMimeType();
      voiceRecorder = mimeType
        ? new window.MediaRecorder(voiceStream, {mimeType})
        : new window.MediaRecorder(voiceStream);
      voiceRecorder.addEventListener("dataavailable", (event) => {
        if (event.data && event.data.size > 0) voiceChunks.push(event.data);
      });
      voiceRecorder.addEventListener("stop", transcribeVoiceRecording, {once:true});
      voiceRecorder.start();
      voiceRecording = true;
      voiceStatus.textContent = "Nahrávám… záznam ukončíš tlačítkem Ukončit záznam.";
      syncControls();
    } catch (error) {
      voiceStarting = false;
      voiceRecorder = null;
      voiceRecording = false;
      releaseVoiceStream();
      syncControls();
      voiceStatus.textContent = `Mikrofon se nepodařilo spustit: ${error.message || error}`;
    }
  }

  function stopVoiceRecording() {
    if (!voiceRecorder || voiceRecorder.state !== "recording") return;
    voiceStatus.textContent = "Ukončuji záznam…";
    voiceRecorder.stop();
  }

  async function transcribeVoiceRecording() {
    const recorder = voiceRecorder;
    const blob = new Blob(voiceChunks, {type:(recorder && recorder.mimeType) || "audio/webm"});
    voiceRecorder = null;
    voiceChunks = [];
    voiceRecording = false;
    releaseVoiceStream();
    if (!blob.size) {
      voiceStatus.textContent = "Nahrávka je prázdná. Rozepsaný text zůstal zachován.";
      syncControls();
      return;
    }
    voiceTranscribing = true;
    voiceStatus.textContent = "Přepisuji…";
    syncControls();
    try {
      const audioBase64 = await blobToBase64(blob);
      const payload = await api("/api/human-adam/transcribe", {
        method:"POST",
        body:JSON.stringify({audio_base64:audioBase64,mime_type:blob.type || "audio/webm",language:"cs"}),
      });
      if (!payload.ok) throw new Error(payload.message || "Přepis hlasu selhal.");
      insertTranscriptForReview(payload.text);
      voiceStatus.textContent = "Přepis je v poli. Můžeš ho opravit a odeslat tlačítkem Odeslat.";
    } catch (error) {
      voiceStatus.textContent = `Přepis hlasu selhal: ${error.message || error} Rozepsaný text zůstal zachován.`;
    } finally {
      voiceTranscribing = false;
      syncControls();
    }
  }

  function speechPlaybackSupported() {
    return Boolean(window.speechSynthesis && window.SpeechSynthesisUtterance);
  }

  function resetSpeechButton(button) {
    if (!button) return;
    button.textContent = "Přečíst odpověď";
    button.setAttribute("aria-pressed", "false");
  }

  function stopAnswerSpeech(showNotice=false) {
    const previousButton = activeSpeechButton;
    activeSpeechButton = null;
    activeSpeechUtterance = null;
    resetSpeechButton(previousButton);
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (showNotice) notice.textContent = "Čtení odpovědi zastaveno.";
  }

  function finishAnswerSpeech(utterance, message) {
    if (activeSpeechUtterance !== utterance) return;
    const previousButton = activeSpeechButton;
    activeSpeechButton = null;
    activeSpeechUtterance = null;
    resetSpeechButton(previousButton);
    notice.textContent = message;
  }

  function speakAnswer(text, button) {
    if (!speechPlaybackSupported()) {
      button.textContent = "Čtení nepodporováno";
      button.disabled = true;
      notice.textContent = "Tento prohlížeč nepodporuje systémové čtení odpovědi.";
      return;
    }
    if (activeSpeechButton === button) {
      stopAnswerSpeech(true);
      return;
    }
    stopAnswerSpeech(false);
    const utterance = new window.SpeechSynthesisUtterance(String(text || ""));
    utterance.lang = "cs-CZ";
    const czechVoice = window.speechSynthesis.getVoices().find(
      (voice) => /^cs(?:-|$)/i.test(String(voice.lang || ""))
    );
    if (czechVoice) utterance.voice = czechVoice;
    utterance.addEventListener("end", () => {
      finishAnswerSpeech(utterance, "Čtení odpovědi dokončeno.");
    }, {once:true});
    utterance.addEventListener("error", () => {
      finishAnswerSpeech(utterance, "Čtení odpovědi se nepodařilo dokončit.");
    }, {once:true});
    activeSpeechButton = button;
    activeSpeechUtterance = utterance;
    button.textContent = "Zastavit";
    button.setAttribute("aria-pressed", "true");
    notice.textContent = "Přehrávám Adamovu odpověď systémovým hlasem.";
    window.speechSynthesis.speak(utterance);
  }

  function copyAnswerFallback(text) {
    const field = document.createElement("textarea");
    field.value = String(text || "");
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    field.style.pointerEvents = "none";
    document.body.appendChild(field);
    field.focus();
    field.select();
    field.setSelectionRange(0, field.value.length);
    let copied = false;
    try {
      copied = Boolean(document.execCommand("copy"));
    } finally {
      field.remove();
    }
    return copied;
  }

  async function copyAnswer(text, button) {
    const answer = String(text || "");
    if (!answer) return;
    button.disabled = true;
    let copied = false;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
          await navigator.clipboard.writeText(answer);
          copied = true;
        } catch (_error) {
          copied = false;
        }
      }
      if (!copied) copied = copyAnswerFallback(answer);
      if (!copied) throw new Error("clipboard unavailable");
      notice.textContent = "Adamova odpověď je zkopírovaná.";
    } catch (_error) {
      notice.textContent = "Odpověď se nepodařilo zkopírovat. Označ její text ručně.";
    } finally {
      button.disabled = false;
    }
  }

  function answerSpeechControl(text) {
    const actions = document.createElement("div");
    actions.className = "reply-actions";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "reply-speech";
    button.textContent = speechPlaybackSupported() ? "Přečíst odpověď" : "Čtení nepodporováno";
    button.disabled = !speechPlaybackSupported();
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => speakAnswer(text, button));
    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.className = "reply-copy";
    copyButton.textContent = "Kopírovat";
    copyButton.setAttribute("aria-label", "Kopírovat Adamovu odpověď");
    copyButton.addEventListener("click", () => copyAnswer(text, copyButton));
    actions.append(button, copyButton);
    return actions;
  }

  function looksLikeImageGenerationRequest(text) {
    const value = String(text || "");
    const action = "(?:vytvoř|vytvor|vygeneruj|nakresli|udělej|udelej|navrhni)";
    const image = "(?:obrázek|obrazek|ilustraci|ilustrace|grafiku|vizuál|vizual)";
    return new RegExp(`\\b${action}\\b[\\s\\S]{0,120}\\b${image}\\b|\\b${image}\\b[\\s\\S]{0,120}\\b${action}\\b`, "i").test(value);
  }

  function imageCandidateStatus(candidate) {
    const labels = {
      prepared:trustedExternalGenerationEnabled
        ? "Připraveno ke generování v rámci trvalého souhlasu"
        : "Čeká na samostatné potvrzení generování",
      generated:"Vygenerovaná verze čeká na rozhodnutí",
      approved:"Tato verze je schválená · není publikovaná",
      rejected:"Tato verze je zamítnutá",
    };
    return labels[String(candidate && candidate.status || "")] || "Stav kandidáta nelze ověřit";
  }

  async function loadImageCandidates() {
    if (!imageGenerationEnabled) {
      imageCandidatesByMessage = new Map();
      if (lastSession) renderSession(lastSession);
      return;
    }
    if (imageCandidatesLoading) return;
    const requestedWorkstreamId = activeWorkstreamId;
    imageCandidatesLoading = true;
    try {
      const payload = await api("/api/human-adam/images");
      if (!payload.ok) throw new Error(payload.message || "Kandidáty obrázků nelze načíst.");
      if (requestedWorkstreamId !== activeWorkstreamId) return;
      const next = new Map();
      for (const candidate of Array.isArray(payload.candidates) ? payload.candidates : []) {
        const messageId = String(candidate.client_message_id || "");
        if (messageId) next.set(messageId, candidate);
      }
      imageCandidatesByMessage = next;
      if (lastSession) renderSession(lastSession);
    } catch (error) {
      notice.textContent = `Obrázkové karty nelze načíst: ${error.message}`;
    } finally {
      imageCandidatesLoading = false;
      if (requestedWorkstreamId !== activeWorkstreamId && imageGenerationEnabled) {
        void loadImageCandidates();
      }
    }
  }

  async function generateImageCandidate(candidate, button) {
    const parameters = candidate && candidate.parameters ? candidate.parameters : {};
    const summary = `${parameters.model || "model neuveden"} · ${parameters.size || "rozměr neuveden"} · kvalita ${parameters.quality || "neuvedena"}`;
    if (!trustedExternalGenerationEnabled && !window.confirm(`Placené generování obrázku?\n\n${candidate.prompt}\n\n${summary}\n\nVznikne pouze private kandidát; nic se nepublikuje ani nevloží do projektu.`)) return;
    button.disabled = true;
    notice.textContent = trustedExternalGenerationEnabled
      ? "Generuji obrazového kandidáta v rámci trvalého souhlasu…"
      : "Generuji potvrzeného obrazového kandidáta…";
    try {
      const payload = await api("/api/human-adam/images/generate", {
        method:"POST",
        body:JSON.stringify({
          candidate_id:candidate.candidate_id,
          confirmation:trustedExternalGenerationEnabled ? "" : candidate.confirmation_text,
        }),
      });
      if (!payload.ok) throw new Error(payload.message || "Generování obrázku selhalo.");
      notice.textContent = "Obrázek je připravený jako private kandidát. Není publikovaný ani vložený do projektu.";
      await loadImageCandidates();
    } catch (error) {
      notice.textContent = `Obrázek nebyl vygenerován: ${error.message}`;
    } finally {
      button.disabled = false;
    }
  }

  async function decideImageCandidate(candidate, decision, button) {
    const label = decision === "approve" ? "schválit" : "zamítnout";
    if (!window.confirm(`Opravdu ${label} pouze tuto verzi obrázku? Nic se nebude publikovat ani vkládat do projektu.`)) return;
    button.disabled = true;
    try {
      const payload = await api("/api/human-adam/images/decision", {
        method:"POST",
        body:JSON.stringify({candidate_id:candidate.candidate_id,decision}),
      });
      if (!payload.ok) throw new Error(payload.message || "Rozhodnutí se neuložilo.");
      notice.textContent = decision === "approve"
        ? "Tato verze je označená jako schválená. Nic dalšího se nestalo."
        : "Tato verze je označená jako zamítnutá.";
      await loadImageCandidates();
    } catch (error) {
      notice.textContent = `Rozhodnutí se neuložilo: ${error.message}`;
    } finally {
      button.disabled = false;
    }
  }

  function imageCandidateCard(candidate) {
    const card = document.createElement("section");
    card.className = "image-candidate-card";
    card.dataset.status = String(candidate.status || "unknown");
    const title = document.createElement("h3");
    title.textContent = `Obrázkový kandidát · verze ${Number(candidate.version || 1)}`;
    card.appendChild(title);
    if (candidate.image_url) {
      const image = document.createElement("img");
      image.className = "image-candidate-preview";
      image.src = `${candidate.image_url}&v=${encodeURIComponent(candidate.updated_at || "")}`;
      image.alt = "Náhled vygenerovaného obrazového kandidáta";
      image.loading = "lazy";
      card.appendChild(image);
    } else {
      const placeholder = document.createElement("div");
      placeholder.className = "image-candidate-placeholder";
      placeholder.textContent = "Náhled zadání · placené API ještě nebylo zavoláno";
      card.appendChild(placeholder);
    }
    const prompt = document.createElement("p");
    prompt.className = "image-candidate-prompt";
    prompt.textContent = String(candidate.prompt || "");
    card.appendChild(prompt);
    const parameters = candidate.parameters || {};
    const meta = document.createElement("p");
    meta.className = "image-candidate-meta";
    meta.textContent = `${imageCandidateStatus(candidate)} · ${parameters.model || "—"} · ${parameters.size || "—"} · kvalita ${parameters.quality || "—"}`;
    card.appendChild(meta);
    if (candidate.generation_note) {
      const note = document.createElement("p");
      note.className = "image-candidate-meta";
      note.textContent = candidate.generation_note;
      card.appendChild(note);
    }
    const actions = document.createElement("div");
    actions.className = "image-candidate-actions";
    if (candidate.status === "prepared") {
      const generateButton = document.createElement("button");
      generateButton.type = "button";
      generateButton.textContent = "Potvrdit generování";
      generateButton.addEventListener("click", () => generateImageCandidate(candidate, generateButton));
      actions.appendChild(generateButton);
    }
    if (candidate.image_url) {
      const open = document.createElement("a");
      open.className = "back";
      open.href = candidate.image_url;
      open.target = "_blank";
      open.rel = "noopener";
      open.textContent = "Otevřít náhled";
      actions.appendChild(open);
      const approve = document.createElement("button");
      approve.type = "button";
      approve.className = "approve";
      approve.textContent = "Schválit";
      approve.disabled = candidate.status !== "generated";
      approve.addEventListener("click", () => decideImageCandidate(candidate, "approve", approve));
      const reject = document.createElement("button");
      reject.type = "button";
      reject.className = "reject";
      reject.textContent = "Zamítnout";
      reject.disabled = candidate.status !== "generated";
      reject.addEventListener("click", () => decideImageCandidate(candidate, "reject", reject));
      actions.append(approve, reject);
    }
    card.appendChild(actions);
    return card;
  }

  async function prepareImageCandidate(requestText, clientMessageId) {
    if (!imageGenerationEnabled || !looksLikeImageGenerationRequest(requestText)) return true;
    try {
      const payload = await api("/api/human-adam/images/prepare", {
        method:"POST",
        body:JSON.stringify({request_text:requestText,client_message_id:clientMessageId}),
      });
      if (!payload.ok) throw new Error(payload.message || "Náhled zadání obrázku nelze připravit.");
      return true;
    } catch (error) {
      notice.textContent = `Adam odpověděl, ale obrázkový náhled nevznikl: ${error.message}`;
      return false;
    }
  }

  function bubble(text, className, meta, spokenText="", imageCandidate=null) {
    const node = document.createElement("article");
    node.className = `bubble ${className}`;
    node.textContent = text;
    const small = document.createElement("span");
    small.className = "meta";
    small.textContent = meta;
    node.appendChild(small);
    if (spokenText) node.appendChild(answerSpeechControl(spokenText));
    if (imageCandidate) node.appendChild(imageCandidateCard(imageCandidate));
    return node;
  }

  function renderSession(session) {
    stopAnswerSpeech(false);
    lastSession = session || null;
    chat.replaceChildren();
    const messages = session && Array.isArray(session.messages) ? session.messages : [];
    for (const item of messages) {
      const exchange = document.createElement("div");
      exchange.className = "exchange";
      exchange.appendChild(bubble(item.user_text || "", "human", `Odesláno ${formatTime(item.client_sent_at || item.received_at)}`));
      const confirmed = item.delivery_confirmed ? "Doručení potvrzeno" : (item.status === "delivery_unknown" ? "Doručení nejisté – neposílat automaticky znovu" : "Zpracování nedokončeno");
      if (item.answer) exchange.appendChild(bubble(item.answer, "adam", `Adam · ${formatTime(item.completed_at)} · ${confirmed}`, item.answer, imageCandidatesByMessage.get(String(item.client_message_id || "")) || null));
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

  function workspaceRequiresWorkDetail(workspace) {
    if (!workspace || typeof workspace !== "object" || !("workspace_relation" in workspace)) return true;
    const relation = String(workspace.workspace_relation || "unknown");
    return Boolean(
      workspace.ok === false
      || workspace.prepared === false
      || workspace.ready === false
      || workspace.has_git_remote
      || workspace.dirty
      || workspace.sync_available
      || workspace.source_update_available
      || Number(workspace.source_pending_changes || 0) > 0
      || workspace.local_checkpoint_ahead
      || workspace.local_checkpoint_preserved
      || relation !== "aligned"
    );
  }

  function renderCompactWorkStatus(workspace) {
    const needsAttention = workspaceRequiresWorkDetail(workspace);
    const changeCount = Number(workspace && workspace.change_count || 0);
    const liveDeployment = activeWorkstreamLiveDeployment();
    const deploymentCurrent = String(liveDeployment.state || "") === "verified_current";
    const deployedMain = String(liveDeployment.main_short || "").trim();
    const deployedSmokeCount = Number(liveDeployment.smoke_count || 0);
    workOpenBtn.classList.toggle(
      "work-clean",
      !needsAttention && (!workstreamDeploymentEnabled || deploymentCurrent),
    );
    workOpenBtn.classList.toggle("work-attention", needsAttention);
    if (workspace && workspace.dirty) {
      workOpenBtn.textContent = `Práce: ${changeCount} změn`;
      workOpenBtn.title = "Workspace obsahuje rozpracované změny; otevři detail.";
    } else if (needsAttention) {
      workOpenBtn.textContent = "Práce: kontrola";
      workOpenBtn.title = "Pracovní stav vyžaduje kontrolu; otevři detail.";
    } else if (workstreamDeploymentEnabled && deploymentCurrent) {
      workOpenBtn.textContent = "Práce: nasazeno ✓";
      workOpenBtn.title = `Cockpit běží na aktuálním main${deployedMain ? ` ${deployedMain}` : ""} · smoke ${deployedSmokeCount}/5.`;
    } else if (workstreamDeploymentEnabled) {
      workOpenBtn.textContent = "Práce: nasazení";
      workOpenBtn.title = "Workspace je čistý a tento pracovní proud podporuje nasazení.";
    } else {
      workOpenBtn.textContent = "Práce: čistá";
      workOpenBtn.title = "Workspace je čistý a synchronní s main; velký detail není potřeba.";
    }
    workOpenBtn.setAttribute("aria-label", workOpenBtn.title);
  }

  function activeWorkstreamLiveDeployment() {
    if (
      !currentWorkstreamLiveStatus
      || String(currentWorkstreamLiveStatus.workstream_id || "") !== activeWorkstreamId
      || !currentWorkstreamLiveStatus.deployment
      || typeof currentWorkstreamLiveStatus.deployment !== "object"
    ) {
      return {};
    }
    return currentWorkstreamLiveStatus.deployment;
  }

  function renderStepCompletion(status) {
    const valid = Boolean(
      status
      && typeof status === "object"
      && status.schema_version === 1
      && status.server_authoritative === true
    );
    const state = valid ? String(status.state || "unverified") : "unverified";
    const checkpoint = valid ? String(status.checkpoint_short || "").trim() : "";
    const pendingCount = valid ? Number(status.pending_remote_commit_count || 0) : 0;
    const deploymentState = valid ? String(status.deployment_state || "unknown") : "unknown";
    stepCompletionReceipt.className = "";
    if (state === "none") {
      stepCompletionReceipt.textContent = "";
      stepCompletionReceipt.hidden = true;
      return;
    }
    if (state === "checkpoint_completed") {
      const remote = status.remote_push_deferred === true
        ? ` · GitHub balíček čeká (${pendingCount})`
        : "";
      const deployment = deploymentState === "verified_current"
        ? " · nasazeno"
        : " · nasazení čeká";
      stepCompletionReceipt.textContent = `Vývoj dokončen ✓ · Git checkpoint ${checkpoint || "ověřen"}${remote}${deployment}`;
    } else if (state === "no_changes_completed") {
      stepCompletionReceipt.textContent = "Poradní tah dokončen ✓ · bez změn souborů";
    } else if (state === "turn_started" || state === "receipt_accepted") {
      stepCompletionReceipt.classList.add("running");
      stepCompletionReceipt.textContent = state === "receipt_accepted"
        ? "Účtenka přijata · server dokončuje kontrolní bránu a checkpoint"
        : "Zapisovací tah běží · server čeká na výsledek";
    } else if (state === "integration_deferred") {
      stepCompletionReceipt.classList.add("warn");
      stepCompletionReceipt.textContent = "Vývoj je zachovaný, ale integrace čeká na potvrzené převzetí";
    } else {
      stepCompletionReceipt.classList.add("warn");
      const labels = {
        delivery_uncertain: "Doručení výsledku je nejisté",
        turn_failed: "Zapisovací tah nedoběhl",
        receipt_missing: "Chybí dokončovací účtenka",
        receipt_invalid: "Dokončovací účtenka je neplatná",
        checkpoint_failed: "Checkpoint se nedokončil",
        attention_required: "Výsledek checkpointu neodpovídá aktuálnímu Git stavu",
        unverified: "Výsledek posledního vývoje nelze serverově ověřit",
      };
      stepCompletionReceipt.textContent = `Vývoj vyžaduje kontrolu · ${labels[state] || "stav není ověřený"}`;
    }
    stepCompletionReceipt.hidden = false;
  }

  function renderStatus(payload) {
    renderWorkstreams(payload);
    const session = payload && payload.session ? payload.session : null;
    const connected = Boolean(session && session.connected && payload.runtime && payload.runtime.reachable);
    sessionConnected = connected;
    if (!connected) writeIntentArmed = false;
    connectionBadge.textContent = connected ? "Připojeno" : "Odpojeno";
    connectionBadge.className = connected ? "badge ok" : "badge warn";
    profileBadge.textContent = `Proud: ${activeWorkstreamLabel}`;
    profileBadge.dataset.backend = activeWorkstreamBackend;
    const thread = session && session.thread_id ? session.thread_id : "";
    if (threadRotationAudit && String(threadRotationAudit.thread_id || "") !== thread) {
      resetThreadRotationState("Aktivní vlákno se změnilo. Před další rotací spusť novou kontrolu.");
    }
    threadBadge.textContent = `Relace: ${thread ? thread.slice(0,8) : "—"}`;
    const workspace = payload && payload.workspace ? payload.workspace : {};
    const workspaceDiverged = workspace.workspace_relation === "diverged";
    const checkpointPreserved = workspaceDiverged && workspace.local_checkpoint_preserved === true;
    if (workspace.has_git_remote) workspaceBadge.textContent = "POZOR: Git remote";
    else if (checkpointPreserved) workspaceBadge.textContent = `WIP zachován: ${workspace.local_commit_count} · nutná obnova`;
    else if (workspaceDiverged) workspaceBadge.textContent = "Workspace rozvětvený · nutná kontrola";
    else if (workspace.sync_available) workspaceBadge.textContent = "Workspace čeká na sync";
    else if (workspace.dirty) workspaceBadge.textContent = `Workspace: ${workspace.change_count} změn`;
    else if (workspace.local_checkpoint_ahead) workspaceBadge.textContent = `WIP checkpoint: ${workspace.local_commit_count}`;
    else workspaceBadge.textContent = "Workspace čistý";
    workspaceBadge.className = workspace.has_git_remote || workspaceDiverged || workspace.sync_available || workspace.dirty || workspace.local_checkpoint_ahead ? "badge warn" : "badge";
    renderCompactWorkStatus(workspace);
    renderStepCompletion(payload && payload.last_step_completion ? payload.last_step_completion : null);
    renderDevelopmentBadge(payload && payload.development_semaphore ? payload.development_semaphore : null);
    const deployment = verifiedDeploymentRecord(
      payload && payload.last_simple_main_deployment
        ? payload.last_simple_main_deployment
        : null
    );
    const sourceHeadShort = String(workspace.source_head_short || "").trim().toLowerCase();
    const mainShort = /^[0-9a-f]{12}$/.test(sourceHeadShort) ? sourceHeadShort : "";
    const deploymentCurrent = Boolean(
      deployment && mainShort && deployment.main_short === mainShort
    );
    if (deployment && mainShort && !deploymentCurrent) {
      deploymentReceipt.textContent = `Git/main ${mainShort} · běžící Cockpit ${deployment.main_short} · nový commit čeká na nasazení do Cockpitu`;
    } else if (deployment && deploymentCurrent) {
      const validation = deployment.gate_mode === "quick"
        ? "rychlá lokální brána"
        : `${deployment.test_count} testů`;
      deploymentReceipt.textContent = `Git/main i běžící Cockpit ${mainShort} · ${validation} · smoke ${deployment.smoke_count}/5 · ${formatTime(deployment.deployed_at)}`;
    } else if (deployment) {
      deploymentReceipt.textContent = `Běžící Cockpit ${deployment.main_short} · aktuální Git/main nelze ověřit`;
    } else {
      deploymentReceipt.textContent = "";
    }
    deploymentReceipt.classList.toggle("stale", Boolean(deployment && !deploymentCurrent));
    deploymentReceipt.hidden = !deployment;
    renderTurnState(session);
    renderSession(session);
    void loadImageCandidates();
  }

  function renderDevelopmentBadge(semaphore) {
    if (!semaphore || semaphore.ok !== true) {
      developmentBadge.textContent = "Vývoj: stav neověřen";
      developmentBadge.className = "badge warn";
      return;
    }
    if (!semaphore.active) {
      developmentBadge.textContent = "Vývoj: volno";
      developmentBadge.className = "badge ok";
      return;
    }
    const mode = semaphore.mode === "paused" ? "pozastaven" : "aktivní";
    developmentBadge.textContent = `Vývoj: ${semaphore.owner_label || semaphore.owner_id} · ${mode}`;
    developmentBadge.className = semaphore.mode === "active" ? "badge" : "badge warn";
  }

  function renderWorkstreams(payload) {
    const selection = payload && payload.workstream_selection ? payload.workstream_selection : {};
    const capabilities = payload && payload.workstream_capabilities ? payload.workstream_capabilities : {};
    const generationConsent = payload && payload.trusted_external_generation ? payload.trusted_external_generation : {};
    const activeWorkstream = selection && selection.active ? selection.active : {};
    const workstreams = selection && Array.isArray(selection.workstreams) ? selection.workstreams : [];
    const nextWorkstreamId = String(activeWorkstream.workstream_id || "");
    if (activeWorkstreamId && nextWorkstreamId !== activeWorkstreamId) {
      writeIntentArmed = false;
    }
    activeWorkstreamLabel = String(activeWorkstream.workstream_name || "Pracovní proud");
    workstreamDevelopmentEnabled = capabilities.development !== false;
    workstreamDeploymentEnabled = capabilities.deployment !== false;
    imageGenerationEnabled = capabilities.image_generation === true;
    renderTrustedExternalGeneration(generationConsent);
    privateArchiveHelp.hidden = capabilities.private_archive_direct !== true;
    activeWorkstreamId = nextWorkstreamId;
    activeWorkstreamBackend = String(activeWorkstream.backend || "lazy_private_thread");
    profileSelect.replaceChildren();
    const appendOption = (parent, profile) => {
      const option = document.createElement("option");
      option.value = String(profile.id || "");
      option.dataset.backend = String(profile.backend || "compatibility_adapter");
      option.textContent = String(profile.name || profile.id || "Pracovní proud");
      option.disabled = profile.available === false;
      option.selected = option.value === activeWorkstreamId;
      parent.appendChild(option);
    };
    const groups = Array.isArray(selection.groups) ? selection.groups : [];
    for (const group of groups) {
      const rows = Array.isArray(group.workstreams) ? group.workstreams : [];
      if (!rows.length) continue;
      const optionGroup = document.createElement("optgroup");
      optionGroup.label = String(group.label || group.id || "Pracovní proudy");
      for (const workstream of rows) appendOption(optionGroup, workstream);
      profileSelect.appendChild(optionGroup);
    }
    const paused = Array.isArray(selection.paused) ? selection.paused : [];
    if (paused.length) {
      const optionGroup = document.createElement("optgroup");
      optionGroup.label = "Pozastavené";
      for (const workstream of paused) appendOption(optionGroup, workstream);
      profileSelect.appendChild(optionGroup);
    }
    syncControls();
  }

  function renderTrustedExternalGeneration(consent) {
    const status = consent && typeof consent === "object" ? consent : {};
    trustedExternalGenerationEnabled = status.enabled === true
      && status.state === "active"
      && status.consent_id === "trusted_external_generation_v1";
    trustedExternalGenerationGrantText = String(status.grant_confirmation_text || "");
    trustedExternalGenerationRevokeText = String(status.revoke_confirmation_text || "");
    trustedExternalGenerationBox.dataset.state = trustedExternalGenerationEnabled ? "verified" : "unverified";
    trustedExternalGenerationMeta.textContent = trustedExternalGenerationEnabled
      ? "Aktivní pro registrované generátory a pouze veřejný, smyšlený nebo jiný necitlivý obsah. Nezahrnuje publikování, Git push ani nasazení."
      : "Neaktivní. Generativní služby dál vyžadují vlastní potvrzení nebo zůstávají blokované.";
    trustedExternalGenerationBtn.textContent = trustedExternalGenerationEnabled
      ? "Odvolat trvalý souhlas"
      : "Aktivovat trvalý souhlas";
    const required = trustedExternalGenerationEnabled
      ? trustedExternalGenerationRevokeText
      : trustedExternalGenerationGrantText;
    trustedExternalGenerationConfirmation.textContent = required
      ? `Přesná věta: ${required}`
      : "Potvrzovací větu nelze bezpečně načíst.";
    trustedExternalGenerationInput.value = "";
    syncTrustedExternalGenerationControl();
  }

  function syncTrustedExternalGenerationControl() {
    const required = trustedExternalGenerationEnabled
      ? trustedExternalGenerationRevokeText
      : trustedExternalGenerationGrantText;
    trustedExternalGenerationBtn.disabled = !required
      || trustedExternalGenerationInput.value.trim() !== required;
  }

  async function changeTrustedExternalGeneration() {
    const operation = trustedExternalGenerationEnabled ? "revoke" : "grant";
    const required = trustedExternalGenerationEnabled
      ? trustedExternalGenerationRevokeText
      : trustedExternalGenerationGrantText;
    if (!required) return;
    const entered = trustedExternalGenerationInput.value.trim();
    if (entered.trim() !== required) {
      trustedExternalGenerationMeta.textContent = "Potvrzovací věta nesouhlasí; stav se nezměnil.";
      return;
    }
    trustedExternalGenerationBtn.disabled = true;
    try {
      const payload = await api("/api/human-adam/trusted-external-generation", {
        method:"POST",
        body:JSON.stringify({operation,confirmation:entered.trim()}),
      });
      if (!payload.ok) throw new Error(payload.message || "Stav souhlasu se nepodařilo změnit.");
      renderTrustedExternalGeneration(payload.trusted_external_generation || {});
      notice.textContent = payload.message || "Stav trvalého souhlasu byl změněn.";
    } catch (error) {
      trustedExternalGenerationMeta.textContent = `Stav souhlasu se nezměnil: ${error.message}`;
    } finally {
      syncTrustedExternalGenerationControl();
    }
  }

  function showProfileSwitchFailure(message) {
    notice.textContent = message;
    notice.scrollIntoView({block:"nearest",behavior:"smooth"});
  }

  async function switchProfile() {
    if (busy || sendInFlight || sessionTurnBusy) return;
    const targetId = profileSelect.value;
    const targetOption = profileSelect.options[profileSelect.selectedIndex];
    const targetLabel = targetOption?.textContent || targetId;
    if (!targetId || targetId === activeWorkstreamId) return;
    if (input.value.trim()) {
      showProfileSwitchFailure("Nejdřív odešli nebo odstraň rozepsaný pokyn; proud jsem nepřepnul.");
      profileSelect.value = activeWorkstreamId;
      return;
    }
    if (!window.confirm(`Přepnout pracovní proud na „${targetLabel}“?\n\nBezpečně se přepne vlákno, pracovní kontext, handoff a TVBCP; sdílený workspace se předem ověří a synchronizuje.`)) {
      profileSelect.value = activeWorkstreamId;
      return;
    }
    setWriteIntentArmed(false);
    setBusy(true, `Přepínám pracovní proud na ${targetLabel}…`);
    stopAnswerSpeech(false);
    tvbcpPanel.hidden = true;
    threadRotationPanel.hidden = true;
    workPanel.hidden = true;
    deploymentAudit = null;
    try {
      const payload = await api("/api/human-adam/profile", {
        method:"POST",
        body:JSON.stringify({workstream_id:targetId,confirmed:true}),
      });
      if (!payload.ok) throw new Error(payload.message || "Přepnutí profilu selhalo.");
      resetThreadRotationState();
      renderStatus(payload);
      notice.textContent = `Aktivní pracovní proud: ${activeWorkstreamLabel}.`;
    } catch (error) {
      showProfileSwitchFailure(`Pracovní proud nebyl přepnut: ${error.message}`);
      await loadStatus();
    } finally { setBusy(false); }
  }

  async function api(path, options={}) {
    const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || "HTTP požadavek selhal.");
    return payload;
  }

  async function loadStatus() {
    if (busy) return null;
    setBusy(true, "Načítám stav…");
    try {
      const payload = await api("/api/human-adam/status");
      renderStatus(payload);
      notice.textContent = payload.ok ? "" : (payload.message || "Human–Adam zatím není připravený.");
      return payload;
    } catch (error) {
      notice.textContent = `Stav nelze načíst: ${error.message}`;
      return null;
    }
    finally { setBusy(false); }
  }

  function resultWatchTargetId() {
    const activeTurn = lastSession && lastSession.active_turn ? lastSession.active_turn : {};
    const activeId = String(activeTurn.client_message_id || "");
    if (activeId) return activeId;
    const messages = lastSession && Array.isArray(lastSession.messages) ? lastSession.messages : [];
    const latest = messages.length ? messages[messages.length - 1] : null;
    if (!latest || !["pending", "delivery_unknown"].includes(String(latest.status || ""))) return "";
    return String(latest.client_message_id || "");
  }

  function stopResultWatch() {
    if (resultWatchTimerId !== null) window.clearTimeout(resultWatchTimerId);
    resultWatchTimerId = null;
    resultWatchActive = false;
    resultWatchClientMessageId = "";
    resultWatchAttempt = 0;
    syncControls();
  }

  function scheduleResultWatch() {
    if (!resultWatchActive) return;
    const delay = Math.min(RESULT_WATCH_MAX_DELAY_MS, 3000 + resultWatchAttempt * 2000);
    resultWatchTimerId = window.setTimeout(checkResultWatch, delay);
  }

  async function checkResultWatch() {
    if (!resultWatchActive) return;
    resultWatchTimerId = null;
    resultWatchAttempt += 1;
    try {
      const payload = await api("/api/human-adam/status");
      const session = payload && payload.session ? payload.session : null;
      const messages = session && Array.isArray(session.messages) ? session.messages : [];
      const watched = messages.find((item) => String(item.client_message_id || "") === resultWatchClientMessageId) || null;
      const activeTurn = session && session.active_turn ? session.active_turn : {};
      const activeId = String(activeTurn.client_message_id || "");
      if (watched && String(watched.status || "") === "completed") {
        renderStatus(payload);
        stopResultWatch();
        notice.textContent = "Výsledek byl načten bez opakovaného odeslání pokynu.";
        playCompletionMediaSound();
        return;
      }
      if (watched && String(watched.status || "") === "delivery_unknown") {
        renderStatus(payload);
        stopResultWatch();
        notice.textContent = "Stav doručení zůstává nejistý. Pokyn neposílej znovu.";
        return;
      }
      if (activeId && activeId !== resultWatchClientMessageId) {
        renderStatus(payload);
        stopResultWatch();
        notice.textContent = "Aktivní tah se změnil; kontrolu výsledku jsem bezpečně zastavil.";
        return;
      }
      lastSession = session || lastSession;
      renderTurnState(session);
      if (resultWatchAttempt >= RESULT_WATCH_MAX_ATTEMPTS) {
        stopResultWatch();
        notice.textContent = "Výsledek zatím nebyl potvrzen. Pokyn neposílej znovu; stav můžeš zkontrolovat znovu.";
        return;
      }
      notice.textContent = "Čekám na výsledek a pouze ověřuji stav; pokyn znovu neposílám.";
      scheduleResultWatch();
    } catch (error) {
      if (resultWatchAttempt >= RESULT_WATCH_MAX_ATTEMPTS) {
        stopResultWatch();
        notice.textContent = `Výsledek se nepodařilo ověřit: ${error.message} Pokyn neposílej znovu.`;
        return;
      }
      notice.textContent = `Kontrola stavu se přerušila: ${error.message} Zkusím ji znovu bez odeslání pokynu.`;
      scheduleResultWatch();
    }
  }

  function startResultWatch() {
    if (busy || resultWatchActive) return;
    const targetId = resultWatchTargetId();
    if (!targetId) {
      loadStatus();
      return;
    }
    resultWatchActive = true;
    resultWatchClientMessageId = targetId;
    resultWatchAttempt = 0;
    notice.textContent = "Čekám na výsledek a pouze ověřuji stav; pokyn znovu neposílám.";
    syncControls();
    checkResultWatch();
  }

  function handleRefreshStatus() {
    if (sessionTurnBusy || deliveryUncertain || sendInFlight) startResultWatch();
    else loadStatus();
  }

  async function connect() {
    if (busy) return;
    setBusy(true, "Připojuji kanonickou relaci…");
    try {
      const payload = await api("/api/human-adam/connect", {method:"POST", body:"{}"});
      if (!payload.ok) throw new Error(payload.message || "Připojení selhalo.");
      renderStatus(payload);
      notice.textContent = payload.workspace_synced
        ? "Workspace byl bezpečně aktualizovaný z main a kanonická relace je připravená."
        : "Kanonická relace je připravená.";
      input.focus();
    } catch (error) { notice.textContent = `Připojení selhalo: ${error.message}`; }
    finally { setBusy(false); }
  }

  function scrollTvbcpToEnd() {
    const applyEndPosition = () => {
      tvbcpScroll.scrollTop = tvbcpScroll.scrollHeight;
      tvbcpEnd.scrollIntoView({block:"end",inline:"nearest",behavior:"auto"});
    };
    requestAnimationFrame(() => {
      requestAnimationFrame(applyEndPosition);
    });
    window.setTimeout(applyEndPosition, 120);
  }

  function resetThreadRotationState(message="Spusť kontrolu připravenosti. Staré vlákno se nemaže ani nearchivuje.") {
    threadRotationAudit = null;
    threadRotationConfirmation.value = "";
    threadRotationConfirmation.hidden = true;
    threadRotationConfirmation.disabled = true;
    threadRotationBtn.hidden = true;
    threadRotationBtn.disabled = true;
    threadRotationMeta.textContent = message;
    syncControls();
  }

  function openThreadRotation() {
    tvbcpPanel.hidden = true;
    workPanel.hidden = true;
    threadRotationPanel.hidden = false;
  }

  function closeThreadRotation() {
    threadRotationPanel.hidden = true;
  }

  function renderThreadRotationAudit(payload) {
    const blockers = payload && Array.isArray(payload.blockers) ? payload.blockers.filter(Boolean) : [];
    if (!payload || payload.ok !== true) {
      resetThreadRotationState(payload && payload.message ? payload.message : "Kontrolu rotace nelze načíst.");
      return;
    }
    if (payload.ready !== true) {
      resetThreadRotationState(`Rotace zatím není připravená: ${blockers.join(" ") || "zkontroluj připojení a stav relace."}`);
      return;
    }
    threadRotationAudit = payload;
    const messages = Number(payload.thread_message_count || 0);
    const rotations = Number(payload.rotation_count || 0);
    const required = String(payload.confirmation_text || "");
    threadRotationMeta.textContent = `Připraveno · aktuální vlákno má ${messages} zpráv · dosavadní rotace: ${rotations}. Staré vlákno zůstane zachované a nearchivované. Vlož přesně: ${required}`;
    threadRotationConfirmation.value = "";
    threadRotationConfirmation.hidden = false;
    threadRotationConfirmation.disabled = false;
    threadRotationBtn.hidden = false;
    syncControls();
  }

  async function auditThreadRotation() {
    if (threadRotationAuditBtn.disabled) return;
    setBusy(true, "Ověřuji připojení, stav tahu a doručení…");
    threadRotationMeta.textContent = "Kontroluji připravenost nového profilového vlákna…";
    try {
      const payload = await api("/api/human-adam/thread-rotation");
      renderThreadRotationAudit(payload);
      notice.textContent = payload.ready === true
        ? "Rotace je připravená; nové vlákno vznikne až po přesné potvrzovací větě."
        : "Rotace nebyla provedena. Nejdřív vyřeš uvedené podmínky.";
    } catch (error) {
      resetThreadRotationState(`Kontrola rotace selhala: ${error.message}`);
    } finally { setBusy(false); }
  }

  async function rotateProfileThread() {
    if (threadRotationBtn.disabled || !threadRotationAudit) return;
    const required = String(threadRotationAudit.confirmation_text || "");
    const confirmation = threadRotationConfirmation.value.trim();
    if (!required || confirmation !== required) {
      threadRotationMeta.textContent = "Potvrzovací věta nesouhlasí; vlákno nebylo změněno.";
      return;
    }
    const expectedThreadId = String(threadRotationAudit.thread_id || "");
    setBusy(true, "Zakládám nové profilové vlákno; původní zůstává zachované…");
    let rotated = null;
    try {
      const payload = await api("/api/human-adam/thread-rotation", {
        method:"POST",
        body:JSON.stringify({confirmation,expected_thread_id:expectedThreadId}),
      });
      if (!payload.ok || payload.rotated !== true || payload.previous_thread_preserved !== true) {
        throw new Error(payload.message || "Rotace vlákna nebyla potvrzena.");
      }
      rotated = payload;
      resetThreadRotationState("Nové profilové vlákno bylo založeno; staré vlákno zůstalo zachované.");
    } catch (error) {
      resetThreadRotationState(`Vlákno nebylo změněno: ${error.message}`);
    } finally { setBusy(false); }
    if (rotated) {
      await loadStatus();
      threadRotationMeta.textContent = "Nové profilové vlákno je aktivní; staré vlákno zůstalo zachované.";
      notice.textContent = "Rotace dokončena bez odeslání zprávy a bez smazání starého vlákna.";
    }
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
      const initializationState = payload.initialized === false
        ? "Dosud neinicializováno · pouze pro čtení"
        : `změněno ${formatTime(payload.modified_at)}`;
      tvbcpMeta.textContent = `Pracovní TVBCP · ${workState}${syncState} · ${initializationState}`;
      scrollTvbcpToEnd();
    } catch (error) {
      tvbcpContent.textContent = "";
      tvbcpMeta.textContent = `TVBCP nelze načíst: ${error.message}`;
    } finally { tvbcpRefreshBtn.disabled = false; }
  }

  function openTvbcp() {
    threadRotationPanel.hidden = true;
    workPanel.hidden = true;
    tvbcpPanel.hidden = false;
    loadTvbcp();
  }

  function closeTvbcp() {
    tvbcpPanel.hidden = true;
  }

  function renderPendingIntegrationAudit(audit) {
    const valid = audit && typeof audit === "object" && audit.ok === true;
    const state = valid ? String(audit.state || "") : "audit_unavailable";
    const canIntegrate = valid
      && state === "ready_for_confirmed_integration"
      && audit.can_integrate === true
      && audit.ownership_marker_verified === true
      && Boolean(String(audit.confirmation_text || "").trim());
    const canRecover = valid
      && state === "owned_wip_missing_metadata"
      && audit.can_recover === true
      && audit.ownership_marker_verified === true
      && audit.metadata_required === true
      && Boolean(String(audit.confirmation_text || "").trim());
    pendingIntegrationAudit = canIntegrate ? audit : null;
    pendingIntegrationRecovery = canRecover ? audit : null;
    integrationAuditBox.hidden = state === "not_applicable";
    integrationAuditBox.className = "integration-audit-box";
    if (
      state === "waiting_source_clean"
      || state === "source_advanced_service_decision"
    ) {
      integrationAuditBox.classList.add("warn");
    } else if (
      state === "not_pending"
      || canIntegrate
      || canRecover
    ) {
      integrationAuditBox.classList.add("ready");
    } else {
      integrationAuditBox.classList.add("blocked");
    }
    const label = valid ? String(audit.label || "Audit bez popisu") : "Audit čekající integrace není dostupný";
    const message = valid ? String(audit.message || "") : "Stav nelze bezpečně ověřit.";
    const nextStep = valid ? String(audit.next_step || "") : "Nic neintegruj.";
    integrationAuditMeta.textContent = `${label} · ${message}${nextStep ? ` Další krok: ${nextStep}` : ""}`;
    integrationAuditPaths.replaceChildren();
    const paths = valid && Array.isArray(audit.overlap_paths) ? audit.overlap_paths : [];
    if (state === "source_advanced_service_decision") {
      if (!paths.length) {
        const row = document.createElement("li");
        row.textContent = "Audit nenašel přesný překryv cest; servisní rozhodnutí je přesto povinné.";
        integrationAuditPaths.appendChild(row);
      } else {
        for (const path of paths) {
          const row = document.createElement("li");
          row.textContent = String(path || "");
          integrationAuditPaths.appendChild(row);
        }
      }
    }
    integrationAuditPaths.hidden = !integrationAuditPaths.children.length;
    integrationRecoveryFields.hidden = !canRecover;
    integrationRecoveryCommit.value = "";
    integrationRecoverySummary.value = "";
    integrationRecoveryNextStep.value = "";
    integrationRecoveryFields.querySelectorAll("input").forEach((field) => {
      field.disabled = !canRecover;
    });
    integrationConfirmation.value = "";
    integrationConfirmation.placeholder = canIntegrate || canRecover
      ? String(audit.confirmation_text)
      : "Potvrzovací věta";
    integrationConfirmation.hidden = !canIntegrate && !canRecover;
    integrationConfirmation.disabled = !canIntegrate && !canRecover;
    integrationBtn.hidden = !canIntegrate;
    integrationBtn.disabled = true;
    integrationRecoveryBtn.hidden = !canRecover;
    integrationRecoveryBtn.disabled = true;
  }

  async function integrateDeferredChanges() {
    if (integrationBtn.disabled || !pendingIntegrationAudit) return;
    const required = String(pendingIntegrationAudit.confirmation_text || "").trim();
    const confirmation = integrationConfirmation.value.trim();
    if (!required || confirmation !== required) {
      integrationAuditMeta.textContent = "Potvrzovací věta nesouhlasí; nic nebylo integrováno.";
      return;
    }
    integrationConfirmation.disabled = true;
    integrationBtn.disabled = true;
    integrationAuditMeta.textContent = "Ověřuji marker, společný základ a přesný WIP…";
    try {
      const payload = await api("/api/human-adam/deferred-integration", {
        method:"POST",
        body:JSON.stringify({confirmation}),
      });
      if (!payload.ok) {
        const failure = payload.message || "Integrační brána selhala.";
        await loadWork();
        integrationAuditMeta.textContent = `Nic nebylo integrováno: ${failure}`;
        return;
      }
      await loadWork();
      const remote = payload.remote_push_deferred
        ? " GitHub čeká na denní balíček."
        : " Commit je pushnutý.";
      notice.textContent = `Odložený WIP je v main jako ${payload.checkpoint_short || "nový checkpoint"}.${remote} Nasazení zůstává samostatný krok.`;
    } catch (error) {
      await loadWork();
      integrationAuditMeta.textContent = `Stav integrace nelze potvrdit: ${error.message}`;
    }
  }

  function syncIntegrationRecoveryAction() {
    const audit = pendingIntegrationRecovery || pendingIntegrationAudit;
    const required = audit ? String(audit.confirmation_text || "").trim() : "";
    const confirmed = Boolean(required && integrationConfirmation.value.trim() === required);
    integrationBtn.disabled = !pendingIntegrationAudit || !confirmed;
    integrationRecoveryBtn.disabled = !pendingIntegrationRecovery
      || !confirmed
      || !integrationRecoveryCommit.value.trim()
      || !integrationRecoverySummary.value.trim()
      || !integrationRecoveryNextStep.value.trim();
  }

  async function recoverOwnedChanges() {
    if (integrationRecoveryBtn.disabled || !pendingIntegrationRecovery) return;
    const required = String(pendingIntegrationRecovery.confirmation_text || "").trim();
    const confirmation = integrationConfirmation.value.trim();
    if (!required || confirmation !== required) {
      integrationAuditMeta.textContent = "Potvrzovací věta nesouhlasí; nic nebylo integrováno.";
      return;
    }
    integrationRecoveryFields.querySelectorAll("input").forEach((field) => { field.disabled = true; });
    integrationConfirmation.disabled = true;
    integrationRecoveryBtn.disabled = true;
    integrationAuditMeta.textContent = "Ověřuji předběžný marker, přesný WIP a úplnou testovací bránu…";
    try {
      const payload = await api("/api/human-adam/owned-wip-recovery", {
        method:"POST",
        body:JSON.stringify({
          confirmation,
          commit_message:integrationRecoveryCommit.value.trim(),
          summary:integrationRecoverySummary.value.trim(),
          next_step:integrationRecoveryNextStep.value.trim(),
        }),
      });
      if (!payload.ok) {
        const failure = payload.message || "Recovery vlastněného WIP selhala.";
        await loadWork();
        integrationAuditMeta.textContent = `Nic nebylo integrováno: ${failure}`;
        return;
      }
      await loadWork();
      const remote = payload.remote_push_deferred
        ? " GitHub čeká na denní balíček."
        : " Commit je pushnutý.";
      notice.textContent = `Vlastněný WIP je v main jako ${payload.checkpoint_short || "nový checkpoint"}.${remote} Nasazení zůstává samostatný krok.`;
    } catch (error) {
      await loadWork();
      integrationAuditMeta.textContent = `Stav recovery nelze potvrdit: ${error.message}`;
    }
  }

  function renderMainRemoteSyncAudit(audit, deploymentFailure="") {
    mainRemoteSyncAudit = audit && typeof audit === "object" ? audit : null;
    const state = mainRemoteSyncAudit ? String(mainRemoteSyncAudit.state || "") : "";
    const canFastForward = Boolean(
      mainRemoteSyncAudit
      && mainRemoteSyncAudit.ok === true
      && mainRemoteSyncAudit.can_fast_forward === true
      && state === "fast_forward_available"
    );
    const visible = Boolean(mainRemoteSyncAudit && state && state !== "aligned");
    mainSyncBox.hidden = !visible;
    mainSyncBtn.disabled = !canFastForward;
    mainSyncChanges.replaceChildren();
    const changes = mainRemoteSyncAudit && Array.isArray(mainRemoteSyncAudit.changes)
      ? mainRemoteSyncAudit.changes
      : [];
    for (const item of changes) {
      const row = document.createElement("li");
      const path = item.from_path
        ? `${item.from_path} → ${item.path || ""}`
        : (item.path || "");
      row.textContent = `${item.status || "?"} · ${path}`;
      mainSyncChanges.appendChild(row);
    }
    mainSyncChanges.hidden = !changes.length;
    if (!mainRemoteSyncAudit) {
      mainSyncMeta.textContent = "Nejdřív spusť audit nasazení.";
    } else if (canFastForward) {
      const commits = Number(mainRemoteSyncAudit.commit_count || 0);
      const files = Number(mainRemoteSyncAudit.change_count || 0);
      const target = String(mainRemoteSyncAudit.origin_short || "");
      const truncated = mainRemoteSyncAudit.changes_truncated ? " · seznam je zkrácený" : "";
      mainSyncMeta.textContent = `GitHub je napřed o ${commits} commitů · cíl ${target} · ${files} změněných souborů${truncated} · lze použít pouze fast-forward.`;
    } else if (state === "local_ahead") {
      mainSyncMeta.textContent = githubBatchModeEnabled
        ? "Lokální main je napřed; commity patří do denního GitHub balíčku."
        : "Lokální main je napřed; automatický fast-forward není možný.";
    } else if (state === "diverged") {
      mainSyncMeta.textContent = "Lokální main a GitHub se rozešly; je nutné servisní rozhodnutí.";
    } else {
      mainSyncMeta.textContent = deploymentFailure
        ? `Dorovnání není bezpečně dostupné: ${deploymentFailure}`
        : (mainRemoteSyncAudit.message || "Dorovnání není bezpečně dostupné.");
    }
  }

  async function auditMainRemoteSync(deploymentFailure="") {
    try {
      const payload = await api("/api/human-adam/main-sync-audit");
      renderMainRemoteSyncAudit(payload, deploymentFailure);
      return payload;
    } catch (error) {
      renderMainRemoteSyncAudit({
        ok:false,
        state:"audit_failed",
        can_fast_forward:false,
        message:error.message,
      }, deploymentFailure || error.message);
      return null;
    }
  }

  async function applyMainRemoteSync() {
    if (mainSyncBtn.disabled || !mainRemoteSyncAudit) return;
    const commits = Number(mainRemoteSyncAudit.commit_count || 0);
    const target = String(mainRemoteSyncAudit.origin_short || "");
    if (!window.confirm(
      `Dorovnat čistý lokální main s GitHubem?\n\n${commits} commitů · cíl ${target}\n\nPoužije se pouze fast-forward; merge, rebase ani přepis historie se neprovedou.`
    )) return;
    mainSyncBtn.disabled = true;
    mainSyncMeta.textContent = "Znovu ověřuji GitHub a přesný auditovaný commit…";
    try {
      const payload = await api("/api/human-adam/main-sync", {
        method:"POST",
        body:JSON.stringify({
          confirmed:true,
          expected_local_head:String(mainRemoteSyncAudit.local_head || ""),
          expected_origin_head:String(mainRemoteSyncAudit.origin_head || ""),
        }),
      });
      if (!payload.ok) {
        if (payload.main_fast_forwarded) {
          mainSyncMeta.textContent = payload.message || "Main je dorovnaný, profil ještě čeká na synchronizaci.";
          await loadWork();
          await loadStatus();
          return;
        }
        throw new Error(payload.message || "Ruční dorovnání main selhalo.");
      }
      renderMainRemoteSyncAudit(null);
      notice.textContent = `Main i čisté profily jsou dorovnané na ${payload.main_short || "auditovaný commit"}.`;
      await loadWork();
      await loadStatus();
      await auditDeployment();
    } catch (error) {
      mainSyncMeta.textContent = `Nic nebylo dorovnáno: ${error.message}`;
      mainSyncBtn.disabled = false;
    }
  }

  function renderBatchWorkflow(payload) {
    batchWorkflowBox.hidden = !githubBatchModeEnabled;
    if (!githubBatchModeEnabled) return;
    const workspace = payload && typeof payload === "object" ? payload : {};
    const live = workspace.workstream_live_status && typeof workspace.workstream_live_status === "object"
      ? workspace.workstream_live_status
      : {};
    const deployment = live.deployment && typeof live.deployment === "object"
      ? live.deployment
      : {};
    const deploymentState = String(deployment.state || "unverified");
    const relation = String(workspace.workspace_relation || "unknown");

    if (workspace.dirty) {
      batchWorkflowLocal.textContent = `Vývoj: čeká dokončení ${Number(workspace.change_count || 0)} pracovních změn.`;
      batchWorkflowNext.textContent = "Nejdřív nech Adama bezpečně dokončit lokální commit.";
    } else if (relation !== "aligned") {
      batchWorkflowLocal.textContent = "Vývoj: workspace není čistě zarovnaný s lokálním main.";
      batchWorkflowNext.textContent = "Nejdřív přečti zobrazený audit; nic neopakuj naslepo.";
    } else {
      batchWorkflowLocal.textContent = "Vývoj: lokální main i profily jsou čisté; můžeš zadat další krok.";
      batchWorkflowNext.textContent = "Můžeš pokračovat dalším vývojem. GitHub nemusí čekání přerušit.";
    }

    if (!workstreamDeploymentEnabled) {
      batchWorkflowDeploy.textContent = "Cockpit: tento pracovní proud nemá vlastní nasazení.";
    } else if (deploymentState === "verified_current") {
      batchWorkflowDeploy.textContent = "Cockpit: běží aktuální lokální main; nasazení není potřeba.";
    } else if (
      deploymentState === "pending_restart"
      || deploymentState === "verified_other_main"
      || deploymentState === "code_mismatch"
    ) {
      batchWorkflowDeploy.textContent = "Cockpit: lokální main je novější; nasazuj jen změnu běžícího UI nebo backendu.";
      if (!workspace.dirty && relation === "aligned") {
        batchWorkflowNext.textContent = "Můžeš pokračovat; pokud změna ovlivňuje Cockpit, použij jednou jeho audit a nasazení.";
      }
    } else {
      batchWorkflowDeploy.textContent = "Cockpit: shodu s lokálním main zatím nelze potvrdit.";
    }
    batchWorkflowGithub.textContent = "GitHub: ověřuji počet commitů čekajících v denním balíčku.";
  }

  function renderGithubBatchAudit(audit) {
    githubBatchAudit = audit && typeof audit === "object" ? audit : null;
    githubBatchBox.hidden = !githubBatchModeEnabled;
    githubBatchCommits.replaceChildren();
    githubBatchConfirmation.value = "";
    githubBatchConfirmation.hidden = true;
    githubBatchConfirmation.disabled = true;
    githubBatchBtn.hidden = true;
    githubBatchBtn.disabled = true;
    if (!githubBatchModeEnabled) return;
    if (!githubBatchAudit) {
      githubBatchMeta.textContent = "Denní balíček zatím nebyl ověřen.";
      batchWorkflowGithub.textContent = "GitHub: denní balíček zatím nebyl ověřen.";
      return;
    }
    const state = String(githubBatchAudit.state || "");
    const commits = Array.isArray(githubBatchAudit.commits) ? githubBatchAudit.commits : [];
    for (const item of commits) {
      const row = document.createElement("li");
      row.textContent = `${item.head || "?"} · ${item.subject || "commit bez popisu"}`;
      githubBatchCommits.appendChild(row);
    }
    githubBatchCommits.hidden = !commits.length;
    if (githubBatchAudit.ready === true && state === "ready") {
      const count = Number(githubBatchAudit.commit_count || 0);
      const files = Number(githubBatchAudit.change_count || 0);
      githubBatchMeta.textContent = `${count} čekajících commitů · ${files} změněných souborů · před jedním pushem proběhne úplná brána · vlož přesně: ${githubBatchAudit.confirmation_text || ""}`;
      batchWorkflowGithub.textContent = `GitHub: ${count} lokálních commitů bezpečně čeká na pozdější denní balíček.`;
      githubBatchConfirmation.hidden = false;
      githubBatchConfirmation.disabled = false;
      githubBatchBtn.hidden = false;
      return;
    }
    if (state === "aligned") {
      githubBatchMeta.textContent = "GitHub je aktuální; žádný denní balíček nečeká.";
      batchWorkflowGithub.textContent = "GitHub: žádný lokální commit nečeká.";
      return;
    }
    if (state === "origin_ahead") {
      githubBatchMeta.textContent = "GitHub je napřed. Nejdřív použij bezpečné dorovnání main; balíček se neodeslal.";
      batchWorkflowGithub.textContent = "GitHub: je napřed; další lokální vývoj může pokračovat, ale balíček čeká na dorovnání.";
      return;
    }
    if (state === "diverged") {
      githubBatchMeta.textContent = "Lokální main a GitHub se rozešly. Balíček je zablokovaný a vyžaduje servisní rozhodnutí.";
      batchWorkflowGithub.textContent = "GitHub: balíček blokuje divergence; lokální práci nemaž.";
      return;
    }
    githubBatchMeta.textContent = githubBatchAudit.message || "Denní balíček nelze bezpečně ověřit.";
    batchWorkflowGithub.textContent = "GitHub: denní balíček nelze bezpečně ověřit.";
  }

  async function auditGithubBatch() {
    if (!githubBatchModeEnabled) {
      renderGithubBatchAudit(null);
      return null;
    }
    githubBatchBox.hidden = false;
    githubBatchMeta.textContent = "Ověřuji GitHub a přesný seznam čekajících lokálních commitů…";
    try {
      const payload = await api("/api/human-adam/github-batch-audit");
      renderGithubBatchAudit(payload);
      return payload;
    } catch (error) {
      renderGithubBatchAudit({
        ok:false,
        state:"audit_failed",
        ready:false,
        message:error.message,
      });
      return null;
    }
  }

  async function pushGithubBatch() {
    if (githubBatchBtn.disabled || !githubBatchAudit) return;
    const required = String(githubBatchAudit.confirmation_text || "").trim();
    const confirmation = githubBatchConfirmation.value.trim();
    if (!required || confirmation !== required) {
      githubBatchMeta.textContent = "Potvrzovací věta nesouhlasí; nic se neodeslalo.";
      return;
    }
    githubBatchBtn.disabled = true;
    githubBatchConfirmation.disabled = true;
    githubBatchMeta.textContent = "Spouštím jednu úplnou bránu a potom jeden přesný push denního balíčku…";
    try {
      const payload = await api("/api/human-adam/github-batch", {
        method:"POST",
        body:JSON.stringify({
          confirmation,
          expected_origin_head:String(githubBatchAudit.origin_head || ""),
          expected_local_head:String(githubBatchAudit.local_head || ""),
        }),
      });
      if (!payload.ok || payload.pushed !== true) {
        throw new Error(payload.message || "Denní GitHub balíček se neodeslal.");
      }
      notice.textContent = `Denní GitHub balíček byl odeslaný: ${Number(payload.commit_count || 0)} commitů · main ${payload.local_short || ""}.`;
      await loadWork();
      await loadStatus();
    } catch (error) {
      githubBatchMeta.textContent = `Nic se neodeslalo: ${error.message}`;
      githubBatchConfirmation.disabled = false;
      githubBatchBtn.disabled = false;
    }
  }

  function renderWork(payload) {
    deploymentAudit = null;
    githubBatchModeEnabled = payload.github_batch_mode === true;
    if (!githubBatchModeEnabled) renderGithubBatchAudit(null);
    renderMainRemoteSyncAudit(null);
    renderHandoffTakeoverCheck(null);
    renderProjectContinuity(payload.project_continuity || null);
    renderDevelopmentSemaphore(payload.development_semaphore || null);
    renderHandoffProposal(payload.handoff_proposal || null);
    renderPendingIntegrationAudit(payload.pending_integration_audit || null);
    renderWorkstreamLiveStatus(payload.workstream_live_status || null);
    renderStepCompletion(payload.last_step_completion || null);
    renderBatchWorkflow(payload);
    workChanges.replaceChildren();
    const pending = Array.isArray(payload.changes) ? payload.changes : [];
    const checkpointed = Array.isArray(payload.checkpoint_changes) ? payload.checkpoint_changes : [];
    const checkpointPreserved = payload.workspace_relation === "diverged" && payload.local_checkpoint_preserved === true;
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
    else if (checkpointPreserved) workMeta.textContent = `WIP checkpoint je zachovaný: ${payload.local_commit_count} commitů · ${payload.checkpoint_change_count} souborů · vyžaduje obnovu`;
    else if (payload.workspace_relation === "diverged") workMeta.textContent = "Workspace a main se rozešly; je nutná servisní kontrola.";
    else workMeta.textContent = "Workspace je čistý a odpovídá main.";
    const semaphore = payload.development_semaphore || {};
    const liveDeployment = activeWorkstreamLiveDeployment();
    const deploymentCurrent = String(liveDeployment.state || "") === "verified_current";
    const deployedMain = String(liveDeployment.main_short || "").trim();
    const deployedSmokeCount = Number(liveDeployment.smoke_count || 0);
    checkpointBtn.disabled = !workstreamDevelopmentEnabled || !payload.dirty || semaphore.can_checkpoint !== true;
    const simpleDeployReady = workstreamDeploymentEnabled
      && !deploymentCurrent
      && !payload.dirty
      && !payload.local_checkpoint_ahead
      && payload.workspace_relation === "aligned"
      && Number(payload.source_pending_changes || 0) === 0;
    deployAuditBtn.hidden = !workstreamDeploymentEnabled;
    deployAuditBtn.disabled = !simpleDeployReady;
    deployAuditBtn.textContent = deploymentCurrent
      ? "Nasazení je aktuální ✓"
      : "Audit nasazení do Cockpitu";
    deployAuditBtn.classList.toggle("deployment-current", deploymentCurrent);
    deployConfirmation.value = "";
    deployConfirmation.hidden = true;
    deployConfirmation.disabled = true;
    deployBtn.hidden = !workstreamDeploymentEnabled || deploymentCurrent;
    deployBtn.disabled = true;
    deployBtn.textContent = "Nasadit aktuální main do Cockpitu";
    if (!workstreamDeploymentEnabled) deployMeta.textContent = "Vývoj spusť tlačítkem Zahájit vývoj. Po úspěšném tahu vznikne lokální commit; GitHub počká na denní balíček. Nasazení z tohoto pracovního proudu není dostupné.";
    else if (deploymentCurrent) deployMeta.textContent = `Cockpit už běží na aktuálním main${deployedMain ? ` ${deployedMain}` : ""} · smoke ${deployedSmokeCount}/5. Audit ani opakované nasazení nejsou potřeba.`;
    else if (!workstreamDevelopmentEnabled) deployMeta.textContent = "Tento pracovní proud je pouze pro čtení; vývoj zde zatím není povolen.";
    else if (payload.dirty) deployMeta.textContent = "Nejdřív dokonči automatický checkpoint změn do main.";
    else if (payload.local_checkpoint_ahead) deployMeta.textContent = "Je zachovaný starší lokální checkpoint; nejdřív proveď servisní kontrolu.";
    else if (checkpointPreserved) deployMeta.textContent = "WIP je bezpečně zachovaný, ale audit je zablokovaný. Nejdřív proveď obnovu nad aktuálním main.";
    else if (payload.workspace_relation === "diverged") deployMeta.textContent = "Audit je zablokovaný: workspace a main se rozešly.";
    else if (simpleDeployReady) deployMeta.textContent = "Čistý main je připravený k auditu nasazení do Cockpitu.";
    else deployMeta.textContent = "Workspace nejdřív synchronizuj s čistým main.";
    renderCompactWorkStatus(payload);
  }

  const LIVE_WORK_STATUS_LABELS = Object.freeze({
    overall: Object.freeze({
      current:"Aktuální",
      current_runtime_disconnected:"Aktuální · Adam je odpojený",
      attention_required:"Vyžaduje kontrolu",
      unverified:"Neověřeno",
    }),
    main: Object.freeze({
      aligned:"Shodné s GitHubem",
      dirty:"Main obsahuje pracovní změny",
      origin_ahead:"GitHub je napřed",
      local_ahead:"Lokální main je napřed",
      diverged:"Main a GitHub se rozešly",
      origin_unverified:"GitHub nelze ověřit",
      unverified:"Neověřeno",
    }),
    deployment: Object.freeze({
      verified_current:"Ověřeno pro tento main",
      pending_restart:"Čeká na restart",
      verified_other_main:"Ověřeno pro jiný main",
      code_mismatch:"Serverový otisk nesouhlasí",
      current_head_server_unverified:"Serverový otisk nelze ověřit",
      unavailable:"Není dostupné",
      unverified:"Neověřeno",
    }),
    workspaces: Object.freeze({
      aligned_clean:"Čisté a zarovnané",
      attention_required:"Vyžadují kontrolu",
      unverified:"Neověřeno",
    }),
    runtime: Object.freeze({
      connected:"Připojeno",
      disconnected:"Odpojeno",
      unreachable:"Runtime není dostupný",
      busy:"Adam pracuje",
      delivery_uncertain:"Nejisté doručení",
      unverified:"Neověřeno",
    }),
  });

  function liveWorkStatusLabel(group, state) {
    const labels = LIVE_WORK_STATUS_LABELS[group] || {};
    return labels[String(state || "")] || "Neověřeno";
  }

  function renderWorkstreamLiveStatus(liveStatus) {
    const valid = Boolean(
      liveStatus
      && typeof liveStatus === "object"
      && Number(liveStatus.schema_version) === 1
      && liveStatus.read_only === true
      && liveStatus.writes_performed === false
      && String(liveStatus.workstream_id || "") === activeWorkstreamId
    );
    const status = valid ? liveStatus : {};
    currentWorkstreamLiveStatus = valid ? status : null;
    const overallState = valid ? String(status.state || "unverified") : "unverified";
    liveWorkStatusBox.dataset.state = overallState;
    const observed = valid ? formatTime(status.observed_at) : "čas neověřen";
    liveWorkStatusMeta.textContent = `${liveWorkStatusLabel("overall", overallState)} · read-only snapshot · ${observed}`;
    liveWorkStatusAxes.replaceChildren();

    const main = valid && status.main && typeof status.main === "object" ? status.main : {};
    const deployment = valid && status.deployment && typeof status.deployment === "object" ? status.deployment : {};
    const workspaces = valid && status.workspaces && typeof status.workspaces === "object" ? status.workspaces : {};
    const runtime = valid && status.runtime && typeof status.runtime === "object" ? status.runtime : {};
    const mainHead = main.head_short ? ` · ${String(main.head_short)}` : "";
    const deploymentEvidence = Number(deployment.test_count || 0) > 0
      ? ` · ${Number(deployment.test_count)} testů · smoke ${Number(deployment.smoke_count || 0)}/5`
      : (deployment.gate_mode === "quick" && Number(deployment.smoke_count || 0) === 5
        ? " · rychlá lokální brána · smoke 5/5"
        : "");
    const workspaceCount = Number(workspaces.count || 0) > 0
      ? ` · ${Number(workspaces.aligned_count || 0)}/${Number(workspaces.count)} zarovnáno`
      : "";
    const rows = [
      `Main a GitHub: ${liveWorkStatusLabel("main", main.state)}${mainHead}`,
      `Nasazení: ${liveWorkStatusLabel("deployment", deployment.state)}${deploymentEvidence}`,
      `Workspaces: ${liveWorkStatusLabel("workspaces", workspaces.state)}${workspaceCount}`,
      `Runtime: ${liveWorkStatusLabel("runtime", runtime.state)}`,
    ];
    for (const text of rows) {
      const row = document.createElement("li");
      row.textContent = text;
      liveWorkStatusAxes.appendChild(row);
    }
  }

  function renderHandoffProposal(proposal) {
    const valid = proposal && typeof proposal === "object";
    const state = valid ? String(proposal.state || "") : "";
    const visible = valid && state !== "waiting_checkpoint";
    handoffProposalBox.hidden = !visible;
    handoffProposalDraft.textContent = valid ? String(proposal.draft || "") : "";
    handoffProposalDraft.hidden = !visible || proposal.available !== true || !handoffProposalDraft.textContent;
    if (!visible) {
      handoffProposalMeta.textContent = "Návrh vznikne až po úspěšném checkpointu.";
      return;
    }
    const target = proposal.target_handoff ? ` · cíl: ${String(proposal.target_handoff).split("/").pop()}` : "";
    handoffProposalMeta.textContent = `${proposal.label || "Nelze připravit"} · ${proposal.message || ""}${target} · nic nebylo uloženo.`;
  }

  function renderDevelopmentSemaphore(semaphore) {
    developmentSemaphore = semaphore && typeof semaphore === "object" ? semaphore : null;
    renderDevelopmentBadge(developmentSemaphore);
    const valid = developmentSemaphore && developmentSemaphore.ok === true;
    const active = Boolean(valid && developmentSemaphore.active);
    const owner = active ? String(developmentSemaphore.owner_label || developmentSemaphore.owner_id || "Neznámý vlastník") : "";
    const topic = active ? String(developmentSemaphore.topic || "bez tématu") : "";
    const blockers = valid && Array.isArray(developmentSemaphore.blockers) ? developmentSemaphore.blockers.filter(Boolean) : [];
    if (!valid) developmentSemaphoreMeta.textContent = developmentSemaphore && developmentSemaphore.message ? developmentSemaphore.message : "Vývojový semafor nelze ověřit; zápis je zablokovaný.";
    else if (!active) developmentSemaphoreMeta.textContent = "Semafor je volný. Převezmi jej před první změnou kódu; druhý Adam pak zůstane read-only.";
    else developmentSemaphoreMeta.textContent = `Vlastník: ${owner} · ${developmentSemaphore.mode === "paused" ? "pozastaveno" : "aktivní"} · projekt: ${developmentSemaphore.project_label || "bez vazby"} · téma: ${topic}${blockers.length ? ` · blokery: ${blockers.join(" ")}` : ""}`;
    developmentAcquireProfileBtn.textContent = `Převzít pro ${activeWorkstreamLabel}`;
    developmentAcquireProfileBtn.hidden = active;
    developmentAcquireTerminalBtn.hidden = active;
    developmentPauseBtn.hidden = !active || developmentSemaphore.mode !== "active";
    developmentResumeBtn.hidden = !active || developmentSemaphore.mode !== "paused";
    developmentReleaseBtn.hidden = !active;
    if (active) developmentTopic.value = topic === "bez tématu" ? "" : topic;
    syncControls();
  }

  async function changeDevelopmentSemaphore(operation) {
    if (!developmentSemaphore || developmentSemaphore.ok !== true) return;
    const acquiring = operation === "acquire_profile" || operation === "acquire_terminal";
    const topic = developmentTopic.value.trim();
    const projectId = developmentProject.value;
    const handoffPath = developmentHandoff.value;
    if (acquiring && !topic) {
      developmentSemaphoreMeta.textContent = "Zadej krátké téma vývoje.";
      developmentTopic.focus();
      return;
    }
    if (acquiring && (!projectId || !handoffPath)) {
      developmentSemaphoreMeta.textContent = "Vyber projekt a jeho aktuální handoff.";
      (projectId ? developmentHandoff : developmentProject).focus();
      return;
    }
    const labels = {
      acquire_profile:`Převzít globální vývojový semafor pro proud ${activeWorkstreamLabel}?`,
      acquire_terminal:"Převzít globální vývojový semafor pro terminálového Adama?",
      pause:"Pozastavit vývoj? Vlastník zůstane stejný a ostatní zápis zůstane zablokovaný.",
      resume:"Obnovit pozastavený vývoj?",
      release:"Uvolnit vývojový semafor? To projde jen při čistých workspaces bez čekajícího WIP.",
    };
    if (!window.confirm(labels[operation] || "Změnit vývojový semafor?")) return;
    setBusy(true, "Aktualizuji globální vývojový semafor…");
    try {
      const payload = await api("/api/human-adam/development-semaphore", {
        method:"POST",
        body:JSON.stringify({operation,expected_revision:Number(developmentSemaphore.revision),topic,project_id:projectId,handoff_path:handoffPath,confirmed:true}),
      });
      if (!payload.ok) throw new Error(payload.message || "Vývojový semafor nelze změnit.");
      developmentSemaphore = payload;
      if (acquiring) developmentTopic.value = "";
      notice.textContent = "Vývojový semafor byl bezpečně aktualizovaný.";
    } catch (error) {
      notice.textContent = `Vývojový semafor nebyl změněn: ${error.message}`;
    } finally { setBusy(false); }
    await loadWork();
    await loadStatus();
  }

  async function loadWork() {
    workRefreshBtn.disabled = true;
    workMeta.textContent = "Načítám pracovní stav…";
    try {
      const payload = await api("/api/human-adam/workspace");
      if (!payload.ok) throw new Error(payload.message || "Pracovní stav nelze načíst.");
      renderWork(payload);
      if (githubBatchModeEnabled && !workPanel.hidden) await auditGithubBatch();
      return payload;
    } catch (error) {
      workChanges.replaceChildren();
      workMeta.textContent = `Pracovní stav nelze načíst: ${error.message}`;
      renderWorkstreamLiveStatus(null);
      renderPendingIntegrationAudit(null);
      checkpointBtn.disabled = true;
      return null;
    } finally { workRefreshBtn.disabled = false; }
  }

  function updateDevelopmentHandoffs(selectedPath="") {
    developmentHandoff.replaceChildren();
    const project = projectContinuity && Array.isArray(projectContinuity.projects)
      ? projectContinuity.projects.find((item) => item.id === developmentProject.value)
      : null;
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = project ? "Vyber aktuální handoff" : "Nejdřív vyber projekt";
    developmentHandoff.appendChild(placeholder);
    for (const item of project && Array.isArray(project.handoffs) ? project.handoffs : []) {
      const option = document.createElement("option");
      option.value = String(item.path || "");
      option.textContent = String(item.label || item.path || "Handoff");
      developmentHandoff.appendChild(option);
    }
    developmentHandoff.value = selectedPath && [...developmentHandoff.options].some((item) => item.value === selectedPath) ? selectedPath : "";
    syncControls();
  }

  function renderProjectContinuity(payload) {
    projectContinuity = payload && typeof payload === "object" ? payload : null;
    projectContinuityReasons.replaceChildren();
    const valid = projectContinuity && projectContinuity.ok === true;
    const projects = valid && Array.isArray(projectContinuity.projects) ? projectContinuity.projects : [];
    const binding = valid && projectContinuity.binding && typeof projectContinuity.binding === "object" ? projectContinuity.binding : {};
    const previousProject = developmentProject.value;
    developmentProject.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = valid ? "Vyber projekt" : "Projekty nelze ověřit";
    developmentProject.appendChild(placeholder);
    for (const item of projects) {
      const option = document.createElement("option");
      option.value = String(item.id || "");
      option.textContent = `${item.label || "Projekt"}${item.priority ? ` · priorita ${item.priority}` : ""}`;
      developmentProject.appendChild(option);
    }
    const wantedProject = String(binding.project_id || previousProject || projectContinuity.default_project_id || "");
    developmentProject.value = [...developmentProject.options].some((item) => item.value === wantedProject) ? wantedProject : "";
    updateDevelopmentHandoffs(String(binding.handoff_path || ""));
    const audit = valid && projectContinuity.audit && typeof projectContinuity.audit === "object" ? projectContinuity.audit : null;
    const reasons = audit && Array.isArray(audit.reasons) ? audit.reasons.filter(Boolean) : [];
    for (const reason of reasons) {
      const row = document.createElement("li");
      row.textContent = String(reason);
      projectContinuityReasons.appendChild(row);
    }
    projectContinuityReasons.hidden = !reasons.length;
    if (!valid) projectContinuityMeta.textContent = audit && audit.message ? audit.message : "Projektovou kontinuitu nelze bezpečně ověřit.";
    else if (!audit) projectContinuityMeta.textContent = "Audit zatím nemá výsledek. Nic nebylo změněno.";
    else projectContinuityMeta.textContent = `${audit.label || "Nelze ověřit"} · ${audit.message || ""} · pouze read-only, nic neblokuje.`;
    syncControls();
  }

  async function loadProjectContinuity() {
    projectContinuityAuditBtn.disabled = true;
    projectContinuityMeta.textContent = "Prověřuji vazbu, handoff, TVBCP a nasazení bez zápisu…";
    try {
      const payload = await api("/api/human-adam/project-continuity");
      renderProjectContinuity(payload);
    } catch (error) {
      projectContinuityMeta.textContent = `Audit kontinuity selhal bezpečně: ${error.message}`;
    } finally {
      projectContinuityAuditBtn.disabled = busy;
    }
  }

  async function openWork() {
    if (workOpenBtn.disabled) return;
    workOpenBtn.disabled = true;
    const payload = await loadWork();
    workOpenBtn.disabled = busy;
    threadRotationPanel.hidden = true;
    tvbcpPanel.hidden = true;
    workPanel.hidden = false;
    if (payload && payload.github_batch_mode === true) await auditGithubBatch();
  }

  function setWorkHelpOpen(open) {
    const expanded = Boolean(open);
    workHelpPanel.hidden = !expanded;
    workHelpBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
    if (expanded) workHelpPanel.focus();
  }

  function closeWork() {
    setWorkHelpOpen(false);
    workPanel.hidden = true;
  }

  async function createCheckpoint() {
    if (checkpointBtn.disabled) return;
    checkpointMessage.blur();
    await new Promise((resolve) => window.setTimeout(resolve, 0));
    const checkpointTitle = checkpointMessage.value.trim();
    if (!checkpointTitle) {
      workMeta.textContent = "Zadej krátký název WIP checkpointu.";
      checkpointMessage.focus();
      return;
    }
    if (!window.confirm(`Vytvořit lokální WIP checkpoint bez pushnutí?\n\n${checkpointTitle}`)) return;
    checkpointBtn.disabled = true;
    workMeta.textContent = "Vytvářím bezpečný lokální checkpoint…";
    let failure = "";
    try {
      const payload = await api("/api/human-adam/checkpoint", {method:"POST", body:JSON.stringify({confirmed:true,message:checkpointTitle})});
      if (!payload.ok) throw new Error(payload.message || "Checkpoint selhal.");
      checkpointMessage.value = "";
      renderWork(payload.work);
      renderStatus(payload.status);
      if (payload.work && payload.work.handoff_proposal && payload.work.handoff_proposal.available === true) {
        handoffProposalBox.scrollIntoView({block:"nearest",behavior:"smooth"});
      }
    } catch (error) {
      failure = `Checkpoint selhal: ${error.message}`;
      await loadWork();
    }
    if (failure) workMeta.textContent = failure;
  }

  function renderDeploymentAudit(payload) {
    deploymentAudit = payload;
    renderHandoffTakeoverCheck(payload.handoff_takeover_check || null);
    workChanges.replaceChildren();
    for (const item of payload.changes || []) {
      const row = document.createElement("li");
      row.textContent = `${item.status || "?"} · ${item.path || ""}`;
      workChanges.appendChild(row);
    }
    const workstream = payload.workstream && payload.workstream.name ? payload.workstream.name : "aktivní pracovní proud";
    const target = payload.main_short || "?";
    deployMeta.textContent = `Audit OK · Git/main ${target} · připraveno k nasazení do běžícího Cockpitu · ${workstream} · vlož přesně: ${payload.confirmation_text}`;
    deployBtn.textContent = `Restartovat Cockpit na ${target} a ověřit`;
    deployConfirmation.value = "";
    deployConfirmation.hidden = false;
    deployConfirmation.disabled = false;
    deployBtn.disabled = true;
  }

  function renderHandoffTakeoverCheck(check) {
    const valid = check && typeof check === "object";
    handoffTakeoverCheck.hidden = !valid;
    handoffTakeoverCheck.className = valid && check.state === "verified" ? "verified" : "";
    if (!valid) {
      handoffTakeoverCheck.textContent = "";
      return;
    }
    const target = check.target_handoff ? ` · ${String(check.target_handoff).split("/").pop()}` : "";
    const warning = check.state === "verified" ? "" : " · Pouze varování; nasazení zatím neblokuje.";
    handoffTakeoverCheck.textContent = `${check.label || "Nelze ověřit"} · ${check.message || ""}${target}${warning}`;
  }

  async function auditDeployment() {
    deployAuditBtn.disabled = true;
    deployBtn.disabled = true;
    deployMeta.textContent = "Audituji nasazení aktuálního lokálního main do Cockpitu: ověřuji oba profilové workspaces…";
    try {
      const payload = await api("/api/human-adam/deploy-audit");
      if (!payload.ok || !payload.ready) throw new Error(payload.message || "Audit nasazení do Cockpitu neprošel.");
      renderMainRemoteSyncAudit(null);
      renderDeploymentAudit(payload);
    } catch (error) {
      deploymentAudit = null;
      deployMeta.textContent = `Audit nasazení do Cockpitu selhal: ${error.message}`;
      deployAuditBtn.disabled = false;
      await auditMainRemoteSync(error.message);
    }
  }

  async function waitForCockpitAndReload(previousPid, expectedMainShort) {
    const expected = String(expectedMainShort || "").trim().toLowerCase();
    let lastVerificationMessage = "";
    for (let attempt = 1; attempt <= deploymentReturnMaxAttempts; attempt += 1) {
      try {
        const response = await fetch("/api/server/health", {cache:"no-store"});
        if (response.ok) {
          const health = await response.json();
          const currentPid = health && health.server ? health.server.pid : 0;
          if (currentPid && currentPid !== previousPid) {
            try {
              const verification = await api("/api/human-adam/deploy-verification", {
                method:"POST",
                body:JSON.stringify({}),
              });
              const verified = expectedDeploymentRecord(verification, expected);
              if (!verification.ok || verification.state !== "deployed" || !verified) {
                lastVerificationMessage = verification.message || "Server ještě nemá úplný důkaz pro auditovaný main.";
              } else {
                deployMeta.textContent = verifiedDeploymentSummary(verification);
                storeVerifiedDeploymentResult(verification);
                window.location.reload();
                return;
              }
            } catch (error) {
              lastVerificationMessage = error.message;
            }
          }
        }
      } catch (_error) {
        // Očekávané krátké odpojení během restartu Cockpitu.
      }
      const verificationNote = lastVerificationMessage
        ? " · server ještě dokončuje ověření"
        : "";
      deployMeta.textContent = `Restart a ověření probíhají · neopakuj nasazení · ${attempt}/${deploymentReturnMaxAttempts}${verificationNote}`;
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
    }
    try {
      const status = await api("/api/human-adam/status");
      const record = expectedDeploymentRecord(
        status && status.last_simple_main_deployment,
        expected,
      );
      if (record) {
        deployMeta.textContent = verifiedDeploymentSummary(
          status.last_simple_main_deployment,
        );
        storeVerifiedDeploymentResult(status.last_simple_main_deployment);
        window.location.reload();
        return;
      }
    } catch (error) {
      lastVerificationMessage = error.message;
    }
    const detail = lastVerificationMessage
      ? ` Poslední kontrola: ${lastVerificationMessage}`
      : "";
    deployMeta.textContent = `Výsledek nasazení zatím nelze potvrdit.${detail} Nasazení neopakuj. Nejdřív obnov stav; terminálový fallback použij pouze tehdy, když server skutečně neodpovídá.`;
  }

  function verifiedDeploymentRecord(payload) {
    const mainShort = String(payload && payload.main_short || "").trim().toLowerCase();
    const testCount = Number(
      payload && payload.gate ? payload.gate.test_count : (payload && payload.test_count || 0)
    );
    const gateMode = String(
      payload && payload.gate ? payload.gate.mode : (payload && payload.gate_mode || "full")
    ).trim();
    const smokeCount = Number(
      payload && payload.smoke ? payload.smoke.check_count : (payload && payload.smoke_count || 0)
    );
    const deployedAt = String(payload && payload.deployed_at || "").trim();
    const parsedTime = new Date(deployedAt);
    if (!/^[0-9a-f]{7,12}$/.test(mainShort)) return null;
    if (!["full","quick"].includes(gateMode)) return null;
    if (!Number.isInteger(testCount)) return null;
    if ((gateMode === "full" && testCount <= 0) || (gateMode === "quick" && testCount !== 0)) return null;
    if (smokeCount !== 5 || Number.isNaN(parsedTime.getTime())) return null;
    return {
      schema_version:1,
      main_short:mainShort,
      test_count:testCount,
      gate_mode:gateMode,
      smoke_count:smokeCount,
      deployed_at:parsedTime.toISOString(),
      stored_at:Date.now(),
    };
  }

  function expectedDeploymentRecord(payload, expectedMainShort) {
    const expected = String(expectedMainShort || "").trim().toLowerCase();
    const record = verifiedDeploymentRecord(payload);
    if (!/^[0-9a-f]{7,12}$/.test(expected)) return null;
    if (!record || record.main_short !== expected) return null;
    return record;
  }

  function verifiedDeploymentSummary(payload) {
    const record = verifiedDeploymentRecord(payload);
    if (!record) return "Běžící Cockpit ověřen · úplný serverový důkaz je uložený.";
    const validation = record.gate_mode === "quick"
      ? "rychlá lokální brána"
      : `${record.test_count} testů`;
    return `Běžící Cockpit ověřen na main ${record.main_short} · ${validation} · smoke ${record.smoke_count}/5 · dokončeno ${formatTime(record.deployed_at)}.`;
  }

  function storeVerifiedDeploymentResult(payload) {
    const record = verifiedDeploymentRecord(payload);
    if (!record) return false;
    try {
      window.sessionStorage.setItem(verifiedDeploymentStorageKey, JSON.stringify(record));
      return true;
    } catch (_error) {
      return false;
    }
  }

  function takeVerifiedDeploymentResult() {
    let raw = "";
    try {
      raw = window.sessionStorage.getItem(verifiedDeploymentStorageKey) || "";
      window.sessionStorage.removeItem(verifiedDeploymentStorageKey);
    } catch (_error) {
      return null;
    }
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw);
      const record = verifiedDeploymentRecord(parsed);
      const storedAt = Number(parsed && parsed.stored_at || 0);
      if (!record || !Number.isFinite(storedAt)) return null;
      if (Date.now() - storedAt < 0 || Date.now() - storedAt > verifiedDeploymentMaxAgeMs) return null;
      return record;
    } catch (_error) {
      return null;
    }
  }

  function verifiedDeploymentFingerprint(record) {
    if (!record) return "";
    return `${record.main_short}:${record.deployed_at}`;
  }

  function recentServerDeploymentRecord(payload) {
    const record = verifiedDeploymentRecord(payload && payload.recent_simple_main_deployment);
    if (!record) return null;
    const ageMs = Date.now() - new Date(record.deployed_at).getTime();
    if (ageMs < 0 || ageMs > verifiedDeploymentMaxAgeMs) return null;
    try {
      if (window.sessionStorage.getItem(verifiedDeploymentSeenStorageKey) === verifiedDeploymentFingerprint(record)) {
        return null;
      }
    } catch (_error) {
      // Serverový důkaz zůstává použitelný i bez browserového úložiště.
    }
    return record;
  }

  function markVerifiedDeploymentSeen(record) {
    try {
      window.sessionStorage.setItem(verifiedDeploymentSeenStorageKey, verifiedDeploymentFingerprint(record));
    } catch (_error) {
      // Bez úložiště se může čerstvé potvrzení zobrazit znovu, ale neztratí se.
    }
  }

  function hasCurrentUncertainDelivery(messages) {
    const rows = Array.isArray(messages) ? messages : [];
    for (let index = rows.length - 1; index >= 0; index -= 1) {
      const item = rows[index] && typeof rows[index] === "object" ? rows[index] : {};
      const status = String(item.status || "");
      if (status === "completed") return false;
      if (
        status === "pending"
        || status === "delivery_unknown"
        || item.recovery_required === true
      ) {
        return true;
      }
    }
    return false;
  }

  function safePostDeploymentReconnectStatus(payload) {
    if (!payload || payload.ok !== true || !payload.runtime || payload.runtime.reachable !== true) return false;
    const session = payload.session || {};
    const uncertain = hasCurrentUncertainDelivery(session.messages);
    return (
      session.connected !== true
      && String(session.connection_state || "") === "disconnected"
      && session.turn_busy !== true
      && !session.active_turn
      && !uncertain
    );
  }

  async function reconnectAfterVerifiedDeployment(statusPayload) {
    if (!safePostDeploymentReconnectStatus(statusPayload)) {
      return {payload:statusPayload,reconnected:false};
    }
    setBusy(true, "Nasazení je ověřené · znovu připojuji Human–Adam…");
    try {
      const payload = await api("/api/human-adam/connect", {
        method:"POST",
        body:JSON.stringify({}),
      });
      if (!payload.ok) throw new Error(payload.message || "Připojení po nasazení selhalo.");
      renderStatus(payload);
      return {
        payload,
        reconnected:Boolean(payload.session && payload.session.connected),
      };
    } catch (error) {
      notice.textContent = `Nasazení je dokončené, ale Human–Adam se nepodařilo znovu připojit: ${error.message}`;
      return {payload:statusPayload,reconnected:false};
    } finally {
      setBusy(false);
    }
  }

  async function restoreVerifiedDeploymentResult() {
    let record = takeVerifiedDeploymentResult();
    let statusPayload = await loadStatus();
    if (!record) record = recentServerDeploymentRecord(statusPayload);
    if (!record) return;
    const reconnectResult = await reconnectAfterVerifiedDeployment(statusPayload);
    statusPayload = reconnectResult.payload;
    threadRotationPanel.hidden = true;
    tvbcpPanel.hidden = true;
    workPanel.hidden = false;
    await loadWork();
    deployMeta.textContent = verifiedDeploymentSummary(record)
      + (reconnectResult.reconnected ? " Human–Adam je znovu připojený." : "");
    markVerifiedDeploymentSeen(record);
  }

  async function deployCheckpoint() {
    if (deployBtn.disabled || !deploymentAudit) return;
    const required = deploymentAudit.confirmation_text || "";
    const confirmation = deployConfirmation.value.trim();
    if (confirmation.trim() !== required) {
      deployMeta.textContent = "Potvrzovací věta nesouhlasí; nic nebylo nasazeno.";
      return;
    }
    deployAuditBtn.disabled = true;
    deployBtn.disabled = true;
    checkpointBtn.disabled = true;
    deployMeta.textContent = "Spouštím rychlou lokální bránu nad přesným main před nasazením do Cockpitu…";
    let previousPid = 0;
    const auditedMainShort = String(deploymentAudit.main_short || "");
    try {
      const healthResponse = await fetch("/api/server/health", {cache:"no-store"});
      if (healthResponse.ok) {
        const health = await healthResponse.json();
        previousPid = health && health.server ? health.server.pid : 0;
      }
      const payload = await api("/api/human-adam/deploy", {
        method:"POST",
        body:JSON.stringify({confirmation}),
      });
      if (!payload.ok) {
        const deploymentFailure = `Nic nebylo nasazeno: ${payload.message || "lokální brána nebo audit selhaly."}`;
        await loadWork();
        deployMeta.textContent = deploymentFailure;
        return;
      }
      const gateLabel = payload.gate && payload.gate.mode === "quick"
        ? "rychlá lokální brána"
        : (payload.gate && payload.gate.test_count ? `${payload.gate.test_count} testů` : "úplná brána");
      if (!payload.restart || !payload.restart.ok) {
        deployMeta.textContent = `${gateLabel} prošla, ale restart Cockpitu nezačal. Kód ještě neběží; použij Restart Cockpitu nebo terminálový fallback.`;
        return;
      }
      deployMeta.textContent = `${gateLabel} prošla · Cockpit se restartuje na auditovaný main…`;
      await waitForCockpitAndReload(
        Number(payload.restart.pid || previousPid),
        String(payload.main_short || auditedMainShort),
      );
    } catch (error) {
      if (previousPid) {
        deployMeta.textContent = "Spojení se přerušilo; ověřuji, zda probíhá restart po nasazení…";
        await waitForCockpitAndReload(previousPid, auditedMainShort);
      } else {
        deployMeta.textContent = `Nasazení nebylo potvrzeno: ${error.message}`;
        await loadWork();
      }
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    if (busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing) return;
    const text = input.value.trim();
    if (!text) { notice.textContent = "Napiš nejdřív zprávu."; return; }
    const writeIntent = writeIntentArmed;
    writeIntentArmed = false;
    sendInFlight = true;
    clearMessageInput();
    runSendUiBestEffort(syncControls);
    primeCompletionMediaSound().catch(() => {});
    const sentAt = new Date().toISOString();
    const clientId = messageId();
    const pendingMessage = {user_text:text,client_sent_at:sentAt,received_at:sentAt,status:"pending",answer:""};
    const optimistic = lastSession
      ? {...lastSession, turn_busy:true, active_turn:{client_message_id:clientId,started_at:sentAt}, messages:[...(lastSession.messages || []), pendingMessage]}
      : {turn_busy:true, active_turn:{client_message_id:clientId,started_at:sentAt}, messages:[pendingMessage]};
    runSendUiBestEffort(() => {
      renderSession(optimistic);
      renderTurnState(optimistic);
      notice.textContent = `Odesláno ${formatTime(sentAt)} · Adam pracuje…`;
    });
    let failure = "";
    let payload = null;
    try {
      payload = await api(HUMAN_ADAM_SEND_PATH, {method:"POST", body:JSON.stringify({message:text,client_message_id:clientId,client_sent_at:sentAt,write_intent:writeIntent})});
      if (!payload.ok) {
        const error = new Error(payload.message || "Odeslání selhalo.");
        error.status = String(payload.status || "");
        throw error;
      }
    } catch (error) {
      const confirmedRejection = new Set(["human_adam_busy","human_adam_send_failed"]).has(error.status);
      if (!confirmedRejection) {
        failure = `Stav doručení je nejistý: ${error.message} Pokyn neposílej znovu.`;
      } else {
        restoreRejectedMessage(text);
        failure = `Odeslání bylo odmítnuto: ${error.message} Text byl vrácen do editoru.`;
      }
    } finally {
      sendInFlight = false;
      runSendUiBestEffort(syncControls);
    }
    if (payload && payload.ok) {
      runSendUiBestEffort(() => {
        stopResultWatch();
        renderSession(payload.session);
        renderTurnState(payload.session);
        notice.textContent = "Odpověď doručena a potvrzena.";
        playCompletionMediaSound();
      });
      await prepareImageCandidate(text, clientId);
    }
    await loadStatus();
    if (failure) notice.textContent = failure;
  }

  composer.addEventListener("submit", sendMessage);
  connectBtn.addEventListener("click", connect);
  writeIntentBtn.addEventListener("click", armWriteIntent);
  profileSelect.addEventListener("change", syncControls);
  profileSwitchBtn.addEventListener("click", switchProfile);
  mobileStatusSummary.addEventListener("click", () => {
    setMobileStatusDetails(mobileStatusSummary.getAttribute("aria-expanded") !== "true");
  });
  mediaSoundTestBtn.addEventListener("click", testCompletionMediaSound);
  window.addEventListener("pagehide", () => {
    stopResultWatch();
    stopAnswerSpeech(false);
    stopCompletionMediaSound();
  });
  refreshBtn.addEventListener("click", handleRefreshStatus);
  threadRotationOpenBtn.addEventListener("click", openThreadRotation);
  threadRotationCloseBtn.addEventListener("click", closeThreadRotation);
  threadRotationAuditBtn.addEventListener("click", auditThreadRotation);
  threadRotationConfirmation.addEventListener("input", syncControls);
  threadRotationBtn.addEventListener("click", rotateProfileThread);
  tvbcpOpenBtn.addEventListener("click", openTvbcp);
  tvbcpCloseBtn.addEventListener("click", closeTvbcp);
  tvbcpRefreshBtn.addEventListener("click", loadTvbcp);
  workOpenBtn.addEventListener("click", openWork);
  workCloseBtn.addEventListener("click", closeWork);
  workHelpBtn.addEventListener("click", () => setWorkHelpOpen(workHelpPanel.hidden));
  workHelpCloseBtn.addEventListener("click", () => {
    setWorkHelpOpen(false);
    workHelpBtn.focus();
  });
  workRefreshBtn.addEventListener("click", loadWork);
  githubBatchConfirmation.addEventListener("input", () => {
    const required = githubBatchAudit ? String(githubBatchAudit.confirmation_text || "") : "";
    githubBatchBtn.disabled = !required || githubBatchConfirmation.value.trim() !== required;
  });
  githubBatchBtn.addEventListener("click", pushGithubBatch);
  integrationConfirmation.addEventListener("input", syncIntegrationRecoveryAction);
  integrationRecoveryCommit.addEventListener("input", syncIntegrationRecoveryAction);
  integrationRecoverySummary.addEventListener("input", syncIntegrationRecoveryAction);
  integrationRecoveryNextStep.addEventListener("input", syncIntegrationRecoveryAction);
  integrationBtn.addEventListener("click", integrateDeferredChanges);
  integrationRecoveryBtn.addEventListener("click", recoverOwnedChanges);
  developmentAcquireProfileBtn.addEventListener("click", () => changeDevelopmentSemaphore("acquire_profile"));
  developmentAcquireTerminalBtn.addEventListener("click", () => changeDevelopmentSemaphore("acquire_terminal"));
  developmentPauseBtn.addEventListener("click", () => changeDevelopmentSemaphore("pause"));
  developmentResumeBtn.addEventListener("click", () => changeDevelopmentSemaphore("resume"));
  developmentReleaseBtn.addEventListener("click", () => changeDevelopmentSemaphore("release"));
  developmentProject.addEventListener("change", () => updateDevelopmentHandoffs(""));
  projectContinuityAuditBtn.addEventListener("click", loadProjectContinuity);
  trustedExternalGenerationInput.addEventListener("input", syncTrustedExternalGenerationControl);
  trustedExternalGenerationBtn.addEventListener("click", changeTrustedExternalGeneration);
  checkpointBtn.addEventListener("click", createCheckpoint);
  deployAuditBtn.addEventListener("click", auditDeployment);
  mainSyncBtn.addEventListener("click", applyMainRemoteSync);
  deployConfirmation.addEventListener("input", () => {
    const required = deploymentAudit ? deploymentAudit.confirmation_text || "" : "";
    deployBtn.disabled = !required || deployConfirmation.value.trim() !== required;
  });
  deployBtn.addEventListener("click", deployCheckpoint);
  voiceRecordBtn.addEventListener("click", startVoiceRecording);
  voiceStopBtn.addEventListener("click", stopVoiceRecording);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) sendMessage(event);
  });
  clearMessageInput();
  window.addEventListener("pageshow", clearMessageInput);
  restoreVerifiedDeploymentResult();
</script>
</body>
</html>
"""
