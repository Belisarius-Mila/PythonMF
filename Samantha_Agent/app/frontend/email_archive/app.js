    const listNode = document.getElementById("archiveList");
    const detailPane = document.getElementById("detailPane");
    const statusNode = document.getElementById("status");
    const searchInput = document.getElementById("searchInput");
    const searchBtn = document.getElementById("searchBtn");
    const refreshBtn = document.getElementById("refreshBtn");
    const returnBtn = document.getElementById("returnBtn");
    const messageBackBtn = document.getElementById("messageBackBtn");
    const listTitle = document.getElementById("messageListTitle");
    const allCount = document.getElementById("allCount");
    const attachmentCount = document.getElementById("attachmentCount");
    const folderButtons = [...document.querySelectorAll("[data-filter]")];

    let archiveItems = [];
    let selectedArchiveRef = "";
    let activeFilter = "all";
    let listRequestNumber = 0;
    let detailRequestNumber = 0;
    const requestedArchiveRef = new URLSearchParams(window.location.search).get("archive") || "";

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[character]));
    }

    function fileSize(bytes) {
      const value = Number(bytes || 0);
      if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
      if (value >= 1024) return `${Math.round(value / 1024)} kB`;
      return value > 0 ? `${value} B` : "velikost nezjištěna";
    }

    function parsedDate(value) {
      const moment = new Date(String(value || ""));
      return Number.isNaN(moment.getTime()) ? null : moment;
    }

    function shortDate(value) {
      const moment = parsedDate(value);
      if (!moment) return String(value || "");
      const now = new Date();
      const sameYear = moment.getFullYear() === now.getFullYear();
      return new Intl.DateTimeFormat("cs-CZ", sameYear
        ? {day: "numeric", month: "short"}
        : {day: "numeric", month: "short", year: "numeric"}
      ).format(moment);
    }

    function longDate(value) {
      const moment = parsedDate(value);
      if (!moment) return String(value || "Datum není uvedeno");
      return new Intl.DateTimeFormat("cs-CZ", {
        day: "numeric",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      }).format(moment);
    }

    function normalizeFilename(value) {
      return String(value || "")
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9.]+/g, "-")
        .replace(/^-+|-+$/g, "");
    }

    function fileExtension(value) {
      const name = String(value || "");
      const dot = name.lastIndexOf(".");
      return dot > 0 ? name.slice(dot + 1).toUpperCase() : "SOUBOR";
    }

    function visibleItems() {
      if (activeFilter === "attachments") {
        return archiveItems.filter((item) => Number(item.attachments_count || 0) > 0);
      }
      return archiveItems;
    }

    function updateFolderState() {
      allCount.textContent = String(archiveItems.length);
      attachmentCount.textContent = String(
        archiveItems.filter((item) => Number(item.attachments_count || 0) > 0).length
      );
      folderButtons.forEach((button) => {
        const active = button.dataset.filter === activeFilter;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");
      });
      listTitle.textContent = activeFilter === "attachments" ? "S přílohami" : "Archivované";
    }

    function updateActiveMessage() {
      listNode.querySelectorAll("[data-archive-ref]").forEach((button) => {
        const active = button.dataset.archiveRef === selectedArchiveRef;
        button.classList.toggle("active", active);
        button.setAttribute("aria-current", active ? "true" : "false");
      });
    }

    function renderList() {
      updateFolderState();
      const items = visibleItems();
      if (!items.length) {
        listNode.innerHTML = '<div class="empty-list">V této části archivu nic není.</div>';
        return;
      }
      listNode.innerHTML = items.map((item) => {
        const archiveRef = item.archive_ref || item.archive_id || "";
        const attachmentTotal = Number(item.attachments_count || 0);
        const sender = item.sender || "Odesílatel není uveden";
        const subject = item.subject || "(bez předmětu)";
        return `
          <button class="message-item ${archiveRef === selectedArchiveRef ? "active" : ""}"
                  data-archive-ref="${escapeHtml(archiveRef)}"
                  aria-label="${escapeHtml(`${sender}: ${subject}`)}">
            <div class="sender-line">
              <div class="sender">${escapeHtml(sender)}</div>
              <div class="message-date">${escapeHtml(shortDate(item.date || item.archived_at))}</div>
            </div>
            <div class="message-subject">${escapeHtml(subject)}</div>
            <div class="message-summary">
              ${attachmentTotal > 0
                ? `<span class="attachment-indicator">📎 ${attachmentTotal}</span>`
                : ""}
              <span class="message-archive-date">uloženo v archivu</span>
            </div>
          </button>
        `;
      }).join("");
      listNode.querySelectorAll("[data-archive-ref]").forEach((button) => {
        button.addEventListener("click", () => loadDetail(button.dataset.archiveRef || ""));
      });
    }

    function attachmentKey(item, fallback) {
      return normalizeFilename(item.filename || item.title) || fallback;
    }

    function buildAttachmentCards(data) {
      const cards = new Map();
      (data.attachments || []).forEach((item, index) => {
        const key = attachmentKey(item, `email-${index}`);
        cards.set(key, {
          key,
          filename: item.filename || "Příloha bez názvu",
          contentType: item.content_type || "",
          sizeBytes: item.size_bytes,
          location: "email",
          url: item.url || "",
          attachmentRef: item.attachment_ref || ""
        });
      });

      (data.downloaded_attachments || []).forEach((item, index) => {
        const normalized = attachmentKey(item, `download-${index}`);
        const matchingKey = [...cards.keys()].find((key) => normalized === key || normalized.endsWith(key));
        const key = matchingKey || normalized;
        const previous = cards.get(key) || {};
        cards.set(key, {
          ...previous,
          key,
          filename: previous.filename || item.filename || "Stažená příloha",
          contentType: previous.contentType || item.content_type || "",
          sizeBytes: item.size_bytes || previous.sizeBytes,
          location: "downloaded",
          url: item.url || ""
        });
      });

      (data.vault_attachments || []).forEach((item, index) => {
        const normalized = attachmentKey(item, `vault-${index}`);
        const matchingKey = [...cards.keys()].find((key) => normalized === key || normalized.endsWith(key) || key.endsWith(normalized));
        const key = matchingKey || normalized;
        const previous = cards.get(key) || {};
        cards.set(key, {
          ...previous,
          key,
          filename: item.filename || previous.filename || item.title || "Uložená příloha",
          title: item.title || "",
          contentType: previous.contentType || item.document_type || "",
          documentType: item.document_type || "",
          sizeBytes: item.size_bytes || previous.sizeBytes,
          readingStatus: item.reading_status_label || "",
          location: "vault",
          url: item.can_open ? (item.direct_url || item.url || "") : ""
        });
      });
      return [...cards.values()];
    }

    function attachmentStatus(card) {
      if (card.location === "vault") {
        return ["Uloženo v dokumentech", card.readingStatus].filter(Boolean).join(" · ");
      }
      if (card.location === "downloaded") return "Staženo do dokumentů";
      return "Soubor této přílohy není v místním archivu uložený";
    }

    function attachmentActionLabel(card) {
      const contentType = String(card.contentType || "").toLowerCase();
      const filename = String(card.filename || "").toLowerCase();
      if (contentType.includes("pdf") || filename.endsWith(".pdf")) {
        return "Otevřít celé PDF";
      }
      return "Otevřít přílohu";
    }

    function renderAttachmentCards(data) {
      const cards = buildAttachmentCards(data);
      if (!cards.length) {
        return '<div class="empty-attachments">Tento e-mail nemá evidovanou přílohu.</div>';
      }
      return `
        <div class="attachment-grid">
          ${cards.map((card) => `
            <div class="attachment-card">
              <div class="attachment-icon" aria-hidden="true">${escapeHtml(fileExtension(card.filename))}</div>
              <div>
                <div class="attachment-name">${escapeHtml(card.filename || card.title)}</div>
                <div class="attachment-meta">
                  ${escapeHtml(fileSize(card.sizeBytes))} · ${escapeHtml(attachmentStatus(card))}
                </div>
              </div>
              ${card.url
                ? `<div class="attachment-actions">
                     <a class="action-link" target="_blank" rel="noopener"
                        href="${escapeHtml(card.url)}">${escapeHtml(attachmentActionLabel(card))}</a>
                     ${card.attachmentRef
                       ? `<button type="button" class="ai-link"
                            data-ai-attachment-ref="${escapeHtml(card.attachmentRef)}">AI přečíst e-mail + přílohu</button>`
                       : ""}
                   </div>`
                : `${card.attachmentRef
                    ? `<div class="attachment-actions">
                         <button type="button" class="ai-link"
                           data-ai-attachment-ref="${escapeHtml(card.attachmentRef)}">AI přečíst e-mail + přílohu</button>
                       </div>`
                    : '<div class="attachment-unavailable">Přílohu nelze otevřít</div>'}`}
            </div>
          `).join("")}
        </div>
      `;
    }

    function renderMoreActions(files) {
      const friendlyLabels = {
        body_html: "Původní vzhled zprávy",
        body_txt: "Textový soubor",
        original_eml: "Původní e-mail (.eml)"
      };
      const useful = (files || []).filter((file) => friendlyLabels[file.key]);
      if (!useful.length) return "";
      return `
        <details class="more">
          <summary>Další možnosti</summary>
          <div class="more-actions">
            ${useful.map((file) => `
              <a target="_blank" rel="noopener" href="${escapeHtml(file.url)}">
                ${escapeHtml(friendlyLabels[file.key])}
              </a>
            `).join("")}
          </div>
        </details>
      `;
    }

    function renderAiMetadataResult(data) {
      if (!data.ok) {
        return `<div class="ai-error">${escapeHtml(data.message || "AI návrh se nepodařilo připravit.")}</div>`;
      }
      const changedFields = (data.fields || []).filter((item) => item.proposed);
      const fieldRows = changedFields.map((item) => `
        <div class="ai-comparison">
          <div><strong>${escapeHtml(item.label || item.field)}</strong></div>
          <div>${escapeHtml(
            `${Array.isArray(item.current) ? item.current.join(", ") : (item.current || "nezjištěno")} → `
            + `${Array.isArray(item.proposed) ? item.proposed.join(", ") : item.proposed}`
          )}</div>
          ${item.evidence
            ? `<div class="ai-evidence">Důkaz: „${escapeHtml(item.evidence)}“ · ${escapeHtml(item.confidence || "low")}</div>`
            : ""}
        </div>
      `).join("");
      const dates = (data.important_dates || []).map((item) => `
        <div class="ai-date">
          <strong>${escapeHtml(item.date)}</strong> · ${escapeHtml(item.type)} · ${escapeHtml(item.confidence)}
          <div class="ai-evidence">Důkaz: „${escapeHtml(item.evidence)}“</div>
        </div>
      `).join("");
      const warnings = (data.warnings || []).length
        ? `<div class="ai-warning">${escapeHtml(data.warnings.join(" "))}</div>`
        : "";
      const truncation = data.input_truncated || data.body_truncated
        ? '<div class="ai-warning">AI neměla celý mimořádně dlouhý text; výsledek ber jako částečný.</div>'
        : "";
      return `
        <div class="ai-summary">${escapeHtml(data.summary || data.message || "")}</div>
        ${fieldRows || '<div class="ai-evidence">AI nenašla ověřenou změnu základních metadat.</div>'}
        ${dates ? `<div class="ai-dates"><strong>Důležitá data</strong>${dates}</div>` : ""}
        ${warnings}
        ${truncation}
        <div class="ai-readonly">Jen návrh ke kontrole. Nic nebylo uloženo ani změněno.</div>
      `;
    }

    async function requestAiMetadata(attachmentRef, triggerButton) {
      if (!selectedArchiveRef) return;
      const resultNode = detailPane.querySelector("[data-ai-result]");
      if (!resultNode) return;
      const originalLabel = triggerButton.textContent;
      triggerButton.disabled = true;
      triggerButton.textContent = "AI čte…";
      resultNode.innerHTML = '<div class="ai-loading">Codex připravuje read-only návrh…</div>';
      try {
        const response = await fetch("/api/email-archive/ai-metadata", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            archive_id: selectedArchiveRef,
            attachment_ref: attachmentRef || ""
          })
        });
        const data = await response.json();
        resultNode.innerHTML = renderAiMetadataResult(data);
      } catch (error) {
        resultNode.innerHTML = `<div class="ai-error">AI návrh se nepodařilo načíst: ${escapeHtml(error)}</div>`;
      } finally {
        triggerButton.disabled = false;
        triggerButton.textContent = originalLabel;
      }
    }

    function renderDetail(data) {
      if (!data.ok) {
        detailPane.innerHTML = `
          <div class="reader-empty">
            <div class="reader-empty-icon" aria-hidden="true">!</div>
            <h2>Zprávu se nepodařilo otevřít</h2>
            <p>${escapeHtml(data.message || "Archiv není dostupný.")}</p>
          </div>
        `;
        return;
      }
      const bodyText = String(data.body_text || "").trim();
      detailPane.innerHTML = `
        <article class="mail-content">
          <header class="mail-header">
            <h2 class="mail-subject">${escapeHtml(data.subject || "(bez předmětu)")}</h2>
            <div class="mail-header-line">
              <div>
                <div class="mail-sender">${escapeHtml(data.sender || "Odesílatel není uveden")}</div>
                <div class="attachment-meta">archivovaná zpráva</div>
              </div>
              <div class="mail-date">${escapeHtml(longDate(data.date || data.archived_at))}</div>
            </div>
          </header>

          <section class="section-block" aria-labelledby="attachmentsTitle">
            <h3 class="section-title" id="attachmentsTitle">Přílohy</h3>
            ${renderAttachmentCards(data)}
          </section>

          <section class="section-block" aria-labelledby="bodyTitle">
            <h3 class="section-title" id="bodyTitle">Zpráva</h3>
            <div class="message-body">${escapeHtml(bodyText || "Text zprávy není v archivu k dispozici.")}</div>
            ${data.body_truncated
              ? '<div class="body-truncated">Zpráva je velmi dlouhá. Zobrazuje se její bezpečně omezená část.</div>'
              : ""}
          </section>

          <section class="section-block ai-section" aria-labelledby="aiTitle">
            <div class="ai-heading">
              <div>
                <h3 class="section-title" id="aiTitle">AI návrh metadat</h3>
                <div class="ai-evidence">Spustí se jen ručně pro tento otevřený e-mail. Návrh se nikam nezapíše.</div>
              </div>
              <button type="button" class="ai-action" data-ai-email>AI přečíst e-mail</button>
            </div>
            <div class="ai-result" data-ai-result>
              Zatím nebyla spuštěna žádná AI analýza.
            </div>
          </section>

          ${renderMoreActions(data.files)}
          <div class="privacy-note">
            Zobrazuje se místní kopie. Tato stránka nic neposílá, nemaže ani nemění ve schránce.
          </div>
        </article>
      `;
      const emailAiButton = detailPane.querySelector("[data-ai-email]");
      if (emailAiButton) {
        emailAiButton.addEventListener("click", () => requestAiMetadata("", emailAiButton));
      }
      detailPane.querySelectorAll("[data-ai-attachment-ref]").forEach((button) => {
        button.addEventListener("click", () => {
          requestAiMetadata(button.dataset.aiAttachmentRef || "", button);
        });
      });
    }

    function showMessageList() {
      document.body.classList.remove("detail-open");
    }

    async function loadList() {
      const requestNumber = ++listRequestNumber;
      statusNode.textContent = "Načítám…";
      listNode.innerHTML = '<div class="loading-card">Načítám uložené e-maily…</div>';
      try {
        const params = new URLSearchParams({q: searchInput.value || "", limit: "160"});
        const response = await fetch(`/api/email-archive/list?${params.toString()}`);
        const data = await response.json();
        if (requestNumber !== listRequestNumber) return;
        archiveItems = Array.isArray(data.items) ? data.items : [];
        statusNode.textContent = `${archiveItems.length} e-mailů`;
        if (
          requestedArchiveRef
          && archiveItems.some((item) => (item.archive_ref || item.archive_id) === requestedArchiveRef)
        ) {
          selectedArchiveRef = requestedArchiveRef;
        }
        if (!archiveItems.some((item) => (item.archive_ref || item.archive_id) === selectedArchiveRef)) {
          selectedArchiveRef = "";
        }
        renderList();
        if (requestedArchiveRef) {
          await loadDetail(requestedArchiveRef);
          return;
        }
        const first = visibleItems()[0];
        if (!selectedArchiveRef && first && window.matchMedia("(min-width: 821px)").matches) {
          await loadDetail(first.archive_ref || first.archive_id || "");
        }
      } catch (error) {
        if (requestNumber !== listRequestNumber) return;
        archiveItems = [];
        updateFolderState();
        statusNode.textContent = "Archiv se nepodařilo načíst";
        listNode.innerHTML = `<div class="empty-list">Chyba načtení archivu: ${escapeHtml(error)}</div>`;
      }
    }

    async function loadDetail(archiveRef) {
      if (!archiveRef) return;
      const requestNumber = ++detailRequestNumber;
      selectedArchiveRef = archiveRef;
      updateActiveMessage();
      document.body.classList.add("detail-open");
      detailPane.innerHTML = '<div class="loading-card">Otevírám zprávu…</div>';
      try {
        const params = new URLSearchParams({archive_id: archiveRef});
        const response = await fetch(`/api/email-archive/detail?${params.toString()}`);
        const data = await response.json();
        if (requestNumber !== detailRequestNumber) return;
        renderDetail(data);
      } catch (error) {
        if (requestNumber !== detailRequestNumber) return;
        renderDetail({ok: false, message: `Chyba načtení: ${error}`});
      }
    }

    function returnToCockpit() {
      if (window.opener && !window.opener.closed) {
        window.opener.focus();
        window.close();
        return;
      }
      window.location.href = "/";
    }

    folderButtons.forEach((button) => {
      button.addEventListener("click", () => {
        activeFilter = button.dataset.filter || "all";
        renderList();
      });
    });
    searchBtn.addEventListener("click", loadList);
    refreshBtn.addEventListener("click", loadList);
    returnBtn.addEventListener("click", returnToCockpit);
    messageBackBtn.addEventListener("click", showMessageList);
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        loadList();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && document.body.classList.contains("detail-open")) {
        showMessageList();
      }
    });
    loadList();
