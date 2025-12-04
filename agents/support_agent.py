"""
Main customer support agent that orchestrates RAG, LLM, sentiment, and ticket creation.
Handles function calls from Gemini to create actual tickets.
"""
from agents.sentiment_agent import SentimentRouter
from agents.summarization_agent import summarize_conversation
from llm import GeminiLLM
from rag.vector_store import get_context_for_query
from tickets.service import TicketService
from tickets.email_service import send_ticket_email
from utils.memory import ConversationMemory


class SupportAgent:
    """Customer support agent with RAG, sentiment routing, and ticket creation."""
    
    def __init__(self, session_id: str = None):
        """Initialize the support agent."""
        self.session_id = session_id
        self._llm = GeminiLLM()
        self._memory = ConversationMemory()
        self._sentiment_router = SentimentRouter()
        self._ticket_offered = False
        self._escalated = False
        self._created_ticket_ids = []
    
    def chat(self, user_message: str) -> dict:
        """Process a user message and generate a response.
        
        Args:
            user_message: The user's message
            
        Returns:
            Dict with 'response', 'sentiment', routing info, and ticket info
        """
        # Add user message to memory
        self._memory.add_message("user", user_message)
        
        # Analyze sentiment
        routing = self._sentiment_router.process_message(user_message)
        
        # Get RAG context
        context = get_context_for_query(user_message)
        
        # Generate response (may include function call)
        history = self._memory.get_messages()[:-1]
        llm_result = self._llm.generate_with_context(
            query=user_message,
            context=context,
            conversation_history=history
        )
        
        # Handle function calls
        ticket_created = None
        if llm_result.get("function_call") == "create_support_ticket":
            ticket_created = self._handle_ticket_creation(llm_result["function_args"])
            response = ticket_created["message"]
        else:
            response = llm_result.get("text", "I apologize, I had trouble generating a response.")
        
        # Also check sentiment-based escalation
        if routing["should_escalate"] and not self._escalated and not ticket_created:
            self._escalated = True
            # Auto-create ticket on escalation
            ticket_created = self._create_escalation_ticket()
            response = f"{response}\n\n{ticket_created['message']}"
        
        # Add assistant response to memory
        self._memory.add_message("assistant", response)
        
        return {
            "response": response,
            "sentiment": routing["sentiment"],
            "action": routing["action"],
            "should_offer_ticket": routing["should_offer_ticket"] and not self._ticket_offered,
            "should_escalate": routing["should_escalate"],
            "routing_message": routing["message"],
            "ticket_created": ticket_created
        }
    
    def _handle_ticket_creation(self, args: dict) -> dict:
        """Handle the create_support_ticket function call.
        
        Args:
            args: Function arguments from LLM
            
        Returns:
            Dict with ticket info and confirmation message
        """
        problem_summary = args.get("problem_summary", "Customer needs assistance")
        urgency = args.get("urgency", "medium")
        
        # Get conversation summary
        messages = self._memory.get_messages()
        summary = summarize_conversation(messages)
        
        # Map urgency to sentiment
        sentiment_map = {
            "urgent": ("negative", 0.9),
            "high": ("negative", 0.7),
            "medium": ("neutral", 0.5),
            "low": ("positive", 0.3)
        }
        sentiment_label, sentiment_score = sentiment_map.get(urgency, ("neutral", 0.5))
        
        # Create the ticket
        ticket = TicketService.create_ticket(
            problem_summary=problem_summary,
            conversation_summary=summary.get("conversation_summary"),
            advice_given=summary.get("advice_given"),
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            session_id=self.session_id
        )
        
        self._created_ticket_ids.append(ticket.id)
        self._ticket_offered = True
        
        # Send email notification
        email_sent = send_ticket_email(ticket)
        if email_sent:
            TicketService.mark_email_sent(ticket.id)
        
        # Generate confirmation
        confirmation = self._llm.generate_ticket_confirmation(ticket.id, problem_summary)
        
        return {
            "ticket_id": ticket.id,
            "problem_summary": problem_summary,
            "priority": ticket.priority.value if ticket.priority else "medium",
            "email_sent": email_sent,
            "message": confirmation
        }
    
    def _create_escalation_ticket(self) -> dict:
        """Create a ticket due to sentiment escalation."""
        messages = self._memory.get_messages()
        summary = summarize_conversation(messages)
        
        ticket = TicketService.create_ticket(
            problem_summary=summary.get("problem_summary", "Customer needs human assistance"),
            conversation_summary=summary.get("conversation_summary"),
            advice_given=summary.get("advice_given"),
            sentiment_score=0.8,
            sentiment_label="negative",
            session_id=self.session_id
        )
        
        self._created_ticket_ids.append(ticket.id)
        
        email_sent = send_ticket_email(ticket)
        if email_sent:
            TicketService.mark_email_sent(ticket.id)
        
        return {
            "ticket_id": ticket.id,
            "message": f"I've created support ticket #{ticket.id} for you. Our team will contact you shortly!",
            "email_sent": email_sent
        }
    
    def create_manual_ticket(self, user_email: str = None) -> dict:
        """Manually create a ticket (e.g., from UI button).
        
        Args:
            user_email: Optional user email
            
        Returns:
            Dict with ticket info
        """
        messages = self._memory.get_messages()
        summary = summarize_conversation(messages)
        sentiment_summary = self._sentiment_router.get_average_sentiment()
        
        negative_score = sentiment_summary.get("negative", 0)
        if negative_score > 0.5:
            sentiment_label = "negative"
        elif negative_score > 0.3:
            sentiment_label = "neutral"
        else:
            sentiment_label = "positive"
        
        ticket = TicketService.create_ticket(
            problem_summary=summary.get("problem_summary", "Customer support request"),
            conversation_summary=summary.get("conversation_summary"),
            advice_given=summary.get("advice_given"),
            sentiment_score=negative_score,
            sentiment_label=sentiment_label,
            session_id=self.session_id,
            user_email=user_email
        )
        
        self._created_ticket_ids.append(ticket.id)
        self._ticket_offered = True
        
        email_sent = send_ticket_email(ticket)
        if email_sent:
            TicketService.mark_email_sent(ticket.id)
        
        return {
            "ticket_id": ticket.id,
            "priority": ticket.priority.value if ticket.priority else "medium",
            "email_sent": email_sent
        }
    
    def get_conversation_history(self) -> list:
        """Get the full conversation history."""
        return self._memory.get_messages()
    
    def get_sentiment_summary(self) -> dict:
        """Get sentiment summary for the conversation."""
        return self._sentiment_router.get_average_sentiment()
    
    def get_created_tickets(self) -> list:
        """Get list of ticket IDs created in this session."""
        return self._created_ticket_ids
    
    def reset(self):
        """Reset the agent for a new conversation."""
        self._memory.clear()
        self._sentiment_router.reset()
        self._ticket_offered = False
        self._escalated = False
        self._created_ticket_ids = []
    
    def is_escalated(self) -> bool:
        """Check if the conversation has been escalated."""
        return self._escalated
