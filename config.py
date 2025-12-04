"""
Configuration management for the Customer Support Chatbot.
Loads settings from environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "shopify-support")
    PINECONE_DIMENSION: int = 384  # Dimension for all-MiniLM-L6-v2 embeddings
    
    # Google Gemini
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # HuggingFace (for embeddings)
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL_ID: str = os.getenv("HUGGINGFACE_MODEL_ID", "AyotundeOni/shopify_qa")
    
    # Embedding model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Sentiment model (not used - using VADER instead)
    SENTIMENT_MODEL: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    
    # Gmail SMTP
    GMAIL_EMAIL: str = os.getenv("GMAIL_EMAIL", "")
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", "")
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "")
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///tickets.db")
    
    # Conversation memory
    MEMORY_WINDOW_SIZE: int = 10  # Number of messages to keep in memory
    
    # Sentiment thresholds
    NEGATIVE_THRESHOLD: float = 0.6  # Score above this is considered negative
    ESCALATION_COUNT: int = 2  # Number of negative messages before auto-escalation
    
    # RAG settings
    RAG_TOP_K: int = 3  # Number of similar documents to retrieve
    
    @classmethod
    def validate(cls) -> list:
        """Validate that all required configuration is present."""
        errors = []
        if not cls.PINECONE_API_KEY:
            errors.append("PINECONE_API_KEY is not set")
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is not set")
        if not cls.HUGGINGFACE_API_KEY:
            errors.append("HUGGINGFACE_API_KEY is not set (needed for embeddings)")
        if not cls.GMAIL_EMAIL:
            errors.append("GMAIL_EMAIL is not set")
        if not cls.GMAIL_APP_PASSWORD:
            errors.append("GMAIL_APP_PASSWORD is not set")
        return errors


# Singleton instance
config = Config()
