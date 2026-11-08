(() => {
  const endpoint = "/api/email-agent/calendar-draft";
  let dialog, ui = {}, item, draft, review, write, generation = 0, busy = false, dirty = false;
  let timer, pollTimer, polls = 0, stopped = false;
  const el = (tag, text) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; return node; };
  function button(text, action, secondary = false) {
    const b = el("button", text); b.type = "button"; if (secondary) b.className = "secondary";
    b.addEventListener("click", action); return b;
  }
  function field(key, title, type = "text") {
    const label = el("label", title), input = el(key === "kind" ? "select" : "input");
    if (key === "kind") for (const [value, title] of [["meeting","Schůzka"],["all_day","Celý den"],["task_deadline","Termín"]]) {
      const option = el("option", title); option.value = value; input.append(option);
    } else input.type = type;
    input.id = `calendarDraft_${key}`;
    input.addEventListener("input", changed); input.addEventListener("change", changed);
    ui[key] = input; label.append(input); return label;
  }
  function create() {
    dialog = el("dialog"); dialog.id = "calendarDraftEditor";
    const form = el("form"); form.addEventListener("submit", event => { event.preventDefault(); submit(); });
    form.append(el("h2", "Do kalendáře")); ui.subject = el("p"); ui.status = el("p");
    ui.status.setAttribute("role", "status"); ui.status.setAttribute("aria-live", "polite");
    form.append(ui.subject, ui.status);
    ui.fields = el("section"); ui.fields.append(field("title", "Název"), field("start", "Začátek", "datetime-local"), field("kind", "Typ"), field("location", "Místo (nepovinné)"));
    form.append(ui.fields); ui.summary = el("p"); ui.conflicts = el("p"); form.append(ui.summary, ui.conflicts);
    ui.link = el("a", "Otevřít událost"); ui.link.hidden = true; form.append(ui.link);
    ui.savedActions=el("div");form.append(ui.savedActions);
    const actions = el("div"); actions.className = "actions";
    ui.write = button("Zapsat do kalendáře", submit); ui.permission = button("Povolit zápis na Macu", authorize, true);
    ui.refresh = button("Obnovit stav", refresh, true); ui.refresh.hidden = true;
    ui.close = button("Zrušit", close, true); actions.append(ui.write, ui.permission, ui.refresh, ui.close); form.append(actions);
    dialog.append(form); dialog.addEventListener("cancel", event => { event.preventDefault(); close(); });
    document.body.append(dialog);
  }
  const values = () => ({title:ui.title.value, start:ui.start.value, kind:ui.kind.value, location:ui.location.value});
  function controls() {
    for (const key of ["title","start","kind","location"]) ui[key].disabled = busy || !draft || Boolean(write && write.state !== "blocked");
    ui.write.disabled = busy || !draft || stopped || write?.state === "verified";
    ui.write.hidden = write?.state === "verified";
    ui.write.textContent = write && ["pending","unknown"].includes(write.state) ? "Ověřit původní zápis" : review?.conflicts?.length ? "Zapsat i přes kolizi" : "Zapsat do kalendáře";
    ui.close.disabled = busy; ui.close.textContent = write?.state === "verified" ? "Zavřít" : "Zrušit";
    ui.permission.disabled = busy; ui.refresh.disabled = busy;
    window.SamanthaCalendarDelete?.update(dialog);
  }
  function render(data, setValues = false) {
    if (data.draft && (!dirty || setValues)) {
      draft = data.draft; const f = draft.fields;
      ui.title.value = f.title; ui.location.value = f.location;
      ui.kind.value = f.kind === "task_deadline" ? "task_deadline" : f.all_day ? "all_day" : "meeting";
      ui.start.type = f.all_day ? "date" : "datetime-local";
      ui.start.value = f.date + (f.start_time && !f.all_day ? "T" + f.start_time : "");
    }
    review = data.review; write = data.write;
    ui.permission.hidden = Boolean(data.writer_built && write?.state !== "blocked");
    ui.fields.hidden = !draft;
    ui.link.hidden = write?.state !== "verified";
    if (!ui.link.hidden) ui.link.href = `/calendar/?email=${encodeURIComponent(item.id)}`;
    ui.savedActions.replaceChildren();
    if(write?.state==="verified"&&write.verified_event&&window.SamanthaCalendarDelete) {
      window.SamanthaCalendarDelete.attach(ui.savedActions,write.verified_event,{disabled:()=>busy,onDeleted:()=>{ui.status.textContent="Událost byla smazaná z kalendáře.";ui.link.hidden=true;}});
    }
    const f = draft?.fields;
    const reminderText = (draft?.reminders || [1440,60]).map(n => n === 1440 ? "den" : "hodinu").join(" a ");
    ui.summary.textContent = f ? `${f.all_day ? "Celý den" : f.end_time ? `Konec ${f.end_date !== f.date ? f.end_date + " " : ""}${f.end_time}` : "Termín"} · ${f.time_zone || "Europe/Prague"} · ${reminderText ? "upozornění " + reminderText + " předem" : "bez upozornění"}${review?.target ? " · " + review.target.title : ""}` : "";
    ui.conflicts.textContent = review?.conflicts?.length ? `Kolize: ${review.conflicts.map(row => row.title).join(", ")}.` : "";
    const active = data.job && ["queued","running"].includes(data.job.status);
    stopped = Boolean(data.job && ["failed","delivery_unknown"].includes(data.job.status) && !draft);
    ui.status.textContent = data.message || write?.message || (active ? "Terra připravuje návrh…" : stopped ? "Výsledek přípravy není potvrzený. Obnov pouze stav původního požadavku." : draft ? "Zkontroluj a zapiš." : "Připravuji návrh…");
    ui.refresh.hidden = !stopped;
    controls(); if (active) poll();
  }
  async function request(payload) {
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 35000);
    try {
      const response = await fetch(endpoint + (payload ? "" : "?id=" + encodeURIComponent(item.id)), {
        method: payload ? "POST" : "GET", cache: "no-store", signal: controller.signal,
        ...(payload ? {headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)} : {})});
      const data = await response.json(); if (!response.ok || !data.ok) throw new Error(data.message || "Operace se nezdařila."); return data;
    } finally { clearTimeout(timeout); }
  }
  function fail(error) {
    ui.status.textContent = error.name === "AbortError" ? "Výsledek není potvrzený. Obnov stav; požadavek znovu neposílej." : error.message;
    ui.refresh.hidden = false;
  }
  async function check(token) {
    if (!draft || write && write.state !== "blocked") return;
    const data = await request({action:"review",id:item.id,expected_revision:draft.revision,confirmed:true});
    if (token === generation) render(data);
  }
  function poll() {
    if (pollTimer || polls >= 180 || !dialog.open) return;
    pollTimer = setTimeout(async () => {
      pollTimer = null; const token = generation; polls++;
      try {
        const data = await request(); if (token !== generation || !dialog.open) return;
        render(data);
        if (data.draft) { busy = true; controls(); try { await check(token); } finally { busy = false; controls(); } }
        else if (polls >= 180) { ui.status.textContent = "Příprava trvá déle. Obnov pouze stav."; ui.refresh.hidden = false; }
      } catch (error) { if (token === generation) fail(error); }
    }, 1000);
  }
  function clearTimers() { clearTimeout(timer); clearTimeout(pollTimer); timer = pollTimer = null; }
  function changed(event) {
    if (busy) return;
    dirty = true; review = null;
    const day = ui.start.value.slice(0,10);
    const allDay = ui.kind.value === "all_day" || ui.kind.value === "task_deadline" && ui.start.type === "date";
    ui.start.type = allDay ? "date" : "datetime-local";
    if (allDay) ui.start.value = day;
    else if (ui.start.value.length === 10) ui.start.value = day + "T09:00";
    ui.summary.textContent = "Ukládám úpravy…"; ui.conflicts.textContent = ""; clearTimeout(timer);
    timer = setTimeout(() => save(), 600); controls();
  }
  async function saveValues() {
    if (!dirty) return;
    const data = await request({action:"save_simple",id:item.id,expected_revision:draft.revision,values:values()});
    dirty = false; render(data, true);
  }
  async function save() {
    if (busy || !dirty) return;
    busy = true; controls(); const token = generation;
    try { await saveValues(); if (token === generation) await check(token); }
    catch (error) { if (token === generation) fail(error); }
    finally { if (token === generation) { busy = false; controls(); } }
  }
  async function submit() {
    if (busy || !draft || stopped || write?.state === "verified") return;
    clearTimeout(timer); busy = true; controls(); const token = generation;
    try {
      await saveValues();
      // A newly edited card is checked automatically before accepting collision consent.
      if (!review && !(write && ["pending","unknown"].includes(write.state))) {
        await check(token);
        if (review?.conflicts?.length) { ui.status.textContent = "Termín koliduje. Můžeš jej upravit nebo zapsat i přes kolizi."; return; }
      }
      ui.status.textContent = "Ověřuji a zapisuji…";
      const data = await request({action:"write",id:item.id,expected_revision:draft.revision,review_fingerprint:review?.fingerprint || "",confirmed:true});
      if (token === generation) render(data, true);
    } catch (error) { if (token === generation) { fail(error); stopped = true; } }
    finally { if (token === generation) { busy = false; controls(); } }
  }
  async function authorize() {
    if (busy) return; busy = true; controls(); const token = generation;
    try { const data = await request({action:"authorize_writer",id:item.id,confirmed:true}); if (token === generation) render(data); }
    catch (error) { if (token === generation) fail(error); }
    finally { if (token === generation) { busy = false; controls(); } }
  }
  async function refresh() {
    if (busy) return; busy = true; controls(); const token = generation;
    try { const data = await request(); if (token === generation) { stopped = false; render(data); if (!dirty) await check(token); } }
    catch (error) { if (token === generation) fail(error); }
    finally { if (token === generation) { busy = false; controls(); } }
  }
  function close() {
    if (busy) return;
    clearTimers(); generation++; dialog.close(); draft = review = write = null; dirty = false;
  }
  async function open(selected) {
    if (busy) return; if (!dialog) create(); clearTimers(); generation++; const token = generation;
    item = selected; draft = review = write = null; dirty = stopped = false; busy = true; polls = 0;
    ui.subject.textContent = selected.header?.subject || ""; ui.fields.hidden = true; ui.link.hidden = true;
    ui.summary.textContent = ui.conflicts.textContent = ""; ui.permission.hidden = ui.refresh.hidden = true;
    ui.status.textContent = "Terra připravuje návrh z tohoto e-mailu…";
    if (!dialog.open) dialog.showModal(); controls();
    try {
      let data = await request(); if (token !== generation) return;
      if (!data.job) data = await request({action:"prepare",id:item.id,request_id:crypto.randomUUID(),expected_content_digest:item.content_digest,confirmed:true});
      if (token === generation) { render(data,true); if (data.draft) await check(token); }
    } catch (error) { if (token === generation) { fail(error); stopped = true; } }
    finally { if (token === generation) { busy = false; controls(); } }
  }
  window.SamanthaCalendarDraft = {open, isOpen:() => Boolean(dialog?.open)};
})();
