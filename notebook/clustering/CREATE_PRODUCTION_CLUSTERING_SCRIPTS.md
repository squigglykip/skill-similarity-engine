# LLM Prompt: Create Production Clustering Scripts

## 🎯 **Task Overview**
Create two production-ready clustering scripts that implement the optimized parameters discovered through comprehensive data exploration and parameter optimization. These scripts will generate actual cluster assignments for strategic use in job archetype identification and skills bundle creation.

---

## 📋 **Required Files to Create**

### **1. `02b_job_profile_clustering_production.py`**
**Purpose**: Generate production job profile clusters using optimal DBSCAN parameters  
**Expected Output**: 331 job clusters with 0.962 silhouette score

### **2. `03b_skills_clustering_production.py`**  
**Purpose**: Generate production skills clusters using optimal DBSCAN parameters  
**Expected Output**: 193 skill bundles with 0.824 silhouette score + specialized skills category

---

## 🔍 **Context: Optimization Results & Strategic Framework**

### **Job Profile Clustering Optimization Results**
From `02a_job_profile_parameter_optimization.py` (25 July 2025):
```
🥇 OPTIMAL DBSCAN PARAMETERS:
   → eps: 0.1
   → min_samples: 2.0
   → Expected clusters: 331.0
   → Expected noise ratio: 5.2%
   → Silhouette score: 0.962
   → Composite score: 0.921

🥇 OPTIMAL K-MEANS PARAMETERS:
   → Elbow method suggests: 10.0 clusters
   → Best silhouette score at: 23.0 clusters (0.139)
   → Recommended: 10.0 clusters
```

**Enhanced Similarity Configuration**:
- **Defining Skills Strategy**: 20% percentile rarest skills per job profile
- **Gentle Multiplier**: 1.05x boost for shared defining skills
- **Average defining skills per job**: 8.4 skills (18.9% of 44.2 average skills)

### **Skills Clustering Optimization Results**
From `03a_skills_parameter_optimization.py` (25 July 2025):
```
🥇 OPTIMAL DBSCAN PARAMETERS:
   → Similarity method: cosine
   → eps: 0.1
   → min_samples: 3
   → Expected clusters: 193
   → Expected noise ratio: 38.1%
   → Silhouette score: 0.824
   → Taxonomy alignment: 0.563

🥇 OPTIMAL HIERARCHICAL PARAMETERS:
   → Similarity method: combined
   → n_clusters: 8
   → linkage: average
   → Silhouette score: 0.064
   → Taxonomy alignment: 0.479

🥇 OPTIMAL K-MEANS PARAMETERS:
   → Similarity method: cosine
   → n_clusters: 8
   → Silhouette score: 0.176
   → Taxonomy alignment: 0.411
```

### **Strategic Context from CLUSTERING_STRATEGY_ROADMAP.md**

**Two-Layer Architecture** (Section: Integration with Predictive Pathway Engine):
- **Job Profile Clustering**: "Individual mobility analysis and pathway assessment" 
- **Skills Clustering**: "Learning ecosystem enhancement and capability building"

**Dual-Stream Approach** (Section: Strategic Positioning):
- **Production Focus**: Immediate clustering results for operational decisions
- **Complementary Intelligence**: Ecosystem understanding for strategic planning

**Success Metrics** (Section: Success Metrics & Validation):
- **Technical Quality**: Optimal parameters with high silhouette scores and low noise
- **Business Relevance**: Clusters align with stakeholder intuition while revealing new insights
- **Strategic Value**: Clustering insights inform strategic initiatives and decisions

---

## 📊 **Data Foundation & Database Context**

### **Database Configuration**
```python
DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"
```

### **Core Data Characteristics** (from `01_data_exploration_foundation.py`)
- **Job profiles**: 1,743 total
- **Total job-skill relationships**: 76,994  
- **Unique skills**: 2,442 actively used
- **Skills per job (avg)**: 44.2 ± 10.2 std dev
- **Co-occurrence density**: 6.5% (ideal for clustering)

### **Enhanced Similarity Strategy** (Empirically Validated)
```python
# Hardcoded hyperparameters based on empirical tuning results
# 20% percentile, 1.05x multiplier = optimal balance of smoothness + practical impact
DEFINING_SKILLS_PERCENTILE = 20   # Top 20% rarest skills per job profile  
GENTLE_MULTIPLIER = 1.05          # 5% boost per shared defining skill
```

---

## 🛠️ **Technical Specifications**

### **File 1: `02b_job_profile_clustering_production.py`**

**Core Functionality**:
1. **Database Connection**: Connect to workforce_intelligence.sqlite
2. **Data Loading**: Load job profiles and skills with full context
3. **Defining Skills Creation**: Implement 20% percentile + 1.05x multiplier strategy
4. **Enhanced Similarity Matrix**: Job-to-job similarity with defining skills boost
5. **DBSCAN Clustering**: Apply optimal parameters (eps=0.1, min_samples=2)
6. **Cluster Analysis**: Characterize 331 job clusters by function, skills, archetypes
7. **Output Generation**: 
   - Job cluster assignments CSV
   - Cluster characterization report
   - Job archetype summaries
   - Visualization plots

**Key Technical Requirements**:
- Use hardcoded optimal parameters (no parameter testing)
- Implement enhanced similarity from `skill_intelligence_engine.py` approach
- Generate 331 micro-clusters with ~5-6 jobs each
- Handle 5.2% noise ratio gracefully
- Include job metadata (function, level, category) in cluster analysis
- Create cluster stability and quality metrics

**Expected Output Structure**:
```csv
JobProfileID,JobProfile,JobFunction,Cluster_ID,Cluster_Size,Silhouette_Score
1001,Senior Data Analyst,Data & Analytics,45,6,0.923
1002,Marketing Manager,Marketing,12,5,0.941
...
```

### **File 2: `03b_skills_clustering_production.py`**

**Core Functionality**:
1. **Database Connection**: Connect to workforce_intelligence.sqlite  
2. **Skills Co-occurrence Matrix**: Build skill-to-skill relationships
3. **Cosine Similarity Calculation**: Use optimal similarity method
4. **DBSCAN Clustering**: Apply optimal parameters (cosine, eps=0.1, min_samples=3)
5. **Skills Bundle Analysis**: Characterize 193 skill clusters + 38.1% specialized skills
6. **Taxonomy Validation**: Compare with existing skill categories
7. **Output Generation**:
   - Skills cluster assignments CSV
   - Skills bundle characterization
   - Specialized/emerging skills list
   - Taxonomy alignment analysis

**Key Technical Requirements**:
- Use cosine similarity matrix (not Jaccard for skills clustering)
- Generate 193 skill bundles with ~11.4 skills each
- Handle 38.1% noise as "Specialized/Emerging" skills category
- Include skill metadata (category, type) in analysis
- Validate against existing taxonomy (56.3% alignment baseline)
- Create skills bundle learning pathway recommendations

**Expected Output Structure**:
```csv
Skill_ID,Skill_Name,Category,Cluster_ID,Cluster_Size,Bundle_Theme,Is_Specialized
501,Python Programming,Information Technology,23,12,Data Engineering,False
502,Quantum Computing,Information Technology,-1,1,Specialized/Emerging,True
...
```

---

## 📈 **Output Requirements & Success Criteria**

### **Job Profile Clustering Outputs**
1. **Primary Output**: `job_clusters_production_YYYYMMDD_HHMMSS.csv`
2. **Cluster Analysis**: `job_cluster_analysis_YYYYMMDD_HHMMSS.txt`
3. **Visualizations**: Job cluster plots and archetype analysis
4. **Success Criteria**: 
   - 331 ± 10 clusters achieved
   - Silhouette score ≥ 0.95
   - Noise ratio ≤ 6%
   - Clear job family patterns evident

### **Skills Clustering Outputs**  
1. **Primary Output**: `skills_clusters_production_YYYYMMDD_HHMMSS.csv`
2. **Skills Bundles**: `skills_bundles_analysis_YYYYMMDD_HHMMSS.txt`
3. **Specialized Skills**: `specialized_emerging_skills_YYYYMMDD_HHMMSS.csv`
4. **Success Criteria**:
   - 193 ± 10 clusters achieved
   - Silhouette score ≥ 0.80
   - Noise ratio 35-40% (expected for skills)
   - Meaningful skill bundle themes identified

### **Integration Readiness**
Both scripts should generate outputs ready for:
- Strategic workforce planning presentations
- L&D curriculum design (skills bundles)
- Career pathway enhancement (job archetypes)
- Organisational design insights (natural job families)

---

## 🎯 **Strategic Alignment & Validation**

### **Business Context** (from CLUSTERING_STRATEGY_ROADMAP.md Section: Strategic Positioning)
"**Purpose**: 'How do jobs and skills naturally group in our skills ecosystem?'  
**Strategic Value**: Conceptual understanding and future organisational design"

### **Integration Points** (Section: Integration with Predictive Pathway Engine)
- **Job Clusters**: "Natural job families and archetype discovery"
- **Skills Bundles**: "Skills bundle identification transcending traditional boundaries"  
- **Combined Intelligence**: "Pathway feasibility + cluster evolution + strategic workforce planning"

### **Success Validation** (Section: Success Metrics & Validation)
- **Technical Quality**: Optimal clustering parameters with high silhouette scores
- **Business Relevance**: Job clusters align with stakeholder intuition while revealing new insights
- **Skills Intelligence**: Skills bundles identify meaningful L&D pathways

---

## 💡 **Implementation Guidelines**

### **Code Structure Best Practices**
1. **Configuration Classes**: Hardcode optimal parameters at top of file
2. **Modular Functions**: Separate data loading, similarity calculation, clustering, analysis
3. **Error Handling**: Robust database connection and clustering validation
4. **Output Management**: Timestamped files with comprehensive metadata
5. **Visualization**: Professional plots suitable for stakeholder presentations

### **Performance Considerations**
- **Memory Management**: Handle 1,743 x 1,743 job similarity matrix efficiently
- **Computation Optimization**: Use vectorized operations for similarity calculations  
- **Progress Tracking**: Include progress indicators for long-running operations
- **Scalability**: Design for potential growth in job profiles and skills

### **Documentation Requirements**
- **Comprehensive docstrings**: Explain clustering methodology and parameter rationale
- **Strategic context**: Reference optimization results and business value
- **Usage instructions**: Clear execution steps and output interpretation
- **Integration notes**: How outputs connect to broader strategic framework

---

## 🚀 **Expected Deliverables**

### **Immediate Outputs**
1. **`02b_job_profile_clustering_production.py`** - Production job clustering
2. **`03b_skills_clustering_production.py`** - Production skills clustering  
3. **Execution validation** - Both scripts run successfully on production data
4. **Output files** - CSV and analysis files ready for strategic use

### **Strategic Value**
- **331 job archetypes** for precise career pathway targeting
- **193 skills bundles** for evidence-based L&D design
- **Ecosystem intelligence** for organisational design insights
- **Integration readiness** for pathway engine enhancement

### **Next Phase Enablement**
These production scripts will enable **Phase 2: Strategic Integration** from the roadmap:
- Organisational design intelligence
- Learning ecosystem enhancement  
- Predictive engine enhancement
- Skills-based operational evolution

---

## 🎉 **Success Definition**

**Primary Success**: Both scripts execute successfully and generate cluster assignments matching optimization predictions (331 job clusters, 193 skill bundles) with target silhouette scores (≥0.95 jobs, ≥0.80 skills).

**Strategic Success**: Outputs provide actionable intelligence for workforce planning, L&D design, and organisational evolution, advancing the vision of skills-based operational transformation.

**Integration Success**: Generated clusters serve as foundation for enhanced pathway predictions and strategic capability planning, bridging current job-centric operations with future skills-centric organisation design. 