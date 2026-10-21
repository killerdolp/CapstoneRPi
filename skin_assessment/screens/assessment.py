"""Patient assessment screen (wireframe page 1): step 1 of the new-session flow."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..app_state import ERYTHEMA_GRADES, SKIN_TYPES
from ..widgets import Header, OptionButton, make_button


class AssessmentScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        self.header = Header("New session")
        self.header.back_clicked.connect(self.controller.go_home)
        root.addWidget(self.header)

        # Session ID banner.
        self.id_banner = QLabel()
        self.id_banner.setObjectName("DashedBanner")
        root.addWidget(self.id_banner)

        section = QLabel("1. Patient assessment")
        section.setObjectName("CardTitle")
        root.addWidget(section)

        # Skin type row.
        root.addWidget(self._field_label("Skin type (2\u20136)"))
        self.skin_group = QButtonGroup(self)
        self.skin_group.setExclusive(True)
        skin_row = QHBoxLayout()
        skin_row.setSpacing(10)
        self.skin_buttons = {}
        for value in SKIN_TYPES:
            btn = OptionButton(value)
            self.skin_group.addButton(btn)
            self.skin_buttons[value] = btn
            skin_row.addWidget(btn)
        root.addLayout(skin_row)

        # Erythema grade row.
        root.addWidget(self._field_label("Erythema grade"))
        self.erythema_group = QButtonGroup(self)
        self.erythema_group.setExclusive(True)
        ery_row = QHBoxLayout()
        ery_row.setSpacing(10)
        self.erythema_buttons = {}
        for value in ERYTHEMA_GRADES:
            btn = OptionButton(value)
            self.erythema_group.addButton(btn)
            self.erythema_buttons[value] = btn
            ery_row.addWidget(btn)
        root.addLayout(ery_row)

        helper = QLabel(
            'Opened from \u201cEdit session\u201d, these fields arrive '
            "pre-filled with the saved values."
        )
        helper.setObjectName("HelperText")
        helper.setWordWrap(True)
        root.addWidget(helper)

        root.addStretch(1)

        # Footer actions.
        footer = QHBoxLayout()
        footer.setSpacing(16)
        self.save_btn = make_button(
            "Save (incomplete)", "outline", self._save_incomplete
        )
        self.next_btn = make_button("Next: take photo \u203a", "primary", self._next)
        footer.addWidget(self.save_btn, 1)
        footer.addWidget(self.next_btn, 1)
        root.addLayout(footer)

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        return lbl

    # ---- state binding ----------------------------------------------------
    def on_enter(self) -> None:
        session = self.controller.draft_session
        if session is None:
            return
        self.id_banner.setText(
            f"Session ID: {session.session_id} (auto-generated)"
        )
        self._set_selection(self.skin_buttons, session.skin_type)
        self._set_selection(self.erythema_buttons, session.erythema_grade)

    def _set_selection(self, buttons: dict, value: Optional[str]) -> None:
        # Allow clearing: temporarily disable exclusivity to uncheck all.
        for val, btn in buttons.items():
            btn.setChecked(val == value)

    def _collect(self) -> None:
        session = self.controller.draft_session
        session.skin_type = self._selected(self.skin_buttons)
        session.erythema_grade = self._selected(self.erythema_buttons)

    def _selected(self, buttons: dict) -> Optional[str]:
        for val, btn in buttons.items():
            if btn.isChecked():
                return val
        return None

    # ---- actions ----------------------------------------------------------
    def _save_incomplete(self) -> None:
        self._collect()
        self.controller.save_draft(complete=False)
        self.controller.go_home()

    def _next(self) -> None:
        self._collect()
        self.controller.show_take_photo()
