from __future__ import annotations

import unittest

from app.voice_bridge_state import (
    VoiceCommandState,
    VoiceCommandStateMachine,
    VoiceDeliveryOwner,
    inline_delivery_state,
    watcher_command_state,
)


class VoiceBridgeStateTests(unittest.TestCase):
    def test_watcher_route_has_one_owner_and_stops_at_queue(self) -> None:
        machine = VoiceCommandStateMachine()
        machine.transition(VoiceCommandState.PERSISTED, event="text_saved")
        machine.transition(
            VoiceCommandState.WATCHER_QUEUED,
            event="watcher_selected",
            owner=VoiceDeliveryOwner.WATCHER,
        )

        snapshot = machine.snapshot()
        self.assertEqual(snapshot["state"], "watcher_queued")
        self.assertEqual(snapshot["delivery_owner"], "watcher")
        self.assertFalse(snapshot["terminal"])

    def test_inline_route_reaches_verified_delivery(self) -> None:
        machine = VoiceCommandStateMachine()
        machine.transition(VoiceCommandState.PERSISTED, event="text_saved")
        machine.transition(
            VoiceCommandState.INLINE_DELIVERING,
            event="inline_selected",
            owner=VoiceDeliveryOwner.INLINE,
        )
        machine.transition(VoiceCommandState.DELIVERED, event="delivery_verified")

        self.assertEqual(machine.snapshot()["state"], "delivered")
        self.assertTrue(machine.snapshot()["terminal"])

    def test_owner_cannot_change_after_selection(self) -> None:
        machine = VoiceCommandStateMachine()
        machine.transition(VoiceCommandState.PERSISTED, event="saved")
        machine.transition(
            VoiceCommandState.INLINE_DELIVERING,
            event="inline_selected",
            owner=VoiceDeliveryOwner.INLINE,
        )

        with self.assertRaisesRegex(ValueError, "už vlastní inline"):
            machine.transition(
                VoiceCommandState.DELIVERED,
                event="wrong_owner",
                owner=VoiceDeliveryOwner.WATCHER,
            )

    def test_invalid_transition_is_rejected(self) -> None:
        machine = VoiceCommandStateMachine()

        with self.assertRaisesRegex(ValueError, "Nepovolený"):
            machine.transition(VoiceCommandState.DELIVERED, event="skip")

    def test_transcription_failure_is_terminal_without_owner(self) -> None:
        machine = VoiceCommandStateMachine()
        machine.transition(VoiceCommandState.TRANSCRIBING, event="transcription_started")
        machine.transition(VoiceCommandState.TRANSCRIPTION_FAILED, event="transcription_failed")

        snapshot = machine.snapshot()
        self.assertEqual(snapshot["delivery_owner"], "none")
        self.assertTrue(snapshot["terminal"])

    def test_inline_result_mapping_is_conservative(self) -> None:
        self.assertEqual(inline_delivery_state("voice_command_delivered"), VoiceCommandState.DELIVERED)
        self.assertEqual(
            inline_delivery_state("voice_command_delivery_unverified"),
            VoiceCommandState.DELIVERY_UNVERIFIED,
        )
        self.assertEqual(inline_delivery_state("anything_else"), VoiceCommandState.DELIVERY_FAILED)

    def test_watcher_can_resume_queue_and_finish_processing(self) -> None:
        machine = VoiceCommandStateMachine(
            state=VoiceCommandState.WATCHER_QUEUED,
            owner=VoiceDeliveryOwner.WATCHER,
        )
        machine.transition(VoiceCommandState.WATCHER_PROCESSING, event="watcher_picked_up")
        machine.transition(VoiceCommandState.AWAITING_ADAM, event="codex_work_pending")

        snapshot = machine.snapshot()
        self.assertEqual(snapshot["state"], "awaiting_adam")
        self.assertEqual(snapshot["delivery_owner"], "watcher")
        self.assertFalse(snapshot["terminal"])

    def test_watcher_helper_maps_pending_confirmation(self) -> None:
        snapshot = watcher_command_state(
            pending={"pending": True, "reason": "requires_confirmation"},
            command_ok=True,
        )

        self.assertEqual(snapshot["state"], "awaiting_confirmation")
        self.assertEqual(snapshot["delivery_owner"], "watcher")


if __name__ == "__main__":
    unittest.main()
