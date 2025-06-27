"""
Configuration module for Career Transition Analysis Generator system.
Contains styling, formatting, and other configuration settings.
"""

from .document_styles import DocumentStyles, NABColors, FontSettings, SpacingSettings
from .settings import CareerAnalysisSettings, get_section_config, get_output_config, get_database_config, get_analysis_config

__all__ = [
    'DocumentStyles',
    'NABColors', 
    'FontSettings',
    'SpacingSettings',
    'CareerAnalysisSettings',
    'get_section_config',
    'get_output_config', 
    'get_database_config',
    'get_analysis_config'
]
