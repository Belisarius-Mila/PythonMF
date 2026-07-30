from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.documents.ai_metadata import (
    AIMetadataError,
    build_ai_metadata_prompt,
    parse_ai_metadata_answer,
    request_codex_metadata_suggestion,
)
from app.documents.scandocu import suggest_scandocu_candidate_metadata_with_ai


SYNTHETIC_TEXT = (
    "ACME Energie s.r.o.\n"
    "Vyúčtování elektrické energie\n"
    "Částku uhraďte nejpozději do 08.08.2026.\n"
)


def synthetic_answer(*, counterparty_evidence: str = "ACME Energie s.r.o.") -> str:
    return json.dumps(
        {
            "summary": "Jde o vyúčtování energie s termínem úhrady.",
            "metadata": {
                "title": {
                    "value": "Vyúčtování elektrické energie",
                    "confidence": "high",
                    "evidence": "Vyúčtování elektrické energie",
                },
                "domain": {
                    "value": "energy",
                    "confidence": "high",
                    "evidence": "elektrické energie",
                },
                "document_type": {
                    "value": "invoice",
                    "confidence": "medium",
                    "evidence": "Vyúčtování",
                },
                "counterparty": {
                    "value": "ACME Energie s.r.o.",
                    "confidence": "high",
                    "evidence": counterparty_evidence,
                },
                "related_asset": {
                    "value": None,
                    "confidence": "low",
                    "evidence": None,
                },
                "tags": {
                    "value": ["energie", "vyuctovani"],
                    "confidence": "medium",
                    "evidence": "Vyúčtování elektrické energie",
                },
            },
            "important_dates": [
                {
                    "date": "2026-08-08",
                    "type": "due_date",
                    "confidence": "high",
                    "evidence": "nejpozději do 08.08.2026",
                }
            ],
            "unknown_fields": ["related_asset"],
        },
        ensure_ascii=False,
    )


class FakeCodexClient:
    instances: list["FakeCodexClient"] = []

    def __init__(self, **kwargs: object) -> None:
        self.init_kwargs = kwargs
        self.start_kwargs: dict[str, object] = {}
        self.send_kwargs: dict[str, object] = {}
        self.__class__.instances.append(self)

    def __enter__(self) -> "FakeCodexClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def start_thread(self, **kwargs: object) -> str:
        self.start_kwargs = kwargs
        return "thread-synthetic"

    def send_text(self, **kwargs: object) -> SimpleNamespace:
        self.send_kwargs = kwargs
        return SimpleNamespace(answer=synthetic_answer())


class DocumentAIMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeCodexClient.instances.clear()

    def test_parser_accepts_only_evidence_backed_values(self) -> None:
        result = parse_ai_metadata_answer(
            answer=synthetic_answer(),
            source_name="synthetic-energy.pdf",
            source_text=SYNTHETIC_TEXT,
            current_metadata={
                "title": "synthetic energy",
                "domain": "other",
                "document_type": "document",
                "counterparty": "",
                "related_asset": "",
                "tags": [],
            },
            allowed_domains=["energy", "other"],
        )

        self.assertTrue(result["read_only"])
        self.assertFalse(result["persisted"])
        self.assertEqual(result["suggestion"]["domain"], "energy")
        self.assertEqual(result["suggestion"]["counterparty"], "ACME Energie s.r.o.")
        self.assertEqual(result["important_dates"][0]["date"], "2026-08-08")
        self.assertGreaterEqual(result["changed_count"], 4)

    def test_parser_drops_value_when_evidence_is_not_in_source(self) -> None:
        result = parse_ai_metadata_answer(
            answer=synthetic_answer(counterparty_evidence="Vymyšlená společnost"),
            source_name="synthetic-energy.pdf",
            source_text=SYNTHETIC_TEXT,
            current_metadata={},
            allowed_domains=["energy", "other"],
        )

        self.assertEqual(result["suggestion"]["counterparty"], "")
        self.assertTrue(any("Protistrana" in warning for warning in result["warnings"]))

    def test_codex_request_is_ephemeral_read_only_and_never_approved(self) -> None:
        result = request_codex_metadata_suggestion(
            source_name="synthetic-energy.pdf",
            source_text=SYNTHETIC_TEXT,
            current_metadata={"domain": "other"},
            allowed_domains=["energy", "other"],
            client_factory=FakeCodexClient,
            codex_binary="codex-test",
        )

        client = FakeCodexClient.instances[0]
        self.assertTrue(result["ok"])
        self.assertTrue(client.start_kwargs["ephemeral"])
        self.assertEqual(client.start_kwargs["sandbox"], "read-only")
        self.assertEqual(client.start_kwargs["approval_policy"], "never")
        self.assertEqual(client.send_kwargs["sandbox_policy"], {"type": "readOnly"})
        self.assertEqual(client.send_kwargs["approval_policy"], "never")
        self.assertIn("NEDŮVĚRYHODNÉHO TEXTU", str(client.send_kwargs["text"]))

    def test_empty_document_text_never_starts_codex(self) -> None:
        with self.assertRaisesRegex(AIMetadataError, "nemá použitelný text"):
            request_codex_metadata_suggestion(
                source_name="empty.pdf",
                source_text="",
                current_metadata={},
                allowed_domains=["other"],
                client_factory=FakeCodexClient,
            )
        self.assertEqual(FakeCodexClient.instances, [])

    def test_prompt_contains_schema_and_not_a_write_instruction(self) -> None:
        prompt = build_ai_metadata_prompt(
            source_name="synthetic-energy.pdf",
            source_text=SYNTHETIC_TEXT,
            current_metadata={"domain": "other"},
            allowed_domains=["energy", "other"],
        )
        self.assertIn('"important_dates"', prompt)
        self.assertIn("Současná metadata slouží jen ke srovnání", prompt)
        self.assertNotIn("ulož dokument", prompt.casefold())

    def test_scandocu_wrapper_reads_one_candidate_without_mutating_it(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            root = Path(temp_dir)
            vault = root / "documents"
            token = "synthetic-candidate"
            candidate_dir = vault / "scandocu" / "processing" / token
            candidate_dir.mkdir(parents=True)
            source = root / "synthetic-energy.txt"
            source.write_text(SYNTHETIC_TEXT, encoding="utf-8")
            record = {
                "token": token,
                "source_path": str(source),
                "working_path": str(source),
                "title": "synthetic energy",
                "domain": "other",
                "document_type": "document",
                "counterparty": "",
                "related_asset": "",
                "tags": [],
                "extraction_method": "plain-text",
                "ocr_needed": False,
                "due_date_count": 1,
            }
            metadata_path = candidate_dir / "candidate.json"
            metadata_path.write_text(json.dumps(record), encoding="utf-8")
            before = metadata_path.read_bytes()
            captured: dict[str, object] = {}

            def analyzer(**kwargs: object) -> dict[str, object]:
                captured.update(kwargs)
                return {"ok": True, "read_only": True, "persisted": False}

            result = suggest_scandocu_candidate_metadata_with_ai(
                token,
                vault_dir=vault,
                analyzer=analyzer,
            )

            self.assertTrue(result["read_only"])
            self.assertEqual(captured["source_text"], SYNTHETIC_TEXT)
            self.assertEqual(captured["current_metadata"]["domain"], "other")
            self.assertEqual(metadata_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
