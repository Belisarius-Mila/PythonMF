    const listNode = document.getElementById("archiveList");
    const detailPane = document.getElementById("detailPane");
    const statusNode = document.getElementById("status");
    const searchInput = document.getElementById("searchInput");
    const searchBtn = document.getElementById("searchBtn");
    const refreshBtn = document.getElementById("refreshBtn");
    const returnBtn = document.getElementById("returnBtn");
    let selectedArchiveId = "";

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }[ch]));
    }

    function fileSize(bytes) {
      const value = Number(bytes || 0);
      if (value >= 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
      if (value >= 1024) return `${Math.round(value / 1024)} kB`;
      return `${value} B`;
    }

    function renderList(items) {
      if (!items.length) {
        listNode.innerHTML = '<div class="empty">Nic nenalezeno.</div>';
        return;
      }
      listNode.innerHTML = items.map((item) => `
        <button class="item ${item.archive_id === selectedArchiveId ? "active" : ""}" data-archive-id="${escapeHtml(item.archive_id)}">
          <div class="subject">${escapeHtml(item.subject || item.archive_id)}</div>
          <div class="meta">UID ${escapeHtml(item.uid || "")} | ${escapeHtml(item.date || "")}</div>
          <div class="meta">${escapeHtml(item.sender || "")}</div>
          <div class="actions">
            <span class="pill">odkazy: ${Number(item.links_count || 0)}</span>
            <span class="pill">přílohy: ${Number(item.attachments_count || 0)}</span>
          </div>
        </button>
      `).join("");
      listNode.querySelectorAll("[data-archive-id]").forEach((button) => {
        button.addEventListener("click", () => loadDetail(button.dataset.archiveId || ""));
      });
    }

    function renderDetail(data) {
      if (!data.ok) {
        detailPane.innerHTML = `<div class="empty">${escapeHtml(data.message || "Archiv se nepodařilo načíst.")}</div>`;
        return;
      }
      const files = data.files || [];
      const attachments = data.attachments || [];
      const downloaded = data.downloaded_attachments || [];
      detailPane.innerHTML = `
        <div class="subject">${escapeHtml(data.subject || data.archive_id)}</div>
        <div class="meta">Archive ID: ${escapeHtml(data.archive_id || "")}</div>
        <div class="meta">UID: ${escapeHtml(data.uid || "")}</div>
        <div class="meta">Datum: ${escapeHtml(data.date || "")}</div>
        <div class="meta">Odesílatel: ${escapeHtml(data.sender || "")}</div>
        <div class="meta">Složka: ${escapeHtml(data.relative_path || "")}</div>
        <div class="files">
          ${files.map((file) => `<a class="button secondary" target="_blank" href="${escapeHtml(file.url)}">${escapeHtml(file.label)} (${fileSize(file.size_bytes)})</a>`).join("")}
        </div>
        <h2>Stažené přílohy v document inboxu</h2>
        ${downloaded.length ? downloaded.map((item) => `
          <div class="attachment">
            <div class="subject">${escapeHtml(item.filename)}</div>
            <div class="meta">${escapeHtml(item.content_type)} | ${fileSize(item.size_bytes)}</div>
            <div class="meta">${escapeHtml(item.relative_path || "")}</div>
            <div><a class="button secondary" target="_blank" href="${escapeHtml(item.url)}">Otevřít přílohu</a></div>
          </div>
        `).join("") : '<div class="empty">Žádná fyzicky stažená příloha nenalezena.</div>'}
        <h2>Metadata příloh z e-mailu</h2>
        ${attachments.length ? attachments.map((item) => `
          <div class="attachment">
            <div class="subject">${escapeHtml(item.filename || "(bez názvu)")}</div>
            <div class="meta">${escapeHtml(item.content_type || "")} | ${fileSize(item.size_bytes)} | saved=${item.saved ? "ano" : "ne"}</div>
          </div>
        `).join("") : '<div class="empty">Bez metadat příloh.</div>'}
        <div class="note">Bezpečnost: stránka čte jen lokální archiv. Nevolá e-mailový provider, neotevírá externí odkazy a nic nemaže ani neposílá.</div>
      `;
    }

    async function loadList() {
      statusNode.textContent = "Načítám...";
      try {
        const params = new URLSearchParams({q: searchInput.value || "", limit: "160"});
        const res = await fetch(`/api/email-archive/list?${params.toString()}`);
        const data = await res.json();
        statusNode.textContent = data.message || "";
        renderList(data.items || []);
      } catch (err) {
        statusNode.textContent = `Chyba načtení archivu: ${err}`;
      }
    }

    async function loadDetail(archiveId) {
      selectedArchiveId = archiveId;
      detailPane.innerHTML = '<div class="empty">Načítám detail...</div>';
      try {
        const params = new URLSearchParams({archive_id: archiveId});
        const res = await fetch(`/api/email-archive/detail?${params.toString()}`);
        const data = await res.json();
        renderDetail(data);
        await loadList();
      } catch (err) {
        detailPane.innerHTML = `<div class="empty">Chyba načtení: ${escapeHtml(err)}</div>`;
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

    searchBtn.addEventListener("click", loadList);
    refreshBtn.addEventListener("click", loadList);
    returnBtn.addEventListener("click", returnToCockpit);
    searchInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") loadList();
    });
    loadList();
