"""
Validation script for shopify_qa.jsonl
Checks format, structure, and data quality
"""

import json
import sys
from typing import Dict, List


def validate_jsonl(filename: str) -> Dict:
    """
    Validate the JSONL file for correctness
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'total_entries': 0,
        'valid_entries': 0,
        'errors': [],
        'topics': {},
        'avg_question_length': 0,
        'avg_answer_length': 0,
        'sample_entries': []
    }
    
    question_lengths = []
    answer_lengths = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                results['total_entries'] += 1
                
                try:
                    # Parse JSON
                    entry = json.loads(line)
                    
                    # Check required fields
                    if 'messages' not in entry:
                        results['errors'].append(f"Line {line_num}: Missing 'messages' field")
                        continue
                    
                    if 'metadata' not in entry:
                        results['errors'].append(f"Line {line_num}: Missing 'metadata' field")
                        continue
                    
                    # Check messages structure
                    messages = entry['messages']
                    if not isinstance(messages, list) or len(messages) != 2:
                        results['errors'].append(f"Line {line_num}: 'messages' should be a list with 2 items")
                        continue
                    
                    # Check message roles
                    if messages[0].get('role') != 'user':
                        results['errors'].append(f"Line {line_num}: First message should have role 'user'")
                        continue
                    
                    if messages[1].get('role') != 'assistant':
                        results['errors'].append(f"Line {line_num}: Second message should have role 'assistant'")
                        continue
                    
                    # Check message content
                    user_content = messages[0].get('content', '')
                    assistant_content = messages[1].get('content', '')
                    
                    if not user_content or not assistant_content:
                        results['errors'].append(f"Line {line_num}: Empty content in messages")
                        continue
                    
                    # Check metadata
                    metadata = entry['metadata']
                    required_metadata = ['source_url', 'topic', 'date_scraped']
                    
                    for field in required_metadata:
                        if field not in metadata:
                            results['errors'].append(f"Line {line_num}: Missing metadata field '{field}'")
                            continue
                    
                    # Track statistics
                    question_lengths.append(len(user_content))
                    answer_lengths.append(len(assistant_content))
                    
                    topic = metadata.get('topic', 'Unknown')
                    results['topics'][topic] = results['topics'].get(topic, 0) + 1
                    
                    # Store sample entries (first 3)
                    if len(results['sample_entries']) < 3:
                        results['sample_entries'].append({
                            'line': line_num,
                            'question': user_content[:100] + '...' if len(user_content) > 100 else user_content,
                            'answer_preview': assistant_content[:150] + '...' if len(assistant_content) > 150 else assistant_content,
                            'topic': topic,
                            'url': metadata.get('source_url', '')
                        })
                    
                    results['valid_entries'] += 1
                    
                except json.JSONDecodeError as e:
                    results['errors'].append(f"Line {line_num}: Invalid JSON - {str(e)}")
                except Exception as e:
                    results['errors'].append(f"Line {line_num}: Error - {str(e)}")
        
        # Calculate averages
        if question_lengths:
            results['avg_question_length'] = sum(question_lengths) / len(question_lengths)
        if answer_lengths:
            results['avg_answer_length'] = sum(answer_lengths) / len(answer_lengths)
        
    except FileNotFoundError:
        results['errors'].append(f"File '{filename}' not found")
    
    return results


def print_validation_report(results: Dict) -> None:
    """Print a formatted validation report"""
    
    print("=" * 80)
    print("SHOPIFY Q&A JSONL VALIDATION REPORT")
    print("=" * 80)
    print()
    
    print(f"Total Entries: {results['total_entries']}")
    print(f"Valid Entries: {results['valid_entries']}")
    print(f"Invalid Entries: {results['total_entries'] - results['valid_entries']}")
    print()
    
    if results['errors']:
        print(f"Errors Found: {len(results['errors'])}")
        print("First 10 errors:")
        for error in results['errors'][:10]:
            print(f"  - {error}")
        print()
    else:
        print("✓ No errors found!")
        print()
    
    print(f"Average Question Length: {results['avg_question_length']:.0f} characters")
    print(f"Average Answer Length: {results['avg_answer_length']:.0f} characters")
    print()
    
    print("Topic Distribution:")
    for topic, count in sorted(results['topics'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {topic}: {count}")
    print()
    
    print("Sample Entries:")
    for i, sample in enumerate(results['sample_entries'], 1):
        print(f"\n  Entry #{i} (Line {sample['line']}):")
        print(f"    Topic: {sample['topic']}")
        print(f"    URL: {sample['url']}")
        print(f"    Question: {sample['question']}")
        print(f"    Answer: {sample['answer_preview']}")
    print()
    
    # Overall assessment
    success_rate = (results['valid_entries'] / results['total_entries'] * 100) if results['total_entries'] > 0 else 0
    print("=" * 80)
    if success_rate == 100:
        print("✓ ALL ENTRIES VALID - READY FOR USE!")
    elif success_rate >= 95:
        print(f"⚠ {success_rate:.1f}% valid - Mostly good, review errors")
    else:
        print(f"✗ {success_rate:.1f}% valid - Issues found, review required")
    print("=" * 80)


def main():
    """Main entry point"""
    filename = 'shopify_qa.jsonl'
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    print(f"Validating {filename}...")
    print()
    
    results = validate_jsonl(filename)
    print_validation_report(results)


if __name__ == "__main__":
    main()
