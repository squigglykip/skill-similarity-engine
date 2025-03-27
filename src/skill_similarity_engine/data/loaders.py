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
                    categories_file: Optional[str] = None) -> SkillTaxonomy:
        """
        Load skill taxonomy from CSV files.
        
        Args:
            skills_file: Path to the skills CSV file
            categories_file: Path to the categories CSV file (optional)
            
        Returns:
            Loaded skill taxonomy
        """
        # Create empty taxonomy
        taxonomy = SkillTaxonomy()
        
        # Load categories if provided
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
        
        # Load skills
        skills_path = os.path.join(self.base_dir, skills_file)
        skills_df = pd.read_csv(skills_path)
        
        # Create category mapping if categories are in skills file
        category_mapping = {}
        if "category" in skills_df.columns and "subcategory" in skills_df.columns:
            # Create main categories
            for category in skills_df["category"].unique():
                if pd.notna(category):
                    category_id = f"C{len(category_mapping) + 1:03d}"
                    category_mapping[category] = category_id
                    if not taxonomy.get_category(category_id):
                        taxonomy.add_category(SkillCategory(
                            category_id=category_id,
                            name=category,
                            description=f"{category} skills and competencies"
                        ))
            
            # Create subcategories
            for _, row in skills_df.iterrows():
                if pd.notna(row["subcategory"]):
                    parent_id = category_mapping.get(row["category"])
                    if parent_id:
                        subcategory_id = f"C{len(category_mapping) + 1:03d}"
                        category_mapping[row["subcategory"]] = subcategory_id
                        if not taxonomy.get_category(subcategory_id):
                            taxonomy.add_category(SkillCategory(
                                category_id=subcategory_id,
                                name=row["subcategory"],
                                parent_id=parent_id,
                                description=f"{row['subcategory']} skills"
                            ))
        
        for _, row in skills_df.iterrows():
            # Parse skill type
            skill_type = SkillType.OTHER
            if "skill_type" in row and pd.notna(row["skill_type"]):
                try:
                    skill_type = SkillType.from_string(row["skill_type"])
                except ValueError:
                    # Default to OTHER if invalid
                    pass
            
            # Parse lists
            aliases = self._parse_list_field(row, "aliases")
            related_skills = self._parse_list_field(row, "related_skills")
            prerequisites = self._parse_list_field(row, "prerequisites")
            
            # Get category ID from mapping if available
            category_id = None
            if "category" in row and "subcategory" in row:
                category_id = category_mapping.get(row["subcategory"]) or category_mapping.get(row["category"])
            
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
            taxonomy.add_skill(skill)
        
        return taxonomy
    
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
            # Parse skill type
            skill_type = SkillType.OTHER
            if "skill_type" in row and pd.notna(row["skill_type"]):
                try:
                    skill_type = SkillType.from_string(row["skill_type"])
                except ValueError:
                    # Default to OTHER if invalid
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
                skill_type=skill_type,
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
                     job_skills_file: Optional[str] = None) -> JobArchitecture:
        """
        Load job architecture from CSV files.
        
        Args:
            jobs_file: Path to the jobs CSV file
            job_skills_file: Path to the job skills CSV file (optional)
            
        Returns:
            Loaded job architecture
        """
        # Create empty job architecture
        architecture = JobArchitecture()
        
        # Load jobs
        jobs_path = os.path.join(self.base_dir, jobs_file)
        jobs_df = pd.read_csv(jobs_path)
        
        # Create dictionary to store job skills
        job_skills: Dict[str, Dict[str, int]] = {}
        
        for _, row in jobs_df.iterrows():
            job_id = str(row["job_id"])
            
            # Parse job level
            job_level = JobLevel.ASSOCIATE
            if "level" in row and pd.notna(row["level"]):
                try:
                    job_level = JobLevel(row["level"])
                except ValueError:
                    # Default to ASSOCIATE if invalid
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
                job_id=job_id,
                title=row["title"],
                department=row["department"],
                level=job_level,
                skills=skills_dict
            )
            
            # Add job to architecture
            architecture.add_job(job)
        
        # Load job skills if provided as a separate file
        if job_skills_file:
            job_skills_path = os.path.join(self.base_dir, job_skills_file)
            job_skills_df = pd.read_csv(job_skills_path)
            
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
            job_id = str(row["job_id"])
            
            # Parse job level
            job_level = JobLevel.ASSOCIATE
            if "level" in row and pd.notna(row["level"]):
                try:
                    job_level = JobLevel(row["level"])
                except ValueError:
                    # Default to ASSOCIATE if invalid
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
                job_id=job_id,
                title=row["title"],
                department=row["department"],
                level=job_level,
                skills=skills_dict
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
        
        # Load employees
        employees_path = os.path.join(self.base_dir, employees_file)
        employees_df = pd.read_csv(employees_path)
        
        # Create dictionary to store employee skills
        employee_skills: Dict[str, Dict[str, int]] = {}
        
        for _, row in employees_df.iterrows():
            employee_id = str(row["employee_id"])
            job_id = str(row["current_job"])
            
            # Validate job_id
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
            
            # Validate job_id
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
