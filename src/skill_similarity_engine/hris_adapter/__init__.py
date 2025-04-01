#!/usr/bin/env python3
"""
HRIS Adapter Package

This package provides functionality to adapt data from various HRIS systems to be used with 
the Skill Similarity Engine.
"""

# Import the classes but not anything that will trigger complex imports
from .transformer import HRISTransformerError

# Define what's available from this package
__all__ = [
    'HRISTransformerError',
    'HRISTransformer',  # Will be imported later
    'HRISWorkflow',     # Will be imported later
    'create_workflow'   # Will be imported later
]

# Import more complex items after defining __all__
from .transformer import HRISTransformer
from .workflow import HRISWorkflow, create_workflow 