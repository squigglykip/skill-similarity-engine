"""
Models for representing skills and skill taxonomies in the skill similarity engine.

This module defines the data structures for representing skills, skill categories,
and skill taxonomies in a hierarchical structure.
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


class SkillType(Enum):
    """Types of skills in the taxonomy."""
    COMMON = auto()
    SPECIALIZED = auto()
    CERTIFICATION = auto()
    
    @classmethod
    def from_string(cls, type_str: str) -> 'SkillType':
        """
        Convert a string representation to a SkillType enum value.
        
        Args:
            type_str: String representation of skill type
            
        Returns:
            Corresponding SkillType enum value
            
        Raises:
            ValueError: If the string doesn't match any known skill type
        """
        # Handle the case where the full enum is provided (e.g., "SkillType.SPECIALIZED")
        if isinstance(type_str, str) and type_str.startswith("SkillType."):
            # Extract the part after "SkillType."
            type_str = type_str.split(".", 1)[1]
        
        # Direct enum name match (case-insensitive)
        if isinstance(type_str, str) and type_str.upper() in ["COMMON", "SPECIALIZED", "CERTIFICATION"]:
            return getattr(cls, type_str.upper())
        
        type_map = {
            "common": cls.COMMON,
            "common skill": cls.COMMON,
            "specialized": cls.SPECIALIZED,
            "specialized skill": cls.SPECIALIZED,
            "certification": cls.CERTIFICATION,
            # Map legacy types to appropriate new types
            "technical": cls.SPECIALIZED,
            "soft": cls.COMMON,
            "domain": cls.SPECIALIZED,
            "methodology": cls.SPECIALIZED,
            "tool": cls.SPECIALIZED,
        }
        
        normalized_type = type_str.lower().strip()
        if normalized_type in type_map:
            return type_map[normalized_type]
        
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
        """Validate the category attributes after initialization."""
        if not self.category_id:
            raise ValueError("Category ID cannot be empty")
        
        if not self.name:
            raise ValueError("Category name cannot be empty")


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
        """Validate the skill attributes after initialization."""
        if not self.skill_id:
            raise ValueError("Skill ID cannot be empty")
        
        if not self.name:
            raise ValueError("Skill name cannot be empty")
        
        # Convert string skill type to enum if needed
        if isinstance(self.skill_type, str):
            try:
                print(f"Converting skill type for {self.skill_id}: '{self.skill_type}' to enum")
                self.skill_type = SkillType.from_string(self.skill_type)
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
        Check if this skill matches a search query.
        
        Args:
            query: Search query to match against
            
        Returns:
            True if the skill's name, description, or aliases match the query
        """
        query = query.lower()
        return (
            query in self.name.lower() or
            query in self.description.lower() or
            any(query in alias.lower() for alias in self.aliases)
        )


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
        Create a taxonomy from a file.
        
        Args:
            file_path: Path to the file containing skill data
            
        Returns:
            SkillTaxonomy object populated with skills from the file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        # Create empty taxonomy
        taxonomy = cls()
        
        # Determine file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            # Load from CSV file
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
                
                # Check if skill ID already exists in taxonomy
                if skill.skill_id in taxonomy.skills:
                    # Handle duplicate by keeping the first occurrence and logging 
                    duplicate_count += 1
                    # For debugging, can be removed in production
                    existing_skill = taxonomy.skills[skill.skill_id]
                    print(f"Warning: Duplicate skill ID {skill.skill_id} found. "
                          f"Original: {existing_skill.name} ({existing_skill.skill_type}), "
                          f"Duplicate: {skill.name} ({skill.skill_type})")
                else:
                    # Add skill to taxonomy
                    taxonomy.add_skill(skill)
            
            if duplicate_count > 0:
                print(f"Warning: {duplicate_count} duplicate skill IDs were found and skipped.")
                
        elif file_ext == '.json':
            # Load from JSON file
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
                    
                    # Check for duplicates
                    if skill.skill_id in taxonomy.skills:
                        # Log duplicate but don't add again
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
                    
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        return taxonomy
    
    @classmethod
    def _parse_list_field(cls, row, field_name):
        """
        Parse a list field from a DataFrame row using field mapping.
        
        Args:
            row: DataFrame row
            field_name: Canonical field name to parse
            
        Returns:
            List of values
        """
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
            
        # If string, parse based on delimiters
        if isinstance(value, str):
            if ',' in value:
                return [item.strip() for item in value.split(',') if item.strip()]
            elif ';' in value:
                return [item.strip() for item in value.split(';') if item.strip()]
            else:
                # Single value
                return [value.strip()]
                
        # If other type, convert to string and return as single item
        return [str(value)] 