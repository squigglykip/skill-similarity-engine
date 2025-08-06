#!/usr/bin/env python3

"""
NAB Workforce Intelligence Platform - Main Entry Point

This script provides an intuitive, business-focused interface for workforce
intelligence analysis, designed for both technical and non-technical users.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path if not installed as a package
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.logging.config import setup_logging
from skill_similarity_engine.cli.utilities import print_banner, prompt_int
from skill_similarity_engine.cli.commands import (
    DataLoadCommand, SimilarityMatrixCommand, MovementAnalysisCommand, QuerySimilarityCommand
)
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
        self.logger = setup_logging(level='INFO')
        self.session_manager = get_session_manager()
        
        # Initialize commands
        self.data_load_cmd = DataLoadCommand()
        self.similarity_cmd = SimilarityMatrixCommand()
        self.movement_cmd = MovementAnalysisCommand()
        self.query_cmd = QuerySimilarityCommand()
        
        self.logger.info("Workforce Intelligence Platform initialized")
    
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
        print("1. Build Workforce Database")
        print("2. Generate Career Intelligence") 
        print("3. Query Job Similarities")
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
        print("1. Check database health")
        print("2. View database summary") 
        print("3. Export database backup")
        print("4. Advanced analytics tools")
        print("5. System diagnostics")
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
            self.logger.error(f"Data loading failed: {e}")
            print(f"❌ Unable to load data: {e}")
    
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
            self.logger.error(f"Similarity generation failed: {e}")
            print(f"❌ Unable to generate similarity analysis: {e}")
    
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
            self.logger.error(f"Movement analysis failed: {e}")
            print(f"❌ Unable to analyse career movements: {e}")
    
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
            self.logger.error(f"Query failed: {e}")
            print(f"❌ Unable to search similarities: {e}")
    
    def handle_workforce_intelligence(self) -> None:
        """Handle workforce database building with user-friendly messaging."""
        try:
            print("🏗️ Opening workforce database builder...")
            print()
            
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
            
            # Pass explicit config path to orchestrator
            orchestrator = BusinessContextOrchestrator(data_config_path=data_config_path)
            orchestrator.handle_workforce_intelligence_menu()
            
        except Exception as e:
            self.logger.error(f"Workforce database builder error: {e}")
            print(f"❌ Unable to open database builder: {e}")
    
    def show_analytics_phases_menu(self) -> str:
        """Display analytics capabilities menu with user-friendly options."""
        print("\n=== Career Intelligence Generation ===")
        print("Generate advanced analytics directly into your database.\n")
        
        print("Select analytics capability:")
        print("1. Enhanced Similarity Analytics")
        print("2. Generate Movement Analysis")  # NEW: Populate movement patterns
        print("3. Train Predictive Movement Models")  # NEW: ML training step 
        print("4. Strategic Clustering Analytics")
        print("5. Run All Capabilities (Recommended)")
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
                    print("\n🧠 Executing Phase 1: Enhanced Similarity Analytics...")
                    print("   This will calculate enhanced job similarities using configuration-driven algorithms")
                    print("   with Optuna-optimized parameters and populate analytics tables directly in your database.")
                    print("   • Parameters: 8.8% defining skills threshold, 1.206x multiplier")
                    print("   • Algorithm: Asymmetric Jaccard with corpus normalization")
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
                        
                elif choice == '2':
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
                        
                elif choice == '3':
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
                    
                elif choice == '4':
                    print("\n🎯 Strategic Clustering Analytics...")
                    print("   This will perform job clustering, skills bundling, and velocity")
                    print("   analysis to provide strategic workforce insights.")
                    print()
                    
                    success = orchestrator.execute_phase_3_clustering_velocity()
                    if success:
                        print("✅ Strategic clustering completed! Insights added to database.")
                    else:
                        print("❌ Strategic clustering failed or not yet implemented. Check logs for details.")
                        
                elif choice == '5':
                    print("\n🚀 Running All Capabilities...")
                    print("   This will execute all available analytics capabilities in sequence.")
                    print()
                    
                    # Step 1: Enhanced Similarity
                    print("Step 1: Enhanced Similarity Analytics...")
                    similarity_success = orchestrator.execute_phase_1_enhanced_similarity()
                    if similarity_success:
                        print("✅ Enhanced similarity analytics completed")
                    else:
                        print("❌ Enhanced similarity analytics failed")
                    
                    # Step 2: Movement Analysis
                    print("\nStep 2: Movement Analysis...")
                    movement_success = orchestrator.execute_movement_pattern_analysis()
                    if movement_success:
                        print("✅ Movement analysis completed")
                    else:
                        print("⚠️ Movement analysis failed")
                    
                    # Step 3: ML Training
                    print("\nStep 3: ML Model Training...")
                    ml_success = orchestrator.execute_movement_ml_training()
                    if ml_success:
                        print("✅ ML model training completed")
                    else:
                        print("⚠️ ML model training failed")
                    
                    # Step 4: Strategic Clustering
                    print("\nStep 4: Strategic Clustering...")
                    clustering_success = orchestrator.execute_phase_3_clustering_velocity()
                    if clustering_success:
                        print("✅ Strategic clustering completed")
                    else:
                        print("⚠️ Strategic clustering failed or not implemented")
                    
                    # Summary
                    completed_capabilities = sum([similarity_success, movement_success, ml_success])
                    if completed_capabilities > 0:
                        print(f"\n✅ Completed {completed_capabilities} capabilities! Your database now contains enhanced analytics.")
                        print("   Career intelligence data is available for queries and applications.")
                    else:
                        print("\n❌ No capabilities completed successfully. Check logs for details.")
                        
                elif choice == '0':
                    break
                else:
                    print("❌ Invalid choice. Please select a number from the menu.")
                
                if choice != '0':
                    input("\nPress Enter to continue...")
                    
        except Exception as e:
            self.logger.error(f"Career intelligence generation failed: {e}")
            print(f"❌ Unable to generate career intelligence: {e}")
            print("   Please check that your foundation database is properly configured.")
    
    def handle_system_tools(self) -> None:
        """Handle system tools menu."""
        while True:
            choice = self.show_system_tools_menu()
            
            if choice == '1':
                print("🔍 Checking database health...")
                print("   This feature is coming soon.")
            elif choice == '2':
                print("📊 Generating database summary...")
                print("   This feature is coming soon.")
            elif choice == '3':
                print("💾 Exporting database backup...")
                print("   This feature is coming soon.")
            elif choice == '4':
                self.run_legacy_precompute_menu()
            elif choice == '5':
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
                self.handle_workforce_intelligence()
            elif choice == '2':
                self.handle_career_intelligence_generation()
            elif choice == '3':
                self.handle_query_similarities()
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

