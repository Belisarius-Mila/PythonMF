from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.decision_cockpit import (
    build_decision_cockpit,
    extract_handoff_next_step,
    load_handoff_next_steps,
)
from app.memory_truth_audit import (
    STATUS_CANDIDATE_DRIFT,
    STATUS_PROVEN_CONTRADICTION,
    STATUS_REGISTRY_CONSISTENT,
)


GENERATED_AT = "2026-08-18T12:00:00+02:00"


def memory_row(
    workstream_id: str,
    *,
    name: str,
    priority: str = "1",
    mode: str = "active",
    status: str = STATUS_REGISTRY_CONSISTENT,
    committed_at: str | None = "2026-08-10T09:00:00+02:00",
    contradictions: tuple[str, ...] = (),
    handoff_path: str = "memory/handoffs/workstreams/example.md",
    handoff_exists: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        workstream_id=workstream_id,
        name=name,
        expected_priority=priority,
        expected_mode=mode,
        status=status,
        canonical_latest_committed_at=committed_at,
        contradictions=contradictions,
        handoff_path=handoff_path,
        handoff_exists=handoff_exists,
    )


def memory_truth(*rows: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(generated_at=GENERATED_AT, rows=rows)


class DecisionCockpitTests(unittest.TestCase):
    def test_selects_at_most_three_and_deduplicates_same_navigation(self) -> None:
        queue = {
            "items": [
                {
                    "kind": "reminder",
                    "priority": 1,
                    "title": "První připomínka",
                    "detail": "Po termínu",
                    "action": "open_reminders",
                    "action_label": "Otevřít připomenutí",
                },
                {
                    "kind": "reminder",
                    "priority": 1,
                    "title": "Druhá připomínka",
                    "detail": "Po termínu",
                    "action": "open_reminders",
                    "action_label": "Otevřít připomenutí",
                },
                {
                    "kind": "document_problem",
                    "priority": 1,
                    "title": "Nečitelný dokument",
                    "detail": "Ruční kontrola",
                    "action": "open_scandocu",
                    "action_label": "Otevřít ScanDocu",
                },
            ]
        }
        truth = memory_truth(
            memory_row(
                "project-conflict",
                name="Konfliktní projekt",
                status=STATUS_PROVEN_CONTRADICTION,
                contradictions=("mode_mismatch:x:expected=paused:actual=active",),
            ),
            memory_row("project-alpha", name="Alpha"),
        )

        result = build_decision_cockpit(
            action_queue=queue,
            memory_truth=truth,
            handoff_next_steps={"project-alpha": "Pokračovat v Alpha."},
            generated_at=GENERATED_AT,
        )

        self.assertTrue(result["read_only"])
        self.assertEqual(len(result["items"]), 3)
        self.assertEqual(
            [item["title"] for item in result["items"]],
            ["První připomínka", "Nečitelný dokument", "Srovnat stav projektu Konfliktní projekt"],
        )
        self.assertEqual(result["items"][0]["freshness"], "live")
        self.assertTrue(all(item["navigation"] in {"open_reminders", "open_scandocu", "open_projects"} for item in result["items"]))
        self.assertEqual(
            [item["id"] for item in result["memory_suggestions"]],
            ["handoff:project-alpha"],
        )

    def test_only_live_evidence_is_current_and_handoffs_are_suggestions(self) -> None:
        truth = memory_truth(
            memory_row(
                "project-conflict",
                name="Konflikt",
                status=STATUS_PROVEN_CONTRADICTION,
                contradictions=("priority_mismatch:x:expected=2:actual=1",),
            ),
            memory_row("project-old", name="Starý P1"),
            memory_row(
                "project-drift",
                name="Novější handoff",
                priority="2",
                status=STATUS_CANDIDATE_DRIFT,
                committed_at="2026-08-18T08:00:00+02:00",
            ),
        )

        result = build_decision_cockpit(
            action_queue={"items": []},
            memory_truth=truth,
            handoff_next_steps={
                "project-old": "Historický krok.",
                "project-drift": "Použít novější konkrétní krok.",
            },
            generated_at=GENERATED_AT,
        )

        self.assertEqual(
            [item["id"] for item in result["items"]],
            ["memory-conflict:project-conflict"],
        )
        self.assertEqual(result["message"], "1 aktuální ToDo podle živého důkazu.")
        self.assertEqual(
            [item["id"] for item in result["memory_suggestions"]],
            ["handoff:project-drift", "handoff:project-old"],
        )
        self.assertEqual(result["memory_suggestions"][0]["freshness"], "today")
        self.assertEqual(result["memory_suggestions"][1]["freshness"], "historical")
        self.assertIn("8 d.", result["memory_suggestions"][1]["freshness_label"])
        self.assertIn("2 návrhy", result["memory_message"])

    def test_historical_handoffs_never_fill_missing_current_slots(self) -> None:
        result = build_decision_cockpit(
            action_queue={
                "items": [
                    {
                        "kind": "document_review",
                        "priority": 2,
                        "title": "Zkontrolovat dokument",
                        "detail": "Živá fronta dokumentů",
                        "action": "open_document_review",
                    }
                ]
            },
            memory_truth=memory_truth(
                memory_row("project-one", name="První projekt"),
                memory_row("project-two", name="Druhý projekt", priority="2"),
            ),
            handoff_next_steps={
                "project-one": "Starý první krok.",
                "project-two": "Starý druhý krok.",
            },
            generated_at=GENERATED_AT,
        )

        self.assertEqual([item["title"] for item in result["items"]], ["Zkontrolovat dokument"])
        self.assertEqual(len(result["memory_suggestions"]), 2)
        self.assertEqual(result["message"], "1 aktuální ToDo podle živého důkazu.")

    def test_partial_result_keeps_live_items_and_rejects_unknown_navigation(self) -> None:
        result = build_decision_cockpit(
            action_queue={
                "items": [
                    {
                        "kind": "unsafe",
                        "priority": 2,
                        "title": "Jen vysvětlit",
                        "detail": "Bez spuštění akce",
                        "action": "delete_everything",
                    }
                ]
            },
            memory_truth=None,
            generated_at=GENERATED_AT,
            memory_truth_error="Audit není dostupný.",
        )

        self.assertEqual(result["source_status"], "partial")
        self.assertEqual(result["source_warning"], "Audit není dostupný.")
        self.assertEqual(result["items"][0]["navigation"], "")
        self.assertEqual(result["memory_suggestions"], [])

    def test_extracts_only_first_canonical_next_step(self) -> None:
        text = """## Aktuální stav
Hotovo.

### Další krok
- Udělat první bezpečný krok.
- Druhý krok se nemá zobrazit.

### Rozhodnutí
Beze změny.
"""

        self.assertEqual(
            extract_handoff_next_step(text),
            "Udělat první bezpečný krok.",
        )

    def test_handoff_loader_stays_inside_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            handoff = root / "memory" / "handoffs" / "workstreams" / "alpha.md"
            handoff.parent.mkdir(parents=True)
            handoff.write_text("### Další krok\n- Ověřit výsledek.\n", encoding="utf-8")
            truth = memory_truth(
                memory_row(
                    "project-alpha",
                    name="Alpha",
                    handoff_path="memory/handoffs/workstreams/alpha.md",
                ),
                memory_row(
                    "project-outside",
                    name="Mimo",
                    handoff_path="../outside.md",
                ),
            )

            result = load_handoff_next_steps(truth, project_root=root)

        self.assertEqual(result, {"project-alpha": "Ověřit výsledek."})


if __name__ == "__main__":
    unittest.main()
