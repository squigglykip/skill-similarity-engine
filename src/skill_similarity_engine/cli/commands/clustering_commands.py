"""
Clustering Commands for Optimization and Analysis

Contains CLI commands for clustering workflows, extracted from precompute_commands.py
and focused on clustering parameter optimization and production analysis.
"""

from pathlib import Path
from typing import Any, Dict
import sqlite3

from .base_command import BaseCommand, CommandResult
from ...config.architectural_config_manager import get_config_manager


class SkillsOptimizationCommand(BaseCommand):
    """
    Command for optimizing skills clustering parameters across multiple algorithms.
    
    Tests DBSCAN, Hierarchical, and K-means clustering across Jaccard, Cosine,
    and Combined similarity measures with taxonomy alignment validation.
    """
    
    def __init__(self):
        super().__init__(
            name="skills_optimization",
            description="Optimize skills clustering parameters with multiple similarity measures and algorithms"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for skills optimization."""
        return CommandResult(
            success=True,
            message="Skills optimization arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute skills clustering parameter optimization.
        
        Returns:
            CommandResult with optimization status and results
        """
        try:
            print("\n🔗 Skills Clustering Parameter Optimization")
            print("="*50)
            print("📊 This will analyze your skills data to find optimal clustering parameters")
            print("   • DBSCAN parameters (eps/min_samples)")
            print("   • Hierarchical clustering (n_clusters/linkage)")
            print("   • K-means parameters (n_clusters)")
            print("   • Multiple similarity measures (Jaccard, Cosine, Combined)")
            print("   • Taxonomy alignment validation")
            print()
            
            # Get database path from kwargs or use default
            db_path = kwargs.get('db_path')
            if not db_path:
                # Fallback to default path
                db_path = "models/2025-Q3/business_context.sqlite"
            
            # Verify database exists
            if not Path(db_path).exists():
                return CommandResult(
                    success=False,
                    message=f"Database not found: {db_path}",
                    errors=[f"Database file not found at {db_path}"]
                )
            
            print(f"📂 Database: {db_path}")
            print()
            
            # Import and run skills optimization
            from ...models.clustering_optimizer import SkillsParameterOptimizer
            
            print("🔍 Initializing skills parameter optimizer...")
            optimizer = SkillsParameterOptimizer(db_path)
            
            print("📊 Starting comprehensive parameter analysis...")
            print("   • Loading skills co-occurrence data")
            print("   • Creating multiple similarity matrices")
            print("   • Testing algorithm combinations")
            print("   • Calculating taxonomy alignment scores")
            print()
            
            # Run optimization
            results = optimizer.optimize_skills_parameters()
            
            if results:
                # Save skills configuration to separate YAML file
                print("💾 Saving skills clustering configuration...")
                save_success = optimizer.save_skills_configuration(results)
                if save_success:
                    print("✅ Configuration saved to config/core/skills_clustering.yaml")
                else:
                    print("⚠️  Warning: Failed to save configuration file")
                
                print()
                print("✅ Skills parameter optimization completed successfully!")
                print(f"   • Best Algorithm: {results.get('algorithm', 'Unknown')}")
                print(f"   • Best Similarity Method: {results.get('similarity_method', 'Unknown')}")
                print(f"   • Silhouette Score: {results.get('silhouette_score', 0):.3f}")
                print(f"   • Taxonomy Alignment: {results.get('taxonomy_alignment', 0):.3f}")
                print(f"   • Combined Score: {results.get('combined_score', 0):.3f}")
                
                if results['algorithm'] == 'dbscan':
                    print(f"   • Optimal eps: {results.get('eps', 'N/A')}")
                    print(f"   • Optimal min_samples: {results.get('min_samples', 'N/A')}")
                    print(f"   • Expected clusters: {results.get('n_clusters', 'N/A')}")
                    print(f"   • Noise ratio: {results.get('noise_ratio', 0):.1%}")
                elif results['algorithm'] == 'hierarchical':
                    print(f"   • Optimal clusters: {results.get('n_clusters', 'N/A')}")
                    print(f"   • Optimal linkage: {results.get('linkage', 'N/A')}")
                elif results['algorithm'] == 'kmeans':
                    print(f"   • Optimal clusters: {results.get('n_clusters', 'N/A')}")
                
                return CommandResult(
                    success=True,
                    message="Skills clustering parameters optimized successfully",
                    data={'optimization_results': results}
                )
            else:
                return CommandResult(
                    success=False,
                    message="Skills parameter optimization failed to find optimal parameters",
                    errors=["No valid clustering configurations found"]
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Skills optimization failed: {str(e)}",
                errors=[str(e)]
            )


class ClusteringOptimizationCommand(BaseCommand):
    """
    Command for optimizing clustering parameters using systematic analysis.
    
    Performs silhouette analysis, elbow method, and stability assessment
    to find optimal DBSCAN parameters for job profile clustering.
    Updates configuration files automatically with optimized parameters.
    """
    
    def __init__(self):
        super().__init__(
            name="clustering_optimization",
            description="Optimize clustering parameters using Bayesian analysis and update configuration"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for clustering optimization."""
        return CommandResult(
            success=True,
            message="Clustering optimization arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute clustering parameter optimization.
        
        Returns:
            CommandResult with optimization status and results
        """
        try:
            print("\n🎯 Clustering Parameter Optimization")
            print("="*50)
            print("📊 This will analyze your data to find optimal clustering parameters")
            print("   • Job profile clustering (DBSCAN eps/min_samples)")
            print("   • Skills clustering and bundling parameters")
            print("   • Silhouette analysis across parameter ranges")
            print("   • Elbow method validation")
            print()
            
            # Import clustering optimizer
            from ...models.clustering_optimizer import ClusteringParameterOptimizer
            
            if not ClusteringParameterOptimizer.is_available():
                print("❌ Clustering optimization not available.")
                print("   Required dependencies may be missing.")
                return CommandResult(
                    success=False,
                    message="Clustering optimization dependencies not available",
                    errors=["Missing scikit-learn or related dependencies"]
                )
            
            # Get database path
            config_manager = get_config_manager()
            
            # Try to get database path from config or use default
            try:
                db_config = config_manager.get_nested_value('database', 'paths')
                if db_config and 'business_context' in db_config:
                    db_path = db_config['business_context']
                else:
                    # Fallback to default path
                    db_path = "models/2025-Q3/business_context.sqlite"
            except:
                db_path = "models/2025-Q3/business_context.sqlite"
            
            print(f"📂 Database: {db_path}")
            print()
            
            # Confirm with user since this overwrites config
            print("⚠️  This will update config/core/clustering_analysis.yaml")
            print("   with optimized parameters based on your data analysis.")
            
            if not kwargs.get('auto_confirm', False):
                confirm = input("   Continue? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("   Optimization cancelled.")
                    return CommandResult(
                        success=False,
                        message="Optimization cancelled by user"
                    )
            
            # Run optimization
            print("🔍 Initializing clustering parameter optimizer...")
            optimizer = ClusteringParameterOptimizer(db_path)
            
            print("📊 Starting parameter analysis...")
            print("   • Loading job similarity data")
            print("   • Testing DBSCAN parameter combinations")
            print("   • Calculating silhouette scores")
            print("   • Performing elbow method analysis")
            print()
            
            success = optimizer.optimize_and_update()
            
            if success:
                # Reload configuration to pick up new parameters
                config_manager.reload_configuration()
                
                print("✅ Clustering parameter optimization completed successfully!")
                print()
                print("📋 Next Steps:")
                print("   1. Review the updated configuration file")
                print("   2. Run 'Strategic Clustering Analytics' to apply optimized parameters")
                print("   3. Validate clustering results in your database")
                print()
                
                return CommandResult(
                    success=True,
                    message="Clustering parameters optimized successfully",
                    metadata={
                        'config_updated': True,
                        'database_path': db_path
                    }
                )
            else:
                print("❌ Clustering parameter optimization failed.")
                print("   Check your database and ensure job similarity data exists.")
                return CommandResult(
                    success=False,
                    message="Clustering parameter optimization failed",
                    errors=["Optimization process failed - check logs for details"]
                )
                
        except Exception as e:
            print(f"❌ Clustering optimization command failed: {e}")
            print("   Check your database and configuration.")
            return CommandResult(
                success=False,
                message=f"Clustering optimization failed: {str(e)}",
                errors=[str(e)]
            )


class ClusteringAnalysisCommand(BaseCommand):
    """
    Command for executing production clustering analysis.
    
    Performs job profile clustering, skills bundling, and velocity analysis
    using optimized parameters from configuration. Populates database tables
    with comprehensive clustering intelligence.
    """
    
    def __init__(self):
        super().__init__(
            name="clustering_analysis", 
            description="Execute production clustering analysis and populate database tables"
        )
    
    def validate_args(self, **kwargs) -> CommandResult:
        """Validate arguments for clustering analysis."""
        return CommandResult(
            success=True,
            message="Clustering analysis arguments validated"
        )
    
    def execute(self, **kwargs) -> CommandResult:
        """
        Execute comprehensive clustering analysis.
        
        Returns:
            CommandResult with analysis status and results
        """
        try:
            print("\n🧩 Production Clustering Analytics")
            print("="*50)
            print("📊 Comprehensive clustering analysis for strategic intelligence:")
            print("   • Job Families: DBSCAN clustering of job profiles with business naming")
            print("   • Skill Bundles: DBSCAN clustering of skills with specialization detection")
            print("   • Cluster quality metrics and validation")
            print("   • Database population with clustering results")
            print()
            
            # Import clustering analyzer
            from ...models.clustering_analyzer import ClusteringAnalyzer
            
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
            
            # Check if clustering configuration exists
            clustering_config = config_manager.get_nested_value('core', 'clustering_analysis')
            if not clustering_config:
                print("⚠️  No clustering configuration found.")
                print("   Run 'Optimize Clustering Parameters' first to generate optimal parameters.")
                print("   Proceeding with default parameters...")
            else:
                print("✅ Using optimized clustering parameters from configuration")
            
            print()
            
            # Initialize clustering analyzer
            print("🔧 Initializing clustering analyzer...")
            analyzer = ClusteringAnalyzer(config_manager)
            
            print("📊 Executing clustering analysis...")
            print("   • Job profile clustering (DBSCAN)")
            print("   • Skills clustering and bundling")
            print("   • Business context generation")
            print("   • Quality metrics calculation")
            
            # Execute clustering analysis
            clustering_result = analyzer.execute_clustering_analysis(db_path)
            
            print()
            print("💾 Populating database tables...")
            
            # Import database integrator for clustering results
            from ...business_context.database_integrator import DatabaseIntegrator
            
            db_integrator = DatabaseIntegrator(Path(db_path))
            
            # Populate clustering tables
            success = self._populate_clustering_tables(db_integrator, clustering_result)
            
            if success:
                print("✅ Clustering analysis completed successfully!")
                print()
                print("📊 Results Summary:")
                metadata = clustering_result.metadata
                job_meta = metadata.get('job_clustering', {})
                skills_meta = metadata.get('skills_clustering', {})
                
                print(f"   • Job Clusters: {job_meta.get('n_clusters', 0)} clusters")
                print(f"   • Job Clustering Quality: {job_meta.get('quality_assessment', 'Unknown')}")
                print(f"   • Silhouette Score: {job_meta.get('silhouette_score', 0):.3f}")
                print(f"   • Skills Bundles: {skills_meta.get('n_bundles', 0)} bundles")
                print(f"   • Specialized Skills: {skills_meta.get('n_specialized', 0)} skills")
                print(f"   • Total Skills Processed: {skills_meta.get('total_skills', 0)}")
                print()
                
                return CommandResult(
                    success=True,
                    message="Clustering analysis completed successfully",
                    data=clustering_result.metadata,
                    metadata={
                        'database_path': db_path,
                        'job_clusters': job_meta.get('n_clusters', 0),
                        'skills_bundles': skills_meta.get('n_bundles', 0),
                        'specialized_skills': skills_meta.get('n_specialized', 0)
                    }
                )
            else:
                print("❌ Failed to populate clustering tables.")
                return CommandResult(
                    success=False,
                    message="Clustering analysis completed but database population failed",
                    errors=["Database population failed"]
                )
                
        except Exception as e:
            print(f"❌ Clustering analysis command failed: {e}")
            print("   Check your database and configuration.")
            return CommandResult(
                success=False,
                message=f"Clustering analysis failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _populate_clustering_tables(self, db_integrator, clustering_result) -> bool:
        """Populate database tables with clustering results."""
        try:
            print("   📊 Populating clustering analytics tables...")
            
            # Populate job families table
            print("     • Job families (cluster assignments)...")
            
            # Filter DataFrame to match database schema
            job_families_df = clustering_result.job_clusters_df.copy()
            
            # Map DataFrame columns to database schema columns
            schema_columns = [
                'job_profile_id', 'job_profile', 'job_function', 'job_sub_function', 
                'job_category', 'management_level', 'cluster_id', 'cluster_name', 
                'cluster_description', 'cluster_rationale', 'cluster_size', 
                'sample_jobs', 'sample_skills', 'cluster_confidence', 'silhouette_score',
                'intra_cluster_similarity', 'inter_cluster_distance', 'clustering_algorithm', 
                'algorithm_parameters', 'analysis_date', 'created_timestamp'
            ]
            
            # Rename columns to match schema
            column_mapping = {
                'JobProfileID': 'job_profile_id',
                'JobProfile': 'job_profile', 
                'JobFunction': 'job_function',
                'JobSubFunction': 'job_sub_function',
                'JobCategory': 'job_category',
                'ManagementLevel': 'management_level'
            }
            
            # Apply column mapping
            job_families_df = job_families_df.rename(columns=column_mapping)
            
            # Select only schema columns that exist in the DataFrame
            available_columns = [col for col in schema_columns if col in job_families_df.columns]
            job_families_df = job_families_df[available_columns]
            
            job_success = db_integrator.populate_job_families(job_families_df)
            if not job_success:
                print("     ❌ Failed to populate job families")
                return False
            
            # Populate skill bundles table
            print("     • Skill bundles (cluster assignments)...")
            bundles_success = db_integrator.populate_skill_bundles(clustering_result.skill_bundles_df)
            if not bundles_success:
                print("     ❌ Failed to populate skill bundles")
                return False
            
            # Populate bundle characteristics table
            print("     • Bundle characteristics (cluster metadata)...")
            chars_success = db_integrator.populate_bundle_characteristics(clustering_result.skill_characteristics_df)
            if not chars_success:
                print("     ❌ Failed to populate bundle characteristics")
                return False
            
            # Populate specialized skills table (if available)
            if hasattr(clustering_result, 'specialized_skills_df') and clustering_result.specialized_skills_df is not None:
                print("     • Specialized skills...")
                specialized_success = db_integrator.populate_specialized_skills(clustering_result.specialized_skills_df)
                if not specialized_success:
                    print("     ⚠️ Failed to populate specialized skills (non-critical)")
            
            print("   ✅ All clustering tables populated successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to populate clustering tables: {e}")
            return False
