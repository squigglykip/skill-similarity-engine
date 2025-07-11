"""
CLI Commands Module for Skill Similarity Engine

This module provides command-based CLI operations following the Command pattern.
Each command encapsulates a specific workflow or operation.
"""

from .base_command import BaseCommand, CommandResult
from .data_commands import DataLoadCommand, DataValidationCommand
from .precompute_commands import SimilarityMatrixCommand, MovementAnalysisCommand
from .query_commands import QuerySimilarityCommand

__all__ = [
    # Base classes
    'BaseCommand',
    'CommandResult',
    
    # Data commands
    'DataLoadCommand',
    'DataValidationCommand',
    
    # Precompute commands
    'SimilarityMatrixCommand',
    'MovementAnalysisCommand',
    
    # Query commands
    'QuerySimilarityCommand',
] 