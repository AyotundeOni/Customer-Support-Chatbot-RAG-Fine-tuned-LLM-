# Shopify Q&A Dataset Generator

Complete scraping solution for building high-quality Q&A datasets from Shopify's official documentation and community support threads.

## 📊 Dataset Overview

**Total Q&A Pairs: 1,521**

- ✅ **1,126** from Official Shopify Documentation
- ✅ **395** from Reddit Community (r/shopify)

**Output File:** `shopify_complete_qa.jsonl`

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Scrapers

**Official Documentation Scraper:**
```bash
python scraper.py
```

**Reddit Community Scraper (No API Keys Required):**
```bash
python reddit_scraper_no_api.py
```

## 📁 Project Files

### Main Scripts

| File | Purpose | Output |
|------|---------|--------|
| `scraper.py` | Scrapes Shopify official help center | `shopify_qa.jsonl` |
| `reddit_scraper_no_api.py` | Scrapes r/shopify using browser automation | `shopify_community_qa.jsonl` |
| `content_cleaner.py` | Shared utilities for cleaning and validating content | - |

### Validation Scripts

| File | Purpose |
|------|---------|
| `validate_output.py` | Validates official docs Q&A format and quality |
| `validate_community_output.py` | Validates community Q&A with confidence metrics |

### Output Files

| File | Description | Size |
|------|-------------|------|
| `shopify_complete_qa.jsonl` | **Combined dataset** (1,521 Q&A pairs) | ~10MB |
| `shopify_qa.jsonl` | Official documentation only (1,126 pairs) | ~9MB |
| `shopify_community_qa.jsonl` | Reddit community only (395 pairs) | ~735KB |

### Documentation

| File | Description |
|------|-------------|
| `README.md` | This file - project overview |
| `BROWSER_SCRAPER_README.md` | Guide for browser-based Reddit scraper |

## 📋 Output Format

Each Q&A pair follows the OpenAI fine-tuning format:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "How do I set up Shopify Payments?"
    },
    {
      "role": "assistant",
      "content": "The step-by-step guide for 'Setting up Shopify Payments' is:..."
    }
  ],
  "metadata": {
    "source_url": "https://help.shopify.com/en/manual/payments/...",
    "platform": "shopify_docs",
    "topic": "Payments",
    "date_scraped": "2025-12-02"
  }
}
```

### Community Q&A Additional Metadata

Reddit entries include extra quality metrics:

```json
{
  "metadata": {
    "platform": "reddit",
    "resolution_type": "official_response",
    "confidence": 0.95,
    "original_score": 42,
    "num_comments": 15,
    ...
  }
}
```

## 🎯 Use Cases

### 1. **LLM Fine-Tuning**
- Direct compatibility with OpenAI, Anthropic, and other LLM fine-tuning APIs
- 1,521 high-quality Q&A pairs covering comprehensive Shopify topics
- Pre-cleaned and formatted data

### 2. **RAG (Retrieval-Augmented Generation)**
- Each entry includes source URLs for citation
- Topic metadata for filtered retrieval
- Confidence scores for quality-based ranking (community data)

### 3. **Chatbot Training**
- Customer support chatbot training data
- Real customer questions from Reddit
- Official Shopify answers from documentation

### 4. **Knowledge Base**
- Searchable knowledge base creation
- FAQ generation
- Support documentation

## 🔍 Data Quality

### Official Documentation (shopify_qa.jsonl)
- ✅ 100% accurate (official source)
- ✅ Comprehensive coverage of all Shopify features
- ✅ Well-structured, step-by-step guides
- ✅ Average answer length: 5,897 characters

### Community Data (shopify_community_qa.jsonl)
- ✅ Real customer questions and issues
- ✅ Multi-strategy solution identification
- ✅ Confidence scores for quality filtering
- ✅ High-confidence entries (≥0.8): ~70%

**Recommended:** For training, filter community data to `confidence >= 0.6`

## 🛠️ How It Works

### Official Docs Scraper

1. **Discovery**: Crawls help.shopify.com/en recursively
2. **Extraction**: Extracts clean content from help articles
3. **Q&A Generation**: Creates natural questions from page titles
4. **Output**: Saves to JSONL in real-time

**Features:**
- Recursive crawling (depth: 5)
- Rate limiting (2s delay)
- Automatic content cleaning
- Progress logging

### Reddit Community Scraper

1. **Search**: Searches r/shopify with 17 keywords
2. **Extract**: Gets post titles, bodies, and comments
3. **Solution ID**: Uses 5 strategies to find best answers:
   - Official Shopify staff responses (0.95 confidence)
   - OP-confirmed solutions (0.9 confidence)
   - High-scored comments (0.6 confidence)
   - OP updates (0.7 confidence)
   - Matched official docs (variable confidence)
4. **Clean**: Removes Reddit formatting, usernames, noise
5. **Output**: Saves with metadata and confidence scores

**No API Keys Required!**
- Uses Selenium browser automation
- Scrapes old.reddit.com
- Works out of the box

## 📈 Statistics

### Topic Coverage

Official docs cover:
- Intro to Shopify, Pricing Plans
- Point of Sale (POS)
- Payments & Processing
- Domains & Hosting
- Themes & Design
- Products & Collections
- Marketing & SEO
- Discounts & Promotions
- International Selling
- Orders & Shipping
- Apps & Integrations
- And 100+ more topics

### Resolution Types (Community Data)

- **Official Response** (95% confidence): Shopify staff answers
- **OP Confirmed** (90% confidence): Solutions confirmed by original poster
- **Upvoted** (60% confidence): Highly-voted community answers
- **OP Update** (70% confidence): Solutions in post edits
- **Matched Docs** (variable): Matched with official documentation

## 🚦 Validation

Validate your scraped data:

```bash
# Validate official docs
python validate_output.py

# Validate community data
python validate_community_output.py
```

## 📦 Dependencies

```
selenium >= 4.15.0
beautifulsoup4 >= 4.12.0
webdriver-manager >= 4.0.0
lxml >= 4.9.0
praw >= 7.7.0  # Optional, only for API-based Reddit scraper
```

## 🎓 Examples

### Load and Use the Data

```python
import json

# Load combined dataset
with open('shopify_complete_qa.jsonl', 'r') as f:
    qa_pairs = [json.loads(line) for line in f]

print(f"Total Q&A pairs: {len(qa_pairs)}")

# Filter high-confidence community answers
high_conf = [
    qa for qa in qa_pairs 
    if qa['metadata'].get('confidence', 1.0) >= 0.8
]

print(f"High-confidence pairs: {len(high_conf)}")
```

### Filter by Topic

```python
# Get all payment-related Q&A
payment_qa = [
    qa for qa in qa_pairs
    if 'payment' in qa['metadata'].get('topic', '').lower()
]
```

## 🤝 Contributing

To extend this project:

1. **Add Twitter Scraper**: Scrape @ShopifySupport threads
2. **Add Forum Scraper**: Scrape community.shopify.com
3. **Add Languages**: Scrape non-English help centers
4. **Improve Cleaning**: Enhance content cleaning logic

## 📝 License

Educational and research purposes. Please respect Shopify's terms of service and robots.txt.

## 🙏 Acknowledgments

- Shopify Help Center for comprehensive documentation
- r/shopify community for real customer insights
- PRAW and Selenium for scraping capabilities

---

**Built for:** Customer Support Chatbot RAG & Fine-tuned LLM Project  
**Date:** December 2025  
**Total Q&A Pairs:** 1,521  
**Ready for:** Fine-tuning, RAG, Chatbots, Knowledge Bases