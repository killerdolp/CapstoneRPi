"""Past sessions: filterable list of session labels."""

from __future__ import annotations

from typing import List

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QFont, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QScrollArea,
    QScroller,
    QScrollerProperties,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import icons
from ..app_state import Session
from ..theme import GAP, C
from ..widgets import (
    InkButton,
    LabelCard,
    StatusFlag,
    Thumb,
    _TouchButton,
    make_label,
    paint_label,
)
from .base import Screen


class SessionRow(_TouchButton):
    """A tappable session label: solid edge complete, perforated incomplete."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session
        self.setFixedHeight(78)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 14, 9)
        lay.setSpacing(14)
        thumb = Thumb(60)
        thumb.set_path(session.photo_path if session.has_photo else None)
        thumb.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(thumb)

        col = QVBoxLayout()
        col.setSpacing(0)
        ident = make_label(session.session_id, "title", QFont.Bold, mono=True)
        when = make_label(session.saved_at_display, "small", QFont.Medium, color=C.INK_SOFT)
        col.addWidget(ident)
        col.addWidget(when)
        lay.addLayout(col)
        lay.addSpacing(10)

        ident.setFixedWidth(118)
        when.setFixedWidth(150)
        type_lbl = make_label(f"Type {session.field_or_dash(session.skin_type)}", "body", QFont.Medium)
        grade_lbl = make_label(f"Grade {session.field_or_dash(session.erythema_grade)}", "body", QFont.Medium)
        type_lbl.setFixedWidth(90)
        grade_lbl.setFixedWidth(120)
        lay.addWidget(type_lbl)
        lay.addWidget(grade_lbl)
        lay.addStretch(1)

        flag = StatusFlag()
        flag.set_for_session(session)
        lay.addWidget(flag)
        lay.addSpacing(30)  # room for the painted chevron

        for w in (ident, when, type_lbl, grade_lbl, flag):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        edge = "solid" if self.session.is_complete else "perforated"
        paint_label(p, QRectF(self.rect()), edge, fill=C.PRESSED if self.isDown() else C.LABEL)
        icons.paint(p, "next", QRectF(self.width() - 36, (self.height() - 24) / 2, 24, 24), C.INK, 2.4)
        self._paint_focus(p)


class PastSessionsScreen(Screen):
    def __init__(self, controller) -> None:
        super().__init__(controller, "Past sessions")
        self._filter = "all"

        from ..widgets import FilterTabs

        bar = QHBoxLayout()
        self.tabs = FilterTabs([("all", "All", False), ("complete", "Complete", False),
                                ("incomplete", "Incomplete", True)])
        self.tabs.changed.connect(self._set_filter)
        bar.addWidget(self.tabs)
        bar.addStretch(1)
        self.body.addLayout(bar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(10)
        self.scroll.setWidget(self.container)
        self.body.addWidget(self.scroll, 1)
        self.legend = make_label("Solid edge: complete  ·  Perforated edge: incomplete  ·  "
                                 "Drag to scroll, tap a session to open it",
                                 "small", QFont.Medium, color=C.INK_ON_LINER)
        self.body.addWidget(self.legend)

        # Touch: drag the list with a finger (kinetic), no overshoot bounce.
        QScroller.grabGesture(self.scroll.viewport(), QScroller.LeftMouseButtonGesture)
        scroller = QScroller.scroller(self.scroll.viewport())
        props = scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.VerticalOvershootPolicy,
                              QScrollerProperties.OvershootAlwaysOff)
        props.setScrollMetric(QScrollerProperties.DragStartDistance, 0.004)
        scroller.setScrollerProperties(props)

    def _set_filter(self, key: str) -> None:
        self._filter = key
        self._rebuild()

    def _filtered(self) -> List[Session]:
        sessions = sorted(self.controller.state.sessions,
                          key=lambda s: (s.saved_at is not None, s.saved_at), reverse=True)
        if self._filter == "complete":
            return [s for s in sessions if s.is_complete]
        if self._filter == "incomplete":
            return [s for s in sessions if not s.is_complete]
        return sessions

    def _clear(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    def _rebuild(self) -> None:
        self._clear()
        state = self.controller.state
        self.tabs.set_label("all", f"All ({len(state.sessions)})")
        self.tabs.set_label("complete", f"Complete ({len(state.complete_sessions())})")
        self.tabs.set_label("incomplete", f"Incomplete ({len(state.incomplete_sessions())})")
        self.tabs.setFixedWidth(self.tabs.sizeHint().width())

        sessions = self._filtered()
        self.legend.setVisible(bool(sessions))
        if not sessions:
            self.list_layout.addWidget(self._empty_state())
        for session in sessions:
            row = SessionRow(session)
            row.clicked.connect(lambda _=False, s=session: self.controller.show_session_detail(s))
            self.list_layout.addWidget(row)
        self.list_layout.addStretch(1)
        self.scroll.verticalScrollBar().setValue(0)

    def _empty_state(self) -> QWidget:
        card = LabelCard("perforated", padding=(24, 20, 24, 20))
        lay = QVBoxLayout(card)
        lay.setSpacing(8)
        if self._filter == "all":
            title, body = ("No sessions on this device yet",
                           "Sessions you save appear here, newest first.")
        elif self._filter == "complete":
            title, body = ("No complete sessions",
                           "A session is complete once it has a skin type, an erythema grade and a photo.")
        else:
            title, body = ("No incomplete sessions", "Every saved session is complete.")
        lay.addWidget(make_label(title, "title", QFont.Bold))
        lay.addWidget(make_label(body, "body", color=C.INK_SOFT, wrap=True))
        if self._filter == "all":
            btn = InkButton("New session", "primary", icon="plus",
                            on_click=self.controller.start_new_session)
            btn.setFixedWidth(240)
            lay.addSpacing(6)
            lay.addWidget(btn)
        return card

    def on_enter(self) -> None:
        self._rebuild()
