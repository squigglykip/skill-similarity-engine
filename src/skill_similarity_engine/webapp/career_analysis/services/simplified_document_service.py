"""
Simplified Document Service

HTML-to-PDF/Word document generation service that replaces the complex Word styling system.
Supports multiple output formats:
- PDF: Uses weasyprint (preferred) or reportlab (Windows fallback)
- Word: Uses python-docx with BeautifulSoup parsing (preferred) or pypandoc/basic fallbacks
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
import tempfile
import os
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

# WeasyPrint will be imported lazily when needed to avoid Windows library issues
WEASYPRINT_AVAILABLE = None  # Will be determined at runtime

# Alternative PDF generation using reportlab (Windows-friendly)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from html import unescape
    import re
    REPORTLAB_AVAILABLE = True
    logging.info("reportlab available for PDF generation")
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("Neither weasyprint nor reportlab available. PDF generation will be disabled.")

try:
    from .preview_service import PreviewService
    from .validation_service import ValidationService
except ImportError:
    # Fallback for when running as script
    from preview_service import PreviewService
    from validation_service import ValidationService

logger = logging.getLogger(__name__)

def _check_weasyprint_availability():
    """Check if WeasyPrint is available at runtime (lazy import)."""
    global WEASYPRINT_AVAILABLE
    if WEASYPRINT_AVAILABLE is None:
        try:
            import weasyprint
            WEASYPRINT_AVAILABLE = True
            logger.info("WeasyPrint successfully imported")
        except ImportError as e:
            WEASYPRINT_AVAILABLE = False
            logger.warning(f"WeasyPrint not available: {str(e)}")
        except OSError as e:
            WEASYPRINT_AVAILABLE = False
            logger.warning(f"WeasyPrint library dependencies missing: {str(e)}")
    return WEASYPRINT_AVAILABLE

class SimplifiedDocumentService:
    """
    Simplified document generation service using HTML-to-PDF pipeline.
    
    This service replaces the complex Word document generation system with a
    streamlined approach that converts HTML previews directly to PDF using weasyprint.
    """
    
    def __init__(self, db_connection):
        """Initialize the simplified document service."""
        self.db = db_connection
        self.preview_service = PreviewService(db_connection)
        self.validation_service = ValidationService(db_connection)
        
        # Check PDF generation capabilities
        weasyprint_available = _check_weasyprint_availability()
        
        if not weasyprint_available and not REPORTLAB_AVAILABLE:
            logger.error("No PDF generation libraries available. Install weasyprint or reportlab.")
        elif not weasyprint_available:
            logger.info("Using reportlab for PDF generation (weasyprint not available)")
        else:
            logger.info("Using weasyprint for PDF generation")
        
        print("SimplifiedDocumentService initialized")
    
    def generate_document(self, form_data: Dict, output_format: str = 'pdf') -> Tuple[bool, Dict[str, Any]]:
        """
        Generate a downloadable document from career analysis data.
        
        Args:
            form_data: Form data from the frontend
            output_format: Output format ('pdf' currently supported)
            
        Returns:
            Tuple of (success, result_data)
        """
        try:
            print(f"Generating {output_format} document for form data: {form_data}")
            
            # Validate form data first
            is_valid, cleaned_data, errors = self.validation_service.validate_form_data(form_data)
            
            if not is_valid:
                return False, {
                    'error': 'Validation failed',
                    'validation_errors': errors
                }
            
            # Generate preview data (this includes V2 analytics if enabled)
            preview_result = self.preview_service.generate_preview(cleaned_data)
            
            if not preview_result['success']:
                return False, {
                    'error': 'Failed to generate preview data',
                    'details': preview_result.get('error', 'Unknown error')
                }
            
            # Generate HTML content for document
            html_content = self._generate_document_html(preview_result, cleaned_data)
            
            # Convert to requested format
            if output_format.lower() == 'pdf':
                # Check if any PDF generation library is available
                weasyprint_available = _check_weasyprint_availability()
                if not weasyprint_available and not REPORTLAB_AVAILABLE:
                    return False, {
                        'error': 'PDF generation not available',
                        'details': 'Neither weasyprint nor reportlab libraries are available'
                    }
                
                pdf_data, filename = self._convert_html_to_pdf(html_content, cleaned_data)
                
                return True, {
                    'content': pdf_data,
                    'filename': filename,
                    'content_type': 'application/pdf',
                    'format': 'pdf'
                }
            
            elif output_format.lower() == 'word':
                # Generate Word document
                word_data, filename = self._convert_html_to_word(html_content, cleaned_data)
                
                return True, {
                    'content': word_data,
                    'filename': filename,
                    'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'format': 'word'
                }
            
            else:
                return False, {
                    'error': f'Unsupported output format: {output_format}',
                    'supported_formats': ['pdf', 'word']
                }
                
        except Exception as e:
            logger.error(f"Error generating document: {str(e)}", exc_info=True)
            return False, {
                'error': f'Document generation failed: {str(e)}'
            }
    
    def _generate_document_html(self, preview_data: Dict[str, Any], form_data: Dict) -> str:
        """
        Generate complete HTML content for document generation.
        
        This creates a standalone HTML document with embedded CSS that can be
        converted to PDF while maintaining proper formatting.
        """
        
        # Extract metadata
        metadata = preview_data.get('metadata', {})
        content = preview_data.get('content', {})
        v2_analytics = preview_data.get('v2_analytics', {})
        
        # Debug: Log available content keys for development
        logger.debug(f"Available content keys: {list(content.keys())}")
        logger.debug(f"V2 analytics keys: {list(v2_analytics.keys()) if v2_analytics else 'None'}")
        
        # Generate document header
        job_from = form_data.get('job_from', 'Unknown')
        analysis_mode = form_data.get('analysis_mode', 'top_matches')
        generated_date = datetime.now().strftime('%B %d, %Y')
        
        # Get job title for header
        job_title = self._get_job_title(job_from)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Career Transition Analysis - {job_title}</title>
            <style>
                {self._get_document_css()}
            </style>
        </head>
        <body>
            <div class="document-container">
                {self._generate_document_header(job_title, analysis_mode, generated_date)}
                {self._generate_executive_summary(content)}
                {self._generate_main_content(content)}
                {self._generate_v2_analytics_content(v2_analytics)}
                {self._generate_document_footer(generated_date)}
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _get_document_css(self) -> str:
        """Generate CSS styles for PDF document formatting."""
        return """
        @page {
            margin: 2cm;
            size: A4;
            @top-center {
                content: "Career Transition Analysis";
                font-family: 'Arial', sans-serif;
                font-size: 10pt;
                color: #666;
            }
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-family: 'Arial', sans-serif;
                font-size: 10pt;
                color: #666;
            }
        }
        
        body {
            font-family: 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .document-container {
            max-width: 100%;
            margin: 0 auto;
        }
        
        .document-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #1e40af;
        }
        
        .document-title {
            font-size: 24pt;
            font-weight: bold;
            color: #1e40af;
            margin-bottom: 10px;
        }
        
        .document-subtitle {
            font-size: 14pt;
            color: #666;
            margin-bottom: 5px;
        }
        
        .document-meta {
            font-size: 10pt;
            color: #888;
        }
        
        .section {
            margin-bottom: 25px;
            page-break-inside: avoid;
        }
        
        .section-title {
            font-size: 16pt;
            font-weight: bold;
            color: #1e40af;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .subsection {
            margin-bottom: 20px;
        }
        
        .subsection-title {
            font-size: 14pt;
            font-weight: bold;
            color: #374151;
            margin-bottom: 10px;
        }
        
        .content-paragraph {
            margin-bottom: 12px;
            text-align: justify;
        }
        
        .opportunity-card {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }
        
        .opportunity-header {
            background-color: #1e40af;
            color: white;
            padding: 10px 15px;
            border-radius: 6px 6px 0 0;
            margin: -15px -15px 15px -15px;
            font-weight: bold;
            font-size: 12pt;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin: 10px 0;
        }
        
        .metric-item {
            text-align: center;
            padding: 8px;
            background-color: #f1f5f9;
            border-radius: 4px;
        }
        
        .metric-label {
            font-size: 9pt;
            color: #666;
            display: block;
        }
        
        .metric-value {
            font-size: 11pt;
            font-weight: bold;
            color: #1e40af;
        }
        
        .v2-analytics-section {
            background-color: #f0f9ff;
            border: 2px solid #0ea5e9;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
            page-break-inside: avoid;
        }
        
        .v2-section-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .v2-icon {
            width: 24px;
            height: 24px;
            background-color: #0ea5e9;
            color: white;
            border-radius: 4px;
            margin-right: 10px;
            text-align: center;
            line-height: 24px;
            font-size: 10pt;
        }
        
        .v2-title {
            font-size: 14pt;
            font-weight: bold;
            color: #0c4a6e;
        }
        
        .v2-badge {
            background-color: #0ea5e9;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 8pt;
            margin-left: auto;
        }
        
        .skills-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 15px 0;
        }
        
        .skill-card {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
        }
        
        .skill-name {
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 5px;
        }
        
        .skill-rarity {
            font-size: 9pt;
            color: #0ea5e9;
            font-weight: bold;
        }
        
        .skill-description {
            font-size: 9pt;
            color: #666;
            margin-top: 5px;
        }
        
        .document-footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            font-size: 9pt;
            color: #666;
        }
        
        .page-break {
            page-break-before: always;
        }
        
        .no-break {
            page-break-inside: avoid;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        th, td {
            border: 1px solid #e2e8f0;
            padding: 8px 12px;
            text-align: left;
        }
        
        th {
            background-color: #f8fafc;
            font-weight: bold;
            color: #374151;
        }
        
        .highlight {
            background-color: #fef3c7;
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .font-bold { font-weight: bold; }
        .text-sm { font-size: 9pt; }
        .text-lg { font-size: 13pt; }
        .mb-2 { margin-bottom: 8px; }
        .mb-4 { margin-bottom: 16px; }
        .mt-4 { margin-top: 16px; }
        """
    
    def _generate_document_header(self, job_title: str, analysis_mode: str, generated_date: str) -> str:
        """Generate document header section."""
        mode_display = "Top Discovery Analysis" if analysis_mode == "top_matches" else "Specific Transition Analysis"
        
        return f"""
        <div class="document-header">
            <div class="document-title">Career Transition Analysis</div>
            <div class="document-subtitle">Strategic Career Intelligence Report</div>
            <div class="document-subtitle">Source Role: {job_title}</div>
            <div class="document-meta">
                Analysis Type: {mode_display} | Generated: {generated_date} | NAB Skills Intelligence Platform
            </div>
        </div>
        """
    
    def _generate_executive_summary(self, content: Dict[str, Any]) -> str:
        """Generate executive summary section from content."""
        # Try both 'executive_summary' and 'introduction' keys for compatibility
        executive_summary = content.get('executive_summary', content.get('introduction', {}))
        
        if not executive_summary:
            return ""
        
        html = '<div class="section"><div class="section-title">Executive Summary</div>'
        
        # Process subsections
        subsections = executive_summary.get('subsections', {})
        for subsection_key, subsection_data in subsections.items():
            title = subsection_data.get('title', subsection_key.replace('_', ' ').title())
            html += f'<div class="subsection"><div class="subsection-title">{title}</div>'
            
            # Process content
            if subsection_data.get('type') == 'content_items':
                items = subsection_data.get('items', [])
                for item in items:
                    content_text = item.get('content', '')
                    if content_text:
                        html += f'<div class="content-paragraph">{self._clean_content_for_pdf(content_text)}</div>'
            else:
                content_text = subsection_data.get('content', '')
                if content_text:
                    html += f'<div class="content-paragraph">{self._clean_content_for_pdf(content_text)}</div>'
            
            html += '</div>'
        
        html += '</div>'
        return html
    
    def _generate_main_content(self, content: Dict[str, Any]) -> str:
        """Generate main content sections."""
        html = ""
        
        # Section order for document - with key mapping for compatibility
        section_order = [
            ('current_role_context', 'Current Role Context'),
            ('pathway_analysis', 'Strategic Career Opportunities'),  # Also try 'pathways'
            ('strategic_recommendations', 'Strategic Recommendations'),
            ('conclusion', 'Conclusion')
        ]
        
        for section_key, section_title in section_order:
            # Try the expected key first, then check for alternative keys
            section_data = None
            if section_key in content:
                section_data = content[section_key]
            elif section_key == 'pathway_analysis' and 'pathways' in content:
                section_data = content['pathways']  # Map 'pathways' to 'pathway_analysis'
            
            if section_data:
                html += self._generate_content_section(section_data, section_title)
        
        return html
    
    def _generate_content_section(self, section_data: Dict[str, Any], section_title: str) -> str:
        """Generate a content section for the document."""
        html = f'<div class="section"><div class="section-title">{section_title}</div>'
        
        subsections = section_data.get('subsections', {})
        for subsection_key, subsection_data in subsections.items():
            title = subsection_data.get('title', subsection_key.replace('_', ' ').title())
            html += f'<div class="subsection"><div class="subsection-title">{title}</div>'
            
            # Handle opportunities list specially
            if subsection_data.get('type') == 'opportunities_list':
                opportunities = subsection_data.get('content', [])
                html += self._generate_opportunities_content(opportunities)
            elif subsection_data.get('type') == 'content_items':
                items = subsection_data.get('items', [])
                for item in items:
                    content_text = item.get('content', '')
                    if content_text:
                        html += f'<div class="content-paragraph">{self._clean_content_for_pdf(content_text)}</div>'
            else:
                content_text = subsection_data.get('content', '')
                if content_text:
                    html += f'<div class="content-paragraph">{self._clean_content_for_pdf(content_text)}</div>'
            
            html += '</div>'
        
        html += '</div>'
        return html
    
    def _generate_opportunities_content(self, opportunities: List[Dict]) -> str:
        """Generate formatted opportunities content for PDF."""
        html = ""
        
        for i, opportunity in enumerate(opportunities, 1):
            if isinstance(opportunity, dict) and opportunity.get('header'):
                # Parse opportunity header
                header_info = self._parse_opportunity_header(opportunity.get('header', ''))
                
                html += f'''
                <div class="opportunity-card">
                    <div class="opportunity-header">
                        Strategic Opportunity {i}: {header_info.get('title', 'Career Transition')}
                    </div>
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <span class="metric-label">Target Role</span>
                            <span class="metric-value">{header_info.get('targetRole', 'N/A')}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Similarity</span>
                            <span class="metric-value">{header_info.get('similarity', 'N/A')}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">Move Type</span>
                            <span class="metric-value">{header_info.get('moveType', 'N/A')}</span>
                        </div>
                    </div>
                '''
                
                # Add opportunity subsections
                subsection_order = [
                    'opportunity_overview',
                    'strategic_positioning', 
                    'skills_transition_analysis',
                    'business_case',
                    'implementation_roadmap'
                ]
                
                for subsection_key in subsection_order:
                    if subsection_key in opportunity:
                        subsection = opportunity[subsection_key]
                        title = subsection.get('title', subsection_key.replace('_', ' ').title())
                        content_text = subsection.get('content', '')
                        
                        if content_text:
                            html += f'''
                            <div class="subsection">
                                <div class="subsection-title">{title}</div>
                                <div class="content-paragraph">{self._clean_content_for_pdf(str(content_text))}</div>
                            </div>
                            '''
                
                html += '</div>'
        
        return html
    
    def _generate_v2_analytics_content(self, v2_analytics: Dict[str, Any]) -> str:
        """Generate V2 Analytics sections for PDF."""
        if not v2_analytics:
            return ""
        
        html = '<div class="page-break"></div><div class="section"><div class="section-title">Enhanced V2 Analytics</div>'
        
        # Defining Skills
        if 'defining_skills' in v2_analytics:
            html += self._generate_v2_defining_skills_pdf(v2_analytics['defining_skills'])
        
        # Job Family Context
        if 'job_family_context' in v2_analytics:
            html += self._generate_v2_job_family_pdf(v2_analytics['job_family_context'])
        
        # Movement Patterns
        if 'movement_patterns' in v2_analytics:
            html += self._generate_v2_movement_patterns_pdf(v2_analytics['movement_patterns'])
        
        # Skills Rarity
        if 'skills_rarity' in v2_analytics:
            html += self._generate_v2_skills_rarity_pdf(v2_analytics['skills_rarity'])
        
        # Transition Insights
        if 'transition_insights' in v2_analytics:
            html += self._generate_v2_transition_insights_pdf(v2_analytics['transition_insights'])
        
        html += '</div>'
        return html
    
    def _generate_v2_defining_skills_pdf(self, defining_skills: Dict[str, Any]) -> str:
        """Generate defining skills section for PDF."""
        skills = defining_skills.get('skills', [])
        if not skills:
            return ""
        
        html = '''
        <div class="v2-analytics-section">
            <div class="v2-section-header">
                <div class="v2-icon">★</div>
                <div class="v2-title">Defining Skills Analysis</div>
                <div class="v2-badge">V2 Enhanced</div>
            </div>
            <div class="skills-grid">
        '''
        
        for skill in skills[:8]:  # Limit for PDF layout
            html += f'''
            <div class="skill-card">
                <div class="skill-name">{skill.get('name', 'Unknown Skill')}</div>
                <div class="skill-rarity">{skill.get('rarity_score', 0)}% rare</div>
                <div class="skill-description">{skill.get('description', 'Core competency for role differentiation')}</div>
            </div>
            '''
        
        html += '</div></div>'
        return html
    
    def _generate_v2_job_family_pdf(self, job_family: Dict[str, Any]) -> str:
        """Generate job family section for PDF."""
        return f'''
        <div class="v2-analytics-section">
            <div class="v2-section-header">
                <div class="v2-icon">⚡</div>
                <div class="v2-title">Job Family Context</div>
                <div class="v2-badge">V2 Enhanced</div>
            </div>
            <div class="content-paragraph">
                <strong>Family:</strong> {job_family.get('family_name', 'Professional Services')}<br>
                <strong>Description:</strong> {job_family.get('description', 'Related roles with similar skill requirements')}<br>
                <strong>Family Size:</strong> {job_family.get('family_size', 12)} related roles<br>
                <strong>Average Similarity:</strong> {job_family.get('avg_similarity', 78)}%<br>
                <strong>Transition Rate:</strong> {job_family.get('transition_rate', 23)}% annually
            </div>
        </div>
        '''
    
    def _generate_v2_movement_patterns_pdf(self, movement_patterns: Dict[str, Any]) -> str:
        """Generate movement patterns section for PDF."""
        patterns = movement_patterns.get('patterns', [])
        if not patterns:
            return ""
        
        html = '''
        <div class="v2-analytics-section">
            <div class="v2-section-header">
                <div class="v2-icon">→</div>
                <div class="v2-title">Movement Patterns</div>
                <div class="v2-badge">V2 Enhanced</div>
            </div>
        '''
        
        for pattern in patterns[:4]:  # Limit for PDF layout
            html += f'''
            <div class="content-paragraph">
                <strong>{pattern.get('pattern_name', 'Pattern')}</strong> ({pattern.get('frequency', 0)}% of transitions)<br>
                {pattern.get('description', 'Career transition pattern')}<br>
                <em>Average timeframe: {pattern.get('avg_timeframe', '18 months')}</em>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _generate_v2_skills_rarity_pdf(self, skills_rarity: Dict[str, Any]) -> str:
        """Generate skills rarity section for PDF."""
        rare_skills = skills_rarity.get('rare_skills', [])
        if not rare_skills:
            return ""
        
        html = '''
        <div class="v2-analytics-section">
            <div class="v2-section-header">
                <div class="v2-icon">◆</div>
                <div class="v2-title">Skills Rarity Analysis</div>
                <div class="v2-badge">V2 Enhanced</div>
            </div>
            <div class="skills-grid">
        '''
        
        for skill in rare_skills[:6]:  # Limit for PDF layout
            rarity_level = "Extremely Rare" if skill.get('rarity_score', 0) >= 90 else \
                          "Very Rare" if skill.get('rarity_score', 0) >= 70 else \
                          "Moderately Rare" if skill.get('rarity_score', 0) >= 50 else "Common"
            
            html += f'''
            <div class="skill-card">
                <div class="skill-name">{skill.get('name', 'Unknown Skill')}</div>
                <div class="skill-rarity">{rarity_level} ({skill.get('rarity_score', 0)}%)</div>
                <div class="skill-description">Market advantage potential</div>
            </div>
            '''
        
        html += '</div></div>'
        return html
    
    def _generate_v2_transition_insights_pdf(self, transition_insights: Dict[str, Any]) -> str:
        """Generate transition insights section for PDF."""
        insights = transition_insights.get('insights', [])
        if not insights:
            return ""
        
        html = '''
        <div class="v2-analytics-section">
            <div class="v2-section-header">
                <div class="v2-icon">💡</div>
                <div class="v2-title">Strategic Transition Insights</div>
                <div class="v2-badge">V2 Enhanced</div>
            </div>
        '''
        
        for insight in insights:
            priority_color = "red" if insight.get('priority') == 'high' else \
                           "orange" if insight.get('priority') == 'medium' else "green"
            
            html += f'''
            <div class="content-paragraph">
                <strong>{insight.get('title', 'Insight')}</strong> 
                <span style="color: {priority_color}; font-weight: bold;">({insight.get('priority', 'medium').upper()} PRIORITY)</span><br>
                {insight.get('description', 'Strategic insight for career transition')}<br>
                <strong>Recommendation:</strong> {insight.get('recommendation', 'Consider strategic approach')}
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _generate_document_footer(self, generated_date: str) -> str:
        """Generate document footer."""
        return f'''
        <div class="document-footer">
            <div>Generated by NAB Skills Intelligence Platform on {generated_date}</div>
            <div>This analysis is based on similarity algorithms and V2 analytics data</div>
            <div>For internal use only - Commercial in Confidence</div>
        </div>
        '''
    
    def _convert_html_to_pdf(self, html_content: str, form_data: Dict) -> Tuple[bytes, str]:
        """Convert HTML content to PDF using weasyprint or reportlab fallback."""
        # Generate filename
        job_from = form_data.get('job_from', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"career_analysis_{job_from}_{timestamp}.pdf"
        
        # Try weasyprint first (better HTML support) - lazy import
        weasyprint_available = _check_weasyprint_availability()
        if weasyprint_available:
            try:
                logger.info("Attempting PDF generation with weasyprint")
                # Import weasyprint here to avoid module-level import issues
                import weasyprint
                pdf_document = weasyprint.HTML(string=html_content)
                pdf_data = pdf_document.write_pdf()
                
                if pdf_data is None:
                    raise ValueError("Weasyprint PDF generation returned None")
                
                print(f"✅ Successfully generated PDF with weasyprint: {filename}")
                return pdf_data, filename
                
            except Exception as e:
                logger.warning(f"Weasyprint failed: {str(e)}. Trying reportlab fallback.")
                # Mark as unavailable for future calls in this session
                global WEASYPRINT_AVAILABLE
                WEASYPRINT_AVAILABLE = False
        
        # Fallback to reportlab (Windows-friendly)
        if REPORTLAB_AVAILABLE:
            try:
                logger.info("Attempting PDF generation with reportlab")
                return self._convert_html_to_pdf_reportlab(html_content, filename, form_data)
                
            except Exception as e:
                logger.error(f"Reportlab PDF generation failed: {str(e)}", exc_info=True)
                raise
        
        # No PDF libraries available
        raise RuntimeError("No PDF generation libraries available. Please install weasyprint or reportlab.")
    
    def _convert_html_to_pdf_reportlab(self, html_content: str, filename: str, form_data: Dict) -> Tuple[bytes, str]:
        """Convert HTML content to PDF using reportlab (Windows-friendly fallback)."""
        import io
        
        # Create a buffer to store the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1e3a8a')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#1e40af'),
            leftIndent=0
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        )
        
        # Parse HTML and convert to PDF elements
        elements = []
        
        # Add title
        job_from = form_data.get('job_from', 'Unknown Position')
        elements.append(Paragraph("Career Transition Analysis", title_style))
        elements.append(Paragraph(f"Strategic Career Intelligence Report", normal_style))
        elements.append(Paragraph(f"Source Role: {job_from}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Simple HTML parsing for basic content
        clean_content = self._extract_text_from_html(html_content)
        
        # Split content into sections and paragraphs
        sections = clean_content.split('\n\n')
        
        for section in sections:
            if section.strip():
                # Check if it looks like a heading
                if len(section.strip()) < 100 and not section.strip().endswith('.'):
                    elements.append(Paragraph(section.strip(), heading_style))
                else:
                    # Regular paragraph
                    elements.append(Paragraph(section.strip(), normal_style))
                elements.append(Spacer(1, 6))
        
        # Add footer
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("Generated by NAB Career Intelligence System", footer_style))
        elements.append(Paragraph("Commercial in Confidence", footer_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        print(f"✅ Successfully generated PDF with reportlab: {filename}")
        return pdf_data, filename
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract text content from HTML for reportlab processing."""
        class HTMLTextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self.in_title = False
                
            def handle_starttag(self, tag, attrs):
                if tag in ['h1', 'h2', 'h3', 'h4']:
                    self.in_title = True
                    self.text_parts.append('\n\n')
                elif tag in ['p', 'div']:
                    self.text_parts.append('\n')
                elif tag == 'br':
                    self.text_parts.append('\n')
                    
            def handle_endtag(self, tag):
                if tag in ['h1', 'h2', 'h3', 'h4']:
                    self.in_title = False
                    self.text_parts.append('\n')
                    
            def handle_data(self, data):
                if data.strip():
                    self.text_parts.append(data.strip())
                    
        extractor = HTMLTextExtractor()
        extractor.feed(html_content)
        return ' '.join(extractor.text_parts)
    
    def _clean_content_for_pdf(self, content: str) -> str:
        """Clean content for PDF generation."""
        if not isinstance(content, str):
            content = str(content)
        
        # Remove or replace problematic characters/formatting
        content = content.replace('\n\n', '</p><p>')
        content = content.replace('\n', '<br>')
        
        # Handle basic formatting
        content = content.replace('**', '<strong>').replace('**', '</strong>')
        content = content.replace('*', '<em>').replace('*', '</em>')
        
        # Wrap in paragraph tags if not already wrapped
        if not content.startswith('<'):
            content = f'<p>{content}</p>'
        
        return content
    
    def _parse_opportunity_header(self, header_string: str) -> Dict[str, str]:
        """Parse opportunity header string into structured data."""
        result = {}
        
        if not header_string:
            return result
        
        lines = header_string.split('\n')
        
        # Parse title from first line
        if lines:
            result['title'] = lines[0].replace('##', '').strip()
        
        # Parse metadata from subsequent lines
        for line in lines:
            if 'Target Role:' in line:
                match = line.split('Target Role:')
                if len(match) > 1:
                    result['targetRole'] = match[1].split('|')[0].strip()
            
            if 'Similarity Score:' in line:
                match = line.split('Similarity Score:')
                if len(match) > 1:
                    result['similarity'] = match[1].split('|')[0].strip()
            
            if 'Move Type:' in line:
                match = line.split('Move Type:')
                if len(match) > 1:
                    result['moveType'] = match[1].strip()
        
        return result
    
    def _get_job_title(self, job_id: str) -> str:
        """Get job title from database."""
        try:
            result = self.db.execute(
                "SELECT JobProfile FROM core_job_architecture WHERE JobProfileID = ?", 
                (job_id,)
            ).fetchone()
            
            if result:
                return result['JobProfile']
            else:
                return f"Job {job_id}"
                
        except Exception as e:
            logger.error(f"Error fetching job title for {job_id}: {e}")
            return f"Job {job_id}"
    
    def _convert_html_to_word(self, html_content: str, form_data: Dict) -> Tuple[bytes, str]:
        """Convert HTML content to Word document."""
        try:
            # Try different HTML-to-Word libraries in order of preference
            return self._convert_html_to_word_python_docx(html_content, form_data)
        except ImportError:
            try:
                return self._convert_html_to_word_mammoth(html_content, form_data)
            except ImportError:
                try:
                    return self._convert_html_to_word_pandoc(html_content, form_data)
                except ImportError:
                    # Fallback to basic text extraction
                    return self._convert_html_to_word_basic(html_content, form_data)
    
    def _convert_html_to_word_python_docx(self, html_content: str, form_data: Dict) -> Tuple[bytes, str]:
        """Convert HTML to Word using python-docx with html parsing."""
        try:
            from docx import Document
            from docx.shared import Inches
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.shared import RGBColor
            from bs4 import BeautifulSoup
            import io
            
        except ImportError:
            raise ImportError("python-docx and beautifulsoup4 are required for Word generation")
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Create new document
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Add title
        title = soup.find('h1')
        if title:
            title_p = doc.add_heading(title.get_text().strip(), level=1)
            title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add subtitle with date
        subtitle = soup.find('p', class_='document-subtitle')
        if subtitle:
            subtitle_p = doc.add_paragraph(subtitle.get_text().strip())
            subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Process main content sections
        sections = soup.find_all(['section', 'div'], class_=['section', 'v2-section'])
        
        for section in sections:
            # Add section heading
            heading = section.find(['h2', 'h3', 'h4'])
            if heading:
                doc.add_heading(heading.get_text().strip(), level=2)
            
            # Add paragraphs
            paragraphs = section.find_all('p')
            for p in paragraphs:
                if not p.get('class') or 'document-subtitle' not in p.get('class', []):
                    text = p.get_text().strip()
                    if text:
                        doc.add_paragraph(text)
            
            # Add lists
            lists = section.find_all(['ul', 'ol'])
            for ul in lists:
                items = ul.find_all('li')
                for li in items:
                    doc.add_paragraph(li.get_text().strip(), style='List Bullet')
            
            # Add tables (simplified)
            tables = section.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                if rows:
                    # Create Word table
                    word_table = doc.add_table(rows=len(rows), cols=len(rows[0].find_all(['td', 'th'])))
                    word_table.style = 'Table Grid'
                    
                    for i, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        for j, cell in enumerate(cells):
                            if i < len(word_table.rows) and j < len(word_table.rows[i].cells):
                                word_table.rows[i].cells[j].text = cell.get_text().strip()
            
            # Add spacing between sections
            doc.add_paragraph('')
        
        # Generate filename
        job_from = form_data.get('job_from', 'unknown')
        job_title = self._get_job_title(job_from).replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"career_analysis_{job_title}_{timestamp}.docx"
        
        # Save to bytes
        doc_buffer = io.BytesIO()
        doc.save(doc_buffer)
        doc_buffer.seek(0)
        
        return doc_buffer.getvalue(), filename
    
    def _convert_html_to_word_mammoth(self, html_content: str, form_data: Dict) -> Tuple[bytes, str]:
        """Convert HTML to Word using mammoth (alternative approach)."""
        try:
            import mammoth
            import tempfile
            import os
        except ImportError:
            raise ImportError("mammoth is required for this Word generation method")
        
        # This is a simplified implementation - mammoth is primarily for reading Word docs
        # For now, we'll use a basic approach
        raise ImportError("mammoth method not fully implemented")
    
    def _convert_html_to_word_pandoc(self, html_content: str, form_data: Dict) -> Tuple[bytes, str]:
        """Convert HTML to Word using pypandoc."""
        try:
            import pypandoc
            import tempfile
            import os
        except ImportError:
            raise ImportError("pypandoc is required for this Word generation method")
        
        # Generate filename
        job_from = form_data.get('job_from', 'unknown')
        job_title = self._get_job_title(job_from).replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"career_analysis_{job_title}_{timestamp}.docx"
        
        # Use pypandoc to convert HTML to docx
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_html:
            temp_html.write(html_content)
            temp_html_path = temp_html.name
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
                temp_docx_path = temp_docx.name
            
            # Convert using pandoc
            pypandoc.convert_file(temp_html_path, 'docx', outputfile=temp_docx_path)
            
            # Read the generated Word document
            with open(temp_docx_path, 'rb') as f:
                docx_data = f.read()
            
            return docx_data, filename
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_html_path)
                os.unlink(temp_docx_path)
            except:
                pass
    
    def _convert_html_to_word_basic(self, html_content: str, form_data: Dict) -> Tuple[bytes, str]:
        """Basic fallback HTML to Word conversion using python-docx only."""
        try:
            from docx import Document
            import io
            import re
        except ImportError:
            raise ImportError("python-docx is required for basic Word generation")
        
        # Create new document
        doc = Document()
        
        # Extract text content from HTML (very basic)
        # Remove HTML tags
        text_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up extra whitespace
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Split into paragraphs (basic heuristic)
        paragraphs = text_content.split('\n\n')
        
        # Add title
        doc.add_heading('Career Transition Analysis Report', level=1)
        
        # Add content paragraphs
        for para in paragraphs:
            para = para.strip()
            if para:
                if len(para) < 100 and para.isupper():
                    # Likely a heading
                    doc.add_heading(para, level=2)
                else:
                    doc.add_paragraph(para)
        
        # Generate filename
        job_from = form_data.get('job_from', 'unknown')
        job_title = self._get_job_title(job_from).replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"career_analysis_{job_title}_{timestamp}.docx"
        
        # Save to bytes
        doc_buffer = io.BytesIO()
        doc.save(doc_buffer)
        doc_buffer.seek(0)
        
        return doc_buffer.getvalue(), filename
