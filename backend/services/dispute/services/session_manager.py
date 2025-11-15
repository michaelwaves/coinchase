"""
Session manager for multi-turn dispute conversations.
"""
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DisputeSession:
    """Represents a dispute analysis session."""
    
    def __init__(self, session_id: str, transaction_id: str):
        self.session_id = session_id
        self.transaction_id = transaction_id
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.step = 0
        self.evidence_collected = []
        self.conversation_history = []
    
    def add_evidence(self, evidence_type: str):
        """Record that evidence was collected."""
        if evidence_type not in self.evidence_collected:
            self.evidence_collected.append(evidence_type)
    
    def increment_step(self):
        """Move to next step."""
        self.step += 1
        self.last_accessed = datetime.utcnow()
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() - self.last_accessed > timedelta(minutes=timeout_minutes)


class SessionManager:
    """Manages active dispute analysis sessions."""
    
    def __init__(self):
        self._sessions: Dict[str, DisputeSession] = {}
        logger.info("SessionManager initialized")
    
    def create_session(self, transaction_id: str) -> DisputeSession:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        session = DisputeSession(session_id, transaction_id)
        self._sessions[session_id] = session
        logger.info(f"Created session: {session_id} for transaction: {transaction_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[DisputeSession]:
        """Get an existing session."""
        session = self._sessions.get(session_id)
        if session:
            if session.is_expired():
                logger.info(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None
            session.last_accessed = datetime.utcnow()
        return session
    
    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        for sid in expired:
            self.delete_session(sid)
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

