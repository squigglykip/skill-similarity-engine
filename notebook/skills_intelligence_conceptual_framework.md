# Skills Intelligence Conceptual Framework

> **Updated**: January 2025  
> **Purpose**: Descriptive skill intelligence to support Future Skills Team's architectural thinking  
> **Philosophy**: Provide skill architecture maps, not strategic value judgments  
> **Status**: Refined framework focused on what we can actually know from our data

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

### **1. Skill Rarity Intelligence**
**Role**: **Job Archetype Definition**  
**Business Question**: *"What skills actually differentiate and define different roles?"*

**What it Measures**:
- Prevalence percentage across job profiles in the enterprise
- Identifies what makes roles unique and distinguishable
- **Enhanced Context**: Skill type metadata (Specialized Skill, Certification, Common Skill) for development pathway insights

**How This Supports Architectural Thinking**:
- **Role Differentiation**: Understand what truly makes a Data Scientist different from a Business Analyst
- **Defining Skills Identification**: Skills with <5% prevalence that are core to specific role archetypes
- **Capability Architecture**: Map the skill landscape to understand organisational capability structure
- **Training Investment Logic**: Focus development on skills that actually define roles

**Technical Approach**:
- Simple percentage calculation: `skill_prevalence = profiles_with_skill / total_profiles * 100`
- Categories: Rare (<5%), Uncommon (5-20%), Common (20-50%), Universal (>50%)
- **Future Enhancement**: Rarity-weighted job similarity scoring for more accurate job relationships

**What This Intelligence Enables**:
- Better job-to-job similarity calculations (rare skills matter more than common ones)
- Realistic career pathway assessment (focus on roles that share defining capabilities)
- Evidence-based training prioritisation (develop skills that actually differentiate roles)

**Status**: ✅ **Working Well** - Foundation for weighted similarity scoring

---

### **2. Skill Velocity Intelligence**
**Role**: **Temporal Context Provider**  
**Business Question**: *"What does recent movement data tell us about skill demand patterns?"*

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

**Status**: ✅ **Working Well** - Provides temporal context, not strategic direction

---

### **3. Network Intelligence (Skills Clustering)**
**Role**: **Skill Ecosystem Mapping**  
**Business Question**: *"How do skills naturally group together in our organisation?"*

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

**Status**: 🎯 **Priority Focus** - High value for architectural understanding

**Example Output**:
```
Cluster 1: Data Science Bundle {Python, SQL, Machine Learning, Statistics}
Cluster 2: Leadership Bundle {Strategic Planning, Team Management, Communication}  
Cluster 3: Digital Marketing Bundle {SEO, Analytics, Content Strategy, Social Media}
```

---

### **4. Job Opportunity Breadth Intelligence**
**Role**: **Transferability Descriptor**  
**Business Question**: *"How broadly distributed is this skill across different roles?"*

**What it Measures**:
- Simple count: number of job profiles that require this skill
- Direct transferability measurement without complex calculations
- **Important Caveat**: Describes current distribution, not strategic value

**How This Supports Architectural Thinking**:
- **Skill Distribution Understanding**: Know which skills are specialist vs. generalist
- **Career Pathway Context**: Understand the breadth of roles that involve specific skills
- **Capability Planning**: See which skills are concentrated vs. distributed across the organisation

**Technical Approach**:
- Direct percentage: `opportunity_breadth = job_profiles_with_skill / total_profiles * 100`
- Categories: Universal (≥20%), Cross-Functional (10-20%), Transferable (5-10%), Specialised (1-5%), Niche (<1%)

**What This Intelligence Enables**:
- Realistic career guidance conversations ("This skill appears in X% of roles")
- Training investment context (understand skill distribution patterns)
- Workforce planning insights (see which skills are concentrated vs. distributed)

**Status**: ✅ **Simplified and Working** - Clear, interpretable transferability measurement

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

### **The Rarity-Weighted Similarity Concept**

**Current State**: Simple skill overlap
```python
# Current: All skills weighted equally
simple_similarity = shared_skills / total_unique_skills
# Result: "Job A and Job B share 60% of skills"
```

**Enhanced State**: Rarity-weighted similarity  
```python
# Future: Rare skills carry more weight in job relationships
def calculate_weighted_job_similarity(job_a_skills, job_b_skills, skill_rarity_weights):
    shared_skills = job_a_skills & job_b_skills
    
    # Weight by inverse rarity (rare skills matter more for job relationships)
    weighted_overlap = sum(1/skill_rarity_weights[skill] for skill in shared_skills)
    max_possible_weight = sum(1/skill_rarity_weights[skill] for skill in job_a_skills | job_b_skills)
    
    return weighted_overlap / max_possible_weight
# Result: "Job A and Job B share 60% of skills, including 3 rare defining skills"
```

### **How This Supports the Future Skills Team**

**Better Job Architecture Understanding**:
- More accurate job-to-job relationships based on skills that actually differentiate roles
- Focus on defining capabilities rather than common skills everyone has

**Evidence-Based Strategic Discussions**:
- Clear data on what skills actually define different roles
- Factual foundation for strategic capability development decisions
- Understanding of current skill distribution without strategic bias

**Architectural Thinking Support**:
- Map the current skill landscape accurately
- Understand how skills cluster and connect across the organisation
- Provide factual foundation for strategic workforce architecture decisions

### **Implementation Strategy**

**Phase 1**: Perfect descriptive intelligence (current focus)
- Accurate skill rarity calculations and role differentiation
- Clear skill clustering and ecosystem mapping
- Reliable transferability measurements

**Phase 2**: Enhanced job relationship scoring
- Implement rarity-weighted similarity calculations
- Validate that rare skill overlap produces better job relationship assessments
- Test with stakeholder intuition about actual job similarities

**Phase 3**: Strategic architecture support
- Provide comprehensive skill architecture maps for strategic planning
- Enable evidence-based capability development decisions
- Support Future Skills Team's architectural and strategic thinking

**Status**: 🎯 **Foundation Ready** - Descriptive intelligence established, ready to support strategic thinking 