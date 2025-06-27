# Career Pathway Diversity Strategy
## Addressing Similarity Bias in Precomputed Career Recommendations

**Document Version**: 1.0  
**Created**: 2025-01-19  
**Last Updated**: 2025-01-19  
**Status**: Design Phase  

---

## Executive Summary

The NAB Skills Intelligence Platform's career pathway recommendation system faces a critical **similarity bias problem** where precomputed pathways cluster within job functions, potentially missing valuable cross-functional opportunities. This document outlines the problem, analyzes solution patterns, and recommends a hybrid approach that maintains performance while ensuring pathway diversity.

---

## Problem Statement

### Current Architecture Challenge

Our precomputation strategy in `precompute.py` generates the top 12 most similar career pathways per job using pure similarity scoring. This creates an **echo chamber effect**:

**Example - Data Scientist Pathways:**
```
Top 12 Recommendations:
1. Senior Data Scientist (95% similarity) - Same function ✓
2. Principal Data Scientist (92% similarity) - Same function ✓
3. Lead Data Scientist (89% similarity) - Same function ✓
4. Data Science Manager (87% similarity) - Same function ✓
...
12. Chief Data Officer (78% similarity) - Same function ✓

Missing Cross-Functional Opportunities:
- Product Manager (73% similarity) - Different function ❌
- Strategy Consultant (71% similarity) - Different function ❌
- Business Intelligence Lead (69% similarity) - Different function ❌
```

### Business Impact

**For Employees:**
- Limited career horizon visibility
- Missed cross-functional opportunities
- Reinforced functional silos

**For NAB:**
- Reduced workforce agility
- Suboptimal talent mobility
- Missed innovation through cross-pollination

### Technical Constraints

**Performance Requirements:**
- Career pathway queries must return in <100ms
- Career Transition Analysis Generator involves 3+ pathway queries per document
- Expected load: 100+ concurrent users during peak times

**Precomputation Benefits:**
- 510,510 job similarities precomputed (instant lookup vs. real-time calculation)
- Consistent ranking across user sessions
- Enables complex pathway analytics and reporting

---

## Solution Architecture Analysis

### Pattern 1: Stratified Sampling Approach

**Concept**: Implement quota-based selection during precomputation.

```sql
-- Precompute diverse pathways per job
INSERT INTO career_pathways (source_job_id, target_job_id, similarity_score, pathway_category, rank_within_category)
SELECT 
    source_job_id,
    target_job_id,
    similarity_score,
    CASE 
        WHEN source_function = target_function THEN 'same_function'
        WHEN source_family = target_family THEN 'same_family'
        ELSE 'cross_functional'
    END as pathway_category,
    ROW_NUMBER() OVER (PARTITION BY source_job_id, pathway_category ORDER BY similarity_score DESC) as rank_within_category
FROM job_similarities js
JOIN jobs j1 ON js.job_from = j1.JobProfileID
JOIN jobs j2 ON js.job_to = j2.JobProfileID
WHERE rank_within_category <= 4;  -- Top 4 per category
```

**Pros:**
- Guaranteed diversity across precomputed data
- Simple query logic: `SELECT * WHERE pathway_category = ? AND rank_within_category <= 4`
- No real-time computation overhead

**Cons:**
- Inflexible diversity ratios (fixed 4:4:4 split)
- Larger precomputed dataset (12 → 36 pathways per job)
- Complex precomputation logic

### Pattern 2: Multi-Dimensional Ranking

**Concept**: Enhance similarity scores with diversity bonuses during precomputation.

```python
def calculate_diversified_score(similarity_score, source_job, target_job):
    base_score = similarity_score
    
    # Apply diversity bonuses
    if source_job.function != target_job.function:
        diversity_bonus = 0.1  # 10% bonus for cross-functional moves
    elif source_job.family != target_job.family:
        diversity_bonus = 0.05  # 5% bonus for cross-family moves
    else:
        diversity_bonus = 0.0
    
    return min(1.0, base_score + diversity_bonus)
```

**Pros:**
- Maintains single ranking list (simpler queries)
- Tunable diversity weighting
- Backward compatible with existing schema

**Cons:**
- Artificial score inflation may confuse users
- Difficulty explaining "adjusted" similarity scores
- Still limited to top N constraint

### Pattern 3: Hybrid Query Strategy (RECOMMENDED)

**Concept**: Expand precomputation breadth, apply diversity at query time.

**Precomputation Changes:**
```python
# In precompute.py - expand from top 12 to top 24
TOP_N_PATHWAYS = 24  # Broader net for query-time diversity
MIN_SIMILARITY_THRESHOLD = 0.01  # Lower threshold for more options

# Add job function metadata to career_pathways table
pathway_record = {
    'source_job_id': source_job_id,
    'target_job_id': target_job_id,
    'similarity_rank': rank,
    'similarity_score': similarity_score,
    'source_job_function': source_job.function,
    'target_job_function': target_job.function,
    'career_move_type': move_type,
    'is_cross_functional': source_job.function != target_job.function
}
```

**Query-Time Diversity Logic:**
```python
def get_diverse_pathways(source_job_id, diversity_config):
    """Get diversified career pathways from precomputed data."""
    
    # Query expanded precomputed data (24 pathways)
    all_pathways = query_career_pathways(source_job_id, limit=24)
    
    # Apply diversity filters
    same_function = [p for p in all_pathways if not p.is_cross_functional][:diversity_config.same_function_count]
    cross_function = [p for p in all_pathways if p.is_cross_functional][:diversity_config.cross_function_count]
    
    # Combine and maintain overall similarity ranking
    diverse_pathways = same_function + cross_function
    diverse_pathways.sort(key=lambda x: x.similarity_score, reverse=True)
    
    return diverse_pathways[:12]  # Return final 12
```

**Frontend Configuration:**
```javascript
// In career_pathways.html - user-configurable diversity
const diversityConfig = {
    same_function_count: 8,      // Adjustable via UI
    cross_function_count: 4,     // Adjustable via UI
    show_diversity_controls: true
};
```

### Pattern 4: Smart Caching Layer

**Concept**: Redis-based caching for common diversity patterns.

```python
def get_pathways_with_caching(source_job_id, diversity_ratio):
    cache_key = f"pathways:{source_job_id}:diversity_{diversity_ratio}"
    
    # Try cache first
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # Fall back to dynamic calculation
    pathways = calculate_diverse_pathways(source_job_id, diversity_ratio)
    
    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(pathways))
    
    return pathways
```

---

## Recommended Solution: Hybrid Query Strategy

### Implementation Plan

#### Phase 1: Enhanced Precomputation (Week 1-2)

**File**: `src/skill_similarity_engine/similarity/precompute.py`

1. **Expand pathway breadth**:
   - Increase `TOP_N_PATHWAYS` from 12 to 24
   - Lower `MIN_SIMILARITY_THRESHOLD` from 0.15 to 0.05

2. **Add function metadata**:
   - Include `source_job_function` and `target_job_function` in pathway records
   - Add `is_cross_functional` boolean flag
   - Maintain existing performance optimizations

3. **Update database schema**:
   ```sql
   ALTER TABLE career_pathways 
   ADD COLUMN source_job_function TEXT,
   ADD COLUMN target_job_function TEXT,
   ADD COLUMN is_cross_functional BOOLEAN DEFAULT FALSE;
   
   CREATE INDEX idx_career_pathways_cross_functional 
   ON career_pathways(source_job_id, is_cross_functional, similarity_rank);
   ```

#### Phase 2: Query-Time Diversity Logic (Week 3)

**File**: `src/skill_similarity_engine/webapp/database.py`

1. **Create diversity-aware query methods**:
   ```python
   def get_diverse_career_pathways(self, source_job_id, same_function_count=8, cross_function_count=4):
       """Get diversified career pathways maintaining performance."""
   ```

2. **Add configuration management**:
   ```python
   @dataclass
   class PathwayDiversityConfig:
       same_function_count: int = 8
       cross_function_count: int = 4
       enable_diversity: bool = True
   ```

#### Phase 3: Frontend Integration (Week 4)

**File**: `src/skill_similarity_engine/webapp/templates/career_pathways.html`

1. **Add diversity controls**:
   ```html
   <div class="pathway-diversity-controls">
       <label>Same Function: <input type="range" min="4" max="12" value="8" id="same-function-slider"></label>
       <label>Cross-Functional: <input type="range" min="0" max="8" value="4" id="cross-function-slider"></label>
   </div>
   ```

2. **Update pathway display**:
   ```html
   <div class="pathway-item {{ 'cross-functional' if pathway.is_cross_functional }}">
       <span class="pathway-type-badge">{{ 'Cross-Functional' if pathway.is_cross_functional else 'Same Function' }}</span>
   </div>
   ```

3. **AJAX endpoint for dynamic updates**:
   ```javascript
   function updatePathwayDiversity() {
       const diversityConfig = {
           same_function_count: parseInt($('#same-function-slider').val()),
           cross_function_count: parseInt($('#cross-function-slider').val())
       };
       
       $.ajax({
           url: `/api/career-pathways/${jobId}/diverse`,
           data: diversityConfig,
           success: updatePathwayDisplay
       });
   }
   ```

### Performance Analysis

**Query Performance Impact:**
- Precomputed data size: 17,160 → 42,900 records (+150%)
- Query time impact: <5ms additional overhead for diversity filtering
- Memory usage: Minimal increase due to indexed queries

**Cache Efficiency:**
- Common diversity ratios (8:4, 10:2, 6:6) can be cached
- 95% cache hit rate expected for standard configurations
- Fallback to dynamic calculation for custom ratios

### User Experience Enhancements

**Diversity Awareness:**
- Visual indicators for cross-functional pathways
- Explanatory tooltips for pathway types
- "Show more cross-functional options" expandable sections

**Personalisation:**
- Save user diversity preferences
- Recommend optimal diversity ratios based on user role
- A/B test different default configurations

---

## Alternative Considerations

### Real-Time Similarity Calculation

**When to Consider:**
- If precomputation maintenance becomes complex
- For highly personalised similarity factors (location, preferences)
- With improved hardware capabilities

**Technical Requirements:**
- Sub-50ms similarity calculation performance
- Caching layer for frequently accessed job pairs
- Optimised skill set comparison algorithms

### Machine Learning Diversity Models

**Future Enhancement:**
- Train models to predict optimal diversity ratios per user
- Use historical pathway success data to weight recommendations
- Incorporate external factors (market demand, skill gaps)

---

## Success Metrics

### Technical Performance
- Query response time: <100ms (maintained)
- Cache hit rate: >90% for common diversity patterns
- Database load: <10% increase from expanded precomputation

### Business Value
- Cross-functional pathway engagement: >25% of total pathway views
- Pathway diversity index: Average of 3+ job functions in top 12 recommendations
- User satisfaction: Qualitative feedback on pathway relevance

### User Adoption
- Diversity control usage: >40% of users interact with diversity settings
- Cross-functional pathway click-through rate: >15%
- Career Transition Analysis Generator: Include cross-functional recommendations in >80% of documents

---

## Implementation Timeline

| Phase | Duration | Deliverables | Dependencies |
|-------|----------|--------------|--------------|
| **Phase 1**: Enhanced Precomputation | 2 weeks | Updated precompute.py, database schema changes | Database migration window |
| **Phase 2**: Query-Time Diversity | 1 week | New query methods, diversity logic | Phase 1 completion |
| **Phase 3**: Frontend Integration | 1 week | Updated career_pathways.html, AJAX endpoints | Phase 2 completion |
| **Phase 4**: Testing & Optimisation | 1 week | Performance validation, user testing | All phases complete |

**Total Timeline**: 5 weeks  
**Risk Mitigation**: Phased rollout with feature flags, A/B testing for diversity ratios

---

## Conclusion

The hybrid query strategy provides the optimal balance between performance, flexibility, and user experience. By expanding precomputation breadth and applying diversity logic at query time, we maintain sub-100ms response times while ensuring meaningful cross-functional pathway representation.

This approach positions the NAB Skills Intelligence Platform to deliver genuinely valuable career guidance that breaks down functional silos and promotes workforce agility across the organisation.

---

**Next Steps:**
1. Review and approve architectural approach
2. Plan database migration for expanded precomputation
3. Design user testing protocol for diversity controls
4. Begin Phase 1 implementation

**References:**
- `src/skill_similarity_engine/similarity/precompute.py`
- `src/skill_similarity_engine/webapp/templates/career_pathways.html`
- `docs/sqlite_schema_design.md`
- `docs/career_analysis_example_gold_standard.md` 
