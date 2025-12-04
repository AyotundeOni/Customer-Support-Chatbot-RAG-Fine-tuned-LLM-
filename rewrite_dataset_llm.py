import google.generativeai as genai
import json
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
API_KEY = "AIzaSyCHqU7dgZglpLQbDF-9LCXBw30_NJkoDF0" # User provided key
INPUT_FILE = "shopify_complete_qa.jsonl"
OUTPUT_FILE = "shopify_llm_rewritten_qa.jsonl"
MODEL_NAME = "gemini-2.5-flash" 

# Configure Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

def rewrite_entry(question, answer, retries=3):
    """Rewrites both question and answer using Gemini API."""
    prompt = f"""
    You are an expert customer support agent for Shopify. 
    Rewrite the following Q&A pair to be high-quality training data.
    
    Guidelines for Question:
    1. Make it sound like a real user asking a natural question.
    2. AVOID starting with "How do I" if possible. Use variety: "Can I...", "What's the best way to...", "I need help with...", or just a direct question.
    3. Keep it specific to the topic.
    
    Guidelines for Answer:
    1. Remove boilerplate ("In this section", "The following features").
    2. Fix spacing errors (e.g., "useShopify" -> "use Shopify").
    3. Be friendly, concise, and helpful.
    4. Do not invent new info.
    
    Original Question: {question}
    Original Answer: {answer}
    
    Output JSON ONLY:
    {{
        "question": "rewritten question",
        "answer": "rewritten answer"
    }}
    """
    
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            if "429" in str(e): # Rate limit
                wait_time = (2 ** attempt) + 1
                print(f"Rate limit hit. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Error rewriting: {e}")
                return {"question": question, "answer": answer} # Return original if failed
    return {"question": question, "answer": answer}

def process_line(line, index):
    try:
        data = json.loads(line)
        messages = data.get('messages', [])
        
        user_msg = next((m for m in messages if m['role'] == 'user'), None)
        assistant_msg = next((m for m in messages if m['role'] == 'assistant'), None)
        
        if user_msg and assistant_msg:
            # Skip if content is very short (likely already fine or just a link)
            if len(assistant_msg['content']) < 50:
                return json.dumps(data)

            rewritten = rewrite_entry(user_msg['content'], assistant_msg['content'])
            
            user_msg['content'] = rewritten['question']
            assistant_msg['content'] = rewritten['answer']
        
        return json.dumps(data)
    except json.JSONDecodeError:
        return None

def main():
    print(f"Starting LLM rewrite using {MODEL_NAME}...")
    
    # Read all lines first
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total = len(lines)
    print(f"Found {total} entries to process.")
    
    # Process in parallel (careful with rate limits)
    # Using a small number of workers to avoid hitting rate limits too hard
    # Flash model has decent limits, but let's be conservative: 2 workers
    # Actually, for sequential consistency and rate limit handling, single thread might be safer 
    # unless we have high tier. Let's try sequential first with a small sleep to ensure reliability.
    
    rewritten_lines = []
    
    # Check if output file exists to resume? (Simple version: overwrite)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for i, line in enumerate(lines):
            processed_line = process_line(line, i)
            if processed_line:
                f_out.write(processed_line + '\n')
                f_out.flush() # Ensure written to disk
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{total} entries...")
            
            # Rate limit pacing
            time.sleep(0.5) # ~120 requests per minute max
            
    print(f"Done! Rewritten dataset saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
