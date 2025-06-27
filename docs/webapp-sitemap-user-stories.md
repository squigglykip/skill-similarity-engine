# NAB Skills Intelligence Platform - Webapp Sitemap & User Stories

**Version**: 1.0  
**Date**: 2025-01-08  
**Project Phase**: 8.2 Flask Webapp Development  
**Status**: Planning & Implementation

---

## 🎯 **Strategic Overview**

The NAB Skills Intelligence Platform is a **restricted-access strategic tool** designed exclusively for the Future Skills team to support data-driven workforce planning and capability analysis. Built on pre-computed job similarity matrices and comprehensive business context data, this platform provides sensitive workforce intelligence for strategic decision-making.

### **Core Value Propositions**
1. **Strategic Workforce Intelligence** - Data-driven insights for capability planning and workforce optimization
2. **Transition Impact Analysis** - Professional reports and analysis for organizational changes
3. **Skills-Based Decision Support** - Evidence-based recommendations for workforce transformation

---

## 👥 **User Personas & Access Control**

### **Primary Users** (RESTRICTED ACCESS ONLY)
- **Future Skills Team Members** - Strategic workforce analysts conducting capability assessments
- **Future Skills Team Leaders** - Senior strategists making workforce transformation recommendations
- **Authorized Strategic Partners** - Selected HR and business leaders with specific project access

### **Access Control Note**
> ⚠️ **SENSITIVE TOOL**: This platform contains highly sensitive workforce intelligence that informs strategic organizational decisions. Access is strictly limited to authorized Future Skills team members and selected strategic partners. All usage is logged and monitored.

---

## 🗺️ **Site Architecture & Navigation**

### **Information Architecture**
```
NAB Skills Intelligence Platform [RESTRICTED ACCESS]
├── 🏠 Strategic Dashboard (/)
├── 🔍 Workforce Intelligence (/workforce-intelligence/)
│   ├── Job Similarity Analysis
│   ├── Skills Capability Mapping
│   └── Role Comparison Tools
├── 📋 Strategic Reports (/strategic-reports/)
│   ├── Transition Impact Analysis
│   ├── Capability Assessment Reports
│   └── Workforce Optimization Studies
├── 🎯 Transition Pathways (/transition-pathways/)
│   ├── Role Transition Analysis
│   ├── Skills Gap Assessment
│   └── Redeployment Opportunities
├── 📊 Advanced Analytics (/analytics/)
│   ├── Skills Drift Analysis
│   ├── Capability Intelligence
│   └── Workforce Planning Insights
└── ℹ️ System Documentation (/documentation/)
    ├── User Guide
    ├── Methodology Documentation
    └── Data Sources & Quality
```

---

## 🎯 **Detailed Feature Specifications**

## **PHASE 1: Workforce Intelligence Core (8.2.3) - IN PROGRESS** 🚧

### **1.1 Job Similarity Analysis** (`/workforce-intelligence/similarity`)
**User Story**: *"As a Future Skills analyst, I need to identify roles with high similarity to assess transition opportunities and workforce optimization potential."*

**Functionality** (Strategic Focus):
- [ ] **Strategic Job Search Interface**
  - Advanced job search using JobProfile data from SQLite
  - Filter by JobFamily, JobFamilyGroup, business unit, location
  - Analysis history and saved searches for strategic projects
  - Advanced filtering (salary group, career level, position count)

- [ ] **Similarity Analysis Results**
  - Job cards with strategic information (title, family, similarity score, position count)
  - Visual similarity indicators with strategic context
  - Multi-select for bulk analysis and comparison
  - Export capabilities for strategic reports and presentations

**Database Queries**: `jobs.sql` → `search_jobs`, `get_job_families`

### **1.2 Role Transition Assessment** (`/workforce-intelligence/transitions`)
**User Story**: *"As a Future Skills analyst, I need to assess the viability of role transitions to support workforce planning recommendations."*

**Functionality** (Strategic Analysis):
- [ ] **Transition Viability Interface**
  - Query `job_similarities` table with strategic thresholds
  - Display comprehensive transition analysis with skills overlap
  - Categorise transition complexity (High viability >0.8, Medium >0.6, Low >0.4)
  - Show workforce impact metrics (position counts, business distribution)

- [ ] **Strategic Insights**
  - Expandable detailed transition analysis
  - Skills overlap visualization with strategic context
  - Bulk transition analysis for organizational planning
  - Export capabilities for strategic documentation

**Database Queries**: `similarities.sql` → `get_similar_jobs`, `get_top_similar_jobs`

### **1.3 Comparative Role Analysis** (`/workforce-intelligence/compare`)
**User Story**: *"As a Future Skills strategist, I need detailed role comparisons to understand workforce transformation requirements and opportunities."*

**Functionality** (Strategic Comparison):
- [ ] **Strategic Comparison Interface**
  - Select multiple jobs for comprehensive strategic analysis
  - Side-by-side skills and capability breakdown
  - Highlight skills transferability and development requirements
  - Display organizational context (teams, locations, position distribution)

- [ ] **Workforce Impact Analysis**
  - Visual representation of skills gaps and overlaps
  - Strategic assessment of transition complexity
  - Workforce redeployment opportunity identification
  - Export capabilities for strategic planning documentation

**Database Queries**: `skills.sql` → `get_skills_gap_between_jobs`, `jobs.sql` → `get_job_skills`

---

## **PHASE 2: Career Pathway Explorer (8.2.4) - PLANNED** 📋

### **2.1 Interactive Career Tree** (`/career-pathways`)
**User Story**: *"As a Risk Analyst, I want to see visual career pathways showing how I can progress to different roles over time."*

**Functionality** (Building on existing D3.js work):
- [ ] **D3.js Tree Visualization**
  - Interactive collapsible tree starting from current role
  - Multi-hop pathway discovery (depth 2-4 levels)
  - Colour-coded similarity strength between steps
  - Click-to-expand pathway exploration

- [ ] **Pathway Intelligence**
  - Pathway ranking algorithm based on similarity scores
  - Career progression logic (junior → senior role detection)
  - Alternative vs. recommended pathway highlighting
  - Geographic mobility considerations

**Database Queries**: `career_pathways.sql` → `get_career_progression_options`, `similarities.sql` → `get_top_similar_jobs`

### **2.2 Skills Development Roadmaps** (`/career-pathways/roadmap`)
**User Story**: *"As an employee, I want a personalized roadmap showing what skills I need to develop to reach my target role."*

**Functionality**:
- [ ] **Skill Gap Analysis per Pathway**
  - Calculate skills gaps for each step in career pathway
  - Prioritise skills by importance and transferability
  - Show skill adjacencies and prerequisites
  - Create learning pathway recommendations

- [ ] **Roadmap Visualization**
  - Timeline view of skill development journey
  - Milestone markers for pathway progression
  - Integration points with learning systems (future)
  - Progress tracking and achievement badges

**Database Queries**: `career_pathways.sql` → `get_skills_gap_analysis`, `skills.sql` → `get_skill_development_recommendations`

---

## **PHASE 3: Career Transition Analysis Generator (8.2.5) - PLANNED** 📋

### **3.1 Role Transition Reports** (`/career-analysis/create`)
**User Story**: *"As an HR partner, I need professional documentation when roles are being sunset to help employees understand their options."*

**Functionality**:
- [ ] **Report Configuration**
  - Single role or bulk team analysis selection
  - Customizable report sections and focus areas
  - Recipient personalization (name, current role, team)
  - NAB branding and professional formatting

- [ ] **Content Generation**
  - Automated job similarity analysis and ranking
  - Career pathway recommendations with rationale
  - Skills gap identification and development priorities
  - Market context and opportunity scoring

**Templates**: Jinja2 templates for PDF/Word generation

### **3.2 Team Transition Analysis** (`/career-analysis/bulk`)
**User Story**: *"As a manager planning team restructure, I need comprehensive analysis of where my team members could be redeployed."*

**Functionality**:
- [ ] **Bulk Analysis Engine**
  - Multi-role selection and batch processing
  - Team capacity and absorption analysis
  - Cross-functional mobility opportunities
  - Skills inventory and gap assessment

- [ ] **Executive Summary Generation**
  - High-level transition options and recommendations
  - Risk assessment and mitigation strategies
  - Timeline and resource requirements
  - Success metrics and monitoring framework

**Output Formats**: PDF, Word, PowerPoint slides, CSV data exports

---

## **PHASE 4: Workforce Analytics (Future) - PLANNED** 📊

### **4.1 Executive Dashboard** (`/analytics/dashboard`)
**User Story**: *"As a business leader, I want high-level insights into our workforce capabilities and transition opportunities."*

**Functionality** (RESTRICTED ACCESS):
- [ ] **Key Performance Indicators**
  - Workforce mobility index and transition success rates
  - Skills gap analysis across business units
  - Career pathway utilization and effectiveness
  - Employee engagement with career development tools

- [ ] **Strategic Intelligence**
  - Capability concentration and risk assessment
  - Skills demand trends and future requirements
  - Internal talent market dynamics
  - Workforce transformation progress tracking

### **4.2 Skills Drift Analysis** (`/analytics/drift`)
**User Story**: *"As Future Skills team, I want to understand how our skills taxonomy evolves and identify emerging capabilities."*

**Functionality** (Porting from enhanced_drift_analysis.ipynb):
- [ ] **Temporal Drift Analysis**
  - Skills taxonomy version analysis over time
  - Identification of obsolete vs. emerging skills
  - Skills lifecycle and evolution patterns
  - Industry benchmarking and trend analysis

- [ ] **Skills Intelligence**
  - Skills adjacency and transferability mapping
  - Capability gap identification and prioritization
  - Learning pathway optimization recommendations
  - Skills investment ROI analysis

**Database Queries**: Enhanced temporal analysis using `skills.Latest_Version` and processing timestamps

---

## 🚀 **Development Sprint Plan**

### **Sprint 1: Foundation (Current - 8.2.3)** 
*Estimated: 2 weeks*
- [ ] Complete job search templates (`job_search.html`, `similarity_results.html`)
- [ ] Implement basic job comparison functionality
- [ ] Polish existing D3.js career pathway work
- [ ] API endpoints for AJAX functionality

### **Sprint 2: Career Pathways (8.2.4)**
*Estimated: 3 weeks*
- [ ] Enhanced D3.js tree with skills gap integration
- [ ] Multi-hop pathway discovery engine
- [ ] Skills development roadmap generator
- [ ] Pathway filtering and recommendation algorithms

### **Sprint 3: Career Transition Analysiss (8.2.5)**
*Estimated: 2 weeks*
- [ ] Jinja2 template engine for report generation
- [ ] PDF/Word document generation system
- [ ] Bulk analysis and batch processing
- [ ] Professional NAB-branded report templates

### **Sprint 4: Analytics Platform (Future)**
*Estimated: 4 weeks*
- [ ] Executive dashboard with KPIs
- [ ] Skills drift analysis ported from notebook
- [ ] Workforce intelligence and capability mapping
- [ ] Advanced analytics and predictive insights

---

## 📐 **Technical Architecture Integration**

### **Database Integration Points**
- **jobs** table → Job search, comparison, and pathway discovery
- **job_similarities** table → Similarity scoring and pathway recommendations
- **positions** table → Workforce context and business intelligence
- **skills** table → Skills analysis, gap calculation, and drift tracking

### **Existing Assets Leveraged**
- ✅ SQLite business context database (comprehensive and optimized)
- ✅ Organized SQL queries (`similarities.sql`, `jobs.sql`, etc.)
- ✅ Professional NAB-styled UI components
- ✅ D3.js visualization foundation (career pathways)
- ✅ Flask app architecture with proper routing

### **Performance Considerations**
- Sub-2-second query response targets
- Smart caching for frequently accessed data
- Progressive loading for complex visualizations
- Efficient pagination for large result sets

---

## 🎯 **Success Metrics**

### **User Adoption Metrics**
- Monthly active users and session engagement
- Career pathway exploration completion rates
- Career Transition Analysis Generator volume and usage
- User satisfaction and feedback scores

### **Business Impact Metrics**
- Internal mobility success rates
- Workforce transition effectiveness
- Skills development program adoption
- Employee retention and career satisfaction

### **Technical Performance Metrics**
- Query response times and system reliability
- Data accuracy and completeness scores
- User interface responsiveness and accessibility
- System scalability and maintenance efficiency

---

## 📝 **Implementation Notes**

### **Design System Compliance**
- Follow NAB style guide (`nab-style-guide.md`)
- Consistent color palette and typography
- Accessible design patterns (WCAG compliance)
- Mobile-responsive layouts for tablet/phone access

### **Security & Privacy**
- Employee data privacy protection
- Role-based access control implementation
- Secure document generation and sharing
- Audit logging for sensitive operations

### **Future Integration Points**
- Learning Management System API integration
- HRIS real-time data synchronization
- External market intelligence data sources
- Enterprise collaboration platform integration

This sitemap provides the strategic foundation for building a comprehensive, user-focused Skills Intelligence Platform that delivers measurable business value while maintaining exceptional user experience. 
