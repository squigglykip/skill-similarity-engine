"""
Business Context Database Orchestrator

Provides CLI integration and workflow coordination for generating comprehensive
SQLite databases with job similarities and business context data.

Integrates with existing main.py menu system and model versioning infrastructure.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .schema_builder import SchemaBuilder
from .data_loader import DataLoader
from .similarity_integrator import SimilarityIntegrator
from .validator import DatabaseValidator

# Import existing infrastructure
from skill_similarity_engine.models.versioning import ModelVersionManager

logger = logging.getLogger(__name__)


class BusinessContextOrchestrator:
    """Orchestrates business context database generation workflow."""
    
    def __init__(self, 
                 base_models_dir: str = "models",
                 data_root_dir: str = "data"):
        """
        Initialize orchestrator.
        
        Args:
            base_models_dir: Base directory for model outputs
            data_root_dir: Root directory for CSV data sources
        """
        self.base_models_dir = Path(base_models_dir)
        self.data_root_dir = Path(data_root_dir)
        self.version_manager = ModelVersionManager(str(base_models_dir))
        self.workflow_stats = {}
        
    def show_business_context_menu(self) -> str:
        """
        Display business context generation menu.
        
        Returns:
            User's menu choice
        """
        print("\n=== Business Context Database Generation ===")
        print("Generate comprehensive SQLite database with job similarities and business context")
        print()
        print("Options:")
        print("1. Create database schema only")
        print("2. Load job architecture data")
        print("3. Load skills library data")
        print("4. Load workforce context data")
        print("5. Load job-skill mapping data") 
        print("6. Load similarity matrices")
        print("7. Validate database integrity")
        print("8. Generate complete database (all steps)")
        print("9. Show database statistics")
        print("0. Back to main menu")
        print()
        
        return input("Enter your choice: ").strip()
    
    def handle_business_context_menu(self) -> None:
        """Handle business context menu interactions."""
        while True:
            choice = self.show_business_context_menu()
            
            if choice == '1':
                self._create_schema_only()
            elif choice == '2':
                self._load_job_architecture_data()
            elif choice == '3':
                self._load_skills_library_data()
            elif choice == '4':
                self._load_workforce_context_data()
            elif choice == '5':
                self._load_job_skill_mapping_data()
            elif choice == '6':
                self._load_similarity_matrices()
            elif choice == '7':
                self._validate_database_integrity()
            elif choice == '8':
                self._generate_complete_database()
            elif choice == '9':
                self._show_database_statistics()
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please enter a valid option.")
    
    def _get_database_path(self, interactive: bool = True) -> Optional[Path]:
        """Get the path for the business context database."""
        try:
            # Use existing model versioning system with business_context output type
            quarter_dir = self.version_manager.setup_output_directory(
                interactive=interactive,
                output_type="business_context"
            )
            db_path = quarter_dir / "business_context.sqlite"
            
            logger.info(f"Database path: {db_path}")
            return db_path
            
        except Exception as e:
            logger.error(f"Failed to setup database path: {e}")
            print(f"[ERROR] Could not setup database path: {e}")
            return None
    
    def _create_schema_only(self) -> None:
        """Create database schema only."""
        print("\n=== Create Database Schema ===")
        
        db_path = self._get_database_path()
        if not db_path:
            return
        
        print(f"Creating schema at: {db_path}")
        
        # Ask about dropping existing tables
        drop_existing = False
        if db_path.exists():
            print(f"Database file already exists: {db_path}")
            response = input("Drop existing tables? [y/N]: ").strip().lower()
            drop_existing = response in ('y', 'yes')
        
        try:
            schema_builder = SchemaBuilder(str(db_path))
            
            logger.info("Creating database schema...")
            success = schema_builder.create_schema(drop_existing=drop_existing)
            
            if success:
                print("✓ Database schema created successfully")
                
                # Validate schema
                if schema_builder.validate_schema():
                    print("✓ Schema validation passed")
                    
                    # Show table info
                    table_info = schema_builder.get_table_info()
                    print("\nTables created:")
                    for table, count in table_info.items():
                        if table != 'schema_metadata':
                            print(f"  - {table}: {count} rows")
                else:
                    print("⚠ Schema validation failed")
            else:
                print("✗ Failed to create database schema")
                
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            print(f"[ERROR] Schema creation failed: {e}")
    
    def _load_job_architecture_data(self) -> None:
        """Load job architecture data."""
        print("\n=== Load Job Architecture Data ===")
        
        db_path = self._get_database_path()
        if not db_path or not db_path.exists():
            print("[ERROR] Database not found. Create schema first (option 1).")
            return
        
        data_file = self.data_root_dir / "job_architecture" / "dummy_job_architecture.csv"
        print(f"Loading from: {data_file}")
        
        if not data_file.exists():
            print(f"[ERROR] Data file not found: {data_file}")
            return
        
        try:
            data_loader = DataLoader(str(db_path))
            success = data_loader.load_single_dataset('jobs', str(data_file))
            
            if success:
                stats = data_loader.get_load_statistics()
                job_stats = stats.get('jobs', {})
                print(f"✓ Loaded {job_stats.get('rows_loaded', 0):,} job records")
            else:
                print("✗ Failed to load job architecture data")
                
        except Exception as e:
            logger.error(f"Job architecture loading failed: {e}")
            print(f"[ERROR] Job architecture loading failed: {e}")
    
    def _load_skills_library_data(self) -> None:
        """Load skills library data."""
        print("\n=== Load Skills Library Data ===")
        
        db_path = self._get_database_path()
        if not db_path or not db_path.exists():
            print("[ERROR] Database not found. Create schema first (option 1).")
            return
        
        data_file = self.data_root_dir / "skills_library" / "lightcast_skills_comprehensive.csv"
        print(f"Loading from: {data_file}")
        
        if not data_file.exists():
            print(f"[ERROR] Data file not found: {data_file}")
            return
        
        try:
            data_loader = DataLoader(str(db_path))
            
            print("Loading skills library (this may take a moment for large files)...")
            success = data_loader.load_single_dataset('skills', str(data_file))
            
            if success:
                stats = data_loader.get_load_statistics()
                skills_stats = stats.get('skills', {})
                print(f"✓ Loaded {skills_stats.get('rows_loaded', 0):,} skill records")
            else:
                print("✗ Failed to load skills library data")
                
        except Exception as e:
            logger.error(f"Skills library loading failed: {e}")
            print(f"[ERROR] Skills library loading failed: {e}")
    
    def _load_workforce_context_data(self) -> None:
        """Load workforce context data."""
        print("\n=== Load Workforce Context Data ===")
        
        db_path = self._get_database_path()
        if not db_path or not db_path.exists():
            print("[ERROR] Database not found. Create schema first (option 1).")
            return
        
        data_file = self.data_root_dir / "workforce_context" / "dummy_workforce_context.csv"
        print(f"Loading from: {data_file}")
        
        if not data_file.exists():
            print(f"[ERROR] Data file not found: {data_file}")
            return
        
        try:
            data_loader = DataLoader(str(db_path))
            success = data_loader.load_single_dataset('positions', str(data_file))
            
            if success:
                stats = data_loader.get_load_statistics()
                positions_stats = stats.get('positions', {})
                print(f"✓ Loaded {positions_stats.get('rows_loaded', 0):,} position records")
            else:
                print("✗ Failed to load workforce context data")
                
        except Exception as e:
            logger.error(f"Workforce context loading failed: {e}")
            print(f"[ERROR] Workforce context loading failed: {e}")
    
    def _load_job_skill_mapping_data(self) -> None:
        """Load job-skill mapping data."""
        print("\n=== Load Job-Skill Mapping Data ===")
        
        db_path = self._get_database_path()
        if not db_path or not db_path.exists():
            print("[ERROR] Database not found. Create schema first (option 1).")
            return
        
        data_file = self.data_root_dir / "input_data" / "job_skill_mapping.csv"
        print(f"Loading from: {data_file}")
        
        if not data_file.exists():
            print(f"[ERROR] Data file not found: {data_file}")
            return
        
        try:
            data_loader = DataLoader(str(db_path))
            success = data_loader.load_single_dataset('job_skills', str(data_file))
            
            if success:
                stats = data_loader.get_load_statistics()
                job_skills_stats = stats.get('job_skills', {})
                print(f"✓ Loaded {job_skills_stats.get('rows_loaded', 0):,} job-skill mappings")
            else:
                print("✗ Failed to load job-skill mapping data")
                
        except Exception as e:
            logger.error(f"Job-skill mapping loading failed: {e}")
            print(f"[ERROR] Job-skill mapping loading failed: {e}")
    
    def _load_similarity_matrices(self) -> None:
        """Load pre-computed similarity matrices."""
        print("\n=== Load Similarity Matrices ===")
        
        db_path = self._get_database_path()
        if not db_path or not db_path.exists():
            print("[ERROR] Database not found. Create schema first (option 1).")
            return
        
        try:
            similarity_integrator = SimilarityIntegrator(str(db_path))
            
            # Find available similarity files
            similarity_files = similarity_integrator.find_similarity_files(str(self.base_models_dir))
            
            if not similarity_files:
                print("[ERROR] No similarity matrix files found.")
                print("Run similarity computation first (main menu option 1).")
                return
            
            # Show available files
            print("Available similarity matrix files:")
            for i, file_path in enumerate(similarity_files[:5], 1):  # Show top 5
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                print(f"  {i}. {file_path} ({mod_time.strftime('%Y-%m-%d %H:%M')})")
            
            if len(similarity_files) > 5:
                print(f"  ... and {len(similarity_files) - 5} more")
            
            # Let user choose or use latest
            choice = input(f"\nUse latest file? [Y/n] or enter number [1-{min(5, len(similarity_files))}]: ").strip()
            
            if choice.lower() in ('n', 'no'):
                return
            elif choice.isdigit() and 1 <= int(choice) <= min(5, len(similarity_files)):
                selected_file = similarity_files[int(choice) - 1]
            else:
                selected_file = similarity_files[0]  # Latest
            
            print(f"Loading similarity matrix from: {selected_file}")
            
            success = similarity_integrator.load_similarity_matrix(str(selected_file))
            
            if success:
                stats = similarity_integrator.get_integration_statistics()
                print(f"✓ Loaded {stats.get('total_similarity_pairs', 0):,} similarity pairs")
                print(f"  Coverage: {stats.get('unique_jobs_total', 0):,} unique jobs")
                print(f"  Average similarity: {stats.get('avg_similarity_score', 0):.3f}")
            else:
                print("✗ Failed to load similarity matrices")
                
        except Exception as e:
            logger.error(f"Similarity matrix loading failed: {e}")
            print(f"[ERROR] Similarity matrix loading failed: {e}")
    
    def _validate_database_integrity(self) -> None:
        """Validate database integrity."""
        print("\n=== Validate Database Integrity ===")
        
        db_path = self._get_database_path()
        if not db_path or not db_path.exists():
            print("[ERROR] Database not found. Create schema first (option 1).")
            return
        
        try:
            validator = DatabaseValidator(str(db_path))
            
            print("Running comprehensive database validation...")
            results = validator.run_full_validation()
            
            # Results are already printed by validator
            
            # Offer to save detailed report
            if results.get('overall_status') in ['FAIL', 'WARNING']:
                save_report = input("\nSave detailed validation report? [y/N]: ").strip().lower()
                if save_report in ('y', 'yes'):
                    report_path = db_path.parent / "validation_report.md"
                    validator.generate_validation_report(str(report_path))
                    print(f"Report saved to: {report_path}")
                    
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            print(f"[ERROR] Database validation failed: {e}")
    
    def _generate_complete_database(self) -> None:
        """Generate complete database with all data."""
        print("\n=== Generate Complete Business Context Database ===")
        print("This will create schema and load all data sources...")
        
        # Confirm before proceeding
        proceed = input("Continue with complete database generation? [y/N]: ").strip().lower()
        if proceed not in ('y', 'yes'):
            print("Operation cancelled.")
            return
        
        start_time = datetime.now()
        
        try:
            # Step 1: Create schema
            print("\n[1/6] Creating database schema...")
            db_path = self._get_database_path()
            if not db_path:
                return
            
            schema_builder = SchemaBuilder(str(db_path))
            if not schema_builder.create_schema(drop_existing=True):
                print("✗ Schema creation failed")
                return
            print("✓ Schema created")
            
            # Step 2: Load all CSV data
            print("\n[2/6] Loading all CSV data sources...")
            data_loader = DataLoader(str(db_path))
            if not data_loader.load_all_data(str(self.data_root_dir)):
                print("✗ Data loading failed")
                return
            print("✓ All CSV data loaded")
            
            # Step 3: Load similarity matrices
            print("\n[3/6] Loading similarity matrices...")
            similarity_integrator = SimilarityIntegrator(str(db_path))
            latest_similarity_file = similarity_integrator.get_latest_similarity_file(str(self.base_models_dir))
            
            if latest_similarity_file:
                if not similarity_integrator.load_similarity_matrix(str(latest_similarity_file)):
                    print("✗ Similarity matrix loading failed")
                    return
                print("✓ Similarity matrices loaded")
            else:
                print("⚠ No similarity matrices found - database will be incomplete")
                print("  Run similarity computation first (main menu option 1)")
            
            # Step 4: Validate database
            print("\n[4/6] Validating database integrity...")
            validator = DatabaseValidator(str(db_path))
            validation_results = validator.run_full_validation()
            
            if validation_results.get('overall_status') == 'FAIL':
                print("✗ Database validation failed")
                return
            elif validation_results.get('overall_status') == 'WARNING':
                print("⚠ Database validation passed with warnings")
            else:
                print("✓ Database validation passed")
            
            # Step 5: Generate statistics
            print("\n[5/6] Generating database statistics...")
            self._collect_final_statistics(db_path)
            
            # Step 6: Complete
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\n[6/6] Database generation complete!")
            print(f"✓ Business context database created: {db_path}")
            print(f"✓ Generation time: {duration.total_seconds():.1f} seconds")
            
            # Show summary statistics
            self._print_final_summary()
            
        except Exception as e:
            logger.error(f"Complete database generation failed: {e}")
            print(f"[ERROR] Complete database generation failed: {e}")
    
    def _show_database_statistics(self) -> None:
        """Show database statistics."""
        print("\n=== Database Statistics ===")
        
        db_path = self._get_database_path()
        if not db_path or not db_path.exists():
            print("[ERROR] Database not found. Create database first (option 8).")
            return
        
        try:
            schema_builder = SchemaBuilder(str(db_path))
            table_info = schema_builder.get_table_info()
            
            print(f"Database: {db_path}")
            print(f"Size: {db_path.stat().st_size / (1024*1024):.1f} MB")
            print()
            
            print("Table Statistics:")
            total_rows = 0
            for table, count in table_info.items():
                if table != 'schema_metadata':
                    if isinstance(count, int):
                        total_rows += count
                        print(f"  {table}: {count:,} rows")
                    else:
                        print(f"  {table}: {count}")
            
            print(f"\nTotal data rows: {total_rows:,}")
            
            # Show similarity distribution if available
            if table_info.get('job_similarities', 0) > 0:
                similarity_integrator = SimilarityIntegrator(str(db_path))
                distribution = similarity_integrator.analyze_similarity_distribution()
                
                if 'error' not in distribution:
                    print(f"\nSimilarity Distribution:")
                    print(f"  High similarity (≥0.8): {distribution.get('high_similarity', 0):,} pairs")
                    print(f"  Medium similarity (0.6-0.8): {distribution.get('medium_similarity', 0):,} pairs")
                    print(f"  Moderate similarity (0.4-0.6): {distribution.get('moderate_similarity', 0):,} pairs")
                    print(f"  Low similarity (<0.4): {distribution.get('low_similarity', 0):,} pairs")
                    print(f"  Average score: {distribution.get('avg_score', 0):.3f}")
            
        except Exception as e:
            logger.error(f"Failed to show database statistics: {e}")
            print(f"[ERROR] Failed to show database statistics: {e}")
    
    def _collect_final_statistics(self, db_path: Path) -> None:
        """Collect final statistics for the workflow."""
        try:
            schema_builder = SchemaBuilder(str(db_path))
            table_info = schema_builder.get_table_info()
            
            self.workflow_stats = {
                'database_path': str(db_path),
                'database_size_mb': db_path.stat().st_size / (1024*1024),
                'table_info': table_info,
                'generation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to collect final statistics: {e}")
    
    def _print_final_summary(self) -> None:
        """Print final summary of database generation."""
        if not self.workflow_stats:
            return
        
        print("\n=== Final Database Summary ===")
        print(f"Database: {self.workflow_stats['database_path']}")
        print(f"Size: {self.workflow_stats['database_size_mb']:.1f} MB")
        print()
        
        table_info = self.workflow_stats.get('table_info', {})
        for table, count in table_info.items():
            if table != 'schema_metadata' and isinstance(count, int):
                print(f"  {table}: {count:,} rows")
        
        print("\n✓ Business context database ready for Flask webapp!")
        print("  Use this database for:")
        print("  - Career pathway exploration")
        print("  - Skills gap analysis") 
        print("  - Team transition planning")
        print("  - White paper generation")
        print("=" * 35) 