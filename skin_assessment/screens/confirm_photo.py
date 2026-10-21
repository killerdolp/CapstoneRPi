"""Confirm photo screen (wireframe page 3): step 3 of the new-session flow."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..widgets import Header, ImagePlaceholder, make_button


class ConfirmPhotoScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        self.header = Header("Confirm photo (step 3)")
        self.header.back_clicked.connect(self.controller.show_take_photo)
        root.addWidget(self.header)

        body = QHBoxLayout()
        body.setSpacing(16)

        self.preview = ImagePlaceholder("[ captured photo preview ]")
        body.addWidget(self.preview, 3)

        right = QVBoxLayout()
        right.setSpacing(12)

        helper = QLabel(
            "Confirming stamps the save time and writes the session to file."
        )
        helper.setObjectName("HelperText")
        helper.setWordWrap(True)
        helper.setAlignment(Qt.AlignTop)
        right.addWidget(helper)

        right.addStretch(1)

        self.retake_btn = make_button(
            "Retake", "outline", self.controller.show_take_photo
        )
        self.confirm_btn = make_button(
            "Confirm & save", "primary", self._confirm
        )
        right.addWidget(self.retake_btn)
        right.addWidget(self.confirm_btn)
        body.addLayout(right, 1)

        root.addLayout(body, 1)

    def on_enter(self) -> None:
        pass

    def _confirm(self) -> None:
        self.controller.draft_session.has_photo = True
        self.controller.save_draft(complete=True)
        self.controller.show_session_saved()
