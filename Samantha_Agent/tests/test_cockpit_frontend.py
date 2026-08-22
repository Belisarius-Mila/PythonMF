from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from app import cockpit
from app.cockpit_frontend import (
    COCKPIT_HTML,
    EMAIL_ARCHIVE_HTML,
    EMAIL_PROCESSING_HTML,
    FRONTEND_JAVASCRIPT_MODULES,
    FRONTEND_ROOT,
    CockpitFrontendError,
    load_frontend_page,
)
from scripts.cockpit_quality_gate import node_binary


EXPECTED_PAGES = {
    "email_archive": (
        EMAIL_ARCHIVE_HTML,
        38462,
        1084,
        "159b198eeb662274f90d37328f0c846beac22129c9aabbdb5e609a01b9c418a1",
    ),
    "email_processing": (
        EMAIL_PROCESSING_HTML,
        68452,
        1423,
        "b180c0d76edf446e9e34906d4bbf6d545580aea4f9267844c69704847d692bf3",
    ),
    "cockpit": (
        COCKPIT_HTML,
        448757,
        9071,
        "78646415babac692173e7de030ddf60117072e7ac5445ff9d021373dfbc5a09b",
    ),
}


class CockpitFrontendContractTests(unittest.TestCase):
    def test_rendered_pages_keep_exact_pre_extraction_contract(self) -> None:
        for page_id, (rendered, length, line_count, expected_sha256) in EXPECTED_PAGES.items():
            with self.subTest(page_id=page_id):
                self.assertEqual(len(rendered), length)
                self.assertEqual(len(rendered.splitlines()), line_count)
                self.assertEqual(
                    hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
                    expected_sha256,
                )

    def test_asset_layout_and_composition(self) -> None:
        for page_id, (rendered, _length, _line_count, _sha256) in EXPECTED_PAGES.items():
            with self.subTest(page_id=page_id):
                page_dir = FRONTEND_ROOT / page_id
                template = (page_dir / "page.html").read_text(encoding="utf-8")
                styles = (page_dir / "styles.css").read_text(encoding="utf-8")
                javascript = (page_dir / "app.js").read_text(encoding="utf-8")
                modules = [
                    (page_dir / module_name).read_text(encoding="utf-8")
                    for module_name in FRONTEND_JAVASCRIPT_MODULES.get(page_id, ())
                ]

                self.assertEqual(template.count("{{SAMANTHA_CSS}}"), 1)
                self.assertEqual(template.count("{{SAMANTHA_JAVASCRIPT}}"), 1)
                self.assertNotIn("{{SAMANTHA_CSS}}", styles)
                self.assertNotIn("{{SAMANTHA_JAVASCRIPT}}", styles)
                self.assertNotIn("{{SAMANTHA_CSS}}", javascript)
                self.assertNotIn("{{SAMANTHA_JAVASCRIPT}}", javascript)
                for module in modules:
                    self.assertNotIn("{{SAMANTHA_CSS}}", module)
                    self.assertNotIn("{{SAMANTHA_JAVASCRIPT}}", module)
                self.assertEqual(load_frontend_page(page_id), rendered)

    def test_cockpit_uses_frontend_loader_instead_of_embedded_pages(self) -> None:
        source = Path(cockpit.__file__).read_text(encoding="utf-8")

        self.assertIn("from app.cockpit_frontend import (", source)
        self.assertNotIn('EMAIL_ARCHIVE_HTML = """', source)
        self.assertNotIn('EMAIL_PROCESSING_HTML = """', source)
        self.assertNotIn('COCKPIT_HTML = """', source)

    def test_cockpit_frontend_has_read_only_three_step_decision_view(self) -> None:
        for expected in (
            "Co teď?",
            "decisionCockpitStatus",
            "decisionCockpitList",
            "/api/decision-status",
            "items.slice(0, 3)",
            "Zdroj:",
            "Úplný katalog provozních položek",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, COCKPIT_HTML)

    def test_document_review_opens_exact_item_in_same_origin_scandocu(self) -> None:
        source = (FRONTEND_ROOT / "cockpit" / "app.js").read_text(encoding="utf-8")
        page = (FRONTEND_ROOT / "cockpit" / "page.html").read_text(encoding="utf-8")

        self.assertIn('action === "open_document_review"', source)
        self.assertIn('showMessage("Vyber dokument; celý se otevře se všemi možnostmi ve ScanDocu.")', source)
        self.assertIn('dashboardReviewBtn.addEventListener("click", openDocumentReviewPanel)', source)
        self.assertIn('scanDocuReviewBtn.addEventListener("click", () => openScanDocu({mode: "review", button: scanDocuReviewBtn}))', source)
        self.assertIn("await loadDocumentReviewReport()", source)
        self.assertIn("openScanDocuReview", source)
        self.assertIn('openBtn.textContent = "Vyřešit ve ScanDocu"', source)
        self.assertIn('body: JSON.stringify({mode, document_ref: documentRef})', source)
        self.assertNotIn("acceptDocumentReviewMetadataSuggestion", source)
        self.assertNotIn("updateDocumentReviewMetadata", source)
        self.assertNotIn('openBtn.textContent = "Doplnit metadata"', source)
        self.assertNotIn('openBtn.textContent = "Otevřít / číst"', source)
        self.assertEqual(page.count("<h3>Dokumenty k vyřešení</h3>"), 1)
        self.assertNotIn("Uložené dokumenty k revizi", page)
        self.assertNotIn("<h3>Dokumenty k revizi</h3>", page)
        self.assertNotIn("<h3>Klasifikace</h3>", page)
        self.assertNotIn('`${data.url}/?mode=review`', source)

    def test_health_recovery_autosave_is_an_extracted_frontend_module(self) -> None:
        page_dir = FRONTEND_ROOT / "cockpit"
        app_source = (page_dir / "app.js").read_text(encoding="utf-8")
        module_source = (page_dir / "health_recovery_autosave.js").read_text(encoding="utf-8")

        self.assertEqual(
            FRONTEND_JAVASCRIPT_MODULES["cockpit"],
            ("health_recovery_autosave.js",),
        )
        self.assertIn("createHealthRecoveryAutosaveFrontend", module_source)
        self.assertIn("async function runFrontendHealthCheck()", module_source)
        self.assertIn("async function openRecoveryModal()", module_source)
        self.assertIn("async function previewAutosaveCleanup(button)", module_source)
        self.assertIn("async function applyAutosaveCleanup()", module_source)
        self.assertIn('confirmation_text: "SMAZAT STARE AUTOSAVE"', module_source)
        self.assertNotIn("async function runFrontendHealthCheck()", app_source)
        self.assertNotIn("async function openRecoveryModal()", app_source)
        self.assertNotIn("function formatAutosaveCleanupPlan(data)", app_source)
        self.assertIn("window.SamanthaHealthRecoveryAutosave.create", app_source)
        self.assertLess(
            COCKPIT_HTML.index("createHealthRecoveryAutosaveFrontend"),
            COCKPIT_HTML.index("window.SamanthaHealthRecoveryAutosave.create"),
        )

    def test_health_recovery_autosave_module_runs_preview_through_injected_api(self) -> None:
        module_path = FRONTEND_ROOT / "cockpit" / "health_recovery_autosave.js"
        script = f"""
global.window = {{setTimeout, clearTimeout, confirm: () => false}};
global.document = {{createElement: () => ({{}})}};
global.performance = {{now: () => 0}};
require({json.dumps(str(module_path))});

const previewButton = {{disabled: false}};
const applyButton = {{disabled: true}};
const status = {{textContent: ""}};
const output = {{textContent: ""}};
const servicePanel = {{open: false}};
const calls = [];
const messages = [];
const errors = [];
const api = window.SamanthaHealthRecoveryAutosave.create({{
  elements: {{
    autosaveCleanupApplyBtn: applyButton,
    autosaveCleanupOutput: output,
    autosaveCleanupPreviewBtn: previewButton,
    autosaveCleanupStatus: status,
    dashboardAutosaveCleanupBtn: previewButton,
    servicePanel,
  }},
  postJson: async (url, payload) => {{
    calls.push({{url, payload}});
    return {{
      message: "Dry-run hotov.",
      plan: {{delete_count: 2, logical_gib: 1.25, allocated_gib: 0.75, keep_latest_snapshots: 12}},
      runtime: {{watcher_count: 1, disk_free_gib: 40, disk_state: "ok"}},
      disk_measurement: {{free_change_gib: null}},
    }};
  }},
  recordFrontendError: (error) => errors.push(String(error)),
  showMessage: (message) => messages.push(message),
}});

(async () => {{
  await api.previewAutosaveCleanup(previewButton);
  if (calls.length !== 1 || calls[0].url !== "/api/session-autosave/cleanup") throw new Error("wrong endpoint");
  if (calls[0].payload.apply !== false || calls[0].payload.keep_latest_snapshots !== 12) throw new Error("wrong preview payload");
  if (previewButton.disabled || applyButton.disabled) throw new Error("wrong button state");
  if (!servicePanel.open || status.textContent !== "Dry-run hotov.") throw new Error("wrong panel state");
  if (!output.textContent.includes("Logická velikost kandidátů: 1.250 GiB")) throw new Error("missing logical metric");
  if (!output.textContent.includes("Fyzicky alokované bloky kandidátů: 0.750 GiB")) throw new Error("missing allocated metric");
  if (!output.textContent.includes("Skutečná změna volného místa: změří se až po potvrzeném úklidu")) throw new Error("missing measured delta");
  if (errors.length || messages[0] !== "Dry-run hotov.") throw new Error("unexpected result");
  process.stdout.write("OK");
}})().catch((error) => {{ console.error(error); process.exitCode = 1; }});
"""
        completed = subprocess.run(
            [node_binary(), "-"],
            input=script,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "OK")

    def test_email_archive_frontend_is_a_human_readable_mailbox(self) -> None:
        for expected in (
            "Archivované",
            "S přílohami",
            "messageBackBtn",
            "body_text",
            "Otevřít přílohu",
            "Otevřít celé PDF",
            "AI přečíst e-mail",
            "/api/email-archive/ai-metadata",
            "Nic nebylo uloženo ani změněno",
            'aria-label="Rolovatelný výsledek AI"',
            "overflow-y: auto",
            "-webkit-overflow-scrolling: touch",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, EMAIL_ARCHIVE_HTML)

        for technical_label in ("Archive ID:", "UID:", "Metadata příloh", "Složka:"):
            with self.subTest(technical_label=technical_label):
                self.assertNotIn(technical_label, EMAIL_ARCHIVE_HTML)


class CockpitFrontendFailureTests(unittest.TestCase):
    def test_unknown_page_is_rejected(self) -> None:
        with self.assertRaises(CockpitFrontendError):
            load_frontend_page("unknown")

    def test_missing_asset_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page_dir = root / "cockpit"
            page_dir.mkdir()
            (page_dir / "page.html").write_text(
                "{{SAMANTHA_CSS}}{{SAMANTHA_JAVASCRIPT}}",
                encoding="utf-8",
            )
            (page_dir / "styles.css").write_text("", encoding="utf-8")

            with self.assertRaises(CockpitFrontendError):
                load_frontend_page("cockpit", frontend_root=root)

    def test_malformed_template_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page_dir = root / "cockpit"
            page_dir.mkdir()
            (page_dir / "page.html").write_text(
                "{{SAMANTHA_CSS}}{{SAMANTHA_CSS}}{{SAMANTHA_JAVASCRIPT}}",
                encoding="utf-8",
            )
            (page_dir / "styles.css").write_text("", encoding="utf-8")
            (page_dir / "health_recovery_autosave.js").write_text("", encoding="utf-8")
            (page_dir / "app.js").write_text("", encoding="utf-8")

            with self.assertRaises(CockpitFrontendError):
                load_frontend_page("cockpit", frontend_root=root)


if __name__ == "__main__":
    unittest.main()
