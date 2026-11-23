"""Home screen (Figma 01): three stacked primary actions."""

from __future__ import annotations

from PySide6.QtCore import Qt

from ..theme import px
from ..widgets import FigmaScreen, action_button


class HomeScreen(FigmaScreen):
    def __init__(self, controller) -> None:
        super().__init__("Whyre 2D Imaging", footer=False)
        self.controller = controller

        self.add_tile = action_button(
            "New Session", "primary", 480, self.controller.start_new_session, figma_height=90
        )
        self.view_tile = action_button(
            "Past Sessions", "primary", 480, self.controller.show_past_sessions, figma_height=90
        )
        self.export_tile = action_button(
            "Export Data", "primary", 480, self.controller.show_export, figma_height=90
        )
        self.content.setSpacing(px(24))
        self.content.addStretch(1)
        for tile in (self.add_tile, self.view_tile, self.export_tile):
            self.content.addWidget(tile, 0, Qt.AlignHCenter)
        self.content.addStretch(1)

    def on_enter(self) -> None:
        pass
