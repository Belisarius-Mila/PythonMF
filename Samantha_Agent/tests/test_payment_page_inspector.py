from __future__ import annotations

import unittest

from app.reminders.payment_page_inspector import (
    has_explicit_payment_page_inspection_confirmation,
    inspect_payment_page_for_reminder_text,
    inspect_payment_page_text,
)


RIXO_PAGE = """
<!doctype html>
<html>
  <head><title>Platba pojisteni</title></head>
  <body>
    <h1>Pojistka cislo 3275111280</h1>
    <p>Castka k uhrade: 4956.00 Kc</p>
    <p>Splatnost do 31.7.2026</p>
    <p>Pojisteni plati od 1.8.2026</p>
  </body>
</html>
"""

RIXO_PAYMENT_JSON = """
{
  "bankAccountNumber": "700135002/0800",
  "bankAccountIban": "CZ9008000000000700135002",
  "dueDate": "2026-08-01",
  "amount": 4956,
  "variableSymbol": "3275111280",
  "paymentFrequency": "YEARLY",
  "gatewayUrl": "https://moje-platba-gw.cpp.cz/payments-gateway-b4f/request-for-payment/secret-gateway-token",
  "product": {
    "name": "Autopojisteni Combi Plus IV",
    "provider": {"name": "Ceska podnikatelska pojistovna"}
  },
  "terms": {
    "dueDatePaymentGateway": "2026-07-31",
    "dueDateBankTransfer": "2026-07-30"
  },
  "contractValidityStartDate": "2026-08-01"
}
"""


class PaymentPageInspectorTests(unittest.TestCase):
    def test_confirmation_requires_domain_and_payment_context(self) -> None:
        self.assertTrue(
            has_explicit_payment_page_inspection_confirmation(
                domain="app.rixo.cz",
                confirmation_text=(
                    "Potvrzuji, prozkoumej read-only platebni stranku app.rixo.cz."
                ),
            )
        )
        self.assertFalse(
            has_explicit_payment_page_inspection_confirmation(
                domain="app.rixo.cz",
                confirmation_text="Potvrzuji, prozkoumej odkaz.",
            )
        )
        self.assertFalse(
            has_explicit_payment_page_inspection_confirmation(
                domain="app.rixo.cz",
                confirmation_text="app.rixo.cz",
            )
        )

    def test_extracts_due_date_start_date_amount_and_policy_number(self) -> None:
        inspection = inspect_payment_page_text(
            page_text=RIXO_PAGE,
            domain="app.rixo.cz",
            source_label="test",
        )

        self.assertEqual(inspection.policy_number, "3275111280")
        self.assertEqual(inspection.amount, "4956.00 Kc")
        self.assertEqual(inspection.due_date, "2026-07-31")
        self.assertEqual(inspection.due_confidence, "high")
        self.assertEqual(inspection.start_date, "2026-08-01")

    def test_tool_does_not_fetch_without_confirmation(self) -> None:
        calls: list[str] = []

        def fetcher(url: str, max_bytes: int) -> str:
            calls.append(url)
            return RIXO_PAGE

        result = inspect_payment_page_for_reminder_text(
            payment_url="https://app.rixo.cz/platba/secret-token",
            user_confirmed=False,
            confirmation_text="",
            fetcher=fetcher,
        )

        self.assertIn("Bez toho odkaz neoteviram", result)
        self.assertEqual(calls, [])

    def test_tool_returns_safe_summary_without_full_url_or_token(self) -> None:
        fetched_urls: list[str] = []

        def fetcher(url: str, max_bytes: int) -> str:
            fetched_urls.append(url)
            return RIXO_PAYMENT_JSON

        result = inspect_payment_page_for_reminder_text(
            payment_url="https://app.rixo.cz/platba/secret-token",
            user_confirmed=True,
            confirmation_text=(
                "Potvrzuji, prozkoumej read-only platebni stranku/fakturu app.rixo.cz."
            ),
            fetcher=fetcher,
        )

        self.assertIn("Domena: app.rixo.cz", result)
        self.assertIn("Cislo pojistky/smlouvy/faktury: 3275111280", result)
        self.assertIn("Castka: 4956 Kc", result)
        self.assertIn("Overena splatnost: 2026-07-31", result)
        self.assertIn("Splatnost pro platbu kartou/branu: 2026-07-31", result)
        self.assertIn("Splatnost pro bankovni prevod: 2026-07-30", result)
        self.assertIn("Pocatek pojisteni/sluzby: 2026-08-01", result)
        self.assertIn("verified_due_date=2026-07-31", result)
        self.assertIn("Domena platebni brany: moje-platba-gw.cpp.cz", result)
        self.assertEqual(
            fetched_urls,
            [
                "https://app.rixo.cz/be/api/public/quick-contracts/secret-token/payment",
            ],
        )
        self.assertNotIn("https://", result)
        self.assertNotIn("secret-token", result)
        self.assertNotIn("secret-gateway-token", result)

    def test_rejects_non_https_url(self) -> None:
        result = inspect_payment_page_for_reminder_text(
            payment_url="http://app.rixo.cz/platba/secret-token",
            user_confirmed=True,
            confirmation_text=(
                "Potvrzuji, prozkoumej read-only platebni stranku/fakturu app.rixo.cz."
            ),
            fetcher=lambda _url, _max_bytes: RIXO_PAGE,
        )

        self.assertIn("odmitnuta", result)
        self.assertIn("HTTPS", result)


if __name__ == "__main__":
    unittest.main()
