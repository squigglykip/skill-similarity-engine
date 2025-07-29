# NAB Skills Intelligence Platform - Project Context & Standards

**Document Version**: 1.0  
**Created**: 2025-01-19  
**Purpose**: Macro-level context and technical standards for LLM assistants working on the NAB Skills Intelligence Platform  
**Audience**: LLM assistants, developers, system architects  

---

## 🎯 **PROJECT OVERVIEW**

The **NAB Skills Intelligence Platform** is an enterprise-grade web application that provides data-driven insights for workforce planning, career development, and skills analysis. Built for NAB's Future Skills team, HR professionals, and employees.

### **Core Capabilities**
- **Job Similarity Analysis**: Compare 715+ job profiles using comprehensive skills data
- **Career Pathway Discovery**: Identify progression opportunities and skill gaps
- **Skills Intelligence**: Analyse 38K+ skills with Lightcast integration
- **Career Transition Analysis Generator**: Professional Word documents for strategic planning
- **Workforce Analytics**: SQLite-based business context database

### **Target Users**
- **Primary**: NAB Future Skills team, HR Business Partners
- **Secondary**: NAB employees exploring career options
- **Tertiary**: Senior leadership consuming strategic insights

---

## 🏗️ **TECHNICAL ARCHITECTURE**

### **Application Stack**
- **Backend**: Python 3.9+ with Flask web framework
- **Database**: SQLite for business context, Parquet files for similarity matrices
- **Frontend**: HTML5 + Tailwind CSS + Vanilla JavaScript
- **Document Generation**: python-docx for Word document creation
- **Data Processing**: Pandas, NumPy for large-scale similarity calculations

### **Project Structure**
```
skill-similarity-engine/
├── src/skill_similarity_engine/
│   ├── similarity/          # Core similarity calculation engine
│   ├── business_context/    # SQLite database generation
│   ├── webapp/             # Flask web application
│   ├── utils/              # Shared utilities and helpers
│   └── data/               # Data loading and validation
├── docs/                   # Comprehensive documentation
├── models/                 # Generated similarity matrices and databases
└── scripts/                # Development and testing scripts
```

### **Data Architecture Philosophy**
- **Single Source of Truth**: No data duplication across systems
- **Performance First**: Precomputed similarities for sub-100ms queries
- **Separation of Concerns**: Similarity calculation separate from business context
- **Scalability**: Chunked processing for large datasets (38K+ skills, 510K+ job pairs)

---

## 🎨 **FRONTEND STANDARDS**

### **CSS Framework: Tailwind CSS**
**Why Tailwind**: Utility-first approach provides consistent design system, responsive design out-of-the-box, and rapid development cycles.

**Core Principles**:
- **Utility-First**: Use Tailwind utilities instead of custom CSS where possible
- **Component-Based**: Create reusable component patterns with consistent spacing
- **Mobile-First**: Always design responsive with `sm:`, `md:`, `lg:` breakpoints
- **Accessibility**: Ensure WCAG AA compliance with proper contrast and focus states

**Example Component Pattern**:
```html
<!-- Standard Card Component -->
<div class="bg-white rounded-lg shadow-md overflow-hidden">
  <div class="px-6 py-4 border-b border-gray-200">
    <h3 class="text-lg font-epilogue font-medium text-gray-900">Card Title</h3>
  </div>
  <div class="p-6">
    <!-- Card content -->
  </div>
</div>
```

### **Typography System**
- **Headers**: `font-epilogue` (Epilogue) - clean, modern, professional
- **Body Text**: `font-source` (Source Sans Pro) - highly readable, data-friendly
- **Code/IDs**: `font-mono` (system monospace) - job IDs, skill codes, technical references

**Typography Scale**:
- **Page Titles**: `text-3xl md:text-4xl font-epilogue font-bold`
- **Section Headers**: `text-xl md:text-2xl font-epilogue font-semibold`
- **Card Titles**: `text-lg font-epilogue font-medium`
- **Body Text**: `text-sm md:text-base font-source`
- **Labels**: `text-xs font-source font-medium uppercase tracking-wide`
- **Captions**: `text-xs font-source text-gray-400`

**Text Alignment**: All text is left-aligned (`text-left`) - never centred except for loading/empty states

### **Color Palette**
- **Primary Background**: `bg-black` (NAB brand foundation)
- **Content Areas**: `bg-white`, `bg-gray-50` for readability
- **Accent Color**: `text-red-600`, `bg-red-600` (NAB red)
- **Text Hierarchy**: `text-gray-900` → `text-gray-600` → `text-gray-400`

**Usage Patterns**:
- **Primary Actions**: `bg-red-600 hover:bg-red-700`
- **Secondary Actions**: `border border-red-600 text-red-600 hover:bg-red-600 hover:text-white`
- **Text on Dark**: `text-white` or `text-gray-100`
- **Text on Light**: `text-black` or `text-gray-900`

**Accessibility**: Minimum contrast ratio 4.5:1 for normal text, 3:1 for large text. Red accents only for highlights, never for critical information alone.

### **Layout System**
**Container & Spacing**:
```html
<!-- Standard page container -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <!-- Content with consistent vertical rhythm -->
  <div class="space-y-6 py-6">
    <!-- Components here -->
  </div>
</div>
```

**Grid Systems**:
- **Dashboard Layouts**: `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`
- **Two-column forms**: `grid grid-cols-1 lg:grid-cols-2 gap-8`
- **Detail views**: `grid grid-cols-1 lg:grid-cols-3 gap-8` (sidebar + main)

### **Responsive Design Standards**
- **Mobile**: `< 768px` - single column, touch-friendly
- **Tablet**: `768px - 1024px` - two columns, compact
- **Desktop**: `> 1024px` - full layout, optimal information density

---

## 📝 **JAVASCRIPT STANDARDS**

### **Architecture Philosophy**
- **Vanilla JavaScript**: No frameworks - keeps bundle size minimal and reduces complexity
- **Modular Design**: Namespace functions under logical modules (e.g., `window.SkillEngine.SearchModule`)
- **Progressive Enhancement**: HTML works without JavaScript, JS enhances experience
- **Performance Focus**: Minimal DOM manipulation, efficient event handling

### **Code Organisation Patterns**
```javascript
// Namespace pattern for modular JavaScript
window.SkillEngine = window.SkillEngine || {};

window.SkillEngine.SearchModule = {
    init: function(config) {
        // Initialisation logic
    },
    
    searchJobs: function(query) {
        // Search functionality
    },
    
    displayResults: function(results) {
        // Display logic
    }
};

// Usage in templates
document.addEventListener('DOMContentLoaded', function() {
    window.SkillEngine.SearchModule.init({
        apiEndpoint: '/api/career-analysis-jobs',
        containerId: 'search-container'
    });
});
```

### **API Integration Standards**
- **Consistent Endpoints**: All search uses `/api/career-analysis-jobs`
- **Error Handling**: Graceful fallbacks for API failures
- **Loading States**: Show progress indicators for long operations
- **Data Validation**: Validate responses before DOM updates

### **Event Handling Patterns**
```javascript
// Standard event delegation pattern
document.addEventListener('click', function(event) {
    if (event.target.matches('.search-result-item')) {
        handleJobSelection(event.target.dataset.jobId);
    }
});

// Form submission with validation
function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const validation = validateFormData(formData);
    
    if (!validation.isValid) {
        displayValidationErrors(validation.errors);
        return;
    }
    
    submitForm(formData);
}
```

---

## 🧩 **COMPONENT LIBRARY**

### **Standard Components**

**Navigation Bar**:
```html
<nav class="bg-black border-b border-gray-800">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex justify-between h-16">
      <div class="flex items-center">
        <a href="/" class="font-epilogue font-bold text-xl text-white hover:text-red-600 transition-colors">
          Skills Intelligence
        </a>
      </div>
      <div class="hidden md:flex items-center space-x-8">
        <a href="/dashboard" class="text-gray-300 hover:text-white transition-colors">Dashboard</a>
        <a href="/jobs" class="text-gray-300 hover:text-white transition-colors">Job Explorer</a>
        <a href="/pathways" class="text-gray-300 hover:text-white transition-colors">Career Pathways</a>
      </div>
    </div>
  </div>
</nav>
```

**Dashboard Cards**:
```html
<!-- Metric Card -->
<div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-600">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-xs font-source font-medium text-gray-500 uppercase tracking-wide">Jobs Analyzed</p>
      <p class="text-2xl font-epilogue font-bold text-gray-900">2,847</p>
    </div>
    <div class="p-3 bg-red-100 rounded-full">
      <!-- Icon here -->
    </div>
  </div>
  <div class="mt-4">
    <p class="text-sm font-source text-gray-600">↑ 12% from last month</p>
  </div>
</div>
```

**Button Variants**:
```html
<!-- Primary Button -->
<button class="bg-red-600 hover:bg-red-700 text-white font-source font-medium px-6 py-2 rounded-md transition-colors duration-200">
  Analyze Skills
</button>

<!-- Secondary Button -->
<button class="border border-red-600 text-red-600 hover:bg-red-600 hover:text-white font-source font-medium px-6 py-2 rounded-md transition-colors duration-200">
  View Details
</button>

<!-- Tertiary Button -->
<button class="text-red-600 hover:text-red-700 font-source font-medium px-4 py-2 transition-colors duration-200">
  Learn More →
</button>
```

---

## 📊 **DATA VISUALIZATION PATTERNS**

### **Similarity Scores**
```html
<!-- Progress Bar Style -->
<div class="flex items-center space-x-3">
  <span class="text-sm font-source font-medium text-gray-900">87%</span>
  <div class="flex-1 bg-gray-200 rounded-full h-2">
    <div class="bg-red-600 h-2 rounded-full" style="width: 87%"></div>
  </div>
</div>

<!-- Badge Style -->
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-source font-medium bg-red-100 text-red-800">
  High Match
</span>
```

### **Skills Lists**
```html
<div class="space-y-2">
  <div class="flex flex-wrap gap-2">
    <span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-source font-medium bg-gray-100 text-gray-800">
      Python
    </span>
    <span class="inline-flex items-center px-3 py-1 rounded-md text-xs font-source font-medium bg-gray-100 text-gray-800">
      Data Analysis
    </span>
  </div>
</div>
```

### **Empty States**
```html
<div class="text-center py-12">
  <div class="text-gray-400 mb-4">
    <!-- Icon -->
  </div>
  <h3 class="text-lg font-epilogue font-medium text-gray-900">No results found</h3>
  <p class="text-sm font-source text-gray-500 mt-2">
    Try adjusting your search criteria or explore different job families.
  </p>
  <button class="mt-4 bg-red-600 hover:bg-red-700 text-white font-source font-medium px-4 py-2 rounded-md transition-colors duration-200">
    Reset Filters
  </button>
</div>
```

### **Multi-Step Process Indicators**
For career pathway exploration and Career Transition Analysis Generator workflows:
```html
<div class="bg-gray-900 border border-gray-700 rounded-lg p-6 mb-6">
  <nav aria-label="Progress">
    <ol class="flex items-center">
      <li class="relative">
        <div class="flex items-center">
          <div class="relative w-8 h-8 flex items-center justify-center bg-red-600 rounded-full">
            <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
          </div>
          <span class="ml-3 text-sm font-medium text-white">Select Starting Role</span>
        </div>
      </li>
      <!-- Additional steps -->
    </ol>
  </nav>
</div>
```

---

## 🗄️ **DATABASE STANDARDS**

### **SQLite Schema Principles**
- **Backward Compatibility**: New columns added with graceful defaults
- **Foreign Key Integrity**: All relationships properly constrained
- **Performance Indexing**: Strategic indexes on frequently queried columns
- **Data Quality**: Handle nulls gracefully with COALESCE defaults

### **Query Performance Guidelines**
- **Sub-100ms Target**: All career pathway queries must be fast
- **Parameterised Queries**: Always use parameterised queries for security
- **Efficient Joins**: Leverage indexes for complex multi-table queries
- **Chunked Loading**: Large datasets loaded in chunks with progress tracking

### **Enhanced Schema Features**
- **14-Column Job Architecture**: Rich organisational metadata (management levels, job categories)
- **18-Column Skills Library**: Comprehensive Lightcast integration with JSON fields
- **Multiple Display Formats**: JobDisplayManager provides consistent job naming

---

## 🔧 **BACKEND STANDARDS**

### **Python Code Quality**
- **Type Hints**: All functions have proper type annotations
- **Docstrings**: Comprehensive documentation for all public methods
- **Error Handling**: Graceful error handling with meaningful messages
- **Testing**: Unit tests for core business logic

### **Flask Application Patterns**
```python
# Standard API endpoint pattern
@app.route('/api/endpoint/<parameter>')
def api_endpoint(parameter):
    """
    API endpoint description.
    
    Args:
        parameter: Description of parameter
        
    Returns:
        JSON response with standardised structure
    """
    try:
        # Validate input
        if not parameter:
            return jsonify({'error': 'Parameter required'}), 400
            
        # Process request
        result = process_request(parameter)
        
        # Enhance with display names if job data
        if 'jobs' in result:
            display_manager = get_display_manager()
            result['jobs'] = [
                add_display_names_to_job(job, display_manager) 
                for job in result['jobs']
            ]
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error in endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
```

### **Job Display Standardisation**
**Critical Pattern**: All job data must use JobDisplayManager for consistent naming.

```python
from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat

# Standard job enhancement pattern
def add_display_names_to_job(job_data: Dict, display_manager: JobDisplayManager) -> Dict:
    """Enhance job data with standardised display names."""
    job_id = job_data.get('id') or job_data.get('JobProfileID')
    if job_id:
        job_data.update({
            'display_name_logical': display_manager.get_display_name(job_id, DisplayFormat.LOGICAL),
            'display_name_standard': display_manager.get_display_name(job_id, DisplayFormat.STANDARD),
            'display_name_search': display_manager.get_display_name(job_id, DisplayFormat.SEARCH),
            'display_name_dropdown': display_manager.get_display_name(job_id, DisplayFormat.DROPDOWN),
            'display_name_compact': display_manager.get_display_name(job_id, DisplayFormat.COMPACT),
            'job_profile_id': job_id  # Always include for reference
        })
    return job_data
```

---

## 📋 **DATA PROCESSING STANDARDS**

### **Performance Requirements**
- **Similarity Calculation**: Must handle 715 jobs × 38K skills efficiently
- **Progress Tracking**: All long operations show progress with tqdm
- **Memory Management**: Chunked processing for datasets >10K records
- **Parallel Processing**: Utilise multiple cores for similarity calculations

### **Data Quality Standards**
- **Validation**: Comprehensive data validation with detailed error reporting
- **Error Handling**: Graceful handling of missing or malformed data
- **Logging**: Detailed logging for debugging and monitoring
- **Documentation**: All data transformations thoroughly documented

### **File Format Standards**
- **Primary**: Parquet files for performance (similarity matrices)
- **Compatibility**: CSV files for human readability and tool compatibility
- **Metadata**: JSON files with processing information and validation results

---

## 🏢 **DEPLOYMENT CONTEXT**

### **Local Desktop Application Environment**
- **Single-User Local Server**: Application runs on each user's laptop as a local Flask server
- **Corporate Network Restrictions**: Designed for environments with limited external connectivity  
- **Desktop-Only Focus**: No mobile responsiveness or multi-device considerations required
- **Simplified Architecture**: No caching, load balancing, security hardening, or multi-user features needed
- **Direct Database Access**: SQLite files stored locally with direct filesystem access

### **Simplified Development Requirements**
- **No Mobile Support**: Design exclusively for desktop browser experience (1024px+ screens)
- **No Accessibility Requirements**: Standard desktop usability is sufficient
- **No Security Hardening**: Local-only deployment removes external threat vectors
- **No Performance Scaling**: Single-user environment with local database access
- **No User Onboarding**: Users are trained NAB employees with domain knowledge

---

## 🎯 **USER EXPERIENCE PRINCIPLES**

### **Design Philosophy**
- **Clean, minimal, professional SaaS aesthetic** - Inspired by Eightfold.ai, Gloat, and modern SaaS platforms
- **Data-driven and analytical** (not marketing-focused)
- **Enterprise-grade credibility** with modern usability
- **NAB heritage** through selective red accents on black foundation
- **Sophisticated and trustworthy** with focus on clarity over decoration
- **Desktop-optimised** design patterns (no mobile responsiveness required)

### **Interaction Patterns**
- **Search-First**: Powerful search functionality as primary navigation
- **Progressive Disclosure**: Show overview first, details on demand
- **Context Preservation**: Always show JobProfileID for colleague reference
- **Feedback Loops**: Clear progress indicators and success/error states
- **Contextual Help**: '?' icons with hover tooltips for complex metrics and business concepts

### **Help Icon UI Pattern**
Standard help icon implementation for providing contextual explanations:

```html
<!-- Standard help icon with tooltip -->
<div class="relative">
    <button class="text-gray-400 hover:text-blue-600 transition-colors duration-200 group">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"></path>
        </svg>
        <div class="absolute left-0 bottom-full mb-3 w-72 px-4 py-3 bg-slate-800 text-white text-sm leading-relaxed rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-all duration-300 z-20 border border-slate-600 pointer-events-none text-left">
            <div class="font-medium text-slate-100 mb-1">Metric Title</div>
            <div class="text-slate-200">Detailed explanation of the metric, its calculation, and business context.</div>
            <div class="absolute top-full left-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-800"></div>
        </div>
    </button>
</div>
```

**Help Icon Usage Guidelines**:
- Use for complex business metrics requiring explanation
- Include metric title and contextual business explanation
- Position tooltips to avoid UI collisions
- Keep explanations concise but comprehensive

### **Content Guidelines**

**Language Standards**:
- **UK English**: All content uses British spelling and terminology throughout
  - "Analyse" not "Analyze", "Organisation" not "Organization"
  - "Colour" not "Color", "Centre" not "Center"
  - "Realise" not "Realize", "Optimise" not "Optimize"
- **Professional tone**: Suitable for enterprise environment
- **Data-focused language**: Emphasise insights and evidence
- **Action-oriented button text**: Clear, specific calls-to-action
- **Clear, concise descriptions**: Avoid jargon and ambiguity

**Terminology Standards**:
- Use "Skills" not "Competencies"
- Use "Job Profiles" not "Roles" 
- Use "Career Pathways" not "Career Paths"
- Use "Similarity Score" not "Match Percentage"
- Use "JobProfileID" for technical references
- Use standardised display names from JobDisplayManager for user-facing content

---

## 🔄 **DEVELOPMENT WORKFLOW**

### **Code Quality Gates**
1. **Functionality**: Feature works as specified
2. **Performance**: No regression in response times
3. **Desktop Compatibility**: Works on standard desktop browsers (Chrome, Firefox, Safari, Edge)
4. **UK English**: All text content uses British spelling and terminology

### **Documentation Requirements**
- **Code Comments**: Complex business logic explained inline
- **API Documentation**: All endpoints documented with examples
- **User Guides**: End-user documentation for new features
- **Architecture Decisions**: Document significant technical choices

### **Testing Standards**
- **Unit Tests**: Core business logic tested
- **Integration Tests**: API endpoints validated
- **User Acceptance**: Manual testing with real users
- **Performance Tests**: Load testing for critical paths

### **Component Development Workflow**
1. **Design in Isolation**: Create components in `/components` page first, test with sample data, ensure desktop usability
2. **Integration**: Move successful components to main pages, maintain consistency across implementations, document any variations needed  
3. **Testing**: Test with real database data, verify performance with large datasets, ensure desktop browser compatibility

---

## 🚨 **COMMON PITFALLS TO AVOID**

### **CSS/JavaScript Issues**
- ❌ **Avoid**: Custom CSS that conflicts with Tailwind utilities
- ❌ **Avoid**: Hardcoded job title construction (use JobDisplayManager)
- ❌ **Avoid**: Framework dependencies (stick to vanilla JavaScript)
- ❌ **Avoid**: Inline styles (use Tailwind classes)

### **Backend Issues**
- ❌ **Avoid**: Manual job display name construction
- ❌ **Avoid**: Direct database queries without parameterisation
- ❌ **Avoid**: Missing error handling in API endpoints
- ❌ **Avoid**: Loading large datasets without chunking

### **Data Quality Issues**
- ❌ **Avoid**: Hardcoded assumptions about data structure
- ❌ **Avoid**: Missing validation for user inputs
- ❌ **Avoid**: Ignoring null values in database queries
- ❌ **Avoid**: Data duplication across systems

---

## 📚 **KEY ARCHITECTURAL PATTERNS**

### **1. JobDisplayManager Integration**
**Always use JobDisplayManager for consistent job naming across the platform.**

### **2. Unified Search Module**
**All pages use `window.SkillEngine.SearchModule` with `/api/career-analysis-jobs` endpoint.**

### **3. Progress Tracking**
**Long operations use ProgressTracker with tqdm for user feedback.**

### **4. Error Boundaries**
**All components handle errors gracefully with meaningful user feedback.**

### **5. Desktop-Optimised Design**
**Design for desktop browsers with 1024px+ screen width as primary target.**

---

## 🎯 **SUCCESS CRITERIA**

### **Technical Excellence**
- **Performance**: Sub-100ms API responses for career pathway queries
- **Reliability**: Stable local server operation for single-user sessions
- **Maintainability**: Clear, documented, modular codebase
- **UK English**: Consistent British spelling and terminology throughout

### **User Experience**
- **Usability**: Intuitive navigation requiring minimal training
- **Desktop Optimisation**: Optimal experience on desktop browsers
- **Professional Quality**: Executive-ready outputs and presentation
- **Consistency**: Unified experience across all platform components

### **Business Value**
- **Data Quality**: Accurate, up-to-date skills and job information
- **Strategic Insights**: Actionable recommendations for workforce planning
- **Efficiency**: Reduced time-to-insight for HR teams
- **Adoption**: High user engagement and platform utilisation

---

## 🔄 **DOCUMENT MAINTENANCE**

This document should be updated when:
- **New architectural patterns** are established
- **Technology stack changes** are made
- **Design system updates** are implemented
- **Performance standards** are modified
- **User experience principles** evolve

**Next Review**: Quarterly or after major releases

---

**Remember**: This platform serves strategic workforce planning decisions. Every design choice should reflect professional quality, data accuracy, and user trust. When in doubt, prioritise clarity, performance, and accessibility.
