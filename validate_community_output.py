"""
Validation script for shopify_community_qa.jsonl
Checks format, structure, and community-specific quality metrics
"""

import json
import sys
from typing import Dict
from collections import defaultdict


def validate_community_jsonl(filename: str) -> Dict:
    """
    Validate the community Q&A JSONL file
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'total_entries': 0,
        'valid_entries': 0,
        'errors': [],
        'platforms': defaultdict(int),
        'resolution_types': defaultdict(int),
        'topics': defaultdict(int),
        'avg_confidence': 0.0,
        'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
        'avg_question_length': 0,
        'avg_answer_length': 0,
        'sample_entries': []
    }
    
    question_lengths = []
    answer_lengths = []
    confidences = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                results['total_entries'] += 1
                
                try:
                    entry = json.loads(line)
                    
                    # Check structure
                    if 'messages' not in entry:
                        results['errors'].append(f"Line {line_num}: Missing 'messages' field")
                        continue
                    
                    if 'metadata' not in entry:
                        results['errors'].append(f"Line {line_num}: Missing 'metadata' field")
                        continue
                    
                    messages = entry['messages']
                    if len(messages) != 2:
                        results['errors'].append(f"Line {line_num}: Expected 2 messages, got {len(messages)}")
                        continue
                    
                    if messages[0].get('role') != 'user' or messages[1].get('role') != 'assistant':
                        results['errors'].append(f"Line {line_num}: Invalid message roles")
                        continue
                    
                    # Check metadata
                    metadata = entry['metadata']
                    required_fields = ['source_url', 'platform', 'resolution_type', 'confidence']
                    
                    for field in required_fields:
                        if field not in metadata:
                            results['errors'].append(f"Line {line_num}: Missing metadata field '{field}'")
                            continue
                    
                    # Track statistics
                    user_content = messages[0].get('content', '')
                    assistant_content = messages[1].get('content', '')
                    
                    question_lengths.append(len(user_content))
                    answer_lengths.append(len(assistant_content))
                    
                    platform = metadata.get('platform', 'unknown')
                    results['platforms'][platform] += 1
                    
                    resolution_type = metadata.get('resolution_type', 'unknown')
                    results['resolution_types'][resolution_type] += 1
                    
                    topic = metadata.get('topic', 'General')
                    results['topics'][topic] += 1
                    
                    confidence = metadata.get('confidence', 0.0)
                    confidences.append(confidence)
                    
                    # Confidence distribution
                    if confidence >= 0.8:
                        results['confidence_distribution']['high'] += 1
                    elif confidence >= 0.5:
                        results['confidence_distribution']['medium'] += 1
                    else:
                        results['confidence_distribution']['low'] += 1
                    
                    # Sample entries (first 3)
                    if len(results['sample_entries']) < 3:
                        results['sample_entries'].append({
                            'line': line_num,
                            'question': user_content[:100] + '...' if len(user_content) > 100 else user_content,
                            'answer_preview': assistant_content[:150] + '...' if len(assistant_content) > 150 else assistant_content,
                            'platform': platform,
                            'resolution_type': resolution_type,
                            'confidence': confidence,
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
        if confidences:
            results['avg_confidence'] = sum(confidences) / len(confidences)
        
    except FileNotFoundError:
        results['errors'].append(f"File '{filename}' not found")
    
    return results


def print_validation_report(results: Dict) -> None:
    """Print formatted validation report"""
    
    print("=" * 80)
    print("SHOPIFY COMMUNITY Q&A VALIDATION REPORT")
    print("=" * 80)
    print()
    
    print(f"Total Entries: {results['total_entries']}")
    print(f"Valid Entries: {results['valid_entries']}")
    print(f"Invalid Entries: {results['total_entries'] - results['valid_entries']}")
    print()
    
    if results['errors']:
        print(f"❌ Errors Found: {len(results['errors'])}")
        print("First 10 errors:")
        for error in results['errors'][:10]:
            print(f"  - {error}")
        print()
    else:
        print("✓ No errors found!")
        print()
    
    print(f"Average Question Length: {results['avg_question_length']:.0f} characters")
    print(f"Average Answer Length: {results['avg_answer_length']:.0f} characters")
    print(f"Average Confidence: {results['avg_confidence']:.2f}")
    print()
    
    print("Platform Distribution:")
    for platform, count in sorted(results['platforms'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {platform.capitalize()}: {count}")
    print()
    
    print("Resolution Type Distribution:")
    for res_type, count in sorted(results['resolution_types'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / results['valid_entries'] * 100) if results['valid_entries'] > 0 else 0
        print(f"  {res_type}: {count} ({percentage:.1f}%)")
    print()
    
    print("Confidence Distribution:")
    total = sum(results['confidence_distribution'].values())
    for level in ['high', 'medium', 'low']:
        count = results['confidence_distribution'][level]
        percentage = (count / total * 100) if total > 0 else 0
        emoji = '🟢' if level == 'high' else '🟡' if level == 'medium' else '🔴'
        print(f"  {emoji} {level.capitalize()} (≥0.8 / ≥0.5 / <0.5): {count} ({percentage:.1f}%)")
    print()
    
    print("Top Topics:")
    sorted_topics = sorted(results['topics'].items(), key=lambda x: x[1], reverse=True)[:10]
    for topic, count in sorted_topics:
        print(f"  {topic}: {count}")
    print()
    
    print("Sample Entries:")
    for i, sample in enumerate(results['sample_entries'], 1):
        print(f"\n  Entry #{i} (Line {sample['line']}):")
        print(f"    Platform: {sample['platform']}")
        print(f"    Resolution Type: {sample['resolution_type']}")
        print(f"    Confidence: {sample['confidence']:.2f}")
        print(f"    URL: {sample['url']}")
        print(f"    Question: {sample['question']}")
        print(f"    Answer: {sample['answer_preview']}")
    print()
    
    # Quality assessment
    success_rate = (results['valid_entries'] / results['total_entries'] * 100) if results['total_entries'] > 0 else 0
    high_confidence_rate = (results['confidence_distribution']['high'] / results['valid_entries'] * 100) if results['valid_entries'] > 0 else 0
    
    print("=" * 80)
    print("QUALITY ASSESSMENT")
    print("=" * 80)
    
    if success_rate == 100:
        print("✓ FORMAT: All entries valid")
    elif success_rate >= 95:
        print(f"⚠ FORMAT: {success_rate:.1f}% valid - Mostly good")
    else:
        print(f"✗ FORMAT: {success_rate:.1f}% valid - Issues found")
    
    if high_confidence_rate >= 50:
        print(f"✓ CONFIDENCE: {high_confidence_rate:.1f}% high confidence")
    elif high_confidence_rate >= 30:
        print(f"⚠ CONFIDENCE: {high_confidence_rate:.1f}% high confidence - Acceptable")
    else:
        print(f"⚠ CONFIDENCE: {high_confidence_rate:.1f}% high confidence - Consider filtering")
    
    print("=" * 80)


def main():
    """Main entry point"""
    filename = 'shopify_community_qa.jsonl'
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    print(f"Validating {filename}...")
    print()
    
    results = validate_community_jsonl(filename)
    print_validation_report(results)


if __name__ == "__main__":
    main()
