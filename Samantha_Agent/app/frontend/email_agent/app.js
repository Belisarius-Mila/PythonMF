(() => {
  const byId = id => document.getElementById(id);
  const editor = byId("replyEditor");
  let editing = null;
  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }
  async function request(path, payload) {
    const response = await fetch(path, payload === undefined ? {cache: "no-store"} : {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.message || "Operaci se nepodařilo dokončit.");
    return result;
  }
  function action(label, callback, secondary = false) {
    const button = node("button", label, secondary ? "secondary" : "");
    button.type = "button";
    button.addEventListener("click", async () => {
      button.disabled = true;
      try { await callback(); await refresh(); }
      catch (error) { byId("notice").textContent = error.message; }
      finally { button.disabled = false; }
    });
    return button;
  }
  function renderCard(item) {
    const card = node("article", undefined, "card");
    const header = item.header || {}, proposal = item.proposal;
    card.append(node("h3", header.subject || "(bez předmětu)"));
    card.append(node("p", `${header.sender || ""} · ${header.date || ""}`, "meta"));
    card.append(node("p", proposal.summary));
    card.append(node("p", proposal.reason, "reason"));
    const full = node("details");
    full.append(node("summary", "Celý e-mail"), node("pre", (item.message || {}).body_text || "Text není dostupný."));
    card.append(full);
    const metadata = node("details");
    metadata.append(node("summary", "Návrh uložení"));
    const m = proposal.metadata;
    metadata.append(node("p", [m.title, m.domain, m.document_type, m.counterparty, ...m.tags].filter(Boolean).join(" · ")));
    card.append(metadata);
    const buttons = node("div", undefined, "actions");
    const enabled = item.status === "awaiting_confirmation";
    if (enabled) {
      buttons.append(action("Uložit", async () => {
        if (!window.confirm(`Uložit e-mail „${m.title}“ podle zobrazeného návrhu?`)) return;
        await request("/api/email-agent/archive", {id: item.id, proposal_digest: item.proposal_digest, confirmed: true});
        byId("notice").textContent = "E-mail byl uložen do místního archivu.";
      }));
      if (proposal.reply_draft) buttons.append(action("Upravit odpověď", async () => {
        editing = item;
        byId("replyRecipient").textContent = `Odpověď na zprávu od: ${header.sender || ""}`;
        byId("replySubject").value = proposal.reply_subject || `Re: ${header.subject || ""}`;
        byId("replyBody").value = proposal.reply_draft;
        byId("replyStatus").textContent = "";
        editor.showModal();
      }));
      for (const [label, kind] of [["Ignorovat", "ignore"], ["Smazat z Cockpitu", "dismiss"]]) {
        buttons.append(action(label, () => request("/api/email-agent/dismiss", {ids: [item.id], action: kind}), true));
      }
    } else buttons.append(action("Ověřit uložení", async () => {
      await request("/api/email-agent/archive", {id: item.id, proposal_digest: item.proposal_digest, confirmed: true});
    }));
    card.append(buttons);
    return card;
  }
  async function refresh() {
    if (editor.open) return;
    const data = await request("/api/email-agent/overview");
    const last = data.schedule.completed_at;
    byId("status").textContent = last ? `Poslední dokončená kontrola: ${new Date(last).toLocaleString("cs-CZ")}.` : "Průběžná kontrola zatím nebyla spuštěna.";
    const sourceErrors = data.sources.some(source => source.health === "error");
    if (sourceErrors || data.assessment_errors) byId("status").textContent += " Některé kontroly nebo návrhy vyžadují ověření.";
    const cards = byId("cards"); cards.replaceChildren();
    data.cards.forEach(item => cards.append(renderCard(item)));
    if (!data.cards.length) cards.append(node("p", "Žádné důležité zprávy k řešení."));
    const hours = byId("hours"); hours.replaceChildren();
    for (const hour of data.hours) {
      const row = node("div", undefined, "hour");
      row.append(node("p", hour.text), action("Smazat z Cockpitu", () => request("/api/email-agent/dismiss", {ids: hour.ids, action: "dismiss"}), true));
      hours.append(row);
    }
    if (!data.hours.length) hours.append(node("p", "Žádné další zprávy v přehledu."));
    const archived = byId("archived"); archived.replaceChildren();
    data.archived.forEach(item => archived.append(node("p", item.proposal.metadata.title)));
    if (!data.archived.length) archived.append(node("p", "Zatím žádné uložené zprávy."));
  }
  byId("closeEditor").addEventListener("click", () => editor.close());
  byId("replyForm").addEventListener("submit", async event => {
    event.preventDefault();
    const button = event.submitter; if (button) button.disabled = true;
    try {
      const proposal = {...editing.proposal, reply_subject: byId("replySubject").value, reply_draft: byId("replyBody").value};
      await request("/api/email-agent/edit", {id: editing.id, expected_digest: editing.proposal_digest, proposal});
      editor.close(); await refresh();
    } catch (error) { byId("replyStatus").textContent = error.message; }
    finally { if (button) button.disabled = false; }
  });
  refresh().catch(error => { byId("status").textContent = error.message; });
  window.setInterval(() => refresh().catch(error => { byId("status").textContent = error.message; }), 30000);
})();
