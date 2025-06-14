# NAB Skill Similarity Engine - Handover Documentation

## Project Overview & Current Status

You are taking over development of the **NAB Skill Similarity Engine**, a sophisticated workforce analytics platform that identifies reskilling opportunities through job-to-job skill similarity analysis. This is Phase 8 of an 8-phase project with Phases 1-7 completed and production-ready.

## What Has Been Achieved ✅

### 🎯 **Core Engine (Production Ready)**
- **510,510 job pair comparisons** processed in ~3 seconds
- **Asymmetric similarity calculation** using pure skill-based overlap
- **79MB SQLite business context database** with comprehensive job, skills, and similarity data
- **Quarterly versioning system** with automated data pipeline
- **Memory-optimized processing** handling 35,000+ jobs efficiently

### 🗄️ **Database Architecture (Completed)**
```sql
-- Core tables in production use:
- jobs (715 JobProfiles)              ✅ COMPLETED
- job_skills (7,280 relationships)    ✅ COMPLETED  
- job_similarities (510,510 records)  ✅ COMPLETED
- career_pathways (8,500+ records)    ✅ COMPLETED (NEW)
- positions (1,200+ employee positions) ✅ COMPLETED
- skills (comprehensive taxonomy)      ✅ COMPLETED
```

### 🚀 **Career Pathways Solution (Just Implemented)**
We just solved a **major performance bottleneck** in the career pathway visualization:

**Problem:** D3.js tree was artificially limited to 3→2→1 relationships due to `max_results` parameter constraints
**Solution:** Pre-computed career pathways with ~8,500 relationships (top 12 per job)

**New `career_pathways` Table Schema:**
```sql
CREATE TABLE career_pathways (
    source_job_id TEXT NOT NULL,            -- Source JobProfileID
    target_job_id TEXT NOT NULL,            -- Target JobProfileID
    similarity_rank INTEGER NOT NULL,       -- Rank (1-12) based on similarity
    similarity_score REAL NOT NULL,        -- Overall similarity (0-1)
    skill_overlap_score REAL,              -- Skills-specific similarity
    shared_skills_count INTEGER,           -- Number of overlapping skills
    career_move_type TEXT,                  -- 'lateral', 'progression', 'cross_family'
    difficulty_score REAL,                 -- Estimated transition difficulty (0-1)
    
    PRIMARY KEY (source_job_id, target_job_id)
);
```

### 🌐 **Flask Webapp (In Progress)**
- **Professional NAB-styled UI** with responsive design
- **Multi-page application** (job search, similarities, career pathways)
- **D3.js tree visualization** for career progression
- **Comprehensive filters** (organizational, skills, similarity thresholds)
- **API endpoints** for AJAX functionality

## Current Issue & Next Steps 🎯

### **CRITICAL ISSUE: D3 Tree Node Spacing & Text Overlap**

The career pathway tree visualization has a **persistent text overlap problem** that has resisted multiple attempted solutions. This is now the **highest priority issue** blocking user adoption.

**Current Problem:**
- **Text labels overlap** at deeper tree levels (level 2+), especially with cousin nodes
- **D3.js separation function** is being called correctly but spacing is insufficient
- **Auto-fit scaling** negates large spacing values when tree is fitted to viewport
- **Cousin node confusion** - D3's separation function struggles with non-sibling relationships

**What Has Been Attempted (All Failed):**

1. **✗ Standardized text layout** (68px fixed height, 0.9em line spacing, 180px width, 3-line max)
2. **✗ Aggressive D3 separation values** (300-600 D3 units, 20% of tree height)
3. **✗ Absolute minimum spacing** (7.8 D3 units minimum based on text height)
4. **✗ Tree state multipliers** (1.1-1.5x for different tree sizes)
5. **✗ Manual level spacing** (88px per level added to y-coordinates after D3 layout)
6. **✗ Disabled auto-fit** (confirmed spacing works at 100% scale but gets compressed)

**Root Cause Analysis:**
- D3's `separation()` function only controls **horizontal spacing between siblings/cousins**
- **Vertical spacing between tree levels** requires manual y-coordinate adjustment
- **Auto-fit scaling** compresses the entire tree, negating large spacing values
- **Cousin relationships** confuse D3's separation logic at deeper levels

**Current State:**
- Spacing function returns 139-209 D3 units (confirmed via debug logs)
- Level spacing adds 88px per depth level (confirmed applied)
- Auto-fit disabled for testing (spacing visible at 100% scale)
- Text still overlaps at levels 2+ when tree is viewed normally

### **Next Approach Needed: Alternative Spacing Strategy**

The current D3.js tree layout approach may be fundamentally incompatible with dense text labels. Consider:

1. **Switch to D3 nodeSize() instead of size()** - gives fixed node dimensions
2. **Custom tree layout algorithm** - bypass D3's built-in spacing entirely  
3. **Force-directed layout** - let physics handle spacing naturally
4. **Hierarchical grid layout** - place nodes on a predictable grid
5. **Text-aware spacing calculation** - measure actual text dimensions dynamically

**Alternative: SQL Query Optimization (Lower Priority)**

The SQL queries are working but could be simplified:
- Remove recursive complexity from `career_pathways.sql`
- Use direct lookups from pre-computed `career_pathways` table
- Optimize for 12 children per node (not limited to 3)
- Ensure <2 second response times

### **Key Files to Focus On:**

```
├── src/skill_similarity_engine/webapp/
│   ├── templates/career_pathways.html (lines 995-1050)    # Spacing functions - CRITICAL
│   ├── templates/career_pathways.html (lines 1200-1210)   # D3 separation function
│   ├── templates/career_pathways.html (lines 1150-1200)   # Level spacing function
│   ├── app.py (lines 290-450)                            # /api/d3-tree-data endpoint
│   └── sql/career_pathways.sql                           # Tree queries (lower priority)
```

### **Current Spacing Implementation Details**

**1. Standardized Text Layout (career_pathways.html lines 1650-1700):**
```javascript
// Fixed text dimensions for predictable spacing
.style("font-size", "11px")
.style("line-height", "0.9em")        // Tight line spacing
.call(wrapText, 180);                 // 180px width, max 3 lines

function getNodeTextHeight() {
    return 68; // Always returns 68px (20px circle + 39px text + 9px padding)
}
```

**2. D3 Separation Function (career_pathways.html lines 1200-1210):**
```javascript
.separation((a, b) => {
    const spacing = getAdaptiveNodeSpacing(a, b);
    return spacing; // Returns 139-209 D3 units
});

function getAdaptiveNodeSpacing(a, b) {
    const minimumAbsoluteSpacing = 139; // 6% of 2320px tree height
    const multiplier = a.parent == b.parent ? 1.1 : 1.2; // Siblings vs cousins
    return minimumAbsoluteSpacing * multiplier;
}
```

**3. Manual Level Spacing (career_pathways.html lines 1150-1200):**
```javascript
function applyLevelSpacing() {
    const levelSpacing = 88; // 68px node + 20px buffer
    pathwayRoot.descendants().forEach(node => {
        node.y += node.depth * levelSpacing; // Add vertical spacing per level
    });
}
```

**4. Auto-fit Problem (career_pathways.html lines 1250-1300):**
```javascript
// This scales down the entire tree, negating our large spacing values
function fitTreeToView() {
    const scale = Math.min(scaleX, scaleY, 1); // Compresses tree to fit viewport
    pathwaySvg.call(pathwaySvg.zoom.transform, d3.zoomIdentity.scale(scale));
}
```

### **Research Findings & Potential Solutions**

**Key Insight from Stack Overflow Research:**
- D3's `separation()` function **only controls horizontal spacing** between nodes at the same level
- **Vertical spacing between tree levels** must be handled separately via manual y-coordinate adjustment
- **nodeSize() vs size()**: Using `tree.nodeSize([width, height])` instead of `tree.size([width, height])` gives fixed node dimensions

**Promising Alternative Approaches:**

**Option 1: Switch to nodeSize() Layout**
```javascript
// Instead of: pathwayTree = d3.tree().size([pathwayHeight, pathwayWidth])
pathwayTree = d3.tree().nodeSize([180, 88]); // Fixed width x height per node
// This gives each node exactly 180px width x 88px height
// Should eliminate overlap by guaranteeing minimum space
```

**Option 2: Force-Directed Layout**
```javascript
// Replace tree layout with force simulation
const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width/2, height/2))
    .force("collision", d3.forceCollide().radius(50)); // Prevent overlap
```

**Option 3: Custom Grid Layout**
```javascript
// Place nodes on predictable grid positions
function calculateGridPosition(node) {
    const x = node.depth * 250; // Fixed horizontal spacing
    const y = node.index * 88;  // Fixed vertical spacing based on sibling index
    return {x, y};
}
```

**Option 4: Text-Aware Dynamic Spacing**
```javascript
// Measure actual text dimensions and adjust spacing accordingly
function measureTextDimensions(text, fontSize) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    context.font = `${fontSize}px Source Sans Pro`;
    return context.measureText(text);
}
```

**Debug Tools Already Implemented:**
- Comprehensive console logging for spacing calculations
- Tree state analysis (COLLAPSED/MEDIUM/LARGE detection)
- D3 separation function call verification
- Level spacing application confirmation

## Technical Context You Need

### **Database Connection Pattern:**
```python
db = get_db()
cursor = db.execute(query, params)
results = cursor.fetchall()
```

### **D3.js Expected Format:**
```javascript
{
    "id": "job_123",
    "name": "Data Analyst", 
    "parent": "job_456",           // null for root
    "level": 2,
    "similarity_score": 0.85,
    "category": "Analytics",
    "children": [...]              // Populated by D3
}
```

### **Current Query Parameters:**
- `job_ids` - Starting job(s) for tree root
- `similarity_threshold` - Minimum similarity (0.2 default)
- `max_depth` - Tree levels (3 default) 
- `max_results` - Children per node (10 default)
- Organizational filters (division, business_unit, location, region)

## Pre-computed Data Advantages

The new `career_pathways` table gives you:
- **Pre-ranked relationships** (similarity_rank 1-12 per job)
- **Career move classification** (lateral/progression/cross_family)
- **Difficulty scoring** for transition analysis
- **Indexed performance** - queries should be <1 second

## Key Architectural Principles

1. **JobProfile-Centric**: Everything centers on JobProfileID, not individual positions
2. **Pre-computation First**: Avoid on-the-fly calculations in web queries
3. **Configurability**: Similarity thresholds and tree depth should be adjustable
4. **NAB Styling**: Professional red/white color scheme with Epilogue/Source Sans fonts
5. **Performance**: Target <2 second response times for tree generation

## Development Environment

- **Python 3.11+** with Flask webapp
- **SQLite database** (79MB) at `data/business_context/nab_business_context.db`
- **Windows PowerShell** environment
- **UK English spelling** throughout
- **Run via:** `python main.py` → Option 4 (Run Flask Webapp)

## SQL Query Rebuild Strategy & Steps

### **Step 1: Replace the Complex Recursive Query**

The current `get_career_tree_fast` query in `career_pathways.sql` is overly complex. Replace it with a simple, level-based approach:

```sql
-- query_name: get_d3_tree_data_simple
-- Simple tree builder using pre-computed career pathways
-- No recursion needed - just direct lookups by level

-- Level 0: Root nodes (selected starting jobs)
SELECT 
    j.JobProfileID as id,
    j.JobProfile as name,
    NULL as parent,
    0 as level,
    j.JobFamily as category,
    1.0 as similarity_score,
    'root' as node_type,
    j.JobProfileID as path
FROM jobs j
WHERE j.JobProfileID IN ({job_placeholders})

UNION ALL

-- Level 1: Direct career pathways from selected jobs
SELECT 
    cp.target_job_id as id,
    j.JobProfile as name,
    cp.source_job_id as parent,
    1 as level,
    j.JobFamily as category,
    cp.similarity_score,
    'career_option' as node_type,
    cp.source_job_id || '->' || cp.target_job_id as path
FROM career_pathways cp
JOIN jobs j ON cp.target_job_id = j.JobProfileID
WHERE cp.source_job_id IN ({job_placeholders})
  AND cp.similarity_score >= ?  -- similarity_threshold
  AND cp.similarity_rank <= ?   -- max_results
  
UNION ALL

-- Level 2: Second-level pathways
SELECT 
    cp2.target_job_id as id,
    j.JobProfile as name,
    cp2.source_job_id as parent,
    2 as level,
    j.JobFamily as category,
    cp2.similarity_score,
    'career_option' as node_type,
    cp1.source_job_id || '->' || cp1.target_job_id || '->' || cp2.target_job_id as path
FROM career_pathways cp1
JOIN career_pathways cp2 ON cp1.target_job_id = cp2.source_job_id
JOIN jobs j ON cp2.target_job_id = j.JobProfileID
WHERE cp1.source_job_id IN ({job_placeholders})
  AND cp1.similarity_score >= ?
  AND cp1.similarity_rank <= ?
  AND cp2.similarity_score >= ?
  AND cp2.similarity_rank <= ?
  AND cp2.target_job_id NOT IN ({job_placeholders})  -- Avoid cycles back to root

-- Continue pattern for Level 3, 4, etc. based on max_depth parameter
```

### **Step 2: Implement Dynamic Level Generation**

Create a Python function to generate the appropriate number of UNION clauses based on `max_depth`:

```python
def build_tree_query(job_count: int, max_depth: int) -> str:
    """Build dynamic tree query based on depth requirements."""
    
    job_placeholders = ','.join(['?' for _ in range(job_count)])
    
    # Level 0: Root nodes
    query_parts = [f"""
    SELECT 
        j.JobProfileID as id,
        j.JobProfile as name,
        NULL as parent,
        0 as level,
        j.JobFamily as category,
        1.0 as similarity_score,
        'root' as node_type
    FROM jobs j
    WHERE j.JobProfileID IN ({job_placeholders})
    """]
    
    # Generate levels 1 through max_depth
    for level in range(1, max_depth + 1):
        level_query = build_level_query(level, job_placeholders)
        query_parts.append(level_query)
    
    return " UNION ALL ".join(query_parts) + " ORDER BY level, similarity_score DESC"
```

### **Step 3: Add Organizational Filtering**

Apply organizational filters efficiently using LEFT JOINs:

```sql
-- Add to each level's query:
LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
WHERE (? = '' OR p.Division = ?)
  AND (? = '' OR p.Business_Unit = ?)
  AND (? = '' OR p.Location = ?)
  AND (? = '' OR p.Rg = ?)
```

### **Step 4: Optimize Parameter Handling**

The Flask endpoint should pass parameters in this order:
1. `job_ids` (repeated for each level)
2. `similarity_threshold` (repeated for each level)
3. `max_results` (repeated for each level)
4. Organizational filters (division, business_unit, location, region)

### **Step 5: Update Flask Endpoint Logic**

Modify the `/api/d3-tree-data` endpoint in `app.py`:

```python
@app.route('/api/d3-tree-data')
def api_d3_tree_data():
    # Get parameters
    job_ids = request.args.get('jobs', '').split(',')
    similarity_threshold = float(request.args.get('similarity', 0.2))
    max_depth = int(request.args.get('depth', 3))
    max_results = int(request.args.get('max_results', 12))  # Now supports 12!
    
    # Build dynamic query
    tree_query = build_tree_query(len(job_ids), max_depth)
    
    # Execute with proper parameter repetition
    params = []
    for level in range(max_depth + 1):
        params.extend(job_ids)  # Job IDs for each level
        if level > 0:  # Skip for root level
            params.extend([similarity_threshold, max_results])
    
    # Add organizational filters
    params.extend([division_filter, division_filter, 
                   business_unit_filter, business_unit_filter,
                   location_filter, location_filter,
                   region_filter, region_filter])
    
    db = get_db()
    results = db.execute(tree_query, params).fetchall()
    
    # Convert to D3.js format and return
    return jsonify(build_tree_structure(results))
```

### **Step 6: Performance Optimizations**

1. **Use Indexes**: The query will automatically use `idx_career_pathways_source` and `idx_career_pathways_rank`
2. **Limit Early**: Apply `similarity_rank <= ?` to use pre-computed rankings
3. **Avoid Subqueries**: Use direct JOINs instead of nested SELECTs
4. **Cache Results**: Consider caching common tree structures

### **Step 7: Testing Strategy**

Test the rebuilt queries with:
1. Single job root → Should show 12 children at level 1
2. Multiple job roots → Should create virtual root with multiple branches
3. Deep trees (5+ levels) → Should complete in <2 seconds
4. Organizational filters → Should properly filter at each level
5. Edge cases → Empty results, circular references, etc.

## Expected Outcome

After rebuilding the queries, the career pathway tree should:
- ✅ Show 12 children per node (configurable)
- ✅ Build trees in <2 seconds  
- ✅ Support 3-7 levels of depth
- ✅ Handle multiple starting jobs
- ✅ Apply organizational filters correctly
- ✅ Generate proper D3.js format

## Questions to Ask Yourself

1. Can I simplify this query by removing recursive elements?
2. Am I using the pre-computed `similarity_rank` effectively?
3. Are the organizational filters being applied efficiently?
4. Is the query result structure optimal for D3.js tree building?

## Success Metrics

**Primary Goal (Critical):**
- ✅ **Zero text overlap** at all tree levels (1-7)
- ✅ **Readable text labels** with proper spacing between nodes
- ✅ **Consistent spacing** regardless of tree size or depth
- ✅ **Scalable solution** that works with auto-fit enabled

**Secondary Goals (Important):**
- Tree generation time: Target <2 seconds
- Node children: Up to 12 per parent (currently working)
- Tree depth: Configurable 1-7 levels (currently working)
- Memory usage: Minimal (direct table lookups)
- UI responsiveness: Smooth D3.js rendering

**Current Status:**
- ❌ Text overlap persists at levels 2+ (BLOCKING ISSUE)
- ✅ Tree generation performance is acceptable
- ✅ 12 children per node supported
- ✅ Configurable depth working
- ✅ SQL queries optimized

## Files That Should NOT Be Changed

- Core engine (`similarity/`, `models/`, `data/`)
- Database schema (`schema_builder.py`)
- Pre-computation logic (`precompute.py`)
- Main CLI (`main.py`)

**Focus only on the webapp SQL queries and potentially the Flask endpoint logic.**

---

**Your Mission:** Rebuild the career pathway tree SQL queries from scratch to be simple, fast, and fully utilize the pre-computed `career_pathways` table. The user wants to start over with a clean, optimized approach. 