    const overviewStatus = document.getElementById("overviewStatus");
    const overview = document.getElementById("overview");
    const sourcePath = document.getElementById("sourcePath");
    const updatedAt = document.getElementById("updatedAt");
    const refreshBtn = document.getElementById("refreshBtn");
    const loadHeadersBtn = document.getElementById("loadHeadersBtn");
    const loadPendingBtn = document.getElementById("loadPendingBtn");
    const emailDaysInput = document.getElementById("emailDaysInput");
    const headersBusy = document.getElementById("headersBusy");
    const headersBusyText = document.getElementById("headersBusyText");
    const newHeadersStatus = document.getElementById("newHeadersStatus");
    const processEmailsBtn = document.getElementById("processEmailsBtn");
    const processEmailsStatus = document.getElementById("processEmailsStatus");
    const cockpitBtn = document.getElementById("cockpitBtn");
    let headersBusyTimer = null;
    let emailItems = [];
    let overviewSince = "";
    let recoveredPermanentDeleteItems = [];
    let unrecoverablePurgeCount = 0;

    function categoryTitle(raw) {
      return raw.replace(/^#+\s*/, "").trim();
    }

    function splitOverview(text) {
      const allowed = new Set([
        "Faktury / e-shopy",
        "Pojisteni / smlouvy",
        "Pojištění / smlouvy",
        "Urady / dane",
        "Úřady / daně",
        "Ostatni kandidati",
        "Ostatní kandidáti",
        "Doporučeny dalsi krok po navazani",
        "Doporučený další krok po navázání"
      ]);
      const sections = [];
      let current = null;
      text.split(/\r?\n/).forEach((line) => {
        if (line.startsWith("## ")) {
          const title = categoryTitle(line);
          if (allowed.has(title)) {
            current = {title, lines: []};
            sections.push(current);
          } else {
            current = null;
          }
          return;
        }
        if (current) current.lines.push(line);
      });
      return sections.map((section) => ({
        title: section.title,
        text: section.lines.join("\n").trim()
      })).filter((section) => section.text);
    }

    function renderSections(sections) {
      overview.innerHTML = "";
      if (!sections.length) {
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = "Uložený přehled neobsahuje rozpoznatelné kategorie.";
        overview.appendChild(empty);
        return;
      }
      sections.forEach((section) => {
        const card = document.createElement("div");
        card.className = "category";
        const title = document.createElement("h3");
        title.textContent = section.title;
        const pre = document.createElement("pre");
        pre.textContent = section.text;
        card.appendChild(title);
        card.appendChild(pre);
        overview.appendChild(card);
      });
    }

    function actionLabel(action) {
      if (action === "process") return "Zpracovat";
      if (action === "ignore") return "Ignorovat";
      if (action === "trash_requested") return "Koš - čeká na potvrzení";
      return "";
    }

    function decisionCounts(items) {
      const counts = {total: 0, decided: 0, process: 0, ignore: 0, trash: 0};
      (items || []).forEach((item) => {
        counts.total += 1;
        if (item.action) counts.decided += 1;
        if (item.action === "process") counts.process += 1;
        if (item.action === "ignore") counts.ignore += 1;
        if (item.action === "trash_requested") counts.trash += 1;
      });
      return counts;
    }

    function updateWorkQueueState() {
      const counts = decisionCounts(emailItems);
      updateRefreshButtonState();
      const actionable = counts.process + counts.trash;
      if (!counts.total) {
        if (recoveredPermanentDeleteItems.length) {
          processEmailsBtn.disabled = false;
          processEmailsBtn.textContent = `Otevřít koš (${recoveredPermanentDeleteItems.length})`;
          processEmailsStatus.textContent = "Obnovené položky v koši čekají na samostatné přesné potvrzení trvalého smazání.";
        } else {
          processEmailsBtn.disabled = true;
          processEmailsBtn.textContent = "Zpracovat e-maily";
          processEmailsStatus.textContent = unrecoverablePurgeCount
            ? `Starší košové záznamy bez bezpečné obnovovací identity: ${unrecoverablePurgeCount}. Nebudou automaticky mazány.`
            : "Zatím není načtený žádný e-mailový seznam.";
        }
        return;
      }
      if (counts.decided < counts.total) {
        processEmailsBtn.disabled = true;
        processEmailsBtn.textContent = "Zpracovat e-maily";
        processEmailsStatus.textContent = `Rozhodnuto ${counts.decided}/${counts.total}. Zbývá označit ${counts.total - counts.decided}.`;
        return;
      }
      processEmailsBtn.disabled = false;
      processEmailsStatus.textContent = `Připraveno: zpracovat ${counts.process}, koš ${counts.trash}, ignorovat ${counts.ignore}.`;
      processEmailsBtn.textContent = actionable ? `Zpracovat e-maily (${actionable})` : "Zpracovat e-maily";
    }

    function itemMeta(item) {
      const parts = [];
      if (item.provider) parts.push(item.provider);
      if (item.folder) parts.push(item.folder);
      if (item.uid) parts.push(`UID ${item.uid}`);
      if (item.sender) parts.push(item.sender);
      if (item.date) parts.push(item.date);
      if (item.category) parts.push(item.category);
      return parts.join(" | ");
    }

    function categoryTitleForKey(key) {
      if (key === "faktury/e-shopy") return "Faktury / e-shopy";
      if (key === "pojištění/smlouvy") return "Pojištění / smlouvy";
      if (key === "úřady/daně") return "Úřady / daně";
      return "Ostatní";
    }

    function itemDateValue(item) {
      const parsed = Date.parse(item.date || "");
      return Number.isFinite(parsed) ? parsed : 0;
    }

    function knownItemIds() {
      const ids = [];
      emailItems.forEach((item) => {
        if (item && item.id) ids.push(item.id);
        if (item && item.legacy_id) ids.push(item.legacy_id);
      });
      return ids;
    }

    function newestItemIso() {
      const latest = Math.max(0, ...emailItems.map(itemDateValue));
      return latest ? new Date(latest).toISOString() : "";
    }

    function updateRefreshButtonState() {
      const canRefresh = Boolean(newestItemIso());
      refreshBtn.disabled = !canRefresh;
      refreshBtn.title = canRefresh
        ? "Doplní jen e-maily novější než nejnovější viditelný e-mail."
        : "Nejdřív použij Načti emaily.";
    }

    function selectedDays() {
      const parsed = Number.parseInt(emailDaysInput.value, 10);
      if (!Number.isFinite(parsed)) return 7;
      return Math.min(14, Math.max(1, parsed));
    }

    function updateDoneButton(button, flagged) {
      button.classList.toggle("active", Boolean(flagged));
      button.textContent = flagged ? "★ Hotovo" : "☆ Hotovo";
      button.setAttribute("aria-pressed", flagged ? "true" : "false");
    }

    async function setDoneFlag(item, button, statusNode, dialogWindow = window) {
      if (!item || String(item.provider || "").toLowerCase() !== "seznam" || !item.uid) return;
      const nextDone = !Boolean(item.imap_flagged);
      const prompt = nextDone
        ? "Označit tento e-mail na Seznamu příznakem Hotovo? Ve schránce se zobrazí jako hvězdička nebo příznak."
        : "Zrušit u tohoto e-mailu na Seznamu příznak Hotovo?";
      if (!dialogWindow.confirm(prompt)) return;
      button.disabled = true;
      statusNode.textContent = nextDone ? "Nastavuji příznak Hotovo..." : "Ruším příznak Hotovo...";
      try {
        const res = await fetch("/api/email-processing/done-flag", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            provider: item.provider,
            folder: item.folder || "INBOX",
            uid: item.uid,
            done: nextDone
          })
        });
        const data = await res.json();
        if (!data.ok) {
          statusNode.textContent = data.message || "Příznak Hotovo se nepodařilo změnit.";
          return;
        }
        item.imap_flagged = Boolean(data.flagged);
        updateDoneButton(button, item.imap_flagged);
        statusNode.textContent = data.message || "Příznak Hotovo byl změněn.";
      } catch (err) {
        statusNode.textContent = "Chyba změny příznaku Hotovo: " + err;
      } finally {
        button.disabled = false;
      }
    }

    function normalizeDaysInput() {
      emailDaysInput.value = String(selectedDays());
    }

    function mergeItems(existing, incoming) {
      const byId = new Map();
      (existing || []).forEach((item) => {
        if (item && item.id) byId.set(item.id, item);
      });
      (incoming || []).forEach((item) => {
        if (!item || !item.id || byId.has(item.id)) return;
        if (item.legacy_id && byId.has(item.legacy_id)) return;
        byId.set(item.id, item);
        if (item.legacy_id) byId.set(item.legacy_id, item);
      });
      return Array.from(new Set(byId.values())).sort((a, b) => itemDateValue(b) - itemDateValue(a));
    }

    function createEmailCard(item) {
      const card = document.createElement("div");
      card.className = item.is_new_header ? "email-card new-header" : "email-card";
      card.dataset.itemId = item.id || "";
      const head = document.createElement("div");
      head.className = "email-head";
      const summary = document.createElement("div");
      const title = document.createElement("div");
      title.className = "email-title";
      title.textContent = item.subject || "(bez předmětu)";
      const meta = document.createElement("div");
      meta.className = "email-meta";
      meta.textContent = itemMeta(item);
      const decision = document.createElement("div");
      decision.className = "decision";
      decision.textContent = item.is_new_header ? "nově načteno" : actionLabel(item.action || "");
      summary.appendChild(title);
      summary.appendChild(meta);
      if (item.reason) {
        const reason = document.createElement("div");
        reason.className = "email-reason";
        reason.textContent = `Důvod: ${item.reason}`;
        summary.appendChild(reason);
      }
      head.appendChild(summary);
      head.appendChild(decision);

      const actions = document.createElement("div");
      actions.className = "email-actions";
      if (String(item.provider || "").toLowerCase() === "seznam") {
        const done = document.createElement("button");
        done.className = "done-button";
        done.type = "button";
        updateDoneButton(done, item.imap_flagged);
        done.addEventListener("click", () => setDoneFlag(item, done, overviewStatus));
        actions.appendChild(done);
      }
      [
        ["process", "Zpracovat"],
        ["ignore", "Ignorovat"]
      ].forEach(([value, labelText]) => {
        const label = document.createElement("label");
        const input = document.createElement("input");
        input.type = "checkbox";
        input.checked = item.action === value;
        input.addEventListener("change", () => {
          const nextAction = input.checked ? value : "";
          actions.querySelectorAll('input[type="checkbox"]').forEach((other) => {
            if (other !== input) other.checked = false;
          });
          item.is_new_header = false;
          card.classList.remove("new-header");
          saveDecision(item, nextAction, decision);
        });
        label.appendChild(input);
        label.appendChild(document.createTextNode(labelText));
        actions.appendChild(label);
      });

      const trash = document.createElement("button");
      trash.className = "trash-button";
      trash.type = "button";
      trash.textContent = "Koš";
      trash.addEventListener("click", () => {
        const ok = window.confirm("Označit tento e-mail ke smazání?\n\nE-mail se teď fyzicky nemaže, jen se uloží pracovní rozhodnutí.");
        if (!ok) return;
        actions.querySelectorAll('input[type="checkbox"]').forEach((input) => {
          input.checked = false;
        });
        item.is_new_header = false;
        card.classList.remove("new-header");
        saveDecision(item, "trash_requested", decision);
      });
      actions.appendChild(trash);
      card.appendChild(head);
      card.appendChild(actions);
      return card;
    }

    function renderItems(items) {
      overview.innerHTML = "";
      if (!items || !items.length) {
        if (!window.lastOverviewText) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = "Pracovní seznam je prázdný. Zadej rozsah 1-14 dní a klikni Načti emaily.";
          overview.appendChild(empty);
          return;
        }
        renderSections(splitOverview(window.lastOverviewText || ""));
        return;
      }
      const order = ["faktury/e-shopy", "pojištění/smlouvy", "úřady/daně", "ostatní"];
      const grouped = new Map(order.map((key) => [key, []]));
      items.forEach((item) => {
        const key = order.includes(item.category) ? item.category : "ostatní";
        grouped.get(key).push(item);
      });
      order.forEach((key) => {
        const groupItems = grouped.get(key);
        const section = document.createElement("div");
        section.className = "category";
        const title = document.createElement("h3");
        title.textContent = `${categoryTitleForKey(key)} (${groupItems.length})`;
        const body = document.createElement("div");
        body.className = "category-items";
        if (groupItems.length) {
          groupItems.forEach((item) => body.appendChild(createEmailCard(item)));
        } else {
          const empty = document.createElement("div");
          empty.className = "status-line";
          empty.textContent = "Žádné položky.";
          body.appendChild(empty);
        }
        section.appendChild(title);
        section.appendChild(body);
        overview.appendChild(section);
      });
    }

    async function saveDecision(item, action, decisionNode) {
      if (!item || !item.id) return;
      decisionNode.textContent = "Ukládám...";
      try {
        const operationId = (window.crypto && typeof window.crypto.randomUUID === "function")
          ? window.crypto.randomUUID()
          : "email-decision-" + Date.now() + "-" + Math.random().toString(16).slice(2);
        const res = await fetch("/api/email-processing/decision", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({item_id: item.id, action, item, operation_id: operationId})
        });
        const data = await res.json();
        if (!data.ok) {
          decisionNode.textContent = data.message || "Uložení selhalo";
          return;
        }
        item.action = action;
        decisionNode.textContent = actionLabel(action);
        overviewStatus.textContent = data.message || "Rozhodnutí uloženo.";
        updateWorkQueueState();
      } catch (err) {
        decisionNode.textContent = `Chyba: ${err}`;
      }
    }

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function initializeWorkQueueWindow(queue, queueItems, initialPermanentDeleteItems = []) {
      const queueDoc = queue.document;
      const queueList = queueDoc.getElementById("queueList");
      const detailPane = queueDoc.getElementById("detailPane");
      const queueStatus = queueDoc.getElementById("queueStatus");
      const queueProcessCount = queueDoc.getElementById("queueProcessCount");
      const queueTrashCount = queueDoc.getElementById("queueTrashCount");
      const queuePurgeCount = queueDoc.getElementById("queuePurgeCount");
      const queueVisibleCount = queueDoc.getElementById("queueVisibleCount");
      const batchFilters = queueDoc.getElementById("batchFilters");
      const batchBtn = queueDoc.getElementById("batchBtn");
      const trashBatchBtn = queueDoc.getElementById("trashBatchBtn");
      const purgeTrashBtn = queueDoc.getElementById("purgeTrashBtn");
      const backToEmailsBtn = queueDoc.getElementById("backToEmailsBtn");
      const backToCockpitBtn = queueDoc.getElementById("backToCockpitBtn");
      let selectedId = queueItems.length ? queueItems[0].id : "";
      let activeBatchFilter = "all";
      let permanentDeleteItems = initialPermanentDeleteItems.map((item) => ({...item}));
      let recentImportedAttachments = [];

      function decisionLabel(item) {
        if (item.detailLoading) return "načítám detail...";
        if (item.detailLoaded) return item.queueDecision ? decisionLabel({...item, detailLoaded: false}) : "detail načten";
        if (item.queueDecision === "save") return "uložit";
        if (item.queueDecision === "skip") return "neukládat";
        if (item.queueDecision === "trash_requested") return "koš připraven";
        return "čeká na rozhodnutí";
      }

      function itemBatchGroups(item) {
        const groups = Array.isArray(item.batch_groups) ? item.batch_groups : [];
        return groups
          .map((group) => ({id: String(group.id || ""), label: String(group.label || group.id || "")}))
          .filter((group) => group.id);
      }

      function itemMatchesBatchFilter(item) {
        if (activeBatchFilter === "all") return true;
        return itemBatchGroups(item).some((group) => group.id === activeBatchFilter);
      }

      function visibleQueueItems() {
        return queueItems.filter((item) => itemMatchesBatchFilter(item));
      }

      function activeBatchLabel() {
        if (activeBatchFilter === "all") return "Vše";
        for (const item of queueItems) {
          const found = itemBatchGroups(item).find((group) => group.id === activeBatchFilter);
          if (found) return found.label;
        }
        return activeBatchFilter;
      }

      function ensureSelectedVisible() {
        const visible = visibleQueueItems();
        if (!visible.length) {
          selectedId = "";
          return null;
        }
        if (!visible.some((item) => item.id === selectedId)) selectedId = visible[0].id;
        return visible.find((item) => item.id === selectedId) || visible[0];
      }

      function currentItem() {
        return ensureSelectedVisible();
      }

      function renderBatchFilters() {
        const groupMap = new Map();
        groupMap.set("all", {id: "all", label: "Vše", count: queueItems.length});
        queueItems.forEach((item) => {
          itemBatchGroups(item).forEach((group) => {
            const current = groupMap.get(group.id) || {id: group.id, label: group.label, count: 0};
            current.count += 1;
            groupMap.set(group.id, current);
          });
        });
        const priority = ["all", "tax_office", "vak", "invoice_over_2000", "invoice", "pdf", "large_pdf", "other"];
        const groups = Array.from(groupMap.values()).sort((left, right) => {
          const leftRank = priority.includes(left.id) ? priority.indexOf(left.id) : 99;
          const rightRank = priority.includes(right.id) ? priority.indexOf(right.id) : 99;
          if (leftRank !== rightRank) return leftRank - rightRank;
          return left.label.localeCompare(right.label, "cs");
        });
        if (!groups.some((group) => group.id === activeBatchFilter)) activeBatchFilter = "all";
        batchFilters.innerHTML = groups.map((group) => {
          const active = group.id === activeBatchFilter ? " active" : "";
          return '<button type="button" class="filter-chip' + active + '" data-filter="' + escapeHtml(group.id) + '">' +
            escapeHtml(group.label) + ' <span>' + escapeHtml(String(group.count)) + '</span></button>';
        }).join("");
        batchFilters.querySelectorAll(".filter-chip").forEach((button) => {
          button.addEventListener("click", () => {
            activeBatchFilter = button.dataset.filter || "all";
            selectedId = "";
            renderQueueList();
            const item = currentItem();
            if (item) renderDetail(item);
            else detailPane.innerHTML = '<div class="empty">V tomto bloku není žádný e-mail.</div>';
          });
        });
      }

      function updateSummaryCounts() {
        const visible = visibleQueueItems();
        const workItems = visible.filter((item) => item.queueDecision !== "trash_requested");
        const trashItems = visible.filter((item) => item.queueDecision === "trash_requested");
        if (queueProcessCount) queueProcessCount.textContent = String(workItems.length);
        if (queueTrashCount) queueTrashCount.textContent = String(trashItems.length);
        if (queuePurgeCount) queuePurgeCount.textContent = String(permanentDeleteItems.length);
        if (queueVisibleCount) queueVisibleCount.textContent = `${visible.length}/${queueItems.length}`;
      }

      function updateBatchState() {
        const visible = visibleQueueItems();
        const decided = visible.filter((item) => Boolean(item.queueDecision)).length;
        const workItems = visible.filter((item) => item.queueDecision !== "trash_requested");
        const workReady = workItems.filter((item) => Boolean(item.queueDecision)).length;
        const trashItems = visible.filter((item) => item.queueDecision === "trash_requested");
        updateSummaryCounts();
        batchBtn.disabled = !workItems.length || workReady < workItems.length;
        trashBatchBtn.disabled = !trashItems.length;
        purgeTrashBtn.disabled = !permanentDeleteItems.length;
        queueStatus.textContent = visible.length
          ? `Blok: ${activeBatchLabel()}. Rozhodnuto ${decided}/${visible.length}. Koš: ${trashItems.length}. Dávkové akce platí jen pro aktuální blok.`
          : "Fronta je prázdná.";
      }

      function renderQueueList() {
        renderBatchFilters();
        const visible = visibleQueueItems();
        ensureSelectedVisible();
        if (!queueItems.length || !visible.length) {
          queueList.innerHTML = !queueItems.length
            ? '<div class="empty">Fronta je prázdná.</div>'
            : '<div class="empty">V tomto bloku není žádný e-mail.</div>';
          detailPane.innerHTML = '<div class="empty">Žádný e-mail ke zpracování v aktuálním bloku.</div>';
          batchBtn.disabled = true;
          trashBatchBtn.disabled = true;
          purgeTrashBtn.disabled = !permanentDeleteItems.length;
          updateSummaryCounts();
          return;
        }
        queueList.innerHTML = visible.map((item) => {
          const active = item.id === selectedId ? " active" : "";
          const done = item.queueDecision || item.detailLoaded ? " done" : "";
          const loading = item.detailLoading ? " loading" : "";
          const groups = itemBatchGroups(item).map((group) => group.label).slice(0, 3).join(" | ");
          const amount = item.amount_scan && item.amount_scan.max_amount_czk
            ? " | max " + Math.round(Number(item.amount_scan.max_amount_czk)).toLocaleString("cs-CZ") + " Kč"
            : "";
          return '<button type="button" class="item' + active + '" data-id="' + escapeHtml(item.id) + '">' +
            '<span class="subject">' + escapeHtml(item.subject || "(bez předmětu)") + '</span>' +
            '<span class="meta">' + escapeHtml(itemMeta(item)) + '</span>' +
            (groups ? '<span class="meta">' + escapeHtml(groups + amount) + '</span>' : "") +
            (item.reason ? '<span class="reason">Důvod: ' + escapeHtml(item.reason) + '</span>' : "") +
            '<span class="status' + done + loading + '">' + escapeHtml(decisionLabel(item)) + '</span>' +
            '</button>';
        }).join("");
        queueList.querySelectorAll(".item").forEach((button) => {
          button.addEventListener("click", () => selectItem(button.dataset.id || ""));
        });
        updateBatchState();
      }

      function renderAttachmentRows(item, attachments) {
        if (!attachments.length) return '<div class="empty">Bez příloh.</div>';
        return attachments.map((attachment, index) => {
          const partId = attachment.part_id || String(index);
          const filename = attachment.filename || "";
          const contentType = (attachment.content_type || "").toLowerCase();
          const lowerFilename = filename.toLowerCase();
          const canSaveToVault = contentType === "application/pdf" ||
            contentType.startsWith("image/") ||
            lowerFilename.endsWith(".pdf") ||
            lowerFilename.endsWith(".png") ||
            lowerFilename.endsWith(".jpg") ||
            lowerFilename.endsWith(".jpeg") ||
            lowerFilename.endsWith(".gif") ||
            lowerFilename.endsWith(".webp") ||
            lowerFilename.endsWith(".tif") ||
            lowerFilename.endsWith(".tiff");
          const checked = canSaveToVault && (item.saveAttachments || []).includes(partId) ? " checked" : "";
          const size = attachment.size_bytes === null || attachment.size_bytes === undefined
            ? "velikost neznámá"
            : Math.round(Number(attachment.size_bytes) / 1024) + " kB";
          const saveControl = canSaveToVault
            ? '<label><input type="checkbox" class="attachment-save" data-part-id="' + escapeHtml(partId) + '"' + checked + '> Uložit</label>'
            : '<span class="meta">Jen náhled</span>';
          return '<div class="attachment-row" data-part-id="' + escapeHtml(partId) + '">' +
            '<div><strong>' + escapeHtml(filename || "(bez názvu)") + '</strong></div>' +
            '<div class="meta">' + escapeHtml(attachment.content_type || "") + " | " + escapeHtml(size) + '</div>' +
            '<div class="attachment-tools">' +
            saveControl +
            '<button type="button" class="secondary attachment-preview" data-part-id="' + escapeHtml(partId) + '" data-filename="' + escapeHtml(filename) + '">Náhled</button>' +
            '<button type="button" class="secondary attachment-toggle">Metadata</button>' +
            '</div>' +
            '<div class="meta hidden attachment-detail">part_id: ' + escapeHtml(partId) + '<br>dispozice: ' + escapeHtml(attachment.disposition || "") + '<br>Náhled otevře dočasnou kopii PDF nebo obrázku; trvalé uložení podporované PDF/obrázkové přílohy do vaultu proběhne až po zaškrtnutí Uložit a zpracování dávky.</div>' +
            '</div>';
        }).join("");
      }

      function renderRecentImportedAttachments() {
        if (!recentImportedAttachments.length) return "";
        return '<div><strong>Právě uložené přílohy</strong></div>' +
          '<div class="attachments">' +
          recentImportedAttachments.map((attachment) => {
            const documentId = attachment.document_ref || attachment.document_id || "";
            return '<div class="attachment-row">' +
              '<div><strong>' + escapeHtml(attachment.filename || "uložená příloha") + '</strong></div>' +
              '<div class="meta">Dokument: ' + escapeHtml(documentId) + '</div>' +
              '<div class="attachment-tools">' +
              '<button type="button" class="primary attachment-open" data-document-id="' + escapeHtml(documentId) + '">Otevřít uložené PDF</button>' +
              '</div>' +
              '</div>';
          }).join("") +
          '</div>';
      }

      function bindAttachmentOpenButtons() {
        detailPane.querySelectorAll(".attachment-open").forEach((button) => {
          button.addEventListener("click", () => {
            const documentId = button.dataset.documentId || "";
            if (!documentId) return;
            const url = "/documents/read?document_id=" + encodeURIComponent(documentId);
            button.disabled = true;
            queueStatus.textContent = "Otevírám uložené PDF ve čtecím okně Cockpitu.";
            try {
              const reader = window.open(url, "samanthaDocumentReader", "width=1180,height=860");
              if (reader) {
                reader.focus();
              } else {
                window.location.href = url;
              }
            } catch (err) {
              queueStatus.textContent = "Chyba otevření PDF: " + err;
            } finally {
              button.disabled = false;
            }
          });
        });
      }

      function bindAttachmentPreviewButtons(item) {
        detailPane.querySelectorAll(".attachment-preview").forEach((button) => {
          button.addEventListener("click", async () => {
            const partId = button.dataset.partId || "";
            const filename = button.dataset.filename || "";
            if (!partId) return;
            button.disabled = true;
            queueStatus.textContent = "Otevírám dočasný náhled PDF přílohy. Příloha se neukládá do vaultu.";
            try {
              const res = await fetch("/api/email-processing/preview-attachment", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                  provider: item.provider,
                  folder: item.folder || "INBOX",
                  uid: item.uid,
                  part_id: partId,
                  filename: filename
                })
              });
              const data = await res.json();
              queueStatus.textContent = data.message || (data.ok ? "Náhled otevřen." : "Náhled se nepodařilo otevřít.");
            } catch (err) {
              queueStatus.textContent = "Chyba náhledu přílohy: " + err;
            } finally {
              button.disabled = false;
            }
          });
        });
      }

      function collectImportedAttachments(results, items) {
        const itemById = new Map((items || []).map((item) => [item.id, item]));
        const imported = [];
        (results || []).forEach((result) => {
          const sourceItem = itemById.get(result.item_id) || {};
          (result.attachments || []).forEach((attachment) => {
            if (!attachment || !attachment.ok || !(attachment.document_ref || attachment.document_id)) return;
            imported.push({
              ...attachment,
              subject: sourceItem.subject || ""
            });
          });
        });
        return imported;
      }

      function setQueueDecision(item, decision) {
        item.queueDecision = decision;
        if (decision === "skip") item.saveAttachments = [];
        renderQueueList();
        renderDetail(item);
      }

      function renderLoadingDetail(item) {
        detailPane.innerHTML =
          '<div class="detail-head">' +
            '<div>' +
              '<div class="subject">' + escapeHtml(item.subject || "(bez předmětu)") + '</div>' +
              '<div class="meta">' + escapeHtml(itemMeta(item)) + '</div>' +
            '</div>' +
            '<div class="status loading">načítám detail</div>' +
          '</div>' +
          '<div class="loading-box"><span class="mini-spinner" aria-hidden="true"></span><span>Načítám celý e-mail read-only. U zpráv s PDF přílohami to může chvíli trvat.</span></div>';
      }

      function renderDetail(item) {
        const detail = item.detail || {};
        const attachments = detail.attachments || [];
        detailPane.innerHTML =
          '<div class="detail-head">' +
            '<div>' +
              '<div class="subject">' + escapeHtml(detail.subject || item.subject || "(bez předmětu)") + '</div>' +
              '<div class="meta">' + escapeHtml((detail.sender ? detail.sender + " | " : "") + itemMeta(item)) + '</div>' +
            '</div>' +
            '<div class="status' + (item.queueDecision ? " done" : "") + '">' + escapeHtml(decisionLabel(item)) + '</div>' +
          '</div>' +
          '<div class="detail-actions">' +
            (String(item.provider || "").toLowerCase() === "seznam"
              ? '<button type="button" class="done-button' + (item.imap_flagged ? " active" : "") + '" id="doneEmail" aria-pressed="' + (item.imap_flagged ? "true" : "false") + '">' + (item.imap_flagged ? "★ Hotovo" : "☆ Hotovo") + '</button>'
              : "") +
            '<label><input type="checkbox" id="saveEmail"' + (item.queueDecision === "save" ? " checked" : "") + '> Uložit e-mail</label>' +
            '<label><input type="checkbox" id="skipEmail"' + (item.queueDecision === "skip" ? " checked" : "") + '> Neukládat</label>' +
            '<button type="button" class="danger" id="trashEmail">Koš</button>' +
          '</div>' +
          '<div><strong>Tělo e-mailu</strong></div>' +
          '<pre>' + escapeHtml(detail.body_text || "") + (detail.truncated ? "\n\n[Text je zkrácený.]" : "") + '</pre>' +
          '<div><strong>Přílohy</strong></div>' +
          '<div class="attachments">' + renderAttachmentRows(item, attachments) + '</div>' +
          renderRecentImportedAttachments();

        bindAttachmentOpenButtons();
        bindAttachmentPreviewButtons(item);
        const doneEmailButton = queueDoc.getElementById("doneEmail");
        if (doneEmailButton) {
          doneEmailButton.addEventListener("click", () => setDoneFlag(item, doneEmailButton, queueStatus, queue));
        }
        queueDoc.getElementById("saveEmail").addEventListener("change", (event) => {
          setQueueDecision(item, event.target.checked ? "save" : "");
        });
        queueDoc.getElementById("skipEmail").addEventListener("change", (event) => {
          setQueueDecision(item, event.target.checked ? "skip" : "");
        });
        queueDoc.getElementById("trashEmail").addEventListener("click", () => {
          const ok = queue.confirm("Opravdu označit e-mail ke smazání?\n\nSkutečné smazání bude samostatná potvrzená akce v dalším kroku.");
          if (!ok) return;
          setQueueDecision(item, "trash_requested");
        });
        detailPane.querySelectorAll(".attachment-save").forEach((input) => {
          input.addEventListener("change", () => {
            const partId = input.dataset.partId || "";
            const current = new Set(item.saveAttachments || []);
            if (input.checked) current.add(partId);
            else current.delete(partId);
            item.saveAttachments = Array.from(current);
            if (item.saveAttachments.length && item.queueDecision !== "save") item.queueDecision = "save";
            renderQueueList();
          });
        });
        detailPane.querySelectorAll(".attachment-toggle").forEach((button) => {
          button.addEventListener("click", () => {
            const detailNode = button.closest(".attachment-row").querySelector(".attachment-detail");
            detailNode.classList.toggle("hidden");
            button.textContent = detailNode.classList.contains("hidden") ? "Metadata" : "Zavřít";
          });
        });
      }

      async function selectItem(itemId) {
        selectedId = itemId;
        const item = currentItem();
        renderQueueList();
        if (!item) return;
        if (item.detailLoaded) {
          queueStatus.textContent = "Detail načten z cache v tomto okně. IMAP se znovu nevolal.";
          renderDetail(item);
          return;
        }
        if (item.detailLoading) {
          renderLoadingDetail(item);
          return;
        }
        item.detailLoading = true;
        renderQueueList();
        renderLoadingDetail(item);
        queueStatus.textContent = "Načítám celý e-mail read-only. U větších zpráv s PDF to může chvíli trvat.";
        try {
          const res = await fetch("/api/email-processing/read-message", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              provider: item.provider,
              folder: item.folder || "INBOX",
              uid: item.uid,
              max_chars: 12000
            })
          });
          const data = await res.json();
          if (!data.ok) {
            detailPane.innerHTML = '<div class="empty">' + escapeHtml(data.message || "E-mail se nepodařilo načíst.") + '</div>';
            return;
          }
          item.detail = data.email || {};
          item.detailLoaded = true;
          queueStatus.textContent = "Detail načten. Další kliknutí na stejný e-mail použije cache v tomto okně.";
          renderDetail(item);
        } catch (err) {
          detailPane.innerHTML = '<div class="empty">Chyba načtení: ' + escapeHtml(err) + '</div>';
        } finally {
          item.detailLoading = false;
          renderQueueList();
        }
      }

      batchBtn.addEventListener("click", async () => {
        const workItems = visibleQueueItems().filter((item) => item.queueDecision !== "trash_requested");
        if (!workItems.length) {
          queueStatus.textContent = "V této frontě jsou jen kandidáti ke koši. Použij tlačítko Emaily určené ke smazání smazat.";
          return;
        }
        const ok = queue.confirm(`Zpracovat aktuální blok "${activeBatchLabel()}" (${workItems.length} položek)?\n\nUložené e-maily půjdou do EmailArchiveVault. Vybrané PDF přílohy půjdou do private document vaultu a fulltextového indexu.`);
        if (!ok) return;
        batchBtn.disabled = true;
        queueStatus.textContent = "Zpracovávám dávku. U větších PDF to může chvíli trvat.";
        try {
          const res = await fetch("/api/email-processing/process-batch", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: workItems,
              trash_confirmation_text: ""
            })
          });
          const data = await res.json();
          if (!data.ok) {
            queueStatus.textContent = data.message || "Zpracování dávky skončilo s chybou.";
          } else {
            queueStatus.textContent = data.message || "Dávka zpracována.";
          }
          const importedNow = collectImportedAttachments(data.items || [], workItems);
          if (importedNow.length) {
            recentImportedAttachments = importedNow.concat(recentImportedAttachments).slice(0, 20);
            queueStatus.textContent += " Uložené PDF přílohy můžeš otevřít v detailu.";
          }
          const remaining = [];
          const byId = new Map((data.items || []).map((result) => [result.item_id, result]));
          queueItems.forEach((item) => {
            const result = byId.get(item.id);
            item.batchResult = result || {};
            if (!result || !result.ok || result.status === "trash_pending" || item.queueDecision === "trash_requested") remaining.push(item);
          });
          queueItems.splice(0, queueItems.length, ...remaining);
          selectedId = queueItems.length ? queueItems[0].id : "";
          renderQueueList();
          if (selectedId) renderDetail(currentItem());
          else {
            detailPane.innerHTML = '<div class="empty">Dávka je hotová.</div>' + renderRecentImportedAttachments();
            bindAttachmentOpenButtons();
          }
        } catch (err) {
          queueStatus.textContent = "Chyba zpracování dávky: " + err;
        } finally {
          updateBatchState();
        }
      });

      trashBatchBtn.addEventListener("click", async () => {
        const trashItems = visibleQueueItems().filter((item) => item.queueDecision === "trash_requested");
        if (!trashItems.length) {
          queueStatus.textContent = "Žádné e-maily nejsou označené ke smazání.";
          return;
        }
        const noun = trashItems.length === 1
          ? "e-mail označený"
          : (trashItems.length >= 2 && trashItems.length <= 4 ? "e-maily označené" : "e-mailů označených");
        const required = "Potvrzuji, přesuň " + trashItems.length + " " + noun + " ke smazání do koše.";
        const ok = queue.confirm(
          "Přesunout do koše " + trashItems.length + " e-mailů označených ke smazání?\n\n" +
          "Nepoužívá se EXPUNGE; zprávy se jen přesunou do koše provideru."
        );
        if (!ok) return;
        trashBatchBtn.disabled = true;
        queueStatus.textContent = "Přesouvám označené e-maily do koše.";
        try {
          const res = await fetch("/api/email-processing/process-batch", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: trashItems,
              trash_confirmation_text: required
            })
          });
          const data = await res.json();
          queueStatus.textContent = data.message || (data.ok ? "Koš zpracován." : "Koš skončil s chybou.");
          const byId = new Map((data.items || []).map((result) => [result.item_id, result]));
          const remaining = [];
          queueItems.forEach((item) => {
            const result = byId.get(item.id);
            item.batchResult = result || {};
            if (result && result.ok && result.status === "trashed") {
              permanentDeleteItems.push({
                id: item.id,
                item_id: item.id,
                provider: item.provider,
                folder: item.folder || "INBOX",
                uid: item.uid,
                subject: item.subject || "",
                trash_folder: result.trash_folder || "",
                trash_uid: result.trash_uid || "",
                message_id: result.message_id || ""
              });
              recoveredPermanentDeleteItems = permanentDeleteItems.map((candidate) => ({...candidate}));
            }
            if (!result || !result.ok || result.status === "trash_pending") remaining.push(item);
          });
          queueItems.splice(0, queueItems.length, ...remaining);
          selectedId = queueItems.length ? queueItems[0].id : "";
          renderQueueList();
          if (selectedId) renderDetail(currentItem());
          else detailPane.innerHTML = '<div class="empty">Koš je hotový.</div>';
        } catch (err) {
          queueStatus.textContent = "Chyba přesunu do koše: " + err;
        } finally {
          updateBatchState();
        }
      });

      purgeTrashBtn.addEventListener("click", async () => {
        if (!permanentDeleteItems.length) {
          queueStatus.textContent = "Žádné e-maily nejsou připravené k trvalému smazání z koše.";
          return;
        }
        const count = permanentDeleteItems.length;
        const ok = queue.confirm(
          "Trvale smazat z koše " + count + " e-mailů?\n\n" +
          "Tato akce je nevratná a použije IMAP EXPUNGE nad zprávami v koši."
        );
        if (!ok) return;
        purgeTrashBtn.disabled = true;
        queueStatus.textContent = "Připravuji přesné potvrzení pro trvalé smazání.";
        try {
          const previewRes = await fetch("/api/email-processing/purge-trash", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: permanentDeleteItems,
              confirmed: false
            })
          });
          const preview = await previewRes.json();
          const required = preview.required_confirmation || "";
          if (!required) {
            queueStatus.textContent = preview.message || "Backend nevrátil potvrzovací větu pro trvalé smazání.";
            return;
          }
          const typed = queue.prompt(
            "Pro trvalé smazání opiš přesně potvrzovací větu:\n\n" + required,
            ""
          );
          if (typed !== required) {
            queueStatus.textContent = "Trvalé smazání z koše nebylo potvrzeno přesnou větou.";
            return;
          }
          queueStatus.textContent = "Trvale mažu e-maily z koše.";
          const res = await fetch("/api/email-processing/purge-trash", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              items: permanentDeleteItems,
              confirmed: true,
              confirmation_text: typed
            })
          });
          const data = await res.json();
          queueStatus.textContent = data.message || (data.ok ? "Trvalé smazání dokončeno." : "Trvalé smazání skončilo s chybou.");
          const byId = new Map((data.items || []).map((result) => [result.item_id, result]));
          permanentDeleteItems = permanentDeleteItems.filter((item) => {
            const result = byId.get(item.item_id || item.id);
            item.purgeResult = result || {};
            return !result || !result.ok || result.status !== "purged";
          });
          recoveredPermanentDeleteItems = permanentDeleteItems.map((candidate) => ({...candidate}));
          updateBatchState();
        } catch (err) {
          queueStatus.textContent = "Chyba trvalého smazání z koše: " + err;
          updateBatchState();
        }
      });

      backToEmailsBtn.addEventListener("click", () => {
        const emailWindow = queue.opener;
        if (emailWindow && !emailWindow.closed) {
          emailWindow.focus();
          queue.close();
          return;
        }
        queue.location.href = "/email-processing/";
      });

      backToCockpitBtn.addEventListener("click", () => {
        const emailWindow = queue.opener;
        const cockpitWindow = emailWindow && !emailWindow.closed ? emailWindow.opener : null;
        if (cockpitWindow && !cockpitWindow.closed) {
          cockpitWindow.focus();
          try {
            emailWindow.close();
          } catch (_err) {
            // The queue can still close and return focus to the known Cockpit window.
          }
          queue.close();
          return;
        }
        queue.location.href = "/";
      });

      renderQueueList();
      if (selectedId) selectItem(selectedId);
    }

    function openWorkQueueWindow() {
      const counts = decisionCounts(emailItems);
      if (!counts.total && !recoveredPermanentDeleteItems.length) {
        window.alert("Není připravený žádný e-mail ani bezpečně obnovená položka v koši.");
        return;
      }
      if (counts.total && counts.decided < counts.total) {
        window.alert("Nejdřív přiřaď status všem viditelným e-mailům.");
        return;
      }
      const toProcess = emailItems.filter((item) => item.action === "process");
      const toTrash = emailItems.filter((item) => item.action === "trash_requested");
      const ignored = emailItems.filter((item) => item.action === "ignore");
      const queue = window.open("", "SamanthaEmailWorkQueue", "popup=yes,width=980,height=760,left=140,top=70");
      if (!queue) {
        window.alert("Popup okno bylo blokováno. Povol v prohlížeči vyskakovací okna pro lokální Cockpit.");
        return;
      }
      const queueItems = [...toProcess, ...toTrash].map((item) => ({
        ...item,
        queueAction: item.action === "trash_requested" ? "trash_requested" : "process",
        queueDecision: item.action === "trash_requested" ? "trash_requested" : "",
        saveAttachments: []
      }));
      queue.document.open();
      queue.document.write(`<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Email Work Queue</title>
  <style>
    :root { --bg: #f5f7fb; --panel: #ffffff; --ink: #162033; --muted: #667085; --line: #d9e0ea; --blue: #1f5fbf; --red: #991b1b; --amber: #9a5b00; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink); font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    header { padding: 16px 20px; background: var(--panel); border-bottom: 1px solid var(--line); }
    h1 { margin: 0; font-size: 20px; }
    button { border: 0; border-radius: 6px; padding: 8px 11px; font: inherit; font-weight: 650; cursor: pointer; white-space: nowrap; }
    button.primary { background: var(--blue); color: white; }
    button.secondary { background: #e8eef8; color: #1d3b74; }
    button.danger { background: #fee2e2; color: var(--red); }
    button.done-button { background: #fff3bf; color: #704800; }
    button.done-button.active { background: #f5c542; color: #3d2900; }
    button:disabled { opacity: 0.45; cursor: not-allowed; }
    main { padding: 18px 20px 28px; display: grid; gap: 14px; }
    .topbar { display: flex; justify-content: space-between; gap: 10px; align-items: center; flex-wrap: wrap; }
    .topbar-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .batch-filters { display: flex; flex-wrap: wrap; gap: 7px; }
    .filter-chip { background: #eef2f7; color: #263244; border: 1px solid #d9e0ea; }
    .filter-chip.active { background: var(--blue); color: white; border-color: var(--blue); }
    .filter-chip span { opacity: 0.78; font-weight: 700; }
    .queue-grid { display: grid; grid-template-columns: 360px minmax(0, 1fr); gap: 14px; align-items: start; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
    h2 { margin: 0; padding: 12px 14px; font-size: 14px; border-bottom: 1px solid var(--line); background: #f8fafc; }
    .body { padding: 13px 14px; display: grid; gap: 9px; }
    .item { border: 1px solid #edf0f4; border-radius: 8px; padding: 10px; background: #fbfcfe; display: grid; gap: 5px; text-align: left; width: 100%; color: inherit; }
    .item.active { border-color: #8eb1ed; background: #f4f8ff; }
    .subject { font-weight: 750; overflow-wrap: anywhere; }
    .meta, .reason, .empty, .note { color: var(--muted); font-size: 13px; overflow-wrap: anywhere; }
    .note strong { color: var(--ink); }
    .status { font-size: 12px; font-weight: 700; color: var(--amber); }
    .status.done { color: #16794c; }
    .status.loading { color: #1f5fbf; }
    .detail-head { display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; flex-wrap: wrap; }
    .detail-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; border-top: 1px solid #edf0f4; padding-top: 10px; }
    .detail-actions label, .attachment-row label { display: inline-flex; gap: 5px; align-items: center; }
    pre { margin: 0; max-height: 360px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; background: #fbfcfe; border: 1px solid #edf0f4; border-radius: 7px; padding: 10px; }
    .attachments { display: grid; gap: 8px; }
    .attachment-row { border: 1px solid #edf0f4; border-radius: 7px; padding: 9px; display: grid; gap: 6px; background: #fbfcfe; }
    .attachment-tools { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .loading-box { display: flex; align-items: center; gap: 8px; padding: 10px; border: 1px solid #bfd0ef; border-radius: 7px; background: #eef4ff; color: #1d3b74; font-weight: 650; }
    .mini-spinner { width: 14px; height: 14px; border: 2px solid #bfd0ef; border-top-color: var(--blue); border-radius: 50%; animation: spin 0.8s linear infinite; flex: 0 0 auto; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .hidden { display: none; }
    @media (max-width: 820px) { .queue-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <h1>Email Work Queue</h1>
      <div class="topbar-actions">
        <button class="secondary" id="backToEmailsBtn">← Zpět na e-maily</button>
        <button class="secondary" id="backToCockpitBtn">← Zpět do Cockpitu</button>
        <button class="danger" id="purgeTrashBtn" disabled>Trvale smazat e-maily v koši</button>
        <button class="danger" id="trashBatchBtn" disabled>Emaily určené ke smazání smazat</button>
        <button class="primary" id="batchBtn" disabled>Zpracovat dávku</button>
      </div>
    </div>
  </header>
  <main>
    <section>
      <h2>Souhrn</h2>
      <div class="body note">
        <div><strong>Připraveno ke zpracování:</strong> <span id="queueProcessCount">${toProcess.length}</span></div>
        <div><strong>Koš čeká na potvrzení:</strong> <span id="queueTrashCount">${toTrash.length}</span></div>
        <div><strong>Trvalé smazání v koši:</strong> <span id="queuePurgeCount">${recoveredPermanentDeleteItems.length}</span></div>
        <div><strong>Aktuální blok:</strong> <span id="queueVisibleCount">${toProcess.length + toTrash.length}/${toProcess.length + toTrash.length}</span></div>
        <div><strong>Ignorováno:</strong> ${ignored.length}</div>
        <div class="batch-filters" id="batchFilters"></div>
        <div id="queueStatus">Klikni na e-mail vlevo. Detail se načte read-only, bez stahování příloh a bez mazání.</div>
      </div>
    </section>
    <div class="queue-grid">
      <section>
        <h2>E-maily k rozhodnutí</h2>
        <div class="body" id="queueList"></div>
      </section>
      <section>
        <h2>Detail e-mailu</h2>
        <div class="body" id="detailPane">
          <div class="empty">Vyber e-mail ze seznamu.</div>
        </div>
      </section>
    </div>
  </main>
</body>
</html>`);
      queue.document.close();
      initializeWorkQueueWindow(queue, queueItems, recoveredPermanentDeleteItems);
      queue.focus();
      emailItems = [];
      window.lastOverviewText = "";
      renderItems(emailItems);
      updateWorkQueueState();
      overviewStatus.textContent = "Fronta byla otevřena v okně Email Work Queue; hlavní seznam je vyprázdněný.";
    }

    async function loadNewHeaders(options = {}) {
      const lastSevenDays = Boolean(options.lastSevenDays);
      const newOnly = Boolean(options.newOnly);
      const newestVisible = newestItemIso();
      if (newOnly && !newestVisible) {
        newHeadersStatus.textContent = "Obnovit nové je dostupné až po prvním načtení seznamu. Nejdřív použij Načti emaily.";
        updateRefreshButtonState();
        return;
      }
      const startedAt = Date.now();
      const days = selectedDays();
      refreshBtn.disabled = true;
      loadHeadersBtn.disabled = true;
      loadPendingBtn.disabled = true;
      emailDaysInput.disabled = true;
      headersBusy.classList.add("active");
      headersBusyText.textContent = lastSevenDays
        ? `Doplňuji chybějící hlavičky za posledních ${days} dní... 0 s`
        : "Načítám nové hlavičky... 0 s";
      headersBusyTimer = window.setInterval(() => {
        const seconds = Math.max(0, Math.round((Date.now() - startedAt) / 1000));
        headersBusyText.textContent = lastSevenDays
          ? `Doplňuji posledních ${days} dní z iCloud + Seznam... ${seconds} s`
          : `Načítám nové hlavičky z iCloud + Seznam... ${seconds} s`;
      }, 1000);
      newHeadersStatus.textContent = lastSevenDays
        ? `Doplňuji jen dosud nenačtené a nerozhodnuté hlavičky za posledních ${days} dní...`
        : "Doplňuji jen nové příchozí hlavičky z iCloud + Seznam...";
      try {
        const payload = lastSevenDays
          ? {limit_per_source: days <= 7 ? 50 : 75, days, known_ids: knownItemIds()}
          : {limit_per_source: 25, since: newestVisible, known_ids: knownItemIds()};
        const res = await fetch("/api/email-processing/new-headers", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        const incoming = data.items || [];
        const before = emailItems.length;
        emailItems = mergeItems(emailItems, incoming);
        renderItems(emailItems);
        updateWorkQueueState();
        const added = emailItems.length - before;
        const unavailable = data.unavailable && data.unavailable.length
          ? ` Nedostupné zdroje: ${data.unavailable.join("; ")}`
          : "";
        newHeadersStatus.textContent = `${data.message || "Hotovo."} Přidáno do hlavního seznamu: ${added}.${unavailable}`;
      } catch (err) {
        newHeadersStatus.textContent = `Chyba načtení hlaviček: ${err}`;
      } finally {
        if (headersBusyTimer) {
          window.clearInterval(headersBusyTimer);
          headersBusyTimer = null;
        }
        headersBusy.classList.remove("active");
        updateRefreshButtonState();
        loadHeadersBtn.disabled = false;
        loadPendingBtn.disabled = false;
        emailDaysInput.disabled = false;
      }
    }

    async function loadPendingWork() {
      loadPendingBtn.disabled = true;
      newHeadersStatus.textContent = "Načítám rozpracované e-maily z uložených rozhodnutí...";
      try {
        const res = await fetch("/api/email-processing/pending-work");
        const data = await res.json();
        if (!data.ok) {
          newHeadersStatus.textContent = data.message || "Rozpracované e-maily se nepodařilo načíst.";
          return;
        }
        const before = emailItems.length;
        emailItems = mergeItems(emailItems, data.items || []);
        renderItems(emailItems);
        updateWorkQueueState();
        const added = emailItems.length - before;
        newHeadersStatus.textContent = `${data.message || "Rozpracované e-maily načteny."} Přidáno do hlavního seznamu: ${added}.`;
      } catch (err) {
        newHeadersStatus.textContent = `Chyba načtení rozpracovaných e-mailů: ${err}`;
      } finally {
        loadPendingBtn.disabled = false;
      }
    }

    async function loadPendingPurgeItems() {
      try {
        const res = await fetch("/api/email-processing/pending-purge");
        const data = await res.json();
        recoveredPermanentDeleteItems = Array.isArray(data.items) ? data.items : [];
        unrecoverablePurgeCount = Number(data.unrecoverable_count || 0);
        updateWorkQueueState();
      } catch (_err) {
        recoveredPermanentDeleteItems = [];
        unrecoverablePurgeCount = 0;
      }
    }

    async function loadOverview() {
      refreshBtn.disabled = true;
      loadPendingBtn.disabled = true;
      overviewStatus.textContent = "Načítám uložený přehled...";
      overview.innerHTML = "";
      try {
        const res = await fetch("/api/email-processing/overview");
        const data = await res.json();
        overviewStatus.textContent = data.message || "";
        sourcePath.textContent = data.path ? `Soubor: ${data.path}` : "";
        updatedAt.textContent = data.updated_at ? `Aktualizováno: ${data.updated_at}` : "";
        if (!data.ok) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = data.message || "Přehled není k dispozici.";
          overview.appendChild(empty);
          return;
        }
        window.lastOverviewText = data.text || "";
        overviewSince = data.updated_at || "";
        emailItems = mergeItems([], data.items || []);
        renderItems(emailItems);
        updateWorkQueueState();
      } catch (err) {
        overviewStatus.textContent = `Chyba načtení: ${err}`;
      } finally {
        updateRefreshButtonState();
        loadPendingBtn.disabled = false;
      }
    }

    function returnToCockpit() {
      const cockpitUrl = "/";
      if (window.opener && !window.opener.closed) {
        try {
          window.opener.focus();
        } catch (err) {
          // Focus can fail across browser contexts; closing this popup still avoids duplicate Cockpit windows.
        }
        window.close();
        window.setTimeout(() => {
          if (!window.closed) window.location.href = cockpitUrl;
        }, 250);
        return;
      }
      const cockpit = window.open(cockpitUrl, "SamanthaCockpit", "popup=yes,width=1280,height=880,left=90,top=60");
      if (cockpit) {
        cockpit.focus();
        window.close();
      } else {
        window.location.href = cockpitUrl;
      }
    }

    refreshBtn.addEventListener("click", () => loadNewHeaders({newOnly: true}));
    emailDaysInput.addEventListener("change", normalizeDaysInput);
    loadHeadersBtn.addEventListener("click", () => loadNewHeaders({lastSevenDays: true}));
    loadPendingBtn.addEventListener("click", loadPendingWork);
    processEmailsBtn.addEventListener("click", openWorkQueueWindow);
    cockpitBtn.addEventListener("click", returnToCockpit);
    loadPendingPurgeItems();
    loadOverview();
