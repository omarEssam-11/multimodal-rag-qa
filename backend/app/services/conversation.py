"""Bounded conversation history management."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.config import settings


@dataclass
class ConversationMessage:
    role: str  # user | assistant
    content: str
    has_image: bool = False


@dataclass
class Conversation:
    messages: list[ConversationMessage] = field(default_factory=list)

    def add(self, role: str, content: str, has_image: bool = False) -> None:
        self.messages.append(ConversationMessage(role=role, content=content, has_image=has_image))
        self._trim()

    def _trim(self) -> None:
        max_msgs = settings.max_history_messages * 2  # user+assistant pairs
        if len(self.messages) > max_msgs:
            self.messages = self.messages[-max_msgs:]

    def to_list(self) -> list[dict]:
        return [
            {"role": m.role, "content": m.content, "has_image": m.has_image}
            for m in self.messages
        ]

    def clear(self) -> None:
        self.messages.clear()


class ConversationManager:
    """In-memory conversation store keyed by session id."""

    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}

    def get(self, session_id: str) -> Conversation:
        if session_id not in self._conversations:
            self._conversations[session_id] = Conversation()
        return self._conversations[session_id]

    def clear(self, session_id: str) -> None:
        if session_id in self._conversations:
            self._conversations[session_id].clear()


conversation_manager = ConversationManager()
