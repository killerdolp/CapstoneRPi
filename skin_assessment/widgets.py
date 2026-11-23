"""Reusable UI building blocks shared across screens.

``FigmaScreen``, ``action_button``, ``OptionRow``, ``Preview`` and
``InfoCard`` implement the Whyre Figma design. ``Header``, ``OptionButton``,
``ImagePlaceholder`` and ``make_button`` are the original wireframe widgets,
still used by the Export data and Export failed screens.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .theme import FOOTER_H, GAP, HEADER_H, MARGIN, px


# ---------------------------------------------------------------------------
# Whyre design
# ---------------------------------------------------------------------------
def action_button(
    text: str,
    variant: str,
    figma_width: int,
    on_click: Optional[Callable[[], None]] = None,
    figma_height: int = 60,
) -> QPushButton:
    """A footer/action button sized from its Figma width and height.

    variant is "primary" (filled teal) or "secondary" (teal outline).
    """
    btn = QPushButton(text)
    btn.setProperty("variant", variant)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedSize(px(figma_width), px(figma_height))
    if on_click is not None:
        btn.clicked.connect(on_click)
    return btn


class FigmaScreen(QWidget):
    """Header bar (title + optional step), content area and optional footer."""

    def __init__(self, title: str, step: Optional[str] = None, footer: bool = True) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("HeaderBar")
        header.setFixedHeight(HEADER_H)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(MARGIN, 0, MARGIN, 0)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("HeaderTitle")
        hl.addWidget(self.title_label)
        hl.addStretch(1)
        self.step_label = QLabel(step or "")
        self.step_label.setObjectName("StepLabel")
        self.step_label.setVisible(bool(step))
        hl.addWidget(self.step_label)
        outer.addWidget(header)

        content = QFrame()
        content.setObjectName("Content")
        self.content = QVBoxLayout(content)
        self.content.setContentsMargins(MARGIN, px(16), MARGIN, px(16))
        self.content.setSpacing(GAP)
        outer.addWidget(content, 1)

        self.footer: Optional[QHBoxLayout] = None
        if footer:
            bar = QFrame()
            bar.setObjectName("FooterBar")
            bar.setFixedHeight(FOOTER_H)
            self.footer = QHBoxLayout(bar)
            self.footer.setContentsMargins(MARGIN, 0, MARGIN, 0)
            self.footer.setSpacing(GAP)
            outer.addWidget(bar)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_step(self, step: Optional[str]) -> None:
        self.step_label.setText(step or "")
        self.step_label.setVisible(bool(step))

    def set_footer(
        self,
        left: Sequence[QPushButton] = (),
        right: Sequence[QPushButton] = (),
        center: Sequence[QPushButton] = (),
    ) -> None:
        """Place footer buttons: left-aligned, right-aligned, or centred."""
        assert self.footer is not None
        if center:
            self.footer.addStretch(1)
            for b in center:
                self.footer.addWidget(b)
            self.footer.addStretch(1)
            return
        for b in left:
            self.footer.addWidget(b)
        self.footer.addStretch(1)
        for b in right:
            self.footer.addWidget(b)


class OptionRow(QWidget):
    """A centred row of exclusive, checkable score buttons (110x90 in Figma)."""

    def __init__(self, values: Sequence[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(GAP)
        lay.addStretch(1)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons: Dict[str, QPushButton] = {}
        for value in values:
            btn = QPushButton(value)
            btn.setProperty("variant", "option")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(px(110), px(90))
            self.group.addButton(btn)
            self.buttons[value] = btn
            lay.addWidget(btn)
        lay.addStretch(1)

    def value(self) -> Optional[str]:
        for val, btn in self.buttons.items():
            if btn.isChecked():
                return val
        return None

    def set_value(self, value: Optional[str]) -> None:
        # An exclusive group will not uncheck its last button, so lift
        # exclusivity while clearing.
        self.group.setExclusive(False)
        for val, btn in self.buttons.items():
            btn.setChecked(val == value)
        self.group.setExclusive(True)


class Preview(QLabel):
    """Dark box for the camera preview or a photo, with a caption fallback.

    Images are scaled to fit inside the box without cropping, so the whole
    frame the camera will capture stays visible.
    """

    def __init__(self, caption: str, figma_w: int, figma_h: int) -> None:
        super().__init__(caption)
        self.setObjectName("Preview")
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(px(figma_w), px(figma_h))

    def show_caption(self, caption: str) -> None:
        self.clear()
        self.setText(caption)

    def show_image(self, image: QImage) -> None:
        if image.isNull():
            return
        self.setPixmap(QPixmap.fromImage(image.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)))

    def show_file(self, path: Optional[Path], fallback: str) -> None:
        """Show an image file, or the fallback caption if it can't be read."""
        image = QImage(str(path)) if path is not None and path.exists() else QImage()
        if image.isNull():
            self.show_caption(fallback)
        else:
            self.show_image(image)


class InfoCard(QFrame):
    """Bordered card of "Label: value" lines with the value in bold."""

    def __init__(self, figma_w: int, figma_h: int) -> None:
        super().__init__()
        self.setObjectName("InfoCard")
        self.setFixedSize(px(figma_w), px(figma_h))
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(px(17), px(17), px(17), px(17))
        self._lay.setSpacing(px(14))
        self._labels: List[QLabel] = []
        self._lay.addStretch(1)

    def set_lines(self, lines: Sequence[Tuple[str, str]]) -> None:
        for lbl in self._labels:
            self._lay.removeWidget(lbl)
            lbl.setParent(None)
            lbl.deleteLater()
        self._labels = []
        for i, (label, value) in enumerate(lines):
            lbl = QLabel(f"{escape(label)}: <b>{escape(value)}</b>")
            lbl.setObjectName("InfoLine")
            lbl.setTextFormat(Qt.RichText)
            self._lay.insertWidget(i, lbl)
            self._labels.append(lbl)


def session_info_lines(session, show_edited: bool = True) -> List[Tuple[str, str]]:
    """The info-card lines used by Session Saved and Session Details."""
    lines = [
        ("Session ID", session.session_id),
        ("Skin Type", session.field_or_dash(session.skin_type)),
        ("Erythema Grade", session.field_or_dash(session.erythema_grade)),
        ("Saved", session.saved_at_display),
    ]
    if show_edited and session.was_edited:
        lines.append(("Edited", session.updated_at_display))
    lines.append(("Status", "Complete" if session.is_complete else "Incomplete"))
    return lines


# ---------------------------------------------------------------------------
# Original wireframe widgets (Export data / Export failed)
# ---------------------------------------------------------------------------
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
    """Grey box with centered caption and crossing diagonals."""

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
    """Create a wireframe-style QPushButton (outline, primary, tile, chip)."""
    btn = QPushButton(text)
    btn.setProperty("variant", variant)
    btn.setCursor(Qt.PointingHandCursor)
    if on_click is not None:
        btn.clicked.connect(on_click)
    return btn
