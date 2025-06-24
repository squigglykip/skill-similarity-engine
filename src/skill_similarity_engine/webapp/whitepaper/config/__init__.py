"""
Configuration module for white paper generation system.
Contains styling, formatting, and other configuration settings.
"""

from .document_styles import DocumentStyles, NABColors, FontSettings, SpacingSettings
from .settings import WhitePaperSettings, get_section_config, get_output_config, get_database_config, get_analysis_config

__all__ = [
    'DocumentStyles',
    'NABColors', 
    'FontSettings',
    'SpacingSettings',
    'WhitePaperSettings',
    'get_section_config',
    'get_output_config', 
    'get_database_config',
    'get_analysis_config'
]