"""Home screen (wireframe page 5): Skin Assessment landing with three tiles."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..widgets import make_button


class HomeScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)

        # Top row: title + SSD status banner.
        top = QHBoxLayout()
        title = QLabel("Skin Assessment")
        title.setObjectName("ScreenTitle")
        top.addWidget(title)
        top.addStretch(1)

        self.ssd_banner = QLabel()
        self.ssd_banner.setObjectName("DashedBanner")
        self.ssd_banner.setAlignment(Qt.AlignCenter)
        top.addWidget(self.ssd_banner)
        root.addLayout(top)

        # Three tiles.
        tiles = QHBoxLayout()
        tiles.setSpacing(16)

        self.add_tile = make_button(
            "\u2795\nAdd new session", "tile", self.controller.start_new_session
        )
        self.add_tile.setProperty("accent", "true")

        self.view_tile = make_button(
            "[ list icon ]\nView past sessions",
            "tile",
            self.controller.show_past_sessions,
        )
        self.export_tile = make_button(
            "[ export icon ]\nExport data", "tile", self.controller.show_export
        )

        for tile in (self.add_tile, self.view_tile, self.export_tile):
            tile.setMinimumHeight(260)
            tiles.addWidget(tile, 1)
        root.addLayout(tiles, 1)

        # Footer summary.
        self.summary = QLabel()
        self.summary.setObjectName("HelperText")
        self.summary.setAlignment(Qt.AlignCenter)
        root.addWidget(self.summary)

    def on_enter(self) -> None:
        state = self.controller.state
        status = "connected" if state.ssd_connected else "not connected"
        self.ssd_banner.setText(f"Clinical SSD: {status}")
        self.summary.setText(state.summary_text())
