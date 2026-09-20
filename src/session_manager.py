"""
src/session_manager.py — Phase 3 & 4
In-memory multi-turn session management for WhatsApp farmers.

Preserves conversational state across messages from the same phone number:
  • Farmer's name, district, crop, and variety
  • Recent conversation history (last 6 turns)
  • Allows follow-up questions ("aur paani kab lagana hai?") without re-specifying crop
  • Supports session reset keywords ("reset", "shuru", "restart")
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ConversationTurn:
    role: str  # "farmer" or "kisan_mitra"
    text: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class FarmerSession:
    phone_number: str
    farmer_name: Optional[str] = None
    district: str = "Ludhiana"
    crop: Optional[str] = None
    variety: Optional[str] = None
    growth_stage: Optional[str] = None
    turns: List[ConversationTurn] = field(default_factory=list)
    last_active: float = field(default_factory=time.time)

    def add_turn(self, role: str, text: str):
        self.turns.append(ConversationTurn(role=role, text=text))
        # Keep only the last 6 turns to avoid context overflow
        if len(self.turns) > 6:
            self.turns = self.turns[-6:]
        self.last_active = time.time()

    def get_conversation_context(self) -> str:
        """Format recent conversation history for prompt injection."""
        if not self.turns:
            return ""

        lines = ["\nRECENT CONVERSATION HISTORY WITH THIS FARMER:"]
        for turn in self.turns[:-1]:  # Exclude current message
            prefix = "Farmer" if turn.role == "farmer" else "Kisan Mitra"
            # Truncate lengthy assistant replies to 150 chars for prompt brevity
            text_snippet = turn.text[:200] + "..." if len(turn.text) > 200 else turn.text
            lines.append(f"- {prefix}: {text_snippet}")

        return "\n".join(lines)


class SessionManager:
    """Manages active sessions for WhatsApp senders."""

    def __init__(self, session_timeout_seconds: int = 7200):
        # 2 hours session timeout
        self.timeout = session_timeout_seconds
        self.sessions: Dict[str, FarmerSession] = {}

    def get_or_create(self, phone_number: str, profile_name: Optional[str] = None) -> FarmerSession:
        now = time.time()
        # Check if session exists and is not expired
        if phone_number in self.sessions:
            session = self.sessions[phone_number]
            if now - session.last_active < self.timeout:
                if profile_name and not session.farmer_name:
                    session.farmer_name = profile_name
                return session

        # New or expired session
        new_session = FarmerSession(
            phone_number=phone_number,
            farmer_name=profile_name,
            district="Ludhiana",
        )
        self.sessions[phone_number] = new_session
        return new_session

    def reset(self, phone_number: str) -> None:
        if phone_number in self.sessions:
            del self.sessions[phone_number]

    def update_profile(
        self,
        session: FarmerSession,
        crop: Optional[str] = None,
        district: Optional[str] = None,
    ):
        if crop:
            session.crop = crop
        if district:
            session.district = district
        session.last_active = time.time()


# Global singleton instance
session_manager = SessionManager()
