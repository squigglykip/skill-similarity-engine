# White Paper Generation File Structure
## Modular, Threshold-Based Content System

Based on your existing webapp structure pattern, here's the recommended organization for modular white paper generation:

```
src/skill_similarity_engine/webapp/
├── whitepaper/                              # New white paper module
│   ├── __init__.py                         # Module initialization
│   ├── generator.py                        # Main white paper generation engine
│   ├── analyzer.py                         # Data analysis and threshold logic
│   ├── formatter.py                        # Document formatting (Word, PDF, PowerPoint)
│   │
│   ├── templates/                          # Content templates (following your templates/ pattern)
│   │   ├── narratives/                     # Story-based narrative templates
│   │   │   ├── excellent_opportunities.yaml    # High similarity content
│   │   │   ├── good_opportunities.yaml         # Medium similarity content  
│   │   │   ├── development_required.yaml       # Low similarity content
│   │   │   └── transformation_required.yaml    # Very low similarity content
│   │   │
│   │   ├── audiences/                      # Audience-specific adaptations
│   │   │   ├── business_leaders.yaml          # Executive focus content
│   │   │   ├── hr_partners.yaml               # Implementation focus content
│   │   │   ├── affected_colleagues.yaml       # Personal support content
│   │   │   └── learning_teams.yaml            # Educational content
│   │   │
│   │   ├── scenarios/                      # Scenario-specific content
│   │   │   ├── skill_sunsetting.yaml          # Skill obsolescence scenarios
│   │   │   ├── division_restructure.yaml      # Organizational change scenarios
│   │   │   └── skills_gap_analysis.yaml       # Development pathway scenarios
│   │   │
│   │   ├── sections/                       # Modular document sections
│   │   │   ├── executive_summary.yaml         # Executive summary templates
│   │   │   ├── context_analysis.yaml          # Context and current state
│   │   │   ├── opportunity_analysis.yaml      # Transition opportunities
│   │   │   ├── skills_development.yaml        # Skills gap and development
│   │   │   ├── implementation_roadmap.yaml    # Implementation planning
│   │   │   └── appendices.yaml               # Supporting data and analysis
│   │   │
│   │   └── word_templates/                 # Corporate Word document templates
│   │       ├── nab_executive_template.docx    # NAB executive white paper template
│   │       ├── nab_technical_template.docx    # NAB technical analysis template
│   │       └── nab_presentation_template.pptx  # NAB PowerPoint template
│   │
│   ├── sql/                                # White paper specific queries (following your sql/ pattern)
│   │   ├── __init__.py                     # SQL query loader
│   │   ├── whitepaper_queries.sql          # Core white paper data queries
│   │   ├── skills_gap_analysis.sql         # Skills gap calculation queries
│   │   ├── workforce_impact.sql            # Workforce impact analysis queries
│   │   └── similarity_thresholds.sql       # Similarity threshold calculations
│   │
│   ├── content/                            # Dynamic content generation
│   │   ├── __init__.py                     # Content module initialization
│   │   ├── thresholds.py                   # Threshold definitions and logic
│   │   ├── variables.py                    # Template variable definitions
│   │   ├── narratives.py                   # Narrative generation logic
│   │   └── personalizer.py                # Content personalization engine
│   │
│   └── outputs/                            # Generated output handling
│       ├── __init__.py                     # Output module initialization
│       ├── word_generator.py               # Word document generation
│       ├── powerpoint_generator.py         # PowerPoint summary generation
│       ├── visualizations.py              # matplotlib/seaborn chart generation
│       └── export_handler.py               # Multi-format export coordination
```

## File Type Strategy & Content Organization

### 1. YAML Templates for Modular Content

**Why YAML**: Easy to read, supports hierarchical data, allows comments, and integrates well with Python.

#### Example: `templates/narratives/excellent_opportunities.yaml`

```yaml
# Excellent Opportunities Narrative Template
# Similarity Score: >0.7 (Top 10th percentile)

meta:
  name: "excellent_opportunities"
  similarity_range: [0.7, 1.0]
  percentile_rank: ">90th"
  confidence_level: "High"

paragraphs:
  executive_summary:
    opening: |
      Analysis indicates {transition_quality} transition prospects for colleagues in the {source_jobprofile} 
      job architecture, which encompasses positions including {position_breakdown}. Multiple high-similarity 
      pathways (average similarity: {avg_similarity_percent}%) provide {opportunity_descriptor} redeployment 
      options with {disruption_level} business disruption.
    
    recommendation: |
      Recommended approach: proceed with confidence through a managed {timeline_weeks} week transition process. 
      Expected outcome: successful redeployment with {skill_retention_percent}% skill utilisation retention.
    
    confidence_statement: |
      Our assessment indicates {confidence_level} confidence in successful outcomes, supported by 
      {pathway_count} viable pathways and {success_probability_percent}% projected success rate.

  context_analysis:
    workforce_impact: |
      Current deployment encompasses {colleague_count} colleagues within the {source_jobprofile} job 
      architecture, including {position_breakdown_detailed}. Geographic distribution spans 
      {location_count} major centres with {geographic_distribution}.
    
    business_context: |
      The emergence of {technology_driver} capabilities creates strategic opportunities to transform 
      {current_process_type} processes while maintaining {quality_standards} and positioning for 
      {strategic_benefits}.

  opportunity_analysis:
    pathway_quality: |
      Our comprehensive analysis identified {pathway_count} primary career transition pathways with an 
      average similarity score of {avg_similarity_score} indicating {transferability_assessment} and 
      {viability_assessment} transition prospects.
    
    top_opportunities:
      - pathway_template: |
          The transition to {target_role} positions represents our {ranking_descriptor} opportunity with 
          a similarity score of {similarity_score} ({alignment_description}). Current conditions present 
          {available_positions} openings across {location_distribution} with {timeline_estimate} transition timeline.

variables:
  # Dynamic variables based on data analysis
  transition_quality:
    thresholds:
      - range: [0.9, 1.0]
        value: "exceptional"
      - range: [0.8, 0.9]
        value: "excellent" 
      - range: [0.7, 0.8]
        value: "strong"
  
  opportunity_descriptor:
    thresholds:
      - range: [0.9, 1.0]
        value: "outstanding"
      - range: [0.8, 0.9]
        value: "excellent"
      - range: [0.7, 0.8]
        value: "good"
  
  disruption_level:
    thresholds:
      - range: [0.9, 1.0]
        value: "minimal"
      - range: [0.8, 0.9]
        value: "low"
      - range: [0.7, 0.8]
        value: "manageable"

conditions:
  # Conditional content based on data patterns
  geographic_flexibility:
    condition: "location_count > 1"
    content: |
      Geographic flexibility significantly enhances placement probability, with opportunities 
      distributed across {location_list} operational centres.
  
  cross_division_opportunities:
    condition: "cross_division_pathways > 0"
    content: |
      Cross-divisional opportunities expand career horizons with {cross_division_count} pathways 
      spanning {division_list} divisions.
```

### 2. Python Classes for Threshold Logic

#### Example: `content/thresholds.py`

```python
"""
Threshold-based content selection logic for white paper generation.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import yaml

@dataclass
class ThresholdRange:
    """Represents a threshold range with associated content."""
    min_value: float
    max_value: float
    content_key: str
    descriptor: str

class ContentThresholds:
    """Manages threshold-based content selection."""
    
    def __init__(self):
        self.similarity_thresholds = [
            ThresholdRange(0.9, 1.0, "outstanding_opportunities", "Outstanding"),
            ThresholdRange(0.7, 0.9, "excellent_opportunities", "Excellent"), 
            ThresholdRange(0.4, 0.7, "good_opportunities", "Good"),
            ThresholdRange(0.2, 0.4, "development_opportunities", "Development Required"),
            ThresholdRange(0.0, 0.2, "transformation_required", "Transformation Required")
        ]
        
        self.pathway_count_thresholds = [
            ThresholdRange(5, 999, "multiple_pathways", "Multiple viable pathways"),
            ThresholdRange(2, 4, "several_pathways", "Several pathway options"),
            ThresholdRange(1, 1, "limited_pathways", "Limited pathway options")
        ]
    
    def get_narrative_type(self, similarity_score: float) -> str:
        """Determine narrative type based on similarity score."""
        for threshold in self.similarity_thresholds:
            if threshold.min_value <= similarity_score <= threshold.max_value:
                return threshold.content_key
        return "transformation_required"  # fallback
    
    def get_dynamic_descriptor(self, variable_name: str, value: float, 
                             variable_config: Dict) -> str:
        """Get dynamic descriptor based on threshold ranges."""
        if variable_name not in variable_config:
            return str(value)
        
        thresholds = variable_config[variable_name].get('thresholds', [])
        for threshold in thresholds:
            range_vals = threshold['range']
            if range_vals[0] <= value <= range_vals[1]:
                return threshold['value']
        
        return str(value)  # fallback to raw value

class ContentPersonalizer:
    """Personalizes content based on calculated data and thresholds."""
    
    def __init__(self, template_loader):
        self.template_loader = template_loader
        self.thresholds = ContentThresholds()
    
    def personalize_paragraph(self, template_text: str, data: Dict[str, Any], 
                            variable_config: Dict = None) -> str:
        """Replace template variables with personalized content."""
        personalized = template_text
        
        # Replace basic variables
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in personalized:
                personalized = personalized.replace(placeholder, str(value))
        
        # Replace threshold-based variables
        if variable_config:
            for var_name, var_data in variable_config.items():
                if 'thresholds' in var_data and var_name in data:
                    descriptor = self.thresholds.get_dynamic_descriptor(
                        var_name, data[var_name], variable_config
                    )
                    placeholder = f"{{{var_name}}}"
                    personalized = personalized.replace(placeholder, descriptor)
        
        return personalized
```

### 3. Integration with Your Existing Flask Structure

#### Add to `app.py`:

```python
# Add white paper route
@app.route('/white-papers')
def white_papers():
    """White paper generation interface."""
    return render_template('white_papers.html')

@app.route('/api/generate-whitepaper', methods=['POST'])
def api_generate_whitepaper():
    """Generate white paper based on user selections."""
    from .whitepaper.generator import WhitePaperGenerator
    
    data = request.get_json()
    generator = WhitePaperGenerator(get_db())
    
    # Generate white paper based on selections
    result = generator.generate(
        job_from=data['job_from'],
        job_to=data.get('job_to'),  # Optional for "top 3" mode
        scenario=data['scenario'],
        audience=data['audience'],
        filters=data.get('filters', {})
    )
    
    return jsonify(result)
```

### 4. Main Generator Class

#### Example: `whitepaper/generator.py`

```python
"""
Main white paper generation engine.
"""

from .content.thresholds import ContentThresholds, ContentPersonalizer
from .content.narratives import NarrativeBuilder
from .analyzer import DataAnalyzer
from .formatter import DocumentFormatter
import yaml
from pathlib import Path

class WhitePaperGenerator:
    """Main white paper generation engine."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.analyzer = DataAnalyzer(db_connection)
        self.thresholds = ContentThresholds()
        self.templates_path = Path(__file__).parent / 'templates'
        
    def generate(self, job_from: str, job_to: str = None, 
                scenario: str = 'skills_gap_analysis',
                audience: str = 'business_leaders',
                output_format: str = 'word') -> Dict:
        """Generate complete white paper."""
        
        # 1. Analyze data and determine thresholds
        analysis_data = self.analyzer.analyze_transition(
            job_from, job_to, scenario
        )
        
        # 2. Determine narrative type based on similarity score
        narrative_type = self.thresholds.get_narrative_type(
            analysis_data['avg_similarity']
        )
        
        # 3. Load appropriate templates
        narrative_template = self._load_template(f'narratives/{narrative_type}.yaml')
        audience_template = self._load_template(f'audiences/{audience}.yaml')
        scenario_template = self._load_template(f'scenarios/{scenario}.yaml')
        
        # 4. Generate personalized content
        content = self._generate_content(
            narrative_template, audience_template, scenario_template, analysis_data
        )
        
        # 5. Format into requested output
        formatter = DocumentFormatter()
        document = formatter.format_document(content, output_format, analysis_data)
        
        return {
            'success': True,
            'narrative_type': narrative_type,
            'confidence_level': analysis_data['confidence_level'],
            'document': document,
            'analysis_summary': analysis_data['summary']
        }
    
    def _load_template(self, template_path: str) -> Dict:
        """Load YAML template file."""
        full_path = self.templates_path / template_path
        with open(full_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _generate_content(self, narrative_template: Dict, 
                         audience_template: Dict, scenario_template: Dict,
                         analysis_data: Dict) -> Dict:
        """Generate personalized content using templates."""
        personalizer = ContentPersonalizer(self._load_template)
        
        # Merge templates with audience and scenario adaptations
        content = {}
        
        # Generate each section
        for section_name, section_template in narrative_template['paragraphs'].items():
            if isinstance(section_template, str):
                # Simple paragraph
                content[section_name] = personalizer.personalize_paragraph(
                    section_template, analysis_data, narrative_template.get('variables')
                )
            elif isinstance(section_template, dict):
                # Complex section with subsections
                content[section_name] = {}
                for subsection, subsection_template in section_template.items():
                    content[section_name][subsection] = personalizer.personalize_paragraph(
                        subsection_template, analysis_data, narrative_template.get('variables')
                    )
        
        return content
```

## Benefits of This Structure

1. **Follows Your Patterns**: Mirrors your existing `sql/`, `templates/`, and modular approach
2. **Threshold-Based**: Content automatically adapts based on similarity scores and data patterns
3. **Modular & Maintainable**: Each component is focused and easy to update
4. **Template-Driven**: Non-technical users can modify content in YAML files
5. **Extensible**: Easy to add new narratives, audiences, or scenarios
6. **Integration-Ready**: Fits seamlessly into your existing Flask structure

This structure will allow you to have dynamic paragraphs that change based on thresholds while maintaining the organized approach you've established in your webapp.

## Example Usage Flow

```python
# Example of how the system would work:

# 1. User selects options in UI
request_data = {
    'job_from': 'node_42',  # Data Entry Specialist
    'job_to': None,         # Top 3 mode
    'scenario': 'skills_gap_analysis',
    'audience': 'business_leaders',
    'filters': {
        'division_from': 'Technology',
        'division_to': 'Corporate Banking',
        'management_level': 'Individual Contributor'
    }
}

# 2. System analyzes data
analysis = {
    'avg_similarity': 0.68,  # Good opportunities range
    'pathway_count': 3,
    'colleague_count': 15,
    'confidence_level': 'Medium-High'
}

# 3. System selects narrative template
narrative_type = 'good_opportunities'  # Based on 0.68 similarity

# 4. System personalizes content
final_paragraph = """
Analysis indicates strong transition prospects for colleagues in the 
Data Entry Specialist job architecture, which encompasses positions 
including Data Entry Clerk (8), Administrative Assistant (5), Records 
Specialist (2). Multiple good redeployment options with manageable 
business disruption have been identified.
"""

# 5. System generates Word document with NAB branding
document = generate_word_document(content, 'nab_executive_template.docx')
```

This approach gives you maximum flexibility while maintaining the organized, maintainable structure you've established in your existing webapp. 