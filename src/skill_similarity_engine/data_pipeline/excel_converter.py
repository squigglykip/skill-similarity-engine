#!/usr/bin/env python3
"""
Excel to CSV Converter Module

Modularized version of the Excel to CSV conversion functionality
for integration into the CLI workflow.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ExcelConverter:
    """
    Converts Excel workbook tabs to CSV files with organized folder structure
    based on tab naming conventions.
    """
    
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
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the Excel converter.
        
        Args:
            project_root: Path to project root. If None, auto-detects.
        """
        if project_root is None:
            # Auto-detect project root (assuming we're in src/skill_similarity_engine/data_pipeline/)
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.data_dir = self.project_root / 'data'
        
    def prompt_for_excel_file(self) -> Optional[Path]:
        """
        Prompt user for Excel file path.
        
        Returns:
            Path to Excel file if valid, None otherwise
        """
        print("📂 Please specify the path to your Excel file:")
        print("   You can provide either:")
        print("   • Full path: C:\\path\\to\\your\\file.xlsx")
        print("   • Relative path: data\\my_file.xlsx")
        print("   • Just filename if in project root: my_file.xlsx")
        print()
        
        while True:
            user_input = input("Excel file path: ").strip()
            
            if not user_input:
                print("❌ Please provide a file path.")
                continue
            
            # Try the path as provided first
            excel_path = Path(user_input)
            
            # If not absolute and doesn't exist, try relative to project root
            if not excel_path.is_absolute() and not excel_path.exists():
                excel_path = self.project_root / user_input
            
            # Check if file exists and has valid extension
            if excel_path.exists() and excel_path.suffix.lower() in ['.xlsx', '.xls', '.xlsm']:
                return excel_path
            elif excel_path.exists():
                print(f"❌ File exists but is not a valid Excel file: {excel_path}")
                print("   Supported formats: .xlsx, .xls, .xlsm")
            else:
                print(f"❌ File not found: {excel_path}")
                
            print("   Please try again or press Ctrl+C to cancel.")
            print()
    
    def determine_output_folder(self, tab_name: str) -> str:
        """
        Determine which folder a tab should go to based on naming patterns.
        
        Args:
            tab_name: Name of the Excel tab/sheet
            
        Returns:
            Folder name for the tab
        """
        tab_name_lower = tab_name.lower()
        
        # Check exact matches first
        if tab_name_lower in ['job_architecture', 'job_arch_to_positions_mapping', 
                              'job_skill_mapping', 'workforce_context']:
            return self.FOLDER_MAPPINGS[tab_name_lower]
        
        # Check pattern matches
        if tab_name_lower.startswith('d_colleague_position_fy'):
            return self.FOLDER_MAPPINGS['d_colleague_position_fy']
        elif tab_name_lower.startswith('d_positions_fy'):
            return self.FOLDER_MAPPINGS['d_positions_fy']
        
        # Default fallback
        return 'misc'
    
    def create_output_directories(self) -> None:
        """Create all necessary output directories."""
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
            folder_path = self.data_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/verified directory: {folder_path}")
    
    def convert_excel_to_csvs(self, excel_file_path: Path) -> List[Dict[str, Any]]:
        """
        Convert Excel tabs to CSV files.
        
        Args:
            excel_file_path: Path to the Excel file
            
        Returns:
            List of conversion summary dictionaries
            
        Raises:
            Exception: If conversion fails
        """
        logger.info(f"Reading Excel file: {excel_file_path}")
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(excel_file_path)
            sheet_names = excel_file.sheet_names
            
            logger.info(f"Found {len(sheet_names)} sheets: {sheet_names}")
            
            conversion_summary = []
            
            for sheet_name in sheet_names:
                logger.info(f"Processing sheet: '{sheet_name}'")
                
                # Read the sheet
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                
                # Determine output folder (ensure sheet_name is a string)
                output_folder = self.determine_output_folder(str(sheet_name))
                
                # Create output path
                output_dir = self.data_dir / output_folder
                csv_filename = f"{sheet_name}.csv"
                output_path = output_dir / csv_filename
                
                # Save as CSV
                df.to_csv(output_path, index=False)
                
                logger.info(f"Saved: {output_path} ({df.shape[0]} rows, {df.shape[1]} columns)")
                
                conversion_summary.append({
                    'sheet_name': sheet_name,
                    'output_folder': output_folder,
                    'output_path': str(output_path),
                    'rows': df.shape[0],
                    'columns': df.shape[1]
                })
            
            return conversion_summary
            
        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            raise
    
    def print_summary(self, conversion_summary: List[Dict[str, Any]]) -> None:
        """
        Print conversion summary.
        
        Args:
            conversion_summary: List of conversion result dictionaries
        """
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
    
    def run_conversion(self) -> bool:
        """
        Run the complete Excel to CSV conversion process.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("🚀 Excel to CSV Converter")
            print(f"📂 Project root: {self.project_root}")
            print()
            
            # Prompt for Excel file
            excel_file = self.prompt_for_excel_file()
            if not excel_file:
                print("❌ No valid Excel file specified!")
                return False
            
            print(f"\n📄 Using Excel file: {excel_file}")
            print(f"   File size: {excel_file.stat().st_size / 1024 / 1024:.1f} MB")
            
            # Create output directories
            print("\n🔧 Setting up output directories...")
            self.create_output_directories()
            
            # Convert Excel to CSVs
            print("\n🔄 Converting Excel tabs to CSV files...")
            conversion_summary = self.convert_excel_to_csvs(excel_file)
            
            if conversion_summary:
                self.print_summary(conversion_summary)
                return True
            else:
                print("❌ No files were converted")
                return False
                
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            logger.error(f"Excel conversion failed: {e}")
            return False


def run_excel_conversion(project_root: Optional[Path] = None) -> bool:
    """
    Convenience function to run Excel conversion.
    
    Args:
        project_root: Path to project root. If None, auto-detects.
        
    Returns:
        True if successful, False otherwise
    """
    converter = ExcelConverter(project_root)
    return converter.run_conversion()


if __name__ == "__main__":
    # Allow running as standalone script
    run_excel_conversion()