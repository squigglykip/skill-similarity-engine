"""
Pathway Ordering Utilities
Provides consistent pathway ordering for Executive Summary and Pathway Analysis generators.
Ensures that job rankings are identical across all sections of the Career Transition Analysis.
"""

import sqlite3
from typing import Dict, List, Optional

# Import display utilities
try:
    from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat
except ImportError:
    # Handle relative imports when running from within the CAREER_ANALYSIS directory
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(src_path))
    from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat

class PathwayOrderingManager:
    """Centralized manager for consistent pathway ordering across Career Transition Analysis generators."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.display_manager = JobDisplayManager(db_connection) if JobDisplayManager else None
        
    def get_top_pathways_ordered(self, job_from: str, limit: int = 3, executive_refs: bool = True, 
                                tie_breaking_options: Optional[Dict] = None, similarity_range: Optional[tuple] = None, 
                                primary_algorithm: str = 'enhanced', exclude_same_job_id: bool = False, 
                                exclude_same_job_function: bool = False) -> List[Dict]:
        """
        Get top similarity pathways with consistent ordering for all Career Transition Analysis sections.
        
        Args:
            job_from: Source job ID
            limit: Number of pathways to return (default 3 for discovery mode, but can be unlimited for specific transitions)
            executive_refs: If True, use executive summary reference numbering; if False, use pathway analysis refs
            tie_breaking_options: Dict of user-controlled tie-breaking preferences
            
        Returns:
            List of pathway dictionaries with consistent ordering and complete metadata
        """
        try:
            # Apply similarity range filtering if provided
            similarity_min, similarity_max = similarity_range if similarity_range else (0.0, 0.99)
            
            # Build dynamic ORDER BY clause based on user preferences and algorithm selection
            order_clause = self._build_order_clause(job_from, tie_breaking_options or {}, primary_algorithm)
            
            # Build enhanced query with tie-breaking support, dual similarity scores, and V2 analytics
            query = f"""
            SELECT 
                js.job_to,
                js.similarity_score,
                js.enhanced_similarity_score,
                js.rarity_weighted_score,
                js.shared_defining_skills_count,
                js.defining_skill_boost,
                js.shared_skills_count,
                js.total_skills_from,
                js.total_skills_to,
                js.skill_overlap_percentage,
                j.JobProfile as target_job_title,
                j.JobFunction as target_job_function,
                j.ManagementLevel as target_management_level,
                source_j.JobFunction as source_job_function,
                source_j.ManagementLevel as source_management_level,
                -- Enhanced tie-breaking fields
                CASE WHEN j.JobFunction = source_j.JobFunction THEN 0 ELSE 1 END as function_diff,
                CASE 
                    WHEN CAST(SUBSTR(j.ManagementLevel, -1) AS INTEGER) > CAST(SUBSTR(source_j.ManagementLevel, -1) AS INTEGER) THEN 0
                    WHEN CAST(SUBSTR(j.ManagementLevel, -1) AS INTEGER) = CAST(SUBSTR(source_j.ManagementLevel, -1) AS INTEGER) THEN 1
                    ELSE 2
                END as career_progression_priority,
                ABS(CAST(SUBSTR(j.ManagementLevel, -1) AS INTEGER) - CAST(SUBSTR(source_j.ManagementLevel, -1) AS INTEGER)) as level_jump_distance,
                ROW_NUMBER() OVER ({order_clause}) as rank
            FROM analytics_job_similarities js
            JOIN core_job_architecture j ON js.job_to = j.JobProfileID
            JOIN core_job_architecture source_j ON js.job_from = source_j.JobProfileID
            WHERE js.job_from = ?
              AND {self._get_similarity_filter_column(primary_algorithm)} >= ?  -- Apply similarity minimum from slider
              AND {self._get_similarity_filter_column(primary_algorithm)} <= ?  -- Apply similarity maximum from slider
              AND js.job_from != js.job_to  -- Exclude self-matches only
              AND js.enhanced_similarity_score IS NOT NULL  -- V2 analytics validation
              -- Job filtering logic: exclude same JobID if filter enabled
              AND (? = 0 OR j.JobID != source_j.JobID)
              -- Job function filtering logic: exclude same JobFunction if filter enabled
              AND (? = 0 OR j.JobFunction != source_j.JobFunction)
            {order_clause}
            LIMIT ?
            """
            
            cursor = self.db.execute(query, (job_from, similarity_min, similarity_max, 
                                           int(exclude_same_job_id), int(exclude_same_job_function), limit))
            results = cursor.fetchall()
            
            pathways = []
            for result in results:
                pathway = {
                    'target_job_id': result[0],
                    'similarity_score': round(result[1] * 100, 1),  # Basic similarity percentage
                    'enhanced_similarity_score': round(result[2] * 100, 1),  # V2 enhanced similarity percentage
                    'rarity_weighted_score': round(result[3] * 100, 1) if result[3] else 0,
                    'shared_defining_skills_count': result[4] or 0,
                    'defining_skill_boost': round(result[5] * 100, 1) if result[5] else 0,
                    'shared_skills_count': result[6] or 0,
                    'total_skills_from': result[7] or 0,
                    'total_skills_to': result[8] or 0,
                    'skill_overlap_percentage': result[9] or 0,
                    'target_job_title': result[10],
                    'target_job_function': result[11],
                    'target_management_level': result[12],
                    'source_job_function': result[13],
                    'source_management_level': result[14],
                    'rank': result[18],
                    # Add tie-breaking transparency data
                    'function_match': result[15] == 0,
                    'career_progression_score': result[16],
                    'level_jump_distance': result[17],
                    # V2 Analytics Insights
                    'v2_insights': {
                        'similarity_method': 'dual_score_v2',
                        'basic_vs_enhanced_ratio': round((result[1] / max(result[2], 0.001)), 2),
                        'defining_skills_impact': result[5] or 0,
                        'rarity_advantage': 'High' if result[3] and result[3] > 0.7 else 'Medium' if result[3] and result[3] > 0.4 else 'Standard',
                        'strategic_value': self._calculate_strategic_value(result[2], result[4], result[3])
                    }
                }
                
                # Add consistent reference numbering based on section
                if executive_refs:
                    # Executive Summary references: 5, 7, 9
                    pathway['similarity_ref'] = str(4 + result[18])  # References 5, 7, 9
                    pathway['move_type_ref'] = str(5 + result[18])   # References 6, 8, 10
                else:
                    # Pathway Analysis references: 57, 58, 59
                    pathway['similarity_ref'] = str(56 + result[18])  # References 57, 58, 59
                    pathway['move_type_ref'] = str(58 + result[18])   # References 59, 60, 61
                
                # Add logical role display name using centralized display manager
                if self.display_manager and DisplayFormat:
                    pathway['target_logical_role'] = self.display_manager.get_display_name(
                        pathway['target_job_id'], DisplayFormat.STANDARD
                    )
                else:
                    pathway['target_logical_role'] = pathway['target_job_title']
                
                # Calculate move type and level transition with consistent logic
                pathway.update(self._calculate_move_type(job_from, pathway))
                
                # Add tie-breaking explanation if options were used
                if tie_breaking_options:
                    pathway['tie_breaking_explanation'] = self._generate_tie_breaking_explanation(pathway, tie_breaking_options)
                
                pathways.append(pathway)
            
            return pathways
            
        except Exception as e:
            print(f"⚠️ Error getting ordered pathways: {e}")
            # Fallback to standard ordering
            return self._get_fallback_pathways(job_from, limit, executive_refs)

    def _build_order_clause(self, job_from: str, tie_breaking_options: Dict, primary_algorithm: str = 'enhanced') -> str:
        """Build dynamic ORDER BY clause based on user preferences and algorithm selection."""
        
        # Choose primary sort column based on algorithm selection
        primary_sort = "js.enhanced_similarity_score DESC" if primary_algorithm == 'enhanced' else "js.similarity_score DESC"
        order_parts = [primary_sort]
        
        # Add user-selected tie-breaking criteria in priority order
        if tie_breaking_options.get('same_function_priority'):
            order_parts.append("CASE WHEN j.JobFunction = source_j.JobFunction THEN 0 ELSE 1 END")
            
        if tie_breaking_options.get('career_progression_priority'):
            order_parts.append("CASE WHEN CAST(SUBSTR(j.ManagementLevel, -1) AS INTEGER) > CAST(SUBSTR(source_j.ManagementLevel, -1) AS INTEGER) THEN 0 ELSE 1 END")
            
        if tie_breaking_options.get('minimal_level_jump'):
            order_parts.append("ABS(CAST(SUBSTR(j.ManagementLevel, -1) AS INTEGER) - CAST(SUBSTR(source_j.ManagementLevel, -1) AS INTEGER))")
        
        # Always end with deterministic ordering
        order_parts.append("js.job_to ASC")
        
        return "ORDER BY " + ", ".join(order_parts)
    
    def _get_similarity_filter_column(self, primary_algorithm: str) -> str:
        """Get the appropriate similarity column for filtering based on algorithm selection."""
        return "js.enhanced_similarity_score" if primary_algorithm == 'enhanced' else "js.similarity_score"

    def _generate_tie_breaking_explanation(self, pathway: Dict, tie_breaking_options: Dict) -> str:
        """Generate explanation of why this pathway was ranked at its position."""
        
        explanations = []
        
        if tie_breaking_options.get('same_function_priority') and pathway.get('function_match'):
            explanations.append("Same function priority")
            
        if tie_breaking_options.get('career_progression_priority') and pathway.get('career_progression_score') == 0:
            explanations.append("Career progression opportunity")
            
        if tie_breaking_options.get('minimal_level_jump'):
            distance = pathway.get('level_jump_distance', 0)
            if distance <= 1:
                explanations.append(f"Minimal level jump ({distance} level{'s' if distance != 1 else ''})")
            
        if explanations:
            return "Prioritised: " + ", ".join(explanations)
        else:
            return "Standard similarity ranking"

    def _get_fallback_pathways(self, job_from: str, limit: int, executive_refs: bool) -> List[Dict]:
        """Fallback method when enhanced query fails."""
        try:
            # Use original simple query
            query = """
            SELECT 
                js.job_to,
                js.similarity_score,
                j.JobProfile as target_job_title,
                j.JobFunction as target_job_function,
                j.ManagementLevel as target_management_level,
                ROW_NUMBER() OVER (ORDER BY js.similarity_score DESC, js.job_to ASC) as rank
            FROM analytics_job_similarities js
            JOIN core_job_architecture j ON js.job_to = j.JobProfileID
            WHERE js.job_from = ?
              AND js.job_from != js.job_to  -- Exclude self-matches only
            ORDER BY js.similarity_score DESC, js.job_to ASC  -- Secondary sort for deterministic ordering
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
                }
                
                # Add consistent reference numbering based on section
                if executive_refs:
                    # Executive Summary references: 5, 7, 9
                    pathway['similarity_ref'] = str(4 + result[5])  # References 5, 7, 9
                    pathway['move_type_ref'] = str(5 + result[5])   # References 6, 8, 10
                else:
                    # Pathway Analysis references: 57, 58, 59
                    pathway['similarity_ref'] = str(56 + result[5])  # References 57, 58, 59
                    pathway['move_type_ref'] = str(58 + result[5])   # References 59, 60, 61
                
                # Add logical role display name using centralized display manager
                if self.display_manager and DisplayFormat:
                    pathway['target_logical_role'] = self.display_manager.get_display_name(
                        pathway['target_job_id'], DisplayFormat.STANDARD
                    )
                else:
                    pathway['target_logical_role'] = pathway['target_job_title']
                
                # Calculate move type and level transition with consistent logic
                pathway.update(self._calculate_move_type(job_from, pathway))
                
                pathways.append(pathway)
            
            return pathways
            
        except Exception as e:
            print(f"⚠️ Error in fallback pathways: {e}")
            return []

    def get_specific_job_pathways_ordered(self, job_from: str, target_job_list: List[str], executive_refs: bool = True) -> List[Dict]:
        """
        Get pathways for specific target jobs with consistent ordering.
        This method is used for specific job transition analysis where the user specifies exact target jobs.
        
        Args:
            job_from: Source job ID
            target_job_list: List of specific target job IDs to analyze
            executive_refs: If True, use executive summary reference numbering
            
        Returns:
            List of pathway dictionaries for specified target jobs in similarity score order
        """
        try:
            if not target_job_list:
                return []
            
            # Create parameterized query for specific job targets
            placeholders = ','.join(['?' for _ in target_job_list])
            query = f"""
            SELECT 
                js.job_to,
                js.similarity_score,
                j.JobProfile as target_job_title,
                j.JobFunction as target_job_function,
                j.ManagementLevel as target_management_level,
                ROW_NUMBER() OVER (ORDER BY js.similarity_score DESC, js.job_to ASC) as rank
            FROM analytics_job_similarities js
            JOIN core_job_architecture j ON js.job_to = j.JobProfileID
            WHERE js.job_from = ?
              AND js.job_to IN ({placeholders})
            ORDER BY js.similarity_score DESC, js.job_to ASC  -- Consistent deterministic ordering
            """
            
            # Execute query with job_from + target job list
            params = [job_from] + target_job_list
            cursor = self.db.execute(query, params)
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
                }
                
                # Add consistent reference numbering based on section
                if executive_refs:
                    # Executive Summary references: 5, 7, 9, 11, 13, ... (incremental)
                    pathway['similarity_ref'] = str(4 + result[5])  
                    pathway['move_type_ref'] = str(5 + result[5])   
                else:
                    # Pathway Analysis references: 57, 58, 59, 60, 61, ... (incremental)
                    pathway['similarity_ref'] = str(56 + result[5])  
                    pathway['move_type_ref'] = str(58 + result[5])   
                
                # Add logical role display name using centralized display manager
                if self.display_manager and DisplayFormat:
                    pathway['target_logical_role'] = self.display_manager.get_display_name(
                        pathway['target_job_id'], DisplayFormat.STANDARD
                    )
                else:
                    pathway['target_logical_role'] = pathway['target_job_title']
                
                # Calculate move type and level transition with consistent logic
                pathway.update(self._calculate_move_type(job_from, pathway))
                
                pathways.append(pathway)
            
            return pathways
            
        except Exception as e:
            print(f"⚠️ Error getting specific job pathways: {e}")
            return []
    
    def _calculate_move_type(self, job_from: str, pathway: Dict) -> Dict:
        """Calculate move type and level transition with consistent logic."""
        try:
            # Get source job details
            source_query = """
            SELECT JobProfile, ManagementLevel, JobFunction 
            FROM core_job_architecture 
            WHERE JobProfileID = ?
            """
            source_result = self.db.execute(source_query, (job_from,)).fetchone()
            
            if not source_result:
                return {
                    'move_type': 'Other',
                    'move_type_display': 'Strategic Transition',
                    'level_transition': 'Unknown',
                    'level_transition_display': 'Unknown transition',
                    'strategic_context_explanation': 'Analysis not available'
                }
            
            source_job_title = source_result[0]
            source_level = source_result[1]
            source_function = source_result[2]
            target_job_title = pathway['target_job_title']
            target_level = pathway['target_management_level']
            target_function = pathway['target_job_function']
            
            # Extract numeric levels (Group 1 = 1, Group 2 = 2, etc.)
            source_level_num = self._extract_level_number(source_level)
            target_level_num = self._extract_level_number(target_level)
            
            # Get base role titles for comparison (remove pay band suffixes)
            source_base_title = source_job_title.split(" - ")[0] if " - " in source_job_title else source_job_title
            target_base_title = target_job_title.split(" - ")[0] if " - " in target_job_title else target_job_title
            
            # Store source base title for use in transition description
            pathway['source_base_title'] = source_base_title
            
            # Determine move type based on logical role progression
            if source_base_title == target_base_title and target_level_num > source_level_num:
                move_type = 'Progression - Same_Role_Higher_Level'
            elif source_base_title == target_base_title and target_level_num == source_level_num:
                move_type = 'Lateral - Same_Role_Same_Level'  # Different pay bands
            elif source_base_title != target_base_title and target_level_num > source_level_num:
                move_type = 'Progression - Different_Role_Higher_Level'
            elif source_base_title != target_base_title and target_level_num == source_level_num:
                move_type = 'Lateral - Different_Role_Same_Level'
            elif target_level_num < source_level_num:
                move_type = 'Transition - Lower_Level'  # Could be strategic move
            else:
                move_type = 'Other'
            
            # Create level transition description with business context
            level_transition = f"{source_level} → {target_level}"
            level_transition_display = f"{level_transition} ({source_base_title} → {target_base_title})"
            
            # For logical roles, focus on the role type rather than organizational function
            if source_base_title != target_base_title:
                context_description = f"Strategic transition opportunity from {source_base_title.lower()} to {target_base_title.lower()}"
            else:
                context_description = f"Career progression within {source_base_title.lower()} role track"
            
            # Get business-friendly display name for move type
            move_type_displays = {
                "Progression - Same_Role_Higher_Level": "Direct Progression (Same Role, Higher Level)",
                "Progression - Different_Role_Higher_Level": "Career Advancement (Different Role, Higher Level)",
                "Lateral - Different_Role_Same_Level": "Lateral Transition (Different Role, Same Level)",
                "Lateral - Same_Role_Same_Level": "Role Optimisation (Same Role, Same Level)",
                "Transition - Lower_Level": "Strategic Repositioning (Lower Level)",
                "Other": "Strategic Transition (Other)"
            }
            move_type_display = move_type_displays.get(move_type, "Strategic Transition")
            
            return {
                'move_type': move_type,
                'move_type_display': move_type_display,
                'level_transition': level_transition,
                'level_transition_display': level_transition_display,
                'strategic_context_explanation': context_description,
                'source_function': source_function,
                'target_function': target_function
            }
            
        except Exception as e:
            print(f"⚠️ Error calculating move type: {e}")
            return {
                'move_type': 'Other',
                'move_type_display': 'Strategic Transition',
                'level_transition': 'Analysis not available',
                'level_transition_display': 'Analysis not available',
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

    def _calculate_strategic_value(self, enhanced_similarity_score: float, 
                                  shared_defining_skills_count: int, 
                                  rarity_weighted_score: float) -> str:
        """Calculate strategic value assessment based on V2 analytics."""
        try:
            # Normalize scores for calculation
            enhanced_score = enhanced_similarity_score or 0
            defining_skills = shared_defining_skills_count or 0
            rarity_score = rarity_weighted_score or 0
            
            # Strategic value algorithm
            strategic_score = (enhanced_score * 0.4) + (min(defining_skills / 5, 1) * 0.3) + (rarity_score * 0.3)
            
            if strategic_score >= 0.7:
                return 'Exceptional'
            elif strategic_score >= 0.5:
                return 'High'
            elif strategic_score >= 0.3:
                return 'Moderate'
            else:
                return 'Developing'
                
        except Exception:
            return 'Standard'

# Convenience function for easy imports
def get_consistent_pathways(db_connection, job_from: str, limit: int = 3, executive_refs: bool = True, 
                          tie_breaking_options: Optional[Dict] = None, similarity_range: Optional[tuple] = None,
                          primary_algorithm: str = 'enhanced', exclude_same_job_id: bool = False, 
                          exclude_same_job_function: bool = False) -> List[Dict]:
    """
    Convenience function to get consistently ordered pathways.
    
    Args:
        db_connection: Database connection
        job_from: Source job ID  
        limit: Number of pathways to return (3 for discovery mode, unlimited for specific transitions)
        executive_refs: If True, use executive summary reference numbering
        tie_breaking_options: Dict of user-controlled tie-breaking preferences
        
    Returns:
        List of consistently ordered pathway dictionaries
    """
    manager = PathwayOrderingManager(db_connection)
    return manager.get_top_pathways_ordered(job_from, limit, executive_refs, tie_breaking_options, similarity_range, primary_algorithm, exclude_same_job_id, exclude_same_job_function)

def get_specific_job_pathways(db_connection, job_from: str, target_job_list: List[str], executive_refs: bool = True) -> List[Dict]:
    """
    Get pathways for specific target jobs with consistent ordering.
    
    Args:
        db_connection: Database connection
        job_from: Source job ID
        target_job_list: List of specific target job IDs to analyze
        executive_refs: If True, use executive summary reference numbering
        
    Returns:
        List of pathway dictionaries for specified target jobs in consistent order
    """
    manager = PathwayOrderingManager(db_connection)
    return manager.get_specific_job_pathways_ordered(job_from, target_job_list, executive_refs) 
