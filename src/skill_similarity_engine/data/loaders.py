"""
Data loaders for importing skill taxonomy, job architecture, and employee data.

This module provides functionality for loading data from CSV and Excel files.
"""

import os
import logging
from typing import Dict, List, Optional, Set, Tuple, Union

import pandas as pd

from ..config.settings import get_config, get_data_path
from ..config.field_mapping import get_field_mapper, get_raw_field_name
from ..models.employees import Employee, EmployeeDatabase
from ..models.jobs import Job, JobArchitecture, JobLevel
from ..models.skills import Skill, SkillCategory, SkillTaxonomy, SkillType


class SkillTaxonomyLoader:
    """
    Loader for skill taxonomy data from CSV or Excel files.
    
    Attributes:
        base_dir: Base directory for data files
        field_mapper: Field mapping utility for handling different data schemas
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the skill taxonomy loader.
        
        Args:
            base_dir: Base directory for data files (default: from config)
        """
        self.base_dir = base_dir or get_config().data_dir
        self.field_mapper = get_field_mapper()
    
    def load_from_csv(self, 
                    skills_file: str,
                    categories_file: Optional[str] = None,
                    chunked: bool = False,
                    chunksize: int = 10000,
                    validate: bool = True) -> SkillTaxonomy:
        """
        Load skill taxonomy from CSV files, with optional chunked/streaming loading and validation.
        
        Args:
            skills_file: Path to the skills CSV file
            categories_file: Path to the categories CSV file (optional)
            chunked: Whether to use chunked/streaming loading (default: False)
            chunksize: Number of rows per chunk if chunked (default: 10000)
            validate: Whether to validate rows using the validation engine (default: True)
            
        Returns:
            Loaded skill taxonomy
        """
        from skill_similarity_engine.data_validation.validators import ValidationEngine
        from skill_similarity_engine.utils.progress import ProgressTracker
        import logging
        logger = logging.getLogger("skill_similarity_engine.data.loaders")
        
        # Create empty taxonomy
        taxonomy = SkillTaxonomy()
        
        # Load categories if provided (not chunked, as usually small)
        if categories_file:
            categories_path = os.path.join(self.base_dir, categories_file)
            categories_df = pd.read_csv(categories_path)
            for _, row in categories_df.iterrows():
                category = self._parse_category_row(row)
                if category:
                    taxonomy.add_category(category)
        
        # Prepare validation engine if needed
        validator = None
        if validate:
            try:
                validator = ValidationEngine('skills')
            except Exception as e:
                logger.warning(f"Could not initialise validation engine: {e}")
                validator = None
        
        # Load skills (chunked or not)
        skills_path = os.path.join(self.base_dir, skills_file)
        total_rows = None
        if chunked:
            # Try to get total rows for progress bar
            try:
                with open(skills_path, 'r', encoding='utf-8') as f:
                    total_rows = sum(1 for _ in f) - 1  # minus header
            except Exception:
                total_rows = 0
            reader = pd.read_csv(skills_path, chunksize=chunksize)
            processed = 0
            with ProgressTracker(total=total_rows if total_rows is not None else 0, desc="Loading skills (chunked)", show_tqdm=True) as progress:
                for chunk in reader:
                    for idx, row in chunk.iterrows():
                        row_dict = row.to_dict()
                        # Validate row if enabled
                        if validator:
                            results = validator.validate_row(row_dict)
                            if any(not r.passed for r in results):
                                logger.warning(f"Validation failed for row {int(processed)+1}: {[r.message for r in results if not r.passed]}")
                                continue
                        # Parse and add skill
                        skill = self._parse_skill_row(row, taxonomy)
                        if skill:
                            taxonomy.add_skill(skill)
                        processed += 1
                        progress.update(1)
        else:
            skills_df = pd.read_csv(skills_path)
            total_rows = len(skills_df)
            with ProgressTracker(total=total_rows, desc="Loading skills", show_tqdm=True) as progress:
                for idx, row in skills_df.iterrows():
                    row_dict = row.to_dict()
                    if validator:
                        results = validator.validate_row(row_dict)
                        if any(not r.passed for r in results):
                            logger.warning(f"Validation failed for row {idx+1}: {[r.message for r in results if not r.passed]}")
                            continue
                    skill = self._parse_skill_row(row, taxonomy)
                    if skill:
                        taxonomy.add_skill(skill)
                    progress.update(1)
        logger.info(f"Loaded {len(taxonomy.skills)} skills into taxonomy.")
        return taxonomy
    
    def _parse_category_row(self, row: pd.Series) -> Optional[SkillCategory]:
        """
        Parse a category row into a SkillCategory object using field mapping.
        
        Args:
            row: Pandas Series representing a category row
            
        Returns:
            SkillCategory object or None if parsing fails
        """
        try:
            # Get field names using field mapping
            category_id_field = get_raw_field_name('category_id', 'skill_categories')
            name_field = get_raw_field_name('name', 'skill_categories')
            parent_id_field = get_raw_field_name('parent_id', 'skill_categories')
            description_field = get_raw_field_name('description', 'skill_categories')
            
            # Extract values using mapped field names
            category_id = str(row[category_id_field]) if category_id_field in row else None
            name = row[name_field] if name_field in row else None
            parent_id = str(row[parent_id_field]) if parent_id_field in row and pd.notna(row.get(parent_id_field, None)) else None
            description = row.get(description_field, "") if description_field in row else ""
            
            if not category_id or not name:
                return None
                
            return SkillCategory(
                category_id=category_id,
                name=name,
                parent_id=parent_id,
                description=description
            )
        except Exception as e:
            logger = logging.getLogger("skill_similarity_engine.data.loaders")
            logger.warning(f"Failed to parse category row: {e}")
            return None
    
    def _parse_skill_row(self, row: pd.Series, taxonomy: SkillTaxonomy) -> Optional[Skill]:
        """
        Parse a skill row into a Skill object using field mapping.
        
        Args:
            row: Pandas Series representing a skill row
            taxonomy: The skill taxonomy for context
            
        Returns:
            Skill object or None if parsing fails
        """
        try:
            # Get field names using field mapping
            skill_id_field = get_raw_field_name('skill_id', 'skills')
            name_field = get_raw_field_name('name', 'skills')
            description_field = get_raw_field_name('description', 'skills')
            category_id_field = get_raw_field_name('category_id', 'skills')
            
            # Extract core values - handle both comprehensive and simple schemas
            skill_id = None
            # Try comprehensive schema first
            if 'skill_id' in row and pd.notna(row['skill_id']):
                skill_id = str(row['skill_id'])
            elif skill_id_field in row and pd.notna(row[skill_id_field]):
                skill_id = str(row[skill_id_field])
            elif 'Skill_ID' in row and pd.notna(row['Skill_ID']):
                skill_id = str(row['Skill_ID'])  # Legacy fallback
            
            name = None
            # Try comprehensive schema first
            if 'name' in row and pd.notna(row['name']):
                name = row['name']
            elif name_field in row and pd.notna(row[name_field]):
                name = row[name_field]
            elif 'Skill_Name' in row and pd.notna(row['Skill_Name']):
                name = row['Skill_Name']  # Legacy fallback
            
            # Description
            description = ""
            if 'description' in row and pd.notna(row['description']):
                description = row['description']
            elif description_field in row and pd.notna(row[description_field]):
                description = row[description_field]
            
            # Category ID - try multiple sources
            category_id = None
            if 'category_id' in row and pd.notna(row['category_id']):
                category_id = str(row['category_id'])
            elif category_id_field in row and pd.notna(row[category_id_field]):
                category_id = str(row[category_id_field])
            elif 'Category' in row and pd.notna(row['Category']):
                category_id = str(row['Category'])  # Legacy fallback
            
            # Handle skill_type which may have multiple possible field names
            skill_type_field = None
            skill_type_value = None
            
            # Try comprehensive schema first
            if 'type' in row and pd.notna(row['type']):
                skill_type_value = row['type']
            elif 'skill_type' in row and pd.notna(row['skill_type']):
                skill_type_value = row['skill_type']
            elif 'SkillType' in row and pd.notna(row['SkillType']):
                skill_type_value = row['SkillType']  # Legacy fallback
            else:
                # Try different possible skill type field names
                for possible_field in ['category', 'Category']:
                    mapped_field = get_raw_field_name(possible_field, 'skills')
                    if mapped_field in row and pd.notna(row[mapped_field]):
                        skill_type_field = mapped_field
                        skill_type_value = row[mapped_field]
                        break
            
            # Determine skill type
            skill_type = SkillType.COMMON  # Default
            if skill_type_value:
                try:
                    skill_type = SkillType.from_string(skill_type_value)
                except ValueError:
                    # If conversion fails, keep default
                    pass
            
            if not skill_id or not name:
                return None
            
            return Skill(
                skill_id=skill_id,
                name=name,
                description=description,
                category_id=category_id,
                skill_type=skill_type
            )
        except Exception as e:
            logger = logging.getLogger("skill_similarity_engine.data.loaders")
            logger.warning(f"Failed to parse skill row: {e}")
            return None
    
    def load_from_excel(self,
                       excel_file: str,
                       skills_sheet: str = "Skills",
                       categories_sheet: Optional[str] = "Categories") -> SkillTaxonomy:
        """
        Load skill taxonomy from an Excel file.
        
        Args:
            excel_file: Path to the Excel file
            skills_sheet: Name of the sheet containing skills data
            categories_sheet: Name of the sheet containing categories data (optional)
            
        Returns:
            Loaded skill taxonomy
        """
        # Create empty taxonomy
        taxonomy = SkillTaxonomy()
        
        excel_path = os.path.join(self.base_dir, excel_file)
        
        # Load categories if sheet exists
        if categories_sheet:
            try:
                categories_df = pd.read_excel(excel_path, sheet_name=categories_sheet)
                
                for _, row in categories_df.iterrows():
                    category = self._parse_category_row(row)
                    if category:
                        taxonomy.add_category(category)
            except Exception as e:
                import logging
                logger = logging.getLogger("skill_similarity_engine.data.loaders")
                logger.warning(f"Could not load categories from Excel sheet '{categories_sheet}': {e}")
        
        # Load skills
        try:
            skills_df = pd.read_excel(excel_path, sheet_name=skills_sheet)
            
            for _, row in skills_df.iterrows():
                skill = self._parse_skill_row(row, taxonomy)
                if skill:
                    taxonomy.add_skill(skill)
                    
        except Exception as e:
            import logging
            logger = logging.getLogger("skill_similarity_engine.data.loaders")
            logger.error(f"Could not load skills from Excel sheet '{skills_sheet}': {e}")
            raise
        
        return taxonomy

    def _parse_list_field(self, row: pd.Series, field_name: str, section: str = 'skills') -> List[str]:
        """
        Parse a list field from a DataFrame row using field mapping.
        
        Args:
            row: DataFrame row
            field_name: Canonical field name to parse
            section: Configuration section for field mapping
            
        Returns:
            List of values
        """
        # Get the raw field name using field mapping
        raw_field_name = get_raw_field_name(field_name, section)
        
        if raw_field_name not in row or pd.isna(row[raw_field_name]):
            return []
            
        value = row[raw_field_name]
        
        # If already a list, return it
        if isinstance(value, list):
            return value
            
        # If string, parse based on delimiters
        if isinstance(value, str):
            if ',' in value:
                return [item.strip() for item in value.split(',') if item.strip()]
            elif ';' in value:
                return [item.strip() for item in value.split(';') if item.strip()]
            else:
                # Single value
                return [value.strip()]
                
        # If other type, convert to string and return as single item
        return [str(value)]


class JobArchitectureLoader:
    """
    Loader for job architecture data from CSV or Excel files.
    
    Attributes:
        base_dir: Base directory for data files
        skill_taxonomy: Skill taxonomy for validation
        field_mapper: Field mapping utility for handling different data schemas
    """
    
    def __init__(self, skill_taxonomy: SkillTaxonomy, base_dir: Optional[str] = None):
        """
        Initialize the job architecture loader.
        
        Args:
            skill_taxonomy: Skill taxonomy for validation
            base_dir: Base directory for data files (default: from config)
        """
        self.skill_taxonomy = skill_taxonomy
        self.base_dir = base_dir or get_config().data_dir
        self.field_mapper = get_field_mapper()
    
    def load_from_csv(self,
                     job_skills_file: str,
                     jobs_file: Optional[str] = None,
                     chunked: bool = False,
                     chunksize: int = 10000,
                     validate: bool = True) -> JobArchitecture:
        """
        Load job architecture from CSV files, with optional chunked/streaming loading and validation.
        
        Args:
            job_skills_file: Path to the job skills CSV file (required)
            jobs_file: Path to the jobs CSV file (optional - if None, auto-generate from job_skills_file)
            chunked: Whether to use chunked/streaming loading (default: False)
            chunksize: Number of rows per chunk if chunked (default: 10000)
            validate: Whether to validate rows using the validation engine (default: True)
            
        Returns:
            Loaded job architecture
        """
        from skill_similarity_engine.data_validation.validators import ValidationEngine
        from skill_similarity_engine.utils.progress import ProgressTracker
        logger = logging.getLogger("skill_similarity_engine.data.loaders")
        
        # Create empty job architecture
        architecture = JobArchitecture()
        
        # Prepare validation engines if needed
        jobs_validator = None
        skills_validator = None
        if validate:
            if jobs_file:  # Only prepare jobs validator if we have a jobs file
                try:
                    jobs_validator = ValidationEngine('jobs')
                except Exception as e:
                    logger.warning(f"Could not initialise jobs validation engine: {e}")
                    jobs_validator = None
            try:
                skills_validator = ValidationEngine('job_skill_mapping')
            except Exception as e:
                logger.warning(f"Could not initialise job_skill_mapping validation engine: {e}")
                skills_validator = None
        
        # Load jobs from file if provided, otherwise auto-generate from job-skill mapping
        if jobs_file:
            jobs_path = os.path.join(self.base_dir, jobs_file)
            total_rows = None
            if chunked:
                try:
                    with open(jobs_path, 'r', encoding='utf-8') as f:
                        total_rows = sum(1 for _ in f) - 1
                except Exception:
                    total_rows = 0
                reader = pd.read_csv(jobs_path, chunksize=chunksize)
                processed = 0
                with ProgressTracker(total=total_rows if total_rows is not None else 0, desc="Loading jobs (chunked)", show_tqdm=True) as progress:
                    for chunk in reader:
                        for idx, row in chunk.iterrows():
                            row_dict = row.to_dict()
                            # Validate row if enabled
                            if jobs_validator:
                                results = jobs_validator.validate_row(row_dict)
                                if any(not r.passed for r in results):
                                    logger.warning(f"Validation failed for job row {int(processed)+1}: {[r.message for r in results if not r.passed]}")
                                    continue
                            # Parse and add job
                            job = self._parse_job_row(row)
                            if job:
                                architecture.add_job(job)
                            processed += 1
                            progress.update(1)
            else:
                jobs_df = pd.read_csv(jobs_path)
                total_rows = len(jobs_df)
                with ProgressTracker(total=total_rows, desc="Loading jobs", show_tqdm=True) as progress:
                    for idx, row in jobs_df.iterrows():
                        row_dict = row.to_dict()
                        if jobs_validator:
                            results = jobs_validator.validate_row(row_dict)
                            if any(not r.passed for r in results):
                                logger.warning(f"Validation failed for job row {idx+1}: {[r.message for r in results if not r.passed]}")
                                continue
                        job = self._parse_job_row(row)
                        if job:
                            architecture.add_job(job)
                        progress.update(1)
        else:
            # Auto-generate jobs from job-skill mapping
            logger.info("No jobs file provided, auto-generating jobs from job-skill mapping")
            self._auto_generate_jobs_from_mapping(architecture, job_skills_file, chunked, chunksize)
                    
        # Load job skills
        self._load_job_skills(architecture, job_skills_file, chunked, chunksize, skills_validator)
        
        logger.info(f"Loaded {len(architecture.jobs)} jobs into architecture.")
        return architecture
    
    def _parse_job_row(self, row: pd.Series) -> Optional[Job]:
        """
        Parse a job row into a Job object using field mapping.
        
        Args:
            row: Pandas Series representing a job row
            
        Returns:
            Job object or None if parsing fails
        """
        try:
            # Get field names using field mapping
            job_id_field = get_raw_field_name('job_id', 'jobs')
            title_field = get_raw_field_name('title', 'jobs')
            
            # For department, we might need to derive it from other fields
            # Check if we have a direct department field or need to use location info
            department_field = get_raw_field_name('department', 'jobs')
            
            # Extract core values - handle both comprehensive and simple schemas
            job_id = None
            # Try comprehensive schema first (JobProfileID)
            if 'JobProfileID' in row and pd.notna(row['JobProfileID']):
                job_id = str(row['JobProfileID'])
            elif job_id_field in row and pd.notna(row[job_id_field]):
                job_id = str(row[job_id_field])
            elif 'job_id' in row and pd.notna(row['job_id']):
                job_id = str(row['job_id'])  # Legacy fallback
                
            title = None
            # Try comprehensive schema first (JobProfile or Job)
            if 'JobProfile' in row and pd.notna(row['JobProfile']):
                title = row['JobProfile']
            elif 'Job' in row and pd.notna(row['Job']):
                title = row['Job']
            elif title_field in row and pd.notna(row[title_field]):
                title = row[title_field]
            elif 'RoleSet' in row and pd.notna(row['RoleSet']):
                title = row['RoleSet']  # Fallback to HRIS schema
            elif 'title' in row and pd.notna(row['title']):
                title = row['title']  # Legacy fallback
                
            # For department, try comprehensive schema (JobFunction, JobFunctionID, or legacy JobFamily/JobFamilyGroup)
            department = "Unknown"  # Default value
            if 'JobFunction' in row and pd.notna(row['JobFunction']):
                department = row['JobFunction']
            elif 'JobFunctionID' in row and pd.notna(row['JobFunctionID']):
                department = row['JobFunctionID']
            elif 'JobFamily' in row and pd.notna(row['JobFamily']):
                department = row['JobFamily']  # Legacy compatibility
            elif 'JobFamilyGroup' in row and pd.notna(row['JobFamilyGroup']):
                department = row['JobFamilyGroup']  # Legacy compatibility
            elif department_field in row and pd.notna(row[department_field]):
                department = row[department_field]
            elif 'Org Unit Name' in row and pd.notna(row['Org Unit Name']):
                department = row['Org Unit Name']  # HRIS fallback
            elif 'department' in row and pd.notna(row['department']):
                department = row['department']  # Legacy fallback
            elif 'Location' in row and pd.notna(row['Location']):
                department = row['Location']  # Use location as department fallback
                
            if not job_id or not title:
                logger = logging.getLogger("skill_similarity_engine.data.loaders")
                logger.warning(f"Missing required fields (job_id or title) in job row, skipping")
                return None
            
            # Handle other optional fields
            job_level = JobLevel.ASSOCIATE  # Default level
            level_field = get_raw_field_name('level', 'jobs')
            if level_field in row and pd.notna(row[level_field]):
                try:
                    job_level = JobLevel(str(row[level_field]))
                except ValueError:
                    pass  # Keep default
            
            # Handle seniority
            seniority = 3  # Default seniority
            seniority_field = get_raw_field_name('seniority', 'jobs')
            if seniority_field in row and pd.notna(row[seniority_field]):
                try:
                    seniority = int(row[seniority_field])
                except ValueError:
                    pass  # Keep default
            
            # Handle embedded skills data
            skills = {}
            skills_field = get_raw_field_name('skills', 'jobs')
            if skills_field in row and pd.notna(row[skills_field]):
                skills_str = str(row[skills_field])
                skills = self._parse_embedded_skills(skills_str)
            
            return Job(
                job_id=job_id,
                title=title,
                department=department,
                level=job_level,
                skills=skills,
                seniority=seniority
            )
        except Exception as e:
            logger = logging.getLogger("skill_similarity_engine.data.loaders")
            logger.warning(f"Failed to parse job row: {e}")
            return None
    
    def _load_job_skills(self, 
                        architecture: JobArchitecture, 
                        job_skills_file: str,
                        chunked: bool = False,
                        chunksize: int = 10000,
                        skills_validator = None) -> None:
        """
        Load job-skill mappings from a separate file using field mapping.
        
        Args:
            architecture: Job architecture to update
            job_skills_file: Path to job skills file
            chunked: Whether to use chunked loading
            chunksize: Chunk size for loading
            skills_validator: Validation engine for skills
        """
        from skill_similarity_engine.utils.progress import ProgressTracker
        logger = logging.getLogger("skill_similarity_engine.data.loaders")
        
        job_skills_path = os.path.join(self.base_dir, job_skills_file)
        total_skills_rows = None
        
        if chunked:
            try:
                with open(job_skills_path, 'r', encoding='utf-8') as f:
                    total_skills_rows = sum(1 for _ in f) - 1
            except Exception:
                total_skills_rows = 0
            reader = pd.read_csv(job_skills_path, chunksize=chunksize)
            processed = 0
            with ProgressTracker(total=total_skills_rows if total_skills_rows is not None else 0, desc="Loading job skills (chunked)", show_tqdm=True) as progress:
                for chunk in reader:
                    for idx, row in chunk.iterrows():
                        row_dict = row.to_dict()
                        if skills_validator:
                            results = skills_validator.validate_row(row_dict)
                            if any(not r.passed for r in results):
                                logger.warning(f"Validation failed for job skill row {int(processed)+1}: {[r.message for r in results if not r.passed]}")
                                continue
                        self._parse_job_skill_row(architecture, row)
                        processed += 1
                        progress.update(1)
        else:
            job_skills_df = pd.read_csv(job_skills_path)
            total_skills_rows = len(job_skills_df)
            with ProgressTracker(total=total_skills_rows, desc="Loading job skills", show_tqdm=True) as progress:
                for idx, row in job_skills_df.iterrows():
                    row_dict = row.to_dict()
                    if skills_validator:
                        results = skills_validator.validate_row(row_dict)
                        if any(not r.passed for r in results):
                            logger.warning(f"Validation failed for job skill row {idx+1}: {[r.message for r in results if not r.passed]}")
                            continue
                    self._parse_job_skill_row(architecture, row)
                    progress.update(1)
    
    def _parse_job_skill_row(self, architecture: JobArchitecture, row: pd.Series) -> None:
        """
        Parse a job-skill mapping row using field mapping.
        
        Args:
            architecture: Job architecture to update
            row: Pandas Series representing a job-skill row
        """
        try:
            # Get field names using field mapping
            job_id_field = get_raw_field_name('job_id', 'job_skill_mapping')
            skill_id_field = get_raw_field_name('skill_id', 'job_skill_mapping')
            proficiency_field = get_raw_field_name('proficiency', 'job_skill_mapping')
            
            # Extract values
            job_id = str(row[job_id_field]) if job_id_field in row else None
            skill_id = str(row[skill_id_field]) if skill_id_field in row else None
            
            # Handle proficiency - may have different field names
            proficiency = 1  # Default proficiency
            if proficiency_field in row and pd.notna(row[proficiency_field]):
                try:
                    proficiency = int(row[proficiency_field])
                except ValueError:
                    pass  # Keep default
            elif 'Proficiency' in row and pd.notna(row['Proficiency']):
                try:
                    proficiency = int(row['Proficiency'])  # HRIS schema fallback
                except ValueError:
                    pass
            
            if not job_id or not skill_id:
                return  # Skip invalid rows
                
            # Add skill to job if job exists
            job = architecture.get_job(job_id)
            if job:
                job.add_skill(skill_id, proficiency)
        except Exception as e:
            logger = logging.getLogger("skill_similarity_engine.data.loaders")
            logger.warning(f"Failed to parse job-skill row: {e}")
    
    def _parse_embedded_skills(self, skills_str: str) -> Dict[str, int]:
        """
        Parse embedded skills data from a string.
        
        Args:
            skills_str: String containing skills data (e.g., "skill1:3,skill2:4")
            
        Returns:
            Dictionary mapping skill IDs to proficiency levels
        """
        skills = {}
        try:
            for skill_entry in skills_str.split(','):
                if ':' in skill_entry:
                    skill_id, proficiency = skill_entry.split(':', 1)
                    skills[skill_id.strip()] = int(proficiency.strip())
                else:
                    # Assume proficiency 1 if not specified
                    skills[skill_entry.strip()] = 1
        except Exception as e:
            logger = logging.getLogger("skill_similarity_engine.data.loaders")
            logger.warning(f"Failed to parse embedded skills '{skills_str}': {e}")
        return skills

    def _auto_generate_jobs_from_mapping(self, 
                                       architecture: JobArchitecture, 
                                       job_skills_file: str,
                                       chunked: bool = False,
                                       chunksize: int = 10000) -> None:
        """
        Auto-generate minimal Job objects from job-skill mapping file.
        
        Args:
            architecture: JobArchitecture to populate
            job_skills_file: Path to job-skill mapping CSV file
            chunked: Whether to use chunked loading
            chunksize: Chunk size for processing
        """
        from skill_similarity_engine.utils.progress import ProgressTracker
        logger = logging.getLogger("skill_similarity_engine.data.loaders")
        
        job_skills_path = os.path.join(self.base_dir, job_skills_file)
        
        # First pass: collect unique JobProfileIDs
        unique_job_ids = set()
        
        if chunked:
            try:
                with open(job_skills_path, 'r', encoding='utf-8') as f:
                    total_rows = sum(1 for _ in f) - 1
            except Exception:
                total_rows = 0
            reader = pd.read_csv(job_skills_path, chunksize=chunksize)
            with ProgressTracker(total=total_rows if total_rows is not None else 0, desc="Scanning for unique job IDs", show_tqdm=True) as progress:
                for chunk in reader:
                    for _, row in chunk.iterrows():
                        if 'JobProfileID' in row and pd.notna(row['JobProfileID']):
                            unique_job_ids.add(str(row['JobProfileID']))
                        progress.update(1)
        else:
            job_skills_df = pd.read_csv(job_skills_path)
            total_rows = len(job_skills_df)
            with ProgressTracker(total=total_rows, desc="Scanning for unique job IDs", show_tqdm=True) as progress:
                for _, row in job_skills_df.iterrows():
                    if 'JobProfileID' in row and pd.notna(row['JobProfileID']):
                        unique_job_ids.add(str(row['JobProfileID']))
                    progress.update(1)
        
        # Second pass: create minimal Job objects
        logger.info(f"Auto-generating {len(unique_job_ids)} jobs from job-skill mapping")
        with ProgressTracker(total=len(unique_job_ids), desc="Creating minimal job objects", show_tqdm=True) as progress:
            for job_id in unique_job_ids:
                job = Job(
                    job_id=job_id,
                    title=job_id,  # Use JobProfileID as title
                    department="Auto-generated",  # Default department
                    level=JobLevel.ASSOCIATE,  # Default level
                    skills={},  # Will be populated by _load_job_skills
                    seniority=3  # Default seniority
                )
                architecture.add_job(job)
                progress.update(1)
        
        logger.info(f"Auto-generated {len(architecture.jobs)} jobs from job-skill mapping")

    def load_from_excel(self,
                       excel_file: str,
                       jobs_sheet: str = "Jobs",
                       job_skills_sheet: Optional[str] = "JobSkills") -> JobArchitecture:
        """
        Load job architecture from an Excel file.
        
        Args:
            excel_file: Path to the Excel file
            jobs_sheet: Name of the sheet containing jobs data
            job_skills_sheet: Name of the sheet containing job skills data (optional)
            
        Returns:
            Loaded job architecture
        """
        # Create empty job architecture
        architecture = JobArchitecture()
        
        excel_path = os.path.join(self.base_dir, excel_file)
        
        # Load jobs
        jobs_df = pd.read_excel(excel_path, sheet_name=jobs_sheet)
        
        # Create dictionary to store job skills
        job_skills: Dict[str, Dict[str, int]] = {}
        
        for _, row in jobs_df.iterrows():
            # Parse job level
            job_level = JobLevel.ASSOCIATE
            if "level" in row and pd.notna(row["level"]):
                try:
                    job_level = JobLevel(str(row["level"]))
                except ValueError:
                    # Default to ASSOCIATE if invalid
                    pass
            
            # Parse seniority if available
            seniority = 3  # Default to mid-level seniority
            if "seniority" in row and pd.notna(row["seniority"]):
                try:
                    seniority = int(row["seniority"])
                except ValueError:
                    # Default to 3 if not a valid integer
                    pass
            
            # Parse skills if they're embedded in the row
            skills_dict = {}
            if "skills" in row and pd.notna(row["skills"]):
                skills_str = str(row["skills"])
                # Handle different delimiter formats
                if ";" in skills_str:
                    skill_pairs = skills_str.split(";")
                elif "," in skills_str:
                    skill_pairs = skills_str.split(",")
                else:
                    skill_pairs = [skills_str]
                
                for pair in skill_pairs:
                    if ":" in pair:
                        skill_id, proficiency = pair.split(":")
                        skills_dict[skill_id.strip()] = int(proficiency.strip())
            
            job = Job(
                job_id=str(row["job_id"]),
                title=row["title"],
                department=row["department"],
                level=job_level,
                skills=skills_dict,
                seniority=seniority  # Add seniority parameter
            )
            
            # Add job to architecture
            architecture.add_job(job)
        
        # Load job skills if sheet exists
        if job_skills_sheet:
            try:
                job_skills_df = pd.read_excel(excel_path, sheet_name=job_skills_sheet)
                
                for _, row in job_skills_df.iterrows():
                    job_id = str(row["job_id"])
                    skill_id = str(row["skill_id"])
                    proficiency = int(row["proficiency"])
                    
                    # Validate job_id
                    if job_id not in architecture.jobs:
                        continue
                    
                    # Validate skill_id
                    if skill_id not in self.skill_taxonomy.skills:
                        continue
                    
                    # Validate proficiency
                    if not 0 <= proficiency <= 5:
                        continue
                    
                    # Add skill to job
                    architecture.jobs[job_id].add_skill(skill_id, proficiency)
            except ValueError:
                # Sheet doesn't exist, continue without job skills
                pass
        
        return architecture


class EmployeeLoader:
    """
    Loader for employee data from CSV or Excel files.
    
    Attributes:
        base_dir: Base directory for data files
        skill_taxonomy: Skill taxonomy for validation
        job_architecture: Job architecture for validation
        field_mapper: Field mapping utility for handling different data schemas
    """
    
    def __init__(self,
                skill_taxonomy: SkillTaxonomy,
                job_architecture: JobArchitecture,
                base_dir: Optional[str] = None):
        """
        Initialize the employee loader.
        
        Args:
            skill_taxonomy: Skill taxonomy for validation
            job_architecture: Job architecture for validation
            base_dir: Base directory for data files (default: from config)
        """
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        self.base_dir = base_dir or get_config().data_dir
        self.field_mapper = get_field_mapper()
    
    def load_from_csv(self,
                     employees_file: str,
                     employee_skills_file: Optional[str] = None) -> EmployeeDatabase:
        """
        Load employee database from CSV files.
        
        Args:
            employees_file: Path to the employees CSV file
            employee_skills_file: Path to the employee skills CSV file (optional)
            
        Returns:
            Loaded employee database
        """
        # Create empty employee database
        database = EmployeeDatabase()
        
        employees_path = os.path.join(self.base_dir, employees_file)
        employees_df = pd.read_csv(employees_path)
        
        # Create dictionary to store employee skills
        employee_skills: Dict[str, Dict[str, int]] = {}
        
        for _, row in employees_df.iterrows():
            # Use field mapping for employee data
            employee_id_field = get_raw_field_name('employee_id', 'employees')
            current_job_field = get_raw_field_name('current_job', 'employees')
            name_field = get_raw_field_name('name', 'employees')
            
            # Extract values using mapped field names with fallbacks
            employee_id = None
            if employee_id_field in row and pd.notna(row[employee_id_field]):
                employee_id = str(row[employee_id_field])
            elif 'employee_id' in row and pd.notna(row['employee_id']):
                employee_id = str(row['employee_id'])  # Legacy fallback
                
            current_job = None
            if current_job_field in row and pd.notna(row[current_job_field]):
                current_job = str(row[current_job_field])
            elif 'current_job' in row and pd.notna(row['current_job']):
                current_job = str(row['current_job'])  # Legacy fallback
                
            name = None
            if name_field in row and pd.notna(row[name_field]):
                name = row[name_field]
            elif 'name' in row and pd.notna(row['name']):
                name = row['name']  # Legacy fallback
                
            if not employee_id or not current_job or not name:
                logger = logging.getLogger("skill_similarity_engine.data.loaders")
                logger.warning(f"Missing required employee fields, skipping row")
                continue
            
            # Validate job_id only if job_architecture is provided
            if self.job_architecture is not None:
                if current_job not in self.job_architecture.jobs:
                    continue
            
            # Parse embedded skills using field mapping
            skills_dict = {}
            skills_field = get_raw_field_name('skills', 'employees')
            
            # Check for embedded skills data
            skills_data = None
            if skills_field in row and pd.notna(row[skills_field]):
                skills_data = str(row[skills_field])
            elif 'skills' in row and pd.notna(row['skills']):
                skills_data = str(row['skills'])  # Legacy fallback
                
            if skills_data:
                skills_dict = self._parse_embedded_skills(skills_data)
            
            employee = Employee(
                employee_id=employee_id,
                name=name,
                current_job=current_job,
                skills=skills_dict
            )
            
            # Add employee to database
            database.add_employee(employee)
        
        # Load employee skills if provided as a separate file
        if employee_skills_file:
            employee_skills_path = os.path.join(self.base_dir, employee_skills_file)
            employee_skills_df = pd.read_csv(employee_skills_path)
            
            for _, row in employee_skills_df.iterrows():
                # Use field mapping for employee-skills data
                employee_id_field = get_raw_field_name('employee_id', 'employee_skills')
                skill_id_field = get_raw_field_name('skill_id', 'employee_skills')
                proficiency_field = get_raw_field_name('proficiency', 'employee_skills')
                
                # Extract values with fallbacks
                employee_id = None
                if employee_id_field in row and pd.notna(row[employee_id_field]):
                    employee_id = str(row[employee_id_field])
                elif 'employee_id' in row and pd.notna(row['employee_id']):
                    employee_id = str(row['employee_id'])  # Legacy fallback
                    
                skill_id = None
                if skill_id_field in row and pd.notna(row[skill_id_field]):
                    skill_id = str(row[skill_id_field])
                elif 'skill_id' in row and pd.notna(row['skill_id']):
                    skill_id = str(row['skill_id'])  # Legacy fallback
                    
                proficiency = 1  # Default proficiency
                if proficiency_field in row and pd.notna(row[proficiency_field]):
                    try:
                        proficiency = int(row[proficiency_field])
                    except ValueError:
                        pass  # Keep default
                elif 'proficiency' in row and pd.notna(row['proficiency']):
                    try:
                        proficiency = int(row['proficiency'])  # Legacy fallback
                    except ValueError:
                        pass
                
                if not employee_id or not skill_id:
                    continue  # Skip invalid rows
                
                # Validate employee_id
                if employee_id not in database.employees:
                    continue
                
                # Validate skill_id
                if skill_id not in self.skill_taxonomy.skills:
                    continue
                
                # Validate proficiency
                if not 0 <= proficiency <= 5:
                    continue
                
                # Add skill to employee
                database.employees[employee_id].add_skill(skill_id, proficiency)
        
        return database
    
    def _parse_embedded_skills(self, skills_str: str) -> Dict[str, int]:
        """
        Parse embedded skills data from a string.
        
        Args:
            skills_str: String containing skills data (e.g., "skill1:3,skill2:4")
            
        Returns:
            Dictionary mapping skill IDs to proficiency levels
        """
        skills = {}
        try:
            # Handle different delimiter formats
            if ";" in skills_str:
                skill_pairs = skills_str.split(";")
            elif "," in skills_str:
                skill_pairs = skills_str.split(",")
            else:
                skill_pairs = [skills_str]
            
            for pair in skill_pairs:
                if ":" in pair:
                    skill_id, proficiency = pair.split(":", 1)
                    skills[skill_id.strip()] = int(proficiency.strip())
                else:
                    # Assume proficiency 1 if not specified
                    skills[pair.strip()] = 1
        except Exception as e:
            logger = logging.getLogger("skill_similarity_engine.data.loaders")
            logger.warning(f"Failed to parse embedded skills '{skills_str}': {e}")
        return skills

    def load_from_excel(self,
                       excel_file: str,
                       employees_sheet: str = "Employees",
                       employee_skills_sheet: Optional[str] = "EmployeeSkills") -> EmployeeDatabase:
        """
        Load employee database from an Excel file.
        
        Args:
            excel_file: Path to the Excel file
            employees_sheet: Name of the sheet containing employees data
            employee_skills_sheet: Name of the sheet containing employee skills data (optional)
            
        Returns:
            Loaded employee database
        """
        # Create empty employee database
        database = EmployeeDatabase()
        
        excel_path = os.path.join(self.base_dir, excel_file)
        
        # Load employees
        employees_df = pd.read_excel(excel_path, sheet_name=employees_sheet)
        
        # Create dictionary to store employee skills
        employee_skills: Dict[str, Dict[str, int]] = {}
        
        for _, row in employees_df.iterrows():
            # Use field mapping for employee data
            employee_id_field = get_raw_field_name('employee_id', 'employees')
            current_job_field = get_raw_field_name('current_job', 'employees')
            name_field = get_raw_field_name('name', 'employees')
            
            # Extract values using mapped field names with fallbacks
            employee_id = None
            if employee_id_field in row and pd.notna(row[employee_id_field]):
                employee_id = str(row[employee_id_field])
            elif 'employee_id' in row and pd.notna(row['employee_id']):
                employee_id = str(row['employee_id'])  # Legacy fallback
                
            current_job = None
            if current_job_field in row and pd.notna(row[current_job_field]):
                current_job = str(row[current_job_field])
            elif 'current_job' in row and pd.notna(row['current_job']):
                current_job = str(row['current_job'])  # Legacy fallback
                
            name = None
            if name_field in row and pd.notna(row[name_field]):
                name = row[name_field]
            elif 'name' in row and pd.notna(row['name']):
                name = row['name']  # Legacy fallback
                
            if not employee_id or not current_job or not name:
                logger = logging.getLogger("skill_similarity_engine.data.loaders")
                logger.warning(f"Missing required employee fields, skipping row")
                continue
            
            # Validate job_id only if job_architecture is provided
            if self.job_architecture is not None:
                if current_job not in self.job_architecture.jobs:
                    continue
            
            # Parse embedded skills using field mapping
            skills_dict = {}
            skills_field = get_raw_field_name('skills', 'employees')
            
            # Check for embedded skills data
            skills_data = None
            if skills_field in row and pd.notna(row[skills_field]):
                skills_data = str(row[skills_field])
            elif 'skills' in row and pd.notna(row['skills']):
                skills_data = str(row['skills'])  # Legacy fallback
                
            if skills_data:
                skills_dict = self._parse_embedded_skills(skills_data)
            
            employee = Employee(
                employee_id=employee_id,
                name=name,
                current_job=current_job,
                skills=skills_dict
            )
            
            # Add employee to database
            database.add_employee(employee)
        
        # Load employee skills if sheet exists
        if employee_skills_sheet:
            try:
                employee_skills_df = pd.read_excel(excel_path, sheet_name=employee_skills_sheet)
                
                for _, row in employee_skills_df.iterrows():
                    # Use field mapping for employee-skills data
                    employee_id_field = get_raw_field_name('employee_id', 'employee_skills')
                    skill_id_field = get_raw_field_name('skill_id', 'employee_skills')
                    proficiency_field = get_raw_field_name('proficiency', 'employee_skills')
                    
                    # Extract values with fallbacks
                    employee_id = None
                    if employee_id_field in row and pd.notna(row[employee_id_field]):
                        employee_id = str(row[employee_id_field])
                    elif 'employee_id' in row and pd.notna(row['employee_id']):
                        employee_id = str(row['employee_id'])  # Legacy fallback
                        
                    skill_id = None
                    if skill_id_field in row and pd.notna(row[skill_id_field]):
                        skill_id = str(row[skill_id_field])
                    elif 'skill_id' in row and pd.notna(row['skill_id']):
                        skill_id = str(row['skill_id'])  # Legacy fallback
                        
                    proficiency = 1  # Default proficiency
                    if proficiency_field in row and pd.notna(row[proficiency_field]):
                        try:
                            proficiency = int(row[proficiency_field])
                        except ValueError:
                            pass  # Keep default
                    elif 'proficiency' in row and pd.notna(row['proficiency']):
                        try:
                            proficiency = int(row['proficiency'])  # Legacy fallback
                        except ValueError:
                            pass
                    
                    if not employee_id or not skill_id:
                        continue  # Skip invalid rows
                    
                    # Validate employee_id
                    if employee_id not in database.employees:
                        continue
                    
                    # Validate skill_id
                    if skill_id not in self.skill_taxonomy.skills:
                        continue
                    
                    # Validate proficiency
                    if not 0 <= proficiency <= 5:
                        continue
                    
                    # Add skill to employee
                    database.employees[employee_id].add_skill(skill_id, proficiency)
            except ValueError:
                # Sheet doesn't exist, continue without employee skills
                pass
        
        return database


def load_all_data(
    taxonomy_source: str,
    job_source: str,
    employee_source: str,
    is_csv: bool = True
) -> Tuple[SkillTaxonomy, JobArchitecture, EmployeeDatabase]:
    """
    Load all data from the specified sources.
    
    Args:
        taxonomy_source: Source file for skill taxonomy data
        job_source: Source file for job architecture data
        employee_source: Source file for employee data
        is_csv: Whether the sources are CSV files (True) or Excel files (False)
        
    Returns:
        Tuple containing the loaded skill taxonomy, job architecture, and employee database
    """
    # Load skill taxonomy
    taxonomy_loader = SkillTaxonomyLoader()
    if is_csv:
        skill_taxonomy = taxonomy_loader.load_from_csv(taxonomy_source)
    else:
        skill_taxonomy = taxonomy_loader.load_from_excel(taxonomy_source)
    
    # Load job architecture
    job_loader = JobArchitectureLoader(skill_taxonomy)
    if is_csv:
        job_architecture = job_loader.load_from_csv(job_source)
    else:
        job_architecture = job_loader.load_from_excel(job_source)
    
    # Load employee database
    employee_loader = EmployeeLoader(skill_taxonomy, job_architecture)
    if is_csv:
        employee_database = employee_loader.load_from_csv(employee_source)
    else:
        employee_database = employee_loader.load_from_excel(employee_source)
    
    return skill_taxonomy, job_architecture, employee_database