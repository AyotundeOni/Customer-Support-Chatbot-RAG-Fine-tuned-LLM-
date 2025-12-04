"""
Content Cleaning Utilities for Community Scraper
Shared functions for cleaning and processing user/assistant content
"""

import re
import json
from typing import Optional, Dict, List, Tuple
from datetime import datetime


class ContentCleaner:
    """Utilities for cleaning community content"""
    
    # Patterns to remove from user content
    USER_NOISE_PATTERNS = [
        r'^(hi|hello|hey|dear)\s+[\w@]+[,!.\s]*',  # Greetings with usernames
        r'thanks?\s+in\s+advance[!.]*',  # "thanks in advance"
        r'(any|please)\s+help[!.]*$',  # "please help"
        r'u/\w+',  # Reddit usernames
        r'@\w+',  # @ mentions
        r'\*\*(edit|update):\*\*.*$',  # Edit annotations
        r'^\s*edit\s*:.*$',  # Edit lines
        r'tldr:.*$',  # TLDR sections
    ]
    
    # Patterns to clean from both
    COMMON_PATTERNS = [
        r'\[deleted\]',
        r'\[removed\]',
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
    ]
    
    @staticmethod
    def clean_user_content(text: str) -> str:
        """
        Clean noise from user questions
        
        Args:
            text: Raw user text
            
        Returns:
            Cleaned question text
        """
        if not text:
            return ""
        
        # Remove Reddit markdown
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
        text = re.sub(r'~~(.+?)~~', r'\1', text)  # Strikethrough
        
        # Apply user-specific noise patterns
        for pattern in ContentCleaner.USER_NOISE_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Apply common patterns
        for pattern in ContentCleaner.COMMON_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_assistant_content(text: str) -> str:
        """
        Clean and format assistant responses
        
        Args:
            text: Raw assistant text
            
        Returns:
            Cleaned, formatted response
        """
        if not text:
            return ""
        
        # Remove Reddit markdown (preserve structure)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        
        # Apply common patterns
        for pattern in ContentCleaner.COMMON_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove "Edit:" annotations
        text = re.sub(r'^\s*edit\s*:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_steps(text: str) -> Optional[List[str]]:
        """
        Extract numbered or bulleted steps from text
        
        Args:
            text: Text potentially containing steps
            
        Returns:
            List of step strings, or None if no steps found
        """
        # Try numbered steps
        numbered_pattern = r'^\s*\d+[\.)]\s+(.+)$'
        numbered_steps = re.findall(numbered_pattern, text, re.MULTILINE)
        
        if numbered_steps and len(numbered_steps) >= 2:
            return numbered_steps
        
        # Try bulleted steps
        bullet_pattern = r'^\s*[-*•]\s+(.+)$'
        bullet_steps = re.findall(bullet_pattern, text, re.MULTILINE)
        
        if bullet_steps and len(bullet_steps) >= 2:
            return bullet_steps
        
        return None
    
    @staticmethod
    def format_as_answer(text: str, add_prefix: bool = True) -> str:
        """
        Format cleaned text as a proper answer
        
        Args:
            text: Cleaned text
            add_prefix: Whether to add "Here's how to..." prefix
            
        Returns:
            Formatted answer
        """
        if not text:
            return ""
        
        # Check if already has a helpful opening
        has_opening = any(text.lower().startswith(phrase) for phrase in [
            'here', 'you can', 'to solve', 'try', 'follow these', 'the solution'
        ])
        
        if add_prefix and not has_opening:
            # Extract steps if present
            steps = ContentCleaner.extract_steps(text)
            if steps:
                return f"Here's how to resolve this issue:\n\n{text}"
            else:
                return f"Here's the solution:\n\n{text}"
        
        return text
    
    @staticmethod
    def is_valid_qa_pair(question: str, answer: str, min_question_len: int = 20, 
                        min_answer_len: int = 50) -> Tuple[bool, str]:
        """
        Validate if question and answer meet quality standards
        
        Args:
            question: Cleaned question text
            answer: Cleaned answer text
            min_question_len: Minimum question length
            min_answer_len: Minimum answer length
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if not question or not answer:
            return False, "Empty question or answer"
        
        if len(question) < min_question_len:
            return False, f"Question too short (<{min_question_len} chars)"
        
        if len(answer) < min_answer_len:
            return False, f"Answer too short (<{min_answer_len} chars)"
        
        # Check if question is actually a question
        question_indicators = ['?', 'how', 'what', 'why', 'when', 'where', 'can', 'does', 'is', 'help', 'issue', 'problem']
        has_indicator = any(indicator in question.lower() for indicator in question_indicators)
        
        if not has_indicator:
            return False, "Question doesn't appear to be a question"
        
        # Check answer quality
        if answer.lower().count('i don\'t know') > 0 or answer.lower().count('not sure') > 1:
            return False, "Answer appears uncertain"
        
        return True, "Valid"
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        Calculate simple keyword-based similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple keyword overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class OfficialDocsManager:
    """Manager for matching with official documentation"""
    
    def __init__(self, docs_file: str = "shopify_qa.jsonl"):
        """
        Initialize with official docs file
        
        Args:
            docs_file: Path to official docs JSONL file
        """
        self.docs_file = docs_file
        self.docs_cache = []
        self._load_docs()
    
    def _load_docs(self):
        """Load official docs into memory"""
        try:
            with open(self.docs_file, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = json.loads(line)
                    if 'messages' in entry and len(entry['messages']) >= 2:
                        self.docs_cache.append({
                            'question': entry['messages'][0].get('content', ''),
                            'answer': entry['messages'][1].get('content', ''),
                            'url': entry.get('metadata', {}).get('source_url', '')
                        })
        except FileNotFoundError:
            print(f"Warning: Official docs file '{self.docs_file}' not found")
    
    def find_best_match(self, question: str, threshold: float = 0.3) -> Optional[Dict]:
        """
        Find best matching official doc for a question
        
        Args:
            question: Question to match
            threshold: Minimum similarity threshold
            
        Returns:
            Best matching doc dict or None
        """
        if not self.docs_cache:
            return None
        
        best_match = None
        best_score = 0.0
        
        for doc in self.docs_cache:
            # Calculate similarity with both question and answer
            q_similarity = ContentCleaner.calculate_similarity(question, doc['question'])
            a_similarity = ContentCleaner.calculate_similarity(question, doc['answer'])
            
            # Take the better of the two
            score = max(q_similarity, a_similarity * 0.7)  # Slight preference for question match
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = {**doc, 'confidence': score}
        
        return best_match


def create_qa_entry(question: str, answer: str, metadata: Dict) -> Dict:
    """
    Create a properly formatted Q&A entry
    
    Args:
        question: Cleaned question
        answer: Cleaned answer
        metadata: Metadata dict
        
    Returns:
        Formatted Q&A entry
    """
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ],
        "metadata": {
            **metadata,
            "date_scraped": datetime.now().strftime("%Y-%m-%d")
        }
    }
