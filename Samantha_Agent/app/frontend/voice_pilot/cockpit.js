/* Loading the panel never requests a microphone or starts a paid session. */
(function(){
  "use strict";
  const config=document.getElementById("voiceConfig");
  const renew=document.getElementById("new");
  const broker=window.makeSamanthaVoiceCandidateBroker(config.dataset.csrf,config.dataset.confirmation);
  renew.disabled=config.dataset.canRenew!=="true";
  renew.addEventListener("click",async()=>{
    renew.disabled=true;
    try {await broker.renew();window.location.reload();}
    catch (_) {
      document.getElementById("status").textContent="Ukončení a konečná spotřeba nejsou potvrzené serverem. Novou relaci nezahajuji.";
    }
  });
  if(config.dataset.ready!=="true") return;
  if(!window.isSecureContext || !navigator.mediaDevices || !window.RTCPeerConnection) {
    document.getElementById("status").textContent="Hlas vyžaduje HTTPS nebo localhost a podporovaný prohlížeč.";
    return;
  }
  window.mountSamanthaVoicePilot(broker,{requireConsent:true,maxSeconds:60,
    onState(state){if(state.finalUsage) renew.disabled=false;}});
})();
