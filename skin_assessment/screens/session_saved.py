"""Session saved screen (wireframe page 4): step 4 of the new-session flow."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..widgets import Header, ImagePlaceholder, make_button


class SessionSavedScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        self.header = Header("Session saved (step 4)")
        self.header.back_clicked.connect(self.controller.go_home)
        root.addWidget(self.header)

        body = QHBoxLayout()
        body.setSpacing(16)

        self.preview = ImagePlaceholder("[ captured photo preview ]")
        body.addWidget(self.preview, 3)

        right = QVBoxLayout()
        right.setSpacing(16)

        # Summary card.
        card = QWidget()
        card.setObjectName("Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        self.value_labels = {}
        rows = [
            ("Session ID", "session_id"),
            ("Saved at", "saved_at"),
            ("Skin type", "skin_type"),
            ("Erythema grade", "erythema_grade"),
            ("Status", "status"),
        ]
        for i, (label_text, key) in enumerate(rows):
            lbl = QLabel(label_text)
            val = QLabel("—")
            val.setObjectName("ValueStrong")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(lbl, i, 0)
            grid.addWidget(val, i, 1)
            self.value_labels[key] = val
        right.addWidget(card)

        right.addStretch(1)

        self.view_btn = make_button(
            "View past sessions", "primary", self.controller.show_past_sessions
        )
        self.home_btn = make_button("Home", "outline", self.controller.go_home)
        right.addWidget(self.view_btn)
        right.addWidget(self.home_btn)
        body.addLayout(right, 1)

        root.addLayout(body, 1)

    def on_enter(self) -> None:
        session = self.controller.last_saved_session
        if session is None:
            return
        self.value_labels["session_id"].setText(session.session_id)
        self.value_labels["saved_at"].setText(session.saved_at_display)
        self.value_labels["skin_type"].setText(
            session.field_or_dash(session.skin_type)
        )
        self.value_labels["erythema_grade"].setText(
            session.field_or_dash(session.erythema_grade)
        )
        self.value_labels["status"].setText(
            "Complete" if session.is_complete else "Incomplete"
        )
