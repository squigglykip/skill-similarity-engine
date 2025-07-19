# Predictive Career Pathway Engine - Context & Implementation Plan

> **Strategic Initiative**: Transform NAB's career pathway recommendations from descriptive skill-based suggestions to predictive, empirically-grounded strategic workforce intelligence  
> **Team**: Future Skills, Talent Business Unit, P&C  
> **Timeline**: Phase 1 (2 weeks) - Foundation & Discovery | Phase 2 (Ongoing) - Predictive Enhancement

---

## 🎯 **Strategic Context**

### **Current Challenge**
The workforce is undergoing fundamental transformation driven by AI/LLM adoption. NAB is proactively managing this through role rationalisation and strategic workforce planning. The Future Skills team needs to evolve from reactive colleague support to proactive, strategic workforce intelligence.

### **Business Problem**
- **Current State**: "Naive" career pathways based solely on asymmetric skill similarity
- **Pain Point**: Recommendations lack feasibility grounding - suggesting theoretically similar roles that may never actually happen
- **Business Risk**: Ineffective redeployment of impacted colleagues, missed strategic workforce planning opportunities
- **Strategic Opportunity**: Use skills as the language to express workforce transformation targets

### **Vision Statement**
Transform colleague conversations from:
> *"Here are some jobs you might have the skills for..."*

To:
> *"This role has been a successful transition for people in your situation. It aligns with your current skills, the bank's future, and we have a targeted development path for the gap."*

---

## 📊 **Current Data Assets**

### **Foundational Analytics Completed**
1. **Feature Evaluation Analysis** (`02_feature_evaluation_discovery_optimized.py`)
   - Comprehensive univariate and multivariate analysis
   - Job architecture features consistently outperformed organisational context
   - Movement characteristics (movement_count, avg_days_between) showed strong predictive power
   - Multivariate combinations peaked around 60-70% accuracy

2. **Role Typology & Pathway Enhancement** (`03_role_typology_pathway_enhancement_enhanced.py`)
   - Mobility scoring framework with tiers (Super Launchpad → Career Silo)
   - Job Profile level analysis providing actionable insights
   - Pathway probability calculations with confidence scoring
   - Enhanced architectural focus with defining skills analysis

3. **Skill Enrichment Analysis** (`skill_enrichment_analysis.py`)
   - Skill rarity categorisation (rare, uncommon, common, universal)
   - Growth trend analysis from internal movement patterns
   - Strategic priority scoring for development recommendations
   - Comprehensive skill mobility scoring

### **Key Data Infrastructure**
- **Movement Data**: 92,107+ movement events across 5+ years
- **Skills Taxonomy**: 40,170+ job-skill relationships mapped to 715 job profiles
- **Job Architecture**: Hierarchical structure (Function → Sub-Function → Job Profile → Management Level)
- **Workforce Context**: Current position assignments and organisational structure
- **Recency Weighting**: Aggressive exponential decay (40% annual decay rate) reflecting fast-changing banking environment

---

## 🧠 **Analytical Insights Driving Next Steps**

### **Validated Approaches**
1. **Random Forest + Gradient Boosting** consistently delivered best performance
2. **Job Profile level** provides optimal granularity for pathway analysis
3. **Dual confidence scoring** (Skills + Movement) enables transparent decision support
4. **Defining skills weighted by rarity** more predictive than common skill overlaps
5. **Mobility scores** effectively differentiate role types and career potential

### **Key Discovery: Skills vs Movement Intelligence**
- **Skills Intelligence**: Reveals hidden connections and non-obvious pathways
- **Movement Intelligence**: Grounds recommendations in organisational reality
- **Synthesis Need**: Combine both to surface strategic opportunities while maintaining feasibility

### **Architectural Decisions Made**
- **Recency Bias**: Aggressive exponential weighting (40% annual decay)
- **Analysis Level**: Job Profile (not position-level) for strategic relevance
- **Confidence Framework**: Multi-dimensional transparency over black-box predictions
- **Exclusions**: Employee group transitions (personal life choices, not career development)

---

## 🚀 **Phase 1: Predictive Engine Foundation (2 Weeks)**

### **Implementation Strategy: Cartesian Product Analysis with Smart Filtering**

Build two focused prediction engines that generate comprehensive job-to-job pathway analysis:

#### **Cartesian Product Scope**
- **Complete Coverage**: All 715 × 715 = 510,510 job profile pairs
- **Computational Optimization**: Exclude pairs with <10% confidence in both engines
- **Strategic Value**: Ensures no potentially valuable pathways are missed

#### **Engine 1: Movement Predictive Analysis (04_)**
- **Input**: Historical job profile transitions, mobility scores, pathway probabilities
- **Processing**: Historical success rates + target role mobility + recency weighting
- **Output**: Movement Confidence Score (0-100) for all 510,510 job profile pairs

#### **Engine 2: Skills Intelligence Predictive (05_)**
- **Input**: Current role skills, target role skills, skill rarity scores
- **Processing**: Defining skills overlap weighted by rarity tiers (rare=3x, uncommon=2x, common=1x)
- **Output**: Skills Confidence Score (0-100) for all 510,510 job profile pairs

#### **Smart Filtering Strategy**
- **Retention Criteria**: Keep pairs where either Movement OR Skills confidence ≥ 10%
- **Data Reduction**: Filter out low-potential pathways while preserving strategic opportunities
- **Consensus Integration**: Combine outputs for final pathway recommendations

### **Detailed Implementation Plan**

#### **Week 1: Foundation & Discovery**
1. **Data Integration Pipeline**
   - Consolidate existing analysis outputs into unified dataset
   - Implement aggressive recency weighting across all historical data
   - Create job profile movement matrices with confidence intervals

2. **Feature Importance Validation**
   - Apply mutual information analysis to validate optimal grouping dimensions
   - Chi-square testing for statistical significance of movement patterns
   - Feature selection using Random Forest importance rankings

3. **Role & Skill Typology Enhancement**
   - Expand mobility scoring with pathway diversity metrics
   - Categorise skills by transition frequency and cross-functional presence
   - Identify "gateway skills" that enable job family transitions

#### **Week 2: Model Development & Integration**
1. **Skills Confidence Module**
   - Implement rarity-weighted defining skills analysis
   - Create skill gap identification with learning pathway suggestions
   - Build confidence calibration using historical validation data

2. **Movement Confidence Module**
   - Develop pathway probability calculations with sample size weighting
   - Integrate mobility scores as confidence modifiers
   - Handle "cold start" scenarios with job function fallback logic

3. **Consensus Framework Prototype**
   - Build weighted averaging system with disagreement detection
   - Create user-adjustable weighting interface concept
   - Develop explanation framework for recommendation transparency

### **Phase 1 Deliverables**
- `04_movement_predictive_analysis.py` - Historical movement analysis with cartesian product output
- `05_skills_intelligence_predictive.py` - Skills-based prediction with cartesian product output
- Enhanced pathway dataset with dual confidence scores for all viable job profile pairs
- Smart filtering implementation to optimize computational performance
- Validation report comparing movement vs skills predictive power

---

## 🔮 **Phase 2: Strategic Enhancement & Market Integration**

### **Advanced Predictive Capabilities**
1. **Market Intelligence Integration**
   - Lightcast labour market projections as pathway multipliers
   - Internal vacancy patterns as demand signals
   - Skills growth trend validation against external market data

2. **Individual Personalisation**
   - Colleague-specific factors (tenure, performance, preferences)
   - Learning velocity and development pathway optimisation
   - Geographic and organisational constraint integration

3. **Strategic Workforce Planning Integration**
   - Future-state organisation design alignment
   - Capability gap analysis and targeted development planning
   - Scenario planning for workforce transformation initiatives

### **Advanced Analytics Techniques**
1. **Graph Neural Networks** for complex organisational relationship modelling
2. **Reinforcement Learning** for optimal career progression policy development
3. **Causal Inference** to understand true drivers of successful transitions
4. **Natural Language Processing** for skills extraction from job descriptions and learning content

### **Operational Integration**
1. **Real-time API** for webapp and HR system integration
2. **Automated redeployment playbooks** for common transition scenarios
3. **A/B testing framework** for continuous model improvement
4. **Stakeholder dashboard** for strategic workforce planning insights

---

## 💡 **Key Design Principles**

### **Transparency Over Accuracy**
- Explainable recommendations with clear confidence indicators
- Component score breakdown for user understanding
- Model disagreement flagging for nuanced decision-making

### **Strategic Alignment Over Historical Replication**
- Future-focused pathway weighting, not just historical pattern replication
- User control over traditional vs innovative pathway exploration
- Skills-based opportunity discovery for workforce transformation

### **Modularity Over Monolithic Design**
- Independent model components that can be enhanced separately
- User-adjustable weighting for different strategic scenarios
- Easy integration of new data sources and analytical techniques

### **Feasibility Grounding**
- Historical validation of recommended pathways
- Confidence calibration using actual transition outcomes
- Sample size and recency considerations in all recommendations

---

## 🎯 **Success Metrics**

### **Technical Performance**
- **Accuracy Improvement**: 15-25% vs baseline asymmetric-only approach
- **Confidence Calibration**: R² > 0.7 correlation with actual success rates
- **Response Time**: Sub-2-second pathway generation
- **Model Stability**: <10% variance across data subsets

### **User Experience**
- **Transparency**: Clear explanation of recommendation logic
- **Actionability**: Confidence levels enable informed decision-making
- **Strategic Value**: Alignment with business priorities and market demands

### **Business Impact**
- **Adoption**: Increased usage by Future Skills and Strategic Workforce Planning teams
- **Outcomes**: Higher success rates for implemented career transitions
- **Strategic Alignment**: Recommendations support organisational transformation goals

---

## 🛠️ **Technical Architecture**

### **Development Environment**
- **Location**: `/notebook` for experimental development
- **Language**: Python with scikit-learn, pandas, numpy
- **Database**: SQLite with workforce intelligence schema
- **Validation**: Cross-validation with holdout testing on recent transitions

### **Modular Structure**
```
skill-similarity-engine/notebook/
├── 04_predictive_pathway_engine.py          # Main orchestration
├── 05_skills_confidence_engine.py           # Skills-based predictions
├── 06_movement_confidence_engine.py         # Historical movement analysis
├── 07_consensus_decision_framework.py       # Weighted combination
├── 08_pathway_validation_analysis.py        # Performance evaluation
└── 09_enhanced_pathway_generator.py         # Final output pipeline
```

### **Output Format**
```python
@dataclass
class EnhancedPathwayRecommendation:
    source_job_id: str
    target_job_id: str
    overall_confidence: float           # Weighted consensus score
    skills_confidence: float            # Skills-based component
    movement_confidence: float          # Historical movement component
    recommendation_strength: str        # HIGH/MEDIUM/LOW
    skills_explanation: Dict           # Defining skills overlap, gaps
    movement_explanation: Dict         # Historical precedent, sample size
    strategic_context: Dict           # Market trends, organisational priorities
```

---

## 📋 **Immediate Next Steps**

1. **Stakeholder Alignment** - Share this context document with Head of Future Skills
2. **Data Pipeline Setup** - Consolidate existing analyses into unified working dataset
3. **Module Development** - Begin with Skills Confidence Engine as foundation
4. **Validation Framework** - Establish performance metrics and testing methodology
5. **User Experience Design** - Plan webapp integration for dual confidence display

This foundation enables NAB to transition from reactive colleague support to proactive, strategic workforce intelligence - using skills as the language to navigate organisational transformation while maintaining the architectural integrity of existing job frameworks. 