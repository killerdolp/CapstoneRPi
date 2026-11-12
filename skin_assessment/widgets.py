"""Specimen Label component set.

All surfaces are painted so the label grammar (die-cut stock, perforation,
hatching, thermal ink) holds exactly, instead of approximating it with QSS.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import barcode, icons
from .theme import (
    GAP,
    GUTTER,
    HEAD_HEIGHT,
    RADIUS,
    TOUCH_MIN,
    TOUCH_PRIMARY,
    C,
    font,
    q,
)

KBD_REASONS = (Qt.TabFocusReason, Qt.BacktabFocusReason, Qt.ShortcutFocusReason)


# ---------------------------------------------------------------------------
# Painting primitives
# ---------------------------------------------------------------------------
def die_cut_path(rect: QRectF, radius: float = RADIUS) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def paint_hatch(p: QPainter, path: QPainterPath, color: str = C.HATCH, spacing: int = 9) -> None:
    p.save()
    p.setClipPath(path, Qt.IntersectClip)
    pen = QPen(q(color), 1.4)
    p.setPen(pen)
    r = path.boundingRect()
    x = r.left() - r.height()
    while x < r.right():
        p.drawLine(QPointF(x, r.bottom()), QPointF(x + r.height(), r.top()))
        x += spacing
    p.restore()


def paint_label(
    p: QPainter,
    rect: QRectF,
    edge: str = "plain",
    fill: Optional[str] = None,
    hatch: bool = False,
    radius: float = RADIUS,
) -> QPainterPath:
    """Paint label stock on the liner.

    edge: plain | solid | perforated | ink | stat
    """
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(rect).adjusted(1, 1, -1, -2)
    # Stock thickness: a 1px liner-side line under the bottom edge.
    if edge != "ink":
        p.setPen(Qt.NoPen)
        p.setBrush(q(C.LINER_EDGE))
        p.drawPath(die_cut_path(r.translated(0, 1.5), radius))

    path = die_cut_path(r, radius)
    p.setPen(Qt.NoPen)
    p.setBrush(q(fill or (C.INK if edge == "ink" else C.LABEL)))
    p.drawPath(path)
    if hatch:
        paint_hatch(p, path)

    if edge == "plain":
        p.setPen(QPen(q(C.LABEL_EDGE), 1))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
    elif edge in ("solid", "stat"):
        inset = die_cut_path(r.adjusted(1, 1, -1, -1), radius - 1)
        p.setPen(QPen(q(C.INK), 2))
        p.setBrush(Qt.NoBrush)
        p.drawPath(inset)
    elif edge == "perforated":
        inset = die_cut_path(r.adjusted(1, 1, -1, -1), radius - 1)
        pen = QPen(q(C.INK), 2)
        pen.setDashPattern([3.2, 2.4])
        pen.setCapStyle(Qt.FlatCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawPath(inset)
    return path


def elide(text: str, f: QFont, width: int) -> str:
    return QFontMetrics(f).elidedText(text, Qt.ElideRight, max(0, width))


def make_label(text: str = "", size: str = "body", weight=QFont.Normal, mono: bool = False,
               color: str = C.INK, wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(font(size, weight, mono))
    lbl.setStyleSheet(f"color: {color};")
    lbl.setWordWrap(wrap)
    return lbl


def set_label_color(lbl: QLabel, color: str) -> None:
    lbl.setStyleSheet(f"color: {color};")


# ---------------------------------------------------------------------------
# Label surfaces
# ---------------------------------------------------------------------------
class LabelCard(QWidget):
    """A die-cut label that hosts child widgets."""

    def __init__(self, edge: str = "plain", padding: Tuple[int, int, int, int] = (16, 14, 16, 14),
                 hatch: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._edge = edge
        self._hatch = hatch
        self._band: Optional[Tuple[str, str]] = None  # (text, kind)
        self._padding = padding
        self.setContentsMargins(*padding)

    def set_edge(self, edge: str, hatch: Optional[bool] = None) -> None:
        self._edge = edge
        if hatch is not None:
            self._hatch = hatch
        self.update()

    def set_band(self, text: Optional[str], kind: str = "ink") -> None:
        """A printed band across the top of the label (status header)."""
        self._band = (text, kind) if text else None
        top = self._padding[1] + (34 if self._band else 0)
        self.setContentsMargins(self._padding[0], top, self._padding[2], self._padding[3])
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        path = paint_label(p, QRectF(self.rect()), self._edge, hatch=self._hatch)
        if self._band:
            text, kind = self._band
            p.save()
            p.setClipPath(path)
            band = QRectF(0, 0, self.width(), 30)
            p.fillRect(band, q(C.STAT if kind == "stat" else C.INK))
            p.setPen(q(C.INK if kind == "stat" else C.LABEL))
            f = font("small", QFont.Bold, mono=True)
            f.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)
            p.setFont(f)
            p.drawText(band.adjusted(16, 1, -16, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
            p.restore()
            if self._edge in ("solid", "stat", "perforated"):
                # Redraw the edge over the band so the die-cut stays legible.
                p.setRenderHint(QPainter.Antialiasing)
                r = QRectF(self.rect()).adjusted(2, 2, -2, -3)
                pen = QPen(q(C.INK), 2)
                if self._edge == "perforated":
                    pen.setDashPattern([3.2, 2.4])
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
                p.drawPath(die_cut_path(r, RADIUS - 1))


class StatusFlag(QWidget):
    """Small printed flag: COMPLETE (ink), INCOMPLETE / DEMO DATA (STAT)."""

    def __init__(self, text: str = "", kind: str = "ink", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._text = text
        self._kind = kind
        self._font = font("small", QFont.Bold, mono=True)
        self._font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumSize(self.sizeHint())

    def set(self, text: str, kind: str) -> None:
        self._text, self._kind = text, kind
        self.setMinimumSize(self.sizeHint())
        self.updateGeometry()
        self.update()

    def set_for_session(self, session) -> None:
        if session.is_complete:
            self.set("COMPLETE", "ink")
        else:
            self.set("INCOMPLETE", "stat")

    def sizeHint(self) -> QSize:  # noqa: N802
        w = QFontMetrics(self._font).horizontalAdvance(self._text) + 20
        return QSize(w, 26)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._kind == "ink":
            p.setBrush(q(C.INK))
            p.setPen(Qt.NoPen)
            fg = C.LABEL
        elif self._kind == "stat":
            p.setBrush(q(C.STAT))
            p.setPen(Qt.NoPen)
            fg = C.INK
        else:  # outline
            p.setBrush(q(C.LABEL))
            p.setPen(QPen(q(C.INK), 1.5))
            fg = C.INK
        p.drawRoundedRect(r, 4, 4)
        p.setPen(q(fg))
        p.setFont(self._font)
        p.drawText(self.rect(), Qt.AlignCenter, self._text)


class Icon(QWidget):
    def __init__(self, name: str, size: int = 24, color: str = C.INK, stroke: float = 2.0,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._name, self._color, self._stroke = name, color, stroke
        self.setFixedSize(size, size)

    def set(self, name: Optional[str] = None, color: Optional[str] = None) -> None:
        if name:
            self._name = name
        if color:
            self._color = color
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        icons.paint(p, self._name, QRectF(self.rect()), self._color, self._stroke)


class Barcode(QWidget):
    """Code 128 barcode of ``text`` with the human-readable line beneath."""

    def __init__(self, text: str = "", bar_height: int = 40, show_text: bool = True,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._text = text
        self._bar_h = bar_height
        self._show_text = show_text
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_text(self, text: str) -> None:
        self._text = text
        self.updateGeometry()
        self.update()

    def _module(self) -> int:
        return 2

    def sizeHint(self) -> QSize:  # noqa: N802
        if not self._text:
            return QSize(0, 0)
        w = barcode.total_modules(self._text) * self._module()
        return QSize(w, self._bar_h + (20 if self._show_text else 0))

    def paintEvent(self, _event) -> None:  # noqa: N802
        if not self._text:
            return
        p = QPainter(self)
        m = self._module()
        x = barcode.QUIET * m
        bar = True
        for width in barcode.encode(self._text):
            if bar:
                p.fillRect(QRect(x, 0, width * m, self._bar_h), q(C.INK))
            x += width * m
            bar = not bar
        if self._show_text:
            f = font("small", QFont.Medium, mono=True)
            f.setLetterSpacing(QFont.AbsoluteSpacing, 2)
            p.setFont(f)
            p.setPen(q(C.INK))
            p.drawText(QRect(0, self._bar_h + 2, self.width(), 18), Qt.AlignHCenter | Qt.AlignTop, self._text)


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------
class _TouchButton(QAbstractButton):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.TabFocus)
        self.setCursor(Qt.PointingHandCursor)
        self._kbd_focus = False

    def focusInEvent(self, event) -> None:  # noqa: N802
        self._kbd_focus = event.reason() in KBD_REASONS
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        self._kbd_focus = False
        super().focusOutEvent(event)

    def _paint_focus(self, p: QPainter, radius: float = RADIUS) -> None:
        if self.hasFocus() and self._kbd_focus:
            pen = QPen(q(C.INK), 2)
            pen.setDashPattern([1, 2])
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(3, 3, -3, -4), radius - 3, radius - 3)


class InkButton(_TouchButton):
    """Action button.

    variant: primary (inked label) | secondary (outlined label)
    Disabled renders as hatched, perforated stock: visibly unavailable.
    """

    def __init__(self, text: str, variant: str = "secondary", icon: Optional[str] = None,
                 icon_after: bool = False, on_click: Optional[Callable[[], None]] = None,
                 size: str = "body", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self._variant = variant
        self._icon = icon
        self._icon_after = icon_after
        self._size = size
        self.setMinimumHeight(TOUCH_PRIMARY if variant == "primary" else TOUCH_MIN + 8)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if on_click is not None:
            self.clicked.connect(on_click)

    def set_icon(self, name: Optional[str]) -> None:
        self._icon = name
        self.update()

    def _font(self) -> QFont:
        return font(self._size, QFont.Bold)

    def sizeHint(self) -> QSize:  # noqa: N802
        fm = QFontMetrics(self._font())
        w = fm.horizontalAdvance(self.text()) + 48 + (32 if self._icon else 0)
        return QSize(w, self.minimumHeight())

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        enabled = self.isEnabled()
        down = self.isDown()
        rect = QRectF(self.rect())
        if not enabled:
            paint_label(p, rect, "perforated", hatch=True)
            fg = C.DISABLED
        elif self._variant == "primary":
            paint_label(p, rect, "ink", fill=C.INK_PRESSED if down else C.INK)
            fg = C.LABEL
        else:
            paint_label(p, rect, "solid", fill=C.PRESSED if down else C.LABEL)
            fg = C.INK

        f = self._font()
        fm = QFontMetrics(f)
        text = self.text()
        icon_size = 28 if self._size == "title" else 24
        gap = 10
        text_w = fm.horizontalAdvance(text)
        total = text_w + ((icon_size + gap) if self._icon else 0)
        x = (self.width() - total) / 2
        cy = self.height() / 2
        if self._icon and not self._icon_after:
            icons.paint(p, self._icon, QRectF(x, cy - icon_size / 2, icon_size, icon_size), fg, 2.2)
            x += icon_size + gap
        p.setFont(f)
        p.setPen(q(fg))
        p.drawText(QRectF(x, 0, text_w + 2, self.height()), Qt.AlignVCenter | Qt.AlignLeft, text)
        if self._icon and self._icon_after:
            icons.paint(p, self._icon, QRectF(x + text_w + gap, cy - icon_size / 2, icon_size, icon_size), fg, 2.2)
        self._paint_focus(p)


class HomeTile(_TouchButton):
    """Tall label on the Home screen: icon, title, and a printed info line."""

    def __init__(self, title: str, icon: str, inked: bool = False,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._inked = inked
        self._lines: List[Tuple[str, bool]] = []  # (text, emphasised)
        self._flag: Optional[Tuple[str, str]] = None
        self._line_icon: Optional[str] = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(220)

    def set_info(self, lines: Sequence[Tuple[str, bool]], flag: Optional[Tuple[str, str]] = None,
                 line_icon: Optional[str] = None) -> None:
        self._lines = list(lines)
        self._flag = flag
        self._line_icon = line_icon
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        down = self.isDown()
        rect = QRectF(self.rect())
        if not self.isEnabled():
            paint_label(p, rect, "perforated", hatch=True)
            fg, soft = C.DISABLED, C.DISABLED
        elif self._inked:
            paint_label(p, rect, "ink", fill=C.INK_PRESSED if down else C.INK)
            fg, soft = C.LABEL, "#C9CDD1"
        else:
            paint_label(p, rect, "solid", fill=C.PRESSED if down else C.LABEL)
            fg, soft = C.INK, C.INK_SOFT

        pad = 20
        # Icon block, top-left.
        icons.paint(p, self._icon, QRectF(pad, pad, 44, 44), fg, 2.2)

        # Flag, top-right.
        if self._flag:
            text, kind = self._flag
            ff = font("small", QFont.Bold, mono=True)
            ff.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
            fw = QFontMetrics(ff).horizontalAdvance(text) + 20
            fr = QRectF(self.width() - pad - fw, pad + 9, fw, 26)
            p.setPen(Qt.NoPen)
            p.setBrush(q(C.STAT if kind == "stat" else (C.LABEL if self._inked else C.INK)))
            p.drawRoundedRect(fr, 4, 4)
            p.setFont(ff)
            p.setPen(q(C.INK if kind == "stat" or self._inked else C.LABEL))
            p.drawText(fr, Qt.AlignCenter, text)

        # Title and lines anchored to the bottom.
        tf = font("title", QFont.Bold)
        lf = font("body", QFont.Normal)
        lfb = font("body", QFont.Bold)
        line_h = 24
        y = self.height() - pad - line_h * len(self._lines)
        title_y = y - 12 - 30
        # Rule between title and info, like a label's printed divider.
        p.setFont(tf)
        p.setPen(q(fg))
        p.drawText(QRectF(pad, title_y, self.width() - 2 * pad, 30), Qt.AlignLeft | Qt.AlignVCenter, self._title)
        if self._lines:
            pen = QPen(q(fg), 1)
            pen.setDashPattern([1, 3])
            p.setPen(pen)
            p.drawLine(QPointF(pad, y - 6), QPointF(self.width() - pad, y - 6))
        for i, (text, strong) in enumerate(self._lines):
            ly = y + i * line_h
            x = pad
            if i == 0 and self._line_icon:
                icons.paint(p, self._line_icon, QRectF(x, ly + 2, 20, 20), fg, 2)
                x += 26
            f = lfb if strong else lf
            p.setFont(f)
            p.setPen(q(fg if strong else soft))
            p.drawText(QRectF(x, ly, self.width() - x - pad, line_h), Qt.AlignLeft | Qt.AlignVCenter,
                       elide(text, f, int(self.width() - x - pad)))
        self._paint_focus(p)


class BackTab(_TouchButton):
    """'Back' control in the running head: a small label tab."""

    def __init__(self, text: str = "Back", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setFixedHeight(TOUCH_MIN)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(QFontMetrics(font("body", QFont.Bold)).horizontalAdvance(self.text()) + 54, TOUCH_MIN)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        paint_label(p, QRectF(self.rect()), "solid", fill=C.PRESSED if self.isDown() else C.LABEL, radius=8)
        icons.paint(p, "back", QRectF(10, (self.height() - 22) / 2, 22, 22), C.INK, 2.4)
        p.setFont(font("body", QFont.Bold))
        p.setPen(q(C.INK))
        p.drawText(QRectF(34, 0, self.width() - 40, self.height()), Qt.AlignVCenter | Qt.AlignLeft, self.text())
        self._paint_focus(p, 8)


# ---------------------------------------------------------------------------
# Selection controls
# ---------------------------------------------------------------------------
class GradeSelector(QWidget):
    """A row of exclusive value cells. The chosen cell fills its whole slot
    in ink; the others stay as inset outlines."""

    changed = Signal(object)  # value or None

    def __init__(self, values: Sequence[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._values = list(values)
        self._value: Optional[str] = None
        self._pressed: Optional[int] = None
        self.setMinimumHeight(76)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.TabFocus)
        self._kbd = False

    def value(self) -> Optional[str]:
        return self._value

    def set_value(self, value: Optional[str], emit: bool = False) -> None:
        self._value = value if value in self._values else None
        self.update()
        if emit:
            self.changed.emit(self._value)

    def _cells(self) -> List[QRectF]:
        n = len(self._values)
        gap = 10
        w = (self.width() - gap * (n - 1)) / n
        return [QRectF(i * (w + gap), 0, w, self.height()) for i in range(n)]

    def _hit(self, pos) -> Optional[int]:
        for i, r in enumerate(self._cells()):
            if r.contains(QPointF(pos)):
                return i
        return None

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self._pressed = self._hit(e.position())
        self.update()

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        hit = self._hit(e.position())
        if hit is not None and hit == self._pressed:
            self.set_value(self._values[hit], emit=True)
        self._pressed = None
        self.update()

    def focusInEvent(self, e) -> None:  # noqa: N802
        self._kbd = e.reason() in KBD_REASONS
        super().focusInEvent(e)

    def keyPressEvent(self, e) -> None:  # noqa: N802
        idx = self._values.index(self._value) if self._value in self._values else -1
        if e.key() in (Qt.Key_Right, Qt.Key_Down):
            self.set_value(self._values[min(len(self._values) - 1, idx + 1)], emit=True)
        elif e.key() in (Qt.Key_Left, Qt.Key_Up):
            self.set_value(self._values[max(0, idx - 1 if idx >= 0 else 0)], emit=True)
        else:
            super().keyPressEvent(e)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        glyph = font("display", QFont.Bold)
        for i, (val, r) in enumerate(zip(self._values, self._cells())):
            selected = val == self._value
            pressed = i == self._pressed
            if selected:
                paint_label(p, r, "ink", fill=C.INK_PRESSED if pressed else C.INK, radius=8)
                fg = C.LABEL
                icons.paint(p, "check", QRectF(r.right() - 26, r.top() + 7, 18, 18), C.LABEL, 2.6)
            else:
                inner = r.adjusted(4, 4, -4, -4)
                paint_label(p, inner, "solid", fill=C.PRESSED if pressed else C.LABEL, radius=7)
                fg = C.INK
            p.setFont(glyph)
            p.setPen(q(fg))
            p.drawText(r, Qt.AlignCenter, val)
        if self.hasFocus() and self._kbd:
            pen = QPen(q(C.INK), 2)
            pen.setDashPattern([1, 2])
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF(self.rect()).adjusted(1, 1, -1, -1))


class CheckRow(_TouchButton):
    """Large checkbox row (56px). Checked = inked box with a check."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setText(text)
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._detail = ""

    def set_detail(self, detail: str) -> None:
        self._detail = detail
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(240, 52)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.isDown():
            p.setPen(Qt.NoPen)
            p.setBrush(q(C.PRESSED))
            p.drawRoundedRect(QRectF(self.rect()), 6, 6)
        box = QRectF(4, (self.height() - 30) / 2, 30, 30)
        enabled = self.isEnabled()
        if self.isChecked():
            p.setPen(Qt.NoPen)
            p.setBrush(q(C.INK if enabled else C.DISABLED))
            p.drawRoundedRect(box, 5, 5)
            icons.paint(p, "check", box.adjusted(4, 4, -4, -4), C.LABEL, 2.8)
        else:
            p.setPen(QPen(q(C.INK if enabled else C.DISABLED), 2))
            p.setBrush(q(C.LABEL))
            p.drawRoundedRect(box.adjusted(1, 1, -1, -1), 5, 5)
        f = font("body", QFont.Medium)
        p.setFont(f)
        p.setPen(q(C.INK if enabled else C.DISABLED))
        x = box.right() + 14
        p.drawText(QRectF(x, 0, self.width() - x, self.height()), Qt.AlignVCenter | Qt.AlignLeft, self.text())
        if self._detail:
            df = font("body", QFont.Bold, mono=True)
            p.setFont(df)
            p.drawText(QRectF(0, 0, self.width() - 4, self.height()), Qt.AlignVCenter | Qt.AlignRight, self._detail)
        self._paint_focus(p, 6)


class FilterTabs(QWidget):
    """Exclusive tabs. Selected tab is inked. A tab flagged ``perforated``
    shows a perforated edge when unselected (the Incomplete filter)."""

    changed = Signal(str)

    def __init__(self, tabs: Sequence[Tuple[str, str, bool]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._keys = [k for k, _, _ in tabs]
        self._labels = {k: t for k, t, _ in tabs}
        self._perf = {k: perf for k, _, perf in tabs}
        self._current = self._keys[0]
        self._pressed: Optional[str] = None
        self.setFixedHeight(TOUCH_MIN)
        self.setCursor(Qt.PointingHandCursor)

    def set_label(self, key: str, text: str) -> None:
        self._labels[key] = text
        self.updateGeometry()
        self.update()

    def current(self) -> str:
        return self._current

    def set_current(self, key: str) -> None:
        self._current = key
        self.update()

    def _rects(self) -> List[Tuple[str, QRectF]]:
        f = font("body", QFont.Bold)
        fm = QFontMetrics(f)
        x = 0.0
        out = []
        for k in self._keys:
            w = fm.horizontalAdvance(self._labels[k]) + 40
            out.append((k, QRectF(x, 0, w, self.height())))
            x += w + 10
        return out

    def sizeHint(self) -> QSize:  # noqa: N802
        rects = self._rects()
        return QSize(int(rects[-1][1].right()) + 2, TOUCH_MIN)

    def _hit(self, pos) -> Optional[str]:
        for k, r in self._rects():
            if r.contains(QPointF(pos)):
                return k
        return None

    def mousePressEvent(self, e) -> None:  # noqa: N802
        self._pressed = self._hit(e.position())
        self.update()

    def mouseReleaseEvent(self, e) -> None:  # noqa: N802
        hit = self._hit(e.position())
        if hit and hit == self._pressed and hit != self._current:
            self._current = hit
            self.changed.emit(hit)
        self._pressed = None
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        f = font("body", QFont.Bold)
        p.setFont(f)
        for k, r in self._rects():
            if k == self._current:
                paint_label(p, r, "ink", radius=8)
                fg = C.LABEL
            else:
                edge = "perforated" if self._perf[k] else "solid"
                paint_label(p, r, edge, fill=C.PRESSED if k == self._pressed else C.LABEL, radius=8)
                fg = C.INK
            p.setPen(q(fg))
            p.drawText(r, Qt.AlignCenter, self._labels[k])


# ---------------------------------------------------------------------------
# Data display
# ---------------------------------------------------------------------------
class ValueList(QWidget):
    """Key/value rows separated by dotted print rules."""

    def __init__(self, rows: Iterable[Tuple[str, str]] = (), value_size: str = "body",
                 key_width: int = 0, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(16)
        self._grid.setVerticalSpacing(0)
        self._value_size = value_size
        self._key_width = key_width
        self._values: dict = {}
        self._row_count = 0
        for key, value in rows:
            self.add_row(key, value)

    def add_row(self, key: str, value: str = "—", mono: bool = False) -> QLabel:
        row = self._row_count
        k = make_label(key, "body", QFont.Normal, color=C.INK_SOFT)
        k.setMinimumHeight(38)
        if self._key_width:
            k.setFixedWidth(self._key_width)
        v = make_label(value, self._value_size, QFont.Bold, mono=mono)
        v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        v.setMinimumHeight(38)
        self._grid.addWidget(k, row, 0)
        self._grid.addWidget(v, row, 1)
        self._values[key] = v
        self._row_count += 1
        return v

    def set(self, key: str, value: str) -> None:
        self._values[key].setText(value)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        pen = QPen(q(C.INK_SOFT), 1)
        pen.setDashPattern([1, 3])
        p.setPen(pen)
        for row in range(self._row_count - 1):
            item = self._grid.itemAtPosition(row, 0)
            if item is None or item.widget() is None:
                continue
            y = item.widget().geometry().bottom() + 0.5
            p.drawLine(QPointF(0, y), QPointF(self.width(), y))


class PhotoView(QWidget):
    """Photo on label stock. Empty state is hatched with an explicit caption."""

    def __init__(self, empty_text: str = "No photo", fit: str = "contain",
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._image: Optional[QImage] = None
        self._empty_text = empty_text
        self._fit = fit
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_image(self, image: Optional[QImage]) -> None:
        self._image = image if image is not None and not image.isNull() else None
        self.update()

    def set_path(self, path: Optional[Path], max_side: int = 1200) -> None:
        if path is None or not Path(path).exists():
            self.set_image(None)
            return
        img = QImage(str(path))
        if not img.isNull() and max(img.width(), img.height()) > max_side:
            img = img.scaled(max_side, max_side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.set_image(img)

    def set_empty_text(self, text: str) -> None:
        self._empty_text = text
        self.update()

    def image(self) -> Optional[QImage]:
        return self._image

    def image_rect(self) -> QRectF:
        frame = QRectF(self.rect()).adjusted(8, 8, -8, -9)
        if self._image is None:
            return frame
        iw, ih = self._image.width(), self._image.height()
        scale = (min if self._fit == "contain" else max)(frame.width() / iw, frame.height() / ih)
        w, h = iw * scale, ih * scale
        return QRectF(frame.center().x() - w / 2, frame.center().y() - h / 2, w, h)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        outer = QRectF(self.rect())
        if self._image is None:
            paint_label(p, outer, "perforated", hatch=True)
            box = QRectF(0, 0, 180, 84)
            box.moveCenter(outer.center())
            p.setPen(Qt.NoPen)
            p.setBrush(q(C.LABEL))
            p.drawRoundedRect(box, 6, 6)
            icons.paint(p, "no-image", QRectF(box.center().x() - 16, box.top() + 12, 32, 32), C.INK_SOFT, 2)
            p.setFont(font("body", QFont.Medium))
            p.setPen(q(C.INK_SOFT))
            p.drawText(QRectF(box.left(), box.top() + 48, box.width(), 26), Qt.AlignCenter, self._empty_text)
            return
        paint_label(p, outer, "plain")
        frame = outer.adjusted(8, 8, -8, -9)
        p.fillRect(frame, q(C.INK))
        p.save()
        p.setClipRect(frame)
        p.drawImage(self.image_rect(), self._image)
        p.restore()


class Viewfinder(PhotoView):
    """Live camera view with framing marks and a status flag."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Camera not available", fit="contain", parent=parent)
        self._flag: Tuple[str, str] = ("LIVE", "ink")
        self._overlay_text = ""
        self._unavailable_reason = ""

    def set_flag(self, text: str, kind: str) -> None:
        self._flag = (text, kind)
        self.update()

    def set_overlay(self, text: str) -> None:
        self._overlay_text = text
        self.update()

    def set_unavailable(self, reason: str) -> None:
        self._unavailable_reason = reason
        self.set_image(None)

    def paintEvent(self, event) -> None:  # noqa: N802
        if self._image is None:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            outer = QRectF(self.rect())
            paint_label(p, outer, "perforated", hatch=True)
            box = outer.adjusted(48, 0, -48, 0)
            box.setHeight(150)
            box.moveCenter(outer.center())
            p.setPen(Qt.NoPen)
            p.setBrush(q(C.LABEL))
            p.drawRoundedRect(box, 8, 8)
            icons.paint(p, "camera-off", QRectF(box.left() + 20, box.top() + 20, 36, 36), C.INK, 2.2)
            p.setPen(q(C.INK))
            p.setFont(font("body", QFont.Bold))
            title = "Camera not available" if self._unavailable_reason else "Starting camera…"
            p.drawText(QRectF(box.left() + 68, box.top() + 20, box.width() - 88, 36), Qt.AlignVCenter, title)
            if self._unavailable_reason:
                p.setFont(font("small"))
                p.setPen(q(C.INK_SOFT))
                p.drawText(QRectF(box.left() + 20, box.top() + 66, box.width() - 40, box.height() - 76),
                           Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, self._unavailable_reason)
            return

        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.image_rect().adjusted(18, 18, -18, -18)
        # Framing marks: four corners, white with an ink keyline so they read
        # on any skin tone.
        L = 26
        for pen in (QPen(q(C.INK, 160), 5), QPen(q("#FFFFFF"), 2.5)):
            pen.setCapStyle(Qt.SquareCap)
            p.setPen(pen)
            for (x, y, sx, sy) in ((r.left(), r.top(), 1, 1), (r.right(), r.top(), -1, 1),
                                   (r.left(), r.bottom(), 1, -1), (r.right(), r.bottom(), -1, -1)):
                p.drawLine(QPointF(x, y), QPointF(x + sx * L, y))
                p.drawLine(QPointF(x, y), QPointF(x, y + sy * L))

        # Flag, top-left of the image.
        text, kind = self._flag
        ff = font("small", QFont.Bold, mono=True)
        ff.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        fw = QFontMetrics(ff).horizontalAdvance(text) + 20
        ir = self.image_rect()
        fr = QRectF(ir.left() + 56, ir.top() + 22, fw, 26)
        p.setPen(Qt.NoPen)
        p.setBrush(q(C.STAT if kind == "stat" else C.INK))
        p.drawRoundedRect(fr, 4, 4)
        p.setFont(ff)
        p.setPen(q(C.INK if kind == "stat" else C.LABEL))
        p.drawText(fr, Qt.AlignCenter, text)

        if self._overlay_text:
            f = font("title", QFont.Bold)
            tw = QFontMetrics(f).horizontalAdvance(self._overlay_text) + 40
            box = QRectF(0, 0, tw, 52)
            box.moveCenter(ir.center())
            p.setPen(Qt.NoPen)
            p.setBrush(q(C.LABEL))
            p.drawRoundedRect(box, 8, 8)
            p.setFont(f)
            p.setPen(q(C.INK))
            p.drawText(box, Qt.AlignCenter, self._overlay_text)


class Thumb(QWidget):
    """Square photo thumbnail for list rows (cover-fit, cached)."""

    _cache: dict = {}

    def __init__(self, size: int = 60, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._pm: Optional[QPixmap] = None

    def set_path(self, path: Optional[Path]) -> None:
        self._pm = None
        if path is not None and Path(path).exists():
            key = (str(path), Path(path).stat().st_mtime, self.width())
            pm = Thumb._cache.get(key)
            if pm is None:
                img = QImage(str(path))
                if not img.isNull():
                    s = self.width() * 2
                    img = img.scaled(s, s, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    x = (img.width() - s) // 2
                    y = (img.height() - s) // 2
                    pm = QPixmap.fromImage(img.copy(x, y, s, s))
                    pm.setDevicePixelRatio(2)
                    Thumb._cache[key] = pm
            self._pm = pm
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = die_cut_path(r, 6)
        if self._pm is None:
            p.setPen(Qt.NoPen)
            p.setBrush(q(C.LABEL))
            p.drawPath(path)
            paint_hatch(p, path, spacing=7)
            pen = QPen(q(C.INK), 1.5)
            pen.setDashPattern([3, 2])
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
            icons.paint(p, "no-image", QRectF(r.center().x() - 12, r.center().y() - 12, 24, 24), C.INK_SOFT, 2)
            return
        p.setClipPath(path)
        p.drawPixmap(r.toRect(), self._pm)
        p.setClipping(False)
        p.setPen(QPen(q(C.INK), 1))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)


# ---------------------------------------------------------------------------
# Running head
# ---------------------------------------------------------------------------
class StepMarks(QWidget):
    """'Step n of 4' with four printed tick segments."""

    def __init__(self, step: int, total: int = 4, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._step, self._total = step, total
        self.setFixedSize(112, 40)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setFont(font("small", QFont.Bold))
        p.setPen(q(C.INK_ON_LINER))
        p.drawText(QRectF(0, 0, self.width(), 20), Qt.AlignLeft | Qt.AlignVCenter,
                   f"Step {self._step} of {self._total}")
        seg_w, gap = 24, 4
        for i in range(self._total):
            r = QRectF(i * (seg_w + gap), 26, seg_w, 6)
            if i < self._step:
                p.setPen(Qt.NoPen)
                p.setBrush(q(C.INK))
            else:
                p.setPen(QPen(q(C.INK_ON_LINER), 1.2))
                p.setBrush(Qt.NoBrush)
                r = r.adjusted(0.6, 0.6, -0.6, -0.6)
            p.drawRoundedRect(r, 1.5, 1.5)


class DeviceStatus(QWidget):
    """Camera and SSD state plus the device clock, printed on the liner."""

    def __init__(self, show_camera: bool = True, show_ssd: bool = True, compact: bool = False,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._compact = compact
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        self._demo = StatusFlag("DEMO DATA", "stat")
        self._demo.setVisible(False)
        lay.addWidget(self._demo)
        lay.addSpacing(14)
        self._cam_icon = Icon("camera", 22, C.INK_ON_LINER)
        self._cam_text = make_label("", "small", QFont.Bold, color=C.INK_ON_LINER)
        self._ssd_icon = Icon("drive", 22, C.INK_ON_LINER)
        self._ssd_text = make_label("", "small", QFont.Bold, color=C.INK_ON_LINER)
        for w, show in ((self._cam_icon, show_camera), (self._cam_text, show_camera)):
            w.setVisible(show)
            lay.addWidget(w)
        if show_camera:
            lay.addSpacing(10)
        for w in (self._ssd_icon, self._ssd_text):
            w.setVisible(show_ssd)
            lay.addWidget(w)
        if compact:
            # Icon-only: the crossed icon carries state by shape, not colour.
            self._cam_text.setVisible(False)
            self._ssd_text.setVisible(False)
        lay.addSpacing(14)
        self._clock = make_label("", "body", QFont.Bold, mono=True, color=C.INK)
        lay.addWidget(self._clock)

    def refresh(self, state, camera) -> None:
        self._demo.setVisible(bool(getattr(state, "demo", False)))
        from .camera import CameraState  # local import avoids a cycle

        if camera is not None:
            if camera.state == CameraState.LIVE:
                self._cam_icon.set("camera")
                self._cam_text.setText("Camera")
            elif camera.state == CameraState.SIMULATED:
                self._cam_icon.set("camera")
                self._cam_text.setText("Sim camera")
            else:
                self._cam_icon.set("camera-off")
                self._cam_text.setText("No camera")
        if state.ssd_connected:
            self._ssd_icon.set("drive")
            self._ssd_text.setText("SSD")
        else:
            self._ssd_icon.set("drive-off")
            self._ssd_text.setText("No SSD")
        self._clock.setText(datetime.now().strftime("%H:%M"))


class RunningHead(QWidget):
    """Top strip of every screen: back, session ID, title, step, status."""

    back_clicked = Signal()

    def __init__(self, title: str, show_back: bool = True, step: Optional[int] = None,
                 show_camera: bool = True, show_ssd: bool = True,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(HEAD_HEIGHT)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(GUTTER, 6, GUTTER, 0)
        lay.setSpacing(GAP)

        self.back = BackTab()
        self.back.clicked.connect(self.back_clicked.emit)
        self.back.setVisible(show_back)
        lay.addWidget(self.back)

        self.id_flag = StatusFlag("", "outline")
        self.id_flag.setVisible(False)
        lay.addWidget(self.id_flag, 0, Qt.AlignVCenter)

        self.title = make_label(title, "title", QFont.Bold)
        lay.addWidget(self.title)

        self.steps = StepMarks(step) if step else None
        if self.steps:
            lay.addSpacing(4)
            lay.addWidget(self.steps, 0, Qt.AlignVCenter)
        lay.addStretch(1)

        self.status = DeviceStatus(show_camera=show_camera, show_ssd=show_ssd, compact=bool(step))
        lay.addWidget(self.status)

    def set_title(self, title: str) -> None:
        self.title.setText(title)

    def set_session_id(self, session_id: Optional[str]) -> None:
        if session_id:
            self.id_flag.set(session_id, "outline")
            self.id_flag._font = font("body", QFont.Bold, mono=True)
            self.id_flag.setFixedSize(self.id_flag.sizeHint().width() + 4, 32)
        self.id_flag.setVisible(bool(session_id))


# ---------------------------------------------------------------------------
# Motion: the print feed
# ---------------------------------------------------------------------------
class PrintFeed(QWidget):
    """Hosts one child and feeds it out from the top edge, like a label
    leaving a printer. Children are clipped to this widget's bounds."""

    def __init__(self, child: QWidget, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._child = child
        child.setParent(self)
        self._progress = 1.0
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(560)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._set_progress)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self._child.sizeHint()

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self._child.minimumSizeHint()

    def _set_progress(self, value: float) -> None:
        self._progress = float(value)
        self._place()

    def _place(self) -> None:
        h = self.height()
        offset = int(round(-(1.0 - self._progress) * h))
        self._child.setGeometry(0, offset, self.width(), h)

    def resizeEvent(self, _event) -> None:  # noqa: N802
        self._place()

    def play(self, reduced_motion: bool = False) -> None:
        if reduced_motion:
            self._set_progress(1.0)
            return
        self._anim.stop()
        self._set_progress(0.0)
        self._anim.start()


# ---------------------------------------------------------------------------
# Confirmation sheet
# ---------------------------------------------------------------------------
class ConfirmSheet(QWidget):
    """Protected-focus confirmation for actions that lose data. The safe
    choice is the primary (inked) action; the losing choice is outlined."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setVisible(False)
        self._on_confirm: Optional[Callable[[], None]] = None

        self.card = LabelCard("stat", padding=(24, 20, 24, 20), parent=self)
        self.card.setFixedWidth(500)
        lay = QVBoxLayout(self.card)
        lay.setSpacing(10)
        self.title = make_label("", "title", QFont.Bold, wrap=True)
        self.body = make_label("", "body", color=C.INK_SOFT, wrap=True)
        lay.addWidget(self.title)
        lay.addWidget(self.body)
        lay.addSpacing(10)
        row = QHBoxLayout()
        row.setSpacing(GAP)
        self.confirm_btn = InkButton("", "secondary", icon="alert")
        self.cancel_btn = InkButton("", "primary")
        self.confirm_btn.clicked.connect(self._confirm)
        self.cancel_btn.clicked.connect(self.hide_sheet)
        row.addWidget(self.confirm_btn, 1)
        row.addWidget(self.cancel_btn, 1)
        lay.addLayout(row)

    def ask(self, title: str, body: str, confirm: str, cancel: str,
            on_confirm: Callable[[], None]) -> None:
        self.title.setText(title)
        self.body.setText(body)
        self.confirm_btn.setText(confirm)
        self.cancel_btn.setText(cancel)
        self._on_confirm = on_confirm
        self.setGeometry(self.parentWidget().rect())
        self.card.adjustSize()
        self.card.move((self.width() - self.card.width()) // 2, (self.height() - self.card.height()) // 2)
        self.setVisible(True)
        self.raise_()

    def hide_sheet(self) -> None:
        self.setVisible(False)
        self._on_confirm = None

    def _confirm(self) -> None:
        cb = self._on_confirm
        self.hide_sheet()
        if cb:
            cb()

    def mousePressEvent(self, e) -> None:  # noqa: N802
        e.accept()  # swallow taps on the scrim; choose explicitly

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(self.rect(), q(C.SCRIM, 150))
