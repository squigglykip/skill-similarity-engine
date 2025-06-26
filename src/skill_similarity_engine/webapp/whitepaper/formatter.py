"""
Document formatting (Word, PDF, PowerPoint) for white paper generation.
Uses pre-styled NAB Word templates for professional output.
"""

from typing import Dict, Any, List, cast, Union, Optional
from pathlib import Path
import io
import logging
import re

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

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
    def create_table(headers: List[str], rows: List[List[str]], table_style: str = 'simple') -> Dict[str, Any]:
        """Create a table with headers and rows for Word document formatting."""
        # Convert table data to text format for now
        # Headers
        table_text = " | ".join(headers) + "\n"
        table_text += "|".join(["-" * len(header) for header in headers]) + "\n"
        
        # Rows
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
                    level_progression = f"{source_level} → {target_level}"
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
    """Formats generated content into various document formats using NAB templates."""
    
    def __init__(self, template_path=None):
        """
        Initialize formatter with optional template path.
        
        Args:
            template_path: Path to NAB Word template file (.docx)
        """
        self.template_path = template_path
        self.templates_path = Path(__file__).parent / 'templates' / 'word_templates'
    
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
        """Format content as Word document using NAB styling from screenshots."""
        
        if not DOCX_AVAILABLE:
            logger.warning("python-docx not available. Install with: pip install python-docx")
            return {
                'format': 'word',
                'filename': f'whitepaper_{analysis_data.get("summary", "analysis").replace(" ", "_")}.docx',
                'content': content,
                'status': 'error',
                'message': 'python-docx not installed'
            }
        
        try:
            # Create new document from scratch with NAB styling
            doc = Document()
            logger.info("Creating document from scratch with NAB styling")
            
            job_name = analysis_data.get('source_job_logical_display_name', 'Professional Role')
            
            # Setup NAB styles and create professional document
            self._setup_nab_styles(doc)
            self._create_nab_document(doc, content, analysis_data, job_name)
            
            # Set up page margins (Normal Word margins: 2.54cm all around)
            from docx.shared import Inches
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
            
            filename = f'whitepaper_{job_name.replace(" ", "_").replace("(", "").replace(")", "")}.docx'
            
            return {
                'format': 'word',
                'filename': filename,
                'content': content_bytes,
                'status': 'generated',
                'buffer': buffer
            }
            
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            return {
                'format': 'word',
                'filename': 'whitepaper_error.docx',
                'content': content,
                'status': 'error',
                'message': str(e)
            }
    
    def _setup_nab_styles(self, doc):
        """Create NAB styles based on screenshot styling, with TOC-compatible headings."""
        
        from docx.shared import RGBColor, Pt
        from docx.enum.style import WD_STYLE_TYPE
        
        styles = doc.styles
        
        # NAB Red color from screenshots
        nab_red = RGBColor(220, 38, 38)  # #DC2626
        dark_gray = RGBColor(55, 65, 81)  # #374151
        medium_gray = RGBColor(107, 114, 128)  # #6B7280
        
        # Cover Title Style - Epilogue Semibold 42pt Red (custom style for cover)
        if 'NAB Cover Title' not in [s.name for s in styles]:
            cover_title = styles.add_style('NAB Cover Title', WD_STYLE_TYPE.PARAGRAPH)
            title_font = cover_title.font
            title_font.name = 'Epilogue'
            title_font.size = Pt(42)
            title_font.bold = True
            title_font.color.rgb = nab_red
            cover_title.paragraph_format.space_after = Pt(12)
        
        # Cover Subtitle Style - Epilogue Medium 28pt Black (custom style for cover)
        if 'NAB Cover Subtitle' not in [s.name for s in styles]:
            cover_subtitle = styles.add_style('NAB Cover Subtitle', WD_STYLE_TYPE.PARAGRAPH)
            subtitle_font = cover_subtitle.font
            subtitle_font.name = 'Epilogue'
            subtitle_font.size = Pt(28)
            subtitle_font.color.rgb = RGBColor(0, 0, 0)
            cover_subtitle.paragraph_format.space_after = Pt(24)
        
        # Modify Word's built-in Heading 1 style for TOC compatibility
        h1_style = styles['Heading 1']
        h1_font = h1_style.font
        h1_font.name = 'Epilogue'
        h1_font.size = Pt(22)
        h1_font.bold = True
        h1_font.color.rgb = nab_red
        h1_style.paragraph_format.space_before = Pt(18)
        h1_style.paragraph_format.space_after = Pt(12)
        
        # Modify Word's built-in Heading 2 style for TOC compatibility  
        h2_style = styles['Heading 2']
        h2_font = h2_style.font
        h2_font.name = 'Source Sans Pro'
        h2_font.size = Pt(14)
        h2_font.bold = True
        h2_font.color.rgb = dark_gray
        h2_style.paragraph_format.space_before = Pt(12)
        h2_style.paragraph_format.space_after = Pt(8)
        
        # Modify Word's built-in Heading 3 style for TOC compatibility
        h3_style = styles['Heading 3']
        h3_font = h3_style.font
        h3_font.name = 'Source Sans Pro'
        h3_font.size = Pt(13)
        h3_font.bold = True
        h3_font.color.rgb = medium_gray
        h3_style.paragraph_format.space_before = Pt(8)
        h3_style.paragraph_format.space_after = Pt(6)
        
        # Body Text - Source Sans Pro Regular 11pt (custom style)
        if 'NAB Body' not in [s.name for s in styles]:
            body_style = styles.add_style('NAB Body', WD_STYLE_TYPE.PARAGRAPH)
            body_font = body_style.font
            body_font.name = 'Source Sans Pro'
            body_font.size = Pt(11)
            body_font.color.rgb = dark_gray
            body_style.paragraph_format.line_spacing = 1.5
            body_style.paragraph_format.space_after = Pt(6)
        
        # Call to Action - Epilogue Medium 12pt Red (custom style)
        if 'NAB Call to Action' not in [s.name for s in styles]:
            cta_style = styles.add_style('NAB Call to Action', WD_STYLE_TYPE.PARAGRAPH)
            cta_font = cta_style.font
            cta_font.name = 'Epilogue'
            cta_font.size = Pt(12)
            cta_font.color.rgb = nab_red
            cta_style.paragraph_format.space_after = Pt(6)
    
    def _create_nab_document(self, doc, content: Dict, analysis_data: Dict, job_name: str):
        """Create NAB-styled document with content."""
        
        from datetime import datetime
        
        # Page 1: Cover Page
        title_para = doc.add_paragraph('NAB Skills Intelligence Platform')
        title_para.style = 'NAB Cover Title'
        
        subtitle_para = doc.add_paragraph(f'Strategic Career Pathway Analysis')
        subtitle_para.style = 'NAB Cover Subtitle'
        
        # Remove "White Paper:" prefix and add job function
        job_para = doc.add_paragraph(job_name)
        job_para.style = 'Heading 2'
        
        # Add source job function from analysis data
        source_job_function = analysis_data.get('source_job_function', 'Professional Services')
        function_para = doc.add_paragraph(source_job_function)
        function_para.style = 'NAB Body'
        
        # Date and version info
        date_para = doc.add_paragraph(f'Generated: {datetime.now().strftime("%B %d, %Y")}')
        date_para.style = 'NAB Body'
        
        version_para = doc.add_paragraph('Version 1.0 - Skills Intelligence Analysis')
        version_para.style = 'NAB Body'
        
        doc.add_page_break()
        
        # Page 2: Table of Contents
        toc_heading = doc.add_paragraph('Table of Contents')
        toc_heading.style = 'Heading 1'
        
        # Add instruction for automatic TOC generation
        toc_instruction = doc.add_paragraph()
        toc_instruction.style = 'NAB Body'
        instruction_run = toc_instruction.add_run("Instructions: ")
        instruction_run.bold = True
        toc_instruction.add_run("Place cursor here and go to References → Table of Contents → Automatic Table to generate TOC")
        
        # Add space for TOC
        doc.add_paragraph()
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
        
        for i, (section_key, section_title) in enumerate(section_order):
            if section_key in content:
                # Add page break before each section (except the first one)
                if i > 0:
                    doc.add_page_break()
                self._add_nab_section(doc, section_title, content[section_key])
    
    def _add_nab_section(self, doc, section_title: str, section_content: Dict):
        """Add section using NAB styles."""
        
        # Add main section heading using Word's built-in Heading 1 (modified with NAB styling)
        section_heading = doc.add_paragraph(section_title)
        section_heading.style = 'Heading 1'
        
        # Handle different content structures
        if isinstance(section_content, dict):
            if 'opportunities' in section_content:
                # Handle pathway analysis with multiple opportunities
                for i, opportunity in enumerate(section_content['opportunities'], 1):
                    self._add_nab_opportunity(doc, opportunity, i)
            else:
                # Handle other structured sections
                for key, subsection in section_content.items():
                    if isinstance(subsection, dict) and 'title' in subsection and 'content' in subsection:
                        # Add subsection heading using Word's built-in Heading 2 (modified with NAB styling)
                        subsection_heading = doc.add_paragraph(subsection['title'])
                        subsection_heading.style = 'Heading 2'
                        
                        # Add content
                        self._add_nab_content(doc, subsection['content'])
        
        elif isinstance(section_content, str):
            # Simple string content
            self._add_nab_content(doc, section_content)
    
    def _add_nab_opportunity(self, doc, opportunity: Dict, opportunity_num: int):
        """Add pathway opportunity using NAB styles with enhanced headers."""
        
        # Use the enhanced header from pathway analysis, fallback to simple title
        if 'header' in opportunity:
            # New enhanced header format with detailed opportunity information
            header_content = opportunity['header']
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
            opp_heading = doc.add_paragraph(f"{opportunity_num}. {opp_title}")
            opp_heading.style = 'Heading 2'
        
        # Add opportunity details (skip the header field since we already processed it)
        for detail_key, detail_content in opportunity.items():
            if detail_key not in ['title', 'header'] and isinstance(detail_content, dict):
                if 'title' in detail_content:
                    # Detail subheading using Word's built-in Heading 3 (modified with NAB styling)
                    detail_heading = doc.add_paragraph(detail_content['title'])
                    detail_heading.style = 'Heading 3'
                
                if 'content' in detail_content:
                    self._add_nab_content(doc, detail_content['content'])
    
    def _add_nab_content(self, doc, content: Union[str, Dict, List]):
        """Add content using NAB body style with structured formatting support."""
        
        if not content:
            return
        
        # Handle list of content items (new for table support)
        if isinstance(content, list):
            for content_item in content:
                self._add_nab_content(doc, content_item)
            return
        
        # Handle both legacy string content and new structured content
        if isinstance(content, str):
            # Legacy string content - use basic formatting
            self._add_legacy_string_content(doc, content)
        elif isinstance(content, dict):
            # Check for new pathway analysis table format
            if 'content_type' in content and content.get('content_type') == 'table':
                self._add_pathway_table(doc, content)
            elif 'content_type' in content and content.get('content_type') == 'mixed':
                # Mixed content with bold labels
                table_content = content.get('content', '')
                bold_labels = content.get('bold_labels', [])
                self._add_structured_mixed_content(doc, table_content, {'bold_labels': bold_labels})
            elif 'content_type' in content and content.get('content_type') == 'paragraph':
                # Simple paragraph content
                paragraph_content = content.get('content', '')
                self._add_structured_paragraph(doc, paragraph_content, {})
            elif 'text' in content:
                # New structured content with formatting metadata
                self._add_structured_content(doc, content)
            else:
                # Handle other dict structures (like sections with title/content)
                if 'content' in content:
                    self._add_nab_content(doc, content['content'])
    
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
            if line.startswith(('- ', '• ', '* ')):
                # Remove bullet indicator and create bullet point
                bullet_text = line[2:].strip()
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                para.paragraph_format.left_indent = Inches(indent_level)
                
                # Add bullet
                para.add_run("• ")
                
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
                    elif line.startswith(('- ', '• ', '* ')):
                        # This is a bullet item - indent and add bullet
                        para.paragraph_format.left_indent = Inches(0.25)
                        bullet_text = line[2:].strip()
                        para.add_run("• ")
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
            if col_count == 3:  # Skills Analysis Table (Skill Type, Skill Count, All Skills)
                col_widths = [Inches(1.5), Inches(1.0), Inches(4.0)]  # Give most space to skills list
            elif col_count == 4:  # Strategic Metrics Table (Metric, Score, Assessment, Strategic Significance)
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
                    print(f"✅ Applied table style: {style_name}")
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
            para.add_run("Table data (formatted as text due to processing limitations)")
            
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
        bullet_lines = [line for line in lines if line.strip().startswith(('- ', '• ', '* '))]
        return len(bullet_lines) >= 2
    
    def _add_legacy_bullet_list(self, doc, text: str):
        """Legacy method to add formatted bullet list to document."""
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(('- ', '• ', '* ')):
                # Remove bullet indicator and create bullet point
                bullet_text = line[2:].strip()
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                para.paragraph_format.left_indent = Inches(0.25)
                
                # Add bullet and format text
                para.add_run("• ")
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
            'filename': f'whitepaper_{analysis_data.get("summary", "analysis").replace(" ", "_")}.pdf',
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
