(() => {
  "use strict";

  function createDocumentReviewFrontend(dependencies) {
    const {documentsPanel, reviewReportBtn, reviewReportStatus,
      reviewReportList, reviewReportCount} = dependencies.elements;
    const {fetch, recordFrontendError, showMessage, openScanDocuReview} = dependencies;
    const {setDocumentCardState = () => {}, revealReviewCard = () => {}} = dependencies;

    async function loadDocumentReviewReport() {
      reviewReportBtn.disabled = true;
      reviewReportStatus.textContent = "Načítám dokumenty k vyřešení...";
      reviewReportList.innerHTML = "";
      let loaded = false;
      try {
        const res = await fetch("/api/documents/review-report");
        const data = await res.json();
        if (res.ok === false || data.ok === false || !Array.isArray(data.groups)) throw new Error(data.message || "Report není dostupný.");
        renderDocumentReviewReport(data);
        loaded = true;
      } catch (err) {
        recordFrontendError(err);
        reviewReportStatus.textContent = `Chyba reportu: ${err}`;
        setDocumentCardState(reviewReportCount, false, true);
      } finally {
        reviewReportBtn.disabled = false;
      }
      return loaded;
    }

    async function openDocumentReviewPanel() {
      documentsPanel.open = true;
      showMessage("Otevírám dokumenty k vyřešení...");
      const loaded = await loadDocumentReviewReport();
      revealReviewCard();
      reviewReportList.scrollIntoView({behavior: "smooth", block: "start"});
      if (loaded) {
        showMessage("Vyber dokument; celý se otevře se všemi možnostmi ve ScanDocu.");
      }
    }

    function renderDocumentReviewReport(data) {
      const summary = data.summary || {};
      const groups = data.groups || [];
      reviewReportCount.textContent = String(summary.candidate_count || 0);
      setDocumentCardState(reviewReportCount, groups.length > 0 || Number(summary.candidate_count) > 0, data.ok === false || !Array.isArray(data.groups));
      reviewReportStatus.textContent = data.message || "Report načten.";
      reviewReportList.innerHTML = "";
      if (!groups.length) {
        const empty = document.createElement("div");
        empty.className = "work-item empty";
        empty.textContent = "Žádný dokument nyní nevyžaduje zásah.";
        reviewReportList.appendChild(empty);
        return;
      }
      groups.forEach((group) => {
        const groupNode = document.createElement("div");
        groupNode.className = "review-group";
        const head = document.createElement("div");
        head.className = "review-group-head";
        const title = document.createElement("div");
        title.className = "review-group-title";
        title.textContent = group.label || group.id || "Skupina";
        const count = document.createElement("div");
        count.className = "review-group-count";
        count.textContent = `${group.count || 0} položek`;
        head.appendChild(title);
        head.appendChild(count);
        groupNode.appendChild(head);
        const action = document.createElement("div");
        action.className = "review-action";
        action.textContent = group.recommended_action || "";
        groupNode.appendChild(action);
        const items = group.items || [];
        if (!items.length) {
          const empty = document.createElement("div");
          empty.className = "work-meta";
          empty.textContent = group.empty_label || "Bez položek.";
          groupNode.appendChild(empty);
          reviewReportList.appendChild(groupNode);
          return;
        }
        items.forEach((item) => {
          groupNode.appendChild(renderDocumentReviewReportItem(item));
        });
        if (group.truncated) {
          const note = document.createElement("div");
          note.className = "work-meta";
          note.textContent = "Skupina je zkrácená; další položky existují v indexu.";
          groupNode.appendChild(note);
        }
        reviewReportList.appendChild(groupNode);
      });
      if (data.truncated) {
        const note = document.createElement("div");
        note.className = "status-line";
        note.textContent = "Celkový report je zkrácený; další položky existují v indexu.";
        reviewReportList.appendChild(note);
      }
    }

    function renderDocumentReviewReportItem(item) {
        const row = document.createElement("div");
        row.className = "work-item";
        const documentRef = item.document_ref || "";
        const title = document.createElement("div");
        title.className = "work-title";
        title.textContent = item.title || item.document_id || "Dokument bez názvu";
        const recommendation = document.createElement("div");
        recommendation.className = "work-meta";
        recommendation.textContent = item.recommended_action || item.review_summary || "Zkontrolovat dokument.";
        const meta = document.createElement("div");
        meta.className = "work-meta";
        meta.textContent = `${item.classification_summary || ""} | ${item.reading_summary || ""}`;
        const reasons = document.createElement("div");
        reasons.className = "work-meta";
        reasons.textContent = (item.reasons || []).map((reason) => reason.label || reason.id || "").filter(Boolean).join(", ");
        const suggestion = item.metadata_suggestion || {};
        const suggestionNode = document.createElement("div");
        suggestionNode.className = "work-meta";
        suggestionNode.textContent = suggestion.can_accept && suggestion.summary ? `Návrh: ${suggestion.summary}` : "";
        const id = document.createElement("div");
        id.className = "work-meta";
        id.textContent = `ID: ${item.document_id || ""}`;
        const actions = document.createElement("div");
        actions.className = "actions";
        const openBtn = document.createElement("button");
        openBtn.className = "primary";
        openBtn.type = "button";
        openBtn.textContent = "Vyřešit ve ScanDocu";
        openBtn.addEventListener("click", () => openScanDocuReview(item, openBtn));
        actions.appendChild(openBtn);
        row.appendChild(title);
        row.appendChild(recommendation);
        row.appendChild(meta);
        if (reasons.textContent) row.appendChild(reasons);
        if (suggestionNode.textContent) row.appendChild(suggestionNode);
        row.appendChild(id);
        row.appendChild(actions);
        return row;
    }

    return Object.freeze({loadDocumentReviewReport, openDocumentReviewPanel, renderDocumentReviewReport, renderDocumentReviewReportItem});
  }

  window.SamanthaDocumentReview = Object.freeze({create: createDocumentReviewFrontend});
})();
