"""
Document styling configuration for NAB Career Transition Analysis Generator.
Centralizes all styling variables including colors, fonts, spacing, and style definitions.
Based on NAB's CSS design system variables.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    from docx.shared import RGBColor, Pt
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import parse_xml
    from docx.oxml.ns import qn
    DOCX_AVAILABLE = True
except ImportError:
    # Fallback classes for when python-docx is not available
    RGBColor = None
    Pt = None
    WD_STYLE_TYPE = None
    WD_ALIGN_PARAGRAPH = None
    parse_xml = None
    qn = None
    DOCX_AVAILABLE = False


@dataclass
class NABColors:
    """NAB brand colors from CSS design system."""
    
    # Primary NAB colors
    NAB_BLACK = (0, 0, 0)          # --color-nab-black
    NAB_RED = (220, 38, 38)        # --color-nab-red
    
    # Blue palette
    BLUE_600 = (37, 99, 235)       # --color-blue-600
    BLUE_700 = (29, 78, 216)       # --color-blue-700
    
    # Gray palette
    GRAY_600 = (75, 85, 99)        # --color-gray-600
    GRAY_700 = (55, 65, 81)        # --color-gray-700
    GRAY_800 = (31, 41, 55)        # --color-gray-800
    GRAY_900 = (17, 24, 39)        # --color-gray-900
    
    # White and neutral
    WHITE = (255, 255, 255)
    
    @classmethod
    def get_rgb_color(cls, color_name: str) -> Optional[Any]:
        """Get RGBColor object for docx if available."""
        if not RGBColor:
            return None
            
        color_map = {
            'nab_black': cls.NAB_BLACK,
            'nab_red': cls.NAB_RED,
            'blue_600': cls.BLUE_600,
            'blue_700': cls.BLUE_700,
            'gray_600': cls.GRAY_600,
            'gray_700': cls.GRAY_700,
            'gray_800': cls.GRAY_800,
            'gray_900': cls.GRAY_900,
            'white': cls.WHITE
        }
        
        rgb_tuple = color_map.get(color_name.lower())
        if rgb_tuple:
            return RGBColor(rgb_tuple[0], rgb_tuple[1], rgb_tuple[2])
        return None


@dataclass
class FontSettings:
    """Font configuration from CSS design system."""
    
    # Font families
    FONT_HEADING = 'Epilogue'       # --font-heading
    FONT_PRIMARY = 'Source Sans Pro' # --font-primary
    FONT_MONO = 'Monaco'            # --font-mono
    
    # Font sizes (in points) - Updated to match NAB style template
    SIZE_COVER_TITLE = 42    # Cover title (Epilogue Semibold 42pt)
    SIZE_COVER_SUBTITLE = 28 # Cover subtitle (Epilogue Medium 28pt)
    SIZE_H1 = 22            # Heading 1 (Epilogue Semibold 22pt)
    SIZE_H2 = 14            # Heading 2 (Source Sans Pro Bold 14pt)
    SIZE_H3 = 13            # Heading 3 (Source Sans Pro Bold 13pt)
    SIZE_BODY = 11          # Body text (Source Sans Pro Regular 11pt)
    SIZE_TABLE_HEADER = 9   # Table headers (Source Sans Pro Semibold 9pt) - Updated per user request
    SIZE_TABLE_BODY = 9     # Table body text (Source Sans Pro Regular 9pt) - Added per user request
    SIZE_CAPTION = 9        # Captions and small text
    
    # Legacy size mappings for backwards compatibility
    SIZE_4XL = SIZE_COVER_TITLE    # 42pt (titles)
    SIZE_3XL = SIZE_COVER_SUBTITLE # 28pt (subtitles)
    SIZE_2XL = SIZE_H1             # 22pt (H1)
    SIZE_XL = SIZE_H2              # 14pt (H2)
    SIZE_LG = SIZE_H3              # 13pt (H3)
    SIZE_BASE = SIZE_BODY          # 11pt (body)
    SIZE_SM = SIZE_BODY            # 11pt (small text)
    SIZE_XS = SIZE_CAPTION         # 9pt (captions)
    
    @classmethod
    def get_pt_size(cls, size_name: str) -> Optional[Any]:
        """Get Pt object for docx if available."""
        if not Pt:
            return None
            
        size_map = {
            # NAB-specific size names
            'cover_title': cls.SIZE_COVER_TITLE,
            'cover_subtitle': cls.SIZE_COVER_SUBTITLE,
            'h1': cls.SIZE_H1,
            'h2': cls.SIZE_H2,
            'h3': cls.SIZE_H3,
            'body': cls.SIZE_BODY,
            'table_header': cls.SIZE_TABLE_HEADER,
            'table_body': cls.SIZE_TABLE_BODY,
            'caption': cls.SIZE_CAPTION,
            
            # Legacy size names for backwards compatibility
            '4xl': cls.SIZE_4XL,
            '3xl': cls.SIZE_3XL,
            '2xl': cls.SIZE_2XL,
            'xl': cls.SIZE_XL,
            'lg': cls.SIZE_LG,
            'base': cls.SIZE_BASE,
            'sm': cls.SIZE_SM,
            'xs': cls.SIZE_XS
        }
        
        size = size_map.get(size_name.lower())
        if size:
            return Pt(size)
        return None


@dataclass
class SpacingSettings:
    """Spacing configuration from CSS design system."""
    
    # Spacing values (in points)
    SPACING_1 = 4    # --spacing-1
    SPACING_2 = 8    # --spacing-2
    SPACING_3 = 12   # --spacing-3
    SPACING_4 = 16   # --spacing-4
    SPACING_5 = 20   # --spacing-5
    SPACING_6 = 24   # --spacing-6
    SPACING_8 = 32   # --spacing-8
    SPACING_10 = 40  # --spacing-10
    SPACING_12 = 48  # --spacing-12
    SPACING_16 = 64  # --spacing-16
    
    # Line height values
    LINE_HEIGHT_TIGHT = 1.25  # --line-height-tight
    LINE_HEIGHT_NORMAL = 1.5  # --line-height-normal
    LINE_HEIGHT_RELAXED = 1.75 # --line-height-relaxed
    
    @classmethod
    def get_pt_spacing(cls, spacing_name: str) -> Optional[Any]:
        """Get Pt object for docx if available."""
        if not Pt:
            return None
            
        spacing_map = {
            '1': cls.SPACING_1,
            '2': cls.SPACING_2,
            '3': cls.SPACING_3,
            '4': cls.SPACING_4,
            '5': cls.SPACING_5,
            '6': cls.SPACING_6,
            '8': cls.SPACING_8,
            '10': cls.SPACING_10,
            '12': cls.SPACING_12,
            '16': cls.SPACING_16
        }
        
        spacing = spacing_map.get(str(spacing_name))
        if spacing:
            return Pt(spacing)
        return None


class DocumentStyles:
    """Main class for managing all document styling configuration."""
    
    def __init__(self):
        self.colors = NABColors()
        self.fonts = FontSettings()
        self.spacing = SpacingSettings()
        
    def setup_document_styles(self, doc) -> None:
        """Setup professional document styles based on NAB design system."""
        
        if not DOCX_AVAILABLE:
            print("⚠️ python-docx not available, skipping style setup")
            return
            
        styles = doc.styles
        
        # Cover Title Style (Epilogue Semibold 42pt - RED)
        if WD_STYLE_TYPE and 'NAB Title' not in [s.name for s in styles]:
            title_style = styles.add_style('NAB Title', WD_STYLE_TYPE.PARAGRAPH)
            title_font = title_style.font
            title_font.name = self.fonts.FONT_HEADING  # Epilogue
            title_font.size = self.fonts.get_pt_size('cover_title')  # 42pt
            title_font.bold = True  # Semibold
            
            title_color = self.colors.get_rgb_color('nab_red')  # RED per template
            if title_color:
                title_font.color.rgb = title_color
                
            title_style.paragraph_format.space_after = self.spacing.get_pt_spacing('6')
        
        # Cover Subtitle Style (Epilogue Medium 28pt - BLACK)
        if WD_STYLE_TYPE and 'NAB Subtitle' not in [s.name for s in styles]:
            subtitle_style = styles.add_style('NAB Subtitle', WD_STYLE_TYPE.PARAGRAPH)
            subtitle_font = subtitle_style.font
            subtitle_font.name = self.fonts.FONT_HEADING  # Epilogue
            subtitle_font.size = self.fonts.get_pt_size('cover_subtitle')  # 28pt
            subtitle_font.bold = False  # Medium weight, not bold
            
            subtitle_color = self.colors.get_rgb_color('nab_black')  # BLACK per template
            if subtitle_color:
                subtitle_font.color.rgb = subtitle_color
                
            subtitle_style.paragraph_format.space_after = self.spacing.get_pt_spacing('4')
        
        # Heading 1 Style (Epilogue Semibold 22pt - RED)
        if WD_STYLE_TYPE and 'NAB Heading 1' not in [s.name for s in styles]:
            h1_style = styles.add_style('NAB Heading 1', WD_STYLE_TYPE.PARAGRAPH)
            h1_font = h1_style.font
            h1_font.name = self.fonts.FONT_HEADING  # Epilogue per template
            h1_font.size = self.fonts.get_pt_size('h1')  # 22pt per template
            h1_font.bold = True  # Semibold
            
            h1_color = self.colors.get_rgb_color('nab_red')  # RED per template
            if h1_color:
                h1_font.color.rgb = h1_color
                
            h1_style.paragraph_format.space_before = self.spacing.get_pt_spacing('8')
            h1_style.paragraph_format.space_after = self.spacing.get_pt_spacing('4')
        
        # Heading 2 Style (Source Sans Pro Bold 14pt - BLACK)
        if WD_STYLE_TYPE and 'NAB Heading 2' not in [s.name for s in styles]:
            h2_style = styles.add_style('NAB Heading 2', WD_STYLE_TYPE.PARAGRAPH)
            h2_font = h2_style.font
            h2_font.name = self.fonts.FONT_PRIMARY  # Source Sans Pro per template
            h2_font.size = self.fonts.get_pt_size('h2')  # 14pt per template
            h2_font.bold = True  # Bold
            
            h2_color = self.colors.get_rgb_color('nab_black')  # BLACK per template
            if h2_color:
                h2_font.color.rgb = h2_color
                
            h2_style.paragraph_format.space_before = self.spacing.get_pt_spacing('6')
            h2_style.paragraph_format.space_after = self.spacing.get_pt_spacing('3')
        
        # Heading 3 Style (Source Sans Pro Bold 13pt - BLACK)
        if WD_STYLE_TYPE and 'NAB Heading 3' not in [s.name for s in styles]:
            h3_style = styles.add_style('NAB Heading 3', WD_STYLE_TYPE.PARAGRAPH)
            h3_font = h3_style.font
            h3_font.name = self.fonts.FONT_PRIMARY  # Source Sans Pro per template
            h3_font.size = self.fonts.get_pt_size('h3')  # 13pt per template
            h3_font.bold = True  # Bold
            
            h3_color = self.colors.get_rgb_color('nab_black')  # BLACK per template
            if h3_color:
                h3_font.color.rgb = h3_color
                
            h3_style.paragraph_format.space_before = self.spacing.get_pt_spacing('4')
            h3_style.paragraph_format.space_after = self.spacing.get_pt_spacing('2')
        
        # Body Text Style (Source Sans Pro Regular 11pt - BLACK)
        if WD_STYLE_TYPE and 'NAB Body' not in [s.name for s in styles]:
            body_style = styles.add_style('NAB Body', WD_STYLE_TYPE.PARAGRAPH)
            body_font = body_style.font
            body_font.name = self.fonts.FONT_PRIMARY  # Source Sans Pro per template
            body_font.size = self.fonts.get_pt_size('body')  # 11pt per template
            body_font.bold = False  # Regular weight
            
            body_color = self.colors.get_rgb_color('nab_black')  # BLACK per template
            if body_color:
                body_font.color.rgb = body_color
                
            body_style.paragraph_format.space_after = self.spacing.get_pt_spacing('2')
            body_style.paragraph_format.line_spacing = self.spacing.LINE_HEIGHT_NORMAL
        
        # Table Header Style (Source Sans Pro Semibold 11pt - WHITE on BLACK)
        if WD_STYLE_TYPE and 'NAB Table Header' not in [s.name for s in styles]:
            table_header_style = styles.add_style('NAB Table Header', WD_STYLE_TYPE.PARAGRAPH)
            table_header_font = table_header_style.font
            table_header_font.name = self.fonts.FONT_PRIMARY  # Source Sans Pro per template
            table_header_font.size = self.fonts.get_pt_size('table_header')  # 11pt per template
            table_header_font.bold = True  # Semibold (using bold as closest approximation)
            
            # White text for table headers (will be on black background)
            table_header_color = self.colors.get_rgb_color('white')
            if table_header_color:
                table_header_font.color.rgb = table_header_color
                
        # Table Body Style (Source Sans Pro Regular 11pt - BLACK)
        if WD_STYLE_TYPE and 'NAB Table Body' not in [s.name for s in styles]:
            table_body_style = styles.add_style('NAB Table Body', WD_STYLE_TYPE.PARAGRAPH)
            table_body_font = table_body_style.font
            table_body_font.name = self.fonts.FONT_PRIMARY  # Source Sans Pro per template
            table_body_font.size = self.fonts.get_pt_size('table_body')  # 11pt per template
            table_body_font.bold = False  # Regular weight
            
            # Black text for table body
            table_body_color = self.colors.get_rgb_color('nab_black')
            if table_body_color:
                table_body_font.color.rgb = table_body_color

    def create_title_page(self, doc, analysis_data: Dict[str, Any]) -> None:
        """Create professional title page with NAB styling."""
        
        try:
            from datetime import datetime
        except ImportError:
            datetime = None
        
        job_name = analysis_data.get('source_job_logical_display_name', 'Professional Role')
        
        # Main title
        title_para = doc.add_paragraph('NAB Skills Intelligence Platform')
        title_para.style = doc.styles['NAB Title']
        
        # Subtitle
        subtitle_para = doc.add_paragraph('Strategic Career Pathway Analysis')
        subtitle_para.style = doc.styles['NAB Subtitle']
        
        # Add vertical spacing
        doc.add_paragraph()
        doc.add_paragraph()
        
        # Role-specific title
        role_para = doc.add_paragraph(f'Career Transition Analysis: {job_name}')
        role_para.style = doc.styles['NAB Heading 1']
        
        # Add more spacing
        doc.add_paragraph()
        doc.add_paragraph()
        
        # Date
        if datetime:
            date_str = datetime.now().strftime("%B %d, %Y")
        else:
            date_str = "2025"
            
        date_para = doc.add_paragraph(f'Generated: {date_str}')
        date_para.style = doc.styles['NAB Body']
    
    def add_table_of_contents(self, doc) -> None:
        """Add a professional table of contents using Word TOC field."""
        
        if not DOCX_AVAILABLE:
            print("⚠️ python-docx not available, skipping TOC")
            return
        
        # Add TOC heading
        toc_heading = doc.add_paragraph('Table of Contents')
        toc_heading.style = doc.styles['NAB Heading 1']
        
        # Add some spacing
        doc.add_paragraph()
        
                # Create TOC placeholder with instructions for Word
        try:
            # Add TOC instructions paragraph
            toc_instructions = doc.add_paragraph()
            toc_instructions.style = doc.styles['NAB Body']
            toc_instructions.add_run("Table of Contents").bold = True
            
            # Add spacing
            doc.add_paragraph()
            
            # Create instructions for generating TOC in Word
            instructions = doc.add_paragraph()
            instructions.style = doc.styles['NAB Body']
            instructions.add_run("Instructions: ").bold = True
            instructions.add_run("In Microsoft Word, place cursor here and go to References → Table of Contents → Automatic Table 1")
            
            # Add spacing for TOC area
            doc.add_paragraph()
            doc.add_paragraph("[Table of Contents will appear here when generated in Word]")
            doc.add_paragraph()
            
            print("✅ TOC placeholder created with instructions")
            
        except Exception as e:
            print(f"⚠️ TOC creation failed: {e}")
            # Fallback: Create a manual TOC
            self._create_manual_toc(doc)
    
    def _create_manual_toc(self, doc) -> None:
        """Create a manual table of contents as fallback."""
        
        # Manual TOC entries - these would ideally be generated dynamically
        toc_entries = [
            ("Executive Summary", 1),
            ("Current Role Context", 1),
            ("    Job Profile Overview", 2),
            ("    Core Competency Foundation", 2),
            ("    Strategic Value Proposition", 2),
            ("    Strategic Intelligence Metrics", 2),
            ("Pathway Analysis: Top 3 Strategic Opportunities", 1),
            ("Strategic Recommendations", 1),
            ("    Database-Driven Decision Support", 2),
            ("    Immediate Actions (Next 30 Days)", 2),
            ("    Medium-Term Initiatives (Next 90 Days)", 2),
            ("    Success Metrics & Evaluation", 2),
            ("Conclusion", 1)
        ]
        
        for entry_text, level in toc_entries:
            toc_entry = doc.add_paragraph()
            toc_entry.style = doc.styles['NAB Body']
            
            # Add indentation for sub-levels
            if level == 2:
                # Add indent for level 2 items
                toc_entry.paragraph_format.left_indent = self.spacing.get_pt_spacing('4')
            
            # Add the entry text with dots and page number placeholder
            dots = "." * (50 - len(entry_text))
            toc_entry.add_run(f"{entry_text} {dots} ")
            
            # Page number (placeholder - would be updated by Word's TOC)
            page_run = toc_entry.add_run("X")
            if hasattr(page_run.font, 'color') and self.colors.get_rgb_color('gray_600'):
                page_run.font.color.rgb = self.colors.get_rgb_color('gray_600')
    
    def add_section_heading(self, doc, heading_text: str, level: int = 1) -> None:
        """Add a section heading that will appear in the TOC using Word's built-in heading styles."""
        
        # Use Word's built-in heading styles for TOC compatibility
        if level == 1:
            style_name = 'Heading 1'
        elif level == 2:
            style_name = 'Heading 2'
        elif level == 3:
            style_name = 'Heading 3'
        else:
            style_name = 'Heading 3'  # Default to H3 for deeper levels
        
        heading = doc.add_paragraph(heading_text)
        heading.style = doc.styles[style_name]
        
        # Apply NAB styling to the built-in heading if we have custom fonts/colors
        if DOCX_AVAILABLE and hasattr(heading, 'runs') and heading.runs:
            run = heading.runs[0]
            
            # Apply NAB font and colors while keeping Word's outline structure
            if level == 1:
                run.font.name = self.fonts.FONT_HEADING  # Epilogue
                run.font.size = self.fonts.get_pt_size('h1')  # 22pt per NAB template
                run.font.bold = True
                if self.colors.get_rgb_color('nab_red'):  # RED per NAB template
                    run.font.color.rgb = self.colors.get_rgb_color('nab_red')
            elif level == 2:
                run.font.name = self.fonts.FONT_PRIMARY  # Source Sans Pro per NAB template
                run.font.size = self.fonts.get_pt_size('h2')  # 14pt per NAB template
                run.font.bold = True
                if self.colors.get_rgb_color('nab_black'):  # BLACK per NAB template
                    run.font.color.rgb = self.colors.get_rgb_color('nab_black')
            elif level == 3:
                run.font.name = self.fonts.FONT_PRIMARY  # Source Sans Pro per NAB template
                run.font.size = self.fonts.get_pt_size('h3')  # 13pt per NAB template
                run.font.bold = True
                if self.colors.get_rgb_color('nab_black'):  # BLACK per NAB template
                    run.font.color.rgb = self.colors.get_rgb_color('nab_black')
        
        return heading
    
    def add_executive_summary_page(self, doc, exec_content: Dict[str, Any]) -> None:
        """Add Executive Summary on its own page with professional formatting."""
        
        # Executive Summary heading
        exec_heading = doc.add_paragraph('Executive Summary')
        exec_heading.style = doc.styles['NAB Heading 1']
        
        # Add content sections
        if isinstance(exec_content, dict):
            section_order = ['strategic_context', 'key_findings', 'primary_recommendations', 'confidence_assessment']
            
            for section_key in section_order:
                if section_key in exec_content:
                    section = exec_content[section_key]
                    if isinstance(section, dict):
                        # Add section title
                        if 'title' in section:
                            section_heading = doc.add_paragraph(section['title'])
                            section_heading.style = doc.styles['NAB Heading 2']
                        
                        # Add content
                        if 'content' in section:
                            self.add_formatted_content_with_style(doc, section['content'])
    
    def add_formatted_content_with_style(self, doc, content: str) -> None:
        """Add formatted content with proper NAB styling and table detection."""
        
        if not content:
            return
        
        # First, try to detect and format pipe-delimited tables
        tables_found = self.detect_and_format_pipe_delimited_tables(doc, content)
        
        # If tables were found and formatted, we're done
        if tables_found:
            return
        
        # No tables found, proceed with regular content formatting
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        
        for para_text in paragraphs:
            if para_text.strip():
                para = doc.add_paragraph()
                para.style = doc.styles['NAB Body']
                
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

    def add_section_content_with_styles(self, doc, section_data: Dict[str, Any]) -> None:
        """Add section content with professional NAB styling."""
        
        if not isinstance(section_data, dict):
            return
        
        for subsection_key, subsection in section_data.items():
            if isinstance(subsection, dict) and 'content' in subsection:
                # Add subsection title with H2 style
                if 'title' in subsection:
                    subsection_heading = doc.add_paragraph(subsection['title'])
                    subsection_heading.style = doc.styles['NAB Heading 2']
                
                # Add formatted content
                self.add_formatted_content_with_style(doc, subsection['content'])

    def create_nab_table_design_2(self, doc, headers: List[str], rows: List[List[str]], table_style: str = 'compact') -> None:
        """
        Create a table using NAB Table Design 2 specifications:
        - BLACK header row with WHITE text (matching user's image)
        - Alternating grey/white banded rows for better readability
        - Source Sans Pro font throughout
        - 9pt font size for better real estate (per user request)
        - Light borders for professional appearance
        """
        if not DOCX_AVAILABLE:
            self._add_fallback_table_text(doc, headers, rows)
            return
            
        try:
            # Calculate number of columns
            col_count = len(headers)
            if not col_count:
                return
                
            # Create table with all rows at once
            table = doc.add_table(rows=1 + len(rows), cols=col_count)
            
            # DON'T apply built-in table style yet - it will override our custom styling
            # We'll apply table styling manually to maintain black headers
            
            # Configure BLACK header row with WHITE text (NAB Table Design 2 style)
            header_row = table.rows[0]
            for i, header_text in enumerate(headers):
                cell = header_row.cells[i]
                
                # Set black background for header cell (MUST be done before applying table style)
                try:
                    if qn:
                        # Access the cell's background shading
                        cell_shading = cell._element.get_or_add_tcPr().get_or_add_shd()
                        cell_shading.set(qn('w:fill'), "000000")  # Black background
                        cell_shading.set(qn('w:val'), "clear")
                    else:
                        # Fallback if qn not available
                        cell_shading = cell._element.get_or_add_tcPr().get_or_add_shd()
                        cell_shading.fill = "000000"
                except Exception as e:
                    # Try alternative method for setting black background
                    try:
                        if parse_xml and qn:
                            shading_xml = '<w:shd {} w:fill="000000"/>'.format(
                                'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
                            )
                            cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))
                        else:
                            # Final fallback
                            cell_shading = cell._element.get_or_add_tcPr().get_or_add_shd()
                            cell_shading.fill = "000000"
                    except Exception as final_e:
                        print(f"⚠️ Failed to set black background for header cell {i}: {e}, {final_e}")
                
                # Add header text with WHITE text and bold formatting
                para = cell.paragraphs[0]
                para.clear()
                run = para.add_run(str(header_text))
                run.font.name = self.fonts.FONT_PRIMARY  # Source Sans Pro
                run.font.size = self.fonts.get_pt_size('table_header')  # 9pt
                run.font.bold = True
                # WHITE text for headers on black background
                if self.colors.get_rgb_color('white'):
                    run.font.color.rgb = self.colors.get_rgb_color('white')
            
            # Add data rows with proper banding and hyperlink support
            for row_idx, row_data in enumerate(rows):
                table_row = table.rows[row_idx + 1]
                
                # Apply alternating row colors for banding (NAB Table Design 2 style)
                try:
                    if row_idx % 2 == 1:  # Every other row gets light grey banding
                        for cell in table_row.cells:
                            try:
                                if qn:
                                    # Use proper XML namespace method
                                    cell_shading = cell._element.get_or_add_tcPr().get_or_add_shd()
                                    cell_shading.set(qn('w:fill'), "F5F5F5")  # Light grey
                                    cell_shading.set(qn('w:val'), "clear")
                                else:
                                    # Fallback method
                                    cell_shading = cell._element.get_or_add_tcPr().get_or_add_shd()
                                    cell_shading.fill = "F5F5F5"  # Light grey
                            except:
                                # If individual cell shading fails, try alternative method
                                try:
                                    if parse_xml:
                                        shading_xml = '<w:shd {} w:fill="F5F5F5"/>'.format(
                                            'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
                                        )
                                        cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))
                                except:
                                    pass  # If all shading methods fail, continue without banding
                except Exception as row_error:
                    print(f"⚠️ Failed to apply row banding for row {row_idx}: {row_error}")
                
                for col_idx, cell_data in enumerate(row_data):
                    if col_idx < col_count:  # Ensure we don't exceed column count
                        cell = table_row.cells[col_idx]
                        
                        # Add cell content with hyperlink support for skills columns
                        self._add_cell_content_with_hyperlinks(cell, str(cell_data))
            
            # NOW apply a light table style for borders but not background (after our custom styling)
            try:
                # Use a table style that adds borders but doesn't override our background colors
                table.style = 'Table Grid'  # Basic grid with borders, minimal background interference
            except:
                # If table style application fails, continue without table style
                print("⚠️ Failed to apply Table Grid style, continuing without built-in table styling")
            
            # Add spacing after table
            doc.add_paragraph()
            
        except Exception as e:
            print(f"Error creating NAB Table Design 2: {e}")
            # Fallback to text-based table
            self._add_fallback_table_text(doc, headers, rows)
    
    def _add_cell_content_with_hyperlinks(self, cell, content: str):
        """Add content to table cell with proper hyperlink support for skills URLs."""
        para = cell.paragraphs[0]
        para.clear()
        
        # Check if content contains skills with URLs
        if '•' in content and '|https://lightcast.io/' in content:
            # Split by newlines to handle multiple skills
            skills = content.split('\n')
            
            for i, skill in enumerate(skills):
                skill = skill.strip()
                if not skill:
                    continue
                
                # Check if this skill has an embedded URL
                if '|https://lightcast.io/' in skill:
                    # Extract skill name and URL
                    parts = skill.split('|', 1)
                    skill_name = parts[0].strip()
                    skill_url = parts[1].strip()
                    
                    # Add hyperlink for this skill
                    self._add_hyperlink(para, skill_name, skill_url)
                else:
                    # Regular skill without URL
                    run = para.add_run(skill)
                    run.font.name = self.fonts.FONT_PRIMARY
                    run.font.size = self.fonts.get_pt_size('table_body')
                    if self.colors.get_rgb_color('nab_black'):
                        run.font.color.rgb = self.colors.get_rgb_color('nab_black')
                
                # Add line break AFTER skill content (except for last skill)
                # This prevents line breaks from interfering with hyperlink formatting
                if i < len(skills) - 1:
                    para.add_run('\n')
        else:
            # Regular cell content without skills
            run = para.add_run(content)
            run.font.name = self.fonts.FONT_PRIMARY
            run.font.size = self.fonts.get_pt_size('table_body')
            if self.colors.get_rgb_color('nab_black'):
                run.font.color.rgb = self.colors.get_rgb_color('nab_black')
    
    def _add_hyperlink(self, paragraph, text: str, url: str):
        """Add a functional hyperlink to a paragraph using Word's relationship system."""
        try:
            if not parse_xml or not qn:
                # Fallback to styled text if XML tools not available
                run = paragraph.add_run(text)
                run.font.name = self.fonts.FONT_PRIMARY
                run.font.size = self.fonts.get_pt_size('table_body')
                run.font.underline = True
                if self.colors.get_rgb_color('blue_600'):
                    run.font.color.rgb = self.colors.get_rgb_color('blue_600')
                return
            
            # Check if paragraph has 'part' attribute (some table cells might not)
            if not hasattr(paragraph, 'part'):
                # Fallback to styled text for table cells without document part access
                run = paragraph.add_run(text)
                run.font.name = self.fonts.FONT_PRIMARY
                run.font.size = self.fonts.get_pt_size('table_body')
                run.font.underline = True
                if self.colors.get_rgb_color('blue_600'):
                    run.font.color.rgb = self.colors.get_rgb_color('blue_600')
                return
            
            # Get the document part and create relationship
            part = paragraph.part
            r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
            
            # Create hyperlink element with proper Word hyperlink XML
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
            print(f"Failed to create functional hyperlink, using styled text: {e}")
            # Fallback to styled text if hyperlink creation fails
            run = paragraph.add_run(text)
            run.font.name = self.fonts.FONT_PRIMARY
            run.font.size = self.fonts.get_pt_size('table_body')
            run.font.underline = True
            if self.colors.get_rgb_color('blue_600'):
                run.font.color.rgb = self.colors.get_rgb_color('blue_600')
    
    def _add_fallback_table_text(self, doc, headers: List[str], rows: List[List[str]]):
        """Fallback method to add table as formatted text when docx table creation fails."""
        # Add table header
        header_para = doc.add_paragraph()
        header_para.style = 'NAB Body'
        header_run = header_para.add_run(" | ".join(headers))
        header_run.bold = True
        
        # Add separator line
        sep_para = doc.add_paragraph()
        sep_para.style = 'NAB Body'
        sep_run = sep_para.add_run(" | ".join(["-" * len(header) for header in headers]))
        
        # Add data rows
        for row in rows:
            row_para = doc.add_paragraph()
            row_para.style = 'NAB Body'
            row_run = row_para.add_run(" | ".join(str(cell) for cell in row))
        
        # Add spacing
        doc.add_paragraph()

    def detect_and_format_pipe_delimited_tables(self, doc, content: str) -> bool:
        """
        Detect pipe-delimited tables in string content and format them using NAB Table Design 2.
        
        This method handles tables without separator lines (as shown in user's images):
        - Tables can have introductory text before headers
        - Tables start with a header line containing pipes
        - Followed directly by data rows (no separator line needed)
        - Special handling for Skills Transition Analysis with embedded pipes (skill_name|url format)
        - 26 total tables across the document are processed this way
        
        Args:
            doc: Document object
            content: String content that may contain pipe-delimited tables
            
        Returns:
            bool: True if tables were found and formatted, False otherwise
        """
        if not content or '|' not in content:
            return False
        
        lines = content.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        if len(lines) < 2:
            return False
        
        # Check if this looks like a Skills Transition Analysis table
        if self._is_skills_transition_table(lines):
            return self._format_skills_transition_table(doc, lines)
        
        # Scan through all lines to find table headers (not just first line)
        table_start_idx = -1
        table_headers = []
        
        for i, line in enumerate(lines):
            if '|' in line:
                # Check if this could be a table header
                potential_headers = [h.strip() for h in line.split('|') if h.strip()]
                
                # Look for common table header patterns
                if len(potential_headers) >= 2:
                    # Check if this looks like table headers (not data) - be very explicit
                    line_lower = line.lower()
                    
                    # Exact matches for Core Competency Foundation
                    core_competency_patterns = [
                        'skill type' in line_lower and 'skill count' in line_lower,
                        'skill type' in line_lower and 'all skills' in line_lower
                    ]
                    
                    # Exact matches for Strategic Intelligence Metrics  
                    strategic_metrics_patterns = [
                        'metric' in line_lower and 'score' in line_lower and 'assessment' in line_lower,
                        'metric' in line_lower and 'strategic significance' in line_lower
                    ]
                    
                    # Other common table patterns
                    other_patterns = [
                        'category' in line_lower and 'current' in line_lower,
                        'pathway' in line_lower and 'similarity' in line_lower,
                        'current skills' in line_lower and 'new skills' in line_lower,
                        'gap assessment' in line_lower
                    ]
                    
                    if any(core_competency_patterns + strategic_metrics_patterns + other_patterns):
                        table_start_idx = i
                        table_headers = potential_headers
                        break
                    
                    # Also check if next line is a separator (------)
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if set(next_line.replace('|', '').replace('-', '').replace(' ', '')) == set():
                            table_start_idx = i
                            table_headers = potential_headers
                            break
        
        if table_start_idx == -1 or not table_headers:
            return False
        
        # Find data rows starting after headers (and optional separator)
        data_start_idx = table_start_idx + 1
        
        # Skip separator line if it exists
        if (data_start_idx < len(lines) and 
            set(lines[data_start_idx].replace('|', '').replace('-', '').replace(' ', '')) == set()):
            data_start_idx += 1
        
        # Collect data rows
        data_lines = []
        for line in lines[data_start_idx:]:
            if '|' in line:
                data_lines.append(line)
        
        if not data_lines:
            return False
        
        # Parse data rows
        rows = []
        for line in data_lines:
            row_data = [cell.strip() for cell in line.split('|')]
            # Pad or trim to match header count
            while len(row_data) < len(table_headers):
                row_data.append('')
            row_data = row_data[:len(table_headers)]
            rows.append(row_data)
        
        if rows:
            # Add any content before the table as regular paragraphs
            if table_start_idx > 0:
                intro_content = '\n'.join(lines[:table_start_idx])
                if intro_content.strip():
                    self.add_formatted_content_with_style(doc, intro_content)
            
            # Create the table
            self.create_nab_table_design_2(doc, table_headers, rows)
            
            # Add any content after the table as regular paragraphs
            table_end_idx = data_start_idx + len(data_lines)
            if table_end_idx < len(lines):
                outro_content = '\n'.join(lines[table_end_idx:])
                if outro_content.strip():
                    self.add_formatted_content_with_style(doc, outro_content)
            
            return True
            
        return False
    
    def _is_skills_transition_table(self, lines: List[str]) -> bool:
        """Check if this content represents a Skills Transition Analysis table"""
        if len(lines) < 3:
            return False
            
        # Look for the specific headers pattern
        first_line = lines[0].lower()
        skills_indicators = ['category', 'current skills', 'new skills', 'gap assessment', 'skills transition']
        
        return any(indicator in first_line for indicator in skills_indicators)
    
    def _format_skills_transition_table(self, doc, lines: List[str]) -> bool:
        """
        Format Skills Transition Analysis table with special handling for skills content.
        
        Based on JavaScript logic from career-analysis.js:
        - Skills format: "• Strategic Communication|https://lightcast.io/open-skills/skills/ID"
        - The pipe separates skill name from URL within the same cell
        - 4-column structure: Category | Current Skills | New Skills Required | Gap Assessment
        """
        # Parse headers from first line
        headers = [h.strip() for h in lines[0].split('|') if h.strip()]
        
        # Expected 4 columns for Skills Transition Analysis
        if len(headers) != 4:
            headers = ['Category', 'Current Skills Applicable for New Role', 'New Skills Required', 'Gap Assessment']
        
        # Reconstruct table rows using JavaScript-inspired logic
        rows = self._reconstruct_skills_table_rows(lines[1:])
        
        if rows:
            self.create_nab_table_design_2(doc, headers, rows)
            return True
            
        return False
    
    def _reconstruct_skills_table_rows(self, data_lines: List[str]) -> List[List[str]]:
        """
        Reconstruct Skills Transition table rows from malformed data.
        
        Based on JavaScript reconstructSkillsTableRows method:
        - Each category starts a new row
        - Skills with embedded pipes (name|url) are kept together
        - Skills are grouped into current vs new skills columns
        - Filters out rows with no skills (like JavaScript does)
        """
        rows = []
        current_row = None
        is_in_new_skills_section = False
        
        for line in data_lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this starts a new row (has category)
            pipe_count = line.count('|')
            
            # Line starts a new row if it has multiple pipes and doesn't start with bullet
            if pipe_count >= 2 and not line.startswith('•'):
                # Finalize previous row
                if current_row:
                    finalized_row = self._finalize_skills_row(current_row)
                    if finalized_row:  # Only add non-empty rows (filters out empty skill rows)
                        rows.append(finalized_row)
                
                # Start new row
                parts = line.split('|')
                current_row = {
                    'category': parts[0].strip(),
                    'current_skills': [],
                    'new_skills': [],
                    'gap_assessment': '',
                }
                is_in_new_skills_section = False
                
                # Add any skills from this line
                for i, part in enumerate(parts[1:], 1):
                    part = part.strip()
                    if part and part.startswith('•'):
                        current_row['current_skills'].append(part)
                    elif part and i == len(parts) - 1:
                        # Last part might be gap assessment
                        gap_keywords = ['ready', 'foundation', 'development', 'strong', 'moderate', 'limited', 'assessment']
                        if any(keyword in part.lower() for keyword in gap_keywords):
                            current_row['gap_assessment'] = part
                            
            elif line.startswith('•') and current_row:
                # This is a skill line - determine if current or new skill
                if len(current_row['current_skills']) > 5 and not is_in_new_skills_section:
                    is_in_new_skills_section = True
                
                if is_in_new_skills_section:
                    current_row['new_skills'].append(line)
                else:
                    current_row['current_skills'].append(line)
                    
            elif current_row and not line.startswith('•'):
                # Check if this is gap assessment or new skills
                gap_keywords = ['ready', 'foundation', 'development', 'strong', 'moderate', 'limited', 'assessment']
                if any(keyword in line.lower() for keyword in gap_keywords):
                    current_row['gap_assessment'] = line
                else:
                    # Treat as new skills section indicator
                    is_in_new_skills_section = True
        
        # Finalize last row
        if current_row:
            finalized_row = self._finalize_skills_row(current_row)
            if finalized_row:  # Only add non-empty rows (filters out empty skill rows)
                rows.append(finalized_row)
            
        return rows
    
    def _finalize_skills_row(self, row_data: dict) -> Optional[List[str]]:
        """
        Finalize skills row by formatting skills content for Word document.
        
        Based on JavaScript finalizeSkillsRow method:
        - Convert skills arrays to formatted text with preserved URLs
        - Calculate gap assessment based on new skills count
        - Filter out rows where both current and new skills are empty
        
        Returns:
            List[str] if row has content, None if row should be filtered out
        """
        # Format current skills (keep URLs for hyperlinks)
        current_skills_text = self._format_skills_for_word_with_urls(row_data['current_skills'])
        
        # Format new skills (keep URLs for hyperlinks)
        new_skills_text = self._format_skills_for_word_with_urls(row_data['new_skills'])
        
        # FILTER OUT "No skills in this category" rows like JavaScript does
        # If both current and new skills are empty, skip this row entirely
        if not current_skills_text.strip() and not new_skills_text.strip():
            return None  # Signal to skip this row
        
        # Calculate Gap Assessment based on JavaScript logic from finalizeSkillsRow
        gap_assessment = row_data.get('gap_assessment', '')
        if not gap_assessment or gap_assessment == 'Assessment pending':
            # Count new skills required (based on JavaScript logic)
            new_skills_count = len([s for s in row_data['new_skills'] if s.strip().startswith('•')])
            
            if new_skills_count == 0:
                # No new skills needed = strong foundation
                gap_assessment = 'Strong foundation - ready for transition'
            elif new_skills_count <= 3:
                # Few new skills needed = moderate development  
                gap_assessment = 'Moderate foundation - some development needed'
            else:
                # Many new skills needed = significant development
                gap_assessment = 'Limited foundation - significant development required'
        
        return [
            row_data['category'],
            current_skills_text,
            new_skills_text,
            gap_assessment
        ]
    
    def _format_skills_for_word_with_urls(self, skills_list: List[str]) -> str:
        """
        Format skills list for Word document while preserving URLs for hyperlinks.
        
        Handles skills with embedded pipes (skill_name|url) by:
        - Keeping both skill name AND URL for hyperlink creation
        - Maintaining bullet point formatting
        - Joining with line breaks for Word table cells
        """
        if not skills_list:
            return ""
        
        formatted_skills = []
        for skill in skills_list:
            skill = skill.strip()
            if not skill:
                continue
                
            # Keep the full skill with URL for hyperlink processing
            # The _add_cell_content_with_hyperlinks method will handle the URL extraction
            formatted_skills.append(skill)
        
        return '\n'.join(formatted_skills)

    def get_style_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current style configuration for debugging."""
        
        return {
            'colors': {
                'nab_black': self.colors.NAB_BLACK,
                'nab_red': self.colors.NAB_RED,
                'blue_600': self.colors.BLUE_600,
                'gray_700': self.colors.GRAY_700,
                'gray_600': self.colors.GRAY_600
            },
            'fonts': {
                'heading': self.fonts.FONT_HEADING,
                'primary': self.fonts.FONT_PRIMARY,
                'sizes': {
                    'title': self.fonts.SIZE_4XL,
                    'h1': self.fonts.SIZE_3XL,
                    'h2': self.fonts.SIZE_XL,
                    'h3': self.fonts.SIZE_LG,
                    'body': self.fonts.SIZE_BASE
                }
            },
            'spacing': {
                'line_height': self.spacing.LINE_HEIGHT_NORMAL,
                'spacing_values': [
                    self.spacing.SPACING_2,
                    self.spacing.SPACING_3,
                    self.spacing.SPACING_4,
                    self.spacing.SPACING_6,
                    self.spacing.SPACING_8
                ]
            },
            'docx_available': DOCX_AVAILABLE,
            'table_design_2_available': True
        }


# Create a default instance for easy importing
default_styles = DocumentStyles()

# Export convenience functions
def setup_document_styles(doc):
    """Convenience function to setup document styles."""
    return default_styles.setup_document_styles(doc)

def create_title_page(doc, analysis_data):
    """Convenience function to create title page."""
    return default_styles.create_title_page(doc, analysis_data)

def add_table_of_contents(doc):
    """Convenience function to add table of contents."""
    return default_styles.add_table_of_contents(doc)

def add_section_heading(doc, heading_text, level=1):
    """Convenience function to add section heading."""
    return default_styles.add_section_heading(doc, heading_text, level)

def add_executive_summary_page(doc, exec_content):
    """Convenience function to add executive summary page."""
    return default_styles.add_executive_summary_page(doc, exec_content)

def add_section_content_with_styles(doc, section_data):
    """Convenience function to add section content with styles."""
    return default_styles.add_section_content_with_styles(doc, section_data)
