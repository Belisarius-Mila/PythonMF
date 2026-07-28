"""Thin Cockpit adapter and standalone UI for Janička R2 TXT compilation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.communication.janicka_r2_backend import JanickaR2Backend
from app.communication.janicka_r2_compiler import (
    DocumentInspector,
    JanickaR2CompilationError,
)
from app.communication.janicka_r2_document_selection import (
    DocumentSearchProvider,
    JanickaR2DocumentSelectionError,
)
from app.communication.janicka_r2_documents import (
    R2_DOCUMENTS_RELATIVE_ROOT,
    JanickaR2DocumentError,
)


@dataclass(frozen=True)
class JanickaR2CockpitAdapter:
    """Bind the standalone UI actions to one guarded R2 backend."""

    backend: JanickaR2Backend
    document_search: DocumentSearchProvider | None = None
    document_inspector: DocumentInspector | None = None

    @classmethod
    def bind(
        cls,
        *,
        canonical_private_root: Path,
    ) -> "JanickaR2CockpitAdapter":
        private_root = Path(canonical_private_root).resolve()
        return cls(
            backend=JanickaR2Backend.bind(
                canonical_private_root=private_root,
                document_root=private_root / R2_DOCUMENTS_RELATIVE_ROOT,
            )
        )

    def selection_flow(self):
        return self.backend.document_selection_flow(
            document_search=self.document_search,
            document_inspector=self.document_inspector,
        )


def janicka_r2_document_search_action(
    payload: object,
    *,
    adapter: JanickaR2CockpitAdapter,
) -> dict[str, object]:
    """Return only redacted candidates for an explicit human selection."""

    if not isinstance(adapter, JanickaR2CockpitAdapter):
        return _safe_failure(
            "Hledání dokumentů R2 nemá dostupný bezpečný backend.",
            include_candidates=True,
        )
    body = payload if isinstance(payload, dict) else {}
    try:
        result = adapter.selection_flow().search_documents(body.get("query"))
    except (
        JanickaR2DocumentSelectionError,
        JanickaR2DocumentError,
        ValueError,
    ) as exc:
        return _safe_failure(str(exc), include_candidates=True)
    except Exception:
        return _safe_failure(
            "Hledání dokumentů selhalo bezpečně bez zveřejnění detailu.",
            include_candidates=True,
        )
    return {
        "ok": True,
        **result.as_dict(),
        "message": (
            f"Nalezeno bezpečných voleb: {result.count}."
            if result.count
            else "Nebyla nalezena žádná bezpečná volba."
        ),
    }


def janicka_r2_document_compile_action(
    payload: object,
    *,
    adapter: JanickaR2CockpitAdapter,
) -> dict[str, object]:
    """Create one TXT only after a current human-selected search reference."""

    if not isinstance(adapter, JanickaR2CockpitAdapter):
        return _safe_failure("Vytvoření TXT nemá dostupný bezpečný backend.")
    body = payload if isinstance(payload, dict) else {}
    try:
        result = adapter.selection_flow().compile_selected_document(
            name=body.get("name"),
            query=body.get("query"),
            selection_ref=body.get("selection_ref"),
        )
    except (
        JanickaR2CompilationError,
        JanickaR2DocumentSelectionError,
        JanickaR2DocumentError,
        ValueError,
    ) as exc:
        return _safe_failure(str(exc))
    except Exception:
        return _safe_failure(
            "Vytvoření TXT selhalo bezpečně bez zveřejnění detailu."
        )
    return {
        "ok": True,
        "status": "created",
        "document": result.document.as_dict(),
        "source_count": result.source_count,
        "message": f"Nový dokument {result.document.name} byl vytvořen.",
    }


def _safe_failure(
    message: str,
    *,
    include_candidates: bool = False,
) -> dict[str, object]:
    result: dict[str, object] = {
        "ok": False,
        "message": str(message or "Operace R2 selhala bezpečně."),
    }
    if include_candidates:
        result.update(
            {
                "source_type": "search_private_documents",
                "count": 0,
                "candidates": [],
            }
        )
    return result


JANICKA_R2_DOCUMENTS_HTML = """<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Janička – vytvořit TXT z dokumentu</title>
  <style>
    :root { color-scheme: light; --pink: #be185d; --ink: #271923; --muted: #705366; --line: #fbcfe8; --paper: #fff7fb; --ok: #166534; --bad: #991b1b; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--paper); color: var(--ink); }
    header { position: sticky; top: 0; z-index: 2; display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 13px 18px; background: #fce7f3; border-bottom: 1px solid var(--line); }
    h1 { margin: 0; font-size: 20px; color: #581c35; }
    main { width: min(920px, calc(100% - 28px)); margin: 18px auto 40px; display: grid; gap: 14px; }
    section { background: white; border: 1px solid var(--line); border-radius: 10px; padding: 16px; display: grid; gap: 12px; }
    h2 { margin: 0; font-size: 18px; color: #581c35; }
    p { margin: 0; line-height: 1.5; }
    label { display: grid; gap: 6px; font-weight: 700; color: #581c35; }
    input { width: 100%; border: 1px solid #d8b4c7; border-radius: 7px; padding: 10px 11px; font: inherit; color: var(--ink); background: white; }
    button { border: 0; border-radius: 7px; padding: 10px 13px; font: inherit; font-weight: 750; cursor: pointer; background: #fce7f3; color: #831843; }
    button.primary { background: var(--pink); color: white; }
    button:disabled { opacity: .55; cursor: wait; }
    .row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: end; }
    .status { min-height: 22px; color: var(--muted); line-height: 1.45; }
    .status.ok { color: var(--ok); }
    .status.bad { color: var(--bad); }
    .results { display: grid; gap: 10px; }
    .candidate { border: 1px solid var(--line); border-radius: 8px; padding: 12px; display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 10px; cursor: pointer; background: #fffafd; }
    .candidate.selected { border-color: var(--pink); box-shadow: 0 0 0 2px #fce7f3; }
    .candidate input { width: auto; margin-top: 4px; }
    .candidate-title { font-weight: 800; color: #581c35; overflow-wrap: anywhere; }
    .candidate-meta { margin-top: 3px; color: var(--muted); font-size: 13px; }
    .candidate-snippet { margin-top: 7px; font-size: 14px; line-height: 1.45; overflow-wrap: anywhere; }
    .safety { background: #fffbeb; border-color: #fed7aa; color: #5f370e; }
    @media (max-width: 680px) { header { align-items: flex-start; flex-direction: column; } .row { grid-template-columns: 1fr; } .row button { width: 100%; } }
  </style>
</head>
<body>
  <header>
    <h1>Janička – vytvořit TXT z dokumentu</h1>
    <button id="backBtn" type="button">Zpět do Cockpitu</button>
  </header>
  <main>
    <section>
      <h2>1. Najdi zdrojový dokument</h2>
      <p>Zadej několik slov z názvu nebo obsahu. Uvidíš nejvýše pět krátkých redigovaných náhledů.</p>
      <div class="row">
        <label>Co hledáš
          <input id="queryInput" maxlength="200" autocomplete="off" placeholder="například katastrální dokument">
        </label>
        <button class="primary" id="searchBtn" type="button">Hledat</button>
      </div>
      <div id="searchStatus" class="status" role="status" aria-live="polite">Nejdřív spusť hledání.</div>
      <div id="results" class="results" role="radiogroup" aria-label="Nalezené dokumenty"></div>
    </section>
    <section>
      <h2>2. Vytvoř nový TXT</h2>
      <p>Vyber jeden výsledek a zadej nový název. Existující soubor se nikdy nepřepíše.</p>
      <div class="row">
        <label>Název nového dokumentu
          <input id="nameInput" maxlength="120" autocomplete="off" placeholder="Nový přehled.txt">
        </label>
        <button class="primary" id="createBtn" type="button" disabled>Vytvořit TXT</button>
      </div>
      <div id="createStatus" class="status" role="status" aria-live="polite">Čekám na hledání a ruční výběr.</div>
    </section>
    <section class="safety">
      <strong>Bezpečnost</strong>
      <p>Zdroj se pouze čte. Výstup vznikne jako nový TXT ve vlastním prostoru Janičky. Nic se neodesílá e-mailem a žádný výsledek se nevybere automaticky.</p>
    </section>
  </main>
  <script>
    const queryInput = document.getElementById("queryInput");
    const nameInput = document.getElementById("nameInput");
    const searchBtn = document.getElementById("searchBtn");
    const createBtn = document.getElementById("createBtn");
    const searchStatus = document.getElementById("searchStatus");
    const createStatus = document.getElementById("createStatus");
    const results = document.getElementById("results");
    const backBtn = document.getElementById("backBtn");
    let selectedRef = "";
    let activeQuery = "";

    async function postJson(url, payload) {
      const response = await fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload || {})
      });
      return await response.json();
    }

    function setStatus(node, message, state) {
      node.textContent = message || "";
      node.className = `status ${state || ""}`.trim();
    }

    function updateCreateState() {
      const validName = nameInput.value.trim().toLowerCase().endsWith(".txt");
      createBtn.disabled = !selectedRef || !validName;
    }

    function selectCandidate(card, input, selectionRef) {
      selectedRef = selectionRef;
      results.querySelectorAll(".candidate").forEach((item) => item.classList.remove("selected"));
      results.querySelectorAll('input[type="radio"]').forEach((item) => { item.checked = false; });
      card.classList.add("selected");
      input.checked = true;
      setStatus(createStatus, "Dokument je ručně vybraný. Zkontroluj název nového TXT.", "");
      updateCreateState();
    }

    function renderCandidates(candidates) {
      results.replaceChildren();
      selectedRef = "";
      updateCreateState();
      candidates.forEach((candidate, index) => {
        const card = document.createElement("label");
        card.className = "candidate";
        const input = document.createElement("input");
        input.type = "radio";
        input.name = "r2-document-choice";
        input.value = candidate.selection_ref || "";
        input.setAttribute("aria-label", `Vybrat ${candidate.title || "dokument"}`);
        const body = document.createElement("div");
        const title = document.createElement("div");
        title.className = "candidate-title";
        title.textContent = candidate.title || `Dokument ${index + 1}`;
        const meta = document.createElement("div");
        meta.className = "candidate-meta";
        meta.textContent = `${candidate.domain || "nezjištěno"} / ${candidate.document_type || "nezjištěno"} · stav ${candidate.reading_status || "nezjištěno"}`;
        const snippet = document.createElement("div");
        snippet.className = "candidate-snippet";
        snippet.textContent = candidate.snippet || "Náhled není k dispozici.";
        body.append(title, meta, snippet);
        card.append(input, body);
        card.addEventListener("click", () => selectCandidate(card, input, input.value));
        input.addEventListener("change", () => selectCandidate(card, input, input.value));
        results.appendChild(card);
      });
    }

    async function searchDocuments() {
      const query = queryInput.value.trim();
      activeQuery = "";
      selectedRef = "";
      results.replaceChildren();
      updateCreateState();
      if (query.length < 2) {
        setStatus(searchStatus, "Zadej konkrétnější hledání.", "bad");
        return;
      }
      searchBtn.disabled = true;
      setStatus(searchStatus, "Hledám bezpečné volby…", "");
      try {
        const data = await postJson("/api/janicka-r2/documents/search", {query});
        if (!data.ok) {
          setStatus(searchStatus, data.message || "Hledání se nepodařilo.", "bad");
          return;
        }
        activeQuery = query;
        const candidates = Array.isArray(data.candidates) ? data.candidates : [];
        renderCandidates(candidates);
        setStatus(searchStatus, data.message || "Hledání dokončeno.", candidates.length ? "ok" : "");
        setStatus(createStatus, candidates.length ? "Vyber jeden dokument." : "Není co vybrat.", "");
      } catch (_error) {
        setStatus(searchStatus, "Hledání se nepodařilo spojit s Cockpitem.", "bad");
      } finally {
        searchBtn.disabled = false;
      }
    }

    async function createDocument() {
      const name = nameInput.value.trim();
      if (!activeQuery || !selectedRef || !name.toLowerCase().endsWith(".txt")) {
        setStatus(createStatus, "Vyber dokument a zadej název končící .txt.", "bad");
        return;
      }
      createBtn.disabled = true;
      setStatus(createStatus, "Vytvářím nový TXT…", "");
      try {
        const data = await postJson("/api/janicka-r2/documents/compile", {
          query: activeQuery,
          selection_ref: selectedRef,
          name
        });
        if (!data.ok) {
          setStatus(createStatus, data.message || "TXT se nepodařilo vytvořit.", "bad");
          updateCreateState();
          return;
        }
        const documentInfo = data.document || {};
        setStatus(
          createStatus,
          `${data.message || "TXT byl vytvořen."} Velikost: ${Number(documentInfo.size_bytes || 0)} B.`,
          "ok"
        );
        selectedRef = "";
        results.querySelectorAll('input[type="radio"]').forEach((item) => { item.checked = false; });
        results.querySelectorAll(".candidate").forEach((item) => item.classList.remove("selected"));
      } catch (_error) {
        setStatus(createStatus, "Vytvoření TXT se nepodařilo spojit s Cockpitem.", "bad");
        updateCreateState();
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

    searchBtn.addEventListener("click", searchDocuments);
    createBtn.addEventListener("click", createDocument);
    nameInput.addEventListener("input", updateCreateState);
    queryInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        searchDocuments();
      }
    });
    backBtn.addEventListener("click", returnToCockpit);
  </script>
</body>
</html>
"""
