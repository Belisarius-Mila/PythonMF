"use strict";
(() => {
  const $ = id => document.getElementById(id);
  let state = null, formRevision = 0, dirty = false, busy = false;
  const dateFormat = new Intl.DateTimeFormat("cs-CZ", {timeZone:"Europe/Prague",dateStyle:"medium",timeStyle:"short"});
  const dayFormat = new Intl.DateTimeFormat("cs-CZ", {timeZone:"UTC",dateStyle:"medium"});
  function day(value) { return new Date(value + "T00:00:00Z"); }
  function timing(event) {
    if (!event.all_day) return dateFormat.format(new Date(event.start)) + " – " + dateFormat.format(new Date(event.end));
    const end = day(event.end_day); end.setUTCDate(end.getUTCDate() - 1);
    const first = dayFormat.format(day(event.start_day)), last = dayFormat.format(end);
    return "Celý den · " + first + (first === last ? "" : " – " + last);
  }
  function element(tag, text, className) {
    const node = document.createElement(tag); node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  const messages = {
    ready:"Přehled vybraných kalendářů je načtený. Jde o poslední načtený snímek, ne o rezervaci času.",
    selection_required:"Vyber kalendáře, které chceš v přehledu sledovat. Kolize zatím nejsou ověřené.",
    refresh_required:"Přehled potřebuje nové načtení. Kolize nejsou ověřené.",
    authorization_required:"Kalendáře nejsou dostupné bez přístupu na Macu. Kolize nejsou ověřené.",
    source_unavailable:"Kalendáře se nepodařilo načíst. Kolize nejsou ověřené. Zobrazené dřívější události nemusí být aktuální.",
    missing_calendars:"Některý vybraný kalendář není dostupný. Přehled je neúplný a kolize nejsou ověřené.",
    limited:"Načtený přehled překročil limit událostí. Přehled je neúplný a kolize nejsou ověřené."
  };
  function controls() {
    $("refresh").disabled = busy; $("authorize").disabled = busy;
    $("save").disabled = busy || !state || !state.can_select;
    for (const input of $("settings").querySelectorAll("input,select")) input.disabled = busy;
  }
  function render(value) {
    state = value;
    $("notice").textContent = messages[value.status] || messages.source_unavailable;
    $("notice").dataset.ready = String(value.ready);
    $("permission").hidden = value.status !== "authorization_required";
    $("loaded").textContent = value.last_loaded_at ? "Poslední načtení: " + dateFormat.format(new Date(value.last_loaded_at)) : "Zatím nenačteno.";
    const count=value.events.length;
    $("count").textContent = count ? count + (count===1 ? " událost" : count>=2 && count<=4 ? " události" : " událostí") : "";
    const names = new Map(value.calendars.map(row => [row.id,row.title]));
    $("events").replaceChildren();
    for (const event of value.events) {
      const card = element("article", "", "event");
      card.append(element("div",timing(event),"time"),element("h3",event.title || "Bez názvu"),element("div",names.get(event.calendar_id) || "Nedostupný kalendář","calendar-name"));
      $("events").append(card);
    }
    if (!value.events.length) $("events").append(element("p", value.ready ? "Ve vybraných kalendářích nejsou v načteném období žádné události." : "Události se zobrazí po výběru kalendářů a úspěšném načtení. Prázdný přehled nepotvrzuje volný čas.","empty"));
    if (!dirty) {
      formRevision = value.revision;
      $("calendars").replaceChildren(); $("target").replaceChildren(element("option","Zatím nevybrán"));
      $("target").firstChild.value = "";
      for (const calendar of value.calendars) {
        const label = element("label","","calendar-choice"), input = document.createElement("input");
        input.type="checkbox"; input.value=calendar.id; input.checked=value.read_calendar_ids.includes(calendar.id);
        const title=element("span",calendar.title); title.append(element("span",calendar.source_title,"source"));
        label.append(input,title); $("calendars").append(label);
        if (calendar.writable) { const option=element("option",calendar.title + " · " + calendar.source_title); option.value=calendar.id; $("target").append(option); }
      }
      if (!value.calendars.length) $("calendars").append(element("p","Nejdřív obnov dostupné kalendáře.","muted"));
      $("target").value=value.target_calendar_id;
      $("selection").open = !value.read_calendar_ids.length || !value.ready;
    }
    $("draft").textContent=dirty ? "Výběr má neuložené změny." : "";
    controls();
  }
  async function api(payload) {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(),35000);
    try {
      const response = await fetch(payload ? "/api/calendar/action" : "/api/calendar/overview", {
        method:payload ? "POST" : "GET",cache:"no-store",signal:controller.signal,
        ...(payload ? {headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)} : {})
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.message || "Kalendáře nejsou dostupné. Kolize nejsou ověřené.");
      return result;
    } finally { clearTimeout(timer); }
  }
  async function run(action) {
    if (busy) return;
    busy=true; controls(); $("notice").textContent="Načítám…";
    try { await action(); }
    catch(error) { $("notice").textContent=error.name === "AbortError" ? "Výsledek operace zatím není potvrzený. Obnov přehled; kolize nejsou ověřené." : error.message; $("notice").dataset.ready="false"; }
    finally { busy=false; controls(); }
  }
  $("settings").addEventListener("change", () => { dirty=true; $("draft").textContent="Výběr má neuložené změny."; });
  $("refresh").addEventListener("click", () => run(async () => render(await api({action:"refresh",confirmed:true}))));
  $("authorize").addEventListener("click", () => run(async () => {
    await api({action:"authorize",confirmed:true});
    $("notice").textContent="Dokonči případné povolení na Macu a potom zvol Obnovit kalendáře.";
  }));
  $("settings").addEventListener("submit", event => {
    event.preventDefault();
    const ids=Array.from($("calendars").querySelectorAll("input:checked"),input=>input.value), target=$("target").value;
    run(async () => {
      await api({action:"save_selection",confirmed:true,expected_revision:formRevision,read_calendar_ids:ids,target_calendar_id:target});
      dirty=false; render(await api({action:"refresh",confirmed:true}));
    });
  });
  run(async () => render(await api()));
  // A returning page must not keep a previously "ready" banner indefinitely.
  setInterval(() => { if (state && !busy && state.ready && Date.now()-Date.parse(state.last_loaded_at)>900000) { state={...state,ready:false,status:"refresh_required"}; render(state); } },30000);
})();
