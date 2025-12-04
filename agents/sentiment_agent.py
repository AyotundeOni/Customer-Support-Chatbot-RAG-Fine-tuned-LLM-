"""
Sentiment analysis and routing for customer support.
Uses NLTK VADER for lightweight sentiment analysis (no GPU required).
"""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import config


class SentimentAnalyzer:
    """Analyzes sentiment using VADER (no GPU required)."""
    
    _instance = None
    _analyzer = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the VADER sentiment analyzer."""
        if self._analyzer is None:
            self._analyzer = SentimentIntensityAnalyzer()
    
    def analyze(self, text: str) -> dict:
        """Analyze sentiment of a text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dict with 'label' (positive/neutral/negative), 
            'score' (compound score), and 'all_scores'
        """
        scores = self._analyzer.polarity_scores(text)
        
        # Determine label from compound score
        compound = scores["compound"]
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        
        # Calculate scaled scores for compatibility
        all_scores = {
            "positive": scores["pos"],
            "neutral": scores["neu"],
            "negative": scores["neg"]
        }
        
        return {
            "label": label,
            "score": abs(compound),  # Confidence-like score
            "compound": compound,
            "all_scores": all_scores,
            "is_negative": self._is_negative(compound, scores["neg"])
        }
    
    def _is_negative(self, compound: float, neg_score: float) -> bool:
        """Determine if sentiment should be considered negative.
        
        Args:
            compound: Compound score (-1 to 1)
            neg_score: Negative component score (0 to 1)
            
        Returns:
            True if sentiment is negative enough to escalate
        """
        return compound <= -config.NEGATIVE_THRESHOLD or neg_score >= 0.5


class SentimentRouter:
    """Routes conversations based on sentiment analysis."""
    
    def __init__(self):
        """Initialize the router with sentiment analyzer."""
        self._analyzer = SentimentAnalyzer()
        self._negative_count = 0
        self._history = []
    
    def process_message(self, message: str) -> dict:
        """Process a message and determine routing.
        
        Args:
            message: User's message
            
        Returns:
            Dict with routing decision and sentiment info
        """
        sentiment = self._analyzer.analyze(message)
        self._history.append(sentiment)
        
        if sentiment["is_negative"]:
            self._negative_count += 1
        
        # Determine if escalation is needed
        should_escalate = (
            sentiment["is_negative"] and 
            self._negative_count >= config.ESCALATION_COUNT
        )
        
        # Offer ticket on first negative (but don't force escalate)
        offer_ticket = sentiment["is_negative"] and self._negative_count == 1
        
        return {
            "sentiment": sentiment,
            "action": self._determine_action(sentiment, should_escalate, offer_ticket),
            "should_offer_ticket": offer_ticket,
            "should_escalate": should_escalate,
            "negative_count": self._negative_count,
            "message": self._get_routing_message(sentiment, should_escalate, offer_ticket)
        }
    
    def _determine_action(
        self, 
        sentiment: dict, 
        escalate: bool, 
        offer_ticket: bool
    ) -> str:
        """Determine the action to take based on sentiment.
        
        Returns:
            One of: 'continue', 'offer_ticket', 'escalate'
        """
        if escalate:
            return "escalate"
        elif offer_ticket:
            return "offer_ticket"
        else:
            return "continue"
    
    def _get_routing_message(
        self, 
        sentiment: dict, 
        escalate: bool, 
        offer_ticket: bool
    ) -> str:
        """Get a message to show based on routing decision."""
        if escalate:
            return (
                "I understand you're frustrated, and I'm sorry the assistance "
                "hasn't been helpful. Let me create a support ticket so our team "
                "can help you personally."
            )
        elif offer_ticket:
            return (
                "I sense this might be frustrating. Would you like me to create "
                "a support ticket so a human agent can assist you directly?"
            )
        else:
            return None
    
    def reset(self):
        """Reset the router for a new conversation."""
        self._negative_count = 0
        self._history = []
    
    def get_average_sentiment(self) -> dict:
        """Get the average sentiment across the conversation.
        
        Returns:
            Dict with average scores for each sentiment label
        """
        if not self._history:
            return {"positive": 0, "neutral": 0, "negative": 0}
        
        totals = {"positive": 0, "neutral": 0, "negative": 0}
        count = len(self._history)
        
        for sentiment in self._history:
            for label, score in sentiment["all_scores"].items():
                if label in totals:
                    totals[label] += score
        
        return {k: v / count for k, v in totals.items()}


# Convenience function
def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Sentiment analysis result
    """
    analyzer = SentimentAnalyzer()
    return analyzer.analyze(text)
