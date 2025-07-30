"""
NAB Workforce Intelligence Platform - Database Builder

This module provides the main orchestrator for building and managing
the workforce intelligence database, with a business-focused interface
designed for both technical and non-technical users.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

from ..config.architectural_config_manager import get_config_manager
from .schema_builder import SchemaBuilder
from .data_loader import DataLoader
from ..models.versioning import ModelVersionManager

class BusinessContextOrchestrator:
    """
    Main orchestrator for workforce database building and management.
    
    Provides an intuitive, business-focused interface that guides users
    through the natural workflow of building workforce intelligence.
    """
    
    def __init__(self, data_config_path: Optional[str] = None):
        """
        Initialize the workforce database orchestrator.

        Args:
            data_config_path: Optional path to data configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = get_config_manager()
        self.data_config_path = data_config_path
        
        # Load UI configuration
        self.ui_config = self.config_manager.get_nested_value(
            'business_context', 'orchestrator_ui', 
            default=self._get_fallback_ui_config()
        )
        
        self.logger.info("Workforce database orchestrator initialized")
    
    def _get_fallback_ui_config(self) -> Dict[str, Any]:
        """Provide fallback UI configuration if config file not available."""
        return {
            'menus': {
                'workforce_intelligence': {
                    'title': 'Build Workforce Database',
                    'options': {
                        'foundation_data': {
                            'number': '1',
                            'title': 'Load employee and job data',
                            'description': 'Import workforce information from CSV files'
                        }
                    }
                }
            },
            'messages': {
                'success': {
                    'foundation_loaded': '✅ Employee and job data loaded successfully'
                },
                'progress': {
                    'loading_foundation': '📊 Loading workforce data...'
                },
                'errors': {
                    'data_not_loaded': '❌ Workforce data not available'
                }
            },
            'formatting': {
                'separator': '=',
                'separator_length': 50,
                'indent': '   '
            }
        }
    
    def get_database_status(self) -> Dict[str, str]:
        """
        Determine current database status for display by checking versioned database.

        Returns:
            Dictionary with status information
        """
        status_indicators = self.ui_config.get('status_indicators', {}).get('database_states', {})
        
        try:
            # Check for versioned database using ModelVersionManager
            version_manager = ModelVersionManager()
            
            # Get the current quarterly directory where business_context.sqlite should be
            current_quarter = version_manager.get_current_quarter()
            quarterly_dir = version_manager.base_models_dir / current_quarter
            db_path = quarterly_dir / 'business_context.sqlite'
            
            if db_path.exists():
                # Database exists, check if it has data
                try:
                    import sqlite3
                    with sqlite3.connect(str(db_path)) as conn:
                        cursor = conn.cursor()
                        # Check for core tables to verify it's properly loaded
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='core_job_architecture'")
                        if cursor.fetchone():
                            return status_indicators.get('ready', {
                                'icon': '✅',
                                'text': 'Ready',
                                'description': f'Database loaded at {db_path}',
                                'next_action': 'Ready for analysis and similarity calculations'
                            })
                        else:
                            return status_indicators.get('incomplete', {
                                'icon': '⚠️',
                                'text': 'Incomplete',
                                'description': f'Database exists but lacks core data at {db_path}',
                                'next_action': 'Load employee and job data to complete setup'
                            })
                except sqlite3.Error:
                    return status_indicators.get('corrupted', {
                        'icon': '❌',
                        'text': 'Error',
                        'description': f'Database file corrupted at {db_path}',
                        'next_action': 'Rebuild database by loading employee and job data'
                    })
            else:
                # Check if there's a database in any quarterly folder (fallback)
                for version_dir in version_manager.list_versions():
                    fallback_db = version_dir / 'business_context.sqlite'
                    if fallback_db.exists():
                        return status_indicators.get('different_version', {
                            'icon': '📁',
                            'text': 'Different Version',
                            'description': f'Database found in {version_dir.name} (not current quarter {current_quarter})',
                            'next_action': 'Load data to create current quarter database'
                        })
                
                # No database found anywhere
                return status_indicators.get('not_created', {
                    'icon': '❌',
                    'text': 'Not Created',
                    'description': 'No workforce database exists yet',
                    'next_action': 'Start by loading employee and job data'
                })
                
        except Exception as e:
            self.logger.error(f"Error checking database status: {e}")
            return status_indicators.get('error', {
                'icon': '❌',
                'text': 'Error',
                'description': 'Unable to check database status',
                'next_action': 'Check system configuration'
            })
    
    def show_workforce_intelligence_menu(self) -> str:
        """Display the main workforce database menu."""
        menu_config = self.ui_config.get('menus', {}).get('workforce_intelligence', {})
        formatting = self.ui_config.get('formatting', {})
        
        # Header
        title = menu_config.get('title', 'Build Workforce Database')
        subtitle = menu_config.get('subtitle', 'Create and populate your workforce intelligence database')
        separator = formatting.get('separator', '=') * formatting.get('separator_length', 50)
        
        print(f"\n{separator}")
        print(f"{title}")
        print(f"{subtitle}")
        print(f"{separator}")
        
        # Status
        db_status = self.get_database_status()
        print(f"\n{db_status.get('icon', '📊')} Database Status: {db_status.get('text', 'Unknown')}")
        if db_status.get('description'):
            print(f"{formatting.get('indent', '   ')}{db_status['description']}")
        print()
        
        # Menu options - use fallback if config not loaded properly
        options = menu_config.get('options', {})
        if not options:
            # Fallback menu options if config isn't loaded
            print("What would you like to do?")
            print("1. Load employee and job data")
            print("   Import workforce information from CSV files")
            print("2. Analyse job similarities")
            print("   Identify which jobs are similar to each other")
            print("   ℹ️  Employee and job data must be loaded first")
            print("3. Understand career movements")
            print("   Analyse how people move between roles")
            print("   ℹ️  Employee and job data must be loaded first")
            print("4. Create job families")
            print("   Group similar jobs into families")
            print("   ℹ️  Job similarity analysis must be completed first")
            print("5. Database tools")
            print("   Check status and manage your database")
            print("6. Create production database")
            print("   Build a complete database with real data")
            print("0. Back to main menu")
        else:
            print("What would you like to do?")
            
            # Foundation data
            if 'foundation_data' in options:
                opt = options['foundation_data']
                print(f"{opt.get('number', '1')}. {opt.get('title', 'Load data')}")
                print(f"{formatting.get('indent', '   ')}{opt.get('description', '')}")
            
            # Similarity analysis
            if 'similarity_analysis' in options:
                opt = options['similarity_analysis']
                print(f"{opt.get('number', '2')}. {opt.get('title', 'Analyse similarities')}")
                print(f"{formatting.get('indent', '   ')}{opt.get('description', '')}")
                if opt.get('requires'):
                    print(f"{formatting.get('indent', '   ')}ℹ️  {opt['requires']}")
            
            # Movement analysis
            if 'movement_analysis' in options:
                opt = options['movement_analysis']
                print(f"{opt.get('number', '3')}. {opt.get('title', 'Analyse movements')}")
                print(f"{formatting.get('indent', '   ')}{opt.get('description', '')}")
                if opt.get('requires'):
                    print(f"{formatting.get('indent', '   ')}ℹ️  {opt['requires']}")
            
            # Clustering analysis
            if 'clustering_analysis' in options:
                opt = options['clustering_analysis']
                print(f"{opt.get('number', '4')}. {opt.get('title', 'Create job families')}")
                print(f"{formatting.get('indent', '   ')}{opt.get('description', '')}")
                if opt.get('requires'):
                    print(f"{formatting.get('indent', '   ')}ℹ️  {opt['requires']}")
            
            # Database tools
            if 'database_tools' in options:
                opt = options['database_tools']
                print(f"{opt.get('number', '5')}. {opt.get('title', 'Database tools')}")
                print(f"{formatting.get('indent', '   ')}{opt.get('description', '')}")
            
            # Production database
            if 'production_database' in options:
                opt = options['production_database']
                print(f"{opt.get('number', '6')}. {opt.get('title', 'Create production database')}")
                print(f"{formatting.get('indent', '   ')}{opt.get('description', '')}")
            
            # Back option
            if 'back' in options:
                opt = options['back']
                print(f"{opt.get('number', '0')}. {opt.get('title', 'Back to main menu')}")
        
        print()
        
        # Show guidance
        if db_status.get('next_action'):
            messages = self.ui_config.get('messages', {}).get('info', {})
            guidance_prefix = messages.get('workflow_guidance', '💡 Recommended')
            print(f"{guidance_prefix}: {db_status['next_action']}")
        
        return input("Enter your choice: ").strip()
    
    def _load_foundation_data(self) -> None:
        """Load foundation workforce data with user-friendly messaging."""
        messages = self.ui_config.get('messages', {})
        progress_msgs = messages.get('progress', {})
        success_msgs = messages.get('success', {})
        error_msgs = messages.get('errors', {})
        
        try:
            # Progress message
            print(progress_msgs.get('loading_foundation', '📊 Loading workforce data...'))
            print(progress_msgs.get('loading_details', 'Importing employee records and job information from CSV files.'))
            print()
            
            # Check for skills library updates before loading (API → CSV → DB workflow)
            print("🔍 Checking skills library for updates...")
            try:
                from ..api.skills_updater import prompt_skills_update
                if not prompt_skills_update(self.logger):
                    print("⚠️  Skills library update failed, but continuing with existing data...")
            except ImportError:
                print("ℹ️  Skills updater not available - using existing skills library")
            except Exception as e:
                self.logger.warning(f"Skills update check failed: {e}")
                print("⚠️  Could not check for skills updates - using existing skills library")
            
            # Use versioning system to get proper quarterly database path
            version_manager = ModelVersionManager()
            output_dir = version_manager.setup_output_directory(
                interactive=False,  # Non-interactive for automated loading
                output_type='business_context'  # This ensures quarterly-level placement
            )
            db_path = output_dir / 'business_context.sqlite'
            
            print(f"📁 Database location: {db_path}")
            
            # Create schema with versioned path (drop existing for clean rebuild)
            schema_builder = SchemaBuilder(str(db_path))
            schema_builder.create_schema(drop_existing=True)
            
            # Load data (Phase 0: core data only, no analytics)
            data_loader = DataLoader(str(db_path))
            success = data_loader.load_all_data()

            if success:
                print(success_msgs.get('foundation_loaded', '✅ Employee and job data loaded successfully'))
                print(success_msgs.get('foundation_details', 'Your database now contains workforce information and is ready for analysis.'))
            else:
                print(error_msgs.get('general_error', '❌ An error occurred'))
                print("Failed to load foundation data. Please check the logs for details.")

        except Exception as e:
            self.logger.error(f"Foundation data loading failed: {e}")
            print(error_msgs.get('general_error', '❌ An error occurred'))
            print(f"Unable to load workforce data: {e}")
            print(error_msgs.get('contact_admin', 'Please contact your system administrator if this problem persists.'))
    
    def _generate_similarity_analysis(self) -> None:
        """Generate job similarity analysis with user-friendly messaging."""
        messages = self.ui_config.get('messages', {})
        progress_msgs = messages.get('progress', {})
        success_msgs = messages.get('success', {})
        error_msgs = messages.get('errors', {})
        
        try:
            print(progress_msgs.get('generating_similarity', '🧠 Generating job similarity analysis...'))
            print(progress_msgs.get('similarity_details', 'Identifying which jobs are similar based on required skills.'))
            print()
            
            # This would integrate with similarity generation modules
            print(error_msgs.get('feature_coming_soon', 'This feature is coming soon'))

        except Exception as e:
            self.logger.error(f"Similarity analysis failed: {e}")
            print(error_msgs.get('general_error', '❌ An error occurred'))
            print(f"Unable to generate similarity analysis: {e}")
    
    def _analyse_career_movements(self) -> None:
        """Analyse career movement patterns with user-friendly messaging."""
        messages = self.ui_config.get('messages', {})
        progress_msgs = messages.get('progress', {})
        error_msgs = messages.get('errors', {})
        
        try:
            print(progress_msgs.get('analysing_movement', '📈 Analysing career movement patterns...'))
            print(progress_msgs.get('movement_details', 'Examining how people typically move between different roles.'))
            print()
            
            # This would integrate with movement analysis modules
            print(error_msgs.get('feature_coming_soon', 'This feature is coming soon'))

        except Exception as e:
            self.logger.error(f"Movement analysis failed: {e}")
            print(error_msgs.get('general_error', '❌ An error occurred'))
            print(f"Unable to analyse career movements: {e}")
    
    def _create_job_families(self) -> None:
        """Create job family clusters with user-friendly messaging."""
        messages = self.ui_config.get('messages', {})
        error_msgs = messages.get('errors', {})
        
        try:
            print("🏗️ Creating job families...")
            print("   Using advanced algorithms to group similar jobs into meaningful career families.")
            print()
            
            # This would integrate with clustering modules
            print(error_msgs.get('feature_coming_soon', 'This feature is coming soon'))

        except Exception as e:
            self.logger.error(f"Job family creation failed: {e}")
            print(error_msgs.get('general_error', '❌ An error occurred'))
            print(f"Unable to create job families: {e}")
    
    def _show_database_tools(self) -> None:
        """Show database tools and status information."""
        print("\n=== Database Tools ===")
        print("Database maintenance and status information.\n")
        
        db_status = self.get_database_status()
        print(f"Current Status: {db_status.get('text', 'Unknown')}")
        print(f"Description: {db_status.get('description', 'No information available')}")
        print()
        
        print("Available Tools:")
        print("1. Check database health")
        print("2. View database summary")
        print("3. Export database backup")
        print("0. Back to database menu")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            print("🔍 Checking database health...")
            print("   This feature is coming soon.")
        elif choice == '2':
            print("📊 Generating database summary...")
            print("   This feature is coming soon.")
        elif choice == '3':
            print("💾 Exporting database backup...")
            print("   This feature is coming soon.")
        elif choice != '0':
            print("❌ Invalid choice. Please select a number from the menu.")
    
    def _create_production_database(self) -> None:
        """Create a production database with versioning."""
        messages = self.ui_config.get('messages', {})
        progress_msgs = messages.get('progress', {})
        success_msgs = messages.get('success', {})
        error_msgs = messages.get('errors', {})
        
        try:
            print(progress_msgs.get('creating_database', '🏗️ Creating production database...'))
            print(progress_msgs.get('database_details', 'Building a complete workforce intelligence database with real data.'))
            print()
            
            # Setup versioned output directory for business context
            version_manager = ModelVersionManager()
            output_dir = version_manager.setup_output_directory(
                interactive=False,
                output_type='business_context'  # This ensures quarterly-level placement
            )
            db_path = output_dir / 'business_context.sqlite'
            
            print(f"📁 Production database location: {db_path}")
            
            # Confirm with user
            confirm = input("Proceed with production database creation? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("❌ Production database creation cancelled.")
                return
            
            # Create schema
            print("🏗️ Creating database schema...")
            schema_builder = SchemaBuilder(str(db_path))
            schema_builder.create_schema(drop_existing=True)
            
            # Load data (Phase 0: core data only, no analytics)
            print("📊 Loading foundation data...")
            data_loader = DataLoader(str(db_path))
            success = data_loader.load_all_data()

            if success:
                print(success_msgs.get('database_created', '✅ Production database created successfully'))
                print(success_msgs.get('database_details', 'Your workforce intelligence database is ready for use.'))
                print(f"📁 Database saved to: {db_path}")
            else:
                print(error_msgs.get('general_error', '❌ An error occurred'))
                print("⚠️ Production database creation had issues")

        except Exception as e:
            self.logger.error(f"Production database creation failed: {e}")
            print(error_msgs.get('general_error', '❌ An error occurred'))
            print(f"Unable to create production database: {e}")
            print(error_msgs.get('contact_admin', 'Please contact your system administrator if this problem persists.'))
    
    def handle_workforce_intelligence_menu(self) -> None:
        """Handle the main workforce intelligence menu loop."""
        while True:
            choice = self.show_workforce_intelligence_menu()
            
            if choice == '1':
                self._load_foundation_data()
            elif choice == '2':
                self._generate_similarity_analysis()
            elif choice == '3':
                self._analyse_career_movements()
            elif choice == '4':
                self._create_job_families()
            elif choice == '5':
                self._show_database_tools()
            elif choice == '6':
                self._create_production_database()
            elif choice == '0':
                break
            else:
                error_msgs = self.ui_config.get('messages', {}).get('errors', {})
                print("❌ Invalid choice. Please select a number from the menu.")
            print()
            
            # Add spacing between operations
            if choice != '0':
                input("\nPress Enter to continue...")
        print()

