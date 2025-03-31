"""
Unit tests for the models module.

This module tests the core data models for skills, jobs, and related classes.
"""

import sys
import os

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import unittest
from unittest.mock import patch, MagicMock

from skill_similarity_engine.models.skills import (
    Skill, SkillCategory, SkillTaxonomy, SkillType
)
from skill_similarity_engine.models.jobs import (
    Job, JobArchitecture, JobLevel
)
from skill_similarity_engine.models.employees import (
    Employee, EmployeeDatabase
)


class TestSkillModels(unittest.TestCase):
    """Test cases for skill-related models."""

    def test_skill_type_from_string(self):
        """Test converting string to SkillType enum."""
        self.assertEqual(SkillType.from_string("technical"), SkillType.SPECIALIZED)
        self.assertEqual(SkillType.from_string("SOFT"), SkillType.COMMON)
        self.assertEqual(SkillType.from_string(" domain "), SkillType.SPECIALIZED)
        
        # Test invalid skill type
        with self.assertRaises(ValueError):
            SkillType.from_string("nonexistent_type")

    def test_skill_category_creation(self):
        """Test creating a SkillCategory."""
        category = SkillCategory(category_id="C001", name="Programming")
        self.assertEqual(category.category_id, "C001")
        self.assertEqual(category.name, "Programming")
        self.assertIsNone(category.parent_id)
        self.assertEqual(category.description, "")
        
        # Test validation
        with self.assertRaises(ValueError):
            SkillCategory(category_id="", name="Invalid")
            
        with self.assertRaises(ValueError):
            SkillCategory(category_id="C002", name="")

    def test_skill_creation(self):
        """Test creating a Skill."""
        skill = Skill(
            skill_id="S001",
            name="Python",
            description="Programming language",
            category_id="C001",
            skill_type=SkillType.SPECIALIZED
        )
        
        self.assertEqual(skill.skill_id, "S001")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.description, "Programming language")
        self.assertEqual(skill.category_id, "C001")
        self.assertEqual(skill.skill_type, SkillType.SPECIALIZED)
        self.assertEqual(len(skill.aliases), 0)
        self.assertEqual(len(skill.related_skills), 0)
        self.assertEqual(len(skill.prerequisites), 0)
        
        # Test validation
        with self.assertRaises(ValueError):
            Skill(skill_id="", name="Invalid")
            
        with self.assertRaises(ValueError):
            Skill(skill_id="S002", name="")
            
        # Test string skill type conversion
        skill = Skill(skill_id="S003", name="TypeScript", skill_type="technical")
        self.assertEqual(skill.skill_type, SkillType.SPECIALIZED)
        
        # Test invalid skill type
        with self.assertRaises(ValueError):
            Skill(skill_id="S004", name="Invalid Type", skill_type="not_a_real_type")

    def test_skill_methods(self):
        """Test Skill class methods."""
        skill = Skill(skill_id="S001", name="Python")
        
        # Test adding aliases
        skill.add_alias("py")
        skill.add_alias("python3")
        self.assertEqual(len(skill.aliases), 2)
        self.assertIn("py", skill.aliases)
        self.assertIn("python3", skill.aliases)
        
        # Test duplicate alias
        skill.add_alias("py")
        self.assertEqual(len(skill.aliases), 2)  # Should not add duplicate
        
        # Test empty alias
        skill.add_alias("")
        self.assertEqual(len(skill.aliases), 2)  # Should not add empty alias
        
        # Test related skills
        skill.add_related_skill("S002")
        skill.add_related_skill("S003")
        self.assertEqual(len(skill.related_skills), 2)
        self.assertIn("S002", skill.related_skills)
        
        # Test duplicate related skill
        skill.add_related_skill("S002")
        self.assertEqual(len(skill.related_skills), 2)  # Should not add duplicate
        
        # Test prerequisites
        skill.add_prerequisite("S004")
        self.assertEqual(len(skill.prerequisites), 1)
        self.assertIn("S004", skill.prerequisites)
        
        # Test matches method
        self.assertTrue(skill.matches("python"))
        self.assertTrue(skill.matches("py"))  # Should match alias
        self.assertFalse(skill.matches("java"))

    def test_skill_taxonomy(self):
        """Test SkillTaxonomy class."""
        taxonomy = SkillTaxonomy()
        
        # Add categories
        category1 = SkillCategory(category_id="C001", name="Programming")
        category2 = SkillCategory(
            category_id="C002", 
            name="Web Development",
            parent_id="C001"
        )
        
        taxonomy.add_category(category1)
        taxonomy.add_category(category2)
        
        self.assertEqual(len(taxonomy.categories), 2)
        self.assertIn("C001", taxonomy.categories)
        self.assertIn("C002", taxonomy.categories)
        self.assertIn("C002", taxonomy.category_hierarchy["C001"])
        
        # Try adding duplicate category
        with self.assertRaises(ValueError):
            taxonomy.add_category(SkillCategory(category_id="C001", name="Duplicate"))
            
        # Add skills
        skill1 = Skill(
            skill_id="S001",
            name="Python",
            category_id="C001",
            skill_type=SkillType.SPECIALIZED
        )
        
        skill2 = Skill(
            skill_id="S002",
            name="JavaScript",
            category_id="C002",
            skill_type=SkillType.SPECIALIZED
        )
        
        taxonomy.add_skill(skill1)
        taxonomy.add_skill(skill2)
        
        self.assertEqual(len(taxonomy.skills), 2)
        self.assertIn("S001", taxonomy.skills)
        self.assertIn("S002", taxonomy.skills)
        
        # Test skills_by_category
        self.assertIn("S001", taxonomy.skills_by_category["C001"])
        self.assertIn("S002", taxonomy.skills_by_category["C002"])
        
        # Try adding duplicate skill
        with self.assertRaises(ValueError):
            taxonomy.add_skill(Skill(skill_id="S001", name="Duplicate"))
            
        # Test retrieval methods
        self.assertEqual(taxonomy.get_skill("S001"), skill1)
        self.assertEqual(taxonomy.get_category("C001"), category1)
        self.assertIsNone(taxonomy.get_skill("nonexistent"))
        
        # Test get_skills_in_category
        skills_in_c001 = taxonomy.get_skills_in_category("C001", include_subcategories=False)
        self.assertEqual(len(skills_in_c001), 1)
        self.assertIn(skill1, skills_in_c001)
        
        # Test with include_subcategories=True
        skills_in_c001_with_subs = taxonomy.get_skills_in_category("C001", include_subcategories=True)
        self.assertEqual(len(skills_in_c001_with_subs), 2)
        
        # Test get_subcategories
        subcategories = taxonomy.get_subcategories("C001")
        self.assertEqual(len(subcategories), 1)
        self.assertEqual(subcategories[0], category2)
        
        # Test search_skills
        search_results = taxonomy.search_skills("java")
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0], skill2)

    def test_taxonomy_serialization(self):
        """Test SkillTaxonomy serialization to dict and back."""
        # Create a taxonomy
        taxonomy = SkillTaxonomy()
        taxonomy.add_category(SkillCategory(category_id="C001", name="Programming"))
        taxonomy.add_skill(Skill(skill_id="S001", name="Python", category_id="C001"))
        
        # Convert to dict
        taxonomy_dict = taxonomy.to_dict()
        
        # Check dict structure
        self.assertIn("categories", taxonomy_dict)
        self.assertIn("skills", taxonomy_dict)
        self.assertEqual(len(taxonomy_dict["categories"]), 1)
        self.assertEqual(len(taxonomy_dict["skills"]), 1)
        
        # Convert back from dict
        new_taxonomy = SkillTaxonomy.from_dict(taxonomy_dict)
        
        # Check new taxonomy
        self.assertEqual(len(new_taxonomy.categories), 1)
        self.assertEqual(len(new_taxonomy.skills), 1)
        self.assertIn("C001", new_taxonomy.categories)
        self.assertIn("S001", new_taxonomy.skills)
        self.assertEqual(new_taxonomy.skills["S001"].name, "Python")

    def test_taxonomy_from_file(self):
        """Test loading taxonomy from file."""
        # Get the path to sample data
        sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
        
        # Test CSV loading
        csv_path = os.path.join(sample_dir, 'skills.csv')
        taxonomy = SkillTaxonomy.from_file(csv_path)
        self.assertGreater(len(taxonomy.skills), 0)
        self.assertGreater(len(taxonomy.categories), 0)
        
        # Test JSON loading
        json_path = os.path.join(sample_dir, 'skills.json')
        taxonomy = SkillTaxonomy.from_file(json_path)
        self.assertGreater(len(taxonomy.skills), 0)
        self.assertGreater(len(taxonomy.categories), 0)
        
        # Test unsupported file type
        with self.assertRaises(ValueError):
            SkillTaxonomy.from_file("skills.txt")


class TestJobModels(unittest.TestCase):
    """Test cases for job-related models."""

    def test_job_creation(self):
        """Test creating a Job."""
        # Test basic creation
        job = Job(
            job_id="J001",
            title="Software Engineer",
            department="Engineering",
            level=JobLevel.MID_LEVEL
        )
        
        self.assertEqual(job.job_id, "J001")
        self.assertEqual(job.title, "Software Engineer")
        self.assertEqual(job.department, "Engineering")
        self.assertEqual(job.level, JobLevel.MID_LEVEL)
        self.assertEqual(len(job.skills), 0)
        
        # Test with skills
        job_with_skills = Job(
            job_id="J002",
            title="Data Scientist",
            department="Data",
            level=JobLevel.SENIOR,
            skills={"S001": 4, "S002": 3}
        )
        
        self.assertEqual(len(job_with_skills.skills), 2)
        self.assertEqual(job_with_skills.skills["S001"], 4)
        
        # Test string level conversion
        job_with_string_level = Job(
            job_id="J003",
            title="Manager",
            department="HR",
            level="Manager"
        )
        
        self.assertEqual(job_with_string_level.level, JobLevel.MANAGER)
        
        # Test invalid level
        with self.assertRaises(ValueError):
            Job(
                job_id="J004",
                title="Invalid Level",
                department="Test",
                level="NonExistentLevel"
            )
            
        # Test validation
        with self.assertRaises(ValueError):
            Job(job_id="", title="Invalid", department="Test", level=JobLevel.ENTRY)
            
        with self.assertRaises(ValueError):
            Job(job_id="J005", title="", department="Test", level=JobLevel.ENTRY)
            
        with self.assertRaises(ValueError):
            Job(job_id="J006", title="No Department", department="", level=JobLevel.ENTRY)
            
        # Test skill proficiency validation
        with self.assertRaises(ValueError):
            Job(
                job_id="J007",
                title="Invalid Proficiency",
                department="Test",
                level=JobLevel.ENTRY,
                skills={"S001": 10}  # Should be 0-5
            )
        
        # Test string proficiency conversion
        job = Job(
            job_id="J008",
            title="String Proficiency",
            department="Test",
            level=JobLevel.ENTRY,
            skills={"S001": "3"}
        )
        self.assertEqual(job.skills["S001"], 3)

    def test_job_methods(self):
        """Test Job class methods."""
        job = Job(
            job_id="J001",
            title="Software Engineer",
            department="Engineering",
            level=JobLevel.MID_LEVEL
        )
        
        # Test adding skills
        job.add_skill("S001", 3)
        job.add_skill("S002", 4)
        self.assertEqual(len(job.skills), 2)
        self.assertEqual(job.skills["S001"], 3)
        
        # Test invalid proficiency
        with self.assertRaises(ValueError):
            job.add_skill("S003", 6)
        
        # Test removing skills
        job.remove_skill("S001")
        self.assertEqual(len(job.skills), 1)
        self.assertNotIn("S001", job.skills)
        
        # Test removing non-existent skill (should not raise error)
        job.remove_skill("nonexistent")
        
        # Test get_skill_proficiency
        self.assertEqual(job.get_skill_proficiency("S002"), 4)
        self.assertIsNone(job.get_skill_proficiency("nonexistent"))
        
        # Test has_skill
        self.assertTrue(job.has_skill("S002"))
        self.assertFalse(job.has_skill("nonexistent"))
        
        # Test has_skill with min_proficiency
        self.assertTrue(job.has_skill("S002", min_proficiency=3))
        self.assertTrue(job.has_skill("S002", min_proficiency=4))
        self.assertFalse(job.has_skill("S002", min_proficiency=5))

    def test_job_architecture(self):
        """Test JobArchitecture class."""
        architecture = JobArchitecture()
        
        # Create jobs
        job1 = Job(
            job_id="J001",
            title="Software Engineer",
            department="Engineering",
            level=JobLevel.MID_LEVEL,
            skills={"S001": 3, "S002": 4}
        )
        
        job2 = Job(
            job_id="J002",
            title="Data Scientist",
            department="Data",
            level=JobLevel.SENIOR,
            skills={"S001": 2, "S003": 5}
        )
        
        # Add jobs
        architecture.add_job(job1)
        architecture.add_job(job2)
        
        self.assertEqual(len(architecture.jobs), 2)
        self.assertEqual(len(architecture.departments), 2)
        self.assertEqual(len(architecture.levels), 2)
        
        # Test duplicate job ID
        with self.assertRaises(ValueError):
            architecture.add_job(Job(
                job_id="J001",  # Duplicate ID
                title="Duplicate",
                department="Test",
                level=JobLevel.ENTRY
            ))
        
        # Test retrieval methods
        self.assertEqual(architecture.get_job("J001"), job1)
        self.assertIsNone(architecture.get_job("nonexistent"))
        
        # Test get_jobs_by_department
        eng_jobs = architecture.get_jobs_by_department("Engineering")
        self.assertEqual(len(eng_jobs), 1)
        self.assertEqual(eng_jobs[0], job1)
        
        # Test get_jobs_by_level
        senior_jobs = architecture.get_jobs_by_level(JobLevel.SENIOR)
        self.assertEqual(len(senior_jobs), 1)
        self.assertEqual(senior_jobs[0], job2)
        
        # Test get_jobs_by_level with string
        senior_jobs = architecture.get_jobs_by_level("Senior")
        self.assertEqual(len(senior_jobs), 1)
        self.assertEqual(senior_jobs[0], job2)
        
        # Test get_jobs_requiring_skill
        jobs_with_s001 = architecture.get_jobs_requiring_skill("S001")
        self.assertEqual(len(jobs_with_s001), 2)
        
        # Test with min_proficiency
        jobs_with_s001_proficient = architecture.get_jobs_requiring_skill("S001", min_proficiency=3)
        self.assertEqual(len(jobs_with_s001_proficient), 1)
        self.assertEqual(jobs_with_s001_proficient[0], job1)

    def test_job_architecture_serialization(self):
        """Test JobArchitecture serialization to dict and back."""
        # Create an architecture
        architecture = JobArchitecture()
        architecture.add_job(Job(
            job_id="J001",
            title="Software Engineer",
            department="Engineering",
            level=JobLevel.MID_LEVEL,
            skills={"S001": 3}
        ))
        
        # Convert to dict
        arch_dict = architecture.to_dict()
        
        # Check dict structure
        self.assertIn("J001", arch_dict)
        self.assertEqual(arch_dict["J001"]["title"], "Software Engineer")
        self.assertEqual(arch_dict["J001"]["department"], "Engineering")
        self.assertEqual(arch_dict["J001"]["level"], "Mid-level")
        self.assertEqual(arch_dict["J001"]["skills"], {"S001": 3})
        
        # Convert back from dict
        new_architecture = JobArchitecture.from_dict(arch_dict)
        
        # Check new architecture
        self.assertEqual(len(new_architecture.jobs), 1)
        self.assertIn("J001", new_architecture.jobs)
        self.assertEqual(new_architecture.jobs["J001"].title, "Software Engineer")
        self.assertEqual(new_architecture.jobs["J001"].skills, {"S001": 3})
        
        # Test parsing string skill format
        string_skills_dict = {
            "J002": {
                "title": "Data Scientist",
                "department": "Data",
                "level": "Senior",
                "skills": "S001:4,S002:5"
            }
        }
        
        string_arch = JobArchitecture.from_dict(string_skills_dict)
        self.assertEqual(string_arch.jobs["J002"].skills, {"S001": 4, "S002": 5})

    @patch("skill_similarity_engine.data.loaders.JobArchitectureLoader")
    def test_architecture_from_file(self, mock_loader):
        """Test loading architecture from file."""
        # Mock the loader
        mock_loader_instance = MagicMock()
        mock_loader.return_value = mock_loader_instance
        mock_architecture = MagicMock()
        
        # Set up return values for different file types
        mock_loader_instance.load_from_csv.return_value = mock_architecture
        mock_loader_instance.load_from_excel.return_value = mock_architecture
        
        # Test CSV loading
        result = JobArchitecture.from_file("jobs.csv")
        mock_loader_instance.load_from_csv.assert_called_once_with("jobs.csv")
        self.assertEqual(result, mock_architecture)
        
        # Test Excel loading
        result = JobArchitecture.from_file("jobs.xlsx")
        mock_loader_instance.load_from_excel.assert_called_once_with("jobs.xlsx")
        self.assertEqual(result, mock_architecture)
        
        # Test unsupported file type
        with self.assertRaises(ValueError):
            JobArchitecture.from_file("jobs.txt")


class TestEmployeeModels(unittest.TestCase):
    """Test cases for employee-related models."""

    def test_employee_creation(self):
        """Test creating an Employee."""
        # Test basic creation
        employee = Employee(
            employee_id="E001",
            name="John Smith",
            current_job="J001"
        )
        
        self.assertEqual(employee.employee_id, "E001")
        self.assertEqual(employee.name, "John Smith")
        self.assertEqual(employee.current_job, "J001")
        self.assertEqual(len(employee.skills), 0)
        
        # Test with skills
        employee_with_skills = Employee(
            employee_id="E002",
            name="Jane Doe",
            current_job="J002",
            skills={"S001": 4, "S002": 3}
        )
        
        self.assertEqual(len(employee_with_skills.skills), 2)
        self.assertEqual(employee_with_skills.skills["S001"], 4)
        
        # Test validation
        with self.assertRaises(ValueError):
            Employee(employee_id="", name="Invalid", current_job="J001")
            
        with self.assertRaises(ValueError):
            Employee(employee_id="E003", name="", current_job="J001")
            
        with self.assertRaises(ValueError):
            Employee(employee_id="E004", name="No Job", current_job="")
            
        # Test skill proficiency validation
        with self.assertRaises(ValueError):
            Employee(
                employee_id="E005",
                name="Invalid Proficiency",
                current_job="J001",
                skills={"S001": 10}  # Should be 0-5
            )
        
        # Test string proficiency conversion
        employee = Employee(
            employee_id="E006",
            name="String Proficiency",
            current_job="J001",
            skills={"S001": "3"}
        )
        self.assertEqual(employee.skills["S001"], 3)

    def test_employee_methods(self):
        """Test Employee class methods."""
        employee = Employee(
            employee_id="E001",
            name="John Smith",
            current_job="J001"
        )
        
        # Test adding skills
        employee.add_skill("S001", 3)
        employee.add_skill("S002", 4)
        self.assertEqual(len(employee.skills), 2)
        self.assertEqual(employee.skills["S001"], 3)
        
        # Test invalid proficiency
        with self.assertRaises(ValueError):
            employee.add_skill("S003", 6)
        
        # Test updating skills
        employee.update_skill("S001", 5)
        self.assertEqual(employee.skills["S001"], 5)
        
        # Test updating non-existent skill
        with self.assertRaises(ValueError):
            employee.update_skill("nonexistent", 3)
        
        # Test removing skills
        employee.remove_skill("S001")
        self.assertEqual(len(employee.skills), 1)
        self.assertNotIn("S001", employee.skills)
        
        # Test removing non-existent skill (should not raise error)
        employee.remove_skill("nonexistent")
        
        # Test get_skill_proficiency
        self.assertEqual(employee.get_skill_proficiency("S002"), 4)
        self.assertIsNone(employee.get_skill_proficiency("nonexistent"))
        
        # Test has_skill
        self.assertTrue(employee.has_skill("S002"))
        self.assertFalse(employee.has_skill("nonexistent"))
        
        # Test has_skill with min_proficiency
        self.assertTrue(employee.has_skill("S002", min_proficiency=3))
        self.assertTrue(employee.has_skill("S002", min_proficiency=4))
        self.assertFalse(employee.has_skill("S002", min_proficiency=5))

    def test_meets_job_requirements(self):
        """Test the meets_job_requirements method."""
        employee = Employee(
            employee_id="E001",
            name="John Smith",
            current_job="J001",
            skills={"S001": 3, "S002": 4, "S003": 2}
        )
        
        # Create a job with requirements
        job = Job(
            job_id="J002",
            title="New Role",
            department="IT",
            level=JobLevel.MID_LEVEL,
            skills={"S001": 3, "S002": 3, "S004": 2}
        )
        
        # Test with default threshold (0.7)
        # Employee has 2 out of 3 required skills at sufficient level (S001, S002)
        # 2/3 = 0.67 which is < 0.7, so should return False
        self.assertFalse(employee.meets_job_requirements(job))
        
        # Test with lower threshold
        self.assertTrue(employee.meets_job_requirements(job, min_proficiency_ratio=0.6))
        
        # Test with higher threshold
        self.assertFalse(employee.meets_job_requirements(job, min_proficiency_ratio=0.8))
        
        # Test with job that has no skill requirements
        empty_job = Job(
            job_id="J003",
            title="No Skills Required",
            department="IT",
            level=JobLevel.ENTRY
        )
        self.assertTrue(employee.meets_job_requirements(empty_job))

    def test_employee_database(self):
        """Test EmployeeDatabase class."""
        database = EmployeeDatabase()
        
        # Create employees
        employee1 = Employee(
            employee_id="E001",
            name="John Smith",
            current_job="J001",
            skills={"S001": 3, "S002": 4}
        )
        
        employee2 = Employee(
            employee_id="E002",
            name="Jane Doe",
            current_job="J002",
            skills={"S001": 2, "S003": 5}
        )
        
        # Add employees
        database.add_employee(employee1)
        database.add_employee(employee2)
        
        self.assertEqual(len(database.employees), 2)
        self.assertEqual(len(database.job_counts), 2)
        self.assertEqual(len(database.skills_distribution), 3)
        
        # Test job counts
        self.assertEqual(database.job_counts["J001"], 1)
        self.assertEqual(database.job_counts["J002"], 1)
        
        # Test skills distribution
        self.assertEqual(database.skills_distribution["S001"], 2)
        self.assertEqual(database.skills_distribution["S002"], 1)
        self.assertEqual(database.skills_distribution["S003"], 1)
        
        # Test duplicate employee ID
        with self.assertRaises(ValueError):
            database.add_employee(Employee(
                employee_id="E001",  # Duplicate ID
                name="Duplicate",
                current_job="J003"
            ))
        
        # Test retrieval methods
        self.assertEqual(database.get_employee("E001"), employee1)
        self.assertIsNone(database.get_employee("nonexistent"))
        
        # Test get_employees_by_job
        j001_employees = database.get_employees_by_job("J001")
        self.assertEqual(len(j001_employees), 1)
        self.assertEqual(j001_employees[0], employee1)
        
        # Test get_employees_with_skill
        employees_with_s001 = database.get_employees_with_skill("S001")
        self.assertEqual(len(employees_with_s001), 2)
        
        # Test with min_proficiency
        employees_with_s001_proficient = database.get_employees_with_skill("S001", min_proficiency=3)
        self.assertEqual(len(employees_with_s001_proficient), 1)
        self.assertEqual(employees_with_s001_proficient[0], employee1)

    def test_employee_database_updates(self):
        """Test updating and removing employees from the database."""
        database = EmployeeDatabase()
        
        # Add initial employee
        employee1 = Employee(
            employee_id="E001",
            name="John Smith",
            current_job="J001",
            skills={"S001": 3, "S002": 4}
        )
        database.add_employee(employee1)
        
        # Test updating employee
        updated_employee = Employee(
            employee_id="E001",
            name="John Smith Updated",
            current_job="J002",  # Changed job
            skills={"S001": 4, "S003": 3}  # Changed skills
        )
        database.update_employee(updated_employee)
        
        # Check the update worked
        self.assertEqual(database.employees["E001"].name, "John Smith Updated")
        self.assertEqual(database.employees["E001"].current_job, "J002")
        
        # Check job counts were updated
        self.assertEqual(database.job_counts.get("J001", 0), 0)  # Should be removed or zero
        self.assertEqual(database.job_counts["J002"], 1)
        
        # Check skills distribution was updated
        self.assertEqual(database.skills_distribution["S001"], 1)
        self.assertEqual(database.skills_distribution.get("S002", 0), 0)  # Should be removed or zero
        self.assertEqual(database.skills_distribution["S003"], 1)
        
        # Test updating non-existent employee
        with self.assertRaises(ValueError):
            database.update_employee(Employee(
                employee_id="nonexistent",
                name="Nonexistent",
                current_job="J001"
            ))
        
        # Test removing employee
        database.remove_employee("E001")
        self.assertEqual(len(database.employees), 0)
        self.assertLessEqual(database.job_counts.get("J002", 0), 0)  # Should be 0 or not present
        self.assertEqual(len(database.skills_distribution), 0)
        
        # Test removing non-existent employee
        with self.assertRaises(ValueError):
            database.remove_employee("nonexistent")

    def test_get_eligible_employees_for_job(self):
        """Test getting eligible employees for a job."""
        database = EmployeeDatabase()
        
        # Add employees with different skills
        database.add_employee(Employee(
            employee_id="E001",
            name="John Smith",
            current_job="J001",
            skills={"S001": 4, "S002": 3, "S003": 5}
        ))
        
        database.add_employee(Employee(
            employee_id="E002",
            name="Jane Doe",
            current_job="J002",
            skills={"S001": 2, "S002": 2}
        ))
        
        database.add_employee(Employee(
            employee_id="E003",
            name="Bob Johnson",
            current_job="J003",
            skills={"S004": 5, "S005": 4}
        ))
        
        # Create a job
        job = Job(
            job_id="J004",
            title="Target Job",
            department="IT",
            level=JobLevel.SENIOR,
            skills={"S001": 3, "S002": 3, "S003": 4}
        )
        
        # Test with default threshold (0.8)
        eligible = database.get_eligible_employees_for_job(job)
        self.assertEqual(len(eligible), 1)  # Only John meets all requirements
        self.assertEqual(eligible[0].name, "John Smith")
        
        # Test with lower threshold
        eligible_lower = database.get_eligible_employees_for_job(job, min_proficiency_ratio=0.5)
        self.assertEqual(len(eligible_lower), 1)  # Only John qualifies
        
        # Test with job having no requirements
        empty_job = Job(
            job_id="J005",
            title="No Requirements",
            department="HR",
            level=JobLevel.ENTRY
        )
        eligible_for_empty = database.get_eligible_employees_for_job(empty_job)
        self.assertEqual(len(eligible_for_empty), 3)  # All employees should qualify

    def test_employee_database_serialization(self):
        """Test EmployeeDatabase serialization to dict and back."""
        # Create a database
        database = EmployeeDatabase()
        database.add_employee(Employee(
            employee_id="E001",
            name="John Smith",
            current_job="J001",
            skills={"S001": 3, "S002": 4}
        ))
        
        # Convert to dict
        db_dict = database.to_dict()
        
        # Check dict structure
        self.assertIn("E001", db_dict)
        self.assertEqual(db_dict["E001"]["name"], "John Smith")
        self.assertEqual(db_dict["E001"]["current_job"], "J001")
        self.assertEqual(db_dict["E001"]["skills"], {"S001": 3, "S002": 4})
        
        # Convert back from dict
        new_database = EmployeeDatabase.from_dict(db_dict)
        
        # Check new database
        self.assertEqual(len(new_database.employees), 1)
        self.assertIn("E001", new_database.employees)
        self.assertEqual(new_database.employees["E001"].name, "John Smith")
        self.assertEqual(new_database.employees["E001"].skills, {"S001": 3, "S002": 4})
        
        # Test parsing string skill format
        string_skills_dict = {
            "E002": {
                "name": "Jane Doe",
                "current_job": "J002",
                "skills": "S001:4,S002:5"
            }
        }
        
        string_db = EmployeeDatabase.from_dict(string_skills_dict)
        self.assertEqual(string_db.employees["E002"].skills, {"S001": 4, "S002": 5})

    @patch("skill_similarity_engine.data.loaders.EmployeeLoader.load_from_csv")
    @patch("skill_similarity_engine.data.loaders.EmployeeLoader.load_from_excel") 
    def test_database_from_file(self, mock_load_excel, mock_load_csv):
        """Test loading database from file."""
        # Mock the loader functions
        mock_database = MagicMock()
        mock_load_csv.return_value = mock_database
        mock_load_excel.return_value = mock_database
        
        # We also need to mock the EmployeeLoader.__init__ method to avoid error
        with patch("skill_similarity_engine.data.loaders.EmployeeLoader.__init__", return_value=None):
            # Test CSV loading
            result = EmployeeDatabase.from_file("employees.csv")
            self.assertEqual(result, mock_database)
            
            # Test Excel loading
            result = EmployeeDatabase.from_file("employees.xlsx")
            self.assertEqual(result, mock_database)
            
            # Test unsupported file type
            with self.assertRaises(ValueError):
                EmployeeDatabase.from_file("employees.txt")


class TestModelsWithRealData(unittest.TestCase):
    """Test cases for models using real sample data."""
    
    def setUp(self):
        """Set up test environment with real sample data."""
        # Get the path to sample data
        self.sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
        
        # Load the skill taxonomy
        from skill_similarity_engine.models.skills import SkillTaxonomy
        self.taxonomy = SkillTaxonomy.from_file(os.path.join(self.sample_dir, 'skills.csv'))
        
        # Load the job architecture
        from skill_similarity_engine.models.jobs import JobArchitecture
        from skill_similarity_engine.data.loaders import JobArchitectureLoader
        job_loader = JobArchitectureLoader(self.taxonomy)
        self.job_arch = job_loader.load_from_csv(os.path.join(self.sample_dir, 'jobs.csv'))
        
        # Load the employee database
        from skill_similarity_engine.models.employees import EmployeeDatabase
        from skill_similarity_engine.data.loaders import EmployeeLoader
        employee_loader = EmployeeLoader(self.taxonomy, self.job_arch)
        self.employee_db = employee_loader.load_from_csv(os.path.join(self.sample_dir, 'employees.csv'))
    
    def test_skill_taxonomy_structure(self):
        """Test the structure of the loaded skill taxonomy."""
        # Check that we have skills and categories
        self.assertGreater(len(self.taxonomy.skills), 0)
        self.assertGreater(len(self.taxonomy.categories), 0)
        
        # Check skill structure
        for skill_id, skill in self.taxonomy.skills.items():
            self.assertIsInstance(skill_id, str)
            self.assertIsInstance(skill.name, str)
            self.assertIsInstance(skill.category_id, str)
            self.assertIn(skill.category_id, self.taxonomy.categories)
    
    def test_job_architecture_structure(self):
        """Test the structure of the loaded job architecture."""
        # Check that we have jobs
        self.assertGreater(len(self.job_arch.jobs), 0)
        
        # Check job structure
        for job_id, job in self.job_arch.jobs.items():
            self.assertIsInstance(job_id, str)
            self.assertIsInstance(job.title, str)
            self.assertIsInstance(job.department, str)
            self.assertIsInstance(job.skills, dict)
            
            # Check that all skills in jobs exist in taxonomy
            for skill_id, level in job.skills.items():
                self.assertIn(skill_id, self.taxonomy.skills)
                self.assertIsInstance(level, (int, float))
    
    def test_employee_database_structure(self):
        """Test the structure of the loaded employee database."""
        # Check that we have employees
        self.assertGreater(len(self.employee_db.employees), 0)
        
        # Check employee structure
        for emp_id, employee in self.employee_db.employees.items():
            self.assertIsInstance(emp_id, str)
            self.assertIsInstance(employee.name, str)
            self.assertIsInstance(employee.current_job, str)
            self.assertIn(employee.current_job, self.job_arch.jobs)
            self.assertIsInstance(employee.skills, dict)
            
            # Check that all skills in employee profiles exist in taxonomy
            for skill_id, level in employee.skills.items():
                self.assertIn(skill_id, self.taxonomy.skills)
                self.assertIsInstance(level, (int, float))
    
    def test_model_relationships(self):
        """Test relationships between models using real data."""
        # Get a sample employee
        sample_emp_id = next(iter(self.employee_db.employees))
        employee = self.employee_db.employees[sample_emp_id]
        
        # Check employee-job relationship
        self.assertIn(employee.current_job, self.job_arch.jobs)
        current_job = self.job_arch.jobs[employee.current_job]
        
        # Check that employee's skills are a subset of job's skills
        for skill_id in employee.skills:
            self.assertIn(skill_id, current_job.skills)
        
        # Check that all skills exist in taxonomy
        for skill_id in current_job.skills:
            self.assertIn(skill_id, self.taxonomy.skills)
    
    def test_skill_categories(self):
        """Test skill categories using real data."""
        # Check that all skills have valid categories
        for skill_id, skill in self.taxonomy.skills.items():
            self.assertIn(skill.category_id, self.taxonomy.categories)
            
            # Check that skill is listed in its category
            self.assertIn(skill_id, self.taxonomy.skills_by_category[skill.category_id])
    
    def test_department_structure(self):
        """Test department structure in job architecture."""
        departments = set(job.department for job in self.job_arch.jobs.values())
        self.assertGreater(len(departments), 0)
        
        # Check that each department has at least one job
        for department in departments:
            department_jobs = [job for job in self.job_arch.jobs.values() 
                             if job.department == department]
            self.assertGreater(len(department_jobs), 0)
    
    def test_skill_levels(self):
        """Test skill levels across models."""
        # Check that skill levels are within valid range (1-5)
        for job in self.job_arch.jobs.values():
            for skill_id, level in job.skills.items():
                self.assertGreaterEqual(level, 1)
                self.assertLessEqual(level, 5)
        
        for employee in self.employee_db.employees.values():
            for skill_id, level in employee.skills.items():
                self.assertGreaterEqual(level, 1)
                self.assertLessEqual(level, 5)


if __name__ == "__main__":
    unittest.main()
