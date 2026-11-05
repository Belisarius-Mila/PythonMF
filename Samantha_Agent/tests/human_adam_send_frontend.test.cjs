const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const html = JSON.parse(fs.readFileSync(0, "utf8"));
for (const id of ["sendFailure", "sendFailureText", "sendFailureDraft"]) {
  assert(html.includes(`id="${id}"`), `missing actual DOM element ${id}`);
}
function between(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a + start.length);
  assert(a >= 0 && b > a, `missing ${start}`);
  return html.slice(a, b);
}
const source = [
  between("function messageId()", "function formatTime("),
  between("function clearMessageInput()", "function preferredVoiceMimeType("),
  between("async function sendMessage(event)", '  composer.addEventListener("submit", sendMessage);'),
].join("\n");
function harness(mode="ok") {
  const el = () => ({value:"",defaultValue:"",hidden:true,textContent:"",maxLength:12000,
    focus(){}, scrollIntoView(){}, classList:{add(){},remove(){},toggle(){}}});
  const s = {busy:false,sendInFlight:false,sessionTurnBusy:false,voiceStarting:false,
    voiceRecording:false,voiceTranscribing:false,lunaReleaseStatusLoaded:true,
    writeIntentArmed:false,deliveryUncertain:false,pendingSubmission:null,
    activeWorkstreamId:"synthetic-workstream",input:el(),notice:el(),
    sendFailure:el(),sendFailureText:el(),sendFailureDraft:el(),
    lastSession:{thread_id:"synthetic-thread",messages:[]}, imageImportFailure:"",
    HUMAN_ADAM_SEND_PATH:"/api/human-adam/send",calls:[],renders:[],
    window:{crypto:{randomUUID:()=>"synthetic-id"}},
    syncControls(){}, updateMobileStatusSummary(){},
    shouldInterceptLunaReleaseCommand:()=>false,
    primeCompletionMediaSound:async()=>{},formatTime:()=>"synthetic-time",
    stopResultWatch(){},playCompletionMediaSound(){},prepareImageCandidate:async()=>{},
    startResultWatch(){},
  };
  s.document={getElementById:name=>s[name]};
  s.crypto=s.window.crypto;
  s.input.value="SYNTHETIC REQUEST";
  s.renderSession=session=>{s.lastSession=session;s.renders.push(session);};
  s.renderTurnState=()=>{};
  s.api=async(path, options)=>{
    s.calls.push({path,options});
    if(mode==="network")throw new Error("synthetic connection loss");
    if(mode==="generic_rejection")return {ok:false,status:"human_adam_send_failed",message:"synthetic failure"};
    if(mode==="busy")return {ok:false,status:"human_adam_busy",message:"synthetic busy"};
    const id=JSON.parse(options.body).client_message_id;
    return {ok:true,session:{thread_id:"synthetic-thread",messages:[{client_message_id:id,status:"completed",delivery_confirmed:true,answer:"synthetic"}]}};
  };
  s.loadStatus=async()=>{
    const session={thread_id:"synthetic-thread",messages:[]};
    s.renderSession(session);
    if(s.reconcilePendingSubmission)s.reconcilePendingSubmission(session);
    return {ok:true,session};
  };
  const context=vm.createContext(s);
  vm.runInContext(source+"\nglobalThis.send=sendMessage;globalThis.makeId=messageId;",context);
  return s;
}
(async()=>{
  const failedPreparation=harness();
  failedPreparation.messageId=()=>{throw new Error("synthetic preflight failure");};
  // Replace the actual VM global binding, not a separate mock sender.
  let failure;
  try { await failedPreparation.send({preventDefault(){}}); } catch(e) { failure=e; }
  assert.equal(failure,undefined,"preparation errors must be handled visibly");
  assert.equal(failedPreparation.calls.length,0);
  assert.equal(failedPreparation.input.value,"SYNTHETIC REQUEST");
  assert.equal(failedPreparation.sendInFlight,false);
  assert.equal(failedPreparation.sendFailure.hidden,false);

  const cryptoFailure=harness();
  cryptoFailure.window.crypto.randomUUID=()=>{throw new Error("unavailable secure API");};
  await cryptoFailure.send({preventDefault(){}});
  assert.equal(cryptoFailure.calls.length,1,"safe fallback must send once");
  assert(JSON.parse(cryptoFailure.calls[0].options.body).client_message_id.startsWith("human-adam-"));

  const missingCrypto=harness();
  missingCrypto.window.crypto=null;
  await missingCrypto.send({preventDefault(){}});
  assert.equal(missingCrypto.calls.length,1);
  const brokenSound=harness();
  brokenSound.primeCompletionMediaSound=()=>{throw new Error("synthetic media failure");};
  await brokenSound.send({preventDefault(){}});
  assert.equal(brokenSound.calls.length,1,"optional media cannot block transport");

  for(const mode of ["network","generic_rejection"]){
    const s=harness(mode);
    await s.send({preventDefault(){}});
    assert.equal(s.calls.length,1);
    assert.equal(s.input.value,"","uncertain request must not return to the resend editor");
    assert.equal(s.sendFailure.hidden,false);
    assert.equal(s.sendFailureDraft.textContent,"SYNTHETIC REQUEST");
    assert(s.pendingSubmission);
    await s.loadStatus();
    assert.equal(s.sendFailure.hidden,false,"refresh cannot erase unknown delivery");
    assert.equal(s.sendFailureDraft.textContent,"SYNTHETIC REQUEST");
    await s.send({preventDefault(){}});
    assert.equal(s.calls.length,1,"unknown delivery must block a second send");
    s.reconcilePendingSubmission({thread_id:"other",messages:[{client_message_id:s.pendingSubmission.clientId,status:"completed",delivery_confirmed:true}]});
    assert(s.pendingSubmission,"other thread cannot resolve the request");
    s.reconcilePendingSubmission({thread_id:"synthetic-thread",messages:[{client_message_id:s.pendingSubmission.clientId,status:"delivery_unknown"}]});
    assert(s.pendingSubmission);
    s.reconcilePendingSubmission({thread_id:"synthetic-thread",messages:[{client_message_id:s.pendingSubmission.clientId,status:"completed",delivery_confirmed:false}]});
    assert(s.pendingSubmission,"unconfirmed completion cannot resolve the request");
    s.reconcilePendingSubmission({thread_id:"synthetic-thread",messages:[{client_message_id:"other-id",status:"completed",delivery_confirmed:true}]});
    assert(s.pendingSubmission,"other request cannot resolve the request");
    s.reconcilePendingSubmission({thread_id:"synthetic-thread",messages:[{client_message_id:s.pendingSubmission.clientId,status:"completed",delivery_confirmed:true}]});
    assert.equal(s.pendingSubmission,null);
    assert.equal(s.sendFailure.hidden,true);
  }
  const busy=harness("busy");
  await busy.send({preventDefault(){}});
  assert.equal(busy.input.value,"SYNTHETIC REQUEST");
  assert.equal(busy.pendingSubmission,null);
  assert.equal(busy.sendFailure.hidden,false);
  const ok=harness();
  await ok.send({preventDefault(){}});
  assert.equal(ok.calls.length,1);
  assert.equal(ok.pendingSubmission,null);
  const lateProof=harness("network");
  lateProof.loadStatus=async()=>{
    const session={thread_id:"synthetic-thread",messages:[{client_message_id:lateProof.pendingSubmission.clientId,status:"completed",delivery_confirmed:true}]};
    lateProof.reconcilePendingSubmission(session);
    return {ok:true,session};
  };
  await lateProof.send({preventDefault(){}});
  assert.equal(lateProof.calls.length,1);
  assert.equal(lateProof.pendingSubmission,null);
  assert.equal(lateProof.sendFailure.hidden,true,"a proven result must not be labelled unknown");
  console.log("Human-Adam send contracts: preparation, crypto fallback, unknown delivery, receipt and rejection PASS");
})().catch(e=>{console.error(e);process.exitCode=1;});
