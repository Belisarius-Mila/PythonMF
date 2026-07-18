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
    button.deploy-action { background:var(--ok); color:#fff; border-color:var(--ok); }
    button:disabled { opacity:.55; cursor:wait; }
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
    #deploymentReceipt[hidden] { display:none; }
    #deploymentDiagnostic { margin:8px 0 0; padding:6px 10px; border-radius:10px; color:var(--muted); background:var(--soft); font-size:13px; }
    #deploymentDiagnostic.running { color:var(--warn); background:#fff7ed; }
    #deploymentDiagnostic.passed { color:var(--ok); background:#ecfdf3; }
    #deploymentDiagnostic.failed { color:#991b1b; background:#fef2f2; }
    #deploymentDiagnostic[hidden] { display:none; }
    #chat { flex:1; padding:14px 18px 180px; display:flex; flex-direction:column; gap:14px; }
    .exchange { display:grid; gap:8px; }
    .bubble { max-width:86%; padding:12px 14px; border-radius:16px; white-space:pre-wrap; overflow-wrap:anywhere; }
    .human { justify-self:end; background:#dbeafe; border-bottom-right-radius:5px; }
    .adam { justify-self:start; background:var(--soft); border-bottom-left-radius:5px; }
    .meta { display:block; margin-top:6px; color:var(--muted); font-size:12px; }
    .reply-actions { display:flex; gap:8px; margin-top:8px; }
    .reply-speech { padding:6px 9px; font-size:12px; white-space:nowrap; }
    .composer { position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:min(920px,100%); padding:12px max(16px,env(safe-area-inset-right)) calc(12px + env(safe-area-inset-bottom)) max(16px,env(safe-area-inset-left)); border-top:1px solid var(--line); background:rgba(255,255,255,.98); }
    textarea { width:100%; min-height:86px; max-height:230px; resize:vertical; border:1px solid #bac7d8; border-radius:13px; padding:12px; font:inherit; color:var(--ink); }
    .voice-controls { display:flex; align-items:center; gap:8px; min-width:0; }
    #voiceRecordBtn.recording { color:#991b1b; border-color:#ef4444; background:#fef2f2; }
    #voiceStatus { min-width:0; overflow:hidden; color:var(--muted); font-size:12px; text-align:center; text-overflow:ellipsis; white-space:nowrap; }
    .compose-actions { display:grid; grid-template-columns:auto minmax(0,1fr) auto; align-items:center; gap:10px; margin-top:8px; }
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
    .checkpoint-box { padding:12px 16px calc(12px + env(safe-area-inset-bottom)); border-top:1px solid var(--line); display:grid; gap:8px; }
    .checkpoint-box input { width:100%; border:1px solid #bac7d8; border-radius:11px; padding:10px 12px; font:inherit; }
    #deployMeta { color:var(--muted); font-size:13px; line-height:1.4; }
    .context-anchor-body { flex:1; min-height:0; overflow:auto; padding:16px; display:flex; flex-direction:column; gap:10px; }
    #contextAnchorInput { flex:1; min-height:320px; font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }
    #contextAnchorMeta,.context-anchor-help { margin:0; color:var(--muted); font-size:13px; }
    .context-anchor-actions { display:flex; justify-content:flex-end; gap:8px; }
    @media (max-width:620px) { .head { display:grid; grid-template-columns:auto minmax(0,1fr) auto; } .head h1 { text-align:center; } .head-tools { grid-column:1/-1; grid-row:2; justify-content:center; } .profile-tools { display:grid; grid-template-columns:auto minmax(0,1fr) auto; } .profile-tools select { min-width:0; width:100%; } .back { padding:8px 10px; } #mobileStatusSummary { display:flex; } .status-details { display:none; } .status-details.expanded { display:block; } .bubble { max-width:94%; } #chat { padding-left:12px; padding-right:12px; } }
    @media (max-width:620px) {
      .tvbcp-panel { width:100%; max-width:100vw; min-width:0; overflow-x:hidden; }
      .tvbcp-head,.context-anchor-body { min-width:0; max-width:100%; }
      #contextAnchorMeta,.context-anchor-help { overflow-wrap:anywhere; }
      #contextAnchorInput { min-width:0; max-width:100%; }
      #contextAnchorProposeBtn { width:100%; min-width:0; white-space:normal; }
      .context-anchor-actions { width:100%; min-width:0; flex-wrap:wrap; }
      .context-anchor-actions > button { flex:1 1 calc(50% - 4px); min-width:0; padding-left:8px; padding-right:8px; white-space:normal; }
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
        <button id="contextAnchorOpenBtn" type="button">Plán</button>
        <button id="tvbcpOpenBtn" type="button">TVBCP</button>
        <button id="workOpenBtn" type="button">Práce</button>
        <button id="refreshBtn" type="button">Stav</button>
      </div>
      <a class="back" href="/">← Cockpit</a>
    </div>
    <div class="profile-tools">
      <label for="profileSelect">Pracovní profil</label>
      <select id="profileSelect" aria-label="Pracovní profil Human–Adam"></select>
      <button id="profileSwitchBtn" type="button" disabled>Přepnout</button>
    </div>
    <button id="mobileStatusSummary" type="button" aria-expanded="false" aria-controls="statusDetails">
      <span id="mobileStatusText" role="status" aria-live="polite">Odpojeno · Izolovaný workspace · Adam není připojen</span>
      <span id="mobileStatusToggleText">Podrobnosti</span>
    </button>
    <div class="status-details" id="statusDetails">
      <div class="statusline">
        <span class="badge warn" id="connectionBadge">Odpojeno</span>
        <span class="badge" id="profileBadge">Profil: Human–Adam</span>
        <span class="badge" id="threadBadge">Relace: —</span>
        <span class="badge" id="workspaceBadge">Izolovaný workspace</span>
        <span class="badge" id="contextAnchorBadge">Kontext: nepřipnut</span>
        <button class="badge sound-badge warn" id="soundTestBtn" type="button">Zvuk: vyzkoušet</button>
        <button class="badge sound-badge warn" id="mediaSoundTestBtn" type="button">Zvuk média: vyzkoušet</button>
        <audio id="completionMediaAudio" preload="auto" playsinline hidden></audio>
      </div>
      <div id="turnActivity" role="status" aria-live="polite" hidden></div>
    </div>
    <div id="deploymentReceipt" role="status" aria-live="polite" hidden></div>
    <div id="deploymentDiagnostic" role="status" aria-live="polite" hidden></div>
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
    <div id="tvbcpScroll" data-scroll-mode="end-anchor-v3">
      <pre id="tvbcpContent"></pre>
      <div id="tvbcpEnd" aria-hidden="true"></div>
    </div>
  </aside>
  <aside class="tvbcp-panel" id="contextAnchorPanel" hidden aria-label="Připnutý aktivní kontext">
    <div class="tvbcp-head">
      <h2>Aktivní kontext</h2>
      <button id="contextAnchorRefreshBtn" type="button">Obnovit</button>
      <button id="contextAnchorCloseBtn" type="button">Zavřít</button>
    </div>
    <div class="context-anchor-body">
      <p id="contextAnchorMeta">Kontext se načte až po otevření.</p>
      <p class="context-anchor-help">Nech Adama připravit návrh, zkontroluj jej a nejdřív jej soukromě ulož. Připnutý plán se přikládá k tahům; pozastavený zůstává uložený, ale nepřikládá se. Ulož pouze stručný cíl, očíslovaný plán, hotové body, rozhodnutí a další krok. Nevkládej hesla, tokeny, osobní údaje ani absolutní cesty. Novější pokyn v chatu má vždy přednost.</p>
      <textarea id="contextAnchorInput" maxlength="6000" autocomplete="off" placeholder="Cíl:&#10;&#10;Plán:&#10;1. …&#10;&#10;Hotovo:&#10;- …&#10;&#10;Rozhodnutí:&#10;- …&#10;&#10;Další krok:&#10;- …" aria-label="Připnutý aktivní kontext"></textarea>
      <button id="contextAnchorProposeBtn" type="button">Adam: připravit návrh</button>
      <div class="context-anchor-actions">
        <button id="contextAnchorDeleteBtn" type="button">Smazat</button>
        <button id="contextAnchorPauseBtn" type="button">Pozastavit</button>
        <button id="contextAnchorPinBtn" type="button">Připnout</button>
        <button class="primary" id="contextAnchorSaveBtn" type="button">Uložit návrh</button>
      </div>
    </div>
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
      <div id="deployMeta">Nasazení je dostupné až po lokálním WIP checkpointu.</div>
      <button class="audit-action" id="deployAuditBtn" type="button" disabled>Audit nasazení</button>
      <input id="deployConfirmation" maxlength="80" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" placeholder="Po auditu sem vlož potvrzovací větu" hidden disabled>
      <button class="deploy-action" id="deployBtn" type="button" disabled>Ověřit a nasadit</button>
    </div>
  </aside>
</main>
<script>
  const chat = document.getElementById("chat");
  const notice = document.getElementById("notice");
  const deploymentReceipt = document.getElementById("deploymentReceipt");
  const deploymentDiagnostic = document.getElementById("deploymentDiagnostic");
  const mobileStatusSummary = document.getElementById("mobileStatusSummary");
  const mobileStatusText = document.getElementById("mobileStatusText");
  const mobileStatusToggleText = document.getElementById("mobileStatusToggleText");
  const statusDetails = document.getElementById("statusDetails");
  const connectionBadge = document.getElementById("connectionBadge");
  const profileBadge = document.getElementById("profileBadge");
  const threadBadge = document.getElementById("threadBadge");
  const workspaceBadge = document.getElementById("workspaceBadge");
  const contextAnchorBadge = document.getElementById("contextAnchorBadge");
  const soundTestBtn = document.getElementById("soundTestBtn");
  const mediaSoundTestBtn = document.getElementById("mediaSoundTestBtn");
  const completionMediaAudio = document.getElementById("completionMediaAudio");
  const turnActivity = document.getElementById("turnActivity");
  const connectBtn = document.getElementById("connectBtn");
  const profileSelect = document.getElementById("profileSelect");
  const profileSwitchBtn = document.getElementById("profileSwitchBtn");
  const refreshBtn = document.getElementById("refreshBtn");
  const contextAnchorOpenBtn = document.getElementById("contextAnchorOpenBtn");
  const contextAnchorPanel = document.getElementById("contextAnchorPanel");
  const contextAnchorCloseBtn = document.getElementById("contextAnchorCloseBtn");
  const contextAnchorRefreshBtn = document.getElementById("contextAnchorRefreshBtn");
  const contextAnchorMeta = document.getElementById("contextAnchorMeta");
  const contextAnchorInput = document.getElementById("contextAnchorInput");
  const contextAnchorProposeBtn = document.getElementById("contextAnchorProposeBtn");
  const contextAnchorSaveBtn = document.getElementById("contextAnchorSaveBtn");
  const contextAnchorPinBtn = document.getElementById("contextAnchorPinBtn");
  const contextAnchorPauseBtn = document.getElementById("contextAnchorPauseBtn");
  const contextAnchorDeleteBtn = document.getElementById("contextAnchorDeleteBtn");
  const composer = document.getElementById("composer");
  const input = document.getElementById("messageInput");
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
  const workMeta = document.getElementById("workMeta");
  const workChanges = document.getElementById("workChanges");
  const checkpointMessage = document.getElementById("checkpointMessage");
  const checkpointBtn = document.getElementById("checkpointBtn");
  const deployMeta = document.getElementById("deployMeta");
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
  let activeProfileId = "";
  let activeProfileLabel = "Human–Adam";
  let deliveryUncertain = false;
  let deploymentAudit = null;
  let completionAudioContext = null;
  let completionAudioUnlocked = false;
  let completionMediaUrl = "";
  let activeSpeechButton = null;
  let activeSpeechUtterance = null;
  let contextAnchorLoaded = false;
  let savedContextAnchorContent = "";
  let savedContextAnchorActive = false;
  let savedContextAnchorRevision = 0;
  const HUMAN_ADAM_SEND_PATH = "/api/human-adam/send";
  const RESULT_WATCH_MAX_ATTEMPTS = 60;
  const RESULT_WATCH_MAX_DELAY_MS = 30000;
  const CONTEXT_ANCHOR_PROPOSAL_PROMPT = `Připrav návrh aktivního kontextu pro další pokračování tohoto pracovního profilu. Odpověz pouze stručným českým textem do 6000 znaků v přesné struktuře:
Cíl:
Plán:
Hotovo:
Rozhodnutí:
Další krok:
Zachyť jen současný plán, prokazatelně hotové body, rozhodnutí a nejmenší další krok. Při nejistotě ji výslovně označ a nic si nevymýšlej. Neuváděj obsah souborů, celé soukromé cesty, hesla, tokeny, klíče, osobní údaje ani citlivé texty.`;
  const CONTEXT_ANCHOR_REQUIRED_HEADINGS = ["Cíl:", "Plán:", "Hotovo:", "Rozhodnutí:", "Další krok:"];

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

  function discardCompletionAudioContext() {
    const previous = completionAudioContext;
    completionAudioContext = null;
    completionAudioUnlocked = false;
    if (!previous || previous.state === "closed" || typeof previous.close !== "function") return;
    try {
      const closing = previous.close();
      if (closing && typeof closing.catch === "function") closing.catch(() => {});
    } catch (_error) {
      // Výměna iOS audiokontextu je best-effort a nesmí blokovat komunikaci.
    }
  }

  function getCompletionAudioContext() {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return null;
    if (completionAudioContext && completionAudioContext.state === "closed") {
      completionAudioContext = null;
      completionAudioUnlocked = false;
    }
    if (!completionAudioContext) {
      completionAudioContext = new AudioContextClass();
      const observedContext = completionAudioContext;
      observedContext.addEventListener("statechange", () => {
        if (completionAudioContext !== observedContext) return;
        const ready = observedContext.state === "running" && completionAudioUnlocked;
        updateCompletionSoundUi(ready);
      });
    }
    return completionAudioContext;
  }

  function updateCompletionSoundUi(ready, supported=true) {
    soundTestBtn.textContent = !supported ? "Zvuk: nepodporován" : (ready ? "Zvuk: kanál aktivní" : "Zvuk: vyzkoušet");
    soundTestBtn.className = ready ? "badge sound-badge ok" : "badge sound-badge warn";
    soundTestBtn.disabled = !supported;
  }

  async function ensureCompletionAudioRunning(context) {
    if (!context) return false;
    if (["suspended", "interrupted"].includes(String(context.state || ""))) {
      const resumeAttempt = context.resume();
      await Promise.race([
        resumeAttempt,
        new Promise((resolve) => window.setTimeout(resolve, 500)),
      ]);
    }
    return context.state === "running";
  }

  async function primeCompletionSound({fresh=false}={}) {
    try {
      configureCompletionAudioSession();
      if (fresh) discardCompletionAudioContext();
      const context = getCompletionAudioContext();
      if (!context) {
        updateCompletionSoundUi(false, false);
        return false;
      }
      if (!await ensureCompletionAudioRunning(context)) throw new Error("Audiokanál se neotevřel.");
      const source = context.createBufferSource();
      source.buffer = context.createBuffer(1, 1, 22050);
      source.connect(context.destination);
      source.start(0);
      completionAudioUnlocked = true;
      updateCompletionSoundUi(true);
      return true;
    } catch (_error) {
      completionAudioUnlocked = false;
      updateCompletionSoundUi(false);
      return false;
    }
  }

  async function playCompletionSound() {
    try {
      const context = getCompletionAudioContext();
      if (!context || !completionAudioUnlocked) return false;
      if (!await ensureCompletionAudioRunning(context)) return false;
      const start = context.currentTime + 0.02;
      const notes = [
        {frequency:740, offset:0, duration:0.16},
        {frequency:988, offset:0.18, duration:0.24},
      ];
      for (const note of notes) {
        const oscillator = context.createOscillator();
        const gain = context.createGain();
        const noteStart = start + note.offset;
        const noteEnd = noteStart + note.duration;
        oscillator.type = "sine";
        oscillator.frequency.setValueAtTime(note.frequency, noteStart);
        gain.gain.setValueAtTime(0.0001, noteStart);
        gain.gain.exponentialRampToValueAtTime(0.12, noteStart + 0.025);
        gain.gain.exponentialRampToValueAtTime(0.0001, noteEnd);
        oscillator.connect(gain);
        gain.connect(context.destination);
        oscillator.start(noteStart);
        oscillator.stop(noteEnd + 0.02);
      }
      updateCompletionSoundUi(true);
      return true;
    } catch (_error) {
      // Zvuk je pouze doplňkový; nesmí změnit potvrzený stav dokončeného tahu.
      updateCompletionSoundUi(false);
      return false;
    }
  }

  async function testCompletionSound() {
    soundTestBtn.disabled = true;
    const ready = await primeCompletionSound({fresh:true});
    const played = ready && await playCompletionSound();
    soundTestBtn.textContent = played ? "Test zvuku odeslán" : "Zvuk: zkusit znovu";
    soundTestBtn.className = played ? "badge sound-badge ok" : "badge sound-badge warn";
    soundTestBtn.disabled = false;
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

  async function testCompletionMediaSound() {
    mediaSoundTestBtn.disabled = true;
    try {
      const source = completionMediaWavUrl();
      if (!source) throw new Error("Mediální zvuk není podporovaný.");
      stopCompletionMediaSound();
      if (completionMediaAudio.src !== source) {
        completionMediaAudio.src = source;
        completionMediaAudio.load();
      }
      completionMediaAudio.volume = 1;
      const playback = completionMediaAudio.play();
      if (playback && typeof playback.then === "function") await playback;
      mediaSoundTestBtn.textContent = "Test média odeslán";
      mediaSoundTestBtn.className = "badge sound-badge ok";
    } catch (_error) {
      mediaSoundTestBtn.textContent = "Zvuk média: zkusit znovu";
      mediaSoundTestBtn.className = "badge sound-badge warn";
    } finally {
      mediaSoundTestBtn.disabled = false;
    }
  }

  function contextAnchorDraftDirty() {
    return contextAnchorLoaded && contextAnchorInput.value.trim() !== savedContextAnchorContent;
  }

  async function restoreCompletionAudioAfterVisibility() {
    if (document.hidden || !completionAudioUnlocked || !completionAudioContext) return;
    try {
      const ready = await ensureCompletionAudioRunning(completionAudioContext);
      updateCompletionSoundUi(ready);
    } catch (_error) {
      updateCompletionSoundUi(false);
    }
  }

  function syncControls() {
    const anchorMutationBlocked = busy || sendInFlight || sessionTurnBusy;
    const anchorDirty = contextAnchorDraftDirty();
    const anchorHasContent = Boolean(savedContextAnchorContent);
    connectBtn.disabled = busy;
    profileSelect.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing;
    profileSwitchBtn.disabled = profileSelect.disabled || !profileSelect.value || profileSelect.value === activeProfileId;
    refreshBtn.disabled = busy || resultWatchActive;
    refreshBtn.textContent = resultWatchActive ? "Čekám na výsledek…" : "Stav";
    sendBtn.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing;
    voiceRecordBtn.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing;
    voiceRecordBtn.classList.toggle("recording", voiceRecording);
    voiceRecordBtn.textContent = voiceRecording ? "Nahrávám…" : "Nahrát pokyn";
    voiceStopBtn.hidden = !voiceRecording;
    voiceStopBtn.disabled = !voiceRecording;
    contextAnchorSaveBtn.disabled = anchorMutationBlocked || !contextAnchorLoaded || (!anchorDirty && anchorHasContent);
    contextAnchorPinBtn.disabled = anchorMutationBlocked || anchorDirty || !anchorHasContent || savedContextAnchorActive;
    contextAnchorPauseBtn.disabled = anchorMutationBlocked || anchorDirty || !anchorHasContent || !savedContextAnchorActive;
    contextAnchorDeleteBtn.disabled = anchorMutationBlocked || anchorDirty || !anchorHasContent;
    contextAnchorProposeBtn.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing || !sessionConnected;
  }

  function setBusy(value, text="") {
    busy = value;
    syncControls();
    if (text) notice.textContent = text;
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
      text = `${activeProfileLabel} · ${connectionText} · ${workspaceText} · ${adamText}`;
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
    actions.appendChild(button);
    return actions;
  }

  function bubble(text, className, meta, spokenText="") {
    const node = document.createElement("article");
    node.className = `bubble ${className}`;
    node.textContent = text;
    const small = document.createElement("span");
    small.className = "meta";
    small.textContent = meta;
    node.appendChild(small);
    if (spokenText) node.appendChild(answerSpeechControl(spokenText));
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
      if (item.answer) exchange.appendChild(bubble(item.answer, "adam", `Adam · ${formatTime(item.completed_at)} · ${confirmed}`, item.answer));
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

  function renderDeploymentDiagnostic(diagnostic, confirmedCommit = "") {
    const allowedStages = new Set(["audit","gate","receipt","remote_recheck","push","fast_forward","workspace_alignment","restart"]);
    const allowedOutcomes = new Set(["running","passed","failed"]);
    const shortCommit = diagnostic ? String(diagnostic.checkpoint_short || "") : "";
    const stage = diagnostic ? String(diagnostic.stage || "") : "";
    const outcome = diagnostic ? String(diagnostic.outcome || "") : "";
    const message = diagnostic ? String(diagnostic.message || "") : "";
    const updatedTime = diagnostic && diagnostic.updated_at ? formatTime(diagnostic.updated_at) : "";
    const coveredByConfirmation = outcome === "passed" && shortCommit === confirmedCommit;
    const showDiagnostic = Boolean(
      diagnostic
      && /^[0-9a-f]{7}$/.test(shortCommit)
      && allowedStages.has(stage)
      && allowedOutcomes.has(outcome)
      && message
      && updatedTime
      && !coveredByConfirmation
    );
    deploymentDiagnostic.textContent = showDiagnostic
      ? `Poslední nasazení ${shortCommit} · ${message} · ${updatedTime}`
      : "";
    deploymentDiagnostic.className = showDiagnostic ? outcome : "";
    deploymentDiagnostic.hidden = !showDiagnostic;
  }

  function renderStatus(payload) {
    renderProfiles(payload);
    const session = payload && payload.session ? payload.session : null;
    const connected = Boolean(session && session.connected && payload.runtime && payload.runtime.reachable);
    sessionConnected = connected;
    connectionBadge.textContent = connected ? "Připojeno" : "Odpojeno";
    connectionBadge.className = connected ? "badge ok" : "badge warn";
    profileBadge.textContent = `Profil: ${activeProfileLabel}`;
    const thread = session && session.thread_id ? session.thread_id : "";
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
    renderContextAnchorBadge(payload && payload.context_anchor ? payload.context_anchor : null);
    const confirmation = payload && payload.deployment_confirmation ? payload.deployment_confirmation : null;
    const shortCommit = confirmation ? String(confirmation.checkpoint_short || "") : "";
    const completedAt = confirmation ? String(confirmation.completed_at || "") : "";
    const completedTime = completedAt ? formatTime(completedAt) : "";
    const showConfirmation = Boolean(
      confirmation && confirmation.gate_passed === true && /^[0-9a-f]{7}$/.test(shortCommit) && completedTime
    );
    deploymentReceipt.textContent = showConfirmation ? `Nasazeno ${shortCommit} · plná brána prošla · ${completedTime}` : "";
    deploymentReceipt.hidden = !showConfirmation;
    renderDeploymentDiagnostic(
      payload && payload.deployment_diagnostic ? payload.deployment_diagnostic : null,
      showConfirmation ? shortCommit : ""
    );
    renderTurnState(session);
    renderSession(session);
  }

  function renderProfiles(payload) {
    const active = payload && payload.work_profile ? payload.work_profile : {};
    const profiles = payload && Array.isArray(payload.work_profiles) ? payload.work_profiles : [];
    activeProfileId = String(active.id || "");
    activeProfileLabel = String(active.label || "Human–Adam");
    profileSelect.replaceChildren();
    for (const profile of profiles) {
      const option = document.createElement("option");
      option.value = String(profile.id || "");
      option.textContent = String(profile.label || profile.id || "Profil");
      option.selected = option.value === activeProfileId;
      profileSelect.appendChild(option);
    }
    syncControls();
  }

  function showProfileSwitchFailure(message) {
    notice.textContent = message;
    notice.scrollIntoView({block:"nearest",behavior:"smooth"});
  }

  async function switchProfile() {
    if (busy || sendInFlight || sessionTurnBusy) return;
    const targetId = profileSelect.value;
    const targetLabel = profileSelect.options[profileSelect.selectedIndex]?.textContent || targetId;
    if (!targetId || targetId === activeProfileId) return;
    if (input.value.trim()) {
      showProfileSwitchFailure("Nejdřív odešli nebo odstraň rozepsaný pokyn; profil jsem nepřepnul.");
      profileSelect.value = activeProfileId;
      return;
    }
    if (contextAnchorDraftDirty()) {
      showProfileSwitchFailure("Nejdřív ulož nebo výslovně zahoď rozepsanou změnu kotvy; profil jsem nepřepnul.");
      profileSelect.value = activeProfileId;
      return;
    }
    if (!window.confirm(`Přepnout celý pracovní profil na „${targetLabel}“?\n\nPřepne se vlákno, workspace i TVBCP.`)) {
      profileSelect.value = activeProfileId;
      return;
    }
    setBusy(true, `Přepínám pracovní profil na ${targetLabel}…`);
    stopAnswerSpeech(false);
    tvbcpPanel.hidden = true;
    contextAnchorPanel.hidden = true;
    workPanel.hidden = true;
    deploymentAudit = null;
    try {
      const payload = await api("/api/human-adam/profile", {
        method:"POST",
        body:JSON.stringify({profile_id:targetId,confirmed:true}),
      });
      if (!payload.ok) throw new Error(payload.message || "Přepnutí profilu selhalo.");
      resetContextAnchorEditorState();
      renderStatus(payload);
      notice.textContent = `Aktivní pracovní profil: ${activeProfileLabel}.`;
    } catch (error) {
      showProfileSwitchFailure(`Profil nebyl přepnut: ${error.message}`);
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
    if (busy) return;
    setBusy(true, "Načítám stav…");
    try {
      const payload = await api("/api/human-adam/status");
      renderStatus(payload);
      notice.textContent = payload.ok ? "" : (payload.message || "Human–Adam zatím není připravený.");
    } catch (error) { notice.textContent = `Stav nelze načíst: ${error.message}`; }
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
        playCompletionSound();
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
      notice.textContent = "Kanonická relace je připravená.";
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

  function renderContextAnchorBadge(anchor) {
    const failed = Boolean(anchor && anchor.ok === false);
    const active = Boolean(anchor && anchor.ok === true && anchor.active === true);
    const stored = Boolean(anchor && anchor.ok === true && anchor.has_content === true);
    contextAnchorBadge.textContent = failed ? "Kontext: chyba" : (active ? "Kontext: připnut" : (stored ? "Kontext: uložen" : "Kontext: žádný"));
    contextAnchorBadge.className = failed ? "badge warn" : (active ? "badge ok" : "badge");
  }

  function resetContextAnchorEditorState() {
    contextAnchorLoaded = false;
    savedContextAnchorContent = "";
    savedContextAnchorActive = false;
    savedContextAnchorRevision = 0;
    contextAnchorInput.value = "";
    contextAnchorSaveBtn.textContent = "Uložit návrh";
    contextAnchorMeta.textContent = "Kontext se načte až po otevření.";
    syncControls();
  }

  function renderContextAnchorEditor(anchor) {
    renderContextAnchorBadge(anchor);
    if (!anchor || anchor.ok === false) {
      contextAnchorMeta.textContent = anchor && anchor.message ? anchor.message : "Aktivní kontext nelze načíst.";
      return;
    }
    const content = String(anchor.content || "");
    const hasContent = anchor.has_content === true || Boolean(content);
    contextAnchorLoaded = true;
    savedContextAnchorContent = hasContent ? content : "";
    savedContextAnchorActive = hasContent && anchor.active === true;
    contextAnchorInput.value = savedContextAnchorContent;
    contextAnchorSaveBtn.textContent = hasContent ? "Uložit aktualizaci" : "Uložit návrh";
    const revision = Number(anchor.revision || 0);
    savedContextAnchorRevision = Number.isSafeInteger(revision) && revision >= 0 ? revision : 0;
    contextAnchorMeta.textContent = savedContextAnchorActive
      ? `Připnuto · revize ${revision} · ${formatTime(anchor.updated_at)}`
      : (hasContent
        ? `Uloženo a pozastaveno · revize ${revision} · ${formatTime(anchor.updated_at)}`
        : (deliveryUncertain
          ? "Žádná kotva není uložená. Můžeš ji napsat, nebo nechat připravit Adamem; kvůli předchozímu nejistému doručení bude nový odlišný pokyn vyžadovat potvrzení."
          : "Žádná kotva není uložená. Napiš návrh do pole a stiskni Uložit návrh."));
    syncControls();
  }

  async function loadContextAnchor() {
    if (contextAnchorDraftDirty() && !window.confirm("Zahodit rozepsanou změnu a znovu načíst naposledy uloženou kotvu?")) return false;
    contextAnchorRefreshBtn.disabled = true;
    contextAnchorMeta.textContent = "Načítám aktivní kontext…";
    try {
      const payload = await api("/api/human-adam/context-anchor");
      renderContextAnchorEditor(payload);
    } catch (error) {
      contextAnchorMeta.textContent = `Aktivní kontext nelze načíst: ${error.message}`;
    } finally {
      contextAnchorRefreshBtn.disabled = false;
      syncControls();
    }
    return true;
  }

  function openContextAnchor() {
    tvbcpPanel.hidden = true;
    workPanel.hidden = true;
    contextAnchorPanel.hidden = false;
    if (!contextAnchorLoaded) loadContextAnchor();
  }

  function closeContextAnchor() {
    contextAnchorPanel.hidden = true;
  }

  async function changeContextAnchor(operation) {
    if (busy || sendInFlight || sessionTurnBusy) return;
    const content = contextAnchorInput.value.trim();
    if (operation === "save" && !content) {
      contextAnchorMeta.textContent = "Nejdřív napiš stručný aktivní kontext k uložení.";
      contextAnchorInput.focus();
      return;
    }
    if (operation !== "save" && contextAnchorDraftDirty()) {
      contextAnchorMeta.textContent = "Nejdřív ulož nebo obnovou výslovně zahoď rozepsanou změnu.";
      return;
    }
    if (operation === "delete" && !window.confirm("Trvale smazat uloženou kotvu tohoto profilu? Historie chatu se nezmění.")) return;
    const progressMessages = {
      save:"Ukládám aktivní kontext…",
      pin:"Připínám uložený kontext…",
      pause:"Pozastavuji připnutý kontext…",
      delete:"Mažu uložený kontext…",
    };
    setBusy(true);
    contextAnchorMeta.textContent = progressMessages[operation] || "Měním aktivní kontext…";
    try {
      const payload = await api("/api/human-adam/context-anchor", {
        method:"POST",
        body:JSON.stringify({
          operation,
          expected_revision:savedContextAnchorRevision,
          content:operation === "save" ? content : "",
          confirmed:true,
        }),
      });
      if (!payload.ok) {
        const error = new Error(payload.message || "Aktivní kontext nelze uložit.");
        error.status = String(payload.status || "");
        error.currentRevision = Number(payload.current_revision);
        throw error;
      }
      renderContextAnchorEditor(payload);
      const successMessages = {
        save: payload.active
          ? "Aktualizovaná připnutá kotva se použije od příštího tahu."
          : "Kotva je soukromě uložená a zatím se k tahům nepřikládá.",
        pin:"Kotva je připnutá a od příštího tahu se přiloží pouze modelu.",
        pause:"Kotva je pozastavená, zůstává uložená a k tahům se nepřikládá.",
        delete:"Uložená kotva byla smazána; historie chatu se nezměnila.",
      };
      notice.textContent = successMessages[operation] || "Aktivní kontext byl změněn.";
    } catch (error) {
      if (error.status === "human_adam_context_anchor_conflict") {
        const newerRevision = Number.isSafeInteger(error.currentRevision) ? ` Aktuální je revize ${error.currentRevision}.` : "";
        contextAnchorMeta.textContent = `Kotva byla mezitím změněna na jiném zařízení.${newerRevision} Tento editor nic nepřepsal a jeho obsah zůstal zachovaný. Nejdřív si případný rozepsaný text zkopíruj, potom stiskni Obnovit.`;
        notice.textContent = "Konflikt kotvy: novější verze z Macu nebo iPhonu zůstala bezpečně zachovaná.";
      } else {
        contextAnchorMeta.textContent = `Aktivní kontext nebyl změněn: ${error.message}`;
      }
    } finally { setBusy(false); }
  }

  function validContextAnchorProposal(text) {
    const proposal = String(text || "").trim();
    const limit = Number(contextAnchorInput.maxLength) || 6000;
    return Boolean(proposal && proposal.length <= limit && CONTEXT_ANCHOR_REQUIRED_HEADINGS.every((heading) => proposal.includes(heading)));
  }

  async function proposeContextAnchor() {
    if (busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing || !sessionConnected) return;
    if (deliveryUncertain && !window.confirm("Předchozí doručení je nejisté. Odeslat nový odlišný pokyn pouze pro přípravu kotvy? Předchozí pokyn se nebude opakovat.")) return;
    const editorBefore = contextAnchorInput.value;
    if (editorBefore.trim() && !window.confirm("Adamův nový návrh po dokončení nahradí současný obsah editoru. Pokračovat?")) return;
    sendInFlight = true;
    syncControls();
    await primeCompletionSound({fresh:true});
    const sentAt = new Date().toISOString();
    const clientId = messageId();
    const pendingMessage = {user_text:CONTEXT_ANCHOR_PROPOSAL_PROMPT,client_sent_at:sentAt,received_at:sentAt,status:"pending",answer:""};
    const optimistic = lastSession
      ? {...lastSession,turn_busy:true,active_turn:{client_message_id:clientId,started_at:sentAt},messages:[...(lastSession.messages || []),pendingMessage]}
      : {turn_busy:true,active_turn:{client_message_id:clientId,started_at:sentAt},messages:[pendingMessage]};
    renderSession(optimistic);
    renderTurnState(optimistic);
    contextAnchorMeta.textContent = "Adam připravuje návrh; zatím se nic neukládá…";
    notice.textContent = `Odesláno ${formatTime(sentAt)} · Adam připravuje návrh…`;
    let outcomeNotice = "";
    try {
      const payload = await api(HUMAN_ADAM_SEND_PATH, {method:"POST",body:JSON.stringify({message:CONTEXT_ANCHOR_PROPOSAL_PROMPT,client_message_id:clientId,client_sent_at:sentAt})});
      if (!payload.ok) {
        const error = new Error(payload.message || "Příprava návrhu selhala.");
        error.status = String(payload.status || "");
        throw error;
      }
      stopResultWatch();
      renderSession(payload.session);
      renderTurnState(payload.session);
      const entry = payload.entry && typeof payload.entry === "object" ? payload.entry : {};
      const proposal = String(entry.answer || "").trim();
      if (entry.status !== "completed" || entry.delivery_confirmed !== true) {
        const error = new Error("Dokončení návrhu nebylo potvrzeno.");
        error.status = "delivery_unknown";
        throw error;
      }
      if (contextAnchorInput.value !== editorBefore) {
        contextAnchorMeta.textContent = "Editor se během čekání změnil; Adamův návrh zůstal v historii a nebyl vložen.";
        outcomeNotice = "Návrh je potvrzený v historii, ale rozepsaný obsah kotvy jsem nepřepsal.";
      } else if (!validContextAnchorProposal(proposal)) {
        contextAnchorMeta.textContent = "Adamův návrh nemá bezpečnou úplnou strukturu; zůstal pouze v historii.";
        outcomeNotice = "Návrh nebyl vložen ani uložen, protože chybí povinná struktura nebo překročil limit.";
      } else {
        contextAnchorInput.value = proposal;
        contextAnchorMeta.textContent = "Návrh Adama je vložený, ale zatím není uložený. Zkontroluj jej a stiskni Uložit návrh.";
        outcomeNotice = "Adamův návrh je připravený k tvé kontrole; automaticky se neuložil.";
      }
      if (payload.context_anchor_warning) {
        outcomeNotice += ` Upozornění: ${payload.context_anchor_warning}`;
      }
      playCompletionSound();
    } catch (error) {
      const confirmedRejection = new Set(["human_adam_busy","human_adam_send_failed"]).has(error.status);
      outcomeNotice = confirmedRejection
        ? `Příprava návrhu byla odmítnuta: ${error.message}`
        : `Stav doručení návrhu je nejistý: ${error.message} Požadavek neposílej automaticky znovu.`;
      contextAnchorMeta.textContent = "Návrh nebyl vložen ani uložen.";
    } finally {
      sendInFlight = false;
      syncControls();
    }
    await loadStatus();
    if (outcomeNotice) notice.textContent = outcomeNotice;
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
      scrollTvbcpToEnd();
    } catch (error) {
      tvbcpContent.textContent = "";
      tvbcpMeta.textContent = `TVBCP nelze načíst: ${error.message}`;
    } finally { tvbcpRefreshBtn.disabled = false; }
  }

  function openTvbcp() {
    contextAnchorPanel.hidden = true;
    workPanel.hidden = true;
    tvbcpPanel.hidden = false;
    loadTvbcp();
  }

  function closeTvbcp() {
    tvbcpPanel.hidden = true;
  }

  function renderWork(payload) {
    deploymentAudit = null;
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
    checkpointBtn.disabled = !payload.dirty;
    deployAuditBtn.disabled = Boolean(payload.dirty) || !payload.local_checkpoint_ahead;
    deployConfirmation.value = "";
    deployConfirmation.hidden = true;
    deployConfirmation.disabled = true;
    deployBtn.disabled = true;
    if (payload.dirty) deployMeta.textContent = "Nejdřív vytvoř jeden lokální WIP checkpoint.";
    else if (payload.local_checkpoint_ahead) deployMeta.textContent = "Checkpoint čeká na read-only audit cest.";
    else if (checkpointPreserved) deployMeta.textContent = "WIP je bezpečně zachovaný, ale audit je zablokovaný. Nejdřív proveď obnovu nad aktuálním main.";
    else if (payload.workspace_relation === "diverged") deployMeta.textContent = "Audit je zablokovaný: workspace a main se rozešly.";
    else deployMeta.textContent = "Není připravený žádný WIP checkpoint k nasazení.";
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
    contextAnchorPanel.hidden = true;
    tvbcpPanel.hidden = true;
    workPanel.hidden = false;
    loadWork();
  }

  function closeWork() {
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
    } catch (error) {
      failure = `Checkpoint selhal: ${error.message}`;
      await loadWork();
    }
    if (failure) workMeta.textContent = failure;
  }

  function renderDeploymentAudit(payload) {
    deploymentAudit = payload;
    workChanges.replaceChildren();
    for (const item of payload.changes || []) {
      const row = document.createElement("li");
      row.textContent = `${item.status || "?"} · ${item.path || ""}`;
      workChanges.appendChild(row);
    }
    deployMeta.textContent = `Audit OK · ${payload.checkpoint_head} · ${payload.checkpoint_subject} · ${payload.change_count} souborů · vlož přesně: ${payload.confirmation_text}`;
    deployConfirmation.value = "";
    deployConfirmation.hidden = false;
    deployConfirmation.disabled = false;
    deployBtn.disabled = true;
  }

  async function auditDeployment() {
    deployAuditBtn.disabled = true;
    deployBtn.disabled = true;
    deployMeta.textContent = "Ověřuji commit, rodiče, cesty a Git stav…";
    try {
      const payload = await api("/api/human-adam/deploy-audit");
      if (!payload.ok || !payload.ready) throw new Error(payload.message || "Audit nasazení neprošel.");
      renderDeploymentAudit(payload);
    } catch (error) {
      deploymentAudit = null;
      deployMeta.textContent = `Audit nasazení selhal: ${error.message}`;
      deployAuditBtn.disabled = false;
    }
  }

  async function waitForCockpitAndReload(previousPid) {
    for (let attempt = 1; attempt <= 60; attempt += 1) {
      try {
        const response = await fetch("/api/server/health", {cache:"no-store"});
        if (response.ok) {
          const health = await response.json();
          const currentPid = health && health.server ? health.server.pid : 0;
          if (currentPid && currentPid !== previousPid) {
            window.location.reload();
            return;
          }
        }
      } catch (_error) {
        // Očekávané krátké odpojení během restartu Cockpitu.
      }
      deployMeta.textContent = `Nasazeno · čekám na Cockpit ${attempt}/60…`;
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
    }
    deployMeta.textContent = "Checkpoint je nasazený, ale Cockpit se nevrátil v limitu. Použij terminálový fallback.";
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
    deployMeta.textContent = "Spouštím plnou bránu nad přesným checkpointem…";
    let previousPid = 0;
    try {
      const healthResponse = await fetch("/api/server/health", {cache:"no-store"});
      if (healthResponse.ok) {
        const health = await healthResponse.json();
        previousPid = health && health.server ? health.server.pid : 0;
      }
      const payload = await api("/api/human-adam/deploy", {
        method:"POST",
        body:JSON.stringify({confirmation,checkpoint_token:deploymentAudit.checkpoint_token}),
      });
      if (!payload.ok) {
        const deploymentFailure = `Nic nebylo nasazeno: ${payload.message || "plná brána nebo audit selhaly."}`;
        renderDeploymentDiagnostic(payload.deployment_diagnostic || null);
        await loadWork();
        deployMeta.textContent = deploymentFailure;
        return;
      }
      const tests = payload.gate && payload.gate.test_count ? `${payload.gate.test_count} testů` : "plná brána";
      if (!payload.restart || !payload.restart.ok) {
        renderDeploymentDiagnostic(payload.deployment_diagnostic || null);
        deployMeta.textContent = `Checkpoint je nasazený (${tests}), ale automatický restart nezačal. Použij Restart Cockpitu nebo terminálový fallback.`;
        return;
      }
      renderDeploymentDiagnostic(payload.deployment_diagnostic || null);
      deployMeta.textContent = `Nasazeno · ${tests} · Cockpit se restartuje…`;
      await waitForCockpitAndReload(Number(payload.restart.pid || previousPid));
    } catch (error) {
      if (previousPid) {
        deployMeta.textContent = "Spojení se přerušilo; ověřuji, zda probíhá restart po nasazení…";
        await waitForCockpitAndReload(previousPid);
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
    sendInFlight = true;
    syncControls();
    await primeCompletionSound({fresh:true});
    clearMessageInput();
    const sentAt = new Date().toISOString();
    const clientId = messageId();
    const pendingMessage = {user_text:text,client_sent_at:sentAt,received_at:sentAt,status:"pending",answer:""};
    const optimistic = lastSession
      ? {...lastSession, turn_busy:true, active_turn:{client_message_id:clientId,started_at:sentAt}, messages:[...(lastSession.messages || []), pendingMessage]}
      : {turn_busy:true, active_turn:{client_message_id:clientId,started_at:sentAt}, messages:[pendingMessage]};
    renderSession(optimistic);
    renderTurnState(optimistic);
    notice.textContent = `Odesláno ${formatTime(sentAt)} · Adam pracuje…`;
    let failure = "";
    try {
      const payload = await api(HUMAN_ADAM_SEND_PATH, {method:"POST", body:JSON.stringify({message:text,client_message_id:clientId,client_sent_at:sentAt})});
      if (!payload.ok) {
        const error = new Error(payload.message || "Odeslání selhalo.");
        error.status = String(payload.status || "");
        throw error;
      }
      stopResultWatch();
      renderSession(payload.session);
      renderTurnState(payload.session);
      notice.textContent = "Odpověď doručena a potvrzena.";
      if (payload.context_anchor_warning) {
        notice.textContent = `Odpověď doručena. Upozornění: ${payload.context_anchor_warning}`;
      }
      playCompletionSound();
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
      syncControls();
    }
    await loadStatus();
    if (failure) notice.textContent = failure;
  }

  connectBtn.addEventListener("click", connect);
  profileSelect.addEventListener("change", syncControls);
  profileSwitchBtn.addEventListener("click", switchProfile);
  mobileStatusSummary.addEventListener("click", () => {
    setMobileStatusDetails(mobileStatusSummary.getAttribute("aria-expanded") !== "true");
  });
  soundTestBtn.addEventListener("click", testCompletionSound);
  mediaSoundTestBtn.addEventListener("click", testCompletionMediaSound);
  document.addEventListener("visibilitychange", restoreCompletionAudioAfterVisibility);
  window.addEventListener("pagehide", () => {
    stopResultWatch();
    stopAnswerSpeech(false);
    stopCompletionMediaSound();
  });
  refreshBtn.addEventListener("click", handleRefreshStatus);
  contextAnchorOpenBtn.addEventListener("click", openContextAnchor);
  contextAnchorCloseBtn.addEventListener("click", closeContextAnchor);
  contextAnchorRefreshBtn.addEventListener("click", loadContextAnchor);
  contextAnchorProposeBtn.addEventListener("click", proposeContextAnchor);
  contextAnchorInput.addEventListener("input", syncControls);
  contextAnchorSaveBtn.addEventListener("click", () => changeContextAnchor("save"));
  contextAnchorPinBtn.addEventListener("click", () => changeContextAnchor("pin"));
  contextAnchorPauseBtn.addEventListener("click", () => changeContextAnchor("pause"));
  contextAnchorDeleteBtn.addEventListener("click", () => changeContextAnchor("delete"));
  tvbcpOpenBtn.addEventListener("click", openTvbcp);
  tvbcpCloseBtn.addEventListener("click", closeTvbcp);
  tvbcpRefreshBtn.addEventListener("click", loadTvbcp);
  workOpenBtn.addEventListener("click", openWork);
  workCloseBtn.addEventListener("click", closeWork);
  workRefreshBtn.addEventListener("click", loadWork);
  checkpointBtn.addEventListener("click", createCheckpoint);
  deployAuditBtn.addEventListener("click", auditDeployment);
  deployConfirmation.addEventListener("input", () => {
    const required = deploymentAudit ? deploymentAudit.confirmation_text || "" : "";
    deployBtn.disabled = !required || deployConfirmation.value.trim() !== required;
  });
  deployBtn.addEventListener("click", deployCheckpoint);
  voiceRecordBtn.addEventListener("click", startVoiceRecording);
  voiceStopBtn.addEventListener("click", stopVoiceRecording);
  composer.addEventListener("submit", sendMessage);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) sendMessage(event);
  });
  clearMessageInput();
  window.addEventListener("pageshow", clearMessageInput);
  loadStatus();
</script>
</body>
</html>
"""
