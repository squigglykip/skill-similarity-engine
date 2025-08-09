"""
Precompute Commands Orchestrator

Centralised access point for all precompute command classes.
Maintains backward compatibility while providing modular architecture.

This file serves as an orchestrator, importing all command classes from their
respective focused modules and providing a unified interface for command discovery.
"""

# Import all command modules
from .similarity_commands import SimilarityMatrixCommand
from .movement_commands import (
    MovementAnalysisCommand, 
    MovementPatternPopulationCommand, 
    MovementMLTrainingCommand
)
from .clustering_commands import (
    SkillsOptimizationCommand,
    ClusteringOptimizationCommand, 
    ClusteringAnalysisCommand
)
from .analytics_commands import (
    VelocityAnalysisCommand,
    DiagnosticsAnalysisCommand
)
from .utility_commands import (
    DatabaseCleanupCommand,
    ExcelConverterCommand,
    SchemaDocumentationCommand
)

# Command registry for discovery and programmatic access
PRECOMPUTE_COMMANDS = {
    'similarity_matrix': SimilarityMatrixCommand,
    'movement_analysis': MovementAnalysisCommand,
    'movement_pattern_population': MovementPatternPopulationCommand,
    'movement_ml_training': MovementMLTrainingCommand,
    'skills_optimization': SkillsOptimizationCommand,
    'clustering_optimization': ClusteringOptimizationCommand,
    'clustering_analysis': ClusteringAnalysisCommand,
    'velocity_analysis': VelocityAnalysisCommand,
    'diagnostics_analysis': DiagnosticsAnalysisCommand,
    'database_cleanup': DatabaseCleanupCommand,
    'excel_converter': ExcelConverterCommand,
    'schema_documentation': SchemaDocumentationCommand,
}

# Command categories for organized access
COMMAND_CATEGORIES = {
    'similarity': ['similarity_matrix'],
    'movement': ['movement_analysis', 'movement_pattern_population', 'movement_ml_training'],
    'clustering': ['skills_optimization', 'clustering_optimization', 'clustering_analysis'],
    'analytics': ['velocity_analysis', 'diagnostics_analysis'],
    'utilities': ['database_cleanup', 'excel_converter', 'schema_documentation'],
}

# Export all classes for backward compatibility
__all__ = [
    # Individual command classes
    'SimilarityMatrixCommand',
    'MovementAnalysisCommand', 
    'MovementPatternPopulationCommand',
    'MovementMLTrainingCommand',
    'SkillsOptimizationCommand',
    'ClusteringOptimizationCommand',
    'ClusteringAnalysisCommand', 
    'VelocityAnalysisCommand',
    'DiagnosticsAnalysisCommand',
    'DatabaseCleanupCommand',
    'ExcelConverterCommand',
    'SchemaDocumentationCommand',
    
    # Command registry and utilities
    'PRECOMPUTE_COMMANDS',
    'COMMAND_CATEGORIES',
    'get_command_class',
    'list_commands',
    'get_commands_by_category',
]

# Utility functions for command discovery
def get_command_class(command_name: str):
    """
    Get a command class by name.
    
    Args:
        command_name: Name of the command
        
    Returns:
        Command class or None if not found
    """
    return PRECOMPUTE_COMMANDS.get(command_name)

def list_commands():
    """
    List all available command names.
    
    Returns:
        List of command names
    """
    return list(PRECOMPUTE_COMMANDS.keys())

def get_commands_by_category(category: str):
    """
    Get command names for a specific category.
    
    Args:
        category: Category name (similarity, movement, clustering, analytics, utilities)
        
    Returns:
        List of command names in the category
    """
    return COMMAND_CATEGORIES.get(category, [])

def get_command_info():
    """
    Get information about all commands.
    
    Returns:
        Dictionary with command metadata
    """
    info = {}
    for name, cls in PRECOMPUTE_COMMANDS.items():
        info[name] = {
            'class': cls.__name__,
            'description': cls().description,
            'module': cls.__module__,
        }
    return info

# Module metadata
__version__ = "2.0.0"
__refactor_date__ = "2024-12-19"
__original_lines__ = 2376
__new_structure__ = {
    'similarity_commands.py': '~500 lines',
    'movement_commands.py': '~700 lines', 
    'clustering_commands.py': '~600 lines',
    'analytics_commands.py': '~300 lines',
    'utility_commands.py': '~400 lines',
    'precompute_commands.py (orchestrator)': '~100 lines'
}
