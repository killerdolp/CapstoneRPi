"""Step 5 of 5: the saved session's label feeds out of the printer."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ..theme import GAP, C
from ..widgets import (
    Barcode,
    Icon,
    InkButton,
    LabelCard,
    PrintFeed,
    Thumb,
    ValueList,
    make_label,
)
from .base import Screen


class SessionLabel(LabelCard):
    """The printed record: status band, ID, barcode, values, photo."""

    def __init__(self) -> None:
        super().__init__("solid", padding=(20, 12, 20, 14))
        lay = QVBoxLayout(self)
        lay.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(16)
        ident = QVBoxLayout()
        ident.setSpacing(2)
        self.id_label = make_label("", "display", QFont.Bold, mono=True)
        self.saved = make_label("", "small", QFont.Medium, color=C.INK_SOFT)
        ident.addWidget(self.id_label)
        ident.addWidget(self.saved)
        top.addLayout(ident)
        top.addStretch(1)
        self.thumb = Thumb(84)
        top.addWidget(self.thumb, 0, Qt.AlignTop)
        lay.addLayout(top)

        self.values = ValueList()
        self.values.add_row("Skin type")
        self.values.add_row("Erythema grade")
        self.values.add_row("Photo")
        lay.addWidget(self.values)
        lay.addStretch(1)
        self.barcode = Barcode("", bar_height=34)
        lay.addWidget(self.barcode, 0, Qt.AlignLeft)

    def bind(self, session) -> None:
        if session.is_complete:
            self.set_edge("solid")
            self.set_band("COMPLETE", "ink")
        else:
            self.set_edge("perforated")
            missing = ", ".join(session.missing_fields())
            self.set_band(f"INCOMPLETE · MISSING {missing.upper()}", "stat")
        self.id_label.setText(session.session_id)
        self.saved.setText(f"Saved {session.saved_at_display} · revision {session.revision}")
        self.values.set("Skin type", session.field_or_dash(session.skin_type))
        self.values.set("Erythema grade", session.field_or_dash(session.erythema_grade))
        self.values.set("Photo", "Attached" if session.has_photo else "—")
        self.thumb.set_path(session.photo_path if session.has_photo else None)
        self.barcode.set_text(session.session_id)


class SessionSavedScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Session saved", step=5)
        self.head.back.setVisible(False)

        row = QHBoxLayout()
        row.setSpacing(GAP + 8)
        self.label = SessionLabel()
        self.feed = PrintFeed(self.label)
        row.addWidget(self.feed, 1)

        side = QVBoxLayout()
        side.setSpacing(GAP)
        confirm = QHBoxLayout()
        confirm.setSpacing(8)
        confirm.addWidget(Icon("check", 26, C.INK, 2.6))
        self.stored = make_label("Stored on this device", "body", QFont.Bold)
        confirm.addWidget(self.stored)
        confirm.addStretch(1)
        side.addLayout(confirm)
        self.detail = make_label("", "small", color=C.INK_ON_LINER, wrap=True)
        side.addWidget(self.detail)
        side.addStretch(1)
        self.next_btn = InkButton("Next patient", "primary", icon="plus",
                                  on_click=controller.start_new_session)
        self.view_btn = InkButton("View past sessions", "secondary", icon="list",
                                  on_click=controller.show_past_sessions)
        self.home_btn = InkButton("Home", "secondary", icon="home", on_click=controller.go_home)
        for w in (self.next_btn, self.view_btn, self.home_btn):
            side.addWidget(w)
        holder = QWidget()
        holder.setLayout(side)
        holder.setFixedWidth(248)
        row.addWidget(holder)
        self.body.addLayout(row, 1)

    def on_enter(self) -> None:
        session = self.controller.last_saved
        if session is None:
            return
        self.head.set_session_id(session.session_id)
        self.label.bind(session)
        if session.is_complete:
            self.detail.setText("Record and photo written to device storage. "
                                "Export to the clinical SSD from Home.")
        else:
            self.detail.setText("Saved as incomplete. Open it from Past sessions "
                                "to finish the assessment.")
        self.feed.play(self.controller.reduced_motion)
