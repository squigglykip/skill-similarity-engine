"""
Models for representing skills and skill taxonomies in the skill similarity engine.

This module defines the data structures for representing skills, skill categories,
and skill taxonomies in a hierarchical structure.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


class SkillType(Enum):
    """Types of skills in the taxonomy."""
    TECHNICAL = auto()
    SOFT = auto()
    DOMAIN = auto()
    METHODOLOGY = auto()
    TOOL = auto()
    CERTIFICATION = auto()
    OTHER = auto()
    
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
        type_map = {
            "technical": cls.TECHNICAL,
            "soft": cls.SOFT,
            "domain": cls.DOMAIN,
            "methodology": cls.METHODOLOGY,
            "tool": cls.TOOL,
            "certification": cls.CERTIFICATION,
            "other": cls.OTHER
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
    skill_type: SkillType = SkillType.OTHER
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
                self.skill_type = SkillType.from_string(self.skill_type)
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
    skills_by_category: Dict[str, Set[str]] = field(default_factory=lambda: Dict[str, Set[str]]())
    category_hierarchy: Dict[str, Set[str]] = field(default_factory=lambda: Dict[str, Set[str]]())
    
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
            skill_type = skill_data.get("skill_type", SkillType.OTHER)
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