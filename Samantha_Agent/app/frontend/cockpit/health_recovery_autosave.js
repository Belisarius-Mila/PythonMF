(() => {
  "use strict";

  const DIAGNOSTICS_ENDPOINTS = [
    ["Server health", "/api/server/health"],
    ["Hlavní status", "/api/status"],
    ["Co teď?", "/api/decision-status"],
    ["Recovery", "/api/recovery/status"],
    ["Webové aplikace", "/api/web-apps"],
    ["Knihovna", "/api/library/list?category=other&limit=1"],
    ["Projekty", "/api/projects/status"],
    ["Quick Notes", "/api/quick-notes/status"],
    ["Důležitá připomenutí", "/api/urgent-reminders/status"],
    ["Kvantitativní", "/api/quantitative-status"],
    ["Systémový audit", "/api/project-audit?mode=quick"],
    ["Consistency audit", "/api/consistency-status"],
    ["Dokumenty k revizi", "/api/documents/review-report"]
  ];

  function createHealthRecoveryAutosaveFrontend(dependencies) {
    const deps = dependencies || {};
    const elements = deps.elements || {};
    let currentAutosaveCleanupPlan = null;

    async function checkEndpointHealth(url, timeoutMs = 6000) {
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), timeoutMs);
      try {
        const startedAt = performance.now();
        const res = await fetch(url, {cache: "no-store", signal: controller.signal});
        const elapsed = Math.round(performance.now() - startedAt);
        return {url, ok: res.ok, status: res.status, elapsed};
      } catch (err) {
        const isAbort = err && err.name === "AbortError";
        return {
          url,
          ok: false,
          status: 0,
          elapsed: timeoutMs,
          error: isAbort ? `timeout po ${timeoutMs} ms` : String(err)
        };
      } finally {
        window.clearTimeout(timer);
      }
    }

    async function runFrontendHealthCheck() {
      deps.setHealthValue(elements.frontendHealthJs, "běží", "ok");
      deps.verifyButtonHealth();
      deps.setHealthValue(elements.frontendHealthApi, "kontroluji...", "warn");
      const results = await Promise.all([
        checkEndpointHealth("/api/server/health"),
        checkEndpointHealth("/api/recovery/status")
      ]);
      const failed = results.filter((item) => !item.ok);
      if (failed.length) {
        deps.setHealthValue(
          elements.frontendHealthApi,
          `chyba ${failed.map((item) => item.url).join(", ")}`,
          "bad"
        );
        deps.recordFrontendError(
          `API health selhal: ${failed.map((item) => `${item.url} ${item.status || item.error || ""}`).join("; ")}`
        );
      } else {
        const slowest = Math.max(...results.map((item) => item.elapsed || 0));
        deps.setHealthValue(elements.frontendHealthApi, `OK, max ${slowest} ms`, "ok");
        deps.clearRecoverableFrontendNetworkErrors();
        if (!deps.getFrontendErrorState().lastError) {
          deps.setHealthValue(elements.frontendHealthError, "žádná", "ok");
        }
      }
    }

    async function openDiagnosticsModal() {
      elements.diagnosticsModal.classList.remove("hidden");
      elements.diagnosticsStatus.textContent = "Měřím endpointy...";
      elements.diagnosticsFrontend.textContent = "";
      renderDiagnosticsStatusSignals();
      elements.diagnosticsEndpointList.innerHTML = "";
      elements.diagnosticsErrorList.innerHTML = "";
      const buttonsOk = deps.verifyButtonHealth();
      const errorState = deps.getFrontendErrorState();
      elements.diagnosticsFrontend.textContent = [
        "Frontend JS: běží",
        `Tlačítka: ${buttonsOk ? "napojeno" : "problém"}`,
        `Poslední chyba: ${errorState.lastError || "žádná"}`
      ].join(" | ");
      try {
        const results = await Promise.all(
          DIAGNOSTICS_ENDPOINTS.map(([label, url]) =>
            checkEndpointHealth(url, 8000).then((result) => ({...result, label}))
          )
        );
        renderDiagnosticsEndpointRows(results);
        renderDiagnosticsErrors();
        const failed = results.filter((item) => !item.ok);
        elements.diagnosticsStatus.textContent = failed.length
          ? `Diagnostika doběhla: ${failed.length} endpointů má problém.`
          : "Diagnostika doběhla: endpointy odpovídají.";
      } catch (err) {
        deps.recordFrontendError(err);
        elements.diagnosticsStatus.textContent = `Chyba diagnostiky: ${err}`;
      }
    }

    function closeDiagnosticsModal() {
      elements.diagnosticsModal.classList.add("hidden");
    }

    function renderDiagnosticsStatusSignals() {
      if (!elements.diagnosticsStatusSignals) return;
      elements.diagnosticsStatusSignals.innerHTML = "";
      const signals = Object.values(deps.getDashboardStatusSignals() || {}).filter(Boolean);
      if (!signals.length) {
        const empty = document.createElement("div");
        empty.className = "diagnostics-row";
        empty.textContent = "Stavové signály zatím nejsou načtené.";
        elements.diagnosticsStatusSignals.appendChild(empty);
        return;
      }
      signals.slice().sort((a, b) => {
        const rankDiff = deps.dashboardStatusRank(b.level) - deps.dashboardStatusRank(a.level);
        if (rankDiff) return rankDiff;
        return deps.dashboardStatusPriority(b.key) - deps.dashboardStatusPriority(a.key);
      }).forEach((signal) => {
        const row = document.createElement("div");
        row.className = `diagnostics-row ${signal.level || "ok"}`;
        const title = document.createElement("div");
        title.className = "diagnostics-row-title";
        title.textContent = `${dashboardSignalLabel(signal.key)}: ${dashboardSignalMeaning(signal.level)}`;
        const detail = document.createElement("div");
        detail.className = "project-meta";
        detail.textContent = signal.reason || "";
        const action = document.createElement("div");
        action.className = "project-meta";
        action.textContent = `Co teď: ${dashboardSignalNextAction(signal)}`;
        row.appendChild(title);
        row.appendChild(detail);
        row.appendChild(action);
        elements.diagnosticsStatusSignals.appendChild(row);
      });
    }

    function dashboardSignalMeaning(level) {
      return {
        bad: "chyba nebo nutná akce",
        warn: "varování / ruční kontrola",
        loading: "samostatné načítání",
        ok: "v pořádku"
      }[level] || "stav neznámý";
    }

    function dashboardSignalNextAction(signal) {
      const level = signal && signal.level || "ok";
      const reason = String(signal && signal.reason || "").toLocaleLowerCase("cs-CZ");
      if (level === "loading") return "počkat na samostatné načtení nebo stisknout Obnovit stav";
      if (level === "bad") return "otevřít diagnostiku endpointů nebo příslušné okno a řešit chybu";
      if (level === "warn") {
        if (reason.includes("připomen")) return "otevřít příslušný přehled a rozhodnout, jestli je akce potřeba";
        if (reason.includes("git")) return "zkontrolovat pracovní strom a případně udělat tematický commit";
        if (reason.includes("záloh")) return "zkontrolovat stav zálohy";
        if (reason.includes("audit")) return "otevřít auditní detail";
        if (reason.includes("dokument")) return "otevřít dokumentovou frontu nebo ScanDocu";
        return "otevřít detail dané oblasti a rozhodnout další krok";
      }
      return "nic akutního";
    }

    function dashboardSignalLabel(key) {
      return {
        main: "Hlavní status",
        consistency: "Audit",
        documents: "Dokumenty",
        reminders: "Připomenutí",
        backup: "Záloha",
        git: "Git",
        projects: "Projekty",
        quickNotes: "QN",
        quantitative: "Systém",
        scandocu: "ScanDocu"
      }[key] || key || "Signál";
    }

    function renderDiagnosticsEndpointRows(results) {
      elements.diagnosticsEndpointList.innerHTML = "";
      results.forEach((item) => {
        const row = document.createElement("div");
        row.className = "diagnostics-row";
        const text = document.createElement("div");
        const title = document.createElement("div");
        title.className = "diagnostics-row-title";
        title.textContent = item.label || item.url || "";
        const meta = document.createElement("div");
        meta.className = "diagnostics-row-meta";
        meta.textContent = `${item.url || ""} | status ${item.status || 0} | ${item.elapsed || 0} ms${item.error ? " | " + item.error : ""}`;
        const badge = document.createElement("div");
        badge.className = `diagnostics-badge ${item.ok ? "ok" : "bad"}`;
        badge.textContent = item.ok ? "OK" : "chyba";
        text.appendChild(title);
        text.appendChild(meta);
        row.appendChild(text);
        row.appendChild(badge);
        elements.diagnosticsEndpointList.appendChild(row);
      });
    }

    function renderDiagnosticsErrors() {
      elements.diagnosticsErrorList.innerHTML = "";
      const errorHistory = deps.getFrontendErrorState().history;
      if (!errorHistory.length) {
        const empty = document.createElement("div");
        empty.className = "status-line";
        empty.textContent = "Žádné frontend/API chyby nejsou zachycené.";
        elements.diagnosticsErrorList.appendChild(empty);
        return;
      }
      errorHistory.forEach((item) => {
        const row = document.createElement("div");
        row.className = "diagnostics-row";
        const text = document.createElement("div");
        const title = document.createElement("div");
        title.className = "diagnostics-row-title";
        title.textContent = item.text || "";
        const meta = document.createElement("div");
        meta.className = "diagnostics-row-meta";
        meta.textContent = item.createdAt || "";
        text.appendChild(title);
        text.appendChild(meta);
        row.appendChild(text);
        elements.diagnosticsErrorList.appendChild(row);
      });
    }

    async function openRecoveryModal() {
      elements.recoveryModal.classList.remove("hidden");
      elements.recoveryStatus.textContent = "Načítám recovery stav...";
      elements.recoveryAutosave.textContent = "";
      elements.recoveryGit.textContent = "";
      elements.recoveryProject.textContent = "";
      elements.recoveryHandoffs.innerHTML = "";
      elements.recoveryCommands.innerHTML = "";
      try {
        const data = await deps.fetchJson("/api/recovery/status");
        renderRecoveryStatus(data);
      } catch (err) {
        deps.recordFrontendError(err);
        elements.recoveryStatus.textContent = `Chyba načtení Recovery centra: ${err}`;
      }
    }

    function closeRecoveryModal() {
      elements.recoveryModal.classList.add("hidden");
      deps.maybeReturnToJanicka("recovery");
    }

    function renderRecoveryStatus(data) {
      const autosave = data.autosave || {};
      const autosaveRuntime = autosave.runtime || {};
      const git = data.git || {};
      const project = data.active_project || {};
      elements.recoveryStatus.textContent = `${data.message || "Recovery centrum načteno."} ${data.safety_note || ""}`;
      elements.recoveryAutosave.textContent = autosave.ok
        ? `Poslední: ${autosave.latest_file || ""} | ${autosave.latest_modified_at || ""} | ${formatAge(autosave.latest_age_seconds)} | souborů: ${autosave.file_count || 0} | watchery: ${Number(autosaveRuntime.watcher_count || 0)} (očekáván 1)${autosaveRuntime.warning ? ` | ${autosaveRuntime.warning}` : ""}`
        : (autosave.message || "Autosave metadata nejsou dostupná.");
      elements.recoveryGit.textContent = git.ok
        ? `${git.message || ""} | ${git.branch || ""}${git.dirty_count ? ` | ukázka: ${(git.dirty_files || []).join("; ")}` : ""}`
        : (git.message || "Git status nejde načíst.");
      elements.recoveryProject.textContent = project.ok
        ? `${project.name || "Cockpit Recovery centrum"} | priorita ${project.priority || ""} | ${project.next_step || project.status || ""}`
        : (project.message || "Aktivní projekt Recovery centra není nalezen.");
      renderRecoveryHandoffs(data.handoffs || []);
      renderRecoveryCommands(data.commands || []);
    }

    function renderRecoveryHandoffs(items) {
      elements.recoveryHandoffs.innerHTML = "";
      if (!items.length) {
        elements.recoveryHandoffs.textContent = "Žádné recovery handoffy nejsou nastavené.";
        return;
      }
      items.forEach((item) => {
        const card = document.createElement("div");
        card.className = "project-card";
        const title = document.createElement("div");
        title.className = "project-title";
        title.textContent = item.title || item.path || "Handoff";
        const meta = document.createElement("div");
        meta.className = "project-meta";
        meta.textContent = `${item.path || ""} | priorita ${item.priority || ""} | ${item.status || ""} | ${item.date || ""}`;
        const next = document.createElement("div");
        next.className = "project-next";
        next.textContent = item.next_step || item.message || "";
        card.appendChild(title);
        card.appendChild(meta);
        card.appendChild(next);
        elements.recoveryHandoffs.appendChild(card);
      });
    }

    function renderRecoveryCommands(items) {
      elements.recoveryCommands.innerHTML = "";
      items.forEach((item) => {
        const card = document.createElement("div");
        card.className = "project-card";
        const title = document.createElement("div");
        title.className = "project-title";
        title.textContent = item.label || "Příkaz";
        const command = document.createElement("div");
        command.className = "recovery-command";
        command.textContent = item.command || "";
        const note = document.createElement("div");
        note.className = "project-meta";
        note.textContent = item.note || "";
        card.appendChild(title);
        card.appendChild(command);
        card.appendChild(note);
        elements.recoveryCommands.appendChild(card);
      });
    }

    function formatAge(seconds) {
      if (seconds === null || seconds === undefined) return "stáří neznámé";
      const value = Number(seconds);
      if (!Number.isFinite(value)) return "stáří neznámé";
      if (value < 60) return `${Math.round(value)} s`;
      if (value < 3600) return `${Math.round(value / 60)} min`;
      if (value < 86400) return `${Math.round(value / 3600)} h`;
      return `${Math.round(value / 86400)} d`;
    }

    function formatAutosaveCleanupPlan(data) {
      const plan = data.plan || {};
      const runtime = data.runtime || {};
      const measurement = data.disk_measurement || {};
      const logical = Number(plan.logical_gib || 0);
      const allocated = Number(plan.allocated_gib || 0);
      const freeChange = measurement.free_change_gib;
      const currentFree = measurement.free_after_gib == null
        ? runtime.disk_free_gib
        : measurement.free_after_gib;
      const actualChangeLine = freeChange === null || freeChange === undefined
        ? "Skutečná změna volného místa: změří se až po potvrzeném úklidu"
        : `Skutečná změna volného místa: ${Number(freeChange) >= 0 ? "+" : ""}${Number(freeChange).toFixed(3)} GiB ` +
          `(před ${Number(measurement.free_before_gib).toFixed(3)} GiB, po ${Number(measurement.free_after_gib).toFixed(3)} GiB)`;
      return [
        data.message || "Autosave úklid spočítán.",
        "",
        Number(plan.retention_days || 0) > 0
          ? `Retence: ponechat posledních ${plan.retention_days} dní`
          : "Retence podle stáří: vypnutá",
        `Pojistka: ponechat nejnovějších ${plan.keep_latest_snapshots || 12} časových snapshotů`,
        `Timestampované soubory: ${plan.scanned_timestamped_files || 0}`,
        `Chráněné soubory: ${plan.protected_timestamped_files || 0}`,
        `Ke smazání: ${plan.delete_count || 0}`,
        `Logická velikost kandidátů: ${logical.toFixed(3)} GiB`,
        `Fyzicky alokované bloky kandidátů: ${allocated.toFixed(3)} GiB`,
        actualChangeLine,
        `Autosave watchery: ${Number(runtime.watcher_count || 0)} (očekáván 1)`,
        currentFree == null
          ? "SSD volné místo: nezjištěno"
          : `SSD volné místo: ${Number(currentFree).toFixed(1)} GiB (${runtime.disk_state || "unknown"})`,
        runtime.warning ? `Varování: ${runtime.warning}` : "Autosave watcher stav: OK",
        "",
        data.measurement_note || "Alokované bloky nejsou zárukou skutečně uvolněného místa.",
        data.safety_note || "Obsah autosave logů se nečte."
      ].join("\n");
    }

    async function previewAutosaveCleanup(button) {
      const targetButton = button || elements.autosaveCleanupPreviewBtn || elements.dashboardAutosaveCleanupBtn;
      targetButton.disabled = true;
      if (elements.autosaveCleanupStatus) elements.autosaveCleanupStatus.textContent = "Počítám autosave úklid...";
      if (elements.autosaveCleanupOutput) elements.autosaveCleanupOutput.textContent = "";
      try {
        const data = await deps.postJson("/api/session-autosave/cleanup", {
          retention_days: 0,
          keep_latest_snapshots: 12,
          apply: false
        });
        currentAutosaveCleanupPlan = data.plan || null;
        if (elements.autosaveCleanupStatus) elements.autosaveCleanupStatus.textContent = data.message || "Dry-run hotov.";
        if (elements.autosaveCleanupOutput) elements.autosaveCleanupOutput.textContent = formatAutosaveCleanupPlan(data);
        if (elements.autosaveCleanupApplyBtn) elements.autosaveCleanupApplyBtn.disabled = !((data.plan || {}).delete_count > 0);
        elements.servicePanel.open = true;
        deps.showMessage(data.message || "Autosave úklid spočítán.");
      } catch (err) {
        deps.recordFrontendError(err);
        if (elements.autosaveCleanupStatus) elements.autosaveCleanupStatus.textContent = `Chyba autosave dry-runu: ${err}`;
        if (elements.autosaveCleanupApplyBtn) elements.autosaveCleanupApplyBtn.disabled = true;
        deps.showMessage(`Chyba autosave dry-runu: ${err}`);
      } finally {
        targetButton.disabled = false;
      }
    }

    async function applyAutosaveCleanup() {
      if (!currentAutosaveCleanupPlan) {
        await previewAutosaveCleanup(elements.autosaveCleanupPreviewBtn);
      }
      const plan = currentAutosaveCleanupPlan || {};
      const deleteCount = Number(plan.delete_count || 0);
      const logical = Number(plan.logical_gib || 0);
      const allocated = Number(plan.allocated_gib || 0);
      if (!deleteCount) {
        if (elements.autosaveCleanupStatus) elements.autosaveCleanupStatus.textContent = "Není co mazat.";
        return;
      }
      const ok = window.confirm(
        "Vyčistit staré autosave snapshoty?\n\n" +
        `Smazat se má ${deleteCount} starých timestampovaných souborů.\n` +
        `Logická velikost: ${logical.toFixed(3)} GiB.\n` +
        `Fyzicky alokované bloky: ${allocated.toFixed(3)} GiB.\n` +
        "Skutečná změna volného místa se změří až po úklidu.\n\n" +
        "Zůstanou latest soubory a 12 nejnovějších časových snapshotů."
      );
      if (!ok) return;
      elements.autosaveCleanupApplyBtn.disabled = true;
      if (elements.autosaveCleanupPreviewBtn) elements.autosaveCleanupPreviewBtn.disabled = true;
      if (elements.autosaveCleanupStatus) elements.autosaveCleanupStatus.textContent = "Mažu staré autosave snapshoty...";
      try {
        const data = await deps.postJson("/api/session-autosave/cleanup", {
          retention_days: 0,
          keep_latest_snapshots: 12,
          apply: true,
          confirmation_text: "SMAZAT STARE AUTOSAVE"
        });
        currentAutosaveCleanupPlan = null;
        if (elements.autosaveCleanupStatus) elements.autosaveCleanupStatus.textContent = data.message || "Autosave úklid hotov.";
        if (elements.autosaveCleanupOutput) elements.autosaveCleanupOutput.textContent = formatAutosaveCleanupPlan(data);
        deps.showMessage(data.message || "Autosave úklid hotov.");
        await deps.refresh({silent: true, includeSecondary: false});
      } catch (err) {
        deps.recordFrontendError(err);
        if (elements.autosaveCleanupStatus) elements.autosaveCleanupStatus.textContent = `Chyba autosave úklidu: ${err}`;
        deps.showMessage(`Chyba autosave úklidu: ${err}`);
      } finally {
        if (elements.autosaveCleanupPreviewBtn) elements.autosaveCleanupPreviewBtn.disabled = false;
        if (elements.autosaveCleanupApplyBtn) {
          elements.autosaveCleanupApplyBtn.disabled = !currentAutosaveCleanupPlan || !(currentAutosaveCleanupPlan.delete_count > 0);
        }
      }
    }

    return Object.freeze({
      applyAutosaveCleanup,
      closeDiagnosticsModal,
      closeRecoveryModal,
      formatAutosaveCleanupPlan,
      openDiagnosticsModal,
      openRecoveryModal,
      previewAutosaveCleanup,
      runFrontendHealthCheck,
    });
  }

  window.SamanthaHealthRecoveryAutosave = Object.freeze({
    create: createHealthRecoveryAutosaveFrontend,
  });
})();
