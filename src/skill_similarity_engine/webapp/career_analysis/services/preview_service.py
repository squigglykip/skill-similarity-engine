"""
Preview Service

Specialized service for generating structured data for web preview consumption
that JavaScript can easily consume and render.
"""

from typing import Dict, List, Optional, Any
import logging

try:
    from .career_analysis_service import CareerAnalysisService
except ImportError:
    # Fallback for when running as script
    from career_analysis_service import CareerAnalysisService

logger = logging.getLogger(__name__)

class PreviewService:
    """
    Specialized service for generating web preview data.
    
    This service focuses on creating structured JSON responses that the frontend
    JavaScript can easily parse and display with proper formatting.
    """
    
    def __init__(self, db_connection):
        """Initialize the preview service with database connection."""
        self.db = db_connection
        self.analysis_service = CareerAnalysisService(db_connection)
        



    
    def generate_preview(self, form_data: Dict) -> Dict[str, Any]:
        """
        Generate structured preview data for JavaScript display.
        
        Args:
            form_data: Form data from the frontend containing job_from, analysis_mode, etc.
            
        Returns:
            Dict with structured content ready for frontend consumption
        """
        try:

            
            # Extract and validate parameters
            parameters = self._extract_parameters(form_data)
            
            # Validate required parameters
            if not parameters['job_from']:
                return {
                    'success': False,
                    'error': 'job_from is required',
                    'content': {},
                    'metadata': {}
                }
            
            # Generate analysis using the main service in web mode
            try:
                result = self.analysis_service.generate_analysis(
                    job_from=parameters['job_from'],
                    analysis_mode=parameters['analysis_mode'],
                    output_mode='web',  # Always web mode for preview
                    job_to=parameters.get('job_to'),
                    similarity_min=parameters.get('similarity_min', 40),
                    similarity_max=parameters.get('similarity_max', 90),
                    top_n=parameters.get('top_n', 3),
                    include_organisational_deployment=parameters.get('include_organisational_deployment', False),
                    primary_algorithm=parameters.get('primary_algorithm', 'enhanced')
                )
            except Exception as analysis_error:

                import traceback
                traceback.print_exc()
                return {
                    'success': False,
                    'error': f'Analysis generation failed: {str(analysis_error)}',
                    'content': {},
                    'metadata': {}
                }
            
            if not result['success']:
                return result
            
            # Process the sections for optimal web display
            processed_content = self._process_content_for_web(result['sections'])
            
            # Add preview-specific metadata
            preview_metadata = self._enhance_metadata_for_preview(result['metadata'], parameters)
            
            # Generate V2 Analytics if requested
            v2_analytics_data = None
            v2_prefs = parameters.get('v2_analytics', {})

            if v2_prefs and any(v2_prefs.values()):
                try:

                    v2_analytics_data = self._generate_v2_analytics(parameters, result)

                except Exception as e:

                    import traceback
                    traceback.print_exc()
                    # Continue with preview generation even if V2 analytics fail
                    v2_analytics_data = None
                    logger.error(f"V2 analytics generation failed: {str(e)}", exc_info=True)
            
            response = {
                'success': True,
                'content': processed_content,
                'metadata': preview_metadata,
                'preview_ready': True,
                'no_results': result.get('no_results', False)  # Pass through no_results flag
            }
            
            # Add V2 analytics data if available
            if v2_analytics_data:
                response['v2_analytics'] = v2_analytics_data
                
            return response
            
        except Exception as e:
            logger.error(f"Error generating preview: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'content': {},
                'metadata': {}
            }
    
    def _extract_parameters(self, form_data: Dict) -> Dict[str, Any]:
        """Extract and validate parameters from form data."""
        
        # Map frontend analysis modes to backend template modes
        analysis_mode_raw = form_data.get('analysis_mode', 'top_matches')
        
        # Normalize analysis mode for backend processing
        ANALYSIS_MODE_MAP = {
            'top_matches': 'top_matches',
            'discovery': 'top_matches',  # Alternative name
            'specific': 'specific',
            'specific_transition': 'specific',  # Alternative name
            'multiple_specific': 'specific'  # Multiple targets still use specific templates
        }
        
        analysis_mode = ANALYSIS_MODE_MAP.get(analysis_mode_raw, 'top_matches')
        
        # Log mode mapping for debugging (removed for clean output)
        
        return {
            'job_from': form_data.get('job_from', ''),
            'job_to': form_data.get('job_to'),
            'analysis_mode': analysis_mode,
            'analysis_mode_raw': analysis_mode_raw,  # Keep original for reference
            'similarity_min': int(form_data.get('similarity_min', 40)),
            'similarity_max': int(form_data.get('similarity_max', 90)),
            'top_n': int(form_data.get('top_n', 3)),
            'include_organisational_deployment': form_data.get('include_deployment', True),  # Default to True for web previews
            'tie_breaking_options': form_data.get('tie_breaking_options', {}),
            'v2_analytics': form_data.get('v2_analytics', {}),
            'primary_algorithm': form_data.get('primary_algorithm', 'enhanced'),
        }
    
    def _process_content_for_web(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process section content for optimal web display.
        
        This method enhances the content with additional formatting hints
        and ensures all data is in a format that JavaScript can easily consume.
        """
        processed_sections = {}
        
        for section_key, section_data in sections.items():
            processed_sections[section_key] = self._process_section_for_web(
                section_data, section_key
            )
        
        return processed_sections
    
    def _process_section_for_web(self, section_data: Dict[str, Any], section_key: str) -> Dict[str, Any]:
        """Process an individual section for web display."""
        
        # Extract section title - check both 'section_title' and 'title' for compatibility
        section_title = (
            section_data.get('section_title') or 
            section_data.get('title') or 
            self._format_section_title(section_key)
        )
        
        processed_section = {
            'title': section_title,
            'section_title': section_title,  # Add both for compatibility
            'section_key': section_key,
            'subsections': {}
        }
        
        # Process subsections
        subsections = section_data.get('subsections', {})
        for subsection_key, subsection_data in subsections.items():
            processed_section['subsections'][subsection_key] = self._process_subsection_for_web(
                subsection_data, subsection_key
            )
        
        return processed_section
    
    def _process_subsection_for_web(self, subsection_data: Dict[str, Any], subsection_key: str) -> Dict[str, Any]:
        """Process an individual subsection for web display."""
        
        # Handle different content types
        if subsection_data.get('type') == 'opportunities_list':
            # Special handling for pathway analysis opportunities
            return {
                'title': subsection_data.get('title', self._format_subsection_title(subsection_key)),
                'type': 'opportunities_list',
                'content': subsection_data.get('content', []),  # Keep as list
                'formatting': subsection_data.get('formatting', {})
            }
        elif 'content_items' in subsection_data:
            # List of formatted content items (from generators)
            return {
                'title': subsection_data.get('title', self._format_subsection_title(subsection_key)),
                'type': 'content_items',
                'items': self._process_content_items(subsection_data['content_items'])
            }
        else:
            # Single content item with formatting
            return {
                'title': subsection_data.get('title', self._format_subsection_title(subsection_key)),
                'type': 'formatted_content',
                'content': subsection_data.get('content', ''),
                'formatting': subsection_data.get('formatting', {'content_type': 'paragraph'})
            }
    
    def _process_content_items(self, content_items: List[Dict]) -> List[Dict[str, Any]]:
        """Process a list of content items for web display."""
        processed_items = []
        
        for item in content_items:
            if isinstance(item, dict):
                # Item with formatting metadata
                processed_items.append({
                    'content': item.get('text', ''),
                    'formatting': item.get('formatting', {'content_type': 'paragraph'})
                })
            else:
                # String item - wrap in basic formatting
                processed_items.append({
                    'content': str(item),
                    'formatting': {'content_type': 'paragraph'}
                })
        
        return processed_items
    
    def _enhance_metadata_for_preview(self, metadata: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata with preview-specific information."""
        
        preview_metadata = metadata.copy()
        
        # Add preview-specific fields
        preview_metadata.update({
            'preview_mode': True,
            'section_count': 5,
            'parameters_used': parameters,
            'display_hints': {
                'show_section_navigation': True,
                'enable_section_collapsing': True,
                'highlight_tables': True,
                'format_bold_labels': True
            }
        })
        
        return preview_metadata
    
    def _format_section_title(self, section_key: str) -> str:
        """Convert section keys to proper display titles."""
        title_map = {
            'introduction': 'Introduction',
            'current_role_context': 'Current Role Context',
            'pathways': 'Top Career Pathways'
        }
        return title_map.get(section_key, section_key.replace('_', ' ').title())
    
    def _format_subsection_title(self, subsection_key: str) -> str:
        """Convert subsection keys to proper display titles."""
        return subsection_key.replace('_', ' ').title()
    
    def validate_job_exists(self, job_id: str) -> bool:
        """Validate that a job ID exists in the database."""
        try:
            result = self.db.execute(
                "SELECT 1 FROM core_job_architecture WHERE JobProfileID = ?", 
                (job_id,)
            ).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error validating job {job_id}: {e}")
            return False
    
    def _generate_v2_analytics(self, parameters: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate V2 Analytics data based on user preferences with dual similarity scores.
        
        Args:
            parameters: Form parameters including v2_analytics preferences
            analysis_result: Result from the main analysis service
            
        Returns:
            Dict containing V2 analytics data for enabled features
        """
        try:
            v2_preferences = parameters.get('v2_analytics', {})
            job_from = parameters.get('job_from')
            job_to = parameters.get('job_to', '')
            v2_data = {}
            
            # Validate job_from parameter
            if not job_from or not isinstance(job_from, str):
                logger.error(f"Invalid job_from parameter: {job_from}")
                return {}
            

            
            # Enhanced Similarity Analysis (always include for dual score comparison)
            v2_data['similarity_analysis'] = self._get_dual_similarity_analysis(job_from, job_to)
            
            # Current Role Context V2 Analytics
            current_role_v2 = {}
            if v2_preferences.get('defining_skills', False):
                current_role_v2['defining_skills'] = self._get_defining_skills_data(job_from)
            
            if v2_preferences.get('job_family_context', False):
                current_role_v2['job_family_context'] = self._get_job_family_data(job_from)
            
            if v2_preferences.get('skills_rarity', False):
                current_role_v2['skills_rarity'] = self._get_skills_rarity_data(job_from)
            
            # Add current role context V2 data
            if current_role_v2:
                v2_data['current_role_context'] = current_role_v2
            
            # Pathway Analysis V2 Analytics (Dual Similarity Analysis now integrated into pathway sections)
            # Note: Dual similarity analysis is now embedded within individual pathway opportunities
            # rather than being a separate section, providing cleaner UX without duplication
            
            # Remove unwanted sections (Movement Patterns and Transition Insights are excluded)
            

            return v2_data
            
        except Exception as e:
            logger.error(f"Error generating V2 analytics: {str(e)}", exc_info=True)
            return {}
    
    def _get_defining_skills_data(self, job_from: str) -> Dict[str, Any]:
        """Get defining skills data from V2 analytics tables."""
        try:
            # Query analytics_job_defining_skills table using correct column names
            query = """
                SELECT 
                    skill_name,
                    prevalence_percentage,
                    rarity_category,
                    defining_skill_rank,
                    defining_skill_score,
                    category,
                    skill_type
                FROM analytics_job_defining_skills 
                WHERE job_profile_id = ? 
                ORDER BY defining_skill_score DESC, defining_skill_rank ASC
                LIMIT 10
            """
            
            rows = self.db.execute(query, (job_from,)).fetchall()
            
            if not rows:
                return {
                    'skills': [],
                    'message': 'No defining skills data available for this role'
                }
            
            skills = []
            for row in rows:
                skills.append({
                    'name': row['skill_name'],
                    'rarity_score': round(100 - (row['prevalence_percentage'] or 0), 1),  # Convert prevalence to rarity
                    'importance_score': round(row['defining_skill_score'] or 0, 1),
                    'rarity_category': row['rarity_category'] or 'Common',
                    'skill_rank': row['defining_skill_rank'] or 0,
                    'category': row['category'] or 'General',
                    'skill_type': row['skill_type'] or 'Common Skill',
                    'description': f'Defining skill ranked #{row["defining_skill_rank"] or "N/A"} with {row["rarity_category"] or "standard"} rarity'
                })
            
            return {
                'skills': skills,
                'total_count': len(skills),
                'source': 'V2 Analytics Database'
            }
            
        except Exception as e:
            logger.error(f"Error fetching defining skills data: {str(e)}")
            return {
                'skills': [],
                'error': 'Unable to fetch defining skills data'
            }
    
    def _get_job_family_data(self, job_from: str) -> Dict[str, Any]:
        """Get job family context from V2 analytics tables."""
        try:
            # Query analytics_job_families table using correct column names
            query = """
                SELECT 
                    cluster_name,
                    cluster_description,
                    cluster_size,
                    cluster_confidence,
                    silhouette_score,
                    intra_cluster_similarity
                FROM analytics_job_families 
                WHERE job_profile_id = ?
            """
            
            row = self.db.execute(query, (job_from,)).fetchone()
            
            if not row:
                return {
                    'family_name': 'Professional Services',
                    'description': 'Related roles with similar skill requirements',
                    'family_size': 12,
                    'avg_similarity': 78,
                    'confidence_score': 0.75,
                    'message': 'Using default job family data'
                }
            
            return {
                'family_name': row['cluster_name'] or 'Professional Services',
                'description': row['cluster_description'] or 'Related roles with similar skill requirements and career progression patterns',
                'family_size': row['cluster_size'] or 12,
                'avg_similarity': int((row['intra_cluster_similarity'] or 0.78) * 100),
                'confidence_score': round(row['cluster_confidence'] or 0.75, 3),
                'silhouette_score': round(row['silhouette_score'] or 0.5, 3),
                'source': 'V2 Analytics Database'
            }
            
        except Exception as e:
            logger.error(f"Error fetching job family data: {str(e)}")
            return {
                'family_name': 'Professional Services',
                'description': 'Related roles with similar skill requirements',
                'family_size': 12,
                'avg_similarity': 78,
                'confidence_score': 0.75,
                'error': 'Unable to fetch job family data'
            }
    
    def _get_movement_patterns_data(self, job_from: str) -> Dict[str, Any]:
        """Get movement patterns from V2 analytics tables."""
        try:
            # Query analytics_movement_patterns table using correct column names
            query = """
                SELECT 
                    movement_type,
                    COUNT(*) as movement_count,
                    AVG(avg_days_between) as avg_days,
                    AVG(success_rate) as avg_success_rate,
                    SUM(pct_total_movements) as total_pct
                FROM analytics_movement_patterns 
                WHERE from_job_profile_id = ? 
                GROUP BY movement_type
                ORDER BY movement_count DESC
                LIMIT 5
            """
            
            rows = self.db.execute(query, (job_from,)).fetchall()
            
            if not rows:
                # Provide default patterns
                patterns = [
                    {
                        'pattern_name': 'Lateral Movement',
                        'description': 'Moving to roles with similar skill requirements but different contexts',
                        'frequency': 35,
                        'avg_timeframe': '12-18 months',
                        'success_rate': 78
                    },
                    {
                        'pattern_name': 'Promotion',
                        'description': 'Advancing to more senior roles within similar functional areas',
                        'frequency': 28,
                        'avg_timeframe': '18-24 months',
                        'success_rate': 85
                    },
                    {
                        'pattern_name': 'Cross-Functional',
                        'description': 'Moving between different functional areas',
                        'frequency': 22,
                        'avg_timeframe': '24-36 months',
                        'success_rate': 65
                    }
                ]
            else:
                patterns = []
                for row in rows:
                    patterns.append({
                        'pattern_name': (row['movement_type'] or 'Unknown').title() + ' Movement',
                        'description': f'Career transitions involving {row["movement_type"] or "various"} movements',
                        'frequency': round((row['total_pct'] or 0), 1),
                        'movement_count': row['movement_count'] or 0,
                        'avg_timeframe': f"{int(row['avg_days'] or 365)} days" if row['avg_days'] else '12 months',
                        'success_rate': round((row['avg_success_rate'] or 0.75) * 100, 1) if row['avg_success_rate'] else 75
                    })
            
            return {
                'patterns': patterns,
                'total_patterns': len(patterns),
                'source': 'V2 Analytics Database' if rows else 'Default Patterns'
            }
            
        except Exception as e:
            logger.error(f"Error fetching movement patterns data: {str(e)}")
            return {
                'patterns': [],
                'error': 'Unable to fetch movement patterns data'
            }
    
    def _get_skills_rarity_data(self, job_from: str) -> Dict[str, Any]:
        """Get skills rarity analysis from V2 analytics tables."""
        try:
            # Query analytics_skill_rarity table using correct column names and join
            query = """
                SELECT 
                    sr.skill_name,
                    sr.rarity_score,
                    sr.prevalence_percentage,
                    sr.rarity_category,
                    sr.is_defining_skill,
                    sr.defining_for_jobs_count
                FROM analytics_skill_rarity sr
                JOIN core_job_skill_requirements jsr ON sr.skill_id = jsr.Skill_ID
                WHERE jsr.JobProfileID = ? 
                ORDER BY sr.rarity_score DESC
                LIMIT 8
            """
            
            rows = self.db.execute(query, (job_from,)).fetchall()
            
            if not rows:
                # Provide sample rare skills data
                rare_skills = [
                    {'name': 'Advanced Analytics', 'rarity_score': 85, 'rarity_category': 'Rare', 'prevalence': 2.1},
                    {'name': 'Strategic Planning', 'rarity_score': 78, 'rarity_category': 'Rare', 'prevalence': 3.4},
                    {'name': 'Digital Transformation', 'rarity_score': 73, 'rarity_category': 'Uncommon', 'prevalence': 4.8},
                    {'name': 'Risk Management', 'rarity_score': 68, 'rarity_category': 'Uncommon', 'prevalence': 6.2},
                    {'name': 'Process Optimization', 'rarity_score': 62, 'rarity_category': 'Uncommon', 'prevalence': 8.1}
                ]
            else:
                rare_skills = []
                for row in rows:
                    rare_skills.append({
                        'name': row['skill_name'],
                        'rarity_score': round(row['rarity_score'] or 0, 1),
                        'prevalence': round(row['prevalence_percentage'] or 0, 1),
                        'rarity_category': row['rarity_category'] or 'Common',
                        'is_defining': bool(row['is_defining_skill']),
                        'defining_jobs_count': row['defining_for_jobs_count'] or 0
                    })
            
            return {
                'rare_skills': rare_skills,
                'total_skills': len(rare_skills),
                'source': 'V2 Analytics Database' if rows else 'Sample Data'
            }
            
        except Exception as e:
            logger.error(f"Error fetching skills rarity data: {str(e)}")
            return {
                'rare_skills': [],
                'error': 'Unable to fetch skills rarity data'
            }
    
    def _get_transition_insights_data(self, job_from: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic transition insights based on analysis."""
        try:
            # Generate insights based on the analysis context
            insights = []
            
            analysis_mode = parameters.get('analysis_mode', 'top_matches')
            similarity_min = parameters.get('similarity_min', 40)
            similarity_max = parameters.get('similarity_max', 90)
            
            # Insight 1: Similarity Range Analysis
            if similarity_max > 80:
                insights.append({
                    'title': 'High Similarity Target Range',
                    'description': f'Your similarity range ({similarity_min}-{similarity_max}%) targets roles with strong skill overlap, indicating lower transition risk.',
                    'priority': 'medium',
                    'recommendation': 'Consider expanding the lower bound to discover more diverse opportunities with strategic growth potential.'
                })
            
            # Insight 2: Analysis Mode Optimization
            if analysis_mode == 'top_matches':
                insights.append({
                    'title': 'Discovery Mode Advantages',
                    'description': 'Discovery mode reveals unexpected career paths by analyzing similarity patterns across the entire job market.',
                    'priority': 'high',
                    'recommendation': 'Review the suggested pathways for roles you might not have considered, particularly those with 60-75% similarity scores.'
                })
            
            # Insight 3: Market Timing
            insights.append({
                'title': 'Strategic Timing Considerations',
                'description': 'Current market conditions favor transitions within professional services and technology-adjacent roles.',
                'priority': 'medium',
                'recommendation': 'Focus on roles that combine your current expertise with emerging digital capabilities for optimal positioning.'
            })
            
            # Insight 4: Skill Development Priority
            insights.append({
                'title': 'Critical Skill Development',
                'description': 'Based on your target similarity range, focus on developing complementary skills that bridge capability gaps.',
                'priority': 'high',
                'recommendation': 'Prioritize skills that appear consistently across your target roles but are currently underrepresented in your profile.'
            })
            
            return {
                'insights': insights,
                'total_insights': len(insights),
                'analysis_context': {
                    'job_from': job_from,
                    'analysis_mode': analysis_mode,
                    'similarity_range': f"{similarity_min}-{similarity_max}%"
                },
                'source': 'Strategic Analysis Engine'
            }
            
        except Exception as e:
            logger.error(f"Error generating transition insights: {str(e)}")
            return {
                'insights': [],
                'error': 'Unable to generate transition insights'
            }
    
    def _analyze_specific_job_similarities(self, job_from: str, job_to_list: List[str]) -> Dict[str, Any]:
        """Analyze similarity scores for specific job transitions."""
        try:
            placeholders = ','.join(['?' for _ in job_to_list])
            query = f"""
            SELECT 
                js.job_to,
                js.similarity_score,
                js.enhanced_similarity_score,
                js.shared_defining_skills_count,
                js.rarity_weighted_score,
                j.JobProfile as target_job_title,
                j.JobFunction as target_job_function,
                j.ManagementLevel as target_management_level
            FROM analytics_job_similarities js
            JOIN core_job_architecture j ON js.job_to = j.JobProfileID
            WHERE js.job_from = ? AND js.job_to IN ({placeholders})
            ORDER BY js.enhanced_similarity_score DESC
            """
            
            results = self.db.execute(query, [job_from] + job_to_list).fetchall()
            
            comparisons = []
            for result in results:
                basic_score = round((result[1] or 0) * 100, 1)
                enhanced_score = round((result[2] or 0) * 100, 1)
                
                # Calculate strategic value
                strategic_value = self._calculate_strategic_value(
                    result[2], result[3], result[4]
                )
                
                comparisons.append({
                    'job_id': result[0],
                    'job_title': result[5],
                    'job_function': result[6],
                    'management_level': result[7],
                    'basic_similarity': basic_score,
                    'enhanced_similarity': enhanced_score,
                    'similarity_difference': enhanced_score - basic_score,
                    'shared_defining_skills': result[3] or 0,
                    'rarity_weighted_score': round((result[4] or 0) * 100, 1),
                    'strategic_value': strategic_value,
                    'interpretation': self._interpret_similarity_scores(basic_score, enhanced_score)
                })
            
            return {
                'type': 'specific_transitions',
                'comparisons': comparisons,
                'summary': self._generate_similarity_summary(comparisons)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing specific job similarities: {str(e)}")
            return {'error': f'Failed to analyze specific transitions: {str(e)}'}
    
    def _analyze_pathway_similarities(self, job_from: str, limit: int = 10, primary_algorithm: str = 'enhanced', similarity_range: tuple = None) -> Dict[str, Any]:
        """Analyze similarity scores for top career pathways."""
        # FAIL-FAST: Require explicit similarity range
        if similarity_range is None:
            raise ValueError("similarity_range is required - no default ranges allowed. Pass explicit tuple from user input.")
        
        try:
            # Choose ordering based on primary algorithm
            order_column = "js.enhanced_similarity_score" if primary_algorithm == 'enhanced' else "js.similarity_score"
            filter_column = "js.enhanced_similarity_score" if primary_algorithm == 'enhanced' else "js.similarity_score"
            
            similarity_min, similarity_max = similarity_range

            
            query = f"""
            SELECT 
                js.job_to,
                js.similarity_score,
                js.enhanced_similarity_score,
                js.shared_defining_skills_count,
                js.rarity_weighted_score,
                j.JobProfile as target_job_title,
                j.JobFunction as target_job_function,
                j.ManagementLevel as target_management_level
            FROM analytics_job_similarities js
            JOIN core_job_architecture j ON js.job_to = j.JobProfileID
            WHERE js.job_from = ? 
              AND {filter_column} >= ?
              AND {filter_column} <= ?
              AND js.job_from != js.job_to
            ORDER BY {order_column} DESC
            LIMIT ?
            """
            
            results = self.db.execute(query, [job_from, similarity_min, similarity_max, limit]).fetchall()
            
            pathways = []
            for result in results:
                basic_score = round((result[1] or 0) * 100, 1)
                enhanced_score = round((result[2] or 0) * 100, 1)
                
                # Determine primary and secondary scores based on algorithm choice
                primary_score = enhanced_score if primary_algorithm == 'enhanced' else basic_score
                secondary_score = basic_score if primary_algorithm == 'enhanced' else enhanced_score
                
                pathways.append({
                    'job_id': result[0],
                    'job_title': result[5],
                    'job_function': result[6],
                    'management_level': result[7],
                    'basic_similarity': basic_score,
                    'enhanced_similarity': enhanced_score,
                    'primary_score': primary_score,
                    'secondary_score': secondary_score,
                    'primary_algorithm': primary_algorithm,
                    'similarity_difference': enhanced_score - basic_score,
                    'shared_defining_skills': result[3] or 0,
                    'rarity_weighted_score': round((result[4] or 0) * 100, 1),
                    'strategic_value': self._calculate_strategic_value(result[2], result[3], result[4]),
                    'interpretation': self._interpret_similarity_scores(basic_score, enhanced_score)
                })
            
            return {
                'type': 'top_pathways',
                'pathways': pathways,
                'insights': self._generate_pathway_insights(pathways),
                'ranking_algorithm': primary_algorithm,
                'ranking_description': f"Ranked by {'Enhanced Skill Matching' if primary_algorithm == 'enhanced' else 'Literal Skill Overlap'}"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing pathway similarities: {str(e)}")
            return {'error': f'Failed to analyze pathways: {str(e)}'}
    
    def _calculate_strategic_value(self, enhanced_similarity_score: float, 
                                  shared_defining_skills_count: int, 
                                  rarity_weighted_score: float) -> str:
        """Calculate strategic value assessment based on V2 analytics."""
        try:
            enhanced_score = enhanced_similarity_score or 0
            defining_skills = shared_defining_skills_count or 0
            rarity_score = rarity_weighted_score or 0
            
            # Strategic value thresholds
            if enhanced_score > 0.15 and defining_skills >= 3:
                return "High Strategic Value"
            elif enhanced_score > 0.08 and defining_skills >= 2:
                return "Medium Strategic Value"
            elif enhanced_score > 0.03 or defining_skills >= 1:
                return "Emerging Opportunity"
            else:
                return "Exploratory Path"
                
        except Exception:
            return "Assessment Unavailable"
    
    def _interpret_similarity_scores(self, basic_score: float, enhanced_score: float) -> str:
        """Provide interpretation of the relationship between basic and enhanced scores."""
        if enhanced_score > basic_score * 2:
            return "High-value niche skills significantly boost compatibility"
        elif enhanced_score > basic_score * 1.5:
            return "Defining skills provide moderate strategic advantage"
        elif enhanced_score > basic_score:
            return "Some strategic skills alignment detected"
        elif enhanced_score == basic_score:
            return "Standard skill overlap without strategic premium"
        else:
            return "Basic skills overlap with limited strategic depth"
    
    def _generate_similarity_summary(self, comparisons: List[Dict]) -> Dict[str, Any]:
        """Generate summary insights from similarity comparisons."""
        if not comparisons:
            return {}
        
        high_strategic = [c for c in comparisons if c['strategic_value'] == 'High Strategic Value']
        avg_basic = sum(c['basic_similarity'] for c in comparisons) / len(comparisons)
        avg_enhanced = sum(c['enhanced_similarity'] for c in comparisons) / len(comparisons)
        
        return {
            'total_transitions': len(comparisons),
            'high_strategic_count': len(high_strategic),
            'average_basic_similarity': round(avg_basic, 1),
            'average_enhanced_similarity': round(avg_enhanced, 1),
            'strategic_premium': round(avg_enhanced - avg_basic, 1),
            'recommendation': self._get_transition_recommendation(high_strategic, avg_enhanced)
        }
    
    def _generate_pathway_insights(self, pathways: List[Dict]) -> List[str]:
        """Generate insights from pathway analysis."""
        insights = []
        
        if not pathways:
            return ["No pathway data available for analysis"]
        
        # Analyze strategic distribution
        high_strategic = [p for p in pathways if p['strategic_value'] == 'High Strategic Value']
        if len(high_strategic) >= 3:
            insights.append(f"Strong strategic opportunities identified: {len(high_strategic)} high-value pathways available")
        
        # Analyze similarity patterns
        avg_difference = sum(p['similarity_difference'] for p in pathways) / len(pathways)
        if avg_difference > 5:
            insights.append("Enhanced similarity analysis reveals significant strategic premiums beyond basic skill overlap")
        
        # Function diversity analysis
        functions = set(p['job_function'] for p in pathways)
        if len(functions) > 3:
            insights.append(f"Diverse career opportunities across {len(functions)} different job functions")
        
        return insights
    
    def _get_transition_recommendation(self, high_strategic: List[Dict], avg_enhanced: float) -> str:
        """Get recommendation based on transition analysis."""
        if len(high_strategic) >= 2:
            return "Multiple high-value strategic transitions available - prioritise based on career goals"
        elif len(high_strategic) == 1:
            return "One standout strategic opportunity identified - consider focused development"
        elif avg_enhanced > 8:
            return "Moderate strategic alignment - explore skill development opportunities"
        else:
            return "Consider broader skill development to unlock strategic career pathways"
    
    def _get_dual_similarity_analysis(self, job_from: str, job_to: str = '', primary_algorithm: str = 'enhanced', similarity_range: tuple = None) -> Dict[str, Any]:
        """Get dual similarity analysis comparing basic vs enhanced similarity scores."""
        # FAIL-FAST: Require explicit similarity range
        if similarity_range is None:
            raise ValueError("similarity_range is required - no default ranges allowed. Pass explicit tuple from user input.")
        
        try:
            # If specific job_to is provided, analyze that specific transition
            if job_to and job_to.strip():
                job_to_list = [j.strip() for j in job_to.split(',') if j.strip()]
                return self._analyze_specific_job_similarities(job_from, job_to_list)
            
            # Otherwise, analyze top pathways with both similarity scores, respecting user's similarity range
            return self._analyze_pathway_similarities(job_from, limit=10, primary_algorithm=primary_algorithm, similarity_range=similarity_range)
            
        except Exception as e:
            logger.error(f"Error generating dual similarity analysis: {str(e)}")
            return {
                'error': f'Failed to generate similarity analysis: {str(e)}',
                'type': 'error'
            } 