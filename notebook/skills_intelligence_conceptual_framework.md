# Skills Intelligence Conceptual Framework

> **Updated**: January 2025  
> **Purpose**: Descriptive skill intelligence to support Future Skills Team's architectural thinking  
> **Philosophy**: Provide skill architecture maps, not strategic value judgments  
> **Status**: Core backbone complete, supplemental insights in development

---

## 🎯 **Strategic Purpose: Descriptive Intelligence for Architectural Thinking**

### **What Skills Intelligence Provides**:
**Skill Architecture Maps** - Clear, factual descriptions of how skills are distributed and clustered across the organisation

### **What Skills Intelligence Does NOT Provide**:
**Strategic Value Judgments** - We don't determine which pathways are "high-value" or which skills are "strategically important"

### **Why This Distinction Matters**:
- **Historical movement data** might reflect reactive hiring patterns, not strategic direction
- **Popular pathways** might show organisational anxiety, not future value
- **The Future Skills Team** brings the strategic judgment; the engine provides the raw intelligence

---

## 📊 **Four Core Intelligence Dimensions**

### **1. Skill Rarity Intelligence** ✅ **COMPLETE**
**Role**: **Job Archetype Definition**  
**Business Question**: *"What skills actually differentiate and define different roles?"*
**Implementation**: `skill_intelligence_engine_v2.py`

**What it Measures**:
- Prevalence percentage across job profiles in the enterprise
- **Job-specific defining skills**: Top 25% rarest skills per role (not global threshold)
- Identifies what makes roles unique and distinguishable
- **Enhanced Context**: Skill type metadata (Specialized Skill, Certification, Common Skill) for development pathway insights

**How This Supports Architectural Thinking**:
- **Role Differentiation**: Understand what truly makes a Data Scientist different from a Business Analyst
- **Defining Skills Identification**: Top quartile rarest skills that characterize specific job profiles
- **Capability Architecture**: Map the skill landscape to understand organisational capability structure
- **Training Investment Logic**: Focus development on skills that actually define roles

**Technical Approach**: ✅ **IMPLEMENTED**
- Global prevalence calculation: `skill_prevalence = profiles_with_skill / total_profiles * 100`
- **Job-specific defining**: Top 25% rarest skills per job profile
- Categories: Rare (<5%), Uncommon (5-20%), Common (20-50%), Universal (>50%)
- **Rarity-weighted job similarity**: Asymmetrical A→B and B→A transitions with defining skills boost

**What This Intelligence Enables**:
- ✅ **Better job-to-job similarity calculations** (rare skills matter more than common ones)
- ✅ **Realistic career pathway assessment** (focus on roles that share defining capabilities)
- ✅ **Evidence-based training prioritisation** (develop skills that actually differentiate roles)
- ✅ **Asymmetrical transition analysis** (A→B ≠ B→A for directional career guidance)

**Status**: ✅ **COMPLETE** - Core backbone of skills intelligence established

---

### **2. Skill Velocity Intelligence** 🚧 **SUPPLEMENTAL INSIGHT**
**Role**: **Temporal Context Provider**  
**Business Question**: *"What does recent movement data tell us about skill demand patterns?"*
**Implementation**: `skill_velocity_analysis.py` *(to be created)*

**What it Measures**:
- Growth/decline trends over time using movement destination data
- Momentum and acceleration in skill demand patterns
- **Important Caveat**: This reflects what happened historically, not what should happen strategically

**How This Supports Architectural Thinking**:
- **Temporal Context**: Understand recent patterns in skill demand (without assuming they're strategically correct)
- **Change Detection**: Identify which skills are seeing increased/decreased movement activity
- **Pattern Recognition**: Spot organisational hiring trends and reactive patterns

**Technical Approach**:
- CAGR analysis from movement patterns to roles requiring the skill
- Momentum scoring based on recent trend direction
- Categories: Accelerating, Growing, Stable, Declining, Steep Decline

**What This Intelligence Enables**:
- Context for strategic discussions ("We've been hiring lots of X lately - is this reactive or strategic?")
- Baseline understanding of recent organisational behaviour
- Input for strategic workforce planning decisions (not the decision itself)

**Status**: 🚧 **SEPARATE FILE NEEDED** - Supplemental temporal insight

---

### **3. Network Intelligence (Skills Clustering)** 🚧 **SUPPLEMENTAL INSIGHT**
**Role**: **Skill Ecosystem Mapping**  
**Business Question**: *"How do skills naturally group together in our organisation?"*
**Implementation**: `skill_network_clustering.py` *(to be created)*

**What it Measures**:
- Co-occurrence patterns of skills within job profiles
- Natural skill families and bundles as they exist today
- Bridge skills that connect different domains

**How This Supports Architectural Thinking**:
- **Skill Ecosystem Understanding**: Map how skills cluster in practice across the organisation
- **Training Bundle Logic**: Understand which skills naturally appear together
- **Role Archetype Characterisation**: See the skill bundles that define different types of roles
- **Cross-Domain Connections**: Identify skills that bridge different functional areas

**Technical Approach**:
- Co-occurrence matrix of skills within job profiles
- DBSCAN clustering to identify natural skill groups
- Cluster characterisation and labelling

**What This Intelligence Enables**:
- Evidence-based training program design (bundle skills that actually appear together)
- Role archetype definition (understand the skill signatures of different job types)
- Strategic capability mapping (see how skills connect across the organisation)

**Status**: 🚧 **SEPARATE FILE NEEDED** - Supplemental network insight

**Example Output**:
```
Cluster 1: Data Science Bundle {Python, SQL, Machine Learning, Statistics}
Cluster 2: Leadership Bundle {Strategic Planning, Team Management, Communication}  
Cluster 3: Digital Marketing Bundle {SEO, Analytics, Content Strategy, Social Media}
```

---

### **4. Job Opportunity Breadth Intelligence** ✅ **COMPLETE**
**Role**: **Transferability Descriptor**  
**Business Question**: *"How broadly distributed is this skill across different roles?"*
**Implementation**: `skill_intelligence_engine_v2.py` (included in mobility score analysis)

**What it Measures**:
- Simple count: number of job profiles that require this skill
- Direct transferability measurement without complex calculations
- **Important Caveat**: Describes current distribution, not strategic value

**How This Supports Architectural Thinking**:
- **Skill Distribution Understanding**: Know which skills are specialist vs. generalist
- **Career Pathway Context**: Understand the breadth of roles that involve specific skills
- **Capability Planning**: See which skills are concentrated vs. distributed across the organisation

**Technical Approach**: ✅ **IMPLEMENTED**
- Direct percentage: `opportunity_breadth = job_profiles_with_skill / total_profiles * 100`
- Categories: Universal (≥20%), Cross-Functional (10-20%), Transferable (5-10%), Specialised (1-5%), Niche (<1%)
- **Integrated into mobility scoring**: Captured in skills gap analysis

**What This Intelligence Enables**:
- ✅ **Realistic career guidance conversations** ("This skill appears in X% of roles")
- ✅ **Training investment context** (understand skill distribution patterns)
- ✅ **Workforce planning insights** (see which skills are concentrated vs. distributed)

**Status**: ✅ **COMPLETE** - Integrated into core architecture analysis

---

## 🚫 **What We Explicitly Don't Do**

### **No Strategic Value Judgments**:
- ❌ We don't determine which pathways are "high-value"
- ❌ We don't identify "strategic" skills vs. "non-strategic" skills  
- ❌ We don't predict which capabilities will be important in the future

### **No Movement-Based Strategy**:
- ❌ We don't assume popular pathways are strategically valuable
- ❌ We don't treat historical movement patterns as strategic direction
- ❌ We don't confuse "what happened" with "what should happen"

### **No Complex Composites**:
- ❌ We don't create multi-dimensional scores that obscure individual insights
- ❌ We don't weight different intelligence types against each other
- ❌ We don't pretend to know which dimension matters most

---

## 📊 **Skills Intelligence as Strategic Foundation**

### **The Rarity-Weighted Similarity Concept** ✅ **COMPLETE**

**Current State**: ✅ **IMPLEMENTED** - Job-specific defining skills with asymmetrical analysis
```python
# IMPLEMENTED: Job-specific defining skills with rarity weighting
def create_job_specific_defining_skills(skill_universe, job_skills_df):
    # For each job: take top 25% rarest skills as "defining"
    # Global rarity calculation, job-specific application
    
def calculate_skills_mobility_score(job_a_id, job_b_id, ...):
    # Asymmetrical A→B analysis
    # Defining skills boost for shared rare capabilities
    # 0-100 scale with comprehensive skills gap analysis
```

### **How This Supports the Future Skills Team** ✅ **COMPLETE**

**Better Job Architecture Understanding**: ✅ **IMPLEMENTED**
- More accurate job-to-job relationships based on skills that actually differentiate roles
- Focus on defining capabilities rather than common skills everyone has

**Evidence-Based Strategic Discussions**: ✅ **IMPLEMENTED**
- Clear data on what skills actually define different roles
- Factual foundation for strategic capability development decisions
- Understanding of current skill distribution without strategic bias

**Architectural Thinking Support**: ✅ **IMPLEMENTED**
- Map the current skill landscape accurately
- Understand how skills cluster and connect across the organisation
- Provide factual foundation for strategic workforce architecture decisions

### **Implementation Strategy**

**Phase 1**: ✅ **COMPLETE** - Perfect descriptive intelligence (current focus)
- ✅ **Accurate skill rarity calculations and role differentiation**
- ✅ **Asymmetrical career transition analysis (A→B and B→A)**
- ✅ **Job-specific defining skills (top 25% rarest per role)**
- ✅ **Rarity-weighted mobility scoring with skills gap analysis**

**Phase 2**: 🚧 **IN PROGRESS** - Supplemental insights
- 🚧 **Temporal skill velocity analysis** (`skill_velocity_analysis.py`)
- 🚧 **Network clustering and skill ecosystem mapping** (`skill_network_clustering.py`)
- 🚧 **Comprehensive supplemental intelligence suite**

**Phase 3**: 🎯 **FUTURE** - Strategic architecture support
- Provide comprehensive skill architecture maps for strategic planning
- Enable evidence-based capability development decisions
- Support Future Skills Team's architectural and strategic thinking

**Status**: ✅ **CORE BACKBONE COMPLETE** - Supplemental insights in development 