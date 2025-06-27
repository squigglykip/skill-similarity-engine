"""
Test data access module.

This module provides helper functions to access the synthetic test data
for unit, integration, and functional tests.
"""

import os
import pandas as pd
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.models.employees import EmployeeDatabase

# Path to the test data directory
TEST_DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# HRIS schema file paths
HRIS_JOBS_CSV = os.path.join(TEST_DATA_DIR, "hris_jobs.csv")
HRIS_SKILLS_CSV = os.path.join(TEST_DATA_DIR, "hris_skills.csv") 
HRIS_JOB_SKILLS_CSV = os.path.join(TEST_DATA_DIR, "hris_job_skills.csv")
HRIS_EMPLOYEES_CSV = os.path.join(TEST_DATA_DIR, "hris_employees.csv")

# Engine schema file paths
ENGINE_JOBS_CSV = os.path.join(TEST_DATA_DIR, "jobs.csv")
ENGINE_SKILLS_CSV = os.path.join(TEST_DATA_DIR, "skills.csv")
ENGINE_SKILLS_JSON = os.path.join(TEST_DATA_DIR, "skills.json")
ENGINE_EMPLOYEES_CSV = os.path.join(TEST_DATA_DIR, "employees.csv")

# Configuration file paths
TEST_HRIS_CONFIG = os.path.join(TEST_DATA_DIR, "test_hris_config.yaml")


def load_hris_jobs_df():
    """Load HRIS jobs data as a pandas DataFrame."""
    return pd.read_csv(HRIS_JOBS_CSV)


def load_hris_skills_df():
    """Load HRIS skills data as a pandas DataFrame."""
    return pd.read_csv(HRIS_SKILLS_CSV)


def load_hris_job_skills_df():
    """Load HRIS job-skills mapping data as a pandas DataFrame."""
    return pd.read_csv(HRIS_JOB_SKILLS_CSV, comment='#')


def load_hris_employees_df():
    """Load HRIS employees data as a pandas DataFrame."""
    return pd.read_csv(HRIS_EMPLOYEES_CSV)


def load_engine_jobs_df():
    """Load engine jobs data as a pandas DataFrame."""
    return pd.read_csv(ENGINE_JOBS_CSV)


def load_engine_skills_df():
    """Load engine skills data as a pandas DataFrame."""
    return pd.read_csv(ENGINE_SKILLS_CSV)


def load_engine_employees_df():
    """Load engine employees data as a pandas DataFrame."""
    return pd.read_csv(ENGINE_EMPLOYEES_CSV)


def load_skill_taxonomy():
    """Load a SkillTaxonomy from the test data."""
    return SkillTaxonomy.from_file(ENGINE_SKILLS_CSV)


def load_job_architecture():
    """Load a JobArchitecture from the test data."""
    return JobArchitecture.from_file(ENGINE_JOBS_CSV)


def load_employee_database():
    """Load an EmployeeDatabase from the test data."""
    # First load the job architecture, which is required by EmployeeLoader
    job_arch = load_job_architecture()
    return EmployeeDatabase.from_file(ENGINE_EMPLOYEES_CSV, job_architecture=job_arch)


def get_hris_config_path():
    """Get the path to the test HRIS configuration file."""
    return TEST_HRIS_CONFIG 
