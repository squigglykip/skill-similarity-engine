"""
Analytics Commands for Advanced Analysis

Contains CLI commands for advanced analytics workflows, extracted from precompute_commands.py
and focused on velocity analysis and job architecture diagnostics.
"""

from pathlib import Path
from typing import Any, Dict

from .base_command import BaseCommand, CommandResult
from ...config.architectural_config_manager import get_config_manager


class VelocityAnalysisCommand(BaseCommand):
    """
    Command for executing skill velocity analysis.
    
    Analyzes skill demand trends over time using CAGR calculations
    and categorizes skills by velocity patterns for strategic planning.
    """
    
    def __init__(self):
        super().__init__(
            name="velocity_analysis",
            description="Execute skill velocity analysis and trend categorization"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for velocity analysis."""
        return CommandResult(
            success=True,
            message="Velocity analysis arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute skill velocity analysis.
        
        Returns:
            CommandResult with velocity analysis status and results
        """
        try:
            print("\n📈 Skill Velocity Analysis")
            print("="*50)
            print("🕒 Multi-timeframe skill demand trend analysis:")
            print("   • CAGR calculation (1, 2, 3 year timeframes)")
            print("   • Velocity categorization (accelerating, growing, stable, declining)")
            print("   • Recency-weighted growth metrics")
            print("   • Strategic trend intelligence")
            print()
            
            # Import and use the proper SkillVelocityAnalyzer
            from ...models.velocity_analyzer import SkillVelocityAnalyzer
            
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
            
            print("📊 Executing velocity analysis...")
            print("   • Loading skills with temporal demand data")
            print("   • Calculating multi-timeframe CAGR")
            print("   • Categorizing velocity patterns")
            print("   • Generating trend intelligence")
            print()
            
            # Initialize and run velocity analyzer
            analyzer = SkillVelocityAnalyzer(config_manager)
            velocity_result = analyzer.analyze_all_skills_velocity(db_path)
            
            velocity_df = velocity_result.velocity_df
            summary = velocity_result.velocity_summary
            
            if summary and velocity_df is not None:
                print("✅ Velocity analysis completed successfully!")
                print()
                print("📊 Results Summary:")
                
                print(f"   • Total Skills Analyzed: {summary.get('total_skills_analyzed', 0)}")
                
                categories = summary.get('velocity_categories', {})
                print(f"   • Accelerating Skills: {categories.get('accelerating', 0)}")
                print(f"   • Growing Skills: {categories.get('growing', 0)}")
                print(f"   • Stable Skills: {categories.get('stable', 0)}")
                print(f"   • Declining Skills: {categories.get('declining', 0)}")
                
                # Show top accelerating skills
                top_accelerating = summary.get('top_accelerating_skills', [])[:3]
                if top_accelerating:
                    print("   • Top Accelerating Skills:")
                    for skill in top_accelerating:
                        print(f"     - {skill.get('skill_name', 'Unknown')} ({skill.get('short_term_cagr', 0):.1%} CAGR)")
                
                print()
                
                # Populate database with results
                print("💾 Saving velocity data to analytics database...")
                from ...business_context.database_integrator import DatabaseIntegrator
                from pathlib import Path
                db_integrator = DatabaseIntegrator(Path(db_path))
                population_success = db_integrator.populate_skill_demand_trends(velocity_df)
                
                if population_success:
                    print("✅ Velocity data saved to analytics database")
                else:
                    print("⚠️ Velocity analysis completed but database population failed")
                
                return CommandResult(
                    success=True,
                    message="Velocity analysis completed successfully",
                    data=summary,
                    metadata={
                        'total_skills': summary.get('total_skills_analyzed', 0),
                        'velocity_categories': categories,
                        'database_populated': population_success
                    }
                )
            else:
                print("❌ Velocity analysis returned no results.")
                return CommandResult(
                    success=False,
                    message="Velocity analysis completed but returned no results",
                    errors=["No velocity data returned"]
                )
                
        except Exception as e:
            print(f"❌ Velocity analysis command failed: {e}")
            print("   Check your database and ensure temporal data exists.")
            return CommandResult(
                success=False,
                message=f"Velocity analysis failed: {str(e)}",
                errors=[str(e)]
            )


class DiagnosticsAnalysisCommand(BaseCommand):
    """
    Command for executing job architecture health diagnostics.
    
    Analyzes job architecture structural integrity including role differentiation,
    duplicate detection, network analysis, and entropy metrics for strategic planning.
    """
    
    def __init__(self):
        super().__init__(
            name="diagnostics_analysis",
            description="Execute job architecture health diagnostics and governance analysis"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for diagnostics analysis."""
        return CommandResult(
            success=True,
            message="Diagnostics analysis arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute job architecture health diagnostics.
        
        Returns:
            CommandResult with diagnostics analysis status and results
        """
        try:
            print("\n🏥 Job Architecture Health Diagnostics")
            print("="*50)
            print("🩺 Comprehensive architecture health evaluation:")
            print("   • Silhouette score analysis (role differentiation)")
            print("   • Near-duplicate role detection (similarity thresholds)")
            print("   • Network analysis (hub skills, communities)")
            print("   • Entropy analysis (role focus vs generality)")
            print("   • Executive summary with governance recommendations")
            print()
            
            # Import the modularized diagnostics analyzer
            from ...models.diagnostics_analyzer import analyze_job_architecture_health
            
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
            
            print(f"📂 Loading diagnostics from: {__file__.replace('analytics_commands.py', '../models/diagnostics_analyzer.py')}")
            print("📊 Executing diagnostics analysis...")
            print("   • Loading job architecture data")
            print("   • Calculating role differentiation metrics")
            print("   • Detecting near-duplicate roles")
            print("   • Analyzing skill network structure")
            print("   • Generating governance recommendations")
            print()
            
            # Execute diagnostics analysis
            results = analyze_job_architecture_health(db_path)
            
            if results:
                print("✅ Job architecture diagnostics completed successfully!")
                print()
                print("📊 Results Summary:")
                
                # Extract summary information from results
                summary = self._extract_summary(results)
                
                print(f"   • Total Roles Analyzed: {summary.get('total_roles_analyzed', 0)}")
                print(f"   • Near-Duplicate Pairs: {summary.get('near_duplicate_pairs', 0)}")
                print(f"   • Hub Skills Identified: {summary.get('hub_skills_count', 0)}")
                print(f"   • Communities Detected: {summary.get('communities_detected', 0)}")
                
                # Show key insights
                if summary.get('top_insights'):
                    print("   • Key Insights:")
                    for i, insight in enumerate(summary['top_insights'][:3], 1):
                        print(f"     {i}. {insight}")
                
                # Show governance recommendations
                if summary.get('governance_recommendations'):
                    print("   • Governance Recommendations:")
                    for i, rec in enumerate(summary['governance_recommendations'][:3], 1):
                        print(f"     {i}. {rec}")
                
                print()
                
                return CommandResult(
                    success=True,
                    message="Job architecture diagnostics completed successfully",
                    data=summary,
                    metadata={
                        'total_roles': summary.get('total_roles_analyzed', 0),
                        'duplicate_pairs': summary.get('near_duplicate_pairs', 0),
                        'communities': summary.get('communities_detected', 0)
                    }
                )
            else:
                print("❌ Diagnostics analysis returned no results.")
                return CommandResult(
                    success=False,
                    message="Diagnostics analysis completed but returned no results",
                    errors=["No diagnostics data returned"]
                )
                
        except Exception as e:
            print(f"❌ Diagnostics analysis command failed: {e}")
            print("   Check your database and ensure job architecture data exists.")
            return CommandResult(
                success=False,
                message=f"Diagnostics analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _extract_summary(self, results) -> dict:
        """Extract summary information from diagnostics results."""
        try:
            # Default summary structure - the actual implementation will depend on 
            # what the diagnostics main() function returns
            summary = {
                'total_roles_analyzed': 0,
                'near_duplicate_pairs': 0,
                'hub_skills_count': 0,
                'communities_detected': 0,
                'top_insights': [],
                'governance_recommendations': []
            }
            
            # If results is a dictionary, extract values
            if isinstance(results, dict):
                summary.update({
                    'total_roles_analyzed': results.get('total_roles', 0),
                    'near_duplicate_pairs': results.get('duplicate_pairs', 0),
                    'hub_skills_count': results.get('hub_skills', 0),
                    'communities_detected': results.get('communities', 0),
                    'top_insights': results.get('insights', []),
                    'governance_recommendations': results.get('recommendations', [])
                })
            
            return summary
            
        except Exception as e:
            print(f"   ⚠️  Warning: Could not extract summary: {e}")
            return {
                'total_roles_analyzed': 'Unknown',
                'near_duplicate_pairs': 'Unknown',
                'hub_skills_count': 'Unknown',
                'communities_detected': 'Unknown',
                'top_insights': ['Analysis completed - check detailed output above'],
                'governance_recommendations': ['Review detailed diagnostics output for recommendations']
            }
