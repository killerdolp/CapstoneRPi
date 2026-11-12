"""Authored stroke icon set (24-unit grid, 2-unit stroke, round joins).

Icons are SVG fragments rendered through QtSvg so they stay crisp at any
size and can be re-inked per state.
"""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_PATHS = {
    "plus": '<path d="M12 4.5v15M4.5 12h15"/>',
    "list": '<path d="M9 6.5h11M9 12h11M9 17.5h11"/><path d="M4.2 6.5h.1M4.2 12h.1M4.2 17.5h.1" stroke-width="3"/>',
    "export": '<path d="M12 3.5v11"/><path d="M7.5 8L12 3.5 16.5 8"/><path d="M4 14v4.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V14"/>',
    "camera": '<path d="M3.5 8.5A1.5 1.5 0 0 1 5 7h2.5l1.8-2.5h5.4L16.5 7H19a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 19 19H5a1.5 1.5 0 0 1-1.5-1.5z"/><circle cx="12" cy="12.8" r="3.4"/>',
    "camera-off": '<path d="M3.5 8.5A1.5 1.5 0 0 1 5 7h2.5l1.8-2.5h5.4L16.5 7H19a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 19 19H5a1.5 1.5 0 0 1-1.5-1.5z"/><path d="M3 3l18 18"/>',
    "back": '<path d="M14.5 5L7.5 12l7 7"/>',
    "next": '<path d="M9.5 5l7 7-7 7"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "drive": '<rect x="3" y="8" width="18" height="9" rx="1.5"/><path d="M7 12.5h.1M10 12.5h.1" stroke-width="2.6"/><path d="M14 12.5h3.5"/>',
    "drive-off": '<rect x="3" y="8" width="18" height="9" rx="1.5"/><path d="M3 3l18 18"/>',
    "alert": '<path d="M10.3 4.2L2.8 17.5A2 2 0 0 0 4.5 20.5h15a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4.5"/><path d="M12 17.2h.1" stroke-width="2.6"/>',
    "retake": '<path d="M3.5 4.5v5.5H9"/><path d="M5 15a7.5 7.5 0 1 0 1.7-7.8L3.5 10"/>',
    "no-image": '<rect x="3.5" y="5" width="17" height="14" rx="1.5"/><path d="M3 3l18 18"/>',
    "home": '<path d="M3.5 11L12 4l8.5 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5h4v5"/>',
    "save": '<path d="M5 4h11l3 3v13H5z"/><path d="M8.5 4v5h7V4"/><path d="M8.5 20v-6h7v6"/>',
    "edit": '<path d="M4 20h4.5L19.5 9a2.1 2.1 0 0 0-3-3L5.5 17z"/><path d="M14.5 8l3 3"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
}


def _svg(name: str, color: str, stroke: float) -> bytes:
    body = _PATHS[name]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</svg>'
    ).encode()


@lru_cache(maxsize=256)
def _renderer(name: str, color: str, stroke: float) -> QSvgRenderer:
    return QSvgRenderer(QByteArray(_svg(name, color, stroke)))


def paint(painter: QPainter, name: str, rect: QRectF, color: str, stroke: float = 2.0) -> None:
    """Paint icon ``name`` into ``rect`` with the given ink colour."""
    _renderer(name, color, stroke).render(painter, rect)


def pixmap(name: str, size: int, color: str, stroke: float = 2.0, dpr: float = 1.0) -> QPixmap:
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    paint(p, name, QRectF(0, 0, size, size), color, stroke)
    p.end()
    return pm
