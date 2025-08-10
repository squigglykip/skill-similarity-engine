"""
Document formatting (Word, PDF, PowerPoint) for Career Transition Analysis Generator.
Uses pre-styled NAB Word templates for professional output.
"""

from docx import Document
from docx.shared import RGBColor, Pt, Inches
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from typing import Dict, Any, List, Union, Optional
from pathlib import Path
import logging
import io
import os
import re

# Set DOCX availability constant
DOCX_AVAILABLE = True

# Import NAB styling configuration
try:
    # Try absolute import first (works in Flask context)
    from skill_similarity_engine.webapp.career_analysis.config import DocumentStyles, NABColors, FontSettings, SpacingSettings
    STYLING_AVAILABLE = True
except ImportError:
    try:
        # Fallback to relative import
        from .config import DocumentStyles, NABColors, FontSettings, SpacingSettings
        STYLING_AVAILABLE = True
    except ImportError:
        try:
            # Third fallback for standalone test context
            from config import DocumentStyles, NABColors, FontSettings, SpacingSettings
            STYLING_AVAILABLE = True
        except ImportError:
            # Final fallback if config module is not available
            DocumentStyles = None
            NABColors = None
            FontSettings = None
            SpacingSettings = None
            STYLING_AVAILABLE = False
    
logger = logging.getLogger(__name__)

class ContentFormatter:
    """Structured content formatting helper for document generation."""
    
    @staticmethod
    def create_formatted_content(text: str, formatting: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create structured content with formatting metadata.
        
        Args:
            text: The text content
            formatting: Dictionary with formatting options like:
                - 'bold_labels': List of labels that should be bold
                - 'content_type': 'bullet_list', 'numbered_list', 'paragraph'
                - 'list_style': 'bullet', 'number', 'none'
                - 'bold_patterns': List of regex patterns that should be bold
                - 'indent_level': 0, 1, 2 for indentation
        
        Returns:
            Dict with 'text' and 'formatting' keys
        """
        return {
            'text': text,
            'formatting': formatting or {}
        }
    
    @staticmethod
    def create_bullet_list(items: List[str], bold_labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a bullet list with optional bold labels."""
        text = '\n'.join([f"- {item}" for item in items])
        return ContentFormatter.create_formatted_content(
            text,
            {
                'content_type': 'bullet_list',
                'bold_labels': bold_labels or []
            }
        )
    
    @staticmethod
    def create_numbered_list(items: List[str], bold_headers: bool = False) -> Dict[str, Any]:
        """Create a numbered list with optional bold headers."""
        text = '\n'.join([f"{i+1}. {item}" for i, item in enumerate(items)])
        return ContentFormatter.create_formatted_content(
            text,
            {
                'content_type': 'numbered_list',
                'bold_numbered_headers': bold_headers
            }
        )
    
    @staticmethod
    def create_paragraph(text: str, bold_labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a formatted paragraph with optional bold labels."""
        return ContentFormatter.create_formatted_content(
            text,
            {
                'content_type': 'paragraph',
                'bold_labels': bold_labels or []
            }
        )
    
    @staticmethod
    def create_table(headers: List[str], rows: List[List[str]], table_style: str = 'simple', output_format: str = 'document') -> Dict[str, Any]:
        """Create table with dual output: structured for web, formatted for documents."""
        
        if output_format == 'web':
            # Return structured data for frontend consumption
            return {
                'type': 'structured_table',
                'headers': headers,
                'rows': rows,
                'metadata': {
                    'table_style': table_style,
                    'column_count': len(headers),
                    'row_count': len(rows)
                }
            }
        else:
            # Existing document generation logic
            table_text = " | ".join(headers) + "\n"
            table_text += "|".join(["-" * len(header) for header in headers]) + "\n"
            for row in rows:
                table_text += " | ".join(str(cell) for cell in row) + "\n"
            
            return ContentFormatter.create_formatted_content(
                table_text,
                {
                    'content_type': 'table',
                    'table_style': table_style,
                    'headers': headers,
                    'rows': rows
                }
            )
    
    @staticmethod
    def create_skills_analysis_table(skill_categories: List[Dict], total_skills: int, skills_overlap_job_count: int) -> Dict[str, Any]:
        """Create a Skills Analysis Table with SkillType grouping for Current Role Context section."""
        
        # Headers for the Skills Analysis Table (removed Demand Level)
        headers = ['Skill Type', 'Skill Count', 'All Skills']
        
        # Build rows from skill categories (now grouped by SkillType)
        rows = []
        for category in skill_categories:
            skill_type = category.get('name', 'Other')
            skill_count = category.get('skill_count', 0)
            skill_list = category.get('skill_list', '')
            
            # No truncation - show ALL skills
            rows.append([
                skill_type,
                str(skill_count),
                skill_list  # Full skill list without truncation
            ])
        
        return ContentFormatter.create_table(
            headers=headers,
            rows=rows,
            table_style='compact'  # Use compact styling for better real estate
        )

    @staticmethod
    def create_pathway_comparison_table(pathways: List[Dict]) -> Dict[str, Any]:
        """Create a Career Pathway Comparison Table for Executive Summary."""
        
        # Headers for the Career Pathway Comparison Table
        headers = ['Rank', 'Target Role', 'Similarity', 'Move Type', 'Management Level', 'Strategic Context']
        
        # Build rows from pathway data
        rows = []
        for i, pathway in enumerate(pathways, 1):
            target_role = pathway.get('target_logical_role', 'Unknown Role')
            similarity = f"{pathway.get('similarity_score', 0)}%"
            move_type = pathway.get('move_type', 'Unknown')
            
            # Extract management level progression
            source_level = pathway.get('source_management_level', 'Unknown')
            target_level = pathway.get('target_management_level', 'Unknown')
            if source_level != 'Unknown' and target_level != 'Unknown':
                if source_level == target_level:
                    level_progression = source_level
                else:
                    level_progression = f"{source_level} â†’ {target_level}"
            else:
                level_progression = target_level
            
            # Get strategic context (truncate if too long for table)
            strategic_context = pathway.get('strategic_context_explanation', 'Strategic transition opportunity')
            if len(strategic_context) > 80:
                strategic_context = strategic_context[:77] + '...'
            
            rows.append([
                str(i),                # Rank
                target_role,           # Target Role
                similarity,            # Similarity %
                move_type,            # Move Type
                level_progression,    # Management Level
                strategic_context     # Strategic Context
            ])
        
        return ContentFormatter.create_table(
            headers=headers,
            rows=rows,
            table_style='compact'  # Use compact styling for better real estate
        )

    @staticmethod
    def create_strategic_metrics_table(metrics: Dict) -> Dict[str, Any]:
        """Create a Strategic Intelligence Metrics Table for Current Role Context."""
        
        # Headers for the Strategic Intelligence Metrics Table
        headers = ['Metric', 'Score', 'Assessment', 'Strategic Significance']
        
        # Build rows from metrics data
        rows = []
        
        # Mobility Hub Score
        mobility_score = f"{metrics.get('mobility_hub_score', 0)}%"
        mobility_assessment = metrics.get('mobility_hub_assessment', 'Medium Hub Potential')
        mobility_description = metrics.get('mobility_strategic_value', 'Medium connectivity within career pathway network')
        rows.append(['Mobility Hub Score', mobility_score, mobility_assessment, mobility_description])
        
        # Transition Readiness
        readiness_score = f"{metrics.get('transition_readiness', 0)}%"
        readiness_assessment = metrics.get('transition_readiness_assessment', 'Medium Readiness')
        readiness_description = metrics.get('transition_investment_descriptor', 'Moderate investment requirements for transitions')
        rows.append(['Transition Readiness', readiness_score, readiness_assessment, readiness_description])
        
        # Cross-Family Reach
        reach_count = str(metrics.get('cross_family_reach', 0))
        reach_assessment = metrics.get('cross_family_diversity_assessment', 'Moderate Diversity')
        reach_description = metrics.get('organisational_agility_descriptor', 'Cross-functional capability potential')
        rows.append(['Cross-Family Reach', f"{reach_count} functions", reach_assessment, reach_description])
        
        # Strategic Value
        value_score = metrics.get('strategic_value_assessment', 'MEDIUM')
        value_assessment = metrics.get('strategic_value_descriptor', 'Valuable Position')
        value_description = metrics.get('workforce_planning_priority', 'Strategic workforce planning asset')
        rows.append(['Strategic Value', value_score, value_assessment, value_description])
        
        return ContentFormatter.create_table(
            headers=headers,
            rows=rows,
            table_style='compact'  # Use compact styling for better real estate
        )

class DocumentFormatter:
    """Enhanced document formatter with NAB professional styling."""
    
    def __init__(self, template_path=None):
        """Initialize the formatter with optional template path."""
        self.template_path = template_path
        # Initialize NAB styling system
        if STYLING_AVAILABLE and DocumentStyles:
            self.nab_styles = DocumentStyles()
            print("✅ NAB styling system initialized")
        else:
            self.nab_styles = None
            logger.warning("⚠️ NAB styling not available, using basic styles")
    
    def format_document(self, content: Dict, output_format: str, analysis_data: Dict) -> Dict:
        """Format content into requested document format."""
        
        if output_format == 'word':
            return self._format_word_document(content, analysis_data)
        elif output_format == 'powerpoint':
            return self._format_powerpoint_summary(content, analysis_data)
        elif output_format == 'pdf':
            return self._format_pdf_document(content, analysis_data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _format_word_document(self, content: Dict, analysis_data: Dict) -> Dict:
        """Create Word document with professional NAB styling."""
        try:
            print("Creating document from scratch with NAB styling")
            
            # Create new document
            doc = Document()
            
            # Get job name for document
            job_name = analysis_data.get('source_job_logical_display_name', 'Professional Role')
            
            # Log styling system status
            print(f"🔍 STYLING_AVAILABLE: {STYLING_AVAILABLE}")
            print(f"🔍 DocumentStyles available: {DocumentStyles is not None}")
            print(f"🔍 self.nab_styles: {self.nab_styles is not None}")
            
            # Use professional NAB styling if available
            if self.nab_styles:
                print("🎨 Applying professional NAB styling")
                
                # Setup document styles
                self.nab_styles.setup_document_styles(doc)
                print("✅ Professional document styles setup completed")
                
                # Create professional title page
                self.nab_styles.create_title_page(doc, analysis_data)
                print("✅ Professional title page created")
                
                # Add page break after title page
                doc.add_page_break()
                
                # Add professional table of contents
                self.nab_styles.add_table_of_contents(doc)
                print("✅ Professional table of contents added")
                
                # Add page break after TOC
                doc.add_page_break()
                
                # Process content sections with professional styling
                self._create_professional_content(doc, content, analysis_data, job_name)
                print("✅ Professional content sections created")
                
            else:
                logger.warning("🎨 Using basic styling (NAB styles not available)")
                logger.warning(f"🔍 Reason: STYLING_AVAILABLE={STYLING_AVAILABLE}, DocumentStyles={DocumentStyles is not None}")
                # Fallback to basic styling
                self._setup_nab_styles(doc)
                logger.debug("✅ NAB styles setup completed successfully")
                
                try:
                    self._create_nab_document(doc, content, analysis_data, job_name)
                    logger.debug("✅ NAB document creation completed successfully")
                except Exception as doc_error:
                    logger.error(f"❌ Error in _create_nab_document: {doc_error}")
                    logger.error(f"❌ Error type: {type(doc_error)}")
                    logger.error(f"❌ Content type passed: {type(content)}")
                    logger.error(f"❌ Analysis_data type passed: {type(analysis_data)}")
                    raise doc_error
            
            # Set up page margins (Normal Word margins: 2.54cm all around)
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(1.0)      # 2.54cm = 1.0 inch
                section.bottom_margin = Inches(1.0)   # 2.54cm = 1.0 inch  
                section.left_margin = Inches(1.0)     # 2.54cm = 1.0 inch
                section.right_margin = Inches(1.0)    # 2.54cm = 1.0 inch
            
            # Save to memory buffer
            buffer = io.BytesIO()
            doc.save(buffer)  # type: ignore
            buffer.seek(0)  # type: ignore
            content_bytes = buffer.getvalue()  # type: ignore
            
            # Use enhanced filename from analysis_data if available
            filename = analysis_data.get('enhanced_filename', f'career_analysis_{job_name.replace(" ", "_").replace("(", "").replace(")", "")}.docx')
            
            return {
                'format': 'word',
                'filename': filename,
                'content': content_bytes,
                'status': 'generated'
            }
            
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            return {
                'format': 'word',
                'filename': 'career_analysis_error.docx',
                'content': content,
                'status': 'error',
                'message': str(e)
            }
    
    def _setup_nab_styles(self, doc):
        """Set up comprehensive NAB styling system for professional documents."""
        print("🎨 Applying professional NAB styling")
        
        # Import NAB styling configuration
        if STYLING_AVAILABLE and DocumentStyles:
            try:
                self.nab_styles = DocumentStyles()
                print("✅ NAB styling system initialized")
                
                # FIX 3: Apply complete NAB styling to document
                self._apply_comprehensive_nab_styling(doc)
                
            except Exception as e:
                logger.error(f"❌ Error initializing NAB styles: {e}")
                self.nab_styles = None
        else:
            logger.warning("⚠️ NAB styling not available - using basic formatting")
            self.nab_styles = None
    
    def _apply_comprehensive_nab_styling(self, doc):
        """Apply comprehensive NAB styling including colors, fonts, and table styles."""
        logger.debug("🎨 Applying comprehensive NAB styling to document")
        
        # FIX 3: Set up complete NAB document styles
        styles = doc.styles
        
        # NAB Corporate Colors (based on DocumentStyles configuration)
        nab_red = RGBColor(204, 0, 51)      # NAB Corporate Red  
        nab_dark_grey = RGBColor(64, 64, 64)  # NAB Dark Grey
        nab_light_grey = RGBColor(128, 128, 128)  # NAB Light Grey
        nab_black = RGBColor(0, 0, 0)       # NAB Black
        
        # FIX 3: Create/update NAB Heading 1 style
        try:
            heading1_style = styles['Heading 1']
        except KeyError:
            heading1_style = styles.add_style('Heading 1', WD_STYLE_TYPE.PARAGRAPH)
        
        heading1_style.font.name = 'Source Sans Pro'
        heading1_style.font.size = Pt(18)
        heading1_style.font.bold = True
        heading1_style.font.color.rgb = nab_red  # NAB Red for headings
        heading1_style.paragraph_format.space_before = Pt(18)
        heading1_style.paragraph_format.space_after = Pt(12)
        heading1_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
        # FIX 3: Create/update NAB Heading 2 style  
        try:
            heading2_style = styles['Heading 2']
        except KeyError:
            heading2_style = styles.add_style('Heading 2', WD_STYLE_TYPE.PARAGRAPH)
            
        heading2_style.font.name = 'Source Sans Pro'
        heading2_style.font.size = Pt(14)
        heading2_style.font.bold = True
        heading2_style.font.color.rgb = nab_dark_grey  # NAB Dark Grey for subheadings
        heading2_style.paragraph_format.space_before = Pt(12)
        heading2_style.paragraph_format.space_after = Pt(6)
        heading2_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
        # FIX 3: Create/update NAB Body style
        try:
            body_style = styles['NAB Body']
        except KeyError:
            body_style = styles.add_style('NAB Body', WD_STYLE_TYPE.PARAGRAPH)
            
        body_style.font.name = 'Source Sans Pro'
        body_style.font.size = Pt(11)
        body_style.font.color.rgb = nab_black  # NAB Black for body text
        body_style.paragraph_format.space_before = Pt(0)
        body_style.paragraph_format.space_after = Pt(6)
        body_style.paragraph_format.line_spacing = 1.15  # NAB standard line spacing
        body_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        # FIX 3: Create/update NAB Table style
        try:
            table_style = styles['NAB Table']
        except KeyError:
            table_style = styles.add_style('NAB Table', WD_STYLE_TYPE.TABLE)
            
        # Apply NAB table styling
        table_style.font.name = 'Source Sans Pro'
        table_style.font.size = Pt(10)
        
        logger.debug("✅ Comprehensive NAB styling applied to document")
    
    def _add_yaml_content_type(self, doc, subsection: Dict):
        """
        Process content based on YAML template content_type specifications.
        
        Handles content_type: table, paragraph, mixed, etc. from YAML templates
        including table_headers, table_data, bold_labels specifications.
        This method now handles ALL content processing to avoid duplication.
        """
        content_type = subsection.get('content_type', 'paragraph')
        
        if content_type == 'table':
            # Handle table content type with table_headers and table_data
            self._add_yaml_table_content(doc, subsection)
        elif content_type == 'mixed':
            # Handle mixed content with bold labels
            self._add_yaml_mixed_content(doc, subsection)
        elif content_type == 'paragraph':
            # Handle paragraph content using NAB styling
            content = subsection.get('content', '')
            bold_labels = subsection.get('bold_labels', [])
            if content:
                if hasattr(self, 'nab_styles') and self.nab_styles:
                    if bold_labels:
                        # Handle paragraph with bold labels using NAB styling
                        self._add_nab_styled_content_with_bold_labels(doc, content, bold_labels)
                    else:
                        self.nab_styles.add_formatted_content_with_style(doc, content)
                else:
                    self._add_legacy_string_content(doc, content)
        else:
            # Fallback for unknown content types using NAB styling
            content = subsection.get('content', '')
            if content:
                if hasattr(self, 'nab_styles') and self.nab_styles:
                    self.nab_styles.add_formatted_content_with_style(doc, content)
                else:
                    self._add_legacy_string_content(doc, content)
        
        # ALSO handle the 'content' field if it exists and is structured (dict) 
        # This covers cases where subsections have both content_type and a structured content field
        if 'content' in subsection:
            content_field = subsection['content']
            if isinstance(content_field, dict):
                # Handle structured content (like from pathway analysis opportunities)
                self._add_structured_content_with_nab_styling(doc, content_field)
            elif isinstance(content_field, str) and content_type == 'paragraph':
                # String content was already handled above for paragraph type
                pass
            elif isinstance(content_field, str):
                # Handle string content with table detection for other content types
                if hasattr(self, 'nab_styles') and self.nab_styles:
                    if hasattr(self.nab_styles, 'detect_and_format_pipe_delimited_tables'):
                        tables_found = self.nab_styles.detect_and_format_pipe_delimited_tables(doc, content_field)
                        if not tables_found:
                            # No tables found, add as regular formatted content
                            self.nab_styles.add_formatted_content_with_style(doc, content_field)
                    else:
                        # Fallback: regular formatted content
                        self.nab_styles.add_formatted_content_with_style(doc, content_field)
                else:
                    self._add_legacy_string_content(doc, content_field)
    
    def _add_yaml_table_content(self, doc, subsection: Dict):
        """Handle table content_type from YAML templates with NAB styling."""
        table_headers = subsection.get('table_headers', [])
        table_data = subsection.get('table_data', '')
        
        if not table_headers or not table_data:
            logger.warning("⚠️ Missing table_headers or table_data for table content_type")
            return
        
        # Parse table_data (pipe-delimited format from YAML)
        rows = []
        for line in table_data.strip().split('\n'):
            if line.strip():
                row = [cell.strip() for cell in line.split('|')]
                if len(row) == len(table_headers):
                    rows.append(row)
        
        if rows:
            # Create table using proper NAB styling system
            table = doc.add_table(rows=len(rows) + 1, cols=len(table_headers))
            # DON'T apply built-in table style yet - it will override our black headers
            # table.style = 'Light Grid Accent 1'  # Commented out to prevent header override
            
            # Use NAB color system
            nab_red = self.nab_styles.colors.get_rgb_color('nab_red') if self.nab_styles else RGBColor(204, 0, 51)
            nab_black = self.nab_styles.colors.get_rgb_color('nab_black') if self.nab_styles else RGBColor(0, 0, 0)
            nab_white = self.nab_styles.colors.get_rgb_color('white') if self.nab_styles else RGBColor(255, 255, 255)
            
            # Add headers with NAB styling
            header_cells = table.rows[0].cells
            for i, header in enumerate(table_headers):
                header_cells[i].text = header
                
                # Set BLACK background for header cell (NAB Table Design 2)
                try:
                    from docx.oxml.ns import qn
                    cell_shading = header_cells[i]._element.get_or_add_tcPr().get_or_add_shd()
                    cell_shading.set(qn('w:fill'), "000000")  # Black background
                    cell_shading.set(qn('w:val'), "clear")
                except:
                    # If shading fails, continue with text styling
                    pass
                
                # Apply NAB table header styling
                for paragraph in header_cells[i].paragraphs:
                    paragraph.style = doc.styles['NAB Body']
                    for run in paragraph.runs:
                        run.font.bold = True
                        run.font.name = self.nab_styles.fonts.FONT_PRIMARY if self.nab_styles else 'Source Sans Pro'
                        run.font.size = self.nab_styles.fonts.get_pt_size('table_header') if self.nab_styles else Pt(11)
                        run.font.color.rgb = nab_white  # White text on dark header
            
            # Add data rows with NAB styling and banded rows
            for row_idx, row_data in enumerate(rows, 1):
                row_cells = table.rows[row_idx].cells
                
                # Apply alternating row banding for NAB Table Design 2
                if (row_idx - 1) % 2 == 1:  # Every other row gets light grey
                    for cell in row_cells:
                        try:
                            from docx.oxml.ns import qn
                            cell_shading = cell._element.get_or_add_tcPr().get_or_add_shd()
                            cell_shading.set(qn('w:fill'), "F5F5F5")  # Light grey
                            cell_shading.set(qn('w:val'), "clear")
                        except:
                            # If shading fails, continue without banding
                            pass
                
                for col_idx, cell_data in enumerate(row_data):
                    row_cells[col_idx].text = cell_data
                    # Apply NAB body styling to table cells
                    for paragraph in row_cells[col_idx].paragraphs:
                        paragraph.style = doc.styles['NAB Body']
                        for run in paragraph.runs:
                            run.font.name = self.nab_styles.fonts.FONT_PRIMARY if self.nab_styles else 'Source Sans Pro'
                            run.font.size = self.nab_styles.fonts.get_pt_size('body') if self.nab_styles else Pt(11)
                            run.font.color.rgb = nab_black
    
    def _add_nab_styled_content_with_bold_labels(self, doc, content: str, bold_labels: list):
        """Handle content with bold labels using proper NAB styling."""
        if not content:
            return
            
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        for para_text in paragraphs:
            if para_text.strip():
                para = doc.add_paragraph()
                para.style = doc.styles['NAB Body']
                
                # Process bold labels in the text
                remaining_text = para_text.strip()
                
                for label in bold_labels:
                    if label in remaining_text:
                        # Split at the first occurrence of the label
                        parts = remaining_text.split(label, 1)
                        if len(parts) == 2:
                            # Add text before label
                            if parts[0]:
                                para.add_run(parts[0])
                            # Add bold label with NAB styling
                            bold_run = para.add_run(label)
                            bold_run.bold = True
                            # Continue with remaining text
                            remaining_text = parts[1]
                        else:
                            break
                
                # Add any remaining text
                if remaining_text:
                    para.add_run(remaining_text)

    def _add_yaml_mixed_content(self, doc, subsection: Dict):
        """Handle mixed content_type with bold_labels from YAML templates using proper NAB styling."""
        content = subsection.get('content', '')
        bold_labels = subsection.get('bold_labels', [])
        
        if content:
            # Use the new NAB styled content method
            if hasattr(self, 'nab_styles') and self.nab_styles:
                if bold_labels:
                    self._add_nab_styled_content_with_bold_labels(doc, content, bold_labels)
                else:
                    self.nab_styles.add_formatted_content_with_style(doc, content)
            else:
                # Fallback to legacy styling if NAB styles not available
                self._add_legacy_mixed_content(doc, content, bold_labels)
    
    def _add_structured_content_with_nab_styling(self, doc, content: dict):
        """Add structured content using proper NAB styling instead of old blue/Epilogue styling."""
        if not content:
            return
            
        # Handle different content types with NAB styling
        content_type = content.get('content_type', 'paragraph')
        
        if content_type == 'table':
            # Use existing NAB table styling
            self._add_yaml_table_content(doc, content)
        elif content_type in ['bullet_list', 'bullets']:
            # Handle bullet lists with NAB styling
            items = content.get('items', [])
            if items:
                for item in items:
                    para = doc.add_paragraph(style='NAB Body')
                    para.add_run(f"• {item}")
        elif content_type == 'numbered_list':
            # Handle numbered lists with NAB styling
            items = content.get('items', [])
            if items:
                for i, item in enumerate(items, 1):
                    para = doc.add_paragraph(style='NAB Body')
                    para.add_run(f"{i}. {item}")
        else:
            # Handle as text content with NAB styling and pipe-delimited table detection
            text_content = content.get('text', content.get('content', ''))
            if text_content:
                if hasattr(self, 'nab_styles') and self.nab_styles:
                    # Try to detect and format pipe-delimited tables first
                    if hasattr(self.nab_styles, 'detect_and_format_pipe_delimited_tables'):
                        tables_found = self.nab_styles.detect_and_format_pipe_delimited_tables(doc, text_content)
                        if not tables_found and hasattr(self.nab_styles, 'add_formatted_content_with_style'):
                            # No tables found, add as regular formatted content
                            self.nab_styles.add_formatted_content_with_style(doc, text_content)
                    elif hasattr(self.nab_styles, 'add_formatted_content_with_style'):
                        # Fallback: regular formatted content
                        self.nab_styles.add_formatted_content_with_style(doc, text_content)
                else:
                    # Fallback if NAB styles not available
                    para = doc.add_paragraph(style='NAB Body')
                    para.add_run(text_content)

    def _add_legacy_mixed_content(self, doc, content: str, bold_labels: list):
        """Legacy fallback method for mixed content when NAB styles aren't available."""
        # NAB Corporate Colors (fallback)
        nab_black = RGBColor(0, 0, 0)
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        for para_text in paragraphs:
            if para_text.strip():
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                
                # Apply bold labels if specified
                if bold_labels:
                    for label in bold_labels:
                        if label in para_text:
                            # Split text at the label and apply bold formatting
                            parts = para_text.split(label, 1)
                            if len(parts) == 2:
                                # Add text before label
                                if parts[0]:
                                    run = para.add_run(parts[0])
                                    run.font.name = 'Source Sans Pro'
                                    run.font.size = Pt(11)
                                    run.font.color.rgb = nab_black
                                # Add bold label
                                bold_run = para.add_run(label)
                                bold_run.bold = True
                                bold_run.font.name = 'Source Sans Pro'
                                bold_run.font.size = Pt(11)
                                bold_run.font.color.rgb = nab_black
                                # Add text after label
                                if parts[1]:
                                    run = para.add_run(parts[1])
                                    run.font.name = 'Source Sans Pro'
                                    run.font.size = Pt(11)
                                    run.font.color.rgb = nab_black
                                break
                    else:
                        # No bold labels found, add regular text
                        run = para.add_run(para_text.strip())
                        run.font.name = 'Source Sans Pro'
                        run.font.size = Pt(11)
                        run.font.color.rgb = nab_black
                else:
                    # No bold labels specified, add regular text
                    run = para.add_run(para_text.strip())
                    run.font.name = 'Source Sans Pro'
                    run.font.size = Pt(11)
                    run.font.color.rgb = nab_black
    
    def _create_professional_content(self, doc, content: Dict, analysis_data: Dict, job_name: str):
        """Create professional content sections using NAB styling system."""
        
        if not self.nab_styles:
            logger.error("❌ NAB styling system not available for professional content")
            # Fallback to basic document creation
            self._create_nab_document(doc, content, analysis_data, job_name)
            return
            
        logger.debug(f"🎨 Creating professional content for job: {job_name}")
        logger.debug(f"📄 Content sections available: {list(content.keys())}")
        
        # Define section order and titles
        section_order = [
            ('executive_summary', 'Executive Summary'),
            ('current_role_context', 'Current Role Context'),
            ('pathway_analysis', 'Pathway Analysis: Top 3 Strategic Opportunities'),
            ('strategic_recommendations', 'Strategic Recommendations'),
            ('conclusion', 'Conclusion')
        ]
        
        for i, (section_key, section_title) in enumerate(section_order):
            logger.debug(f"🔍 Processing section {i+1}: {section_key} -> {section_title}")
            
            if section_key in content:
                section_content = content[section_key]
                logger.debug(f"✅ Section {section_key} found, type: {type(section_content)}")
                
                # Add section heading using NAB styling
                self.nab_styles.add_section_heading(doc, section_title, level=1)
                
                # Process section content
                if isinstance(section_content, dict):
                    self._add_professional_section_content(doc, section_content)
                elif isinstance(section_content, str):
                    # Simple string content
                    self.nab_styles.add_formatted_content_with_style(doc, section_content)
                else:
                    logger.warning(f"⚠️ Unexpected section content type for {section_key}: {type(section_content)}")
                
                # Add page break after each section except the last one
                if i < len(section_order) - 1:
                    doc.add_page_break()
            else:
                logger.warning(f"❌ Section {section_key} not found in content")
    
    def _add_professional_section_content(self, doc, section_content: Dict):
        """Add section content using professional NAB styling."""
        
        if not self.nab_styles:
            logger.error("❌ NAB styling system not available for section content")
            return
            
        try:
            # Handle opportunities section specially (for pathway analysis)
            if 'opportunities' in section_content:
                opportunities = section_content.get('opportunities', [])
                logger.debug(f"🎯 Processing {len(opportunities)} opportunities for Word document")
                
                for i, opportunity in enumerate(opportunities, 1):
                    if isinstance(opportunity, dict):
                        logger.debug(f"🔹 Processing opportunity {i}: {list(opportunity.keys())}")
                        
                        # Add opportunity main heading from header if available
                        if 'header' in opportunity:
                            # Parse the header to extract the opportunity title
                            header_lines = opportunity['header'].split('\n')
                            if header_lines:
                                # Extract title from the first line (remove ## prefix)
                                opp_title = header_lines[0].replace('##', '').strip()
                                self.nab_styles.add_section_heading(doc, opp_title, level=2)
                                
                                # Add the metadata lines as a formatted paragraph
                                if len(header_lines) > 1:
                                    metadata_text = '\n'.join(header_lines[1:]).strip()
                                    if metadata_text:
                                        self.nab_styles.add_formatted_content_with_style(doc, metadata_text)
                        else:
                            # Fallback title
                            self.nab_styles.add_section_heading(doc, f"Strategic Opportunity {i}", level=2)
                        
                        # Process each subsection of the opportunity
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
                                if isinstance(subsection, dict):
                                    # Add subsection heading
                                    subsection_title = subsection.get('title', subsection_key.replace('_', ' ').title())
                                    self.nab_styles.add_section_heading(doc, subsection_title, level=3)
                                    
                                    # Process content based on content_type (YAML template specification)
                                    # This method now handles all content processing to avoid duplication
                                    self._add_yaml_content_type(doc, subsection)
                                else:
                                    logger.warning(f"⚠️ Subsection {subsection_key} is not a dict: {type(subsection)}")
                        
                        # Add spacing between opportunities (but not after the last one)
                        if i < len(opportunities):
                            doc.add_paragraph()
                            
                    else:
                        logger.warning(f"⚠️ Opportunity {i} is not a dict: {type(opportunity)}")
                        
            else:
                # Handle regular subsections
                for key, subsection in section_content.items():
                    logger.debug(f"🔹 Processing subsection: {key}")
                    
                    if isinstance(subsection, dict):
                        if 'title' in subsection and 'content' in subsection:
                            # Add subsection heading
                            self.nab_styles.add_section_heading(doc, subsection['title'], level=2)
                            # Add content using professional styling
                            self.nab_styles.add_formatted_content_with_style(doc, subsection['content'])
                        else:
                            logger.warning(f"⚠️ Subsection {key} missing title or content")
                    elif isinstance(subsection, str):
                        # String subsection - add as content with generated title
                        title = key.replace('_', ' ').title()
                        self.nab_styles.add_section_heading(doc, title, level=2)
                        self.nab_styles.add_formatted_content_with_style(doc, subsection)
                    else:
                        logger.warning(f"⚠️ Unexpected subsection type for {key}: {type(subsection)}")
                        
        except Exception as section_error:
            logger.error(f"❌ Error processing professional section content: {section_error}")
            logger.error(f"❌ Section content: {section_content}")
            raise section_error
    
    def _create_nab_document(self, doc, content, analysis_data, job_name):
        """Create the main NAB document content"""
        
        logger.debug(f"🔍 _create_nab_document called with:")
        logger.debug(f"   - content type: {type(content)}")
        logger.debug(f"   - analysis_data type: {type(analysis_data)}")
        logger.debug(f"   - job_name: {job_name}")
        
        if isinstance(content, dict):
            logger.debug(f"   - content keys: {list(content.keys())}")
        if isinstance(analysis_data, dict):
            logger.debug(f"   - analysis_data keys: {list(analysis_data.keys())}")
            
        # Document header - ensure we have at least one paragraph
        if not doc.paragraphs:
            doc.add_paragraph()  # Add initial paragraph if none exists
        header_para = doc.paragraphs[0]
        header_para.clear()  # Clear any default content
        
        # Add title page
        title = doc.add_paragraph('Career Transition Analysis')
        title.style = 'Heading 1'  # Use built-in style instead of 'NAB Document Title'
        
        # Add job information
        job_info = doc.add_paragraph(f'Source Role: {job_name}')
        job_info.style = 'NAB Body'
        
        # Add generated date
        from datetime import datetime
        date_para = doc.add_paragraph(f'Generated: {datetime.now().strftime("%d %B %Y")}')
        date_para.style = 'NAB Body'
        
        # Add spacing
        doc.add_paragraph()
        
        # Table of Contents placeholder (would be filled by Word)
        toc_heading = doc.add_paragraph('Table of Contents')
        toc_heading.style = 'Heading 1'  # Use built-in style instead of 'NAB Heading 1'
        
        toc_placeholder = doc.add_paragraph("[Table of Contents will be generated here]")
        toc_placeholder.style = 'NAB Body'
        doc.add_paragraph()
        
        doc.add_page_break()
        
        # Add content sections using dynamic titles if available
        section_order = analysis_data.get('section_titles', [
            ('executive_summary', 'Executive Summary'),
            ('current_role_context', 'Current Role Context'),
            ('pathway_analysis', 'Pathway Analysis: Top 3 Strategic Opportunities'),
            ('strategic_recommendations', 'Strategic Recommendations'),
            ('conclusion', 'Conclusion')
        ])
        
        logger.debug(f"section_order: {section_order}")
        
        for i, (section_key, section_title) in enumerate(section_order):
            logger.debug(f"Processing section {i}: {section_key} -> {section_title}")
            if section_key in content:
                logger.debug(f"Section {section_key} found in content")
                section_content = content[section_key]
                logger.debug(f"Section content type: {type(section_content)}")
                logger.debug(f"Section content: {section_content}")
                
                # Add page break before each section (except the first one)
                if i > 0:
                    doc.add_page_break()
                self._add_nab_section(doc, section_title, section_content)
            else:
                logger.warning(f"Section {section_key} not found in content. Available keys: {list(content.keys())}")
    
    def _add_nab_section(self, doc, section_title: str, section_content: Dict):
        """
        Add a section with NAB styling and enhanced YAML processing.
        
        Args:
            doc: Document object
            section_title: Title for the section
            section_content: Section content with metadata
        """
        logger.debug(f"🔹 Adding NAB section: {section_title}")
        
        # Add section heading using proper NAB styling
        heading = doc.add_heading(section_title, level=1)
        if hasattr(self, 'nab_styles') and self.nab_styles:
            # Apply professional NAB heading style
            for run in heading.runs:
                run.font.name = 'Source Sans Pro'
                run.font.size = Pt(18)
                run.font.bold = True
                run.font.color.rgb = RGBColor(204, 0, 51)  # NAB Red
        
        # FIX 2 & 3: Process content with enhanced YAML support and NAB styling
        content = section_content.get('content', '')
        content_type = section_content.get('content_type', 'text')
        
        # Enhanced content processing with YAML template support
        if content_type == 'yaml_content_type':
            self._add_yaml_content_type(doc, section_content)
        elif content_type == 'yaml_table_content':
            self._add_yaml_table_content(doc, section_content)
        elif content_type == 'yaml_mixed_content':
            self._add_yaml_mixed_content(doc, section_content)
        elif isinstance(content, str):
            if content.strip():
                self._add_nab_content(doc, content)
        elif isinstance(content, dict):
            # Handle structured content
            if 'opportunities' in content:
                opportunities = content['opportunities']
                logger.debug(f"🎯 Processing {len(opportunities)} opportunities")
                for i, opportunity in enumerate(opportunities, 1):
                    self._add_nab_opportunity(doc, opportunity, i)
            else:
                # Generic dict content processing
                self._add_nab_content(doc, content)
        elif isinstance(content, list):
            # Handle list content
            self._add_nab_content(doc, content)
        else:
            logger.warning(f"⚠️ Unknown content type for section {section_title}: {type(content)}")
        
        # Add section break
        doc.add_paragraph()  # Professional section spacing
    
    def _add_nab_opportunity(self, doc, opportunity: Dict, opportunity_num: int):
        """Add pathway opportunity using NAB styles with enhanced headers."""
        
        logger.debug(f"_add_nab_opportunity called with opportunity_num: {opportunity_num}")
        logger.debug(f"opportunity type: {type(opportunity)}")
        logger.debug(f"opportunity: {opportunity}")
        
        if not isinstance(opportunity, dict):
            logger.error(f"❌ Expected dict for opportunity, got {type(opportunity)}")
            logger.error(f"❌ opportunity content: {opportunity}")
            # Try to convert to dict or handle as string
            if isinstance(opportunity, str):
                para = doc.add_paragraph(f"{opportunity_num}. {opportunity}")
                para.style = 'NAB Body'
                return
            else:
                logger.error(f"❌ Cannot process opportunity of type {type(opportunity)}")
                return
        
        try:
            # Use the enhanced header from pathway analysis, fallback to simple title
            if 'header' in opportunity:
                # New enhanced header format with detailed opportunity information
                header_content = opportunity.get('header', '')
                logger.debug(f"Processing header content: {header_content[:100]}...")
                # Split header into lines and format appropriately
                header_lines = header_content.strip().split('\n')
                
                for i, line in enumerate(header_lines):
                    line = line.strip()
                    if not line:
                        continue
                        
                    if i == 0 and line.startswith('##'):
                        # Main opportunity heading (remove ## and use as Heading 2)
                        heading_text = line.replace('##', '').strip()
                        opp_heading = doc.add_paragraph(heading_text)
                        opp_heading.style = 'Heading 2'
                    elif line.startswith('**') and line.endswith('**'):
                        # Bold formatted line (like **Target Role**: ...)
                        para = doc.add_paragraph()
                        para.style = 'NAB Body'
                        
                        # Parse bold label and content
                        clean_line = line.replace('**', '')
                        if ':' in clean_line:
                            label, content = clean_line.split(':', 1)
                            label_run = para.add_run(f"{label.strip()}: ")
                            label_run.bold = True
                            para.add_run(content.strip())
                        else:
                            full_run = para.add_run(clean_line)
                            full_run.bold = True
                    else:
                        # Regular line
                        para = doc.add_paragraph(line)
                        para.style = 'NAB Body'
            else:
                # Fallback to legacy format
                opp_title = opportunity.get('title', f'Opportunity {opportunity_num}')
                logger.debug(f"Using fallback title: {opp_title}")
                opp_heading = doc.add_paragraph(f"{opportunity_num}. {opp_title}")
                opp_heading.style = 'Heading 2'
            
            # Add opportunity details (skip the header field since we already processed it)
            for detail_key, detail_content in opportunity.items():
                logger.debug(f"Processing opportunity detail: {detail_key}, type: {type(detail_content)}")
                
                if detail_key not in ['title', 'header']:
                    if isinstance(detail_content, dict):
                        logger.debug(f"Processing dict detail: {detail_key}")
                        if 'title' in detail_content:
                            # Detail subheading using Word's built-in Heading 3 (modified with NAB styling)
                            detail_heading = doc.add_paragraph(detail_content['title'])
                            detail_heading.style = 'Heading 3'
                        
                        if 'content' in detail_content:
                            self._add_nab_content(doc, detail_content['content'])
                    elif isinstance(detail_content, str):
                        logger.debug(f"Processing string detail: {detail_key}")
                        # Handle string details
                        detail_heading = doc.add_paragraph(detail_key.replace('_', ' ').title())
                        detail_heading.style = 'Heading 3'
                        self._add_nab_content(doc, detail_content)
                    else:
                        logger.warning(f"Unexpected detail type for {detail_key}: {type(detail_content)}")
                        
        except Exception as opp_error:
            logger.error(f"❌ Error in _add_nab_opportunity: {opp_error}")
            logger.error(f"❌ opportunity_num: {opportunity_num}")
            logger.error(f"❌ opportunity type: {type(opportunity)}")
            logger.error(f"❌ opportunity: {opportunity}")
            raise opp_error
    
    def _add_nab_content(self, doc, content: Union[str, Dict, List]):
        """Add content using NAB body style with structured formatting support."""
        
        if not content:
            return
        
        logger.debug(f"_add_nab_content called with content type: {type(content)}")
        
        try:
            # Handle list of content items (new for table support)
            if isinstance(content, list):
                logger.debug(f"Processing list content with {len(content)} items")
                for i, content_item in enumerate(content):
                    logger.debug(f"Processing list item {i}, type: {type(content_item)}")
                    self._add_nab_content(doc, content_item)
                return
            
            # Handle both legacy string content and new structured content
            if isinstance(content, str):
                # Legacy string content - use basic formatting
                logger.debug(f"Processing string content, length: {len(content)}")
                self._add_legacy_string_content(doc, content)
            elif isinstance(content, dict):
                logger.debug(f"Processing dict content with keys: {list(content.keys())}")
                
                # Check for new pathway analysis table format
                if 'content_type' in content:
                    content_type = content.get('content_type')
                    logger.debug(f"Content type: {content_type}")
                    
                    if content_type == 'table':
                        self._add_pathway_table(doc, content)
                    elif content_type == 'mixed':
                        # Mixed content with bold labels
                        table_content = content.get('content', '')
                        bold_labels = content.get('bold_labels', [])
                        self._add_structured_mixed_content(doc, table_content, {'bold_labels': bold_labels})
                    elif content_type == 'paragraph':
                        # Simple paragraph content
                        paragraph_content = content.get('content', '')
                        self._add_structured_paragraph(doc, paragraph_content, {})
                    else:
                        logger.warning(f"Unknown content_type: {content_type}")
                        # Fall back to legacy processing
                        if 'content' in content:
                            self._add_nab_content(doc, content['content'])
                elif 'text' in content:
                    # New structured content with formatting metadata
                    logger.debug("Processing structured content with 'text' field")
                    self._add_structured_content(doc, content)
                else:
                    # Handle other dict structures (like sections with title/content)
                    logger.debug("Processing legacy dict content")
                    if 'content' in content:
                        self._add_nab_content(doc, content['content'])
                    else:
                        logger.warning(f"Dict content has no recognized structure: {content}")
            else:
                logger.warning(f"Unexpected content type: {type(content)}, converting to string")
                self._add_legacy_string_content(doc, str(content))
                
        except Exception as content_error:
            logger.error(f"❌ Error in _add_nab_content: {content_error}")
            logger.error(f"❌ Content type: {type(content)}")
            logger.error(f"❌ Content: {content}")
            raise content_error
    
    def _add_pathway_table(self, doc, table_content: Dict):
        """Add pathway analysis table with proper structure mapping."""
        
        try:
            # Fix the structure mapping issue identified in handover document
            headers = table_content.get('table_headers', [])
            content = table_content.get('content', [])
            
            if not headers or not content:
                return
            
            # Map to the format expected by _add_structured_table
            formatting = {
                'headers': headers,      # Map table_headers -> headers
                'rows': content,         # Map content -> rows  
                'table_size': 'normal'
            }
            
            # Use existing structured table method
            self._add_structured_table(doc, formatting)
            
        except Exception as e:
            print(f"⚠️ Error creating pathway table: {e}")
            # Fallback to text content
            para = doc.add_paragraph()
            para.style = 'NAB Body'
            para.add_run(f"Table content processing failed: {e}")
    
    def _add_structured_content(self, doc, structured_content: Dict):
        """Add structured content with explicit formatting metadata."""
        
        text = structured_content.get('text', '')
        formatting = structured_content.get('formatting', {})
        content_type = formatting.get('content_type', 'paragraph')
        
        if content_type == 'bullet_list':
            self._add_structured_bullet_list(doc, text, formatting)
        elif content_type == 'numbered_list':
            self._add_structured_numbered_list(doc, text, formatting)
        elif content_type == 'mixed':
            self._add_structured_mixed_content(doc, text, formatting)
        elif content_type == 'table':
            self._add_structured_table(doc, formatting)
        else:
            # Default to paragraph
            self._add_structured_paragraph(doc, text, formatting)
    
    def _add_structured_bullet_list(self, doc, text: str, formatting: Dict):
        """Add bullet list using explicit formatting metadata."""
        
        lines = text.strip().split('\n')
        bold_labels = formatting.get('bold_labels', [])
        indent_level = formatting.get('indent_level', 0.25)
        
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', 'â€¢ ', '* ')):
                # Remove bullet indicator and create bullet point
                bullet_text = line[2:].strip()
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                para.paragraph_format.left_indent = Inches(indent_level)
                
                # Add bullet
                para.add_run("â€¢ ")
                
                # Add formatted text
                self._add_formatted_text_with_labels(para, bullet_text, bold_labels)
            elif line:
                # Non-bullet line
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                self._add_formatted_text_with_labels(para, line, bold_labels)
    
    def _add_structured_numbered_list(self, doc, text: str, formatting: Dict):
        """Add numbered list using explicit formatting metadata."""
        
        # Split on double newlines to get individual numbered items
        items = text.strip().split('\n\n')
        bold_headers = formatting.get('bold_numbered_headers', False)
        bold_labels = formatting.get('bold_labels', [])
        small_italic_text = formatting.get('small_italic_text', False)
        
        for i, item in enumerate(items, 1):
            if not item.strip():
                continue
                
            lines = item.strip().split('\n')
            
            # First line is the main header for this numbered item
            if lines:
                main_header = lines[0].strip()
                
                # Add numbered header
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                
                # Check if this has a header:content format (e.g., "Individual Career Conversations: Conduct structured...")
                if ':' in main_header:
                    header_part, content_part = main_header.split(':', 1)
                    header_part = header_part.strip()
                    content_part = content_part.strip()
                    
                    # Add number and header part (bold if specified)
                    number_header_run = para.add_run(f"{i}. {header_part}: ")
                    if bold_headers:
                        number_header_run.bold = True
                    
                    # Add content part (regular formatting)
                    content_run = para.add_run(content_part)
                    
                    # Apply small italic formatting if specified (for references)
                    if small_italic_text:
                        number_header_run.font.size = Pt(9)
                        number_header_run.italic = True
                        content_run.font.size = Pt(9)
                        content_run.italic = True
                else:
                    # No colon separator, treat entire line as header
                    if bold_headers:
                        # Bold numbered header
                        header_run = para.add_run(f"{i}. {main_header}")
                        header_run.bold = True
                    else:
                        # Regular numbered header
                        header_run = para.add_run(f"{i}. {main_header}")
                    
                    # Apply small italic formatting if specified (for references)
                    if small_italic_text:
                        header_run.font.size = Pt(9)
                        header_run.italic = True
    
    def _add_structured_paragraph(self, doc, text: str, formatting: Dict):
        """Add paragraph using explicit formatting metadata."""
        
        paragraphs = text.split('\n\n')
        bold_labels = formatting.get('bold_labels', [])
        
        for para_text in paragraphs:
            if para_text.strip():
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                self._add_formatted_text_with_labels(para, para_text.strip(), bold_labels)
    
    def _add_structured_mixed_content(self, doc, text: str, formatting: Dict):
        """Add mixed content with both numbered headers and bullet sub-items."""
        
        paragraphs = text.strip().split('\n\n')
        bold_labels = formatting.get('bold_labels', [])
        bold_headers = formatting.get('bold_numbered_headers', False)
        
        for para_text in paragraphs:
            if para_text.strip():
                lines = para_text.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    para = doc.add_paragraph()
                    para.style = 'NAB Body'
                    
                    # Check for numbered header
                    numbered_match = re.match(r'^(\d+\.\s+)(.+)', line)
                    if numbered_match and bold_headers:
                        # This is a numbered header that should be bold
                        full_run = para.add_run(line)
                        full_run.bold = True
                    elif line.startswith(('- ', 'â€¢ ', '* ')):
                        # This is a bullet item - indent and add bullet
                        para.paragraph_format.left_indent = Inches(0.25)
                        bullet_text = line[2:].strip()
                        para.add_run("â€¢ ")
                        self._add_formatted_text_with_labels(para, bullet_text, bold_labels)
                    else:
                        # Regular text
                        self._add_formatted_text_with_labels(para, line, bold_labels)
    
    def _add_structured_table(self, doc, formatting: Dict):
        """Add a structured table to the document."""
        
        if not DOCX_AVAILABLE:
            return
        
        try:
            from docx.shared import Inches
            from docx.enum.table import WD_TABLE_ALIGNMENT
            
            headers = formatting.get('headers', [])
            rows = formatting.get('rows', [])
            table_size = formatting.get('table_size', 'normal')  # 'compact' or 'normal'
            
            if not headers or not rows:
                return
            
            # Create table
            table = doc.add_table(rows=1 + len(rows), cols=len(headers))
            table.alignment = WD_TABLE_ALIGNMENT.LEFT
            
            # Set table to use full page width
            table.autofit = False
            table.width = Inches(6.5)  # Page width minus margins (8.5" - 2" margins = 6.5")
            
            # Set column widths based on content type and number of columns
            col_count = len(headers)
            if col_count == 3:
                # Check if this is Skills Development table from YAML templates
                if ('Current Skills' in headers and 'Development Needed' in headers) or \
                   ('Current Foundation' in headers and 'Development Needed' in headers):
                    # Skills Development table: Give equal space to all columns for better readability
                    col_widths = [Inches(1.8), Inches(2.3), Inches(2.4)]  # More breathing room for skills content
                else:
                    # Other 3-column tables (Skill Type, Skill Count, All Skills)
                    col_widths = [Inches(1.5), Inches(1.0), Inches(4.0)]  # Give most space to skills list
            elif col_count == 4:
                # Check if this is Skills Transition Analysis table (generated dynamically)
                if ('Current Skills' in headers and 'Required Skills' in headers and 'Gap Assessment' in headers):
                    # Skills Transition Analysis: Give more space to the skills columns
                    col_widths = [Inches(1.3), Inches(2.1), Inches(2.1), Inches(1.0)]  # More space for skills content
                else:
                    # Other 4-column tables (Metric, Score, Assessment, Strategic Significance)
                    col_widths = [Inches(1.5), Inches(0.8), Inches(1.2), Inches(3.0)]  # Balanced distribution
            elif col_count == 6:  # Pathway Comparison Table
                col_widths = [Inches(0.5), Inches(1.8), Inches(0.8), Inches(1.0), Inches(1.2), Inches(1.2)]
            else:
                # Default: Equal distribution
                width_per_col = 6.5 / col_count
                col_widths = [Inches(width_per_col) for _ in range(col_count)]
            
            # Apply column widths
            for i, width in enumerate(col_widths[:col_count]):
                for row in table.rows:
                    row.cells[i].width = width
            
            # Apply Table Design 2 style - banded rows with grey shading
            # Try different built-in styles that match Table Design 2
            table_styles_to_try = [
                'Medium Shading 1',           # Banded rows with grey shading
                'Light Shading',              # Light version
                'Medium Grid 1',              # Grid with shading
                'Light List Accent 1',        # Fallback option
                'Table Grid'                  # Basic fallback
            ]
            
            style_applied = False
            for style_name in table_styles_to_try:
                try:
                    table.style = style_name
                    style_applied = True
                    print(f"ℹ️ Applied table style: {style_name}")
                    break
                except:
                    continue
            
            if not style_applied:
                print("⚠️ Could not apply any table style, using default")
            
            # Use consistent 9pt font size for all tables (headers and body)
            header_font_size = Pt(9)  # 9pt font for all table headers
            body_font_size = Pt(9)    # 9pt font for all table body text
            
            # Add headers with dark background (similar to Table Design 2)
            header_row = table.rows[0]
            for i, header in enumerate(headers):
                cell = header_row.cells[i]
                para = cell.paragraphs[0]
                para.style = 'NAB Body'
                run = para.add_run(header)
                run.bold = True
                run.font.size = header_font_size
                
                # Enhanced header formatting
                try:
                    # Make header text white for better contrast
                    run.font.color.rgb = RGBColor(255, 255, 255)
                except:
                    # Fallback if color setting fails
                    pass
            
            # Add data rows (banding handled by built-in table style)
            for row_idx, row_data in enumerate(rows):
                table_row = table.rows[row_idx + 1]
                
                for col_idx, cell_data in enumerate(row_data):
                    cell = table_row.cells[col_idx]
                    
                    # Use hyperlink-aware cell content method
                    self._add_cell_content_with_hyperlinks(cell, str(cell_data))
                    
                    # Apply compact cell margins for better space utilization
                    if table_size == 'compact':
                        try:
                            # Reduce cell margins for compact tables
                            cell.margin_top = Inches(0.02)
                            cell.margin_bottom = Inches(0.02)
                            cell.margin_left = Inches(0.05)
                            cell.margin_right = Inches(0.05)
                        except:
                            # Fallback if margin setting fails
                            pass
            
            # Add spacing after table
            doc.add_paragraph()
            
        except Exception as e:
            # Fallback to text-based table if docx table creation fails
            print(f"⚠️ Table creation failed, using text format: {e}")
            para = doc.add_paragraph()
            para.style = 'NAB Body'
            para.add_run(f"Table data (formatted as text due to processing limitations)")
            
            headers = formatting.get('headers', [])
            rows = formatting.get('rows', [])
            
            # Headers
            if headers:
                header_para = doc.add_paragraph()
                header_para.style = 'NAB Body'
                header_run = header_para.add_run(" | ".join(headers))
                header_run.bold = True
                header_run.font.size = Pt(9)  # 9pt font for fallback table headers
            
            # Rows
            for row in rows:
                row_para = doc.add_paragraph()
                row_para.style = 'NAB Body'
                row_run = row_para.add_run(" | ".join(str(cell) for cell in row))
                row_run.font.size = Pt(9)  # 9pt font for fallback table body text
    
    def _add_formatted_text_with_labels(self, para, text: str, bold_labels: List[str]):
        """Add formatted text with specified labels in bold."""
        
        # Clean markdown bold formatting (**text**)
        clean_text = self._clean_markdown_bold(text)
        
        # Find bold label at start of text
        label_found = None
        for label in bold_labels:
            if clean_text.startswith(label):
                label_found = label
                break
        
        if label_found:
            # Add label in bold
            label_run = para.add_run(label_found)
            label_run.bold = True
            
            # Add remaining text in regular format
            remaining_text = clean_text[len(label_found):].strip()
            if remaining_text:
                para.add_run(f" {remaining_text}")
        else:
            # No label found, add text normally
            para.add_run(clean_text)
    
    def _clean_markdown_bold(self, text: str) -> str:
        """Remove markdown bold formatting (**text**)."""
        
        clean_text = text
        while '**' in clean_text:
            start = clean_text.find('**')
            if start == -1:
                break
            end = clean_text.find('**', start + 2)
            if end == -1:
                break
            # Extract bold text and remove asterisks
            bold_text = clean_text[start + 2:end]
            clean_text = clean_text[:start] + bold_text + clean_text[end + 2:]
        
        return clean_text
    
    def _add_legacy_string_content(self, doc, content: str):
        """Handle legacy string content with basic bullet list detection."""
        
        if not content:
            return
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        for para_text in paragraphs:
            if para_text.strip():
                # Check if this should be a bullet list
                if self._is_legacy_bullet_list(para_text):
                    self._add_legacy_bullet_list(doc, para_text)
                else:
                    # Regular paragraph
                    para = doc.add_paragraph()
                    para.style = 'NAB Body'
                    
                    # Handle bold text and formatting with legacy approach
                    self._add_legacy_formatted_text(para, para_text.strip())
    
    def _is_legacy_bullet_list(self, text: str) -> bool:
        """Legacy method to check if text should be formatted as a bullet list."""
        lines = text.strip().split('\n')
        
        # Check if multiple lines start with bullet indicators
        bullet_lines = [line for line in lines if line.strip().startswith(('- ', 'â€¢ ', '* '))]
        return len(bullet_lines) >= 2
    
    def _add_legacy_bullet_list(self, doc, text: str):
        """Legacy method to add formatted bullet list to document."""
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', 'â€¢ ', '* ')):
                # Remove bullet indicator and create bullet point
                bullet_text = line[2:].strip()
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                para.paragraph_format.left_indent = Inches(0.25)
                
                # Add bullet and format text
                para.add_run("â€¢ ")
                self._add_legacy_formatted_text(para, bullet_text)
            elif line:
                # Regular line within list context
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                self._add_legacy_formatted_text(para, line)
    
    def _add_legacy_formatted_text(self, para, text: str):
        """Legacy method for formatting text with hardcoded labels."""
        
        # Define legacy key labels that should be bold
        legacy_key_labels = [
            'Move Type:', 'Strategic Context:', 'Business Context:',
            'Organisational Deployment:', 'Primary Locations:', 'Divisional Distribution:',
            'Skills Portfolio Analysis:', 'Organisational Context:', 'About Strategic Intelligence Metrics:',
            'Important Context:', 'Results for', 'Mobility Hub Score:', 'Transition Readiness:',
            'Cross-Family Reach:', 'Strategic Value:', 'Strategic Context Assessment:',
            'Workforce Impact Analysis:', 'Organisational Capability Context:', 'Key Context:',
            'Function Alignment:', 'Management Progression:', 'Skills Transferability:',
            'Cross-Function Demand:', 'Directly Transferable Skills:', 'Skills Development Required:',
            'Development Timeline:', 'Strategic Alignment:', 'Organisational Benefits:',
            'Individual Value Proposition:', 'Calculated Development Time:', 'Phase 1:',
            'Phase 2:', 'Phase 3:', 'Phase 4:', 'Quantitative Measures:', 'Strategic Impact Measures:',
            'Organisational Resilience Indicators:', 'What this means:', 'Recommended Approach:'
        ]
        
        # Remove markdown bold formatting
        clean_text = self._clean_markdown_bold(text)
        
        # Use the new label-based formatting
        self._add_formatted_text_with_labels(para, clean_text, legacy_key_labels)
    
    def _format_powerpoint_summary(self, content: Dict, analysis_data: Dict) -> Dict:
        """Format content as PowerPoint summary."""
        
        # TODO: Implement PowerPoint generation
        # Placeholder implementation
        
        return {
            'format': 'powerpoint',
            'filename': f'summary_{analysis_data.get("summary", "analysis").replace(" ", "_")}.pptx',
            'slides': self._generate_summary_slides(content, analysis_data),
            'status': 'generated'
        }
    
    def _format_pdf_document(self, content: Dict, analysis_data: Dict) -> Dict:
        """Format content as PDF document."""
        
        # TODO: Implement PDF generation
        # Placeholder implementation
        
        return {
            'format': 'pdf',
            'filename': f'career_analysis_{analysis_data.get("summary", "analysis").replace(" ", "_")}.pdf',
            'content': content,
            'status': 'generated'
        }
    
    def _generate_summary_slides(self, content: Dict, analysis_data: Dict) -> List[Dict]:
        """Generate PowerPoint summary slides."""
        
        slides = [
            {
                'title': 'Executive Summary',
                'content': content.get('executive_summary', 'Summary content here'),
                'type': 'text'
            },
            {
                'title': 'Key Findings',
                'content': f"Similarity Score: {analysis_data.get('avg_similarity', 0):.1%}",
                'type': 'metrics'
            },
            {
                'title': 'Recommendations',
                'content': 'Recommended actions based on analysis',
                'type': 'bullets'
            }
        ]
        
        return slides

    def _add_cell_content_with_hyperlinks(self, cell, cell_data):
        """Add content to a table cell, processing hyperlinks if present."""
        if not DOCX_AVAILABLE:
            return
        
        try:
            # Convert to string and handle None/empty values
            if cell_data is None:
                cell_data = ""
            elif not isinstance(cell_data, str):
                cell_data = str(cell_data)
            
            # Clear existing paragraphs
            cell.text = ""
            para = cell.paragraphs[0]
            para.style = 'NAB Body'
            
            # Handle empty content
            if not cell_data.strip():
                run = para.add_run("")
                run.font.size = Pt(9)
                return
            
            # Split by newlines to handle bullet points
            lines = cell_data.split('\n')
            
            for line_idx, line in enumerate(lines):
                if not line.strip():  # Skip empty lines
                    continue
                    
                if line_idx > 0:
                    # Add a new paragraph for each line after the first
                    para = cell.add_paragraph()
                    para.style = 'NAB Body'
                
                # Check if line contains hyperlink (format: text|url)
                if '|' in line and line.count('|') == 1:
                    text_part, url_part = line.split('|', 1)
                    text_part = text_part.strip()
                    url_part = url_part.strip()
                    
                    # Validate URL (basic check)
                    if url_part and url_part.startswith(('http://', 'https://', 'www.')):
                        # Create proper Word hyperlink
                        try:
                            self._add_hyperlink(para, text_part, url_part)
                        except Exception as hyperlink_error:
                            # Fallback: add text with URL in parentheses
                            run = para.add_run(f"{text_part} ({url_part})")
                            run.font.size = Pt(9)
                    else:
                        # Not a valid URL, treat as regular text
                        run = para.add_run(line)
                        run.font.size = Pt(9)
                else:
                    # Regular text without hyperlink
                    run = para.add_run(line)
                    run.font.size = Pt(9)
                    
        except Exception as e:
            # Fallback to simple text
            try:
                cell.text = str(cell_data) if cell_data is not None else ""
                para = cell.paragraphs[0]
                para.style = 'NAB Body'
                for run in para.runs:
                    run.font.size = Pt(9)
            except:
                # Final fallback
                pass

    def _add_hyperlink(self, paragraph, text, url):
        """Add a functional hyperlink to a paragraph using Word's relationship system."""
        try:
            from docx.oxml import parse_xml
            from docx.oxml.ns import qn
            
            # Check if paragraph has 'part' attribute (some table cells might not)
            if not hasattr(paragraph, 'part'):
                # Fallback to styled text for table cells without document part access
                run = paragraph.add_run(text)
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(5, 99, 193)  # Blue hyperlink color
                run.underline = True
                return
            
            # Get the document part and create relationship
            part = paragraph.part
            r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
            
            # Create hyperlink element with 9pt font size
            hyperlink = parse_xml(f'''
                <w:hyperlink xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" 
                             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" 
                             r:id="{r_id}">
                    <w:r>
                        <w:rPr>
                            <w:color w:val="0563C1"/>
                            <w:u w:val="single"/>
                            <w:sz w:val="18"/>
                            <w:szCs w:val="18"/>
                        </w:rPr>
                        <w:t>{text}</w:t>
                    </w:r>
                </w:hyperlink>
            ''')
            
            # Add hyperlink to paragraph
            paragraph._element.append(hyperlink)
            
        except Exception as e:
            # Fallback to styled text if hyperlink creation fails
            run = paragraph.add_run(text)
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(5, 99, 193)  # Blue hyperlink color
            run.underline = True



