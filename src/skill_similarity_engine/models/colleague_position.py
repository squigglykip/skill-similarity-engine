"""
Core ColleaguePosition data model for movement tracking.

Ported from Position Transition History (PTH) to Skill Similarity Engine (SSE).
This is the critical dataset that tracks colleague positions over time.
The movement detection logic depends entirely on this model.

Architecture: Enterprise OOP with Configuration-Driven Field Mapping
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
import logging

from ..config.workforce_config_loader import get_workforce_config_loader

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class ColleaguePosition:
    """
    Represents a colleague's position at a specific point in time.
    
    This is the core building block for movement detection - any change
    in Position Number for the same Employee Number represents movement.
    
    Data Types from Production (SSE Integration):
    - Week Ending: DD/MM/YYYY string (e.g. "30/04/2020")
    - Employee Number: int64 (e.g. 21091693)
    - Operational: "TRUE"/"FALSE" string converted to bool
    - Position Start Date: DD/MM/YYYY string, nullable (e.g. "7/09/2020")
    - PosIDLookupKey: scientific notation string (e.g. "1.36795E+11") - lookup key only
    - Position Number: int (e.g. 65285891) - actual position identifier for movement tracking
    
    Integration Notes:
    - Uses SSE's WorkforceConfigLoader for field mapping
    - Compatible with SSE's data processing pipeline
    - Designed for SSE's precompute strategy integration
    """
    
    # Core identifiers
    pos_id_lookup_key: str
    employee_number: int
    week_ending: Union[date, str]  # Can be date initially, converted to str in __post_init__
    
    # Position details
    position_number: Optional[int] = None
    position_start_date: Optional[Union[date, str]] = None  # Can be date initially, converted to str in __post_init__
    operational: bool = True
    
    # Extended position information (from positions dataset)
    cost_centre_number: Optional[str] = None
    organisational_unit: Optional[str] = None
    position_title: Optional[str] = None
    employment_category: Optional[str] = None
    role_level: Optional[str] = None
    manager_position_number: Optional[int] = None
    
    # SSE Integration fields
    job_profile_id: Optional[str] = None        # Link to SSE job architecture
    skill_similarity_score: Optional[float] = None  # Integration with SSE similarity engine
    
    def __post_init__(self):
        """Validate the core fields required for movement tracking."""
        if not self.employee_number:
            raise ValueError("Employee number is required for movement tracking")
        
        if not self.pos_id_lookup_key:
            raise ValueError("PosIDLookupKey is required for movement tracking")
        
        if not self.week_ending:
            raise ValueError("Week ending date is required for temporal tracking")
        
        # Convert dates to ISO format for SSE compatibility
        if isinstance(self.week_ending, date):
            self.week_ending = self.week_ending.strftime("%Y-%m-%d")
        
        if self.position_start_date and isinstance(self.position_start_date, date):
            self.position_start_date = self.position_start_date.strftime("%Y-%m-%d")
        
        # NOTE: Temporal consistency check removed - in workforce data, position start dates
        # can legitimately be after week ending dates (reporting periods vs actual start dates)
        # This is normal business logic, not a data quality issue.
        
        # REMOVED: Temporal consistency validation that was generating false warnings
        # The original validation was:
        # if (self.position_start_date and self.position_start_date > self.week_ending):
        #     logger.warning(f"Position start date {self.position_start_date} is after week ending {self.week_ending}...")
        
        # This validation was incorrect because:
        # - Week Ending = reporting period (when data was captured)
        # - Position Start Date = when person actually started in position
        # - It's normal for start dates to be after reporting periods in workforce data
    
    @property
    def movement_key(self) -> tuple:
        """
        Generate a key for movement tracking.
        
        Returns:
            Tuple of (employee_number, week_ending) for tracking changes over time
        """
        return (self.employee_number, self.week_ending)
    
    @property
    def position_key(self) -> Optional[int]:
        """
        Get the position identifier for movement detection.
        
        Returns:
            Position Number (actual position) if available, otherwise None
            Records with None position_key should be excluded from movement analysis
        """
        return self.position_number
    
    @property
    def temporal_id(self) -> str:
        """
        Generate a unique temporal identifier for this position record.
        
        Returns:
            String combining employee number and week ending for unique identification
        """
        return f"{self.employee_number}_{self.week_ending}"
    
    def has_moved_from(self, previous_position: 'ColleaguePosition') -> bool:
        """
        Check if this represents a movement from a previous position.
        
        Args:
            previous_position: The previous ColleaguePosition for same employee
            
        Returns:
            True if colleague has moved positions (based on position_number)
        """
        if self.employee_number != previous_position.employee_number:
            raise ValueError("Cannot compare positions for different employees")
        
        return self.position_key != previous_position.position_key
    
    def get_movement_type(self, previous_position: 'ColleaguePosition') -> str:
        """
        Determine the type of movement from a previous position.
        
        Args:
            previous_position: The previous ColleaguePosition for same employee
            
        Returns:
            String describing movement type: 'lateral', 'promotion', 'demotion', 'department_change'
        """
        if not self.has_moved_from(previous_position):
            return 'no_movement'
        
        # Basic movement classification (can be enhanced with org hierarchy)
        if (self.organisational_unit and previous_position.organisational_unit and
            self.organisational_unit != previous_position.organisational_unit):
            return 'department_change'
        
        # Default to lateral move if we can't determine hierarchy
        return 'lateral'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export or analysis."""
        return {
            'Week Ending': self.week_ending,
            'Employee Number': self.employee_number,
            'Operational': self.operational,
            'Position Start Date': self.position_start_date,
            'PosIDLookupKey': self.pos_id_lookup_key,
            'Position Number': self.position_number,
            'Cost Centre Number': self.cost_centre_number,
            'Organisational Unit': self.organisational_unit,
            'Position Title': self.position_title,
            'Employment Category': self.employment_category,
            'Role Level': self.role_level,
            'Manager Position Number': self.manager_position_number,
            'Job Profile ID': self.job_profile_id,
            'Skill Similarity Score': self.skill_similarity_score
        }
    
    def to_parquet_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary optimized for Parquet export (SSE integration).
        
        Returns:
            Dictionary with appropriate data types for Parquet serialization
        """
        return {
            'week_ending': self.week_ending,
            'employee_number': self.employee_number,
            'position_number': self.position_number,
            'pos_id_lookup_key': self.pos_id_lookup_key,
            'operational': self.operational,
            'position_start_date': self.position_start_date,
            'cost_centre_number': self.cost_centre_number,
            'organisational_unit': self.organisational_unit,
            'position_title': self.position_title,
            'employment_category': self.employment_category,
            'role_level': self.role_level,
            'manager_position_number': self.manager_position_number,
            'job_profile_id': self.job_profile_id,
            'skill_similarity_score': self.skill_similarity_score,
            'temporal_id': self.temporal_id,
            'position_key': self.position_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColleaguePosition':
        """
        Create a ColleaguePosition instance from a dictionary with external field names.
        
        Uses SSE's WorkforceConfigLoader to map external field names to internal field names.
        
        Args:
            data: Dictionary containing position data with external field names
            
        Returns:
            ColleaguePosition: New instance created from the data
            
        Raises:
            ValueError: If required fields are missing or invalid
            KeyError: If expected mapped fields are not found
        """
        # Get field mappings from SSE configuration
        config_loader = get_workforce_config_loader()
        field_mappings = config_loader.get_field_mappings('colleague_positions')
        
        # Create a dictionary to map external keys to internal values
        mapped_data = {}
        
        # Map external field names to internal field names
        for external_field, internal_field in field_mappings.items():
            if external_field in data:
                mapped_data[internal_field] = data[external_field]
        
        # Clean and prepare the data
        clean_data = cls._clean_data(mapped_data)
        
        # Extract and convert required fields using internal field names
        pos_id_str = str(clean_data['pos_id_lookup_key'])
        emp_num = int(clean_data['employee_number'])
        
        # Handle operational field - default to True if missing
        operational_str = str(clean_data.get('operational', 'TRUE')).upper()
        operational = operational_str in ['TRUE', 'T', '1', 'YES', 'Y']
        
        # Parse dates using SSE-compatible formats
        week_ending_date = cls._parse_date(clean_data['week_ending'])
        if week_ending_date is None:
            raise ValueError("week_ending is required and cannot be None")
        
        # Handle optional position start date
        pos_start = clean_data.get('position_start_date')
        pos_start_date = cls._parse_date(pos_start) if pos_start else None
        
        # Handle optional position number
        pos_num_str = clean_data.get('position_number')
        pos_num = int(pos_num_str) if pos_num_str and str(pos_num_str).strip() else None
        
        # Handle optional manager position number
        mgr_pos_num_str = clean_data.get('manager_position_number')
        mgr_pos_num = int(mgr_pos_num_str) if mgr_pos_num_str and str(mgr_pos_num_str).strip() else None
        
        return cls(
            pos_id_lookup_key=pos_id_str,
            employee_number=emp_num,
            week_ending=week_ending_date,
            position_number=pos_num,
            position_start_date=pos_start_date,
            operational=operational,
            cost_centre_number=clean_data.get('cost_centre_number'),
            organisational_unit=clean_data.get('organisational_unit'),
            position_title=clean_data.get('position_title'),
            employment_category=clean_data.get('employment_category'),
            role_level=clean_data.get('role_level'),
            manager_position_number=mgr_pos_num,
            job_profile_id=clean_data.get('job_profile_id'),  # SSE integration
        )
    
    @classmethod
    def from_parquet_dict(cls, data: Dict[str, Any]) -> 'ColleaguePosition':
        """
        Create a ColleaguePosition instance from Parquet data (SSE integration).
        
        Args:
            data: Dictionary containing position data in internal format
            
        Returns:
            ColleaguePosition: New instance created from Parquet data
        """
        # Handle dates that might be strings from Parquet
        week_ending = data['week_ending']
        if isinstance(week_ending, str):
            week_ending = cls._parse_date(week_ending)
        
        # Ensure week_ending is not None (required field)
        if week_ending is None:
            raise ValueError("week_ending is required and cannot be None")
        
        position_start_date = data.get('position_start_date')
        if isinstance(position_start_date, str):
            position_start_date = cls._parse_date(position_start_date)
        
        return cls(
            pos_id_lookup_key=str(data['pos_id_lookup_key']),
            employee_number=int(data['employee_number']),
            week_ending=week_ending,
            position_number=data.get('position_number'),
            position_start_date=position_start_date,
            operational=bool(data.get('operational', True)),
            cost_centre_number=data.get('cost_centre_number'),
            organisational_unit=data.get('organisational_unit'),
            position_title=data.get('position_title'),
            employment_category=data.get('employment_category'),
            role_level=data.get('role_level'),
            manager_position_number=data.get('manager_position_number'),
            job_profile_id=data.get('job_profile_id'),
            skill_similarity_score=data.get('skill_similarity_score')
        )
    
    def __str__(self) -> str:
        """Human-readable representation."""
        pos_display = self.position_number if self.position_number else f"Lookup:{self.pos_id_lookup_key}"
        return f"Employee {self.employee_number} in position {pos_display} ({self.week_ending})"
    
    def __eq__(self, other) -> bool:
        """Check equality based on movement key and position."""
        if not isinstance(other, ColleaguePosition):
            return False
        return (self.movement_key == other.movement_key and 
                self.position_key == other.position_key)
    
    def __hash__(self) -> int:
        """Enable use in sets and as dict keys."""
        return hash((self.employee_number, self.week_ending, self.position_key))

    @staticmethod
    def _clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean the data by removing BOM and converting to the correct type."""
        clean_data = {}
        for key, value in data.items():
            # Remove BOM from key if present
            clean_key = key.lstrip('\ufeff')
            # Convert value to string and strip whitespace
            if value is not None:
                clean_data[clean_key] = str(value).strip()
            else:
                clean_data[clean_key] = value
        return clean_data

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[date]:
        """
        Parse a date string to a date object, supporting multiple formats.
        
        Uses SSE's operational configuration for date format preferences.
        
        Supported formats:
        - YYYY-MM-DD (ISO format - SSE preferred)
        - DD/MM/YYYY (UK/AU format - PTH legacy)
        - MM/DD/YYYY (US format)
        """
        if not date_str or str(date_str).strip() == '':
            return None
        
        date_str = str(date_str).strip()
        
        # Get date formats from SSE operational configuration
        try:
            config_loader = get_workforce_config_loader()
            operational_config = config_loader.load_operational_config()
            date_formats = operational_config.get('date_processing', {}).get('alternative_date_formats', [])
            
            # Ensure we have fallback formats
            if not date_formats:
                date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        except Exception:
            # Fallback if configuration loading fails
            date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format).date()
            except ValueError:
                continue
        
        # If none of the formats worked, raise an error
        supported_formats = ", ".join(date_formats)
        raise ValueError(f"Invalid date format. Expected one of [{supported_formats}], got: {date_str}")


class ColleaguePositionBuilder:
    """
    Builder pattern for creating ColleaguePosition instances with validation.
    
    Follows PTH's enterprise design patterns while integrating with SSE's architecture.
    """
    
    def __init__(self):
        self._reset()
    
    def _reset(self):
        """Reset the builder to initial state."""
        self._data = {}
        self._errors = []
    
    def employee_number(self, emp_num: int) -> 'ColleaguePositionBuilder':
        """Set employee number with validation."""
        if not isinstance(emp_num, int) or emp_num <= 0:
            self._errors.append(f"Invalid employee number: {emp_num}")
        else:
            self._data['employee_number'] = emp_num
        return self
    
    def position_details(self, pos_id_lookup: str, position_num: Optional[int] = None) -> 'ColleaguePositionBuilder':
        """Set position identification details."""
        if not pos_id_lookup:
            self._errors.append("PosIDLookupKey is required")
        else:
            self._data['pos_id_lookup_key'] = str(pos_id_lookup)
        
        if position_num is not None:
            self._data['position_number'] = int(position_num)
        return self
    
    def temporal_details(self, week_ending: str, position_start: Optional[str] = None) -> 'ColleaguePositionBuilder':
        """Set temporal details with date validation."""
        try:
            self._data['week_ending'] = ColleaguePosition._parse_date(week_ending)
            if position_start:
                self._data['position_start_date'] = ColleaguePosition._parse_date(position_start)
        except ValueError as e:
            self._errors.append(f"Date parsing error: {e}")
        return self
    
    def organisational_details(self, org_unit: Optional[str] = None, 
                             cost_centre: Optional[str] = None,
                             position_title: Optional[str] = None) -> 'ColleaguePositionBuilder':
        """Set organisational context details."""
        if org_unit:
            self._data['organisational_unit'] = str(org_unit)
        if cost_centre:
            self._data['cost_centre_number'] = str(cost_centre)
        if position_title:
            self._data['position_title'] = str(position_title)
        return self
    
    def operational_status(self, is_operational: bool = True) -> 'ColleaguePositionBuilder':
        """Set operational status."""
        self._data['operational'] = bool(is_operational)
        return self
    
    def build(self) -> ColleaguePosition:
        """
        Build the ColleaguePosition instance.
        
        Returns:
            ColleaguePosition: Validated instance
            
        Raises:
            ValueError: If validation errors occurred during building
        """
        if self._errors:
            error_msg = "; ".join(self._errors)
            self._reset()
            raise ValueError(f"ColleaguePosition validation failed: {error_msg}")
        
        # Check required fields
        required_fields = ['employee_number', 'pos_id_lookup_key', 'week_ending']
        missing_fields = [field for field in required_fields if field not in self._data]
        
        if missing_fields:
            self._reset()
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        try:
            colleague_position = ColleaguePosition(**self._data)
            self._reset()
            return colleague_position
        except Exception as e:
            self._reset()
            raise ValueError(f"Failed to create ColleaguePosition: {e}") 