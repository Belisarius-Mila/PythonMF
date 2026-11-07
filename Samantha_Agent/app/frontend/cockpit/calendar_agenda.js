(() => {
  const panel = document.getElementById("calendarAgenda");
  if (!panel) return;
  const notice = document.getElementById("calendarAgendaStatus"), refreshButton = document.getElementById("calendarAgendaRefresh");
  const date = new Intl.DateTimeFormat("cs-CZ", {timeZone:"Europe/Prague",day:"numeric",month:"short"});
  const time = new Intl.DateTimeFormat("cs-CZ", {timeZone:"Europe/Prague",hour:"2-digit",minute:"2-digit"});
  let state = null, busy = false, generation = 0, pollTimer = null, polls = 0, lastStarted = 0;
  const element = (tag, text, cls) => { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; };
  async function api(payload) {
    const controller = new AbortController(), timer=setTimeout(()=>controller.abort(),10000);
    try {
      const response=await fetch("/api/calendar/agenda", {method:payload?"POST":"GET",cache:"no-store",signal:controller.signal,
        ...(payload?{headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}:{})});
      const value=await response.json(); if(!response.ok||!value.ok)throw new Error(value.message||"Přehled kalendáře není dostupný."); return value;
    } finally {clearTimeout(timer);}
  }
  function timing(row) {
    if(row.all_day) {
      const first=new Date(row.start_day+"T12:00:00Z"), last=new Date(row.end_day+"T12:00:00Z");last.setUTCDate(last.getUTCDate()-1);
      return date.format(first)+(first.getTime()!==last.getTime()?" – "+date.format(last):"")+" · celý den";
    }
    const a=new Date(row.start), b=new Date(row.end);
    return date.format(a)+" · "+time.format(a)+(row.kind==="task_deadline"?"":"–"+(date.format(a)!==date.format(b)?date.format(b)+" ":"")+time.format(b));
  }
  function row(item) {
    const li=element("li",undefined,"calendar-agenda-row"), text=element("div",undefined,"calendar-agenda-content");
    text.append(element("span",timing(item),"calendar-agenda-time"),element("strong",item.title||"Bez názvu"));
    li.append(text);
    const types=element("details",undefined,"calendar-agenda-type");types.append(element("summary","Typ"));
    const label=element("label","Typ pro tento přehled"), select=element("select");select.setAttribute("aria-label","Typ události "+item.title);
    for(const [value,title] of [["auto","Automaticky"],["task_deadline","Termín"],["meeting","Schůzka"]]) {const option=element("option",title);option.value=value;select.append(option);}
    select.value=item.display_kind;select.dataset.classify=String(item.can_classify);select.disabled=busy||!item.can_classify;
    select.addEventListener("change",()=>setKind(item.key,select.value));label.append(select);types.append(label);
    types.append(element("small","Označení platí pro tento název a čas. Nemění událost v kalendáři."));li.append(types);
    return li;
  }
  function list(id,items,empty) {
    const target=document.getElementById(id), open=target.querySelector("details.calendar-agenda-more")?.open;
    target.replaceChildren();
    if(!items.length) {target.append(element("p",state.classification_partial&&id==="calendarAgendaDeadlines"?"Rozdělení termínů nyní není úplné.":state.fresh?empty:"Zatím nejsou k dispozici aktuální položky.","calendar-agenda-empty"));return;}
    const first=element("ul");items.slice(0,6).forEach(item=>first.append(row(item)));target.append(first);
    if(items.length>6) {
      const more=element("details",undefined,"calendar-agenda-more"), rest=element("ul");more.open=Boolean(open);
      more.append(element("summary",`Dalších ${items.length-6}`));items.slice(6).forEach(item=>rest.append(row(item)));more.append(rest);target.append(more);
    }
  }
  function render(value) {
    state=value;
    let message=value.selected_count===0?"Vyber kalendáře v Komunikace → Kalendář.":value.refreshing?"Načítám aktuální kalendáře…":value.fresh?"Aktuální přehled na příštích 30 dní.":"Přehled není aktuálně ověřený. Zobrazené dřívější údaje mohou být zastaralé.";
    if(value.loaded_at)message+=" Aktualizováno "+date.format(new Date(value.loaded_at))+" v "+time.format(new Date(value.loaded_at))+".";
    if(value.classification_partial)message+=" Část označení typů nelze načíst; položky zůstávají mezi ostatními událostmi.";
    notice.textContent=message;notice.dataset.fresh=String(value.fresh);panel.setAttribute("aria-busy",String(value.refreshing));
    list("calendarAgendaDeadlines",value.deadlines,"V příštích 30 dnech nejsou označené termíny.");
    list("calendarAgendaMeetings",value.meetings,"V příštích 30 dnech nejsou schůzky ani další události.");
    document.getElementById("calendarAgendaDeadlineCount").textContent=String(value.deadlines.length);
    document.getElementById("calendarAgendaMeetingCount").textContent=String(value.meetings.length);
    if(value.refreshing)schedulePoll();
  }
  function error(err) {panel.setAttribute("aria-busy","false");if(state)state={...state,fresh:false};notice.textContent=(err.name==="AbortError"?"Načítání trvá déle. Přehled nyní není ověřený.":err.message)+ (state?.loaded_at?" Poslední načtené údaje zůstávají zobrazené.":"");notice.dataset.fresh="false";controls();}
  function controls() {refreshButton.disabled=busy;for(const select of panel.querySelectorAll("select"))select.disabled=busy||!state?.fresh||state.classification_partial||select.dataset.classify!=="true";}
  function schedulePoll() {
    if(pollTimer||polls>=30||document.hidden)return;
    pollTimer=setTimeout(async()=>{
      pollTimer=null;if(document.hidden)return;
      if(busy){schedulePoll();return;}
      const token=generation;polls++;
      try {const value=await api();if(token===generation)render(value);}
      catch(err){if(token===generation)error(err);}
    },1500);
  }
  async function refresh(force=false) {
    if(busy||document.hidden||(!force&&Date.now()-lastStarted<60000))return;
    busy=true;lastStarted=Date.now();polls=0;clearTimeout(pollTimer);pollTimer=null;const token=++generation;controls();
    try {
      const cached=await api();if(token!==generation)return;render(cached);
      if(!cached.refreshing&&cached.selected_count>0&&!document.hidden){const value=await api({action:"refresh"});if(token===generation)render(value);}
    } catch(err){if(token===generation)error(err);}
    finally {if(token===generation){busy=false;controls();}}
  }
  async function setKind(key,kind) {
    if(busy||!state)return;
    busy=true;clearTimeout(pollTimer);pollTimer=null;const token=++generation;controls();
    try {const value=await api({action:"set_kind",key,kind,expected_selection_revision:state.selection_revision,expected_labels_revision:state.labels_revision,confirmed:true});if(token===generation)render(value);}
    catch(err){if(token===generation)error(err);}
    finally {if(token===generation){busy=false;controls();}}
  }
  refreshButton.addEventListener("click",()=>refresh(true));
  window.addEventListener("focus",()=>refresh());window.addEventListener("pageshow",()=>refresh());
  document.addEventListener("visibilitychange",()=>{if(document.hidden){clearTimeout(pollTimer);pollTimer=null;}else refresh();});
  setInterval(()=>refresh(),120000);
  refresh(true);
})();
