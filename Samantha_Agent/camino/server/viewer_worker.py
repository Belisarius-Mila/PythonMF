"""One serial, opt-in media worker owned by the Camino application lifespan."""

from __future__ import annotations

import math
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camino.server.viewer import CaminoViewer


class ViewerWorker:
    def __init__(self, viewer: CaminoViewer, *, interval: float = 60):
        if not math.isfinite(interval) or not 1 <= interval <= 3600:
            raise ValueError("Viewer interval must be between 1 and 3600 seconds")
        self.viewer = viewer
        self.interval = interval
        self.stopping = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread is not None and self.thread.is_alive():
            raise RuntimeError("Viewer worker is already running")
        self.stopping.clear()
        self.thread = threading.Thread(target=self._run, name="camino-viewer", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stopping.set()
        if self.thread is not None:
            # Finish the current bounded ffmpeg command, not the whole archive.
            self.thread.join()
        self.viewer.build_state = "stopped"

    def _run(self) -> None:
        while not self.stopping.is_set():
            self.viewer.build_state = "building"
            try:
                result = self.viewer.build_pending(should_stop=self.stopping.is_set)
                self.viewer.build_state = "waiting" if result["waiting"] else "checked"
            except Exception:
                # No paths, source text, credentials or exception detail in logs/HTML.
                # The next cycle retries, while HTTP still enforces current privacy.
                self.viewer.build_state = "failed"
            if self.stopping.wait(self.interval):
                break
