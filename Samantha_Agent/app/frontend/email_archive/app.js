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
          url: ""
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
          url: item.can_open ? (item.url || "") : ""
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
                        href="${escapeHtml(card.url)}">Otevřít přílohu</a>
                   </div>`
                : '<div class="attachment-unavailable">Přílohu nelze otevřít</div>'}
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

          ${renderMoreActions(data.files)}
          <div class="privacy-note">
            Zobrazuje se místní kopie. Tato stránka nic neposílá, nemaže ani nemění ve schránce.
          </div>
        </article>
      `;
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
        if (!archiveItems.some((item) => (item.archive_ref || item.archive_id) === selectedArchiveRef)) {
          selectedArchiveRef = "";
        }
        renderList();
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
