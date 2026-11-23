"""Entry point and navigation controller for the Skin Assessment app.

Run with:
    .venv/bin/python -m skin_assessment.main            # real database
    .venv/bin/python -m skin_assessment.main --demo     # separate demo database
    .venv/bin/python -m skin_assessment.main --kiosk    # fullscreen device mode

Options: ``--camera {auto,pi,sim}`` (auto uses the Pi camera on a Pi and a
simulated camera elsewhere), ``--db PATH``.

A MainWindow hosts a QStackedWidget. Each screen is a page, and the
controller exposes navigation methods the screens call. A draft session
carries data through the new-session and edit-session steps.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget

from .app_state import DEFAULT_DB_PATH, AppState, Session
from .camera import CameraBackend, create_camera
from .export import ExportRequest, ExportResult, SimulatedExporter
from .theme import SCREEN_HEIGHT, SCREEN_WIDTH, STYLESHEET, load_fonts
from .screens.assessment import ErythemaGradeScreen, SkinTypeScreen
from .screens.confirm_photo import ConfirmPhotoScreen
from .screens.export_complete import ExportCompleteScreen
from .screens.export_data import ExportDataScreen
from .screens.export_failed import ExportFailedScreen
from .screens.home import HomeScreen
from .screens.new_session import NewSessionScreen
from .screens.past_sessions import PastSessionsScreen
from .screens.session_detail import SessionDetailScreen
from .screens.session_saved import SessionSavedScreen
from .screens.take_photo import TakePhotoScreen


class MainWindow(QMainWindow):
    def __init__(self, state: AppState, camera: CameraBackend) -> None:
        super().__init__()
        self.setWindowTitle("Whyre 2D Imaging")

        self.state = state
        self.camera = camera
        self.exporter = SimulatedExporter(state)
        self.exporter.finished.connect(self.export_finished)
        self.last_export: Optional[ExportResult] = None

        # Workflow state.
        self.draft_session: Optional[Session] = None
        self.last_saved_session: Optional[Session] = None
        self.selected_session: Optional[Session] = None
        self._editing: bool = False

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.screens: Dict[str, QWidget] = {
            "home": HomeScreen(self),
            "new_session": NewSessionScreen(self),
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

        self._navigate("home")

        # Developer shortcut: toggle SSD connection (Ctrl+D) to demo the
        # connected / not-connected / failed export states.
        toggle = QShortcut(QKeySequence("Ctrl+D"), self)
        toggle.activated.connect(self._toggle_ssd)

    # ---- navigation core --------------------------------------------------
    def _navigate(self, key: str) -> None:
        screen = self.screens[key]
        current = self.stack.currentWidget()
        if current is not None and current is not screen:
            # Lets the Capture screen stop the camera preview.
            on_leave = getattr(current, "on_leave", None)
            if callable(on_leave):
                on_leave()
        on_enter = getattr(screen, "on_enter", None)
        if callable(on_enter):
            on_enter()
        self.stack.setCurrentWidget(screen)

    @property
    def editing(self) -> bool:
        return self._editing

    # ---- navigation API used by screens ----------------------------------
    def go_home(self) -> None:
        # Leaving the flow without Confirm & Save drops any draft photo.
        self.state.discard_pending_photo()
        self._navigate("home")

    def start_new_session(self) -> None:
        """Open the New Session screen with the ID the database will assign."""
        self._editing = False
        self.draft_session = Session(session_id=self.state.next_session_id())
        self._navigate("new_session")

    def begin_assessment(self) -> None:
        self._navigate("skin_type")

    def edit_session(self, session: Session) -> None:
        self._editing = True
        self.draft_session = session
        self._navigate("skin_type")

    def show_skin_type(self) -> None:
        self._navigate("skin_type")

    def show_erythema_grade(self) -> None:
        self._navigate("erythema_grade")

    def show_take_photo(self) -> None:
        self._navigate("take_photo")

    def show_confirm_photo(self) -> None:
        self._navigate("confirm_photo")

    def retake_photo(self) -> None:
        self.state.discard_pending_photo()
        self._navigate("take_photo")

    def show_session_saved(self) -> None:
        self._navigate("session_saved")

    def show_past_sessions(self) -> None:
        self._navigate("past_sessions")

    def show_session_detail(self, session: Session) -> None:
        self.selected_session = session
        self._navigate("session_detail")

    def show_export(self) -> None:
        self._navigate("export")

    def show_export_complete(self) -> None:
        self._navigate("export_complete")

    def show_export_failed(self) -> None:
        self._navigate("export_failed")

    # ---- workflow helpers -------------------------------------------------
    def save_draft(self, complete: bool) -> None:
        """Persist the draft session (insert if new, update if editing).

        complete=True is Confirm & Save: the draft photo is kept as the
        session's photo. Any other save discards the draft photo.
        """
        if self.draft_session is None:
            return
        self.last_saved_session = self.state.save_session(
            self.draft_session, commit_photo=complete
        )

    def start_export(self, request: ExportRequest) -> None:
        self.exporter.start(request)

    def export_finished(self, result: ExportResult) -> None:
        self.last_export = result
        if result.ok:
            self.show_export_complete()
        else:
            self.show_export_failed()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self.camera.shutdown()
        self.state.discard_pending_photo()
        super().closeEvent(event)

    def _toggle_ssd(self) -> None:
        self.state.ssd_connected = not self.state.ssd_connected
        current = self.stack.currentWidget()
        on_enter = getattr(current, "on_enter", None)
        if callable(on_enter):
            on_enter()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Whyre 2D Imaging device UI")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH,
                        help=f"SQLite database file (default {DEFAULT_DB_PATH})")
    parser.add_argument("--demo", action="store_true",
                        help="use demo.db next to the database, seeded with sample sessions")
    parser.add_argument("--kiosk", action="store_true",
                        help="fullscreen, frameless, hidden cursor (device mode)")
    parser.add_argument("--camera", choices=("auto", "pi", "sim"), default="auto")
    args = parser.parse_args(argv)

    db_path = args.db.with_name("demo.db") if args.demo else args.db

    app = QApplication(sys.argv[:1])
    load_fonts()
    app.setStyleSheet(STYLESHEET)
    window = MainWindow(AppState(db_path, demo=args.demo), create_camera(args.camera))
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
