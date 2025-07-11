"""
Workflows Module for Skill Similarity Engine

This module provides workflow orchestrators that coordinate complex multi-step
operations following SSE's architectural patterns and the Orchestrator pattern.
"""

from .base_workflow import BaseWorkflow, WorkflowResult, WorkflowStep
from .session_manager import SessionManager, get_session_manager, get_current_session, is_data_loaded

__all__ = [
    # Base classes
    'BaseWorkflow',
    'WorkflowResult', 
    'WorkflowStep',
    
    # Session management
    'SessionManager',
    'get_session_manager',
    'get_current_session', 
    'is_data_loaded',
] 