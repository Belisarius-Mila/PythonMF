(() => {
  const $ = id => document.getElementById(id), form = $("taskForm"), fields = $("taskFields");
  const title = $("taskTitle"), day = $("taskDay"), month = $("taskMonth"), year = $("taskYear"), time = $("taskTime");
  const notice = $("taskNotice"), recoverButton = $("taskRecover"), storageKey = "samantha.calendarTask.pending.v1";
  const formatter = new Intl.DateTimeFormat("cs-CZ", {timeZone:"Europe/Prague",weekday:"long",day:"numeric",month:"long",year:"numeric"});
  const months = ["leden","únor","březen","duben","květen","červen","červenec","srpen","září","říjen","listopad","prosinec"];
  let context = null, pending = null, busy = false, storageBroken = false, generation = 0, pollTimer = null, polls = 0;
  const pad = n => String(n).padStart(2,"0");
  function requestId() {
    // getRandomValues also works on trusted private-LAN HTTP pages. The ID is
    // the same 128-bit random hex identity expected by the server, not a token.
    const bytes=new Uint8Array(16);window.crypto.getRandomValues(bytes);
    return Array.from(bytes,value=>value.toString(16).padStart(2,"0")).join("");
  }
  const dateValue = () => `${year.value}-${pad(month.value)}-${pad(day.value)}`;
  const option = (value,text) => {const n=document.createElement("option");n.value=String(value);n.textContent=text;return n;};
  function message(text,state="error") {notice.textContent=text;notice.dataset.state=state;}
  function controls() {
    fields.disabled=busy||Boolean(pending)||!context?.ready;
    $("taskSubmit").disabled=fields.disabled||storageBroken;recoverButton.disabled=busy||storageBroken;
    form.setAttribute("aria-busy",String(busy));
    window.SamanthaCalendarDelete?.update(document);
  }
  function summary() {
    if(!year.value||!month.value||!day.value)return;
    $("taskSummary").textContent=formatter.format(new Date(dateValue()+"T12:00:00Z"))+" v "+time.value;
  }
  function days(selected=day.value||1) {
    const count=new Date(Date.UTC(Number(year.value),Number(month.value),0)).getUTCDate();
    day.replaceChildren(...Array.from({length:count},(_,i)=>option(i+1,String(i+1))));
    day.value=String(Math.min(Number(selected),count));summary();
  }
  function setDate(value,today) {
    const [y,m,d]=value.split("-").map(Number), current=Number(today.slice(0,4));
    month.replaceChildren(...months.map((name,i)=>option(i+1,name)));
    const first=Math.min(current,y);
    year.replaceChildren(...Array.from({length:current+11-first},(_,i)=>option(first+i,String(first+i))));
    year.value=String(y);month.value=String(m);days(d);
  }
  function readStored() {
    const raw=window.localStorage.getItem(storageKey);
    if(!raw)return null;
    if(raw.length>10000)throw new Error("Uložené zadání nelze načíst. Ověř jeho stav v kalendáři.");
    const value=JSON.parse(raw);
    if(!/^[a-f0-9]{32}$/.test(value?.id)||value.payload?.request_id!==value.id||value.payload?.action!=="create"
       ||typeof value.payload.title!=="string"||!/^\d{4}-\d{2}-\d{2}$/.test(value.payload.date)
       ||!/^\d{2}:\d{2}$/.test(value.payload.time))throw new Error("Uložené zadání nelze načíst. Ověř jeho stav v kalendáři.");
    return value;
  }
  function clearPending() {
    const id=pending?.id;
    try {if(readStored()?.id===id)window.localStorage.removeItem(storageKey);}
    catch(error){storageBroken=true;}
    pending=null;clearTimeout(pollTimer);pollTimer=null;recoverButton.hidden=true;
  }
  async function api(payload) {
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),70000);
    try {
      const response=await fetch("/api/calendar/tasks",{method:payload?"POST":"GET",cache:"no-store",signal:controller.signal,
        ...(payload?{headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}:{})});
      const value=await response.json();if(!response.ok||!value.ok)throw new Error(value.message||"Kalendář nyní není dostupný.");return value;
    } finally {clearTimeout(timer);}
  }
  async function loadContext() {
    try {
      const value=await api(), old=context;context=value;
      if(!old||old.today!==value.today&&!title.value&&!pending) {
        const saved=pending?.payload;setDate(saved?.date||value.today,value.today);time.value=saved?.time||value.default_time;
        if(saved)title.value=saved.title;summary();
      }
      const target=$("taskTarget");target.replaceChildren();
      if(value.target)target.append(document.createTextNode("Kalendář: "+value.target.title+" · "));
      const link=document.createElement("a");link.href="/calendar/";link.textContent=value.ready?"Nastavení":"Vybrat cílový kalendář";target.append(link);
      if(!old&&!pending&&!storageBroken)message(value.ready?"Připraveno.":"Nejdřív vyber cílový kalendář.",value.ready?"ready":"error");
    } catch(error){context=null;message("Nastavení kalendáře nelze načíst. Obnov stránku.");}
    controls();
  }
  function apply(value) {
    if(!pending||value.request_id!==pending.id)return;
    pending.state=value.state;
    if(value.state==="verified") {
      const saved=value.task||pending.payload;
      clearPending();title.value="";
      message(`Zapsáno: ${saved.title} · ${formatter.format(new Date(saved.date+"T12:00:00Z"))} v ${saved.time}.`,"verified");
      const actions=$("taskSavedActions");
      if(actions&&value.event&&window.SamanthaCalendarDelete) {
        actions.replaceChildren();window.SamanthaCalendarDelete.attach(actions,value.event,{disabled:()=>busy,onDeleted:()=>message("Úkol byl smazaný z kalendáře.","verified")});
      }
    } else if(value.state==="blocked") {
      clearPending();message(value.message,"blocked");loadContext();
    } else {
      message(value.message||"Zápis se ověřuje…",value.state);
      recoverButton.hidden=false;recoverButton.textContent=value.state==="not_found"?"Zapsat stejné zadání":"Ověřit zápis";
      if(value.state==="pending")scheduleStatus();
    }
    controls();
  }
  function scheduleStatus() {
    if(pollTimer||!pending||polls>=30||document.hidden)return;
    pollTimer=setTimeout(async()=>{pollTimer=null;if(document.hidden)return;if(busy){scheduleStatus();return;}polls++;await readStatus();},1500);
  }
  async function readStatus() {
    if(!pending)return;const id=pending.id,token=generation;
    try {const value=await api({action:"status",request_id:id});if(token===generation&&pending?.id===id)apply(value);}
    catch(error){if(token===generation&&pending?.id===id){message("Stav zatím nelze ověřit. Zadání zůstává uchované.");recoverButton.hidden=false;recoverButton.textContent="Ověřit zápis";controls();}}
  }
  async function write(payload) {
    if(busy||!pending)return;busy=true;const token=++generation;clearTimeout(pollTimer);pollTimer=null;polls=0;controls();
    message(payload.action==="recover"?"Ověřuji původní zápis…":"Zapisuji úkol…","pending");
    try {const value=await api(payload);if(token===generation)apply(value);}
    catch(error) {
      if(token===generation) {
        message("Výsledek zatím není potvrzený. Zadání je uchované; ověř původní zápis.");
        if(pending)pending.state="pending";recoverButton.hidden=false;recoverButton.textContent="Ověřit zápis";
      }
    } finally {if(token===generation){busy=false;controls();if(pending?.state==="pending")scheduleStatus();}}
  }
  form.addEventListener("submit",async event=>{
    event.preventDefault();if(busy||pending||!context?.ready||storageBroken||!form.reportValidity())return;
    if(!title.value.trim()||/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/.test(title.value)) {message("Doplň text úkolu bez neplatných znaků.");return;}
    let value;
    try {
      if(readStored()) {storageBroken=true;message("Nejdřív obnov stránku a ověř rozpracované zadání.");controls();return;}
      const id=requestId();
      value={id,payload:{action:"create",request_id:id,title:title.value.trim(),date:dateValue(),time:time.value,
        expected_selection_revision:context.selection_revision,expected_target_calendar_id:context.target.id,confirmed:true}};
      const raw=JSON.stringify(value);window.localStorage.setItem(storageKey,raw);
      if(window.localStorage.getItem(storageKey)!==raw)throw new Error("Zadání se nepodařilo bezpečně uchovat. Neodesláno.");
    } catch(error){
      // No POST has started. Do not freeze an editable form for an ID/API error
      // or a proven empty store. A partially persisted identity is recovered
      // as-is, never replaced by a new request.
      let saved=null;
      try {saved=readStored();}catch(storageError){storageBroken=true;}
      if(value&&saved?.id===value.id&&JSON.stringify(saved.payload)===JSON.stringify(value.payload)) {
        pending=value;recoverButton.hidden=false;recoverButton.textContent="Ověřit zápis";
        message("Zadání je uchované. Ověř jeho stav před dalším odesláním.","pending");readStatus();
      } else if(saved||storageBroken) {
        storageBroken=true;message("Rozpracované zadání nelze ověřit. Text zůstává, před odesláním obnov stránku.");
      } else {
        message("Zadání se nepodařilo připravit. Neodesláno; text zůstává a můžeš to zkusit znovu.");
      }
      controls();return;
    }
    pending=value;await write(value.payload);
  });
  recoverButton.addEventListener("click",()=>{
    if(pending&&!busy)return write(pending.state==="not_found"?pending.payload:{action:"recover",request_id:pending.id,confirmed:true});
  });
  day.addEventListener("change",summary);month.addEventListener("change",()=>days());year.addEventListener("change",()=>days());time.addEventListener("input",summary);
  window.addEventListener("pageshow",()=>{if(context&&!busy){loadContext();if(pending)readStatus();}});
  document.addEventListener("visibilitychange",()=>{
    if(document.hidden){clearTimeout(pollTimer);pollTimer=null;}else if(context&&!busy){loadContext();if(pending)readStatus();}
  });
  try {pending=readStored();}catch(error){storageBroken=true;message("Uložené zadání nelze načíst. Ověř kalendář před dalším zápisem.");}
  controls();loadContext().then(()=>{if(pending)readStatus();});
})();
