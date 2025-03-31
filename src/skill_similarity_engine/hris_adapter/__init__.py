#!/usr/bin/env python3
"""
HRIS Adapter Package for the Skill Similarity Engine.

This package provides functionality for transforming data from external HRIS systems
into the format required by the Skill Similarity Engine. It allows for flexible mapping
of schemas between different HRIS systems and our internal data model.
"""

from .transformer import HRISTransformer
from .config import HRISConfigLoader
from .workflow import HRISWorkflow, hris_workflow

__all__ = ["HRISTransformer", "HRISConfigLoader", "HRISWorkflow", "hris_workflow"] 