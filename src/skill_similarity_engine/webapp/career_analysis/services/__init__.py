"""
Career Analysis Services Package

This package provides a clean service layer for career analysis functionality,
replacing the CLI-to-web hack with proper service-oriented architecture.

Services:
- CareerAnalysisService: Main orchestrator for career analysis generation
- PreviewService: Specialized service for web preview generation
- DocumentService: Service for downloadable document generation
- ValidationService: Input validation and sanitization
"""

from .career_analysis_service import CareerAnalysisService
from .preview_service import PreviewService
from .document_service import DocumentService
from .validation_service import ValidationService

__all__ = [
    'CareerAnalysisService',
    'PreviewService', 
    'DocumentService',
    'ValidationService'
] 