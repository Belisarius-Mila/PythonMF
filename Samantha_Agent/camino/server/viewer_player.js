"use strict";
// Map deep links open only their target card; never auto-play its media.
function caminoOpenMoment() {
  const id = window.location.hash.slice(1);
  if (!/^moment-[0-9a-f-]{36}$/.test(id)) return;
  const article = document.getElementById(id);
  const detail = article && article.querySelector("details");
  if (detail) { detail.open = true; article.scrollIntoView(); }
}
window.addEventListener("hashchange", caminoOpenMoment);
caminoOpenMoment();
// Photos open in a read-only enlarged preview; the served derivative remains the same.
const caminoLightbox = document.getElementById("mediaLightbox");
const caminoLightboxImage = document.getElementById("mediaLightboxImage");
const caminoLightboxClose = caminoLightbox && caminoLightbox.querySelector
  ? caminoLightbox.querySelector(".media-lightbox-close") : null;
let caminoLightboxReturnFocus = null;
function caminoCloseLightbox() {
  if (!caminoLightbox || !caminoLightboxImage) return;
  caminoLightbox.hidden = true;
  caminoLightbox.setAttribute("aria-hidden", "true");
  caminoLightboxImage.removeAttribute("src");
  if (document.body && document.body.classList) document.body.classList.remove("media-lightbox-open");
  if (caminoLightboxReturnFocus && caminoLightboxReturnFocus.focus) caminoLightboxReturnFocus.focus();
  caminoLightboxReturnFocus = null;
}
function caminoOpenLightbox(button) {
  const source = button.dataset.lightboxSrc;
  if (!source || !caminoLightbox || !caminoLightboxImage) return;
  caminoLightboxReturnFocus = button;
  caminoLightboxImage.src = source;
  caminoLightboxImage.alt = button.dataset.lightboxAlt || "Zvětšená fotografie";
  caminoLightbox.hidden = false;
  caminoLightbox.setAttribute("aria-hidden", "false");
  if (document.body && document.body.classList) document.body.classList.add("media-lightbox-open");
  if (caminoLightboxClose && caminoLightboxClose.focus) caminoLightboxClose.focus();
}
const caminoLightboxButtons = Array.from(document.querySelectorAll("[data-lightbox-src]"));
for (const button of caminoLightboxButtons) button.addEventListener("click", () => caminoOpenLightbox(button));
if (caminoLightboxClose) caminoLightboxClose.addEventListener("click", caminoCloseLightbox);
if (caminoLightbox) caminoLightbox.addEventListener("click", event => {
  if (event.target === caminoLightbox) caminoCloseLightbox();
});
window.addEventListener("keydown", event => {
  if (event.key === "Escape" && caminoLightbox && !caminoLightbox.hidden) caminoCloseLightbox();
});
// Long day pages expose a compact, keyboard-accessible way back to the top.
const caminoBackToTop = document.getElementById("backToTop");
if (caminoBackToTop && window.addEventListener) {
  const caminoUpdateBackToTop = () => {
    const offset = Number(window.scrollY || window.pageYOffset || 0);
    caminoBackToTop.hidden = offset < 480;
  };
  caminoBackToTop.addEventListener("click", () => {
    if (typeof window.scrollTo === "function") window.scrollTo({top: 0, behavior: "smooth"});
  });
  window.addEventListener("scroll", caminoUpdateBackToTop, {passive: true});
  caminoUpdateBackToTop();
}
// Only server-proven adjacent checkpoint segments auto-advance. Never skip gaps.
const caminoAudioPlayers = Array.from(document.querySelectorAll("audio"));
for (const player of caminoAudioPlayers) {
  player.addEventListener("play", () => {
    for (const other of caminoAudioPlayers) if (other !== player) other.pause();
  });
  player.addEventListener("ended", async () => {
    const id = player.dataset.next;
    const next = id ? document.getElementById(id) : null;
    if (!next || !caminoAudioPlayers.includes(next)) return;
    try {
      next.currentTime = 0;
      await next.play();
    } catch {
      next.focus();
      const status = document.getElementById("audioPlaybackStatus");
      if (status) status.textContent = "Další úsek spusť tlačítkem přehrát. Prohlížeč automatické pokračování nepovolil nebo médium není dostupné.";
    }
  });
}
