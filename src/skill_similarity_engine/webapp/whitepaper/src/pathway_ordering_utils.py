"""
Pathway Ordering Utilities
Provides consistent pathway ordering for Executive Summary and Pathway Analysis generators.
Ensures that job rankings are identical across all sections of the white paper.
"""

import sqlite3
from typing import Dict, List, Optional

# Import display utilities
try:
    from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat
except ImportError:
    # Handle relative imports when running from within the whitepaper directory
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent.parent.parent
    sys.path.insert(0, str(src_path))
    from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat

class PathwayOrderingManager:
    """Centralized manager for consistent pathway ordering across white paper generators."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.display_manager = JobDisplayManager(db_connection) if JobDisplayManager else None
        
    def get_top_pathways_ordered(self, job_from: str, limit: int = 3, executive_refs: bool = True) -> List[Dict]:
        """
        Get top similarity pathways with consistent ordering for all white paper sections.
        
        Args:
            job_from: Source job ID
            limit: Number of pathways to return (default 3 for discovery mode, but can be unlimited for specific transitions)
            executive_refs: If True, use executive summary reference numbering; if False, use pathway analysis refs
            
        Returns:
            List of pathway dictionaries with consistent ordering and complete metadata
        """
        try:
            # Use deterministic ordering with consistent SQL query
            query = """
            SELECT 
                js.job_to,
                js.similarity_score,
                j.JobProfile as target_job_title,
                j.JobFunction as target_job_function,
                j.ManagementLevel as target_management_level,
                ROW_NUMBER() OVER (ORDER BY js.similarity_score DESC, js.job_to ASC) as rank
            FROM job_similarities js
            JOIN jobs j ON js.job_to = j.JobProfileID
            WHERE js.job_from = ?
              AND js.similarity_score < 1.0  -- Exclude 100% matches
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
            print(f"⚠️ Error getting ordered pathways: {e}")
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
            FROM job_similarities js
            JOIN jobs j ON js.job_to = j.JobProfileID
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
            FROM jobs 
            WHERE JobProfileID = ?
            """
            source_result = self.db.execute(source_query, (job_from,)).fetchone()
            
            if not source_result:
                return {
                    'move_type': 'Other',
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
            
            return {
                'move_type': move_type,
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

# Convenience function for easy imports
def get_consistent_pathways(db_connection, job_from: str, limit: int = 3, executive_refs: bool = True) -> List[Dict]:
    """
    Convenience function to get consistently ordered pathways.
    
    Args:
        db_connection: Database connection
        job_from: Source job ID  
        limit: Number of pathways to return (3 for discovery mode, unlimited for specific transitions)
        executive_refs: If True, use executive summary reference numbering
        
    Returns:
        List of consistently ordered pathway dictionaries
    """
    manager = PathwayOrderingManager(db_connection)
    return manager.get_top_pathways_ordered(job_from, limit, executive_refs)

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