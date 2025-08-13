"""
Analytics Orchestrator for Phase 1-3 Enhanced Analytics Integration

This module provides the main orchestrator for Phase 1-3 analytics generation
with direct database integration, eliminating intermediate files and creating
a seamless user experience following the NEXT_PHASE_IMPLEMENTATION_GUIDE.md.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

from ..config.architectural_config_manager import get_config_manager
from ..error_handling.recovery import retry, circuit_breaker, recovery_strategy
from ..models.versioning import ModelVersionManager
from ..similarity.rarity_weighted import RarityWeightedCalculator
from ..similarity.skill_rarity import SkillRarityAnalyzer
from ..similarity.defining_skills import DefiningSkillsAnalyzer
from ..similarity.corpus_normalizer import CorpusNormalizer
from ..utils.processing_orchestrator import SimilarityProcessingOrchestrator, ProcessingConfig


class AnalyticsOrchestrator:
    """
    Orchestrates advanced analytics with direct database population.
    
    This class coordinates Phase 1-3 analytics generation, eliminating
    intermediate files and providing a database-first workflow as specified
    in the NEXT_PHASE_IMPLEMENTATION_GUIDE.md.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the analytics orchestrator with modular components.
        
        Args:
            db_path: Optional path to the business context database (auto-detected if None)
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = get_config_manager()
        
        # Auto-detect database path if not provided
        if db_path is None:
            from ..models.versioning import ModelVersionManager
            version_manager = ModelVersionManager()
            output_dir = version_manager.setup_output_directory(
                interactive=False,
                output_type='business_context'
            )
            self.db_path = output_dir / 'business_context.sqlite'
        else:
            self.db_path = db_path
        
        # Initialize database integrator
        from .database_integrator import DatabaseIntegrator
        self.db_integrator = DatabaseIntegrator(self.db_path)
        
        # Initialize modular components
        self.rarity_analyzer = SkillRarityAnalyzer()
        self.defining_analyzer = DefiningSkillsAnalyzer()
        self.rarity_calculator = RarityWeightedCalculator()
        
        print(f"Analytics orchestrator initialized with database: {self.db_path}")
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def execute_phase_1_enhanced_similarity(self) -> bool:
        """
        Execute Phase 1: Enhanced Similarity Analytics directly to database.
        
        This method:
        1. Loads data from core tables
        2. Executes enhanced similarity calculations
        3. Populates analytics_job_similarities, analytics_skill_rarity, analytics_job_defining_skills
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("\n🚀 Starting Enhanced Similarity Analytics...")
            print()
            
            # Step 1: Verify database prerequisites
            if not self._verify_phase_0_completion():
                print("❌ Foundation database not ready. Cannot proceed with analytics.")
                return False
            
            # Step 2: Initialize enhanced similarity components
            print("🔧 Setting up enhanced similarity components...")
            enhanced_components = self._setup_enhanced_similarity()
            if not enhanced_components:
                print("❌ Failed to setup enhanced similarity components")
                return False
            
            # Step 3: Generate enhanced similarity matrix
            print("\n📊 Calculating enhanced job similarities...")
            similarity_results = self._calculate_enhanced_similarities(enhanced_components)
            if similarity_results is None:
                print("❌ Failed to calculate enhanced similarities")
                return False
            
            # Step 4: Generate skill rarity analysis
            print("\n🎯 Generating skill rarity analysis...")
            skill_rarity_results = self._generate_skill_rarity_analysis(enhanced_components)
            if skill_rarity_results is None:
                print("❌ Failed to generate skill rarity analysis")
                return False
            
            # Step 5: Generate job defining skills
            print("\n🔍 Generating job defining skills analysis...")
            defining_skills_results = self._generate_job_defining_skills(enhanced_components)
            if defining_skills_results is None:
                print("❌ Failed to generate job defining skills")
                return False
            
            # Step 6: Populate database tables directly
            print("\n💾 Populating analytics database...")
            success = True
            success &= self.db_integrator.populate_job_similarities(similarity_results)
            success &= self.db_integrator.populate_skill_rarity(skill_rarity_results) 
            success &= self.db_integrator.populate_job_defining_skills(defining_skills_results)
            
            if success:
                # Update phase completion status
                self._update_phase_completion_status("phase_1", len(similarity_results))
                
                # Show completion summary
                print(f"\n✅ Enhanced Similarity Analytics Complete!")
                print(f"   📊 {len(similarity_results):,} job similarity calculations")
                print(f"   🎯 {len(skill_rarity_results):,} skill rarity analyses")  
                print(f"   🔍 {len(defining_skills_results):,} job defining skill mappings")
                print(f"   💾 All data saved to analytics database")
                return True
            else:
                print("❌ Failed to save results to database")
                return False
                
        except Exception as e:
            print(f"❌ Analytics processing failed: {e}")
            print(f"Phase 1 execution failed: {e}")
            return False
    
    def execute_movement_pattern_analysis(self) -> bool:
        """
        Execute movement pattern analysis and populate analytics tables.
        
        This method:
        1. Loads historical position data from database
        2. Detects employee movement patterns
        3. Populates analytics_movement_patterns table
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Starting movement pattern analysis")
            
            # Import and execute the movement pattern population command
            from ..cli.commands.precompute_commands import MovementPatternPopulationCommand
            
            # Create and execute the command
            command = MovementPatternPopulationCommand()
            result = command.run()
            
            if result.success:
                print(f"Movement pattern analysis completed: {result.message}")
                return True
            else:
                print(f"Movement pattern analysis failed: {result.message}")
                if result.errors:
                    for error in result.errors:
                        print(f"  Error: {error}")
                return False
            
        except Exception as e:
            print(f"Movement pattern analysis execution failed: {e}")
            return False
    
    def execute_movement_ml_training(self) -> bool:
        """
        Execute ML model training from populated movement patterns.
        
        This method:
        1. Validates that movement patterns are available
        2. Trains ensemble ML models (Random Forest, XGBoost, Gradient Boosting)
        3. Generates pathway predictions for real-time prediction models
        4. Saves trained models as .joblib files for webapp consumption
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Starting Phase 2.2: ML Model Training")
            
            # Verify movement patterns are available
            if not self._verify_movement_patterns_available():
                print("Movement patterns not available - run movement pattern analysis first")
                return False
            
            # Import and execute the ML training command
            from ..cli.commands.precompute_commands import MovementMLTrainingCommand
            
            # Create and execute the command
            command = MovementMLTrainingCommand()
            result = command.run(db_path=str(self.db_path), interactive=True)
            
            if result.success:
                # ML training completed successfully - models saved to quarterly folder
                print(f"ML model training completed: {result.message}")
                
                # Get model info from command result for logging
                model_info = result.data.get('performance_metrics', {}) if result.data else {}
                if model_info:
                    total_predictions = model_info.get('total_predictions', 0)
                    best_model_r2 = model_info.get('best_model_r2', 0)
                    print(f"Models trained with {total_predictions:,} pathway predictions, R²: {best_model_r2:.3f}")
                    
                    # Update phase completion status
                    self._update_phase_completion_status("phase_2_ml", total_predictions)
                else:
                    # Update phase completion status with default
                    self._update_phase_completion_status("phase_2_ml", 0)
                return True
            else:
                print(f"ML model training failed: {result.message}")
                if result.errors:
                    for error in result.errors:
                        print(f"  Error: {error}")
                return False
            
        except Exception as e:
            print(f"ML model training execution failed: {e}")
            return False
    
    def _verify_movement_patterns_available(self) -> bool:
        """Verify that movement patterns are available for ML training."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM analytics_movement_patterns")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print("No movement patterns found in analytics_movement_patterns table")
                    return False
                
                print(f"Found {count:,} movement patterns ready for ML training")
                return True
                
        except sqlite3.Error as e:
            print(f"Failed to verify movement patterns availability: {e}")
            return False
    
    def execute_phase_3_clustering_velocity(self) -> bool:
        """
        Execute Phase 3: Clustering & Velocity directly to database.
        
        This method:
        1. Loads similarity and movement data
        2. Executes clustering algorithms
        3. Populates analytics_job_families, analytics_skill_bundles, etc.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Starting Phase 3: Clustering & Velocity Analytics")
            
            # Phase 3 implementation would go here
            # For now, return False to indicate not implemented
            print("Phase 3 implementation not yet available")
            return False
            
        except Exception as e:
            print(f"Phase 3 execution failed: {e}")
            return False
    
    def _verify_phase_0_completion(self) -> bool:
        """
        Verify that Phase 0 foundation data is complete.
        
        Returns:
            True if Phase 0 is complete, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check for required core tables with data
                required_tables = [
                    'core_job_architecture',
                    'core_skills_taxonomy', 
                    'core_job_skill_requirements',
                    'core_workforce_current',
                    'core_position_timeline'
                ]
                
                for table in required_tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count == 0:
                        print(f"Phase 0 incomplete: {table} is empty")
                        return False
                
                print("Phase 0 verification complete - all core tables populated")
                return True
                
        except Exception as e:
            print(f"Failed to verify Phase 0 completion: {e}")
            return False
    
    def _setup_enhanced_similarity(self) -> Optional[Dict[str, Any]]:
        """
        Setup enhanced similarity components using modular architecture.
        
        Returns:
            Dictionary with enhanced similarity components or None if setup failed
        """
        try:
            print("Setting up enhanced similarity components")
            
            # Load skill universe with rarity data
            skill_universe_df = self.rarity_analyzer.load_skill_universe_from_database(str(self.db_path))
            
            # Load job-skill relationships
            job_skills_df = self.defining_analyzer.load_job_skills_from_database(str(self.db_path))
            
            # Convert to job_to_skills mapping
            job_to_skills = {}
            for job_id, group in job_skills_df.groupby('JobProfileID'):
                job_to_skills[job_id] = set(group['Skill_Name'].tolist())
            
            # Create job-specific defining skills
            defining_skills_map = self.defining_analyzer.create_job_specific_defining_skills(
                skill_universe_df, job_skills_df
            )
            
            print(f"   ✅ Components ready: {len(skill_universe_df):,} skills • {len(job_to_skills):,} jobs • {len(defining_skills_map):,} defining skill mappings")
            
            return {
                'skill_universe_df': skill_universe_df,
                'job_skills_df': job_skills_df,
                'job_to_skills': job_to_skills,
                'defining_skills_map': defining_skills_map
            }
            
        except Exception as e:
            print(f"Failed to setup enhanced similarity: {e}")
            return None
    
    def _calculate_enhanced_similarities(self, enhanced_components: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Calculate enhanced similarities for all job pairs using centralized processing orchestrator.
        
        Args:
            enhanced_components: Enhanced similarity components
            
        Returns:
            DataFrame with enhanced similarity results or None if failed
        """
        try:
            # Starting similarity calculations
            
            job_to_skills = enhanced_components['job_to_skills']
            defining_skills_map = enhanced_components['defining_skills_map']
            job_ids = list(job_to_skills.keys())
            
            # Create job pairs for full asymmetric comparison
            job_pairs = []
            for job_a_id in job_ids:
                for job_b_id in job_ids:
                    if job_a_id != job_b_id:  # Skip self-comparison
                        job_pairs.append((job_a_id, job_b_id))
            
            print(f"   Processing {len(job_pairs):,} job similarity pairs...")
            
            # Show stratified job distribution for enhanced transparency  
            job_categories = self.rarity_calculator._stratify_jobs_by_size(job_ids, job_to_skills)
            print(f"📊 Job Distribution by Size Category:")
            for category, category_jobs in job_categories.items():
                if category_jobs:
                    # Get parameters for this category
                    sample_job_size = len(job_to_skills.get(category_jobs[0], set()))
                    multiplier = self.rarity_calculator._get_stratified_multiplier_for_job(sample_job_size)
                    percentile = self.rarity_calculator._get_stratified_percentile_for_job(sample_job_size)
                    
                    # Count pairs for this category (source jobs from this category to all other jobs)
                    category_pairs_count = len(category_jobs) * (len(job_ids) - 1)  # -1 for no self-comparison
                    
                    print(f"   • {category.replace('_', ' ').title()}: {len(category_jobs)} jobs → {category_pairs_count:,} comparisons ({percentile:.1f}% threshold, {multiplier:.3f}x multiplier)")
            
            # Configure processing orchestrator for production workload
            config = ProcessingConfig(
                memory_threshold_mb=1500.0,  # 1.5GB threshold for chunking
                item_size_estimate_bytes=300.0,  # Each similarity record ~300 bytes
                target_chunk_count=25,  # Good balance for 500K+ comparisons
                min_chunk_size=10000,   # Minimum 10K comparisons per chunk
                max_chunk_size=50000,   # Maximum 50K comparisons per chunk
                progress_desc="Enhanced Similarity Calculation",
                show_memory_tracking=True
            )
            
            # Initialize the centralized processing orchestrator
            processing_orchestrator = SimilarityProcessingOrchestrator(config)
            
            # Show processing estimates
            estimates = processing_orchestrator.estimate_processing_requirements(len(job_pairs))
            print(f"Processing estimates: {estimates['processing_strategy']} strategy, "
                           f"{estimates['estimated_memory_mb']:.1f} MB, "
                           f"{estimates['estimated_chunks']} chunks")
            
            # Process using centralized orchestrator with intelligent strategy selection and stratified progress
            similarities = processing_orchestrator.process_job_similarities(
                calculator=self.rarity_calculator,
                job_pairs=job_pairs,
                job_to_skills=job_to_skills,
                job_defining_skills=defining_skills_map,
                use_intelligent_processing=True,
                use_stratified_progress=True  # Enable stratified progress tracking by job size
            )
            
            # Convert to DataFrame for corpus normalization
            similarities_df = pd.DataFrame(similarities)
            print(f"   ✅ Generated {len(similarities_df):,} similarity calculations")
            
            # Apply corpus normalization to preserve differentiation while ensuring 0-1 range
            normalized_df = self._apply_corpus_normalization(similarities_df)
            
            return normalized_df
            
        except Exception as e:
            print(f"Failed to calculate enhanced similarities: {e}")
            return None
    
    def _apply_corpus_normalization(self, similarities_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply corpus-wide normalization with selective column handling based on configuration.
        
        Args:
            similarities_df: DataFrame with raw similarity scores
            
        Returns:
            DataFrame with selective normalization applied per configuration
        """
        try:
            print(f"   🔧 Applying selective corpus normalization...")
            
            # Load normalization configuration
            normalization_config = self.config_manager.get_nested_value(
                'core', 'similarity_parameters', 'normalization_config'
            )
            
            # Apply default behavior if no config
            if not normalization_config:
                return self._apply_legacy_normalization(similarities_df)
            
            # Initialize corpus normalizer with method from config
            normalization_method = normalization_config.get('method', 'corpus_max_normalization')
            normalizer = CorpusNormalizer(normalization_method=normalization_method)
            similarities_df = similarities_df.copy()
            
            # Determine which column contains the enhanced scores for normalization
            if 'enhanced_similarity_score' in similarities_df.columns:
                enhanced_scores = similarities_df['enhanced_similarity_score'].tolist()
            elif 'rarity_weighted_score' in similarities_df.columns:
                enhanced_scores = similarities_df['rarity_weighted_score'].tolist()
            else:
                enhanced_scores_series = similarities_df.get('similarity_score', pd.Series([0.0] * len(similarities_df)))
                enhanced_scores = enhanced_scores_series.tolist() if hasattr(enhanced_scores_series, 'tolist') else list(enhanced_scores_series)
            
            # Collect and normalize the enhanced scores
            normalizer.collect_raw_scores_batch(enhanced_scores)
            normalization_stats = normalizer.normalize_corpus()
            normalized_scores = normalizer.get_normalized_scores_batch(enhanced_scores)
            
            # Apply selective normalization based on configuration
            if normalization_config.get('normalize_enhanced_similarity_score', True):
                # Normalize the enhanced_similarity_score column
                similarities_df['enhanced_similarity_score'] = normalized_scores
                print(f"   ✅ Normalized enhanced_similarity_score column")
            
            if normalization_config.get('preserve_raw_rarity_weighted_score', True):
                # Keep rarity_weighted_score as raw values
                if 'rarity_weighted_score' not in similarities_df.columns:
                    similarities_df['rarity_weighted_score'] = enhanced_scores
                print(f"   💾 Preserved raw values in rarity_weighted_score column")
            
            # IMPORTANT: Keep similarity_score as the original baseline scores (NOT normalized enhanced scores)
            # similarity_score should contain the basic Jaccard similarity without defining skills boost
            # This is already set correctly from the original calculation, so we DON'T overwrite it
            print(f"   📊 Preserved baseline similarity_score column (basic Jaccard without defining skills boost)")
            
            # Show normalization summary
            print(f"   📊 Normalized {normalization_stats.total_scores:,} scores (range: {normalization_stats.raw_min:.2f} - {normalization_stats.raw_max:.2f} → 0.00 - 1.00)")
            print(f"   🚀 Normalization factor: {normalization_stats.normalization_factor:.2f} • {normalization_stats.scores_above_1:,} scores ({normalization_stats.percentage_above_1:.1f}%) boosted above 1.0")
            
            return similarities_df
            
        except Exception as e:
            print(f"Failed to apply corpus normalization: {e}")
            # Return original DataFrame if normalization fails
            return similarities_df
    
    def _apply_legacy_normalization(self, similarities_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply legacy normalization behavior for backward compatibility.
        
        Args:
            similarities_df: DataFrame with raw similarity scores
            
        Returns:
            DataFrame with legacy normalization applied
        """
        # Initialize corpus normalizer
        normalizer = CorpusNormalizer()
        similarities_df = similarities_df.copy()
        
        # Use enhanced score for normalization
        if 'enhanced_similarity_score' in similarities_df.columns:
            raw_scores = similarities_df['enhanced_similarity_score'].tolist()
        elif 'rarity_weighted_score' in similarities_df.columns:
            similarities_df['enhanced_similarity_score'] = similarities_df['rarity_weighted_score']
            raw_scores = similarities_df['enhanced_similarity_score'].tolist()
        else:
            similarities_df['enhanced_similarity_score'] = similarities_df.get('similarity_score', 0.0)
            raw_scores = similarities_df['enhanced_similarity_score'].tolist()
        
        # Collect raw scores for normalization
        normalizer.collect_raw_scores_batch(raw_scores)
        
        # Normalize the corpus
        normalization_stats = normalizer.normalize_corpus()
        
        # Get normalized scores and put in similarity_score column (final 0-1 range)
        normalized_scores = normalizer.get_normalized_scores_batch(raw_scores)
        similarities_df['similarity_score'] = normalized_scores
        
        return similarities_df
    
    def _generate_skill_rarity_analysis(self, enhanced_components: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Generate skill rarity analysis using modular components.
        
        Args:
            enhanced_components: Enhanced similarity components
            
        Returns:
            DataFrame with skill rarity analysis or None if failed
        """
        try:
            # Starting skill rarity analysis
            
            skill_universe_df = enhanced_components['skill_universe_df']
            
            # Use the modular rarity analyzer to generate analysis
            rarity_analysis_df = self.rarity_analyzer.generate_skill_rarity_analysis(skill_universe_df)
            
            # Rarity analysis completed
            
            return rarity_analysis_df
            
        except Exception as e:
            print(f"Failed to generate skill rarity analysis: {e}")
            return None
    
    def _generate_job_defining_skills(self, enhanced_components: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Generate job defining skills analysis using modular components.
        
        Args:
            enhanced_components: Enhanced similarity components
            
        Returns:
            DataFrame with job defining skills or None if failed
        """
        try:
            # Starting job defining skills analysis
            
            defining_skills_map = enhanced_components['defining_skills_map']
            skill_universe_df = enhanced_components['skill_universe_df']
            job_skills_df = enhanced_components['job_skills_df']
            
            # Use the modular defining skills analyzer to generate analysis
            defining_skills_df = self.defining_analyzer.generate_job_defining_skills_analysis(
                defining_skills_map, skill_universe_df, job_skills_df
            )
            
            # Defining skills analysis completed
            
            return defining_skills_df
            
        except Exception as e:
            print(f"Failed to generate job defining skills: {e}")
            return None
    
    def _update_phase_completion_status(self, phase: str, record_count: int):
        """
        Update phase completion status in system metadata.
        
        Args:
            phase: Phase identifier (e.g., 'phase_1')
            record_count: Number of records processed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update sys_schema_metadata with correct column names
                metadata_key = f"analytics_{phase}_record_count"
                metadata_value = str(record_count)
                updated_timestamp = pd.Timestamp.now().isoformat()
                
                conn.execute("""
                    INSERT OR REPLACE INTO sys_schema_metadata 
                    (metadata_key, metadata_value, metadata_category, description, updated_timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (metadata_key, metadata_value, "analytics_status", f"Record count for {phase} completion", updated_timestamp))
                
                # Also update phase completion flag
                phase_key = f"analytics_{phase}_completed"
                conn.execute("""
                    INSERT OR REPLACE INTO sys_schema_metadata 
                    (metadata_key, metadata_value, metadata_category, description, updated_timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (phase_key, "true", "analytics_status", f"Completion status for {phase}", updated_timestamp))
                
        except Exception as e:
            print(f"⚠️ Failed to update phase completion status: {e}")
    
    def _load_job_architecture_from_database(self):
        """
        Load job architecture directly from the database.
        
        Returns:
            JobArchitecture instance or None if failed
        """
        try:
            from ..models.jobs import JobArchitecture, Job
            
            print("Loading job architecture from database")
            
            # Create empty architecture
            job_architecture = JobArchitecture()
            
            with sqlite3.connect(self.db_path) as conn:
                # Load jobs from core_job_architecture
                job_query = """
                SELECT JobProfileID, JobProfile, JobID, Job, 
                       ManagementLevel, JobFunction, JobCategory
                FROM core_job_architecture
                """
                job_cursor = conn.execute(job_query)
                
                for row in job_cursor:
                    job_id, job_profile, job_code, job_name, mgmt_level, function, category = row
                    
                    # Create Job instance with correct parameters
                    from ..models.jobs import JobLevel
                    
                    # Map management level to JobLevel enum
                    level_mapping = {
                        'Entry': JobLevel.ENTRY,
                        'Associate': JobLevel.ASSOCIATE, 
                        'Mid-level': JobLevel.MID_LEVEL,
                        'Senior': JobLevel.SENIOR,
                        'Lead': JobLevel.LEAD,
                        'Manager': JobLevel.MANAGER,
                        'Director': JobLevel.DIRECTOR,
                        'Executive': JobLevel.EXECUTIVE
                    }
                    
                    job_level = level_mapping.get(mgmt_level, JobLevel.MID_LEVEL)
                    
                    job = Job(
                        job_id=str(job_id),
                        title=job_name or job_profile,
                        department=category or 'Unknown',
                        level=job_level
                    )
                    
                    # Load skills for this job
                    skills_query = """
                    SELECT s.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, s.SkillType
                    FROM core_job_skill_requirements js
                    JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID
                    WHERE js.JobProfileID = ?
                    """
                    skills_cursor = conn.execute(skills_query, (job_id,))
                    
                    for skill_row in skills_cursor:
                        skill_id, skill_name, category, subcategory, skill_type = skill_row
                        
                        # Add skill to job (Job.add_skill expects skill_id and proficiency)
                        job.add_skill(str(skill_id), proficiency=3)  # Default proficiency level
                    
                    # Add job to architecture
                    job_architecture.add_job(job)
            
            print(f"Loaded job architecture with {len(job_architecture.jobs)} jobs")
            return job_architecture
            
        except Exception as e:
            print(f"Failed to load job architecture from database: {e}")
            return None