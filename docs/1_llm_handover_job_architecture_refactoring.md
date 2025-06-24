# LLM Handover Prompt: NAB Skills Intelligence Job Display Name Standardisation

## 🎯 **YOUR MISSION**

You are a **Senior Software Architect** specializing in enterprise data architecture and web application design. Your task is to implement a **focused display name standardisation** across the NAB Skills Intelligence Platform to improve user experience and job role clarity.

**CRITICAL CONTEXT:** This is a **display layer improvement** that will impact job naming across every page of the webapp. The underlying data architecture is correct - we just need consistent, user-friendly job display names.

## 📋 **DISCOVERED DISPLAY NAMING ISSUE**

### **Current (Inconsistent) Display Pattern**
The webapp currently shows job names inconsistently:
- Sometimes shows raw `JobProfile` field: "Payment Systems Analyst - 5"
- Sometimes shows `JobProfileID`: "R0001.5"
- Inconsistent formatting across different pages and components
- Users see technical codes rather than meaningful job descriptions

### **Correct Understanding (Recently Clarified)**
The database schema is actually correct:
- **JobProfileID** (R0001.5) = unique identifier for a specific job profile
- **Job** = base job title ("Payment Systems Analyst")
- **ProfileTitleSuffix** = seniority level ("Senior Manager")
- **ManagementLevel** = hierarchy level ("Group 2")
- Each JobProfileID represents a distinct position with different responsibilities

### **Business Impact**
- Current inconsistent naming confuses users about actual job roles
- Technical codes (R0001.5) don't communicate meaningful career information
- Career pathways show cryptic identifiers instead of clear job progressions
- Users can't easily understand seniority levels and career advancement paths

## 🏗️ **PROJECT FOUNDATION & CURRENT STATE**

### **Successful White Paper Generation System** ✅
The conversation has successfully established a production-ready white paper generation system:

**Key Achievements:**
- **ExecutiveSummaryGenerator**: 479 lines, fully functional with database integration
- **DatabaseReferenceCalculator**: Comprehensive 19+ reference system working
- **YAML template system**: Dynamic content with threshold-based descriptors
- **Real database integration**: 715 jobs, 38,430 skills, 510,510 similarities
- **Gold standard quality**: Template variable substitution and reference formatting working perfectly

**Working Architecture:**
```
skill-similarity-engine/src/skill_similarity_engine/webapp/whitepaper/
├── executive_summary_generator.py (479 lines) 
├── templates/sections/executive_summary.yaml (174 lines)
├── test_executive_summary.py (168 lines)
└── sql/
    ├── __init__.py (WhitePaperQueries + DatabaseReferenceCalculator)
    ├── executive_summary_queries.sql (reference views 1-16)
    ├── similarity_thresholds.sql (percentile calculations)
    ├── skills_gap_analysis.sql (skills comparison)
    ├── whitepaper_queries.sql (core data queries)
    └── workforce_impact.sql (position analysis)
```

### **Database Architecture** ✅
**Production Database:** `skill-similarity-engine\models\2025-Q2\business_context.sqlite` (118.95 MB)

**Key Tables:**
- **jobs** (715 records): JobProfileID, JobProfile, ManagementLevel, JobFamily, etc.
- **skills** (38,430 records): Comprehensive Lightcast integration with 18-column schema
- **job_similarities** (510,510 records): Pre-computed similarity matrix
- **career_pathways** (17,160 records): Pre-computed career progression data
- **positions** (35,000 records): Workforce context with organisational hierarchy

**Enhanced Schema (14-column job architecture):**
- `ManagementLevel`: Group 1, Group 2, Group 3, Group 4, Group 5, Group 6, Group 7, Group NA
- `JobCategory`: Support, Revenue Generating, Enabling, Executive & General Management
- `Customer_Facing`: Customer Facing, Non-Customer Facing
- `is_Banker`: Banker, Non-Banker

### **Flask Webapp Status** 🔄
**Main Application:** `app.py` (~2314 lines) with professional NAB-branded UI

**Current Pages Affected by Job Architecture:**
- `/` - Dashboard with job statistics
- `/jobs` - Job explorer and search
- `/pathways` - Career pathway analysis  
- `/skills-analysis` - Skills gap analysis
- `/tree/<job_id>` - D3.js career tree visualization
- `/api/pathways/<job_id>` - Career pathway API
- `/white-papers` - White paper generation interface

## 🎯 **SPECIFIC IMPLEMENTATION TASKS**

### **Task 1: Standardise Job Display Name Format**
**Objective**: Implement consistent job display naming across all webapp components.

**Target Display Format**:
```
Job + " - " + ProfileTitleSuffix + " - " + ManagementLevel
```

**Examples**:
- **Current**: "Payment Systems Analyst - 5" or "R0001.5"
- **Target**: "Payment Systems Analyst - Senior Manager - Group 2"

**Method**:
1. **Create Display Name Function**:
   - Implement utility function to format job display names
   - Handle edge cases (empty ProfileTitleSuffix, etc.)
   - Ensure consistent formatting across all components

2. **Frontend Component Updates**:
   - Update all dropdown/select components showing job lists
   - Modify career pathway displays to show clear job titles
   - Update D3.js tree visualization node labels
   - Standardise job cards and tables

3. **Template Updates**:
   - Update Jinja2 templates to use new display format
   - Ensure white paper generation uses consistent naming
   - Update search and filter displays

**Expected Deliverable**: Consistent job naming across all user interfaces

### **Task 2: Database Query Optimisation**
**Objective**: Ensure efficient retrieval of job display components.

**Implementation Strategy**:
```sql
-- Create view for easy display name generation
CREATE VIEW job_display_names AS
SELECT 
    JobProfileID,
    Job || ' - ' || ProfileTitleSuffix || ' - ' || ManagementLevel as display_name,
    Job,
    ProfileTitleSuffix,
    ManagementLevel,
    JobFunction,
    JobCategory
FROM jobs;
```

**Key Benefits**:
1. **Performance**: Pre-computed display names for fast retrieval
2. **Consistency**: Single source of truth for display formatting
3. **Maintainability**: Easy to update format in one place
4. **Compatibility**: No changes to existing JobProfileID relationships

### **Task 3: User Interface Updates**
**Objective**: Update all user-facing components to use standardised display names.

**Priority Components**:

**Priority 1 (Critical) - Core Navigation:**
- Job explorer dropdown/search
- Career pathway cards
- White paper job selection
- Dashboard job statistics

**Priority 2 (High) - Visualisations:**
- D3.js career tree node labels
- Skills analysis job comparisons
- Pathway recommendation lists

**Priority 3 (Medium) - Supporting Features:**
- Search results formatting
- API response standardisation
- Export/report formatting

**UI/UX Examples**:
1. **Job Selection Interface**:
   ```
   Current: "Payment Systems Analyst - 5" (R0001.5)
   Target: "Payment Systems Analyst - Senior Manager - Group 2"
   ```

2. **Career Pathway Display**:
   ```
   Current: R0001.5 → R0002.1
   Target: Payment Systems Analyst - Senior Manager - Group 2 → 
           Sales Manager - Team Lead - Group 4
   ```

3. **White Paper Context**:
   ```
   Current: "Risk Analyst (Group 3)"
   Target: "Risk Analyst - Senior Consultant - Group 3"
   ```

## 📊 **DATABASE SCHEMA UNDERSTANDING**

### **Current Job Architecture Schema (CONFIRMED CORRECT)**
Based on `sqlite_schema_design.md` analysis:

```sql
CREATE TABLE jobs (
    JobProfileID TEXT PRIMARY KEY,           -- R0001.5 format (unique identifier)
    JobProfile TEXT NOT NULL,               -- "Payment Systems Analyst - 5" (includes suffix)
    JobID TEXT,                             -- Hierarchical job code (R0001)
    Job TEXT,                               -- Base job title ("Payment Systems Analyst")
    ProfileTitleSuffix TEXT,                -- Seniority level ("Senior Manager", "Associate")
    ManagementLevel TEXT,                   -- Hierarchy level ("Group 1", "Group 2", etc.)
    JobFunction TEXT,                       -- Function area ("Data & Analytics", "Banking Services")
    JobCategory TEXT,                       -- Category ("Support", "Revenue Generating", etc.)
    -- ... other columns
);
```

### **Example Data Structure (Validated)**
```
JobProfileID: R0001.5
JobProfile: Payment Systems Analyst - 5
Job: Payment Systems Analyst
ProfileTitleSuffix: Senior Manager  
ManagementLevel: Group 2
JobFunction: Data & Analytics

Target Display: "Payment Systems Analyst - Senior Manager - Group 2"
```

### **Display Name View Implementation**
```sql
-- Create view for standardised display names
CREATE VIEW job_display_names AS
SELECT 
    JobProfileID,
    Job || ' - ' || ProfileTitleSuffix || ' - ' || ManagementLevel as display_name,
    Job as base_title,
    ProfileTitleSuffix as seniority_level,
    ManagementLevel as hierarchy_level,
    JobFunction,
    JobCategory,
    JobProfile as original_profile_name
FROM jobs
WHERE Job IS NOT NULL 
  AND ProfileTitleSuffix IS NOT NULL 
  AND ManagementLevel IS NOT NULL;
```

### **Implementation Approach**
- **Zero database schema changes required** - existing structure is perfectly correct
- **Maintain all existing relationships** - JobProfileID foreign keys remain unchanged
- **Display layer transformation only** - focus on presentation formatting
- **No data migration needed** - all required fields already exist

## 🔧 **TECHNICAL IMPLEMENTATION REQUIREMENTS**

### **Core Utility Functions to Implement**

```python
def format_job_display_name(job: str, profile_title_suffix: str, management_level: str) -> str:
    """Format job display name using standard convention."""
    return f"{job} - {profile_title_suffix} - {management_level}"

def get_job_display_name(job_profile_id: str, db_connection) -> str:
    """Get formatted display name for a JobProfileID."""
    query = """
    SELECT Job, ProfileTitleSuffix, ManagementLevel 
    FROM jobs 
    WHERE JobProfileID = ?
    """
    result = db_connection.execute(query, (job_profile_id,)).fetchone()
    if result:
        return format_job_display_name(result[0], result[1], result[2])
    return job_profile_id  # Fallback to ID if not found

class JobDisplayHelper:
    """Helper class for consistent job display name formatting"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def get_display_name(self, job_profile_id: str) -> str:
        """Get formatted display name for a JobProfileID"""
        return get_job_display_name(job_profile_id, self.db)
        
    def get_all_jobs_with_display_names(self) -> List[Dict]:
        """Get all jobs with formatted display names"""
        query = """
        SELECT JobProfileID, 
               Job || ' - ' || ProfileTitleSuffix || ' - ' || ManagementLevel as display_name,
               Job, ProfileTitleSuffix, ManagementLevel, JobFunction, JobCategory
        FROM jobs
        WHERE Job IS NOT NULL AND ProfileTitleSuffix IS NOT NULL AND ManagementLevel IS NOT NULL
        ORDER BY Job, ManagementLevel, ProfileTitleSuffix
        """
        return [dict(row) for row in self.db.execute(query).fetchall()]
        
    def search_jobs_by_display_name(self, search_term: str) -> List[Dict]:
        """Search jobs by display name components"""
        query = """
        SELECT JobProfileID, 
               Job || ' - ' || ProfileTitleSuffix || ' - ' || ManagementLevel as display_name
        FROM jobs
        WHERE (Job LIKE ? OR ProfileTitleSuffix LIKE ? OR ManagementLevel LIKE ?)
          AND Job IS NOT NULL AND ProfileTitleSuffix IS NOT NULL AND ManagementLevel IS NOT NULL
        ORDER BY display_name
        """
        search_pattern = f"%{search_term}%"
        return [dict(row) for row in self.db.execute(query, (search_pattern, search_pattern, search_pattern)).fetchall()]
```

### **Flask Route Updates Required**

**Priority 1 (Critical) - Core Functionality:**
```python
@app.route('/jobs')  # Job explorer - use standardised display names
@app.route('/pathways/<job_id>')  # Career pathways - display clear job titles
@app.route('/api/pathways/<job_id>')  # API - include display names in response
@app.route('/tree/<job_id>')  # D3 tree - show formatted job names as node labels
```

**Priority 2 (High) - User Experience:**
```python
@app.route('/')  # Dashboard - display meaningful job statistics
@app.route('/skills-analysis')  # Skills - clear job comparison names
@app.route('/white-papers')  # White papers - use standard naming format
```

**Priority 3 (Medium) - Supporting Features:**
```python
@app.route('/api/jobs/search')  # Search - search across display name components
@app.route('/api/skills/<job_id>')  # Skills API - include formatted job context
```

### **JavaScript/Frontend Updates Required**

**D3.js Tree Visualization:**
- Update node labels to show "Job - Suffix - Level" format
- Ensure pathway connections show meaningful career progression
- Tooltip displays can show additional context (JobProfileID, etc.)

**Job Selection Components:**
- Update dropdowns to show standardised display names
- Maintain JobProfileID as value while showing user-friendly text
- Implement search across Job, ProfileTitleSuffix, and ManagementLevel

**Career Pathway Interface:**
- Display clear job progression with seniority indicators
- Show meaningful job titles instead of technical codes
- Enable users to understand career advancement clearly

## 🚀 **SUCCESS CRITERIA**

### **Functional Requirements**
1. **Consistent Display Names**: All job lists show "Job - ProfileTitleSuffix - ManagementLevel" format
2. **Career Progression Clarity**: Pathways show meaningful job titles and clear seniority levels
3. **User-Friendly Interface**: Technical codes replaced with descriptive job information
4. **Backward Compatibility**: JobProfileID system continues to work unchanged underneath
5. **Performance Maintained**: Response times remain within current acceptable limits

### **Technical Requirements**
1. **Zero Database Schema Changes**: Implementation uses display layer formatting only
2. **Minimal Code Changes**: Focus on presentation layer without architectural changes
3. **API Enhancement**: Existing endpoints enhanced to include display names alongside IDs
4. **Code Quality**: New utility functions follow established patterns and are well-documented
5. **Testing Coverage**: Tests for display name formatting and edge case handling

### **User Experience Requirements**
1. **Intuitive Job Names**: Users see meaningful job titles instead of technical codes
2. **Clear Career Progression**: Seniority levels and advancement paths are immediately apparent
3. **Consistent Experience**: Same display format across all pages and components
4. **Search Enhancement**: Users can search by job title, seniority level, or management group
5. **Performance**: No degradation in page load times or interaction responsiveness

## 📝 **IMMEDIATE NEXT STEPS**

### **Week 1: Implementation Setup**
1. **Create display utility functions**: Implement `JobDisplayHelper` class and utility functions
2. **Database view creation**: Deploy `job_display_names` view for efficient querying
3. **Component inventory**: Document all UI components that display job names
4. **Testing framework**: Set up tests for display name formatting

### **Week 2: Core Component Updates**
1. **Job selection dropdowns**: Update to use standardised display names
2. **Career pathway displays**: Replace technical codes with meaningful job titles
3. **API endpoint enhancement**: Add display names to JSON responses
4. **White paper generation**: Ensure consistent naming in generated documents

### **Week 3: Advanced Visualisations**
1. **D3.js tree updates**: Modify node labels to show formatted job names
2. **Dashboard statistics**: Update job statistics to use display names
3. **Search functionality**: Enhance search to work across job name components
4. **Skills analysis pages**: Ensure job comparisons show clear titles

### **Week 4: Testing and Deployment**
1. **Comprehensive testing**: Validate all display name formatting
2. **Performance validation**: Ensure no degradation in load times
3. **User acceptance testing**: Validate improved user experience
4. **Documentation updates**: Update user guides and technical documentation

## 💡 **CRITICAL SUCCESS FACTORS**

1. **Consistent Implementation**: All components must use the same display name format
2. **Performance Maintenance**: Display name formatting must not impact system performance
3. **User Experience**: Job titles must be immediately clear and meaningful to users
4. **Backward Compatibility**: All existing functionality must continue to work unchanged
5. **Testing Coverage**: Comprehensive testing of display formatting across all components

## 🔍 **VALIDATION QUESTIONS**

Before implementation, validate:

1. **Display Format Preference**: Do users prefer "Job - Suffix - Level" or alternative formats?
2. **Edge Case Handling**: How to handle jobs with missing ProfileTitleSuffix or ManagementLevel?
3. **Performance Impact**: What's the cost of on-demand display name formatting vs. pre-computed views?
4. **Search Behaviour**: Do users expect to search job components individually or as combined strings?
5. **Integration Impact**: Do external systems need to receive display names in API responses?

## 📞 **WHEN YOU NEED HELP**

If you encounter issues:
1. **Review current white paper system** - it demonstrates successful database integration patterns
2. **Check `enhanced_sqlite_schema_design.md`** - complete database schema documentation
3. **Examine existing Flask patterns** - established conventions for new feature development
4. **Test with production database** - use real data to validate logical role assumptions

## 🎯 **FINAL MISSION STATEMENT**

Implement consistent, user-friendly job display names across the NAB Skills Intelligence Platform to replace technical codes with meaningful job titles that clearly communicate seniority levels and career progression paths.

**The outcome**: HR professionals and employees see intuitive job titles like "Payment Systems Analyst - Senior Manager - Group 2" instead of cryptic codes like "R0001.5", making career progression and job relationships immediately clear.

**Your success will be measured by**: Improved user experience with clear job identification, consistent naming across all platform components, and maintained system performance.

---

**This is a focused display layer improvement that will significantly enhance user experience across the NAB Skills Intelligence Platform. Execute with attention to consistency and user clarity.** 