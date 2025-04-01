"""
HRIS Workflow Integration Module.

This module integrates HRIS data transformation into the skill similarity engine workflow.
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple

from .transformer import HRISTransformer, HRISTransformerError
from ..config.settings import get_config
from ..models.skills import SkillTaxonomy
from ..models.jobs import JobArchitecture
from ..models.employees import EmployeeDatabase


class HRISWorkflow:
    """
    Workflow manager for HRIS data integration.
    
    This class provides a unified workflow that:
    1. Transforms HRIS data into the format expected by the skill similarity engine
    2. Loads the transformed data into the appropriate model objects
    3. Runs the requested analysis
    
    Attributes:
        transformer (HRISTransformer): HRIS data transformer
        logger (logging.Logger): Logger instance
    """
    
    def __init__(self, config_path: Optional[str] = None, log_level: str = "INFO"):
        """
        Initialize the HRIS workflow manager.
        
        Args:
            config_path: Path to the HRIS configuration file (default: use default path)
            log_level: Logging level (default: INFO)
        """
        self.transformer = HRISTransformer(config_path, log_level)
        self.logger = logging.getLogger("hris_workflow")
        self.logger.setLevel(getattr(logging, log_level))
        
        # Add console handler if no handlers exist
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("Initialized HRIS workflow manager")
    
    def run_pipeline(self, analysis_type: str, **kwargs) -> Any:
        """
        Run the complete pipeline from HRIS data to analysis results.
        
        Args:
            analysis_type: Type of analysis to run (job_similarity, employee_job_similarity, etc.)
            **kwargs: Additional arguments for the specific analysis
        
        Returns:
            Analysis results (format depends on the analysis type)
        
        Raises:
            ValueError: If an unsupported analysis type is specified
        """
        try:
            self.logger.info(f"Starting HRIS pipeline for analysis: {analysis_type}")
            
            # Step 1: Transform HRIS data
            jobs_path, skills_path = self.transformer.transform()
            
            # Step 2: Load transformed data into model objects
            taxonomy, job_arch, employee_db = self._load_models(jobs_path, skills_path)
            
            # Step 3: Run the requested analysis
            result = self._run_analysis(analysis_type, taxonomy, job_arch, employee_db, **kwargs)
            
            self.logger.info(f"HRIS pipeline completed successfully for {analysis_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"HRIS pipeline failed: {e}")
            raise
    
    def _load_models(self, jobs_path: str, skills_path: str) -> Tuple[SkillTaxonomy, JobArchitecture, Optional[EmployeeDatabase]]:
        """
        Load transformed data into model objects.
        
        Args:
            jobs_path: Path to the transformed jobs file
            skills_path: Path to the transformed skills file
        
        Returns:
            Tuple of model objects (skill_taxonomy, job_architecture, employee_database)
        """
        self.logger.info("Loading transformed data into model objects")
        
        # Ensure we use absolute paths
        jobs_path = os.path.abspath(jobs_path)
        skills_path = os.path.abspath(skills_path)
        
        # Store these for later use by other components
        self.jobs_path = jobs_path
        self.skills_path = skills_path
        
        # Load skill taxonomy
        self.logger.info(f"Loading skill taxonomy from: {skills_path}")
        taxonomy = SkillTaxonomy.from_file(skills_path)
        self.taxonomy = taxonomy
        
        # Load job architecture
        self.logger.info(f"Loading job architecture from: {jobs_path}")
        job_arch = JobArchitecture.from_file(jobs_path)
        self.job_architecture = job_arch
        
        # Load employee database if available
        employee_db = None
        employee_path = os.path.join(os.path.dirname(jobs_path), "employees.csv")
        if os.path.exists(employee_path):
            self.logger.info(f"Loading employee database from: {employee_path}")
            try:
                employee_db = EmployeeDatabase.from_file(employee_path, job_arch)
            except TypeError:
                # Try without job_arch parameter if signature has changed
                employee_db = EmployeeDatabase.from_file(employee_path)
            self.employee_db = employee_db
        
        return taxonomy, job_arch, employee_db
    
    def _run_analysis(self, analysis_type: str, 
                     taxonomy: SkillTaxonomy, 
                     job_arch: JobArchitecture, 
                     employee_db: Optional[EmployeeDatabase],
                     **kwargs) -> Any:
        """
        Run the requested analysis.
        
        Args:
            analysis_type: Type of analysis to run
            taxonomy: Skill taxonomy model
            job_arch: Job architecture model
            employee_db: Employee database model (optional)
            **kwargs: Additional arguments for the specific analysis
        
        Returns:
            Analysis results (format depends on the analysis type)
        
        Raises:
            ValueError: If an unsupported analysis type is specified
        """
        self.logger.info(f"Running analysis: {analysis_type}")
        
        # Import needed analysis modules
        from ..similarity.cosine import CosineSimilarityCalculator
        from ..config.settings import ConfigManager
        
        # Create configuration manager
        config_manager = ConfigManager()
        config_manager.config = get_config()
        
        # Create similarity calculator
        from ..similarity.cosine import TfidfVectorizer
        vectorizer = TfidfVectorizer(taxonomy)
        calculator = CosineSimilarityCalculator(
            vectorizer=vectorizer,
            skill_taxonomy=taxonomy,
            job_architecture=job_arch,
            employee_database=employee_db,
            config_manager=config_manager
        )
        
        # Run the appropriate analysis based on the analysis type
        if analysis_type == "job_similarity":
            # Calculate job-to-job similarity
            similarity_matrix, job_ids = calculator.calculate_similarity_matrix("job")
            return similarity_matrix, job_ids
            
        elif analysis_type == "employee_job_similarity":
            # Calculate employee-to-job similarity
            if employee_db is None:
                raise ValueError("Employee database is required for employee-job similarity analysis")
            similarity_matrix, employee_ids, job_ids = calculator.calculate_similarity_matrix("emp_job")
            return similarity_matrix, employee_ids, job_ids
            
        elif analysis_type == "employee_similarity":
            # Calculate employee-to-employee similarity
            if employee_db is None:
                raise ValueError("Employee database is required for employee similarity analysis")
            similarity_matrix, employee_ids = calculator.calculate_similarity_matrix("emp")
            return similarity_matrix, employee_ids
            
        elif analysis_type == "skill_gap_analysis":
            # Perform skill gap analysis
            from ..analysis.gap import SkillGapAnalyzer
            
            if employee_db is None:
                raise ValueError("Employee database is required for skill gap analysis")
                
            # Extract specific employee and job IDs if provided
            employee_id = kwargs.get("employee_id")
            job_id = kwargs.get("job_id")
            
            # Create gap analyzer
            gap_analyzer = SkillGapAnalyzer(taxonomy, config_manager.config.gap_analysis)
            
            if employee_id and job_id:
                # Analyze specific employee against specific job
                employee = employee_db.get_employee(employee_id)
                job = job_arch.get_job(job_id)
                return gap_analyzer.analyze_employee_job_gap(employee, job)
            else:
                # Comprehensive gap analysis
                return gap_analyzer.analyze_workforce_gaps(employee_db, job_arch)
                
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")


# Create a singleton instance for easy access
hris_workflow = HRISWorkflow() 