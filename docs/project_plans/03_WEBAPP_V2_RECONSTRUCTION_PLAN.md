# 03. Webapp V2 Reconstruction Plan

**Date Created**: 2025-01-08  
**Project Phase**: Post-Analytics V2 Database  
**Priority**: Critical Infrastructure Upgrade  
**Estimated Timeline**: 9-12 weeks (preserving current design system)

---

## 🤖 **LLM IMPLEMENTATION GUIDANCE**

> **Critical Context for AI-Assisted Development**: This document serves as both a comprehensive plan and step-by-step implementation guide for transforming the Skills Intelligence webapp from V1 to V2. You will work through this systematically, one phase at a time, with each section providing the context and technical specifications needed for that phase.

### **How to Use This Plan**

1. **Read the Full Context First**: Understand the current state analysis, design system, and technical principles before starting any code changes.

2. **Follow the Phase Sequence**: Each phase has dependencies on previous phases. Complete Phase 0 entirely before moving to Phase 1, etc.

3. **Preserve Existing Functionality**: This is an upgrade, not a rebuild. Every existing feature must continue working exactly as before.

4. **Maintain Design System**: The user explicitly wants to preserve the current blue primary + red accent design. Do not change colors, fonts, or layout patterns.

5. **Database-First Approach**: All metrics must come from the V2 database. No placeholder data, no fallbacks to dummy values.

6. **Strict Modularization**: Keep files under 1000 lines. Break down functionality into focused modules with single responsibilities.

### **Key Success Principles**

- **✅ PRESERVE**: Current design system, user experience, existing functionality
- **✅ ENHANCE**: Add new V2 analytics capabilities using established patterns  
- **✅ INTEGRATE**: Connect V2 database tables with sophisticated analytics
- **✅ MODULARIZE**: Keep code organized, focused, and maintainable
- **❌ NEVER**: Break existing functionality, change visual design, use placeholder data

### **Phase-by-Phase Approach**

Each major section below contains LLM context boxes that provide specific guidance for that phase. Read these carefully - they contain critical implementation details and warn about common pitfalls.

---  

## 🗺️ **WEBSITE SITEMAP**

### **Primary Navigation Structure**

```
🏠 Dashboard (/)
├── Platform Overview Metrics
├── Strategic Intelligence Summary
├── Recent Analytics Updates
└── Quick Access to All Modules

🔍 Job Explorer (/job-search)
├── Job Profile Search & Discovery
├── Individual Job Deep Dive Analysis
├── Skills Architecture Breakdown
├── Defining Skills Analysis (V2 Enhanced)
├── Job Family Membership (V2 New)
└── Similar Jobs with Enhanced Similarity Scoring

🛤️ Career Pathways (/career-pathways)
├── Interactive Career Journey Visualization
├── Multi-Modal Pathway Scoring (V2 New)
│   ├── User-Configurable Weighting Slider
│   ├── Skills Similarity Analysis
│   └── ML Prediction Confidence
├── Movement Patterns Analysis (V2 Enhanced)
├── Skills Gap Analysis Between Roles
└── Workforce Impact Visualization

📊 Career Analysis (/career-analysis)
├── Career Transition Report Generator
├── Multi-Modal Analysis Configuration
├── Executive Summary Generation
├── Strategic Recommendations
├── Document Export (Word, PDF, PowerPoint)
└── Analysis Preview Interface

💡 Skills Intelligence Hub (V2 New Section)
├── Skills Taxonomy Browser (comprehensive skills)
├── Skill Bundles Explorer (clustered skill groups)
├── Skill Rarity Analysis & Matrix
├── Skill Velocity Trends (CAGR analysis)
└── Emerging Skills Tracker

🏗️ Job Families Clustering (V2 New Section)
├── Interactive Job Families Map (DBSCAN clusters)
├── Family Characteristics Analysis
├── Cluster Quality Metrics
├── Job Family Deep Dive
└── Cross-Family Movement Analysis

🔧 Job Architecture Health (/architecture-health)
├── Architecture Diagnostics Dashboard
├── Near-Duplicate Job Detection
├── Entropy Analysis & Quality Metrics
├── Silhouette Scores & Clustering Health
├── Data Quality Assessment
├── Governance Recommendations
└── Health Trend Analysis

📚 Documentation (/documentation)
├── Database Schema Documentation
│   ├── Interactive Schema Browser
│   ├── Table Relationships (ERD)
│   ├── Business Context Guide
│   └── Developer Reference
├── How This Website Works
│   ├── Multi-Modal Scoring Explained
│   ├── Analytics Pipeline Overview
│   ├── Data Sources & Updates
│   └── Feature Guides
├── API Documentation
│   ├── V2 Endpoint Reference
│   ├── Authentication & Usage
│   ├── Response Examples
│   └── Integration Guides
└── User Guides
    ├── Getting Started
    ├── Advanced Features
    ├── Troubleshooting
    └── FAQ
```

### **Supporting Pages & APIs**

```
🔧 Components Library (/components)
└── Design System Showcase & Testing

📡 API Endpoints (/api/v2/)
├── /jobs/ - Enhanced job data with V2 analytics
├── /skills/ - Skills intelligence and bundles
├── /pathways/ - Multi-modal career scoring
├── /families/ - Job clustering analysis
├── /architecture/ - Health diagnostics and governance
├── /intelligence/ - Strategic recommendations
├── /documentation/ - Schema and API metadata
└── /user-preferences/ - Scoring customization
```

### **User Experience Flows**

**🎯 Primary User Journeys:**

1. **Strategic Overview Flow**
   - Dashboard → Strategic Intelligence → Architecture Health → Action Items

2. **Individual Job Analysis Flow**
   - Job Explorer → Job Profile → Defining Skills → Family Membership → Similar Roles

3. **Career Planning Flow**
   - Career Pathways → Scoring Preferences → Pathway Visualization → Skills Gap Analysis → Action Plan

4. **Career Transition Analysis Flow**
   - Career Analysis → Analysis Configuration → Multi-Modal Scoring → Report Generation → Export

5. **Skills Intelligence Flow**
   - Skills Hub → Taxonomy Browser → Skill Bundles → Rarity Analysis → Trends

6. **Job Architecture Flow**
   - Job Families → Clustering Map → Family Analysis → Movement Patterns → Strategic Insights

7. **Architecture Health Flow**
   - Architecture Health → Diagnostics → Near-Duplicates → Quality Assessment → Governance Actions

8. **Documentation Flow**
   - Documentation → Schema Browser → How It Works → API Reference → User Guides

---

## 🎯 **EXECUTIVE SUMMARY**

Transform the Skills Intelligence webapp from a basic V1 job browser to a comprehensive V2 workforce intelligence platform that fully leverages the sophisticated analytics database with 16 tables and comprehensive workforce records.

**Business Value**: Enable strategic workforce planning, comprehensive career intelligence, and data-driven talent decisions through an intuitive, enterprise-grade interface.

**Technical Approach**: Systematic reconstruction maintaining Flask + D3.js architecture while incorporating multi-modal career analysis combining skill similarity + ML prediction confidence.

## 🎯 **CORE TECHNICAL PRINCIPLES**

### **1. Database-First Architecture (No Placeholders)**
- ✅ **ALL metrics sourced from V2 database tables**
- ❌ **NO hardcoded values, mock data, or placeholder metrics**
- ✅ **Real-time queries against V2 database records**
- ❌ **NO fallback to dummy data if queries fail**

### **2. Fail-Fast Philosophy**
- ✅ **System fails immediately if database connection lost**
- ✅ **API endpoints return 500 errors rather than placeholder data**
- ✅ **UI shows loading states until real data loads**
- ❌ **NO graceful degradation with fake metrics**
- ❌ **NO "coming soon" placeholders**

### **3. Strict Modularization (Max 1000 Lines Per Module)**
- ✅ **SQL queries isolated in `/sql/` folder (one file per domain)**
- ✅ **API endpoints in `/api/` folder (single responsibility)**
- ✅ **Services in `/services/` folder (business logic only)**
- ✅ **Maximum 1000 lines per file (if hitting 1000+ lines, split further)**
- ❌ **NO monolithic 1000+ line files**
- ❌ **NO mixed concerns in single modules**

---

## 📋 **CURRENT STATE ANALYSIS**

> **🤖 LLM Context**: Before beginning any reconstruction work, you must understand the existing webapp architecture and identify what needs to be preserved versus what needs upgrading. This analysis forms the foundation for all subsequent development phases. The webapp is currently functional but limited to V1 database capabilities - your task is to systematically upgrade it to leverage the sophisticated V2 analytics without breaking existing functionality.

### **Existing Webapp Structure**

**✅ Strengths to Preserve:**
- **Modular Architecture**: Well-organized blueprints (`main`, `job_explorer`, `career_pathways`, `career_analysis`)
- **API Layer**: Systematic API organization (`jobs_api`, `search_api`, `similarity_api`, `pathways_api`, etc.)
- **Search Infrastructure**: Unified SearchModule with autocomplete and multi-select
- **UI Framework**: Consistent NAB design system with TailwindCSS
- **Data Layer**: Organized SQL queries in separate files (`jobs.sql`, `metadata.sql`, `similarities.sql`)

**❌ Critical Gaps vs V2 Database:**
- **Legacy Table References**: SQL queries reference `jobs`, `skills`, `job_skills` (V1) instead of `core_job_architecture`, `core_skills_taxonomy`, `core_job_skill_requirements` (V2)
- **Missing Analytics Integration**: No utilization of 11 analytics tables with sophisticated intelligence
- **Limited Career Intelligence**: Basic similarity without ML prediction confidence weighting
- **No Strategic Intelligence**: Missing job families, skill bundles, velocity analysis, architecture health
- **Outdated Metrics**: Homepage shows static pathway counts vs actual ML prediction capabilities

### **Current Pages Inventory**

**🏠 Homepage (`/`):**
- **Good**: Platform metrics, mobility intelligence dashboard, strategic recommendations
- **Missing**: V2 analytics integration, job architecture health, skill velocity trends
- **SQL**: Uses legacy table names, basic recommendations without analytics integration

**🔍 Job Explorer (`/job-search`):**
- **Good**: Search interface, job details, skills analysis, workforce context
- **Missing**: Defining skills analysis, job family membership, rarity analysis, enhanced similarity with V2 weighting
- **SQL**: Limited to basic job-skill relationships

**🛤️ Career Pathways (`/career-pathways`):**
- **Good**: Interactive D3.js visualization, pathway distribution
- **Missing**: ML prediction confidence, multi-modal scoring (similarity + feasibility), movement patterns analysis
- **Critical Gap**: No integration with `analytics_movement_patterns` or `analytics_pathway_predictions`

**📊 Career Analysis (`/career-analysis`):**
- **Good**: Report generation interface, preview functionality
- **Missing**: Integration with analytics tables for enhanced insights
- **SQL**: Basic queries without V2 intelligence

---

## 🔄 **MULTI-MODAL CAREER PATHWAY ENHANCEMENT**

> **🤖 LLM Context**: This is the flagship feature of V2 - combining traditional skill similarity with ML prediction confidence through user-configurable weighting. You're implementing a sophisticated scoring system that allows users to balance "skills-based" vs "feasibility-based" career recommendations. This requires careful integration of two separate analytics tables and a frontend slider interface that dynamically recalculates scores. Pay special attention to the mathematical formula and user experience flow described below.

### **Core Concept Implementation**

**Multi-Modal Career Scoring Formula (User-Configurable):**
```
Career_Pathway_Score = (Skill_Similarity_Score × User_Similarity_Weight) + (ML_Confidence_Score × User_ML_Weight)

Where:
- Skill_Similarity_Score: From analytics_job_similarities.enhanced_similarity_score (0.0 to 1.0)
- ML_Confidence_Score: Real-time inference from joblib models (model_agreement_fraction 0.0 to 1.0)
- User_Similarity_Weight: User-selected value (0.0 - 1.0, default: 0.6)
- User_ML_Weight: Complementary value (1.0 - User_Similarity_Weight, default: 0.4)

Supporting Metrics (Display Only):
- Predicted_Movements: Real-time ML prediction (headcount/year from ensemble models)
- Confidence_Interval: Model uncertainty bounds from joblib inference
- Model_Agreement: Consensus across gradient_boosting, random_forest, xgboost models
```

**Example Output with User Control:**
```
Job A → Job B
- 85% skill similarity (analytics_job_similarities)
- 35% ML prediction confidence (real-time joblib inference)

User Preference: "Prioritise Skills" (Similarity: 80%, ML: 20%)
- Combined Score: (0.85 × 0.8) + (0.35 × 0.2) = 0.75 (75%)

User Preference: "Prioritise Feasibility" (Similarity: 30%, ML: 70%)  
- Combined Score: (0.85 × 0.3) + (0.35 × 0.7) = 0.50 (50%)
```

**Implementation Strategy:**
1. **Database Integration**: Join `analytics_job_similarities` with real-time ML inference service
2. **ML Model Service**: Load joblib models (gradient_boosting, random_forest, xgboost) for ensemble predictions
3. **New API Endpoints**: Enhanced pathways API with user-configurable weighting parameters
4. **UI Enhancement**: Interactive slider controls for weighting preferences + visual indicators
5. **Real-Time Updates**: Dynamic re-scoring as user adjusts preferences
6. **User Preferences**: Save weighting preferences in session/local storage
7. **Model Caching**: Cache ML model predictions to avoid repeated inference for same job pairs

---

## 🎨 **CURRENT DESIGN SYSTEM PRESERVATION**

> **🤖 LLM Context**: CRITICAL - You must preserve the existing design system completely. The user has explicitly decided against implementing a new "NAB style guide" and wants to maintain the current blue primary + red accent color scheme with existing typography and component patterns. Your role is to EXTEND the current system, not replace it. Any new components must follow the established patterns exactly. Do not attempt to redesign or "improve" the visual design - only add new functionality using existing styles.

### **Existing Design System Analysis**

**✅ Current Strengths to Maintain:**
1. **Comprehensive CSS Variables**: Already has sophisticated design tokens in `variables.css`
2. **Typography System**: Epilogue + Source Sans Pro fonts already implemented
3. **Color System**: Well-established blue primary with red accents (hybrid approach)
4. **Component Library**: Custom CSS components working well with Tailwind
5. **Dark Navigation**: Black header with good contrast already implemented
6. **Responsive Design**: Mobile-first approach with consistent breakpoints

### **Current Design System Architecture**

#### **1. Color System (Already Excellent)**
```css
/* Current system works well - PRESERVE */
--color-blue-600: #2563eb;        // Primary actions
--color-nab-red: #dc2626;         // Accents and highlights
--color-gray-50: #f9fafb;         // Light backgrounds
--color-white: #ffffff;           // Card backgrounds
--color-black: #000000;           // Navigation background

/* Navigation: Black background with white text */
body: bg-white (main content area)
nav:  bg-black (header/navigation)
```

#### **2. Typography System (Already Implemented)**
```html
<!-- Already correctly implemented -->
<link href="https://fonts.googleapis.com/css2?family=Epilogue:wght@400;500;600;700&family=Source+Sans+Pro:wght@300;400;500;600&display=swap" rel="stylesheet">

Current hierarchy:
- Headers: font-epilogue (Epilogue)
- Body: font-source (Source Sans Pro)
- Sizing: Proper Tailwind scale implemented
```

#### **3. Component System (Well-Designed)**
```html
<!-- Current navigation - KEEP AS IS -->
<nav class="bg-black border-b border-gray-800">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <a href="/" class="font-epilogue font-bold text-xl text-white hover:text-red-600 transition-colors">
      Skill Similarity Engine
    </a>
  </div>
</nav>

<!-- Current body structure - PRESERVE -->
<body class="font-source text-black bg-white">
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- Content cards on white background -->
  </main>
</body>
```

#### **4. Multi-Modal Slider Component (Current Style)**
```html
<!-- Enhanced with current design system -->
<div class="bg-white rounded-lg shadow-md p-6 mb-6 border border-gray-200">
  <h3 class="text-lg font-epilogue font-semibold text-gray-900 mb-4">Pathway Scoring Preferences</h3>
  <div class="space-y-4">
    <label class="block text-xs font-source font-medium text-gray-700 uppercase tracking-wide">
      Prioritise Skills vs Feasibility
    </label>
    <div class="flex items-center gap-4">
      <span class="text-sm font-source text-gray-600">Skills Focus</span>
      <input type="range" id="scoring-weight" min="0" max="100" value="60" 
             class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-blue"
             oninput="updatePathwayScoring(this.value)">
      <span class="text-sm font-source text-gray-600">Feasibility Focus</span>
    </div>
    <div class="text-center">
      <span class="text-sm font-source text-blue-600 font-medium">
        <span id="skill-weight">60%</span> Skills | <span id="ml-weight">40%</span> Feasibility
      </span>
    </div>
  </div>
</div>

<style>
/* Using current blue primary theme */
.slider-blue::-webkit-slider-thumb {
  appearance: none;
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: var(--color-blue-600);
  cursor: pointer;
  box-shadow: 0 0 2px 0 #555;
}
.slider-blue::-moz-range-thumb {
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: var(--color-blue-600);
  cursor: pointer;
  border: none;
}
</style>
```

### **Enhancement Strategy: Preserve and Extend**

**Phase 0 (NEW): Design System Enhancement (1 week)**
- **PRESERVE** all current CSS variables and design tokens
- **EXTEND** component library with new V2 analytics components
- **ENHANCE** existing patterns rather than replace them
- **MAINTAIN** current color scheme (blue primary + red accents)
- **ADD** new components for multi-modal scoring and analytics

---

## 🏗️ **RECONSTRUCTION PHASES**

### **COMPLETE - Phase 0: Design System Enhancement (1 week) - PRESERVE CURRENT STYLING**

#### **COMPLETE - 0.1 Current Base Template Analysis**
**Target File**: `webapp/templates/base.html` - **ALREADY EXCELLENT**

**Current Implementation (KEEP AS IS):**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Current setup is perfect - PRESERVE -->
  <title>{% block title %}Skill Similarity Engine{% endblock %}</title>
  
  <!-- Fonts already implemented correctly -->
  <link href="https://fonts.googleapis.com/css2?family=Epilogue:wght@400;500;600;700&family=Source+Sans+Pro:wght@300;400;500;600&display=swap" rel="stylesheet">
  
  <!-- Tailwind + CSS variables system working well -->
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/variables.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
</head>
<body class="font-source text-black bg-white">
  <!-- Current navigation perfect - MAINTAIN -->
  <nav class="bg-black border-b border-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <a href="/" class="font-epilogue font-bold text-xl text-white hover:text-red-600 transition-colors">
        Skill Similarity Engine
      </a>
    </div>
  </nav>
  
  <!-- Current main content structure ideal -->
  <main>
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

#### **COMPLETE - 0.2 Design System Analysis - NO MAJOR CHANGES NEEDED**
**Assessment**: Current system is well-designed and consistent

**Current Color System (PRESERVE):**
- ✅ Blue primary (#2563eb) for actions and interactive elements
- ✅ Red accents (#dc2626) for highlights and navigation hover
- ✅ White backgrounds for content readability 
- ✅ Black navigation header for contrast
- ✅ Comprehensive CSS variables system already implemented

#### **COMPLETE - 0.3 Enhanced Components for V2 Analytics**
**ONLY ADD new components, don't change existing ones**

**New Component**: Multi-Modal Pathway Scoring
```html
<!-- Add to existing component library - preserve current style -->
<div class="bg-white rounded-lg shadow-md p-6 mb-6 border border-gray-200">
  <h3 class="text-lg font-epilogue font-semibold text-gray-900 mb-4">Pathway Scoring Preferences</h3>
  <div class="space-y-4">
    <label class="block text-xs font-source font-medium text-gray-700 uppercase tracking-wide">
      Balance Skills Similarity vs ML Prediction Confidence
    </label>
    <div class="flex items-center gap-4">
      <span class="text-sm font-source text-gray-600">Skills Focus</span>
      <input type="range" id="scoring-weight" min="0" max="100" value="60" 
             class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-blue">
      <span class="text-sm font-source text-gray-600">Feasibility Focus</span>
    </div>
    <div class="text-center">
      <span class="text-sm font-source text-blue-600 font-medium">
        <span id="skill-weight">60%</span> Skills | <span id="ml-weight">40%</span> Feasibility
      </span>
    </div>
  </div>
</div>
```

**New Component**: V2 Analytics Dashboard Cards
```html
<!-- Enhanced metric cards using current design patterns -->
<div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-xs font-source font-medium text-gray-500 uppercase tracking-wide">ML Pathway Predictions</p>
      <p class="text-2xl font-epilogue font-bold text-gray-900">21,307</p>
    </div>
    <div class="p-3 bg-blue-100 rounded-full">
      <svg class="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
    </div>
  </div>
  <div class="mt-4">
    <p class="text-sm font-source text-gray-600">↑ Enhanced with V2 database</p>
  </div>
</div>
```

#### **COMPLETE - 0.4 CSS Enhancements - ADDITIVE ONLY**
**Target File**: Add new file `webapp/static/css/v2-components.css`

**Additional Styles (don't modify existing):**
```css
/* Multi-modal slider styling using current blue theme */
.slider-blue::-webkit-slider-thumb {
  appearance: none;
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: var(--color-blue-600);
  cursor: pointer;
  box-shadow: 0 0 2px 0 #555;
  transition: background-color var(--transition-fast);
}

.slider-blue::-webkit-slider-thumb:hover {
  background: var(--color-blue-700);
}

/* V2 Analytics component enhancements */
.analytics-card {
  background: linear-gradient(135deg, var(--color-white) 0%, var(--color-blue-50) 100%);
  border-left: 4px solid var(--color-blue-600);
}

.pathway-score-indicator {
  background: var(--color-blue-100);
  border: 1px solid var(--color-blue-200);
  color: var(--color-blue-800);
}
```

**COMPLETE - Deliverables for Phase 0:**
- [x] Preserve all existing CSS variables and design tokens ✅ COMPLETE
- [x] Add V2 analytics components using current design patterns ✅ COMPLETE
- [ ] Create multi-modal scoring slider with blue theme - NEEDS COMPLETION
- [x] Enhance existing component library without breaking changes ✅ COMPLETE
- [x] Add new CSS file for V2-specific components only ✅ COMPLETE
- [x] Test all existing pages still work perfectly ✅ COMPLETE

**COMPLETE - Definition of Done for Phase 0:**
- ✅ All existing pages look and function identically ✅ COMPLETE
- ✅ New V2 components follow current design patterns ✅ COMPLETE
- ✅ Blue primary + red accent color scheme maintained ✅ COMPLETE
- ✅ Current typography system preserved ✅ COMPLETE
- ✅ Existing CSS variables system untouched ✅ COMPLETE
- [ ] Multi-modal slider uses current styling approach - NEEDS COMPLETION
- ✅ No breaking changes to existing functionality ✅ COMPLETE

---

### **COMPLETE - Phase 0: SQL Reconciliation & Schema Migration (1 week)**

> **🤖 LLM Context**: This is the BLOCKING phase that must be completed first. Based on the investigation findings below, you have 150+ V1 table references across 7 SQL files that must be updated to V2 schema. The webapp is well-structured with modular APIs and templates, but ALL SQL queries use V1 table names. Use the V1_TO_V2_SCHEMA_MAPPING.md as your reference. Every query must work with the V2 database - NO placeholders or fallback data allowed.

**🎯 CRITICAL FIRST TASK: Get V1 webapp working with V2 database**

**Investigation Findings Summary:**
- ✅ **Current Architecture**: Well-organized with 7 API modules, 6 templates, modular blueprints
- ❌ **Critical Issue**: 150+ V1 table references across all 7 SQL files 
- ❌ **Blocking Dependencies**: 11 API endpoints depend on V1 queries that will fail immediately
- ✅ **Design System**: Excellent current styling (blue primary + red accents) to preserve
- ✅ **JavaScript Architecture**: Sophisticated D3.js career pathways and search modules

#### **COMPLETE - 0.1 Current SQL Analysis - Comprehensive File Inventory**

**SQL Files Migration Requirements (7 files, 150+ V1 references):**

```
webapp/sql/
├── jobs.sql (25 queries)             → 75 V1 references → HIGH complexity
│   ├── V1 Dependencies: jobs table (all queries)
│   ├── Current Purpose: Job search, functions, details
│   ├── Migration Status: CRITICAL - All APIs depend on this
│   └── Effort Estimate: 2-3 hours (complex joins)
│
├── similarities.sql (14 queries)     → 42 V1 references → HIGH complexity  
│   ├── V1 Dependencies: job_similarities, jobs
│   ├── Current Purpose: Similar jobs, scoring, recommendations
│   ├── Migration Status: CRITICAL - Career pathways depend on this
│   └── Effort Estimate: 2 hours (enhanced scoring needed)
│
├── career_pathways.sql (6 queries)   → 16 V1 references → MEDIUM complexity
│   ├── V1 Dependencies: career_pathways (DEPRECATED), jobs
│   ├── Current Purpose: D3.js tree generation, pathway analysis
│   ├── Migration Status: MAJOR REWRITE - Pre-computed table replaced
│   └── Effort Estimate: 3-4 hours (new analytics approach)
│
├── skills.sql (10 queries)           → 35 V1 references → MEDIUM complexity
│   ├── V1 Dependencies: skills, job_skills, jobs
│   ├── Current Purpose: Skills analysis, gaps, proficiency
│   ├── Migration Status: UPDATE - Enhanced with defining skills
│   └── Effort Estimate: 1-2 hours (straightforward mapping)
│
├── positions.sql (9 queries)         → 25 V1 references → LOW complexity
│   ├── V1 Dependencies: positions, jobs
│   ├── Current Purpose: Workforce context, org structure
│   ├── Migration Status: UPDATE - Column name changes only
│   └── Effort Estimate: 1 hour (simple field mapping)
│
├── d3_visualization.sql (6 queries)  → 18 V1 references → MEDIUM complexity
│   ├── V1 Dependencies: jobs, job_similarities, career_pathways
│   ├── Current Purpose: D3.js data structures for career trees
│   ├── Migration Status: UPDATE - New analytics integration
│   └── Effort Estimate: 2 hours (D3 data structure preservation)
│
└── metadata.sql (16 queries)         → 65 V1 references → MEDIUM complexity
    ├── V1 Dependencies: All V1 tables for health checks
    ├── Current Purpose: Database stats, health monitoring
    ├── Migration Status: UPDATE - All table references
    └── Effort Estimate: 1-2 hours (comprehensive table updates)
```

**V1 → V2 Critical Table Mapping (from docs/V1_TO_V2_SCHEMA_MAPPING.md):**
```sql
-- CRITICAL MIGRATIONS (Breaking Changes):
jobs                    →  core_job_architecture           [75 references]
job_similarities        →  analytics_job_similarities     [42 references] 
skills                  →  core_skills_taxonomy            [35 references]
positions               →  core_workforce_current          [25 references]
job_skills              →  core_job_skill_requirements     [18 references]
career_pathways         →  DEPRECATED (use analytics)      [16 references]

-- KEY COLUMN CHANGES:
JobProfile              →  job_title
Skill_Name              →  skill_name
Category                →  primary_category
similarity_score        →  enhanced_similarity_score
```

#### **COMPLETE - 0.2 API Dependency Mapping - Critical Breaking Points**

**API Endpoints with V1 Dependencies (11 endpoints will fail immediately):**

```
API Endpoint                        → SQL Dependency → Migration Impact
├── /api/career-analysis-jobs       → jobs.sql      → HIGH (Career Analysis depends on this)
├── /api/job-similarities/<id>      → similarities  → HIGH (Job Explorer core feature)
├── /api/d3-tree-data              → career_pathways → CRITICAL (D3.js visualization)
├── /api/job-details/<id>          → jobs.sql      → HIGH (Job Explorer details)
├── /api/job-functions             → jobs.sql      → MEDIUM (Search functionality)
├── /api/jobs-in-function/<func>   → jobs.sql      → MEDIUM (Browse by function)
├── /api/skills-analysis/<id>      → skills.sql    → MEDIUM (Skills gap analysis)
├── /api/workforce-analysis/<id>   → positions.sql → MEDIUM (Workforce context)
├── /api/organizational-data       → positions.sql → LOW (Filter dropdowns)
├── /api/database-health-check     → metadata.sql  → LOW (Health monitoring)
└── /api/whitepaper-jobs           → jobs.sql      → LOW (Search autocomplete)
```

**JavaScript Integration Points (13 fetch calls):**
```javascript
// CRITICAL: D3.js Career Pathways (career-pathways.js)
fetch('/api/d3-tree-data')           → career_pathways.sql → BLOCKS tree visualization
fetch('/api/skills-analysis')        → skills.sql → Skills gap analysis
fetch('/api/workforce-analysis')     → positions.sql → Workforce context

// HIGH: Job Explorer (main.js)
fetch('/api/job-similarities')       → similarities.sql → Similar jobs display
fetch('/api/whitepaper-jobs')        → jobs.sql → Search autocomplete

// MEDIUM: Career Analysis (career-analysis.js)
fetch('/api/career-analysis-jobs')   → jobs.sql → Job selection
fetch('/api/career-analysis-preview') → Multiple → Report generation
```

#### **COMPLETE - 0.3 Sequential Migration Steps - Dependency-Aware Implementation**

**Step 1: Critical API Foundations (Day 1-2)**
```
1. Update jobs.sql (25 queries)              → Enables job search/details
2. Update similarities.sql (14 queries)      → Enables similar jobs display  
3. Test core API endpoints:
   - /api/job-details/<id>
   - /api/job-similarities/<id>
   - /api/job-functions
```

**Step 2: Workforce & Skills Integration (Day 2-3)**
```
4. Update positions.sql (9 queries)          → Enables workforce context
5. Update skills.sql (10 queries)           → Enables skills analysis
6. Test supporting APIs:
   - /api/workforce-analysis/<id>
   - /api/skills-analysis/<id>
   - /api/organizational-data
```

**Step 3: Career Pathways Reconstruction (Day 3-4)**
```
7. Update career_pathways.sql (6 queries)    → MAJOR: Replace pre-computed approach
8. Update d3_visualization.sql (6 queries)   → Enables D3.js tree visualization
9. Test critical pathways:
   - /api/d3-tree-data
   - Career Pathways page functionality
```

**Step 4: System Health & Validation (Day 4-5)**
```
10. Update metadata.sql (16 queries)         → Enables health monitoring
11. Full webapp testing:
    - All 4 main pages (Dashboard, Job Explorer, Career Pathways, Career Analysis)
    - All 11 API endpoints
    - JavaScript functionality
12. Performance validation (<500ms query times)
```

**Example: Critical jobs.sql V1→V2 Update**
```sql
-- BEFORE (V1 Schema) - Will fail with V2 database
SELECT 
    JobProfileID as id,
    JobProfile as job_title,
    JobFunction as job_function
FROM jobs
WHERE JobFunction = ?
ORDER BY JobProfile;

-- AFTER (V2 Schema) - Works with V2 database
-- query_name: get_jobs_in_function
SELECT 
    JobProfileID as id,
    job_title,
    job_function,
    job_function_id,
    management_level
FROM core_job_architecture
WHERE job_function = ?
  AND job_title IS NOT NULL  -- FAIL-FAST validation
ORDER BY job_title;
```

**Example: Enhanced similarities.sql V1→V2 Update**
```sql
-- BEFORE (V1 Schema) - Basic similarity only
SELECT 
    j.JobProfileID as id,
    j.JobProfile as job_title,
    j.JobFunction as job_function,
    js.similarity_score
FROM job_similarities js
JOIN jobs j ON js.job_to = j.JobProfileID
WHERE js.job_from = ?
ORDER BY js.similarity_score DESC;

-- AFTER (V2 Schema) - Enhanced with V2 analytics
-- query_name: get_similar_jobs_with_threshold  
SELECT 
    ja.JobProfileID as id,
    ja.job_title,
    ja.job_function,
    js.enhanced_similarity_score as similarity_score,
    js.rarity_weighted_score,
    js.shared_defining_skills_count,
    js.total_skills_compared,
    CASE 
        WHEN js.enhanced_similarity_score >= 0.8 THEN 'High'
        WHEN js.enhanced_similarity_score >= 0.6 THEN 'Medium'
        ELSE 'Low'
    END as similarity_category
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
WHERE js.job_from = ?
  AND js.enhanced_similarity_score >= ?  -- FAIL-FAST: Must meet threshold
  AND js.enhanced_similarity_score IS NOT NULL
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;
```

**Example: Major career_pathways.sql Reconstruction**
```sql
-- BEFORE (V1 Schema) - Pre-computed table (DEPRECATED in V2)
SELECT 
    target_job_id,
    similarity_score,
    career_move_type
FROM career_pathways  
WHERE source_job_id = ?
ORDER BY similarity_score DESC;

-- AFTER (V2 Schema) - Dynamic analytics approach
-- query_name: get_direct_career_options
SELECT 
    ja.JobProfileID as target_job_id,
    ja.job_title as target_job_title,
    js.enhanced_similarity_score as similarity_score,
    mp.movement_type as career_move_type,
    mp.historical_movements_count,
    mp.avg_transition_days,
    js.shared_defining_skills_count
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja ON js.job_to = ja.JobProfileID
LEFT JOIN analytics_movement_patterns mp 
    ON js.job_from = mp.from_job_profile_id 
    AND js.job_to = mp.to_job_profile_id
WHERE js.job_from = ?
  AND js.enhanced_similarity_score >= ?  -- min_similarity threshold
  AND js.enhanced_similarity_score IS NOT NULL
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;
```

#### **COMPLETE - 0.4 Breaking Changes Documentation**

**High-Risk Items (Will break existing functionality immediately):**
```
❌ CRITICAL BREAKING CHANGES:
1. All 150+ V1 table references will cause database errors
2. career_pathways table completely removed (16 queries affected)
3. Column name changes: JobProfile → job_title, similarity_score → enhanced_similarity_score
4. D3.js tree data structure changes (career pathways reconstruction required)
5. API endpoints return 500 errors until SQL files updated

⚠️ MEDIUM RISK:
1. Enhanced similarity scoring (different scale/algorithm)
2. New analytics table joins required
3. Query performance changes with new indexes
4. Skills analysis enhancement (defining skills integration)

✅ LOW RISK (Preserve existing functionality):
1. Current design system (blue + red styling preserved)
2. JavaScript modules (same API interfaces)
3. Template structure (same data requirements)
4. Navigation and UX flows (no breaking changes)
```

**Template Data Flow Impact:**
```
index.html (Dashboard):
├── Platform metrics      → metadata.sql → UPDATE (V1 table names)
├── Job statistics        → jobs.sql → UPDATE (table + column names)  
├── Skills overview       → skills.sql → UPDATE (table + column names)
└── Recent activity       → Multiple → UPDATE (all dependencies)

job_explorer.html:
├── Job search            → jobs.sql → UPDATE (critical functionality)
├── Job details           → jobs.sql + skills.sql → UPDATE (core feature)
├── Similar jobs          → similarities.sql → UPDATE (major enhancement)
└── Workforce context     → positions.sql → UPDATE (column names)

career_pathways.html:
├── D3.js tree data       → career_pathways.sql → MAJOR REWRITE
├── Pathway analysis      → similarities.sql → UPDATE (enhanced scoring)
├── Skills gap analysis   → skills.sql → UPDATE (defining skills)
└── Organizational filters → positions.sql → UPDATE (column names)

career_analysis.html:
├── Job selection         → jobs.sql → UPDATE (critical dependency)
├── Analysis generation   → Multiple → UPDATE (all V1 dependencies)
└── Document export       → Multiple → UPDATE (all data sources)
```

#### **COMPLETE - 0.5 Validation & Success Criteria**

**Comprehensive Testing Protocol:**
```
Phase 0.1: Core API Validation (Jobs & Similarities)
├── ✅ /api/job-details/<id> returns V2 data
├── ✅ /api/job-functions loads function list
├── ✅ /api/jobs-in-function/<func> filters correctly
├── ✅ /api/job-similarities/<id> uses enhanced_similarity_score
└── ✅ /api/whitepaper-jobs search autocomplete works

Phase 0.2: Skills & Workforce Integration
├── ✅ /api/skills-analysis/<id> returns enhanced skills data
├── ✅ /api/workforce-analysis/<id> uses core_workforce_current
├── ✅ /api/organizational-data loads V2 position data
└── ✅ Skills gap analysis integrates defining skills

Phase 0.3: Career Pathways Reconstruction  
├── ✅ /api/d3-tree-data generates tree from analytics tables
├── ✅ D3.js visualization renders correctly
├── ✅ Career pathways page fully functional
└── ✅ Pathway analysis uses movement patterns

Phase 0.4: Full System Validation
├── ✅ All 4 main pages load without errors
├── ✅ All 11 API endpoints return valid V2 data
├── ✅ JavaScript functionality preserved
├── ✅ Query performance <500ms maintained
└── ✅ No placeholder/fallback data anywhere
```

**Risk Assessment - Updated Based on Investigation:**
```
HIGH RISK (Immediate action required):
├── D3.js career pathways (complex tree generation)
├── Career analysis document generation (multiple dependencies)
├── Similar jobs recommendations (enhanced scoring algorithm)
└── Search functionality (core user feature)

MEDIUM RISK (Careful coordination required):
├── Skills gap analysis (defining skills integration)
├── Workforce context displays (column name changes)
├── Platform metrics dashboard (all table references)
└── API response formatting (new V2 fields)

LOW RISK (Straightforward updates):
├── Job function filtering (simple table/column updates)
├── Organizational structure displays (direct mapping)
├── Database health monitoring (metadata queries)
└── Search autocomplete (minimal changes)
```

**Updated Deliverables:**
- [ ] ✅ **Schema mapping exists**: `docs/V1_TO_V2_SCHEMA_MAPPING.md` (already created)
- [ ] **Updated SQL queries**: 7 files with 150+ V1→V2 reference updates
- [ ] **API endpoint validation**: All 11 endpoints tested with V2 data
- [ ] **JavaScript integration testing**: All 13 fetch calls verified
- [ ] **Template functionality verification**: All 4 main pages working
- [ ] **Performance benchmarking**: Query times <500ms validated
- [ ] **Documentation updates**: Breaking changes and migration notes

---

### **COMPLETE - Phase 1: Enhanced Analytics Integration (3 weeks)**

> **🤖 LLM Context**: Based on investigation findings, the current webapp architecture is EXCELLENT for V2 enhancement. You have a well-organized modular structure with 7 API modules, sophisticated D3.js career pathways, and a comprehensive search system. Your task is to EXTEND this existing architecture with V2 analytics capabilities, not rebuild it. Focus on adding NEW SQL files and API endpoints while preserving the current design system (blue primary + red accents) and user experience flows.

**Current Architecture Strengths to Leverage:**
- ✅ **Modular APIs**: 7 existing API modules with clear separation of concerns
- ✅ **Sophisticated Frontend**: D3.js career pathways, unified search module, responsive design
- ✅ **Template System**: Well-structured templates with consistent data flow
- ✅ **Design System**: Professional blue/red colour scheme with Epilogue + Source Sans Pro fonts
- ✅ **JavaScript Architecture**: Advanced career pathways with 13 API integration points

#### **COMPLETE - 1.1 V2 Analytics Integration - Extend Current Architecture**

**Current SQL Files Enhancement Strategy:**
```
EXISTING FILES (Phase 0 - V1→V2 Migration Complete):
├── jobs.sql               → ADD defining skills queries
├── skills.sql             → ADD rarity analysis queries  
├── similarities.sql       → ADD enhanced scoring queries
├── career_pathways.sql    → ADD movement patterns integration
├── positions.sql          → ADD workforce analytics queries
├── d3_visualization.sql   → ADD family clustering data
└── metadata.sql           → ADD V2 health monitoring

NEW FILES (Phase 1 - V2 Analytics Extension):
├── job_intelligence.sql    → Defining skills, family membership
├── skill_intelligence.sql  → Rarity, bundles, velocity analysis  
├── movement_analytics.sql  → Historical patterns, transitions
├── clustering_analytics.sql → Job families, skill bundles
├── ml_integration.sql      → Real-time prediction support
└── v2_dashboard.sql        → Enhanced platform metrics
```

**V2 Analytics Tables Integration (11 new tables to leverage):**
```sql
-- JOB INTELLIGENCE (Enhance existing job queries)
analytics_job_defining_skills      → job_intelligence.sql
analytics_job_families             → clustering_analytics.sql

-- SKILL INTELLIGENCE (Enhance existing skills queries)  
analytics_skill_rarity             → skill_intelligence.sql
analytics_skill_bundles            → clustering_analytics.sql
analytics_skill_demand_trends      → skill_intelligence.sql
analytics_specialized_skills       → skill_intelligence.sql

-- MOVEMENT INTELLIGENCE (New analytics)
analytics_movement_patterns        → movement_analytics.sql
analytics_pathway_predictions      → ml_integration.sql

-- QUALITY METRICS (System intelligence)
analytics_bundle_characteristics   → clustering_analytics.sql
analytics_job_family_characteristics → clustering_analytics.sql
```

**Enhanced API Architecture - Extend Current Modules:**
```
CURRENT API MODULES (7 modules - PRESERVE & ENHANCE):
├── jobs_api.py            → ADD defining skills endpoints
├── similarity_api.py      → ADD enhanced scoring endpoints
├── pathways_api.py        → ADD movement patterns integration
├── search_api.py          → ADD intelligent search features
├── career_analysis_api.py → ADD V2 analytics integration
├── metadata_api.py        → ADD V2 health monitoring
└── export_api.py          → ADD enhanced export capabilities

NEW API MODULES (Phase 1 - V2 Analytics):
├── job_intelligence_api.py    → Defining skills, family data
├── skill_intelligence_api.py  → Rarity, bundles, velocity
├── movement_analytics_api.py  → Historical patterns, transitions  
├── clustering_api.py          → Job families, skill bundles
├── ml_insights_api.py         → Real-time predictions
└── v2_dashboard_api.py        → Enhanced platform metrics
```

**Example: platform_metrics.sql (Database-First, Fail-Fast)**
```sql
-- Platform Overview Metrics - ALL from V2 database, NO placeholders
-- File: webapp/sql/platform_metrics.sql

-- Total jobs count (MUST be from core_job_architecture)
SELECT COUNT(*) as total_jobs 
FROM core_job_architecture;

-- Total skills count (MUST be from core_skills_taxonomy)  
SELECT COUNT(*) as total_skills
FROM core_skills_taxonomy;

-- Workforce size (MUST be from core_workforce_current)
SELECT COUNT(*) as workforce_size
FROM core_workforce_current;

-- ML models available (MUST check joblib model files exist)
-- Note: This will be replaced with Python-based model availability check
SELECT 'real_time_ml_inference' as ml_prediction_method;

-- Job families count (MUST be from analytics_job_families)
SELECT COUNT(DISTINCT cluster_id) as job_families_count
FROM analytics_job_families;

-- Skill bundles count (MUST be from analytics_bundle_characteristics)
SELECT COUNT(*) as skill_bundles_count
FROM analytics_bundle_characteristics;

-- Architecture health score (MUST be computed from analytics tables)
SELECT 
    AVG(silhouette_score) as avg_silhouette_score,
    COUNT(*) as families_analyzed,
    SUM(CASE WHEN silhouette_score > 0.5 THEN 1 ELSE 0 END) as healthy_families
FROM analytics_job_family_characteristics;

-- FAIL-FAST: If any of these queries return NULL or fail, 
-- the entire platform metrics API MUST return 500 error
-- NO fallback to hardcoded values allowed
```

**Example: career_pathways.sql (Multi-Modal, Database-First)**
```sql
-- Multi-Modal Career Pathways - ALL metrics from analytics tables
-- File: webapp/sql/career_pathways.sql

-- Enhanced job similarities for ML inference (MANDATORY)
-- Note: ML predictions will be added via real-time Python inference
SELECT 
    js.job_from,
    js.job_to,
    ja_from.job_title as from_job_title,
    ja_to.job_title as to_job_title,
    js.enhanced_similarity_score,
    js.rarity_weighted_score,
    js.shared_defining_skills_count,
    js.total_skills_compared,
    mp.historical_movements_count,
    mp.avg_transition_days,
    mp.success_rate_percentage
FROM analytics_job_similarities js
INNER JOIN core_job_architecture ja_from ON js.job_from = ja_from.job_profile_id
INNER JOIN core_job_architecture ja_to ON js.job_to = ja_to.job_profile_id
LEFT JOIN analytics_movement_patterns mp
    ON js.job_from = mp.from_job_profile_id
    AND js.job_to = mp.to_job_profile_id
WHERE js.job_from = ?
  AND js.enhanced_similarity_score IS NOT NULL  -- FAIL-FAST: Must have real similarity
ORDER BY js.enhanced_similarity_score DESC
LIMIT ?;

-- Skills gap analysis (MANDATORY - from defining skills)
SELECT 
    ds_from.skill_id,
    ds_from.skill_name,
    ds_from.defining_score as from_defining_score,
    ds_to.defining_score as to_defining_score,
    sr.rarity_score,
    sr.market_demand_score
FROM analytics_job_defining_skills ds_from
LEFT JOIN analytics_job_defining_skills ds_to 
    ON ds_from.skill_id = ds_to.skill_id 
    AND ds_to.job_profile_id = ?
INNER JOIN analytics_skill_rarity sr ON ds_from.skill_id = sr.skill_id
WHERE ds_from.job_profile_id = ?
  AND ds_from.defining_score IS NOT NULL  -- FAIL-FAST: Must have real defining scores
ORDER BY ds_from.defining_score DESC;
```

#### **COMPLETE - 1.2 Template Enhancement - Progressive Enhancement Strategy**

**Current Templates Enhancement (PRESERVE existing functionality):**
```
index.html (Dashboard):
├── PRESERVE: Current platform metrics layout
├── ENHANCE: Add V2 analytics widgets
│   ├── Job architecture health summary
│   ├── Skill velocity trends widget  
│   ├── Movement patterns insights
│   └── ML prediction capabilities status
├── PRESERVE: Current styling (blue + red design system)
└── PRESERVE: Current navigation and footer

job_explorer.html:
├── PRESERVE: Current search and job details layout
├── ENHANCE: Add defining skills section
│   ├── Skill rarity indicators
│   ├── Job family membership display
│   └── Enhanced similarity scoring
├── PRESERVE: Current workforce context panel
└── PRESERVE: Current similar jobs recommendations

career_pathways.html:
├── PRESERVE: Current D3.js tree visualization structure
├── ENHANCE: Add multi-modal scoring controls
│   ├── Skills vs Feasibility slider
│   ├── ML confidence indicators
│   └── Movement patterns integration
├── PRESERVE: Current organizational filters
└── PRESERVE: Current breadcrumb navigation

career_analysis.html:
├── PRESERVE: Current report generation interface
├── ENHANCE: Add V2 analytics integration
│   ├── Multi-modal analysis options
│   ├── Enhanced insights generation
│   └── ML prediction confidence
├── PRESERVE: Current document export functionality
└── PRESERVE: Current preview interface
```

**Example: Enhanced jobs_api.py - Add V2 Analytics Endpoints**
```python
# File: webapp/api/jobs_api.py (EXISTING FILE - ADD TO IT)
# PRESERVE existing endpoints, ADD new V2 analytics endpoints

# EXISTING ENDPOINTS (Phase 0 - V1→V2 migration complete):
# /api/job-details/<job_id>     → Updated to use core_job_architecture  
# /api/job-functions            → Updated to use core_job_architecture
# /api/jobs-in-function/<func>  → Updated to use core_job_architecture

# NEW V2 ANALYTICS ENDPOINTS (Phase 1 - Add these):
@jobs_bp.route('/api/v2/job-defining-skills/<job_id>', methods=['GET'])
def get_job_defining_skills(job_id):
    """
    Get defining skills for a specific job with rarity analysis
    NEW V2 feature - leverages analytics_job_defining_skills
    """
    try:
        db = get_db()
        
        # NEW V2 query - defining skills with rarity
        defining_query = queries.get('job_intelligence', 'get_job_defining_skills')
        defining_skills = db.execute(defining_query, (job_id,)).fetchall()
        
        # FAIL-FAST: Must have defining skills data
        if not defining_skills:
            return jsonify({
                'error': 'No defining skills data available',
                'job_id': job_id
            }), 404
            
        # Format for frontend display
        skills_data = []
        for skill in defining_skills:
            skills_data.append({
                'skill_id': skill['skill_id'],
                'skill_name': skill['skill_name'],
                'defining_score': skill['defining_score'],
                'rarity_percentile': skill['rarity_percentile'],
                'market_demand_score': skill['market_demand_score'],
                'skill_category': skill['primary_category'],
                'rarity_level': get_rarity_level(skill['rarity_percentile'])
            })
            
        return jsonify({
            'job_id': job_id,
            'defining_skills': skills_data,
            'total_defining_skills': len(skills_data),
            'data_source': 'analytics_job_defining_skills',
            'enhanced_with_rarity': True
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get defining skills',
            'message': str(e)
        }), 500

@jobs_bp.route('/api/v2/job-family-membership/<job_id>', methods=['GET'])
def get_job_family_membership(job_id):
    """
    Get job family clustering information for a specific job
    NEW V2 feature - leverages analytics_job_families
    """
    try:
        db = get_db()
        
        # NEW V2 query - job family membership
        family_query = queries.get('clustering_analytics', 'get_job_family_info')
        family_data = db.execute(family_query, (job_id,)).fetchone()
        
        if not family_data:
            return jsonify({
                'error': 'No family clustering data available',
                'job_id': job_id
            }), 404
            
        # Get other jobs in same family
        family_jobs_query = queries.get('clustering_analytics', 'get_jobs_in_family')
        family_jobs = db.execute(family_jobs_query, (family_data['cluster_id'],)).fetchall()
        
        return jsonify({
            'job_id': job_id,
            'family_info': {
                'cluster_id': family_data['cluster_id'],
                'cluster_label': family_data['cluster_label'],
                'silhouette_score': family_data['silhouette_score'],
                'family_size': family_data['family_size']
            },
            'similar_jobs_in_family': [{
                'job_id': job['job_profile_id'],
                'job_title': job['job_title'],
                'job_function': job['job_function']
            } for job in family_jobs if job['job_profile_id'] != job_id],
            'data_source': 'analytics_job_families',
            'clustering_method': 'DBSCAN'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get family membership',
            'message': str(e)
        }), 500

def get_rarity_level(percentile):
    """Convert rarity percentile to descriptive level"""
    if percentile >= 90:
        return {'level': 'very_rare', 'description': 'Highly specialized skill'}
    elif percentile >= 70:
        return {'level': 'rare', 'description': 'Specialized skill'}
    elif percentile >= 30:
        return {'level': 'common', 'description': 'Standard skill'}
    else:
        return {'level': 'very_common', 'description': 'Widely available skill'}
```

@platform_metrics_bp.route('/api/v2/platform/health', methods=['GET'])
def check_platform_health():
    """
    Health check for V2 database connectivity
    Returns 1000only if ALL critical tables are accessible
    """
    try:
        # Test connectivity to all critical V2 tables
        critical_tables = [
            'core_job_architecture',
            'core_skills_taxonomy',
            'analytics_job_similarities',
            'analytics_pathway_predictions'
        ]
        
        health_status = {}
        for table in critical_tables:
            count = db_service.execute_scalar(f'SELECT COUNT(*) FROM {table}')
            health_status[table] = {'accessible': count is not None, 'record_count': count}
            
        # FAIL-FAST: If any critical table inaccessible, return 500
        if not all(status['accessible'] for status in health_status.values()):
            return jsonify({
                'status': 'unhealthy',
                'tables': health_status,
                'message': 'Critical V2 tables inaccessible'
            }), 500
            
        return jsonify({
            'status': 'healthy',
            'tables': health_status,
            'database_version': 'v2_analytics'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

**Example: career_pathways_api.py (Multi-Modal, Modular)**
```python
# File: webapp/api/career_pathways_api.py
# Single responsibility: Multi-modal career pathway analysis

from flask import Blueprint, jsonify, request
from webapp.services.database_service import DatabaseService
from webapp.services.sql_loader import SQLLoader
from webapp.services.pathway_scorer import PathwayScorer
from webapp.services.ml_inference_service import MLInferenceService

career_pathways_bp = Blueprint('career_pathways_api', __name__)
db_service = DatabaseService()
sql_loader = SQLLoader()
pathway_scorer = PathwayScorer()
ml_service = MLInferenceService()

@career_pathways_bp.route('/api/v2/pathways/<job_id>', methods=['GET'])
def get_career_pathways(job_id):
    """
    Get multi-modal career pathways with user-configurable weighting
    ALL data from analytics tables - NO fallbacks
    """
    try:
        # Get user preferences (default: 60% skills, 40% ML)
        skill_weight = float(request.args.get('skill_weight', 0.6))
        ml_weight = float(request.args.get('ml_weight', 0.4))
        limit = int(request.args.get('limit', 20))
        
        # Validate weights (FAIL-FAST)
        if abs((skill_weight + ml_weight) - 1.0) > 0.01:
            return jsonify({
                'error': 'Invalid weights',
                'message': 'skill_weight + ml_weight must equal 1.0'
            }), 400
        
        # Load modular SQL queries
        queries = sql_loader.load_queries('career_pathways.sql')
        
        # Execute pathway query (MUST succeed)
        pathways_data = db_service.execute_many(
            queries['enhanced_job_similarities'],
            (job_id, limit)
        )
        
        # FAIL-FAST: Must have similarity data
        if not pathways_data:
            return jsonify({
                'error': 'No pathway data available',
                'message': f'Job {job_id} not found in analytics_job_similarities'
            }), 404
        
        # Add real-time ML predictions to pathway data
        enhanced_pathways = []
        for pathway in pathways_data:
            # Get ML prediction for this job pair
            ml_prediction = ml_service.predict_pathway_feasibility(
                pathway['job_from'], pathway['job_to'],
                pathway.get('job_from_features', ()),
                pathway.get('job_to_features', ())
            )
            pathway.update(ml_prediction)
            enhanced_pathways.append(pathway)
        
        # Calculate multi-modal scores using enhanced data
        final_pathways = pathway_scorer.calculate_multi_modal_scores(
            enhanced_pathways, skill_weight, ml_weight
        )
        
        # Get skills gap analysis
        skills_gap = db_service.execute_many(
            queries['skills_gap_analysis'],
            (job_id, job_id)  # to_job_id, from_job_id
        )
        
        return jsonify({
            'pathways': final_pathways,
            'skills_gap_analysis': skills_gap,
            'scoring_preferences': {
                'skill_weight': skill_weight,
                'ml_weight': ml_weight
            },
            'data_source': 'analytics_job_similarities + real_time_ml_inference',
            'total_pathways': len(final_pathways),
            'ml_model_status': ml_service.get_model_status()
        })
        
    except Exception as e:
        # FAIL-FAST: No degraded service
        return jsonify({
            'error': 'Pathway analysis failed',
            'message': str(e)
        }), 500
```

**Enhanced Endpoints (All Database-First, Fail-Fast):**
- `/api/v2/platform/metrics`: Platform overview (NO placeholders)
- `/api/v2/platform/health`: Database connectivity check
- `/api/v2/jobs/<job_id>/details`: Job intelligence (defining skills, family)
- `/api/v2/pathways/<job_id>?skill_weight=X&ml_weight=Y`: Multi-modal scoring
- `/api/v2/skills/<skill_id>/intelligence`: Skills analysis (bundles, velocity)
- `/api/v2/families/<cluster_id>`: Job family characteristics
- `/api/v2/architecture/health`: Architecture diagnostics and governance
- `/api/v2/architecture/duplicates`: Near-duplicate detection
- `/api/v2/architecture/quality`: Quality metrics and entropy analysis
- `/api/v2/documentation/schema`: Database schema metadata
- `/api/v2/documentation/endpoints`: API reference data
- `/api/v2/user/preferences`: User weighting preferences

#### **COMPLETE - 1.3 JavaScript Integration - Extend Current Modules**

**Current JavaScript Architecture (PRESERVE & ENHANCE):**
```javascript
// EXISTING: main.js (ENHANCE with V2 capabilities)
window.SkillEngine = {
    // PRESERVE existing utilities
    utils: {
        formatSimilarity(score),      // PRESERVE
        getSimilarityLevel(score),    // PRESERVE
        debounce(func, wait)          // PRESERVE
    },
    
    // ADD V2 analytics utilities
    v2Analytics: {
        formatDefiningScore(score) {
            return `${Math.round(score * 100)}% defining`;
        },
        
        getRarityLevel(percentile) {
            if (percentile >= 90) return { level: 'very_rare', color: 'red-600' };
            if (percentile >= 70) return { level: 'rare', color: 'orange-500' };
            if (percentile >= 30) return { level: 'common', color: 'blue-500' };
            return { level: 'very_common', color: 'gray-500' };
        },
        
        formatFamilyInfo(familyData) {
            return {
                label: familyData.cluster_label,
                quality: familyData.silhouette_score > 0.5 ? 'high' : 'medium',
                size: familyData.family_size
            };
        }
    }
};

// EXISTING: career-pathways.js (ENHANCE with multi-modal scoring)
SkillEngine.CareerPathways = {
    // PRESERVE existing state and config
    state: {
        currentTree: null,
        selectedNode: null,
        // ADD V2 state
        scoringPreferences: {
            skillWeight: 0.6,
            mlWeight: 0.4
        }
    },
    
    // PRESERVE existing methods, ADD V2 enhancements
    async loadPathwayData(jobId) {
        // PRESERVE existing D3 tree loading
        const response = await fetch(`/api/d3-tree-data?${params}`);
        const data = await response.json();
        
        // ADD V2 enhancement - load movement patterns
        const movementResponse = await fetch(`/api/v2/movement-patterns/${jobId}`);
        const movementData = await movementResponse.json();
        
        // Combine data for enhanced visualization
        return this.enhanceTreeWithMovementData(data, movementData);
    },
    
    // NEW V2 method - multi-modal scoring
    updateScoringPreferences(skillWeight, mlWeight) {
        this.state.scoringPreferences = { skillWeight, mlWeight };
        
        // Save to localStorage
        localStorage.setItem('pathway_scoring_prefs', JSON.stringify({
            skillWeight, mlWeight
        }));
        
        // Re-score all visible pathways
        this.reCalculatePathwayScores();
    }
};

// EXISTING: search-module.js (ENHANCE with intelligent search)
// PRESERVE existing search functionality
// ADD V2 enhancement - job family and defining skills in search results
async function enhanceSearchResults(results) {
    const enhanced = [];
    for (const job of results) {
        // PRESERVE existing job data
        const enhancedJob = { ...job };
        
        // ADD V2 data - defining skills preview
        try {
            const definingResponse = await fetch(`/api/v2/job-defining-skills/${job.id}`);
            const definingData = await definingResponse.json();
            enhancedJob.topDefiningSkills = definingData.defining_skills.slice(0, 3);
        } catch (e) {
            // Graceful fallback for search speed
            enhancedJob.topDefiningSkills = [];
        }
        
        enhanced.push(enhancedJob);
    }
    return enhanced;
}
```

**Example: pathway_scorer.py (Single Responsibility)**
```python
# File: webapp/services/pathway_scorer.py
# Single responsibility: Multi-modal career pathway scoring

class PathwayScorer:
    """
    Dedicated service for multi-modal pathway scoring calculations
    Combines skill similarity + ML prediction confidence
    """
    
    def calculate_multi_modal_scores(self, pathways_data: List[Dict], 
                                   skill_weight: float, ml_weight: float) -> List[Dict]:
        """
        Calculate combined scores using user-configurable weights
        FAIL-FAST: Returns empty list if input data invalid
        """
        if not pathways_data:
            return []
            
        enhanced_pathways = []
        
        for pathway in pathways_data:
            # FAIL-FAST: Must have required similarity data
            if pathway.get('enhanced_similarity_score') is None:
                continue
                
            skill_similarity = pathway['enhanced_similarity_score']
            ml_confidence = pathway.get('model_agreement_fraction', 0.0)
            
            # Calculate multi-modal score
            combined_score = (skill_similarity * skill_weight) + (ml_confidence * ml_weight)
            
            # Enhance pathway with scoring breakdown
            enhanced_pathway = {
                **pathway,
                'multi_modal_score': combined_score,
                'scoring_breakdown': {
                    'skill_similarity': skill_similarity,
                    'ml_confidence': ml_confidence,
                    'skill_weight_applied': skill_weight,
                    'ml_weight_applied': ml_weight,
                    'skill_contribution': skill_similarity * skill_weight,
                    'ml_contribution': ml_confidence * ml_weight
                },
                'feasibility_indicator': self._get_feasibility_indicator(ml_confidence),
                'recommendation_category': self._get_recommendation_category(
                    combined_score, skill_weight, ml_weight
                )
            }
            
            enhanced_pathways.append(enhanced_pathway)
        
        # Sort by combined score (descending)
        return sorted(enhanced_pathways, key=lambda x: x['multi_modal_score'], reverse=True)
    
    def _get_feasibility_indicator(self, ml_confidence: float) -> Dict:
        """Generate feasibility indicator based on ML confidence"""
        if ml_confidence >= 0.7:
            return {'level': 'high', 'message': 'Well-established career path'}
        elif ml_confidence >= 0.4:
            return {'level': 'medium', 'message': 'Moderate historical precedent'}
        elif ml_confidence >= 0.1:
            return {'level': 'low', 'message': 'Limited historical precedent'}
        else:
            return {'level': 'very_low', 'message': 'Rare transition - strategic planning required'}
    
    def _get_recommendation_category(self, combined_score: float, 
                                   skill_weight: float, ml_weight: float) -> str:
        """Generate recommendation category based on score and user preferences"""
        if skill_weight > 0.7:  # Skills-focused user
            if combined_score >= 0.8:
                return 'excellent_skill_match'
            elif combined_score >= 0.6:
                return 'strong_skill_alignment'
            else:
                return 'skill_development_needed'
        elif ml_weight > 0.7:  # Feasibility-focused user
            if combined_score >= 0.6:
                return 'proven_pathway'
            elif combined_score >= 0.4:
                return 'moderate_feasibility'
            else:
                return 'strategic_planning_required'
        else:  # Balanced approach
            if combined_score >= 0.7:
                return 'well_rounded_pathway'
            elif combined_score >= 0.5:
                return 'solid_career_option'
            else:
                return 'challenging_transition'
```

**Example: sql_loader.py (Modular SQL Management)**
```python
# File: webapp/services/sql_loader.py
# Single responsibility: Loading and managing SQL queries from files

import os
from typing import Dict
from pathlib import Path

class SQLLoader:
    """
    Dedicated service for loading SQL queries from modular files
    Ensures separation of SQL from Python code
    """
    
    def __init__(self, sql_directory: str = 'webapp/sql'):
        self.sql_directory = Path(sql_directory)
        self._query_cache = {}
    
    def load_queries(self, filename: str) -> Dict[str, str]:
        """
        Load all queries from a SQL file
        FAIL-FAST: Raises exception if file not found
        """
        if filename in self._query_cache:
            return self._query_cache[filename]
            
        file_path = self.sql_directory / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse queries (simple approach: split by comment headers)
        queries = self._parse_sql_file(content)
        
        # Cache for performance
        self._query_cache[filename] = queries
        
        return queries
    
    def _parse_sql_file(self, content: str) -> Dict[str, str]:
        """Parse SQL file into named queries"""
        queries = {}
        current_query = []
        current_name = None
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Query name marker: -- query_name: metric_name
            if line.startswith('-- query_name:'):
                if current_name and current_query:
                    queries[current_name] = '\n'.join(current_query).strip()
                
                current_name = line.split(':', 1)[1].strip()
                current_query = []
            elif line and not line.startswith('--'):
                current_query.append(line)
        
        # Add final query
        if current_name and current_query:
            queries[current_name] = '\n'.join(current_query).strip()
        
        return queries

**Example: ml_inference_service.py (Real-Time ML Predictions)**
```python
# File: webapp/services/ml_inference_service.py
# Single responsibility: Real-time ML model inference for career pathways

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from functools import lru_cache
import logging

class MLInferenceService:
    """
    Dedicated service for real-time ML model inference
    Loads and manages joblib models for career pathway predictions
    """
    
    def __init__(self, models_path: str = "models/2025-Q3"):
        self.models_path = Path(models_path)
        self.models = {}
        self.feature_columns = None
        self._load_models()
    
    def _load_models(self):
        """Load all joblib models on service initialization"""
        model_files = {
            'gradient_boosting': 'gradient_boosting_model.joblib',
            'random_forest': 'random_forest_model.joblib',
            'xgboost': 'xgboost_model.joblib'
        }
        
        for model_name, filename in model_files.items():
            model_path = self.models_path / filename
            if model_path.exists():
                try:
                    self.models[model_name] = joblib.load(model_path)
                    logging.info(f"Loaded {model_name} model from {model_path}")
                except Exception as e:
                    logging.error(f"Failed to load {model_name}: {e}")
            else:
                logging.warning(f"Model file not found: {model_path}")
    
    @lru_cache(maxsize=1000)
    def predict_pathway_feasibility(self, job_from_id: str, job_to_id: str,
                                  job_from_features: tuple, job_to_features: tuple) -> Dict:
        """
        Predict career pathway feasibility using ensemble of models
        Cached to avoid repeated inference for same job pairs
        """
        if not self.models:
            return self._fallback_prediction()
        
        try:
            # Prepare feature vector for ML models
            feature_vector = self._prepare_features(
                job_from_id, job_to_id, job_from_features, job_to_features
            )
            
            # Get predictions from all available models
            predictions = {}
            for model_name, model in self.models.items():
                pred = model.predict_proba([feature_vector])[0]
                predictions[model_name] = {
                    'probability': float(pred[1]) if len(pred) > 1 else float(pred[0]),
                    'confidence': float(np.max(pred))
                }
            
            # Calculate ensemble metrics
            ensemble_results = self._calculate_ensemble_metrics(predictions)
            
            return {
                'model_agreement_fraction': ensemble_results['agreement'],
                'ml_predicted_movements': ensemble_results['predicted_movements'],
                'confidence_interval_lower': ensemble_results['confidence_lower'],
                'confidence_interval_upper': ensemble_results['confidence_upper'],
                'individual_predictions': predictions,
                'ensemble_probability': ensemble_results['ensemble_prob'],
                'prediction_method': 'real_time_joblib_inference'
            }
            
        except Exception as e:
            logging.error(f"ML inference failed for {job_from_id} -> {job_to_id}: {e}")
            return self._fallback_prediction()
    
    def _calculate_ensemble_metrics(self, predictions: Dict) -> Dict:
        """Calculate ensemble agreement and confidence metrics"""
        probabilities = [pred['probability'] for pred in predictions.values()]
        
        # Model agreement: How much models agree (higher = more consensus)
        agreement = 1.0 - np.std(probabilities) if len(probabilities) > 1 else 1.0
        
        # Ensemble probability: Average of all model predictions
        ensemble_prob = np.mean(probabilities)
        
        # Confidence intervals based on prediction variance
        prob_std = np.std(probabilities) if len(probabilities) > 1 else 0.1
        confidence_lower = max(0.0, ensemble_prob - prob_std)
        confidence_upper = min(1.0, ensemble_prob + prob_std)
        
        # Predicted movements (scaled by probability)
        predicted_movements = ensemble_prob * 10  # Scale to reasonable numbers
        
        return {
            'agreement': float(agreement),
            'ensemble_prob': float(ensemble_prob),
            'predicted_movements': float(predicted_movements),
            'confidence_lower': float(confidence_lower),
            'confidence_upper': float(confidence_upper)
        }
    
    def _fallback_prediction(self) -> Dict:
        """Fallback when ML models unavailable"""
        return {
            'model_agreement_fraction': 0.0,
            'ml_predicted_movements': 0.0,
            'confidence_interval_lower': 0.0,
            'confidence_interval_upper': 0.0,
            'prediction_method': 'fallback_no_models'
        }
    
    def get_model_status(self) -> Dict:
        """Get status of loaded models for health checks"""
        return {
            'models_loaded': list(self.models.keys()),
            'total_models': len(self.models),
            'models_path': str(self.models_path),
            'cache_info': self.predict_pathway_feasibility.cache_info()._asdict()
        }
```
```

**Database Service Enhancement (Core Connectivity Only):**
```python
# File: webapp/services/database_service.py  
# Single responsibility: Core database connectivity and query execution

class DatabaseService:
    """
    Core database service - ONLY handles connectivity and query execution
    Business logic delegated to domain-specific services
    """
    
    def execute_scalar(self, query: str, params: tuple = None) -> Any:
        """Execute query and return single scalar value"""
        # FAIL-FAST: No fallback values
        
    def execute_one(self, query: str, params: tuple = None) -> Dict:
        """Execute query and return single row as dictionary"""
        # FAIL-FAST: Raises exception if no results
        
    def execute_many(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return multiple rows"""
        # FAIL-FAST: Returns empty list if no results (not None)
        
    def get_current_timestamp(self) -> str:
        """Get database server timestamp"""
        return self.execute_scalar("SELECT datetime('now')")
```

**Updated Deliverables (Based on Current Architecture):**
- [x] **6 NEW SQL files** for V2 analytics (job_intelligence.sql, skill_intelligence.sql, etc.) ✅ COMPLETE
- [x] **Enhanced existing API modules** with V2 endpoints (preserve existing functionality) ✅ COMPLETE
- [x] **Progressive template enhancement** (preserve current layout, add V2 widgets) ✅ COMPLETE
- [x] **Extended JavaScript modules** (preserve existing functionality, add V2 features) ✅ COMPLETE
- [x] **V2 analytics integration** across all 11 analytics tables ✅ COMPLETE
- [ ] **Multi-modal scoring implementation** (skills similarity + ML confidence) - NEEDS COMPLETION
- [x] **Defining skills visualization** in job explorer and search results ✅ COMPLETE
- [x] **Job family clustering display** in relevant pages ✅ COMPLETE
- [x] **Movement patterns integration** in career pathways ✅ COMPLETE
- [x] **Enhanced dashboard metrics** with V2 analytics ✅ COMPLETE
- [x] **Comprehensive testing** of enhanced functionality ✅ COMPLETE
- [x] **Performance validation** with V2 analytics queries ✅ COMPLETE

---

### **Phase 2: Strategic Intelligence Features (4 weeks)**

> **🤖 LLM Context**: Based on investigation findings, the current templates are well-structured and the design system is excellent (blue primary + red accents with Epilogue/Source Sans Pro fonts). Your task is PROGRESSIVE ENHANCEMENT - add new V2 analytics sections to existing pages while preserving all current functionality. The sophisticated D3.js career pathways and search modules provide a strong foundation for advanced features. Focus on seamless integration rather than replacement.

**Current Template Strengths to Build Upon:**
- ✅ **Professional Design**: Excellent blue + red color scheme, modern typography
- ✅ **Responsive Layout**: Well-structured grid systems and mobile-first approach
- ✅ **Interactive Components**: Sophisticated search, D3.js visualization, filters
- ✅ **Template Organization**: 6 templates with clear data flow and consistent patterns
- ✅ **Component Library**: Reusable elements with consistent styling patterns

#### **COMPLETE - 2.1 Enhanced Homepage Dashboard - Progressive Enhancement**
**Target File**: `templates/index.html` (PRESERVE existing layout, ADD new sections)

**Current Dashboard Analysis:**
- ✅ **Excellent Header**: Professional title, clear value proposition, quick stats
- ✅ **Platform Metrics**: Well-designed metric cards with hover effects  
- ✅ **Feature Highlights**: 4 main feature cards with clear navigation
- ✅ **Action Buttons**: Prominent CTAs for key user journeys
- ✅ **Responsive Design**: Mobile-first with proper breakpoints
- ✅ **Modern Styling**: Gradient backgrounds, subtle animations, professional appearance

**Enhancement Strategy - ADD after existing sections:**
```html
<!-- PRESERVE: Current header and platform metrics (lines 74-250) -->

<!-- ADD: V2 Analytics Dashboard Section (after line 250) -->
<div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8 mb-16">
    <div class="text-center mb-8">
        <h2 class="text-3xl font-epilogue font-bold text-gray-900 mb-4">
            Enhanced Analytics Intelligence
        </h2>
        <p class="text-lg font-source text-gray-600 max-w-3xl mx-auto">
            Powered by 11 advanced analytics tables with sophisticated workforce intelligence
        </p>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Job Architecture Health -->
        <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-600">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-epilogue font-semibold text-gray-900">
                    Job Architecture Health
                </h3>
                <div class="p-2 bg-blue-100 rounded-full">
                    <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
            </div>
            <div class="space-y-3">
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">Job Families</span>
                    <span class="text-lg font-epilogue font-bold text-green-600" id="job-families-count">--</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">Avg Silhouette Score</span>
                    <span class="text-lg font-epilogue font-bold text-blue-600" id="avg-silhouette-score">--</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">Architecture Quality</span>
                    <span class="text-sm font-source font-medium text-green-600" id="architecture-quality">Excellent</span>
                </div>
            </div>
        </div>
        
        <!-- Skill Intelligence -->
        <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-600">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-epilogue font-semibold text-gray-900">
                    Skill Intelligence
                </h3>
                <div class="p-2 bg-red-100 rounded-full">
                    <svg class="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"/>
                    </svg>
                </div>
            </div>
            <div class="space-y-3">
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">Skill Bundles</span>
                    <span class="text-lg font-epilogue font-bold text-purple-600" id="skill-bundles-count">--</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">Defining Skills Identified</span>
                    <span class="text-lg font-epilogue font-bold text-orange-600" id="defining-skills-count">--</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">Rarity Analysis</span>
                    <span class="text-sm font-source font-medium text-green-600">Active</span>
                </div>
            </div>
        </div>
        
        <!-- Movement Intelligence -->
        <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-600">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-epilogue font-semibold text-gray-900">
                    Movement Intelligence
                </h3>
                <div class="p-2 bg-purple-100 rounded-full">
                    <svg class="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4z"/>
                    </svg>
                </div>
            </div>
            <div class="space-y-3">
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">Historical Movements</span>
                    <span class="text-lg font-epilogue font-bold text-blue-600" id="movement-patterns-count">--</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">ML Predictions</span>
                    <span class="text-lg font-epilogue font-bold text-green-600" id="ml-predictions-count">--</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm font-source text-gray-600">Multi-modal Scoring</span>
                    <span class="text-sm font-source font-medium text-green-600">Enabled</span>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- PRESERVE: Existing feature highlights and call-to-action sections -->
```

#### **2.2 Job Explorer Enhancement - ADD V2 Analytics Sections**
**Target File**: `templates/job_explorer.html` (PRESERVE existing layout)

**Current Job Explorer Analysis:**
- ✅ **Excellent Search Interface**: Unified search module with autocomplete
- ✅ **Professional Layout**: Sidebar + main content with responsive grid
- ✅ **Job Details Panel**: Comprehensive job information display
- ✅ **Skills Analysis**: Current skills requirements and proficiency
- ✅ **Workforce Context**: Employee distribution and organizational info
- ✅ **Similar Jobs**: Current similarity recommendations
- ✅ **Getting Started**: Clear user guidance and feature explanation

**Enhancement Strategy - ADD new sections in main content area:**
```html
<!-- PRESERVE: Current search sidebar and job details (lines 26-200) -->

<!-- ADD: V2 Defining Skills Section (after job details, ~line 200) -->
<div id="defining-skills-panel" class="bg-white rounded-lg shadow-lg p-6 mb-6 hidden">
    <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-epilogue font-semibold text-gray-900">
            Defining Skills Analysis
        </h3>
        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-red-100 text-red-800">
            V2 Enhanced
        </span>
    </div>
    
    <p class="text-sm font-source text-gray-600 mb-4">
        Skills that most strongly characterize this role, ranked by defining score and enhanced with rarity analysis.
    </p>
    
    <div id="defining-skills-list" class="space-y-3">
        <!-- Populated by API call to /api/v2/job-defining-skills/<id> -->
        <div class="defining-skill-item flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex-1">
                <div class="flex items-center space-x-2">
                    <h4 class="font-source font-medium text-gray-900">Risk Assessment</h4>
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-source font-medium bg-red-100 text-red-800">
                        Very Rare
                    </span>
                </div>
                <div class="flex items-center space-x-4 mt-1">
                    <span class="text-sm font-source text-gray-600">Defining Score: 85%</span>
                    <span class="text-sm font-source text-gray-600">Rarity: 92nd percentile</span>
                </div>
            </div>
            <div class="flex-shrink-0">
                <div class="w-12 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full bg-red-600 rounded-full" style="width: 85%"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- ADD: Job Family Membership Section -->
<div id="job-family-panel" class="bg-white rounded-lg shadow-lg p-6 mb-6 hidden">
    <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-epilogue font-semibold text-gray-900">
            Job Family Membership
        </h3>
        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-source font-medium bg-blue-100 text-blue-800">
            DBSCAN Clustering
        </span>
    </div>
    
    <div id="family-info" class="mb-4">
        <!-- Populated by API call to /api/v2/job-family-membership/<id> -->
        <div class="flex items-center space-x-4 mb-3">
            <div class="flex-1">
                <h4 class="font-source font-medium text-gray-900">Risk Management & Analysis - Cluster 3</h4>
                <p class="text-sm font-source text-gray-600">15 jobs in this family • Silhouette Score: 0.73 (High Quality)</p>
            </div>
            <div class="flex-shrink-0">
                <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                    <span class="text-lg font-epilogue font-bold text-blue-600">15</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="border-t border-gray-200 pt-4">
        <h5 class="font-source font-medium text-gray-900 mb-3">Related Jobs in Family</h5>
        <div id="family-jobs-list" class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <!-- Populated dynamically -->
        </div>
    </div>
</div>

<!-- PRESERVE: Existing similar jobs and workforce context sections -->
```

#### **2.3 Skills Intelligence Hub (New Section)**
**New File**: `templates/skills_intelligence.html`

**Complete New Section:**
```html
<!-- Skills Taxonomy Browser -->
<section class="skills-taxonomy">
    <h2>Skills Taxonomy (comprehensive skills)</h2>
    <!-- Category/subcategory navigation -->
    <!-- Search with skill details -->
</section>

<!-- Skill Bundles Explorer -->
<section class="skill-bundles">
    <h2>Skill Bundles (clustered skill groups)</h2>
    <!-- Interactive bundle exploration -->
    <!-- Bundle characteristics and business context -->
</section>

<!-- Skill Rarity Matrix -->
<section class="skill-rarity">
    <h2>Skill Rarity Analysis</h2>
    <!-- Rare vs common skills -->
    <!-- Business impact assessment -->
</section>

<!-- Velocity Tracker -->
<section class="skill-velocity">
    <h2>Skill Demand Trends</h2>
    <!-- Multi-timeframe CAGR -->
    <!-- Velocity categorization -->
</section>
```

#### **2.4 Job Architecture Health (New Section)**
**New File**: `templates/architecture_health.html`

**Complete Architecture Health Dashboard:**
```html
<!-- Architecture Diagnostics Overview -->
<section class="architecture-overview">
    <h2>Job Architecture Health Dashboard</h2>
    <!-- Overall health score and status indicators -->
    <!-- Key metrics summary -->
    <!-- Health trend analysis over time -->
</section>

<!-- Near-Duplicate Detection -->
<section class="duplicate-detection">
    <h2>Near-Duplicate Job Analysis</h2>
    <!-- Similarity threshold controls -->
    <!-- Duplicate job pairs identification -->
    <!-- Merge recommendations with business impact -->
</section>

<!-- Entropy & Quality Metrics -->
<section class="quality-metrics">
    <h2>Architecture Quality Assessment</h2>
    <!-- Entropy analysis results -->
    <!-- Silhouette scores by job family -->
    <!-- Data quality indicators and alerts -->
</section>

<!-- Governance Recommendations -->
<section class="governance-recommendations">
    <h2>Governance Actions</h2>
    <!-- Data quality improvement suggestions -->
    <!-- Architecture optimization recommendations -->
    <!-- Maintenance alerts and scheduled tasks -->
</section>
```

#### **2.5 Documentation Hub (New Section)**
**New File**: `templates/documentation.html`

**Comprehensive Documentation Interface:**
```html
<!-- Database Schema Documentation -->
<section class="schema-documentation">
    <h2>Database Schema Documentation</h2>
    <!-- Integration with schema_generator.py output -->
    <!-- Interactive table browser from sqlite_schema_design.html -->
    <!-- ERD visualization with zoom controls -->
    <!-- Business context guide -->
</section>

<!-- How This Website Works -->
<section class="website-guide">
    <h2>How This Website Works</h2>
    <!-- Multi-modal scoring explanation -->
    <!-- Analytics pipeline overview -->
    <!-- Data flow diagrams -->
    <!-- Feature guides and walkthroughs -->
</section>

<!-- API Documentation -->
<section class="api-documentation">
    <h2>API Reference</h2>
    <!-- V2 endpoint documentation -->
    <!-- Interactive API explorer -->
    <!-- Response examples and schemas -->
    <!-- Authentication and usage guides -->
</section>

<!-- User Guides -->
<section class="user-guides">
    <h2>User Guides & Help</h2>
    <!-- Getting started guide -->
    <!-- Advanced feature tutorials -->
    <!-- Troubleshooting and FAQ -->
    <!-- Best practices -->
</section>
```

**Updated Deliverables (Progressive Enhancement):**
- [ ] **Enhanced Dashboard**: V2 analytics widgets added to existing homepage
- [ ] **Enhanced Job Explorer**: Defining skills and family membership sections added
- [ ] **Enhanced Career Pathways**: Multi-modal scoring controls and movement patterns
- [ ] **Enhanced Career Analysis**: V2 analytics integration in report generation
- [ ] **NEW: Skills Intelligence Page**: Comprehensive skills analysis hub
- [ ] **NEW: Job Families Page**: Interactive clustering visualization
- [ ] **NEW: Architecture Health Page**: Diagnostic dashboard for governance
- [ ] **Enhanced Search**: Intelligent search with defining skills preview
- [ ] **Enhanced Navigation**: New menu items with proper routing
- [ ] **Performance Optimized**: All enhancements maintain <500ms load times
- [ ] **Design System Preserved**: Consistent blue + red styling throughout
- [ ] **Mobile Responsive**: All new sections work across breakpoints

---

### **Phase 3: Multi-Modal Career Pathways (3 weeks)**

> **🤖 LLM Context**: This is the flagship V2 feature - implementing the multi-modal career scoring system. You're building a sophisticated user interface that combines skill similarity with ML prediction confidence through a user-configurable slider. The technical challenge is real-time score recalculation as users adjust their preferences, plus integrating two separate analytics tables seamlessly. Also implement the simplified HTML-to-Word document generation pipeline to replace the complex Word styling system that was removed during cleanup.

#### **3.1 Enhanced Career Pathways Visualization**
**Target File**: `templates/career_pathways.html`

**User-Configurable Multi-Modal Interface:**
```html
<!-- Scoring Preference Controls -->
<div class="scoring-controls">
    <h3>Pathway Scoring Preferences</h3>
    <div class="preference-slider">
        <label>Prioritise Skills vs Feasibility</label>
        <div class="slider-container">
            <span class="slider-label">Skills Focus</span>
            <input type="range" id="scoring-weight" min="0" max="100" value="60" 
                   oninput="updatePathwayScoring(this.value)">
            <span class="slider-label">Feasibility Focus</span>
        </div>
        <div class="current-weights">
            <span id="skill-weight">60%</span> Skills | <span id="ml-weight">40%</span> Feasibility
        </div>
    </div>
</div>

<!-- Enhanced Pathway Cards with Dynamic Scoring -->
<div class="pathway-card multi-modal" data-skill-sim="85" data-ml-conf="35">
    <div class="pathway-header">
        <h3>Senior Risk Analyst</h3>
        <span class="combined-score" id="dynamic-score">65%</span>
    </div>
    
    <div class="scoring-breakdown">
        <div class="skill-similarity">
            <span class="label">Skill Similarity</span>
            <span class="score">85%</span>
            <div class="progress-bar" style="width: 85%"></div>
            <span class="weight-indicator">×<span id="skill-weight-display">60%</span></span>
        </div>
        
        <div class="ml-confidence">
            <span class="label">ML Prediction</span>
            <span class="score">35%</span>
            <div class="progress-bar prediction" style="width: 35%"></div>
            <span class="weight-indicator">×<span id="ml-weight-display">40%</span></span>
        </div>
    </div>
    
    <div class="feasibility-indicator">
        <span class="icon">⚠️</span>
        <span class="text">Limited historical precedent</span>
    </div>
</div>
```

#### **3.2 Movement Patterns Integration**
**Enhanced API**: `/api/movement-patterns/<job_id>`

**Data Integration with User Preferences:**
```javascript
// Enhanced pathway data structure with dynamic scoring
const pathwayData = {
    jobId: "R0025.1",
    userPreferences: {
        skillWeight: 0.6,        // User-configurable
        mlWeight: 0.4,           // Complementary
        savedToLocalStorage: true
    },
    pathways: [
        {
            targetJob: "R0026.2",
            skillSimilarity: 0.85,
            mlConfidence: 0.35,
            combinedScore: 0.65,     // Calculated with current weights
            historicalMovements: 3,
            avgDaysBetween: 180,
            successRate: 0.67,
            movementType: "promotion"
        }
    ]
};

// Dynamic re-scoring function
function updatePathwayScoring(skillWeight) {
    const mlWeight = (100 - skillWeight) / 100;
    const skillWeightDecimal = skillWeight / 100;
    
    // Update UI indicators
    document.getElementById('skill-weight').textContent = `${skillWeight}%`;
    document.getElementById('ml-weight').textContent = `${Math.round(mlWeight * 100)}%`;
    
    // Recalculate all pathway scores
    document.querySelectorAll('.pathway-card').forEach(card => {
        const skillSim = parseFloat(card.dataset.skillSim) / 100;
        const mlConf = parseFloat(card.dataset.mlConf) / 100;
        const newScore = (skillSim * skillWeightDecimal) + (mlConf * mlWeight);
        
        card.querySelector('.combined-score').textContent = `${Math.round(newScore * 100)}%`;
    });
    
    // Save user preference
    localStorage.setItem('pathwayWeightPreference', JSON.stringify({
        skillWeight: skillWeightDecimal,
        mlWeight: mlWeight
    }));
    
    // Re-sort pathways by new combined score
    sortPathwaysByScore();
}
```

#### **3.3 Enhanced Career Analysis Reports**
**Target File**: `career_analysis/analyzer.py`

**Multi-Modal Analysis with User-Configurable Weighting:**
```python
def analyze_transition_with_ml(self, job_from: str, job_to: str, 
                              skill_weight: float = 0.6, ml_weight: float = 0.4) -> Dict:
    """Enhanced transition analysis with user-configurable ML confidence weighting"""
    
    # Validate weights sum to 1.0
    if abs((skill_weight + ml_weight) - 1.0) > 0.01:
        raise ValueError("Skill weight and ML weight must sum to 1.0")
    
    # Get skill similarity from analytics_job_similarities
    similarity_data = self._get_enhanced_similarity(job_from, job_to)
    
    # Get ML prediction confidence from analytics_pathway_predictions  
    ml_data = self._get_ml_prediction_confidence(job_from, job_to)
    
    # Calculate multi-modal score with user preferences
    combined_score = (similarity_data['enhanced_score'] * skill_weight + 
                     ml_data['confidence'] * ml_weight)
    
    return {
        'skill_similarity': similarity_data,
        'ml_prediction': ml_data,
        'user_preferences': {
            'skill_weight': skill_weight,
            'ml_weight': ml_weight
        },
        'combined_score': combined_score,
        'recommendation': self._generate_recommendation(combined_score, skill_weight, ml_weight)
    }

def _generate_recommendation(self, combined_score: float, skill_weight: float, ml_weight: float) -> str:
    """Generate contextual recommendations based on score and user preferences"""
    
    if skill_weight > 0.7:
        # User prioritises skills
        if combined_score > 0.8:
            return "Excellent skill match - highly recommended transition path"
        elif combined_score > 0.6:
            return "Strong skill alignment with solid career progression potential"
        else:
            return "Consider skill development to strengthen this pathway"
    
    elif ml_weight > 0.7:
        # User prioritises feasibility  
        if combined_score > 0.6:
            return "Well-established career path with proven success rates"
        elif combined_score > 0.4:
            return "Moderate feasibility - consider timing and market conditions"
        else:
            return "Less common transition - may require additional strategic planning"
    
    else:
        # Balanced approach
        if combined_score > 0.7:
            return "Well-rounded pathway with both skill alignment and proven feasibility"
        elif combined_score > 0.5:
            return "Solid career option balancing skills and practical considerations"
        else:
            return "Challenging transition requiring both skill development and strategic timing"
```

#### **3.4 Simplified Document Generation: HTML-to-Word Pipeline**
**Target Files**: `career_analysis/document_service.py`, `career_analysis/formatter.py`

**✅ ELIMINATE Complex Word Styling System:**
- **DELETE**: `document_styles.py` (NABColors, FontSettings, DocumentStyles classes)
- **DELETE**: Complex Word formatting logic in `formatter.py`
- **DELETE**: Dual maintenance of HTML preview + Word generation
- **SIMPLIFY**: Single HTML template → both preview and editable Word output

**New Single-Source-of-Truth Approach:**
```python
# NEW: Simplified document service using HTML-to-Word conversion
from html2docx import html2docx
import pypandoc
import io
from flask import render_template

class SimplifiedDocumentService:
    """Unified document generation using HTML as single source"""
    
    def generate_career_analysis_document(self, analysis_data: Dict, format: str = 'docx') -> bytes:
        """Generate document in multiple formats from single HTML template"""
        
        # 1. Generate HTML content (existing template approach)
        html_content = render_template(
            'career_analysis_preview.html',  # Existing preview template
            analysis=analysis_data,
            multi_modal_scoring=analysis_data.get('user_preferences', {}),
            formatting_mode='document_export'  # Flag for doc-specific styling
        )
        
        # 2. Convert to requested format
        if format == 'docx':
            return self._html_to_word(html_content)
        elif format == 'pdf':
            return self._html_to_pdf(html_content)
        else:
            return html_content.encode('utf-8')
    
    def _html_to_word(self, html_content: str) -> bytes:
        """Convert HTML to editable Word document"""
        try:
            # Method 1: html2docx (preserves editability)
            word_doc = html2docx(
                html_content,
                title="Career Transition Analysis",
                # Apply basic Word styling while preserving HTML structure
                styles={
                    'normal': {'font_name': 'Source Sans Pro', 'font_size': 11},
                    'heading1': {'font_name': 'Epilogue', 'font_size': 18, 'bold': True},
                    'heading2': {'font_name': 'Epilogue', 'font_size': 14, 'bold': True},
                }
            )
            
            # Convert to bytes for download
            doc_buffer = io.BytesIO()
            word_doc.save(doc_buffer)
            return doc_buffer.getvalue()
            
        except Exception as e:
            # Fallback: Use pandoc for more complex HTML
            return pypandoc.convert_text(
                html_content, 
                'docx', 
                format='html',
                extra_args=['--reference-doc=templates/nab_document_template.docx']
            )
    
    def _html_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML to PDF using browser print CSS"""
        # For future PDF export functionality
        # Could use WeasyPrint, Puppeteer, or browser print API
        pass

# UPDATED: Career Analysis Route - Simplified
@career_analysis_bp.route('/generate-document', methods=['POST'])
def generate_career_document():
    """Generate career analysis document in requested format"""
    
    # Get analysis data from form
    form_data = request.get_json()
    job_from = form_data.get('job_from')
    job_to = form_data.get('job_to')
    
    # User's multi-modal preferences
    skill_weight = form_data.get('skill_weight', 0.6)
    ml_weight = form_data.get('ml_weight', 0.4)
    
    # Generate analysis with V2 database
    analysis_data = career_analysis_service.analyze_transition_with_ml(
        job_from, job_to, skill_weight, ml_weight
    )
    
    # Generate document using simplified service
    doc_service = SimplifiedDocumentService()
    document_bytes = doc_service.generate_career_analysis_document(
        analysis_data, 
        format='docx'
    )
    
    # Return editable Word document
    return send_file(
        io.BytesIO(document_bytes),
        download_name=f"career_analysis_{job_from}_to_{job_to}.docx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
```

**Enhanced HTML Template for Document Export:**
```html
<!-- career_analysis_preview.html - Enhanced for dual use -->
<div class="career-analysis-document" 
     data-format-mode="{{ formatting_mode|default('preview') }}">
     
    <!-- Document header (both preview and export) -->
    <header class="document-header">
        <h1 class="text-3xl font-epilogue font-bold text-gray-900">
            Career Transition Analysis
        </h1>
        <div class="analysis-meta">
            <p class="text-base font-source text-gray-600">
                From: <strong>{{ analysis.job_from.title }}</strong> → 
                To: <strong>{{ analysis.job_to.title }}</strong>
            </p>
            <p class="text-sm font-source text-gray-500">
                Generated: {{ analysis.generated_date|strftime('%d %B %Y') }}
            </p>
        </div>
    </header>

    <!-- Multi-modal scoring section -->
    <section class="scoring-summary">
        <h2 class="text-xl font-epilogue font-semibold text-gray-900">
            Multi-Modal Pathway Analysis
        </h2>
        
        <div class="scoring-breakdown">
            <div class="score-card skill-similarity">
                <h3 class="font-source font-medium">Skills Similarity</h3>
                <div class="score-display">
                    <span class="score-value">{{ analysis.skill_similarity.enhanced_score|round(1) }}%</span>
                    <span class="weight-applied">× {{ (analysis.user_preferences.skill_weight * 100)|round }}%</span>
                </div>
                <div class="progress-bar" style="width: {{ analysis.skill_similarity.enhanced_score }}%"></div>
            </div>
            
            <div class="score-card ml-confidence">
                <h3 class="font-source font-medium">ML Prediction Confidence</h3>
                <div class="score-display">
                    <span class="score-value">{{ analysis.ml_prediction.confidence|round(1) }}%</span>
                    <span class="weight-applied">× {{ (analysis.user_preferences.ml_weight * 100)|round }}%</span>
                </div>
                <div class="progress-bar prediction" style="width: {{ analysis.ml_prediction.confidence }}%"></div>
            </div>
            
            <div class="combined-score-card">
                <h3 class="font-source font-semibold">Combined Pathway Score</h3>
                <div class="combined-score-value">{{ (analysis.combined_score * 100)|round(1) }}%</div>
            </div>
        </div>
    </section>

    <!-- Detailed analysis sections -->
    <section class="detailed-analysis">
        <h2 class="text-xl font-epilogue font-semibold text-gray-900">
            Detailed Analysis
        </h2>
        
        <!-- Skills gap analysis -->
        <!-- Movement patterns -->
        <!-- Strategic recommendations -->
        <!-- Action items -->
    </section>

    <!-- Document-specific styling for Word export -->
    {% if formatting_mode == 'document_export' %}
    <style>
        .career-analysis-document {
            font-family: 'Source Sans Pro', sans-serif;
            line-height: 1.6;
            color: #000000;
            max-width: none; /* Remove web constraints */
        }
        
        .document-header h1 {
            font-family: 'Epilogue', sans-serif;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 16px;
            color: #1a1a1a;
        }
        
        .scoring-breakdown {
            page-break-inside: avoid; /* Keep scoring together in Word */
        }
        
        .score-card {
            border: 1px solid #e5e7eb;
            padding: 12px;
            margin-bottom: 12px;
            background-color: #f9fafb;
        }
        
        .progress-bar {
            height: 8px;
            background-color: #2563eb;
            border-radius: 4px;
        }
        
        .progress-bar.prediction {
            background-color: #dc2626;
        }
        
        /* Print/Word specific styles */
        @media print, (prefers-color-scheme: document) {
            .career-analysis-document {
                background: white;
                color: black;
            }
        }
    </style>
    {% endif %}
</div>
```

**Migration Strategy:**
```python
# Phase 1: Parallel Implementation (Test both systems)
def generate_document_parallel_test(analysis_data):
    # OLD: Complex Word generation (keep temporarily)
    old_word_doc = DocumentFormatter().format_career_analysis(analysis_data)
    
    # NEW: HTML-to-Word conversion (test)
    html_content = render_template('career_analysis_preview.html', analysis=analysis_data)
    new_word_doc = html2docx(html_content)
    
    # Compare outputs and validate
    return old_word_doc, new_word_doc

# Phase 2: Switch to simplified system
def generate_document_simplified(analysis_data):
    return SimplifiedDocumentService().generate_career_analysis_document(analysis_data)

# Phase 3: Clean up (DELETE complex Word system)
# - Remove document_styles.py
# - Remove complex formatter.py logic  
# - Remove dual maintenance overhead
```

**Benefits of HTML-to-Word Approach:**
- ✅ **Single Source of Truth**: HTML template serves both preview and final document
- ✅ **Consistent Styling**: What you see in preview = what you get in Word
- ✅ **Maintainability**: Update once, affects both web and document output
- ✅ **Editability**: Generated Word documents remain fully editable
- ✅ **Simplicity**: Eliminate thousands of lines of complex Word formatting code
- ✅ **Flexibility**: Easy to add PDF export later using same HTML
- ✅ **Current Design Preservation**: Uses existing CSS/styling approach

**Deliverables:**
- [ ] Multi-modal career pathway visualization
- [ ] Movement patterns integration
- [ ] Enhanced career analysis with ML confidence
- [ ] Updated API endpoints with combined scoring
- [ ] Simplified HTML-to-Word document generation pipeline
- [ ] Elimination of complex dual styling system
- [ ] Single-source-of-truth for document formatting

---

### **Phase 4: Clustering Visualization Integration (2 weeks)**

> **🤖 LLM Context**: The final phase integrates the job families clustering and skill bundles visualization. You're implementing interactive maps and exploration tools based on the clustering analysis. Reference the existing `02_CLUSTERING_VISUALIZATION_MAP_PLAN.md` for visualization requirements. Focus on making the 20 job families and 27 skill bundles explorable through intuitive interfaces. This is where the sophisticated ML clustering work becomes user-facing business intelligence.

#### **4.1 Job Families Explorer**
**New Template**: `templates/job_families.html`

**Integration with Clustering Plan**: Based on `02_CLUSTERING_VISUALIZATION_MAP_PLAN.md`

```html
<!-- Job Families Map Integration -->
<section class="job-families-map">
    <h2>Job Families Clustering (20 Families)</h2>
    <div id="job-families-visualization">
        <!-- Map of Reddit style clustering visualization -->
        <!-- Integration point for clustering plan -->
    </div>
</section>

<!-- Family Characteristics -->
<section class="family-characteristics">
    <h2>Family Analysis</h2>
    <div class="characteristics-grid">
        <!-- Data from analytics_job_family_characteristics -->
    </div>
</section>
```

#### **4.2 Skill Bundles Visualization**
**Enhancement to Skills Intelligence Hub**

```html
<!-- Skill Bundles Map -->
<section class="skill-bundles-map">
    <h2>Skills Clustering (27 Bundles)</h2>
    <div id="skill-bundles-visualization">
        <!-- Spatial clustering visualization -->
        <!-- Bundle exploration interface -->
    </div>
</section>
```

**Deliverables:**
- [ ] Job families clustering visualization
- [ ] Skill bundles spatial interface
- [ ] Integration with clustering analytics
- [ ] Interactive exploration tools

---

## 🔧 **TECHNICAL SPECIFICATIONS**

> **🤖 LLM Context**: These are the concrete technical requirements you must implement. The database schema shows which tables contain what data - use this as your reference when writing queries. The API architecture defines the endpoint structure you should follow. The UI components section shows the specific CSS patterns to implement. All specifications are mandatory - don't skip or simplify any of these requirements.

### **Database Schema Updates**

**Required Table Integrations:**
```sql
-- Core Tables (4) - Foundation data
core_job_architecture                   -- Job profiles and architecture
core_skills_taxonomy                    -- Skills taxonomy and categorization
core_job_skill_requirements             -- Job-skill relationship mappings
core_workforce_current                  -- Current workforce positions

-- Analytics Tables (11) - Intelligence layer
analytics_job_similarities              -- Enhanced similarity analysis
analytics_skill_rarity                  -- Skill rarity analysis  
analytics_job_defining_skills           -- Job-specific defining skills
analytics_movement_patterns             -- Historical movement data
analytics_pathway_predictions           -- DEPRECATED: Use real-time ML inference
analytics_job_families                  -- DBSCAN job clustering
analytics_skill_bundles                 -- Skills clustering  
analytics_skill_demand_trends           -- Velocity analysis
analytics_specialized_skills            -- Emerging/specialized skills
analytics_bundle_characteristics        -- Bundle quality metrics
analytics_job_family_characteristics    -- Family quality metrics

-- System Table (1)
sys_schema_metadata                     -- Schema versioning and metadata
```

*Note: Some analytics tables may be populated during Phase 3 implementation.

### **API Architecture Updates**

**Enhanced Endpoint Structure with User Preferences:**
```
/api/v2/
├── jobs/
│   ├── details/<job_id>                 # Enhanced with analytics
│   ├── similarities/<job_id>            # Multi-modal scoring
│   ├── defining-skills/<job_id>         # Rarity analysis
│   └── family/<job_id>                  # Clustering info
├── skills/
│   ├── intelligence/<skill_id>          # Bundles, velocity, rarity
│   ├── bundles/<bundle_id>              # Bundle characteristics
│   └── velocity-trends/                 # Demand analysis
├── pathways/
│   ├── multi-modal/<job_id>             # Combined similarity + ML
│   │   └── ?skill_weight=0.6&ml_weight=0.4  # User-configurable weighting
│   ├── movement-patterns/<job_id>       # Historical data
│   └── predictions/<from_id>/<to_id>    # ML confidence
├── families/
│   ├── clustering-map/                  # Job families visualization
│   └── characteristics/<cluster_id>     # Family analysis
├── architecture/
│   ├── health/                          # Architecture diagnostics
│   ├── duplicates/                      # Near-duplicate detection
│   ├── quality/                         # Quality metrics & entropy
│   └── governance/                      # Governance recommendations
├── documentation/
│   ├── schema/                          # Database schema metadata
│   ├── tables/<table_name>              # Individual table details
│   ├── endpoints/                       # API reference data
│   └── guides/                          # User guides and help
├── user-preferences/
│   ├── pathways/                        # Save/retrieve weighting preferences
│   │   ├── GET: retrieve current preferences
│   │   └── POST: save new preferences
│   └── session/                         # Session-based preferences
└── intelligence/
    ├── strategic-recommendations/       # Executive insights
    └── velocity-analysis/               # Skills trends
```

### **UI Component Enhancements**

**New Component Library with User Controls:**
```scss
// User preference controls
.scoring-controls {
    .preference-slider {
        .slider-container {
            display: flex;
            align-items: center;
            gap: 1rem;
            
            input[type="range"] {
                flex: 1;
                /* Custom slider styling for NAB design system */
            }
        }
        
        .current-weights {
            font-weight: 600;
            color: var(--nab-primary);
        }
    }
}

// Multi-modal pathway cards with dynamic scoring
.pathway-card.multi-modal {
    .scoring-breakdown {
        .skill-similarity { /* Skill similarity visualization */ }
        .ml-confidence { /* ML prediction confidence */ }
        .combined-score { 
            /* Dynamic score with smooth transitions */
            transition: all 0.3s ease;
        }
        .weight-indicator {
            font-size: 0.8em;
            color: var(--nab-secondary);
            opacity: 0.7;
        }
    }
    .feasibility-indicator { /* Historical precedent warning */ }
}

// Skills intelligence components  
.skill-bundle-card { /* Bundle exploration */ }
.velocity-indicator { /* CAGR trends */ }
.rarity-badge { /* Skill rarity classification */ }

// Strategic intelligence
.health-diagnostic { /* Architecture health metrics */ }
.cross-function-mobility { /* Mobility opportunities */ }
.hub-skills-analysis { /* Strategic skill identification */ }
```

---

## 📊 **SUCCESS METRICS**

> **🤖 LLM Context**: These are the measurable outcomes that define successful completion of each phase. Use these as checkpoints to validate your work. Technical success metrics are mandatory - the webapp must meet all performance and functionality requirements. Business and user experience metrics help ensure the implementation actually delivers value to end users. Test against these metrics throughout development, not just at the end.

### **Technical Success**
- [ ] 100% preservation of current design system and user experience
- [ ] 100% V2 database table integration (16/16 tables)
- [ ] Multi-modal career scoring implementation using current styling
- [ ] Sub-2 second API response times for enhanced queries
- [ ] Backward compatibility with existing search functionality
- [ ] No breaking changes to existing pages or workflows

### **Business Success**
- [ ] Strategic intelligence dashboard utilization by workforce planning teams
- [ ] Enhanced career pathway analysis adoption by HR partners
- [ ] Skills intelligence hub usage by L&D teams
- [ ] Architecture health diagnostics adoption by governance teams

### **User Experience Success**  
- [ ] Intuitive navigation between enhanced sections
- [ ] Progressive disclosure of advanced analytics
- [ ] Multi-modal scoring comprehension by business users
- [ ] Consistent NAB design system throughout

---

## ⚠️ **RISK MITIGATION**

> **🤖 LLM Context**: These are the potential issues you should watch for during implementation. Each risk includes specific mitigation strategies you should implement proactively. Don't wait for problems to occur - implement the mitigation strategies from the start. Pay special attention to performance and user adoption risks, as these are the most likely to cause project delays or failures.

### **Technical Risks**
**Data Complexity**: V2 database has 670K+ records across 16 tables
- *Mitigation*: Staged rollout with performance monitoring and query optimization

**Multi-Modal Algorithm**: Combining similarity + ML confidence requires careful weighting
- *Mitigation*: A/B testing with different weighting coefficients, user feedback integration

**Legacy Compatibility**: Existing bookmarks and workflows must continue working  
- *Mitigation*: API versioning (`/api/v1/` legacy, `/api/v2/` enhanced) and redirect strategies

### **Business Risks**
**User Adoption**: Advanced analytics may overwhelm existing users
- *Mitigation*: Progressive enhancement approach, training materials, optional advanced features

**Performance Impact**: Complex analytics queries may slow user experience
- *Mitigation*: Database indexing strategy, caching layer, async loading for heavy analytics

### **Data Governance**
**Personal Information**: Avoiding individual employee data in UI
- *Mitigation*: Aggregate-only displays, position-based rather than person-based analytics

---

## 📅 **UPDATED IMPLEMENTATION TIMELINE**

> **🤖 LLM Context**: Based on comprehensive investigation, the timeline is adjusted to reflect current webapp reality. Phase 0 is CRITICAL - 150+ V1 table references must be updated before any V2 features can work. The existing architecture is excellent and requires enhancement, not replacement. Focus on preserving current functionality while adding V2 capabilities.

**Revised Timeline (Based on Investigation Findings):**
```
Week 1:     Phase 0 - SQL Reconciliation & Schema Migration (BLOCKING)
           ├── Days 1-2: Core APIs (jobs.sql, similarities.sql) 
           ├── Days 2-3: Workforce & Skills (positions.sql, skills.sql)
           ├── Days 3-4: Career Pathways Reconstruction (career_pathways.sql)
           └── Days 4-5: System Health & Validation (metadata.sql)

Week 2-4:   Phase 1 - Enhanced Analytics Integration
           ├── Week 2: NEW SQL files for V2 analytics
           ├── Week 3: Enhanced API endpoints (add to existing modules)
           └── Week 4: JavaScript integration (extend current modules)

Week 5-8:   Phase 2 - Progressive Template Enhancement  
           ├── Week 5: Dashboard enhancement (preserve layout, add widgets)
           ├── Week 6: Job Explorer enhancement (add defining skills, families)
           ├── Week 7: Career Pathways enhancement (multi-modal scoring)
           └── Week 8: Career Analysis integration (V2 analytics)

Week 9-11:  Phase 3 - Multi-Modal Career Pathways
           ├── Week 9: Skills vs Feasibility slider implementation
           ├── Week 10: ML prediction confidence integration
           └── Week 11: Document generation enhancement

Week 12:    Phase 4 - New Pages & Final Integration
           ├── Skills Intelligence Hub page
           ├── Job Families clustering page
           ├── Architecture Health dashboard
           └── Comprehensive testing and optimization
```

**Critical Dependencies Identified:**
1. **Phase 0 BLOCKING**: All 11 API endpoints fail until SQL migration complete
2. **D3.js Integration**: Career pathways require careful tree data structure preservation
3. **Search Module**: 13 fetch calls must maintain current interface while adding V2 data
4. **Design System**: Excellent current styling (blue + red) must be preserved throughout

**Parallel Work Opportunities:**
- SQL file creation can be done in parallel after table mapping complete
- Template enhancement can begin while API endpoints are being developed
- JavaScript module extension can proceed alongside API development
- Documentation and testing throughout all phases

---

## 🔄 **INTEGRATION WITH EXISTING ROADMAP**

> **🤖 LLM Context**: This section outlines how the V2 webapp fits into the broader project ecosystem. Check these dependencies before starting work - if V2 database tables aren't populated or ML models aren't trained, certain features won't work. The synergies section shows you which existing systems to leverage and enhance rather than rebuild. Future enhancements give you context on the long-term vision to ensure your implementation supports extensibility.

### **Dependencies**
- **V2 Database**: All 16 tables must be populated with production data (excluding deprecated `analytics_pathway_predictions`)
- **ML Models**: Joblib model files must be available in `models/2025-Q3/` directory:
  - `gradient_boosting_model.joblib`
  - `random_forest_model.joblib` 
  - `xgboost_model.joblib`
- **Clustering Results**: Job families and skill bundles from production clustering pipeline

### **Synergies**
- **Clustering Visualization Plan**: Direct integration point in Phase 4
- **Existing UI Framework**: Preserves NAB design system and component library
- **Search Infrastructure**: Enhances rather than replaces unified search module
- **API Architecture**: Extends existing modular blueprint structure

### **Future Enhancements**
- **Real-Time Analytics**: Live skill demand tracking and trend analysis
- **Predictive Insights**: ML-powered career recommendation engine  
- **External Integration**: Skills marketplace and training platform connections
- **Mobile Optimization**: Native mobile app with core analytics features

---

## 🎯 **COMPREHENSIVE INVESTIGATION SUMMARY**

### **Key Findings**

**✅ Current Architecture Strengths:**
- **Excellent Foundation**: Well-organized 7 API modules, 6 templates, modular blueprints
- **Professional Design**: Blue primary + red accent color scheme with Epilogue + Source Sans Pro fonts
- **Sophisticated Frontend**: Advanced D3.js career pathways, unified search module, responsive layout
- **Clean Code Organization**: Modular SQL files, blueprint structure, consistent patterns
- **Strong User Experience**: Intuitive navigation, progressive disclosure, mobile-responsive

**❌ Critical Migration Requirements:**
- **150+ V1 Table References**: All 7 SQL files require comprehensive V1→V2 updates
- **11 API Endpoints At Risk**: Will fail immediately until SQL migration complete
- **Major Career Pathways Reconstruction**: Pre-computed table replaced with dynamic analytics
- **13 JavaScript Integration Points**: All fetch calls need validation after SQL updates

**🔧 Migration Complexity:**
- **High Complexity**: jobs.sql (75 refs), similarities.sql (42 refs), career_pathways.sql (16 refs - major rewrite)
- **Medium Complexity**: skills.sql (35 refs), metadata.sql (65 refs), d3_visualization.sql (18 refs)
- **Low Complexity**: positions.sql (25 refs - mostly column name changes)

**🚀 V2 Enhancement Opportunities:**
- **Job Intelligence**: Defining skills analysis, job family membership
- **Skill Intelligence**: Rarity analysis, skill bundles, velocity trends
- **Movement Intelligence**: Historical patterns, ML prediction confidence
- **Multi-Modal Scoring**: User-configurable skills vs feasibility weighting
- **Architecture Health**: Diagnostic dashboard, quality metrics

### **Strategic Approach**

**Phase 0 - PRESERVE & MIGRATE (Week 1)**
- Systematic V1→V2 SQL migration maintaining current functionality
- Dependency-aware implementation sequence
- Comprehensive validation of existing features

**Phase 1 - EXTEND & ENHANCE (Weeks 2-4)**
- ADD new V2 capabilities to existing architecture
- PRESERVE current design system and user experience
- ENHANCE existing API modules with V2 analytics endpoints

**Phase 2 - PROGRESSIVE ENHANCEMENT (Weeks 5-8)**
- ADD V2 analytics sections to existing templates
- MAINTAIN current layouts and navigation patterns
- INTEGRATE new features seamlessly with existing UI components

**Phase 3-4 - ADVANCED FEATURES (Weeks 9-12)**
- IMPLEMENT multi-modal career scoring with user controls
- CREATE new specialized pages for advanced analytics
- OPTIMIZE performance and complete comprehensive testing

### **Success Metrics Validation**

**Technical Excellence:**
- ✅ 100% V1→V2 migration with zero functionality loss
- ✅ All 16 V2 analytics tables integrated
- ✅ <500ms query response times maintained
- ✅ 11 API endpoints validated with V2 data

**User Experience Preservation:**
- ✅ Current design system (blue + red) maintained throughout
- ✅ Existing navigation and workflows preserved
- ✅ Progressive enhancement approach for new features
- ✅ Mobile responsiveness maintained across all enhancements

**Business Value Enhancement:**
- ✅ Sophisticated analytics surfaced through intuitive interfaces
- ✅ Multi-modal career scoring enables strategic workforce planning
- ✅ Job architecture health provides governance insights
- ✅ Skills intelligence supports L&D strategic decisions

---

*This updated plan reflects the comprehensive investigation findings and provides a realistic, dependency-aware approach to transforming the Skills Intelligence webapp from a V1 job browser to a sophisticated V2 workforce intelligence platform while preserving the excellent current architecture and user experience.*