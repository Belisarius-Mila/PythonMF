from __future__ import annotations

import unittest

from app.email.config import EmailConfigError
from app.email.models import EmailHeader
from app.email.tools import list_unified_email_headers_text


class EmailUnifiedToolsTests(unittest.TestCase):
    def test_unified_headers_include_source_and_sort_by_date(self) -> None:
        result = list_unified_email_headers_text(
            limit_per_source=5,
            icloud_provider_factory=lambda: _FakeProvider(
                [
                    EmailHeader(
                        internal_id="10",
                        date="Mon, 18 May 2026 08:00:00 +0200",
                        sender="Sender <sender@example.com>",
                        subject="iCloud older",
                    )
                ]
            ),
            seznam_provider_factory=lambda: _FakeProvider(
                [
                    EmailHeader(
                        internal_id="20",
                        date="Fri, 22 May 2026 09:00:00 +0200",
                        sender="Seznam <seznam@example.com>",
                        subject="Seznam newer",
                    )
                ]
            ),
        )

        self.assertLess(result.index("Zdroj: Seznam"), result.index("Zdroj: iCloud"))
        self.assertIn("UID: 20", result)
        self.assertIn("UID: 10", result)
        self.assertIn("Bezpecnost: jde jen o hlavicky.", result)
        self.assertNotIn("sender@example.com", result)

    def test_unified_headers_report_missing_source_without_failing_all(self) -> None:
        result = list_unified_email_headers_text(
            limit_per_source=5,
            icloud_provider_factory=lambda: _FakeProvider(
                [
                    EmailHeader(
                        internal_id="10",
                        date="Mon, 18 May 2026 08:00:00 +0200",
                        sender="Sender <sender@example.com>",
                        subject="iCloud present",
                    )
                ]
            ),
            seznam_provider_factory=_missing_config,
        )

        self.assertIn("Zdroj: iCloud", result)
        self.assertIn("Nedostupne zdroje:", result)
        self.assertIn("Seznam: chybi lokalni konfigurace pro Seznam Mail", result)

    def test_unified_headers_handles_no_available_sources(self) -> None:
        result = list_unified_email_headers_text(
            icloud_provider_factory=_missing_config,
            seznam_provider_factory=_missing_config,
        )

        self.assertIn("Nenasel jsem zadne dostupne e-mailove hlavicky.", result)
        self.assertIn("iCloud: chybi lokalni konfigurace pro iCloud Mail", result)
        self.assertIn("Seznam: chybi lokalni konfigurace pro Seznam Mail", result)


class _FakeProvider:
    def __init__(self, headers: list[EmailHeader]) -> None:
        self._headers = headers

    def list_recent_headers(self, limit: int = 10) -> list[EmailHeader]:
        return self._headers[:limit]


def _missing_config() -> object:
    raise EmailConfigError("missing test config")


if __name__ == "__main__":
    unittest.main()
