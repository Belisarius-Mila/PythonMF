from __future__ import annotations

import copy
import json
import unittest

from app.communication.workstream_live_status import build_workstream_live_status


HEAD = "a" * 40
ORIGIN_HEAD = "a" * 40
STAMP = "0123456789abcdef"


def source_snapshot(**overrides):
    value = {
        "source_branch": "main",
        "source_head": HEAD,
        "source_pending_changes": 0,
        "private_path": "/private/never-return-this",
    }
    value.update(overrides)
    return value


def remote_snapshot(**overrides):
    value = {
        "state": "aligned",
        "local_head": HEAD,
        "origin_head": ORIGIN_HEAD,
        "read_only": True,
        "writes_performed": False,
        "changes": [{"path": "private/never-return-this"}],
    }
    value.update(overrides)
    return value


def workspace_snapshot(**overrides):
    value = {
        "ok": True,
        "prepared": True,
        "project_ready": True,
        "workspace_relation": "aligned",
        "dirty": False,
        "local_commit_count": 0,
        "source_pending_changes": 0,
        "remotes": [],
        "local_checkpoint_ahead": False,
        "local_checkpoint_preserved": False,
        "changes": ["private/never-return-this"],
    }
    value.update(overrides)
    return value


def deployment_snapshot(**overrides):
    value = {
        "state": "deployed",
        "main_head": HEAD,
        "expected_code_stamp": STAMP,
        "test_count": 1216,
        "smoke_count": 5,
        "gate_passed": True,
        "smoke_passed": True,
        "deployed_at": "2026-07-25T21:56:59+00:00",
        "receipt_path": "/private/never-return-this",
    }
    value.update(overrides)
    return value


def build(**overrides):
    values = {
        "workstream_id": "layer-human-adam-development",
        "observed_at": "2026-07-26T08:00:00+02:00",
        "source_snapshot": source_snapshot(),
        "remote_snapshot": remote_snapshot(),
        "workspace_snapshots": (
            workspace_snapshot(),
            workspace_snapshot(),
        ),
        "deployment_snapshot": deployment_snapshot(),
        "runtime_snapshot": {"reachable": True, "socket_path": "/private/socket"},
        "session_snapshot": {
            "connected": True,
            "turn_busy": False,
            "active_turn": None,
            "messages": [
                {
                    "status": "completed",
                    "user_text": "private message",
                    "answer": "private answer",
                }
            ],
        },
        "server_snapshot": {"code_stamp": STAMP, "pid": 12345},
    }
    values.update(overrides)
    return build_workstream_live_status(**values)


class WorkstreamLiveStatusTests(unittest.TestCase):
    def test_verified_current_status_is_redacted_and_read_only(self) -> None:
        result = build()
        encoded = json.dumps(result, ensure_ascii=False)

        self.assertEqual(result["state"], "current")
        self.assertTrue(result["read_only"])
        self.assertFalse(result["writes_performed"])
        self.assertEqual(result["main"]["state"], "aligned")
        self.assertEqual(result["main"]["head_short"], HEAD[:12])
        self.assertEqual(result["deployment"]["state"], "verified_current")
        self.assertEqual(result["workspaces"]["state"], "aligned_clean")
        self.assertEqual(result["runtime"]["state"], "connected")
        self.assertNotIn("private", encoded.casefold())
        self.assertNotIn("message", encoded.casefold())
        self.assertNotIn("path", encoded.casefold())
        self.assertNotIn("pid", encoded.casefold())

    def test_inputs_are_not_mutated(self) -> None:
        values = {
            "source_snapshot": source_snapshot(),
            "remote_snapshot": remote_snapshot(),
            "workspace_snapshots": [workspace_snapshot()],
            "deployment_snapshot": deployment_snapshot(),
            "runtime_snapshot": {"reachable": True},
            "session_snapshot": {"connected": False, "messages": []},
            "server_snapshot": {"code_stamp": STAMP},
        }
        before = copy.deepcopy(values)

        build(**values)

        self.assertEqual(values, before)

    def test_main_remote_drift_and_workspace_wip_require_attention(self) -> None:
        result = build(
            remote_snapshot=remote_snapshot(
                state="fast_forward_available",
                origin_head="b" * 40,
            ),
            workspace_snapshots=(
                workspace_snapshot(
                    workspace_relation="local_ahead",
                    local_commit_count=2,
                ),
            ),
        )

        self.assertEqual(result["state"], "attention_required")
        self.assertEqual(result["main"]["state"], "origin_ahead")
        self.assertEqual(result["workspaces"]["state"], "attention_required")
        self.assertEqual(result["workspaces"]["local_commit_count"], 2)
        self.assertEqual(
            result["workspaces"]["relation_counts"]["local_ahead"],
            1,
        )

    def test_deployment_for_other_main_is_never_reported_current(self) -> None:
        result = build(
            deployment_snapshot=deployment_snapshot(main_head="b" * 40),
        )

        self.assertEqual(result["state"], "attention_required")
        self.assertEqual(
            result["deployment"]["state"],
            "verified_other_main",
        )
        self.assertFalse(result["deployment"]["current_head"])

    def test_missing_server_stamp_keeps_current_head_unverified(self) -> None:
        result = build(server_snapshot={})

        self.assertEqual(result["state"], "unverified")
        self.assertEqual(
            result["deployment"]["state"],
            "current_head_server_unverified",
        )
        self.assertFalse(result["deployment"]["code_stamp_verified"])

    def test_pending_restart_and_code_mismatch_are_explicit(self) -> None:
        pending = build(
            deployment_snapshot={
                "state": "pending_restart",
                "main_head": HEAD,
                "test_count": 1216,
            }
        )
        mismatch = build(server_snapshot={"code_stamp": "fedcba9876543210"})

        self.assertEqual(pending["state"], "attention_required")
        self.assertEqual(pending["deployment"]["state"], "pending_restart")
        self.assertEqual(mismatch["state"], "attention_required")
        self.assertEqual(mismatch["deployment"]["state"], "code_mismatch")

    def test_latest_completed_message_closes_older_delivery_uncertainty(self) -> None:
        closed = build(
            session_snapshot={
                "connected": True,
                "turn_busy": False,
                "messages": [
                    {"status": "delivery_unknown", "user_text": "secret"},
                    {"status": "completed", "answer": "secret"},
                ],
            }
        )
        current = build(
            session_snapshot={
                "connected": True,
                "turn_busy": False,
                "messages": [
                    {"status": "completed", "answer": "secret"},
                    {"status": "delivery_unknown", "user_text": "secret"},
                ],
            }
        )

        self.assertEqual(closed["state"], "current")
        self.assertFalse(closed["runtime"]["delivery_uncertain"])
        self.assertEqual(current["state"], "attention_required")
        self.assertTrue(current["runtime"]["delivery_uncertain"])

    def test_invalid_identity_time_and_evidence_fail_closed(self) -> None:
        result = build(
            workstream_id="../../private",
            observed_at="not-a-time",
            source_snapshot=source_snapshot(source_head="secret"),
            remote_snapshot=remote_snapshot(
                read_only=False,
                writes_performed=True,
            ),
            workspace_snapshots=(),
            deployment_snapshot=deployment_snapshot(
                deployed_at="not-a-time",
            ),
            runtime_snapshot={},
            session_snapshot={},
            server_snapshot={"code_stamp": "not-a-stamp"},
        )

        self.assertEqual(result["state"], "unverified")
        self.assertEqual(result["workstream_id"], "unknown")
        self.assertEqual(result["observed_at"], "")
        self.assertEqual(result["main"]["state"], "unverified")
        self.assertEqual(result["deployment"]["state"], "unverified")
        self.assertEqual(result["workspaces"]["state"], "unverified")
        self.assertEqual(result["runtime"]["state"], "unverified")

    def test_missing_current_head_never_matches_deployment_prefix(self) -> None:
        result = build(
            source_snapshot=source_snapshot(source_head=""),
        )

        self.assertEqual(result["state"], "unverified")
        self.assertEqual(result["main"]["head_short"], "")
        self.assertEqual(
            result["deployment"]["state"],
            "verified_other_main",
        )
        self.assertFalse(result["deployment"]["current_head"])


if __name__ == "__main__":
    unittest.main()
