"""Capture Image screen (Figma 05): step 3 of the new-session flow.

The camera writes the still to the draft path (photos/pending.jpg). The
session and database change only on Confirm & Save; see AppState.save_session.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QLabel

from ..camera import CameraState
from ..theme import px
from ..widgets import FigmaScreen, Preview, action_button


class TakePhotoScreen(FigmaScreen):
    def __init__(self, controller) -> None:
        super().__init__("Capture Image", step="Step 3 of 3")
        self.controller = controller
        self.camera = controller.camera
        self._capturing = False

        self.hint = QLabel("Position the hand/foot beneath the camera")
        self.hint.setObjectName("Hint")
        self.hint.setAlignment(Qt.AlignCenter)
        # Camera viewfinder.
        self.viewfinder = Preview("Live Camera Preview", 780, 299)

        self.content.setSpacing(px(4))
        self.content.addStretch(1)
        self.content.addWidget(self.hint)
        self.content.addWidget(self.viewfinder, 0, Qt.AlignHCenter)
        self.content.addStretch(1)

        self.capture_btn = action_button("Capture", "primary", 184, self._capture)
        self.save_btn = action_button("Save", "secondary", 160, self._save_incomplete)
        self.back_btn = action_button(
            "Back", "secondary", 160, self.controller.show_erythema_grade
        )
        self.set_footer(left=[self.back_btn], right=[self.save_btn, self.capture_btn])

        self.camera.frame_ready.connect(self._on_frame)
        self.camera.capture_finished.connect(self._on_captured)
        self.camera.capture_failed.connect(self._on_capture_failed)

    def on_enter(self) -> None:
        self._capturing = False
        self._set_busy(False)
        if self.camera.state == CameraState.UNAVAILABLE:
            self.capture_btn.setEnabled(False)
            self.viewfinder.show_caption("Camera not available")
            self.hint.setText(self.camera.error or "No camera detected.")
            return
        self.capture_btn.setEnabled(True)
        self.hint.setText("Position the hand/foot beneath the camera")
        self.viewfinder.show_caption("Starting camera\u2026")
        self.camera.start()

    def on_leave(self) -> None:
        self.camera.stop()

    def _set_busy(self, busy: bool) -> None:
        for btn in (self.capture_btn, self.save_btn, self.back_btn):
            btn.setEnabled(not busy)

    # ---- camera signals -----------------------------------------------------
    def _on_frame(self, image: QImage) -> None:
        if self.isVisible() and not self._capturing:
            self.viewfinder.show_image(image)

    def _on_captured(self, _path: str) -> None:
        if not self._capturing:
            return
        self._capturing = False
        self.controller.show_confirm_photo()

    def _on_capture_failed(self, reason: str) -> None:
        self._capturing = False
        self._set_busy(False)
        self.hint.setText(reason)

    # ---- actions ------------------------------------------------------------
    def _capture(self) -> None:
        # Write the draft photo only; the session and database are unchanged
        # until Confirm & Save.
        self._capturing = True
        self._set_busy(True)
        self.viewfinder.show_caption("Capturing\u2026")
        self.camera.capture(self.controller.state.pending_photo_path)

    def _save_incomplete(self) -> None:
        self.controller.save_draft(complete=False)
        self.controller.go_home()
