#!/usr/bin/env python3
"""Registered nonpaid recovery-guide preview/status and guarded run entrypoint."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.recovery_guide_sources import collect, target_preview
from app.recovery_guide_maintainer import status, weekly_slot
from app.recovery_guide_scheduler import inspect_status, schedule_preview


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("preview", "preflight", "runtime", "schedule-preview", "status", "run", "tick"), nargs="?", default="preview")
    args = parser.parse_args(argv)
    try:
        if args.action == "preview":
            snapshot = collect(Path.home() / "Desktop/OBNOVA_SAMANTHY_NOVY_MAC.txt", ROOT)
            result = {**snapshot.receipt(), "targets": target_preview(Path.home(), Path.home() / "Desktop/PythonMF"),
                      "schedule": schedule_preview(datetime.now(ZoneInfo("Europe/Prague"))),
                      "state": "inventory_review", "model_calls": 0, "writes": False,
                      "missing_before_live_pilot": ["approved_corpus_digest", "approved_exact_tokenizer",
                          "cost_trial_approval_and_limits", "dedicated_role_activation"],
                      "missing_before_schedule": ["accepted_candidate", "verified_icloud_upload_and_iphone",
                          "approved_schedule", "production_configuration_and_activation"]}
        elif args.action == "preflight":
            # Only this CLI process; no shared environment or project dependency
            # change. Upstream vocabulary downloads stay in the isolated pilot.
            os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(ROOT / ".venv/recovery_tokenizer/cache"))
            from app.recovery_guide_preflight import reference_preflight, tokenizer_probe
            probe = tokenizer_probe()
            if probe["state"] == "unavailable":
                result = {"state": "blocked_for_live_pilot", "model_calls": 0, "tokenizer": probe}
            else:
                result = reference_preflight(collect(Path.home() / "Desktop/OBNOVA_SAMANTHY_NOVY_MAC.txt", ROOT))
        elif args.action == "runtime":
            from app.recovery_guide_preflight import runtime_observation
            result = runtime_observation()
        elif args.action == "schedule-preview":
            result = {"state": "schedule_unapproved", **schedule_preview(datetime.now(ZoneInfo("Europe/Prague")))}
        elif args.action == "status":
            result = status(ROOT / "data/private/recovery_guide", weekly_slot(datetime.now(ZoneInfo("Europe/Prague"))))
            result["scheduler"] = inspect_status(ROOT / ".venv/recovery_guide_scheduler")
            result["activation_required"] = True
        else:
            # Intentionally no hidden fallback, default budget or implicit role
            # activation. A later reviewed activation connects the live adapter.
            result = {"state": "activation_required", "model_calls": 0, "writes": False,
                      "scheduler": inspect_status(ROOT / ".venv/recovery_guide_scheduler"),
                      "reason": "Pilot/rozpočet/tokenizer/role a provozní zapojení zatím nejsou aktivované."}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result["state"] in {"activation_required", "blocked_for_live_pilot"} else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"state": "attention", "model_calls": 0,
                          "reason": type(exc).__name__, "content_omitted": True}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
