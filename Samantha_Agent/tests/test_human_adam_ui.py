from __future__ import annotations

import unittest

from app.communication.human_adam_ui import HUMAN_ADAM_HTML


class HumanAdamUiTests(unittest.TestCase):
    def test_ui_exposes_explicit_connection_send_time_and_delivery_evidence(self) -> None:
        for element_id in (
            "connectBtn",
            "refreshBtn",
            "connectionBadge",
            "threadBadge",
            "workspaceBadge",
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
        render_start = HUMAN_ADAM_HTML.index("function renderDeploymentDiagnostic(diagnostic)")
        render_end = HUMAN_ADAM_HTML.index("function renderStatus(payload)", render_start)
        render_source = HUMAN_ADAM_HTML[render_start:render_end]

        self.assertLess(receipt, diagnostic)
        self.assertLess(diagnostic, header_end)
        self.assertIn('new Set(["audit","gate","receipt","remote_recheck","push","fast_forward","workspace_alignment","restart"])', render_source)
        self.assertIn('new Set(["running","passed","failed"])', render_source)
        self.assertIn("deploymentDiagnostic.textContent = showDiagnostic", render_source)
        self.assertIn("Poslední nasazení ${shortCommit} · ${message} · ${updatedTime}", render_source)
        self.assertIn("deploymentDiagnostic.hidden = !showDiagnostic;", render_source)
        self.assertIn("renderDeploymentDiagnostic(payload.deployment_diagnostic || null);", HUMAN_ADAM_HTML)
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
        self.assertIn('/api/human-adam/send"', send_source)
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
        self.assertIn('window.addEventListener("pagehide", () => stopAnswerSpeech(false));', HUMAN_ADAM_HTML)

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
        self.assertIn("refreshBtn.disabled = busy;", controls_source)
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
            send_source.index('await api("/api/human-adam/send"'),
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
        self.assertIn("refreshBtn.disabled = busy;", controls_source)
        self.assertNotIn("refreshBtn.disabled = sessionTurnBusy", controls_source)
        self.assertIn("if (busy || sendInFlight || sessionTurnBusy", send_source)

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

    def test_confirmed_completion_plays_a_primed_non_blocking_chime(self) -> None:
        sound_start = HUMAN_ADAM_HTML.index("function getCompletionAudioContext()")
        sound_end = HUMAN_ADAM_HTML.index("function syncControls()", sound_start)
        sound_source = HUMAN_ADAM_HTML[sound_start:sound_end]
        send_start = HUMAN_ADAM_HTML.index("async function sendMessage(event)")
        send_end = HUMAN_ADAM_HTML.index('connectBtn.addEventListener("click", connect);', send_start)
        send_source = HUMAN_ADAM_HTML[send_start:send_end]
        catch_start = send_source.index("} catch (error) {")

        self.assertIn("window.AudioContext || window.webkitAudioContext", sound_source)
        self.assertIn("async function primeCompletionSound()", sound_source)
        self.assertIn("async function playCompletionSound()", sound_source)
        self.assertIn("context.createBufferSource()", sound_source)
        self.assertIn("context.createBuffer(1, 1, 22050)", sound_source)
        self.assertIn("source.start(0);", sound_source)
        self.assertIn("context.createOscillator()", sound_source)
        self.assertIn("context.createGain()", sound_source)
        self.assertIn("Zvuk je pouze doplňkový", sound_source)
        self.assertLess(send_source.index("await primeCompletionSound();"), send_source.index('await api("/api/human-adam/send"'))
        self.assertLess(send_source.index('notice.textContent = "Odpověď doručena a potvrzena.";'), send_source.index("playCompletionSound();"))
        self.assertLess(send_source.index("playCompletionSound();"), catch_start)
        self.assertNotIn("playCompletionSound", send_source[catch_start:])

    def test_completion_sound_has_direct_ios_test_and_visibility_recovery(self) -> None:
        sound_start = HUMAN_ADAM_HTML.index("function getCompletionAudioContext()")
        sound_end = HUMAN_ADAM_HTML.index("function syncControls()", sound_start)
        sound_source = HUMAN_ADAM_HTML[sound_start:sound_end]

        self.assertIn('id="soundTestBtn"', HUMAN_ADAM_HTML)
        self.assertIn("Zvuk: vyzkoušet", HUMAN_ADAM_HTML)
        self.assertIn("async function testCompletionSound()", sound_source)
        self.assertIn("if (ready) await playCompletionSound();", sound_source)
        self.assertIn('["suspended", "interrupted"]', sound_source)
        self.assertIn("async function restoreCompletionAudioAfterVisibility()", sound_source)
        self.assertIn('soundTestBtn.addEventListener("click", testCompletionSound);', HUMAN_ADAM_HTML)
        self.assertIn('document.addEventListener("visibilitychange", restoreCompletionAudioAfterVisibility);', HUMAN_ADAM_HTML)

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
        api_call = send_source.index('await api("/api/human-adam/send"')

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
