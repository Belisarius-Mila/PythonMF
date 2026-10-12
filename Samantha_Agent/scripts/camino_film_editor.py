#!/usr/bin/env python3
"""Registered local real-day film render; never changes the Camino service."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.camino_film_editor import production_editor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "render", "work"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--project-id")
    args = parser.parse_args()
    editor = production_editor()
    if args.action == "work":
        if not args.project_id:
            parser.error("work requires --project-id")
        editor.run_queue(args.project_id)
        return 0
    view = editor.view()
    requested = []
    if args.action == "render":
        if not args.execute:
            parser.error("render requires --execute")
        for profile in ("preview", "final"):
            queued = editor.enqueue({"project_id": view["project_id"], "revision": view["revision"],
                "request_id": str(uuid4()), "profile": profile, "range": None}, background=False)
            requested.append(queued["job_id"])
        editor.run_queue(view["project_id"])
        view = editor.view()
    print(json.dumps({k:view[k] for k in ("ok", "local_date", "revision", "duration_ms")} |
                     {"jobs": [{k:v for k,v in j.items() if k not in ("job_id", "url")} for j in view["jobs"]]}))
    states = {j["job_id"]: j["state"] for j in view["jobs"]}
    return 0 if args.action == "status" or all(states.get(job_id) == "ready" for job_id in requested) else 1


if __name__ == "__main__":
    raise SystemExit(main())
