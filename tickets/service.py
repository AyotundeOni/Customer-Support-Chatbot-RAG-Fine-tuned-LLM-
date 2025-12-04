"""
Ticket service for CRUD operations.
"""
from datetime import datetime
from typing import Optional
from tickets.database import get_db, close_db, init_db
from tickets.models import Ticket, TicketStatus, TicketPriority


class TicketService:
    """Service for managing support tickets."""
    
    @staticmethod
    def create_ticket(
        problem_summary: str,
        conversation_summary: str = None,
        advice_given: str = None,
        sentiment_score: float = None,
        sentiment_label: str = None,
        session_id: str = None,
        user_email: str = None,
        user_name: str = None
    ) -> Ticket:
        """Create a new support ticket.
        
        Args:
            problem_summary: Brief description of the problem
            conversation_summary: Summary of the conversation
            advice_given: Advice/solutions provided
            sentiment_score: Sentiment score (-1 to 1ish or 0 to 1)
            sentiment_label: Sentiment label (positive/neutral/negative)
            session_id: Session identifier
            user_email: User's email
            user_name: User's name
            
        Returns:
            Created ticket
        """
        # Initialize database if needed
        init_db()
        
        # Determine priority based on sentiment
        priority = TicketService._determine_priority(sentiment_score, sentiment_label)
        
        db = get_db()
        try:
            ticket = Ticket(
                problem_summary=problem_summary,
                conversation_summary=conversation_summary,
                advice_given=advice_given,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                session_id=session_id,
                user_email=user_email,
                user_name=user_name,
                priority=priority,
                status=TicketStatus.OPEN
            )
            
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            
            return ticket
        finally:
            close_db(db)
    
    @staticmethod
    def _determine_priority(
        sentiment_score: float = None, 
        sentiment_label: str = None
    ) -> TicketPriority:
        """Determine ticket priority based on sentiment.
        
        Args:
            sentiment_score: Sentiment score
            sentiment_label: Sentiment label
            
        Returns:
            Appropriate priority level
        """
        if sentiment_label == "negative":
            if sentiment_score and sentiment_score >= 0.8:
                return TicketPriority.URGENT
            return TicketPriority.HIGH
        elif sentiment_label == "neutral":
            return TicketPriority.MEDIUM
        else:
            return TicketPriority.LOW
    
    @staticmethod
    def get_ticket(ticket_id: int) -> Optional[Ticket]:
        """Get a ticket by ID.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Ticket or None if not found
        """
        db = get_db()
        try:
            return db.query(Ticket).filter(Ticket.id == ticket_id).first()
        finally:
            close_db(db)
    
    @staticmethod
    def get_all_tickets(
        status: TicketStatus = None,
        limit: int = 100
    ) -> list[Ticket]:
        """Get all tickets, optionally filtered by status.
        
        Args:
            status: Optional status filter
            limit: Maximum number of tickets to return
            
        Returns:
            List of tickets
        """
        db = get_db()
        try:
            query = db.query(Ticket)
            
            if status:
                query = query.filter(Ticket.status == status)
            
            return query.order_by(Ticket.created_at.desc()).limit(limit).all()
        finally:
            close_db(db)
    
    @staticmethod
    def update_status(ticket_id: int, status: TicketStatus) -> Optional[Ticket]:
        """Update ticket status.
        
        Args:
            ticket_id: Ticket ID
            status: New status
            
        Returns:
            Updated ticket or None
        """
        db = get_db()
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.status = status
                ticket.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(ticket)
            return ticket
        finally:
            close_db(db)
    
    @staticmethod
    def mark_email_sent(ticket_id: int) -> Optional[Ticket]:
        """Mark that email was sent for a ticket.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Updated ticket or None
        """
        db = get_db()
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.email_sent = datetime.utcnow()
                db.commit()
                db.refresh(ticket)
            return ticket
        finally:
            close_db(db)


# Convenience functions
def create_ticket(
    problem_summary: str,
    conversation_summary: str = None,
    advice_given: str = None,
    sentiment_score: float = None,
    **kwargs
) -> Ticket:
    """Create a new ticket."""
    return TicketService.create_ticket(
        problem_summary=problem_summary,
        conversation_summary=conversation_summary,
        advice_given=advice_given,
        sentiment_score=sentiment_score,
        **kwargs
    )


def get_ticket(ticket_id: int) -> Optional[Ticket]:
    """Get a ticket by ID."""
    return TicketService.get_ticket(ticket_id)
