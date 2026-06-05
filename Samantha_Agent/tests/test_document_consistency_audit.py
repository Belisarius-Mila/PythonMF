from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.documents.consistency_audit import (
    format_document_consistency_audit,
    run_document_consistency_audit,
)


class DocumentConsistencyAuditTests(unittest.TestCase):
    def test_audit_reports_duplicate_reminders_and_parallel_policies_without_resolved_option_noise(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "cpp-predpis-pojistne-smlouvy-3270612451-2026",
                        "document_type": "insurance_payment_notice",
                        "domain": "insurance",
                        "counterparty": "ČPP",
                        "related_asset": "auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981",
                        "tags": ["auto", "pojisteni"],
                    },
                    {
                        "document_id": "rixo-navrh-pojistne-smlouvy-3275111280-2026",
                        "document_type": "insurance_policy",
                        "domain": "insurance",
                        "counterparty": "ČPP",
                        "related_asset": "auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981",
                        "tags": ["auto", "pojisteni"],
                    },
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {
                        "document_id": "cpp-predpis-pojistne-smlouvy-3270612451-2026",
                        "text": (
                            "PŘEDPIS POJISTNÉHO POJISTNÁ SMLOUVA | 3270612451. "
                            "Období: 1. 8. 2026 - 31. 7. 2027. "
                            "RZ / VIN: 4SN 8981 / YV1MV79L1G2335020. "
                            "Česká podnikatelská pojišťovna, a. s., Vienna Insurance Group. "
                            "Vaše nově předepsané pojistné činí 4 512 Kč/ ročně. "
                            "Roční pojistné za doplňkové pojištění nákladů na nájem "
                            "náhradního vozidla MAXI: 499 Kč. "
                            "Pojistné za pojistné období (navýšené o doplňkové "
                            "pojištění nákladů na nájem náhradního vozidla MAXI): 5 011 Kč."
                        ),
                    },
                    {
                        "document_id": "rixo-navrh-pojistne-smlouvy-3275111280-2026",
                        "text": (
                            "Číslo návrhu pojistné smlouvy 3275111280. "
                            "POJISTITEL Česká podnikatelská pojišťovna, a. s., Vienna Insurance Group. "
                            "Počátek pojištění: 01.08.2026 00:00. "
                            "Registrační značka (SPZ): 4SN8981. VOLVO V40 CROSS COUNTRY. "
                            "Pojistné za pojistné období - částka k úhradě: 4 956 Kč."
                        ),
                    },
                ],
            )
            reminders_path.write_text(
                json.dumps(
                    {
                        "reminders": [
                            self.reminder("rixo-reminder", "Zaplatit RIXO", "4 956 Kč"),
                            self.reminder("cpp-reminder", "Zaplatit ČPP", "4 512 Kč"),
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_document_consistency_audit(vault_dir=vault, reminders_path=reminders_path)
            codes = [item["code"] for item in result["findings"]]

            self.assertEqual(result["severity_counts"]["critical"], 1)
            self.assertIn("duplicate_open_payment_reminders", codes)
            self.assertIn("parallel_policy_paths_same_asset", codes)
            self.assertNotIn("multiple_payment_options_in_document", codes)
            formatted = format_document_consistency_audit(result)
            self.assertIn("VOLVO V40 SPZ 4SN8981", formatted)
            self.assertIn("4 512 Kč", formatted)
            self.assertIn("4 956 Kč", formatted)

    def test_audit_reports_payment_options_when_no_base_amount_reminder_resolves_them(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            index = vault / "index"
            index.mkdir(parents=True)
            reminders_path = root / "reminders.json"
            self.write_jsonl(
                index / "documents_index.jsonl",
                [
                    {
                        "document_id": "cpp-predpis-pojistne-smlouvy-3270612451-2026",
                        "document_type": "insurance_payment_notice",
                        "domain": "insurance",
                        "counterparty": "ČPP",
                        "related_asset": "auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981",
                        "tags": ["auto", "pojisteni"],
                    },
                ],
            )
            self.write_jsonl(
                index / "text_index.jsonl",
                [
                    {
                        "document_id": "cpp-predpis-pojistne-smlouvy-3270612451-2026",
                        "text": (
                            "Období: 1. 8. 2026 - 31. 7. 2027. "
                            "RZ / VIN: 4SN 8981 / YV1MV79L1G2335020. "
                            "Vaše nově předepsané pojistné činí 4 512 Kč/ ročně. "
                            "Roční pojistné za doplňkové pojištění nákladů na nájem "
                            "náhradního vozidla MAXI: 499 Kč. "
                            "Pojistné za pojistné období (navýšené o doplňkové "
                            "pojištění nákladů na nájem náhradního vozidla MAXI): 5 011 Kč."
                        ),
                    },
                ],
            )
            reminders_path.write_text(json.dumps({"reminders": []}), encoding="utf-8")

            result = run_document_consistency_audit(vault_dir=vault, reminders_path=reminders_path)
            codes = [item["code"] for item in result["findings"]]

            self.assertIn("multiple_payment_options_in_document", codes)

    @staticmethod
    def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

    @staticmethod
    def reminder(reminder_id: str, title: str, amount: str) -> dict[str, object]:
        return {
            "id": reminder_id,
            "title": title,
            "notes": f"Pojistka 3275111280 nebo 3270612451, částka {amount}.",
            "due_date": "2026-08-01",
            "priority": "high",
            "status": "open",
            "related_asset": "auto VOLVO V40 CROSS COUNTRY SPZ 4SN8981",
            "coverage_start": "2026-08-01",
            "amount_due": amount,
            "source": {
                "type": "private_document",
                "uid": reminder_id,
                "date": "",
                "sender": "Private document vault",
            },
            "links": [],
            "attachments": [],
        }


if __name__ == "__main__":
    unittest.main()
