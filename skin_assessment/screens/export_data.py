"""Export data: choose what to export, check the destination, export."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ..app_state import SCHEMA_VERSION
from ..export import ExportRequest
from ..theme import GAP, C, font, q
from ..widgets import (
    CheckRow,
    Icon,
    InkButton,
    LabelCard,
    StatusFlag,
    ValueList,
    make_label,
    paint_label,
)
from .base import Screen


class ProgressStrip(QWidget):
    """Export progress printed as a label filling with ink, record by record."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(60)
        self._done, self._total = 0, 0

    def set_progress(self, done: int, total: int) -> None:
        self._done, self._total = done, total
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        rect = QRectF(self.rect())
        paint_label(p, rect, "solid")
        frac = (self._done / self._total) if self._total else 0.0
        fill = rect.adjusted(3, 3, -3, -4)
        fill.setWidth(fill.width() * frac)
        p.setPen(Qt.NoPen)
        p.setBrush(q(C.INK))
        p.drawRoundedRect(fill, 7, 7)
        text = f"Writing {self._done} of {self._total} sessions…"
        p.setFont(font("body", QFont.Bold))
        # Draw text twice, clipped, so it stays legible over ink and stock.
        for clip, color in ((QRectF(fill), C.LABEL), (QRectF(fill.right(), 0, rect.width(), rect.height()), C.INK)):
            p.save()
            p.setClipRect(clip)
            p.setPen(q(color))
            p.drawText(rect, Qt.AlignCenter, text)
            p.restore()


class ExportDataScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Export data")

        cols = QHBoxLayout()
        cols.setSpacing(GAP)

        # ---- left: what to export --------------------------------------
        data = LabelCard("plain", padding=(16, 12, 16, 10))
        dl = QVBoxLayout(data)
        dl.setSpacing(2)
        dl.addWidget(make_label("Data to export", "body", QFont.Bold))
        self.complete_cb = CheckRow("Complete sessions")
        self.incomplete_cb = CheckRow("Incomplete sessions")
        self.photos_cb = CheckRow("Include photos")
        self.complete_cb.setChecked(True)
        self.photos_cb.setChecked(True)
        for cb in (self.complete_cb, self.incomplete_cb, self.photos_cb):
            cb.toggled.connect(self._update_ready)
            dl.addWidget(cb)
        dl.addSpacing(6)
        self.output = ValueList()
        self.output.add_row("Format", "JSON + ZIP")
        self.output.add_row("Schema", f"v{SCHEMA_VERSION}", mono=True)
        dl.addWidget(self.output)
        dl.addStretch(1)
        cols.addWidget(data, 1)

        # ---- right: destination ----------------------------------------
        self.dest = LabelCard("solid", padding=(16, 12, 16, 14))
        rl = QVBoxLayout(self.dest)
        rl.setSpacing(8)
        rl.addWidget(make_label("Destination", "body", QFont.Bold))
        head = QHBoxLayout()
        head.setSpacing(10)
        self.dest_icon = Icon("drive", 40, C.INK, 2)
        head.addWidget(self.dest_icon)
        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        name_col.addWidget(make_label("Clinical data SSD", "title", QFont.Bold))
        self.dest_status = make_label("", "body", QFont.Medium, color=C.INK_SOFT)
        name_col.addWidget(self.dest_status)
        head.addLayout(name_col)
        head.addStretch(1)
        rl.addLayout(head)
        self.dest_flag = StatusFlag("NOT CONNECTED", "stat")
        rl.addWidget(self.dest_flag, 0, Qt.AlignLeft)
        self.dest_help = make_label("", "body", color=C.INK, wrap=True)
        rl.addWidget(self.dest_help)
        rl.addStretch(1)
        cols.addWidget(self.dest, 1)

        self.body.addLayout(cols, 1)

        self.reason = make_label("", "small", QFont.Medium, color=C.INK_ON_LINER)
        self.body.addWidget(self.reason)
        self.export_btn = InkButton("Export to SSD", "primary", icon="export", on_click=self._export)
        self.body.addWidget(self.export_btn)
        self.progress = ProgressStrip()
        self.progress.setVisible(False)
        self.body.addWidget(self.progress)

        ex = controller.exporter
        ex.progress.connect(self._on_progress)
        ex.finished.connect(self._on_finished)

    # ---- state -----------------------------------------------------------
    def on_enter(self) -> None:
        state = self.controller.state
        self.complete_cb.set_detail(str(len(state.complete_sessions())))
        self.incomplete_cb.set_detail(str(len(state.incomplete_sessions())))
        connected = state.ssd_connected
        self.dest.set_edge("solid" if connected else "perforated", hatch=not connected)
        self.dest_icon.set("drive" if connected else "drive-off")
        self.dest_status.setText("Connected" if connected else "Not connected")
        self.dest_flag.setVisible(not connected)
        self.dest_help.setText("Ready to receive the export." if connected
                               else "Connect the clinical data SSD to continue.")
        running = self.controller.exporter.running
        self.export_btn.setVisible(not running)
        self.progress.setVisible(running)
        self.head.back.setEnabled(not running)
        self._update_ready()

    def _request(self) -> ExportRequest:
        return ExportRequest(self.complete_cb.isChecked(), self.incomplete_cb.isChecked(),
                             self.photos_cb.isChecked())

    def _update_ready(self, *_args) -> None:
        state = self.controller.state
        count = len(self._request().select(state))
        if not state.ssd_connected:
            ok, why = False, "Export is unavailable until an SSD is connected."
        elif count == 0:
            ok, why = False, "Nothing selected to export. Choose a group that has sessions."
        else:
            ok, why = True, f"{count} session{'s' if count != 1 else ''} will be exported."
        self.export_btn.setEnabled(ok)
        self.reason.setText(why)

    # ---- export ----------------------------------------------------------
    def _export(self) -> None:
        if not self.controller.state.ssd_connected:
            return
        self.controller.last_export_request = self._request()
        self.export_btn.setVisible(False)
        self.progress.setVisible(True)
        self.head.back.setEnabled(False)
        for cb in (self.complete_cb, self.incomplete_cb, self.photos_cb):
            cb.setEnabled(False)
        self.controller.exporter.start(self.controller.last_export_request)

    def _on_progress(self, done: int, total: int) -> None:
        self.progress.set_progress(done, total)
        self.reason.setText("Keep the SSD connected until the export finishes.")

    def _on_finished(self, result) -> None:
        for cb in (self.complete_cb, self.incomplete_cb, self.photos_cb):
            cb.setEnabled(True)
        self.progress.setVisible(False)
        self.export_btn.setVisible(True)
        self.head.back.setEnabled(True)
        self.controller.export_finished(result)
