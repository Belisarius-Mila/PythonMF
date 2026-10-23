const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");

const html = JSON.parse(fs.readFileSync(0, "utf8"));

function sourceBetween(start, end) {
  const startAt = html.indexOf(start);
  assert.notEqual(startAt, -1, `missing source marker: ${start}`);
  const endAt = html.indexOf(end, startAt + start.length);
  assert.notEqual(endAt, -1, `missing source end marker: ${end}`);
  return html.slice(startAt, endAt);
}

const source = [
  'const LUNA_RELEASE_POLL_INTERVAL_MS = 2500;',
  sourceBetween("function syncControls() {", "function lunaReleaseJobActive"),
  sourceBetween("function lunaReleaseJobActive", "function setBusy("),
  sourceBetween("function updateMobileStatusSummary()", "function elapsedClock"),
  sourceBetween("function setMobileStatusDetails(expanded)", "function updateMobileStatusSummary()"),
  sourceBetween("async function openWork()", "function setWorkHelpOpen("),
  sourceBetween("function closeWork()", "async function createCheckpoint()"),
  sourceBetween("function renderLunaReleaseJob", "function stopLunaReleasePoll"),
  sourceBetween("function stopLunaReleasePoll", "function scheduleLunaReleasePoll"),
  sourceBetween("function scheduleLunaReleasePoll", "async function loadLunaReleaseStatus"),
  sourceBetween("async function loadLunaReleaseStatus", "async function checkLunaReleaseStatus"),
  sourceBetween("async function checkLunaReleaseStatus", "function restoreLunaReleaseState"),
  sourceBetween("function restoreLunaReleaseState", "function exactLunaReleaseCommand"),
  sourceBetween("function exactLunaReleaseCommand", "async function startLunaRelease"),
  sourceBetween("function shouldInterceptLunaReleaseCommand", "async function startLunaRelease"),
  sourceBetween("async function startLunaRelease", "function renderWork("),
  sourceBetween("async function sendMessage(event)", '  composer.addEventListener("submit", sendMessage);'),
  sourceBetween("async function loadStatus()", "function resultWatchTargetId"),
  sourceBetween("async function restoreVerifiedDeploymentResult()", "async function deployCheckpoint()"),
].join("\n");

const audit = {
  ok: true,
  ready: true,
  workstream_id: "project-cockpit",
  executor: {role:"release_executor",model:"test-executor",reasoning_effort:"high",policy_digest:"f".repeat(64)},
  deployment_target: "cockpit",
  deployment_label: "Běžící Samantha / Cockpit",
  expected_origin_head: "a".repeat(40),
  expected_local_head: "b".repeat(40),
  commit_count: 2,
  confirmation_text: "POTVRZUJI PREDANI P+N LUNE",
  message: "Přesný balíček je připravený.",
};

function harness(apiHandler, confirmResult=true) {
  const calls = [];
  const timers = [];
  const element = () => ({
    disabled: false,
    hidden: false,
    value: "",
    textContent: "",
    attributes: {},
    dataset: {},
    focused: false,
    className: "",
    classList: {add() {}, remove() {}, toggle() {}, contains() { return false; }},
    setAttribute(name, value) { this.attributes[name] = value; },
    focus() { this.focused = true; },
  });
  const names = [
    "connectBtn", "profileSelect", "profileSwitchBtn", "refreshBtn", "workOpenBtn",
    "sendBtn", "input", "writeIntentBtn", "voiceRecordBtn", "voiceStopBtn",
    "lunaReleaseStartBtn", "lunaReleaseDryRunBtn", "threadRotationAuditBtn",
    "threadRotationConfirmation", "threadRotationBtn", "developmentTopic",
    "developmentProject", "developmentHandoff", "developmentAcquireProfileBtn",
    "developmentAcquireTerminalBtn", "developmentPauseBtn", "developmentResumeBtn",
    "developmentReleaseBtn", "projectContinuityAuditBtn", "lunaReleaseMeta",
    "lunaReleaseStatus", "connectionBadge", "mobileStatusText", "mobileStatusSummary",
    "lunaReleaseRefreshBtn", "lunaReleaseRepeatActions", "lunaReleaseRepeatBtn",
    "workspaceBadge", "turnActivity", "workPanel", "deployMeta", "workCloseBtn",
    "threadRotationPanel", "tvbcpPanel",
  ];
  const scope = Object.fromEntries(names.map((name) => [name, element()]));
  scope.input.value = "p+n";
  scope.threadRotationConfirmation.value = "";
  scope.busy = false;
  scope.sendInFlight = false;
  scope.sessionTurnBusy = false;
  scope.voiceStarting = false;
  scope.voiceRecording = false;
  scope.voiceTranscribing = false;
  scope.activeWorkstreamId = "project-cockpit";
  scope.activeWorkstreamLabel = "Cockpit";
  scope.sessionConnected = true;
  scope.deliveryUncertain = false;
  scope.connectionBadge.textContent = "Připojeno";
  scope.workPanel.hidden = true;
  scope.workstreamDevelopmentEnabled = true;
  scope.writeIntentArmed = false;
  scope.imageImportFailure = "";
  scope.resultWatchActive = false;
  scope.threadRotationAudit = null;
  scope.developmentSemaphore = {ok:true};
  scope.projectContinuity = {ok:true};
  scope.lastSession = {thread_id:"existing-parent-thread",messages:[]};
  scope.lunaReleaseJob = null;
  scope.lunaReleaseStarting = false;
  scope.lunaReleaseStatusLoaded = true;
  scope.lunaReleasePollTimerId = null;
  scope.currentWorkstreamLiveStatus = null;
  scope.workstreamProductionTarget = "";
  scope.githubBatchAudit = {ok:true,read_only:true,writes_performed:false,state:"aligned",local_head:"b".repeat(40),origin_head:"b".repeat(40)};
  scope.notice = {textContent:""};
  scope.window = {
    confirm: () => confirmResult,
    setTimeout: (callback, delay) => {
      timers.push({callback, delay});
      return timers.length;
    },
    clearTimeout() {},
  };
  scope.api = async (path, options={}) => {
    calls.push({path, options});
    return apiHandler(path, options);
  };
  scope.messageId = () => "human-adam-test-release-001";
  scope.clearCount = 0;
  scope.clearMessageInput = () => {
    scope.clearCount += 1;
    scope.input.value = "";
  };
  scope.renderedSessions = [];
  scope.renderSession = (session) => scope.renderedSessions.push(session);
  scope.renderTurnStates = [];
  scope.renderTurnState = (session) => scope.renderTurnStates.push(session);
  scope.renderStatus = (payload) => { scope.lastSession = payload.session || null; };
  scope.takeVerifiedDeploymentResult = () => null;
  scope.recentServerDeploymentRecord = () => null;
  scope.reconnectAfterVerifiedDeployment = async (payload) => ({payload, reconnected:false});
  scope.verifiedDeploymentSummary = () => "Ověřené nasazení";
  scope.markVerifiedDeploymentSeen = () => {};
  scope.loadWork = async () => null;
  scope.setWorkHelpOpen = () => {};
  scope.setBusy = (value) => {
    scope.busy = value;
    scope.syncControls();
  };
  scope.lastRenderedSession = null;
  scope.HUMAN_ADAM_SEND_PATH = "/api/human-adam/send";
  scope.runSendUiBestEffort = (callback) => callback();
  scope.primeCompletionMediaSound = async () => {};
  scope.formatTime = () => "12:00";
  scope.stopResultWatch = () => {};
  scope.playCompletionMediaSound = () => {};
  scope.prepareImageCandidate = async () => {};
  scope.setWriteIntentArmed = (value) => { scope.writeIntentArmed = value; };
  scope.restoreRejectedMessage = (text) => { scope.input.value = text; };
  scope.getApiCalls = () => calls;
  scope.getTimers = () => timers;
  scope.getReleaseJob = () => scope.lunaReleaseJob;
  scope.getStatusLoaded = () => scope.lunaReleaseStatusLoaded;

  const context = vm.createContext(scope);
  vm.runInContext(`${source}\n;globalThis.testApi = {
    exactLunaReleaseCommand,
    shouldInterceptLunaReleaseCommand,
    startLunaRelease,
    sendMessage,
    loadLunaReleaseStatus,
    restoreLunaReleaseState,
    restoreVerifiedDeploymentResult,
    updateMobileStatusSummary,
    lunaReleasePanelState,
    syncControls,
    setMobileStatusDetails,
    get job() { return lunaReleaseJob; },
    get statusLoaded() { return lunaReleaseStatusLoaded; },
  };`, context);
  return {scope, test:context.testApi, calls, timers};
}

async function main() {
  const emptyStatus = {ok:true, job:null};
  const publication = harness(async () => emptyStatus);
  const live = () => ({schema_version:1, read_only:true, writes_performed:false,
    workstream_id:"project-cockpit", observed_at:"2026-10-23T10:00:00Z",
    main:{state:"aligned",head_short:"b".repeat(12),origin_short:"b".repeat(12),origin_evidence_read_only:true,pending_change_count:0},
    workspaces:{state:"aligned_clean",source_pending_change_count:0},
    runtime:{state:"connected",turn_busy:false},
    deployment:{state:"verified_current",current_head:true,code_stamp_verified:true,main_short:"b".repeat(12),smoke_count:5}});
  publication.test.syncControls();
  assert.equal(publication.scope.lunaReleaseStartBtn.hidden, true, "missing live proof cannot suggest pending publication");
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.test.syncControls();
  assert.equal(publication.test.lunaReleasePanelState().state, "current");
  assert.equal(publication.scope.lunaReleaseStartBtn.hidden, true);
  assert.equal(publication.scope.lunaReleaseStartBtn.disabled, true);
  assert.equal(publication.scope.lunaReleaseRepeatActions.hidden, false);
  assert.equal(publication.scope.lunaReleaseRepeatBtn.disabled, false);
  assert.match(publication.scope.lunaReleaseMeta.textContent, /Vše je aktuální/);
  assert.equal(publication.calls.length, 0, "rendering never starts or audits a release");
  publication.scope.sessionTurnBusy = true;
  publication.test.syncControls();
  assert.equal(publication.scope.lunaReleaseStartBtn.disabled, true);
  assert.equal(publication.scope.lunaReleaseRepeatBtn.disabled, true);
  publication.scope.sessionTurnBusy = false;
  publication.scope.currentWorkstreamLiveStatus.main.pending_change_count = 1;
  publication.scope.currentWorkstreamLiveStatus.main.state = "dirty";
  publication.test.syncControls();
  assert.equal(publication.test.lunaReleasePanelState().state, "blocked");
  assert.equal(publication.scope.lunaReleaseStartBtn.disabled, true);
  assert.equal(publication.scope.lunaReleaseRepeatActions.hidden, true);
  assert.match(publication.scope.lunaReleaseMeta.textContent, /1 pracovní změnu/);
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.scope.currentWorkstreamLiveStatus.workspaces.source_pending_change_count = 1;
  assert.equal(publication.test.lunaReleasePanelState().state, "blocked", "clean clones do not hide dirty source main");
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.scope.currentWorkstreamLiveStatus.main.state = "local_ahead";
  publication.scope.currentWorkstreamLiveStatus.main.origin_short = "a".repeat(12);
  publication.scope.githubBatchAudit = {...publication.scope.githubBatchAudit,state:"ready",origin_head:"a".repeat(40)};
  publication.test.syncControls();
  assert.equal(publication.test.lunaReleasePanelState().state, "pending");
  assert.equal(publication.scope.lunaReleaseStartBtn.disabled, false);
  assert.match(publication.scope.lunaReleaseMeta.textContent, /Čeká publikace/);
  publication.scope.githubBatchAudit = {...publication.scope.githubBatchAudit,state:"aligned",origin_head:"b".repeat(40)};
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.scope.currentWorkstreamLiveStatus.deployment.state = "verified_other_main";
  assert.match(publication.test.lunaReleasePanelState().message, /Čeká nasazení/);
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.scope.currentWorkstreamLiveStatus.main.origin_evidence_read_only = false;
  assert.equal(publication.test.lunaReleasePanelState().state, "unverified");
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.scope.currentWorkstreamLiveStatus.main.origin_short = "a".repeat(12);
  assert.equal(publication.test.lunaReleasePanelState().state, "unverified");
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.scope.currentWorkstreamLiveStatus.runtime.state = "delivery_uncertain";
  assert.equal(publication.test.lunaReleasePanelState().state, "blocked");
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.scope.githubBatchAudit.ok = false;
  assert.equal(publication.test.lunaReleasePanelState().state, "unverified", "stale tracking refs cannot replace a failed fresh audit");
  publication.scope.githubBatchAudit.ok = true;
  publication.scope.currentWorkstreamLiveStatus = live();
  publication.scope.activeWorkstreamId = "project-mmtx";
  assert.equal(publication.test.lunaReleasePanelState().state, "unverified", "Camino/Cockpit proof cannot leak into another workstream");
  publication.scope.currentWorkstreamLiveStatus.workstream_id = "project-mmtx";
  publication.scope.workstreamProductionTarget = "github_pages";
  assert.equal(publication.test.lunaReleasePanelState().state, "unverified", "Cockpit deployment is not a Pages publication");
  publication.scope.lunaReleaseJob = {workstream_id:"project-mmtx", deployment_target:"github_pages", state:"completed",
    push_state:"confirmed",deployment_state:"confirmed",gate:{passed:true,mode:"full",test_count:10},
    verification:{deployment_target:"github_pages",state:"deployed",smoke_http_status:200,main_head:"b".repeat(40)}};
  assert.equal(publication.test.lunaReleasePanelState().state, "current");
  publication.scope.lunaReleaseJob.workstream_id = "project-camino";
  assert.equal(publication.test.lunaReleasePanelState().state, "unverified");
  publication.scope.lunaReleaseStatusLoaded = false;
  publication.test.syncControls();
  assert.equal(publication.scope.lunaReleaseRefreshBtn.disabled, false, "read-only refresh remains usable after status failure");

  const finished = harness(async () => ({ok:true,job:{state:"completed",active:false,updated_at:"2026-10-23T11:00:00Z"}}));
  finished.scope.currentWorkstreamLiveStatus = live();
  await finished.test.loadLunaReleaseStatus();
  assert.equal(finished.scope.currentWorkstreamLiveStatus, null, "a newer terminal receipt invalidates stale work evidence");
  assert.equal(finished.scope.lunaReleaseStartBtn.hidden, true);
  assert.equal(finished.calls.some(call => call.path.endsWith("/start")), false);
  const otherReceipt = harness(async () => ({ok:true,job:{state:"completed",active:false,workstream_id:"project-camino"}}));
  otherReceipt.scope.profileSelect.options = [{value:"project-camino",textContent:"Camino"}];
  await otherReceipt.test.loadLunaReleaseStatus();
  assert.match(otherReceipt.scope.lunaReleaseStatus.textContent, /^Účtenka: Camino/);
  assert.equal(otherReceipt.scope.lunaReleaseStartBtn.hidden, true);

  const exact = harness(async (path) => path.endsWith("/audit") ? audit : emptyStatus);
  for (const command of ["p+n", "p*n", "vše p+n", " P+N "]) {
    assert.equal(exact.test.exactLunaReleaseCommand(command), true, command);
  }
  for (const ordinaryText of ["proč se to nenasadilo p+n?", "prosím p+n teď", "vše p+n prosím", "něco p*n"] ) {
    assert.equal(exact.test.exactLunaReleaseCommand(ordinaryText), false, ordinaryText);
  }
  assert.equal(exact.test.shouldInterceptLunaReleaseCommand("p+n"), true);
  exact.scope.activeWorkstreamId = "project-mmtx";
  assert.equal(exact.test.shouldInterceptLunaReleaseCommand("p+n"), true);
  exact.scope.workstreamDevelopmentEnabled = false;
  assert.equal(exact.test.shouldInterceptLunaReleaseCommand("p+n"), false);

  const pages = harness(async (path) => {
    if (path.endsWith("/audit")) return {...audit, workstream_id:"project-mmtx", deployment_target:"github_pages", deployment_label:"Web GitHub Pages"};
    if (path.endsWith("/start")) return {ok:true,job:{state:"queued",active:true}};
    throw new Error(`unexpected request ${path}`);
  });
  pages.scope.activeWorkstreamId = "project-mmtx";
  await pages.test.sendMessage({preventDefault() {}});
  const pagesStart = pages.calls.find((call) => call.path.endsWith("/start"));
  const pagesBody = JSON.parse(pagesStart.options.body);
  assert.equal(pagesBody.expected_workstream_id,"project-mmtx");
  assert.equal(pagesBody.expected_deployment_target,"github_pages");
  assert.equal(pages.calls.some((call) => call.path === "/api/human-adam/send"),false);

  const stale = harness(async (path) => {
    if (path.endsWith("/audit")) return {...audit,workstream_id:"project-mmtx",deployment_target:"github_pages"};
    if (path.endsWith("/status")) return {ok:true,job:null,session:{messages:[]}};
    throw new Error(`unexpected request ${path}`);
  });
  assert.equal(await stale.test.startLunaRelease(),false);
  assert.equal(stale.calls.some((call) => call.path.endsWith("/start")),false);

  const noParent = harness(async () => { throw new Error("release API must not be called without an existing parent thread"); });
  noParent.scope.lastSession = null;
  assert.equal(await noParent.test.startLunaRelease({userText:"p+n"}), false);
  assert.equal(noParent.calls.length, 0);
  assert.match(noParent.scope.lunaReleaseMeta.textContent, /obnov existující relaci/);

  const cancelled = harness(async (path) => {
    if (path.endsWith("/audit")) return audit;
    throw new Error(`unexpected request ${path}`);
  }, false);
  const cancelledResult = await cancelled.test.startLunaRelease({userText:"p+n"});
  assert.equal(cancelledResult, false);
  assert.equal(cancelled.calls.filter((call) => call.path.endsWith("/audit")).length, 1);
  assert.equal(cancelled.calls.filter((call) => call.path.endsWith("/start")).length, 0);
  assert.equal(cancelled.scope.clearCount, 0);
  assert.equal(cancelled.scope.input.value, "p+n");
  assert.match(cancelled.scope.lunaReleaseMeta.textContent, /zrušeno/);

  let dryRunBody = null;
  const dryRun = harness(async (path, options) => {
    if (path.endsWith("/audit")) return audit;
    if (path.endsWith("/start")) {
      dryRunBody = JSON.parse(options.body);
      return {ok:true, job:{job_id:"dry-run-1",state:"dry_run_completed",active:false,dry_run:true,message:"Zkouška dokončena bez publikování."}};
    }
    if (path === "/api/human-adam/status") return {ok:true,session:{messages:[]}};
    throw new Error(`unexpected request ${path}`);
  });
  assert.equal(await dryRun.test.startLunaRelease({dryRun:true,userText:"Zkouška bez publikování"}), true);
  assert.equal(dryRunBody.dry_run, true);
  assert.equal(dryRunBody.expected_origin_head, audit.expected_origin_head);
  assert.equal(dryRunBody.expected_local_head, audit.expected_local_head);
  assert.equal(dryRun.scope.clearCount, 0);
  assert.equal(dryRun.scope.renderedSessions.length, 0);
  assert.equal(dryRun.scope.renderTurnStates.length, 0);
  assert.equal(dryRun.calls.filter((call) => call.path === "/api/human-adam/send").length, 0);

  const activeJob = {job_id:"release-1",state:"running",active:true,phase:"push",message:"Luna pracuje na balíčku.",dry_run:false};
  const transportFailure = harness(async (path) => {
    if (path.endsWith("/audit")) return audit;
    if (path.endsWith("/start")) throw new Error("connection lost after request");
    if (path.endsWith("/luna-release/status")) return {ok:true,job:activeJob};
    if (path === "/api/human-adam/status") return {ok:true,session:{messages:[]}};
    throw new Error(`unexpected request ${path}`);
  });
  assert.equal(await transportFailure.test.startLunaRelease({userText:"p+n",clientMessageId:"human-adam-original-pn"}), false);
  assert.equal(transportFailure.calls.filter((call) => call.path.endsWith("/start")).length, 1);
  assert.equal(transportFailure.test.job.state, "running");
  assert.match(transportFailure.scope.lunaReleaseStatus.textContent, /Luna pracuje/);
  assert.equal(transportFailure.scope.input.disabled, true);
  assert.equal(transportFailure.scope.sendBtn.disabled, true);

  const failedStatus = harness(async () => { throw new Error("status offline"); });
  failedStatus.scope.lunaReleaseStatusLoaded = true;
  await failedStatus.test.loadLunaReleaseStatus();
  assert.equal(failedStatus.test.statusLoaded, false);
  assert.equal(failedStatus.scope.input.disabled, true);
  assert.equal(failedStatus.scope.sendBtn.disabled, true);
  assert.equal(failedStatus.scope.refreshBtn.disabled, false);
  assert.equal(failedStatus.timers.length, 1);
  assert.equal(failedStatus.timers[0].delay, 2500);

  const originalTranscript = {
    messages:[{
      client_message_id:"human-adam-original-pn",
      user_text:"p+n",
      answer:"Balíček je potvrzeně odeslaný a nasazený.",
      status:"completed",
    }],
  };
  const restored = harness(async (path) => {
    if (path === "/api/human-adam/status") return {ok:true,session:originalTranscript};
    if (path.endsWith("/luna-release/status")) {
      return {ok:true,job:{job_id:"release-1",state:"completed",active:false,returned_to_adam:true,push_state:"confirmed",deployment_state:"confirmed"}};
    }
    throw new Error(`unexpected request ${path}`);
  });
  await restored.test.restoreVerifiedDeploymentResult();
  await restored.test.loadLunaReleaseStatus();
  assert.equal(restored.scope.lastSession.messages[0].client_message_id, "human-adam-original-pn");
  assert.equal(restored.scope.lastSession.messages[0].answer, originalTranscript.messages[0].answer);
  assert.match(restored.scope.lunaReleaseStatus.textContent, /Adam má výsledek/);

  // A persisted release receipt must never replace current conversation state.
  const compact = harness(async () => emptyStatus);
  compact.scope.lunaReleaseJob = {state:"completed", active:false};
  compact.scope.lunaReleaseStatus.textContent = "Dlouhá historická účtenka ".repeat(80);
  compact.test.updateMobileStatusSummary();
  assert.equal(compact.scope.mobileStatusText.textContent, "Připojeno · Adam čeká");
  compact.scope.sessionTurnBusy = true;
  compact.scope.turnActivity.textContent = "Adam pracuje · 02:15";
  compact.test.updateMobileStatusSummary();
  assert.equal(compact.scope.mobileStatusText.textContent, "Adam pracuje · 02:15");
  compact.scope.deliveryUncertain = true;
  compact.scope.lunaReleaseJob = {state:"running", active:true};
  compact.test.updateMobileStatusSummary();
  assert.match(compact.scope.mobileStatusText.textContent, /Stav doručení je nejistý/);
  compact.scope.deliveryUncertain = false;
  compact.scope.sessionTurnBusy = false;
  compact.test.updateMobileStatusSummary();
  assert.equal(compact.scope.mobileStatusText.textContent, "Probíhá publikování · podrobnosti v Práci");
  compact.scope.lunaReleaseJob = {state:"attention", active:false};
  compact.test.updateMobileStatusSummary();
  assert.match(compact.scope.mobileStatusText.textContent, /vyžaduje kontrolu/);
  compact.scope.lunaReleaseStatusLoaded = false;
  compact.scope.lunaReleaseJob = null;
  compact.test.updateMobileStatusSummary();
  assert.match(compact.scope.mobileStatusText.textContent, /Stav publikování se ověřuje/);
  await compact.test.setMobileStatusDetails(true);
  assert.equal(compact.scope.workPanel.hidden, false);
  assert.equal(compact.scope.mobileStatusSummary.attributes["aria-expanded"], "true");
  assert.equal(compact.scope.workCloseBtn.focused, true);
  compact.test.setMobileStatusDetails(false);
  assert.equal(compact.scope.workPanel.hidden, true);
  assert.equal(compact.scope.mobileStatusSummary.attributes["aria-expanded"], "false");
  assert.equal(compact.scope.mobileStatusSummary.focused, true);

  // Restoring a fresh deployment announces it without covering the transcript.
  restored.scope.takeVerifiedDeploymentResult = () => ({main_short:"123456789abc"});
  await restored.test.restoreVerifiedDeploymentResult();
  assert.equal(restored.scope.workPanel.hidden, true);
  assert.match(restored.scope.notice.textContent, /Nasazení dokončeno/);
  assert.equal(restored.scope.lastSession.messages[0].answer, originalTranscript.messages[0].answer);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
