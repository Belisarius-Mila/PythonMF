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
    .handoff-proposal-box { margin:12px 16px; padding:14px; border:1px solid #93c5fd; border-radius:13px; display:grid; gap:8px; background:#eff6ff; }
    .handoff-proposal-box h3 { margin:0; font-size:15px; }
    #handoffProposalMeta { margin:0; color:var(--muted); font-size:13px; overflow-wrap:anywhere; }
    #handoffProposalDraft { margin:0; padding:12px; border:1px solid #bfdbfe; border-radius:10px; background:#fff; white-space:pre-wrap; overflow-wrap:anywhere; font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }
    .deployment-completion-box { margin:12px 16px; padding:14px; border:1px solid #86efac; border-radius:13px; display:grid; gap:8px; background:#f0fdf4; }
    .deployment-completion-box h3 { margin:0; font-size:15px; }
    .deployment-completion-box p { margin:0; color:var(--muted); font-size:13px; line-height:1.45; overflow-wrap:anywhere; }
    #deploymentCompletionEvidence { margin:0; padding-left:22px; font-size:13px; }
    #deploymentCompletionEvidence li { margin:4px 0; }
    .deployment-completion-box input { width:100%; border:1px solid #86b99a; border-radius:11px; padding:10px 12px; font:inherit; }
    .development-branch-audit-box { padding:12px 16px; border-bottom:1px solid var(--line); display:grid; gap:8px; }
    .development-branch-audit-head { display:flex; align-items:center; gap:8px; }
    .development-branch-audit-head h3 { flex:1; margin:0; font-size:15px; }
    #developmentBranchAuditMeta { margin:0; color:var(--muted); font-size:13px; overflow-wrap:anywhere; }
    #developmentBranchAuditList { max-height:180px; overflow:auto; margin:0; padding:0 0 0 22px; }
    #developmentBranchAuditList li { margin-bottom:6px; overflow-wrap:anywhere; font-size:13px; }
    .checkpoint-box { padding:12px 16px calc(12px + env(safe-area-inset-bottom)); border-top:1px solid var(--line); display:grid; gap:8px; }
    .checkpoint-box input { width:100%; border:1px solid #bac7d8; border-radius:11px; padding:10px 12px; font:inherit; }
    #deployMeta { color:var(--muted); font-size:13px; line-height:1.4; }
    #handoffTakeoverCheck { padding:10px 12px; border:1px solid #f59e0b; border-radius:11px; background:#fffbeb; color:#92400e; font-size:13px; line-height:1.45; overflow-wrap:anywhere; }
    #handoffTakeoverCheck.verified { border-color:#86efac; background:#f0fdf4; color:#166534; }
    .context-anchor-body { flex:1; min-height:0; overflow:auto; padding:16px; display:flex; flex-direction:column; gap:10px; }
    #contextAnchorInput { flex:1; min-height:320px; font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }
    #contextAnchorMeta,.context-anchor-help { margin:0; color:var(--muted); font-size:13px; }
    .context-anchor-actions { display:flex; justify-content:flex-end; gap:8px; }
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
    #workHelpPanel > :not(.workflow-help-head):not(.simple-work-help) { display:none !important; }
    .legacy-work-control { display:none !important; }
    .work-help-panel { flex:0 0 auto; margin:12px 16px; }
    .thread-rotation-box { margin-top:14px; padding-top:12px; border-top:1px solid #dbe3ee; display:grid; gap:8px; }
    .thread-rotation-box h3 { margin:0; font-size:15px; }
    .thread-rotation-actions { display:flex; gap:8px; flex-wrap:wrap; }
    #threadRotationConfirmation { width:100%; min-width:0; }
    @media (max-width:620px) { .head { display:grid; grid-template-columns:auto minmax(0,1fr) auto; } .head h1 { text-align:center; } .head-tools { grid-column:1/-1; grid-row:2; justify-content:center; } .profile-tools { display:grid; grid-template-columns:auto minmax(0,1fr) auto; } .profile-tools select { min-width:0; width:100%; } .back { padding:8px 10px; } #mobileStatusSummary { display:flex; } .status-details { display:none; } .status-details.expanded { display:block; } .bubble { max-width:94%; } #chat { padding-left:12px; padding-right:12px; } }
    @media (max-width:620px) {
      .tvbcp-panel { width:100%; max-width:100vw; min-width:0; overflow-x:hidden; }
      .tvbcp-head,.context-anchor-body { min-width:0; max-width:100%; }
      #contextAnchorMeta,.context-anchor-help { overflow-wrap:anywhere; }
      #contextAnchorInput { min-width:0; max-width:100%; }
      #contextAnchorProposeBtn { width:100%; min-width:0; white-space:normal; }
      .context-anchor-actions { width:100%; min-width:0; flex-wrap:wrap; }
      .context-anchor-actions > button { flex:1 1 calc(50% - 4px); min-width:0; padding-left:8px; padding-right:8px; white-space:normal; }
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
        <button id="contextAnchorOpenBtn" type="button">Plán</button>
        <button id="tvbcpOpenBtn" type="button">TVBCP</button>
        <button id="workOpenBtn" type="button">Práce</button>
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
        <span class="badge" id="contextAnchorBadge">Kontext: nepřipnut</span>
        <button class="badge sound-badge warn" id="mediaSoundTestBtn" type="button">Zvuk odpovědi: vyzkoušet</button>
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
      <button class="workflow-help-trigger" id="planHelpBtn" type="button" aria-label="Nápověda k Plánu a rotaci vlákna" aria-expanded="false" aria-controls="planHelpPanel" title="Jak pracovat s Plánem a rotací">?</button>
      <button id="contextAnchorRefreshBtn" type="button">Obnovit</button>
      <button id="contextAnchorCloseBtn" type="button">Zavřít</button>
    </div>
    <div class="context-anchor-body">
      <section class="workflow-help-panel" id="planHelpPanel" aria-labelledby="planHelpTitle" tabindex="-1" hidden>
        <div class="workflow-help-head">
          <h3 id="planHelpTitle">Jak pracovat s Plánem a rotací</h3>
          <button id="planHelpCloseBtn" type="button">Zavřít návod</button>
        </div>
        <p>Toto je pouze nápověda. Jejím otevřením se nic neukládá, nepřepíná ani neodesílá.</p>

        <h4>Běžná práce s Plánem</h4>
        <ol>
          <li>Vyber správný pracovní profil a klikni na <strong>Připojit</strong>.</li>
          <li>Zkontroluj uložený aktivní kontext. Když se plán změnil, nech připravit návrh a přečti jej.</li>
          <li>Návrh nejdřív ulož a potom připni. Teprve připnutý kontext se přikládá k dalším tahům.</li>
          <li>Pokračuj v běžné práci. Vlákno neotáčej jen preventivně.</li>
        </ol>

        <h4>Kdy přejít do nového vlákna</h4>
        <ul>
          <li>Dosavadní vlákno je příliš dlouhé nebo začíná ztrácet souvislosti.</li>
          <li>Začíná nová ucelená etapa stejného projektu.</li>
          <li>Chceš zachovat profil, workspace a plán, ale pokračovat v čistém Codex vlákně.</li>
        </ul>

        <h4>Bezpečná rotace krok za krokem</h4>
        <ol>
          <li>Počkej na dokončení aktivního tahu a nenechávej rozepsaný pokyn.</li>
          <li>Aktualizuj stručný kontext: Cíl, Plán, Hotovo, Rozhodnutí a Další krok.</li>
          <li>Kontext ulož a připni.</li>
          <li>Klikni na <strong>Prověřit nové vlákno</strong> a přečti případné blokery.</li>
          <li>Po zelené kontrole vlož přesnou nabídnutou potvrzovací větu.</li>
          <li>Klikni na <strong>Přejít do nového vlákna</strong> a ověř nové ID vlákna i správný profil.</li>
        </ol>

        <h4>Když něco nejde</h4>
        <ul>
          <li><strong>Tlačítko je šedé:</strong> připoj profil, dokonči aktivní tah nebo ulož rozepsaný kontext.</li>
          <li><strong>Kotva není aktuální:</strong> obnov návrh, zkontroluj jej, ulož a znovu připni.</li>
          <li><strong>Doručení je nejisté:</strong> pokyn neposílej znovu; nejdřív klikni na Stav.</li>
          <li><strong>Věta nefunguje:</strong> spusť nový audit a použij větu z jeho aktuální kontroly.</li>
          <li><strong>Po rotaci něco chybí:</strong> neposílej vývojový pokyn; nejdřív zkontroluj připnutý kontext.</li>
        </ul>

        <p class="workflow-help-safety"><strong>Nouzový postup:</strong> rotaci neprováděj, nic nemaž a pokračuj ve starém vlákně. Staré vlákno se při rotaci nemaže ani nearchivuje.</p>
      </section>
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
      <section class="thread-rotation-box" aria-label="Bezpečná rotace profilového vlákna">
        <h3>Nové profilové vlákno</h3>
        <p id="threadRotationMeta">Nejdřív připni aktuální kontext a spusť kontrolu připravenosti. Staré vlákno se nemaže ani nearchivuje.</p>
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

        <h4>Běžný vývoj</h4>
        <ol>
          <li>Vyber pracovní proud, například <strong>Human–Adam</strong> nebo <strong>Knihovna</strong>, a klikni na <strong>Připojit</strong>.</li>
          <li>Vývojový úkol napiš přímo Adamovi do textového pole. Nový projekt, tool nebo layer se zakládá pouze v terminálovém dialogu s Adamem.</li>
          <li>Po úspěšné změně Adam automaticky spustí testy, aktualizuje handoff a TVBCP, vytvoří jeden commit přímo v <code>main</code>, pushne jej a synchronizuje čisté profily.</li>
          <li>Okno <strong>Práce</strong> otevři až pro kontrolu stavu nebo nasazení hotového čistého <code>main</code>.</li>
        </ol>

        <h4>Nasazení</h4>
        <ol>
          <li>Workspace musí být čistý, synchronní a odpovídat <code>main</code>.</li>
          <li>Stiskni <strong>Audit nasazení</strong> a přečti výsledek.</li>
          <li>Vlož zobrazenou přesnou větu a stiskni <strong>Ověřit a nasadit</strong>.</li>
          <li>Počkej na řízený restart a potvrzení <strong>Nasazeno a ověřeno</strong>.</li>
        </ol>

        <h4>Když něco nejde</h4>
        <ul>
          <li><strong>Workspace je za <code>main</code>:</strong> při čistém profilu klikni na Připojit.</li>
          <li><strong>Audit nebo nasazení selže:</strong> nic neopakuj naslepo; obnov stav a předej Adamovi přesnou chybu.</li>
          <li><strong>Repo není čisté:</strong> nenasazuj a nech Adama zjistit, co zůstalo rozpracované.</li>
        </ul>

        <p class="workflow-help-safety"><strong>Nouzový postup:</strong> nic nemaž, nepoužívej reset, rebase ani force push. Požádej Adama o read-only kontrolu.</p>
      </div>
      <p>Toto je pouze nápověda. Jejím otevřením se nemění semafor, workspace, checkpoint, větev ani Git.</p>

      <h4>Aktuální jednoduché nasazení</h4>
      <ol>
        <li>Po dokončeném automatickém checkpointu otevři <strong>Práci</strong>. Workspace musí být čistý a odpovídat <code>main</code>.</li>
        <li>Stiskni <strong>Audit nasazení</strong>. Audit ověří přesný <code>main</code>, GitHub a oba profilové workspaces; čistý druhý profil smí být bezpečně dorovnán až při potvrzeném nasazení.</li>
        <li>Vlož zobrazenou přesnou větu a stiskni <strong>Ověřit a nasadit</strong>. Nasazení samo nepoužívá WIP větev, takeover ani vývojový semafor.</li>
        <li>Počkej na řízený restart. Cockpit po návratu sám ověří nový proces, kódový otisk, čistý Git a smoke test 5/5; teprve potom oznámí stav <strong>Nasazeno a ověřeno</strong>.</li>
      </ol>
      <p><strong>Když audit nebo dokončení selže:</strong> nic neposílej znovu naslepo. Obnov stav a předej Adamovi přesnou zobrazenou chybu.</p>

      <h4>Co je co</h4>
      <ul>
        <li><strong>Vývojový semafor</strong> určuje jediného vlastníka zápisu. Ostatní Adamové zůstávají read-only.</li>
        <li><strong>Nový projekt</strong> se zakládá pouze v terminálovém dialogu s Adamem. r-Adam pracuje jen s projekty a handoffy, které už jsou v nabídce.</li>
        <li><strong>WIP větev</strong> bezpečně odděluje jeden vývojový úkol. Není to Codex vlákno a jeho existence nezaplňuje konverzaci.</li>
        <li><strong>Worktree</strong> je oddělená pracovní kopie projektu připojená k určité větvi.</li>
        <li><strong>Projektová vazba</strong> spojuje jeden vývoj se zvoleným projektem a handoffem; audit pouze čte důkazy a nic nepřepisuje.</li>
        <li><strong>Návrh handoffu</strong> se po checkpointu sestaví jen z bezpečných metadat. Zobrazí se k přečtení, ale sám se neuloží.</li>
        <li><strong>Kontrola při převzetí</strong> ověří, zda zvolený handoff patří projektu a je v checkpointu. V této fázi pouze varuje a nasazení neblokuje.</li>
        <li><strong>Potvrzené dokončení</strong> se nabídne až po novém procesu a smoke testu. Zapíše jen commit, testy, restart, smoke test, stav nasazeno a tebou zadaný další krok.</li>
      </ul>

      <h4>Čtyři fáze handoffu od zahájení po nasazení</h4>
      <ol>
        <li>
          <strong>Fáze 1 — projektová vazba a kontrola aktuálnosti.</strong>
          Před první změnou vyber projekt, jeho aktuální handoff a téma práce; potom převezmi semafor. Tlačítko <strong>Prověřit handoff</strong> pouze porovná dostupné důkazy s checkpointem, kotvou a TVBCP.
          <ul>
            <li><strong>Aktuální</strong> znamená, že dostupné důkazy neukazují zaostávání.</li>
            <li><strong>Čeká na aktualizaci</strong> nebo <strong>Nelze ověřit</strong> je zatím varování. Nic se nepřepisuje ani neblokuje.</li>
            <li>Když vybraný projekt nebo handoff nesedí, nepokračuj ve vývoji a oprav výběr ještě před checkpointem.</li>
          </ul>
        </li>
        <li>
          <strong>Fáze 2 — návrh handoffu při checkpointu.</strong>
          Po hotových změnách a testech vytvoř <strong>Checkpoint bez pushnutí</strong>. Cockpit z bezpečných Git metadat zobrazí návrh: téma, checkpoint, změněné soubory, stav a další kroky.
          <ul>
            <li>Návrh si přečti a zkontroluj, zda vystihuje skutečný stav práce.</li>
            <li><strong>Návrh se sám neukládá</strong>, nemění handoff ani nevytváří další commit.</li>
            <li>Nekopíruje chat, obsah změněných souborů, hesla, tokeny ani soukromé texty.</li>
          </ul>
        </li>
        <li>
          <strong>Fáze 3 — kontrola handoffu při převzetí do `main`.</strong>
          Spusť <strong>Audit nasazení</strong>. Vedle běžného Git auditu se zobrazí, zda zvolený handoff patří projektu a zda je obsažen v checkpointu.
          <ul>
            <li><strong>Handoff odpovídá</strong> znamená, že přesný zvolený handoff je součástí checkpointu.</li>
            <li><strong>Handoff chybí</strong> nebo <strong>Nelze ověřit</strong> je v této fázi jen viditelné varování; nasazení zatím neblokuje.</li>
            <li>Převzetí do `main` vždy dál vyžaduje čerstvý audit a jeho přesnou potvrzovací větu.</li>
          </ul>
        </li>
        <li>
          <strong>Fáze 4 — potvrzené dokončení po nasazení.</strong>
          Při samoobslužném nasazení z r-Adama zůstane semafor po pushi aktivní. Počkej na nový Cockpit proces, znovu otevři <strong>Práci</strong> a dokonči zelenou kartu.
          <ul>
            <li>Cockpit musí potvrdit nový proces, správný projekt a handoff, shodu `main` s `origin/main` a smoke test 5/5.</li>
            <li>Zadej nejbližší další krok a přesnou větu <code>POTVRZUJI DOKONCENI HANDOFFU PO NASAZENI</code>.</li>
            <li>Teprve potom se do handoffu přidají ověřená fakta, vznikne jediný dokončovací commit, proběhne push a semafor se uvolní.</li>
            <li>Když karta hlásí <strong>Nelze dokončit</strong>, semafor neuvolňuj a požádej Adama o read-only kontrolu.</li>
          </ul>
        </li>
      </ol>
      <p><strong>Ruční nasazení z terminálového Adama:</strong> zelená karta fáze 4 se sama nepřipraví. Po takeoveru proto ručně proveď restart a smoke test, ověř čistý `main` a teprve potom uvolni semafor.</p>
      <p><strong>Současná hranice:</strong> tvrdá blokace ručního uvolnění semaforu podle aktuálnosti handoffu zatím není zapnutá. Za správné dokončení fáze 4 proto stále odpovídá tento postup.</p>

      <h4>Běžný vývoj z r-Adama</h4>
      <ol>
        <li>Vyber správný profil, klikni na <strong>Připojit</strong> a nech workspace synchronizovat s `main`.</li>
        <li>Pokud projekt v nabídce chybí, zde nepokračuj: založ jej v terminálovém dialogu s Adamem a po synchronizaci se vrať. Jinak vyber projekt a aktuální handoff, do tématu napiš krátký název práce a klikni na <strong>Převzít pro tento profil</strong>.</li>
        <li>Teprve potom zadej vývojový úkol. Druhý Adam zůstane read-only.</li>
        <li>Po dokončení vytvoř <strong>Checkpoint bez pushnutí</strong> s krátkým popisem.</li>
        <li>Spusť <strong>Audit nasazení</strong>, přečti výsledek a použij přesnou potvrzovací větu.</li>
        <li>Po návratu nového Cockpitu znovu otevři <strong>Práci</strong> a potvrď dokončení handoffu. Až tento krok bezpečně uvolní semafor.</li>
      </ol>

      <h4>Vývoj z terminálového Adama</h4>
      <ol>
        <li>Zadej téma a klikni na <strong>Převzít pro terminál</strong>.</li>
        <li>Vývoj patří do izolovaného worktree a vlastní WIP větve.</li>
        <li>Po testech proveď H+C+P: handoff, jeden tematický commit a push WIP větve.</li>
        <li>Takeover do `main` vyžaduje čerstvý audit a přesnou potvrzovací větu.</li>
        <li>Po pushi `main` proveď řízený restart, smoke test a až potom uvolni semafor.</li>
      </ol>

      <h4>Životní cyklus větví</h4>
      <p>Tlačítko <strong>Prověřit WIP větve</strong> pouze čte stav. Nic nemaže ani neaktualizuje ze sítě.</p>
      <ul>
        <li><strong>aktivní · rozpracováno</strong> – worktree obsahuje změny; větev je chráněná.</li>
        <li><strong>aktivní · čisté</strong> – worktree je připojený a čistý; větev zůstává chráněná.</li>
        <li><strong>integrováno do main / obsah je v main</strong> – možný kandidát k později potvrzenému úklidu.</li>
        <li><strong>vědomě archivováno</strong> – větev se záměrně zachovává.</li>
        <li><strong>vyžaduje revizi / nelze ověřit</strong> – nic neuklízet a stav předat Adamovi.</li>
      </ul>
      <p><strong>Kandidát k úklidu neznamená smazáno.</strong> Úklid vždy potřebuje nový audit a samostatné přesné potvrzení.</p>

      <h4>Když něco nejde</h4>
      <ul>
        <li><strong>Semafor nelze převzít:</strong> vývoj už vlastní jiný Adam. Nepřebíjej ho a zjisti jeho téma.</li>
        <li><strong>Checkpoint je šedý:</strong> nejsou změny, semafor vlastní někdo jiný nebo je vývoj pozastavený.</li>
        <li><strong>Nasazení blokuje cizí WIP:</strong> neposílej pokyn znovu a nic neslučuj; nejdřív dokonči nebo bezpečně převezmi původní práci.</li>
        <li><strong>Workspace je za `main`:</strong> při čistém profilu klikni na Připojit a nech jej bezpečně synchronizovat.</li>
        <li><strong>Pozastavit</strong> ponechá stejného vlastníka a blokuje ostatní zápis; <strong>Obnovit</strong> pokračuje a <strong>Uvolnit</strong> projde jen bez čekajícího WIP.</li>
      </ul>

      <p class="workflow-help-safety"><strong>Nouzový postup:</strong> nic nemaž, nepoužívej reset, rebase ani force push. Zachovej semafor i WIP a požádej Adama o read-only audit.</p>
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
    <section class="development-branch-audit-box legacy-work-control" aria-label="Historický životní cyklus vývojových větví">
      <div class="development-branch-audit-head">
        <h3>Životní cyklus WIP větví</h3>
        <button id="developmentBranchAuditBtn" type="button">Prověřit WIP větve</button>
      </div>
      <p id="developmentBranchAuditMeta">Kontrola je pouze read-only a spouští se výslovně.</p>
      <ul id="developmentBranchAuditList" hidden></ul>
    </section>
    <div id="workMeta">Stav se načte až po otevření.</div>
    <ul id="workChanges"></ul>
    <section class="handoff-proposal-box legacy-work-control" id="handoffProposalBox" aria-label="Read-only návrh aktualizace handoffu" hidden>
      <h3>Návrh handoffu po checkpointu</h3>
      <p id="handoffProposalMeta">Návrh zatím není připravený.</p>
      <pre id="handoffProposalDraft" hidden></pre>
    </section>
    <section class="deployment-completion-box legacy-work-control" id="deploymentCompletionBox" aria-label="Potvrzené dokončení handoffu po nasazení" hidden>
      <h3>Potvrzené dokončení po nasazení</h3>
      <p id="deploymentCompletionMeta">Po restartu se ověří skutečný commit, nový proces a smoke test.</p>
      <ul id="deploymentCompletionEvidence" hidden></ul>
      <input id="deploymentCompletionNextStep" maxlength="180" placeholder="Nejbližší další krok" hidden disabled>
      <input id="deploymentCompletionConfirmation" maxlength="80" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" placeholder="Přesná potvrzovací věta" hidden disabled>
      <button class="deploy-action" id="deploymentCompletionBtn" type="button" hidden disabled>Dokončit handoff a uvolnit semafor</button>
      <p id="deploymentCompletionSafety" hidden>Zapíší se pouze uvedená ověřená fakta. Nevkládej hesla, tokeny ani soukromý text.</p>
    </section>
    <div class="checkpoint-box">
      <input class="legacy-work-control" id="checkpointMessage" maxlength="120" placeholder="Historický lokální checkpoint">
      <button class="primary legacy-work-control" id="checkpointBtn" type="button" disabled>Historický lokální checkpoint</button>
      <div id="deployMeta">Nasazení je dostupné až po lokálním WIP checkpointu.</div>
      <div class="legacy-work-control" id="handoffTakeoverCheck" role="status" hidden></div>
      <button class="audit-action" id="deployAuditBtn" type="button" disabled>Audit nasazení</button>
      <input id="deployConfirmation" maxlength="80" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" placeholder="Po auditu sem vlož potvrzovací větu" hidden disabled>
      <button class="deploy-action" id="deployBtn" type="button" disabled>Ověřit a nasadit</button>
    </div>
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
  const developmentBadge = document.getElementById("developmentBadge");
  const contextAnchorBadge = document.getElementById("contextAnchorBadge");
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
  const planHelpBtn = document.getElementById("planHelpBtn");
  const planHelpPanel = document.getElementById("planHelpPanel");
  const planHelpCloseBtn = document.getElementById("planHelpCloseBtn");
  const contextAnchorMeta = document.getElementById("contextAnchorMeta");
  const contextAnchorInput = document.getElementById("contextAnchorInput");
  const contextAnchorProposeBtn = document.getElementById("contextAnchorProposeBtn");
  const contextAnchorSaveBtn = document.getElementById("contextAnchorSaveBtn");
  const contextAnchorPinBtn = document.getElementById("contextAnchorPinBtn");
  const contextAnchorPauseBtn = document.getElementById("contextAnchorPauseBtn");
  const contextAnchorDeleteBtn = document.getElementById("contextAnchorDeleteBtn");
  const threadRotationMeta = document.getElementById("threadRotationMeta");
  const threadRotationConfirmation = document.getElementById("threadRotationConfirmation");
  const threadRotationAuditBtn = document.getElementById("threadRotationAuditBtn");
  const threadRotationBtn = document.getElementById("threadRotationBtn");
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
  const workHelpBtn = document.getElementById("workHelpBtn");
  const workHelpPanel = document.getElementById("workHelpPanel");
  const workHelpCloseBtn = document.getElementById("workHelpCloseBtn");
  const workMeta = document.getElementById("workMeta");
  const workChanges = document.getElementById("workChanges");
  const handoffProposalBox = document.getElementById("handoffProposalBox");
  const handoffProposalMeta = document.getElementById("handoffProposalMeta");
  const handoffProposalDraft = document.getElementById("handoffProposalDraft");
  const deploymentCompletionBox = document.getElementById("deploymentCompletionBox");
  const deploymentCompletionMeta = document.getElementById("deploymentCompletionMeta");
  const deploymentCompletionEvidence = document.getElementById("deploymentCompletionEvidence");
  const deploymentCompletionNextStep = document.getElementById("deploymentCompletionNextStep");
  const deploymentCompletionConfirmation = document.getElementById("deploymentCompletionConfirmation");
  const deploymentCompletionBtn = document.getElementById("deploymentCompletionBtn");
  const deploymentCompletionSafety = document.getElementById("deploymentCompletionSafety");
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
  const developmentBranchAuditBtn = document.getElementById("developmentBranchAuditBtn");
  const developmentBranchAuditMeta = document.getElementById("developmentBranchAuditMeta");
  const developmentBranchAuditList = document.getElementById("developmentBranchAuditList");
  const checkpointMessage = document.getElementById("checkpointMessage");
  const checkpointBtn = document.getElementById("checkpointBtn");
  const deployMeta = document.getElementById("deployMeta");
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
  let deploymentCompletion = null;
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
  let deliveryUncertain = false;
  let deploymentAudit = null;
  const verifiedDeploymentStorageKey = "human-adam:verified-deployment:v1";
  const verifiedDeploymentSeenStorageKey = "human-adam:verified-deployment-seen:v1";
  const verifiedDeploymentMaxAgeMs = 15 * 60 * 1000;
  let developmentSemaphore = null;
  let projectContinuity = null;
  let completionMediaUrl = "";
  let activeSpeechButton = null;
  let activeSpeechUtterance = null;
  let contextAnchorLoaded = false;
  let savedContextAnchorContent = "";
  let savedContextAnchorActive = false;
  let savedContextAnchorRevision = 0;
  let threadRotationAudit = null;
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

  function contextAnchorDraftDirty() {
    return contextAnchorLoaded && contextAnchorInput.value.trim() !== savedContextAnchorContent;
  }

  function syncControls() {
    const anchorMutationBlocked = busy || sendInFlight || sessionTurnBusy;
    const anchorDirty = contextAnchorDraftDirty();
    const anchorHasContent = Boolean(savedContextAnchorContent);
    connectBtn.disabled = busy;
    profileSelect.disabled = busy || sendInFlight || sessionTurnBusy || voiceStarting || voiceRecording || voiceTranscribing;
    profileSwitchBtn.disabled = profileSelect.disabled || !profileSelect.value || profileSelect.value === activeWorkstreamId;
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
    threadRotationAuditBtn.disabled = busy || sendInFlight || sessionTurnBusy || !sessionConnected || anchorDirty;
    const rotationRequired = threadRotationAudit ? String(threadRotationAudit.confirmation_text || "") : "";
    threadRotationConfirmation.disabled = anchorMutationBlocked || !threadRotationAudit || threadRotationAudit.ready !== true;
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
    developmentBranchAuditBtn.disabled = busy;
    syncDeploymentCompletionControls();
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
    renderWorkstreams(payload);
    const session = payload && payload.session ? payload.session : null;
    const connected = Boolean(session && session.connected && payload.runtime && payload.runtime.reachable);
    sessionConnected = connected;
    connectionBadge.textContent = connected ? "Připojeno" : "Odpojeno";
    connectionBadge.className = connected ? "badge ok" : "badge warn";
    profileBadge.textContent = `Proud: ${activeWorkstreamLabel}`;
    profileBadge.dataset.backend = activeWorkstreamBackend;
    const thread = session && session.thread_id ? session.thread_id : "";
    const anchorRevision = Number(payload && payload.context_anchor ? payload.context_anchor.revision || 0 : 0);
    const auditedAnchorRevision = Number(threadRotationAudit ? threadRotationAudit.context_anchor_revision || 0 : 0);
    if (threadRotationAudit && (String(threadRotationAudit.thread_id || "") !== thread || auditedAnchorRevision !== anchorRevision)) {
      resetThreadRotationState("Aktivní vlákno nebo kontext se změnily. Před další rotací spusť novou kontrolu.");
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
    renderDevelopmentBadge(payload && payload.development_semaphore ? payload.development_semaphore : null);
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
    const activeWorkstream = selection && selection.active ? selection.active : {};
    const workstreams = selection && Array.isArray(selection.workstreams) ? selection.workstreams : [];
    activeWorkstreamLabel = String(activeWorkstream.workstream_name || "Pracovní proud");
    workstreamDevelopmentEnabled = capabilities.development !== false;
    workstreamDeploymentEnabled = capabilities.deployment !== false;
    activeWorkstreamId = String(activeWorkstream.workstream_id || "");
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
    if (contextAnchorDraftDirty()) {
      showProfileSwitchFailure("Nejdřív ulož nebo výslovně zahoď rozepsanou změnu kotvy; proud jsem nepřepnul.");
      profileSelect.value = activeWorkstreamId;
      return;
    }
    if (!window.confirm(`Přepnout pracovní proud na „${targetLabel}“?\n\nBezpečně se přepne vlákno, pracovní kontext, handoff a TVBCP; sdílený workspace se předem ověří a synchronizuje.`)) {
      profileSelect.value = activeWorkstreamId;
      return;
    }
    setBusy(true, `Přepínám pracovní proud na ${targetLabel}…`);
    stopAnswerSpeech(false);
    tvbcpPanel.hidden = true;
    contextAnchorPanel.hidden = true;
    workPanel.hidden = true;
    deploymentAudit = null;
    try {
      const payload = await api("/api/human-adam/profile", {
        method:"POST",
        body:JSON.stringify({workstream_id:targetId,confirmed:true}),
      });
      if (!payload.ok) throw new Error(payload.message || "Přepnutí profilu selhalo.");
      resetContextAnchorEditorState();
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
    resetThreadRotationState();
    syncControls();
  }

  function resetThreadRotationState(message="Nejdřív připni aktuální kontext a spusť kontrolu připravenosti. Staré vlákno se nemaže ani nearchivuje.") {
    threadRotationAudit = null;
    threadRotationConfirmation.value = "";
    threadRotationConfirmation.hidden = true;
    threadRotationConfirmation.disabled = true;
    threadRotationBtn.hidden = true;
    threadRotationBtn.disabled = true;
    threadRotationMeta.textContent = message;
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

  function setPlanHelpOpen(open) {
    const expanded = Boolean(open);
    planHelpPanel.hidden = !expanded;
    planHelpBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
    if (expanded) planHelpPanel.focus();
  }

  function closeContextAnchor() {
    setPlanHelpOpen(false);
    contextAnchorPanel.hidden = true;
  }

  function renderThreadRotationAudit(payload) {
    const blockers = payload && Array.isArray(payload.blockers) ? payload.blockers.filter(Boolean) : [];
    if (!payload || payload.ok !== true) {
      resetThreadRotationState(payload && payload.message ? payload.message : "Kontrolu rotace nelze načíst.");
      return;
    }
    if (payload.ready !== true) {
      resetThreadRotationState(`Rotace zatím není připravená: ${blockers.join(" ") || "zkontroluj připojení a aktivní kontext."}`);
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
    if (threadRotationAuditBtn.disabled || contextAnchorDraftDirty()) return;
    setBusy(true, "Ověřuji připnutý kontext, stav tahu a doručení…");
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
    if (threadRotationBtn.disabled || !threadRotationAudit || contextAnchorDraftDirty()) return;
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
      resetThreadRotationState("Nové profilové vlákno bylo založeno. Připnutý kontext se použije při příštím tahu; staré vlákno zůstalo zachované.");
    } catch (error) {
      resetThreadRotationState(`Vlákno nebylo změněno: ${error.message}`);
    } finally { setBusy(false); }
    if (rotated) {
      await loadStatus();
      threadRotationMeta.textContent = "Nové profilové vlákno je aktivní. Připnutý kontext se přiloží k příštímu tahu; staré vlákno zůstalo zachované.";
      notice.textContent = "Rotace dokončena bez odeslání zprávy a bez smazání starého vlákna.";
    }
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
      resetThreadRotationState("Aktivní kontext se změnil. Před rotací spusť novou kontrolu připravenosti.");
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
    await primeCompletionMediaSound();
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
      playCompletionMediaSound();
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
    renderHandoffTakeoverCheck(null);
    renderProjectContinuity(payload.project_continuity || null);
    renderDevelopmentSemaphore(payload.development_semaphore || null);
    renderHandoffProposal(payload.handoff_proposal || null);
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
    checkpointBtn.disabled = !workstreamDevelopmentEnabled || !payload.dirty || semaphore.can_checkpoint !== true;
    const simpleDeployReady = workstreamDeploymentEnabled
      && !payload.dirty
      && !payload.local_checkpoint_ahead
      && payload.workspace_relation === "aligned"
      && Number(payload.source_pending_changes || 0) === 0;
    deployAuditBtn.disabled = !simpleDeployReady;
    deployConfirmation.value = "";
    deployConfirmation.hidden = true;
    deployConfirmation.disabled = true;
    deployBtn.disabled = true;
    if (!workstreamDevelopmentEnabled) deployMeta.textContent = "Tento lazy proud zůstává read-only; zapisovací pilot je zatím povolen jen pro MMTX.";
    else if (!workstreamDeploymentEnabled) deployMeta.textContent = "MMTX pilot může vyvíjet a checkpointovat; nasazení z lazy proudu zatím zůstává zavřené.";
    else if (payload.dirty) deployMeta.textContent = "Nejdřív dokonči automatický checkpoint změn do main.";
    else if (payload.local_checkpoint_ahead) deployMeta.textContent = "Je zachovaný starší lokální checkpoint; nejdřív proveď servisní kontrolu.";
    else if (checkpointPreserved) deployMeta.textContent = "WIP je bezpečně zachovaný, ale audit je zablokovaný. Nejdřív proveď obnovu nad aktuálním main.";
    else if (payload.workspace_relation === "diverged") deployMeta.textContent = "Audit je zablokovaný: workspace a main se rozešly.";
    else if (simpleDeployReady) deployMeta.textContent = "Čistý main je připravený k auditu nasazení.";
    else deployMeta.textContent = "Workspace nejdřív synchronizuj s čistým main.";
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
    } catch (error) {
      workChanges.replaceChildren();
      workMeta.textContent = `Pracovní stav nelze načíst: ${error.message}`;
      checkpointBtn.disabled = true;
    } finally { workRefreshBtn.disabled = false; }
    await loadDeploymentCompletion();
  }

  function syncDeploymentCompletionControls() {
    const required = deploymentCompletion ? deploymentCompletion.confirmation_text || "" : "";
    const ready = deploymentCompletion && deploymentCompletion.ready === true;
    const hasNextStep = deploymentCompletionNextStep.value.trim().length >= 3;
    deploymentCompletionBtn.disabled = busy || !ready || !hasNextStep || deploymentCompletionConfirmation.value.trim() !== required;
  }

  function renderDeploymentCompletion(payload) {
    deploymentCompletion = payload && typeof payload === "object" ? payload : null;
    const visible = deploymentCompletion && deploymentCompletion.available === true;
    const ready = visible && deploymentCompletion.ready === true;
    deploymentCompletionBox.hidden = !visible;
    deploymentCompletionEvidence.replaceChildren();
    for (const item of visible && Array.isArray(deploymentCompletion.evidence) ? deploymentCompletion.evidence : []) {
      const row = document.createElement("li");
      row.textContent = `${item.ok === true ? "OK" : "ČEKÁ"} · ${item.label || "Důkaz"}`;
      deploymentCompletionEvidence.appendChild(row);
    }
    deploymentCompletionEvidence.hidden = !deploymentCompletionEvidence.children.length;
    if (!visible) {
      deploymentCompletionMeta.textContent = "Po restartu se ověří skutečný commit, nový proces a smoke test.";
      deploymentCompletionNextStep.value = "";
      deploymentCompletionConfirmation.value = "";
    } else {
      const target = deploymentCompletion.target_handoff ? ` · ${String(deploymentCompletion.target_handoff).split("/").pop()}` : "";
      deploymentCompletionMeta.textContent = `${deploymentCompletion.label || "Dokončení"} · ${deploymentCompletion.message || ""}${target}`;
    }
    for (const element of [deploymentCompletionNextStep,deploymentCompletionConfirmation,deploymentCompletionBtn,deploymentCompletionSafety]) {
      element.hidden = !ready;
    }
    deploymentCompletionNextStep.disabled = !ready;
    deploymentCompletionConfirmation.disabled = !ready;
    if (!ready) deploymentCompletionConfirmation.value = "";
    syncDeploymentCompletionControls();
  }

  async function loadDeploymentCompletion() {
    try {
      const payload = await api("/api/human-adam/deployment-completion");
      renderDeploymentCompletion(payload);
    } catch (error) {
      renderDeploymentCompletion({ok:false,available:true,ready:false,state:"unverifiable",label:"Nelze dokončit",message:error.message,evidence:[]});
    }
  }

  async function finalizeDeploymentCompletion() {
    if (deploymentCompletionBtn.disabled || !deploymentCompletion) return;
    deploymentCompletionBtn.disabled = true;
    deploymentCompletionMeta.textContent = "Znovu ověřuji důkazy, zapisuji handoff a pushuji jediný dokončovací commit…";
    try {
      const payload = await api("/api/human-adam/deployment-completion", {
        method:"POST",
        body:JSON.stringify({
          confirmation:deploymentCompletionConfirmation.value.trim(),
          next_step:deploymentCompletionNextStep.value.trim(),
        }),
      });
      if (!payload.ok) throw new Error(payload.message || "Dokončení handoffu selhalo.");
      deploymentCompletionNextStep.value = "";
      deploymentCompletionConfirmation.value = "";
      renderDeploymentCompletion(payload);
      notice.textContent = payload.release_message || "Handoff byl potvrzeně dokončen.";
      await loadWork();
      await loadStatus();
    } catch (error) {
      deploymentCompletionMeta.textContent = `Dokončení bylo bezpečně zastaveno: ${error.message}`;
      await loadDeploymentCompletion();
    }
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
    projectContinuityMeta.textContent = "Prověřuji vazbu, handoff, kotvu, TVBCP a nasazení bez zápisu…";
    try {
      const payload = await api("/api/human-adam/project-continuity");
      renderProjectContinuity(payload);
    } catch (error) {
      projectContinuityMeta.textContent = `Audit kontinuity selhal bezpečně: ${error.message}`;
    } finally {
      projectContinuityAuditBtn.disabled = busy;
    }
  }

  function renderDevelopmentBranchAudit(payload) {
    developmentBranchAuditList.replaceChildren();
    const branches = Array.isArray(payload.branches) ? payload.branches : [];
    const labels = {
      active_dirty_worktree:"aktivní · rozpracováno",
      active_clean_worktree:"aktivní · čisté",
      merged:"integrováno do main",
      patch_equivalent:"obsah je v main",
      archived:"vědomě archivováno",
      needs_review:"vyžaduje revizi",
      unverified:"nelze ověřit",
      unverified_worktree:"worktree nelze ověřit",
    };
    for (const item of branches) {
      const row = document.createElement("li");
      const label = labels[item.classification] || String(item.classification || "neznámý stav");
      row.textContent = `${item.name || "neznámá větev"} · ${label} · ${item.reason || ""}`;
      developmentBranchAuditList.appendChild(row);
    }
    developmentBranchAuditList.hidden = !branches.length;
    developmentBranchAuditMeta.textContent = `Větve: ${Number(payload.branch_count || 0)} · aktivní: ${Number(payload.active_worktree_count || 0)} · kandidáti k později potvrzenému úklidu: ${Number(payload.cleanup_candidate_count || 0)} · revize: ${Number(payload.needs_review_count || 0)}. Nic nebylo změněno.`;
  }

  async function loadDevelopmentBranchAudit() {
    developmentBranchAuditBtn.disabled = true;
    developmentBranchAuditMeta.textContent = "Prověřuji Git větve bez změn…";
    try {
      const payload = await api("/api/human-adam/development-branches");
      if (!payload.ok) throw new Error(payload.message || "Audit větví nelze dokončit.");
      renderDevelopmentBranchAudit(payload);
    } catch (error) {
      developmentBranchAuditList.replaceChildren();
      developmentBranchAuditList.hidden = true;
      developmentBranchAuditMeta.textContent = `Audit větví selhal bezpečně: ${error.message}`;
    } finally {
      developmentBranchAuditBtn.disabled = busy;
    }
  }

  function openWork() {
    contextAnchorPanel.hidden = true;
    tvbcpPanel.hidden = true;
    workPanel.hidden = false;
    loadWork();
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
    deployMeta.textContent = `Audit OK · main ${payload.main_short || "?"} · ${workstream} · vlož přesně: ${payload.confirmation_text}`;
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
    deployMeta.textContent = "Ověřuji čistý main, GitHub a oba profilové workspaces…";
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
            try {
              const verification = await api("/api/human-adam/deploy-verification", {
                method:"POST",
                body:JSON.stringify({}),
              });
              if (!verification.ok || verification.state !== "deployed") {
                deployMeta.textContent = `Cockpit se vrátil, ale ověření nasazení selhalo: ${verification.message || "chybí úplný důkaz."}`;
                return;
              }
              deployMeta.textContent = verifiedDeploymentSummary(verification);
              if (!storeVerifiedDeploymentResult(verification)) return;
            } catch (error) {
              deployMeta.textContent = `Cockpit se vrátil, ale ověření nasazení nelze dokončit: ${error.message}`;
              return;
            }
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

  function verifiedDeploymentRecord(payload) {
    const mainShort = String(payload && payload.main_short || "").trim().toLowerCase();
    const testCount = Number(payload && payload.gate ? payload.gate.test_count : 0);
    const smokeCount = Number(payload && payload.smoke ? payload.smoke.check_count : 0);
    const deployedAt = String(payload && payload.deployed_at || "").trim();
    const parsedTime = new Date(deployedAt);
    if (!/^[0-9a-f]{7,12}$/.test(mainShort)) return null;
    if (!Number.isInteger(testCount) || testCount <= 0) return null;
    if (smokeCount !== 5 || Number.isNaN(parsedTime.getTime())) return null;
    return {
      schema_version:1,
      main_short:mainShort,
      test_count:testCount,
      smoke_count:smokeCount,
      deployed_at:parsedTime.toISOString(),
      stored_at:Date.now(),
    };
  }

  function verifiedDeploymentSummary(payload) {
    const record = verifiedDeploymentRecord(payload);
    if (!record) return "Nasazeno a ověřeno · úplný serverový důkaz je uložený.";
    return `Nasazeno a ověřeno · main ${record.main_short} · ${record.test_count} testů · smoke ${record.smoke_count}/5 · dokončeno ${formatTime(record.deployed_at)}.`;
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

  async function restoreVerifiedDeploymentResult() {
    let record = takeVerifiedDeploymentResult();
    const statusPayload = await loadStatus();
    if (!record) record = recentServerDeploymentRecord(statusPayload);
    if (!record) return;
    contextAnchorPanel.hidden = true;
    tvbcpPanel.hidden = true;
    workPanel.hidden = false;
    await loadWork();
    deployMeta.textContent = verifiedDeploymentSummary(record);
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
        body:JSON.stringify({confirmation}),
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
    await primeCompletionMediaSound();
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
      playCompletionMediaSound();
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
  mediaSoundTestBtn.addEventListener("click", testCompletionMediaSound);
  window.addEventListener("pagehide", () => {
    stopResultWatch();
    stopAnswerSpeech(false);
    stopCompletionMediaSound();
  });
  refreshBtn.addEventListener("click", handleRefreshStatus);
  contextAnchorOpenBtn.addEventListener("click", openContextAnchor);
  contextAnchorCloseBtn.addEventListener("click", closeContextAnchor);
  planHelpBtn.addEventListener("click", () => setPlanHelpOpen(planHelpPanel.hidden));
  planHelpCloseBtn.addEventListener("click", () => {
    setPlanHelpOpen(false);
    planHelpBtn.focus();
  });
  contextAnchorRefreshBtn.addEventListener("click", loadContextAnchor);
  contextAnchorProposeBtn.addEventListener("click", proposeContextAnchor);
  contextAnchorInput.addEventListener("input", syncControls);
  contextAnchorSaveBtn.addEventListener("click", () => changeContextAnchor("save"));
  contextAnchorPinBtn.addEventListener("click", () => changeContextAnchor("pin"));
  contextAnchorPauseBtn.addEventListener("click", () => changeContextAnchor("pause"));
  contextAnchorDeleteBtn.addEventListener("click", () => changeContextAnchor("delete"));
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
  developmentAcquireProfileBtn.addEventListener("click", () => changeDevelopmentSemaphore("acquire_profile"));
  developmentAcquireTerminalBtn.addEventListener("click", () => changeDevelopmentSemaphore("acquire_terminal"));
  developmentPauseBtn.addEventListener("click", () => changeDevelopmentSemaphore("pause"));
  developmentResumeBtn.addEventListener("click", () => changeDevelopmentSemaphore("resume"));
  developmentReleaseBtn.addEventListener("click", () => changeDevelopmentSemaphore("release"));
  developmentProject.addEventListener("change", () => updateDevelopmentHandoffs(""));
  projectContinuityAuditBtn.addEventListener("click", loadProjectContinuity);
  developmentBranchAuditBtn.addEventListener("click", loadDevelopmentBranchAudit);
  deploymentCompletionNextStep.addEventListener("input", syncDeploymentCompletionControls);
  deploymentCompletionConfirmation.addEventListener("input", syncDeploymentCompletionControls);
  deploymentCompletionBtn.addEventListener("click", finalizeDeploymentCompletion);
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
  restoreVerifiedDeploymentResult();
</script>
</body>
</html>
"""
