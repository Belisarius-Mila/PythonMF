from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from app import cockpit
from app.cockpit_frontend import (
    COCKPIT_HTML,
    EMAIL_ARCHIVE_HTML,
    EMAIL_PROCESSING_HTML,
    FRONTEND_ROOT,
    CockpitFrontendError,
    load_frontend_page,
)


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
        416234,
        8424,
        "5ee4682c058741e182e997ae319efd5f61a0fa726e8cd70b034684ce0d2753e3",
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

                self.assertEqual(template.count("{{SAMANTHA_CSS}}"), 1)
                self.assertEqual(template.count("{{SAMANTHA_JAVASCRIPT}}"), 1)
                self.assertNotIn("{{SAMANTHA_CSS}}", styles)
                self.assertNotIn("{{SAMANTHA_JAVASCRIPT}}", styles)
                self.assertNotIn("{{SAMANTHA_CSS}}", javascript)
                self.assertNotIn("{{SAMANTHA_JAVASCRIPT}}", javascript)
                self.assertEqual(load_frontend_page(page_id), rendered)

    def test_cockpit_uses_frontend_loader_instead_of_embedded_pages(self) -> None:
        source = Path(cockpit.__file__).read_text(encoding="utf-8")

        self.assertIn("from app.cockpit_frontend import (", source)
        self.assertNotIn('EMAIL_ARCHIVE_HTML = """', source)
        self.assertNotIn('EMAIL_PROCESSING_HTML = """', source)
        self.assertNotIn('COCKPIT_HTML = """', source)

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
            (page_dir / "app.js").write_text("", encoding="utf-8")

            with self.assertRaises(CockpitFrontendError):
                load_frontend_page("cockpit", frontend_root=root)


if __name__ == "__main__":
    unittest.main()
