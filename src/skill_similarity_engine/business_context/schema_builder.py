"""
SQLite Schema Builder for Business Context Database

Implements the exact schema design from docs/sqlite_schema_design.md with:
- 5 core tables: jobs, job_similarities, positions, skills, job_skills
- Performance indexes for webapp queries
- Schema versioning metadata
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SchemaBuilder:
    """Builds SQLite schema for business context database."""
    
    def __init__(self, db_path: str):
        """
        Initialize schema builder.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.schema_version = "1.0"
        
    def create_schema(self, drop_existing: bool = False) -> bool:
        """
        Create complete database schema with all tables and indexes.
        
        Args:
            drop_existing: Whether to drop existing tables first
            
        Returns:
            True if schema created successfully
        """
        try:
            logger.info(f"Creating database schema at: {self.db_path}")
            
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON;")
                
                if drop_existing:
                    logger.info("Dropping existing tables...")
                    self._drop_existing_tables(conn)
                
                # Create core tables
                self._create_jobs_table(conn)
                self._create_job_similarities_table(conn)
                self._create_positions_table(conn)
                self._create_skills_table(conn)
                self._create_job_skills_table(conn)
                self._create_career_pathways_table(conn)
                
                # Create performance indexes
                self._create_indexes(conn)
                
                # Add schema metadata
                self._add_schema_metadata(conn)
                
                conn.commit()
                logger.info("Database schema created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            return False
    
    def _drop_existing_tables(self, conn: sqlite3.Connection) -> None:
        """Drop all existing tables in dependency order."""
        tables = ['job_skills', 'job_similarities', 'career_pathways', 'positions', 'skills', 'jobs', 'schema_metadata']
        
        for table in tables:
            try:
                conn.execute(f"DROP TABLE IF EXISTS {table};")
                logger.debug(f"Dropped table: {table}")
            except sqlite3.Error as e:
                logger.warning(f"Could not drop table {table}: {e}")
    
    def _create_jobs_table(self, conn: sqlite3.Connection) -> None:
        """Create jobs table - Enhanced Job Architecture Master Data with 14-column schema."""
        sql = """
        CREATE TABLE jobs (
            JobProfileID TEXT PRIMARY KEY,           -- R0001.5 format
            JobProfile TEXT NOT NULL,               -- "Analyst - Risk Management"
            JobID TEXT,                             -- Hierarchical job code (R0001)
            Job TEXT,                               -- Job title ("Analyst")
            JobFamily TEXT,                         -- "Technology", "Risk", "Finance"
            JobFamilyGroup TEXT,                    -- Higher-level grouping
            
            -- Enhanced 14-column schema (Phase 2 additions)
            ProfileTitleSuffix TEXT,                -- "Analyst", "Manager", "Consultant", etc. (16 categories)
            ManagementLevel TEXT,                   -- "Group 1", "Group 2", ..., "Group 7", "Group NA" (8 categories)
            JobSubFunctionID TEXT,                  -- "JF0001", "JF0002", ..., "JF0834" (105 unique values)
            JobSubFunction TEXT,                    -- "Corporate Finance", "Executive", etc. (105 categories)
            JobCategoryID TEXT,                     -- "JC1", "JC2", "JC3", "JC10" (4 categories)
            JobCategory TEXT,                       -- "Support", "Revenue Generating", "Enabling", "Executive"
            Customer_Facing TEXT,                   -- "Customer Facing", "Non-Customer Facing" (nullable, 24 nulls)
            is_Banker TEXT,                         -- "Banker", "Non-Banker" (nullable, 24 nulls)
            Executive_Leadership_Group TEXT,        -- "Executive Leadership Group" (nullable, 2903 nulls)
            Accountability_Scope TEXT               -- "Direct", "Supports" (nullable)
        );
        """
        conn.execute(sql)
        logger.debug("Created enhanced jobs table with 14-column schema")
    
    def _create_job_similarities_table(self, conn: sqlite3.Connection) -> None:
        """Create job_similarities table - Pre-computed Job-to-Job Similarities."""
        sql = """
        CREATE TABLE job_similarities (
            job_from TEXT NOT NULL,                 -- Source JobProfileID
            job_to TEXT NOT NULL,                   -- Target JobProfileID  
            similarity_score REAL NOT NULL,        -- Overall similarity (0-1)
            skill_overlap_score REAL,              -- Skills-specific similarity
            shared_skills_count INTEGER,           -- Number of overlapping skills
            total_skills_from INTEGER,             -- Total skills for source job
            total_skills_to INTEGER,               -- Total skills for target job
            
            PRIMARY KEY (job_from, job_to),
            FOREIGN KEY (job_from) REFERENCES jobs(JobProfileID),
            FOREIGN KEY (job_to) REFERENCES jobs(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created job_similarities table")
    
    def _create_positions_table(self, conn: sqlite3.Connection) -> None:
        """Create positions table - Workforce Context with full organizational hierarchy."""
        sql = """
        CREATE TABLE positions (
            "Position Number" TEXT PRIMARY KEY,     -- Unique position identifier
            "Position Name" TEXT,                   -- Human-readable position name/title
            JobProfileID TEXT,                      -- Direct link to jobs table (enriched during loading)
            "Employee Number" TEXT,                 -- Current employee (if filled)
            
            -- Organizational Hierarchy (10-level structure) - renamed for clarity
            Division TEXT,                          -- ORG_UNIT_NAME_2: Divisions
            Business_Unit TEXT,                     -- ORG_UNIT_NAME_3: Business Unit
            Team TEXT,                              -- ORG_UNIT_NAME_4: Team
            SubTeam TEXT,                           -- ORG_UNIT_NAME_5: SubTeam
            Function TEXT,                          -- ORG_UNIT_NAME_6: Function
            SubFunction TEXT,                       -- ORG_UNIT_NAME_7: SubFunction
            Org_Level_8 TEXT,                       -- ORG_UNIT_NAME_8: Org Level 8
            Org_Level_9 TEXT,                       -- ORG_UNIT_NAME_9: Org Level 9
            Org_Level_10 TEXT,                      -- ORG_UNIT_NAME_10: Org Level 10
            
            -- Geographic Context (original field names)
            Location TEXT,                          -- "Melbourne", "Sydney"
            Rg TEXT,                                -- "VIC", "NSW" (original: State/Region)
            Cty TEXT,                               -- "Australia" (original: Country)
            
            -- Employment Details (original field names)
            "Employee Group" TEXT,                  -- "Permanent", "Contract"
            "Salary Group" TEXT,                    -- Text grade: "Group 1", "Group 2", etc.
            "Employee Subgroup" TEXT,               -- "Full Time", "Part Time"
            
            FOREIGN KEY (JobProfileID) REFERENCES jobs(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created positions table")
    
    def _create_skills_table(self, conn: sqlite3.Connection) -> None:
        """Create skills table - Enhanced Comprehensive Skills Library with 18-column schema."""
        sql = """
        CREATE TABLE skills (
            Skill_ID TEXT PRIMARY KEY,              -- Lightcast skill identifier (id field from CSV)
            Skill_Name TEXT NOT NULL,               -- "Python Programming" (name field from CSV)
            Category TEXT,                          -- "Information Technology" (category_name field)
            Subcategory TEXT,                       -- "Enterprise Information Management" (subcategory_name field)
            SkillType TEXT,                         -- "Specialized Skill", "Hard Skill", "Soft Skill" (type field)
            Latest_Version TEXT,                    -- Version tracking (source_version field)
            
            -- Enhanced 18-column schema (Phase 2 additions)
            category_id INTEGER,                    -- Lightcast category ID
            description TEXT,                       -- Detailed skill description
            descriptionSource TEXT,                 -- Source of description
            Info_URL TEXT,                          -- Lightcast skill URL (infoUrl field)
            Is_Language BOOLEAN,                    -- Whether skill is a language (0.77% true)
            isSoftware BOOLEAN,                    -- Whether skill is software (28.35% true)
            subcategory_id INTEGER,               -- Lightcast subcategory ID
            tag_wikipediaExtract TEXT,            -- Wikipedia integration (68% coverage)
            tag_wikipediaUrl TEXT,                -- Wikipedia URL
            tags TEXT,                            -- JSON field: nested structures
            type_id TEXT,                         -- Lightcast type ID (ST1, etc.)
            type_name TEXT,                       -- Human-readable type name
            
            -- Legacy compatibility fields (maintained for backward compatibility)
            Market_Demand TEXT DEFAULT '',         -- "High", "Medium", "Low" (placeholder)
            Rarity_Score REAL DEFAULT NULL        -- 0-1 scale for skill uniqueness (placeholder)
        );
        """
        conn.execute(sql)
        logger.debug("Created enhanced skills table with 18-column schema")
    
    def _create_job_skills_table(self, conn: sqlite3.Connection) -> None:
        """Create job_skills table - Job-to-Skills Mapping."""
        sql = """
        CREATE TABLE job_skills (
            JobProfileID TEXT NOT NULL,             -- Link to jobs table
            Skill_ID TEXT NOT NULL,                 -- Link to skills table
            Skill_Weight REAL DEFAULT 1.0,         -- Importance weight (0-1)
            
            PRIMARY KEY (JobProfileID, Skill_ID),
            FOREIGN KEY (JobProfileID) REFERENCES jobs(JobProfileID),
            FOREIGN KEY (Skill_ID) REFERENCES skills(Skill_ID)
        );
        """
        conn.execute(sql)
        logger.debug("Created job_skills table")
    
    def _create_career_pathways_table(self, conn: sqlite3.Connection) -> None:
        """Create career_pathways table - Pre-computed Career Pathway Relationships."""
        sql = """
        CREATE TABLE career_pathways (
            source_job_id TEXT NOT NULL,            -- Source JobProfileID
            target_job_id TEXT NOT NULL,            -- Target JobProfileID
            similarity_rank INTEGER NOT NULL,       -- Rank (1-N) based on similarity score
            similarity_score REAL NOT NULL,        -- Overall similarity (0-1)
            skill_overlap_score REAL,              -- Skills-specific similarity
            shared_skills_count INTEGER,           -- Number of overlapping skills
            career_move_type TEXT,                  -- 'lateral', 'progression', 'cross_family'
            difficulty_score REAL,                 -- Estimated transition difficulty (0-1)
            
            PRIMARY KEY (source_job_id, target_job_id),
            FOREIGN KEY (source_job_id) REFERENCES jobs(JobProfileID),
            FOREIGN KEY (target_job_id) REFERENCES jobs(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created career_pathways table")
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create performance indexes for webapp queries."""
        indexes = [
            # Job exploration queries
            "CREATE INDEX idx_jobs_family ON jobs(JobFamily);",
            "CREATE INDEX idx_jobs_family_group ON jobs(JobFamilyGroup);",
            
            # Similarity queries (most important)
            "CREATE INDEX idx_similarities_from ON job_similarities(job_from, similarity_score DESC);",
            "CREATE INDEX idx_similarities_to ON job_similarities(job_to, similarity_score DESC);",
            "CREATE INDEX idx_similarities_score ON job_similarities(similarity_score DESC);",
            
            # Career pathways queries (NEW - optimized for tree building)
            "CREATE INDEX idx_career_pathways_source ON career_pathways(source_job_id, similarity_rank);",
            "CREATE INDEX idx_career_pathways_target ON career_pathways(target_job_id, similarity_rank);",
            "CREATE INDEX idx_career_pathways_rank ON career_pathways(similarity_rank, similarity_score DESC);",
            "CREATE INDEX idx_career_pathways_move_type ON career_pathways(career_move_type, similarity_score DESC);",
            
            # Position filtering 
            "CREATE INDEX idx_positions_job_profile ON positions(JobProfileID);",
            "CREATE INDEX idx_positions_business_unit ON positions(Business_Unit);",
            "CREATE INDEX idx_positions_division ON positions(Division);",
            "CREATE INDEX idx_positions_team ON positions(Team);",
            "CREATE INDEX idx_positions_function ON positions(Function);",
            "CREATE INDEX idx_positions_location ON positions(Location, Rg);",
            
            # Skills analysis
            "CREATE INDEX idx_job_skills_job ON job_skills(JobProfileID);",
            "CREATE INDEX idx_job_skills_skill ON job_skills(Skill_ID);",
            "CREATE INDEX idx_skills_category ON skills(Category, Subcategory);"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
                logger.debug(f"Created index: {index_sql.split()[2]}")  # Extract index name
            except sqlite3.Error as e:
                logger.warning(f"Could not create index: {e}")
    
    def _add_schema_metadata(self, conn: sqlite3.Connection) -> None:
        """Add schema versioning metadata."""
        metadata_sql = """
        CREATE TABLE IF NOT EXISTS schema_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
        conn.execute(metadata_sql)
        
        # Insert version information
        created_at = datetime.now().isoformat()
        metadata = [
            ('schema_version', self.schema_version, created_at),
            ('created_date', created_at, created_at),
            ('source_document', 'docs/sqlite_schema_design.md', created_at),
            ('purpose', 'NAB Skill Similarity Engine Business Context Database', created_at)
        ]
        
        conn.executemany(
            "INSERT OR REPLACE INTO schema_metadata (key, value, created_at) VALUES (?, ?, ?)",
            metadata
        )
        logger.debug("Added schema metadata")
    
    def validate_schema(self) -> bool:
        """
        Validate that schema was created correctly.
        
        Returns:
            True if schema is valid
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check all required tables exist
                required_tables = ['jobs', 'job_similarities', 'positions', 'skills', 'job_skills']
                
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = set(required_tables) - set(existing_tables)
                if missing_tables:
                    logger.error(f"Missing tables: {missing_tables}")
                    return False
                
                # Check foreign key constraints are enabled
                cursor = conn.execute("PRAGMA foreign_keys;")
                fk_enabled = cursor.fetchone()[0]
                if not fk_enabled:
                    logger.warning("Foreign key constraints not enabled")
                
                logger.info("Schema validation passed")
                return True
                
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False
    
    def get_table_info(self) -> dict:
        """
        Get information about created tables.
        
        Returns:
            Dictionary with table names and row counts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                tables_info = {}
                
                # Get all table names
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                table_names = [row[0] for row in cursor.fetchall()]
                
                # Get row count for each table
                for table in table_names:
                    try:
                        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        tables_info[table] = row_count
                    except sqlite3.Error:
                        tables_info[table] = "Error counting rows"
                
                return tables_info
                
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {} 