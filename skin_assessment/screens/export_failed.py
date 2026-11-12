"""Export failed (SSD disconnected mid-export)."""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from ..theme import GAP, C
from ..widgets import Icon, InkButton, LabelCard, ValueList, make_label
from .base import Screen


class ExportFailedScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Export failed", show_back=False)

        card = LabelCard("perforated", padding=(22, 14, 22, 12))
        self.card = card
        card.set_band("EXPORT INTERRUPTED", "stat")
        lay = QVBoxLayout(card)
        lay.setSpacing(6)
        head = QHBoxLayout()
        head.setSpacing(12)
        head.addWidget(Icon("alert", 34, C.INK, 2.4))
        self.title = make_label("", "title", QFont.Bold, wrap=True)
        head.addWidget(self.title, 1)
        lay.addLayout(head)
        self.values = ValueList()
        self.values.add_row("Written before failure")
        self.values.add_row("SSD status")
        lay.addWidget(self.values)
        self.note = make_label("Sessions on this device are unchanged. Reconnect the SSD and retry; "
                               "the export starts again from the beginning.",
                               "body", color=C.INK_SOFT, wrap=True)
        lay.addWidget(self.note)
        lay.addStretch(1)
        self.body.addWidget(card, 1)

        self.reason = make_label("", "small", QFont.Medium, color=C.INK_ON_LINER)
        self.body.addWidget(self.reason)
        row = QHBoxLayout()
        row.setSpacing(GAP)
        self.back_btn = InkButton("Back to export data", "secondary", icon="back",
                                  on_click=controller.show_export)
        self.retry_btn = InkButton("Retry export", "primary", icon="retake",
                                   on_click=controller.retry_export)
        row.addWidget(self.back_btn, 1)
        row.addWidget(self.retry_btn, 1)
        self.body.addLayout(row)

    def on_enter(self) -> None:
        r = self.controller.last_export
        connected = self.controller.state.ssd_connected
        if r is not None:
            self.title.setText(r.reason or "The export did not finish.")
            self.values.set("Written before failure", f"{r.written} of {r.total}")
        self.values.set("SSD status", "Connected" if connected else "Not connected")
        if r is not None:
            ssd = "SSD CONNECTED" if connected else "SSD NOT CONNECTED"
            self.card.set_band(f"{r.written} OF {r.total} WRITTEN · {ssd}", "stat")
        self.retry_btn.setEnabled(connected)
        self.reason.setText("" if connected else "Retry is unavailable until the SSD is connected.")
