"""Shared theme constants and stylesheet for the Skin Assessment app.

Designed for a 7-inch Raspberry Pi touchscreen (800x480 landscape).
Low-fidelity black/white aesthetic matching the wireframe.
"""

# Target display size for a common 7" RPi touchscreen.
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

# Palette (low-fi monochrome).
BLACK = "#1a1a1a"
WHITE = "#ffffff"
GREY_FILL = "#d9d9d9"       # filled/primary CTA buttons in wireframe
GREY_IMAGE = "#ececec"      # image placeholder fill
GREY_BORDER = "#9a9a9a"
GREY_TEXT = "#6b6b6b"       # helper/caption text

STYLESHEET = f"""
QWidget {{
    background: {WHITE};
    color: {BLACK};
    font-family: "Helvetica Neue", "Arial", sans-serif;
    font-size: 15px;
}}

/* ---- Header ---- */
#BackButton {{
    background: {WHITE};
    border: 2px solid {BLACK};
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 15px;
    font-weight: 600;
}}
#BackButton:pressed {{
    background: {GREY_IMAGE};
}}
#ScreenTitle {{
    font-size: 24px;
    font-weight: 700;
}}

/* ---- Generic labels ---- */
#FieldLabel {{
    font-size: 15px;
    color: {BLACK};
}}
#HelperText {{
    font-size: 13px;
    color: {GREY_TEXT};
}}
#DashedBanner {{
    border: 2px dashed {BLACK};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
}}

/* ---- Option toggle buttons (skin type / erythema) ---- */
#OptionButton {{
    background: {WHITE};
    border: 2px solid {BLACK};
    border-radius: 6px;
    font-size: 20px;
    font-weight: 700;
    padding: 10px;
}}
#OptionButton:checked {{
    background: {BLACK};
    color: {WHITE};
}}

/* ---- Standard (outline) buttons ---- */
QPushButton[variant="outline"] {{
    background: {WHITE};
    border: 2px solid {BLACK};
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 16px;
    font-weight: 700;
}}
QPushButton[variant="outline"]:pressed {{
    background: {GREY_IMAGE};
}}

/* ---- Primary (filled grey) CTA buttons ---- */
QPushButton[variant="primary"] {{
    background: {GREY_FILL};
    border: 2px solid {GREY_FILL};
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 16px;
    font-weight: 700;
}}
QPushButton[variant="primary"]:pressed {{
    background: #c7c7c7;
}}

/* ---- Disabled CTA ---- */
QPushButton[variant="primary"]:disabled {{
    background: {GREY_IMAGE};
    border-color: {GREY_IMAGE};
    color: {GREY_BORDER};
}}

/* ---- Home tiles ---- */
QPushButton[variant="tile"] {{
    background: {WHITE};
    border: 2px solid {BLACK};
    border-radius: 8px;
    font-size: 18px;
    font-weight: 700;
    padding: 12px;
}}
QPushButton[variant="tile"][accent="true"] {{
    background: {GREY_FILL};
    border-color: {BLACK};
}}
QPushButton[variant="tile"]:pressed {{
    background: {GREY_IMAGE};
}}

/* ---- Image placeholders ---- */
#ImagePlaceholder {{
    background: {GREY_IMAGE};
    border: 1px solid {GREY_BORDER};
    color: {GREY_TEXT};
    font-size: 15px;
}}

/* ---- Cards / framed boxes ---- */
#Card {{
    border: 2px solid {BLACK};
    border-radius: 6px;
    background: {WHITE};
}}
#DashedCard {{
    border: 2px dashed {BLACK};
    border-radius: 6px;
    background: {WHITE};
}}
#WarningCard {{
    border: 2px solid {BLACK};
    border-radius: 6px;
    background: {GREY_FILL};
}}
#WarningCard QLabel {{
    background: transparent;
}}
#Card QLabel, #DashedCard QLabel, #WarningCard QCheckBox {{
    background: transparent;
}}

/* ---- Status pills ---- */
#StatusComplete {{
    background: {BLACK};
    color: {WHITE};
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 700;
}}
#StatusIncomplete {{
    background: {WHITE};
    color: {BLACK};
    border: 2px dashed {BLACK};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 700;
}}

/* ---- Filter chips (past sessions) ---- */
QPushButton[variant="chip"] {{
    background: {WHITE};
    border: 2px solid {BLACK};
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 14px;
    font-weight: 700;
}}
QPushButton[variant="chip"]:checked {{
    background: {BLACK};
    color: {WHITE};
}}
QPushButton[variant="chip"][dashed="true"] {{
    border: 2px dashed {BLACK};
}}

/* ---- Session rows ---- */
#SessionRow {{
    border: 2px solid {BLACK};
    border-radius: 6px;
    background: {WHITE};
}}
#SessionRowIncomplete {{
    border: 2px dashed {BLACK};
    border-radius: 6px;
    background: {WHITE};
}}
#RowId {{
    font-size: 17px;
    font-weight: 700;
}}
#RowDate {{
    font-size: 13px;
    color: {GREY_TEXT};
}}
#RowThumb {{
    background: {GREY_IMAGE};
    border: 1px solid {GREY_BORDER};
    color: {GREY_TEXT};
    font-size: 11px;
}}
#RowThumbEmpty {{
    background: {WHITE};
    border: 2px dashed {BLACK};
    color: {GREY_TEXT};
    font-size: 11px;
}}

/* ---- Checkboxes ---- */
QCheckBox {{
    font-size: 15px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {BLACK};
    border-radius: 3px;
    background: {WHITE};
}}
QCheckBox::indicator:checked {{
    background: {BLACK};
}}

#CardTitle {{
    font-size: 16px;
    font-weight: 700;
}}
#ValueStrong {{
    font-size: 15px;
    font-weight: 700;
}}
#ScrollArea, #ScrollArea > QWidget > QWidget {{
    background: {WHITE};
    border: none;
}}
"""
