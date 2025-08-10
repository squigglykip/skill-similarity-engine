"""
Utility Commands for Data Management and Documentation

Contains CLI commands for utility operations, extracted from precompute_commands.py
and focused on database cleanup, Excel conversion, and documentation generation.
"""

from pathlib import Path
from typing import Any, Dict

from .base_command import BaseCommand, CommandResult
from ...config.architectural_config_manager import get_config_manager
from ...data_pipeline.excel_converter import ExcelConverter


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
