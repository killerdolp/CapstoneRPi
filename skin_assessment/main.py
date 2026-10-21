"""Entry point and navigation controller for the Skin Assessment app.

Run with:
    .venv/bin/python -m skin_assessment.main

A MainWindow hosts a QStackedWidget. Each wireframe screen is a page, and the
controller exposes navigation methods the screens call. A small draft-session
workflow carries data through the new-session steps.
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from .app_state import AppState, Session
from .theme import SCREEN_HEIGHT, SCREEN_WIDTH, STYLESHEET
from .screens.assessment import AssessmentScreen
from .screens.confirm_photo import ConfirmPhotoScreen
from .screens.export_complete import ExportCompleteScreen
from .screens.export_data import ExportDataScreen
from .screens.export_failed import ExportFailedScreen
from .screens.home import HomeScreen
from .screens.past_sessions import PastSessionsScreen
from .screens.session_detail import SessionDetailScreen
from .screens.session_saved import SessionSavedScreen
from .screens.take_photo import TakePhotoScreen


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Skin Assessment")
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.state = AppState()

        # Workflow state.
        self.draft_session: Optional[Session] = None
        self.last_saved_session: Optional[Session] = None
        self.selected_session: Optional[Session] = None
        self._editing: bool = False

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Instantiate screens.
        self.screens: Dict[str, QWidget] = {
            "home": HomeScreen(self),
            "assessment": AssessmentScreen(self),
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
        on_enter = getattr(screen, "on_enter", None)
        if callable(on_enter):
            on_enter()
        self.stack.setCurrentWidget(screen)

    # ---- navigation API used by screens ----------------------------------
    def go_home(self) -> None:
        self._navigate("home")

    def start_new_session(self) -> None:
        self._editing = False
        self.draft_session = Session(session_id=self.state.next_session_id())
        self._navigate("assessment")

    def edit_session(self, session: Session) -> None:
        self._editing = True
        self.draft_session = session
        self._navigate("assessment")

    def show_assessment(self) -> None:
        self._navigate("assessment")

    def show_take_photo(self) -> None:
        self._navigate("take_photo")

    def show_confirm_photo(self) -> None:
        self._navigate("confirm_photo")

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
        """Persist the draft session into app state."""
        if self.draft_session is None:
            return
        self.draft_session.saved_at = datetime.now()
        if not self._editing:
            self.state.add_session(self.draft_session)
        self.last_saved_session = self.draft_session

    def _toggle_ssd(self) -> None:
        self.state.ssd_connected = not self.state.ssd_connected
        # Refresh whatever screen is visible.
        current = self.stack.currentWidget()
        on_enter = getattr(current, "on_enter", None)
        if callable(on_enter):
            on_enter()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
