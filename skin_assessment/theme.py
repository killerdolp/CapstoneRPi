"""Theme for the Whyre 2D Imaging UI (Figma file "Whyre_UI").

The Figma frames are drawn at 1024x600. The device display is 1280x800, so
every Figma measurement goes through ``px()``, which scales it by 1280/1024.
The display is taller than the Figma frame (16:10 vs 128:75), so the extra
height goes to the content area between the header and footer.
"""

from __future__ import annotations

from pathlib import Path

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800

FIGMA_WIDTH = 1024
SCALE = SCREEN_WIDTH / FIGMA_WIDTH


def px(figma_px: float) -> int:
    """Convert a Figma measurement (1024-wide frame) to screen pixels."""
    return max(1, round(figma_px * SCALE))


# ---- Palette -----------------------------------------------------------
WHITE = "#FFFFFF"
NAVY = "#172B4D"        # text
BORDER = "#CBD5E1"      # dividers, card and option outlines
TEAL = "#176B87"        # primary actions, selected options
CONTENT_BG = "#F8FAFC"  # content area behind cards (sampled from Figma)
MUTED = "#64748B"       # secondary text: step label, field captions
PREVIEW_BG = "#1F2937"  # camera / photo placeholder (sampled from Figma)
TEAL_PRESSED = "#12566C"
TEAL_TINT = "#E8F1F4"   # pressed state of outline buttons

# ---- Type (Figma sizes, estimated from the frames) ----------------------
FONT_FAMILY = "Inter"
FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"

SIZE_TITLE = px(28)      # header title
SIZE_STEP = px(16)       # "Step 1 of 3"
SIZE_PROMPT = px(22)     # "Select the patient's skin type"
SIZE_OPTION = px(24)     # score digits
SIZE_BUTTON = px(20)     # button labels
SIZE_BODY = px(18)       # info card lines, captions
SIZE_ID = px(28)         # session ID on the New Session card
SIZE_DATE = px(22)       # date on the New Session card
SIZE_ROW_ID = px(20)     # session ID in the past-sessions list
SIZE_ROW_META = px(16)   # date and status in the past-sessions list

# ---- Layout (Figma px) --------------------------------------------------
HEADER_H = px(72)
FOOTER_H = px(88)
MARGIN = px(32)
BUTTON_H = px(60)
GAP = px(16)
RADIUS = px(8)
CARD_RADIUS = px(12)


def load_fonts() -> None:
    """Register the bundled Inter faces with Qt. Call after QApplication."""
    from PySide6.QtGui import QFontDatabase

    for path in sorted(FONT_DIR.glob("Inter-*.ttf")):
        QFontDatabase.addApplicationFont(str(path))


STYLESHEET = f"""
QMainWindow, QStackedWidget {{
    background: {CONTENT_BG};
}}
QWidget {{
    font-family: "{FONT_FAMILY}";
    color: {NAVY};
}}
QLabel {{
    background: transparent;
}}

/* ---- Screen frame ---- */
#HeaderBar {{
    background: {WHITE};
    border: none;
    border-bottom: 1px solid {BORDER};
}}
#HeaderTitle {{
    font-size: {SIZE_TITLE}px;
    font-weight: 600;
}}
#StepLabel {{
    font-size: {SIZE_STEP}px;
    font-weight: 600;
    color: {MUTED};
}}
#Content {{
    background: {CONTENT_BG};
    border: none;
}}
#FooterBar {{
    background: {WHITE};
    border: none;
    border-top: 1px solid {BORDER};
}}

/* ---- Buttons ---- */
QPushButton[variant="primary"] {{
    background: {TEAL};
    color: {WHITE};
    border: 1px solid {TEAL};
    border-radius: {RADIUS}px;
    font-size: {SIZE_BUTTON}px;
    font-weight: 600;
    padding: 0 {px(12)}px;
}}
QPushButton[variant="primary"]:pressed {{
    background: {TEAL_PRESSED};
    border-color: {TEAL_PRESSED};
}}
QPushButton[variant="primary"]:disabled {{
    background: {BORDER};
    border-color: {BORDER};
    color: {WHITE};
}}
QPushButton[variant="secondary"] {{
    background: {WHITE};
    color: {TEAL};
    border: 1px solid {TEAL};
    border-radius: {RADIUS}px;
    font-size: {SIZE_BUTTON}px;
    font-weight: 600;
    padding: 0 {px(12)}px;
}}
QPushButton[variant="secondary"]:pressed {{
    background: {TEAL_TINT};
}}

/* Filter chips: outline, filled teal when active. */
QPushButton[variant="chip"] {{
    background: {WHITE};
    color: {TEAL};
    border: 1px solid {TEAL};
    border-radius: {RADIUS}px;
    font-size: {SIZE_BUTTON}px;
    font-weight: 600;
}}
QPushButton[variant="chip"]:checked {{
    background: {TEAL};
    color: {WHITE};
}}

/* Score / grade options. */
QPushButton[variant="option"] {{
    background: {WHITE};
    color: {NAVY};
    border: 2px solid {BORDER};
    border-radius: {RADIUS}px;
    font-size: {SIZE_OPTION}px;
    font-weight: 600;
}}
QPushButton[variant="option"]:pressed {{
    background: {TEAL_TINT};
}}
QPushButton[variant="option"]:checked {{
    background: {TEAL};
    color: {WHITE};
    border-color: {TEAL};
}}

/* ---- Text ---- */
#Prompt {{
    font-size: {SIZE_PROMPT}px;
    font-weight: 600;
}}
#Hint {{
    font-size: {SIZE_BODY}px;
    font-weight: 600;
}}
#Caption {{
    font-size: {SIZE_BODY}px;
    font-weight: 500;
    color: {MUTED};
}}
#BigValue {{
    font-size: {SIZE_ID}px;
    font-weight: 600;
}}
#DateValue {{
    font-size: {SIZE_DATE}px;
    font-weight: 600;
}}
#InfoLine {{
    font-size: {SIZE_BODY}px;
}}
#DetailLabel {{
    font-size: {SIZE_BODY}px;
    color: {MUTED};
}}
#DetailValue {{
    font-size: {SIZE_BODY}px;
    font-weight: 600;
}}

/* ---- Cards ---- */
#Card {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: {CARD_RADIUS}px;
}}
#InfoCard {{
    background: {WHITE};
    border: 1px solid {MUTED};
    border-radius: {RADIUS}px;
}}
#Divider {{
    background: {BORDER};
    border: none;
}}
#Preview {{
    background: {PREVIEW_BG};
    color: {WHITE};
    font-size: {SIZE_BUTTON}px;
    font-weight: 600;
}}

/* ---- Past sessions ---- */
#SessionCard {{
    background: {WHITE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS}px;
}}
#SessionCard[pressed="true"] {{
    background: {TEAL_TINT};
}}
#RowId {{
    font-size: {SIZE_ROW_ID}px;
    font-weight: 600;
}}
#RowMeta {{
    font-size: {SIZE_ROW_META}px;
    font-weight: 600;
}}
QScrollArea#SessionList, QScrollArea#SessionList > QWidget > QWidget {{
    background: {CONTENT_BG};
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: {px(8)}px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: {px(4)}px;
    min-height: {px(40)}px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: none;
}}
"""
