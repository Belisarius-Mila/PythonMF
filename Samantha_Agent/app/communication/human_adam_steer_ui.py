"""HA-06 append form: explicit POST once, then only scoped receipt reads."""

HUMAN_ADAM_STEER_SCRIPT = r"""
function createHumanAdamSteer(host) {
  let scope=null, protocol=null, work=null, enabled=false, epoch=0;
  let draft="", draftTarget="", reference=null, receipt=null, revision=0;
  let posting=false, reading=null, postController=null, timer=null, paused=false, failures=0, error="";
  const key=value=>value?`${value.workstream_id}:${value.thread_id}:${value.connection_generation}:${value.operation_id}`:"";
  const storageKey=()=>`human-adam:append-reference:v1:${key(scope)}`;
  const validReference=value=>value && typeof value.command_id==="string"
    && new RegExp(`^ha06-${scope.operation_id}-[a-f0-9]{32}$`).test(value.command_id)
    && typeof value.expected_turn_id==="string" && value.expected_turn_id.length>0 && value.expected_turn_id.length<=256;
  function unresolved(){return Boolean(reference && (!receipt || ["pending","unverified"].includes(receipt.state)));}
  function available(){return Boolean(enabled && !paused && !posting && !unresolved() && !error && work && !work.error
    && work.operation.lifecycle_state==="running" && work.operation.capabilities && work.operation.capabilities.steer===true
    && work.operation.turn_id);}
  function canSubmit(){return Boolean(available() && draft.trim() && draftTarget===key(scope));}
  function snapshot(){return {enabled,draft,receipt,error,posting,reading:Boolean(reading),unresolved:unresolved(),canSubmit:canSubmit(),
    available:available(),detachedDraft:Boolean(draft && draftTarget!==key(scope)),
    finished:Boolean(work && work.operation && ["completed","failed","not_dispatched","awaiting_completion"].includes(work.operation.lifecycle_state)),
    workUnverified:Boolean(work && (work.error || work.operation && work.operation.lifecycle_state==="unverified")),
    scope,canRead:Boolean(reference),recent:work && work.operation && work.operation.recent_commands || null};}
  function changed(){host.onChange(snapshot());}
  function remember(){try{host.storage.setItem(storageKey(),JSON.stringify(reference));}catch(_){}}
  function cancel(){if(timer!==null)host.clearTimeout(timer);timer=null;if(reading)reading.abort();reading=null;
    if(postController)postController.abort();postController=null;}
  function schedule(delay=750){if(paused || !enabled || !reference)return;
    if(timer!==null)host.clearTimeout(timer);timer=host.setTimeout(()=>{timer=null;void read();},delay);}
  function accept(payload, fromPost=false){
    if(!payload || payload.ok!==true || payload.schema_version!==1 || payload.operation_id!==scope.operation_id
      || payload.workstream_id!==scope.workstream_id || !reference)throw Error('invalid_command_envelope');
    if(!fromPost && (payload.read_only!==true || payload.writes_performed!==false))throw Error('mutable_read');
    if(!payload.command){throw Error('missing_command_is_not_proof');}
    const next=payload.command;
    if(next.command_id!==reference.command_id || next.expected_turn_id!==reference.expected_turn_id
      || !["pending","accepted","rejected","unverified"].includes(next.state)
      || next.permission_scope!=="original_turn" || next.accepted_into_turn!==(next.state==="accepted")
      || !Number.isSafeInteger(payload.command_revision) || payload.command_revision<revision
      || !Number.isFinite(Date.parse(next.updated_at)) || next.text!==undefined && (typeof next.text!=="string" || next.text.length>4000))throw Error('invalid_command_proof');
    if(receipt && ["accepted","rejected"].includes(receipt.state) && next.state!==receipt.state)throw Error('changed_terminal_command');
    receipt=structuredClone(next);revision=payload.command_revision;error="";failures=0;
    if(next.state==="accepted" && draftTarget===key(scope) && draft.trim()===next.text){draft="";}
    else if(["rejected","unverified"].includes(next.state) && !draft && next.text){draft=next.text;draftTarget=key(scope);}
    changed();
    if(next.state==="pending")schedule();
  }
  async function read(){
    if(!enabled || paused || !reference || reading)return;
    const token=epoch, ref={...reference}, controller=new AbortController();reading=controller;
    const timeout=host.setTimeout(()=>controller.abort(),5000);
    try{
      const payload=await host.read({workstream_id:scope.workstream_id,operation_id:scope.operation_id,command_id:ref.command_id},controller.signal);
      if(token!==epoch || reading!==controller)return;
      accept(payload);
    }catch(_){
      if(token!==epoch || reading!==controller)return;
      error="Doručení doplnění není ověřené. Text zůstává; neposílej jej znovu.";failures+=1;changed();
      if(failures<8)schedule(Math.min(10000,1000*2**Math.min(failures-1,4)));
    }finally{
      host.clearTimeout(timeout);
      if(reading===controller)reading=null;
    }
  }
  return {
    snapshot,
    configure(nextProtocol,view){
      const operation=view && view.operation;
      const nextScope=operation && {...operation.scope,operation_id:operation.operation_id};
      const supported=Boolean(nextProtocol && nextProtocol.command_protocol===1
        && nextProtocol.steer_path==="/api/human-adam/work/steer" && nextProtocol.command_read_path==="/api/human-adam/work/command"
        && view.enabled && operation && /^[a-f0-9]{32}$/.test(operation.operation_id));
      work=view;
      if(supported!==enabled || key(nextScope)!==key(scope)){
        epoch+=1;cancel();enabled=supported;scope=nextScope;protocol=nextProtocol;
        reference=null;receipt=null;revision=0;posting=false;error="";failures=0;
        if(enabled){
          try{const saved=JSON.parse(host.storage.getItem(storageKey())||"null");if(validReference(saved))reference=saved;}catch(_){}
          if(!reference){
            const commands=operation.recent_commands && operation.recent_commands.commands;
            const pending=Array.isArray(commands)?[...commands].reverse().find(c=>["pending","unverified"].includes(c.state)):null;
            if(pending && validReference(pending)){reference={command_id:pending.command_id,expected_turn_id:pending.expected_turn_id};remember();}
          }
          if(reference)schedule(0);
        }
      }
      changed();
    },
    setDraft(value){draft=String(value||"").slice(0,4000);draftTarget=key(scope);if(!unresolved())error="";changed();},
    async submit(){
      if(!canSubmit()){changed();return false;}
      const text=draft.trim(),turn=work.operation.turn_id;
      let commandId;
      try{commandId=host.newCommandId(scope.operation_id);if(!validReference({command_id:commandId,expected_turn_id:turn}))throw Error('invalid_identity');}
      catch(_){error="Doplnění se nepodařilo připravit. Text zůstává; nic nebylo odesláno.";changed();return false;}
      epoch+=1;cancel();const token=epoch;
      reference={command_id:commandId,expected_turn_id:turn};receipt=null;revision=0;error="";posting=true;remember();changed();
      const controller=new AbortController();postController=controller;
      const timeout=host.setTimeout(()=>controller.abort(),10000);
      try{
        const payload=await host.post({workstream_id:scope.workstream_id,operation_id:scope.operation_id,
          command_id:commandId,expectedTurnId:turn,text,confirmed:true},controller.signal);
        if(token!==epoch || paused)return false;
        accept(payload,true);return receipt.state==="accepted";
      }catch(_){
        if(token!==epoch || paused)return false;
        error="Přijetí doplnění není ověřené. Pouze dohledávám původní účtenku; neposílej znovu.";changed();schedule(0);return false;
      }finally{
        host.clearTimeout(timeout);
        if(token===epoch){posting=false;postController=null;changed();}
      }
    },
    verify(){failures=0;schedule(0);},
    pause(){epoch+=1;paused=true;cancel();posting=false;changed();},
    resume(){paused=false;changed();if(unresolved())schedule(0);},
  };
}

function renderHumanAdamSteer(doc,view){
  const box=doc.getElementById("steerBox"),input=doc.getElementById("steerInput");box.hidden=!view.enabled;
  if(box.hidden)return;
  if(input.value!==view.draft)input.value=view.draft;
  doc.getElementById("steerSendBtn").disabled=!view.canSubmit;
  doc.getElementById("steerVerifyBtn").hidden=!view.canRead;
  const receipt=view.receipt;
  const reasons={work_not_running:"Původní tah už není k dispozici pro doplnění.",scope_changed:"Projekt nebo původní rozsah se změnil.",
    turn_changed:"Doplnění neodpovídá původnímu tahu.",owner_unavailable:"Původní vlastník práce není ověřený.",
    previous_unverified:"Nejdřív ověř předchozí doplnění.",command_limit:"Byl dosažen limit doplnění této práce.",
    server_rejected:"App Server doplnění odmítl."};
  const text=view.error || (view.posting?"Odesílám doplnění do původního tahu…":view.detachedDraft?
    "Text zůstal z jiné práce. Před doplněním do této práce jej nejprve uprav nebo zkopíruj.":
    receipt && receipt.state==="accepted" && view.finished && view.draft?"Původní tah skončil. Nově rozepsaný text nebyl odeslán a zůstává k dispozici.":
    receipt && receipt.state==="accepted"?"Doplnění přijato do původního tahu. Neznamená to dokončení práce.":
    receipt && receipt.state==="rejected"?`Doplnění bylo odmítnuto. ${reasons[receipt.reason]||""} Text zůstává jako rozepsaný pokyn.`:
    receipt && receipt.state==="pending"?"Čekám na potvrzení doplnění. Znovu je neodesílám.":
    receipt && receipt.state==="unverified"?"Doručení doplnění není ověřené. Neposílej jej znovu.":
    view.finished?"Původní modelový tah už neběží. Text zůstává rozepsaný; nový úkol se neodesílá.":
    view.workUnverified?"Průběh původní práce není ověřený. Text zůstává rozepsaný; doplnění se neodesílá.":
    !view.available?"Doplnění zatím není dostupné. Čekám na přesný aktivní tah a ověřenou podporu této relace.":
    "Doplnění platí jen pro tento běžící tah a jeho původní oprávnění.");
  const status=doc.getElementById("steerStatus");if(status.textContent!==text)status.textContent=text;
  const list=doc.getElementById("steerHistory"),rows=view.recent && view.recent.commands || [];
  const values=Array.isArray(rows)?rows.slice(-16).filter(c=>c && ["pending","accepted","rejected","unverified"].includes(c.state)
    && (c.text===undefined || typeof c.text==="string" && c.text.length<=4000)):[];
  const fingerprint=JSON.stringify(values);
  if(list.dataset.fingerprint!==fingerprint){list.dataset.fingerprint=fingerprint;list.replaceChildren(...values.map(c=>{
    const row=doc.createElement("li");row.textContent=`${({pending:"Čeká na potvrzení",accepted:"Přijato do tahu",rejected:"Odmítnuto",unverified:"Doručení neověřeno"})[c.state]}${c.text?`: ${c.text}`:""}`;return row;
  }));}
}
"""
