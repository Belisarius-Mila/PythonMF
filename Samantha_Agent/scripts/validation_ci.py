#!/usr/bin/env python3
"""CI-only domain checks; scheduled/manual runs always use the whole suite.

This entrypoint never issues a local publication certificate. GitHub's event
selects the immutable base, while repository policy selects all test targets.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.communication.validation_policy import ValidationPlan, ValidationPolicyError, git, select_validation_plan


def event_base(name, event):
    if not isinstance(event, dict):
        return None
    if name in {'schedule', 'workflow_dispatch'}:
        return None
    if name == 'push':
        base = event.get('before')
    elif name == 'pull_request':
        pr = event.get('pull_request')
        parent = pr.get('base') if isinstance(pr, dict) else None
        base = parent.get('sha') if isinstance(parent, dict) else None
    else:
        return None
    return base if isinstance(base, str) and re.fullmatch('[0-9a-f]{40}', base) and base != '0'*40 else None


def ci_plan(repo, name, event):
    base = event_base(name, event)
    if base is None:
        return ValidationPlan('full', reason='scheduled_manual_or_unknown_ci_base'), None
    try:
        try:
            git(repo, 'cat-file', '-e', base+'^{commit}')
        except ValidationPolicyError:
            git(repo, 'fetch', '--no-tags', '--depth=1', 'origin', base)
        # Shallow checkout has no reliable ancestor graph. The immutable event
        # base still defines the entire candidate diff, including force pushes.
        paths = git(repo, 'diff', '--no-renames', '--name-only', '-z', base, 'HEAD', '--')
        names = tuple(os.fsdecode(p) for p in paths.split(b'\0') if p)
        return select_validation_plan(names, repo=repo, base=base), base
    except (OSError, ValueError, RuntimeError):
        return ValidationPlan('full', reason='ci_base_or_dependency_unavailable'), None


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    repo = Path(git(PROJECT_ROOT, 'rev-parse', '--show-toplevel').decode().strip())
    plan, base = ci_plan(repo, os.environ.get('GITHUB_EVENT_NAME', ''), event)
    print(json.dumps({'mode':plan.mode, 'reason':plan.reason, 'domains':plan.domains,
                      'modules':plan.modules, 'publication_receipt':False}), flush=True)
    if base:
        subprocess.run(['git', '-C', str(repo), 'diff', '--check', base, 'HEAD', '--'], check=True)
    command = [sys.executable, str(PROJECT_ROOT/'scripts/cockpit_quality_gate.py')]
    if plan.mode == 'targeted':
        command.extend(['--test-modules', *plan.modules])
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
