# Career Analysis Report - User Configuration Specification

**Document Version**: 1.0  
**Created**: 2025-01-26  
**Purpose**: Define user configuration options for career analysis report generation  
**Audience**: LLM assistants, developers, UI/UX designers  

---

## 🎯 **Overview**

This document specifies the user configuration interface for generating career transition analysis reports. Users must configure 6 core parameters before report generation, each with specific business logic and validation rules.

---

## 📋 **Configuration Parameters**

### **1. Source Job Selection**
**Purpose**: Select the starting job profile for career pathway analysis

> **Implementation Prompt**: Create a unified job search component that leverages the existing search infrastructure. This component should integrate with the established `JobDisplayManager` system and provide consistent search behavior across all career analysis workflows.

#### **Existing Codebase Integration**
**Files to Reference**:
- **Search API**: `src/skill_similarity_engine/webapp/api/career_analysis_api.py` - `/api/career-analysis-jobs` endpoint
- **Display Management**: `src/skill_similarity_engine/utils/display.py` - `JobDisplayManager` class with `DisplayFormat.SEARCH`
- **Search Module**: `src/skill_similarity_engine/webapp/static/js/modules/search-module.js` - existing search logic
- **Database Service**: `src/skill_similarity_engine/webapp/services/job_service.py` - job data retrieval

#### **Implementation Requirements**
**Interface**: Search bar with autocomplete
- **Input Type**: Typeahead search with live results
- **Data Source**: `/api/career-analysis-jobs` endpoint (existing)
- **Search Behaviour**: 
  - Minimum 2 characters to trigger search
  - Searches across job titles, JobProfileIDs, and job functions
  - Returns top 10 matches by relevance
  - Displays using `JobDisplayManager.SEARCH` format

**Display Format** (via `JobDisplayManager`):
```
Data Scientist - UNGRADED (Group 3) - R0041.4
Senior Analyst - Banking Services - Group 2 - R0125.8
```

#### **JavaScript Integration Pattern**
```javascript
// Extend existing search-module.js
window.SkillEngine.SearchModule.initCareerAnalysisSearch({
    containerId: 'job-search-container',
    apiEndpoint: '/api/career-analysis-jobs',
    displayFormat: 'search',
    onSelection: function(selectedJob) {
        // Update form state with selected job
        updateFormField('job_from', selectedJob.job_profile_id);
    }
});
```

**Validation**:
- ✅ **Required**: Must select a valid job profile
- ✅ **Existence Check**: JobProfileID must exist in database
- ❌ **Error States**: "Please select a starting job profile"

**Default Behaviour**: No default selection - forces intentional choice

---

### **2. Analysis Mode**
**Purpose**: Define the type of career pathway analysis to perform

> **Implementation Prompt**: Build upon the existing analysis mode architecture already implemented in the `CareerAnalysisService`. This component should leverage the proven workflow patterns and maintain compatibility with the existing generator system while providing clear UI distinction between analysis types.

#### **Existing Codebase Integration**
**Files to Reference**:
- **Core Service**: `src/skill_similarity_engine/webapp/career_analysis/services/career_analysis_service.py` - `generate_analysis()` method with `analysis_mode` parameter
- **Generator Classes**: 
  - `src/skill_similarity_engine/webapp/career_analysis/src/executive_summary_generator.py` - `ExecutiveSummaryGenerator` class
  - `src/skill_similarity_engine/webapp/career_analysis/src/pathway_analysis_generator.py` - `PathwayAnalysisGenerator` class
  - `src/skill_similarity_engine/webapp/career_analysis/src/specific_transition_analyzer.py` - `SpecificTransitionAnalyzer` class
- **Templates**: `src/skill_similarity_engine/webapp/career_analysis/templates/sections/` - YAML templates with mode-specific logic
- **API Handler**: `src/skill_similarity_engine/webapp/api/career_analysis_api.py` - existing POST endpoint structure

#### **Implementation Requirements**
**Interface**: Radio button selection with descriptive text

**Options**:

#### **Top Discovery Mode** (Default)
- **Label**: "Top {n} Discovery"
- **Description**: "Analyzes the top {n} most similar career opportunities within your similarity range. Perfect for exploring career possibilities and workforce planning."
- **Business Logic**: Finds highest similarity matches across all job profiles
- **Generator Integration**: Uses `analysis_mode='top_matches'` in `CareerAnalysisService.generate_analysis()`
- **Use Case**: Exploratory analysis, workforce planning, general career guidance

#### **Specific Transition Mode**
- **Label**: "Specific Transition Analysis"
- **Description**: "Detailed analysis of transition requirements between two specific roles. Ideal for targeted career planning and skills gap assessment."
- **Business Logic**: Direct comparison between source job and user-selected target job
- **Generator Integration**: Uses `analysis_mode='specific'` with `job_to` parameter
- **Additional UI**: Reveals second job search bar when selected (reuse search component from parameter 1)
- **Use Case**: Targeted transition planning, skills gap analysis

#### **Conditional UI Logic**
```javascript
// Extend career-analysis.js
function handleAnalysisModeChange(selectedMode) {
    const targetJobContainer = document.getElementById('target-job-container');
    const pathwaysCountField = document.getElementById('pathways-count');
    
    if (selectedMode === 'specific_transition') {
        targetJobContainer.style.display = 'block';
        pathwaysCountField.disabled = true; // Always 1 for specific
        pathwaysCountField.value = 1;
    } else {
        targetJobContainer.style.display = 'none';
        pathwaysCountField.disabled = false;
    }
}
```

**Validation**:
- ✅ **Required**: Must select one mode
- ✅ **Conditional**: If "Specific Transition" selected, target job must be chosen
- ✅ **Service Integration**: Mode value must match `CareerAnalysisService` expected parameters

---

### **3. Number of Pathways**
**Purpose**: Control how many career opportunities to analyze in detail

> **Implementation Prompt**: Integrate with the existing pathway generation system that already handles variable pathway counts. This component should respect the performance limitations of the report generation system while providing meaningful choice to users for analysis depth.

#### **Existing Codebase Integration**
**Files to Reference**:
- **Service Method**: `src/skill_similarity_engine/webapp/career_analysis/services/career_analysis_service.py` - `generate_analysis()` method accepts `top_n` parameter
- **Pathway Generator**: `src/skill_similarity_engine/webapp/career_analysis/src/pathway_analysis_generator.py` - `PathwayAnalysisGenerator.generate()` method processes `top_n` parameter
- **Ordering Utils**: `src/skill_similarity_engine/webapp/career_analysis/src/pathway_ordering_utils.py` - `PathwayOrderingManager.get_top_pathways_ordered()` with `limit` parameter
- **Executive Generator**: `src/skill_similarity_engine/webapp/career_analysis/src/executive_summary_generator.py` - summary generation scales with pathway count
- **Templates**: `src/skill_similarity_engine/webapp/career_analysis/templates/sections/pathway_analysis.yaml` - template loops handle variable pathway counts

#### **Implementation Requirements**
**Interface**: Number input with slider (optional visual enhancement)

**Configuration**:
- **Range**: 1-10 pathways
- **Default**: 3 pathways (matches existing system defaults)
- **Step**: 1
- **Display**: Number input with validation

**Business Logic**:
- **Top Discovery**: Analyzes top N highest similarity matches via `PathwayOrderingManager`
- **Specific Transition**: Always analyzes exactly 1 pathway (this field disabled via JavaScript)

#### **Integration with Existing Generator System**
```javascript
// Form submission integration
function buildAnalysisRequest() {
    const analysisMode = getSelectedAnalysisMode();
    const formData = {
        // ... other parameters
        top_n: analysisMode === 'specific_transition' ? 1 : 
               parseInt(document.getElementById('pathways-count').value),
        // ... other parameters
    };
    
    // Validates against CareerAnalysisService.generate_analysis() signature
    return formData;
}
```

**Performance Considerations**:
- **Generator Impact**: Each additional pathway requires full skills analysis and template rendering
- **Database Queries**: Pathway generation scales with similarity calculations
- **Report Length**: More pathways = significantly longer documents (especially with V2 analytics)

**Validation**:
- ✅ **Range Check**: Must be between 1-10 (aligns with template capacity)
- ✅ **Integer**: Must be whole number
- ✅ **Mode Integration**: Disabled/forced to 1 for specific transition mode
- ❌ **Error States**: "Please select between 1-10 pathways"

**Labels**:
- **Input Label**: "Number of Pathways"
- **Help Text**: "Choose how many career opportunities to analyze (1-10)"

---

### **4. Similarity Range**
**Purpose**: Filter career opportunities by similarity percentage to focus analysis

> **Implementation Prompt**: Build a sophisticated range selector that integrates with the existing similarity calculation infrastructure. This component should respect the performance characteristics of the similarity engine while providing meaningful filtering capabilities that align with business logic for viable career transitions.

#### **Existing Codebase Integration**
**Files to Reference**:
- **Service Integration**: `src/skill_similarity_engine/webapp/career_analysis/services/career_analysis_service.py` - `generate_analysis()` method accepts `similarity_min` and `similarity_max` parameters
- **Pathway Ordering**: `src/skill_similarity_engine/webapp/career_analysis/src/pathway_ordering_utils.py` - `PathwayOrderingManager.get_top_pathways_ordered()` with `similarity_range` parameter
- **SQL Queries**: `src/skill_similarity_engine/webapp/career_analysis/sql/` - similarity threshold queries filter by range
- **Thresholds Logic**: `src/skill_similarity_engine/webapp/career_analysis/content/thresholds.py` - existing business logic for similarity categorisation
- **Dynamic Thresholds**: `src/skill_similarity_engine/webapp/career_analysis/content/dynamic_thresholds.py` - adaptive similarity range logic

#### **Implementation Requirements**
**Interface**: Dual-handle range slider with numeric inputs

**Configuration**:
- **Minimum Boundary**: 0% - 100%
- **Maximum Boundary**: 0% - 100%
- **Default Range**: 0% - 95% (aligns with existing system defaults)
- **Step Size**: 5% (matches similarity calculation precision)
- **Validation**: Minimum must be less than maximum

**Business Logic** (from existing system):
- **Excludes 100% matches**: Identical roles provide no transition value (established in `PathwayOrderingManager`)
- **Excludes very low matches**: Below 40% typically non-viable (per `thresholds.py` logic)
- **Focus on viable transitions**: 40%-95% represents realistic career moves (validated in existing reports)

#### **Integration with Similarity Engine**
```javascript
// Integration with existing similarity calculation system
function buildSimilarityRange() {
    const minValue = parseInt(document.getElementById('min-similarity').value);
    const maxValue = parseInt(document.getElementById('max-similarity').value);
    
    return {
        similarity_min: minValue,
        similarity_max: maxValue,
        // Format matches CareerAnalysisService.generate_analysis() expectations
        similarity_range: (minValue/100.0, maxValue/100.0)  // Converted to decimal for PathwayOrderingManager
    };
}
```

**Interface Elements**:
```html
<!-- Range Slider with dual inputs -->
<div class="similarity-range-control">
  <label>Similarity Range</label>
  <div class="range-slider-container">
    <input type="range" min="0" max="100" value="0" id="min-similarity">
    <input type="range" min="0" max="100" value="95" id="max-similarity">
  </div>
  <div class="range-inputs">
    <input type="number" min="0" max="100" value="0" placeholder="Min %">
    <input type="number" min="0" max="100" value="95" placeholder="Max %">
  </div>
  <div class="help-text">
    Focus on meaningful transitions. Excludes identical matches (100%) and very low matches for viable career pathways.
  </div>
</div>
```

**Performance Impact**:
- **Database Filtering**: Range filtering happens at SQL level for optimal performance
- **Similarity Matrix**: Pre-computed similarities are filtered, not recalculated
- **Template Rendering**: Fewer pathways to process when range is restrictive

**Validation**:
- ✅ **Range Logic**: Minimum < Maximum
- ✅ **Boundary Check**: Both values 0-100%
- ✅ **Service Integration**: Values passed directly to `CareerAnalysisService`
- ❌ **Error States**: "Maximum similarity must be greater than minimum"

---

### **5. Primary Similarity Algorithm**
**Purpose**: Choose which similarity algorithm determines the ranking order of results

> **Implementation Prompt**: Implement the dual-similarity architecture that's partially built in the existing system. This component should leverage the existing similarity calculation infrastructure while providing clear transparency about algorithmic choices and their impact on result ordering.

#### **Existing Codebase Integration**
**Files to Reference**:
- **Service Parameter**: `src/skill_similarity_engine/webapp/career_analysis/services/career_analysis_service.py` - method should accept `primary_algorithm` parameter (to be added)
- **Preview Service**: `src/skill_similarity_engine/webapp/career_analysis/services/preview_service.py` - `_get_dual_similarity_analysis()` method handles both algorithms
- **Pathway Ordering**: `src/skill_similarity_engine/webapp/career_analysis/src/pathway_ordering_utils.py` - `PathwayOrderingManager` should be enhanced to support algorithm selection
- **V2 Analytics**: All V2 analytics tables (`analytics_job_similarities`) contain both Enhanced and Literal scores
- **Database Schema**: `docs/sqlite_schema_design_schema.md` - dual similarity columns in V2 tables

#### **Implementation Requirements**
**Interface**: Radio button selection with algorithmic transparency

**Critical Distinction**: This controls **ranking order**, not **data availability**. Both similarity scores are **always calculated and displayed** regardless of selection.

#### **Enhanced Skill Matching** (Default/Recommended)
- **Algorithm**: V2 rarity-weighted similarity
- **Label**: "Enhanced Skill Matching (Recommended)"
- **Description**: "V2 rarity-weighted algorithm emphasizing defining skills and strategic value. Identifies high-impact career opportunities beyond basic overlap."
- **Business Logic**: 
  - Results ranked by Enhanced similarity score (highest to lowest)
  - Literal similarity score still calculated and displayed
  - Strategic intelligence prioritised
- **Data Source**: Enhanced scores from V2 analytics tables

#### **Literal Skill Overlap**
- **Algorithm**: Traditional Jaccard similarity
- **Label**: "Literal Skill Overlap (Traditional)"
- **Description**: "Standard Jaccard similarity treating all skills equally. Intuitive and straightforward - shows pure skill overlap percentage between roles."
- **Business Logic**:
  - Results ranked by Literal similarity score (highest to lowest)
  - Enhanced similarity score still calculated and displayed
  - Pure mathematical overlap prioritised
- **Data Source**: Literal scores from existing similarity matrices

#### **Service Integration Pattern**
```python
# Enhancement to CareerAnalysisService.generate_analysis()
def generate_analysis(self, job_from: str, analysis_mode: str = 'top_matches', 
                     primary_algorithm: str = 'enhanced', **kwargs) -> Dict[str, Any]:
    """
    Generate analysis with algorithm-specific pathway ordering.
    
    Args:
        primary_algorithm: 'enhanced' or 'literal' - determines ranking order
    """
    # Pass to PathwayOrderingManager for dual-algorithm sorting
    ordering_manager = PathwayOrderingManager(self.db)
    pathways = ordering_manager.get_top_pathways_ordered(
        job_from=job_from,
        limit=top_n,
        primary_algorithm=primary_algorithm,  # New parameter
        # ... other params
    )
```

**Transparency Guarantee**:
```html
<div class="transparency-notice">
  <h4>Transparency Guarantee</h4>
  <p>Both similarity scores are always displayed in results regardless of your selection. Your choice determines ranking order while maintaining full algorithmic transparency.</p>
</div>
```

**Result Display Impact**:
- **Enhanced Primary**: Results ordered by Enhanced score, both scores shown
- **Literal Primary**: Results ordered by Literal score, both scores shown

**Validation**:
- ✅ **Required**: Must select one algorithm
- ✅ **Default**: Enhanced Skill Matching pre-selected
- ✅ **Service Integration**: Value passed to enhanced `generate_analysis()` method

---

### **6. V2 Enhanced Analytics**
**Purpose**: Enable advanced analytics features for deeper strategic insights

> **Implementation Prompt**: Integrate with the existing V2 analytics infrastructure that's already built into the PreviewService. This component should leverage the V2 database tables and methods while providing granular control over which advanced features are included in the analysis. Each feature represents a significant performance and content enhancement.

#### **Existing Codebase Integration**
**Files to Reference**:
- **Core Service**: `src/skill_similarity_engine/webapp/career_analysis/services/preview_service.py` - all `_get_*_data()` methods for V2 features
- **Service Integration**: `src/skill_similarity_engine/webapp/career_analysis/services/career_analysis_service.py` - should accept `v2_analytics` dictionary parameter
- **Database Schema**: `docs/sqlite_schema_design_schema.md` - all V2 analytics tables
- **V2 Analytics Tables**: 
  - `analytics_job_defining_skills` - defining skills analysis
  - `analytics_job_families` - job family context
  - `analytics_movement_patterns` - movement patterns
  - `analytics_skill_rarity` - skills rarity analysis
  - `analytics_job_similarities` - dual similarity analysis
- **API Integration**: `src/skill_similarity_engine/webapp/api/career_analysis_api.py` - V2 parameters handling

#### **Implementation Requirements**
**Interface**: Checkbox group with feature descriptions

**Features Available**:

#### **Defining Skills Analysis**
- **Checkbox**: "Defining Skills Analysis"
- **Description**: "Critical skills that most strongly characterise role success"
- **Data Source**: `analytics_job_defining_skills` table
- **Method Integration**: `PreviewService._get_defining_skills_data()`
- **Output**: Skills rarity analysis, importance rankings

#### **Job Family Context**
- **Checkbox**: "Job Family Context"
- **Description**: "Clustering intelligence and family membership insights"
- **Data Source**: `analytics_job_families` table
- **Method Integration**: `PreviewService._get_job_family_data()`
- **Output**: Related roles, career progression patterns

#### **Historical Movement Patterns**
- **Checkbox**: "Historical Movement Patterns"
- **Description**: "Real movement data showing career transition patterns"
- **Data Source**: `analytics_movement_patterns` table
- **Method Integration**: `PreviewService._get_movement_patterns_data()`
- **Output**: Transition success rates, common pathways

#### **Skills Rarity Analysis**
- **Checkbox**: "Skills Rarity Analysis"
- **Description**: "Skill prevalence and rarity categorisation insights"
- **Data Source**: `analytics_skill_rarity` table
- **Method Integration**: `PreviewService._get_skills_rarity_data()`
- **Output**: Market scarcity metrics, strategic value

#### **Transition Insights**
- **Checkbox**: "Transition Insights"
- **Description**: "Advanced career transition intelligence and strategic recommendations"
- **Data Source**: Multiple V2 analytics tables
- **Method Integration**: `PreviewService._get_transition_insights_data()`
- **Output**: Strategic recommendations, transition difficulty

#### **Dual Similarity Analysis**
- **Checkbox**: "Dual Similarity Analysis"
- **Description**: "Compare basic vs enhanced similarity scores with strategic insights"
- **Data Source**: Computed similarity matrices
- **Method Integration**: `PreviewService._get_dual_similarity_analysis()`
- **Output**: Algorithm comparison, strategic premium analysis

#### **Service Integration Pattern**
```javascript
// Form data structure for V2 analytics
function buildV2AnalyticsConfig() {
    return {
        v2_analytics: {
            defining_skills: document.getElementById('v2-defining-skills').checked,
            job_family_context: document.getElementById('v2-job-family').checked,
            movement_patterns: document.getElementById('v2-movement-patterns').checked,
            skills_rarity: document.getElementById('v2-skills-rarity').checked,
            transition_insights: document.getElementById('v2-transition-insights').checked,
            dual_similarity_analysis: document.getElementById('v2-dual-similarity').checked
        }
    };
    // Matches PreviewService._generate_v2_analytics() expected parameter structure
}
```

#### **Performance Considerations**
- **Database Impact**: Each feature requires additional V2 table queries
- **Report Length**: V2 analytics significantly expand report content
- **Processing Time**: V2 features add 10-30 seconds to generation time
- **Memory Usage**: V2 data structures require additional memory allocation

**Default State**: All V2 analytics enabled (6/6 selected) - matches existing system behavior

**Validation**:
- ✅ **Optional**: Can be all enabled, all disabled, or mixed
- ✅ **Performance**: No impact on core analysis if disabled
- ✅ **Additive**: Each feature adds complementary intelligence
- ✅ **Service Integration**: Config passed directly to `PreviewService._generate_v2_analytics()`

---

## 🎨 **User Interface Design**

### **Layout Structure**
```html
<div class="career-analysis-configuration">
  <!-- 1. Source Job Selection -->
  <section class="config-section">
    <label class="config-label required">Source Job Profile</label>
    <div class="search-container">
      <!-- Typeahead search component -->
    </div>
  </section>

  <!-- 2. Analysis Mode -->
  <section class="config-section">
    <label class="config-label required">Analysis Mode</label>
    <div class="radio-group">
      <!-- Radio button options with descriptions -->
    </div>
  </section>

  <!-- 3. Number of Pathways -->
  <section class="config-section">
    <label class="config-label required">Number of Pathways</label>
    <div class="number-input-container">
      <!-- Number input with validation -->
    </div>
  </section>

  <!-- 4. Similarity Range -->
  <section class="config-section">
    <label class="config-label required">Similarity Range</label>
    <div class="range-slider-container">
      <!-- Dual-handle range slider -->
    </div>
  </section>

  <!-- 5. Primary Algorithm -->
  <section class="config-section">
    <label class="config-label required">Primary Ranking Algorithm</label>
    <div class="radio-group">
      <!-- Algorithm selection with transparency notice -->
    </div>
  </section>

  <!-- 6. V2 Analytics -->
  <section class="config-section">
    <label class="config-label">Enhanced V2 Analytics</label>
    <div class="checkbox-group">
      <!-- Feature checkboxes with descriptions -->
    </div>
  </section>

  <!-- Action Buttons -->
  <div class="action-buttons">
    <button class="btn-primary" type="submit">Generate Analysis Report</button>
    <button class="btn-secondary" type="button">Preview Configuration</button>
  </div>
</div>
```

### **Responsive Behaviour**
- **Desktop (1024px+)**: Two-column layout for compact presentation
- **Tablet (768-1024px)**: Single column with optimized spacing
- **Mobile**: Not required (desktop-only deployment)

### **Visual Design Standards**
- **Spacing**: `space-y-6` between sections, `space-y-3` within sections
- **Typography**: Section labels use `font-epilogue font-medium text-lg`
- **Colors**: Required fields marked with red asterisk (`text-red-600`)
- **Validation**: Error states use red borders and error text

---

## 🔧 **Technical Implementation**

### **Form Data Structure**
```javascript
const formData = {
  // Required fields
  job_from: "R0041.4",                    // JobProfileID
  analysis_mode: "top_matches",           // "top_matches" | "specific_transition"
  top_n: 3,                               // 1-10
  similarity_min: 0,                      // 0-100
  similarity_max: 95,                     // 0-100
  primary_algorithm: "enhanced",          // "enhanced" | "literal"
  
  // Optional V2 analytics
  v2_analytics: {
    defining_skills: true,
    job_family_context: true,
    movement_patterns: true,
    skills_rarity: true,
    transition_insights: true,
    dual_similarity_analysis: true
  },
  
  // Conditional field (specific transition mode only)
  job_to: "R0125.8"                      // JobProfileID (if specific_transition)
}
```

### **Validation Logic**
```javascript
function validateConfiguration(formData) {
  const errors = [];
  
  // Required field validation
  if (!formData.job_from) {
    errors.push("Source job profile is required");
  }
  
  if (!formData.analysis_mode) {
    errors.push("Analysis mode is required");
  }
  
  // Specific transition validation
  if (formData.analysis_mode === "specific_transition" && !formData.job_to) {
    errors.push("Target job profile required for specific transition analysis");
  }
  
  // Range validation
  if (formData.similarity_min >= formData.similarity_max) {
    errors.push("Maximum similarity must be greater than minimum");
  }
  
  // Numeric validation
  if (formData.top_n < 1 || formData.top_n > 10) {
    errors.push("Number of pathways must be between 1 and 10");
  }
  
  return {
    isValid: errors.length === 0,
    errors: errors
  };
}
```

### **API Endpoint Integration**
```javascript
// Form submission
async function submitAnalysisRequest(formData) {
  const validation = validateConfiguration(formData);
  
  if (!validation.isValid) {
    displayValidationErrors(validation.errors);
    return;
  }
  
  try {
    const response = await fetch('/api/career-analysis-generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    });
    
    if (response.ok) {
      const result = await response.json();
      displayAnalysisResults(result);
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  } catch (error) {
    displayErrorMessage(`Failed to generate analysis: ${error.message}`);
  }
}
```

---

## 📊 **Result Display Impact**

### **Algorithm Selection Impact**

#### **Enhanced Primary Ranking**
```
Results ordered by Enhanced similarity score (descending):

1. Executive Director - 87.3% Enhanced | 72.1% Literal
2. Senior Manager - 84.6% Enhanced | 78.9% Literal  
3. Team Leader - 82.1% Enhanced | 81.2% Literal
```

#### **Literal Primary Ranking**
```
Results ordered by Literal similarity score (descending):

1. Team Leader - 81.2% Literal | 82.1% Enhanced
2. Senior Manager - 78.9% Literal | 84.6% Enhanced
3. Executive Director - 72.1% Literal | 87.3% Enhanced
```

**Key Point**: Same data, different ordering. Both scores always visible.

### **V2 Analytics Integration**
When V2 analytics enabled, each career opportunity includes:
- **Defining Skills**: Top 10 role-defining skills with rarity scores
- **Job Family**: Related roles and progression patterns
- **Movement Data**: Historical transition success rates
- **Skills Rarity**: Market scarcity insights
- **Strategic Intelligence**: Advanced recommendations
- **Dual Comparison**: Algorithm difference analysis

---

## 🎯 **User Experience Considerations**

### **Progressive Disclosure**
- **Essential First**: Show required configuration options prominently
- **Advanced Features**: V2 analytics clearly labeled as "Enhanced" features
- **Contextual Help**: Tooltips and help text for complex concepts

### **Smart Defaults**
- **Analysis Mode**: "Top Discovery" (most common use case)
- **Number of Pathways**: 3 (optimal cognitive load)
- **Similarity Range**: 0%-95% (excludes identical matches)
- **Primary Algorithm**: "Enhanced" (strategic value prioritised)
- **V2 Analytics**: All enabled (comprehensive analysis)

### **Error Prevention**
- **Real-time Validation**: Immediate feedback on invalid inputs
- **Range Constraints**: UI prevents invalid range selections
- **Clear Requirements**: Visual indication of required fields
- **Helpful Defaults**: Sensible starting values reduce errors

### **Performance Feedback**
- **Configuration Summary**: Preview of analysis scope before generation
- **Progress Indicators**: Clear feedback during analysis generation
- **Time Estimates**: Expected completion time based on configuration
- **Cancellation**: Ability to cancel long-running analysis

---

## 🔄 **Future Enhancements**

### **Saved Configurations**
- **Configuration Presets**: Save frequently used analysis configurations
- **Team Templates**: Organization-wide configuration templates
- **Recent Analyses**: Quick access to recently generated analyses

### **Advanced Filtering**
- **Job Function Filter**: Limit analysis to specific functional areas
- **Management Level**: Filter by organizational hierarchy
- **Geographic Location**: Location-based opportunity filtering
- **Division Focus**: Analyze within specific business divisions

### **Collaborative Features**
- **Shared Configurations**: Team collaboration on analysis parameters
- **Approval Workflows**: Management review before analysis generation
- **Comment System**: Collaborative discussion on analysis results

---

## 🗺️ **Implementation Roadmap**

### **Phase 1: Core Configuration Components (Week 1)**

#### **Priority 1: Search Integration**
**Files to Modify/Create**:
- Extend `src/skill_similarity_engine/webapp/static/js/modules/search-module.js`
- Update `src/skill_similarity_engine/webapp/templates/career_analysis.html`
- Ensure `src/skill_similarity_engine/webapp/api/career_analysis_api.py` handles job selection

**Implementation Tasks**:
1. Create unified search component leveraging existing `JobDisplayManager`
2. Integrate with `/api/career-analysis-jobs` endpoint
3. Implement job selection state management
4. Add validation for required job selection

#### **Priority 2: Analysis Mode & Pathways**
**Files to Modify**:
- `src/skill_similarity_engine/webapp/static/js/career-analysis.js`
- `src/skill_similarity_engine/webapp/career_analysis/services/career_analysis_service.py`

**Implementation Tasks**:
1. Build radio button interface for analysis modes
2. Implement conditional UI for specific transition mode
3. Create number input with validation for pathway count
4. Ensure compatibility with existing `generate_analysis()` parameters

### **Phase 2: Advanced Configuration (Week 2)**

#### **Priority 3: Similarity Range & Algorithm Selection**
**Files to Modify/Create**:
- Create dual-handle range slider component
- Enhance `src/skill_similarity_engine/webapp/career_analysis/src/pathway_ordering_utils.py`
- Update `src/skill_similarity_engine/webapp/career_analysis/services/career_analysis_service.py`

**Implementation Tasks**:
1. Build sophisticated range slider with validation
2. Implement algorithm selection with transparency guarantees
3. Enhance `PathwayOrderingManager` to support dual-algorithm sorting
4. Add `primary_algorithm` parameter to `generate_analysis()` method

#### **Priority 4: V2 Analytics Integration**
**Files to Verify/Enhance**:
- `src/skill_similarity_engine/webapp/career_analysis/services/preview_service.py` (existing V2 methods)
- Database connectivity to V2 analytics tables per `docs/sqlite_schema_design_schema.md`

**Implementation Tasks**:
1. Create checkbox group interface for V2 features
2. Validate all `PreviewService._get_*_data()` methods work correctly
3. Implement granular V2 feature control
4. Add performance monitoring for V2 feature impact

### **Phase 3: Form Integration & Submission (Week 3)**

#### **Priority 5: Complete Form Architecture**
**Files to Create/Modify**:
- Enhanced `src/skill_similarity_engine/webapp/static/js/career-analysis.js`
- Updated `src/skill_similarity_engine/webapp/api/career_analysis_api.py`
- Modified `src/skill_similarity_engine/webapp/templates/career_analysis.html`

**Implementation Tasks**:
1. Build complete form validation system
2. Implement form state management
3. Create progress indicators and loading states
4. Add error handling and user feedback

#### **Priority 6: Backend Service Integration**
**Files to Modify**:
- `src/skill_similarity_engine/webapp/career_analysis/services/career_analysis_service.py`
- `src/skill_similarity_engine/webapp/career_analysis/services/validation_service.py`

**Implementation Tasks**:
1. Enhance `CareerAnalysisService` to accept all new parameters
2. Update `ValidationService` for comprehensive form validation
3. Ensure backward compatibility with existing generators
4. Add comprehensive error handling and logging

### **Phase 4: Testing & Optimization (Week 4)**

#### **Priority 7: Performance & Reliability**
**Testing Focus**:
- Load testing with various configuration combinations
- V2 analytics performance impact measurement
- Error handling for edge cases
- Database query optimization

#### **Priority 8: User Experience Polish**
**Enhancement Focus**:
- Responsive design verification
- Accessibility compliance (WCAG AA)
- Help text and tooltips
- Progressive disclosure optimization

### **Critical Integration Points**

#### **Existing System Compatibility**
- ✅ **Maintain**: All existing `CareerAnalysisService` functionality
- ✅ **Extend**: Generator classes (`ExecutiveSummaryGenerator`, `PathwayAnalysisGenerator`, etc.)
- ✅ **Preserve**: YAML template system and existing content generation
- ✅ **Enhance**: `JobDisplayManager` integration throughout

#### **Database Dependencies**
- ✅ **V2 Tables**: Verify all V2 analytics tables exist and are populated
- ✅ **Query Performance**: Ensure V2 queries are optimized
- ✅ **Data Quality**: Validate V2 data completeness
- ✅ **Schema Compliance**: Align with `docs/sqlite_schema_design_schema.md`

#### **Performance Benchmarks**
- **Configuration Load**: < 2 seconds for initial form load
- **Validation Response**: < 100ms for form validation feedback
- **Analysis Generation**: 10-45 seconds depending on V2 features enabled
- **Error Recovery**: Graceful degradation for any component failures

### **Risk Mitigation**

#### **Technical Risks**
1. **V2 Database Integration**: Verify all V2 tables are properly populated
2. **Performance Impact**: Monitor V2 analytics impact on generation time
3. **Backward Compatibility**: Ensure existing reports continue to work
4. **Algorithm Integration**: Validate dual-similarity ranking works correctly

#### **User Experience Risks**
1. **Configuration Complexity**: Provide clear defaults and progressive disclosure
2. **Validation Clarity**: Ensure error messages are helpful and actionable
3. **Performance Expectations**: Set clear expectations for processing time
4. **Feature Discovery**: Make V2 analytics benefits clear to users

### **Success Metrics**

#### **Technical Success**
- ✅ All 6 configuration parameters working correctly
- ✅ Form validation preventing invalid submissions
- ✅ V2 analytics generating enhanced reports
- ✅ Dual-similarity algorithm selection working
- ✅ No regression in existing functionality

#### **User Success**
- ✅ Intuitive configuration without training
- ✅ Clear understanding of feature impact
- ✅ Successful report generation on first attempt
- ✅ Meaningful differentiation between configuration options

---

This specification provides a comprehensive foundation for implementing the user configuration interface while maintaining compatibility with the existing codebase architecture and ensuring optimal user experience for career analysis report generation.
