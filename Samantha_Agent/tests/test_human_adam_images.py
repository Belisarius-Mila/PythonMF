from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.communication.human_adam_images import (
    HumanAdamImageCandidateStore,
    HumanAdamImageError,
    generation_confirmation,
    human_adam_image_candidates_action,
    human_adam_image_decision_action,
    human_adam_image_file_action,
    human_adam_image_generate_action,
    human_adam_image_prepare_action,
    import_completed_generated_images,
    is_image_generation_request,
    prepare_image_prompt,
)
from app.communication.human_adam_workstream_catalog import (
    CanonicalWorkstreamCapabilities,
)


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"private-test-image"
HUMAN_ADAM_TEST_WORKSTREAM_ID = "layer-human-adam-development"


class FakeImages:
    def __init__(self, raw: bytes = PNG_BYTES):
        self.raw = raw
        self.calls: list[dict[str, object]] = []

    def generate(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=base64.b64encode(self.raw).decode("ascii"))]
        )


class FakeClient:
    def __init__(self, raw: bytes = PNG_BYTES):
        self.images = FakeImages(raw)


class FakeService:
    def __init__(
        self,
        workstream_id: str = HUMAN_ADAM_TEST_WORKSTREAM_ID,
        *,
        capabilities: object | None = None,
        durable_generation: bool = False,
    ):
        self.active_workstream_id = workstream_id
        configured = capabilities or CanonicalWorkstreamCapabilities(
            image_generation=True
        )
        self.workstream_backends = SimpleNamespace(
            binding=lambda _workstream_id: SimpleNamespace(
                record=SimpleNamespace(capabilities=configured)
            )
        )
        self.trusted_external_generation_consent = SimpleNamespace(
            status=lambda: {
                "consent_id": "trusted_external_generation_v1",
                "enabled": durable_generation,
                "state": "active" if durable_generation else "missing",
            }
        )


class HumanAdamImageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "candidates"
        self.store = HumanAdamImageCandidateStore(self.root)
        self.service = FakeService()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prepare(
        self,
        suffix: str = "one",
        *,
        workstream_id: str = HUMAN_ADAM_TEST_WORKSTREAM_ID,
    ) -> dict[str, object]:
        return self.store.prepare(
            request_text="Vygeneruj obrázek modré sovy na šířku.",
            client_message_id=f"human-adam-message-{suffix}",
            workstream_id=workstream_id,
        )

    def generate(self, suffix: str = "one") -> tuple[dict[str, object], FakeClient]:
        record = self.prepare(suffix)
        client = FakeClient()
        generated = self.store.generate(
            candidate_id=str(record["candidate_id"]),
            confirmation=generation_confirmation(str(record["candidate_id"])),
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
            client=client,
        )
        return generated, client

    def test_text_request_prepares_prompt_and_allowlisted_parameters(self) -> None:
        self.assertTrue(is_image_generation_request("Nakresli ilustraci domu na výšku."))

        prompt, parameters = prepare_image_prompt(
            "Vytvoř obrázek zahrady na výšku ve vysoké kvalitě."
        )

        self.assertIn("Vytvoř obrázek zahrady", prompt)
        self.assertEqual(parameters["model"], "gpt-image-2")
        self.assertEqual(parameters["size"], "1024x1536")
        self.assertEqual(parameters["quality"], "high")
        self.assertEqual(parameters["output_format"], "png")

    def test_prepare_persists_private_preview_without_image_or_api_call(self) -> None:
        record = self.prepare()
        public = self.store.public(record)

        self.assertEqual(record["status"], "prepared")
        self.assertFalse(list(self.root.rglob("image.*")))
        self.assertTrue(public["confirmation_text"].endswith(str(record["candidate_id"])))
        self.assertEqual(public["image_url"], "")
        serialized = json.dumps(public, ensure_ascii=False)
        self.assertNotIn("b64", serialized.casefold())
        self.assertNotIn(str(self.root), serialized)

    def test_generation_requires_candidate_specific_confirmation_before_client_call(self) -> None:
        record = self.prepare()
        client = FakeClient()

        with self.assertRaisesRegex(HumanAdamImageError, "samostatné přesné potvrzení"):
            self.store.generate(
                candidate_id=str(record["candidate_id"]),
                confirmation="ano",
                workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
                client=client,
            )

        self.assertEqual(client.images.calls, [])
        self.assertEqual(
            self.store.public_list(workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID)[0]["status"],
            "prepared",
        )

    def test_confirmed_generation_uses_allowlisted_parameters_and_create_only_file(self) -> None:
        generated, client = self.generate()
        public = self.store.public(generated)

        self.assertEqual(generated["status"], "generated")
        self.assertEqual(len(client.images.calls), 1)
        self.assertEqual(client.images.calls[0]["model"], "gpt-image-2")
        self.assertEqual(client.images.calls[0]["size"], "1536x1024")
        self.assertEqual(client.images.calls[0]["n"], 1)
        self.assertEqual(public["image_url"], f'/api/human-adam/images/file?id={generated["candidate_id"]}')
        self.assertNotIn("path", public)
        self.assertNotIn("request_text", public)

    def test_completed_turn_imports_multiple_images_idempotently(self) -> None:
        outputs = [
            {
                "item_id": f"exec-image-{index:08d}",
                "result": base64.b64encode(PNG_BYTES + bytes([index])).decode("ascii"),
                "revised_prompt": f"Smyšlená sova {index}",
            }
            for index in range(1, 5)
        ]

        first = self.store.import_generated_images(
            client_message_id="human-adam-message-gallery",
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
            request_text="Vygeneruj čtyři obrázky smyšlené sovy.",
            generated_images=outputs,
        )
        repeated = self.store.import_generated_images(
            client_message_id="human-adam-message-gallery",
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
            request_text="Vygeneruj čtyři obrázky smyšlené sovy.",
            generated_images=outputs,
        )
        public = self.store.public_list(
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID
        )

        self.assertEqual(len(first), 4)
        self.assertEqual(
            [record["candidate_id"] for record in repeated],
            [record["candidate_id"] for record in first],
        )
        self.assertEqual(len(public), 4)
        self.assertEqual([candidate["version"] for candidate in public], [1, 2, 3, 4])
        self.assertTrue(all(candidate["status"] == "generated" for candidate in public))
        self.assertTrue(all(candidate["image_url"] for candidate in public))
        self.assertNotIn("source_item_id", json.dumps(public, ensure_ascii=False))
        self.assertNotIn("aW1hZ2U", json.dumps(public, ensure_ascii=False))

    def test_transient_import_action_returns_only_safe_candidate_ids(self) -> None:
        result = import_completed_generated_images(
            service=self.service,
            client_message_id="human-adam-message-import",
            request_text="Vygeneruj obrázek smyšlené sovy.",
            generated_images=[
                {
                    "item_id": "exec-image-import-12345678",
                    "result": base64.b64encode(PNG_BYTES).decode("ascii"),
                    "revised_prompt": "Smyšlená sova",
                }
            ],
            store=self.store,
        )

        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["imported_count"], 1)
        self.assertRegex(result["candidate_ids"][0], r"^img_[0-9a-f]{32}$")
        serialized = json.dumps(result)
        self.assertNotIn("aW1hZ2U", serialized)
        self.assertNotIn("source_item", serialized)

    def test_active_durable_consent_replaces_candidate_specific_confirmation(self) -> None:
        record = self.prepare("durable")
        client = FakeClient()
        service = FakeService(durable_generation=True)

        result = human_adam_image_generate_action(
            {"candidate_id": record["candidate_id"], "confirmation": ""},
            service=service,
            store=self.store,
            client=client,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate"]["status"], "generated")
        self.assertEqual(len(client.images.calls), 1)

    def test_missing_durable_consent_keeps_candidate_confirmation_gate(self) -> None:
        record = self.prepare("no-durable")
        client = FakeClient()

        result = human_adam_image_generate_action(
            {"candidate_id": record["candidate_id"], "confirmation": ""},
            service=self.service,
            store=self.store,
            client=client,
        )

        self.assertFalse(result["ok"])
        self.assertIn("samostatné přesné potvrzení", result["message"])
        self.assertEqual(client.images.calls, [])

    def test_durable_consent_does_not_cover_obviously_sensitive_prompt(self) -> None:
        record = self.store.prepare(
            request_text="Vygeneruj obrázek podle data/private/dokument.txt.",
            client_message_id="human-adam-message-sensitive",
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
        )
        client = FakeClient()

        result = human_adam_image_generate_action(
            {"candidate_id": record["candidate_id"], "confirmation": ""},
            service=FakeService(durable_generation=True),
            store=self.store,
            client=client,
        )

        self.assertFalse(result["ok"])
        self.assertIn("vypadá citlivě", result["message"])
        self.assertEqual(client.images.calls, [])

    def test_safe_image_load_returns_only_file_inside_candidate_directory(self) -> None:
        generated, _client = self.generate()

        path, mime_type = self.store.image_path(
            str(generated["candidate_id"]),
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
        )

        self.assertEqual(path.parent, self.root.resolve() / str(generated["candidate_id"]))
        self.assertEqual(path.name, "image.png")
        self.assertEqual(mime_type, "image/png")

    def test_approval_marks_only_exact_generated_version_and_survives_restart(self) -> None:
        generated, _client = self.generate()

        approved = self.store.decide(
            candidate_id=str(generated["candidate_id"]),
            decision="approve",
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
        )
        restarted = HumanAdamImageCandidateStore(self.root)
        loaded = restarted.public_list(
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID
        )[0]

        self.assertEqual(approved["status"], "approved")
        self.assertEqual(loaded["status"], "approved")
        self.assertEqual(loaded["version"], 1)
        self.assertTrue((self.root / str(generated["candidate_id"]) / "image.png").exists())

    def test_rejection_marks_only_exact_generated_version_and_survives_restart(self) -> None:
        generated, _client = self.generate("reject")

        rejected = self.store.decide(
            candidate_id=str(generated["candidate_id"]),
            decision="reject",
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
        )
        loaded = HumanAdamImageCandidateStore(self.root).public_list(
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID
        )[0]

        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(loaded["status"], "rejected")
        self.assertTrue((self.root / str(generated["candidate_id"]) / "image.png").exists())

    def test_legacy_human_adam_candidate_is_migrated_without_cross_stream_visibility(self) -> None:
        record = self.prepare("legacy")
        metadata_path = self.root / str(record["candidate_id"]) / "candidate.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["schema_version"] = 1
        metadata.pop("workstream_id")
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        restarted = HumanAdamImageCandidateStore(self.root)
        human_records = restarted.public_list(
            workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID
        )
        other_records = restarted.public_list(
            workstream_id="project-r2-adam-janicka"
        )
        migrated = json.loads(metadata_path.read_text(encoding="utf-8"))

        self.assertEqual(len(human_records), 1)
        self.assertEqual(other_records, [])
        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(
            migrated["workstream_id"], HUMAN_ADAM_TEST_WORKSTREAM_ID
        )

    def test_invalid_candidate_id_is_rejected_by_load_generate_and_decision(self) -> None:
        for operation in (
            lambda: self.store.image_path(
                "../outside", workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID
            ),
            lambda: self.store.generate(
                candidate_id="bad",
                confirmation="bad",
                workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
                client=FakeClient(),
            ),
            lambda: self.store.decide(
                candidate_id="bad",
                decision="approve",
                workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
            ),
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(HumanAdamImageError, "neplatné ID"):
                    operation()

    def test_symlink_cannot_escape_candidate_directory(self) -> None:
        record = self.prepare("escape")
        candidate_dir = self.root / str(record["candidate_id"])
        outside = Path(self.temporary.name) / "outside.png"
        outside.write_bytes(PNG_BYTES)
        (candidate_dir / "image.png").symlink_to(outside)
        metadata_path = candidate_dir / "candidate.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.update(status="generated", image_file="image.png", mime_type="image/png")
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        with self.assertRaisesRegex(HumanAdamImageError, "mimo adresář kandidáta"):
            self.store.image_path(
                str(record["candidate_id"]),
                workstream_id=HUMAN_ADAM_TEST_WORKSTREAM_ID,
            )

    def test_declared_capability_allows_another_workstream(self) -> None:
        other_id = "project-r2-adam-janicka"
        other = FakeService(other_id)
        payload = {
            "request_text": "Vygeneruj obrázek sovy.",
            "client_message_id": "human-adam-message-other",
        }

        prepared = human_adam_image_prepare_action(payload, service=other, store=self.store)
        listed = human_adam_image_candidates_action(service=other, store=self.store)

        self.assertTrue(prepared["ok"])
        self.assertEqual(len(listed["candidates"]), 1)
        metadata = json.loads(
            next(self.root.glob("img_*/candidate.json")).read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["workstream_id"], other_id)

    def test_candidate_is_not_visible_or_mutable_from_another_workstream(self) -> None:
        other_id = "project-r2-adam-janicka"
        record = self.prepare("isolated", workstream_id=other_id)
        human = FakeService(HUMAN_ADAM_TEST_WORKSTREAM_ID)

        listed = human_adam_image_candidates_action(service=human, store=self.store)
        generated = human_adam_image_generate_action(
            {
                "candidate_id": record["candidate_id"],
                "confirmation": generation_confirmation(str(record["candidate_id"])),
            },
            service=human,
            store=self.store,
            client=FakeClient(),
        )
        decided = human_adam_image_decision_action(
            {"candidate_id": record["candidate_id"], "decision": "approve"},
            service=human,
            store=self.store,
        )
        resolved = human_adam_image_file_action(
            str(record["candidate_id"]), service=human, store=self.store
        )

        self.assertEqual(listed["candidates"], [])
        for result in (generated, decided, resolved):
            self.assertFalse(result["ok"])
            self.assertIn("nepatří do aktivního pracovního proudu", result["message"])

    def test_missing_capability_fails_closed_without_private_write(self) -> None:
        disabled = FakeService(
            "project-r2-adam-janicka",
            capabilities=CanonicalWorkstreamCapabilities(image_generation=False),
        )
        payload = {
            "request_text": "Vygeneruj obrázek sovy.",
            "client_message_id": "human-adam-message-disabled",
        }

        result = human_adam_image_prepare_action(
            payload, service=disabled, store=self.store
        )

        self.assertFalse(result["ok"])
        self.assertIn("nemá povolené generování obrázků", result["message"])
        self.assertFalse(self.root.exists())

    def test_invalid_capability_configuration_fails_closed(self) -> None:
        invalid = FakeService(
            "project-r2-adam-janicka",
            capabilities=CanonicalWorkstreamCapabilities(image_generation="yes"),
        )

        result = human_adam_image_candidates_action(
            service=invalid, store=self.store
        )

        self.assertFalse(result["ok"])
        self.assertIn("nelze bezpečně ověřit", result["message"])


if __name__ == "__main__":
    unittest.main()
