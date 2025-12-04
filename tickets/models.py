"""
SQLAlchemy models for the ticket system.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Enum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()


class TicketStatus(enum.Enum):
    """Ticket status enum."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(enum.Enum):
    """Ticket priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base):
    """Support ticket model."""
    
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Session tracking
    session_id = Column(String(100), nullable=True)
    
    # User info (optional)
    user_email = Column(String(255), nullable=True)
    user_name = Column(String(255), nullable=True)
    
    # Ticket content
    problem_summary = Column(Text, nullable=False)
    conversation_summary = Column(Text, nullable=True)
    advice_given = Column(Text, nullable=True)
    
    # Sentiment data
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    sentiment_label = Column(String(50), nullable=True)  # positive/neutral/negative
    
    # Status and priority
    status = Column(
        Enum(TicketStatus), 
        default=TicketStatus.OPEN, 
        nullable=False
    )
    priority = Column(
        Enum(TicketPriority), 
        default=TicketPriority.MEDIUM, 
        nullable=False
    )
    
    # Email tracking
    email_sent = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Ticket {self.id}: {self.problem_summary[:50]}...>"
    
    def to_dict(self) -> dict:
        """Convert ticket to dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "session_id": self.session_id,
            "user_email": self.user_email,
            "problem_summary": self.problem_summary,
            "conversation_summary": self.conversation_summary,
            "advice_given": self.advice_given,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "email_sent": self.email_sent.isoformat() if self.email_sent else None
        }
