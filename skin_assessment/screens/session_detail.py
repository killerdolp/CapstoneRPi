"""Session Details screen (Figma 09)."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout

from ..theme import px
from ..widgets import FigmaScreen, InfoCard, Preview, action_button, session_info_lines


class SessionDetailScreen(FigmaScreen):
    def __init__(self, controller) -> None:
        super().__init__("Session")
        self.controller = controller

        body = QHBoxLayout()
        body.setSpacing(px(20))
        body.addStretch(1)
        self.photo = Preview("Captured Image", 520, 340)
        body.addWidget(self.photo)
        self.info = InfoCard(360, 340)
        body.addWidget(self.info)
        body.addStretch(1)

        self.content.addStretch(1)
        self.content.addLayout(body)
        self.content.addStretch(1)

        self.home_btn = action_button("Home", "secondary", 160, self.controller.go_home)
        self.edit_btn = action_button("Edit Session", "primary", 178, self._edit)
        self.set_footer(left=[self.home_btn], right=[self.edit_btn])

    def on_enter(self) -> None:
        session = self.controller.selected_session
        if session is None:
            return
        self.set_title(session.session_id)
        self.info.set_lines(session_info_lines(session))
        # Show the saved photo, or that there is none.
        self.photo.show_file(self.controller.state.photo_file(session), "No Image")

    def _edit(self) -> None:
        session = self.controller.selected_session
        if session is not None:
            self.controller.edit_session(session)
