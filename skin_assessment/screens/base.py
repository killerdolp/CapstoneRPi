"""Shared screen scaffold: running head on the liner + a body area."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..theme import GAP, GUTTER
from ..widgets import RunningHead


class Screen(QWidget):
    def __init__(self, controller, title: str, show_back: bool = True,
                 step: Optional[int] = None, show_camera: bool = True,
                 show_ssd: bool = True) -> None:
        super().__init__()
        self.controller = controller
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.head = RunningHead(title, show_back=show_back, step=step,
                                show_camera=show_camera, show_ssd=show_ssd)
        self.head.back_clicked.connect(self.on_back)
        outer.addWidget(self.head)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(GUTTER, 8, GUTTER, GUTTER)
        self.body.setSpacing(GAP)
        outer.addLayout(self.body, 1)

    # Overridden by screens.
    def on_back(self) -> None:
        self.controller.go_home()

    def on_enter(self) -> None:
        pass

    def on_leave(self) -> None:
        pass

    def refresh_status(self) -> None:
        self.head.status.refresh(self.controller.state, self.controller.camera)
