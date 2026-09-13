(() => {
  "use strict";

  function createDocumentSearchFrontend(dependencies) {
    const {documentSearchInput, documentSearchBtn, documentSearchStatus,
      documentSearchResults} = dependencies.elements;
    const {fetch, readingStatusOptions, openDocumentForReading,
      openPurchaseForReading, printDocument, moveDocumentLifecycle,
      setDocumentReadingStatus} = dependencies;

	    async function searchDocuments() {
      const query = documentSearchInput.value.trim();
      documentSearchResults.innerHTML = "";
      if (query.length < 2) {
        documentSearchStatus.textContent = "Zadej aspoň dvě písmena nebo číslice.";
        return;
      }
      documentSearchBtn.disabled = true;
      documentSearchStatus.textContent = "Hledám v indexu dokumentů...";
      try {
        const res = await fetch(`/api/documents/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        documentSearchStatus.textContent = data.message || "";
        renderDocumentSearchResults(data.results || []);
      } catch (err) {
        documentSearchStatus.textContent = `Chyba hledání: ${err}`;
      } finally {
        documentSearchBtn.disabled = false;
      }
    }

    function renderDocumentSearchResults(results) {
      documentSearchResults.innerHTML = "";
      if (!results || results.length === 0) {
        return;
      }
      results.forEach((item) => {
        const documentRef = item.document_ref || item.document_id;
        const sourceType = item.source_type || "document";
        const isPurchase = sourceType === "purchase";
        const card = document.createElement("div");
        card.className = "search-result";
        const head = document.createElement("div");
        head.className = "search-result-head";
        const summary = document.createElement("div");
        const title = document.createElement("div");
        title.className = "search-title";
        title.textContent = item.title || item.original_filename || item.document_id || "Dokument bez názvu";
        const meta = document.createElement("div");
        meta.className = "search-meta";
        const sourceLabel = item.source_label || (isPurchase ? "Nákup / záruka" : "Dokument");
        meta.textContent = `${sourceLabel} | ${item.domain || "other"} / ${item.document_type || "document"} | ${item.counterparty || "protistrana nezjištěna"} | ${item.related_asset || "věc nezjištěna"}`;
        const toggle = document.createElement("button");
        toggle.className = "secondary";
        toggle.type = "button";
        toggle.textContent = "Rozbalit";
        const headOpenBtn = document.createElement("button");
        headOpenBtn.className = "primary";
        headOpenBtn.type = "button";
        headOpenBtn.textContent = isPurchase ? "Otevřít PDF" : "Otevřít / číst";
        const headActions = document.createElement("div");
        headActions.className = "search-result-head-actions";
        headActions.appendChild(headOpenBtn);
        headActions.appendChild(toggle);
        const detail = document.createElement("div");
        detail.className = "search-detail hidden";
        const id = document.createElement("div");
        id.className = "search-meta";
        id.textContent = `ID: ${item.document_id || ""}`;
        const path = document.createElement("div");
        path.className = "search-meta";
        path.textContent = `Cesta: ${item.stored_path || ""}`;
        const lifecycle = document.createElement("div");
        lifecycle.className = "search-meta";
        lifecycle.textContent = `Stav: ${item.lifecycle_status || "active"}`;
        const readingStatus = document.createElement("div");
        readingStatus.className = "search-meta";
        readingStatus.textContent = isPurchase ? "Stav: nákupní evidence" : `Stav čtení: ${item.reading_status_label || "k revizi"}`;
        const statusRow = document.createElement("div");
        statusRow.className = "status-select-row";
        const statusLabel = document.createElement("label");
        statusLabel.textContent = "Stav čtení";
        const statusSelect = document.createElement("select");
        readingStatusOptions.forEach(([value, label]) => {
          const option = document.createElement("option");
          option.value = value;
          option.textContent = label;
          option.selected = value === (item.reading_status || "needs_review");
          statusSelect.appendChild(option);
        });
        if (!isPurchase) {
          statusSelect.addEventListener("change", () => setDocumentReadingStatus(documentRef, statusSelect.value));
          statusRow.appendChild(statusLabel);
          statusRow.appendChild(statusSelect);
        }
        const snippet = document.createElement("div");
        snippet.className = "search-snippet";
        snippet.textContent = item.snippet || "";
        const actions = document.createElement("div");
        actions.className = "actions";
        const openBtn = document.createElement("button");
        openBtn.className = "primary";
        openBtn.type = "button";
        openBtn.textContent = isPurchase ? "Otevřít nákupní PDF" : "Otevřít / číst PDF";
        const printBtn = document.createElement("button");
        printBtn.className = "secondary";
        printBtn.type = "button";
        printBtn.textContent = "Tisknout";
        const archiveBtn = document.createElement("button");
        archiveBtn.className = "secondary";
        archiveBtn.type = "button";
        archiveBtn.textContent = "Archivovat";
        const trashBtn = document.createElement("button");
        trashBtn.className = "danger-soft";
        trashBtn.type = "button";
        trashBtn.textContent = "Do koše";
        if (!isPurchase) {
          headOpenBtn.addEventListener("click", () => openDocumentForReading(documentRef, headOpenBtn));
          openBtn.addEventListener("click", () => openDocumentForReading(documentRef, openBtn));
          printBtn.addEventListener("click", () => printDocument(documentRef));
          archiveBtn.addEventListener("click", () => moveDocumentLifecycle(documentRef, "archive"));
          trashBtn.addEventListener("click", () => moveDocumentLifecycle(documentRef, "trash"));
          actions.appendChild(openBtn);
          actions.appendChild(printBtn);
          actions.appendChild(archiveBtn);
          actions.appendChild(trashBtn);
        } else {
          headOpenBtn.addEventListener("click", () => openPurchaseForReading(documentRef, headOpenBtn));
          openBtn.addEventListener("click", () => openPurchaseForReading(documentRef, openBtn));
          actions.appendChild(openBtn);
        }
        summary.appendChild(title);
        summary.appendChild(meta);
        head.appendChild(summary);
        head.appendChild(headActions);
        detail.appendChild(id);
        detail.appendChild(path);
        detail.appendChild(lifecycle);
        detail.appendChild(readingStatus);
        if (!isPurchase) {
          detail.appendChild(statusRow);
        }
        detail.appendChild(snippet);
        detail.appendChild(actions);
        toggle.addEventListener("click", () => {
          const isHidden = detail.classList.toggle("hidden");
          toggle.textContent = isHidden ? "Rozbalit" : "Sbalit";
        });
        card.appendChild(head);
        card.appendChild(detail);
        documentSearchResults.appendChild(card);
      });
    }

    return Object.freeze({searchDocuments});
  }

  window.SamanthaDocumentSearch = Object.freeze({create: createDocumentSearchFrontend});
})();
