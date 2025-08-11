"""
Career Analysis Services Package

This package provides a clean service layer for career analysis functionality,
replacing the CLI-to-web hack with proper service-oriented architecture.

Services:
- CareerAnalysisService: Main orchestrator for career analysis generation
- PreviewService: Specialized service for web preview generation
- ValidationService: Input validation and sanitization

Note: DocumentService removed during V2 migration - will be replaced with
simplified HTML-to-Word pipeline in Phase 3.
"""

from .career_analysis_service import CareerAnalysisService
from .preview_service import PreviewService
from .validation_service import ValidationService

__all__ = [
    'CareerAnalysisService',
    'PreviewService', 
    'ValidationService'
] 