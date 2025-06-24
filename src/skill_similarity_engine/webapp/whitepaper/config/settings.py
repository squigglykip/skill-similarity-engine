"""
General settings and configuration for the white paper generation system.
Contains file paths, output formats, and other system-wide settings.
"""

from pathlib import Path
from typing import Dict, List, Any

class WhitePaperSettings:
    """General configuration settings for white paper generation."""
    
    # File and directory settings
    BASE_DIR = Path(__file__).parent.parent
    TEMPLATES_DIR = BASE_DIR / 'templates'
    OUTPUT_DIR = BASE_DIR / 'output'
    
    # Template directories
    SECTIONS_TEMPLATES_DIR = TEMPLATES_DIR / 'sections'
    NARRATIVES_TEMPLATES_DIR = TEMPLATES_DIR / 'narratives'
    AUDIENCES_TEMPLATES_DIR = TEMPLATES_DIR / 'audiences'
    SCENARIOS_TEMPLATES_DIR = TEMPLATES_DIR / 'scenarios'
    
    # Output formats supported
    SUPPORTED_OUTPUT_FORMATS = [
        'word',
        'pdf', 
        'powerpoint',
        'html',
        'markdown'
    ]
    
    # Default settings
    DEFAULT_OUTPUT_FORMAT = 'word'
    DEFAULT_AUDIENCE = 'business_leaders'
    DEFAULT_SCENARIO = 'skills_gap_analysis'
    
    # Section configuration
    SECTION_ORDER = [
        'executive_summary',
        'current_role_context',
        'pathway_analysis', 
        'strategic_recommendations',
        'conclusion'
    ]
    
    SECTION_TITLES = {
        'executive_summary': 'Executive Summary',
        'current_role_context': 'Current Role Context',
        'pathway_analysis': 'Pathway Analysis: Top 3 Strategic Opportunities',
        'strategic_recommendations': 'Strategic Recommendations',
        'conclusion': 'Conclusion'
    }
    
    # Database settings
    DEFAULT_DB_PATH = BASE_DIR.parent.parent.parent.parent / 'models' / '2025-Q2' / 'business_context.sqlite'
    
    # Performance settings
    MAX_PATHWAYS_ANALYSIS = 5
    DEFAULT_PATHWAYS_ANALYSIS = 3
    CACHE_TIMEOUT_SECONDS = 3600  # 1 hour
    
    # Quality control settings
    MIN_SIMILARITY_THRESHOLD = 0.1
    MAX_SIMILARITY_THRESHOLD = 0.99  # Exclude 100% matches (identical roles)
    
    # Content generation settings
    REFERENCE_NUMBERING_START = 1
    MAX_REFERENCE_NUMBER = 999
    
    # File naming conventions
    FILE_NAME_PATTERNS = {
        'word': 'whitepaper_{job_name}_{timestamp}.docx',
        'pdf': 'whitepaper_{job_name}_{timestamp}.pdf',
        'powerpoint': 'whitepaper_summary_{job_name}_{timestamp}.pptx',
        'html': 'whitepaper_{job_name}_{timestamp}.html',
        'markdown': 'whitepaper_{job_name}_{timestamp}.md'
    }
    
    # Logging configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_section_config(cls) -> Dict[str, Any]:
        """Get configuration for sections."""
        return {
            'order': cls.SECTION_ORDER,
            'titles': cls.SECTION_TITLES,
            'templates_dir': cls.SECTIONS_TEMPLATES_DIR
        }
    
    @classmethod
    def get_output_config(cls) -> Dict[str, Any]:
        """Get configuration for output generation."""
        return {
            'formats': cls.SUPPORTED_OUTPUT_FORMATS,
            'default_format': cls.DEFAULT_OUTPUT_FORMAT,
            'file_patterns': cls.FILE_NAME_PATTERNS,
            'output_dir': cls.OUTPUT_DIR
        }
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            'default_path': cls.DEFAULT_DB_PATH,
            'similarity_thresholds': {
                'min': cls.MIN_SIMILARITY_THRESHOLD,
                'max': cls.MAX_SIMILARITY_THRESHOLD
            }
        }
    
    @classmethod
    def get_analysis_config(cls) -> Dict[str, Any]:
        """Get analysis configuration."""
        return {
            'max_pathways': cls.MAX_PATHWAYS_ANALYSIS,
            'default_pathways': cls.DEFAULT_PATHWAYS_ANALYSIS,
            'default_audience': cls.DEFAULT_AUDIENCE,
            'default_scenario': cls.DEFAULT_SCENARIO
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return any issues."""
        issues = []
        
        # Check if template directories exist
        for template_dir in [
            cls.SECTIONS_TEMPLATES_DIR,
            cls.NARRATIVES_TEMPLATES_DIR,
            cls.AUDIENCES_TEMPLATES_DIR,
            cls.SCENARIOS_TEMPLATES_DIR
        ]:
            if not template_dir.exists():
                issues.append(f"Template directory missing: {template_dir}")
        
        # Check if output directory is writable
        try:
            cls.OUTPUT_DIR.mkdir(exist_ok=True)
        except Exception as e:
            issues.append(f"Cannot create output directory: {e}")
        
        # Validate settings consistency
        if cls.DEFAULT_OUTPUT_FORMAT not in cls.SUPPORTED_OUTPUT_FORMATS:
            issues.append(f"Default output format '{cls.DEFAULT_OUTPUT_FORMAT}' not in supported formats")
        
        if cls.MAX_PATHWAYS_ANALYSIS < cls.DEFAULT_PATHWAYS_ANALYSIS:
            issues.append("Default pathways analysis exceeds maximum pathways analysis")
        
        return issues


# Create default settings instance
default_settings = WhitePaperSettings()

# Export convenience functions
def get_section_config():
    """Get section configuration."""
    return default_settings.get_section_config()

def get_output_config():
    """Get output configuration."""
    return default_settings.get_output_config()

def get_database_config():
    """Get database configuration."""
    return default_settings.get_database_config()

def get_analysis_config():
    """Get analysis configuration."""
    return default_settings.get_analysis_config() 