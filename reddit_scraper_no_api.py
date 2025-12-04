"""
Browser-Based Reddit Scraper (No API Required)
Uses Selenium to scrape r/shopify without needing Reddit API credentials
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from content_cleaner import ContentCleaner, OfficialDocsManager, create_qa_entry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrowserRedditScraper:
    """Browser-based Reddit scraper using Selenium (no API required)"""
    
    # Search keywords
    BROAD_KEYWORDS = ['error', 'bug', 'issue', 'problem', 'help', 'broken']
    FEATURE_KEYWORDS = [
        'shipping', 'payment', 'domain', 'theme', 'product', 
        'checkout', 'order', 'tax', 'discount', 'POS', 'refund'
    ]
    
    def __init__(self, output_file: str = "shopify_community_qa.jsonl",
                 official_docs_file: str = "shopify_qa.jsonl", delay: float = 3.0):
        """
        Initialize browser-based Reddit scraper
        
        Args:
            output_file: Output JSONL filename
            official_docs_file: Official docs file for fallback matching
            delay: Delay between requests (seconds)
        """
        self.output_file = output_file
        self.delay = delay
        self.cleaner = ContentCleaner()
        self.docs_manager = OfficialDocsManager(official_docs_file)
        self.qa_count = 0
        self.processed_urls = set()
        
        # Initialize Selenium
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        logger.info(f"Initialized Browser Reddit Scraper (No API Required)")
        logger.info(f"Output file: {output_file}")
        logger.info(f"Delay: {delay}s")
    
    def search_subreddit(self, keyword: str, limit: int = 50) -> List[str]:
        """
        Search r/shopify and return post URLs
        
        Args:
            keyword: Search keyword
            limit: Maximum results
            
        Returns:
            List of post URLs
        """
        logger.info(f"Searching r/shopify for: '{keyword}'")
        
        # Use old.reddit.com for simpler HTML structure
        search_url = f"https://old.reddit.com/r/shopify/search?q={quote(keyword)}&restrict_sr=on&sort=relevance&t=year"
        
        try:
            self.driver.get(search_url)
            time.sleep(self.delay)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all search result divs - use the correct class for old.reddit search results
            post_urls = []
            posts = soup.find_all('div', class_='search-result')
            
            for post in posts[:limit]:
                # Find the comments link
                comments_link = post.find('a', class_='search-comments')
                if comments_link and comments_link.get('href'):
                    full_url = comments_link['href']
                    # Ensure full URL
                    if not full_url.startswith('http'):
                        full_url = f"https://old.reddit.com{full_url}"
                    
                    if full_url not in self.processed_urls:
                        post_urls.append(full_url)
            
            logger.info(f"Found {len(post_urls)} new posts")
            return post_urls
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def extract_post_data(self, url: str) -> Optional[Dict]:
        """
        Extract post title, body, and comments from URL
        
        Args:
            url: Reddit post URL
            
        Returns:
            Dict with post data or None
        """
        try:
            self.driver.get(url)
            time.sleep(self.delay)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract post title
            title_elem = soup.find('a', class_='title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract post body
            body_elem = soup.find('div', class_='usertext-body')
            body = body_elem.get_text(strip=True) if body_elem else ""
            
            # Extract post metadata
            score_elem = soup.find('div', class_='score')
            score_text = score_elem.get_text(strip=True) if score_elem else "0"
            try:
                score = int(score_text.replace('•', '').strip())
            except:
                score = 0
            
            # Check flair
            flair_elem = soup.find('span', class_='linkflairlabel')
            flair = flair_elem.get_text(strip=True) if flair_elem else ""
            
            # Extract comments
            comments = []
            comment_divs = soup.find_all('div', class_='comment')
            
            for comment_div in comment_divs[:50]:  # Top 50 comments
                # Get comment text
                comment_body = comment_div.find('div', class_='md')
                if not comment_body:
                    continue
                
                comment_text = comment_body.get_text(strip=True)
                
                if not comment_text or comment_text in ['[deleted]', '[removed]']:
                    continue
                
                # Get comment score
                score_elem = comment_div.find('span', class_='score')
                if score_elem:
                    score_text = score_elem.get_text(strip=True)
                    try:
                        comment_score = int(score_text.split()[0])
                    except:
                        comment_score = 0
                else:
                    comment_score = 0
                
                # Get author
                author_elem = comment_div.find('a', class_='author')
                author = author_elem.get_text(strip=True) if author_elem else ""
                
                # Check if author is OP
                is_op = 'submitter' in comment_div.get('class', [])
                
                comments.append({
                    'text': comment_text,
                    'score': comment_score,
                    'author': author,
                    'is_op': is_op
                })
            
            return {
                'title': title,
                'body': body,
                'score': score,
                'flair': flair,
                'comments': comments,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error extracting post data from {url}: {e}")
            return None
    
    def identify_solution(self, post_data: Dict) -> Tuple[Optional[str], str, float]:
        """
        Identify best solution from post data
        
        Args:
            post_data: Post data dict
            
        Returns:
            Tuple of (solution_text, resolution_type, confidence)
        """
        # Strategy 1: Check for "Solved" flair
        if post_data.get('flair'):
            flair_lower = post_data['flair'].lower()
            if any(word in flair_lower for word in ['solved', 'answered', 'resolved']):
                # Look for solution in body updates
                if post_data['body'] and len(post_data['body']) > 100:
                    if 'edit:' in post_data['body'].lower() or 'update:' in post_data['body'].lower():
                        return post_data['body'], 'op_update', 0.7
        
        comments = post_data.get('comments', [])
        
        if not comments:
            # No comments, try official docs matching
            question = f"{post_data['title']} {post_data['body']}"
            question_clean = self.cleaner.clean_user_content(question)
            best_match = self.docs_manager.find_best_match(question_clean, threshold=0.3)
            
            if best_match:
                return best_match['answer'], 'matched_docs', best_match['confidence']
            
            return None, 'no_solution', 0.0
        
        # Strategy 2: Look for staff/moderator responses
        for comment in comments:
            author = comment.get('author', '').lower()
            if any(word in author for word in ['shopify', 'mod', 'support']):
                if len(comment['text']) > 50:
                    return comment['text'], 'official_response', 0.95
        
        # Strategy 3: Find OP confirmations
        sorted_comments = sorted(comments, key=lambda x: x['score'], reverse=True)
        
        for comment in sorted_comments:
            if comment['score'] < 2:
                continue
            
            # Check if OP replied positively to this comment
            # (We can't easily detect replies in old.reddit without deeper parsing)
            # So we'll check if comment is from OP with positive words
            if comment.get('is_op'):
                text_lower = comment['text'].lower()
                positive = ['thank', 'worked', 'fixed', 'solved', 'perfect']
                if any(word in text_lower for word in positive):
                    # This OP comment might reference the solution above
                    # For now, use the highest-scored non-OP comment
                    for c in sorted_comments:
                        if not c.get('is_op') and len(c['text']) > 50:
                            return c['text'], 'op_confirmed', 0.9
        
        # Strategy 4: Use highest-scored comment
        if sorted_comments:
            top_comment = sorted_comments[0]
            if top_comment['score'] >= 2 and len(top_comment['text']) > 50:
                return top_comment['text'], 'upvoted', 0.6
        
        # Strategy 5: Fallback to official docs
        question = f"{post_data['title']} {post_data['body']}"
        question_clean = self.cleaner.clean_user_content(question)
        best_match = self.docs_manager.find_best_match(question_clean, threshold=0.3)
        
        if best_match:
            return best_match['answer'], 'matched_docs', best_match['confidence']
        
        return None, 'no_solution', 0.0
    
    def extract_qa_pair(self, url: str) -> Optional[Dict]:
        """
        Extract Q&A pair from a Reddit post URL
        
        Args:
            url: Reddit post URL
            
        Returns:
            Q&A entry dict or None
        """
        if url in self.processed_urls:
            return None
        
        self.processed_urls.add(url)
        
        # Extract post data
        post_data = self.extract_post_data(url)
        if not post_data:
            return None
        
        # Build question
        question_raw = f"{post_data['title']}\n\n{post_data['body']}" if post_data['body'] else post_data['title']
        question_clean = self.cleaner.clean_user_content(question_raw)
        
        # Find solution
        solution_text, resolution_type, confidence = self.identify_solution(post_data)
        
        if not solution_text:
            logger.debug(f"No solution found for: {post_data['title']}")
            return None
        
        # Clean and format answer
        answer_clean = self.cleaner.clean_assistant_content(solution_text)
        answer_formatted = self.cleaner.format_as_answer(answer_clean, add_prefix=True)
        
        # Validate
        is_valid, reason = self.cleaner.is_valid_qa_pair(question_clean, answer_formatted)
        if not is_valid:
            logger.debug(f"Invalid Q&A: {reason}")
            return None
        
        # Create metadata
        metadata = {
            'source_url': url.replace('old.reddit.com', 'reddit.com'),
            'platform': 'reddit',
            'topic': post_data.get('flair', 'General'),
            'resolution_type': resolution_type,
            'confidence': round(confidence, 2),
            'original_score': post_data.get('score', 0),
            'num_comments': len(post_data.get('comments', []))
        }
        
        # Create Q&A entry
        qa_entry = create_qa_entry(question_clean, answer_formatted, metadata)
        
        logger.info(f"✓ Extracted Q&A: {question_clean[:60]}... (conf: {confidence:.2f}, type: {resolution_type})")
        
        return qa_entry
    
    def save_qa_pair(self, qa_entry: Dict):
        """Save Q&A pair to JSONL"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                json_line = json.dumps(qa_entry, ensure_ascii=False)
                f.write(json_line + '\n')
                self.qa_count += 1
            
            logger.info(f"💾 Saved Q&A pair #{self.qa_count}")
            
        except Exception as e:
            logger.error(f"Error saving Q&A: {e}")
    
    def scrape_with_keywords(self, keywords: List[str], posts_per_keyword: int = 30, 
                            total_limit: int = 500):
        """
        Scrape using multiple keywords
        
        Args:
            keywords: Search keywords
            posts_per_keyword: Max posts per keyword
            total_limit: Max total Q&A pairs
        """
        logger.info("=" * 80)
        logger.info("Starting Browser-Based Reddit Scrape (No API Required)")
        logger.info(f"Keywords: {len(keywords)}")
        logger.info(f"Target: {total_limit} Q&A pairs")
        logger.info("=" * 80)
        
        for keyword in keywords:
            if self.qa_count >= total_limit:
                logger.info(f"✓ Reached target of {total_limit} Q&A pairs")
                break
            
            try:
                # Search for posts
                post_urls = self.search_subreddit(keyword, limit=posts_per_keyword)
                
                for url in post_urls:
                    if self.qa_count >= total_limit:
                        break
                    
                    # Extract Q&A
                    qa_entry = self.extract_qa_pair(url)
                    
                    if qa_entry:
                        self.save_qa_pair(qa_entry)
                    
                    # Rate limiting
                    time.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"Error with keyword '{keyword}': {e}")
                continue
        
        logger.info("=" * 80)
        logger.info(f"✓ Scraping complete! Total Q&A pairs: {self.qa_count}")
        logger.info("=" * 80)
    
    def run(self, limit: int = 500):
        """
        Main execution method
        
        Args:
            limit: Max Q&A pairs to extract
        """
        # Combine keywords
        all_keywords = self.BROAD_KEYWORDS + self.FEATURE_KEYWORDS
        
        # Calculate posts per keyword
        posts_per_keyword = max(20, limit // len(all_keywords))
        
        try:
            self.scrape_with_keywords(all_keywords, posts_per_keyword=posts_per_keyword, total_limit=limit)
        finally:
            self.driver.quit()
            logger.info("Browser closed")


def main():
    """Main entry point"""
    scraper = BrowserRedditScraper(
        output_file="shopify_community_qa.jsonl",
        official_docs_file="shopify_qa.jsonl",
        delay=3.0  # 3 second delay to avoid rate limiting
    )
    
    # Run with target of 500 Q&A pairs
    scraper.run(limit=500)


if __name__ == "__main__":
    main()
