"""Past Sessions list screen (Figma 08)."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..app_state import Session
from ..theme import px
from ..widgets import FigmaScreen, action_button


class SessionRow(QFrame):
    """A single tappable card representing a saved session."""

    def __init__(self, session: Session, on_open) -> None:
        super().__init__()
        self.session = session
        self.on_open = on_open
        self.setObjectName("SessionCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(px(88))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(px(18), 0, px(42), 0)
        layout.setSpacing(px(32))

        row_id = QLabel(session.session_id)
        row_id.setObjectName("RowId")
        layout.addWidget(row_id)
        row_date = QLabel(session.saved_at_display)
        row_date.setObjectName("RowMeta")
        layout.addWidget(row_date)
        layout.addStretch(1)
        status = QLabel(session.status_label)
        status.setObjectName("RowMeta")
        layout.addWidget(status)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.LeftButton:
            self.on_open(self.session)
        super().mouseReleaseEvent(event)


class PastSessionsScreen(FigmaScreen):
    def __init__(self, controller) -> None:
        super().__init__("Past Sessions")
        self.controller = controller
        self._filter = "all"
        self.content.setContentsMargins(px(40), px(8), px(40), 0)
        self.content.setSpacing(px(22))

        # Filter chips.
        chips = QHBoxLayout()
        chips.setSpacing(px(16))
        chips.addStretch(1)
        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)
        self.all_chip = action_button("All", "chip", 180, figma_height=56)
        self.complete_chip = action_button("Complete", "chip", 180, figma_height=56)
        self.incomplete_chip = action_button("Incomplete", "chip", 180, figma_height=56)
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
        self.content.addLayout(chips)

        # Scrollable list.
        self.scroll = QScrollArea()
        self.scroll.setObjectName("SessionList")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(px(12))
        self.scroll.setWidget(self.list_container)
        self.content.addWidget(self.scroll, 1)

        self.back_btn = action_button("Back", "secondary", 160, self.controller.go_home)
        self.set_footer(left=[self.back_btn])

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

    def on_enter(self) -> None:
        self._rebuild()
