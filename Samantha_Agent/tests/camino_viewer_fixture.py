"""Synthetic-only M1 fixture shared by projection, HTTP and browser checks."""

import hashlib
import io
import json
import subprocess
from pathlib import Path

from camino.domain.codec import wire
from camino.domain.model import Asset, CaptureTime, JourneyDay, MomentKind, Privacy, TextRevision, TimeSource, Trip, create_moment
from camino.domain.revision_store import RevisionStore
from camino.server.media_store import MediaStore


def uid(n):
    return f"00000000-0000-0000-0000-{n:012x}"


class ViewerFixture:
    def __init__(self, root: Path):
        self.root = root
        self.store = RevisionStore(root / "metadata.sqlite")
        self.media = MediaStore(root / "media.sqlite", root / "originals", asset_lookup=self.store.asset, reserve_bytes=0)
        self.sequence = 0
        self.trip = Trip(uid(1), "Zkušební cesta", "cs", True, True)
        self.day = JourneyDay(uid(2), self.trip.id, "2026-09-25")
        self.capture = CaptureTime(1790323200000, "2026-09-25T10:00:00", 120, "Europe/Prague", TimeSource.DEVICE_CAPTURE)
        self.send("create_trip", wire(self.trip))
        self.send("create_day", wire(self.day))
        self.public = self.moment(3, Privacy.DIARY)
        self.private = self.moment(4, Privacy.OWNER_ONLY)
        self.text(self.public, 20, "Dnes začíná naše zkušební cesta. <script>alert('text')</script>")
        self.text(self.private, 21, "TAJNA-VETA-NEPATRI-JANE")

    def send(self, kind, payload, expected=None):
        self.sequence += 1
        envelope = {"contract_version": 1, "epoch": self.store.state()["epoch"],
                    "operation_id": uid(1000 + self.sequence), "device_id": uid(90),
                    "device_sequence": self.sequence, "kind": kind,
                    "expected_revision": expected, "payload": payload}
        return self.store.apply(envelope, json.dumps(envelope, sort_keys=True).encode())

    def moment(self, n, privacy):
        m = create_moment(id=uid(n), trip=self.trip, day=self.day, kind=MomentKind.COMMENT,
                          captured=self.capture, new_moment_privacy=privacy)
        self.send("create_moment", wire(m))
        return m

    def text(self, moment, n, content, sources=(), role="typed_source"):
        self.send("append_text", wire(TextRevision(uid(n), moment.id, role, content, sources, None,
                                                  1790323200000)), expected=moment.revision)

    def lock(self):
        self.send("update_metadata", {"moment_id": self.public.id, "change": {
            "type": "privacy", "new_privacy": "owner_only", "user_action": "lock"}}, expected=1)

    def upload(self, n, kind, content, *, private=False, complete=True):
        asset = Asset(uid(n), self.private.id if private else self.public.id, kind,
                      "recording" if kind == "audio" else "camera", len(content),
                      hashlib.sha256(content).hexdigest(), None if kind == "photo" else 1500)
        self.send("create_asset", wire(asset))
        if complete:
            self.media.create_session(asset.id)
            self.media.receive_chunk(asset.id, 0, content_length=len(content),
                                     expected_sha256=asset.sha256, stream=io.BytesIO(content))
            self.media.finalize(asset.id)
        return wire(asset)


def synthetic_media(root: Path) -> dict[str, bytes]:
    commands = {
        "photo": (["-f", "lavfi", "-i", "testsrc2=size=320x180:rate=1", "-frames:v", "1"], "jpg"),
        "video": (["-f", "lavfi", "-i", "testsrc2=size=320x180:rate=10", "-f", "lavfi", "-i",
                   "sine=frequency=330:sample_rate=44100", "-t", "1.5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-metadata", "location=+50.0000+014.0000/", "-metadata", "comment=PRIVATE-EXIF"], "mp4"),
        "audio": (["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100", "-t", "1.5", "-c:a", "pcm_s16le"], "wav"),
    }
    result = {}
    for kind, (args, extension) in commands.items():
        path = root / f"synthetic.{extension}"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-n", *args, str(path)],
                       check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        result[kind] = path.read_bytes()
    return result
