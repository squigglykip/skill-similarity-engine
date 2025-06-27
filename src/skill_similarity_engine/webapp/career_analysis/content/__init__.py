"""
Content generation module for white paper generation.
"""

from .thresholds import ContentThresholds, ContentPersonalizer
from .narratives import NarrativeBuilder
from .variables import VariableManager

__all__ = ["ContentThresholds", "ContentPersonalizer", "NarrativeBuilder", "VariableManager"]
