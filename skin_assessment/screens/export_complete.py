"""Export complete."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from ..theme import C
from ..widgets import Icon, InkButton, LabelCard, ValueList, make_label
from .base import Screen


class ExportCompleteScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Export complete", show_back=False)

        card = LabelCard("solid", padding=(22, 14, 22, 12))
        lay = QVBoxLayout(card)
        lay.setSpacing(6)
        head = QHBoxLayout()
        head.setSpacing(12)
        head.addWidget(Icon("check", 34, C.INK, 2.8))
        head.addWidget(make_label("Saved to clinical data SSD", "title", QFont.Bold))
        head.addStretch(1)
        lay.addLayout(head)
        self.values = ValueList()
        self.values.add_row("File", mono=True)
        self.values.add_row("Sessions", mono=True)
        self.values.add_row("Photos", mono=True)
        self.values.add_row("Schema", mono=True)
        self.values.add_row("Finished", mono=True)
        lay.addWidget(self.values)
        self.body.addWidget(card, 1)

        self.done_btn = InkButton("Done", "primary", icon="home", on_click=controller.go_home)
        self.body.addWidget(self.done_btn)

    def on_enter(self) -> None:
        r = self.controller.last_export
        if r is None:
            return
        self.values.set("File", r.file_name)
        self.values.set("Sessions", str(r.written))
        self.values.set("Photos", str(r.photos))
        self.values.set("Schema", f"v{r.schema}")
        self.values.set("Finished", f"{r.finished_at:%H:%M:%S}")
