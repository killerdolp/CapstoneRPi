"""Home: three tall labels on the liner."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout

from ..theme import GAP, C
from ..widgets import HomeTile, make_label
from .base import Screen


class HomeScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Skin Assessment", show_back=False)

        tiles = QHBoxLayout()
        tiles.setSpacing(GAP)
        self.add_tile = HomeTile("New session", "plus", inked=True)
        self.view_tile = HomeTile("Past sessions", "list")
        self.export_tile = HomeTile("Export data", "export")
        self.add_tile.clicked.connect(controller.start_new_session)
        self.view_tile.clicked.connect(controller.show_past_sessions)
        self.export_tile.clicked.connect(controller.show_export)
        for tile in (self.add_tile, self.view_tile, self.export_tile):
            tiles.addWidget(tile, 1)
        self.body.addLayout(tiles, 1)

        self.summary = make_label("", "small", QFont.Medium, color=C.INK_ON_LINER)
        self.summary.setAlignment(Qt.AlignCenter)
        self.body.addWidget(self.summary)

    def on_enter(self) -> None:
        state = self.controller.state
        self.add_tile.set_info([(f"Next ID  {state.next_session_id()}", False)])

        complete = len(state.complete_sessions())
        incomplete = len(state.incomplete_sessions())
        newest = state.newest()
        lines = [(f"{complete} complete", True), (f"{incomplete} incomplete", True)]
        lines.append((f"Last saved {newest.saved_at:%d %b, %H:%M}".replace(" 0", " ") if newest
                      else "No sessions yet", False))
        self.view_tile.set_info(lines, flag=("INCOMPLETE", "stat") if incomplete else None)

        self.export_tile.setEnabled(bool(state.sessions))
        if not state.sessions:
            self.export_tile.set_info([("Nothing to export", True), ("Save a session first", False)])
        elif state.ssd_connected:
            self.export_tile.set_info(
                [("SSD connected", True), ("JSON + photos (zip)", False)],
                line_icon="drive",
            )
        else:
            self.export_tile.set_info(
                [("SSD not connected", True), ("Connect to export", False)],
                flag=("NO SSD", "stat"), line_icon="drive-off",
            )
        free_gb = state.store.free_bytes() / 1e9
        self.summary.setText(f"{state.summary_text()}   ·   {free_gb:.1f} GB free on device")
