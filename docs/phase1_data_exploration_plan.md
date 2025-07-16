# Phase 1: Data Exploration & Feature Analysis Plan
## Career Pathway Enhancement with Historical Movement Data

**Project**: NAB Future Skills - Career Pathway Enhancement  
**Phase**: 1 - Foundation & Discovery  
**Timeline**: 2 weeks  
**Data Sources**: Synthetic movement data + SQLite workforce intelligence database

---

## 🎯 Objectives

Transform naive skill-based career pathing into empirically grounded, strategically aligned recommendations by:

1. **Understanding movement patterns** in our synthetic but realistic workforce data
2. **Evaluating feature importance** to determine optimal job grouping dimensions  
3. **Categorising roles and skills** by their mobility characteristics
4. **Building enhanced pathway logic** combining skill similarity with historical probability

---

## 📊 Data Sources

### Primary Sources
- **Movement Data**: `realistic_movement_fact_table.csv` (5,543 movement records, 2022-2024)
- **SQLite Database**: `workforce_intelligence.sqlite` (1.4M records across 11 tables)

### Key Tables from SQLite
- `career_pathways` (8,580 records) - Pre-computed skill-based pathways
- `job_similarities` (510,510 records) - Job-to-job similarity scores  
- `jobs` (715 records) - Job architecture with hierarchical groupings
- `job_skills` (40,170 records) - Job-skill mappings
- `skills` (38,430 records) - Skills taxonomy
- `positions` (35,000 records) - Current workforce context

### Movement Data Structure
From realistic synthetic data:
- **Temporal**: `movement_month`, `movement_year` (2022-2024)
- **Movement Flow**: `from_position` → `to_position` (JobProfileID format)
- **Movement Characteristics**: `movement_type`, `cross_function_move`, `customer_facing_transition`
- **Volume Metrics**: `movement_count`, `unique_employees`, `total_movements_month`
- **Context**: `function_pair`, `skills_transition_pattern`, `avg_tenure_months`

---

## 📝 Exploration Notebooks

### Notebook 1: `01_movement_data_discovery.ipynb`
**Purpose**: Initial exploration of movement patterns and data quality

**Key Questions**:
- What are the volume patterns of movements over time?
- Which job functions see the most mobility (in/out flows)?
- How do cross-function vs same-function moves compare?
- What's the distribution of tenure before movement?

**Analyses**:
- Movement volume trends by month/year
- Source vs sink analysis (roles people leave vs join)  
- Cross-function movement patterns
- Tenure distribution analysis
- Data quality assessment (completeness, consistency)

**Outputs**:
- Movement volume summary statistics
- Top 20 movement corridors (from_job → to_job)
- Function-level mobility heatmap
- Tenure vs movement likelihood analysis

---

### Notebook 2: `02_feature_importance_analysis.ipynb`
**Purpose**: Statistical evaluation of job grouping dimensions

**Key Questions**:
- Which job hierarchy level (Function, SubFunction, JobFamily) best explains movement patterns?
- How much does each feature reduce uncertainty in predicting transitions?
- Are movement patterns significantly different across business units, divisions, or management levels?

**Statistical Methods**:
- **Mutual Information** analysis between features and movement targets
- **Chi-square tests** for categorical relationships with movement patterns
- **Entropy reduction** calculations for each potential grouping dimension
- **Feature importance** from basic predictive models (Logistic Regression, XGBoost)

**Features to Evaluate**:
```python
grouping_features = [
    'JobFunction',           # 22 unique values
    'JobSubFunction',        # 110 unique values  
    'JobFunctionID',         # Job function codes
    'ManagementLevel',       # 8 levels (Group 1-7, NA)
    'JobCategory',           # 4 categories (Enabling, Executive, Revenue, Support)
    'Division',              # 6 divisions
    'Business_Unit',         # 10 business units
    'Customer_Facing',       # Customer-facing vs internal roles
    'is_Banker'              # Banker vs non-banker roles
]
```

**Outputs**:
- Mutual information scores ranked by explanatory power
- Chi-square test results with p-values
- Recommended primary grouping dimension for Phase 1
- Feature importance visualization

---

### Notebook 3: `03_role_and_skill_typology.ipynb`
**Purpose**: Categorise roles and skills by mobility characteristics

**Key Questions (Roles)**:
- Which roles are 'launchpads' (high outbound movement diversity)?
- Which roles are 'silos' (low movement in/out)?  
- Which roles are 'stable endpoints' (common destinations, low exit)?
- How do these patterns vary by job function or level?

**Key Questions (Skills)**:
- Which skills appear disproportionately in cross-function movements?
- Which skills are 'bridges' enabling job family transitions?
- Which skills are 'dead ends' (rarely associated with mobility)?
- Which skills are 'ubiquitous' (appear everywhere, potentially low predictive value)?

**Methodologies**:
- **Network centrality analysis** for role connectivity
- **Outbound/inbound movement ratios** for role classification
- **Skill co-occurrence analysis** in successful transitions
- **Cross-function skill frequency** analysis

**Role Typology Framework**:
```python
role_types = {
    'launchpad': 'High outbound movement diversity (>75th percentile)',
    'silo': 'Low total movement volume (<25th percentile)',  
    'stable_endpoint': 'High inbound, low outbound (destination roles)',
    'transitional': 'Balanced in/out flows (career stepping stones)',
    'specialized': 'Function-specific movement patterns'
}
```

**Skill Typology Framework**:
```python
skill_types = {
    'bridge': 'Over-represented in cross-function moves',
    'gateway': 'Enable access to new job families',  
    'anchor': 'Function-specific, rarely transferable',
    'ubiquitous': 'Present across many roles, low discriminative power',
    'emerging': 'Associated with progression movements'
}
```

**Outputs**:
- Role typology classification for all 715 job profiles
- Skill bridge analysis with statistical significance testing
- Visualizations of movement networks and skill transition patterns

---

### Notebook 4: `04_pathway_enrichment_prototype.ipynb`
**Purpose**: Build enhanced career pathway recommendations

**Key Questions**:
- How do we weight skill similarity vs historical movement probability?
- Can we create a composite "Career Feasibility Score"?
- How does the enhanced model compare to naive skill-only recommendations?
- What does a "before and after" pathway recommendation look like?

**Methodology**:
- Merge movement data with existing `career_pathways` table
- Calculate historical transition probabilities by job grouping
- Develop composite scoring algorithm
- Validate against known successful transitions

**Composite Scoring Framework**:
```python
career_consensus_score = (
    α * skill_similarity_score +           # From existing career_pathways
    β * historical_transition_probability + # From movement analysis  
    γ * role_type_modifier +               # Launchpad/silo adjustment
    δ * strategic_alignment_score          # Future: demand growth proxy
)
```

**Outputs**:
- Enhanced pathway recommendation dataset
- Comparison analysis: naive vs enriched suggestions
- Example colleague journey with enriched recommendations
- Performance metrics and validation results

---

## 🔄 Workflow Integration

### Data Pipeline
1. **Load realistic movement data** from CSV
2. **Connect to SQLite database** for job architecture and skills
3. **Merge datasets** on JobProfileID
4. **Apply statistical analysis** methods
5. **Generate enhanced pathways** with composite scoring

### Output Strategy
- **Analytical insights** documented in each notebook
- **Reusable functions** extracted to shared utilities
- **Enriched dataset** ready for integration with main pipeline
- **Business-friendly summary** for stakeholder communication

---

## 📈 Success Criteria

### Technical Outcomes
- [ ] Statistical validation of optimal job grouping dimension
- [ ] Role and skill typology with confidence levels
- [ ] Enhanced pathway algorithm with measurable improvement over baseline
- [ ] Reproducible analysis pipeline for future data updates

### Business Value
- [ ] Clear evidence for choosing job function vs sub-function vs family groupings
- [ ] Actionable insights on role mobility patterns
- [ ] Enhanced colleague recommendations with historical grounding
- [ ] Foundation for predictive workforce planning capabilities

---

## 🚀 Next Steps (Phase 2)

After Phase 1 completion:
- Integration with Lightcast demand forecasting data
- Predictive modelling for individual transition likelihood  
- Strategic alignment scoring for future-fit pathways
- Automated redeployment playbook generation
- Real-time pathway recommendation API

---

## 📂 Notebook File Structure

```
skill-similarity-engine/notebooks/
├── 01_movement_data_discovery.ipynb
├── 02_feature_importance_analysis.ipynb  
├── 03_role_and_skill_typology.ipynb
├── 04_pathway_enrichment_prototype.ipynb
├── shared_utils/
│   ├── data_loaders.py
│   ├── statistical_analysis.py
│   ├── visualization_helpers.py
│   └── pathway_scoring.py
└── outputs/
    ├── movement_summary_stats.csv
    ├── feature_importance_results.json
    ├── role_typology_classifications.csv
    ├── skill_bridge_analysis.csv
    └── enhanced_pathways_sample.csv
```

This exploration plan provides a systematic approach to understanding your movement data and building the enhanced pathway logic. Each notebook builds on the previous one, culminating in a working prototype that combines skill similarity with historical movement patterns. 