"""HA-07 cancellation control; one POST, recovery through the existing work GET."""

HUMAN_ADAM_INTERRUPT_SCRIPT = r"""
function createHumanAdamInterrupt(host) {
  let scope=null, work=null, enabled=false, posting=false, requested=false, receipt=null, error="", epoch=0, controller=null;
  const key=s=>s?`${s.workstream_id}:${s.thread_id}:${s.connection_generation}:${s.operation_id}`:"";
  const storageKey=()=>`human-adam:interrupt:v1:${key(scope)}`;
  function saveDrafts(){
    if(!enabled || !scope)return;
    try{host.storage.setItem(storageKey(),JSON.stringify({requested,turn_id:work.operation.turn_id,drafts:host.getDrafts()}));}catch(_){}
  }
  function accept(value,operation=work.operation){
    if(!value || value.command_id!==`ha07-${scope.operation_id}` || value.expected_turn_id!==work.operation.turn_id
      || !["pending","accepted","rejected","unverified"].includes(value.state)
      || !["waiting","unverified","interrupted","completed","failed","not_dispatched"].includes(value.outcome))throw Error('invalid_interrupt_receipt');
    const expected=["completed","failed","interrupted","not_dispatched"].includes(operation.lifecycle_state)?operation.lifecycle_state:
      operation.lifecycle_state==="unverified"?"unverified":"waiting";
    if(value.outcome!==expected || ["completed","interrupted"].includes(expected) && operation.delivery_state!=="confirmed")throw Error('unconfirmed_stop');
    receipt=structuredClone(value);requested=true;error="";
  }
  function snapshot(){
    return {enabled,posting,receipt,error,requested,phase:work && work.operation && work.operation.lifecycle_state,
      canStop:Boolean(enabled && !posting && !requested && !error && work && !work.error
      && work.operation.lifecycle_state==="running" && work.operation.turn_id && work.operation.capabilities && work.operation.capabilities.interrupt===true)};
  }
  const changed=()=>host.onChange(snapshot());
  return {
    snapshot,saveDrafts,
    configure(protocol,view){
      const op=view && view.operation;
      const next=op && {...op.scope,operation_id:op.operation_id};
      const supported=Boolean(protocol && protocol.interrupt_protocol===1 && protocol.interrupt_path==="/api/human-adam/work/interrupt"
        && view.enabled && op && /^[a-f0-9]{32}$/.test(op.operation_id));
      if(key(scope)!==key(next) || enabled!==supported){
        saveDrafts();epoch+=1;if(controller)controller.abort();controller=null;posting=false;
        scope=next;enabled=supported;requested=false;receipt=null;error="";work=view;
        if(enabled){try{
          const saved=JSON.parse(host.storage.getItem(storageKey())||"null");
          if(saved && saved.turn_id===op.turn_id && saved.requested===true){
            requested=true;host.restoreDrafts(saved.drafts);
          }
        }catch(_){} }
      }
      work=view;
      if(enabled && op.interrupt){try{accept(op.interrupt);}catch(_){error="Výsledek zastavení nelze ověřit.";requested=true;}}
      changed();
    },
    async submit(){
      if(!snapshot().canStop)return false;
      const token=epoch, operation=work.operation;
      requested=true;posting=true;error="";saveDrafts();changed();
      const active=new AbortController();controller=active;
      const timeout=host.setTimeout(()=>active.abort(),10000);
      try{
        const payload=await host.post({workstream_id:scope.workstream_id,operation_id:scope.operation_id,
          command_id:`ha07-${scope.operation_id}`,expectedTurnId:operation.turn_id,confirmed:true},active.signal);
        if(token!==epoch)return false;
        const op=payload && payload.ok===true && payload.operations && payload.operations.length===1 && payload.operations[0];
        if(!op || key({...op.scope,operation_id:op.operation_id})!==key(scope))throw Error('other_work');
        accept(op.interrupt,op);return true;
      }catch(_){if(token===epoch)error="Výsledek žádosti není ověřený. Požadavek neopakuji; ověř původní práci.";return false;}
      finally{host.clearTimeout(timeout);if(token===epoch){posting=false;controller=null;changed();host.refresh();}}
    },
    pause(){saveDrafts();epoch+=1;if(controller)controller.abort();controller=null;posting=false;changed();},
  };
}
function renderHumanAdamInterrupt(doc,view){
  const box=doc.getElementById("interruptBox");box.hidden=!view.enabled;if(box.hidden)return;
  doc.getElementById("interruptBtn").disabled=!view.canStop;
  const receipt=view.receipt;
  const outcome=receipt && receipt.outcome;
  const message=outcome==="interrupted"?"Práce byla zastavena. Rozpracované změny a rozepsané pokyny zůstaly zachované.":
    outcome==="completed"?"Práce už skončila dokončením. Zastavení její výsledek nevrací zpět.":
    outcome==="failed"?"Původní práce skončila chybou. Prohlédni její výsledek.":
    outcome==="unverified"?"Konec původní práce není ověřený. Požadavek na zastavení neopakuji.":
    view.error || (view.posting?"Žádám o zastavení této práce…":
    receipt && receipt.state==="accepted"?"Žádost o zastavení byla přijata. Čekám na potvrzený konec práce.":
    receipt && receipt.state==="rejected"?"Žádost o zastavení byla odmítnuta. Ověř aktuální stav práce.":
    receipt && receipt.state==="unverified"?"Žádost o zastavení není ověřená. Pouze ověř původní stav práce.":
    view.requested?"Ověřuji původní žádost o zastavení; další neodesílám.":
    view.phase==="awaiting_completion"?"Modelový tah skončil. Navazující ověření a checkpoint pokračují; v této fázi není zastavení dostupné.":
    ["completed","failed","interrupted","not_dispatched"].includes(view.phase)?"Původní modelový tah už neběží. Výsledek zůstává v historii práce.":
    "Zastaví modelový tah. Již provedené změny zůstanou zachované.");
  const status=doc.getElementById("interruptStatus");if(status.textContent!==message)status.textContent=message;
}
"""
