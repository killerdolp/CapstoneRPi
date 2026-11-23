"""Session Saved screen (Figma 07; Figma 13 after an edit, with "Edited")."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout

from ..theme import px
from ..widgets import FigmaScreen, InfoCard, Preview, action_button, session_info_lines


class SessionSavedScreen(FigmaScreen):
    def __init__(self, controller) -> None:
        super().__init__("Session Saved", step="Step 3 of 3")
        self.controller = controller

        body = QHBoxLayout()
        body.setSpacing(px(20))
        body.addStretch(1)
        self.preview = Preview("Captured Image", 520, 340)
        body.addWidget(self.preview)
        self.info = InfoCard(360, 340)
        body.addWidget(self.info)
        body.addStretch(1)

        self.content.addStretch(1)
        self.content.addLayout(body)
        self.content.addStretch(1)

        self.home_btn = action_button("Home", "secondary", 160, self.controller.go_home)
        self.view_btn = action_button(
            "View Past Sessions", "primary", 245, self.controller.show_past_sessions
        )
        self.set_footer(left=[self.home_btn], right=[self.view_btn])

    def on_enter(self) -> None:
        session = self.controller.last_saved_session
        if session is None:
            return
        self.info.set_lines(session_info_lines(session))
        self.preview.show_file(self.controller.state.photo_file(session), "No Image")
