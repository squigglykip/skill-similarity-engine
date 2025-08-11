"""
Utility Commands for Data Management and Documentation

Contains CLI commands for utility operations, extracted from precompute_commands.py
and focused on database cleanup, Excel conversion, and documentation generation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, List

from .base_command import BaseCommand, CommandResult
from ...config.architectural_config_manager import get_config_manager
from ...data_pipeline.excel_converter import ExcelConverter

logger = logging.getLogger(__name__)


class DatabaseCleanupCommand(BaseCommand):
    """
    Command for cleaning up unneeded database tables after analytics completion.
    
    Safely removes large intermediate tables (core_colleague_positions_history,
    core_position_timeline) that are only needed during processing but consume
    significant storage space once analytics are complete.
    """
    
    def __init__(self):
        super().__init__(
            name="database_cleanup",
            description="Clear unneeded database tables to reduce storage overhead"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for database cleanup."""
        return CommandResult(
            success=True,
            message="Database cleanup arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute database cleanup operation.
        
        Returns:
            CommandResult with cleanup status and statistics
        """
        try:
            print("\n🧹 Database Cleanup Operations")
            print("="*50)
            print("🗂️  Cleaning up large intermediate tables after analytics completion:")
            print("   • core_colleague_positions_history (historical position data)")
            print("   • core_position_timeline (timeline data)")
            print("   • Database size optimization with VACUUM")
            print()
            
            # Import database cleanup utilities
            from ...utils.database_cleanup import DatabaseCleanupManager
            
            config_manager = get_config_manager()
            
            # Get database path
            try:
                db_config = config_manager.get_nested_value('database', 'paths')
                if db_config and 'business_context' in db_config:
                    db_path = db_config['business_context']
                else:
                    db_path = "models/2025-Q3/business_context.sqlite"
            except:
                db_path = "models/2025-Q3/business_context.sqlite"
            
            print(f"📂 Database: {db_path}")
            print()
            
            # Initialize cleanup manager
            cleanup_manager = DatabaseCleanupManager(db_path)
            
            # Analyze current database state
            print("📊 Analyzing database size and cleanup opportunities...")
            preview = cleanup_manager.preview_cleanup()
            
            if preview['tables_to_cleanup'] == 0:
                print("✅ No tables need cleanup - database is already optimized")
                return CommandResult(
                    success=True,
                    message="Database is already optimized - no cleanup needed",
                    data={'cleanup_needed': False}
                )
            
            # Show cleanup preview
            print(f"   • Tables to cleanup: {preview['tables_to_cleanup']}")
            print(f"   • Rows to remove: {preview['total_rows_to_remove']:,}")
            print(f"   • Storage to free: {preview['total_size_to_free_mb']:.1f} MB")
            print()
            
            print("📋 Cleanup Details:")
            for detail in preview['cleanup_details']:
                print(f"   • {detail['table_name']}: {detail['row_count']:,} rows ({detail['estimated_size_mb']:.1f} MB)")
            print()
            
            # Confirm with user unless auto-confirmed
            if not kwargs.get('auto_confirm', False):
                print("⚠️  WARNING: This will permanently delete the above tables!")
                print("   These tables are only needed for movement analysis processing.")
                print("   Once analytics are complete, they can be safely removed.")
                print("   The analytics results are preserved in other tables.")
                print()
                
                confirm = input("   Proceed with cleanup? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("   Cleanup cancelled.")
                    return CommandResult(
                        success=False,
                        message="Cleanup cancelled by user"
                    )
            
            # Perform cleanup
            print("🧹 Performing database cleanup...")
            cleanup_result = cleanup_manager.perform_cleanup(confirm=True)
            
            if cleanup_result['success']:
                print()
                print("✅ Database cleanup completed successfully!")
                print()
                print("📊 Cleanup Results:")
                print(f"   • Tables cleaned: {cleanup_result['tables_cleaned']}")
                print(f"   • Rows removed: {cleanup_result['total_rows_removed']:,}")
                print(f"   • Storage freed: {cleanup_result['total_size_freed_mb']:.1f} MB")
                
                # Show database size after cleanup
                size_info = cleanup_manager.get_database_size_info()
                if 'error' not in size_info:
                    print(f"   • Database size: {size_info['file_size_mb']:.1f} MB")
                    print(f"   • Used space: {size_info['used_size_mb']:.1f} MB")
                    if size_info['free_size_mb'] > 0:
                        print(f"   • Free space: {size_info['free_size_mb']:.1f} MB (will be reclaimed)")
                
                if cleanup_result.get('errors'):
                    print()
                    print("⚠️  Warnings:")
                    for error in cleanup_result['errors']:
                        print(f"   • {error}")
                
                print()
                print("🎯 Benefits:")
                print("   • Reduced database size and improved performance")
                print("   • Lower storage overhead for production deployment")
                print("   • Analytics capabilities preserved in optimized tables")
                print()
                
                return CommandResult(
                    success=True,
                    message=f"Database cleanup completed - {cleanup_result['total_size_freed_mb']:.1f} MB freed",
                    data={
                        'cleanup_stats': cleanup_result,
                        'size_info': size_info
                    },
                    metadata={
                        'database_path': db_path,
                        'tables_cleaned': cleanup_result['tables_cleaned'],
                        'storage_freed_mb': cleanup_result['total_size_freed_mb']
                    }
                )
            else:
                print("❌ Database cleanup failed.")
                print(f"   Error: {cleanup_result.get('message', 'Unknown error')}")
                if cleanup_result.get('errors'):
                    for error in cleanup_result['errors']:
                        print(f"   • {error}")
                
                return CommandResult(
                    success=False,
                    message=f"Database cleanup failed: {cleanup_result.get('message', 'Unknown error')}",
                    errors=cleanup_result.get('errors', ['Cleanup operation failed'])
                )
                
        except Exception as e:
            print(f"❌ Database cleanup command failed: {e}")
            print("   Check your database connection and permissions.")
            return CommandResult(
                success=False,
                message=f"Database cleanup failed: {str(e)}",
                errors=[str(e)]
            )


class ExcelConverterCommand(BaseCommand):
    """
    Command for converting Excel workbook tabs to CSV files.
    
    Automatically detects Excel files in the project root and converts
    all tabs to organized CSV files in the data/ directory structure.
    """
    
    def __init__(self):
        super().__init__(
            name="excel_converter",
            description="Convert Excel workbook tabs to CSV files"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for Excel conversion."""
        return CommandResult(
            success=True,
            message="Excel converter arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute Excel to CSV conversion.
        
        Returns:
            CommandResult with conversion status
        """
        try:
            print("\n🚀 Data Pipeline Setup - Excel to CSV Conversion")
            print("="*60)
            print("📋 Converting Excel workbook tabs to organized CSV files...")
            print("   You will be prompted to specify the path to your Excel file.")
            print()
            
            # Get project root from config or auto-detect
            try:
                config_manager = get_config_manager()
                # Try to get project root from config, fallback to auto-detection
                project_root = None
            except:
                project_root = None
            
            # Initialize Excel converter
            converter = ExcelConverter(project_root=project_root)
            
            # Run the conversion
            success = converter.run_conversion()
            
            if success:
                print()
                print("✅ Excel to CSV conversion completed successfully!")
                print("   Your data is now ready for database building.")
                print("   Next step: Choose '1. Build Workforce Database' from the main menu.")
                
                return CommandResult(
                    success=True,
                    message="Excel to CSV conversion completed successfully",
                    data={'conversion_completed': True},
                    metadata={
                        'data_directory': str(converter.data_dir),
                        'project_root': str(converter.project_root)
                    }
                )
            else:
                print()
                print("❌ Excel to CSV conversion failed.")
                print("   Please check your Excel file path and try again.")
                print("   Supported formats: .xlsx, .xls, .xlsm")
                
                return CommandResult(
                    success=False,
                    message="Excel to CSV conversion failed",
                    errors=["No Excel file found or conversion failed"]
                )
                
        except Exception as e:
            print(f"❌ Excel converter command failed: {e}")
            print("   Check your Excel file and permissions.")
            return CommandResult(
                success=False,
                message=f"Excel conversion failed: {str(e)}",
                errors=[str(e)]
            )


class SchemaDocumentationCommand(BaseCommand):
    """
    Command for generating enhanced database schema documentation.
    
    Creates comprehensive interactive HTML documentation with:
    - Collapsible sections and modern UI
    - Interactive Mermaid ERD with zoom/pan controls
    - Business context and developer guides
    - Responsive design and smooth navigation
    """
    
    def __init__(self):
        super().__init__(
            name="schema_documentation",
            description="Generate enhanced database schema documentation"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for schema documentation generation."""
        return CommandResult(
            success=True,
            message="Schema documentation arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute schema documentation generation.
        
        Returns:
            CommandResult with generation status
        """
        try:
            print("\n📚 Database Schema Documentation Generator")
            print("="*60)
            print("🌐 Generating interactive HTML documentation with:")
            print("   • Modern responsive UI with collapsible sections")
            print("   • Interactive Mermaid ERD with zoom/pan controls")
            print("   • Business context and usage guides")
            print("   • Developer-friendly query examples")
            print("   • Smooth navigation and professional styling")
            print()
            
            # Get database path from config
            try:
                config_manager = get_config_manager()
                db_config = config_manager.get_nested_value('database', 'paths')
                if db_config and 'business_context' in db_config:
                    db_path = db_config['business_context']
                else:
                    db_path = "models/2025-Q3/business_context.sqlite"
            except:
                db_path = "models/2025-Q3/business_context.sqlite"
            
            # Check if database exists
            db_file = Path(db_path)
            if not db_file.exists():
                print(f"❌ Database not found: {db_path}")
                print("   Please build the workforce database first.")
                return CommandResult(
                    success=False,
                    message="Database not found",
                    errors=[f"Database file does not exist: {db_path}"]
                )
            
            print(f"📂 Database: {db_path}")
            print(f"   Size: {db_file.stat().st_size / 1024 / 1024:.1f} MB")
            print()
            
            # Set output path (now generates HTML instead of markdown)
            output_path = "docs/sqlite_schema_design.html"
            output_file = Path(output_path)
            
            print(f"📄 Output: {output_path}")
            print()
            
            # Import and run the enhanced documentation generator
            from ...documentation.schema_generator import generate_enhanced_schema_docs
            
            print("🔍 Analyzing database schema and generating documentation...")
            success = generate_enhanced_schema_docs(str(db_file), str(output_file))
            
            if success:
                print()
                print("✅ Enhanced schema documentation generated successfully!")
                print(f"   📄 Documentation saved to: {output_path}")
                print(f"   📊 File size: {output_file.stat().st_size / 1024:.1f} KB")
                print()
                print("🎯 Features included:")
                print("   • Interactive collapsible sections")
                print("   • Zoomable/pannable Mermaid ERD")
                print("   • Business context guide")
                print("   • Developer query examples")
                print("   • Responsive modern design")
                print()
                print("💡 Open the HTML file in your web browser to explore the interactive documentation!")
                
                return CommandResult(
                    success=True,
                    message="Schema documentation generated successfully",
                    data={
                        'output_path': str(output_path),
                        'file_size_kb': output_file.stat().st_size / 1024,
                        'database_analyzed': str(db_path)
                    },
                    metadata={
                        'documentation_type': 'enhanced_schema',
                        'features': ['toc', 'mermaid_erd', 'business_context', 'dev_guide']
                    }
                )
            else:
                print()
                print("❌ Schema documentation generation failed.")
                print("   Check database permissions and file access.")
                
                return CommandResult(
                    success=False,
                    message="Schema documentation generation failed",
                    errors=["Documentation generation process failed"]
                )
                
        except Exception as e:
            print(f"❌ Schema documentation command failed: {e}")
            print("   Check your database and file permissions.")
            return CommandResult(
                success=False,
                message=f"Schema documentation failed: {str(e)}",
                errors=[str(e)]
            )


class AnalyticsExportCommand(BaseCommand):
    """
    Command for exporting analytics tables to CSV files.
    
    Provides memory-efficient export of all analytics_* tables with:
    - Chunked processing for large tables (e.g., analytics_job_similarities)
    - Individual CSV files for each table with timestamps
    - Progress tracking and comprehensive error handling
    - Selective export options
    """
    
    def __init__(self):
        super().__init__(
            name="analytics_export",
            description="Export analytics tables to CSV files"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for analytics export."""
        return CommandResult(
            success=True,
            message="Analytics export arguments validated"
        )
    
    def _find_database_path(self) -> Optional[str]:
        """
        Find the database path using existing infrastructure and quarterly folder structure.
        
        Returns:
            Database path if found, None otherwise
        """
        try:
            # Try to get database path from configuration
            config_manager = get_config_manager()
            
            # Look for database configuration patterns used elsewhere in the system
            db_config_paths = [
                'business_context.database.connection.database_path',
                'database.connection.database_path',
                'core.database.path'
            ]
            
            for config_path in db_config_paths:
                try:
                    path_parts = config_path.split('.')
                    db_path = config_manager.get_nested_value(*path_parts)
                    if db_path and Path(db_path).exists():
                        return str(Path(db_path).resolve())
                except:
                    continue
            
            # Search for databases in quarterly folder structure under models/
            models_dir = Path("models")
            if models_dir.exists():
                # Look for quarterly directories (e.g., 2025-Q1, 2025-Q2, etc.)
                quarterly_dirs = []
                for item in models_dir.iterdir():
                    if item.is_dir() and ("-Q" in item.name or "Q" in item.name):
                        quarterly_dirs.append(item)
                
                # Sort quarterly directories to get the most recent
                quarterly_dirs.sort(key=lambda x: x.name, reverse=True)
                
                # Search for database files in quarterly directories
                db_names = [
                    "business_context.sqlite",
                    "workforce_intelligence.db",
                    "skill_similarity_database.db"
                ]
                
                for quarterly_dir in quarterly_dirs:
                    for db_name in db_names:
                        db_path = quarterly_dir / db_name
                        if db_path.exists():
                            print(f"📂 Found database: {db_path}")
                            return str(db_path.resolve())
            
            # Fall back to common database locations (legacy)
            common_paths = [
                "data/skill_similarity_database.db",
                "skill_similarity_database.db",
                "data/workforce_intelligence.db",
                "workforce_intelligence.db",
                "data/business_context.sqlite",
                "business_context.sqlite"
            ]
            
            for common_path in common_paths:
                db_path = Path(common_path)
                if db_path.exists():
                    print(f"📂 Found database: {db_path}")
                    return str(db_path.resolve())
            
            # Also search all subdirectories of models/ for any .sqlite or .db files
            if models_dir.exists():
                for db_file in models_dir.rglob("*.sqlite"):
                    if db_file.is_file():
                        print(f"📂 Found database: {db_file}")
                        return str(db_file.resolve())
                for db_file in models_dir.rglob("*.db"):
                    if db_file.is_file():
                        print(f"📂 Found database: {db_file}")
                        return str(db_file.resolve())
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding database path: {e}")
            return None
    
    def _show_export_menu(self) -> str:
        """Display the export options menu."""
        print("\n=== Analytics Export Options ===")
        print("Choose what to export:\n")
        print("1. Export all analytics tables (recommended)")
        print("2. Export specific tables (interactive selection)")
        print("3. Show table information only")
        print("0. Cancel export")
        
        return input("Enter your choice: ").strip()
    
    def _show_table_selection_menu(self, table_info: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Show table selection menu and return selected tables.
        
        Args:
            table_info: Dictionary of table information
            
        Returns:
            List of selected table names
        """
        from ...data.exporter import AnalyticsExporter
        
        print("\n=== Available Analytics Tables ===")
        print("Select tables to export (enter numbers separated by commas, or 'all'):\n")
        
        table_list = list(AnalyticsExporter.ANALYTICS_TABLES.keys())
        
        for i, table_name in enumerate(table_list, 1):
            info = table_info.get(table_name, {})
            row_count = info.get('row_count', 0)
            size_category = info.get('size_category', 'unknown')
            exists = info.get('exists', False)
            
            status = "✅" if exists and row_count > 0 else "📊" if exists else "❌"
            print(f"{i:2}. {status} {table_name}")
            print(f"      {row_count:,} rows, {size_category} table")
        
        print(f"\n{len(table_list) + 1}. Select all tables")
        print("0. Cancel selection")
        
        while True:
            selection = input("\nEnter your selection: ").strip().lower()
            
            if selection == '0':
                return []
            elif selection == 'all' or selection == str(len(table_list) + 1):
                return table_list
            else:
                try:
                    # Parse comma-separated numbers
                    selected_indices = [int(x.strip()) for x in selection.split(',')]
                    selected_tables = []
                    
                    for idx in selected_indices:
                        if 1 <= idx <= len(table_list):
                            selected_tables.append(table_list[idx - 1])
                        else:
                            print(f"❌ Invalid selection: {idx}. Please try again.")
                            break
                    else:
                        return selected_tables
                        
                except ValueError:
                    print("❌ Invalid input. Please enter numbers separated by commas.")
    
    def _display_table_info(self, table_info: Dict[str, Dict[str, Any]]) -> None:
        """Display information about available analytics tables."""
        from ...data.exporter import AnalyticsExporter
        
        print("\n" + "="*80)
        print("📊 ANALYTICS TABLES INFORMATION")
        print("="*80)
        
        total_tables = len(AnalyticsExporter.ANALYTICS_TABLES)
        tables_with_data = sum(1 for info in table_info.values() if info.get('row_count', 0) > 0)
        total_rows = sum(info.get('row_count', 0) for info in table_info.values())
        
        print(f"📋 Summary: {tables_with_data}/{total_tables} tables contain data")
        print(f"📊 Total rows across all tables: {total_rows:,}")
        print()
        
        for table_name, info in table_info.items():
            row_count = info.get('row_count', 0)
            column_count = info.get('column_count', 0)
            size_category = info.get('size_category', 'unknown')
            exists = info.get('exists', False)
            
            status_icon = "✅" if exists and row_count > 0 else "📊" if exists else "❌"
            status_text = "Has data" if row_count > 0 else "Empty" if exists else "Missing"
            
            print(f"{status_icon} {table_name}")
            print(f"   📈 {row_count:,} rows, {column_count} columns")
            print(f"   🏷️  {size_category.title()} table, {status_text}")
            
            if 'error' in info:
                print(f"   ⚠️  Error: {info['error']}")
            print()
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute analytics export.
        
        Returns:
            CommandResult with export status
        """
        try:
            print("\n🚀 Analytics Export Tool")
            print("="*60)
            print("📤 Export analytics tables to CSV files for external analysis")
            print("   Each table will be exported to a separate timestamped CSV file")
            print()
            
            # Find database path
            db_path = self._find_database_path()
            if not db_path:
                print("❌ No database found!")
                print("   Please ensure your workforce database has been built first.")
                print("   Use the 'Build Workforce Database' option from the main menu.")
                
                return CommandResult(
                    success=False,
                    message="Database not found",
                    errors=["No accessible database file found"]
                )
            
            print(f"📂 Database: {db_path}")
            
            # Import and initialize exporter
            from ...data.exporter import AnalyticsExporter
            
            try:
                exporter = AnalyticsExporter(db_path)
                print(f"📁 Export directory: {exporter.output_dir}")
            except FileNotFoundError as e:
                print(f"❌ Database error: {e}")
                return CommandResult(
                    success=False,
                    message="Database access error",
                    errors=[str(e)]
                )
            
            # Get table information
            print("\n🔍 Analysing available tables...")
            table_info = exporter.get_table_info()
            
            # Show export menu
            choice = self._show_export_menu()
            
            if choice == '1':
                # Export all tables
                print("\n📤 Exporting all analytics tables...")
                selected_tables = None
                
            elif choice == '2':
                # Interactive table selection
                selected_tables = self._show_table_selection_menu(table_info)
                if not selected_tables:
                    print("❌ Export cancelled - no tables selected.")
                    return CommandResult(
                        success=False,
                        message="Export cancelled by user"
                    )
                
            elif choice == '3':
                # Show table information only
                self._display_table_info(table_info)
                print("💡 Use the export options above to export specific tables.")
                return CommandResult(
                    success=True,
                    message="Table information displayed",
                    data={'table_info': table_info}
                )
                
            elif choice == '0':
                print("❌ Export cancelled.")
                return CommandResult(
                    success=False,
                    message="Export cancelled by user"
                )
            else:
                print("❌ Invalid choice. Export cancelled.")
                return CommandResult(
                    success=False,
                    message="Invalid choice",
                    errors=["Invalid menu selection"]
                )
            
            # Perform the export
            summary = exporter.export_all_tables(selected_tables)
            
            # Display results
            print(f"\n✅ Analytics export completed!")
            print(f"📁 Output directory: {summary['output_directory']}")
            print(f"📊 Export summary:")
            print(f"   • Tables exported: {summary['successful_exports']}/{summary['tables_requested']}")
            print(f"   • Total rows: {summary['total_rows_exported']:,}")
            print(f"   • Total file size: {summary['total_file_size_mb']:.2f} MB")
            
            if summary['failed_exports'] > 0:
                print(f"   ⚠️  Failed exports: {summary['failed_exports']}")
                
            print(f"\n📅 Export timestamp: {summary['export_timestamp']}")
            print("💡 CSV files are ready for analysis in Excel, R, Python, or other tools!")
            
            return CommandResult(
                success=True,
                message="Analytics export completed successfully",
                data=summary,
                metadata={
                    'export_directory': summary['output_directory'],
                    'tables_exported': summary['successful_exports'],
                    'total_rows': summary['total_rows_exported']
                }
            )
            
        except Exception as e:
            print(f"❌ Analytics export failed: {e}")
            print("   Check your database and permissions.")
            logger.error(f"Analytics export error: {e}", exc_info=True)
            return CommandResult(
                success=False,
                message=f"Analytics export failed: {str(e)}",
                errors=[str(e)]
            )