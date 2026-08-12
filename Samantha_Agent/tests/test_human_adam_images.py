from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.communication.human_adam_images import (
    HUMAN_ADAM_WORKSTREAM_ID,
    HumanAdamImageCandidateStore,
    HumanAdamImageError,
    generation_confirmation,
    human_adam_image_candidates_action,
    human_adam_image_decision_action,
    human_adam_image_file_action,
    human_adam_image_generate_action,
    human_adam_image_prepare_action,
    is_image_generation_request,
    prepare_image_prompt,
)


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"private-test-image"


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
    def __init__(self, workstream_id: str = HUMAN_ADAM_WORKSTREAM_ID):
        self.active_workstream_id = workstream_id


class HumanAdamImageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "candidates"
        self.store = HumanAdamImageCandidateStore(self.root)
        self.service = FakeService()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def prepare(self, suffix: str = "one") -> dict[str, object]:
        return self.store.prepare(
            request_text="Vygeneruj obrázek modré sovy na šířku.",
            client_message_id=f"human-adam-message-{suffix}",
        )

    def generate(self, suffix: str = "one") -> tuple[dict[str, object], FakeClient]:
        record = self.prepare(suffix)
        client = FakeClient()
        generated = self.store.generate(
            candidate_id=str(record["candidate_id"]),
            confirmation=generation_confirmation(str(record["candidate_id"])),
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
                client=client,
            )

        self.assertEqual(client.images.calls, [])
        self.assertEqual(self.store.public_list()[0]["status"], "prepared")

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

    def test_safe_image_load_returns_only_file_inside_candidate_directory(self) -> None:
        generated, _client = self.generate()

        path, mime_type = self.store.image_path(str(generated["candidate_id"]))

        self.assertEqual(path.parent, self.root.resolve() / str(generated["candidate_id"]))
        self.assertEqual(path.name, "image.png")
        self.assertEqual(mime_type, "image/png")

    def test_approval_marks_only_exact_generated_version_and_survives_restart(self) -> None:
        generated, _client = self.generate()

        approved = self.store.decide(
            candidate_id=str(generated["candidate_id"]), decision="approve"
        )
        restarted = HumanAdamImageCandidateStore(self.root)
        loaded = restarted.public_list()[0]

        self.assertEqual(approved["status"], "approved")
        self.assertEqual(loaded["status"], "approved")
        self.assertEqual(loaded["version"], 1)
        self.assertTrue((self.root / str(generated["candidate_id"]) / "image.png").exists())

    def test_rejection_marks_only_exact_generated_version_and_survives_restart(self) -> None:
        generated, _client = self.generate("reject")

        rejected = self.store.decide(
            candidate_id=str(generated["candidate_id"]), decision="reject"
        )
        loaded = HumanAdamImageCandidateStore(self.root).public_list()[0]

        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(loaded["status"], "rejected")
        self.assertTrue((self.root / str(generated["candidate_id"]) / "image.png").exists())

    def test_invalid_candidate_id_is_rejected_by_load_generate_and_decision(self) -> None:
        for operation in (
            lambda: self.store.image_path("../outside"),
            lambda: self.store.generate(candidate_id="bad", confirmation="bad", client=FakeClient()),
            lambda: self.store.decide(candidate_id="bad", decision="approve"),
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
            self.store.image_path(str(record["candidate_id"]))

    def test_actions_fail_closed_outside_human_adam_workstream(self) -> None:
        other = FakeService("project-r2-adam-janicka")
        payload = {
            "request_text": "Vygeneruj obrázek sovy.",
            "client_message_id": "human-adam-message-other",
        }

        prepared = human_adam_image_prepare_action(payload, service=other, store=self.store)
        listed = human_adam_image_candidates_action(service=other, store=self.store)
        generated = human_adam_image_generate_action({}, service=other, store=self.store, client=FakeClient())
        decided = human_adam_image_decision_action({}, service=other, store=self.store)
        resolved = human_adam_image_file_action("bad", service=other, store=self.store)

        for result in (prepared, listed, generated, decided, resolved):
            self.assertFalse(result["ok"])
            self.assertIn("pouze v proudu Human–Adam", result["message"])
        self.assertFalse(self.root.exists())


if __name__ == "__main__":
    unittest.main()
