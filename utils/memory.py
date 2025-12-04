"""
Conversation memory management for the chatbot.
Uses a sliding window to keep recent messages in context.
"""
from config import config


class ConversationMemory:
    """Manages conversation history with a sliding window."""
    
    def __init__(self, window_size: int = None):
        """Initialize memory with optional custom window size.
        
        Args:
            window_size: Number of message pairs to keep (default from config)
        """
        self._window_size = window_size or config.MEMORY_WINDOW_SIZE
        self._messages: list[dict] = []
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history.
        
        Args:
            role: Either 'user' or 'assistant'
            content: The message content
        """
        self._messages.append({
            "role": role,
            "content": content
        })
        
        # Trim if exceeding window size (keep 2x window for pairs)
        max_messages = self._window_size * 2
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]
    
    def get_messages(self) -> list[dict]:
        """Get all messages in the current window.
        
        Returns:
            List of message dicts with 'role' and 'content'
        """
        return self._messages.copy()
    
    def get_formatted_history(self) -> str:
        """Get history formatted as a string for prompts.
        
        Returns:
            Formatted conversation history
        """
        if not self._messages:
            return ""
        
        formatted = []
        for msg in self._messages:
            role = msg["role"].capitalize()
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def clear(self):
        """Clear all conversation history."""
        self._messages = []
    
    def get_user_messages(self) -> list[str]:
        """Get only user messages.
        
        Returns:
            List of user message contents
        """
        return [
            msg["content"] for msg in self._messages 
            if msg["role"] == "user"
        ]
    
    def get_last_n_messages(self, n: int) -> list[dict]:
        """Get the last n messages.
        
        Args:
            n: Number of messages to retrieve
            
        Returns:
            List of last n messages
        """
        return self._messages[-n:] if self._messages else []
    
    def __len__(self) -> int:
        """Return number of messages in memory."""
        return len(self._messages)
