"""Step 2 of 4: live viewfinder and capture."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout

from ..camera import CameraState
from ..theme import GAP, C
from ..widgets import InkButton, Viewfinder, make_label
from .base import Screen


class TakePhotoScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Take photo", step=2)

        row = QHBoxLayout()
        row.setSpacing(GAP)
        self.viewfinder = Viewfinder()
        row.addWidget(self.viewfinder, 1)

        side = QVBoxLayout()
        side.setSpacing(GAP)
        self.capture_btn = InkButton("Capture", "primary", icon="camera", size="title",
                                     on_click=self._capture)
        self.capture_btn.setMinimumHeight(150)
        self.capture_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        side.addWidget(self.capture_btn, 1)
        self.keep_btn = InkButton("Keep current photo", "secondary", icon="check",
                                  on_click=self._keep_existing)
        side.addWidget(self.keep_btn)
        self.save_btn = InkButton("Save as incomplete", "secondary", icon="save",
                                  on_click=self._save_incomplete)
        side.addWidget(self.save_btn)
        self.cam_info = make_label("", "small", QFont.Medium, color=C.INK_ON_LINER, wrap=True)
        side.addWidget(self.cam_info)

        row.addLayout(side)
        side_width = 236
        for w in (self.capture_btn, self.keep_btn, self.save_btn, self.cam_info):
            w.setFixedWidth(side_width)
        self.body.addLayout(row, 1)

        cam = controller.camera
        cam.frame_ready.connect(self._on_frame)
        cam.capture_finished.connect(self._on_captured)
        cam.capture_failed.connect(self._on_capture_failed)
        self._capturing = False
        self._active = False

    # ---- lifecycle -------------------------------------------------------
    def on_enter(self) -> None:
        self._active = True
        draft = self.controller.draft
        self.head.set_session_id(draft.session_id if draft else None)
        self._capturing = False
        self.viewfinder.set_overlay("")
        self.keep_btn.setVisible(bool(draft and draft.has_photo))

        cam = self.controller.camera
        if cam.state == CameraState.UNAVAILABLE:
            self.viewfinder.set_unavailable(cam.error)
            self.capture_btn.setEnabled(False)
            self.cam_info.setText("Capture is unavailable. You can still save this session as incomplete.")
        else:
            self.viewfinder.set_image(None)
            self.viewfinder.set_flag(*(("LIVE", "ink") if cam.state == CameraState.LIVE
                                       else ("SIMULATED", "stat")))
            self.capture_btn.setEnabled(True)
            if cam.state == CameraState.SIMULATED:
                self.cam_info.setText("Simulated camera. Photos are synthetic and not for clinical use.")
            else:
                self.cam_info.setText(cam.description)
            cam.start()

    def on_leave(self) -> None:
        self._active = False
        if not self._capturing:
            self.controller.camera.stop()

    # ---- camera events ---------------------------------------------------
    def _on_frame(self, image) -> None:
        if self._active and not self._capturing:
            self.viewfinder.set_image(image)

    def _capture(self) -> None:
        if self._capturing:
            return
        self._capturing = True
        self.capture_btn.setText("Capturing…")
        self.viewfinder.set_overlay("Hold still")
        self.controller.camera.capture(self.controller.state.store.pending_photo_path())

    def _reset_capture_ui(self) -> None:
        self._capturing = False
        self.capture_btn.setText("Capture")
        self.capture_btn.setEnabled(self.controller.camera.state != CameraState.UNAVAILABLE)
        self.viewfinder.set_overlay("")

    def _on_captured(self, path: str) -> None:
        self._reset_capture_ui()
        if not self._active:
            return
        self.controller.camera.stop()
        self.controller.photo_captured(path)

    def _on_capture_failed(self, reason: str) -> None:
        self._reset_capture_ui()
        if self._active:
            self.cam_info.setText(f"{reason} Try again, or save as incomplete.")

    # ---- actions ---------------------------------------------------------
    def on_back(self) -> None:
        self.controller.show_assessment()

    def _keep_existing(self) -> None:
        self.controller.keep_existing_photo()

    def _save_incomplete(self) -> None:
        self.controller.save_draft()
