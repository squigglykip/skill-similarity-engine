# White Paper Template Analysis
## Breaking Down the Gold Standard into Programmable Components

This document analyzes the gold standard white paper example to identify:
1. **Static Template Structure** - Consistent sections and formatting
2. **Dynamic Data Requirements** - What data needs to be pulled from the database
3. **Calculation Logic** - What computations need to be performed
4. **Content Generation Rules** - How to create narrative content programmatically

---

## Document Structure Analysis

### 1. Document Header (Static Template)
```yaml
template_section: document_header
static_content:
  - Document Classification: CONFIDENTIAL - Strategic Workforce Intelligence
  - Prepared for: [AUDIENCE_TYPE]
  - Analysis Date: [CURRENT_DATE]
  - Data Version: [DATABASE_VERSION]

dynamic_variables:
  - audience_type: From user selection (Business Leaders, HR Partners, etc.)
  - current_date: System generated
  - database_version: From database metadata
```

### 2. Executive Summary (Dynamic Content Generation)
```yaml
template_section: executive_summary
data_requirements:
  - source_job_profile: JobProfileID, JobProfile name
  - total_job_profiles: COUNT(*) from jobs table  
  - top_pathways: Top 3 similar jobs with similarity scores
  - percentile_ranking: Similarity score percentile calculation

content_generation_rules:
  - strategic_context: Template with job profile name insertion
  - key_findings: Dynamic based on similarity scores and percentile rankings
  - primary_recommendations: List top 3 pathways with scores and classifications
  - confidence_assessment: Based on data completeness and similarity distribution
```

### 3. Current Role Context (Database-Driven)
```yaml
template_section: current_role_context
data_requirements:
  sql_queries:
    - position_deployment: |
        SELECT COUNT(*) as total_positions,
               COUNT(DISTINCT Division) as division_count,
               COUNT(DISTINCT Location) as location_count
        FROM positions 
        WHERE JobProfileID = ?
    
    - location_breakdown: |
        SELECT Location, COUNT(*) as count
        FROM positions 
        WHERE JobProfileID = ?
        GROUP BY Location
        ORDER BY count DESC
    
    - divisional_distribution: |
        SELECT Division, "Business_Unit", COUNT(*) as count
        FROM positions 
        WHERE JobProfileID = ?
        GROUP BY Division, "Business_Unit"
        ORDER BY count DESC
    
    - skills_analysis: |
        SELECT s.Skill_Name, s.Category, s.Subcategory
        FROM job_skills js
        JOIN skills s ON js.Skill_ID = s.Skill_ID
        WHERE js.JobProfileID = ?
        ORDER BY s.Category, s.Skill_Name

content_generation_rules:
  - organisational_deployment: Format position counts and geographic spread
  - core_competency_foundation: Group skills by category and create narrative
  - strategic_value_proposition: Template based on job function and industry context
```

### 4. Pathway Analysis (Complex Content Generation)
```yaml
template_section: pathway_analysis
data_requirements:
  - similarity_calculations: Pre-computed similarity scores from job_similarities table
  - skills_overlap_analysis: Shared skills between source and target jobs
  - skills_gap_analysis: Skills in target job not in source job
  - position_context: Target job position deployment and growth data
  - career_progression_logic: Level comparison and move type classification

content_generation_rules:
  opportunity_classification:
    - outstanding: Top 5% similarity (>90th percentile)
    - excellent: Top 10% similarity (80-90th percentile)  
    - good: Top 25% similarity (75-80th percentile)
    - development_required: Below 75th percentile
  
  move_type_classification:
    - direct_progression: Same job family, higher level
    - cross_functional_expansion: Different job family, same level
    - technical_leadership_track: Technical specialization with leadership component
    - lateral_move: Similar level and function

  narrative_generation:
    - strategic_positioning: Template based on move type and business context
    - organisational_context: Position data and strategic importance
    - skills_transition_analysis: Quantified skills overlap and gap analysis
    - business_case: ROI, strategic alignment, and value proposition
    - implementation_roadmap: Phase-based development plan
```

### 5. Strategic Recommendations (Template-Based)
```yaml
template_section: strategic_recommendations
content_type: mostly_static_with_variables
variables:
  - total_source_positions: Position count for source job
  - pathway_count: Number of viable pathways identified
  - candidate_pool_size: Estimated number of suitable candidates

templates:
  immediate_actions:
    - Individual career conversations with all [total_source_positions] [source_job_title]s
    - Skills gap assessment for interested candidates
    - Stakeholder alignment with hiring managers
  
  medium_term_initiatives:
    - Structured learning programs for [pathway_count] identified pathways
    - Pilot transition program with [pilot_size] candidates
    - Success metrics framework implementation
```

---

## Data Requirements Mapping

### Database Tables Required

```sql
-- Core job information
SELECT j.JobProfileID, j.JobProfile, j.Job, j.JobFunction, j.ManagementLevel
FROM jobs j
WHERE j.JobProfileID = ?

-- Position deployment analysis
SELECT p.Division, p."Business_Unit", p.Location, COUNT(*) as position_count
FROM positions p
WHERE p.JobProfileID = ?
GROUP BY p.Division, p."Business_Unit", p.Location

-- Skills analysis
SELECT s.Skill_Name, s.Category, s.Subcategory, s.Description
FROM job_skills js
JOIN skills s ON js.Skill_ID = s.Skill_ID  
WHERE js.JobProfileID = ?

-- Similarity analysis
SELECT js.job_to, js.similarity_score, j.JobProfile, j.Job
FROM job_similarities js
JOIN jobs j ON js.job_to = j.JobProfileID
WHERE js.job_from = ?
ORDER BY js.similarity_score DESC
LIMIT 10

-- Skills overlap analysis
SELECT 
    source_skills.Skill_Name,
    CASE WHEN target_skills.Skill_ID IS NOT NULL THEN 'Shared' ELSE 'Source Only' END as skill_status
FROM job_skills source_js
JOIN skills source_skills ON source_js.Skill_ID = source_skills.Skill_ID
LEFT JOIN job_skills target_js ON target_js.JobProfileID = ? AND target_js.Skill_ID = source_js.Skill_ID
LEFT JOIN skills target_skills ON target_js.Skill_ID = target_skills.Skill_ID
WHERE source_js.JobProfileID = ?
```

### Calculation Requirements

```python
# Percentile calculations for similarity classification
def calculate_similarity_percentile(similarity_score, all_similarities):
    return percentileofscore(all_similarities, similarity_score)

# Skills overlap calculations
def calculate_skills_overlap(source_job_id, target_job_id):
    source_skills = get_job_skills(source_job_id)
    target_skills = get_job_skills(target_job_id)
    
    shared_skills = set(source_skills) & set(target_skills)
    skills_to_develop = set(target_skills) - set(source_skills)
    transferable_skills = set(source_skills) - set(target_skills)
    
    return {
        'shared_count': len(shared_skills),
        'shared_percentage': len(shared_skills) / len(target_skills) * 100,
        'develop_count': len(skills_to_develop),
        'transferable_count': len(transferable_skills),
        'shared_skills': list(shared_skills),
        'skills_to_develop': list(skills_to_develop)
    }

# Move type classification
def classify_move_type(source_job, target_job, similarity_score):
    if source_job['JobFunction'] == target_job['JobFunction']:
        if target_job['ManagementLevel'] > source_job['ManagementLevel']:
            return 'direct_progression'
        else:
            return 'lateral_move'
    else:
        if 'Technology' in target_job['JobFunction'] or 'Architecture' in target_job['Job']:
            return 'technical_leadership_track'
        else:
            return 'cross_functional_expansion'
```

---

## Content Generation Templates

### Narrative Templates by Move Type

```yaml
strategic_positioning_templates:
  direct_progression: |
    {target_job_title} represents a **natural career progression** that leverages existing {source_competency_area} foundations while expanding into specialised {target_specialization} capabilities. This pathway addresses {organization}'s growing focus on {strategic_priority} across all business units.
  
  cross_functional_expansion: |
    {target_job_title} represents a **cross-functional expansion** that leverages {transferable_competencies} while building broader {target_capability_area} capabilities across {organization}'s {transformation_initiative}. This pathway addresses growing demand for {hybrid_professional_type} who can bridge {source_domain} with {target_domain}.
  
  technical_leadership_track: |
    {target_job_title} represents a **technical leadership pathway** that leverages {analytical_skills} while building {leadership_capabilities} and {technical_architecture} capabilities. This pathway addresses {organization}'s need for technical leaders who can {leadership_responsibility} across the {technical_domain}.

business_case_templates:
  strategic_alignment: |
    - Supports {organization}'s {strategic_initiative} and {business_priority}
    - Addresses {market_requirement} for {capability_type} in {industry_context}
    - Leverages existing {source_skills} while building {target_specialization}
  
  organisational_benefits: |
    - **Internal Mobility:** Reduces external recruitment costs (estimated ${cost_avoidance}+ per senior hire)
    - **Knowledge Retention:** Maintains institutional knowledge while expanding capability
    - **Career Progression:** Provides clear advancement pathway for high-performing {source_role_type}
    - **Capability Building:** Strengthens {target_capability} across multiple business units
```

### Skills Analysis Templates

```yaml
skills_transition_templates:
  transferable_skills: |
    **Directly Transferable Skills ({shared_count} of {total_source_skills} - {shared_percentage}%):**
    {skills_by_category}
  
  development_required: |
    **Skills Development Required ({develop_count} new competencies):**
    {numbered_skills_list_with_descriptions}
    
    **Development Timeline:** {timeline_estimate} structured learning + {applied_experience_estimate} applied experience

skills_categorization:
  technical_analytics:
    - Python Programming
    - SQL Database Management  
    - Statistical Analysis
    - Machine Learning Fundamentals
    - Data Visualisation
  
  business_intelligence:
    - Business Requirements Analysis
    - Stakeholder Communication
    - Project Management
    - Process Improvement
  
  risk_compliance:
    - Risk Assessment
    - Regulatory Compliance
    - Data Governance
    - Audit & Control
```

---

## Implementation Strategy

### Phase 1: Template Engine Development
1. **YAML Template Structure** - Create hierarchical template system
2. **Variable Substitution Engine** - Build robust variable replacement system
3. **Content Generation Rules** - Implement business logic for narrative creation
4. **Database Integration** - Connect templates to SQL queries

### Phase 2: Content Quality Enhancement  
1. **Narrative Variation** - Create multiple templates for each section to avoid repetition
2. **Context-Aware Content** - Adjust narratives based on job families, levels, and industries
3. **Data-Driven Insights** - Generate unique insights based on actual data patterns
4. **Professional Language** - Ensure executive-appropriate tone and terminology

### Phase 3: Advanced Features
1. **Multi-Audience Support** - Different content depth for different audiences
2. **Scenario-Based Templates** - Customized content for different business scenarios
3. **Dynamic Visualizations** - Embed charts and graphs in generated documents
4. **Bulk Generation** - Support for generating multiple white papers simultaneously

### Success Metrics
- **Content Quality**: Generated content matches gold standard example quality
- **Data Accuracy**: All quantitative data matches database calculations
- **Narrative Uniqueness**: Each generated document has unique, role-specific insights
- **Professional Standard**: Documents suitable for executive presentation without editing

This template analysis provides the roadmap for transforming the gold standard example into a fully programmable white paper generation system. 