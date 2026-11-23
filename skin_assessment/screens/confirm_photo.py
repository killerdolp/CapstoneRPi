"""Step 4 of 5: review the captured photo, then confirm and save."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFont, QImageReader
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from ..theme import GAP, C
from ..widgets import InkButton, LabelCard, PhotoView, ValueList, make_label
from .base import Screen


class ConfirmPhotoScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Confirm photo", step=4)

        row = QHBoxLayout()
        row.setSpacing(GAP)
        self.preview = PhotoView("No photo captured")
        row.addWidget(self.preview, 1)

        side = QVBoxLayout()
        side.setSpacing(GAP)
        card = LabelCard("plain", padding=(16, 8, 16, 12))
        cl = QVBoxLayout(card)
        cl.setSpacing(6)
        self.values = ValueList()
        self.values.add_row("Skin type")
        self.values.add_row("Erythema grade")
        self.values.add_row("Photo", mono=True)
        cl.addWidget(self.values)
        note = make_label("Confirming stamps the save time and writes the session to this device.",
                          "small", color=C.INK_SOFT, wrap=True)
        cl.addWidget(note)
        side.addWidget(card)
        side.addStretch(1)
        self.retake_btn = InkButton("Retake", "secondary", icon="retake", on_click=self._retake)
        self.confirm_btn = InkButton("Confirm & save", "primary", icon="check", on_click=self._confirm)
        side.addWidget(self.retake_btn)
        side.addWidget(self.confirm_btn)
        for w in (card, self.retake_btn, self.confirm_btn):
            w.setFixedWidth(288)
        row.addLayout(side)
        self.body.addLayout(row, 1)

    def on_enter(self) -> None:
        draft = self.controller.draft
        path = self.controller.pending_photo
        self.head.set_session_id(draft.session_id if draft else None)
        self.preview.set_path(Path(path) if path else None)
        if draft:
            self.values.set("Skin type", draft.field_or_dash(draft.skin_type))
            self.values.set("Erythema grade", draft.field_or_dash(draft.erythema_grade))
        size = QImageReader(str(path)).size() if path else None
        self.values.set("Photo", f"{size.width()}×{size.height()}" if size and size.isValid() else "—")
        self.confirm_btn.setEnabled(bool(path))

    def on_back(self) -> None:
        self._retake()

    def _retake(self) -> None:
        self.controller.retake_photo()

    def _confirm(self) -> None:
        self.controller.save_draft()
