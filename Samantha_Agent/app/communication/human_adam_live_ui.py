"""HA-05 browser monitor. Reads HA-04; never creates or recovers server work."""

HUMAN_ADAM_LIVE_SCRIPT = r"""
function createHumanAdamWorkMonitor(host) {
  const terminal = new Set(["completed", "failed", "not_dispatched"]);
  const states = new Set([...terminal, "accepted", "running", "awaiting_completion", "unverified"]);
  let scope = null, enabled = false, epoch = 0, timer = null, request = null;
  let operation = null, identity = "", clientId = "", cursor = 0, serverGeneration = "";
  let error = "", failures = 0, suspended = false, finished = false, submitted = false;
  let observedAt = "", lastTerminal = "";
  const key = () => `human-adam:work-reference:v1:${scope.workstream_id}`;
  const sameScope = (a, b) => a && b && a.workstream_id === b.workstream_id
    && a.thread_id === b.thread_id && a.connection_generation === b.connection_generation;
  const validId = value => typeof value === "string" && /^[a-f0-9]{32}$/.test(value);
  const validClient = value => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$/.test(value);
  function remember() {
    try {
      host.storage.setItem(key(), JSON.stringify({thread_id:scope.thread_id, operation_id:identity, client_message_id:clientId}));
    } catch (_) {} // The server remains the authority if browser storage is unavailable.
  }
  function restore() {
    try {
      const value = JSON.parse(host.storage.getItem(key()) || "null");
      if (value && value.thread_id === scope.thread_id && (validId(value.operation_id) || validClient(value.client_message_id))) {
        identity = validId(value.operation_id) ? value.operation_id : "";
        clientId = validClient(value.client_message_id) ? value.client_message_id : "";
      }
    } catch (_) {}
  }
  function snapshot() {
    return {enabled, operation, error, observedAt, pendingIdentity:Boolean(clientId), watching:enabled && !finished && !suspended,
      blocked:enabled && (Boolean(error) || Boolean(!operation && !finished)
        || Boolean(operation && !terminal.has(operation.lifecycle_state))),
      active:Boolean(operation && !terminal.has(operation.lifecycle_state)), cursor};
  }
  function changed() { host.onChange(snapshot()); }
  function cancel() {
    if (timer !== null) host.clearTimeout(timer);
    timer = null;
    if (request) request.controller.abort();
    request = null;
  }
  function schedule(delay) {
    if (!enabled || suspended || finished) return;
    if (timer !== null) host.clearTimeout(timer);
    timer = host.setTimeout(() => { timer = null; void poll(); }, delay);
  }
  function validated(value) {
    if (!value || value.schema_version !== 1 || value.read_only !== true || value.writes_performed !== false
      || !validId(value.operation_id) || !validClient(value.client_request_id)
      || !Number.isSafeInteger(value.revision) || value.revision < 1 || value.cursor !== value.revision
      || !states.has(value.lifecycle_state) || !["not_started","pending","confirmed","unknown"].includes(value.delivery_state)
      || !sameScope(value.scope, scope) || value.thread_id !== scope.thread_id
      || !Array.isArray(value.events) || value.events.length > 128
      || typeof value.resync_required !== "boolean" || typeof value.event_gap !== "boolean"
      || !Number.isFinite(Date.parse(value.created_at)) || !Number.isFinite(Date.parse(value.updated_at))) throw new Error("invalid_view");
    if (value.lifecycle_state === "completed" && value.delivery_state !== "confirmed") throw new Error("unconfirmed_completion");
    if (identity && value.operation_id !== identity || clientId && value.client_request_id !== clientId) throw new Error("other_identity");
    let previous = 0;
    for (const event of value.events) {
      if (!Number.isSafeInteger(event.cursor) || event.cursor <= previous || event.cursor > value.cursor
        || typeof event.kind !== "string" || !/^[a-z][a-z_]{1,63}$/.test(event.kind)
        || !Number.isFinite(Date.parse(event.at))) throw new Error("invalid_events");
      previous = event.cursor;
    }
    return structuredClone(value);
  }
  function apply(payload, admission = false) {
    if (!payload || payload.ok !== true || payload.schema_version !== 1 || !Array.isArray(payload.operations)
      || payload.operations.length > 64 || typeof payload.server_generation !== "string" || !payload.server_generation
      || (!admission && (payload.read_only !== true || payload.writes_performed !== false))) throw new Error("invalid_envelope");
    const candidates = payload.operations.filter(value => value && sameScope(value.scope, scope)
      && (!identity || value.operation_id === identity) && (!clientId || value.client_request_id === clientId));
    if ((identity || clientId) && candidates.length !== 1) throw new Error("missing_identity");
    if (!candidates.length) {
      operation = null; finished = true; error = ""; observedAt = new Date(host.now()).toISOString(); changed(); return;
    }
    // Discovery chooses the newest unfinished operation, never a foreign scope.
    candidates.sort((a,b) => Date.parse(b.created_at) - Date.parse(a.created_at));
    const next = validated(candidates.find(value => !terminal.has(value.lifecycle_state)) || candidates[0]);
    if (operation && operation.operation_id === next.operation_id && next.revision < operation.revision) {
      if (admission) return; // A delayed ACK cannot replace the newer read snapshot.
      throw new Error("stale_revision");
    }
    if (operation && next.revision === operation.revision && serverGeneration === payload.server_generation
      && next.lifecycle_state !== operation.lifecycle_state && next.lifecycle_state !== "unverified") throw new Error("conflicting_revision");
    if (operation && terminal.has(operation.lifecycle_state) && next.lifecycle_state !== operation.lifecycle_state) throw new Error("terminal_changed");
    const oldEvents = operation && operation.operation_id === next.operation_id && !next.resync_required ? operation.events : [];
    const events = new Map(oldEvents.map(value => [value.cursor, value]));
    for (const event of next.events) {
      if (events.has(event.cursor) && JSON.stringify(events.get(event.cursor)) !== JSON.stringify(event)) throw new Error("conflicting_event");
      events.set(event.cursor, event);
    }
    next.events = [...events.values()].sort((a,b) => a.cursor-b.cursor).slice(-128);
    operation = next; identity = next.operation_id; clientId = next.client_request_id;
    cursor = next.cursor; serverGeneration = payload.server_generation;
    error = ""; failures = 0; observedAt = new Date(host.now()).toISOString();
    finished = terminal.has(next.lifecycle_state) || next.lifecycle_state === "unverified";
    remember(); changed();
    const terminalKey = `${identity}:${next.revision}:${next.lifecycle_state}`;
    if (finished && lastTerminal !== terminalKey) {
      lastTerminal = terminalKey;
      Promise.resolve(host.onTerminal(next, {notify:submitted})).catch(() => {});
      submitted = false;
    }
  }
  async function poll() {
    if (!enabled || suspended || finished || request) return;
    const token = epoch, controller = new AbortController();
    const active = {controller}; request = active;
    const timeout = host.setTimeout(() => controller.abort(), 5000);
    try {
      const query = {workstream_id:scope.workstream_id, cursor:String(cursor)};
      if (identity) query.operation_id = identity;
      else if (clientId) query.client_message_id = clientId;
      const payload = await host.read(query, controller.signal);
      if (token !== epoch || request !== active || suspended) return;
      apply(payload);
    } catch (_) {
      if (token !== epoch || request !== active || suspended) return;
      failures += 1;
      error = "Průběh teď nelze ověřit. Zadání se znovu neodesílá; čtení zkusím obnovit.";
      changed();
    } finally {
      host.clearTimeout(timeout);
      if (request === active) {
        request = null;
        schedule(failures ? Math.min(10000, 1000 * 2 ** Math.min(failures - 1, 4)) : host.visible() ? 750 : 5000);
      }
    }
  }
  return {
    snapshot,
    configure(protocol, nextScope) {
      const supported = Boolean(protocol && protocol.schema_version === 1 && protocol.server_owned === true
        && protocol.read_path === "/api/human-adam/work" && protocol.start_path === "/api/human-adam/work/start"
        && protocol.replays_on_restart === false && nextScope.workstream_id && nextScope.thread_id
        && Number.isSafeInteger(nextScope.connection_generation));
      if (supported === enabled && sameScope(scope, nextScope)) return;
      epoch += 1; cancel(); enabled = supported; scope = {...nextScope};
      operation = null; identity = ""; clientId = ""; cursor = 0; serverGeneration = "";
      error = ""; failures = 0; finished = false; submitted = false; observedAt = ""; lastTerminal = "";
      if (enabled) { restore(); schedule(0); }
      changed();
    },
    expect(value) {
      if (!enabled || !validClient(value) || snapshot().blocked) throw new Error("work_not_ready");
      epoch += 1; cancel(); identity = ""; clientId = value; operation = null;
      cursor = 0; finished = false; submitted = true; error = ""; observedAt = ""; lastTerminal = "";
      remember(); changed(); schedule(750);
    },
    accepted(payload) {
      if (!enabled || !clientId || !submitted) return false;
      try { apply(payload, true); } catch (_) { this.uncertain(); return false; }
      schedule(0); return true;
    },
    uncertain() { error = "Přijetí zatím není ověřené. Pouze hledám původní práci; zadání neposílej znovu."; changed(); schedule(0); },
    refresh() { if (!enabled) return; finished = false; failures = 0; schedule(0); },
    pause() { epoch += 1; suspended = true; cancel(); changed(); },
    resume() { suspended = false; changed(); schedule(0); },
    wake() { if (!suspended && enabled && !finished) schedule(0); },
  };
}

function humanAdamLiveSummary(view) {
  if (!view || !view.enabled) return "";
  if (view.error) return "Průběh práce není ověřen";
  const operation = view.operation;
  if (!operation) return view.blocked ? view.pendingIdentity ? "Čekám na potvrzení přijetí" : "Načítám stav práce" : "";
  return ({accepted:"Pokyn přijat · čeká na zpracování", running:"Adam pracuje",
    awaiting_completion:"Ověřuji a dokončuji výsledek", completed:"Práce dokončena",
    failed:"Práce vyžaduje kontrolu", not_dispatched:"Pokyn nebyl spuštěn",
    unverified:"Stav původní práce není ověřen"})[operation.lifecycle_state];
}

function renderHumanAdamLiveCard(doc, view, now = Date.now()) {
  const card = doc.getElementById("liveWorkCard");
  card.hidden = !view.enabled || !(view.operation || view.blocked || view.error);
  if (card.hidden) return;
  const set = (id, value) => { const node = doc.getElementById(id); if (node.textContent !== value) node.textContent = value; };
  const operation = view.operation;
  set("liveWorkTitle", `${operation && ["completed","failed","not_dispatched"].includes(operation.lifecycle_state) ? "Poslední práce · " : ""}${humanAdamLiveSummary(view)}`);
  card.dataset.state = view.error ? "unverified" : operation ? operation.lifecycle_state : "accepted";
  set("liveWorkReadState", view.error || (view.watching ? "Průběh se obnovuje automaticky." : "Sledování skončilo. Stav můžeš znovu ověřit."));
  const checked = Date.parse(view.observedAt);
  set("liveWorkObserved", Number.isFinite(checked) ? `Poslední úspěšné čtení: ${new Date(checked).toLocaleTimeString("cs-CZ")}` : "Stav ještě nebyl načten.");
  const updated = operation ? Date.parse(operation.updated_at) : NaN;
  set("liveWorkUpdated", Number.isFinite(updated) ? `Poslední zaznamenaná změna: ${new Date(updated).toLocaleTimeString("cs-CZ")}` : "Zatím bez potvrzené aktualizace.");
  const start = operation ? Date.parse(operation.created_at) : NaN;
  const end = operation && ["completed","failed","not_dispatched"].includes(operation.lifecycle_state) ? updated : now;
  const seconds = Number.isFinite(start) ? Math.max(0,Math.floor((end-start)/1000)) : null;
  set("liveWorkDuration", seconds === null ? "" : `Od přijetí: ${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,"0")}`);
  const labels = {accepted:"Pokyn byl přijat", model_dispatching:"Předání Adamovi", turn_acknowledged:"Adam přijal tah",
    turn_started:"Adam zpracovává zadání", tool_started:"Probíhá práce s nástrojem", tool_finished:"Nástroj dokončil krok",
    message_started:"Adam připravuje odpověď", message_finished:"Dílčí zpráva dokončena", plan:"Plán byl aktualizován",
    turn_completed:"Modelový tah skončil", execution_finished:"Zpracování skončilo", completion_updated:"Stav dokončování se změnil",
    execution_unverified:"Výsledek vyžaduje ověření", event_gap:"Část průběhu není k dispozici"};
  const events = operation && !view.error ? operation.events : [];
  const latest = [...events].reverse().find(item => labels[item.kind]);
  set("liveWorkActivity", operation && operation.lifecycle_state === "awaiting_completion" ? "Čekám na dokončovací kontrolu."
    : latest ? labels[latest.kind] : "Aktuální činnost není doložena.");
  set("liveWorkGap", operation && (operation.event_gap || operation.resync_required)
    ? "Historie má mezeru. Zobrazený stav vychází z úplného aktuálního snímku." : "");
  // Only an explicitly public server projection is eligible for display.
  // Never fall back to raw event params, tool arguments or reasoning.
  const publicView = operation && operation.lifecycle_state !== "unverified" && !view.error && operation.public_progress;
  const safe = publicView && publicView.schema_version === 1 && publicView.source === "validated_public_progress";
  const plan = safe && Array.isArray(publicView.plan) && publicView.plan.length <= 128
    && publicView.plan.every(item => item && typeof item.step === "string" && item.step.length <= 8192
      && ["pending","inProgress","completed"].includes(item.status)) ? publicView.plan : [];
  const comments = safe && Array.isArray(publicView.comments) && publicView.comments.length <= 32
    && publicView.comments.every(item => item && typeof item.text === "string" && item.text.length <= 4000
      && typeof item.id === "string") ? publicView.comments : [];
  const renderList = (id, values, label) => {
    const list = doc.getElementById(id), fingerprint = JSON.stringify(values);
    if (list.dataset.fingerprint === fingerprint) return;
    list.dataset.fingerprint = fingerprint;
    list.replaceChildren(...values.map(value => { const node=doc.createElement("li"); node.textContent=label(value); return node; }));
  };
  renderList("liveWorkPlan", plan, item => `${({pending:"Čeká",inProgress:"Probíhá",completed:"Hotovo"})[item.status]}: ${item.step}`);
  set("liveWorkPlanEmpty", plan.length ? "" : "Obsah plánu zatím není k dispozici.");
  renderList("liveWorkComments", comments, item => item.text);
  set("liveWorkTruncated", safe && (publicView.plan_truncated === true || publicView.comments_truncated === true) ? "Zobrazený plán nebo průběžné zprávy jsou zkrácené." : "");
  renderList("liveWorkEvents", events.slice(-8).filter(item => labels[item.kind]), item => `${new Date(item.at).toLocaleTimeString("cs-CZ")} · ${labels[item.kind]}`);
}
"""
