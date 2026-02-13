from datetime import datetime, timezone
from typing import Optional

from app.models.schemas import ChatMessage, SessionReport, SessionResponse, SessionStatus


class SessionStore:
    """In-memory session storage. Replace with a DB adapter for production."""

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def create(
        self,
        session_id: str,
        video_filename: str,
        surfer_name: str | None,
        skill_level: str | None,
    ) -> SessionResponse:
        record = {
            "session_id": session_id,
            "status": SessionStatus.PENDING,
            "created_at": datetime.now(timezone.utc),
            "video_filename": video_filename,
            "surfer_name": surfer_name,
            "skill_level": skill_level,
            "report": None,
            "error_message": None,
            "chat_history": [],
        }
        self._sessions[session_id] = record
        return SessionResponse(
            session_id=record["session_id"],
            status=record["status"],
            created_at=record["created_at"],
            video_filename=record["video_filename"],
            surfer_name=record["surfer_name"],
            skill_level=record["skill_level"],
        )

    def update_status(
        self, session_id: str, status: SessionStatus, error_message: str | None = None
    ):
        if session_id in self._sessions:
            self._sessions[session_id]["status"] = status
            if error_message:
                self._sessions[session_id]["error_message"] = error_message

    def save_report(self, session_id: str, report: SessionReport):
        if session_id in self._sessions:
            self._sessions[session_id]["report"] = report
            self._sessions[session_id]["status"] = SessionStatus.COMPLETED

    def append_chat(
        self, session_id: str, user_message: str, assistant_reply: str
    ) -> None:
        """Store a user/assistant message pair in the session's chat history."""
        if session_id not in self._sessions:
            return
        now = datetime.now(timezone.utc)
        self._sessions[session_id]["chat_history"].extend([
            ChatMessage(role="user", content=user_message, timestamp=now),
            ChatMessage(role="assistant", content=assistant_reply, timestamp=now),
        ])

    def get_chat_history(self, session_id: str) -> list[ChatMessage]:
        """Return the chat history for a session."""
        record = self._sessions.get(session_id)
        if not record:
            return []
        return list(record.get("chat_history", []))

    def get(self, session_id: str) -> Optional[dict]:
        return self._sessions.get(session_id)
