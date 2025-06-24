# NAB White Paper Templates

This directory contains Word document templates for generating professional NAB white papers.

## 🎯 **Template Usage**

### **Option 1: Use Your Workplace NAB Template (Recommended)**

1. **Obtain your NAB template** from your workplace's document library
2. **Save it** in this directory as `nab_template.docx`
3. **Update the formatter** to use it:
   ```python
   template_path = "templates/nab_template.docx"
   formatter = DocumentFormatter(template_path=template_path)
   ```

### **Option 2: Create a Custom Template**

If you can't use the workplace template, create a Word document with these exact style names:

#### **Required Style Names:**
- `Cover title in Epilogue Semibold 42pt` - Main title style
- `Cover subtitle in Epilogue Medium 28pt` - Subtitle style  
- `Heading 1 (H1) in 14pt` - Section headings
- `Heading 2 (H2) in 13pt` - Subsection headings
- `Heading 3 (H3) in 11pt` - Detail headings
- `Body copy` - Regular paragraph text

#### **Font Specifications:**
- **Epilogue Semibold** - For titles and main headings
- **Source Sans Pro Bold** - For subheadings
- **Source Sans Pro Regular** - For body text

#### **Color Palette:**
- **NAB Red**: #DC2626 (for main headings)
- **Dark Gray**: #374151 (for body text)
- **Medium Gray**: #6B7280 (for subheadings)

## 🔧 **Template Structure**

Your template should include:

### **Page 1: Cover Page**
```
[NAB Logo - if available]

Cover title in Epilogue Semibold 42pt
Cover subtitle in Epilogue Medium 28pt

Day Month Year
Version information
```

### **Page 2: Table of Contents**
```
Table of contents

[Space for Word's automatic TOC generation]
```

### **Page 3+: Content Pages**
```
[Content will be populated by Python using the defined styles]
```

## 📋 **Implementation Notes**

- The Python formatter will **automatically replace** placeholder text
- **Heading styles** are mapped to create automatic Table of Contents
- **Built-in Word TOC** functionality works with properly styled headings
- **Professional formatting** maintains NAB brand consistency

## 🎯 **Testing Your Template**

1. Create a template with the required styles
2. Test with the formatter:
   ```python
   formatter = DocumentFormatter(template_path="your_template.docx")
   result = formatter.format_document(content, 'word', analysis_data)
   ```
3. Verify that:
   - Styles are applied correctly
   - TOC generates properly in Word
   - NAB branding is maintained

## 📄 **Files in This Directory**

- `README.md` - This guide
- `nab_template.docx` - Your NAB workplace template (add this)
- `custom_template.docx` - Alternative custom template (optional)

---

**Note**: Using your workplace's official NAB template ensures perfect brand compliance and professional presentation quality. 