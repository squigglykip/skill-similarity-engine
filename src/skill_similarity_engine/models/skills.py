"""
Models for representing skills and skill taxonomies in the skill similarity engine.

This module defines the data structures for representing skills, skill categories,
and skill taxonomies in a hierarchical structure.

Architecture: Configuration-driven with ZERO hardcoded values
All skill type mappings and field parsing externalized to architectural configuration.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import os
import pandas as pd
import json
import logging

# Import field mapping utilities
from ..config.field_mapping import get_field_mapper, get_raw_field_name
from ..config.architectural_config_manager import get_config_manager


class SkillType(Enum):
    """Types of skills in the taxonomy."""
    COMMON = auto()
    SPECIALIZED = auto()
    CERTIFICATION = auto()
    
    @classmethod
    def from_string(cls, type_str: str) -> 'SkillType':
        """
        Convert a string representation to a SkillType enum value using configured mappings.
        
        Args:
            type_str: String representation of skill type
            
        Returns:
            Corresponding SkillType enum value
            
        Raises:
            ValueError: If the string doesn't match any known skill type
        """
        # Get configured skill type mappings - NO hardcoded mappings
        config_manager = get_config_manager()
        skill_types_config = config_manager.get_skill_types_config()
        
        # Get mapping configuration with defaults
        type_mappings = skill_types_config.get('type_mappings', {})
        default_type = skill_types_config.get('default_type', 'COMMON')
        fallback_enabled = skill_types_config.get('enable_fallback', True)
        case_sensitive = skill_types_config.get('case_sensitive', False)
        handle_nan_values = skill_types_config.get('handle_nan_values', True)
        enum_prefix_handling = skill_types_config.get('enum_prefix_handling', True)
        
        # Handle None, NaN, or empty values using configuration
        if handle_nan_values and (type_str is None or (hasattr(type_str, '__iter__') and not isinstance(type_str, str)) or str(type_str).lower() in ['nan', '', 'none']):
            return getattr(cls, default_type)
        
        # Convert to string if not already
        type_str = str(type_str)
        
        # Handle the case where the full enum is provided using configuration
        if enum_prefix_handling and type_str.startswith("SkillType."):
            # Extract the part after "SkillType."
            type_str = type_str.split(".", 1)[1]
        
        # Direct enum name match (case handling based on configuration)
        enum_names = ["COMMON", "SPECIALIZED", "CERTIFICATION"]
        comparison_str = type_str if case_sensitive else type_str.upper()
        if comparison_str in enum_names:
            return getattr(cls, comparison_str if case_sensitive else comparison_str.upper())
        
        # Use configured type mappings instead of hardcoded ones
        normalized_type = type_str if case_sensitive else type_str.lower().strip()
        if normalized_type in type_mappings:
            return getattr(cls, type_mappings[normalized_type])
        
        # If we still can't match and fallback is enabled, use default type
        if fallback_enabled:
            return getattr(cls, default_type)
        else:
            raise ValueError(f"Unknown skill type: {type_str}")


@dataclass
class SkillCategory:
    """
    Represents a category of skills in the taxonomy.
    
    Attributes:
        category_id: Unique identifier for the category
        name: Display name for the category
        parent_id: ID of the parent category (None for top-level categories)
        description: Optional description of the category
    """
    category_id: str
    name: str
    parent_id: Optional[str] = None
    description: str = ""
    
    def __post_init__(self):
        """Validate the category attributes after initialization using configured validation."""
        # Get validation configuration - NO hardcoded validation rules
        config_manager = get_config_manager()
        validation_config = config_manager.get_models_validation_config()
        
        # Validate category attributes based on configuration
        category_validation = validation_config.get('category_validation', {})
        require_category_id = category_validation.get('require_category_id', True)
        require_category_name = category_validation.get('require_category_name', True)
        min_category_id_length = category_validation.get('min_category_id_length', 1)
        min_category_name_length = category_validation.get('min_category_name_length', 1)
        
        if require_category_id and (not self.category_id or len(self.category_id) < min_category_id_length):
            raise ValueError(f"Category ID cannot be empty or shorter than {min_category_id_length} characters")
        
        if require_category_name and (not self.name or len(self.name) < min_category_name_length):
            raise ValueError(f"Category name cannot be empty or shorter than {min_category_name_length} characters")


@dataclass
class Skill:
    """
    Represents a skill in the skill taxonomy.
    
    Attributes:
        skill_id: Unique identifier for the skill
        name: Display name for the skill
        description: Detailed description of the skill
        category_id: ID of the category this skill belongs to
        skill_type: Type of skill (technical, soft, etc.)
        aliases: Alternative names for the skill
        related_skills: IDs of related skills
        prerequisites: IDs of skills that are prerequisites for this skill
    """
    skill_id: str
    name: str
    description: str = ""
    category_id: Optional[str] = None
    skill_type: SkillType = SkillType.COMMON
    aliases: List[str] = field(default_factory=list)
    related_skills: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the skill attributes after initialization using configured validation."""
        # Get validation configuration - NO hardcoded validation rules
        config_manager = get_config_manager()
        validation_config = config_manager.get_models_validation_config()
        
        # Validate skill attributes based on configuration
        skill_validation = validation_config.get('skill_validation', {})
        require_skill_id = skill_validation.get('require_skill_id', True)
        require_skill_name = skill_validation.get('require_skill_name', True)
        min_skill_id_length = skill_validation.get('min_skill_id_length', 1)
        min_skill_name_length = skill_validation.get('min_skill_name_length', 1)
        debug_skill_type_conversion = skill_validation.get('debug_skill_type_conversion', False)
        
        if require_skill_id and (not self.skill_id or len(self.skill_id) < min_skill_id_length):
            raise ValueError(f"Skill ID cannot be empty or shorter than {min_skill_id_length} characters")
        
        if require_skill_name and (not self.name or len(self.name) < min_skill_name_length):
            raise ValueError(f"Skill name cannot be empty or shorter than {min_skill_name_length} characters")
        
        # Convert string skill type to enum if needed
        if isinstance(self.skill_type, str):
            try:
                if debug_skill_type_conversion:
                    print(f"Converting skill type for {self.skill_id}: '{self.skill_type}' to enum")
                self.skill_type = SkillType.from_string(self.skill_type)
                if debug_skill_type_conversion:
                    print(f"  Result: {self.skill_type}")
            except ValueError as e:
                raise ValueError(f"Invalid skill type for {self.name}: {e}")
    
    def add_alias(self, alias: str) -> None:
        """
        Add an alias for this skill.
        
        Args:
            alias: Alternative name for the skill
        """
        if alias and alias not in self.aliases:
            self.aliases.append(alias)
    
    def add_related_skill(self, skill_id: str) -> None:
        """
        Add a related skill to this skill.
        
        Args:
            skill_id: ID of the related skill
        """
        if skill_id and skill_id not in self.related_skills:
            self.related_skills.append(skill_id)
    
    def add_prerequisite(self, skill_id: str) -> None:
        """
        Add a prerequisite skill for this skill.
        
        Args:
            skill_id: ID of the prerequisite skill
        """
        if skill_id and skill_id not in self.prerequisites:
            self.prerequisites.append(skill_id)
    
    def matches(self, query: str) -> bool:
        """
        Check if this skill matches a search query using configured search settings.
        
        Args:
            query: Search query to match against
            
        Returns:
            True if the skill's name, description, or aliases match the query
        """
        # Get search configuration - NO hardcoded search behavior
        config_manager = get_config_manager()
        skill_search_config = config_manager.get_models_skills_taxonomy_config().get('search', {})
        
        case_sensitive = skill_search_config.get('case_sensitive', False)
        search_aliases = skill_search_config.get('search_aliases', True)
        search_description = skill_search_config.get('search_description', True)
        search_name = skill_search_config.get('search_name', True)
        
        # Apply case sensitivity configuration
        if case_sensitive:
            query_comp = query
            name_comp = self.name
            description_comp = self.description
            alias_comp = self.aliases
        else:
            query_comp = query.lower()
            name_comp = self.name.lower()
            description_comp = self.description.lower()
            alias_comp = [alias.lower() for alias in self.aliases]
        
        # Check configured search fields
        matches = False
        if search_name:
            matches = matches or (query_comp in name_comp)
        if search_description:
            matches = matches or (query_comp in description_comp)
        if search_aliases:
            matches = matches or any(query_comp in alias for alias in alias_comp)
        
        return matches


@dataclass
class SkillTaxonomy:
    """
    Represents a hierarchical taxonomy of skills.
    
    Attributes:
        skills: Dictionary of skills indexed by skill_id
        categories: Dictionary of categories indexed by category_id
        skills_by_category: Dictionary mapping category IDs to sets of skill IDs
        category_hierarchy: Dictionary mapping parent category IDs to sets of child category IDs
    """
    skills: Dict[str, Skill] = field(default_factory=dict)
    categories: Dict[str, SkillCategory] = field(default_factory=dict)
    skills_by_category: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    category_hierarchy: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    
    def add_skill(self, skill: Skill) -> None:
        """
        Add a skill to the taxonomy.
        
        Args:
            skill: The skill to add
            
        Raises:
            ValueError: If a skill with the same ID already exists
        """
        if skill.skill_id in self.skills:
            raise ValueError(f"Skill with ID {skill.skill_id} already exists")
        
        self.skills[skill.skill_id] = skill
        
        # Update skills_by_category
        if skill.category_id:
            if skill.category_id not in self.skills_by_category:
                self.skills_by_category[skill.category_id] = set()
            
            self.skills_by_category[skill.category_id].add(skill.skill_id)
    
    def add_category(self, category: SkillCategory) -> None:
        """
        Add a category to the taxonomy.
        
        Args:
            category: The category to add
            
        Raises:
            ValueError: If a category with the same ID already exists
        """
        if category.category_id in self.categories:
            raise ValueError(f"Category with ID {category.category_id} already exists")
        
        self.categories[category.category_id] = category
        
        # Update category hierarchy
        if category.parent_id:
            if category.parent_id not in self.category_hierarchy:
                self.category_hierarchy[category.parent_id] = set()
            
            self.category_hierarchy[category.parent_id].add(category.category_id)
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """
        Retrieve a skill by ID.
        
        Args:
            skill_id: The ID of the skill to retrieve
            
        Returns:
            The skill if found, None otherwise
        """
        return self.skills.get(skill_id)
    
    def get_category(self, category_id: str) -> Optional[SkillCategory]:
        """
        Retrieve a category by ID.
        
        Args:
            category_id: The ID of the category to retrieve
            
        Returns:
            The category if found, None otherwise
        """
        return self.categories.get(category_id)
    
    def get_skills_in_category(self, category_id: str, include_subcategories: bool = True) -> List[Skill]:
        """
        Retrieve all skills in a specific category.
        
        Args:
            category_id: The ID of the category to filter by
            include_subcategories: Whether to include skills from subcategories
            
        Returns:
            A list of skills in the specified category
        """
        result = []
        
        # Add skills directly in the category
        for skill_id in self.skills_by_category.get(category_id, set()):
            skill = self.skills.get(skill_id)
            if skill:
                result.append(skill)
        
        # Recursively add skills from subcategories if requested
        if include_subcategories:
            for subcategory_id in self.category_hierarchy.get(category_id, set()):
                result.extend(self.get_skills_in_category(subcategory_id, True))
        
        return result
    
    def get_subcategories(self, category_id: str, recursive: bool = False) -> List[SkillCategory]:
        """
        Retrieve all subcategories of a specific category.
        
        Args:
            category_id: The ID of the parent category
            recursive: Whether to include all descendants
            
        Returns:
            A list of subcategories
        """
        result = []
        
        # Add direct subcategories
        for subcategory_id in self.category_hierarchy.get(category_id, set()):
            subcategory = self.categories.get(subcategory_id)
            if subcategory:
                result.append(subcategory)
                
                # Recursively add descendants if requested
                if recursive:
                    result.extend(self.get_subcategories(subcategory_id, True))
        
        return result
    
    def get_category_path(self, category_id: str) -> List[SkillCategory]:
        """
        Get the path from the root category to the specified category.
        
        Args:
            category_id: The ID of the category to get the path for
            
        Returns:
            A list of categories from root to the specified category
        """
        result = []
        current_id = category_id
        
        # Build the path from the category to the root
        while current_id:
            category = self.categories.get(current_id)
            if not category:
                break
            
            result.append(category)
            current_id = category.parent_id
        
        # Reverse to get path from root to category
        return list(reversed(result))
    
    def search_skills(self, query: str) -> List[Skill]:
        """
        Search for skills matching a query.
        
        Args:
            query: The search query
            
        Returns:
            A list of skills matching the query
        """
        return [skill for skill in self.skills.values() if skill.matches(query)]
    
    def get_related_skills(self, skill_id: str, depth: int = 1) -> List[Skill]:
        """
        Get skills related to the specified skill.
        
        Args:
            skill_id: The ID of the skill to get related skills for
            depth: How many degrees of separation to include
            
        Returns:
            A list of related skills
        """
        if depth < 1:
            return []
        
        skill = self.skills.get(skill_id)
        if not skill:
            return []
        
        # Get directly related skills
        related_skill_ids = set(skill.related_skills)
        result = [self.skills[related_id] for related_id in related_skill_ids if related_id in self.skills]
        
        # Recursively get related skills up to specified depth
        if depth > 1:
            for related_id in related_skill_ids:
                deeper_related = self.get_related_skills(related_id, depth - 1)
                result.extend(deeper_related)
        
        return result
    
    def get_prerequisite_chain(self, skill_id: str) -> List[List[Skill]]:
        """
        Get the prerequisite chains for a skill.
        
        Args:
            skill_id: The ID of the skill to get prerequisites for
            
        Returns:
            A list of prerequisite chains (each chain is a list of skills)
        """
        skill = self.skills.get(skill_id)
        if not skill or not skill.prerequisites:
            return []
        
        result = []
        
        # Process each direct prerequisite
        for prereq_id in skill.prerequisites:
            prereq = self.skills.get(prereq_id)
            if not prereq:
                continue
            
            # Get prerequisite chains for this prerequisite
            prereq_chains = self.get_prerequisite_chain(prereq_id)
            
            if not prereq_chains:
                # If there are no deeper prerequisites, add this as a chain
                result.append([prereq])
            else:
                # Add this prerequisite to each of its prerequisite chains
                for chain in prereq_chains:
                    result.append(chain + [prereq])
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SkillTaxonomy':
        """
        Create a skill taxonomy from a dictionary representation.
        
        Args:
            data: Dictionary containing skill and category data
            
        Returns:
            A new SkillTaxonomy instance
        """
        taxonomy = cls()
        
        # Add categories first
        for category_data in data.get("categories", []):
            category = SkillCategory(
                category_id=category_data["category_id"],
                name=category_data["name"],
                parent_id=category_data.get("parent_id"),
                description=category_data.get("description", "")
            )
            taxonomy.add_category(category)
        
        # Then add skills
        for skill_data in data.get("skills", []):
            # Convert skill type if present
            skill_type = skill_data.get("skill_type", SkillType.COMMON)
            if isinstance(skill_type, str):
                skill_type = SkillType.from_string(skill_type)
            
            skill = Skill(
                skill_id=skill_data["skill_id"],
                name=skill_data["name"],
                description=skill_data.get("description", ""),
                category_id=skill_data.get("category_id"),
                skill_type=skill_type,
                aliases=skill_data.get("aliases", []),
                related_skills=skill_data.get("related_skills", []),
                prerequisites=skill_data.get("prerequisites", [])
            )
            taxonomy.add_skill(skill)
        
        return taxonomy
    
    def to_dict(self) -> Dict:
        """
        Convert the skill taxonomy to a dictionary representation.
        
        Returns:
            A dictionary representation of the taxonomy
        """
        return {
            "categories": [
                {
                    "category_id": category.category_id,
                    "name": category.name,
                    "parent_id": category.parent_id,
                    "description": category.description
                }
                for category in self.categories.values()
            ],
            "skills": [
                {
                    "skill_id": skill.skill_id,
                    "name": skill.name,
                    "description": skill.description,
                    "category_id": skill.category_id,
                    "skill_type": skill.skill_type.name,
                    "aliases": skill.aliases,
                    "related_skills": skill.related_skills,
                    "prerequisites": skill.prerequisites
                }
                for skill in self.skills.values()
            ]
        }
    
    @classmethod
    def from_file(cls, file_path: str) -> 'SkillTaxonomy':
        """
        Create a taxonomy from a file using configured settings.
        
        Args:
            file_path: Path to the file containing skill data
            
        Returns:
            SkillTaxonomy object populated with skills from the file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        # Get file loading configuration - NO hardcoded file handling behavior
        config_manager = get_config_manager()
        file_loading_config = config_manager.get_models_skills_taxonomy_config().get('file_loading', {})
        
        supported_formats = file_loading_config.get('supported_formats', ['.csv', '.json'])
        duplicate_handling = file_loading_config.get('duplicate_handling', 'skip_with_warning')
        debug_duplicates = file_loading_config.get('debug_duplicates', False)
        
        # Create empty taxonomy
        taxonomy = cls()
        
        # Determine file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: {supported_formats}")
        
        if file_ext == '.csv':
            # Load from CSV file using configured field handling
            df = pd.read_csv(file_path)
            
            # Use field mapping to get the required column names
            skill_id_field = get_raw_field_name('skill_id', 'skills')
            name_field = get_raw_field_name('name', 'skills')
            
            # Check if the necessary columns are present (using mapped field names)
            required_columns = [skill_id_field, name_field]
            for column in required_columns:
                if column not in df.columns:
                    # Try legacy/canonical names as fallback
                    if column == skill_id_field and 'skill_id' in df.columns:
                        continue  # Will handle in row parsing
                    elif column == name_field and 'name' in df.columns:
                        continue  # Will handle in row parsing
                    else:
                        raise ValueError(f"CSV file is missing required column: {column} (mapped from canonical field)")
            
            # Load skills from DataFrame
            duplicate_count = 0
            for _, row in df.iterrows():
                # Parse lists from strings if present as strings using field mapping
                aliases = cls._parse_list_field(row, 'aliases')
                related_skills = cls._parse_list_field(row, 'related_skills')
                prerequisites = cls._parse_list_field(row, 'prerequisites')
                
                # Use field mapping for core fields
                skill_id_field = get_raw_field_name('skill_id', 'skills')
                name_field = get_raw_field_name('name', 'skills')
                description_field = get_raw_field_name('description', 'skills')
                category_id_field = get_raw_field_name('category_id', 'skills')
                skill_type_field = get_raw_field_name('skill_type', 'skills')
                
                # Extract values using mapped field names with fallbacks
                skill_id = None
                if skill_id_field in row and pd.notna(row[skill_id_field]):
                    skill_id = str(row[skill_id_field])
                elif 'skill_id' in row and pd.notna(row['skill_id']):
                    skill_id = str(row['skill_id'])  # Legacy fallback
                    
                name = None
                if name_field in row and pd.notna(row[name_field]):
                    name = row[name_field]
                elif 'name' in row and pd.notna(row['name']):
                    name = row['name']  # Legacy fallback
                    
                description = ""
                if description_field in row and pd.notna(row[description_field]):
                    description = row[description_field]
                elif 'description' in row and pd.notna(row['description']):
                    description = row['description']  # Legacy fallback
                    
                category_id = None
                if category_id_field in row and pd.notna(row[category_id_field]):
                    category_id = str(row[category_id_field])
                elif 'category_id' in row and pd.notna(row['category_id']):
                    category_id = str(row['category_id'])  # Legacy fallback
                    
                skill_type = SkillType.COMMON  # Default
                if skill_type_field in row and pd.notna(row[skill_type_field]):
                    skill_type = row[skill_type_field]
                elif 'skill_type' in row and pd.notna(row['skill_type']):
                    skill_type = row['skill_type']  # Legacy fallback
                
                if not skill_id or not name:
                    continue  # Skip rows with missing required fields
                
                # Create skill
                skill = Skill(
                    skill_id=skill_id,
                    name=name,
                    description=description,
                    category_id=category_id,
                    skill_type=skill_type,
                    aliases=aliases,
                    related_skills=related_skills,
                    prerequisites=prerequisites
                )
                
                # Check if skill ID already exists in taxonomy using configured duplicate handling
                if skill.skill_id in taxonomy.skills:
                    duplicate_count += 1
                    if duplicate_handling == 'skip_with_warning' or debug_duplicates:
                        existing_skill = taxonomy.skills[skill.skill_id]
                        print(f"Warning: Duplicate skill ID {skill.skill_id} found. "
                              f"Original: {existing_skill.name} ({existing_skill.skill_type}), "
                              f"Duplicate: {skill.name} ({skill.skill_type})")
                    # Skip duplicate regardless of debug setting
                else:
                    # Add skill to taxonomy
                    taxonomy.add_skill(skill)
            
            if duplicate_count > 0 and duplicate_handling in ['skip_with_warning', 'warn']:
                print(f"Warning: {duplicate_count} duplicate skill IDs were found and skipped.")
                
        elif file_ext == '.json':
            # Load from JSON file using configured settings
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Load skills
            if 'skills' in data:
                for skill_data in data['skills']:
                    skill = Skill(
                        skill_id=str(skill_data['skill_id']),
                        name=skill_data['name'],
                        description=skill_data.get('description', ''),
                        category_id=str(skill_data['category_id']) if 'category_id' in skill_data else None,
                        skill_type=skill_data.get('skill_type', SkillType.COMMON),
                        aliases=skill_data.get('aliases', []),
                        related_skills=skill_data.get('related_skills', []),
                        prerequisites=skill_data.get('prerequisites', [])
                    )
                    
                    # Check for duplicates using configured handling
                    if skill.skill_id in taxonomy.skills:
                        if duplicate_handling in ['skip_with_warning', 'warn']:
                            print(f"Warning: Duplicate skill ID {skill.skill_id} found in JSON - keeping first occurrence")
                    else:
                        taxonomy.add_skill(skill)
            
            # Load categories
            if 'categories' in data:
                for category_data in data['categories']:
                    category = SkillCategory(
                        category_id=str(category_data['category_id']),
                        name=category_data['name'],
                        parent_id=str(category_data['parent_id']) if 'parent_id' in category_data else None,
                        description=category_data.get('description', '')
                    )
                    taxonomy.add_category(category)
        
        return taxonomy
    
    @classmethod
    def _parse_list_field(cls, row, field_name):
        """
        Parse a list field from a DataFrame row using field mapping and configured delimiters.
        
        Args:
            row: DataFrame row
            field_name: Canonical field name to parse
            
        Returns:
            List of values
        """
        # Get list parsing configuration - NO hardcoded delimiters
        config_manager = get_config_manager()
        parsing_config = config_manager.get_models_skills_taxonomy_config().get('list_parsing', {})
        
        primary_delimiter = parsing_config.get('primary_delimiter', ',')
        secondary_delimiter = parsing_config.get('secondary_delimiter', ';')
        strip_whitespace = parsing_config.get('strip_whitespace', True)
        
        # Get the raw field name using field mapping
        raw_field_name = get_raw_field_name(field_name, 'skills')
        
        # Check mapped field name first, then fallback to canonical name
        if raw_field_name in row and pd.notna(row[raw_field_name]):
            value = row[raw_field_name]
        elif field_name in row and pd.notna(row[field_name]):
            value = row[field_name]  # Legacy fallback to canonical name
        else:
            return []
            
        # If already a list, return it
        if isinstance(value, list):
            return value
            
        # If string, parse based on configured delimiters
        if isinstance(value, str):
            if primary_delimiter in value:
                items = value.split(primary_delimiter)
            elif secondary_delimiter in value:
                items = value.split(secondary_delimiter)
            else:
                # Single value
                items = [value]
            
            # Apply whitespace stripping if configured
            if strip_whitespace:
                return [item.strip() for item in items if item.strip()]
            else:
                return [item for item in items if item]
                
        # If other type, convert to string and return as single item
        return [str(value)] 
