from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.media.image_resize import (
    DEFAULT_TARGET_KB,
    IMAGE_RESIZE_CONFIRMATION_PHRASE,
    apply_image_resize,
    format_preview_image_resize,
    preview_image_resize,
)


try:
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover - depends on local environment setup
    Image = None


class MediaImageResizeTests(unittest.TestCase):
    def test_preview_is_read_only_and_uses_default_target(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            image_path = directory / "large_photo.jpg"
            image_path.write_bytes(b"x" * (300 * 1024))
            before = image_path.read_bytes()

            summary = preview_image_resize(path=directory)

            self.assertEqual(summary.target_kb, DEFAULT_TARGET_KB)
            self.assertEqual(summary.total_files, 1)
            self.assertEqual(summary.resize_candidates, 1)
            self.assertEqual(image_path.read_bytes(), before)

    def test_preview_output_mentions_confirmation_phrase_and_backup_scope(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            (directory / "photo.jpg").write_bytes(b"x" * (300 * 1024))

            output = format_preview_image_resize(path=str(directory), target_kb=100)

            self.assertIn("Cilova velikost: cca 100 kB", output)
            self.assertIn("data/media/image_resize_backups", output)
            self.assertIn(IMAGE_RESIZE_CONFIRMATION_PHRASE, output)

    def test_apply_requires_explicit_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            image_path = directory / "large_photo.jpg"
            image_path.write_bytes(b"x" * (300 * 1024))

            with self.assertRaises(ValueError):
                apply_image_resize(path=directory, target_kb=100)

            self.assertEqual(image_path.stat().st_size, 300 * 1024)

    def test_apply_accepts_czech_diacritics_in_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            backup_root = directory / "backups"
            image_path = directory / "small_photo.jpg"
            image_path.write_bytes(b"x" * (80 * 1024))

            result = apply_image_resize(
                path=directory,
                target_kb=100,
                user_confirmed=True,
                confirmation_text="Potvrzuji zmenšení obrazku pro lekarnu.",
                backup_root=backup_root,
            )

            self.assertEqual(result.resized_count, 0)
            self.assertEqual(result.skipped_count, 1)

    @unittest.skipIf(Image is None, "Pillow is not installed")
    def test_apply_resizes_jpeg_and_keeps_backup(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            directory = Path(temp_dir)
            backup_root = directory / "backups"
            image_path = directory / "large_photo.jpg"
            image = Image.effect_noise((1600, 1200), 80).convert("RGB")
            image.save(image_path, format="JPEG", quality=95)
            original_size = image_path.stat().st_size

            result = apply_image_resize(
                path=directory,
                target_kb=120,
                user_confirmed=True,
                confirmation_text=IMAGE_RESIZE_CONFIRMATION_PHRASE,
                backup_root=backup_root,
            )

            self.assertEqual(result.resized_count, 1)
            self.assertLess(image_path.stat().st_size, original_size)
            self.assertTrue((result.backup_dir / "large_photo.jpg").exists())
            self.assertEqual((result.backup_dir / "large_photo.jpg").stat().st_size, original_size)


if __name__ == "__main__":
    unittest.main()
