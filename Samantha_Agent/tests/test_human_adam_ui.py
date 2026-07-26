from __future__ import annotations

import unittest

from app.communication.human_adam_ui import HUMAN_ADAM_HTML


class HumanAdamUiTests(unittest.TestCase):
    def test_ui_exposes_explicit_connection_send_time_and_delivery_evidence(self) -> None:
        for element_id in (
            "connectBtn",
            "profileSelect",
            "profileSwitchBtn",
            "profileBadge",
            "refreshBtn",
            "connectionBadge",
            "threadBadge",
            "workspaceBadge",
            "mediaSoundTestBtn",
            "completionMediaAudio",
            "threadRotationOpenBtn",
            "threadRotationPanel",
            "threadRotationCloseBtn",
            "threadRotationMeta",
            "threadRotationConfirmation",
            "threadRotationAuditBtn",
            "threadRotationBtn",
            "chat",
            "messageInput",
            "writeIntentBtn",
            "sendBtn",
            "tvbcpOpenBtn",
            "tvbcpPanel",
            "tvbcpCloseBtn",
            "tvbcpRefreshBtn",
            "tvbcpScroll",
            "tvbcpContent",
            "tvbcpEnd",
            "workOpenBtn",
            "workPanel",
            "workCloseBtn",
            "workRefreshBtn",
            "workHelpBtn",
            "workHelpPanel",
            "workHelpCloseBtn",
            "liveWorkStatusBox",
            "liveWorkStatusMeta",
            "liveWorkStatusAxes",
            "workChanges",
            "integrationAuditBox",
            "integrationAuditMeta",
            "integrationAuditPaths",
            "integrationConfirmation",
            "integrationBtn",
            "checkpointMessage",
            "checkpointBtn",
            "deployMeta",
            "handoffTakeoverCheck",
            "deployAuditBtn",
            "deployConfirmation",
            "deployBtn",
            "deploymentReceipt",
            "turnActivity",
            "mobileStatusSummary",
            "mobileStatusText",
            "mobileStatusToggleText",
            "statusDetails",
            "voiceRecordBtn",
            "voiceStopBtn",
            "voiceStatus",
        ):
            self.assertIn(f'id="{element_id}"', HUMAN_ADAM_HTML)
        self.assertIn("Odesláno", HUMAN_ADAM_HTML)
        self.assertIn("Adam pracuje…", HUMAN_ADAM_HTML)
        self.assertIn("Doručení potvrzeno", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/status", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/connect", HUMAN_ADAM_HTML)
        self.assertIn("payload.workspace_synced", HUMAN_ADAM_HTML)
        self.assertIn("Workspace byl bezpečně aktualizovaný z main", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/profile", HUMAN_ADAM_HTML)
        self.assertNotIn("/api/human-adam/context-anchor", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/thread-rotation", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/send", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/tvbcp", HUMAN_ADAM_HTML)
        self.assertIn("TVBCP se načte až po otevření.", HUMAN_ADAM_HTML)
        self.assertIn("Workspace: ${workspace.change_count} změn", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/workspace", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/checkpoint", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/deploy-audit", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/deploy", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/transcribe", HUMAN_ADAM_HTML)
        self.assertIn("Audit nasazení", HUMAN_ADAM_HTML)
        self.assertIn("Ověřit a nasadit", HUMAN_ADAM_HTML)
        self.assertIn("Nasazeno a ověřeno", HUMAN_ADAM_HTML)
        self.assertIn('id="deployConfirmation"', HUMAN_ADAM_HTML)
        self.assertIn('autocomplete="off"', HUMAN_ADAM_HTML)
        self.assertIn('autocorrect="off"', HUMAN_ADAM_HTML)
        self.assertIn("window.confirm", HUMAN_ADAM_HTML)
        self.assertIn("checkpointMessage.blur();", HUMAN_ADAM_HTML)
        self.assertIn("const checkpointTitle = checkpointMessage.value.trim();", HUMAN_ADAM_HTML)
        self.assertIn("Zadej krátký název WIP checkpointu.", HUMAN_ADAM_HTML)
        self.assertIn("message:checkpointTitle", HUMAN_ADAM_HTML)
        self.assertLess(
            HUMAN_ADAM_HTML.index("const checkpointTitle = checkpointMessage.value.trim();"),
            HUMAN_ADAM_HTML.index("window.confirm", HUMAN_ADAM_HTML.index("async function createCheckpoint()")),
        )
        self.assertIn("body:JSON.stringify({confirmation})", HUMAN_ADAM_HTML)
        self.assertNotIn("checkpoint_token:deploymentAudit.checkpoint_token", HUMAN_ADAM_HTML)
        self.assertIn("confirmation.trim() !== required", HUMAN_ADAM_HTML)
        self.assertIn("const confirmation = deployConfirmation.value.trim();", HUMAN_ADAM_HTML)
        self.assertIn('deployConfirmation.addEventListener("input"', HUMAN_ADAM_HTML)
        self.assertNotIn("window.prompt", HUMAN_ADAM_HTML)
        failure = HUMAN_ADAM_HTML.index("const deploymentFailure =")
        refresh = HUMAN_ADAM_HTML.index("await loadWork();", failure)
        restore = HUMAN_ADAM_HTML.index("deployMeta.textContent = deploymentFailure;", refresh)
        self.assertLess(refresh, restore)
        self.assertIn("await waitForCockpitAndReload(Number(payload.restart.pid || previousPid));", HUMAN_ADAM_HTML)
        verification = HUMAN_ADAM_HTML.index('api("/api/human-adam/deploy-verification"')
        stored = HUMAN_ADAM_HTML.index("storeVerifiedDeploymentResult(verification)", verification)
        reload_page = HUMAN_ADAM_HTML.index("window.location.reload();", verification)
        self.assertLess(verification, stored)
        self.assertLess(stored, reload_page)
        self.assertNotIn(
            "if (!storeVerifiedDeploymentResult(verification)) return;",
            HUMAN_ADAM_HTML,
        )
        self.assertIn('verification.state !== "deployed"', HUMAN_ADAM_HTML)

    def test_verified_deployment_survives_reload_and_reopens_work_panel_once(self) -> None:
        store_start = HUMAN_ADAM_HTML.index("function storeVerifiedDeploymentResult(payload)")
        restore_end = HUMAN_ADAM_HTML.index("async function deployCheckpoint()", store_start)
        source = HUMAN_ADAM_HTML[store_start:restore_end]
        restore_start = source.index("async function restoreVerifiedDeploymentResult()")
        restore_source = source[restore_start:]

        self.assertIn("window.sessionStorage.setItem", source)
        self.assertIn("window.sessionStorage.getItem", source)
        self.assertIn("window.sessionStorage.removeItem", source)
        self.assertNotIn("localStorage", source)
        self.assertIn("verifiedDeploymentMaxAgeMs", source)
        self.assertIn("payload && payload.recent_simple_main_deployment", source)
        self.assertIn("verifiedDeploymentSeenStorageKey", source)
        self.assertIn("let statusPayload = await loadStatus();", restore_source)
        self.assertIn("recentServerDeploymentRecord(statusPayload)", restore_source)
        reconnect = restore_source.index(
            "await reconnectAfterVerifiedDeployment(statusPayload)"
        )
        no_record = restore_source.index("if (!record) return;")
        self.assertLess(no_record, reconnect)
        self.assertIn("workPanel.hidden = false;", restore_source)
        loaded = restore_source.index("await loadWork();")
        confirmed = restore_source.index(
            "deployMeta.textContent = verifiedDeploymentSummary(record)"
        )
        self.assertLess(reconnect, loaded)
        self.assertLess(loaded, confirmed)
        self.assertIn("Human–Adam je znovu připojený.", restore_source)
        self.assertIn("restoreVerifiedDeploymentResult();", HUMAN_ADAM_HTML)
        self.assertIn("main ${record.main_short}", HUMAN_ADAM_HTML)
        self.assertIn("${record.test_count} testů", HUMAN_ADAM_HTML)
        self.assertIn("smoke ${record.smoke_count}/5", HUMAN_ADAM_HTML)
        startup = HUMAN_ADAM_HTML[HUMAN_ADAM_HTML.rindex("clearMessageInput();"):]
        self.assertNotIn("\n  loadStatus();", startup)

    def test_verified_deployment_reconnect_is_narrow_and_fail_closed(self) -> None:
        uncertainty_start = HUMAN_ADAM_HTML.index(
            "function hasCurrentUncertainDelivery(messages)"
        )
        guard_start = HUMAN_ADAM_HTML.index(
            "function safePostDeploymentReconnectStatus(payload)"
        )
        restore_start = HUMAN_ADAM_HTML.index(
            "async function restoreVerifiedDeploymentResult()",
            guard_start,
        )
        uncertainty_source = HUMAN_ADAM_HTML[uncertainty_start:guard_start]
        source = HUMAN_ADAM_HTML[guard_start:restore_start]

        self.assertIn(
            "for (let index = rows.length - 1; index >= 0; index -= 1)",
            uncertainty_source,
        )
        completed = uncertainty_source.index('status === "completed"')
        pending = uncertainty_source.index('status === "pending"')
        unknown = uncertainty_source.index('status === "delivery_unknown"')
        recovery = uncertainty_source.index("item.recovery_required === true")
        self.assertLess(completed, pending)
        self.assertLess(completed, unknown)
        self.assertLess(completed, recovery)
        self.assertNotIn(".some(", uncertainty_source)
        self.assertIn("payload.runtime.reachable !== true", source)
        self.assertIn('String(session.connection_state || "") === "disconnected"', source)
        self.assertIn("session.turn_busy !== true", source)
        self.assertIn("!session.active_turn", source)
        self.assertIn(
            "hasCurrentUncertainDelivery(session.messages)",
            source,
        )
        self.assertIn('api("/api/human-adam/connect"', source)
        self.assertIn("renderStatus(payload);", source)
        self.assertIn("finally {", source)
        self.assertIn("setBusy(false);", source)
        self.assertIn(
            "Nasazení je dokončené, ale Human–Adam se nepodařilo znovu připojit",
            source,
        )

    def test_thread_rotation_ui_requires_audit_exact_phrase_and_preserves_old_thread(self) -> None:
        audit_start = HUMAN_ADAM_HTML.index("async function auditThreadRotation()")
        audit_end = HUMAN_ADAM_HTML.index("async function rotateProfileThread()", audit_start)
        audit_source = HUMAN_ADAM_HTML[audit_start:audit_end]
        rotate_end = HUMAN_ADAM_HTML.index("async function loadTvbcp", audit_end)
        rotate_source = HUMAN_ADAM_HTML[audit_end:rotate_end]

        self.assertIn('api("/api/human-adam/thread-rotation")', audit_source)
        self.assertIn("Ověřuji připojení, stav tahu a doručení", audit_source)
        self.assertIn("zkontroluj připojení a stav relace", HUMAN_ADAM_HTML)
        self.assertNotIn("Ověřuji připnutý kontext", audit_source)
        self.assertNotIn("zkontroluj připojení a aktivní kontext", HUMAN_ADAM_HTML)
        self.assertIn('api("/api/human-adam/thread-rotation", {', rotate_source)
        self.assertIn("confirmation !== required", rotate_source)
        self.assertIn("expected_thread_id:expectedThreadId", rotate_source)
        self.assertIn("payload.previous_thread_preserved !== true", rotate_source)
        self.assertIn("bez odeslání zprávy", rotate_source)
        self.assertNotIn("context_anchor_revision", HUMAN_ADAM_HTML)
        self.assertNotIn("auditedAnchorRevision", HUMAN_ADAM_HTML)
        self.assertNotIn("Aktivní kontext se změnil. Před rotací", HUMAN_ADAM_HTML)
        self.assertNotIn("contextAnchorDraftDirty", audit_source)
        self.assertNotIn("contextAnchorDraftDirty", rotate_source)
        self.assertIn("staré vlákno se nemaže ani nearchivuje", HUMAN_ADAM_HTML.casefold())
        self.assertIn('threadRotationConfirmation.addEventListener("input", syncControls)', HUMAN_ADAM_HTML)
        self.assertNotIn("window.prompt", rotate_source)

    def test_thread_rotation_has_an_independent_accessible_panel(self) -> None:
        panel_start = HUMAN_ADAM_HTML.index('id="threadRotationPanel"')
        panel_end = HUMAN_ADAM_HTML.index("</aside>", panel_start)
        panel_source = HUMAN_ADAM_HTML[panel_start:panel_end]

        self.assertIn(
            'aria-label="Bezpečná rotace profilového vlákna"',
            panel_source,
        )
        self.assertIn("Nové profilové vlákno", panel_source)
        self.assertIn("Rotaci použij", panel_source)
        self.assertIn(
            "handoffu, TVBCP a krátkého aktuálního kontextu",
            panel_source,
        )
        self.assertIn(
            "Staré vlákno zůstane zachované a nearchivované",
            panel_source,
        )
        self.assertIn('id="threadRotationAuditBtn"', panel_source)
        self.assertIn('id="threadRotationBtn"', panel_source)
        self.assertNotIn("Kotva", panel_source)
        self.assertNotIn("Plán", panel_source)
        self.assertIn(
            'threadRotationOpenBtn.addEventListener("click", openThreadRotation);',
            HUMAN_ADAM_HTML,
        )
        self.assertIn(
            'threadRotationCloseBtn.addEventListener("click", closeThreadRotation);',
            HUMAN_ADAM_HTML,
        )

    def test_mobile_summary_collapses_core_details_without_hiding_deployment_evidence(self) -> None:
        header = HUMAN_ADAM_HTML.index("<header>")
        summary = HUMAN_ADAM_HTML.index('id="mobileStatusSummary"', header)
        details = HUMAN_ADAM_HTML.index('id="statusDetails"', summary)
        badges = HUMAN_ADAM_HTML.index('<div class="statusline">', details)
        turn = HUMAN_ADAM_HTML.index('id="turnActivity"', badges)
        receipt = HUMAN_ADAM_HTML.index('id="deploymentReceipt"', turn)

        self.assertLess(summary, details)
        self.assertLess(details, badges)
        self.assertLess(badges, turn)
        self.assertLess(turn, receipt)
        self.assertIn('aria-expanded="false" aria-controls="statusDetails"', HUMAN_ADAM_HTML)
        self.assertIn("#mobileStatusSummary { display:none;", HUMAN_ADAM_HTML)
        self.assertIn("#mobileStatusSummary { display:flex; }", HUMAN_ADAM_HTML)

        self.assertIn(".status-details { display:none; }", HUMAN_ADAM_HTML)
        self.assertIn(".status-details.expanded { display:block; }", HUMAN_ADAM_HTML)

        summary_start = HUMAN_ADAM_HTML.index("function updateMobileStatusSummary()")
        summary_end = HUMAN_ADAM_HTML.index("function elapsedClock", summary_start)
        summary_source = HUMAN_ADAM_HTML[summary_start:summary_end]
        self.assertIn('text = turnActivity.textContent || "Adam pracuje', summary_source)
        self.assertIn('text = "Stav doručení je nejistý · obnov stav · pokyn neposílej znovu";', summary_source)
        self.assertIn('const adamText = sessionConnected ? "Adam čeká" : "Adam není připojen";', summary_source)
        self.assertIn('text = `${activeWorkstreamLabel} · ${connectionText} · ${workspaceText} · ${adamText}`;', summary_source)
        self.assertIn('mobileStatusSummary.setAttribute("aria-expanded"', HUMAN_ADAM_HTML)
        self.assertIn('mobileStatusToggleText.textContent = showDetails ? "Skrýt" : "Podrobnosti";', HUMAN_ADAM_HTML)
        self.assertIn('mobileStatusSummary.addEventListener("click"', HUMAN_ADAM_HTML)
        self.assertIn("updateMobileStatusSummary();\n    turnTimerId", HUMAN_ADAM_HTML)

    def test_diverged_workspace_keeps_preserved_wip_visible_but_blocks_audit(self) -> None:
        self.assertIn('workspace.workspace_relation === "diverged"', HUMAN_ADAM_HTML)
        self.assertIn("WIP zachován: ${workspace.local_commit_count} · nutná obnova", HUMAN_ADAM_HTML)
        self.assertIn("WIP checkpoint je zachovaný:", HUMAN_ADAM_HTML)
        self.assertIn("WIP je bezpečně zachovaný, ale audit je zablokovaný.", HUMAN_ADAM_HTML)
        self.assertIn('payload.workspace_relation === "aligned"', HUMAN_ADAM_HTML)
        self.assertIn("deployAuditBtn.disabled = !simpleDeployReady;", HUMAN_ADAM_HTML)
        self.assertLess(
            HUMAN_ADAM_HTML.index("else if (checkpointPreserved) workMeta.textContent"),
            HUMAN_ADAM_HTML.index('else workMeta.textContent = "Workspace je čistý a odpovídá main.";'),
        )

    def test_pending_integration_audit_is_read_only_and_fail_closed_in_work_panel(
        self,
    ) -> None:
        render_start = HUMAN_ADAM_HTML.index(
            "function renderPendingIntegrationAudit(audit)"
        )
        render_end = HUMAN_ADAM_HTML.index(
            "async function integrateDeferredChanges()", render_start
        )
        source = HUMAN_ADAM_HTML[render_start:render_end]

        self.assertIn("pending_integration_audit", HUMAN_ADAM_HTML)
        self.assertIn("waiting_source_clean", source)
        self.assertIn("ready_for_confirmed_integration", HUMAN_ADAM_HTML)
        self.assertIn("source_advanced_service_decision", source)
        self.assertIn('integrationAuditBox.classList.add("blocked");', source)
        self.assertLess(
            source.index('state === "ready_for_confirmed_integration"'),
            source.index('integrationAuditBox.classList.add("ready");'),
        )
        self.assertIn("servisní rozhodnutí je přesto povinné", source)
        self.assertIn("audit.overlap_paths", source)
        self.assertNotIn('method:"POST"', source)
        self.assertNotIn("fetch(", source)
        self.assertIn(
            "Při posunu <code>main</code>, cizím WIP, divergenci nebo neshodě markeru "
            "nic nezačleňuj a vyžádej servisní rozhodnutí",
            HUMAN_ADAM_HTML,
        )

    def test_deferred_integration_button_requires_verified_marker_and_exact_phrase(
        self,
    ) -> None:
        render_start = HUMAN_ADAM_HTML.index(
            "function renderPendingIntegrationAudit(audit)"
        )
        render_end = HUMAN_ADAM_HTML.index(
            "async function integrateDeferredChanges()", render_start
        )
        render_source = HUMAN_ADAM_HTML[render_start:render_end]
        integrate_start = render_end
        integrate_end = HUMAN_ADAM_HTML.index(
            "function renderMainRemoteSyncAudit(audit", integrate_start
        )
        integrate_source = HUMAN_ADAM_HTML[integrate_start:integrate_end]

        self.assertIn('state === "ready_for_confirmed_integration"', render_source)
        self.assertIn("audit.can_integrate === true", render_source)
        self.assertIn("audit.ownership_marker_verified === true", render_source)
        self.assertIn("integrationBtn.hidden = !canIntegrate;", render_source)
        self.assertIn("integrationBtn.disabled = true;", render_source)
        self.assertIn(
            'api("/api/human-adam/deferred-integration"',
            integrate_source,
        )
        self.assertIn('method:"POST"', integrate_source)
        self.assertIn("body:JSON.stringify({confirmation})", integrate_source)
        self.assertIn("confirmation !== required", integrate_source)
        self.assertIn("Nasazení zůstává samostatný krok", integrate_source)
        self.assertNotIn("merge", integrate_source.casefold())
        self.assertNotIn("rebase", integrate_source.casefold())
        self.assertNotIn("reset", integrate_source.casefold())
        self.assertIn(
            'integrationConfirmation.addEventListener("input"',
            HUMAN_ADAM_HTML,
        )
        self.assertIn(
            'integrationBtn.addEventListener("click", integrateDeferredChanges);',
            HUMAN_ADAM_HTML,
        )

    def test_work_button_is_compact_and_opens_detail_only_when_needed(self) -> None:
        compact_start = HUMAN_ADAM_HTML.index("function workspaceRequiresWorkDetail(workspace)")
        compact_end = HUMAN_ADAM_HTML.index("function renderStatus(payload)", compact_start)
        compact_source = HUMAN_ADAM_HTML[compact_start:compact_end]
        load_start = HUMAN_ADAM_HTML.index("async function loadWork()")
        open_start = HUMAN_ADAM_HTML.index("async function openWork()", load_start)
        open_end = HUMAN_ADAM_HTML.index("function setWorkHelpOpen(open)", open_start)
        load_source = HUMAN_ADAM_HTML[load_start:open_start]
        open_source = HUMAN_ADAM_HTML[open_start:open_end]

        self.assertIn('<button id="workOpenBtn" type="button">Práce: stav</button>', HUMAN_ADAM_HTML)
        self.assertIn("#workOpenBtn.work-clean", HUMAN_ADAM_HTML)
        self.assertIn("#workOpenBtn.work-attention", HUMAN_ADAM_HTML)
        for marker in (
            "workspace.ok === false",
            "workspace.prepared === false",
            "workspace.ready === false",
            "workspace.has_git_remote",
            "workspace.dirty",
            "workspace.sync_available",
            "workspace.source_update_available",
            "Number(workspace.source_pending_changes || 0) > 0",
            "workspace.local_checkpoint_ahead",
            "workspace.local_checkpoint_preserved",
            'relation !== "aligned"',
        ):
            self.assertIn(marker, compact_source)
        self.assertIn('workOpenBtn.textContent = "Práce: čistá";', compact_source)
        self.assertIn('workOpenBtn.textContent = "Práce: kontrola";', compact_source)
        self.assertIn('workOpenBtn.textContent = "Práce: nasazení";', compact_source)
        self.assertIn("`Práce: ${changeCount} změn`", compact_source)
        self.assertIn('workOpenBtn.setAttribute("aria-label", workOpenBtn.title);', compact_source)
        self.assertGreaterEqual(HUMAN_ADAM_HTML.count("renderCompactWorkStatus("), 3)
        self.assertIn("return payload;", load_source)
        self.assertIn("return null;", load_source)
        self.assertIn(
            "const showDetail = !payload || workspaceRequiresWorkDetail(payload) || workstreamDeploymentEnabled;",
            open_source,
        )
        self.assertIn("if (!showDetail)", open_source)
        self.assertIn("Práce je čistá a synchronní s main. Detail není potřeba.", open_source)
        self.assertLess(open_source.index("if (!showDetail)"), open_source.index("workPanel.hidden = false;"))
        self.assertNotIn('method:"POST"', open_source)

    def test_work_panel_renders_shared_read_only_live_status_fail_closed(
        self,
    ) -> None:
        render_start = HUMAN_ADAM_HTML.index(
            "function renderWorkstreamLiveStatus(liveStatus)"
        )
        render_end = HUMAN_ADAM_HTML.index(
            "function renderHandoffProposal(",
            render_start,
        )
        render_source = HUMAN_ADAM_HTML[render_start:render_end]
        work_start = HUMAN_ADAM_HTML.index("function renderWork(payload)")
        work_end = HUMAN_ADAM_HTML.index(
            "const LIVE_WORK_STATUS_LABELS",
            work_start,
        )
        work_source = HUMAN_ADAM_HTML[work_start:work_end]

        self.assertIn("liveStatus.read_only === true", render_source)
        self.assertIn("liveStatus.writes_performed === false", render_source)
        self.assertIn(
            'String(liveStatus.workstream_id || "") === activeWorkstreamId',
            render_source,
        )
        self.assertIn('overallState = valid ? String(status.state || "unverified") : "unverified"', render_source)
        self.assertIn("liveWorkStatusMeta.textContent", render_source)
        self.assertIn("liveWorkStatusAxes.replaceChildren()", render_source)
        self.assertIn('document.createElement("li")', render_source)
        self.assertIn("row.textContent = text", render_source)
        self.assertNotIn("innerHTML", render_source)
        self.assertNotIn('method:"POST"', render_source)
        self.assertIn(
            "renderWorkstreamLiveStatus(payload.workstream_live_status || null)",
            work_source,
        )
        self.assertIn(
            "renderWorkstreamLiveStatus(null)",
            HUMAN_ADAM_HTML,
        )
        for label in (
            "Shodné s GitHubem",
            "Ověřeno pro tento main",
            "Čisté a zarovnané",
            "Nejisté doručení",
            "Neověřeno",
        ):
            self.assertIn(label, HUMAN_ADAM_HTML)

    def test_development_semaphore_ui_is_explicit_and_blocks_write_actions(self) -> None:
        for element_id in (
            "developmentBadge",
            "developmentSemaphoreMeta",
            "developmentTopic",
            "developmentProject",
            "developmentHandoff",
            "developmentAcquireProfileBtn",
            "developmentAcquireTerminalBtn",
            "developmentPauseBtn",
            "developmentResumeBtn",
            "developmentReleaseBtn",
            "projectContinuityAuditBtn",
            "projectContinuityMeta",
            "projectContinuityReasons",
            "handoffProposalBox",
            "handoffProposalMeta",
            "handoffProposalDraft",
        ):
            self.assertIn(f'id="{element_id}"', HUMAN_ADAM_HTML)
        self.assertIn('api("/api/human-adam/development-semaphore"', HUMAN_ADAM_HTML)
        self.assertIn('api("/api/human-adam/project-continuity")', HUMAN_ADAM_HTML)
        self.assertIn("expected_revision:Number(developmentSemaphore.revision)", HUMAN_ADAM_HTML)
        self.assertIn("project_id:projectId,handoff_path:handoffPath", HUMAN_ADAM_HTML)
        self.assertIn("Vyber projekt a jeho aktuální handoff.", HUMAN_ADAM_HTML)
        self.assertIn("checkpointBtn.disabled = !workstreamDevelopmentEnabled || !payload.dirty || semaphore.can_checkpoint !== true;", HUMAN_ADAM_HTML)
        self.assertIn("deployAuditBtn.hidden = !workstreamDeploymentEnabled;", HUMAN_ADAM_HTML)
        self.assertIn("deployAuditBtn.disabled = !simpleDeployReady;", HUMAN_ADAM_HTML)
        self.assertIn(
            "Tento pracovní proud je pouze pro čtení; vývoj zde zatím není povolen.",
            HUMAN_ADAM_HTML,
        )
        self.assertIn("workstreamDeploymentEnabled = capabilities.deployment !== false;", HUMAN_ADAM_HTML)
        self.assertIn("const simpleDeployReady = workstreamDeploymentEnabled", HUMAN_ADAM_HTML)
        self.assertIn("deployBtn.hidden = !workstreamDeploymentEnabled;", HUMAN_ADAM_HTML)
        self.assertIn(
            "Vývoj spusť tlačítkem Zahájit vývoj. Po úspěšném tahu se změny automaticky checkpointují, commitnou a pushnou; nasazení z tohoto pracovního proudu zatím není dostupné.",
            HUMAN_ADAM_HTML,
        )
        self.assertNotIn("MMTX pilot", HUMAN_ADAM_HTML)
        self.assertNotIn("semaphore.can_deploy", HUMAN_ADAM_HTML)
        self.assertIn("To projde jen při čistých workspaces bez čekajícího WIP", HUMAN_ADAM_HTML)

    def test_project_continuity_ui_is_read_only_and_non_blocking(self) -> None:
        start = HUMAN_ADAM_HTML.index("async function loadProjectContinuity()")
        end = HUMAN_ADAM_HTML.index("async function openWork()", start)
        source = HUMAN_ADAM_HTML[start:end]

        self.assertIn('api("/api/human-adam/project-continuity")', source)
        self.assertNotIn('method:"POST"', source)
        self.assertIn("Nelze ověřit", HUMAN_ADAM_HTML)
        self.assertIn("pouze read-only, nic neblokuje", HUMAN_ADAM_HTML)

    def test_handoff_proposal_ui_is_large_read_only_and_has_no_write_action(self) -> None:
        start = HUMAN_ADAM_HTML.index("function renderHandoffProposal(proposal)")
        end = HUMAN_ADAM_HTML.index("function renderDevelopmentSemaphore", start)
        source = HUMAN_ADAM_HTML[start:end]

        self.assertIn('aria-label="Read-only návrh aktualizace handoffu"', HUMAN_ADAM_HTML)
        self.assertIn("Návrh handoffu po checkpointu", HUMAN_ADAM_HTML)
        self.assertIn("proposal.draft", source)
        self.assertIn("textContent", source)
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("api(", source)
        self.assertNotIn("fetch(", source)
        self.assertNotIn("method:\"POST\"", source)
        self.assertNotIn("handoffProposalSaveBtn", HUMAN_ADAM_HTML)
        self.assertNotIn("max-height", HUMAN_ADAM_HTML[HUMAN_ADAM_HTML.index(".handoff-proposal-box"):HUMAN_ADAM_HTML.index(".checkpoint-box")])
        self.assertIn('handoffProposalBox.scrollIntoView({block:"nearest",behavior:"smooth"});', HUMAN_ADAM_HTML)

    def test_takeover_handoff_check_is_visible_read_only_and_does_not_block_deploy(self) -> None:
        render_start = HUMAN_ADAM_HTML.index("function renderDeploymentAudit(payload)")
        render_end = HUMAN_ADAM_HTML.index("async function auditDeployment()", render_start)
        source = HUMAN_ADAM_HTML[render_start:render_end]

        self.assertIn('id="handoffTakeoverCheck"', HUMAN_ADAM_HTML)
        self.assertIn("payload.handoff_takeover_check", source)
        self.assertIn("function renderHandoffTakeoverCheck(check)", source)
        self.assertIn("handoffTakeoverCheck.textContent", source)
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("api(", source)
        self.assertNotIn("fetch(", source)
        self.assertIn("Pouze varování; nasazení zatím neblokuje", source)
        self.assertIn("deployConfirmation.disabled = false;", source)
        self.assertIn("deployBtn.disabled = true;", source)
        self.assertNotIn("check.blocking", source)

    def test_orphaned_deployment_completion_ui_is_absent(self) -> None:
        self.assertNotIn("/api/human-adam/deployment-completion", HUMAN_ADAM_HTML)
        self.assertNotIn("deploymentcompletion", HUMAN_ADAM_HTML.casefold())
        self.assertNotIn("deployment-completion-box", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/deploy-verification", HUMAN_ADAM_HTML)

    def test_development_branch_lifecycle_ui_is_absent(self) -> None:
        self.assertNotIn("/api/human-adam/development-branches", HUMAN_ADAM_HTML)
        self.assertNotIn("developmentBranchAudit", HUMAN_ADAM_HTML)
        self.assertNotIn("development-branch-audit", HUMAN_ADAM_HTML)
        self.assertNotIn("Životní cyklus WIP větví", HUMAN_ADAM_HTML)

    def test_work_help_is_accessible_static_and_describes_simple_main_workflow(self) -> None:
        work_panel_start = HUMAN_ADAM_HTML.index('id="workPanel"')
        body_start = HUMAN_ADAM_HTML.index('class="work-panel-body"', work_panel_start)
        panel_start = HUMAN_ADAM_HTML.index('id="workHelpPanel"')
        panel_end = HUMAN_ADAM_HTML.index("</section>", panel_start)
        panel_source = HUMAN_ADAM_HTML[panel_start:panel_end]
        toggle_start = HUMAN_ADAM_HTML.index("function setWorkHelpOpen(open)")
        toggle_end = HUMAN_ADAM_HTML.index("function closeWork()", toggle_start)
        toggle_source = HUMAN_ADAM_HTML[toggle_start:toggle_end]

        self.assertIn('aria-label="Nápověda k jednoduchému vývoji a nasazení"', HUMAN_ADAM_HTML)
        self.assertIn('aria-controls="workHelpPanel"', HUMAN_ADAM_HTML)
        self.assertLess(body_start, panel_start)
        self.assertIn(".work-panel-body { flex:1; min-height:0; overflow:auto; display:flex; flex-direction:column; }", HUMAN_ADAM_HTML)
        self.assertIn(".work-help-panel { flex:0 0 auto; margin:12px 16px; }", HUMAN_ADAM_HTML)
        self.assertNotIn(".work-help-panel { flex:0 1 auto; max-height", HUMAN_ADAM_HTML)
        self.assertIn("Jak pracovat a nasazovat", panel_source)
        self.assertIn('class="simple-work-help"', panel_source)
        self.assertIn("Běžný vývoj", panel_source)
        self.assertIn("Zahájit vývoj", panel_source)
        self.assertIn("Platí pouze pro následující odeslaný pokyn", panel_source)
        self.assertIn("Nový projekt, tool nebo layer se zakládá pouze v terminálovém dialogu s Adamem", panel_source)
        self.assertNotIn("<strong>Knihovna:</strong>", panel_source)
        self.assertIn('id="privateArchiveHelp" hidden', panel_source)
        self.assertIn("Soukromý archiv aktivního proudu", panel_source)
        self.assertIn(
            "privateArchiveHelp.hidden = capabilities.private_archive_direct !== true;",
            HUMAN_ADAM_HTML,
        )
        self.assertIn("Při běžném čistém a zarovnaném <code>main</code>", panel_source)
        self.assertIn("jeden commit přímo v <code>main</code>", panel_source)
        self.assertIn("tah zůstane bezpečně odložený bez commitu a pushnutí", panel_source)
        self.assertIn("read-only audit čekající integrace", panel_source)
        self.assertIn("denní soví workflow vytvořilo nový commit", panel_source)
        self.assertIn("dorovnání se nespouští automaticky", panel_source)
        self.assertIn("Převzít přesný WIP do main", panel_source)
        self.assertIn("private ownership marker odpovídá přesnému WIP", panel_source)
        self.assertIn("cizím WIP, divergenci nebo neshodě markeru", panel_source)
        self.assertIn("Nasazení", panel_source)
        self.assertIn("Nasazovací tlačítka se zobrazí jen u pracovního proudu", panel_source)
        self.assertIn("Audit nasazení", panel_source)
        self.assertIn("Nasazeno a ověřeno", panel_source)
        self.assertIn("reset, rebase ani force push", panel_source)
        self.assertIn("Toto je pouze nápověda", panel_source)
        self.assertNotIn("#workHelpPanel > :not(.workflow-help-head):not(.simple-work-help)", HUMAN_ADAM_HTML)
        self.assertNotIn("Vývojový semafor", panel_source)
        self.assertNotIn("WIP větev", panel_source)
        self.assertNotIn("takeover", panel_source.casefold())
        self.assertNotIn("developmentAcquireProfileBtn", panel_source)
        self.assertNotIn("developmentAcquireTerminalBtn", panel_source)
        self.assertNotIn("developmentBranchAuditBtn", panel_source)
        self.assertNotIn("api(", toggle_source)
        self.assertNotIn("fetch(", toggle_source)
        self.assertIn('workHelpBtn.setAttribute("aria-expanded"', toggle_source)
        self.assertIn('workHelpBtn.addEventListener("click"', HUMAN_ADAM_HTML)
        self.assertIn('workHelpCloseBtn.addEventListener("click"', HUMAN_ADAM_HTML)

    def test_legacy_work_controls_are_kept_only_as_hidden_compatibility_layer(self) -> None:
        self.assertIn(".legacy-work-control { display:none !important; }", HUMAN_ADAM_HTML)
        for marker in (
            'class="badge warn legacy-work-control" id="developmentBadge"',
            'class="development-semaphore-box legacy-work-control"',
            'class="project-continuity-box legacy-work-control"',
            'class="handoff-proposal-box legacy-work-control"',
            'class="legacy-work-control" id="checkpointMessage"',
            'class="primary legacy-work-control" id="checkpointBtn"',
            'class="legacy-work-control" id="handoffTakeoverCheck"',
        ):
            self.assertIn(marker, HUMAN_ADAM_HTML)

    def test_profile_switch_is_explicit_atomic_and_preserves_unsent_draft(self) -> None:
        render_start = HUMAN_ADAM_HTML.index("function renderWorkstreams(payload)")
        switch_start = HUMAN_ADAM_HTML.index("async function switchProfile()")
        switch_end = HUMAN_ADAM_HTML.index("function scrollTvbcpToEnd", switch_start)
        render_source = HUMAN_ADAM_HTML[render_start:switch_start]
        source = HUMAN_ADAM_HTML[switch_start:switch_end]

        self.assertIn("payload.workstream_selection", render_source)
        self.assertIn("selection.workstreams", render_source)
        self.assertIn("selection.groups", render_source)
        self.assertIn("selection.paused", render_source)
        self.assertIn('document.createElement("optgroup")', render_source)
        self.assertIn('optionGroup.label = "Pozastavené"', render_source)
        self.assertIn("activeWorkstream.workstream_id", render_source)
        self.assertIn("profile.name", render_source)
        self.assertIn("profile.backend", render_source)
        self.assertNotIn("payload.work_profile", render_source)
        self.assertNotIn("payload.work_profiles", render_source)
        self.assertNotIn("usingWorkstreamCatalog", render_source)
        self.assertIn("if (input.value.trim())", source)
        self.assertIn("proud jsem nepřepnul", source)
        self.assertIn("Přepnout pracovní proud", source)
        self.assertIn("handoff a TVBCP", source)
        self.assertIn("workspace se předem ověří a synchronizuje", source)
        self.assertIn('api("/api/human-adam/profile"', source)
        self.assertIn("{workstream_id:targetId,confirmed:true}", source)
        self.assertNotIn("{profile_id:targetId,confirmed:true}", source)
        self.assertNotIn("contextAnchorDraftDirty", source)
        self.assertIn("threadRotationPanel.hidden = true;", source)
        self.assertIn("resetThreadRotationState();", source)
        self.assertIn("showProfileSwitchFailure", source)
        self.assertIn('<label for="profileSelect">Pracovní proud</label>', HUMAN_ADAM_HTML)
        self.assertIn('notice.scrollIntoView({block:"nearest",behavior:"smooth"});', HUMAN_ADAM_HTML)
        self.assertIn('profileSelect.addEventListener("change", syncControls);', HUMAN_ADAM_HTML)
        self.assertIn('profileSwitchBtn.addEventListener("click", switchProfile);', HUMAN_ADAM_HTML)

    def test_uninitialized_lazy_tvbcp_is_marked_read_only(self) -> None:
        load_start = HUMAN_ADAM_HTML.index("async function loadTvbcp()")
        load_end = HUMAN_ADAM_HTML.index("function openTvbcp()", load_start)
        source = HUMAN_ADAM_HTML[load_start:load_end]

        self.assertIn("payload.initialized === false", source)
        self.assertIn("Dosud neinicializováno · pouze pro čtení", source)
        self.assertIn("tvbcpContent.textContent = payload.content", source)

    def test_context_anchor_editor_and_mutation_ui_are_removed(self) -> None:
        for removed in (
            'id="contextAnchorOpenBtn"',
            'id="contextAnchorPanel"',
            'id="contextAnchorInput"',
            'id="contextAnchorProposeBtn"',
            'id="contextAnchorSaveBtn"',
            'id="contextAnchorPinBtn"',
            'id="contextAnchorPauseBtn"',
            'id="contextAnchorDeleteBtn"',
            'id="planHelpPanel"',
            "changeContextAnchor",
            "loadContextAnchor",
            "proposeContextAnchor",
            "contextAnchorDraftDirty",
            "CONTEXT_ANCHOR_PROPOSAL_PROMPT",
            "/api/human-adam/context-anchor",
            ".context-anchor-body",
            ".context-anchor-actions",
            'id="contextAnchorBadge"',
            "renderContextAnchorBadge",
            "context_anchor_warning",
            "Starší kontext:",
        ):
            self.assertNotIn(removed, HUMAN_ADAM_HTML)

    def test_send_and_status_ui_no_longer_consume_context_anchor_state(self) -> None:
        status_start = HUMAN_ADAM_HTML.index("function renderStatus(payload)")
        status_end = HUMAN_ADAM_HTML.index(
            "function renderDevelopmentBadge",
            status_start,
        )
        status_source = HUMAN_ADAM_HTML[status_start:status_end]
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]

        self.assertNotIn("context_anchor", status_source)
        self.assertNotIn("context_anchor", send_source)
        self.assertIn(
            'notice.textContent = "Odpověď doručena a potvrzena.";',
            send_source,
        )

    def test_composer_places_voice_left_and_send_right_in_one_compact_row(self) -> None:
        actions_start = HUMAN_ADAM_HTML.index('<div class="compose-actions">')
        voice = HUMAN_ADAM_HTML.index('<div class="voice-controls">', actions_start)
        record = HUMAN_ADAM_HTML.index('id="voiceRecordBtn"', voice)
        status = HUMAN_ADAM_HTML.index('id="voiceStatus"', record)
        send = HUMAN_ADAM_HTML.index('id="sendBtn"', status)
        actions_end = HUMAN_ADAM_HTML.index("</div>", send)

        self.assertLess(actions_start, voice)
        self.assertLess(voice, record)
        self.assertLess(record, status)
        self.assertLess(status, send)
        self.assertLess(send, actions_end)
        self.assertIn(
            ".compose-actions { display:grid; grid-template-columns:auto minmax(0,1fr) auto;",
            HUMAN_ADAM_HTML,
        )
        self.assertIn("#voiceStatus { min-width:0; overflow:hidden;", HUMAN_ADAM_HTML)
        self.assertNotIn('class="hint"', HUMAN_ADAM_HTML)

    def test_one_turn_development_requires_visible_explicit_arming(self) -> None:
        controls_start = HUMAN_ADAM_HTML.index("function syncControls()")
        controls_end = HUMAN_ADAM_HTML.index("function setBusy(", controls_start)
        controls_source = HUMAN_ADAM_HTML[controls_start:controls_end]
        arm_start = HUMAN_ADAM_HTML.index("function armWriteIntent()")
        arm_end = HUMAN_ADAM_HTML.index("function setMobileStatusDetails", arm_start)
        arm_source = HUMAN_ADAM_HTML[arm_start:arm_end]
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index(
            'connectBtn.addEventListener("click", connect);', send_start
        )
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        self.assertIn(
            '<button id="writeIntentBtn" type="button" aria-pressed="false">Zahájit vývoj</button>',
            HUMAN_ADAM_HTML,
        )
        self.assertIn("let writeIntentArmed = false;", HUMAN_ADAM_HTML)
        self.assertIn("!sessionConnected || !workstreamDevelopmentEnabled", controls_source)
        self.assertIn("window.confirm", arm_source)
        self.assertIn("pouze pro následující pokyn", arm_source)
        self.assertIn("const writeIntent = writeIntentArmed;", send_source)
        self.assertIn("setWriteIntentArmed(false);", send_source)
        self.assertIn("write_intent:writeIntent", send_source)
        self.assertIn(
            'writeIntentBtn.addEventListener("click", armWriteIntent);',
            HUMAN_ADAM_HTML,
        )

    def test_work_help_shows_private_archive_guidance_only_from_capability(
        self,
    ) -> None:
        self.assertIn(
            "Před změnou kódu nebo projektových souborů",
            HUMAN_ADAM_HTML,
        )
        self.assertIn(
            "Soukromý archiv aktivního proudu",
            HUMAN_ADAM_HTML,
        )
        self.assertIn('id="privateArchiveHelp" hidden', HUMAN_ADAM_HTML)
        self.assertNotIn("<strong>Knihovna:</strong>", HUMAN_ADAM_HTML)
        self.assertIn(
            "privateArchiveHelp.hidden = capabilities.private_archive_direct !== true;",
            HUMAN_ADAM_HTML,
        )
        self.assertIn(
            "mazání, hromadné změny, odesílání ven a systémové zásahy",
            HUMAN_ADAM_HTML,
        )

    def test_ui_renders_persistent_safe_simple_main_deployment(self) -> None:
        self.assertIn("payload.last_simple_main_deployment", HUMAN_ADAM_HTML)
        self.assertIn("verifiedDeploymentRecord(", HUMAN_ADAM_HTML)
        self.assertIn(
            "`Nasazeno ${deployment.main_short} · ${deployment.test_count} testů · smoke ${deployment.smoke_count}/5 · ${formatTime(deployment.deployed_at)}`",
            HUMAN_ADAM_HTML,
        )
        self.assertIn("deploymentReceipt.hidden = !deployment;", HUMAN_ADAM_HTML)
        self.assertNotIn("payload.deployment_confirmation", HUMAN_ADAM_HTML)
        self.assertNotIn("payload.deployment_diagnostic", HUMAN_ADAM_HTML)

    def test_deployment_confirmation_stays_inside_sticky_header_below_badges(self) -> None:
        header = HUMAN_ADAM_HTML.index("<header>")
        badges = HUMAN_ADAM_HTML.index('<div class="statusline">', header)
        receipt = HUMAN_ADAM_HTML.index('id="deploymentReceipt"', badges)
        header_end = HUMAN_ADAM_HTML.index("</header>", receipt)
        notice = HUMAN_ADAM_HTML.index('id="notice"', header_end)

        self.assertLess(header, badges)
        self.assertLess(badges, receipt)
        self.assertLess(receipt, header_end)
        self.assertLess(header_end, notice)
        self.assertIn("header { position:sticky;", HUMAN_ADAM_HTML)
        self.assertIn("#deploymentReceipt { margin:8px 0 0; padding:6px 10px;", HUMAN_ADAM_HTML)

    def test_ui_has_no_legacy_deployment_diagnostic_surface(self) -> None:
        self.assertNotIn('id="deploymentDiagnostic"', HUMAN_ADAM_HTML)
        self.assertNotIn("renderDeploymentDiagnostic", HUMAN_ADAM_HTML)
        self.assertNotIn("deployment_diagnostic", HUMAN_ADAM_HTML)

    def test_deployment_actions_have_distinct_audit_and_apply_colors(self) -> None:
        self.assertIn(
            '<button class="audit-action" id="deployAuditBtn" type="button" disabled>',
            HUMAN_ADAM_HTML,
        )
        self.assertIn(
            '<button class="deploy-action" id="deployBtn" type="button" disabled>',
            HUMAN_ADAM_HTML,
        )
        self.assertIn("button.audit-action { background:#fbbf24;", HUMAN_ADAM_HTML)
        self.assertIn("button.deploy-action { background:var(--ok);", HUMAN_ADAM_HTML)

    def test_failed_deployment_audit_offers_general_confirmed_fast_forward(self) -> None:
        audit_start = HUMAN_ADAM_HTML.index("async function auditDeployment()")
        audit_end = HUMAN_ADAM_HTML.index(
            "async function waitForCockpitAndReload", audit_start
        )
        audit_source = HUMAN_ADAM_HTML[audit_start:audit_end]
        apply_start = HUMAN_ADAM_HTML.index("async function applyMainRemoteSync()")
        apply_end = HUMAN_ADAM_HTML.index("function renderWork(", apply_start)
        apply_source = HUMAN_ADAM_HTML[apply_start:apply_end]

        self.assertIn('id="mainSyncBox"', HUMAN_ADAM_HTML)
        self.assertIn('id="mainSyncBtn"', HUMAN_ADAM_HTML)
        self.assertIn("Dorovnat main s GitHubem", HUMAN_ADAM_HTML)
        self.assertIn('await auditMainRemoteSync(error.message);', audit_source)
        self.assertIn("/api/human-adam/main-sync-audit", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/main-sync", apply_source)
        self.assertIn("window.confirm(", apply_source)
        self.assertIn("expected_local_head", apply_source)
        self.assertIn("expected_origin_head", apply_source)
        self.assertIn("Použije se pouze fast-forward", apply_source)
        self.assertIn("merge, rebase ani přepis historie", apply_source)
        self.assertIn(
            'mainSyncBtn.addEventListener("click", applyMainRemoteSync);',
            HUMAN_ADAM_HTML,
        )

    def test_voice_transcript_is_inserted_into_existing_editable_textarea(self) -> None:
        insert_start = HUMAN_ADAM_HTML.index("function insertTranscriptForReview(text)")
        insert_end = HUMAN_ADAM_HTML.index("async function startVoiceRecording()", insert_start)
        insert_source = HUMAN_ADAM_HTML[insert_start:insert_end]

        self.assertIn('id="messageInput"', HUMAN_ADAM_HTML)
        self.assertNotIn('id="messageInput" readonly', HUMAN_ADAM_HTML)
        self.assertIn("const existing = input.value;", insert_source)
        self.assertIn("const combined = `${existing}${separator}${transcript}`;", insert_source)
        self.assertIn("input.value = combined;", insert_source)
        self.assertIn("input.focus();", insert_source)

    def test_voice_transcription_never_calls_canonical_send_automatically(self) -> None:
        transcribe_start = HUMAN_ADAM_HTML.index("async function transcribeVoiceRecording()")
        transcribe_end = HUMAN_ADAM_HTML.index("function bubble(", transcribe_start)
        transcribe_source = HUMAN_ADAM_HTML[transcribe_start:transcribe_end]

        self.assertIn('api("/api/human-adam/transcribe"', transcribe_source)
        self.assertIn("insertTranscriptForReview(payload.text);", transcribe_source)
        self.assertNotIn("/api/human-adam/send", transcribe_source)
        self.assertNotIn("sendMessage", transcribe_source)
        self.assertNotIn("requestSubmit", transcribe_source)
        self.assertNotIn("submit()", transcribe_source)
        self.assertNotIn("/api/speech/transcribe", HUMAN_ADAM_HTML)

    def test_voice_text_is_sent_only_by_explicit_existing_submit_action(self) -> None:
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]

        self.assertEqual(HUMAN_ADAM_HTML.count("/api/human-adam/send"), 1)
        self.assertIn("api(HUMAN_ADAM_SEND_PATH", send_source)
        self.assertIn('composer.addEventListener("submit", sendMessage);', HUMAN_ADAM_HTML)
        self.assertIn('<button class="primary" id="sendBtn" type="submit">Odeslat</button>', HUMAN_ADAM_HTML)
        self.assertIn('<button id="voiceRecordBtn" type="button">Nahrát pokyn</button>', HUMAN_ADAM_HTML)
        self.assertIn('<button id="voiceStopBtn" type="button" hidden disabled>', HUMAN_ADAM_HTML)

    def test_completed_adam_answers_get_explicit_speech_control_only(self) -> None:
        bubble_start = HUMAN_ADAM_HTML.index("function bubble(text, className, meta, spokenText=\"\")")
        bubble_end = HUMAN_ADAM_HTML.index("function renderSession(session)", bubble_start)
        bubble_source = HUMAN_ADAM_HTML[bubble_start:bubble_end]
        render_start = bubble_end
        render_end = HUMAN_ADAM_HTML.index("function renderStatus", render_start)
        render_source = HUMAN_ADAM_HTML[render_start:render_end]

        self.assertIn("if (spokenText) node.appendChild(answerSpeechControl(spokenText));", bubble_source)
        self.assertIn('bubble(item.answer, "adam"', render_source)
        self.assertIn("item.answer));", render_source)
        pending_branch = render_source.index("else exchange.appendChild")
        self.assertNotIn("answerSpeechControl", render_source[pending_branch:])
        self.assertIn("Přečíst odpověď", HUMAN_ADAM_HTML)

    def test_answer_speech_starts_only_from_explicit_button_click(self) -> None:
        control_start = HUMAN_ADAM_HTML.index("function answerSpeechControl(text)")
        control_end = HUMAN_ADAM_HTML.index("function bubble(", control_start)
        control_source = HUMAN_ADAM_HTML[control_start:control_end]
        speak_start = HUMAN_ADAM_HTML.index("function speakAnswer(text, button)")
        speak_end = control_start
        speak_source = HUMAN_ADAM_HTML[speak_start:speak_end]
        render_start = HUMAN_ADAM_HTML.index("function renderSession(session)")
        render_end = HUMAN_ADAM_HTML.index("function renderStatus", render_start)
        render_source = HUMAN_ADAM_HTML[render_start:render_end]

        self.assertIn('button.addEventListener("click", () => speakAnswer(text, button));', control_source)
        self.assertIn("window.speechSynthesis.speak(utterance);", speak_source)
        self.assertNotIn("speechSynthesis.speak", render_source)
        self.assertNotIn("speakAnswer(", render_source)
        self.assertNotIn("/api/", speak_source)

    def test_answer_speech_uses_czech_system_voice_and_same_button_stops_it(self) -> None:
        stop_start = HUMAN_ADAM_HTML.index("function stopAnswerSpeech(showNotice=false)")
        stop_end = HUMAN_ADAM_HTML.index("function finishAnswerSpeech", stop_start)
        stop_source = HUMAN_ADAM_HTML[stop_start:stop_end]
        speak_start = HUMAN_ADAM_HTML.index("function speakAnswer(text, button)")
        speak_end = HUMAN_ADAM_HTML.index("function answerSpeechControl(text)", speak_start)
        speak_source = HUMAN_ADAM_HTML[speak_start:speak_end]

        self.assertIn("window.speechSynthesis.cancel();", stop_source)
        self.assertIn("if (activeSpeechButton === button)", speak_source)
        self.assertIn("stopAnswerSpeech(true);", speak_source)
        self.assertIn('utterance.lang = "cs-CZ";', speak_source)
        self.assertIn("/^cs(?:-|$)/i", speak_source)
        self.assertIn('button.textContent = "Zastavit";', speak_source)
        self.assertIn('window.addEventListener("pagehide", () => {', HUMAN_ADAM_HTML)
        self.assertIn("stopAnswerSpeech(false);", HUMAN_ADAM_HTML)
        self.assertIn("stopCompletionMediaSound();", HUMAN_ADAM_HTML)

    def test_unsupported_answer_speech_is_fail_closed_and_understandable(self) -> None:
        support_start = HUMAN_ADAM_HTML.index("function speechPlaybackSupported()")
        support_end = HUMAN_ADAM_HTML.index("function resetSpeechButton", support_start)
        support_source = HUMAN_ADAM_HTML[support_start:support_end]
        speak_start = HUMAN_ADAM_HTML.index("function speakAnswer(text, button)")
        speak_end = HUMAN_ADAM_HTML.index("function answerSpeechControl(text)", speak_start)
        speak_source = HUMAN_ADAM_HTML[speak_start:speak_end]

        self.assertIn("window.speechSynthesis", support_source)
        self.assertIn("window.SpeechSynthesisUtterance", support_source)
        self.assertIn('button.textContent = "Čtení nepodporováno";', speak_source)
        self.assertIn("button.disabled = true;", speak_source)
        self.assertIn("Tento prohlížeč nepodporuje systémové čtení odpovědi.", speak_source)

    def test_voice_transcription_failure_preserves_existing_draft(self) -> None:
        transcribe_start = HUMAN_ADAM_HTML.index("async function transcribeVoiceRecording()")
        transcribe_end = HUMAN_ADAM_HTML.index("function bubble(", transcribe_start)
        transcribe_source = HUMAN_ADAM_HTML[transcribe_start:transcribe_end]
        catch_start = transcribe_source.index("} catch (error) {")
        catch_end = transcribe_source.index("} finally {", catch_start)
        catch_source = transcribe_source[catch_start:catch_end]

        self.assertIn("Rozepsaný text zůstal zachován.", catch_source)
        self.assertNotIn("input.value", catch_source)
        self.assertNotIn("clearMessageInput", transcribe_source)

    def test_voice_recording_explains_insecure_http_before_browser_capabilities(self) -> None:
        record_start = HUMAN_ADAM_HTML.index("async function startVoiceRecording()")
        record_end = HUMAN_ADAM_HTML.index("function stopVoiceRecording()", record_start)
        record_source = HUMAN_ADAM_HTML[record_start:record_end]

        secure_check = record_source.index("if (!window.isSecureContext)")
        capability_check = record_source.index("if (!navigator.mediaDevices")
        self.assertLess(secure_check, capability_check)
        self.assertIn("jen přes HTTPS adresu Cockpitu", record_source)
        self.assertIn("tato stránka běží přes HTTP", record_source)

    def test_ios_record_button_focuses_existing_editor_without_touching_mac_recorder(self) -> None:
        detector_start = HUMAN_ADAM_HTML.index("function isIOSDevice()")
        detector_end = HUMAN_ADAM_HTML.index("async function startVoiceRecording()", detector_start)
        detector_source = HUMAN_ADAM_HTML[detector_start:detector_end]
        record_start = detector_end
        record_end = HUMAN_ADAM_HTML.index("function stopVoiceRecording()", record_start)
        record_source = HUMAN_ADAM_HTML[record_start:record_end]
        ios_start = record_source.index("if (isIOSDevice())")
        ios_end = record_source.index("\n    }", ios_start)
        ios_source = record_source[ios_start:ios_end]

        self.assertIn("iPad|iPhone|iPod", detector_source)
        self.assertIn('navigator.platform === "MacIntel"', detector_source)
        self.assertIn("navigator.maxTouchPoints", detector_source)
        self.assertIn("input.focus();", ios_source)
        self.assertIn("mikrofon klávesnice iPhonu", ios_source)
        self.assertNotIn("getUserMedia", ios_source)
        self.assertNotIn("MediaRecorder", ios_source)
        self.assertLess(ios_start, record_source.index("if (!window.isSecureContext)"))

    def test_active_turn_blocks_new_voice_recording_but_not_manual_status(self) -> None:
        controls_start = HUMAN_ADAM_HTML.index("function syncControls()")
        controls_end = HUMAN_ADAM_HTML.index("function setBusy(", controls_start)
        controls_source = HUMAN_ADAM_HTML[controls_start:controls_end]
        record_start = HUMAN_ADAM_HTML.index("async function startVoiceRecording()")
        record_end = HUMAN_ADAM_HTML.index("function stopVoiceRecording()", record_start)
        record_source = HUMAN_ADAM_HTML[record_start:record_end]

        self.assertIn("voiceRecordBtn.disabled = busy || sendInFlight || sessionTurnBusy", controls_source)
        self.assertIn("if (busy || sendInFlight || sessionTurnBusy", record_source)
        self.assertIn("if (sendInFlight || sessionTurnBusy)", record_source)
        self.assertIn("refreshBtn.disabled = busy || resultWatchActive;", controls_source)
        self.assertNotIn("refreshBtn.disabled = sessionTurnBusy", controls_source)

    def test_turn_timer_starts_immediately_before_send_api_call(self) -> None:
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]

        self.assertIn("turn_busy:true", send_source)
        self.assertIn("active_turn:{client_message_id:clientId,started_at:sentAt}", send_source)
        self.assertLess(send_source.index("sendInFlight = true;"), send_source.index("renderTurnState(optimistic);"))
        self.assertLess(
            send_source.index("renderTurnState(optimistic);"),
            send_source.index("await api(HUMAN_ADAM_SEND_PATH"),
        )
        self.assertIn(
            "`Adam pracuje · ${elapsedClock(activeTurnStartedAt)} · pokyn neposílej znovu`",
            HUMAN_ADAM_HTML,
        )

    def test_turn_timer_resumes_from_session_started_at_after_page_reload(self) -> None:
        render_start = HUMAN_ADAM_HTML.index("function renderTurnState(session)")
        render_end = HUMAN_ADAM_HTML.index("function clearMessageInput()", render_start)
        render_source = HUMAN_ADAM_HTML[render_start:render_end]
        status_start = HUMAN_ADAM_HTML.index("function renderStatus(payload)")
        status_end = HUMAN_ADAM_HTML.index("async function api(", status_start)
        status_source = HUMAN_ADAM_HTML[status_start:status_end]
        header = HUMAN_ADAM_HTML.index("<header>")
        activity = HUMAN_ADAM_HTML.index('id="turnActivity"', header)
        header_end = HUMAN_ADAM_HTML.index("</header>", activity)

        self.assertIn("session && session.active_turn", render_source)
        self.assertIn('startTurnTimer(activeTurn.started_at || "");', render_source)
        self.assertIn("renderTurnState(session);", status_source)
        self.assertIn("Date.now() - startedMs", HUMAN_ADAM_HTML)
        self.assertIn('padStart(2, "0")', HUMAN_ADAM_HTML)
        self.assertNotIn("elapsedSeconds = 0", HUMAN_ADAM_HTML)
        self.assertLess(header, activity)
        self.assertLess(activity, header_end)

    def test_active_turn_disables_only_new_send_and_keeps_manual_status_available(self) -> None:
        controls_start = HUMAN_ADAM_HTML.index("function syncControls()")
        controls_end = HUMAN_ADAM_HTML.index("function setBusy(", controls_start)
        controls_source = HUMAN_ADAM_HTML[controls_start:controls_end]
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]

        self.assertIn("sendBtn.disabled = busy || sendInFlight || sessionTurnBusy", controls_source)
        self.assertIn("refreshBtn.disabled = busy || resultWatchActive;", controls_source)
        self.assertNotIn("refreshBtn.disabled = sessionTurnBusy", controls_source)
        self.assertIn("if (busy || sendInFlight || sessionTurnBusy", send_source)

    def test_status_button_starts_bounded_read_only_result_watch_for_active_turn(self) -> None:
        watch_start = HUMAN_ADAM_HTML.index("function resultWatchTargetId()")
        watch_end = HUMAN_ADAM_HTML.index("async function connect()", watch_start)
        watch_source = HUMAN_ADAM_HTML[watch_start:watch_end]
        controls_start = HUMAN_ADAM_HTML.index("function syncControls()")
        controls_end = HUMAN_ADAM_HTML.index("function setBusy(", controls_start)
        controls_source = HUMAN_ADAM_HTML[controls_start:controls_end]

        self.assertIn("const RESULT_WATCH_MAX_ATTEMPTS = 60;", HUMAN_ADAM_HTML)
        self.assertIn("const RESULT_WATCH_MAX_DELAY_MS = 30000;", HUMAN_ADAM_HTML)
        self.assertIn('api("/api/human-adam/status")', watch_source)
        self.assertNotIn("HUMAN_ADAM_SEND_PATH", watch_source)
        self.assertNotIn("/api/human-adam/send", watch_source)
        self.assertIn("window.setTimeout(checkResultWatch, delay);", watch_source)
        self.assertIn("resultWatchAttempt >= RESULT_WATCH_MAX_ATTEMPTS", watch_source)
        self.assertIn('String(watched.status || "") === "completed"', watch_source)
        self.assertIn('String(watched.status || "") === "delivery_unknown"', watch_source)
        self.assertIn("playCompletionMediaSound();", watch_source)
        self.assertIn("stopResultWatch();", watch_source)
        self.assertIn("if (sessionTurnBusy || deliveryUncertain || sendInFlight) startResultWatch();", watch_source)
        self.assertIn('refreshBtn.addEventListener("click", handleRefreshStatus);', HUMAN_ADAM_HTML)
        self.assertIn('refreshBtn.textContent = resultWatchActive ? "Čekám na výsledek…" : "Stav";', controls_source)
        self.assertIn("refreshBtn.disabled = busy || resultWatchActive;", controls_source)
        self.assertNotIn("setInterval", watch_source)

    def test_confirmed_send_completion_stops_parallel_result_watch(self) -> None:
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        success = send_source.index("stopResultWatch();")
        render = send_source.index("renderSession(payload.session);")

        self.assertLess(success, render)
        self.assertIn('notice.textContent = "Výsledek byl načten bez opakovaného odeslání pokynu.";', HUMAN_ADAM_HTML)
        self.assertIn('notice.textContent = "Stav doručení zůstává nejistý. Pokyn neposílej znovu.";', HUMAN_ADAM_HTML)

    def test_turn_timer_stops_after_completion_and_marks_delivery_unknown(self) -> None:
        render_start = HUMAN_ADAM_HTML.index("function renderTurnState(session)")
        render_end = HUMAN_ADAM_HTML.index("function clearMessageInput()", render_start)
        render_source = HUMAN_ADAM_HTML[render_start:render_end]
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        timer_start = HUMAN_ADAM_HTML.index("function updateTurnTimer()")
        timer_end = HUMAN_ADAM_HTML.index("function startTurnTimer(", timer_start)
        timer_source = HUMAN_ADAM_HTML[timer_start:timer_end]

        self.assertIn("} else {\n      stopTurnTimer();", render_source)
        self.assertIn("window.clearTimeout(turnTimerId);", HUMAN_ADAM_HTML)
        self.assertIn('latest.status === "delivery_unknown"', render_source)
        self.assertIn(
            "Stav doručení je nejistý · obnov stav · pokyn neposílej znovu",
            render_source,
        )
        self.assertLess(
            send_source.index("renderSession(payload.session);"),
            send_source.index("renderTurnState(payload.session);"),
        )
        self.assertNotIn("api(", timer_source)
        self.assertNotIn("loadStatus", timer_source)

    def test_confirmed_completion_primes_and_plays_the_loud_media_chime(self) -> None:
        sound_start = HUMAN_ADAM_HTML.index("function configureCompletionAudioSession()")
        sound_end = HUMAN_ADAM_HTML.index("function syncControls()", sound_start)
        sound_source = HUMAN_ADAM_HTML[sound_start:sound_end]
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        catch_start = send_source.index("} catch (error) {")

        self.assertIn("function configureCompletionAudioSession()", sound_source)
        self.assertIn('navigator.audioSession.type = "playback";', sound_source)
        self.assertIn("async function primeCompletionMediaSound()", sound_source)
        self.assertIn("async function playCompletionMediaSound()", sound_source)
        self.assertIn("completionMediaAudio.muted = true;", sound_source)
        self.assertIn("completionMediaAudio.muted = false;", sound_source)
        self.assertIn("completionMediaAudio.play();", sound_source)
        self.assertIn("Zvuk je pouze doplňkový", sound_source)
        self.assertLess(send_source.index("await primeCompletionMediaSound();"), send_source.index("await api(HUMAN_ADAM_SEND_PATH"))
        self.assertLess(send_source.index('notice.textContent = "Odpověď doručena a potvrzena.";'), send_source.index("playCompletionMediaSound();"))
        self.assertLess(send_source.index("playCompletionMediaSound();"), catch_start)
        self.assertNotIn("playCompletionMediaSound", send_source[catch_start:])

    def test_only_the_loud_media_sound_control_remains(self) -> None:
        sound_start = HUMAN_ADAM_HTML.index("function configureCompletionAudioSession()")
        sound_end = HUMAN_ADAM_HTML.index("function syncControls()", sound_start)
        sound_source = HUMAN_ADAM_HTML[sound_start:sound_end]

        self.assertIn('id="mediaSoundTestBtn"', HUMAN_ADAM_HTML)
        self.assertNotIn('id="soundTestBtn"', HUMAN_ADAM_HTML)
        self.assertNotIn("AudioContext", HUMAN_ADAM_HTML)
        self.assertNotIn("createOscillator", HUMAN_ADAM_HTML)
        self.assertIn("Zvuk odpovědi: vyzkoušet", HUMAN_ADAM_HTML)
        self.assertIn('id="completionMediaAudio" preload="auto" playsinline hidden', HUMAN_ADAM_HTML)
        self.assertIn("function completionMediaWavUrl()", sound_source)
        self.assertIn('new Blob([buffer], {type:"audio/wav"})', sound_source)
        self.assertIn("window.URL.createObjectURL", sound_source)
        self.assertIn("completionMediaAudio.volume = 1;", sound_source)
        self.assertIn("completionMediaAudio.play();", sound_source)
        self.assertIn('ready ? "Zvuk odpovědi: připraven" : "Zvuk odpovědi: vyzkoušet"', sound_source)
        self.assertNotIn("fetch(", sound_source)
        self.assertNotIn("api(", sound_source)
        self.assertIn('mediaSoundTestBtn.addEventListener("click", testCompletionMediaSound);', HUMAN_ADAM_HTML)

    def test_ui_is_manual_refresh_only_and_uses_safe_dom_text(self) -> None:
        self.assertNotIn("setInterval", HUMAN_ADAM_HTML)
        self.assertNotIn("innerHTML", HUMAN_ADAM_HTML)
        self.assertIn("textContent", HUMAN_ADAM_HTML)
        self.assertIn("replaceChildren", HUMAN_ADAM_HTML)
        self.assertIn("#tvbcpScroll { flex:1; min-height:0; overflow:auto;", HUMAN_ADAM_HTML)
        self.assertIn('data-scroll-mode="end-anchor-v3"', HUMAN_ADAM_HTML)
        self.assertIn("function scrollTvbcpToEnd()", HUMAN_ADAM_HTML)
        self.assertGreaterEqual(HUMAN_ADAM_HTML.count("requestAnimationFrame"), 2)
        self.assertIn("tvbcpScroll.scrollTop = tvbcpScroll.scrollHeight;", HUMAN_ADAM_HTML)
        self.assertIn('tvbcpEnd.scrollIntoView({block:"end",inline:"nearest",behavior:"auto"});', HUMAN_ADAM_HTML)
        self.assertIn("window.setTimeout(applyEndPosition, 120);", HUMAN_ADAM_HTML)
        self.assertIn("scrollTvbcpToEnd();", HUMAN_ADAM_HTML)
        self.assertNotIn("scrollTop = 0;", HUMAN_ADAM_HTML)

    def test_header_places_connect_left_and_cockpit_right(self) -> None:
        connect = HUMAN_ADAM_HTML.index('id="connectBtn"')
        title = HUMAN_ADAM_HTML.index("<h1>Human–Adam</h1>")
        tools = HUMAN_ADAM_HTML.index('class="head-tools"', title)
        cockpit = HUMAN_ADAM_HTML.index('<a class="back" href="/">← Cockpit</a>')
        self.assertLess(connect, title)
        self.assertLess(title, tools)
        self.assertLess(tools, cockpit)
        self.assertIn("grid-template-columns:auto minmax(0,1fr) auto", HUMAN_ADAM_HTML)
        self.assertIn(".head-tools { grid-column:1/-1; grid-row:2; justify-content:center; }", HUMAN_ADAM_HTML)

    def test_submit_clears_input_before_api_and_blocks_safari_restore(self) -> None:
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        capture = send_source.index("const text = input.value.trim();")
        clear = send_source.index("clearMessageInput();")
        api_call = send_source.index("await api(HUMAN_ADAM_SEND_PATH")

        self.assertLess(capture, clear)
        self.assertLess(clear, api_call)
        self.assertIn("renderSession(optimistic);", send_source)
        self.assertNotIn("input.value = text", send_source)
        self.assertNotIn('input.value = ""', send_source)
        self.assertIn('function clearMessageInput() {\n    input.value = "";\n    input.defaultValue = "";', HUMAN_ADAM_HTML)
        self.assertIn('<form class="composer" id="composer" autocomplete="off">', HUMAN_ADAM_HTML)
        self.assertIn('id="messageInput" maxlength="12000" autocomplete="off"', HUMAN_ADAM_HTML)
        self.assertIn('window.addEventListener("pageshow", clearMessageInput);', HUMAN_ADAM_HTML)

    def test_confirmed_rejection_restores_draft_but_unknown_delivery_never_does(self) -> None:
        helper_start = HUMAN_ADAM_HTML.index("function restoreRejectedMessage(text)")
        helper_end = HUMAN_ADAM_HTML.index("function preferredVoiceMimeType()", helper_start)
        helper_source = HUMAN_ADAM_HTML[helper_start:helper_end]
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        catch_start = send_source.index("} catch (error) {")
        unknown_start = send_source.index('const confirmedRejection = new Set(["human_adam_busy","human_adam_send_failed"])', catch_start)
        rejected_start = send_source.index("} else {", unknown_start)
        rejected_end = send_source.index("\n      }", rejected_start)

        self.assertIn("if (input.value) return;", helper_source)
        self.assertIn('input.value = String(text || "").slice', helper_source)
        self.assertIn("input.focus();", helper_source)
        self.assertIn("if (!confirmedRejection)", send_source[unknown_start:rejected_start])
        self.assertNotIn("restoreRejectedMessage", send_source[unknown_start:rejected_start])
        self.assertIn("restoreRejectedMessage(text);", send_source[rejected_start:rejected_end])
        self.assertIn("Pokyn neposílej znovu.", send_source[unknown_start:rejected_start])
        self.assertIn("Text byl vrácen do editoru.", send_source[rejected_start:rejected_end])

    def test_ui_does_not_depend_on_legacy_delivery_paths(self) -> None:
        lowered = HUMAN_ADAM_HTML.lower()
        self.assertNotIn("watcher", lowered)
        self.assertNotIn("voicebridge", lowered)
        self.assertNotIn("tty", lowered)
        self.assertNotIn("terminal tab", lowered)


if __name__ == "__main__":
    unittest.main()
