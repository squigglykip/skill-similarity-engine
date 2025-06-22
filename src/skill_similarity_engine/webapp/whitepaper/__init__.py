"""
White Paper Generation Module for NAB Skills Intelligence Platform
================================================================

This module provides automated white paper generation capabilities with:
- Threshold-based narrative selection
- Audience-specific content adaptation
- Multi-format output (Word, PDF, PowerPoint)
- Corporate template integration
- Embedded visualizations

Author: Future Skills Team
Date: December 2024
"""

from .generator import WhitePaperGenerator
from .analyzer import DataAnalyzer
from .formatter import DocumentFormatter

__version__ = "1.0.0"
__all__ = ["WhitePaperGenerator", "DataAnalyzer", "DocumentFormatter"]
