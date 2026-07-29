#!/usr/bin/env python3
"""Run small Cockpit domain test suites without replacing the release gate."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TIMEOUT_SECONDS = 120
RELEASE_GATE_COMMAND = ".venv/bin/python scripts/cockpit_quality_gate.py"


@dataclass(frozen=True)
class DomainSuite:
    description: str
    test_targets: tuple[str, ...]


DOMAIN_SUITES = {
    "email-archive": DomainSuite(
        description="Read-only backend, routy a výsledný frontend Archivu e-mailu.",
        test_targets=(
            "tests.test_email_archive_browser",
            (
                "tests.test_cockpit.CockpitTests."
                "test_email_archive_keeps_readonly_routes_and_embedded_frontend_contract"
            ),
            (
                "tests.test_cockpit_frontend.CockpitFrontendContractTests."
                "test_rendered_pages_keep_exact_pre_extraction_contract"
            ),
        ),
    ),
    "frontend": DomainSuite(
        description="Loader a kontrakty odděleného HTML, CSS a JavaScriptu Cockpitu.",
        test_targets=(
            "tests.test_cockpit_frontend",
            "tests.test_codex_approval_cockpit_contract",
            "tests.test_cockpit_voice_frontend_retirement",
        ),
    ),
    "http-security": DomainSuite(
        description="Společné HTTP ochrany, limity, hlavičky a bezpečné chyby.",
        test_targets=(
            "tests.test_cockpit_http_security",
        ),
    ),
}


class FastFeedbackError(ValueError):
    """Raised when a requested fast-feedback domain is unknown or missing."""


def resolve_test_targets(domains: Sequence[str]) -> tuple[str, ...]:
    clean_domains = tuple(str(domain or "").strip().casefold() for domain in domains)
    if not clean_domains:
        raise FastFeedbackError("Vyber alespoň jednu doménu.")

    targets: list[str] = []
    seen_targets: set[str] = set()
    for domain in clean_domains:
        suite = DOMAIN_SUITES.get(domain)
        if suite is None:
            raise FastFeedbackError(f"Neznámá D3 doména: {domain or '(prázdná)'}.")
        for target in suite.test_targets:
            if target in seen_targets:
                continue
            seen_targets.add(target)
            targets.append(target)
    return tuple(targets)


def unittest_command(targets: Sequence[str], *, verbose: bool = False) -> tuple[str, ...]:
    command = [sys.executable, "-m", "unittest"]
    if verbose:
        command.append("-v")
    command.extend(targets)
    return tuple(command)


def run_fast_feedback(
    domains: Sequence[str],
    *,
    verbose: bool = False,
    runner: object = subprocess.run,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> int:
    targets = resolve_test_targets(domains)
    command = unittest_command(targets, verbose=verbose)
    try:
        completed = runner(
            list(command),
            cwd=str(PROJECT_ROOT),
            timeout=int(timeout_seconds),
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(
            f"D3 fast feedback překročil limit {int(timeout_seconds)} s.",
            file=sys.stderr,
        )
        return 124
    except OSError as exc:
        print(f"D3 fast feedback nelze spustit: {exc}", file=sys.stderr)
        return 1
    return int(completed.returncode)


def format_suite_catalog() -> str:
    lines = ["D3 malé doménové testovací sady:"]
    for suite_id, suite in DOMAIN_SUITES.items():
        lines.append(f"- {suite_id}: {suite.description}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Spustí rychlou doménovou regresi Cockpitu. "
            "Nenahrazuje plnou Cockpit Quality Gate."
        )
    )
    parser.add_argument(
        "domains",
        nargs="*",
        metavar="DOMAIN",
        help="Jedna nebo více domén ze seznamu --list.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Vypíše dostupné domény a nic nespustí.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Vypíše jednotlivé unittesty.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    runner: object = subprocess.run,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list:
        print(format_suite_catalog())
        return 0
    try:
        targets = resolve_test_targets(args.domains)
    except FastFeedbackError as exc:
        parser.error(str(exc))

    print(
        "D3 fast feedback: "
        + ", ".join(str(domain).strip().casefold() for domain in args.domains),
        flush=True,
    )
    print(f"Test targets: {len(targets)}", flush=True)
    result = run_fast_feedback(
        args.domains,
        verbose=bool(args.verbose),
        runner=runner,
    )
    if result == 0:
        print("D3 fast feedback: OK")
        print(f"Release pojistka zůstává: {RELEASE_GATE_COMMAND}")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
