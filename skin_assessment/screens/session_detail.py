"""Session detail: photo and the session's printed label."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ..theme import GAP, C
from ..widgets import Barcode, InkButton, LabelCard, PhotoView, ValueList, make_label
from .base import Screen


class SessionDetailScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Session")

        row = QHBoxLayout()
        row.setSpacing(GAP)
        self.photo = PhotoView("No photo")
        row.addWidget(self.photo, 1)

        side = QVBoxLayout()
        side.setSpacing(GAP)
        self.card = LabelCard("solid", padding=(16, 10, 16, 12))
        cl = QVBoxLayout(self.card)
        cl.setSpacing(4)
        self.values = ValueList()
        self.values.add_row("Skin type")
        self.values.add_row("Erythema grade")
        self.values.add_row("Saved", mono=False)
        self.values.add_row("Created")
        self.values.add_row("Revision", mono=True)
        cl.addWidget(self.values)
        cl.addSpacing(4)
        self.barcode = Barcode("", bar_height=30)
        cl.addWidget(self.barcode, 0, Qt.AlignLeft)
        side.addWidget(self.card)
        side.addStretch(1)
        self.edit_btn = InkButton("Edit session", "primary", icon="edit", on_click=self._edit)
        side.addWidget(self.edit_btn)
        holder = QWidget()
        holder.setLayout(side)
        holder.setFixedWidth(330)
        side.setContentsMargins(0, 0, 0, 0)
        row.addWidget(holder)
        self.body.addLayout(row, 1)

    def on_enter(self) -> None:
        session = self.controller.selected
        if session is None:
            return
        self.head.set_title("Session")
        self.head.set_session_id(session.session_id)
        if session.is_complete:
            self.card.set_edge("solid")
            self.card.set_band("COMPLETE", "ink")
            self.edit_btn.setText("Edit session")
        else:
            self.card.set_edge("perforated")
            self.card.set_band("INCOMPLETE · MISSING " + ", ".join(session.missing_fields()).upper(), "stat")
            self.edit_btn.setText("Continue session")
        self.values.set("Skin type", session.field_or_dash(session.skin_type))
        self.values.set("Erythema grade", session.field_or_dash(session.erythema_grade))
        self.values.set("Saved", session.saved_at_display)
        self.values.set("Created", session.created_at_display)
        self.values.set("Revision", str(session.revision))
        self.barcode.set_text(session.session_id)
        self.photo.set_path(session.photo_path if session.has_photo else None)
        self.photo.set_empty_text("No photo yet")

    def on_back(self) -> None:
        self.controller.show_past_sessions()

    def _edit(self) -> None:
        session = self.controller.selected
        if session is not None:
            self.controller.edit_session(session)
