"""New Session screen (Figma 02): shows the next session ID and the time now."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from ..theme import px
from ..widgets import FigmaScreen, action_button


def _label(text: str, name: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName(name)
    lbl.setAlignment(Qt.AlignCenter)
    return lbl


class NewSessionScreen(FigmaScreen):
    def __init__(self, controller) -> None:
        super().__init__("New Session")
        self.controller = controller

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedSize(px(406), px(320))
        lay = QVBoxLayout(card)
        lay.setSpacing(px(6))
        lay.addStretch(1)
        lay.addWidget(_label("Session ID", "Caption"))
        self.id_value = _label("", "BigValue")
        lay.addWidget(self.id_value)
        lay.addSpacing(px(14))
        lay.addWidget(_label("Session Date & Time", "Caption"))
        self.date_value = _label("", "DateValue")
        lay.addWidget(self.date_value)
        lay.addStretch(1)

        self.content.addStretch(1)
        self.content.addWidget(card, 0, Qt.AlignHCenter)
        self.content.addStretch(1)

        self.set_footer(
            left=[action_button("Back", "secondary", 160, self.controller.go_home)],
            right=[action_button("Start Session", "primary", 260,
                                 self.controller.begin_assessment)],
        )

    def on_enter(self) -> None:
        session = self.controller.draft_session
        self.id_value.setText(session.session_id if session else "—")
        # The time this screen opened, e.g. "09 Oct 2026, 10:00 AM".
        self.date_value.setText(datetime.now().strftime("%d %b %Y, %I:%M %p"))
