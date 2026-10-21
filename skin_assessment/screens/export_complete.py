"""Export complete screen (wireframe page 9)."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..widgets import make_button


class ExportCompleteScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)

        title = QLabel("Export complete")
        title.setObjectName("ScreenTitle")
        root.addWidget(title)

        # Confirmation banner.
        banner = QLabel("[ saved to clinical data SSD ]")
        banner.setObjectName("ImagePlaceholder")
        banner.setAlignment(Qt.AlignCenter)
        banner.setMinimumHeight(70)
        banner.setStyleSheet("font-weight: 700;")
        root.addWidget(banner)

        # Summary card.
        card = QWidget()
        card.setObjectName("Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        self.file_value = self._add_row(grid, 0, "File")
        self.sessions_value = self._add_row(grid, 1, "Sessions")
        self.schema_value = self._add_row(grid, 2, "Schema")
        self.dest_value = self._add_row(grid, 3, "Destination")
        root.addWidget(card)

        root.addStretch(1)

        self.done_btn = make_button("Done", "primary", self.controller.go_home)
        self.done_btn.setMinimumHeight(60)
        root.addWidget(self.done_btn)

    def _add_row(self, grid: QGridLayout, row: int, label: str) -> QLabel:
        grid.addWidget(QLabel(label), row, 0)
        value = QLabel("—")
        value.setObjectName("ValueStrong")
        value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(value, row, 1)
        return value

    def on_enter(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        self.file_value.setText(f"metadata_{today}.json")
        self.sessions_value.setText(str(len(self.controller.state.sessions)))
        self.schema_value.setText("[Schema Version]")
        self.dest_value.setText("Clinical data SSD")
