"""
Document formatting (Word, PDF, PowerPoint) for white paper generation.
Uses pre-styled NAB Word templates for professional output.
"""

from typing import Dict, Any, List
from pathlib import Path
import io
import logging

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

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
            
            # Save to memory buffer
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            filename = f'whitepaper_{job_name.replace(" ", "_").replace("(", "").replace(")", "")}.docx'
            
            return {
                'format': 'word',
                'filename': filename,
                'content': buffer.read(),
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
        
        job_para = doc.add_paragraph(f'White Paper: {job_name}')
        job_para.style = 'Heading 2'
        
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
        
        # Add content sections
        section_order = [
            ('executive_summary', 'Executive Summary'),
            ('current_role_context', 'Current Role Context'),
            ('pathway_analysis', 'Pathway Analysis: Top 3 Strategic Opportunities'),
            ('strategic_recommendations', 'Strategic Recommendations'),
            ('conclusion', 'Conclusion')
        ]
        
        for section_key, section_title in section_order:
            if section_key in content:
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
        """Add pathway opportunity using NAB styles."""
        
        # Opportunity heading using Word's built-in Heading 2 (modified with NAB styling)
        opp_title = opportunity.get('title', f'Opportunity {opportunity_num}')
        opp_heading = doc.add_paragraph(f"{opportunity_num}. {opp_title}")
        opp_heading.style = 'Heading 2'
        
        # Add opportunity details
        for detail_key, detail_content in opportunity.items():
            if detail_key != 'title' and isinstance(detail_content, dict):
                if 'title' in detail_content:
                    # Detail subheading using Word's built-in Heading 3 (modified with NAB styling)
                    detail_heading = doc.add_paragraph(detail_content['title'])
                    detail_heading.style = 'Heading 3'
                
                if 'content' in detail_content:
                    self._add_nab_content(doc, detail_content['content'])
    
    def _add_nab_content(self, doc, content: str):
        """Add content using NAB body style."""
        
        if not content:
            return
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        for para_text in paragraphs:
            if para_text.strip():
                para = doc.add_paragraph()
                para.style = 'NAB Body'
                
                # Handle bold text (**text**)
                if '**' in para_text:
                    parts = para_text.split('**')
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            # Regular text
                            if part:
                                para.add_run(part)
                        else:
                            # Bold text
                            if part:
                                run = para.add_run(part)
                                run.bold = True
                else:
                    # Regular paragraph
                    para.add_run(para_text.strip())
    
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
