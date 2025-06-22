"""
Executive Summary Generator
Generates the Executive Summary section for white papers using YAML templates and database queries.
"""

import sqlite3
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from jinja2 import Template

class ExecutiveSummaryGenerator:
    """Generates executive summary content using template-driven approach."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.template_path = Path(__file__).parent / 'templates' / 'sections' / 'executive_summary.yaml'
        self.template_data = self._load_template()
        
    def _load_template(self) -> Dict:
        """Load YAML template for executive summary."""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"⚠️ Error loading executive summary template: {e}")
            return {}
    
    def generate(self, job_from: str, analysis_mode: str = 'top_3') -> Dict:
        """Generate executive summary content for a given source job."""
        
        # Step 1: Get database-derived values
        db_values = self._get_database_values(job_from)
        
        # Step 2: Get top pathways analysis
        top_pathways = self._get_top_pathways(job_from, limit=3)
        
        # Step 3: Calculate dynamic thresholds and descriptors
        dynamic_descriptors = self._calculate_dynamic_descriptors(top_pathways, db_values)
        
        # Step 4: Populate template variables
        template_variables = self._populate_template_variables(
            job_from, db_values, top_pathways, dynamic_descriptors
        )
        
        # Step 5: Generate content sections
        content = self._generate_content_sections(template_variables)
        
        return {
            'section_title': 'Executive Summary',
            'content': content,
            'references': self._generate_references(job_from, top_pathways),
            'template_variables': template_variables  # For debugging
        }
    
    def _get_database_values(self, job_from: str) -> Dict:
        """Execute database queries to get reference values."""
        
        values = {}
        
        try:
            # Reference (1): Total job profiles
            cursor = self.db.execute("SELECT COUNT(*) as total_job_count FROM jobs")
            result = cursor.fetchone()
            values['total_job_count'] = result[0] if result else 0
            
            # Reference (14): Active competencies
            cursor = self.db.execute("SELECT COUNT(DISTINCT Skill_ID) as active_competencies_count FROM job_skills")
            result = cursor.fetchone()
            values['active_competencies_count'] = result[0] if result else 0
            
            # Reference (15): Pre-computed pathways
            cursor = self.db.execute("SELECT COUNT(*) as pathways_count FROM career_pathways")
            result = cursor.fetchone()
            values['pathways_count'] = result[0] if result else 0
            
            # Reference (16): Division count
            cursor = self.db.execute("SELECT COUNT(DISTINCT Division) as division_count FROM positions")
            result = cursor.fetchone()
            values['division_count'] = result[0] if result else 0
            
            # Reference (13): Confidence level calculation
            values['confidence_level'] = self._calculate_confidence_level(values)
            
            # Get similarity distribution for thresholds
            values['similarity_distribution'] = self._get_similarity_distribution()
            
            # Get source job details
            values['source_job_details'] = self._get_source_job_details(job_from)
            
        except Exception as e:
            print(f"⚠️ Error getting database values: {e}")
            values = self._get_fallback_values()
        
        return values
    
    def _get_top_pathways(self, job_from: str, limit: int = 3) -> List[Dict]:
        """Get top similarity pathways for source job using optimized career_pathways table."""
        
        try:
            # Reference (2): Top similarities with job details using career_pathways table
            # Exclude 100% matches (identical jobs) for meaningful career transitions
            # Look at more ranks to find non-100% matches
            query = """
            SELECT 
                cp.target_job_id,
                cp.similarity_score,
                j.JobProfile as target_job_title,
                j.JobFunction as target_job_function,
                j.ManagementLevel as target_management_level,
                cp.similarity_rank as rank,
                cp.career_move_type,
                cp.difficulty_score
            FROM career_pathways cp
            JOIN jobs j ON cp.target_job_id = j.JobProfileID
            WHERE cp.source_job_id = ?
              AND cp.similarity_score < 1.0
            ORDER BY cp.similarity_score DESC, cp.similarity_rank
            LIMIT ?
            """
            
            cursor = self.db.execute(query, (job_from, limit))
            results = cursor.fetchall()
            
            pathways = []
            for result in results:
                pathway = {
                    'target_job_id': result[0],
                    'similarity_score': round(result[1] * 100, 1),  # Convert to percentage
                    'target_job_title': result[2],
                    'target_job_function': result[3],
                    'target_management_level': result[4],
                    'rank': result[5],
                    'career_move_type': result[6],  # Already calculated in career_pathways table
                    'move_type': result[6],  # Add for backwards compatibility
                    'difficulty_score': round(result[7] * 100, 1) if result[7] else 0,
                    'similarity_ref': str(4 + result[5]),  # References 5, 7, 9
                    'move_type_ref': str(5 + result[5])    # References 6, 8, 10
                }
                
                # Add level transition description (move_type already in career_pathways table)
                pathway.update(self._calculate_move_type(job_from, pathway))
                
                pathways.append(pathway)
            
            return pathways
            
        except Exception as e:
            print(f"⚠️ Error getting top pathways: {e}")
            return []
    
    def _calculate_move_type(self, job_from: str, pathway: Dict) -> Dict:
        """Add level transition description and strategic context (move type already calculated)."""
        
        try:
            # Get source job details
            source_query = """
            SELECT JobFunction, ManagementLevel 
            FROM jobs 
            WHERE JobProfileID = ?
            """
            source_result = self.db.execute(source_query, (job_from,)).fetchone()
            
            if not source_result:
                return {
                    'level_transition': 'Unknown',
                    'strategic_context_explanation': 'Analysis not available'
                }
            
            source_function = source_result[0]
            source_level = source_result[1]
            target_function = pathway['target_job_function']
            target_level = pathway['target_management_level']
            
            # Use pre-calculated move type from career_pathways table
            move_type = pathway.get('career_move_type', 'Other')
            
            # Create level transition description
            level_transition = f"{source_level} → {target_level}"
            if source_function != target_function:
                level_transition += f", {source_function} → {target_function}"
            else:
                level_transition += ", same function"
            
            # Get strategic context explanation
            explanations = self.template_data.get('executive_summary', {}).get('primary_recommendations', {}).get('strategic_context_explanations', {})
            strategic_context = explanations.get(move_type, 'Strategic transition opportunity')
            
            # Replace placeholders in explanation
            strategic_context = strategic_context.replace('{source_function}', source_function.lower())
            strategic_context = strategic_context.replace('{target_function}', target_function.lower())
            
            return {
                'level_transition': level_transition,
                'strategic_context_explanation': strategic_context
            }
            
        except Exception as e:
            print(f"⚠️ Error calculating transition details: {e}")
            return {
                'level_transition': 'Analysis not available',
                'strategic_context_explanation': 'Move type analysis not available'
            }
    
    def _extract_level_number(self, management_level: str) -> int:
        """Extract numeric level from management level string."""
        if not management_level:
            return 1
        
        try:
            # Look for "Group X" pattern
            if 'Group' in management_level:
                parts = management_level.split()
                for part in parts:
                    if part.isdigit():
                        return int(part)
            return 1
        except:
            return 1
    
    def _calculate_confidence_level(self, values: Dict) -> str:
        """Calculate confidence level based on data volume."""
        
        active_competencies = values.get('active_competencies_count', 0)
        pathways_count = values.get('pathways_count', 0)
        division_count = values.get('division_count', 0)
        
        if (active_competencies > 2000 and 
            pathways_count > 8000 and 
            division_count >= 6):
            return 'HIGH'
        elif (active_competencies > 1000 and 
              pathways_count > 5000 and 
              division_count >= 4):
            return 'MEDIUM-HIGH'
        else:
            return 'MEDIUM'
    
    def _get_similarity_distribution(self) -> Dict:
        """Get NAB-specific similarity distribution for threshold calculation."""
        
        try:
            query = """
            SELECT 
                similarity_score,
                PERCENT_RANK() OVER (ORDER BY similarity_score) * 100 as percentile_rank
            FROM job_similarities 
            WHERE similarity_score > 0.0 AND similarity_score < 1.0
            ORDER BY similarity_score
            """
            
            cursor = self.db.execute(query)
            results = cursor.fetchall()
            
            if not results:
                return self._get_default_distribution()
            
            scores = [r[0] for r in results]
            
            # Calculate key percentiles
            import numpy as np
            percentiles = {
                95: np.percentile(scores, 95),
                90: np.percentile(scores, 90),
                75: np.percentile(scores, 75),
                50: np.percentile(scores, 50)
            }
            
            return {
                'percentiles': percentiles,
                'total_scores': len(scores),
                'mean': np.mean(scores),
                'scores': scores
            }
            
        except Exception as e:
            print(f"⚠️ Error getting similarity distribution: {e}")
            return self._get_default_distribution()
    
    def _get_default_distribution(self) -> Dict:
        """Fallback similarity distribution."""
        return {
            'percentiles': {95: 0.65, 90: 0.58, 75: 0.48, 50: 0.35},
            'total_scores': 0,
            'mean': 0.35,
            'scores': []
        }
    
    def _get_source_job_details(self, job_from: str) -> Dict:
        """Get source job details for template variables."""
        
        try:
            query = """
            SELECT JobProfile, JobFunction, ManagementLevel, JobCategory
            FROM jobs
            WHERE JobProfileID = ?
            """
            
            result = self.db.execute(query, (job_from,)).fetchone()
            
            if result:
                return {
                    'job_title': result[0],
                    'job_function': result[1],
                    'management_level': result[2],
                    'job_category': result[3]
                }
            else:
                return {
                    'job_title': 'Unknown Job',
                    'job_function': 'Unknown Function',
                    'management_level': 'Group 1',
                    'job_category': 'Unknown Category'
                }
                
        except Exception as e:
            print(f"⚠️ Error getting source job details: {e}")
            return {
                'job_title': 'Unknown Job',
                'job_function': 'Unknown Function', 
                'management_level': 'Group 1',
                'job_category': 'Unknown Category'
            }
    
    def _calculate_dynamic_descriptors(self, top_pathways: List[Dict], db_values: Dict) -> Dict:
        """Calculate dynamic descriptors based on similarity percentiles."""
        
        if not top_pathways:
            return {
                'opportunity_descriptor': 'transformation',
                'percentile_descriptor': '50th',
                'contextual_performance_descriptor': 'challenging but viable',
                'ranking_quality_descriptor': 'alternative',
                'risk_cost_descriptor': 'necessitating comprehensive transformation support',
                'data_quality_descriptor': 'limited data with significant estimates'
            }
        
        # Get highest similarity score from top pathways
        max_similarity = max(p['similarity_score'] for p in top_pathways) / 100.0
        
        # Get percentile thresholds
        distribution = db_values.get('similarity_distribution', {})
        percentiles = distribution.get('percentiles', {95: 0.65, 90: 0.58, 75: 0.48, 50: 0.35})
        
        # Determine category based on NAB-specific percentiles
        if max_similarity >= percentiles[95]:
            category = 'outstanding'
            percentile_desc = '95th'
        elif max_similarity >= percentiles[90]:
            category = 'excellent'
            percentile_desc = '90th'
        elif max_similarity >= percentiles[75]:
            category = 'good'
            percentile_desc = '75th'
        elif max_similarity >= percentiles[50]:
            category = 'development'
            percentile_desc = '50th'
        else:
            category = 'transformation'
            percentile_desc = 'below 50th'
        
        # Get descriptors from template
        template_descriptors = self.template_data.get('executive_summary', {}).get('key_findings', {})
        
        return {
            'opportunity_descriptor': template_descriptors.get('opportunity_descriptors', {}).get(category, category),
            'percentile_descriptor': percentile_desc,
            'contextual_performance_descriptor': template_descriptors.get('contextual_performance_descriptors', {}).get(category, category),
            'ranking_quality_descriptor': template_descriptors.get('ranking_quality_descriptors', {}).get(category, category),
            'risk_cost_descriptor': template_descriptors.get('risk_cost_descriptors', {}).get(category, category),
            'data_quality_descriptor': self._get_data_quality_descriptor(db_values['confidence_level'])
        }
    
    def _get_data_quality_descriptor(self, confidence_level: str) -> str:
        """Get data quality descriptor based on confidence level."""
        explanations = self.template_data.get('executive_summary', {}).get('confidence_assessment', {}).get('confidence_explanations', {})
        return explanations.get(confidence_level, 'balanced real data and validated estimates')
    
    def _populate_template_variables(self, job_from: str, db_values: Dict, 
                                   top_pathways: List[Dict], dynamic_descriptors: Dict) -> Dict:
        """Populate all template variables."""
        
        source_job = db_values['source_job_details']
        
        # Calculate similarity range from top pathways
        if top_pathways:
            min_similarity = min(p['similarity_score'] for p in top_pathways)
            max_similarity = max(p['similarity_score'] for p in top_pathways)
        else:
            min_similarity = max_similarity = 0
        
        variables = {
            # Source job context
            'source_job_title': source_job['job_title'],
            'source_job_title_plural': source_job['job_title'] + 's',  # Simple pluralization
            'source_management_level': source_job['management_level'],
            'source_job_function': source_job['job_function'],
            'source_job_function_lower': source_job['job_function'].lower() + ' and technical',
            'source_function': source_job['job_function'],
            
            # Database metrics
            'total_job_count': f"{db_values['total_job_count']:,}",
            'pathway_count': len(top_pathways),
            'min_similarity': f"{min_similarity:.1f}",
            'max_similarity': f"{max_similarity:.1f}",
            'active_competencies_count': db_values['active_competencies_count'],
            'pathways_count': db_values['pathways_count'],
            'division_count': db_values['division_count'],
            'confidence_level': db_values['confidence_level'],
            
            # Dynamic descriptors
            **dynamic_descriptors,
            
            # Top pathways
            'top_pathways': top_pathways,
            
            # Example values
            'example_good_similarity': '65'
        }
        
        return variables
    
    def _generate_content_sections(self, variables: Dict) -> Dict:
        """Generate content for each section using Jinja2 templates."""
        
        template_sections = self.template_data.get('executive_summary', {})
        content = {}
        
        try:
            # Strategic Context
            strategic_context = template_sections.get('strategic_context', {})
            strategic_template = strategic_context.get('content', '')
            content['strategic_context'] = {
                'title': strategic_context.get('title', 'Strategic Context'),
                'content': Template(strategic_template).render(**variables)
            }
            
            # Key Findings
            key_findings = template_sections.get('key_findings', {})
            key_findings_template = key_findings.get('content', '')
            content['key_findings'] = {
                'title': key_findings.get('title', 'Key Findings'),
                'content': Template(key_findings_template).render(**variables)
            }
            
            # Primary Recommendations
            primary_rec = template_sections.get('primary_recommendations', {})
            primary_template = primary_rec.get('content', '')
            content['primary_recommendations'] = {
                'title': primary_rec.get('title', 'Primary Recommendations'),
                'content': Template(primary_template).render(**variables)
            }
            
            # Data-Driven Classification
            classification = template_sections.get('data_driven_classification', {})
            classification_template = classification.get('content', '')
            content['data_driven_classification'] = {
                'content': Template(classification_template).render(**variables)
            }
            
            # Similarity Benchmarking
            benchmarking = template_sections.get('similarity_benchmarking', {})
            benchmarking_template = benchmarking.get('content', '')
            content['similarity_benchmarking'] = {
                'content': Template(benchmarking_template).render(**variables)
            }
            
            # Template Logic Note
            template_note = template_sections.get('template_logic_note', {})
            template_note_template = template_note.get('content', '')
            content['template_logic_note'] = {
                'content': Template(template_note_template).render(**variables)
            }
            
            # Confidence Assessment
            confidence = template_sections.get('confidence_assessment', {})
            confidence_template = confidence.get('content', '')
            content['confidence_assessment'] = {
                'title': confidence.get('title', 'Confidence Assessment'),
                'content': Template(confidence_template).render(**variables)
            }
            
        except Exception as e:
            print(f"⚠️ Error generating content sections: {e}")
            print(f"⚠️ Available variables: {list(variables.keys())}")
            import traceback
            traceback.print_exc()
            content = {'error': f'Content generation failed: {e}'}
        
        return content
    
    def _generate_references(self, job_from: str, top_pathways: List[Dict]) -> Dict:
        """Generate reference mappings for the executive summary."""
        
        references = self.template_data.get('references', {})
        
        # Add job-specific references
        job_specific_refs = {}
        for pathway in top_pathways:
            ref_num = pathway.get('similarity_ref')
            if ref_num:
                job_specific_refs[ref_num] = f"SELECT similarity_score FROM job_similarities WHERE source_job_id = '{job_from}' AND target_job_id = '{pathway['target_job_id']}'"
        
        return {**references, **job_specific_refs}
    
    def _get_fallback_values(self) -> Dict:
        """Fallback values when database queries fail."""
        return {
            'total_job_count': 715,
            'active_competencies_count': 2091,
            'pathways_count': 8580,
            'division_count': 6,
            'confidence_level': 'MEDIUM',
            'similarity_distribution': self._get_default_distribution(),
            'source_job_details': {
                'job_title': 'Unknown Job',
                'job_function': 'Unknown Function',
                'management_level': 'Group 1',
                'job_category': 'Unknown Category'
            }
        } 