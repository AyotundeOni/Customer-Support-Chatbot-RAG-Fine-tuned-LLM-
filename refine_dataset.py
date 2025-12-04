import json
import re
import sys

def clean_text(text):
    # 1. Remove the scraper prefix
    text = re.sub(r"^The step-by-step guide for '.*?' is:\s*", "", text)
    
    # 2. Remove "In this section" and "On this page" navigation dumps
    # These usually appear at the end or middle and list links
    # We'll try to cut off everything after these headers if they look like navigation lists
    text = re.split(r'\n\s*In this section\s*\n', text)[0]
    text = re.split(r'\n\s*On this page\s*\n', text)[0]
    
    # 3. Remove repetitive lines (headers repeated)
    lines = text.split('\n')
    cleaned_lines = []
    prev_line = None
    for line in lines:
        line = line.strip()
        if not line:
            if prev_line != "":
                cleaned_lines.append("")
            prev_line = ""
            continue
            
        # Skip lines that are just repetitions of the previous line
        if line == prev_line:
            continue
            
        # Skip lines that look like navigation items (often just a few words, repeated later)
        # Heuristic: if line is short and appears again in the next few lines? 
        # For now, just simple dedup
        
        cleaned_lines.append(line)
        prev_line = line
        
    text = '\n'.join(cleaned_lines)
    
    # 4. Fix spacing issues (scraper sometimes merged words)
    # "afree" -> "a free", "guideto" -> "guide to"
    # We can use a regex for common patterns or just specific fixes
    # Generic fix for lowercase followed immediately by word starting with lowercase (rare in English unless typo)
    # But "setup guideto" -> "guide to"
    # Let's fix specific common ones seen in the file
    text = re.sub(r'([a-z])(to)\b', r'\1 \2', text) # "guideto" -> "guide to"
    text = re.sub(r'\b(a)(free)\b', r'\1 \2', text) # "afree" -> "a free"
    text = re.sub(r'\b(the)(initial)\b', r'\1 \2', text) # "theinitial" -> "the initial"
    text = re.sub(r'\b(the)(setup)\b', r'\1 \2', text) # "thesetup" -> "the setup"
    text = re.sub(r'\b(then)(get)\b', r'\1 \2', text) # "thenget" -> "then get"
    
    # 6. Fix missing space between lowercase and uppercase (e.g., "useShopify" -> "use Shopify")
    # This is common when text is concatenated from HTML elements without spaces
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # 7. Remove "The following features are available..." if it's just a lead-in to a list we kept

    # (Optional, maybe keep for context)
    
    # 6. Shorten "To resolve this issue, you can..."
    text = text.replace("To resolve this issue, you can", "To resolve this:")
    
    return text.strip()

def refine_file(input_file, output_file):
    print(f"Refining {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        count = 0
        for line in f_in:
            try:
                data = json.loads(line)
                
                # Process messages
                new_messages = []
                for msg in data['messages']:
                    if msg['role'] == 'assistant':
                        msg['content'] = clean_text(msg['content'])
                    new_messages.append(msg)
                
                data['messages'] = new_messages
                
                # Write back
                f_out.write(json.dumps(data) + '\n')
                count += 1
                
            except json.JSONDecodeError:
                continue
                
    print(f"Refined {count} entries. Saved to {output_file}")

if __name__ == "__main__":
    refine_file('shopify_complete_qa.jsonl', 'shopify_refined_qa.jsonl')
