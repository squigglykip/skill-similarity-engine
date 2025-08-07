"""
Session Manager for Application State

Manages application session state including loaded data, replacing the global
variables pattern from main.py with a proper session management system.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..models.skills import SkillTaxonomy
from ..models.jobs import JobArchitecture
from ..models.employees import EmployeeDatabase


@dataclass
class SessionData:
    """
    Container for session data and application state.
    
    Replaces the global variables loaded_taxonomy and loaded_architecture
    from main.py with a structured approach.
    """
    taxonomy: Optional[SkillTaxonomy] = None
    architecture: Optional[JobArchitecture] = None
    employee_database: Optional[EmployeeDatabase] = None
    session_id: str = ""
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.last_updated = datetime.now()
        if not self.session_id:
            self.session_id = f"session_{self.created_at.strftime('%Y%m%d_%H%M%S')}"
    
    @property
    def is_data_loaded(self) -> bool:
        """Check if core data (taxonomy and architecture) is loaded."""
        return self.taxonomy is not None and self.architecture is not None
    
    @property
    def data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data."""
        return {
            'taxonomy_loaded': self.taxonomy is not None,
            'skills_count': len(self.taxonomy.skills) if self.taxonomy else 0,
            'architecture_loaded': self.architecture is not None,
            'jobs_count': len(self.architecture.jobs) if self.architecture else 0,
            'employee_database_loaded': self.employee_database is not None,
            'employees_count': len(self.employee_database.employees) if self.employee_database else 0,
            'session_age_minutes': (datetime.now() - self.created_at).seconds / 60,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def update_timestamp(self):
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now()


class SessionManager:
    """
    Manages application session state and data persistence.
    
    Provides a centralized way to manage loaded data throughout the application
    lifecycle, replacing the global variable pattern from main.py.
    """
    
    _instance: Optional['SessionManager'] = None
    _current_session: Optional[SessionData] = None
    
    def __new__(cls) -> 'SessionManager':
        """Singleton pattern to ensure only one session manager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize session manager."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
    
    @property
    def current_session(self) -> SessionData:
        """Get the current session, creating one if needed."""
        if self._current_session is None:
            self._current_session = SessionData()
            print(f"🆕 Created new session: {self._current_session.session_id}")
        return self._current_session
    
    def start_new_session(self) -> SessionData:
        """Start a new session, clearing any existing data."""
        old_session_id = self._current_session.session_id if self._current_session else "none"
        self._current_session = SessionData()
        print(f"🔄 Started new session: {self._current_session.session_id} (previous: {old_session_id})")
        return self._current_session
    
    def load_taxonomy(self, taxonomy: SkillTaxonomy) -> None:
        """Load skill taxonomy into the current session."""
        session = self.current_session
        session.taxonomy = taxonomy
        session.update_timestamp()
        session.metadata['taxonomy_loaded_at'] = datetime.now().isoformat()
        print(f"📚 Loaded taxonomy with {len(taxonomy.skills):,} skills")
    
    def load_architecture(self, architecture: JobArchitecture) -> None:
        """Load job architecture into the current session."""
        session = self.current_session
        session.architecture = architecture
        session.update_timestamp()
        session.metadata['architecture_loaded_at'] = datetime.now().isoformat()
        print(f"🏗️ Loaded architecture with {len(architecture.jobs):,} jobs")
    
    def load_employee_database(self, employee_database: EmployeeDatabase) -> None:
        """Load employee database into the current session."""
        session = self.current_session
        session.employee_database = employee_database
        session.update_timestamp()
        session.metadata['employee_database_loaded_at'] = datetime.now().isoformat()
        print(f"👥 Loaded employee database with {len(employee_database.employees):,} employees")
    
    def get_taxonomy(self) -> Optional[SkillTaxonomy]:
        """Get the loaded skill taxonomy."""
        return self.current_session.taxonomy
    
    def get_architecture(self) -> Optional[JobArchitecture]:
        """Get the loaded job architecture."""
        return self.current_session.architecture
    
    def get_employee_database(self) -> Optional[EmployeeDatabase]:
        """Get the loaded employee database."""
        return self.current_session.employee_database
    
    def is_data_ready_for_similarity(self) -> bool:
        """Check if required data is loaded for similarity operations."""
        session = self.current_session
        return session.taxonomy is not None and session.architecture is not None
    
    def clear_session(self) -> None:
        """Clear the current session data."""
        if self._current_session:
            old_session_id = self._current_session.session_id
            self._current_session = None
            print(f"🧹 Cleared session: {old_session_id}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session state."""
        if self._current_session is None:
            return {'session_exists': False}
        
        summary = self.current_session.data_summary
        summary['session_id'] = self.current_session.session_id
        summary['session_exists'] = True
        summary['ready_for_similarity'] = self.is_data_ready_for_similarity()
        return summary
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the current session."""
        session = self.current_session
        session.metadata[key] = value
        session.update_timestamp()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the current session."""
        return self.current_session.metadata.get(key, default)


# Global session manager instance
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return _session_manager


def get_current_session() -> SessionData:
    """Get the current session data."""
    return _session_manager.current_session


def is_data_loaded() -> bool:
    """Check if core data is loaded in the current session."""
    return _session_manager.is_data_ready_for_similarity() 