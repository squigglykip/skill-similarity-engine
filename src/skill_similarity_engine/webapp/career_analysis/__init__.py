"""
Career Transition Analysis Generator Module for NAB Skills Intelligence Platform
================================================================

This module provides automated Career Transition Analysis Generator capabilities with:
- Threshold-based narrative selection
- Audience-specific content adaptation
- Multi-format output (Word, PDF, PowerPoint)
- Corporate template integration
- Embedded visualizations

Author: Future Skills Team
Date: December 2024
"""

from .generator import CareerAnalysisGenerator
from .analyzer import DataAnalyzer
from .formatter import DocumentFormatter

__version__ = "1.0.0"
__all__ = ["CareerAnalysisGenerator", "DataAnalyzer", "DocumentFormatter"]

