"""Take photo screen (wireframe page 2): step 2 of the new-session flow."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from ..widgets import Header, ImagePlaceholder, make_button


class TakePhotoScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        self.header = Header("Take photo (step 2)")
        self.header.back_clicked.connect(self.controller.show_assessment)
        root.addWidget(self.header)

        body = QHBoxLayout()
        body.setSpacing(16)

        # Camera viewfinder placeholder.
        self.viewfinder = ImagePlaceholder("[ camera viewfinder ]")
        body.addWidget(self.viewfinder, 3)

        # Right column: Capture + Save.
        right = QVBoxLayout()
        right.setSpacing(16)
        self.capture_btn = make_button("Capture", "primary", self._capture)
        self.capture_btn.setMinimumHeight(0)
        self.capture_btn.setSizePolicy(
            self.capture_btn.sizePolicy().horizontalPolicy(),
            self.capture_btn.sizePolicy().verticalPolicy(),
        )
        right.addWidget(self.capture_btn, 3)

        self.save_btn = make_button(
            "Save (incomplete)", "outline", self._save_incomplete
        )
        right.addWidget(self.save_btn, 1)
        body.addLayout(right, 1)

        root.addLayout(body, 1)

    def on_enter(self) -> None:
        pass

    def _capture(self) -> None:
        # Front-end stub: mark that a photo exists and move to confirm.
        self.controller.draft_session.has_photo = True
        self.controller.show_confirm_photo()

    def _save_incomplete(self) -> None:
        self.controller.save_draft(complete=False)
        self.controller.go_home()
