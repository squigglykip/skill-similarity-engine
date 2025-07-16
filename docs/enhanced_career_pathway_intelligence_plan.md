# Enhanced Career Pathway Intelligence System
## Multi-Model Consensus Framework for Strategic Workforce Planning

> **Project Vision**: Transform NAB's career pathway recommendations from naive skill-based suggestions to empirically grounded, strategically aligned, and future-focused transitions using a multi-model ensemble approach.

**Document Version**: 1.0  
**Created**: 2025-01-19  
**Purpose**: Technical specification for enhanced career pathway intelligence system  
**Audience**: Data Science team, Future Skills team, System Architects  

---

## 🎯 **EXECUTIVE SUMMARY**

The Enhanced Career Pathway Intelligence System represents a paradigm shift from single-model career recommendations to a sophisticated **multi-model consensus framework**. By combining asymmetric skill similarity with machine learning approaches, we create career pathway recommendations that are simultaneously:

- **Skills-Optimised**: Based on proven asymmetric coverage calculations
- **Historically-Informed**: Leveraging actual movement patterns and success rates
- **ML-Enhanced**: Using predictive models to identify optimal transition opportunities
- **Confidence-Scored**: Providing transparency through model-specific confidence levels
- **Strategically-Aligned**: Weighted toward organisational priorities and market demands

### **Key Innovation: Consensus-Based Confidence Scoring**

Each career pathway recommendation includes **three confidence levels**:
1. **Overall Confidence**: Weighted consensus across all models
2. **Asymmetric Confidence**: Skill-based similarity strength
3. **ML Confidence**: Predictive model certainty

This multi-dimensional confidence scoring enables sophisticated D3.js visualisations where users can hover over pathway nodes to understand **how** recommendations were generated.

---

## 🏗️ **SYSTEM ARCHITECTURE**

### **Two-Phase Architecture Design**

```
Phase 1: PRE-COMPUTATION (Batch Processing)
├── Asymmetric Similarity Matrix Generation
├── Historical Movement Pattern Analysis  
├── ML Model Training & Validation
├── Consensus Score Calculation
└── Enhanced Pathway Dataset Generation

Phase 2: QUERY INTERFACE (Real-time)
├── D3.js Interactive Tree Visualisation
├── Confidence Score Display
├── Model Contribution Breakdown
└── Strategic Context Integration
```

### **Core Components**

#### **1. Asymmetric Similarity Engine** *(Existing - Production Ready)*
- **Purpose**: Calculate skill-based job-to-job similarity using proven asymmetric coverage
- **Status**: ✅ **COMPLETED** - Production-ready with 510,510 job pair comparisons
- **Output**: Pure skill similarity scores (0.0 to 1.0)
- **Performance**: ~3 seconds for 715 jobs, scalable to 35,000+ jobs

#### **2. Historical Movement Analysis** *(In Development)*
- **Purpose**: Extract empirical career transition patterns from 5 years of movement data
- **Data Source**: 92,107 movement events across 157,891 employees
- **Methodology**: Markov chain models, transition probability matrices
- **Output**: Historical transition likelihood scores

#### **3. ML Model Ensemble** *(Feature Selection Phase)*
- **Purpose**: Predictive career pathway recommendations using multiple ML approaches
- **Current Testing**: Logistic Regression, Random Forest, Gradient Boosting, XGBoost, SVM
- **Feature Selection**: Mutual Information, Chi-square tests, feature importance analysis
- **Output**: ML-based pathway predictions with confidence intervals

#### **4. Consensus Decision Engine** *(New Development)*
- **Purpose**: Intelligently combine multiple model outputs into unified recommendations
- **Methodology**: Weighted ensemble with disagreement analysis
- **Output**: Composite career pathway scores with model-specific confidence levels

---

## 🧠 **MULTI-MODEL CONSENSUS FRAMEWORK**

### **Model Portfolio Architecture**

#### **Model 1: Asymmetric Skill Similarity** *(Weight: 40%)*
```python
asymmetric_score = AsymmetricCoverageCalculator.calculate_job_coverage(
    job_from=current_role,
    job_to=target_role
)
asymmetric_confidence = calculate_skill_overlap_confidence(
    shared_skills=shared_skills_count,
    total_skills=current_role_skills_count
)
```

**Strengths**:
- Proven accuracy with 100% skill mapping coverage
- Transparent, interpretable methodology
- Fast computation (sub-second response times)
- No training data requirements

**Limitations**:
- Doesn't consider historical success rates
- May suggest theoretically similar but practically difficult transitions
- No temporal or contextual factors

#### **Model 2: Historical Movement Patterns** *(Weight: 25%)*
```python
historical_score = MovementAnalyzer.calculate_transition_probability(
    from_job=current_role,
    to_job=target_role,
    context_filters=['tenure', 'job_family', 'division']
)
historical_confidence = calculate_sample_size_confidence(
    successful_transitions=historical_count,
    total_population=role_population
)
```

**Strengths**:
- Based on actual organisational behaviour
- Accounts for cultural and structural factors
- Provides realistic feasibility assessment
- Includes contextual success factors

**Limitations**:
- Limited by historical data availability
- May perpetuate existing biases
- Doesn't account for changing business needs
- Sparse data for uncommon transitions

#### **Model 3: ML Predictive Ensemble** *(Weight: 25%)*
```python
ml_predictions = []
ml_confidences = []

for model in [LogisticRegression, RandomForest, GradientBoosting, XGBoost]:
    prediction = model.predict_proba(transition_features)
    confidence = model.predict_confidence(transition_features)
    ml_predictions.append(prediction)
    ml_confidences.append(confidence)

ml_score = weighted_average(ml_predictions)
ml_confidence = ensemble_confidence(ml_confidences)
```

**Current ML Approaches Under Testing**:
- **Logistic Regression**: Baseline interpretable model
- **Random Forest**: Non-linear relationships, feature importance
- **Gradient Boosting**: Superior performance on structured data
- **XGBoost**: Advanced gradient boosting with regularisation
- **SVM (RBF)**: Non-linear decision boundaries

**Feature Selection Methods**:
- **Mutual Information**: Measures predictive relationship strength
- **Chi-square Tests**: Statistical significance of categorical relationships
- **Recursive Feature Elimination**: Optimal feature subset selection
- **L1/L2 Regularisation**: Automated feature selection through penalties

#### **Model 4: Strategic Alignment** *(Weight: 10%)*
```python
strategic_score = StrategicAlignmentCalculator.calculate_alignment(
    target_role=target_role,
    business_priorities=current_strategic_priorities,
    market_demand=lightcast_projections,
    internal_demand=vacancy_analysis
)
strategic_confidence = calculate_strategic_certainty(
    priority_level=role_priority,
    demand_stability=demand_trend_stability
)
```

**Components**:
- **Business Priority Weighting**: Manually tagged strategic roles
- **Market Demand Integration**: Lightcast labour market projections
- **Internal Demand Analysis**: Vacancy patterns and hiring trends
- **Future Skills Alignment**: Emerging capability requirements

### **Consensus Score Calculation**

```python
def calculate_consensus_pathway_score(
    asymmetric_score: float,
    historical_score: float, 
    ml_score: float,
    strategic_score: float,
    weights: Dict[str, float] = {
        'asymmetric': 0.40,
        'historical': 0.25,
        'ml': 0.25,
        'strategic': 0.10
    }
) -> PathwayRecommendation:
    
    # Calculate weighted consensus score
    consensus_score = (
        weights['asymmetric'] * asymmetric_score +
        weights['historical'] * historical_score +
        weights['ml'] * ml_score +
        weights['strategic'] * strategic_score
    )
    
    # Calculate model-specific confidence levels
    asymmetric_confidence = calculate_skill_confidence(asymmetric_score)
    historical_confidence = calculate_sample_confidence(historical_score)
    ml_confidence = calculate_ensemble_confidence(ml_score)
    strategic_confidence = calculate_strategic_confidence(strategic_score)
    
    # Calculate overall confidence using uncertainty propagation
    overall_confidence = calculate_weighted_confidence(
        confidences=[asymmetric_confidence, historical_confidence, 
                    ml_confidence, strategic_confidence],
        weights=list(weights.values())
    )
    
    # Detect model disagreement
    disagreement_score = calculate_model_disagreement(
        [asymmetric_score, historical_score, ml_score, strategic_score]
    )
    
    return PathwayRecommendation(
        consensus_score=consensus_score,
        overall_confidence=overall_confidence,
        asymmetric_confidence=asymmetric_confidence,
        ml_confidence=ml_confidence,
        model_contributions={
            'asymmetric': asymmetric_score * weights['asymmetric'],
            'historical': historical_score * weights['historical'],
            'ml': ml_score * weights['ml'],
            'strategic': strategic_score * weights['strategic']
        },
        disagreement_score=disagreement_score,
        recommendation_strength=classify_recommendation_strength(
            consensus_score, overall_confidence, disagreement_score
        )
    )
```

---

## 🎨 **D3.JS VISUALISATION INTEGRATION**

### **Enhanced Node Data Structure**

```javascript
// Enhanced pathway node with multi-model confidence
const pathwayNode = {
    id: "node_123",
    jobId: "R0045.3",
    jobTitle: "Senior Data Analyst",
    
    // Consensus scoring
    consensusScore: 0.847,
    overallConfidence: 0.78,
    
    // Model-specific scores
    asymmetricScore: 0.92,
    asymmetricConfidence: 0.85,
    historicalScore: 0.65,
    historicalConfidence: 0.71,
    mlScore: 0.89,
    mlConfidence: 0.82,
    strategicScore: 0.73,
    strategicConfidence: 0.69,
    
    // Model contributions
    modelContributions: {
        asymmetric: 0.368,    // 0.92 * 0.40
        historical: 0.163,    // 0.65 * 0.25
        ml: 0.223,           // 0.89 * 0.25
        strategic: 0.073     // 0.73 * 0.10
    },
    
    // Disagreement analysis
    disagreementScore: 0.23,
    recommendationStrength: "HIGH",  // HIGH/MEDIUM/LOW
    
    // Visual properties
    nodeColor: getNodeColor(0.847),
    confidenceRing: getConfidenceRing(0.78),
    
    // Hover tooltip data
    tooltipData: {
        skillsShared: 18,
        skillsTotal: 24,
        historicalTransitions: 12,
        mlAlgorithms: ["Random Forest", "XGBoost", "Gradient Boosting"],
        strategicPriority: "Medium"
    }
};
```

### **Interactive Hover Tooltips**

```javascript
// Enhanced tooltip showing model breakdown
function createEnhancedTooltip(node) {
    return `
        <div class="pathway-tooltip">
            <h3>${node.jobTitle}</h3>
            <div class="consensus-score">
                <strong>Consensus Score: ${(node.consensusScore * 100).toFixed(1)}%</strong>
                <div class="confidence-indicator">
                    Confidence: ${(node.overallConfidence * 100).toFixed(1)}%
                </div>
            </div>
            
            <div class="model-breakdown">
                <h4>How this recommendation was built:</h4>
                
                <div class="model-component">
                    <span class="model-label">Skills Similarity:</span>
                    <span class="model-score">${(node.asymmetricScore * 100).toFixed(1)}%</span>
                    <span class="model-confidence">(${(node.asymmetricConfidence * 100).toFixed(1)}% confident)</span>
                    <div class="contribution-bar" style="width: ${node.modelContributions.asymmetric * 100}%"></div>
                </div>
                
                <div class="model-component">
                    <span class="model-label">Historical Success:</span>
                    <span class="model-score">${(node.historicalScore * 100).toFixed(1)}%</span>
                    <span class="model-confidence">(${(node.historicalConfidence * 100).toFixed(1)}% confident)</span>
                    <div class="contribution-bar" style="width: ${node.modelContributions.historical * 100}%"></div>
                </div>
                
                <div class="model-component">
                    <span class="model-label">ML Prediction:</span>
                    <span class="model-score">${(node.mlScore * 100).toFixed(1)}%</span>
                    <span class="model-confidence">(${(node.mlConfidence * 100).toFixed(1)}% confident)</span>
                    <div class="contribution-bar" style="width: ${node.modelContributions.ml * 100}%"></div>
                </div>
                
                <div class="model-component">
                    <span class="model-label">Strategic Alignment:</span>
                    <span class="model-score">${(node.strategicScore * 100).toFixed(1)}%</span>
                    <span class="model-confidence">(${(node.strategicConfidence * 100).toFixed(1)}% confident)</span>
                    <div class="contribution-bar" style="width: ${node.modelContributions.strategic * 100}%"></div>
                </div>
            </div>
            
            <div class="supporting-evidence">
                <div class="evidence-item">
                    <strong>Skills Match:</strong> ${node.tooltipData.skillsShared}/${node.tooltipData.skillsTotal} skills
                </div>
                <div class="evidence-item">
                    <strong>Historical Precedent:</strong> ${node.tooltipData.historicalTransitions} successful transitions
                </div>
                <div class="evidence-item">
                    <strong>ML Models:</strong> ${node.tooltipData.mlAlgorithms.join(", ")}
                </div>
                <div class="evidence-item">
                    <strong>Strategic Priority:</strong> ${node.tooltipData.strategicPriority}
                </div>
            </div>
            
            ${node.disagreementScore > 0.3 ? 
                `<div class="disagreement-warning">
                    ⚠️ Models show some disagreement (${(node.disagreementScore * 100).toFixed(1)}%)
                </div>` : ''
            }
        </div>
    `;
}
```

### **Visual Confidence Encoding**

```javascript
// Multi-dimensional visual encoding
function getNodeVisualProperties(node) {
    return {
        // Primary colour based on consensus score
        fillColor: d3.scaleSequential(d3.interpolateViridis)
            .domain([0, 1])(node.consensusScore),
        
        // Ring thickness based on overall confidence
        strokeWidth: d3.scaleLinear()
            .domain([0, 1])
            .range([1, 4])(node.overallConfidence),
        
        // Ring colour based on recommendation strength
        strokeColor: {
            'HIGH': '#22c55e',    // Green
            'MEDIUM': '#f59e0b',  // Amber
            'LOW': '#ef4444'      // Red
        }[node.recommendationStrength],
        
        // Node size based on strategic importance
        radius: d3.scaleLinear()
            .domain([0, 1])
            .range([8, 16])(node.strategicScore),
        
        // Opacity based on model disagreement
        opacity: d3.scaleLinear()
            .domain([0, 1])
            .range([1, 0.6])(node.disagreementScore)
    };
}
```

---

## 🔬 **IMPLEMENTATION ROADMAP**

### **Phase 1: Enhanced Asymmetric Foundation** *(Weeks 1-2)*

**Objective**: Extend current asymmetric similarity engine with confidence scoring

**Tasks**:
- [ ] **Confidence Calculation Enhancement**
  - Implement skill overlap confidence based on shared skills ratio
  - Add skill rarity weighting for confidence adjustment
  - Create confidence calibration using historical validation data

- [ ] **Intra-Weighting for Specialised Skills**
  - Implement configurable skill importance weights within asymmetric calculation
  - Add skill category-based weighting (technical vs soft skills)
  - Create skill specialisation detection and weighting

- [ ] **Enhanced Output Format**
  - Extend pathway dataset to include confidence scores
  - Add model contribution tracking
  - Create detailed similarity breakdown for visualisation

**Deliverables**:
- Enhanced `AsymmetricCoverageCalculator` with confidence scoring
- Updated pathway dataset with asymmetric confidence levels
- Validation report comparing confidence scores with historical success rates

### **Phase 2: Historical Movement Integration** *(Weeks 3-4)*

**Objective**: Integrate historical movement analysis with similarity calculations

**Tasks**:
- [ ] **Movement Pattern Analysis**
  - Implement Markov chain models for career progression
  - Calculate transition probability matrices by job family/level
  - Identify "launchpad" vs "dead-end" role classifications

- [ ] **Historical Confidence Scoring**
  - Implement sample size-based confidence calculation
  - Add temporal stability analysis for transition patterns
  - Create success rate validation using outcome tracking

- [ ] **Consensus Integration**
  - Develop weighted averaging framework for asymmetric + historical scores
  - Implement disagreement detection between models
  - Create fallback strategies for sparse historical data

**Deliverables**:
- `HistoricalMovementAnalyzer` with confidence scoring
- Combined asymmetric + historical pathway recommendations
- Movement pattern validation report

### **Phase 3: ML Model Development** *(Weeks 5-8)*

**Objective**: Develop and validate ML ensemble for pathway prediction

**Tasks**:
- [ ] **Feature Engineering & Selection**
  - Complete mutual information and chi-square analysis
  - Implement recursive feature elimination
  - Create feature importance ranking across multiple algorithms

- [ ] **Model Training & Validation**
  - Train ensemble of 5+ ML algorithms (Logistic Regression, Random Forest, Gradient Boosting, XGBoost, SVM)
  - Implement cross-validation with confidence interval calculation
  - Create model-specific confidence scoring

- [ ] **Ensemble Integration**
  - Develop weighted voting mechanism with confidence weighting
  - Implement uncertainty quantification for ensemble predictions
  - Create model disagreement analysis

**Deliverables**:
- Trained ML ensemble with performance validation
- ML confidence scoring methodology
- Feature importance analysis report

### **Phase 4: Consensus Framework** *(Weeks 9-10)*

**Objective**: Integrate all models into unified consensus framework

**Tasks**:
- [ ] **Consensus Algorithm Development**
  - Implement weighted averaging with dynamic weight adjustment
  - Create confidence propagation methodology
  - Develop disagreement scoring and interpretation

- [ ] **Strategic Alignment Integration**
  - Implement business priority weighting system
  - Add market demand integration (Lightcast projections)
  - Create strategic confidence scoring

- [ ] **Performance Validation**
  - Validate consensus recommendations against historical outcomes
  - Create A/B testing framework for model comparison
  - Implement continuous learning and model updating

**Deliverables**:
- Complete consensus framework with all model integration
- Validation report comparing consensus vs individual models
- Strategic alignment scoring methodology

### **Phase 5: D3.js Visualisation Enhancement** *(Weeks 11-12)*

**Objective**: Enhance webapp with multi-model confidence visualisation

**Tasks**:
- [ ] **Enhanced Data Pipeline**
  - Update career pathway pre-computation to include all confidence scores
  - Modify SQLite schema to store model-specific data
  - Create API endpoints for enhanced pathway data

- [ ] **D3.js Visualisation Updates**
  - Implement multi-dimensional visual encoding (colour, size, opacity)
  - Create enhanced hover tooltips with model breakdown
  - Add confidence ring visualisation around nodes

- [ ] **Interactive Features**
  - Implement model weight adjustment sliders
  - Add confidence threshold filtering
  - Create model comparison view

**Deliverables**:
- Enhanced D3.js tree visualisation with confidence display
- Interactive model exploration interface
- User testing validation report

---

## 🎯 **SUCCESS CRITERIA**

### **Technical Performance**
- **Accuracy Improvement**: 15-25% improvement in pathway recommendation accuracy vs baseline asymmetric-only approach
- **Confidence Calibration**: Confidence scores correlate with actual success rates (R² > 0.7)
- **Response Time**: Sub-2-second query performance for enhanced pathway recommendations
- **Model Stability**: Consistent recommendations across different data subsets (variance < 10%)

### **User Experience**
- **Transparency**: Users can understand how recommendations were generated through tooltip explanations
- **Actionability**: Clear confidence levels enable users to make informed decisions
- **Visual Clarity**: Multi-dimensional encoding provides intuitive understanding of recommendation strength
- **Interactive Value**: Model weight adjustment provides personalised recommendations

### **Business Impact**
- **Strategic Alignment**: Recommendations align with business priorities and market demands
- **Feasibility**: Higher success rates for implemented career transitions
- **Adoption**: Increased usage of career pathway recommendations by HR teams
- **Confidence**: Reduced hesitation in making career transition decisions

---

## 🔧 **TECHNICAL SPECIFICATIONS**

### **Data Requirements**
- **Asymmetric Similarity**: 510,510 job pair similarities (existing)
- **Historical Movements**: 92,107 movement events across 5 years
- **Skills Mapping**: 40,170 job-skill relationships
- **Strategic Priorities**: Business priority tags for 715 job profiles
- **Market Data**: Lightcast labour market projections (future integration)

### **Performance Targets**
- **Pre-computation**: Complete enhanced pathway generation in <4 hours
- **Query Performance**: Career pathway tree generation in <100ms
- **Memory Usage**: Efficient processing on 32GB RAM systems
- **Scalability**: Support for 35,000+ job profiles

### **Output Format**
```python
@dataclass
class EnhancedPathwayRecommendation:
    source_job_id: str
    target_job_id: str
    
    # Consensus scoring
    consensus_score: float
    overall_confidence: float
    
    # Model-specific scores
    asymmetric_score: float
    asymmetric_confidence: float
    historical_score: float
    historical_confidence: float
    ml_score: float
    ml_confidence: float
    strategic_score: float
    strategic_confidence: float
    
    # Model contributions
    model_contributions: Dict[str, float]
    
    # Analysis metadata
    disagreement_score: float
    recommendation_strength: str  # HIGH/MEDIUM/LOW
    
    # Supporting evidence
    skills_shared: int
    skills_total: int
    historical_transitions: int
    ml_algorithms: List[str]
    strategic_priority: str
```

---

## 📊 **MONITORING & CONTINUOUS IMPROVEMENT**

### **Model Performance Monitoring**
- **Accuracy Tracking**: Regular validation against actual career outcomes
- **Confidence Calibration**: Ongoing assessment of confidence score accuracy
- **Model Drift Detection**: Monitoring for changes in model performance over time
- **Feature Importance Evolution**: Tracking changes in feature significance

### **User Feedback Integration**
- **Recommendation Ratings**: User feedback on pathway suggestion quality
- **Implementation Tracking**: Success rates of recommended career transitions
- **Confidence Validation**: User assessment of confidence score accuracy
- **Feature Requests**: Ongoing enhancement based on user needs

### **Continuous Learning Framework**
- **Model Retraining**: Quarterly updates with new movement data
- **Feature Engineering**: Ongoing improvement of predictive features
- **Algorithm Updates**: Integration of new ML approaches and techniques
- **Strategic Alignment**: Regular updates to business priority weightings

---

## 🚀 **FUTURE ENHANCEMENTS**

### **Advanced ML Techniques**
- **Deep Learning**: Neural networks for complex pattern recognition
- **Graph Neural Networks**: Explicit modelling of organisational network effects
- **Reinforcement Learning**: Optimal career path policy learning
- **Natural Language Processing**: Skills extraction from job descriptions

### **External Data Integration**
- **Labour Market Intelligence**: Real-time job market demand signals
- **Industry Trends**: Sector-specific career pathway analysis
- **Skills Evolution**: Tracking of emerging and declining skills
- **Economic Indicators**: Market conditions impact on career transitions

### **Personalisation Features**
- **Individual Profiles**: Personalised recommendations based on employee data
- **Learning Preferences**: Customised development pathway suggestions
- **Geographic Constraints**: Location-based career opportunity filtering
- **Timeline Optimisation**: Customised career progression timelines

---

This enhanced career pathway intelligence system represents a significant advancement in workforce analytics, providing the sophisticated, multi-model approach needed for strategic workforce planning in the modern economy. The combination of proven asymmetric similarity with advanced ML techniques and transparent confidence scoring creates a powerful tool for both individual career development and organisational capability planning. 