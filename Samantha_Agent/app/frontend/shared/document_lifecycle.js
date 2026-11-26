(() => {
  "use strict";
  const pending = new Map();
  async function apply(kind, reference, action, button) {
    const key = `${kind}:${reference}:${action}`;
    button.disabled = true;
    try {
      let payload = pending.get(key);
      if (!payload) {
        const response = await fetch(`/api/documents/trash/preview?${new URLSearchParams({kind, reference})}`, {cache: "no-store"});
        const item = await response.json();
        if (!response.ok || !item.ok) throw new Error(item.message || "Dokument není dostupný.");
        const verb = action === "trash" ? "Přesunout do koše" : "Obnovit z koše";
        const copy = kind === "scan" ? "Původní sken" : "Dokument v trezoru";
        if (!window.confirm(`${verb}: „${item.title}“?\n\n${copy}. Změna se týká pouze této položky; ostatní kopie zůstanou zachované.`)) return false;
        const bytes = crypto.getRandomValues(new Uint8Array(16));
        payload = {kind, reference, action, expected_revision: item.revision, confirmed: true,
          request_id: Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("")};
        pending.set(key, payload);
      }
      const response = await fetch("/api/documents/trash", {method: "POST",
        headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
      const result = await response.json();
      if (response.status >= 500) throw new Error("Server nepotvrdil výsledek. Ověř původní požadavek.");
      if (!response.ok || !result.ok) {
        pending.delete(key);
        throw new Error(result.message || "Změna není potvrzená.");
      }
      pending.delete(key);
      return true;
    } catch (error) {
      if (pending.has(key)) button.textContent = "Ověřit původní požadavek";
      throw error;
    } finally {button.disabled = false;}
  }
  globalThis.SamanthaDocumentLifecycle = {apply};
})();
