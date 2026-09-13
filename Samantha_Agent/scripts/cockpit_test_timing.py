"""Optional unittest timing without changing suite order or success semantics."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Callable, Sequence, TextIO


class TimingResult(unittest.TextTestResult):
    def __init__(self, *args, clock: Callable[[], float] = time.perf_counter, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock = clock
        self.timings: list[dict[str, object]] = []
        self.started = 0.0

    def startTest(self, test) -> None:
        self.started = self.clock()
        super().startTest(test)

    def stopTest(self, test) -> None:
        elapsed = self.clock() - self.started
        # Never call custom test.id()/str(test), or persist output/tracebacks.
        module = test.__class__.__module__
        name = f"{test.__class__.__qualname__}.{getattr(test, '_testMethodName', 'unknown')}"
        self.timings.append({
            "module": re.sub(r"[^a-zA-Z0-9_.]", "_", module),
            "test": re.sub(r"[^a-zA-Z0-9_.]", "_", name),
            "seconds": elapsed,
        })
        super().stopTest(test)


def run_timed_suite(
    suite: unittest.TestSuite,
    *,
    load_seconds: float = 0.0,
    stream: TextIO | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> tuple[unittest.TestResult, dict[str, object]]:
    runner = unittest.TextTestRunner(
        stream=stream,
        warnings=None if sys.warnoptions else "default",
        resultclass=lambda *args, **kwargs: TimingResult(*args, clock=clock, **kwargs),
    )
    started = clock()
    result = runner.run(suite)
    run_seconds = clock() - started
    groups = defaultdict(lambda: {"test_count": 0, "seconds": 0.0})
    for row in result.timings:
        group = groups[row["module"]]
        group["test_count"] += 1
        group["seconds"] += row["seconds"]
    measured = sum(row["seconds"] for row in result.timings)
    report = {
        "schema_version": 1,
        "success": result.wasSuccessful() and result.testsRun > 0,
        "test_count": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "load_seconds": load_seconds,
        "run_seconds": run_seconds,
        "measured_test_seconds": measured,
        "unmeasured_run_seconds": max(0.0, run_seconds - measured),
        "measurement_scope": "Test durations include per-test setup/teardown. Module/class fixtures and runner overhead are unmeasured_run_seconds; imports/loading are load_seconds.",
        "modules": sorted(
            [{"module": name, **values} for name, values in groups.items()],
            key=lambda row: (-row["seconds"], row["module"]),
        ),
        "slowest_tests": sorted(result.timings, key=lambda row: -row["seconds"])[:30],
    }
    return result, report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("modules", nargs="+")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromNames(args.modules)
    load_seconds = time.perf_counter() - started
    result, report = run_timed_suite(suite, load_seconds=load_seconds)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\nSlowest test modules (per-test setup/teardown included):")
    for row in report["modules"][:10]:
        print(f"  {row['seconds']:8.3f}s  {row['test_count']:4d} tests  {row['module']}")
    print(f"Load/import: {load_seconds:.3f}s; other run overhead: {report['unmeasured_run_seconds']:.3f}s")
    if result.testsRun == 0:
        return 5
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
