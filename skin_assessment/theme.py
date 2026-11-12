"""Design tokens for the Skin Assessment device.

Visual world: *Specimen Label*. Every surface is a die-cut clinical label
(label stock) sitting on a cool backing liner, printed in thermal black.

State grammar (never colour alone):
    solid edge      -> complete
    perforated edge -> incomplete
    hatched fill    -> unavailable
    STAT orange     -> attention flag, always carries ink text

Type: Atkinson Hyperlegible Next + Atkinson Hyperlegible Mono (OFL), bundled
in ``assets/fonts`` so the device never depends on system fonts. A fixed
four-step ladder; nothing is set between the steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtGui import QColor, QFont, QFontDatabase

# Official Raspberry Pi 7" Touch Display, landscape.
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

ASSETS = Path(__file__).resolve().parent / "assets"


class C:
    """Colour tokens (hex strings, use ``q()`` for QColor)."""

    LINER = "#C5CBD1"        # backing liner: the app ground
    LINER_EDGE = "#A3ACB5"   # liner-side shadow line under label stock
    LABEL = "#FBFBF8"        # label stock
    LABEL_EDGE = "#8E98A2"   # die-cut edge of plain labels
    HATCH = "#C9CDD1"        # hatching for unavailable surfaces
    PRESSED = "#E4E7E3"      # label stock while pressed
    INK = "#141516"          # thermal black: all clinical values
    INK_PRESSED = "#33373B"  # inked control while pressed
    INK_SOFT = "#4B5157"     # secondary text on label stock (7.7:1)
    INK_ON_LINER = "#30363C" # text placed directly on the liner (7.4:1)
    DISABLED = "#6E757C"     # disabled text on hatched stock (4.6:1)
    STAT = "#E8461E"         # attention flag; carries INK text (5.3:1)
    SCRIM = "#141516"        # behind confirmation sheets


def q(hex_value: str, alpha: int = 255) -> QColor:
    color = QColor(hex_value)
    color.setAlpha(alpha)
    return color


# ---- type --------------------------------------------------------------
SIZE: Dict[str, int] = {
    "small": 14,    # captions, flags, field keys
    "body": 17,     # body copy, values, button labels
    "title": 23,    # screen titles, section heads, primary actions
    "display": 36,  # session IDs, grade glyphs
}

_FAMILIES = {"sans": "Atkinson Hyperlegible Next", "mono": "Atkinson Hyperlegible Mono"}


def load_fonts() -> None:
    """Register the bundled faces. Call once after QApplication exists."""
    found: Dict[str, str] = {}
    for path in sorted((ASSETS / "fonts").glob("*.ttf")):
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            continue
        key = "mono" if "Mono" in path.name else "sans"
        found.setdefault(key, families[0])
    _FAMILIES.update(found)


def font(size: str = "body", weight: QFont.Weight = QFont.Normal, mono: bool = False) -> QFont:
    f = QFont(_FAMILIES["mono" if mono else "sans"])
    f.setPixelSize(SIZE[size])
    f.setWeight(weight)
    f.setHintingPreference(QFont.PreferNoHinting)
    if mono:
        f.setStyleHint(QFont.Monospace)
    return f


def family(mono: bool = False) -> str:
    return _FAMILIES["mono" if mono else "sans"]


# ---- geometry ----------------------------------------------------------
RADIUS = 10          # die-cut corner
HEAD_HEIGHT = 60     # running head
GUTTER = 16          # outer margin
GAP = 12             # gap between labels
TOUCH_MIN = 48       # any tappable thing
TOUCH_PRIMARY = 60   # primary actions


def stylesheet() -> str:
    """Global QSS. Most surfaces are painted; this styles what Qt draws."""
    return f"""
QWidget {{
    color: {C.INK};
}}
QMainWindow, #Root {{
    background: {C.LINER};
}}
QLabel {{
    background: transparent;
}}
QScrollArea, QScrollArea > QWidget > QWidget {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px 0 2px 4px;
}}
QScrollBar::handle:vertical {{
    background: {C.INK_SOFT};
    border-radius: 3px;
    min-height: 40px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
    height: 0;
}}
"""
