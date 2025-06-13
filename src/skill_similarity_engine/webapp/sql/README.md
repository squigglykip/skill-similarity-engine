# SQL Query Organisation

This directory contains organised SQL queries for the NAB Skills Intelligence Platform, separated by functional area for better maintainability and discoverability.

## Directory Structure

```
sql/
├── __init__.py              # Query loader and management system
├── README.md                # This documentation
├── jobs.sql                 # Job and job family queries
├── similarities.sql         # Job similarity and matching queries  
├── career_pathways.sql      # Career progression analysis
├── skills.sql               # Skills analysis and proficiency
├── positions.sql            # Position and organisational context
├── d3_visualization.sql     # D3.js tree and network data
└── metadata.sql             # Database statistics and health checks
```

## Usage

### Basic Usage

```python
from sql import queries

# Get a specific query
query = queries.get('jobs', 'get_job_families')

# Execute with database connection
results = db.execute(query).fetchall()
```

### Available Categories

#### 1. Jobs (`jobs.sql`)
- `get_job_families` - All job families with counts
- `get_jobs_in_family` - Jobs within a specific family
- `get_job_details` - Detailed job information
- `search_jobs` - Search jobs by title with optional family filter
- `get_job_skills` - Skills for a specific job
- `get_jobs_by_level` - Jobs filtered by level
- `get_jobs_by_cluster` - Jobs filtered by cluster
- `get_job_summary_stats` - Summary statistics for jobs

#### 2. Similarities (`similarities.sql`)
- `get_similar_jobs` - Similar jobs with minimum similarity threshold
- `get_top_similar_jobs` - Top N most similar jobs
- `get_similarity_distribution` - Distribution of similarity scores
- `get_mutual_similarities` - Bidirectional high similarities
- `get_similarity_by_family` - Similarity statistics between families
- `find_career_clusters` - Clusters of highly similar jobs
- `get_similarity_gaps` - Jobs with low similarity (specialised roles)
- `get_cross_family_similarities` - Highest similarities between different families

#### 3. Career Pathways (`career_pathways.sql`)
- `get_career_progression_options` - Career progression paths from starting job
- `get_skills_gap_analysis` - Skills gap between two jobs
- `get_pathway_by_level_progression` - Career pathways by level progression
- `get_cross_family_pathways` - Pathways to other job families
- `get_common_career_transitions` - Most common career transitions
- `get_skill_development_recommendations` - Skill development for career targets

#### 4. Skills (`skills.sql`)
- `get_skills_by_category` - Skills grouped by category
- `get_top_skills_in_family` - Most common skills within job family
- `get_skill_proficiency_distribution` - Proficiency level distribution
- `get_skill_gaps_between_jobs` - Skills gaps between specific jobs
- `get_transferable_skills` - Skills common across multiple families
- `get_emerging_skills` - Skills in high-level but not entry-level jobs
- `get_skill_combinations` - Common skill combinations
- `get_skills_by_proficiency_requirement` - Skills by proficiency level
- `get_skill_trends_by_level` - How skill requirements change by level

#### 5. Positions (`positions.sql`)
- `get_positions_for_job` - All positions for a specific job profile
- `get_positions_by_organisation` - Positions within organisation/division
- `get_organisation_structure` - Organisational hierarchy
- `get_position_distribution_by_location` - Position distribution by location
- `get_job_family_distribution` - Job family distribution across organisation
- `get_positions_needing_skills` - Positions requiring specific skills
- `get_career_opportunities_by_location` - Career opportunities by location
- `get_skills_demand_by_division` - Skills demand analysis by division
- `get_position_summary_stats` - Position and organisational statistics

#### 6. D3 Visualizations (`d3_visualization.sql`)
- `get_tree_data_for_family` - Hierarchical tree data for D3.js collapsible tree
- `get_network_data_for_similarities` - Network data for force-directed graphs
- `get_sunburst_data` - Hierarchical data for D3.js sunburst charts
- `get_chord_diagram_data` - Data for chord diagrams of skill relationships
- `get_tree_map_data` - Data for treemap of job distribution
- `get_career_pathway_tree` - Tree structure for career pathway visualization

#### 7. Metadata (`metadata.sql`)
- `get_database_stats` - Comprehensive database statistics
- `get_table_sizes` - Size information for each table
- `get_data_quality_metrics` - Data quality and completeness checks
- `get_similarity_metrics` - Similarity analysis metrics
- `get_skills_distribution` - Distribution of skills across categories
- `get_job_family_stats` - Statistics for each job family
- `get_schema_metadata` - Schema information and metadata
- `get_database_health_check` - Database health checks
- `get_performance_metrics` - Performance indicators

## Query File Format

Each SQL file uses a standardised format:

```sql
-- =================================================================
-- CATEGORY NAME QUERIES
-- Description of the category
-- =================================================================

-- query_name: query_identifier
-- Description of what the query does
SELECT 
    column1,
    column2
FROM table1
WHERE condition = ?
ORDER BY column1;

-- query_name: another_query
-- Another query description
SELECT ...
```

## Advanced Usage

### Listing Available Queries

```python
# List all categories
categories = queries.list_categories()

# List queries in a category
job_queries = queries.list_queries_in_category('jobs')

# List all queries
all_queries = queries.list_all()
```

### Searching Queries

```python
# Search for queries containing 'similarity'
results = queries.search_queries('similarity')

# Search for specific patterns
pathway_queries = queries.search_queries('pathway')
```

### Query Information

```python
# Get detailed information about a query
info = queries.get_query_info('jobs', 'get_job_families')
print(f"Parameters needed: {info['parameter_count']}")
print(f"Tables used: {info['tables_used']}")
```

## Database Schema Compatibility

These queries are designed for the actual SQLite database schema:

- **jobs**: `id`, `job_title`, `job_family`, `job_level`, `job_cluster`
- **job_similarities**: `job_id`, `similar_job_id`, `similarity_score`, `similarity_category`
- **job_skills**: `job_id`, `skills_skill_id`, `proficiency_level`
- **skills**: `id`, `skill_name`, `skill_category`, `skill_subcategory`
- **positions**: `PositionID`, `JobProfileID`, `CompanyOrganisationID`, etc.

## Best Practices

1. **Use parameterised queries**: All queries use `?` placeholders for safety
2. **Organise by function**: Keep related queries in the same file
3. **Document thoroughly**: Include clear descriptions for each query
4. **Consistent naming**: Use descriptive, consistent query names
5. **Handle errors**: Always wrap database calls in try-catch blocks
6. **Limit results**: Use LIMIT clauses for performance
7. **Index awareness**: Queries are designed to work with existing indexes

## Adding New Queries

1. Choose the appropriate category file (or create a new one)
2. Follow the standardised format
3. Use descriptive query names
4. Include clear documentation
5. Test thoroughly with real data
6. Update this README if adding new categories

## Performance Considerations

- Queries include appropriate LIMIT clauses
- Complex joins are optimised for the existing schema
- Similarity thresholds are used to reduce result sets
- Aggregations are carefully designed for large datasets

This organisation makes the SQL queries much more maintainable, discoverable, and easier to debug than a single monolithic file. 