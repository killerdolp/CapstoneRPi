"""Steps 1 and 2 of 5: patient assessment, one field per screen.

Step 1 records the skin type, step 2 the erythema grade. Both write into the
controller's draft, so moving back and forth keeps the selections.
"""

from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from ..app_state import ERYTHEMA_GRADES, SKIN_TYPES
from ..theme import GAP, C
from ..widgets import GradeSelector, InkButton, LabelCard, make_label
from .base import Screen


class _GradeStepScreen(Screen):
    """One assessment field: a prompt, a row of value cells, Save and Next."""

    # Set by subclasses.
    field = ""          # Session attribute this screen edits
    prompt = ""
    hint = ""
    missing_note = ""   # shown while nothing is selected
    next_note = ""      # shown once a value is selected

    def __init__(self, controller, title: str, step: int, values: Sequence[str],
                 next_label: str) -> None:
        super().__init__(controller, title, step=step)

        card = LabelCard("plain", padding=(18, 14, 18, 16))
        lay = QVBoxLayout(card)
        lay.setSpacing(8)
        lay.addStretch(1)
        lay.addWidget(make_label(self.prompt, "body", QFont.Bold), 0, Qt.AlignHCenter)
        lay.addWidget(make_label(self.hint, "small", color=C.INK_SOFT), 0, Qt.AlignHCenter)
        lay.addSpacing(10)
        self.selector = GradeSelector(values)
        lay.addWidget(self.selector)
        lay.addStretch(1)
        self.body.addWidget(card, 1)

        self.note = make_label("", "small", QFont.Medium, color=C.INK_ON_LINER)
        self.body.addWidget(self.note)

        footer = QHBoxLayout()
        footer.setSpacing(GAP)
        self.save_btn = InkButton("Save as incomplete", "secondary", icon="save",
                                  on_click=self._save_incomplete)
        self.next_btn = InkButton(next_label, "primary", icon="next", icon_after=True,
                                  on_click=self._next)
        footer.addWidget(self.save_btn, 1)
        footer.addWidget(self.next_btn, 1)
        self.body.addLayout(footer)

        self.selector.changed.connect(self._on_change)

    # ---- state binding ---------------------------------------------------
    def on_enter(self) -> None:
        draft = self.controller.draft
        if draft is None:
            return
        self.head.set_session_id(draft.session_id)
        self.selector.set_value(getattr(draft, self.field))
        self._on_change()

    def _collect(self) -> None:
        draft = self.controller.draft
        if draft is not None:
            setattr(draft, self.field, self.selector.value())

    def _on_change(self, *_args) -> None:
        ready = self.selector.value() is not None
        self.next_btn.setEnabled(ready)
        draft = self.controller.draft
        if not ready:
            self.note.setText(self.missing_note)
        elif self.controller.editing and draft is not None:
            self.note.setText(f"Editing saved session. Saving creates revision {draft.revision + 1}; "
                              "earlier photos are kept.")
        else:
            self.note.setText(self.next_note)

    # ---- actions ---------------------------------------------------------
    def _save_incomplete(self) -> None:
        self._collect()
        self.controller.save_draft()

    def _next(self) -> None:
        self._collect()
        self._go_next()

    def _go_next(self) -> None:
        raise NotImplementedError


class SkinTypeScreen(_GradeStepScreen):
    field = "skin_type"
    prompt = "Select the patient’s skin type"
    hint = "Fitzpatrick 2–6"
    missing_note = "Select a skin type to continue."
    next_note = "Next, select the erythema grade."

    def __init__(self, controller) -> None:
        super().__init__(controller, "Skin type", step=1, values=SKIN_TYPES,
                         next_label="Next: Erythema grade")

    def on_back(self) -> None:
        self._collect()
        self.controller.leave_flow()

    def _go_next(self) -> None:
        self.controller.show_erythema_grade()


class ErythemaGradeScreen(_GradeStepScreen):
    field = "erythema_grade"
    prompt = "Select the erythema grade"
    hint = "0 to +++"
    missing_note = "Select an erythema grade to continue."
    next_note = "Next, photograph the assessed site."

    def __init__(self, controller) -> None:
        super().__init__(controller, "Erythema grade", step=2, values=ERYTHEMA_GRADES,
                         next_label="Next: Take photo")

    def on_back(self) -> None:
        self._collect()
        self.controller.show_skin_type()

    def _go_next(self) -> None:
        self.controller.show_take_photo()
