from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.tomik_family_video_package import build_family_video_package


class TomikFamilyVideoPackageTests(unittest.TestCase):
    def test_builds_private_package_data_and_copies_thumbnails(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            base = Path(temp_dir)
            root = base / "tomik_rok_2"
            app_dir = base / "app"
            out_dir = root / "family_video_organizer_package"

            self._write_app(app_dir)
            self._write_private_source(root)

            summary = build_family_video_package(root=root, app_dir=app_dir, out_dir=out_dir, include_videos=True)

            self.assertEqual(summary.videos, 2)
            self.assertEqual(summary.short_videos, 1)
            self.assertEqual(summary.family_videos, 1)
            self.assertEqual(summary.copied_thumbnails, 3)
            self.assertEqual(summary.missing_thumbnails, 0)
            self.assertEqual(summary.package_videos, 2)
            self.assertEqual(summary.missing_videos, 0)
            self.assertTrue((out_dir / "index.html").exists())
            self.assertTrue((out_dir / "app.js").exists())
            self.assertTrue((out_dir / "styles.css").exists())
            self.assertTrue((out_dir / "thumbs" / "clip001__1.jpg").exists())
            self.assertTrue((out_dir / "videos" / "clip001.mp4").exists())
            self.assertTrue((out_dir / "videos" / "clip002.mp4").exists())
            self.assertIn("videos-data.js", (out_dir / "index.html").read_text(encoding="utf-8"))
            self.assertNotIn("videos-data.example.js", (out_dir / "index.html").read_text(encoding="utf-8"))

            payload = self._read_videos_data(out_dir / "videos-data.js")
            self.assertEqual(payload["project"], "Tomik rok 2 - realna data")
            self.assertEqual(len(payload["videos"]), 2)
            first = payload["videos"][0]
            second = payload["videos"][1]
            self.assertEqual(first["id"], "001")
            self.assertEqual(first["duration"], "32s")
            self.assertEqual(first["title"], "lezení po terase")
            self.assertEqual(first["videoPath"], "videos/clip001.mp4")
            self.assertTrue(first["videoShort"])
            self.assertFalse(first["videoFamily"])
            self.assertEqual(first["thumbs"], ["thumbs/clip001__1.jpg", "thumbs/clip001__2.jpg", "thumbs/clip001__3.jpg"])
            self.assertFalse(second["videoShort"])
            self.assertTrue(second["videoFamily"])

    def test_default_package_is_lightweight_without_video_files(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            base = Path(temp_dir)
            root = base / "tomik_rok_2"
            app_dir = base / "app"
            out_dir = root / "family_video_organizer_package_light"

            self._write_app(app_dir)
            self._write_private_source(root)

            summary = build_family_video_package(root=root, app_dir=app_dir, out_dir=out_dir)

            self.assertEqual(summary.videos, 2)
            self.assertEqual(summary.package_videos, 0)
            self.assertEqual(summary.missing_videos, 0)
            self.assertFalse(summary.includes_videos)
            self.assertFalse((out_dir / "videos" / "clip001.mp4").exists())
            self.assertIn("Slozka s videi", (out_dir / "README.md").read_text(encoding="utf-8"))

    def _write_app(self, app_dir: Path) -> None:
        app_dir.mkdir(parents=True)
        (app_dir / "index.html").write_text(
            '<script src="videos-data.example.js"></script><script src="app.js"></script>',
            encoding="utf-8",
        )
        (app_dir / "app.js").write_text("console.log('app');\n", encoding="utf-8")
        (app_dir / "styles.css").write_text("body {}\n", encoding="utf-8")

    def _write_private_source(self, root: Path) -> None:
        (root / "03_audit").mkdir(parents=True)
        (root / "01_originaly").mkdir(parents=True)
        (root / "02_nahledy").mkdir(parents=True)
        (root / "05_imovie_vyber_short").mkdir(parents=True)
        (root / "06_imovie_vyber_family").mkdir(parents=True)

        (root / "03_audit" / "video_audit_described.csv").write_text(
            "index,taken,date_source,original_name,duration_s,size_mb,width,height,rotation,"
            "thumb_1,thumb_2,thumb_3,draft_description,proposed_name\n"
            "001,2025-04-04 18:07:59,ffprobe_creation_time,clip001.mp4,31.53,64.7,1920,1080,,"
            "clip001__1.jpg,clip001__2.jpg,clip001__3.jpg,Lezení po terase.,001_lezeni.mp4\n"
            "002,2025-04-06 10:31:46,ffprobe_creation_time,clip002.mp4,61.20,86.0,1920,1080,,"
            ",,,Hra doma.,002_hra_doma.mp4\n",
            encoding="utf-8",
        )
        (root / "05_imovie_vyber_short" / "selection_manifest_short.csv").write_text(
            "order,index,taken,chapter,selection_file,source_file,duration_s,description,action\n"
            "001,001,2025-04-04,chapter,001_clip.mp4,001_lezeni.mp4,31.53,Lezení,hardlink\n",
            encoding="utf-8",
        )
        (root / "06_imovie_vyber_family" / "selection_manifest_family.csv").write_text(
            "order,index,taken,chapter,selection_file,source_file,duration_s,description,action\n"
            "001,002,2025-04-06,chapter,002_clip.mp4,002_hra_doma.mp4,61.20,Hra,hardlink\n",
            encoding="utf-8",
        )
        for name in ("clip001__1.jpg", "clip001__2.jpg", "clip001__3.jpg"):
            (root / "02_nahledy" / name).write_bytes(b"jpg")
        (root / "01_originaly" / "clip001.mp4").write_bytes(b"video1")
        (root / "01_originaly" / "clip002.mp4").write_bytes(b"video2")

    def _read_videos_data(self, path: Path) -> dict[str, object]:
        text = path.read_text(encoding="utf-8")
        prefix = "window.FAMILY_VIDEO_DATA = "
        self.assertTrue(text.startswith(prefix))
        return json.loads(text[len(prefix) :].rstrip(";\n"))


if __name__ == "__main__":
    unittest.main()
