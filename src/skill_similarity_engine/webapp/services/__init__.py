"""
Services Module for NAB Skills Intelligence Platform
===================================================

Service layer providing business logic and data access functionality
for the webapp. Follows enterprise architecture patterns with clear
separation of concerns.

Services included:
- DatabaseService: Core database operations and job queries
- JobService: Job display management and formatting
- Career analysis services: Already exists in career_analysis/services/
"""

from .database_service import DatabaseService
from .job_service import JobService

__all__ = [
    'DatabaseService',
    'JobService'
] 