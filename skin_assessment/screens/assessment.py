"""Skin Type (Figma 03 / 10A) and Erythema Grade (Figma 04 / 10B) screens.

The original single assessment screen is split in two. Each screen keeps the
original save / next behaviour for its own field.
"""

from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ..app_state import ERYTHEMA_GRADES, SKIN_TYPES
from ..theme import px
from ..widgets import FigmaScreen, OptionRow, action_button


class _GradeScreen(FigmaScreen):
    """A prompt, a row of score buttons, and Back / Save / Next."""

    field = ""        # Session attribute this screen edits
    title = ""
    edit_title = ""
    step = ""
    prompt = ""

    def __init__(self, controller, values: Sequence[str]) -> None:
        super().__init__(self.title, step=self.step)
        self.controller = controller

        prompt = QLabel(self.prompt)
        prompt.setObjectName("Prompt")
        prompt.setAlignment(Qt.AlignCenter)
        self.options = OptionRow(values)

        self.content.addStretch(1)
        self.content.addWidget(prompt)
        self.content.addSpacing(px(16))
        self.content.addWidget(self.options)
        self.content.addStretch(1)

        self.back_btn = action_button("Back", "secondary", 160, self._back)
        self.save_btn = action_button("Save", "secondary", 160, self._save_incomplete)
        self.next_btn = action_button("Next", "primary", 184, self._next)
        self.set_footer(left=[self.back_btn], right=[self.save_btn, self.next_btn])

    # ---- state binding ----------------------------------------------------
    def on_enter(self) -> None:
        self.set_title(self.edit_title if self.controller.editing else self.title)
        session = self.controller.draft_session
        if session is None:
            return
        self.options.set_value(getattr(session, self.field))

    def _collect(self) -> None:
        session = self.controller.draft_session
        setattr(session, self.field, self.options.value())

    # ---- actions ----------------------------------------------------------
    def _save_incomplete(self) -> None:
        self._collect()
        self.controller.save_draft(complete=False)
        self.controller.go_home()

    def _back(self) -> None:
        raise NotImplementedError

    def _next(self) -> None:
        raise NotImplementedError


class SkinTypeScreen(_GradeScreen):
    field = "skin_type"
    title = "Skin Type"
    edit_title = "Edit Skin Type"
    step = "Step 1 of 3"
    prompt = "Select the patient\u2019s skin type"

    def __init__(self, controller) -> None:
        super().__init__(controller, SKIN_TYPES)

    def _back(self) -> None:
        self.controller.go_home()

    def _next(self) -> None:
        self._collect()
        self.controller.show_erythema_grade()


class ErythemaGradeScreen(_GradeScreen):
    field = "erythema_grade"
    title = "Erythema Grade"
    edit_title = "Edit Erythema Grade"
    step = "Step 2 of 3"
    prompt = "Select the erythema grade"

    def __init__(self, controller) -> None:
        super().__init__(controller, ERYTHEMA_GRADES)

    def _back(self) -> None:
        # Keep this screen's selection when stepping back to Skin Type.
        self._collect()
        self.controller.show_skin_type()

    def _next(self) -> None:
        self._collect()
        self.controller.show_take_photo()
