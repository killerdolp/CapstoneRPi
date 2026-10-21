"""In-memory application state and data model for the Skin Assessment app.

This is a front-end prototype: sessions live in memory and are seeded with the
sample data shown in the wireframe. No real persistence or camera hardware is
wired up; those are left as integration points for the capstone backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


# Erythema grade options as shown in the wireframe.
ERYTHEMA_GRADES = ["0", "±", "+", "++", "+++"]
# Skin type (Fitzpatrick 2-6) options.
SKIN_TYPES = ["2", "3", "4", "5", "6"]


@dataclass
class Session:
    """A single patient assessment session."""

    session_id: str
    skin_type: Optional[str] = None       # one of SKIN_TYPES, or None if unset
    erythema_grade: Optional[str] = None  # one of ERYTHEMA_GRADES, or None
    has_photo: bool = False
    saved_at: Optional[datetime] = None

    @property
    def is_complete(self) -> bool:
        return (
            self.skin_type is not None
            and self.erythema_grade is not None
            and self.has_photo
        )

    @property
    def status_label(self) -> str:
        return "COMPLETE" if self.is_complete else "INCOMPLETE"

    @property
    def saved_at_display(self) -> str:
        if self.saved_at is None:
            return "—"
        # e.g. "13 Oct 2026, 21:10" (strip leading zero on day).
        return self.saved_at.strftime("%d %b %Y, %H:%M").lstrip("0")

    def field_or_dash(self, value: Optional[str]) -> str:
        return value if value else "—"


class AppState:
    """Holds the session list and global device status."""

    def __init__(self) -> None:
        self.ssd_connected: bool = True
        self.sessions: List[Session] = []
        self._seed()

    # ---- seeding ----------------------------------------------------------
    def _seed(self) -> None:
        """Seed with the four sample sessions from the wireframe."""
        self.sessions = [
            Session(
                session_id="S-0001",
                skin_type=None,
                erythema_grade=None,
                has_photo=False,
                saved_at=datetime(2026, 10, 9, 9, 12),
            ),
            Session(
                session_id="S-0002",
                skin_type="3",
                erythema_grade="+",
                has_photo=True,
                saved_at=datetime(2026, 10, 9, 14, 20),
            ),
            Session(
                session_id="S-0003",
                skin_type=None,
                erythema_grade=None,
                has_photo=False,
                saved_at=datetime(2026, 10, 12, 11, 5),
            ),
            Session(
                session_id="S-0004",
                skin_type="3",
                erythema_grade="+",
                has_photo=True,
                saved_at=datetime(2026, 10, 12, 16, 42),
            ),
        ]

    # ---- queries ----------------------------------------------------------
    def complete_sessions(self) -> List[Session]:
        return [s for s in self.sessions if s.is_complete]

    def incomplete_sessions(self) -> List[Session]:
        return [s for s in self.sessions if not s.is_complete]

    def summary_text(self) -> str:
        total = len(self.sessions)
        complete = len(self.complete_sessions())
        incomplete = total - complete
        return (
            f"Sessions saved on device: {total} "
            f"({complete} complete, {incomplete} incomplete)"
        )

    def get(self, session_id: str) -> Optional[Session]:
        for s in self.sessions:
            if s.session_id == session_id:
                return s
        return None

    # ---- mutations --------------------------------------------------------
    def next_session_id(self) -> str:
        """Generate the next auto-incremented session id (e.g. S-0005)."""
        max_num = 0
        for s in self.sessions:
            try:
                num = int(s.session_id.split("-")[1])
            except (IndexError, ValueError):
                continue
            max_num = max(max_num, num)
        return f"S-{max_num + 1:04d}"

    def add_session(self, session: Session) -> None:
        if self.get(session.session_id) is None:
            self.sessions.append(session)
