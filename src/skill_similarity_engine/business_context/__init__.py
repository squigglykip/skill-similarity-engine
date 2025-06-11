"""
Business Context Database Generation Module

This module provides CLI functionality for generating comprehensive SQLite databases
that combine job similarities with business context data for the NAB Skill Similarity Engine.

Module Components:
- schema_builder: SQLite schema creation from design specifications
- data_loader: CSV to SQLite data loading pipeline
- similarity_integrator: Parquet similarity data integration
- validator: Data integrity and relationship validation
- orchestrator: CLI menu integration and workflow coordination
"""

from .orchestrator import BusinessContextOrchestrator

__all__ = ['BusinessContextOrchestrator'] 