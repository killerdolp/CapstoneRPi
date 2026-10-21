"""Session detail screen (wireframe page 7)."""

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


class SessionDetailScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        self.header = Header("Session")
        self.header.back_clicked.connect(self.controller.show_past_sessions)
        root.addWidget(self.header)

        body = QHBoxLayout()
        body.setSpacing(16)

        self.photo = ImagePlaceholder("[ session photo ]")
        body.addWidget(self.photo, 1)

        right = QVBoxLayout()
        right.setSpacing(12)

        # Saved-at + status pill row.
        top_row = QHBoxLayout()
        self.saved_label = QLabel()
        self.saved_label.setObjectName("FieldLabel")
        top_row.addWidget(self.saved_label)
        top_row.addStretch(1)
        self.status_pill = QLabel()
        self.status_pill.setAlignment(Qt.AlignCenter)
        top_row.addWidget(self.status_pill)
        right.addLayout(top_row)

        # Values card.
        card = QWidget()
        card.setObjectName("Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("Skin type"), 0, 0)
        self.skin_value = QLabel("—")
        self.skin_value.setObjectName("ValueStrong")
        self.skin_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.skin_value, 0, 1)

        grid.addWidget(QLabel("Erythema grade"), 1, 0)
        self.erythema_value = QLabel("—")
        self.erythema_value.setObjectName("ValueStrong")
        self.erythema_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.erythema_value, 1, 1)
        right.addWidget(card)

        helper = QLabel(
            'Incomplete sessions show unfilled fields as \u201c\u2014\u201d '
            "and no photo."
        )
        helper.setObjectName("HelperText")
        helper.setWordWrap(True)
        right.addWidget(helper)

        right.addStretch(1)

        self.edit_btn = make_button("Edit session", "primary", self._edit)
        right.addWidget(self.edit_btn)
        body.addLayout(right, 1)

        root.addLayout(body, 1)

    def on_enter(self) -> None:
        session = self.controller.selected_session
        if session is None:
            return
        self.header.set_title(f"Session {session.session_id}")
        self.saved_label.setText(f"Saved {session.saved_at_display}")

        if session.is_complete:
            self.status_pill.setText("COMPLETE")
            self.status_pill.setObjectName("StatusComplete")
        else:
            self.status_pill.setText("INCOMPLETE")
            self.status_pill.setObjectName("StatusIncomplete")
        # Re-polish so the objectName style change takes effect.
        self.status_pill.style().unpolish(self.status_pill)
        self.status_pill.style().polish(self.status_pill)

        self.skin_value.setText(session.field_or_dash(session.skin_type))
        self.erythema_value.setText(
            session.field_or_dash(session.erythema_grade)
        )

        # Hide photo placeholder content when there is no photo.
        self.photo.setText(
            "[ session photo ]" if session.has_photo else "[ no photo ]"
        )

    def _edit(self) -> None:
        session = self.controller.selected_session
        if session is not None:
            self.controller.edit_session(session)
