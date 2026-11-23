"""Review Image screen (Figma 06): review the capture, then confirm and save."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ..theme import px
from ..widgets import FigmaScreen, Preview, action_button


class ConfirmPhotoScreen(FigmaScreen):
    def __init__(self, controller) -> None:
        super().__init__("Review Image", step="Step 3 of 3")
        self.controller = controller

        hint = QLabel("Captured Image Preview")
        hint.setObjectName("Hint")
        hint.setAlignment(Qt.AlignCenter)
        self.preview = Preview("Captured Image", 780, 299)

        self.content.setSpacing(px(4))
        self.content.addStretch(1)
        self.content.addWidget(hint)
        self.content.addWidget(self.preview, 0, Qt.AlignHCenter)
        self.content.addStretch(1)

        self.retake_btn = action_button(
            "Retake", "secondary", 160, self.controller.retake_photo
        )
        self.confirm_btn = action_button("Confirm && Save", "primary", 184, self._confirm)
        self.set_footer(left=[self.retake_btn], right=[self.confirm_btn])

    def on_enter(self) -> None:
        # Show the draft capture so it can be checked before saving.
        self.preview.show_file(self.controller.state.pending_photo_path, "Captured Image")

    def _confirm(self) -> None:
        self.controller.save_draft(complete=True)
        self.controller.show_session_saved()
