"""Reusable UI building blocks shared across screens."""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class Header(QWidget):
    """Top bar with an optional '< Back' button and a screen title."""

    back_clicked = Signal()

    def __init__(
        self,
        title: str,
        show_back: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        if show_back:
            self.back_button = QPushButton("\u2039 Back")
            self.back_button.setObjectName("BackButton")
            self.back_button.setCursor(Qt.PointingHandCursor)
            self.back_button.clicked.connect(self.back_clicked.emit)
            layout.addWidget(self.back_button)
        else:
            self.back_button = None

        self.title_label = QLabel(title)
        self.title_label.setObjectName("ScreenTitle")
        layout.addWidget(self.title_label)
        layout.addStretch(1)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)


class OptionButton(QPushButton):
    """A checkable toggle button used for skin type / erythema selection."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("OptionButton")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(56)


class ImagePlaceholder(QLabel):
    """Grey box with centered caption and an 'X' drawn via border styling.

    Mimics the crossed-box placeholders from the wireframe. The crossing
    diagonals are drawn in paintEvent.
    """

    def __init__(
        self,
        caption: str = "",
        draw_cross: bool = True,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(caption, parent)
        self.setObjectName("ImagePlaceholder")
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._draw_cross = draw_cross

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().paintEvent(event)
        if not self._draw_cross:
            return
        from PySide6.QtGui import QColor, QPainter, QPen

        painter = QPainter(self)
        pen = QPen(QColor("#9a9a9a"))
        pen.setWidth(1)
        painter.setPen(pen)
        w = self.width()
        h = self.height()
        painter.drawLine(0, 0, w, h)
        painter.drawLine(w, 0, 0, h)
        painter.end()


def make_button(
    text: str,
    variant: str,
    on_click: Optional[Callable[[], None]] = None,
) -> QPushButton:
    """Create a QPushButton with a style 'variant' property.

    variant is one of: outline, primary, tile, chip.
    """
    btn = QPushButton(text)
    btn.setProperty("variant", variant)
    btn.setCursor(Qt.PointingHandCursor)
    if on_click is not None:
        btn.clicked.connect(on_click)
    return btn
