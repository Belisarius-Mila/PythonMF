"""Local hourly orchestration; no service installation or automatic activation."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Event
from zoneinfo import ZoneInfo

from app.file_persistence import FileLockTimeoutError, exclusive_file_lock
from .continuous_agent import ContinuousEmailAgent


PRAGUE = ZoneInfo("Europe/Prague")


def hourly_slot(now: datetime) -> str | None:
    if now.tzinfo is None:
        raise ValueError("Čas kontroly musí obsahovat časové pásmo.")
    local = now.astimezone(PRAGUE)
    if not 7 <= local.hour <= 22:
        return None
    return local.replace(minute=0, second=0, microsecond=0).isoformat()


class HourlyEmailScheduler:
    def __init__(self, worker: ContinuousEmailAgent):
        self.worker = worker

    def initialize_from_now(self, sources) -> None:
        """Explicit future activation boundary; never scans historical bodies."""
        with exclusive_file_lock(self.worker.root / "schedule", timeout=0):
            for source in sources:
                if source.key in self.worker.status()["sources"]:
                    continue
                cursor = source.baseline_cursor()
                self.worker._update(lambda d: d["sources"].__setitem__(source.key, cursor))

    def tick(self, sources, propose, *, now: datetime | None = None, batch_size: int = 20,
             max_batches: int = 20, should_stop=lambda: False) -> dict:
        now = now or datetime.now(timezone.utc)
        slot = hourly_slot(now)
        if slot is None:
            return {"status": "outside_hours", "proposals": 0}
        if not 1 <= batch_size <= 100 or max_batches < 1:
            raise ValueError("Neplatná velikost hodinové dávky.")
        sources = tuple(sources)
        if not sources or len({source.key for source in sources}) != len(sources):
            raise ValueError("Je třeba neprázdná sada různých zdrojů.")
        with exclusive_file_lock(self.worker.root / "schedule", timeout=0):
            state = self.worker.status()
            if state.get("schedule", {}).get("completed_slot") == slot:
                return {"status": "already_completed", "proposals": 0}
            if any(source.key not in state["sources"] for source in sources):
                return {"status": "needs_initialization", "proposals": 0}
            self.worker._update(lambda d: d.setdefault("schedule", {}).update(
                running_slot=slot, started_at=now.isoformat(), status="running"))
            total, complete = 0, True
            for source in sources:
                drained = False
                for _ in range(max_batches):
                    try:
                        result = self.worker.cycle(source, propose, limit=batch_size,
                                                   cycle_at=datetime.fromisoformat(slot), should_stop=should_stop)
                    except FileLockTimeoutError:
                        complete = False
                        break
                    total += result["proposals"]
                    if result["health"] != "ok":
                        complete = False
                        break
                    if result["fetched"] < batch_size:
                        drained = True
                        break
                else:
                    complete = False
                if "followups" in self.worker.status():
                    def source_proof(document):
                        document["sources"].setdefault(source.key, {})["followup_scan"] = {
                            "status": "complete" if drained else "incomplete",
                            "uidvalidity": document["sources"][source.key].get("uidvalidity", ""),
                            "as_of": result.get("scan_started_at", "") if drained else "",
                            "verified_at": result.get("scan_finished_at", "") if drained else "", "slot": slot}
                    self.worker._update(source_proof)
            def finish(document):
                schedule = document["schedule"]
                schedule.update(status="completed" if complete else "incomplete", running_slot="")
                if complete:
                    schedule["completed_slot"] = slot
                    schedule["completed_at"] = now.isoformat()
            self.worker._update(finish)
            return {"status": "completed" if complete else "incomplete", "proposals": total}

    def run(self, sources, propose, *, stop: Event, poll_seconds: float = 30) -> None:
        if poll_seconds <= 0:
            raise ValueError("Kontrolní interval musí být kladný.")
        sources = tuple(sources)
        while not stop.is_set():
            self.tick(sources, propose)
            stop.wait(poll_seconds)
