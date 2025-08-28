"""
Document and Content Formatting Module
=====================================

This module provides formatting utilities for career analysis content generation.
It supports both document-level formatting (DocumentFormatter) and content-level
formatting (ContentFormatter) for various output formats.
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ContentFormatter:
    """
    Content formatter for structured content generation.
    
    Provides methods to create formatted content elements like tables,
    lists, and structured text blocks that can be consumed by both
    document generators and web preview systems.
    """
    
    @staticmethod
    def create_table(headers: List[str], rows: List[List[str]], formatting: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a formatted table structure.
        
        Args:
            headers: List of column headers
            rows: List of row data (each row is a list of cell values)
            formatting: Optional formatting metadata
            
        Returns:
            Dict containing structured table data
        """
        return {
            'type': 'table',
            'headers': headers,
            'rows': rows,
            'formatting': formatting or {'table_style': 'standard'},
            'metadata': {
                'row_count': len(rows),
                'column_count': len(headers) if headers else 0
            }
        }
    
    @staticmethod
    def create_formatted_content(content: str, formatting: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create formatted content with metadata.
        
        Args:
            content: The text content
            formatting: Optional formatting metadata
            
        Returns:
            Dict containing structured content data
        """
        return {
            'type': 'formatted_content',
            'text': content,
            'formatting': formatting or {'content_type': 'paragraph'},
            'metadata': {
                'length': len(content),
                'word_count': len(content.split()) if content else 0
            }
        }
    
    @staticmethod
    def create_paragraph(content: str, items: List[str] = None, formatting: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a formatted paragraph structure.
        
        Args:
            content: The main paragraph content
            items: Optional list of items to include
            formatting: Optional formatting metadata
            
        Returns:
            Dict containing structured paragraph data
        """
        return {
            'type': 'paragraph',
            'content': content,
            'items': items or [],
            'formatting': formatting or {'paragraph_style': 'standard'},
            'metadata': {
                'length': len(content),
                'has_items': bool(items)
            }
        }
    
    @staticmethod
    def create_list(items: List[str], list_type: str = 'bullet', formatting: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a formatted list structure.
        
        Args:
            items: List of items
            list_type: Type of list ('bullet', 'numbered', 'plain')
            formatting: Optional formatting metadata
            
        Returns:
            Dict containing structured list data
        """
        return {
            'type': 'list',
            'items': items,
            'list_type': list_type,
            'formatting': formatting or {'list_style': list_type},
            'metadata': {
                'item_count': len(items)
            }
        }

class DocumentFormatter:
    """
    Document-level formatter for career analysis reports.
    
    Handles the overall document structure, section organization,
    and output format generation for career analysis reports.
    """
    
    def __init__(self, output_format: str = 'web'):
        """
        Initialize document formatter.
        
        Args:
            output_format: Target output format ('web', 'pdf', 'word')
        """
        self.output_format = output_format
        self.sections = {}
        
    def add_section(self, section_key: str, section_data: Dict[str, Any]) -> None:
        """
        Add a section to the document.
        
        Args:
            section_key: Unique identifier for the section
            section_data: Section content and metadata
        """
        self.sections[section_key] = section_data
        
    def format_document(self, sections: Dict[str, Any], metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Format the complete document.
        
        Args:
            sections: Dictionary of section data
            metadata: Optional document metadata
            
        Returns:
            Formatted document structure
        """
        return {
            'success': True,
            'document': {
                'sections': sections,
                'metadata': metadata or {},
                'format': self.output_format,
                'generated_at': self._get_timestamp()
            }
        }
    
    def format_for_web(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format document specifically for web preview.
        
        Args:
            sections: Dictionary of section data
            
        Returns:
            Web-optimized document structure
        """
        formatted_sections = {}
        
        for section_key, section_data in sections.items():
            formatted_sections[section_key] = {
                'title': section_data.get('title', section_key.replace('_', ' ').title()),
                'content': section_data.get('content', ''),
                'subsections': section_data.get('subsections', {}),
                'formatting': section_data.get('formatting', {})
            }
        
        return {
            'success': True,
            'content': formatted_sections,
            'format': 'web',
            'preview_ready': True
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for document metadata."""
        from datetime import datetime
        return datetime.now().isoformat()

# Legacy compatibility aliases
class DocumentGenerator:
    """Legacy alias for DocumentFormatter."""
    def __init__(self, *args, **kwargs):
        self.formatter = DocumentFormatter(*args, **kwargs)
        
    def __getattr__(self, name):
        return getattr(self.formatter, name)

# Export main classes
__all__ = ['ContentFormatter', 'DocumentFormatter', 'DocumentGenerator']
