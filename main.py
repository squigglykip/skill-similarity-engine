#!/usr/bin/env python3

"""
NAB Workforce Intelligence Platform - Main Entry Point

This script provides an intuitive, business-focused interface for workforce
intelligence analysis, designed for both technical and non-technical users.
"""

import sys
import os
import warnings
from pathlib import Path

# Suppress warnings for cleaner user experience
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*subprocess.*")
warnings.filterwarnings("ignore", message=".*joblib.*")
warnings.filterwarnings("ignore", message=".*loky.*")

# Add the src directory to the Python path if not installed as a package
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.cli.utilities import print_banner, prompt_int
from skill_similarity_engine.cli.commands import (
    DataLoadCommand, SimilarityMatrixCommand, MovementAnalysisCommand, QuerySimilarityCommand
)
from skill_similarity_engine.cli.commands.precompute_commands import ExcelConverterCommand, SchemaDocumentationCommand
from skill_similarity_engine.workflows.session_manager import get_session_manager
from skill_similarity_engine.business_context import BusinessContextOrchestrator
from skill_similarity_engine.config.architectural_config_manager import get_config_manager

# Welcome banner
BANNER = r'''
███████╗██╗  ██╗██╗██╗     ██╗                                        
██╔════╝██║ ██╔╝██║██║     ██║                                        
███████╗█████╔╝ ██║██║     ██║                                        
╚════██║██╔═██╗ ██║██║     ██║                                        
███████║██║  ██╗██║███████╗███████╗                                   
╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝                                   
                                                                      
███████╗██╗███╗   ███╗██╗██╗      █████╗ ██████╗ ██╗████████╗██╗   ██╗
██╔════╝██║████╗ ████║██║██║     ██╔══██╗██╔══██╗██║╚══██╔══╝╚██╗ ██╔╝
███████╗██║██╔████╔██║██║██║     ███████║██████╔╝██║   ██║    ╚████╔╝ 
╚════██║██║██║╚██╔╝██║██║██║     ██╔══██║██╔══██╗██║   ██║     ╚██╔╝  
███████║██║██║ ╚═╝ ██║██║███████╗██║  ██║██║  ██║██║   ██║      ██║   
╚══════╝╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝   
                                                                      
███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗                      
██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝                      
█████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗                        
██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝                        
███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗                      
╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝       

NAB Workforce Intelligence Platform

'''


class WorkforceIntelligenceOrchestrator:
    """
    Main orchestrator for the NAB Workforce Intelligence Platform.
    
    Provides an intuitive, business-focused interface for workforce analysis
    that guides users through the natural workflow of building and using
    workforce intelligence.
    """
    
    def __init__(self):
        """Initialize the platform orchestrator."""
        self.session_manager = get_session_manager()
        
        # Initialize commands
        self.excel_converter_cmd = ExcelConverterCommand()
        self.schema_doc_cmd = SchemaDocumentationCommand()
        self.data_load_cmd = DataLoadCommand()
        self.similarity_cmd = SimilarityMatrixCommand()
        self.movement_cmd = MovementAnalysisCommand()
        self.query_cmd = QuerySimilarityCommand()
        
        print("🚀 Workforce Intelligence Platform initialized and ready!")
    
    def get_database_status(self) -> dict:
        """Get current database status for display."""
        session_summary = self.session_manager.get_session_summary()
        
        if not session_summary.get('session_exists', False):
            return {
                'status': 'Not Created',
                'description': 'No workforce database exists yet',
                'next_action': 'Start by building your workforce database'
            }
        elif session_summary.get('ready_for_similarity', False):
            return {
                'status': 'Foundation Ready', 
                'description': f"Core data loaded ({session_summary.get('skills_count', 0)} skills, {session_summary.get('jobs_count', 0)} jobs)",
                'next_action': 'Ready to generate career intelligence'
            }
        else:
            return {
                'status': 'In Progress',
                'description': 'Database partially built',
                'next_action': 'Continue building your database'
            }
    
    def show_main_menu(self) -> str:
        """Display the main platform menu with business-focused options."""
        print(BANNER)
        
        # Show database status
        db_status = self.get_database_status()
        print(f"📊 Database Status: {db_status['status']}")
        if db_status['description']:
            print(f"   {db_status['description']}")
        print()
        
        print("What would you like to do?")
        print("1. Data Pipeline Setup")
        print("2. Build Workforce Database")
        print("3. Generate Career Intelligence") 
        print("4. System Tools")
        print("0. Exit")
        print()
        
        # Show contextual guidance
        if db_status['next_action']:
            print(f"💡 Recommended: {db_status['next_action']}")
        
        return input("Enter your choice: ").strip()
    
    def show_legacy_precompute_menu(self) -> str:
        """Display the legacy precompute menu for backward compatibility."""
        print("\n=== Advanced Analytics Tools ===")
        print("These tools generate analysis files for advanced users.\n")
        
        # Show data status
        session_summary = self.session_manager.get_session_summary()
        data_status = "✅ Data Ready" if session_summary.get('ready_for_similarity', False) else "❌ Data Not Loaded"
        print(f"Data Status: {data_status}")
        
        print("\nSelect a task:")
        print("1. Load and validate data")
        print("2. Generate similarity analysis files")
        print("3. Generate career movement analysis")
        print("4. Export results (coming soon)")
        print("0. Back to main menu")
        
        return input("Enter your choice: ").strip()
    
    def show_system_tools_menu(self) -> str:
        """Display system tools menu."""
        print("\n=== System Tools ===")
        print("Database maintenance and advanced options.\n")
        
        db_status = self.get_database_status()
        print(f"Database Status: {db_status['status']}")
        print()
        
        print("Available Tools:")
        print("1. Generate Database Schema Documentation")
        print("2. Check database health")
        print("3. View database summary") 
        print("4. Export database backup")
        print("5. Advanced analytics tools")
        print("6. System diagnostics")
        print("0. Back to main menu")
        
        return input("Enter your choice: ").strip()
    
    def handle_data_loading(self) -> None:
        """Handle data loading with user-friendly messaging."""
        try:
            print("📊 Loading workforce data...")
            print("   This will import employee records and job information from CSV files.")
            print()
            
            result = self.data_load_cmd.run()
            
            if result.success:
                # Load data into session manager
                if result.data and 'taxonomy' in result.data:
                    self.session_manager.load_taxonomy(result.data['taxonomy'])
                if result.data and 'architecture' in result.data:
                    self.session_manager.load_architecture(result.data['architecture'])
                
                print("✅ Workforce data loaded successfully!")
                print("   Your database now contains employee and job information.")
            else:
                print(f"❌ Failed to load workforce data: {result.message}")
                if result.errors:
                    print("   Issues encountered:")
                    for error in result.errors:
                        print(f"   • {error}")
                    
        except Exception as e:
            print(f"❌ Unable to load data: {e}")
            print("   Please check your data files and configuration.")
    
    def handle_similarity_generation(self) -> None:
        """Handle similarity analysis with user-friendly messaging."""
        # Check if data is loaded
        if not self.session_manager.is_data_ready_for_similarity():
            print("❌ Workforce data not available.")
            print("   Please load employee and job data first (option 1 in Build Database menu).")
            return
        
        try:
            print("🧠 Generating job similarity analysis...")
            print("   This will identify which jobs are similar to each other based on required skills.")
            print()
            
            architecture = self.session_manager.get_architecture()
            result = self.similarity_cmd.run(architecture=architecture)
            
            if result.success:
                print("✅ Job similarity analysis completed!")
                print("   The system can now identify similar career opportunities.")
                if result.data and 'output_path' in result.data:
                    print(f"   Analysis files saved to: {result.data['output_path']}")
            else:
                print(f"❌ Similarity analysis failed: {result.message}")
                if result.errors:
                    print("   Issues encountered:")
                    for error in result.errors:
                        print(f"   • {error}")
                    
        except Exception as e:
            print(f"❌ Unable to generate similarity analysis: {e}")
            print("   Please check that your data is properly loaded and configured.")
    
    def handle_movement_analysis(self) -> None:
        """Handle career movement analysis with user-friendly messaging."""
        try:
            print("📈 Analysing career movement patterns...")
            print("   This will examine how people typically move between different roles.")
            print()
            
            result = self.movement_cmd.run()
            
            if result.success:
                print("✅ Career movement analysis completed!")
                print("   The system now understands common career progression paths.")
                if result.data and 'output_path' in result.data:
                    print(f"   Analysis files saved to: {result.data['output_path']}")
            else:
                print(f"❌ Movement analysis failed: {result.message}")
                if result.errors:
                    print("   Issues encountered:")
                    for error in result.errors:
                        print(f"   • {error}")
                    
        except Exception as e:
            print(f"❌ Unable to analyse career movements: {e}")
            print("   Please ensure your movement data is available and properly formatted.")
    
    def handle_query_similarities(self) -> None:
        """Handle similarity queries with user-friendly messaging."""
        try:
            print("🔍 Preparing job similarity search...")
            print("   This will help you find jobs similar to any role you specify.")
            print()
            
            result = self.query_cmd.run()
            
            if result.success:
                print("✅ Search completed!")
            else:
                print(f"❌ Search failed: {result.message}")
                    
        except Exception as e:
            print(f"❌ Unable to search similarities: {e}")
            print("   Please check that similarity analysis has been completed first.")
    
    def handle_data_pipeline_setup(self) -> None:
        """Handle data pipeline setup - convert Excel to CSV."""
        try:
            print("\n" + "="*60)
            print("📊 DATA PIPELINE SETUP")
            print("="*60)
            print()
            print("🔄 This will convert your Excel workbook to organized CSV files.")
            print("   You will be prompted to specify the path to your Excel file.")
            print("   Supported formats: .xlsx, .xls, .xlsm")
            print()
            
            # Ask for confirmation
            confirm = input("   Proceed with Excel to CSV conversion? (y/N): ").strip().lower()
            if confirm != 'y':
                print("   Data pipeline setup cancelled.")
                print()
                return
            
            # Execute the Excel converter command
            result = self.excel_converter_cmd.execute()
            
            if result.success:
                print()
                print("✅ Data pipeline setup completed successfully!")
                print("   Your Excel data has been converted to CSV files in the data/ directory.")
                print("   You can now proceed to 'Build Workforce Database' (Option 1).")
            else:
                print()
                print("❌ Data pipeline setup failed.")
                if result.errors:
                    for error in result.errors:
                        print(f"   Error: {error}")
                print("   Please check your Excel file and try again.")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error during data pipeline setup: {e}")
            print("   Please check your Excel file and permissions.")
            input("\nPress Enter to continue...")
    
    def handle_workforce_intelligence(self) -> None:
        """Handle workforce database building - directly load employee and job data."""
        try:
            # Get configuration paths from architectural config manager
            config_manager = get_config_manager()
            config_search_paths = config_manager.get_nested_value(
                'business_context', 'database', 'file_discovery', 'config_search_paths',
                default=[]
            )
            
            # Find the actual config file path
            data_config_path = None
            for search_path in config_search_paths:
                path = Path(search_path)
                if path.exists():
                    data_config_path = str(path)
                    break
            
            if not data_config_path:
                print(f"❌ Configuration files not found.")
                print("   The system needs configuration files to locate your workforce data.")
                print(f"   Expected locations: {config_search_paths}")
                return
            
            # Create orchestrator and directly load foundation data
            orchestrator = BusinessContextOrchestrator(data_config_path=data_config_path)
            orchestrator._load_foundation_data()
            
        except Exception as e:
            print(f"❌ Unable to build database: {e}")
            print("   Please check your configuration and data files.")
            print("   Ensure all required CSV files are in the correct location.")
    
    def show_analytics_phases_menu(self) -> str:
        """Display analytics capabilities menu with user-friendly options."""
        print("\n=== Career Intelligence Generation ===")
        print("Generate advanced analytics directly into your database.\n")
        
        print("Select analytics capability:")
        print("1. Optimize Similarity Parameters (Run when data refreshed)")
        print("2. Enhanced Similarity Analytics")
        print("3. Generate Movement Analysis")  # NEW: Populate movement patterns
        print("4. Train Predictive Movement Models")  # NEW: ML training step 
        print("5. Optimize Job Clustering Parameters (Run when data refreshed)")
        print("6. Optimize Skills Clustering Parameters (Run when data refreshed)")
        print("7. Production Clustering Analytics (Job Families + Skill Bundles)")
        print("8. Skill Velocity Analysis")
        print("9. Job Architecture Health Diagnostics")
        print("10. Clear Unneeded Database Tables")
        print("11. Run All Capabilities (Recommended)")
        print("0. Back to main menu")
        
        return input("Enter your choice: ").strip()
    
    def handle_career_intelligence_generation(self) -> None:
        """Handle career intelligence generation with database integration."""
        try:
            # Initialize analytics orchestrator (auto-detects correct database path)
            from skill_similarity_engine.business_context.analytics_orchestrator import AnalyticsOrchestrator
            orchestrator = AnalyticsOrchestrator()
            
            # Check Phase 0 completion using orchestrator's verification
            if not orchestrator._verify_phase_0_completion():
                print("❌ Foundation database required. Please complete Phase 0 first.")
                print("   Use option 1 'Build Workforce Database' to create the foundation data.")
                return
            
            while True:
                choice = self.show_analytics_phases_menu()
                
                if choice == '1':
                    self.handle_similarity_optimization(orchestrator)
                elif choice == '2':
                    print("\n🧠 Executing Phase 1: Enhanced Similarity Analytics...")
                    print("   This will calculate enhanced job similarities using configuration-driven algorithms")
                    print("   with Optuna-optimized parameters and populate analytics tables directly in your database.")
                    
                    # Load actual configuration values for display
                    config_manager = get_config_manager()
                    similarity_config = config_manager.get_nested_value(
                        'core', 'similarity_parameters', 'optuna_optimal'
                    )
                    
                    if not similarity_config:
                        print("❌ Configuration Error: Missing core.similarity_parameters.optuna_optimal section")
                        print("   Please ensure config/core/similarity_parameters.yaml contains the required parameters.")
                        continue
                    
                    # Enhanced parameter display
                    opt_metadata = similarity_config.get('optimization_metadata', {})
                    print(f"   • Parameters: {similarity_config['defining_skills_percentile']}% defining skills threshold, {similarity_config['defining_skills_multiplier']}x multiplier")
                    print("   • Algorithm: Asymmetric Jaccard with corpus normalization")
                    
                    if opt_metadata:
                        print(f"   • Optimization Date: {opt_metadata.get('optimization_date', 'Unknown')}")
                        print(f"   • Selected Trial: {opt_metadata.get('selected_trial', 'Unknown')} (from {opt_metadata.get('trial_count', 'Unknown')} trials)")
                        print(f"   • Performance: {opt_metadata.get('smoothness_score', 0):.4f} smoothness, {opt_metadata.get('average_improvement', 0)*100:.1f}% avg improvement")
                        print(f"   • Quality Metrics: {opt_metadata.get('normalization_factor', 0):.1f} norm factor, {opt_metadata.get('scores_above_1_percent', 0):.1f}% scores >1.0")
                    print()
                    
                    success = orchestrator.execute_phase_1_enhanced_similarity()
                    if success:
                        print("✅ Phase 1 completed! Enhanced similarity data added to database.")
                        print("   Your database now contains:")
                        print("   • Enhanced job similarity calculations")
                        print("   • Skill rarity analysis")
                        print("   • Job-specific defining skills")
                    else:
                        print("❌ Phase 1 failed. Check logs for details.")
                        print("   This may be due to missing data or configuration issues.")
                        
                elif choice == '3':
                    print("\n📈 Generating Movement Analysis...")
                    print("   This will detect historical career movement patterns and populate")
                    print("   the analytics database with movement intelligence.")
                    print()
                    
                    success = orchestrator.execute_movement_pattern_analysis()
                    if success:
                        print("✅ Movement analysis completed! Movement patterns added to database.")
                        print("   Your database now contains career transition intelligence.")
                    else:
                        print("❌ Movement analysis failed. Check logs for details.")
                        
                elif choice == '4':
                    print("\n🤖 Training Predictive Movement Models...")
                    print("   This will train machine learning models to predict career")
                    print("   pathway feasibility and transition likelihood.")
                    print()
                    
                    success = orchestrator.execute_movement_ml_training()
                    if success:
                        print("✅ ML model training completed! Pathway predictions added to database.")
                        print("   Your database now contains:")
                        print("   • Trained ML models saved as .joblib files")
                        print("   • Pathway feasibility predictions for all job pairs")
                        print("   • Confidence intervals and model agreement metrics")
                    else:
                        print("❌ ML model training failed. Check logs for details.")
                        print("   This may be due to missing movement patterns or configuration issues.")
                    
                elif choice == '5':
                    self.handle_clustering_optimization(orchestrator)
                    
                elif choice == '6':
                    self.handle_skills_optimization(orchestrator)
                    
                elif choice == '7':
                    self.handle_clustering_analysis(orchestrator)
                    
                elif choice == '8':
                    self.handle_velocity_analysis(orchestrator)
                    
                elif choice == '9':
                    self.handle_diagnostics_analysis(orchestrator)
                    
                elif choice == '10':
                    self.handle_database_cleanup(orchestrator)
                    
                elif choice == '11':
                    print("\n🚀 Running All Capabilities...")
                    print("   This will execute all available analytics capabilities in sequence.")
                    print()
                    
                    # Step 1: Optimize Similarity Parameters
                    print("Step 1: Optimizing Similarity Parameters...")
                    self.handle_similarity_optimization(orchestrator)
                    
                    # Step 2: Enhanced Similarity Analytics
                    print("\nStep 2: Enhanced Similarity Analytics...")
                    similarity_success = orchestrator.execute_phase_1_enhanced_similarity()
                    if similarity_success:
                        print("✅ Enhanced similarity analytics completed")
                    else:
                        print("❌ Enhanced similarity analytics failed")
                    
                    # Step 3: Generate Movement Analysis
                    print("\nStep 3: Movement Analysis...")
                    movement_success = orchestrator.execute_movement_pattern_analysis()
                    if movement_success:
                        print("✅ Movement analysis completed")
                    else:
                        print("⚠️ Movement analysis failed")
                    
                    # Step 4: Train Predictive Movement Models
                    print("\nStep 4: ML Model Training...")
                    ml_success = orchestrator.execute_movement_ml_training()
                    if ml_success:
                        print("✅ ML model training completed")
                    else:
                        print("⚠️ ML model training failed")
                    
                    # Step 5: Optimize Job Clustering Parameters
                    print("\nStep 5: Optimizing Job Clustering Parameters...")
                    self.handle_clustering_optimization(orchestrator)
                    
                    # Step 6: Optimize Skills Clustering Parameters
                    print("\nStep 6: Optimizing Skills Clustering Parameters...")
                    self.handle_skills_optimization(orchestrator)
                    
                    # Step 7: Production Clustering Analytics
                    print("\nStep 7: Strategic Clustering...")
                    self.handle_clustering_analysis(orchestrator)
                    
                    # Step 8: Skill Velocity Analysis
                    print("\nStep 8: Skill Velocity Analysis...")
                    self.handle_velocity_analysis(orchestrator)
                    
                    # Step 9: Job Architecture Health Diagnostics
                    print("\nStep 9: Job Architecture Health Diagnostics...")
                    self.handle_diagnostics_analysis(orchestrator)
                    
                    # Step 10: Clear Unneeded Database Tables
                    print("\nStep 10: Cleaning up large intermediate tables...")
                    self.handle_database_cleanup(orchestrator)
                    
                    # Summary
                    print(f"\n✅ All analytics capabilities completed! Your database now contains enhanced analytics.")
                    print("   Career intelligence data is available for queries and applications.")
                    print("   Database has been optimized by removing large intermediate tables.")
                        
                elif choice == '0':
                    break
                else:
                    print("❌ Invalid choice. Please select a number from the menu.")
                
                if choice != '0':
                    input("\nPress Enter to continue...")
                    
        except Exception as e:
            print(f"❌ Unable to generate career intelligence: {e}")
            print("   Please check that your foundation database is properly configured.")
            print("   Ensure the workforce database has been built successfully first.")
    
    def handle_similarity_optimization(self, orchestrator) -> None:
        """Handle similarity parameter optimization using Optuna"""
        print("\n🎯 Optimizing Similarity Parameters...")
        print("   This will use Bayesian optimization to find optimal parameters for similarity calculations.")
        print("   The system will first analyze your data to determine the optimal number of trials needed.")
        print("   The process may take 10-30 minutes and will completely replace your current configuration.")
        print()
        
        try:
            from skill_similarity_engine.optimization import OptunaSimilarityOptimizer
            
            if not OptunaSimilarityOptimizer.is_available():
                print("❌ Optuna optimization not available.")
                print("   Install with: pip install optuna")
                print("   Or continue with existing parameters.")
                return
            
            # Get database path from orchestrator
            db_path = str(orchestrator.db_path)
            
            # Confirm with user since this overwrites config
            print(f"⚠️  This will completely replace config/core/similarity_parameters.yaml")
            print(f"   Database: {db_path}")
            
            confirm = input("   Continue? (y/N): ").strip().lower()
            if confirm != 'y':
                print("   Optimization cancelled.")
                return
            
            # Run optimization with progress feedback
            print("🔍 Initializing optimization engine...")
            optimizer = OptunaSimilarityOptimizer(db_path)
            print("📊 Starting corpus analysis and optimization...")
            success = optimizer.optimize_and_update()
            
            if success:
                # Reload configuration to pick up new parameters
                config_manager = get_config_manager()
                config_manager.reload_configuration()
                
                print("✅ Parameter optimization completed successfully!")
                print("   Enhanced Similarity Analytics will now use the optimized parameters.")
                print("   You can proceed to run Enhanced Similarity Analytics (option 2).")
            else:
                print("❌ Parameter optimization failed.")
                
        except ImportError:
            print("❌ Optimization module not available.")
            print("   Optuna dependency may be missing: pip install optuna")
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            print("   Continue with existing parameters or check your database.")
    
    def handle_clustering_optimization(self, orchestrator) -> None:
        """Handle clustering parameter optimization using systematic analysis."""
        print("\n🎯 Optimizing Clustering Parameters...")
        print("   This will analyze your data to find optimal clustering parameters for:")
        print("   • Job profile clustering (DBSCAN eps/min_samples)")
        print("   • Skills clustering and bundling parameters")
        print("   • Silhouette analysis across parameter ranges")
        print("   The process will update your configuration with optimized parameters.")
        print()
        
        try:
            from skill_similarity_engine.cli.commands.precompute_commands import ClusteringOptimizationCommand
            
            # Get database path from orchestrator
            db_path = str(orchestrator.db_path)
            
            # Confirm with user since this overwrites config
            print(f"⚠️  This will update config/core/clustering_analysis.yaml")
            print(f"   Database: {db_path}")
            
            confirm = input("   Continue? (y/N): ").strip().lower()
            if confirm != 'y':
                print("   Optimization cancelled.")
                return
            
            # Run optimization command
            print("🔍 Initializing clustering parameter optimizer...")
            command = ClusteringOptimizationCommand()
            result = command.execute(auto_confirm=True)
            
            if result.success:
                print("✅ Clustering parameter optimization completed successfully!")
                print("   Updated configuration with optimal parameters based on your data.")
                print("   You can now run 'Strategic Clustering Analytics' (option 6).")
            else:
                print("❌ Clustering parameter optimization failed.")
                print("   Check your database and ensure job similarity data exists.")
                
        except ImportError:
            print("❌ Clustering optimization module not available.")
            print("   Required dependencies may be missing.")
        except Exception as e:
            print(f"❌ Clustering optimization failed: {e}")
            print("   Check your database and configuration.")
    
    def handle_skills_optimization(self, orchestrator) -> None:
        """Handle skills clustering parameter optimization with multiple algorithms."""
        print("\n🔗 Optimizing Skills Clustering Parameters...")
        print("   This will analyze your skills data to find optimal parameters for:")
        print("   • DBSCAN parameters (eps/min_samples)")
        print("   • Hierarchical clustering (n_clusters/linkage)")
        print("   • K-means parameters (n_clusters)")
        print("   • Multiple similarity measures (Jaccard, Cosine, Combined)")
        print("   • Taxonomy alignment validation")
        print()
        
        try:
            from skill_similarity_engine.cli.commands.precompute_commands import SkillsOptimizationCommand
            
            # Get database path from orchestrator
            db_path = str(orchestrator.db_path)
            
            print(f"📂 Database: {db_path}")
            print()
            print("⚠️  This comprehensive optimization will test multiple algorithms")
            print("   and similarity measures to find the best configuration.")
            
            confirm = input("   Continue? (y/N): ").strip().lower()
            if confirm != 'y':
                print("   Optimization cancelled.")
                return
            
            # Run skills optimization command
            print("🔍 Initializing skills parameter optimizer...")
            command = SkillsOptimizationCommand()
            result = command.execute(db_path=db_path)
            
            if result.success:
                print("✅ Skills parameter optimization completed successfully!")
                print("   Found optimal configuration for skills clustering.")
                
                # Display results if available
                if result.data and 'optimization_results' in result.data:
                    results = result.data['optimization_results']
                    print(f"   • Recommended for production skills clustering (option 7)")
                else:
                    print("   • Use these parameters for production skills clustering")
            else:
                print("❌ Skills parameter optimization failed.")
                print("   Check your database and ensure skills data exists.")
                
        except ImportError:
            print("❌ Skills optimization module not available.")
            print("   Required dependencies may be missing.")
        except Exception as e:
            print(f"❌ Skills optimization failed: {e}")
            print("   Check your database and ensure skills data exists.")
    
    def handle_clustering_analysis(self, orchestrator) -> None:
        """Handle strategic clustering analytics execution."""
        print("\n🧩 Production Clustering Analytics...")
        print("   This will perform comprehensive clustering analysis:")
        print("   • Job Families: DBSCAN clustering of job profiles with business naming")
        print("   • Skill Bundles: DBSCAN clustering of skills with specialization detection")
        print("   • Cluster quality metrics and validation")
        print("   • Database population with clustering intelligence")
        print()
        
        try:
            from skill_similarity_engine.cli.commands.precompute_commands import ClusteringAnalysisCommand
            
            # Get database path from orchestrator
            db_path = str(orchestrator.db_path)
            print(f"📂 Database: {db_path}")
            
            # Check if clustering configuration exists
            from skill_similarity_engine.config.architectural_config_manager import get_config_manager
            config_manager = get_config_manager()
            clustering_config = config_manager.get_nested_value('core', 'clustering_analysis')
            skills_config = config_manager.get_nested_value('core', 'skills_clustering')
            
            if not clustering_config:
                print("⚠️  No job clustering configuration found.")
                print("   Run 'Optimize Job Clustering Parameters' (option 5) first for best results.")
                print("   Proceeding with default parameters...")
            else:
                print("✅ Using optimized job clustering parameters from configuration")
                job_config = clustering_config.get('job_profile_clustering', {})
                algorithm = job_config.get('algorithm', 'dbscan').upper()
                job_params = job_config.get('optimal_parameters', {})
                if job_params:
                    if algorithm == 'DBSCAN':
                        print(f"   -> Job Families: {algorithm}(eps={job_params.get('eps', 'default')}, min_samples={job_params.get('min_samples', 'default')})")
                    elif algorithm in ['HIERARCHICAL', 'KMEANS']:
                        print(f"   -> Job Families: {algorithm}(n_clusters={job_params.get('n_clusters', 'default')}, linkage={job_params.get('linkage', 'ward') if algorithm == 'HIERARCHICAL' else 'N/A'})")
                    else:
                        print(f"   -> Job Families: {algorithm}(parameters from config)")
            
            if not skills_config:
                print("⚠️  No skills clustering configuration found.")
                print("   Run 'Optimize Skills Clustering Parameters' (option 6) first for best results.")
                print("   Proceeding with default parameters...")
            else:
                print("✅ Using optimized skills clustering parameters from configuration")
                skills_cluster_config = skills_config.get('skills_clustering', {})
                skills_algorithm = skills_cluster_config.get('algorithm', 'dbscan').upper()
                skills_params = skills_cluster_config.get('optimal_parameters', {})
                if skills_params:
                    if skills_algorithm == 'DBSCAN':
                        print(f"   -> Skill Bundles: {skills_algorithm}(eps={skills_params.get('eps', 'default')}, min_samples={skills_params.get('min_samples', 'default')})")
                    elif skills_algorithm in ['HIERARCHICAL', 'KMEANS']:
                        print(f"   -> Skill Bundles: {skills_algorithm}(n_clusters={skills_params.get('n_clusters', 'default')}, linkage={skills_params.get('linkage', 'ward') if skills_algorithm == 'HIERARCHICAL' else 'N/A'})")
                    else:
                        print(f"   -> Skill Bundles: {skills_algorithm}(parameters from config)")
            
            print()
            
            # Run clustering analysis command
            command = ClusteringAnalysisCommand()
            result = command.execute()
            
            if result.success:
                print("✅ Strategic clustering analytics completed successfully!")
                print("   Your database now contains comprehensive clustering intelligence.")
            else:
                print("❌ Strategic clustering analytics failed.")
                print("   Check your database and configuration.")
                
        except ImportError:
            print("❌ Clustering analysis module not available.")
            print("   Required dependencies may be missing.")
        except Exception as e:
            print(f"❌ Clustering analysis failed: {e}")
            print("   Check your database and configuration.")
    
    def handle_velocity_analysis(self, orchestrator) -> None:
        """Handle skill velocity analysis execution."""
        print("\n📈 Skill Velocity Analysis...")
        print("   This will analyze skill demand trends over time:")
        print("   • Multi-timeframe CAGR calculations (1, 2, 3 years)")
        print("   • Velocity categorization (accelerating, growing, stable, declining)")
        print("   • Recency-weighted growth metrics")
        print("   • Strategic trend intelligence for workforce planning")
        print()
        
        try:
            from skill_similarity_engine.cli.commands.precompute_commands import VelocityAnalysisCommand
            
            # Get database path from orchestrator
            db_path = str(orchestrator.db_path)
            print(f"📂 Database: {db_path}")
            print()
            
            # Run velocity analysis command
            command = VelocityAnalysisCommand()
            result = command.execute()
            
            if result.success:
                print("✅ Skill velocity analysis completed successfully!")
                print("   Your database now contains temporal skill trend intelligence.")
                
                # Display summary if available
                if result.data:
                    summary = result.data
                    categories = summary.get('velocity_categories', {})
                    print("\n📊 Quick Summary:")
                    print(f"   • Total Skills Analyzed: {summary.get('total_skills_analyzed', 0)}")
                    print(f"   • Accelerating: {categories.get('accelerating', 0)} | Growing: {categories.get('growing', 0)}")
                    print(f"   • Stable: {categories.get('stable', 0)} | Declining: {categories.get('declining', 0)}")
            else:
                print("❌ Skill velocity analysis failed.")
                print("   Check your database and ensure temporal data exists.")
                
        except ImportError:
            print("❌ Velocity analysis module not available.")
            print("   Required dependencies may be missing.")
        except Exception as e:
            print(f"❌ Velocity analysis failed: {e}")
            print("   Check your database and ensure temporal data exists.")
    
    def handle_diagnostics_analysis(self, orchestrator) -> None:
        """Handle job architecture health diagnostics execution."""
        print("\n🏥 Job Architecture Health Diagnostics...")
        print("   This will analyze job architecture structural integrity:")
        print("   • Silhouette score analysis (role differentiation)")
        print("   • Near-duplicate role detection")
        print("   • Network analysis (hub skills, communities)")
        print("   • Entropy analysis (role focus vs generality)")
        print("   • Executive summary with governance recommendations")
        print()
        
        try:
            from skill_similarity_engine.cli.commands.precompute_commands import DiagnosticsAnalysisCommand
            
            # Get database path from orchestrator
            db_path = str(orchestrator.db_path)
            print(f"📂 Database: {db_path}")
            print()
            
            # Run diagnostics analysis command
            command = DiagnosticsAnalysisCommand()
            result = command.execute()
            
            if result.success:
                print("✅ Job architecture diagnostics completed successfully!")
                print("   Your database now contains comprehensive architecture health intelligence.")
                
                # Display summary if available
                if result.data:
                    summary = result.data
                    print("\n📊 Quick Summary:")
                    print(f"   • Total Roles Analyzed: {summary.get('total_roles_analyzed', 0)}")
                    print(f"   • Near-Duplicate Pairs: {summary.get('near_duplicate_pairs', 0)}")
                    print(f"   • Hub Skills Identified: {summary.get('hub_skills_count', 0)}")
                    print(f"   • Communities Detected: {summary.get('communities_detected', 0)}")
                    
                    # Show governance recommendations if available
                    recommendations = summary.get('governance_recommendations', [])
                    if recommendations:
                        print("   • Key Recommendations:")
                        for i, rec in enumerate(recommendations[:3], 1):
                            print(f"     {i}. {rec}")
                        
            else:
                print("❌ Job architecture diagnostics failed.")
                print("   Check your database and ensure job architecture data exists.")
                
        except ImportError:
            print("❌ Diagnostics analysis module not available.")
            print("   Required dependencies may be missing.")
        except Exception as e:
            print(f"❌ Diagnostics analysis failed: {e}")
            print("   Check your database and ensure job architecture data exists.")
    
    def handle_database_cleanup(self, orchestrator) -> None:
        """Handle database cleanup execution."""
        print("\n🧹 Database Cleanup Operations...")
        print("   This will clean up large intermediate tables after analytics completion:")
        print("   • core_colleague_positions_history (historical position data)")
        print("   • core_position_timeline (timeline data)")
        print("   • Database size optimization with VACUUM")
        print()
        
        try:
            from skill_similarity_engine.cli.commands.precompute_commands import DatabaseCleanupCommand
            
            # Get database path from orchestrator
            db_path = str(orchestrator.db_path)
            print(f"📂 Database: {db_path}")
            print()
            
            # Run database cleanup command
            command = DatabaseCleanupCommand()
            result = command.execute()
            
            if result.success:
                print("✅ Database cleanup completed successfully!")
                
                # Display summary if available
                if result.data and result.data.get('cleanup_stats'):
                    cleanup_stats = result.data['cleanup_stats']
                    print("\n📊 Cleanup Summary:")
                    print(f"   • Tables cleaned: {cleanup_stats.get('tables_cleaned', 0)}")
                    print(f"   • Rows removed: {cleanup_stats.get('total_rows_removed', 0):,}")
                    print(f"   • Storage freed: {cleanup_stats.get('total_size_freed_mb', 0):.1f} MB")
                    
                    # Show database size info if available
                    if result.data.get('size_info'):
                        size_info = result.data['size_info']
                        if 'error' not in size_info:
                            print(f"   • Current database size: {size_info.get('file_size_mb', 0):.1f} MB")
                        
                elif result.data and not result.data.get('cleanup_needed', True):
                    print("   Database is already optimized - no cleanup needed")
                    
            else:
                print("❌ Database cleanup failed.")
                print("   Check your database permissions and ensure tables exist.")
                
        except ImportError:
            print("❌ Database cleanup module not available.")
            print("   Required dependencies may be missing.")
        except Exception as e:
            print(f"❌ Database cleanup failed: {e}")
            print("   Check your database connection and permissions.")
    
    def handle_schema_documentation(self) -> None:
        """Handle database schema documentation generation."""
        try:
            print("\n" + "="*60)
            print("📚 DATABASE SCHEMA DOCUMENTATION")
            print("="*60)
            print()
            print("🌐 This will generate comprehensive interactive HTML documentation")
            print("   with modern UI, collapsible sections, and enhanced navigation.")
            print()
            print("📋 Features include:")
            print("   • Interactive collapsible sections with modern design")
            print("   • Zoomable/pannable Mermaid ERD diagrams")
            print("   • Business context and usage guides")
            print("   • Developer-friendly query examples")
            print("   • Responsive design and smooth navigation")
            print()
            
            # Ask for confirmation
            confirm = input("   Generate enhanced schema documentation? (y/N): ").strip().lower()
            if confirm != 'y':
                print("   Documentation generation cancelled.")
                print()
                return
            
            # Execute the schema documentation command
            result = self.schema_doc_cmd.execute()
            
            if result.success:
                print()
                print("✅ Schema documentation generated successfully!")
                if result.data:
                    print(f"   📄 Documentation: {result.data.get('output_path', 'docs/sqlite_schema_design.html')}")
                    print(f"   📊 File size: {result.data.get('file_size_kb', 0):.1f} KB")
                print("   💡 Open the HTML file in your web browser to explore the interactive documentation!")
            else:
                print()
                print("❌ Schema documentation generation failed.")
                if result.errors:
                    for error in result.errors:
                        print(f"   Error: {error}")
                print("   Please check your database and try again.")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error during schema documentation generation: {e}")
            print("   Please check your database and file permissions.")
            input("\nPress Enter to continue...")
    
    def handle_system_tools(self) -> None:
        """Handle system tools menu."""
        while True:
            choice = self.show_system_tools_menu()
            
            if choice == '1':
                self.handle_schema_documentation()
            elif choice == '2':
                print("🔍 Checking database health...")
                print("   This feature is coming soon.")
            elif choice == '3':
                print("📊 Generating database summary...")
                print("   This feature is coming soon.")
            elif choice == '4':
                print("💾 Exporting database backup...")
                print("   This feature is coming soon.")
            elif choice == '5':
                self.run_legacy_precompute_menu()
            elif choice == '6':
                print("🔧 Running system diagnostics...")
                print("   This feature is coming soon.")
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice. Please select a number from the menu.")
    
    def run_legacy_precompute_menu(self) -> None:
        """Run the legacy precompute submenu for advanced users."""
        while True:
            choice = self.show_legacy_precompute_menu()
            
            if choice == '1':
                self.handle_data_loading()
            elif choice == '2':
                self.handle_similarity_generation()
            elif choice == '3':
                self.handle_movement_analysis()
            elif choice == '4':
                print("📤 Export functionality coming soon.")
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice. Please select a number from the menu.")
    
    def run_main_menu(self) -> None:
        """Run the main menu loop with improved user experience."""
        while True:
            choice = self.show_main_menu()
            
            if choice == '1':
                self.handle_data_pipeline_setup()
            elif choice == '2':
                self.handle_workforce_intelligence()
            elif choice == '3':
                self.handle_career_intelligence_generation()
            elif choice == '4':
                self.handle_system_tools()
            elif choice == '0':
                print("👋 Thank you for using the NAB Workforce Intelligence Platform!")
                print("   Your session data has been saved.")
                # Clear session on exit
                self.session_manager.clear_session()
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please select a number from the menu.")
                print()


def main():
    """
    Main entry point for the NAB Workforce Intelligence Platform.
    
    Provides an intuitive interface for building and using workforce
    intelligence, designed for both technical and business users.
    """
    try:
        orchestrator = WorkforceIntelligenceOrchestrator()
        orchestrator.run_main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted. Thank you for using the platform!")
        # Clear session on interrupt
        session_manager = get_session_manager()
        session_manager.clear_session()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        print("   Please contact your system administrator if this problem persists.")
        sys.exit(1)


if __name__ == "__main__":
    main()

