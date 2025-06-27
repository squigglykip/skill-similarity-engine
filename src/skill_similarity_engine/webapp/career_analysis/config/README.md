# White Paper Configuration Module

This directory contains all configuration settings for the NAB Skills Intelligence Platform white paper generation system. The configuration is organized into modular components for easy maintenance and customization.

## 📁 Structure

```
config/
├── __init__.py           # Main configuration exports
├── document_styles.py    # Document styling and formatting
├── settings.py          # General system settings
└── README.md           # This documentation
```

## 🎨 Document Styles (`document_styles.py`)

Centralizes all styling variables and document formatting configuration:

### Key Components

- **`NABColors`**: Brand colors from NAB's CSS design system
  - NAB Black, NAB Red, Blue palette, Gray palette
  - Helper method: `get_rgb_color()` for docx integration

- **`FontSettings`**: Typography configuration
  - Font families: Epilogue (headings), Source Sans Pro (body)
  - Font sizes: 4XL (36pt) down to XS (12pt)
  - Helper method: `get_pt_size()` for docx integration

- **`SpacingSettings`**: Layout and spacing values
  - Spacing scale: 1 (4pt) to 16 (64pt)
  - Line heights: tight, normal, relaxed
  - Helper method: `get_pt_spacing()` for docx integration

- **`DocumentStyles`**: Main styling class
  - `setup_document_styles()`: Creates all paragraph styles
  - `create_title_page()`: Professional title page generation
  - `add_executive_summary_page()`: Dedicated executive summary page
  - Style-aware content formatting methods

### Usage Example

```python
from config.document_styles import DocumentStyles

# Initialize styling
styles = DocumentStyles()

# Setup document with NAB styles
styles.setup_document_styles(doc)

# Create professional title page
styles.create_title_page(doc, analysis_data)
```

## ⚙️ General Settings (`settings.py`)

Contains system-wide configuration and settings:

### Key Components

- **`WhitePaperSettings`**: Main settings class
  - File paths and directory structure
  - Output formats and templates
  - Database configuration
  - Performance and quality settings

### Configuration Areas

1. **File Structure**
   - Template directories (sections, narratives, audiences, scenarios)
   - Output directory configuration
   - Default database path

2. **Output Formats**
   - Supported formats: Word, PDF, PowerPoint, HTML, Markdown
   - File naming patterns
   - Default format selection

3. **Content Generation**
   - Section ordering and titles
   - Reference numbering system
   - Similarity thresholds
   - Maximum pathways analysis

4. **Performance**
   - Cache timeout settings
   - Quality control thresholds
   - Logging configuration

### Usage Example

```python
from config.settings import get_section_config, get_output_config

# Get section configuration
sections = get_section_config()
print(sections['order'])  # ['executive_summary', 'current_role_context', ...]

# Get output configuration  
output = get_output_config()
print(output['formats'])  # ['word', 'pdf', 'powerpoint', ...]
```

## 🔄 Integration with Existing System

### Before (scattered styling)
```python
# Styling variables scattered throughout files
NAB_BLACK = RGBColor(0, 0, 0)
title_font.size = Pt(36)
spacing = Pt(24)
```

### After (centralized configuration)
```python
# All styling centralized in config
from config.document_styles import setup_document_styles
setup_document_styles(doc)
```

## 🚀 Benefits

1. **Centralized Management**: All styling in one place
2. **Easy Customization**: Change brand colors/fonts system-wide
3. **Consistency**: Ensures uniform styling across all documents
4. **Maintainability**: Clear separation of concerns
5. **Fallback Support**: Graceful degradation when dependencies unavailable
6. **Type Safety**: Structured configuration with helper methods

## 🎯 Design Principles

- **CSS Integration**: Mirrors NAB's web design system variables
- **Modular Architecture**: Separate concerns (colors, fonts, spacing)
- **Graceful Degradation**: Works even without python-docx
- **Professional Quality**: Executive-ready document standards
- **Extensibility**: Easy to add new styles and configurations

## 📝 Adding New Styles

To add a new document style:

1. **Define the style in `DocumentStyles.setup_document_styles()`**:
```python
# New style definition
if WD_STYLE_TYPE and 'NAB Custom Style' not in [s.name for s in styles]:
    custom_style = styles.add_style('NAB Custom Style', WD_STYLE_TYPE.PARAGRAPH)
    custom_font = custom_style.font
    custom_font.name = self.fonts.FONT_HEADING
    custom_font.size = self.fonts.get_pt_size('lg')
```

2. **Use the style in document generation**:
```python
paragraph = doc.add_paragraph('Content')
paragraph.style = doc.styles['NAB Custom Style']
```

## 🔍 Configuration Validation

The settings module includes validation to ensure configuration consistency:

```python
from config.settings import WhitePaperSettings

# Validate current configuration
issues = WhitePaperSettings.validate_config()
if issues:
    print("Configuration issues found:", issues)
```

## 📚 Dependencies

- **Optional**: `python-docx` for Word document generation
- **Required**: `pathlib`, `typing` (standard library)
- **Fallbacks**: All components work without optional dependencies

This configuration system provides a solid foundation for maintaining and extending the white paper generation system while ensuring consistent, professional output that meets NAB's brand standards. 