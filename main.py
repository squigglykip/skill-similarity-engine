#!/usr/bin/env python3

"""
Skill Similarity Engine v2 - Modular Entry Point

This script provides a menu-based CLI for the Skill Similarity Engine pipeline
using the modular Command pattern and Workflow orchestrators from /src modules.

This version eliminates cottage industry patterns and uses proper modular design.
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

Skill Similarity Engine v2 - Modular Pipeline (Command Pattern Version)

'''


class ModularMenuOrchestrator:
    """
    Orchestrates the main application menu using modular commands.
    
    Replaces the procedural menu functions from main.py with a proper
    orchestrator that leverages the Command pattern and session management.
    """
    
    def __init__(self):
        """Initialize the menu orchestrator."""
        self.logger = setup_logging(level='INFO')
        self.session_manager = get_session_manager()
        
        # Initialize commands
        self.data_load_cmd = DataLoadCommand()
        self.similarity_cmd = SimilarityMatrixCommand()
        self.movement_cmd = MovementAnalysisCommand()
        self.query_cmd = QuerySimilarityCommand()
        
        self.logger.info("Modular menu orchestrator initialized")
    
    def show_main_menu(self) -> str:
        """Display the main application menu."""
        print(BANNER)
        
        # Show session status
        session_summary = self.session_manager.get_session_summary()
        if session_summary.get('session_exists', False) and session_summary.get('ready_for_similarity', False):
            print(f"📊 Session Status: Data loaded ({session_summary.get('skills_count', 0)} skills, {session_summary.get('jobs_count', 0)} jobs)")
        else:
            print("📊 Session Status: No data loaded")
        
        print("\nPlease select an option:")
        print("1. Precompute Skill Similarities")
        print("2. Generate Business Context Database")
        print("3. Query Skill Similarities (coming soon)")
        print("0. Exit")
        
        return input("Enter your choice: ").strip()
    
    def show_precompute_menu(self) -> str:
        """Display the precompute engine menu."""
        print("\nPrecompute Engine - Generate Parquet Files\n")
        
        # Show data status
        session_summary = self.session_manager.get_session_summary()
        data_status = "✅ Data Ready" if session_summary.get('ready_for_similarity', False) else "❌ Data Not Loaded"
        print(f"Data Status: {data_status}")
        
        print("\nSelect a task:")
        print("1. Load and validate data")
        print("2. Generate similarity matrix + career pathways (both as parquet)")
        print("3. Generate movement analysis (workforce transition data)")
        print("4. Export results (coming soon)")
        print("0. Back to main menu")
        
        return input("Enter your choice: ").strip()
    
    def handle_data_loading(self) -> None:
        """Handle data loading using the DataLoadCommand."""
        try:
            result = self.data_load_cmd.run()
            
            if result.success:
                # Load data into session manager
                if result.data and 'taxonomy' in result.data:
                    self.session_manager.load_taxonomy(result.data['taxonomy'])
                if result.data and 'architecture' in result.data:
                    self.session_manager.load_architecture(result.data['architecture'])
                
                print("✅ Data loaded successfully and stored in session!")
            else:
                print(f"❌ Data loading failed: {result.message}")
                for error in result.errors:
                    print(f"   • {error}")
                    
        except Exception as e:
            self.logger.error(f"Data loading command failed: {e}")
            print(f"❌ Command execution failed: {e}")
    
    def handle_similarity_generation(self) -> None:
        """Handle similarity matrix generation using the SimilarityMatrixCommand."""
        # Check if data is loaded
        if not self.session_manager.is_data_ready_for_similarity():
            print("❌ Data not loaded. Please load and validate data first (option 1).")
            return
        
        try:
            architecture = self.session_manager.get_architecture()
            result = self.similarity_cmd.run(architecture=architecture)
            
            if result.success:
                print("✅ Similarity matrix generation completed!")
                if result.data and 'output_path' in result.data:
                    print(f"📁 Output saved to: {result.data['output_path']}")
            else:
                print(f"❌ Similarity generation failed: {result.message}")
                for error in result.errors:
                    print(f"   • {error}")
                    
        except Exception as e:
            self.logger.error(f"Similarity generation command failed: {e}")
            print(f"❌ Command execution failed: {e}")
    
    def handle_movement_analysis(self) -> None:
        """Handle movement analysis using the MovementAnalysisCommand."""
        try:
            result = self.movement_cmd.run()
            
            if result.success:
                print("✅ Movement analysis completed!")
                if result.data and 'output_path' in result.data:
                    print(f"📁 Output saved to: {result.data['output_path']}")
            else:
                print(f"❌ Movement analysis failed: {result.message}")
                for error in result.errors:
                    print(f"   • {error}")
                    
        except Exception as e:
            self.logger.error(f"Movement analysis command failed: {e}")
            print(f"❌ Command execution failed: {e}")
    
    def handle_query_similarities(self) -> None:
        """Handle similarity queries using the QuerySimilarityCommand."""
        try:
            result = self.query_cmd.run()
            
            if result.success:
                print("✅ Query completed!")
            else:
                print(f"❌ Query failed: {result.message}")
                    
        except Exception as e:
            self.logger.error(f"Query command failed: {e}")
            print(f"❌ Command execution failed: {e}")
    
    def handle_business_context(self) -> None:
        """Handle business context database generation using existing orchestrator."""
        try:
            orchestrator = BusinessContextOrchestrator()
            orchestrator.handle_business_context_menu()
        except Exception as e:
            self.logger.error(f"Business context menu error: {e}")
            print(f"❌ Business context menu failed: {e}")
    
    def run_precompute_menu(self) -> None:
        """Run the precompute submenu loop."""
        while True:
            choice = self.show_precompute_menu()
            
            if choice == '1':
                self.handle_data_loading()
            elif choice == '2':
                self.handle_similarity_generation()
            elif choice == '3':
                self.handle_movement_analysis()
            elif choice == '4':
                print("[INFO] Export functionality coming soon.")
            elif choice == '0':
                break
            else:
                print("Invalid choice. Please enter a valid option.")
    
    def run_main_menu(self) -> None:
        """Run the main menu loop."""
        while True:
            choice = self.show_main_menu()
            
            if choice == '1':
                self.run_precompute_menu()
            elif choice == '2':
                self.handle_business_context()
            elif choice == '3':
                self.handle_query_similarities()
            elif choice == '0':
                print("Exiting. Goodbye!")
                # Clear session on exit
                self.session_manager.clear_session()
                sys.exit(0)
            else:
                print("Invalid choice. Please enter a valid option.")


def main():
    """
    Main entry point using modular architecture.
    
    This version demonstrates:
    - Command pattern for operations
    - Session management for state
    - Orchestrator pattern for menu coordination
    - Proper separation of concerns
    """
    try:
        orchestrator = ModularMenuOrchestrator()
        orchestrator.run_main_menu()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user. Exiting...")
        # Clear session on interrupt
        session_manager = get_session_manager()
        session_manager.clear_session()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Application failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

