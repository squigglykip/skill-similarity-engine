import os
import re

def fix_unicode_in_file(file_path):
    """Fix Unicode character issues in a Python file using byte-level operations."""
    print(f"Processing: {file_path}")
    
    try:
        # Read file in binary mode to handle corrupted Unicode
        with open(file_path, 'rb') as f:
            content_bytes = f.read()
        
        # Track if any changes were made
        modified = False
        original_bytes = content_bytes
        
        # Define byte-level replacements for common corrupted patterns
        # This avoids having Unicode characters in this script
        byte_replacements = [
            # Corrupted bar chart emoji -> proper bar chart
            (b'\xc3\xb0\xc5\xb8\xe2\x80\x99', '\U0001F4CA'.encode('utf-8')),
            # Corrupted warning -> proper warning
            (b'\xc3\xa2\xc5\xa1\xc2\xa0\xc3\xaf\xc2\xb8\x8f', '\u26A0\uFE0F'.encode('utf-8')),
            # Corrupted check mark -> proper check
            (b'\xc3\xa2\xc5\x93\xe2\x80\x9c', '\u2705'.encode('utf-8')),
            # Corrupted X mark -> proper X
            (b'\xc3\xa2\xc5\x92\xc2\x8c', '\u274C'.encode('utf-8')),
            # Corrupted arrow -> proper arrow
            (b'\xc3\xa2\xc6\x92\xe2\x80\x99', '\u2192'.encode('utf-8')),
        ]
        
        # Apply byte-level replacements
        for old_bytes, new_bytes in byte_replacements:
            if old_bytes in content_bytes:
                content_bytes = content_bytes.replace(old_bytes, new_bytes)
                modified = True
                print(f"  Fixed corrupted byte pattern")
        
        # Convert to text for string-based fixes
        try:
            content_text = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to latin1 if UTF-8 fails
            content_text = content_bytes.decode('latin1', errors='replace')
        
        # String-based replacements using Unicode escapes
        string_replacements = [
            # Fix specific patterns we know are problematic
            ('Risk Analyst \u2192 Data Scientist', 'Risk Analyst → Data Scientist'),
            ('\u2713', '✓'),  # Check mark
            ('\u2717', '✗'),  # Cross mark
        ]
        
        for old_str, new_str in string_replacements:
            if old_str in content_text:
                content_text = content_text.replace(old_str, new_str)
                modified = True
                print(f"  Fixed string pattern: {repr(old_str)}")
        
        # Write back if modified
        if modified:
            # Create backup
            backup_path = file_path + '.backup'
            with open(backup_path, 'wb') as f:
                f.write(original_bytes)
            print(f"  Backup created: {backup_path}")
            
            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content_text)
            print(f"  Fixed: {file_path}")
            return True
        else:
            print(f"  No changes needed")
            return False
            
    except Exception as e:
        print(f"  Error processing file: {e}")
        return False

def scan_project(project_path):
    """Find and fix all Python files in the project."""
    print(f"Scanning project: {project_path}")
    
    python_files = []
    for root, dirs, files in os.walk(project_path):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_unicode_in_file(file_path):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files")
    return fixed_count

if __name__ == "__main__":
    # Scan current directory instead of looking for subdirectory
    project_path = '.'
    
    print("Unicode Fix Script")
    print("=" * 30)
    print(f"Current directory: {os.getcwd()}")
    
    fixed_count = scan_project(project_path)
    
    if fixed_count > 0:
        print(f"\nSuccess! Fixed {fixed_count} files")
        print("Try running the webapp again")
    else:
        print("\nNo files needed fixing") 