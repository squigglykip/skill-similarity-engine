"""
Data loaders for importing skill taxonomy, job architecture, and employee data.

This module provides functionality for loading data from CSV and Excel files.
"""

import os
from typing import Dict, List, Optional, Set, Tuple, Union

import pandas as pd

from ..config.settings import get_config, get_data_path
from ..models.employees import Employee, EmployeeDatabase
from ..models.jobs import Job, JobArchitecture, JobLevel
from ..models.skills import Skill, SkillCategory, SkillTaxonomy, SkillType


class SkillTaxonomyLoader:
    """
    Loader for skill taxonomy data from CSV or Excel files.
    
    Attributes:
        base_dir: Base directory for data files
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the skill taxonomy loader.
        
        Args:
            base_dir: Base directory for data files (default: from config)
        """
        self.base_dir = base_dir or get_config().data_dir
    
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
                category = SkillCategory(
                    category_id=str(row["category_id"]),
                    name=row["name"],
                    parent_id=str(row["parent_id"]) if pd.notna(row.get("parent_id", None)) else None,
                    description=row.get("description", "")
                )
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
    
    def _parse_skill_row(self, row: pd.Series, taxonomy: SkillTaxonomy) -> Optional[Skill]:
        """
        Parse a skill row into a Skill object, handling category mapping.
        """
        # Create category mapping if categories are in skills file
        # (This is a simplified version; for full mapping, refactor as needed)
        skill_type = SkillType.COMMON  # Default to COMMON instead of OTHER
        if "skill_type" in row and pd.notna(row["skill_type"]):
            try:
                skill_type = SkillType.from_string(row["skill_type"])
            except ValueError:
                pass
        elif "category" in row and pd.notna(row["category"]):
            try:
                skill_type = SkillType.from_string(row["category"])
            except ValueError:
                pass
        elif "SkillType" in row and pd.notna(row["SkillType"]):
            try:
                skill_type = SkillType.from_string(row["SkillType"])
            except ValueError:
                pass
        # Parse lists
        aliases = self._parse_list_field(row, "aliases")
        related_skills = self._parse_list_field(row, "related_skills")
        prerequisites = self._parse_list_field(row, "prerequisites")
        # Get category ID from mapping if available
        category_id = None
        if "category_id" in row and pd.notna(row["category_id"]):
            category_id = str(row["category_id"])
        skill = Skill(
            skill_id=str(row["skill_id"]),
            name=row["name"],
            description=row.get("description", ""),
            category_id=category_id,
            skill_type=skill_type,
            aliases=aliases,
            related_skills=related_skills,
            prerequisites=prerequisites
        )
        return skill
    
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
                    category = SkillCategory(
                        category_id=str(row["category_id"]),
                        name=row["name"],
                        parent_id=str(row["parent_id"]) if pd.notna(row.get("parent_id", None)) else None,
                        description=row.get("description", "")
                    )
                    taxonomy.add_category(category)
            except ValueError:
                # Sheet doesn't exist, continue without categories
                pass
        
        # Load skills
        skills_df = pd.read_excel(excel_path, sheet_name=skills_sheet)
        
        for _, row in skills_df.iterrows():
            # Parse skill type - try multiple approaches
            skill_type = SkillType.COMMON  # Default to COMMON instead of OTHER
            
            # First check the dedicated skill_type field if it exists
            if "skill_type" in row and pd.notna(row["skill_type"]):
                try:
                    skill_type = SkillType.from_string(row["skill_type"])
                except ValueError:
                    pass
            # Next check if category contains a SkillType value (test data approach)
            elif "category" in row and pd.notna(row["category"]):
                try:
                    skill_type = SkillType.from_string(row["category"])
                except ValueError:
                    pass
            # Finally check if we have a SkillType field from HRIS schema
            elif "SkillType" in row and pd.notna(row["SkillType"]):
                try:
                    skill_type = SkillType.from_string(row["SkillType"])
                except ValueError:
                    pass
            
            # Parse lists
            aliases = self._parse_list_field(row, "aliases")
            related_skills = self._parse_list_field(row, "related_skills")
            prerequisites = self._parse_list_field(row, "prerequisites")
            
            skill = Skill(
                skill_id=str(row["skill_id"]),
                name=row["name"],
                description=row.get("description", ""),
                category_id=str(row["category_id"]) if pd.notna(row.get("category_id", None)) else None,
                skill_type=skill_type,  # Use the parsed skill_type instead of row.get("category", SkillType.COMMON)
                aliases=aliases,
                related_skills=related_skills,
                prerequisites=prerequisites
            )
            taxonomy.add_skill(skill)
        
        return taxonomy
    
    def _parse_list_field(self, row: pd.Series, field_name: str) -> List[str]:
        """
        Parse a list field from a CSV/Excel row.
        
        Args:
            row: DataFrame row
            field_name: Name of the field to parse
            
        Returns:
            List of values (empty if field doesn't exist or is empty)
        """
        if field_name not in row or pd.isna(row[field_name]):
            return []
        
        # Handle different delimiter formats
        value = row[field_name]
        if isinstance(value, list):
            return [str(item) for item in value]
        
        if ";" in value:
            return [item.strip() for item in value.split(";") if item.strip()]
        elif "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        
        # Single value
        return [value.strip()]


class JobArchitectureLoader:
    """
    Loader for job architecture data from CSV or Excel files.
    
    Attributes:
        base_dir: Base directory for data files
        skill_taxonomy: Skill taxonomy for validation
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
    
    def load_from_csv(self,
                     jobs_file: str,
                     job_skills_file: Optional[str] = None,
                     chunked: bool = False,
                     chunksize: int = 10000,
                     validate: bool = True) -> JobArchitecture:
        """
        Load job architecture from CSV files, with optional chunked/streaming loading and validation.
        
        Args:
            jobs_file: Path to the jobs CSV file
            job_skills_file: Path to the job skills CSV file (optional)
            chunked: Whether to use chunked/streaming loading (default: False)
            chunksize: Number of rows per chunk if chunked (default: 10000)
            validate: Whether to validate rows using the validation engine (default: True)
            
        Returns:
            Loaded job architecture
        """
        from skill_similarity_engine.data_validation.validators import ValidationEngine
        from skill_similarity_engine.utils.progress import ProgressTracker
        import logging
        logger = logging.getLogger("skill_similarity_engine.data.loaders")
        
        # Create empty job architecture
        architecture = JobArchitecture()
        
        # Prepare validation engines if needed
        jobs_validator = None
        skills_validator = None
        if validate:
            try:
                jobs_validator = ValidationEngine('jobs')
            except Exception as e:
                logger.warning(f"Could not initialise jobs validation engine: {e}")
                jobs_validator = None
            if job_skills_file:
                try:
                    skills_validator = ValidationEngine('job_skill_mapping')
                except Exception as e:
                    logger.warning(f"Could not initialise job_skill_mapping validation engine: {e}")
                    skills_validator = None
        
        # Load jobs (chunked or not)
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
                        # Use JobProfileID as canonical key
                        job_id = str(row.get("JobProfileID") or row.get("job_id"))
                        if not job_id:
                            logger.warning(f"Missing JobProfileID/job_id in row {int(processed)+1}, skipping.")
                            continue
                        # Parse job level (optional)
                        job_level = JobLevel.ASSOCIATE
                        if "Salary Group" in row and pd.notna(row["Salary Group"]):
                            try:
                                job_level = JobLevel.ASSOCIATE  # Map as needed
                            except Exception:
                                pass
                        # Parse department, title, etc.
                        title = row.get("RoleSet") or row.get("title")
                        department = row.get("Org Unit Name") or row.get("department")
                        # Parse other context fields for reporting only
                        org_unit_number = row.get("Org Unit Number")
                        # Build job object
                        job = Job(
                            job_id=job_id,
                            title=title,
                            department=department,
                            level=job_level,
                            skills={},
                        )
                        # Attach reporting context if needed
                        if hasattr(job, 'org_unit_number'):
                            job.org_unit_number = org_unit_number
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
                    job_id = str(row.get("JobProfileID") or row.get("job_id"))
                    if not job_id:
                        logger.warning(f"Missing JobProfileID/job_id in row {idx+1}, skipping.")
                        continue
                    job_level = JobLevel.ASSOCIATE
                    if "Salary Group" in row and pd.notna(row["Salary Group"]):
                        try:
                            job_level = JobLevel.ASSOCIATE  # Map as needed
                        except Exception:
                            pass
                    title = row.get("RoleSet") or row.get("title")
                    department = row.get("Org Unit Name") or row.get("department")
                    org_unit_number = row.get("Org Unit Number")
                    job = Job(
                        job_id=job_id,
                        title=title,
                        department=department,
                        level=job_level,
                        skills={},
                    )
                    if hasattr(job, 'org_unit_number'):
                        job.org_unit_number = org_unit_number
                    architecture.add_job(job)
                    progress.update(1)
        # Load job skills if provided
        if job_skills_file:
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
                with ProgressTracker(total=total_skills_rows if total_skills_rows is not None else 0, desc="Loading job-skill mappings (chunked)", show_tqdm=True) as progress:
                    for chunk in reader:
                        for idx, row in chunk.iterrows():
                            row_dict = row.to_dict()
                            if skills_validator:
                                results = skills_validator.validate_row(row_dict)
                                if any(not r.passed for r in results):
                                    logger.warning(f"Validation failed for job-skill row {int(processed)+1}: {[r.message for r in results if not r.passed]}")
                                    continue
                            job_id = str(row.get("JobProfileID") or row.get("JobID") or row.get("job_id"))
                            skill_id = str(row.get("Skill_ID") or row.get("skill_id"))
                            if not job_id or not skill_id:
                                logger.warning(f"Missing JobProfileID/JobID or Skill_ID/skill_id in row {int(processed)+1}, skipping.")
                                continue
                            proficiency = 3
                            if "Proficiency" in row and pd.notna(row["Proficiency"]):
                                try:
                                    proficiency = int(row["Proficiency"])
                                except Exception:
                                    pass
                            if job_id in architecture.jobs and skill_id in self.skill_taxonomy.skills:
                                architecture.jobs[job_id].add_skill(skill_id, proficiency)
                            processed += 1
                            progress.update(1)
            else:
                job_skills_df = pd.read_csv(job_skills_path)
                total_skills_rows = len(job_skills_df)
                with ProgressTracker(total=total_skills_rows, desc="Loading job-skill mappings", show_tqdm=True) as progress:
                    for idx, row in job_skills_df.iterrows():
                        row_dict = row.to_dict()
                        if skills_validator:
                            results = skills_validator.validate_row(row_dict)
                            if any(not r.passed for r in results):
                                logger.warning(f"Validation failed for job-skill row {idx+1}: {[r.message for r in results if not r.passed]}")
                                continue
                        job_id = str(row.get("JobProfileID") or row.get("JobID") or row.get("job_id"))
                        skill_id = str(row.get("Skill_ID") or row.get("skill_id"))
                        if not job_id or not skill_id:
                            logger.warning(f"Missing JobProfileID/JobID or Skill_ID/skill_id in row {idx+1}, skipping.")
                            continue
                        proficiency = 3
                        if "Proficiency" in row and pd.notna(row["Proficiency"]):
                            try:
                                proficiency = int(row["Proficiency"])
                            except Exception:
                                pass
                        if job_id in architecture.jobs and skill_id in self.skill_taxonomy.skills:
                            architecture.jobs[job_id].add_skill(skill_id, proficiency)
                        progress.update(1)
        return architecture
    
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
                    job_level = JobLevel.from_string(str(row["level"]))
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
            employee_id = str(row["employee_id"])
            job_id = str(row["current_job"])
            
            # Validate job_id only if job_architecture is provided
            if self.job_architecture is not None:
                if job_id not in self.job_architecture.jobs:
                    continue
            
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
            
            employee = Employee(
                employee_id=employee_id,
                name=row["name"],
                current_job=job_id,
                skills=skills_dict
            )
            
            # Add employee to database
            database.add_employee(employee)
        
        # Load employee skills if provided as a separate file
        if employee_skills_file:
            employee_skills_path = os.path.join(self.base_dir, employee_skills_file)
            employee_skills_df = pd.read_csv(employee_skills_path)
            
            for _, row in employee_skills_df.iterrows():
                employee_id = str(row["employee_id"])
                skill_id = str(row["skill_id"])
                proficiency = int(row["proficiency"])
                
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
            employee_id = str(row["employee_id"])
            job_id = str(row["current_job"])
            
            # Validate job_id only if job_architecture is provided
            if self.job_architecture is not None:
                if job_id not in self.job_architecture.jobs:
                    continue
            
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
            
            employee = Employee(
                employee_id=employee_id,
                name=row["name"],
                current_job=job_id,
                skills=skills_dict
            )
            
            # Add employee to database
            database.add_employee(employee)
        
        # Load employee skills if sheet exists
        if employee_skills_sheet:
            try:
                employee_skills_df = pd.read_excel(excel_path, sheet_name=employee_skills_sheet)
                
                for _, row in employee_skills_df.iterrows():
                    employee_id = str(row["employee_id"])
                    skill_id = str(row["skill_id"])
                    proficiency = int(row["proficiency"])
                    
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