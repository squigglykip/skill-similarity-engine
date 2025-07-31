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
        
        self.logger.info(f"Analytics orchestrator initialized with database: {self.db_path}")
    
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
            self.logger.info("Starting Phase 1: Enhanced Similarity Analytics")
            
            # Step 1: Verify database prerequisites
            if not self._verify_phase_0_completion():
                self.logger.error("Phase 0 not complete. Cannot proceed with Phase 1.")
                return False
            
            # Step 2: Initialize enhanced similarity components
            enhanced_components = self._setup_enhanced_similarity()
            if not enhanced_components:
                self.logger.error("Failed to setup enhanced similarity components")
                return False
            
            # Step 3: Generate enhanced similarity matrix
            similarity_results = self._calculate_enhanced_similarities(enhanced_components)
            if similarity_results is None:
                self.logger.error("Failed to calculate enhanced similarities")
                return False
            
            # Step 4: Generate skill rarity analysis
            skill_rarity_results = self._generate_skill_rarity_analysis(enhanced_components)
            if skill_rarity_results is None:
                self.logger.error("Failed to generate skill rarity analysis")
                return False
            
            # Step 5: Generate job defining skills
            defining_skills_results = self._generate_job_defining_skills(enhanced_components)
            if defining_skills_results is None:
                self.logger.error("Failed to generate job defining skills")
                return False
            
            # Step 6: Populate database tables directly
            success = True
            success &= self.db_integrator.populate_job_similarities(similarity_results)
            success &= self.db_integrator.populate_skill_rarity(skill_rarity_results) 
            success &= self.db_integrator.populate_job_defining_skills(defining_skills_results)
            
            if success:
                # Update phase completion status
                self._update_phase_completion_status("phase_1", len(similarity_results))
                self.logger.info("Phase 1 enhanced similarity analytics completed successfully")
                return True
            else:
                self.logger.error("Failed to populate one or more analytics tables")
                return False
                
        except Exception as e:
            self.logger.error(f"Phase 1 execution failed: {e}", exc_info=True)
            return False
    
    def execute_phase_2_movement_analysis(self) -> bool:
        """
        Execute Phase 2: Movement Analysis directly to database.
        
        This method:
        1. Loads core_position_timeline data
        2. Executes movement pattern analysis
        3. Populates analytics_movement_patterns
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting Phase 2: Movement Analysis")
            
            # Phase 2 implementation would go here
            # For now, return False to indicate not implemented
            self.logger.warning("Phase 2 implementation not yet available")
            return False
            
        except Exception as e:
            self.logger.error(f"Phase 2 execution failed: {e}", exc_info=True)
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
            self.logger.info("Starting Phase 3: Clustering & Velocity Analytics")
            
            # Phase 3 implementation would go here
            # For now, return False to indicate not implemented
            self.logger.warning("Phase 3 implementation not yet available")
            return False
            
        except Exception as e:
            self.logger.error(f"Phase 3 execution failed: {e}", exc_info=True)
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
                        self.logger.error(f"Phase 0 incomplete: {table} is empty")
                        return False
                
                self.logger.info("Phase 0 verification complete - all core tables populated")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to verify Phase 0 completion: {e}")
            return False
    
    def _setup_enhanced_similarity(self) -> Optional[Dict[str, Any]]:
        """
        Setup enhanced similarity components using modular architecture.
        
        Returns:
            Dictionary with enhanced similarity components or None if setup failed
        """
        try:
            self.logger.info("Setting up enhanced similarity components")
            
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
            
            self.logger.info(f"Enhanced similarity components loaded:")
            self.logger.info(f"  - Skills: {len(skill_universe_df):,}")
            self.logger.info(f"  - Jobs: {len(job_to_skills):,}")
            self.logger.info(f"  - Defining skills mappings: {len(defining_skills_map):,}")
            
            return {
                'skill_universe_df': skill_universe_df,
                'job_skills_df': job_skills_df,
                'job_to_skills': job_to_skills,
                'defining_skills_map': defining_skills_map
            }
            
        except Exception as e:
            self.logger.error(f"Failed to setup enhanced similarity: {e}", exc_info=True)
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
            self.logger.info("Calculating enhanced similarities with centralized orchestrator")
            
            job_to_skills = enhanced_components['job_to_skills']
            defining_skills_map = enhanced_components['defining_skills_map']
            job_ids = list(job_to_skills.keys())
            
            # Create job pairs for full asymmetric comparison
            job_pairs = []
            for job_a_id in job_ids:
                for job_b_id in job_ids:
                    if job_a_id != job_b_id:  # Skip self-comparison
                        job_pairs.append((job_a_id, job_b_id))
            
            self.logger.info(f"Processing {len(job_pairs):,} job similarity pairs using orchestrator")
            
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
            self.logger.info(f"Processing estimates: {estimates['processing_strategy']} strategy, "
                           f"{estimates['estimated_memory_mb']:.1f} MB, "
                           f"{estimates['estimated_chunks']} chunks")
            
            # Process using centralized orchestrator with intelligent strategy selection
            similarities = processing_orchestrator.process_job_similarities(
                calculator=self.rarity_calculator,
                job_pairs=job_pairs,
                job_to_skills=job_to_skills,
                job_defining_skills=defining_skills_map,
                use_intelligent_processing=True
            )
            
            # Convert to DataFrame for corpus normalization
            similarities_df = pd.DataFrame(similarities)
            self.logger.info(f"Generated {len(similarities_df):,} similarity records via orchestrator")
            
            # Apply corpus normalization to preserve differentiation while ensuring 0-1 range
            normalized_df = self._apply_corpus_normalization(similarities_df)
            
            return normalized_df
            
        except Exception as e:
            self.logger.error(f"Failed to calculate enhanced similarities: {e}", exc_info=True)
            return None
    
    def _apply_corpus_normalization(self, similarities_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply corpus-wide normalization to preserve differentiation while ensuring 0-1 range.
        
        Args:
            similarities_df: DataFrame with raw similarity scores
            
        Returns:
            DataFrame with both raw and normalized similarity scores
        """
        try:
            self.logger.info("Applying corpus-wide normalization to similarity scores")
            
            # Initialize corpus normalizer
            normalizer = CorpusNormalizer()
            
            # Map to existing database schema columns first
            similarities_df = similarities_df.copy()
            
            # Map similarity calculator output to existing database schema:
            # The calculator outputs 'enhanced_similarity_score' directly, so use that for normalization
            if 'enhanced_similarity_score' in similarities_df.columns:
                # Use the enhanced score (which contains the defining skills boost) for normalization
                raw_scores = similarities_df['enhanced_similarity_score'].tolist()
            elif 'rarity_weighted_score' in similarities_df.columns:
                # Fallback to rarity weighted score if enhanced not available
                similarities_df['enhanced_similarity_score'] = similarities_df['rarity_weighted_score']
                raw_scores = similarities_df['enhanced_similarity_score'].tolist()
            else:
                # Final fallback to simple similarity
                similarities_df['enhanced_similarity_score'] = similarities_df.get('similarity_score', 0.0)
                raw_scores = similarities_df['enhanced_similarity_score'].tolist()
            
            # Collect raw scores for normalization
            normalizer.collect_raw_scores_batch(raw_scores)
            
            # Normalize the corpus
            normalization_stats = normalizer.normalize_corpus()
            
            # Get normalized scores and put in similarity_score column (final 0-1 range)
            normalized_scores = normalizer.get_normalized_scores_batch(raw_scores)
            similarities_df['similarity_score'] = normalized_scores
            
            # Log normalization results
            self.logger.info(f"Corpus normalization complete:")
            self.logger.info(f"  Total scores: {normalization_stats.total_scores:,}")
            self.logger.info(f"  Raw range: {normalization_stats.raw_min:.4f} - {normalization_stats.raw_max:.4f}")
            self.logger.info(f"  Normalized range: 0.0000 - 1.0000")
            self.logger.info(f"  Normalization factor: {normalization_stats.normalization_factor:.4f}")
            self.logger.info(f"  Scores above 1.0: {normalization_stats.scores_above_1:,} ({normalization_stats.percentage_above_1:.1f}%)")
            self.logger.info(f"  Max boost observed: {normalization_stats.max_boost_observed:.4f}")
            
            return similarities_df
            
        except Exception as e:
            self.logger.error(f"Failed to apply corpus normalization: {e}", exc_info=True)
            # Return original DataFrame if normalization fails
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
            self.logger.info("Generating skill rarity analysis")
            
            skill_universe_df = enhanced_components['skill_universe_df']
            
            # Use the modular rarity analyzer to generate analysis
            rarity_analysis_df = self.rarity_analyzer.generate_skill_rarity_analysis(skill_universe_df)
            
            self.logger.info(f"Generated rarity analysis for {len(rarity_analysis_df):,} skills")
            
            return rarity_analysis_df
            
        except Exception as e:
            self.logger.error(f"Failed to generate skill rarity analysis: {e}", exc_info=True)
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
            self.logger.info("Generating job defining skills analysis")
            
            defining_skills_map = enhanced_components['defining_skills_map']
            skill_universe_df = enhanced_components['skill_universe_df']
            job_skills_df = enhanced_components['job_skills_df']
            
            # Use the modular defining skills analyzer to generate analysis
            defining_skills_df = self.defining_analyzer.generate_job_defining_skills_analysis(
                defining_skills_map, skill_universe_df, job_skills_df
            )
            
            self.logger.info(f"Generated defining skills for {len(defining_skills_df):,} job-skill pairs")
            
            return defining_skills_df
            
        except Exception as e:
            self.logger.error(f"Failed to generate job defining skills: {e}", exc_info=True)
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
                # Update sys_schema_metadata
                conn.execute("""
                    INSERT OR REPLACE INTO sys_schema_metadata 
                    (table_name, record_count, last_updated, phase_completed)
                    VALUES (?, ?, ?, ?)
                """, (f"analytics_{phase}", record_count, pd.Timestamp.now().isoformat(), True))
                
        except Exception as e:
            self.logger.warning(f"Failed to update phase completion status: {e}")
    
    def _load_job_architecture_from_database(self):
        """
        Load job architecture directly from the database.
        
        Returns:
            JobArchitecture instance or None if failed
        """
        try:
            from ..models.jobs import JobArchitecture, Job
            
            self.logger.info("Loading job architecture from database")
            
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
            
            self.logger.info(f"Loaded job architecture with {len(job_architecture.jobs)} jobs")
            return job_architecture
            
        except Exception as e:
            self.logger.error(f"Failed to load job architecture from database: {e}", exc_info=True)
            return None