"""Export failed screen (wireframe page 11)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..widgets import make_button


class ExportFailedScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)

        title = QLabel("Export failed")
        title.setObjectName("ScreenTitle")
        root.addWidget(title)

        banner = QLabel("[ export interrupted \u2014 SSD not connected ]")
        banner.setObjectName("ImagePlaceholder")
        banner.setAlignment(Qt.AlignCenter)
        banner.setMinimumHeight(70)
        banner.setStyleSheet("font-weight: 700;")
        root.addWidget(banner)

        # Details card.
        card = QWidget()
        card.setObjectName("Card")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)
        self._add_row(grid, 0, "Export status", "Failed during export")
        self._add_row(grid, 1, "Export time", "Interrupted")
        self._add_row(grid, 2, "Destination", "Clinical data SSD")
        self._add_row(grid, 3, "SSD status", "Not connected")
        root.addWidget(card)

        helper = QLabel(
            "Export did not complete. Connect an SSD, then retry the export."
        )
        helper.setObjectName("HelperText")
        helper.setWordWrap(True)
        root.addWidget(helper)

        root.addStretch(1)

        self.back_btn = make_button(
            "\u2039 Back to export data", "outline", self.controller.show_export
        )
        self.back_btn.setMinimumHeight(54)
        root.addWidget(self.back_btn)

        self.retry_btn = make_button("Retry export to SSD", "primary")
        self.retry_btn.setMinimumHeight(60)
        self.retry_btn.setEnabled(False)
        self.retry_btn.setText(
            "Retry export to SSD\nUnavailable until an SSD is connected"
        )
        root.addWidget(self.retry_btn)

    def _add_row(self, grid: QGridLayout, row: int, label: str, value: str) -> None:
        grid.addWidget(QLabel(label), row, 0)
        val = QLabel(value)
        val.setObjectName("ValueStrong")
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(val, row, 1)

    def on_enter(self) -> None:
        pass
