"""Past sessions list screen (wireframe page 6)."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..app_state import Session
from ..widgets import Header, make_button


class SessionRow(QWidget):
    """A single tappable row representing a saved session."""

    def __init__(self, session: Session, on_open) -> None:
        super().__init__()
        self.session = session
        self.on_open = on_open
        self.setObjectName(
            "SessionRow" if session.is_complete else "SessionRowIncomplete"
        )
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(68)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 16, 8)
        layout.setSpacing(14)

        # Thumbnail.
        thumb = QLabel("img" if session.has_photo else "no img")
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setFixedSize(52, 52)
        thumb.setObjectName("RowThumb" if session.has_photo else "RowThumbEmpty")
        layout.addWidget(thumb)

        # Id + date.
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        row_id = QLabel(session.session_id)
        row_id.setObjectName("RowId")
        row_date = QLabel(session.saved_at_display)
        row_date.setObjectName("RowDate")
        text_col.addWidget(row_id)
        text_col.addWidget(row_date)
        layout.addLayout(text_col)

        layout.addStretch(1)

        # Status pill.
        status = QLabel(session.status_label)
        status.setObjectName(
            "StatusComplete" if session.is_complete else "StatusIncomplete"
        )
        status.setAlignment(Qt.AlignCenter)
        layout.addWidget(status)

        chevron = QLabel("\u203a")
        chevron.setStyleSheet("font-size: 22px; font-weight: 700;")
        layout.addWidget(chevron)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.LeftButton:
            self.on_open(self.session)
        super().mouseReleaseEvent(event)


class PastSessionsScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        self._filter = "all"

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        self.header = Header("Past sessions")
        self.header.back_clicked.connect(self.controller.go_home)
        root.addWidget(self.header)

        # Filter chips.
        chips = QHBoxLayout()
        chips.setSpacing(12)
        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)

        self.all_chip = make_button("All", "chip")
        self.complete_chip = make_button("Complete", "chip")
        self.incomplete_chip = make_button("Incomplete", "chip")
        self.incomplete_chip.setProperty("dashed", "true")

        for chip, key in (
            (self.all_chip, "all"),
            (self.complete_chip, "complete"),
            (self.incomplete_chip, "incomplete"),
        ):
            chip.setCheckable(True)
            chip.clicked.connect(lambda _=False, k=key: self._set_filter(k))
            self.chip_group.addButton(chip)
            chips.addWidget(chip)
        chips.addStretch(1)
        self.all_chip.setChecked(True)
        root.addLayout(chips)

        # Scrollable list.
        self.scroll = QScrollArea()
        self.scroll.setObjectName("ScrollArea")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)
        self.scroll.setWidget(self.list_container)
        root.addWidget(self.scroll, 1)

        helper = QLabel(
            "Solid = complete, dashed = incomplete. Tap a row to open it."
        )
        helper.setObjectName("HelperText")
        root.addWidget(helper)

    def _set_filter(self, key: str) -> None:
        self._filter = key
        self._rebuild()

    def _filtered(self) -> List[Session]:
        # Newest first.
        sessions = sorted(
            self.controller.state.sessions,
            key=lambda s: s.saved_at or 0,
            reverse=True,
        )
        if self._filter == "complete":
            return [s for s in sessions if s.is_complete]
        if self._filter == "incomplete":
            return [s for s in sessions if not s.is_complete]
        return sessions

    def _rebuild(self) -> None:
        # Clear existing rows.
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        for session in self._filtered():
            row = SessionRow(session, self.controller.show_session_detail)
            self.list_layout.addWidget(row)
        self.list_layout.addStretch(1)

        total = len(self.controller.state.sessions)
        self.all_chip.setText(f"All ({total})")

    def on_enter(self) -> None:
        self._rebuild()
