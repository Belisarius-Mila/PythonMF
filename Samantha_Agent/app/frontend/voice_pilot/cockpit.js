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
  function blocked(reason,message) {
    const status=document.getElementById("status");
    status.dataset.blockedReason=reason;
    status.textContent=message;
    document.getElementById("consent").disabled=true;
  }
  if(window.isSecureContext!==true) {
    blocked("secure_context",window.location.protocol==="http:"
      ? "Cockpit je otevřený přes HTTP. Prohlížeč zde nepovolí mikrofon. Otevři privátní HTTPS adresu Cockpitu; samotný Tailscale nestačí. Localhost platí jen na zařízení, kde server běží."
      : "Prohlížeč nepovažuje tuto stránku za zabezpečenou. Otevři Cockpit přímo v samostatné kartě přes HTTPS s platným certifikátem.");
    return;
  }
  if(!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia!=="function") {
    blocked("microphone_api","Stránka používá zabezpečené připojení, ale prohlížeč nezpřístupňuje mikrofon. Otevři ji přímo v aktuálním Chromu nebo Safari; pokud používáš omezení zařízení, ověř je také.");
    return;
  }
  if(typeof window.RTCPeerConnection!=="function") {
    blocked("webrtc","Prohlížeč zde nezpřístupňuje WebRTC potřebné pro hlasové spojení. Otevři stejnou HTTPS adresu v aktuálním Chromu nebo Safari.");
    return;
  }
  window.mountSamanthaVoicePilot(broker,{requireConsent:true,maxSeconds:60,
    onState(state){if(state.finalUsage) renew.disabled=false;}});
})();
