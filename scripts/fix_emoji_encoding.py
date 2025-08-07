#!/usr/bin/env python3
"""
Emoji Encoding Fix Script

This script fixes emoji encoding issues across all Python files in the project.
It specifically targets the corrupted emojis we found in the codebase.

Usage: python scripts/fix_emoji_encoding.py
"""

import os
from pathlib import Path
import argparse


def fix_emoji_encoding_in_file(file_path: Path, dry_run: bool = False):
    """Fix emoji encoding issues in a single file."""
    
    try:
        # Read the file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track changes
        replacement_count = 0
        original_content = content
        
        # Define all emoji replacements - using the exact corrupted sequences found
        emoji_replacements = {
            # Search emojis
            '📁': '🔍',
            
            # Chart emojis  
            '📁Š': '📊',
            
            # Document/file emojis
            '📁„': '📄',
            
            # Rocket emoji
            '🚀': '🚀',
            
            # Target emoji
            '🎯': '🎯',
            
            # Trending up
            '📁ˆ': '📈',
            
            # Trending down
            '📁‰': '📉',
            
            # New badge
            '🆕': '🆕',
            
            # Folder
            '📁': '📁',
            
            # Clipboard/list
            '📁‹': '📋',
            
            # Warning variants
            '⚠️': '⚠️',
            '⚠️': '⚠️', 
            '⚠️': '⚠️',
            
            # Cross mark
            '❌': '❌',
            
            # Question mark
            '❓': '❓',
            
            # Check mark
            '✅': '✅',
            
            # Information
            'ℹ️': 'ℹ️',
            'ℹ️': 'ℹ️',
        }
        
        # Apply all replacements
        for corrupted, correct in emoji_replacements.items():
            if corrupted in content:
                count = content.count(corrupted)
                content = content.replace(corrupted, correct)
                replacement_count += count
        
        if replacement_count > 0:
            if not dry_run:
                # Write back the fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            return replacement_count
        else:
            return 0
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return 0


def fix_all_files(project_root: Path, dry_run: bool = False):
    """Fix emoji encoding issues in all Python files."""
    
    print(f"🔍 Scanning all Python files for emoji encoding issues...")
    print(f"📁 Project root: {project_root}")
    print(f"🏃 Mode: {'DRY RUN' if dry_run else 'LIVE FIX'}")
    print()
    
    files_processed = 0
    files_modified = 0
    total_replacements = 0
    
    # Skip certain directories
    skip_dirs = {'__pycache__', '.git', '.pytest_cache', 'node_modules', '.venv', 'venv', '.env', 'env'}
    
    # Walk through Python files
    for py_file in project_root.rglob('*.py'):
        # Skip certain directories
        if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
            continue
        
        files_processed += 1
        replacement_count = fix_emoji_encoding_in_file(py_file, dry_run)
        
        if replacement_count > 0:
            files_modified += 1
            total_replacements += replacement_count
            print(f"✅ Fixed {replacement_count} emoji(s) in {py_file}")
    
    print()
    print("=" * 80)
    print("📊 EMOJI ENCODING FIX SUMMARY")
    print("=" * 80)
    print(f"Files processed: {files_processed}")
    print(f"Files modified: {files_modified}")
    print(f"Total replacements: {total_replacements}")
    
    if dry_run and files_modified > 0:
        print()
        print("⚠️  This was a DRY RUN. No files were actually modified.")
        print("   Run again without --dry-run to apply the fixes.")
    elif files_modified > 0:
        print()
        print("✅ All emoji encoding issues have been fixed!")
    else:
        print()
        print("✅ No emoji encoding issues found in the project.")
    
    return files_modified > 0


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Fix emoji encoding issues across all Python files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/fix_emoji_encoding.py           # Fix emoji encoding issues
  python scripts/fix_emoji_encoding.py --dry-run # Preview fixes
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Preview changes without modifying files'
    )
    
    args = parser.parse_args()
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
    fix_all_files(project_root, args.dry_run)


if __name__ == "__main__":
    main()