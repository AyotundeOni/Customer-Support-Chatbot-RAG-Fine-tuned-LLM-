# Browser-Based Reddit Scraper (No API Required)

## Quick Start

Since you don't have Reddit API keys, use the browser-based scraper instead:

```bash
python reddit_scraper_no_api.py
```

**No configuration needed!** It works out of the box.

## What It Does

- Uses Selenium to browse old.reddit.com (like a regular user)
- Searches r/shopify with 17 keywords
- Extracts top 500 Q&A pairs from past year
- No API keys or authentication required
- Same resolution strategies as API version

## How It Works

1. **Searches** old.reddit.com/r/shopify for each keyword
2. **Extracts** ~25 posts per keyword search
3. **Analyzes** each post to find solutions
4. **Identifies** solutions using 5 strategies:
   - Official Shopify staff responses (0.95 confidence)
   - OP-confirmed solutions (0.9 confidence)
   - Highly upvoted comments (0.6 confidence)
   - OP updates/edits (0.7 confidence)
   - Matched official docs (variable confidence)
5. **Cleans** content (removes noise, usernames, formatting)
6. **Saves** to `shopify_community_qa.jsonl`

## Current Progress

✅ **Working!** Currently running and extracting Q&A pairs

Sample output:
```
2025-12-02 23:20:14 - INFO - Found 25 new posts
2025-12-02 23:20:18 - INFO - ✓ Extracted Q&A #1 (conf: 0.95, type: official_response)
2025-12-02 23:20:25 - INFO - ✓ Extracted Q&A #2 (conf: 0.95, type: official_response)
...
```

## Advantages vs API Version

✅ **No API setup required**  
✅ **Works immediately**  
✅ **Same quality output**  
✅ **Same resolution strategies**

## Disadvantages

⚠️ Slower (3s delay between requests vs 0.5s)  
⚠️ More resource-intensive (full browser)  
⚠️ Takes longer to reach 500 pairs

## Validation

After scraping:
```bash
python validate_community_output.py
```

Shows stats on:
- Total Q&A pairs
- Resolution types
- Confidence scores
- Topic distribution

## Output Format

Same as API version - each Q&A pair includes:
```json
{
  "messages": [...],
  "metadata": {
    "platform": "reddit",
    "resolution_type": "official_response",
    "confidence": 0.95,
   ...
  }
}
```

## Tips

- Let it run in the background
- Can take 1-2 hours for full 500 pairs
- Press Ctrl+C to stop early (data is saved)
- Higher confidence scores = better quality

**Perfect for when you don't have time to set up Reddit API!**
