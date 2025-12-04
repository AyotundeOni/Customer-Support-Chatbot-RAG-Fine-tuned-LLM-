"""
JSONL Validation and Repair Script
Validates and fixes common JSON issues in JSONL files
"""

import json
import sys
import re


def fix_json_string(line: str) -> str:
    """
    Attempt to fix common JSON string issues
    
    Args:
        line: JSON line with potential issues
        
    Returns:
        Fixed JSON line
    """
    # Fix unescaped quotes within strings
    # This is a complex operation, so we'll try to parse first
    try:
        json.loads(line)
        return line  # Already valid
    except json.JSONDecodeError:
        pass
    
    # Try to fix unescaped newlines
    line = line.replace('\n', '\\n')
    
    # Try parsing again
    try:
        json.loads(line)
        return line
    except json.JSONDecodeError:
        pass
    
    return None  # Can't fix


def validate_and_repair_jsonl(input_file: str, output_file: str = None):
    """
    Validate JSONL file and optionally repair it
    
    Args:
        input_file: Input JSONL filename
        output_file: Output filename for repaired version (optional)
    """
    if output_file is None:
        output_file = input_file.replace('.jsonl', '_fixed.jsonl')
    
    print(f"Validating: {input_file}")
    print("=" * 80)
    
    total_lines = 0
    valid_lines = 0
    invalid_lines = []
    repaired_lines = 0
    
    output_data = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            line = line.strip()
            
            if not line:
                continue
            
            try:
                # Try to parse the line
                entry = json.loads(line)
                
                # Validate structure
                assert 'messages' in entry, "Missing 'messages' field"
                assert isinstance(entry['messages'], list), "'messages' must be a list"
                assert len(entry['messages']) >= 2, "'messages' must have at least 2 items"
                assert entry['messages'][0].get('role') == 'user', "First message must be 'user'"
                assert entry['messages'][1].get('role') == 'assistant', "Second message must be 'assistant'"
                assert 'metadata' in entry, "Missing 'metadata' field"
                
                # Valid entry
                valid_lines += 1
                output_data.append(line)
                
            except json.JSONDecodeError as e:
                # Try to fix
                fixed_line = fix_json_string(line)
                
                if fixed_line:
                    try:
                        json.loads(fixed_line)
                        repaired_lines += 1
                        output_data.append(fixed_line)
                        print(f"✓ Repaired line {line_num}")
                    except:
                        invalid_lines.append((line_num, str(e), line[:100]))
                else:
                    invalid_lines.append((line_num, str(e), line[:100]))
                    
            except AssertionError as e:
                invalid_lines.append((line_num, f"Structure error: {e}", line[:100]))
            except Exception as e:
                invalid_lines.append((line_num, f"Error: {e}", line[:100]))
    
    # Print report
    print(f"\nTotal lines: {total_lines}")
    print(f"Valid lines: {valid_lines}")
    print(f"Repaired lines: {repaired_lines}")
    print(f"Invalid lines: {len(invalid_lines)}")
    
    if invalid_lines:
        print(f"\n❌ Found {len(invalid_lines)} invalid lines:")
        for line_num, error, preview in invalid_lines[:10]:  # Show first 10
            print(f"\nLine {line_num}: {error}")
            print(f"Preview: {preview}...")
    else:
        print(f"\n✓ All lines are valid!")
    
    # Save repaired version if there were repairs or issues
    if repaired_lines > 0 or len(invalid_lines) > 0:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_data))
        
        if len(invalid_lines) == 0:
            print(f"\n✓ Repaired version saved to: {output_file}")
            print(f"  You can replace the original with: mv {output_file} {input_file}")
        else:
            print(f"\n⚠ Repaired version saved to: {output_file}")
            print(f"  {len(invalid_lines)} lines could not be repaired and were excluded")
    
    print("=" * 80)
    
    return len(invalid_lines) == 0


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python fix_jsonl.py <input_file.jsonl> [output_file.jsonl]")
        print("\nValidating all JSONL files in current directory...")
        files = ['shopify_complete_qa.jsonl', 'shopify_qa.jsonl', 'shopify_community_qa.jsonl']
    else:
        files = [sys.argv[1]]
    
    all_valid = True
    
    for filename in files:
        try:
            output_file = sys.argv[2] if len(sys.argv) > 2 else None
            is_valid = validate_and_repair_jsonl(filename, output_file)
            all_valid = all_valid and is_valid
            print()
        except FileNotFoundError:
            print(f"⚠ File not found: {filename}\n")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}\n")
            all_valid = False
    
    if all_valid:
        print("\n✅ ALL FILES ARE VALID!")
    else:
        print("\n❌ Some files have issues - check the output above")


if __name__ == "__main__":
    main()
