"""Step 1 of 4: patient assessment (skin type + erythema grade)."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from ..app_state import ERYTHEMA_GRADES, SKIN_TYPES
from ..theme import GAP, C
from ..widgets import GradeSelector, InkButton, LabelCard, make_label
from .base import Screen


class AssessmentScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Assessment", step=1)

        card = LabelCard("plain", padding=(18, 14, 18, 16))
        lay = QVBoxLayout(card)
        lay.setSpacing(8)

        lay.addLayout(self._field_head("Skin type", "Fitzpatrick 2–6"))
        self.skin = GradeSelector(SKIN_TYPES)
        lay.addWidget(self.skin)
        lay.addSpacing(10)
        lay.addLayout(self._field_head("Erythema grade", "0 to +++"))
        self.erythema = GradeSelector(ERYTHEMA_GRADES)
        lay.addWidget(self.erythema)
        lay.addStretch(1)
        self.body.addWidget(card, 1)

        self.note = make_label("", "small", QFont.Medium, color=C.INK_ON_LINER)
        self.body.addWidget(self.note)

        footer = QHBoxLayout()
        footer.setSpacing(GAP)
        self.save_btn = InkButton("Save as incomplete", "secondary", icon="save",
                                  on_click=self._save_incomplete)
        self.next_btn = InkButton("Next: Take photo", "primary", icon="next", icon_after=True,
                                  on_click=self._next)
        footer.addWidget(self.save_btn, 1)
        footer.addWidget(self.next_btn, 1)
        self.body.addLayout(footer)

        self.skin.changed.connect(self._on_change)
        self.erythema.changed.connect(self._on_change)

    def _field_head(self, title: str, hint: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(make_label(title, "body", QFont.Bold))
        row.addWidget(make_label(hint, "small", color=C.INK_SOFT))
        row.addStretch(1)
        return row

    # ---- state binding ---------------------------------------------------
    def on_enter(self) -> None:
        draft = self.controller.draft
        if draft is None:
            return
        self.head.set_session_id(draft.session_id)
        self.skin.set_value(draft.skin_type)
        self.erythema.set_value(draft.erythema_grade)
        self._on_change()

    def _collect(self) -> None:
        draft = self.controller.draft
        draft.skin_type = self.skin.value()
        draft.erythema_grade = self.erythema.value()

    def _on_change(self, *_args) -> None:
        ready = self.skin.value() is not None and self.erythema.value() is not None
        self.next_btn.setEnabled(ready)
        draft = self.controller.draft
        if not ready:
            self.note.setText("Select a skin type and an erythema grade to continue.")
        elif self.controller.editing and draft is not None:
            self.note.setText(f"Editing saved session. Saving creates revision {draft.revision + 1}; "
                              "earlier photos are kept.")
        else:
            self.note.setText("Next, photograph the assessed site.")

    # ---- actions ---------------------------------------------------------
    def on_back(self) -> None:
        self._collect()
        self.controller.leave_flow()

    def _save_incomplete(self) -> None:
        self._collect()
        self.controller.save_draft()

    def _next(self) -> None:
        self._collect()
        self.controller.show_take_photo()
