"""
Shopify Help Center Web Scraper
Crawls help.shopify.com/en and generates Q&A pairs in JSONL format
"""

import json
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShopifyHelpScraper:
    """Scraper for Shopify Help Center that generates Q&A pairs"""
    
    def __init__(self, base_url: str = "https://help.shopify.com/en", 
                 delay: float = 2.0, output_file: str = "shopify_qa.jsonl"):
        """
        Initialize the scraper
        
        Args:
            base_url: Base URL of the Shopify help center
            delay: Delay between requests in seconds
            output_file: Output JSONL filename
        """
        self.base_url = base_url
        self.delay = delay
        self.output_file = output_file
        self.visited_urls: Set[str] = set()
        self.qa_count = 0
        
        # Initialize Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        logger.info(f"Initialized Shopify Help Scraper")
        logger.info(f"Base URL: {base_url}")
        logger.info(f"Output file: {output_file}")
        logger.info(f"Delay between requests: {delay}s")
    
    def is_valid_help_url(self, url: str) -> bool:
        """Check if URL is within the Shopify help domain"""
        parsed = urlparse(url)
        return (
            parsed.netloc == "help.shopify.com" and
            parsed.path.startswith("/en") and
            url not in self.visited_urls and
            "#" not in url  # Skip anchor links
        )
    
    def discover_topic_links(self, url: str) -> List[str]:
        """
        Discover all help article links from a page
        
        Args:
            url: URL to scrape for links
            
        Returns:
            List of discovered URLs
        """
        links = []
        
        try:
            logger.info(f"Discovering links from: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(2)
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                
                # Add if it's a valid help URL
                if self.is_valid_help_url(href):
                    links.append(href)
            
            logger.info(f"Found {len(links)} new links")
            
        except Exception as e:
            logger.error(f"Error discovering links from {url}: {e}")
        
        return links
    
    def extract_content(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extract main content from a help page
        
        Args:
            url: URL to extract content from
            
        Returns:
            Dictionary with title, content, and topic information
        """
        try:
            logger.info(f"Extracting content from: {url}")
            self.driver.get(url)
            
            # Wait for main content to load
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Extract title
            title = None
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Extract main content - try multiple selectors
            content_text = ""
            
            # Try different content selectors
            content_selectors = [
                {'name': 'main'},
                {'name': 'article'},
                {'class': 'article-content'},
                {'class': 'help-content'},
                {'id': 'content'},
            ]
            
            main_content = None
            for selector in content_selectors:
                main_content = soup.find(**selector)
                if main_content:
                    break
            
            if main_content:
                # Remove unwanted elements
                for unwanted in main_content.find_all(['nav', 'footer', 'script', 'style', 'aside']):
                    unwanted.decompose()
                
                # Extract text from paragraphs, lists, and headings
                content_parts = []
                for elem in main_content.find_all(['p', 'li', 'h2', 'h3', 'h4', 'ol', 'ul']):
                    text = elem.get_text(strip=True)
                    if text and len(text) > 10:  # Filter out very short text
                        content_parts.append(text)
                
                content_text = "\n\n".join(content_parts)
            
            # Extract topic/category from URL path
            path_parts = urlparse(url).path.split('/')
            topic = path_parts[2] if len(path_parts) > 2 else "General"
            
            if not title or not content_text or len(content_text) < 100:
                logger.warning(f"Insufficient content extracted from {url}")
                return None
            
            return {
                'title': title,
                'content': content_text,
                'topic': topic,
                'url': url
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def generate_questions(self, title: str, topic: str) -> List[str]:
        """
        Generate natural language questions based on title and topic
        
        Args:
            title: Page title
            topic: Topic category
            
        Returns:
            List of generated questions
        """
        questions = []
        
        # Clean up title
        title_lower = title.lower()
        
        # Generate different question formats
        if "how to" in title_lower:
            questions.append(title if title.endswith('?') else f"{title}?")
        elif "what" in title_lower or "when" in title_lower or "where" in title_lower or "why" in title_lower:
            questions.append(title if title.endswith('?') else f"{title}?")
        else:
            # Generate questions based on common patterns
            questions.append(f"How do I {title.lower()}?")
            questions.append(f"What are the steps to {title.lower()}?")
        
        # Add topic-specific question
        if topic and topic != "General":
            topic_readable = topic.replace('-', ' ').title()
            questions.append(f"How does {title.lower()} work in {topic_readable}?")
        
        # Return unique questions (take first 2 most relevant)
        return list(dict.fromkeys(questions))[:2]
    
    def generate_qa_pairs(self, content_data: Dict[str, str]) -> List[Dict]:
        """
        Generate Q&A pairs from extracted content
        
        Args:
            content_data: Dictionary containing title, content, topic, url
            
        Returns:
            List of Q&A pair dictionaries in the required format
        """
        qa_pairs = []
        
        title = content_data['title']
        content = content_data['content']
        topic = content_data['topic']
        url = content_data['url']
        
        # Generate questions
        questions = self.generate_questions(title, topic)
        
        # Create Q&A pair for main question
        if questions:
            main_question = questions[0]
            
            # Format assistant response
            assistant_content = f"The step-by-step guide for '{title}' is:\n\n{content}"
            
            qa_pair = {
                "messages": [
                    {"role": "user", "content": main_question},
                    {"role": "assistant", "content": assistant_content}
                ],
                "metadata": {
                    "source_url": url,
                    "topic": topic.replace('-', ' ').title(),
                    "date_scraped": datetime.now().strftime("%Y-%m-%d")
                }
            }
            
            qa_pairs.append(qa_pair)
        
        return qa_pairs
    
    def save_to_jsonl(self, qa_pairs: List[Dict]) -> None:
        """
        Append Q&A pairs to JSONL file
        
        Args:
            qa_pairs: List of Q&A pair dictionaries
        """
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                for qa_pair in qa_pairs:
                    json_line = json.dumps(qa_pair, ensure_ascii=False)
                    f.write(json_line + '\n')
                    self.qa_count += 1
            
            logger.info(f"Saved {len(qa_pairs)} Q&A pairs. Total: {self.qa_count}")
            
        except Exception as e:
            logger.error(f"Error saving to JSONL: {e}")
    
    def crawl_and_extract(self, url: str, max_depth: int = 3, current_depth: int = 0) -> None:
        """
        Recursively crawl and extract content from help pages
        
        Args:
            url: URL to crawl
            max_depth: Maximum depth for recursive crawling
            current_depth: Current depth in the crawl tree
        """
        if url in self.visited_urls or current_depth > max_depth:
            return
        
        self.visited_urls.add(url)
        logger.info(f"Crawling [{len(self.visited_urls)} visited] (depth {current_depth}): {url}")
        
        # Extract content from current page
        content_data = self.extract_content(url)
        
        if content_data:
            # Generate and save Q&A pairs
            qa_pairs = self.generate_qa_pairs(content_data)
            if qa_pairs:
                self.save_to_jsonl(qa_pairs)
        
        # Rate limiting
        time.sleep(self.delay)
        
        # Discover new links and crawl them
        if current_depth < max_depth:
            new_links = self.discover_topic_links(url)
            
            for link in new_links:
                if link not in self.visited_urls:
                    self.crawl_and_extract(link, max_depth, current_depth + 1)
    
    def run(self, max_pages: Optional[int] = None) -> None:
        """
        Main execution method
        
        Args:
            max_pages: Maximum number of pages to scrape (None for unlimited)
        """
        try:
            logger.info("=" * 80)
            logger.info("Starting Shopify Help Center scraper")
            logger.info("=" * 80)
            
            # Start crawling from base URL
            self.crawl_and_extract(self.base_url, max_depth=5)
            
            # Check if we should limit pages
            if max_pages and len(self.visited_urls) >= max_pages:
                logger.info(f"Reached maximum page limit: {max_pages}")
            
            logger.info("=" * 80)
            logger.info(f"Scraping complete!")
            logger.info(f"Total pages visited: {len(self.visited_urls)}")
            logger.info(f"Total Q&A pairs generated: {self.qa_count}")
            logger.info(f"Output file: {self.output_file}")
            logger.info("=" * 80)
            
        except KeyboardInterrupt:
            logger.info("\nScraping interrupted by user")
            logger.info(f"Pages visited so far: {len(self.visited_urls)}")
            logger.info(f"Q&A pairs generated: {self.qa_count}")
        
        finally:
            # Clean up
            self.driver.quit()
            logger.info("WebDriver closed")


def main():
    """Main entry point"""
    # Initialize scraper
    scraper = ShopifyHelpScraper(
        base_url="https://help.shopify.com/en",
        delay=2.0,  # 2 second delay between requests
        output_file="shopify_qa.jsonl"
    )
    
    # Run scraper
    # Set max_pages=10 for testing, or None for full scrape
    scraper.run(max_pages=None)


if __name__ == "__main__":
    main()
