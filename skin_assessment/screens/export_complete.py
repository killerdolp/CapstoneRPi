"""Export Complete screen (Figma 12)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from ..theme import px
from ..widgets import FigmaScreen, action_button


class ExportCompleteScreen(FigmaScreen):
    def __init__(self, controller) -> None:
        super().__init__("Export Complete")
        self.controller = controller

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedSize(px(760), px(340))
        lay = QVBoxLayout(card)
        lay.setContentsMargins(px(32), px(40), px(32), px(40))
        lay.setSpacing(px(16))

        title = QLabel("Saved to Clinical Data SSD")
        title.setObjectName("Prompt")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        lay.addWidget(divider)

        grid = QGridLayout()
        grid.setHorizontalSpacing(px(10))
        grid.setVerticalSpacing(px(16))
        self.file_value = self._add_row(grid, 0, "File")
        self.sessions_value = self._add_row(grid, 1, "Sessions")
        self.schema_value = self._add_row(grid, 2, "Schema")
        self.dest_value = self._add_row(grid, 3, "Destination")
        grid.setColumnMinimumWidth(0, px(169))
        grid.setColumnMinimumWidth(1, px(254))
        lay.addLayout(grid)
        lay.setAlignment(grid, Qt.AlignHCenter)
        lay.addStretch(1)

        self.content.addStretch(1)
        self.content.addWidget(card, 0, Qt.AlignHCenter)
        self.content.addStretch(1)

        self.done_btn = action_button("Done", "primary", 220, self.controller.go_home)
        self.set_footer(center=[self.done_btn])

    def _add_row(self, grid: QGridLayout, row: int, label: str) -> QLabel:
        name = QLabel(label)
        name.setObjectName("DetailLabel")
        name.setAlignment(Qt.AlignCenter)
        grid.addWidget(name, row, 0)
        value = QLabel("—")
        value.setObjectName("DetailValue")
        value.setAlignment(Qt.AlignCenter)
        grid.addWidget(value, row, 1)
        return value

    def on_enter(self) -> None:
        result = self.controller.last_export
        if result is None:
            return
        self.file_value.setText(result.file_name)
        self.sessions_value.setText(str(result.written))
        self.schema_value.setText(result.schema)
        self.dest_value.setText("Clinical Data SSD")
