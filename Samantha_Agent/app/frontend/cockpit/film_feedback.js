(() => {
  "use strict";
  function create(root) {
    const message = root.querySelector("[data-film-feedback-message]");
    const label = root.querySelector("[data-film-feedback-label]");
    const dismiss = root.querySelector("button");
    const doc = root.ownerDocument;
    const entries = new Map();
    const priorities = {info: 0, success: 1, busy: 2, warning: 3, error: 4};
    const labels = {info: "Informace", success: "Hotovo", busy: "Probíhá", warning: "Vyžaduje zásah", error: "Chyba"};
    let serial = 0, visible = null;
    function render() {
      if (doc?.hidden) { root.classList.add("hidden"); message.textContent = ""; label.textContent = ""; return; }
      visible = [...entries.values()].sort((a, b) => priorities[b.kind] - priorities[a.kind] || b.serial - a.serial)[0];
      root.classList.toggle("hidden", !visible);
      if (!visible) { message.textContent = ""; return; }
      root.dataset.kind = visible.kind;
      message.setAttribute("role", visible.kind === "error" ? "alert" : "status");
      label.textContent = labels[visible.kind];
      message.textContent = visible.message;
      dismiss.disabled = visible.kind === "busy";
      dismiss.setAttribute("aria-label", visible.kind === "busy" ? "Právě probíhající operace" : "Zavřít zprávu");
    }
    dismiss.addEventListener("click", () => {
      if (!visible || visible.kind === "busy") return;
      entries.delete(visible.channel); render();
      if (!visible) root.closest(".modal")?.querySelector("#caminoFilmCloseBtn")?.focus({preventScroll: true});
    });
    doc?.addEventListener("visibilitychange", render);
    return {
      report({message: value, kind = "info", channel = "editor", onlyIfBusy = false}) {
        if (!(kind in priorities)) kind = "info";
        const previous = entries.get(channel);
        if (onlyIfBusy && previous?.kind !== "busy") return;
        // Routine autosave/polling must never hide an unresolved warning/error.
        if (value && kind === "info" && previous && priorities[previous.kind] >= priorities.warning) return;
        if (value) entries.set(channel, {message: value, kind, channel, serial: ++serial});
        else entries.delete(channel);
        render();
      },
      clear() { entries.clear(); render(); },
    };
  }
  window.SamanthaFilmFeedback = {create};
})();
