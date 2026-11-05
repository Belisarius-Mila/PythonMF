(() => {
  const byId = id => document.getElementById(id);
  const editor = byId("replyEditor");
  let editing = null;
  let pendingReply = null;
  let replyBusy = false;
  let replyOutcomeLocked = false;
  let pushcutDirty = false;
  let pushcutBusy = false;
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
    const archived = item.status === "archived";
    const replyStatus = (item.reply || {}).status;
    if (replyStatus === "smtp_sent") card.append(node("p", "Odpověď přijal odesílací server."));
    if (["sending", "delivery_unknown"].includes(replyStatus)) card.append(node("p", "Výsledek odeslání vyžaduje ověření. Odpověď znovu neposílej."));
    if ((item.reply || {}).receipt?.sent_copy_status === "failed") card.append(node("p", "Kopie v Odeslané poště se nepodařila ověřit; odpověď znovu neposílej."));
    if (enabled || archived) {
      if (!archived)
      buttons.append(action("Uložit", async () => {
        if (!window.confirm(`Uložit e-mail „${m.title}“ podle zobrazeného návrhu?`)) return;
        await request("/api/email-agent/archive", {id: item.id, proposal_digest: item.proposal_digest, confirmed: true});
        byId("notice").textContent = "E-mail byl uložen do místního archivu.";
      }));
      if (proposal.reply_draft && !["sending", "delivery_unknown", "smtp_sent"].includes(replyStatus)) buttons.append(action("Upravit odpověď", async () => {
        editing = item;
        byId("replyRecipient").textContent = `Odpověď na zprávu od: ${header.sender || ""}`;
        byId("replySubject").value = proposal.reply_subject || `Re: ${header.subject || ""}`;
        byId("replyBody").value = proposal.reply_draft;
        byId("replyStatus").textContent = "";
        resetConfirmation();
        editor.showModal();
      }));
      for (const [label, kind] of [["Ignorovat", "ignore"], ["Smazat z Cockpitu", "dismiss"]]) {
        buttons.append(action(label, () => request("/api/email-agent/dismiss", {ids: [item.id], action: kind}), true));
      }
      buttons.append(action("Příště nedůležité", async () => {
        await request("/api/email-agent/remember-importance", {id: item.id});
        byId("notice").textContent = "Preference pro tohoto odesílatele a podobný předmět je uložená. Tuto kartu můžeš dál vyřídit.";
      }, true));
    } else buttons.append(action("Ověřit uložení", async () => {
      await request("/api/email-agent/archive", {id: item.id, proposal_digest: item.proposal_digest, confirmed: true});
    }));
    card.append(buttons);
    return card;
  }
  function resetConfirmation() {
    pendingReply = null;
    replyOutcomeLocked = false;
    byId("replyConfirmation").hidden = true;
    byId("prepareReplySend").hidden = false;
    byId("saveReplyDraft").hidden = false;
    setReplyBusy(false);
  }
  function setReplyBusy(busy) {
    replyBusy = busy;
    byId("closeEditor").disabled = busy;
    byId("saveReplyDraft").disabled = busy || replyOutcomeLocked;
    byId("prepareReplySend").disabled = busy || replyOutcomeLocked;
    byId("reallySendReply").disabled = busy || !pendingReply;
    byId("backToReply").disabled = busy || replyOutcomeLocked;
    byId("replySubject").readOnly = busy || Boolean(pendingReply) || replyOutcomeLocked;
    byId("replyBody").readOnly = busy || Boolean(pendingReply) || replyOutcomeLocked;
  }
  async function saveEditor() {
    const current = editing;
    const proposal = {...current.proposal, reply_subject: byId("replySubject").value, reply_draft: byId("replyBody").value};
    const result = await request("/api/email-agent/edit", {id: current.id, expected_digest: current.proposal_digest, proposal});
    editing = {...current, proposal, proposal_digest: result.proposal_digest};
  }
  async function refresh() {
    if (editor.open) return;
    const data = await request("/api/email-agent/overview");
    const last = data.schedule.completed_at;
    const pushcut = data.pushcut || {};
    if (!pushcutDirty && !pushcutBusy) {
      byId("pushcutEnabled").checked = Boolean(pushcut.enabled);
      const remoteOrigin = window.location?.protocol === "https:" ? window.location.origin : "";
      byId("pushcutCockpitUrl").value = pushcut.cockpit_url || (remoteOrigin ? remoteOrigin + "/emails-to-resolve/" : "");
    }
    const counts = pushcut.counts || {};
    byId("pushcutStatus").textContent = !pushcut.configured ? "Pushcut zatím není připojený."
      : `Upozornění ${pushcut.enabled ? "zapnutá" : "vypnutá"}. Čeká: ${counts.pending || 0}. Výsledek vyžaduje ověření: ${(counts.delivery_unknown || 0) + (counts.sending || 0) + (counts.rejected || 0)}.`;
    byId("status").textContent = last ? `Poslední dokončená kontrola: ${new Date(last).toLocaleString("cs-CZ")}.` : "Průběžná kontrola zatím nebyla spuštěna.";
    const sourceErrors = data.sources.some(source => source.health === "error");
    if (sourceErrors || data.assessment_errors) byId("status").textContent += " Některé kontroly nebo návrhy vyžadují ověření.";
    const cards = byId("cards"); cards.replaceChildren();
    data.cards.forEach(item => cards.append(renderCard(item)));
    if (!data.cards.length) cards.append(node("p", "Žádné důležité zprávy k řešení."));
    const hours = byId("hours"); hours.replaceChildren();
    for (const hour of data.hours) {
      const row = node("div", undefined, "hour mail-hour");
      row.append(node("p", hour.text), action("Smazat z Cockpitu", () => request("/api/email-agent/dismiss", {ids: hour.ids, action: "dismiss"}), true));
      const choices = node("details");
      choices.append(node("summary", "Příště nezobrazovat…"));
      for (const message of hour.messages || []) {
        const choice = node("div", undefined, "actions");
        choice.append(node("span", message.text), action("Příště nezobrazovat", async () => {
          await request("/api/email-agent/remember-visibility", {id: message.id});
          byId("notice").textContent = "Podobné nedůležité zprávy od tohoto odesílatele se nezobrazují ani v dosavadním přehledu. Důležité zprávy se dál zobrazí.";
        }, true));
        choices.append(choice);
      }
      if ((hour.messages || []).length) row.append(choices);
      hours.append(row);
    }
    if (!data.hours.length) hours.append(node("p", "Žádné další zprávy v přehledu."));
    const preferences = byId("importancePreferences"); preferences.replaceChildren();
    for (const preference of data.importance_preferences || []) {
      const row = node("div", undefined, "hour");
      row.append(node("p", `${preference.sender} · podobný předmět: ${preference.subject}`),
        action("Zrušit preferenci", async () => {
          await request("/api/email-agent/forget-importance", {id: preference.id});
          byId("notice").textContent = "Preference byla zrušena. Další zprávy budou posouzené bez tohoto vodítka.";
        }, true));
      preferences.append(row);
    }
    if (!preferences.children.length) preferences.append(node("p", "Zatím žádné uložené preference."));
    const visibility = byId("visibilityPreferences"); visibility.replaceChildren();
    for (const preference of data.visibility_preferences || []) {
      const row = node("div", undefined, "hour");
      row.append(node("p", `${preference.sender} · podobný předmět: ${preference.subject}`),
        action("Zrušit nezobrazování", async () => {
          await request("/api/email-agent/forget-visibility", {id: preference.id});
          byId("notice").textContent = "Nezobrazování bylo zrušeno. Odpovídající nedůležité zprávy se opět zobrazují.";
        }, true));
      visibility.append(row);
    }
    if (!visibility.children.length) visibility.append(node("p", "Zatím žádná pravidla nezobrazování."));
    const archived = byId("archived"); archived.replaceChildren();
    data.archived.forEach(item => archived.append(node("p", item.proposal.metadata.title)));
    if (!data.archived.length) archived.append(node("p", "Zatím žádné uložené zprávy."));
  }
  function setPushcutBusy(busy) {
    pushcutBusy = busy;
    byId("savePushcut").disabled = busy;
    byId("testPushcut").disabled = busy;
    byId("pushcutWebhook").readOnly = busy;
    byId("pushcutCockpitUrl").readOnly = busy;
    byId("pushcutEnabled").disabled = busy;
  }
  for (const id of ["pushcutWebhook", "pushcutCockpitUrl", "pushcutEnabled"]) {
    byId(id).addEventListener("input", () => { pushcutDirty = true; });
  }
  byId("pushcutForm").addEventListener("submit", async event => {
    event.preventDefault();
    if (pushcutBusy) return;
    setPushcutBusy(true);
    try {
      await request("/api/email-agent/pushcut/configure", {
        webhook_url: byId("pushcutWebhook").value.trim(), cockpit_url: byId("pushcutCockpitUrl").value.trim(),
        enabled: byId("pushcutEnabled").checked
      });
      pushcutDirty = false;
      byId("pushcutWebhook").value = "";
      byId("pushcutTestStatus").textContent = "Nastavení uloženo. Ověř zvuk a otevření odkazu testem na iPhonu.";
    } catch (error) { byId("pushcutTestStatus").textContent = error.message; }
    finally { setPushcutBusy(false); }
    await refresh();
  });
  byId("testPushcut").addEventListener("click", async () => {
    if (pushcutBusy) return;
    if (pushcutDirty) { byId("pushcutTestStatus").textContent = "Nejdřív ulož změněné nastavení."; return; }
    setPushcutBusy(true);
    try {
      const result = await request("/api/email-agent/pushcut/test", {
        request_id: Date.now().toString(36) + "_" + Math.random().toString(36).slice(2), confirmed: true
      });
      byId("pushcutTestStatus").textContent = result.status === "accepted"
        ? "Pushcut test přijal. Na iPhonu ověř zvuk a klepnutím otevři E-maily k řešení."
        : result.status === "rejected" ? "Pushcut test odmítl. Ověř Copy URL a existenci oznámení v aplikaci."
        : "Výsledek testu není potvrzený. Před dalším pokusem zkontroluj iPhone.";
    } catch (error) { byId("pushcutTestStatus").textContent = error.message; }
    finally { setPushcutBusy(false); }
    await refresh();
  });
  byId("closeEditor").addEventListener("click", () => { if (!replyBusy) editor.close(); });
  editor.addEventListener("cancel", event => { if (replyBusy) event.preventDefault(); });
  byId("replyForm").addEventListener("submit", async event => {
    event.preventDefault();
    if (replyBusy || replyOutcomeLocked) return;
    setReplyBusy(true);
    const button = event.submitter; if (button) button.disabled = true;
    try {
      await saveEditor();
      editor.close(); await refresh();
    } catch (error) { byId("replyStatus").textContent = error.message; }
    finally { if (button) button.disabled = false; setReplyBusy(false); }
  });
  byId("backToReply").addEventListener("click", () => { if (!replyBusy && !replyOutcomeLocked) resetConfirmation(); });
  byId("prepareReplySend").addEventListener("click", async () => {
    if (replyBusy || replyOutcomeLocked) return;
    setReplyBusy(true);
    try {
      await saveEditor();
      const result = await request("/api/email-agent/prepare-reply", {id: editing.id, expected_digest: editing.proposal_digest});
      pendingReply = result.prepared;
      byId("replySubject").value = pendingReply.subject;
      byId("replyBody").value = pendingReply.body;
      byId("replySubject").readOnly = true; byId("replyBody").readOnly = true;
      byId("replyQuestion").textContent = `Opravdu odeslat odpověď ${pendingReply.recipient_name || ""} <${pendingReply.recipient}>?`;
      byId("replySender").textContent = `Z účtu: ${pendingReply.sender}`;
      byId("replyConfirmation").hidden = false;
      byId("prepareReplySend").hidden = true; byId("saveReplyDraft").hidden = true;
      byId("replyStatus").textContent = "Zkontroluj příjemce, předmět a konečný text nad tímto potvrzením.";
    } catch (error) { byId("replyStatus").textContent = error.message; }
    finally { setReplyBusy(false); }
  });
  byId("reallySendReply").addEventListener("click", async () => {
    if (!pendingReply || replyBusy || replyOutcomeLocked) return;
    if (byId("replySubject").value !== pendingReply.subject || byId("replyBody").value !== pendingReply.body) {
      resetConfirmation(); byId("replyStatus").textContent = "Text se změnil. Připrav nové potvrzení."; return;
    }
    setReplyBusy(true);
    byId("replyStatus").textContent = "Odesílám odpověď…";
    try {
      const result = await request("/api/email-agent/send-reply", {id: editing.id, confirmed: true,
        confirmation_token: pendingReply.confirmation_token, confirmation_digest: pendingReply.confirmation_digest});
      pendingReply = null;
      if (result.receipt.status === "smtp_sent") {
        editor.close();
        byId("notice").textContent = result.receipt.sent_copy_status === "failed"
          ? "Odpověď přijal odesílací server; kopii v Odeslané poště se nepodařilo ověřit."
          : "Odpověď přijal odesílací server.";
        await refresh();
      } else {
        replyOutcomeLocked = result.receipt.status !== "not_sent";
        byId("replyStatus").textContent = result.receipt.status === "not_sent"
          ? "Server odpověď nepřijal. Zavři okno a zkontroluj stav karty."
          : "Výsledek odeslání je nejistý. Odpověď znovu neposílej; nejdřív ověř původní pokus.";
      }
    } catch (error) { pendingReply = null; replyOutcomeLocked = true; byId("replyStatus").textContent = error.message; }
    finally { setReplyBusy(false); }
  });
  refresh().catch(error => { byId("status").textContent = error.message; });
  window.setInterval(() => refresh().catch(error => { byId("status").textContent = error.message; }), 30000);
})();
