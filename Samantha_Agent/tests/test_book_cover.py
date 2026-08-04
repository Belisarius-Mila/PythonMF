from __future__ import annotations

import base64
import json
import unittest
from io import BytesIO
from types import SimpleNamespace

from PIL import Image
from pillow_heif import from_pillow

from app.book_cover import (
    BookCoverRecognitionError,
    prepare_book_cover_data_url,
    recognize_book_cover,
)


class FakeBookCoverCompletions:
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


def fake_client(completions: FakeBookCoverCompletions) -> SimpleNamespace:
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def synthetic_cover_data_url() -> str:
    output = BytesIO()
    Image.new("RGB", (40, 60), color=(40, 80, 120)).save(output, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(output.getvalue()).decode('ascii')}"


class BookCoverTests(unittest.TestCase):
    def test_recognizes_only_visible_structured_metadata_from_synthetic_cover(self) -> None:
        completions = FakeBookCoverCompletions(
            result={
                "title": "Syntetická kniha",
                "author": "Testovací autor",
                "isbn": "978-1-23456-789-7",
                "confidence": 0.91,
                "uncertainties": [],
            }
        )

        result = recognize_book_cover(
            image_data_url=synthetic_cover_data_url(),
            client=fake_client(completions),
        )

        self.assertEqual(result["title"], "Syntetická kniha")
        self.assertEqual(result["author"], "Testovací autor")
        self.assertEqual(result["isbn"], "9781234567897")
        self.assertEqual(result["confidence"], 0.91)
        call = completions.calls[0]
        self.assertEqual(call["model"], "gpt-4o-mini")
        self.assertEqual(call["max_tokens"], 400)
        content = call["messages"][0]["content"]
        self.assertIn("Nic nedohledávej", content[0]["text"])
        self.assertTrue(content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))

    def test_invalid_recognized_isbn_is_not_prefilled(self) -> None:
        completions = FakeBookCoverCompletions(
            result={
                "title": "Syntetická kniha",
                "author": "Testovací autor",
                "isbn": "1234567890",
                "confidence": 0.6,
                "uncertainties": ["ISBN je rozmazané."],
            }
        )

        result = recognize_book_cover(
            image_data_url=synthetic_cover_data_url(),
            client=fake_client(completions),
        )

        self.assertEqual(result["isbn"], "")
        self.assertTrue(any("neprošlo kontrolou" in item for item in result["uncertainties"]))

    def test_empty_recognition_stays_empty_instead_of_guessing(self) -> None:
        completions = FakeBookCoverCompletions(
            result={
                "title": "",
                "author": "",
                "isbn": "",
                "confidence": 0,
                "uncertainties": ["Text není čitelný."],
            }
        )

        result = recognize_book_cover(
            image_data_url=synthetic_cover_data_url(),
            client=fake_client(completions),
        )

        self.assertEqual({key: result[key] for key in ("title", "author", "isbn")}, {"title": "", "author": "", "isbn": ""})

    def test_rejects_invalid_image_without_calling_provider(self) -> None:
        completions = FakeBookCoverCompletions()
        with self.assertRaisesRegex(ValueError, "Podporované fotografie"):
            recognize_book_cover(
                image_data_url="data:text/plain;base64,dGVzdA==",
                client=fake_client(completions),
            )
        self.assertEqual(completions.calls, [])

    def test_provider_failure_is_redacted(self) -> None:
        completions = FakeBookCoverCompletions(error=RuntimeError("synthetic provider secret"))
        with self.assertRaises(BookCoverRecognitionError) as captured:
            recognize_book_cover(
                image_data_url=synthetic_cover_data_url(),
                client=fake_client(completions),
            )
        self.assertNotIn("provider secret", str(captured.exception))

    def test_preparation_resizes_to_safe_jpeg(self) -> None:
        prepared = prepare_book_cover_data_url(synthetic_cover_data_url())
        self.assertTrue(prepared.startswith("data:image/jpeg;base64,"))
        payload = base64.b64decode(prepared.split(",", 1)[1])
        with Image.open(BytesIO(payload)) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertLessEqual(max(image.size), 1600)

    def test_preparation_accepts_iphone_heic_and_returns_jpeg(self) -> None:
        output = BytesIO()
        from_pillow(Image.new("RGB", (30, 50), color=(70, 90, 110))).save(output, quality=80)
        source = f"data:image/heic;base64,{base64.b64encode(output.getvalue()).decode('ascii')}"

        prepared = prepare_book_cover_data_url(source)

        self.assertTrue(prepared.startswith("data:image/jpeg;base64,"))
        with Image.open(BytesIO(base64.b64decode(prepared.split(",", 1)[1]))) as image:
            self.assertEqual(image.format, "JPEG")


if __name__ == "__main__":
    unittest.main()
