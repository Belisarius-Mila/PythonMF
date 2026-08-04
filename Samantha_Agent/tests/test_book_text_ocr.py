from __future__ import annotations

import base64
import json
import unittest
from io import BytesIO
from types import SimpleNamespace

from PIL import Image

from app.book_text_ocr import BookTextOcrError, extract_book_text_from_images


class FakeBookTextOcrCompletions:
    def __init__(self, *, result: dict[str, object] | None = None, error: Exception | None = None) -> None:
        self.result = result or {}
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(self.result)))]
        )


def fake_client(completions: FakeBookTextOcrCompletions) -> SimpleNamespace:
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def synthetic_text_photo_data_url(color: tuple[int, int, int]) -> str:
    output = BytesIO()
    Image.new("RGB", (60, 40), color=color).save(output, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(output.getvalue()).decode('ascii')}"


class BookTextOcrTests(unittest.TestCase):
    def test_transcribes_one_to_three_temporary_photos_without_summarizing(self) -> None:
        completions = FakeBookTextOcrCompletions(
            result={
                "text": "První syntetický odstavec.\n\nDruhý syntetický odstavec.",
                "uncertainties": ["Jeden znak je méně čitelný."],
            }
        )

        result = extract_book_text_from_images(
            image_data_urls=[
                synthetic_text_photo_data_url((20, 40, 60)),
                synthetic_text_photo_data_url((60, 40, 20)),
            ],
            client=fake_client(completions),
        )

        self.assertEqual(result["image_count"], 2)
        self.assertIn("První syntetický", result["text"])
        self.assertEqual(len(result["uncertainties"]), 1)
        call = completions.calls[0]
        self.assertEqual(call["model"], "gpt-4o-mini")
        self.assertEqual(call["max_tokens"], 3000)
        content = call["messages"][0]["content"]
        self.assertIn("Text neshrnuj", content[0]["text"])
        self.assertEqual(len(content), 3)
        self.assertTrue(all(item["image_url"]["url"].startswith("data:image/jpeg;base64,") for item in content[1:]))

    def test_rejects_missing_too_many_and_invalid_photos_before_provider(self) -> None:
        completions = FakeBookTextOcrCompletions()
        with self.assertRaisesRegex(ValueError, "alespoň jednu"):
            extract_book_text_from_images(image_data_urls=[], client=fake_client(completions))
        with self.assertRaisesRegex(ValueError, "nejvýše 3"):
            extract_book_text_from_images(
                image_data_urls=[synthetic_text_photo_data_url((1, 2, 3))] * 4,
                client=fake_client(completions),
            )
        with self.assertRaisesRegex(ValueError, "Podporované fotografie"):
            extract_book_text_from_images(
                image_data_urls=["data:text/plain;base64,dGVzdA=="],
                client=fake_client(completions),
            )
        self.assertEqual(completions.calls, [])

    def test_provider_failure_and_empty_result_are_safe(self) -> None:
        photo = synthetic_text_photo_data_url((1, 2, 3))
        provider = FakeBookTextOcrCompletions(error=RuntimeError("synthetic provider secret"))
        with self.assertRaises(BookTextOcrError) as captured:
            extract_book_text_from_images(image_data_urls=[photo], client=fake_client(provider))
        self.assertNotIn("provider secret", str(captured.exception))

        empty = FakeBookTextOcrCompletions(result={"text": "", "uncertainties": ["Nečitelné."]})
        with self.assertRaisesRegex(BookTextOcrError, "nebyl nalezen"):
            extract_book_text_from_images(image_data_urls=[photo], client=fake_client(empty))


if __name__ == "__main__":
    unittest.main()
