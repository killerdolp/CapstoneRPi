"""Export to the clinical data SSD.

SSD detection and file writing are not implemented yet (out of scope for
this build). ``SimulatedExporter`` walks the selected records at a realistic
pace and honours the simulated SSD connection, so the connected, exporting,
complete and failed states can all be exercised. Replace ``_write_record`` and
``_finalise`` with real I/O to the mounted SSD when that work lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from PySide6.QtCore import QObject, QTimer, Signal

from .app_state import SCHEMA_VERSION, AppState, Session


@dataclass
class ExportRequest:
    include_complete: bool = True
    include_incomplete: bool = False
    include_photos: bool = True

    def select(self, state: AppState) -> List[Session]:
        out = []
        if self.include_complete:
            out += state.complete_sessions()
        if self.include_incomplete:
            out += state.incomplete_sessions()
        return sorted(out, key=lambda s: s.session_id)


@dataclass
class ExportResult:
    ok: bool
    total: int
    written: int
    photos: int
    file_name: str
    schema: str = SCHEMA_VERSION
    destination: str = "Clinical data SSD"
    finished_at: datetime = field(default_factory=datetime.now)
    reason: str = ""


class SimulatedExporter(QObject):
    progress = Signal(int, int)        # written, total
    finished = Signal(object)          # ExportResult (ok or failed)

    STEP_MS = 140

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._queue: List[Session] = []
        self._written = 0
        self._photos = 0
        self._request = ExportRequest()

    @property
    def running(self) -> bool:
        return self._timer.isActive()

    def start(self, request: ExportRequest) -> None:
        self._request = request
        self._queue = request.select(self.state)
        self._written = 0
        self._photos = 0
        self.progress.emit(0, len(self._queue))
        self._timer.start(self.STEP_MS)

    def _file_name(self) -> str:
        return f"metadata_{datetime.now():%Y-%m-%d}.json"

    def _step(self) -> None:
        total = len(self._queue)
        if not self.state.ssd_connected:
            self._timer.stop()
            self.finished.emit(ExportResult(
                ok=False, total=total, written=self._written, photos=self._photos,
                file_name=self._file_name(),
                reason="The SSD was disconnected during export.",
            ))
            return
        if self._written >= total:
            self._timer.stop()
            self.finished.emit(ExportResult(
                ok=True, total=total, written=self._written, photos=self._photos,
                file_name=self._file_name(),
            ))
            return
        session = self._queue[self._written]
        self._write_record(session)
        self._written += 1
        if self._request.include_photos and session.has_photo:
            self._photos += 1
        self.progress.emit(self._written, total)

    def _write_record(self, session: Session) -> None:
        """Integration point: write the session's database row (and its
        photo file, ``session.image_url``, when requested) to the SSD."""
        return None