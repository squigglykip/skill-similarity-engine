#!/usr/bin/env python3
"""
Excel to CSV Converter

Quick and dirty script to convert Excel workbook tabs to CSV files
with specific folder structure based on tab naming conventions.

Usage: Place your Excel file in the project root and run this script from /scripts/
"""

import pandas as pd
import os
from pathlib import Path
import sys

# Step back from /scripts to project root
PROJECT_ROOT = Path(__file__).parent.parent
EXCEL_FILE = r"C:\Users\P729965\OneDrive - nab\Documents\GitHub\skill-similarity-engine\data\sse_ml_data_prep.xlsx"  # Change this to your Excel filename

# Define folder mappings based on tab naming patterns
FOLDER_MAPPINGS = {
    # Pattern: if tab name starts with this, put in this folder
    'd_colleague_position_fy': 'colleague_positions_history',
    'd_positions_fy': 'positions_history',
    'job_architecture': 'job_architecture',
    'job_arch_to_positions_mapping': 'job_arch_to_positions_mapping',
    'job_skill_mapping': 'job_skill_mapping',
    'workforce_context': 'workforce_context'
}

def find_excel_file():
    """Find the Excel file in project root"""
    # Look for common Excel extensions
    extensions = ['*.xlsx', '*.xls', '*.xlsm']
    
    for ext in extensions:
        excel_files = list(PROJECT_ROOT.glob(ext))
        if excel_files:
            return excel_files[0]  # Return first found
    
    return None

def determine_output_folder(tab_name):
    """Determine which folder a tab should go to based on naming patterns"""
    tab_name_lower = tab_name.lower()
    
    # Check exact matches first
    if tab_name_lower in ['job_architecture', 'job_arch_to_positions_mapping', 
                          'job_skill_mapping', 'workforce_context']:
        return FOLDER_MAPPINGS[tab_name_lower]
    
    # Check pattern matches
    if tab_name_lower.startswith('d_colleague_position_fy'):
        return FOLDER_MAPPINGS['d_colleague_position_fy']
    elif tab_name_lower.startswith('d_positions_fy'):
        return FOLDER_MAPPINGS['d_positions_fy']
    
    # Default fallback
    return 'misc'

def create_output_directories():
    """Create all necessary output directories"""
    base_data_dir = PROJECT_ROOT / 'data'
    
    folders_to_create = [
        'colleague_positions_history',
        'positions_history', 
        'job_architecture',
        'job_arch_to_positions_mapping',
        'job_skill_mapping',
        'workforce_context',
        'misc'  # For any unmatched tabs
    ]
    
    for folder in folders_to_create:
        folder_path = base_data_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created/verified directory: {folder_path}")

def convert_excel_to_csvs(excel_file_path):
    """Convert Excel tabs to CSV files"""
    print(f"🔄 Reading Excel file: {excel_file_path}")
    
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(excel_file_path)
        sheet_names = excel_file.sheet_names
        
        print(f"📊 Found {len(sheet_names)} sheets: {sheet_names}")
        
        conversion_summary = []
        
        for sheet_name in sheet_names:
            print(f"\n🔄 Processing sheet: '{sheet_name}'")
            
            # Read the sheet
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            
            # Determine output folder
            output_folder = determine_output_folder(sheet_name)
            
            # Create output path
            output_dir = PROJECT_ROOT / 'data' / output_folder
            csv_filename = f"{sheet_name}.csv"
            output_path = output_dir / csv_filename
            
            # Save as CSV
            df.to_csv(output_path, index=False)
            
            print(f"✅ Saved: {output_path}")
            print(f"   📊 Shape: {df.shape[0]} rows, {df.shape[1]} columns")
            
            conversion_summary.append({
                'sheet_name': sheet_name,
                'output_folder': output_folder,
                'output_path': str(output_path),
                'rows': df.shape[0],
                'columns': df.shape[1]
            })
        
        return conversion_summary
        
    except Exception as e:
        print(f"❌ Error processing Excel file: {e}")
        return []

def print_summary(conversion_summary):
    """Print conversion summary"""
    print(f"\n{'='*60}")
    print("CONVERSION SUMMARY")
    print(f"{'='*60}")
    
    # Group by folder
    folder_groups = {}
    for item in conversion_summary:
        folder = item['output_folder']
        if folder not in folder_groups:
            folder_groups[folder] = []
        folder_groups[folder].append(item)
    
    for folder, items in folder_groups.items():
        print(f"\n📁 {folder}/")
        for item in items:
            print(f"   └── {item['sheet_name']}.csv ({item['rows']} rows, {item['columns']} cols)")
    
    print(f"\n✅ Total files converted: {len(conversion_summary)}")

def main():
    """Main function"""
    print("🚀 Excel to CSV Converter")
    print(f"📂 Project root: {PROJECT_ROOT}")
    
    # Use the direct path
    excel_file = Path(EXCEL_FILE)
    if not excel_file.exists():
        print(f"❌ Excel file not found at: {excel_file}")
        return
    
    print(f"📄 Found Excel file: {excel_file.name}")
    
    # Create output directories
    print("\n🔧 Setting up output directories...")
    create_output_directories()
    
    # Convert Excel to CSVs
    print("\n🔄 Converting Excel tabs to CSV files...")
    conversion_summary = convert_excel_to_csvs(excel_file)
    
    if conversion_summary:
        print_summary(conversion_summary)
    else:
        print("❌ No files were converted")

if __name__ == "__main__":
    main()