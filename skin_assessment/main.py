"""Entry point and navigation controller for the Skin Assessment device.

Run (development, windowed, simulated camera off-Pi)::

    python -m skin_assessment.main

On the Raspberry Pi (fullscreen kiosk, CSI camera)::

    python -m skin_assessment.main --kiosk

Options: ``--demo`` loads labelled demonstration sessions into a separate
data folder; ``--camera {auto,pi,sim}``; ``--data-dir PATH``.
Developer shortcut: Ctrl+D toggles the simulated clinical SSD connection.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from .app_state import DEFAULT_DATA_DIR, AppState, Session
from .camera import CameraBackend, create_camera
from .export import ExportRequest, ExportResult, SimulatedExporter
from .screens.assessment import ErythemaGradeScreen, SkinTypeScreen
from .screens.confirm_photo import ConfirmPhotoScreen
from .screens.export_complete import ExportCompleteScreen
from .screens.export_data import ExportDataScreen
from .screens.export_failed import ExportFailedScreen
from .screens.home import HomeScreen
from .screens.past_sessions import PastSessionsScreen
from .screens.session_detail import SessionDetailScreen
from .screens.session_saved import SessionSavedScreen
from .screens.take_photo import TakePhotoScreen
from .theme import SCREEN_HEIGHT, SCREEN_WIDTH, font, load_fonts, stylesheet
from .widgets import ConfirmSheet


class MainWindow(QMainWindow):
    def __init__(self, state: AppState, camera: CameraBackend, reduced_motion: bool = False) -> None:
        super().__init__()
        self.setWindowTitle("Skin Assessment")
        self.state = state
        self.camera = camera
        self.reduced_motion = reduced_motion
        self.exporter = SimulatedExporter(state)

        # Workflow state.
        self.draft: Optional[Session] = None          # working copy, never the stored object
        self.draft_dirty_baseline: Optional[tuple] = None
        self.editing = False
        self.pending_photo: Optional[str] = None
        self.keep_photo = False
        self.last_saved: Optional[Session] = None
        self.selected: Optional[Session] = None
        self.last_export: Optional[ExportResult] = None
        self.last_export_request: ExportRequest = ExportRequest()

        root = QWidget()
        root.setObjectName("Root")
        lay = QVBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        self.setCentralWidget(root)
        self.sheet = ConfirmSheet(root)

        self.screens: Dict[str, QWidget] = {
            "home": HomeScreen(self),
            "skin_type": SkinTypeScreen(self),
            "erythema_grade": ErythemaGradeScreen(self),
            "take_photo": TakePhotoScreen(self),
            "confirm_photo": ConfirmPhotoScreen(self),
            "session_saved": SessionSavedScreen(self),
            "past_sessions": PastSessionsScreen(self),
            "session_detail": SessionDetailScreen(self),
            "export": ExportDataScreen(self),
            "export_complete": ExportCompleteScreen(self),
            "export_failed": ExportFailedScreen(self),
        }
        for screen in self.screens.values():
            self.stack.addWidget(screen)

        state.changed.connect(self._refresh_current)
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._refresh_status)
        self._clock.start(10_000)

        QShortcut(QKeySequence("Ctrl+D"), self, activated=self._toggle_ssd)
        self._navigate("home")

    # ---- navigation core -------------------------------------------------
    def _navigate(self, key: str) -> None:
        self.sheet.hide_sheet()
        current = self.stack.currentWidget()
        target = self.screens[key]
        if current is not None and current is not target:
            getattr(current, "on_leave", lambda: None)()
        target.on_enter()
        target.refresh_status()
        self.stack.setCurrentWidget(target)

    def _refresh_status(self) -> None:
        current = self.stack.currentWidget()
        if current is not None:
            current.refresh_status()

    def _refresh_current(self) -> None:
        current = self.stack.currentWidget()
        if current is None:
            return
        # Do not rebuild flow screens under the user's finger; status only.
        if current in (self.screens["home"], self.screens["export"], self.screens["export_failed"]):
            current.on_enter()
        current.refresh_status()

    # ---- navigation API used by screens ---------------------------------
    def go_home(self) -> None:
        self._navigate("home")

    def show_skin_type(self) -> None:
        self._navigate("skin_type")

    def show_erythema_grade(self) -> None:
        self._navigate("erythema_grade")

    def show_take_photo(self) -> None:
        self._navigate("take_photo")

    def show_past_sessions(self) -> None:
        self._navigate("past_sessions")

    def show_session_detail(self, session: Session) -> None:
        self.selected = session
        self._navigate("session_detail")

    def show_export(self) -> None:
        self._navigate("export")

    # ---- new / edit session flow ----------------------------------------
    def _begin(self, draft: Session, editing: bool) -> None:
        self.state.store.discard_pending()
        self.draft = draft
        self.editing = editing
        self.pending_photo = None
        self.keep_photo = False
        self.draft_dirty_baseline = (draft.skin_type, draft.erythema_grade)
        self._navigate("skin_type")

    def start_new_session(self) -> None:
        self._begin(Session(session_id=self.state.next_session_id()), editing=False)

    def edit_session(self, session: Session) -> None:
        self._begin(session.copy(), editing=True)

    def _has_unsaved_work(self) -> bool:
        if self.draft is None:
            return False
        if self.pending_photo:
            return True
        if not self.editing:
            return self.draft.skin_type is not None or self.draft.erythema_grade is not None
        return (self.draft.skin_type, self.draft.erythema_grade) != self.draft_dirty_baseline

    def leave_flow(self) -> None:
        """Back out of the session flow, confirming if work would be lost."""
        def discard() -> None:
            self.state.store.discard_pending()
            self.draft = None
            self.pending_photo = None
            if self.editing and self.selected is not None:
                self._navigate("session_detail")
            else:
                self.go_home()

        if not self._has_unsaved_work():
            discard()
            return
        sid = self.draft.session_id
        if self.editing:
            title = f"Discard changes to {sid}?"
            body = "The saved session stays as it was."
        else:
            title = f"Leave without saving {sid}?"
            body = "Your selections will be lost. Use “Save as incomplete” to keep them."
        self.sheet.ask(title, body, confirm="Discard", cancel="Keep editing", on_confirm=discard)

    def photo_captured(self, path: str) -> None:
        self.pending_photo = path
        self.keep_photo = False
        self._navigate("confirm_photo")

    def retake_photo(self) -> None:
        self.state.store.discard_pending()
        self.pending_photo = None
        self._navigate("take_photo")

    def keep_existing_photo(self) -> None:
        self.state.store.discard_pending()
        self.pending_photo = None
        self.save_draft()

    def save_draft(self) -> None:
        """Write the draft as a new revision and show its printed label."""
        if self.draft is None:
            return
        pending = Path(self.pending_photo) if self.pending_photo else None
        try:
            saved = self.state.save(self.draft, pending)
        except OSError as exc:
            self.sheet.ask(
                "Could not save the session",
                f"Device storage reported: {exc.strerror or exc}. Nothing was changed. "
                "Free some space or check the storage, then try again.",
                confirm="Discard session", cancel="Try again later",
                on_confirm=self.go_home,
            )
            return
        self.last_saved = saved
        self.selected = saved
        self.draft = None
        self.pending_photo = None
        self._navigate("session_saved")

    # ---- export ----------------------------------------------------------
    def export_finished(self, result: ExportResult) -> None:
        self.last_export = result
        self._navigate("export_complete" if result.ok else "export_failed")

    def retry_export(self) -> None:
        if not self.state.ssd_connected:
            return
        self._navigate("export")
        self.screens["export"]._export()

    # ---- device status ---------------------------------------------------
    def _toggle_ssd(self) -> None:
        self.state.set_ssd_connected(not self.state.ssd_connected)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.camera.shutdown()
        super().closeEvent(event)


def seed_demo(state: AppState) -> None:
    """Populate an empty demo store with labelled demonstration sessions."""
    if state.sessions:
        return
    from datetime import datetime

    from .camera import render_scene

    demo = [
        ("S-0001", None, None, False, datetime(2026, 10, 9, 9, 12)),
        ("S-0002", "3", "+", True, datetime(2026, 10, 9, 14, 20)),
        ("S-0003", "4", None, False, datetime(2026, 10, 12, 11, 5)),
        ("S-0004", "3", "++", True, datetime(2026, 10, 12, 16, 42)),
        ("S-0005", "5", "±", True, datetime(2026, 10, 14, 10, 3)),
    ]
    for i, (sid, skin, grade, photo, when) in enumerate(demo):
        session = Session(session_id=sid, skin_type=skin, erythema_grade=grade,
                          created_at=when, demo=True)
        pending = None
        if photo:
            pending = state.store.pending_photo_path()
            render_scene(1600, 1200, t=i * 1.7, seed=11 + i).save(str(pending), "JPG", 90)
        state.save(session, pending, now=when)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Skin Assessment device UI")
    parser.add_argument("--kiosk", action="store_true", help="fullscreen, hidden cursor (device mode)")
    parser.add_argument("--demo", action="store_true", help="use a separate folder of demonstration data")
    parser.add_argument("--camera", choices=("auto", "pi", "sim"), default="auto")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args(argv)

    app = QApplication(sys.argv[:1])
    load_fonts()
    app.setFont(font("body"))
    app.setStyleSheet(stylesheet())

    data_dir = args.data_dir / "demo" if args.demo else args.data_dir
    state = AppState(data_dir, demo=args.demo)
    if args.demo:
        seed_demo(state)
    camera = create_camera(args.camera)
    reduced = os.environ.get("SKIN_REDUCED_MOTION") == "1"
    window = MainWindow(state, camera, reduced_motion=reduced)

    if args.kiosk:
        app.setOverrideCursor(Qt.BlankCursor)
        window.setWindowFlag(Qt.FramelessWindowHint)
        window.showFullScreen()
    else:
        window.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
