"""Export data screen (wireframe pages 8 & 10).

Renders the connected state (page 8) or the not-connected state (page 10)
depending on AppState.ssd_connected.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..widgets import Header, make_button


class ExportDataScreen(QWidget):
    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        self.header = Header("Export data")
        self.header.back_clicked.connect(self.controller.go_home)
        root.addWidget(self.header)

        columns = QHBoxLayout()
        columns.setSpacing(16)

        # ---- Left column: Data to export + Output ----
        left = QVBoxLayout()
        left.setSpacing(12)

        data_card = QWidget()
        data_card.setObjectName("Card")
        data_layout = QVBoxLayout(data_card)
        data_layout.setContentsMargins(16, 12, 16, 12)
        data_layout.setSpacing(8)
        title = QLabel("Data to export")
        title.setObjectName("CardTitle")
        data_layout.addWidget(title)

        self.complete_cb = QCheckBox()
        self.incomplete_cb = QCheckBox()
        self.photos_cb = QCheckBox("Include photos")
        self.complete_cb.setChecked(True)
        self.photos_cb.setChecked(True)
        data_layout.addWidget(self.complete_cb)
        data_layout.addWidget(self.incomplete_cb)
        data_layout.addWidget(self.photos_cb)
        left.addWidget(data_card)

        output_card = QWidget()
        output_card.setObjectName("Card")
        out_grid = QGridLayout(output_card)
        out_grid.setContentsMargins(16, 12, 16, 12)
        out_grid.setHorizontalSpacing(16)
        out_grid.setVerticalSpacing(8)
        out_title = QLabel("Output")
        out_title.setObjectName("CardTitle")
        out_grid.addWidget(out_title, 0, 0, 1, 2)
        out_grid.addWidget(QLabel("Format"), 1, 0)
        fmt = QLabel("JSON, zip")
        fmt.setObjectName("ValueStrong")
        fmt.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        out_grid.addWidget(fmt, 1, 1)
        out_grid.addWidget(QLabel("Schema"), 2, 0)
        schema = QLabel("[Schema Version]")
        schema.setObjectName("ValueStrong")
        schema.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        out_grid.addWidget(schema, 2, 1)
        left.addWidget(output_card)
        left.addStretch(1)
        columns.addLayout(left, 1)

        # ---- Right column: Destination + optional warning ----
        right = QVBoxLayout()
        right.setSpacing(12)

        self.dest_card = QWidget()
        self.dest_card.setObjectName("DashedCard")
        dest_layout = QVBoxLayout(self.dest_card)
        dest_layout.setContentsMargins(16, 12, 16, 12)
        dest_layout.setSpacing(6)
        dest_title = QLabel("Destination")
        dest_title.setObjectName("CardTitle")
        dest_layout.addWidget(dest_title)
        dest_layout.addWidget(QLabel("Clinical data SSD"))
        self.dest_status = QLabel()
        dest_layout.addWidget(self.dest_status)
        right.addWidget(self.dest_card)

        # Warning card (shown only when not connected).
        self.warning_card = QWidget()
        self.warning_card.setObjectName("WarningCard")
        warn_layout = QVBoxLayout(self.warning_card)
        warn_layout.setContentsMargins(16, 12, 16, 12)
        warn_layout.setSpacing(4)
        warn_title = QLabel("SSD not connected")
        warn_title.setObjectName("CardTitle")
        warn_layout.addWidget(warn_title)
        warn_layout.addWidget(QLabel("Connect an SSD to continue."))
        right.addWidget(self.warning_card)

        right.addStretch(1)
        columns.addLayout(right, 1)

        root.addLayout(columns, 1)

        # ---- Footer: Export button ----
        self.export_btn = make_button("Export to SSD", "primary", self._export)
        self.export_btn.setMinimumHeight(60)
        root.addWidget(self.export_btn)

    def on_enter(self) -> None:
        connected = self.controller.state.ssd_connected
        self.incomplete_cb.setText(
            f"Incomplete sessions ({len(self.controller.state.incomplete_sessions())})"
        )
        self.complete_cb.setText(
            f"Complete sessions ({len(self.controller.state.complete_sessions())})"
        )

        status = "connected" if connected else "not connected"
        self.dest_status.setText(f"Status: {status}")
        self.warning_card.setVisible(not connected)

        self.export_btn.setEnabled(connected)
        if connected:
            self.export_btn.setText("Export to SSD")
        else:
            self.export_btn.setText(
                "Export to SSD\nUnavailable until an SSD is connected"
            )

    def _export(self) -> None:
        if not self.controller.state.ssd_connected:
            return
        self.controller.show_export_complete()
