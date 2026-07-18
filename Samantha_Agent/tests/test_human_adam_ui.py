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
            "contextAnchorBadge",
            "mediaSoundTestBtn",
            "completionMediaAudio",
            "contextAnchorOpenBtn",
            "contextAnchorPanel",
            "contextAnchorCloseBtn",
            "contextAnchorRefreshBtn",
            "contextAnchorMeta",
            "contextAnchorInput",
            "contextAnchorProposeBtn",
            "contextAnchorSaveBtn",
            "contextAnchorPinBtn",
            "contextAnchorPauseBtn",
            "contextAnchorDeleteBtn",
            "chat",
            "messageInput",
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
            "workChanges",
            "checkpointMessage",
            "checkpointBtn",
            "deployMeta",
            "deployAuditBtn",
            "deployConfirmation",
            "deployBtn",
            "deploymentReceipt",
            "deploymentDiagnostic",
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
        self.assertIn("/api/human-adam/context-anchor", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/send", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/tvbcp", HUMAN_ADAM_HTML)
        self.assertIn("TVBCP se načte až po otevření.", HUMAN_ADAM_HTML)
        self.assertIn("Workspace: ${workspace.change_count} změn", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/workspace", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/checkpoint", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/deploy-audit", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/deploy", HUMAN_ADAM_HTML)
        self.assertIn("/api/human-adam/transcribe", HUMAN_ADAM_HTML)
        self.assertIn("Checkpoint bez pushnutí", HUMAN_ADAM_HTML)
        self.assertIn("Audit nasazení", HUMAN_ADAM_HTML)
        self.assertIn("Ověřit a nasadit", HUMAN_ADAM_HTML)
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
        self.assertIn("checkpoint_token:deploymentAudit.checkpoint_token", HUMAN_ADAM_HTML)
        self.assertIn("confirmation.trim() !== required", HUMAN_ADAM_HTML)
        self.assertIn("const confirmation = deployConfirmation.value.trim();", HUMAN_ADAM_HTML)
        self.assertIn('deployConfirmation.addEventListener("input"', HUMAN_ADAM_HTML)
        self.assertNotIn("window.prompt", HUMAN_ADAM_HTML)
        failure = HUMAN_ADAM_HTML.index("const deploymentFailure =")
        refresh = HUMAN_ADAM_HTML.index("await loadWork();", failure)
        restore = HUMAN_ADAM_HTML.index("deployMeta.textContent = deploymentFailure;", refresh)
        self.assertLess(refresh, restore)
        self.assertIn("await waitForCockpitAndReload(Number(payload.restart.pid || previousPid));", HUMAN_ADAM_HTML)

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
        self.assertIn('text = `${activeProfileLabel} · ${connectionText} · ${workspaceText} · ${adamText}`;', summary_source)
        self.assertIn('mobileStatusSummary.setAttribute("aria-expanded"', HUMAN_ADAM_HTML)
        self.assertIn('mobileStatusToggleText.textContent = showDetails ? "Skrýt" : "Podrobnosti";', HUMAN_ADAM_HTML)
        self.assertIn('mobileStatusSummary.addEventListener("click"', HUMAN_ADAM_HTML)
        self.assertIn("updateMobileStatusSummary();\n    turnTimerId", HUMAN_ADAM_HTML)

    def test_diverged_workspace_keeps_preserved_wip_visible_but_blocks_audit(self) -> None:
        self.assertIn('workspace.workspace_relation === "diverged"', HUMAN_ADAM_HTML)
        self.assertIn("WIP zachován: ${workspace.local_commit_count} · nutná obnova", HUMAN_ADAM_HTML)
        self.assertIn("WIP checkpoint je zachovaný:", HUMAN_ADAM_HTML)
        self.assertIn("WIP je bezpečně zachovaný, ale audit je zablokovaný.", HUMAN_ADAM_HTML)
        self.assertIn("deployAuditBtn.disabled = Boolean(payload.dirty) || !payload.local_checkpoint_ahead;", HUMAN_ADAM_HTML)
        self.assertLess(
            HUMAN_ADAM_HTML.index("else if (checkpointPreserved) workMeta.textContent"),
            HUMAN_ADAM_HTML.index('else workMeta.textContent = "Workspace je čistý a odpovídá main.";'),
        )

    def test_profile_switch_is_explicit_atomic_and_preserves_unsent_draft(self) -> None:
        switch_start = HUMAN_ADAM_HTML.index("async function switchProfile()")
        switch_end = HUMAN_ADAM_HTML.index("function scrollTvbcpToEnd", switch_start)
        source = HUMAN_ADAM_HTML[switch_start:switch_end]

        self.assertIn("if (input.value.trim())", source)
        self.assertIn("profil jsem nepřepnul", source)
        self.assertIn("Přepnout celý pracovní profil", source)
        self.assertIn("Přepne se vlákno, workspace i TVBCP.", source)
        self.assertIn('api("/api/human-adam/profile"', source)
        self.assertIn("profile_id:targetId,confirmed:true", source)
        self.assertIn("if (contextAnchorDraftDirty())", source)
        self.assertIn("profil jsem nepřepnul", source)
        self.assertIn("resetContextAnchorEditorState();", source)
        self.assertIn("showProfileSwitchFailure", source)
        self.assertIn('notice.scrollIntoView({block:"nearest",behavior:"smooth"});', HUMAN_ADAM_HTML)
        self.assertIn('profileSelect.addEventListener("change", syncControls);', HUMAN_ADAM_HTML)
        self.assertIn('profileSwitchBtn.addEventListener("click", switchProfile);', HUMAN_ADAM_HTML)

    def test_context_anchor_is_explicit_editable_and_profile_scoped_in_ui(self) -> None:
        panel_start = HUMAN_ADAM_HTML.index('id="contextAnchorPanel"')
        panel_end = HUMAN_ADAM_HTML.index('</aside>', panel_start)
        panel_source = HUMAN_ADAM_HTML[panel_start:panel_end]
        save_start = HUMAN_ADAM_HTML.index("async function changeContextAnchor(operation)")
        save_end = HUMAN_ADAM_HTML.index("async function loadTvbcp", save_start)
        save_source = HUMAN_ADAM_HTML[save_start:save_end]
        switch_start = HUMAN_ADAM_HTML.index("async function switchProfile()")
        switch_end = HUMAN_ADAM_HTML.index("function scrollTvbcpToEnd", switch_start)
        switch_source = HUMAN_ADAM_HTML[switch_start:switch_end]

        self.assertIn('maxlength="6000"', panel_source)
        self.assertIn("Cíl:", panel_source)
        self.assertIn("Plán:", panel_source)
        self.assertIn("Hotovo:", panel_source)
        self.assertIn("Rozhodnutí:", panel_source)
        self.assertIn("Další krok:", panel_source)
        self.assertIn("Novější pokyn v chatu má vždy přednost.", panel_source)
        self.assertIn("Adam: připravit návrh", panel_source)
        self.assertIn("Uložit návrh", panel_source)
        self.assertIn("Připnout", panel_source)
        self.assertIn("Pozastavit", panel_source)
        self.assertIn("Smazat", panel_source)
        self.assertIn('api("/api/human-adam/context-anchor"', save_source)
        self.assertIn("expected_revision:savedContextAnchorRevision", save_source)
        self.assertIn('content:operation === "save" ? content : ""', save_source)
        self.assertIn('contextAnchorSaveBtn.addEventListener("click", () => changeContextAnchor("save"));', HUMAN_ADAM_HTML)
        self.assertIn('contextAnchorPinBtn.addEventListener("click", () => changeContextAnchor("pin"));', HUMAN_ADAM_HTML)
        self.assertIn('contextAnchorPauseBtn.addEventListener("click", () => changeContextAnchor("pause"));', HUMAN_ADAM_HTML)
        self.assertIn('contextAnchorDeleteBtn.addEventListener("click", () => changeContextAnchor("delete"));', HUMAN_ADAM_HTML)
        self.assertIn("contextAnchorPanel.hidden = true;", switch_source)

    def test_context_anchor_renders_stored_paused_and_pinned_as_distinct_states(self) -> None:
        badge_start = HUMAN_ADAM_HTML.index("function renderContextAnchorBadge(anchor)")
        badge_end = HUMAN_ADAM_HTML.index("async function loadContextAnchor()", badge_start)
        source = HUMAN_ADAM_HTML[badge_start:badge_end]

        self.assertIn('active ? "Kontext: připnut"', source)
        self.assertIn('stored ? "Kontext: uložen"', source)
        self.assertIn('"Kontext: žádný"', source)
        self.assertIn("savedContextAnchorContent = hasContent ? content", source)
        self.assertIn("savedContextAnchorActive = hasContent && anchor.active === true", source)
        self.assertIn("savedContextAnchorRevision = Number.isSafeInteger(revision)", source)
        self.assertIn("Uloženo a pozastaveno", source)
        self.assertIn("Napiš návrh do pole a stiskni Uložit návrh.", source)
        self.assertIn("nechat připravit Adamem", source)
        self.assertIn("nový odlišný pokyn vyžadovat potvrzení", source)

    def test_empty_loaded_anchor_keeps_save_button_as_usable_entry_point(self) -> None:
        controls_start = HUMAN_ADAM_HTML.index("function syncControls()")
        controls_end = HUMAN_ADAM_HTML.index("function setBusy(", controls_start)
        source = HUMAN_ADAM_HTML[controls_start:controls_end]
        save_line = next(line for line in source.splitlines() if "contextAnchorSaveBtn.disabled" in line)

        self.assertIn("anchorMutationBlocked || !contextAnchorLoaded", save_line)
        self.assertIn("(!anchorDirty && anchorHasContent)", save_line)
        self.assertNotIn("!contextAnchorInput.value.trim()", save_line)
        self.assertIn("Nejdřív napiš stručný aktivní kontext k uložení.", HUMAN_ADAM_HTML)
        self.assertIn("contextAnchorInput.focus();", HUMAN_ADAM_HTML)

    def test_mobile_anchor_controls_wrap_without_widening_panel(self) -> None:
        self.assertIn(".tvbcp-panel { width:100%; max-width:100vw; min-width:0; overflow-x:hidden; }", HUMAN_ADAM_HTML)
        self.assertIn(".tvbcp-head,.context-anchor-body { min-width:0; max-width:100%; }", HUMAN_ADAM_HTML)
        self.assertIn("#contextAnchorInput { min-width:0; max-width:100%; }", HUMAN_ADAM_HTML)
        self.assertIn("#contextAnchorProposeBtn { width:100%; min-width:0; white-space:normal; }", HUMAN_ADAM_HTML)
        self.assertIn(".context-anchor-actions { width:100%; min-width:0; flex-wrap:wrap; }", HUMAN_ADAM_HTML)
        self.assertIn("flex:1 1 calc(50% - 4px); min-width:0;", HUMAN_ADAM_HTML)

    def test_context_anchor_update_preserves_server_owned_state_transitions(self) -> None:
        change_start = HUMAN_ADAM_HTML.index("async function changeContextAnchor(operation)")
        change_end = HUMAN_ADAM_HTML.index("function validContextAnchorProposal", change_start)
        source = HUMAN_ADAM_HTML[change_start:change_end]

        self.assertIn('operation === "save" ? content : ""', source)
        self.assertIn("expected_revision:savedContextAnchorRevision", source)
        self.assertNotIn("active:", source)
        self.assertIn("payload.active", source)
        self.assertIn("Aktualizovaná připnutá kotva se použije od příštího tahu.", source)
        self.assertIn("Kotva je soukromě uložená a zatím se k tahům nepřikládá.", source)
        self.assertIn("Kotva je pozastavená, zůstává uložená", source)

    def test_context_anchor_conflict_preserves_editor_and_requires_explicit_refresh(self) -> None:
        change_start = HUMAN_ADAM_HTML.index("async function changeContextAnchor(operation)")
        change_end = HUMAN_ADAM_HTML.index("function validContextAnchorProposal", change_start)
        source = HUMAN_ADAM_HTML[change_start:change_end]

        self.assertIn('error.status = String(payload.status || "")', source)
        self.assertIn('error.status === "human_adam_context_anchor_conflict"', source)
        self.assertIn("Tento editor nic nepřepsal a jeho obsah zůstal zachovaný.", source)
        self.assertIn("Nejdřív si případný rozepsaný text zkopíruj", source)
        self.assertIn("potom stiskni Obnovit", source)
        conflict_source = source[source.index('if (error.status === "human_adam_context_anchor_conflict")'):]
        self.assertNotIn("contextAnchorInput.value =", conflict_source)
        self.assertNotIn("loadContextAnchor()", conflict_source)

    def test_context_anchor_draft_requires_explicit_discard_before_reload_or_delete(self) -> None:
        load_start = HUMAN_ADAM_HTML.index("async function loadContextAnchor()")
        load_end = HUMAN_ADAM_HTML.index("function openContextAnchor()", load_start)
        load_source = HUMAN_ADAM_HTML[load_start:load_end]
        change_start = HUMAN_ADAM_HTML.index("async function changeContextAnchor(operation)")
        change_end = HUMAN_ADAM_HTML.index("function validContextAnchorProposal", change_start)
        change_source = HUMAN_ADAM_HTML[change_start:change_end]

        self.assertIn("contextAnchorDraftDirty()", load_source)
        self.assertIn("Zahodit rozepsanou změnu", load_source)
        self.assertIn('operation !== "save" && contextAnchorDraftDirty()', change_source)
        self.assertIn('operation === "delete" && !window.confirm', change_source)
        self.assertIn("Trvale smazat uloženou kotvu", change_source)

    def test_adam_proposes_anchor_through_existing_visible_canonical_turn(self) -> None:
        proposal_start = HUMAN_ADAM_HTML.index("async function proposeContextAnchor()")
        proposal_end = HUMAN_ADAM_HTML.index("async function loadTvbcp", proposal_start)
        proposal_source = HUMAN_ADAM_HTML[proposal_start:proposal_end]

        self.assertEqual(HUMAN_ADAM_HTML.count('const HUMAN_ADAM_SEND_PATH = "/api/human-adam/send";'), 1)
        self.assertIn("CONTEXT_ANCHOR_PROPOSAL_PROMPT", proposal_source)
        self.assertIn("user_text:CONTEXT_ANCHOR_PROPOSAL_PROMPT", proposal_source)
        self.assertIn("api(HUMAN_ADAM_SEND_PATH", proposal_source)
        self.assertIn("renderSession(optimistic);", proposal_source)
        self.assertIn("renderSession(payload.session);", proposal_source)
        self.assertNotIn("/api/human-adam/context-anchor", proposal_source)
        self.assertNotIn("saveContextAnchor", proposal_source)
        self.assertIn('contextAnchorProposeBtn.addEventListener("click", proposeContextAnchor);', HUMAN_ADAM_HTML)

    def test_anchor_proposal_fills_editor_only_after_confirmed_structured_answer(self) -> None:
        proposal_start = HUMAN_ADAM_HTML.index("async function proposeContextAnchor()")
        proposal_end = HUMAN_ADAM_HTML.index("async function loadTvbcp", proposal_start)
        proposal_source = HUMAN_ADAM_HTML[proposal_start:proposal_end]
        validation_start = HUMAN_ADAM_HTML.index("function validContextAnchorProposal(text)")
        validation_source = HUMAN_ADAM_HTML[validation_start:proposal_start]

        self.assertIn('entry.status !== "completed" || entry.delivery_confirmed !== true', proposal_source)
        self.assertIn("validContextAnchorProposal(proposal)", proposal_source)
        self.assertIn("CONTEXT_ANCHOR_REQUIRED_HEADINGS.every", validation_source)
        self.assertIn("contextAnchorInput.value = proposal;", proposal_source)
        self.assertLess(
            proposal_source.index('entry.delivery_confirmed !== true'),
            proposal_source.index("contextAnchorInput.value = proposal;"),
        )
        self.assertIn("automaticky se neuložil", proposal_source)

    def test_anchor_proposal_preserves_both_drafts_and_never_retries_unknown_delivery(self) -> None:
        proposal_start = HUMAN_ADAM_HTML.index("async function proposeContextAnchor()")
        proposal_end = HUMAN_ADAM_HTML.index("async function loadTvbcp", proposal_start)
        proposal_source = HUMAN_ADAM_HTML[proposal_start:proposal_end]

        self.assertIn("const editorBefore = contextAnchorInput.value;", proposal_source)
        self.assertIn("contextAnchorInput.value !== editorBefore", proposal_source)
        self.assertNotIn("clearMessageInput", proposal_source)
        self.assertNotIn("restoreRejectedMessage", proposal_source)
        self.assertNotIn("input.value =", proposal_source)
        self.assertIn("Požadavek neposílej automaticky znovu.", proposal_source)
        self.assertEqual(proposal_source.count("api(HUMAN_ADAM_SEND_PATH"), 1)

    def test_active_turn_disables_anchor_proposal_and_uncertain_delivery_requires_confirmation(self) -> None:
        controls_start = HUMAN_ADAM_HTML.index("function syncControls()")
        controls_end = HUMAN_ADAM_HTML.index("function setBusy(", controls_start)
        controls_source = HUMAN_ADAM_HTML[controls_start:controls_end]
        proposal_start = HUMAN_ADAM_HTML.index("async function proposeContextAnchor()")
        proposal_end = HUMAN_ADAM_HTML.index("async function loadTvbcp", proposal_start)
        proposal_source = HUMAN_ADAM_HTML[proposal_start:proposal_end]

        self.assertIn("contextAnchorProposeBtn.disabled = busy || sendInFlight || sessionTurnBusy", controls_source)
        self.assertIn("|| !sessionConnected;", controls_source)
        self.assertNotIn("!sessionConnected || deliveryUncertain", controls_source)
        self.assertIn("if (busy || sendInFlight || sessionTurnBusy", proposal_source)
        self.assertNotIn("!sessionConnected || deliveryUncertain", proposal_source)
        self.assertIn("if (deliveryUncertain && !window.confirm", proposal_source)
        self.assertIn("Odeslat nový odlišný pokyn pouze pro přípravu kotvy?", proposal_source)
        self.assertIn("Předchozí pokyn se nebude opakovat.", proposal_source)

    def test_context_anchor_never_auto_updates_during_message_send(self) -> None:
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        controls_start = HUMAN_ADAM_HTML.index("function syncControls()")
        controls_end = HUMAN_ADAM_HTML.index("function setBusy(", controls_start)
        controls_source = HUMAN_ADAM_HTML[controls_start:controls_end]

        self.assertNotIn("saveContextAnchor", send_source)
        self.assertNotIn("/api/human-adam/context-anchor", send_source)
        self.assertIn("const anchorMutationBlocked = busy || sendInFlight || sessionTurnBusy;", controls_source)
        self.assertIn("contextAnchorSaveBtn.disabled = anchorMutationBlocked", controls_source)
        self.assertIn("contextAnchorPinBtn.disabled = anchorMutationBlocked", controls_source)
        self.assertIn("contextAnchorPauseBtn.disabled = anchorMutationBlocked", controls_source)
        self.assertIn("contextAnchorDeleteBtn.disabled = anchorMutationBlocked", controls_source)
        self.assertIn("payload.context_anchor_warning", send_source)

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

    def test_ui_renders_persistent_safe_deployment_confirmation(self) -> None:
        self.assertIn("payload.deployment_confirmation", HUMAN_ADAM_HTML)
        self.assertIn("confirmation.gate_passed === true", HUMAN_ADAM_HTML)
        self.assertIn("/^[0-9a-f]{7}$/.test(shortCommit)", HUMAN_ADAM_HTML)
        self.assertIn(
            "`Nasazeno ${shortCommit} · plná brána prošla · ${completedTime}`",
            HUMAN_ADAM_HTML,
        )
        self.assertIn("deploymentReceipt.hidden = !showConfirmation;", HUMAN_ADAM_HTML)

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

    def test_ui_renders_safe_persistent_deployment_stage_in_sticky_header(self) -> None:
        header = HUMAN_ADAM_HTML.index("<header>")
        receipt = HUMAN_ADAM_HTML.index('id="deploymentReceipt"', header)
        diagnostic = HUMAN_ADAM_HTML.index('id="deploymentDiagnostic"', receipt)
        header_end = HUMAN_ADAM_HTML.index("</header>", diagnostic)
        render_start = HUMAN_ADAM_HTML.index('function renderDeploymentDiagnostic(diagnostic, confirmedCommit = "")')
        render_end = HUMAN_ADAM_HTML.index("function renderStatus(payload)", render_start)
        render_source = HUMAN_ADAM_HTML[render_start:render_end]

        self.assertLess(receipt, diagnostic)
        self.assertLess(diagnostic, header_end)
        self.assertIn('new Set(["audit","gate","receipt","remote_recheck","push","fast_forward","workspace_alignment","restart"])', render_source)
        self.assertIn('new Set(["running","passed","failed"])', render_source)
        self.assertIn("deploymentDiagnostic.textContent = showDiagnostic", render_source)
        self.assertIn("Poslední nasazení ${shortCommit} · ${message} · ${updatedTime}", render_source)
        self.assertIn("deploymentDiagnostic.hidden = !showDiagnostic;", render_source)
        self.assertIn('const coveredByConfirmation = outcome === "passed" && shortCommit === confirmedCommit;', render_source)
        self.assertIn("&& !coveredByConfirmation", render_source)
        self.assertIn('showConfirmation ? shortCommit : ""', HUMAN_ADAM_HTML)
        self.assertNotIn("diagnostic.path", render_source)
        self.assertNotIn("diagnostic.error", render_source)

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
        render_end = HUMAN_ADAM_HTML.index("function renderDeploymentDiagnostic", render_start)
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
        render_end = HUMAN_ADAM_HTML.index("function renderDeploymentDiagnostic", render_start)
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
