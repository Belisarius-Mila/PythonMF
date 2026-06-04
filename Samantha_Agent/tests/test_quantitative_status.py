from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.quantitative_status import (
    _iter_local_files,
    format_samantha_quantitative_status,
    run_samantha_quantitative_status,
)


class QuantitativeStatusTests(unittest.TestCase):
    def test_quantitative_status_counts_local_and_git_tracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            project_root = _project_root(repo_root)

            result = run_samantha_quantitative_status(
                project_root=project_root,
                repo_root=repo_root,
                runner=_runner(
                    ls_files="Samantha_Agent/app/main.py\nSamantha_Agent/README.md\n",
                    status="## main...origin/main\n",
                ),
            )

        self.assertEqual(result.local_stats[".py"].files, 2)
        self.assertEqual(result.local_stats[".md"].lines, 2)
        self.assertEqual(result.git_stats[".py"].files, 1)
        self.assertEqual(result.git_stats[".md"].files, 1)
        self.assertNotIn(".txt", result.git_stats)
        self.assertEqual(result.stored_path, None)

    def test_quantitative_status_save_appends_aggregate_jsonl_without_file_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            project_root = _project_root(repo_root)
            metrics_path = project_root / "data" / "metrics" / "status.jsonl"

            result = run_samantha_quantitative_status(
                save=True,
                project_root=project_root,
                repo_root=repo_root,
                metrics_path=metrics_path,
                runner=_runner(
                    ls_files="Samantha_Agent/app/main.py\nSamantha_Agent/README.md\n",
                    status="## main...origin/main\n M Samantha_Agent/app/main.py\n",
                ),
            )

            rows = [json.loads(line) for line in metrics_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(result.stored_path, metrics_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["scope"], "Samantha_Agent")
        self.assertEqual(rows[0]["totals"]["local"]["files"], 4)
        self.assertNotIn("main.py", json.dumps(rows[0], ensure_ascii=False))

    def test_format_quantitative_status_contains_markdown_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            project_root = _project_root(repo_root)

            text = format_samantha_quantitative_status(
                project_root=project_root,
                repo_root=repo_root,
                runner=_runner(
                    ls_files="Samantha_Agent/app/main.py\n",
                    status="## main...origin/main\n",
                ),
            )

        self.assertIn("Samantha Quantitative Status", text)
        self.assertIn("| Metrika | Lokalni | Git tracked |", text)
        self.assertIn("Lokalni objem podle typu:", text)
        self.assertIn("Git tracked objem podle typu:", text)

    def test_local_files_skip_runtime_temp_and_virtualenv_dirs(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            (root / "app").mkdir()
            (root / "app" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / ".venv_f5tts2" / "lib").mkdir(parents=True)
            (root / ".venv_f5tts2" / "lib" / "large.py").write_text("ignored\n", encoding="utf-8")
            (root / "tmpabc123").mkdir()
            (root / "tmpabc123" / "scratch.py").write_text("ignored\n", encoding="utf-8")
            (root / "data" / "tmp").mkdir(parents=True)
            (root / "data" / "tmp" / "scratch.py").write_text("ignored\n", encoding="utf-8")
            (root / "data" / "session_autosave").mkdir()
            (root / "data" / "session_autosave" / "autosave.txt").write_text("ignored\n", encoding="utf-8")

            relative_paths = {path.relative_to(root).as_posix() for path in _iter_local_files(root)}

        self.assertEqual(relative_paths, {"app/main.py"})


def _project_root(repo_root: Path) -> Path:
    project_root = repo_root / "Samantha_Agent"
    (project_root / "app").mkdir(parents=True)
    (project_root / "data" / "private").mkdir(parents=True)
    (project_root / "app" / "main.py").write_text("print('hello')\nprint('world')\n", encoding="utf-8")
    (project_root / "app" / "local_only.py").write_text("LOCAL = True\n", encoding="utf-8")
    (project_root / "README.md").write_text("# Title\nBody\n", encoding="utf-8")
    (project_root / "notes.txt").write_text("not tracked\n", encoding="utf-8")
    (project_root / "data" / "private" / "secret.md").write_text("secret\n", encoding="utf-8")
    return project_root


def _runner(*, ls_files: str, status: str):
    def run(args, **kwargs) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["git", "ls-files"]:
            return subprocess.CompletedProcess(args=args, returncode=0, stdout=ls_files, stderr="")
        if args[:3] == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(args=args, returncode=0, stdout=status, stderr="")
        raise AssertionError(f"Unexpected command: {args}")

    return run


if __name__ == "__main__":
    unittest.main()
