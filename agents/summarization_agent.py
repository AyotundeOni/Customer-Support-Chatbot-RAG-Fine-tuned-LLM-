"""
Conversation summarization for ticket creation.
Extracts key information from conversations for support tickets.
"""
import google.generativeai as genai
from config import config


class ConversationSummarizer:
    """Summarizes conversations for support tickets using Gemini."""
    
    _model = None
    
    def __init__(self):
        """Initialize the summarizer with Gemini."""
        if ConversationSummarizer._model is None:
            genai.configure(api_key=config.GOOGLE_API_KEY)
            ConversationSummarizer._model = genai.GenerativeModel('gemini-2.5-flash')
    
    def summarize(self, messages: list) -> dict:
        """Summarize a conversation for a support ticket.
        
        Args:
            messages: List of conversation messages with 'role' and 'content'
            
        Returns:
            Dict with 'problem_summary', 'advice_given', 'conversation_summary'
        """
        if not messages:
            return {
                "problem_summary": "Customer support request",
                "advice_given": "No advice recorded",
                "conversation_summary": "No conversation history"
            }
        
        # Format the conversation
        formatted = self._format_conversation(messages)
        
        # Generate summaries using Gemini
        prompt = f"""Analyze this customer support conversation and provide a structured summary:

CONVERSATION:
{formatted}

Please provide:
1. PROBLEM SUMMARY: A brief description of the customer's main issue (1-2 sentences)
2. ADVICE GIVEN: What solutions or guidance was provided by the assistant (bullet points)
3. CONVERSATION SUMMARY: A brief overview of the entire conversation (2-3 sentences)

Format your response exactly as:
PROBLEM SUMMARY: [your summary]
ADVICE GIVEN: [your bullet points]
CONVERSATION SUMMARY: [your summary]"""
        
        try:
            response = self._model.generate_content(prompt)
            return self._parse_summary(response.text, messages)
        except Exception as e:
            print(f"Error generating summary: {e}")
            return self._fallback_summary(messages)
    
    def _format_conversation(self, messages: list) -> str:
        """Format messages into a readable conversation."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")[:500]  # Limit length
            formatted.append(f"{role}: {content}")
        return "\n\n".join(formatted[-10:])  # Last 10 messages
    
    def _parse_summary(self, response: str, messages: list) -> dict:
        """Parse the LLM response into structured fields."""
        result = {
            "problem_summary": "",
            "advice_given": "",
            "conversation_summary": ""
        }
        
        try:
            lines = response.split("\n")
            current_field = None
            current_content = []
            
            for line in lines:
                line_lower = line.lower().strip()
                
                if line_lower.startswith("problem summary:"):
                    if current_field:
                        result[current_field] = " ".join(current_content).strip()
                    current_field = "problem_summary"
                    current_content = [line.split(":", 1)[1].strip() if ":" in line else ""]
                elif line_lower.startswith("advice given:"):
                    if current_field:
                        result[current_field] = " ".join(current_content).strip()
                    current_field = "advice_given"
                    current_content = [line.split(":", 1)[1].strip() if ":" in line else ""]
                elif line_lower.startswith("conversation summary:"):
                    if current_field:
                        result[current_field] = " ".join(current_content).strip()
                    current_field = "conversation_summary"
                    current_content = [line.split(":", 1)[1].strip() if ":" in line else ""]
                elif current_field and line.strip():
                    current_content.append(line.strip())
            
            if current_field:
                result[current_field] = " ".join(current_content).strip()
                
        except Exception as e:
            print(f"Error parsing summary: {e}")
        
        # Fallback if parsing failed
        if not result["problem_summary"]:
            result = self._fallback_summary(messages)
        
        return result
    
    def _fallback_summary(self, messages: list) -> dict:
        """Generate a basic summary without LLM."""
        user_messages = [
            msg["content"] for msg in messages 
            if msg.get("role") == "user"
        ]
        
        problem = user_messages[0][:300] if user_messages else "Customer needs assistance"
        
        return {
            "problem_summary": problem,
            "advice_given": "See conversation history for details",
            "conversation_summary": f"Customer conversation with {len(messages)} messages"
        }


def summarize_conversation(messages: list) -> dict:
    """Summarize a conversation for a ticket.
    
    Args:
        messages: Conversation messages
        
    Returns:
        Summary dict
    """
    summarizer = ConversationSummarizer()
    return summarizer.summarize(messages)
