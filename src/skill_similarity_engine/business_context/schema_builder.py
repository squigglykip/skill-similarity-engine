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
                
                # Create movement analysis tables
                self._create_colleague_movements_table(conn)
                self._create_position_history_table(conn)
                self._create_workforce_context_table(conn)
                self._create_movement_fact_table(conn)
                
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
        tables = [
            'job_skills', 'job_similarities', 'career_pathways', 
            'colleague_movements', 'position_history', 'workforce_context', 'movement_fact',
            'positions', 'skills', 'jobs', 'schema_metadata'
        ]
        
        for table in tables:
            try:
                conn.execute(f"DROP TABLE IF EXISTS {table};")
                logger.debug(f"Dropped table: {table}")
            except sqlite3.Error as e:
                logger.warning(f"Could not drop table {table}: {e}")
    
    def _create_jobs_table(self, conn: sqlite3.Connection) -> None:
        """Create jobs table - Enhanced Job Architecture Master Data with 16-column schema."""
        sql = """
        CREATE TABLE jobs (
            JobProfileID TEXT PRIMARY KEY,           -- R0001.5 format
            JobProfile TEXT NOT NULL,               -- "Analyst - Risk Management"
            JobID TEXT,                             -- Hierarchical job code (R0001)
            Job TEXT,                               -- Job title ("Analyst")
            
            -- Enhanced 16-column schema (Phase 2 additions)
            ProfileTitleSuffix TEXT,                -- "Analyst", "Manager", "Consultant", etc. (16 categories)
            ManagementLevel TEXT,                   -- "Group 1", "Group 2", ..., "Group 7", "Group NA" (8 categories)
            JobSubFunctionID TEXT,                  -- "JF0001", "JF0002", ..., "JF0834" (105 unique values)
            JobSubFunction TEXT,                    -- "Corporate Finance", "Executive", etc. (105 categories)
            JobFunctionID TEXT,                     -- "JF0001", "JF0002", etc. (Function level grouping)
            JobFunction TEXT,                       -- "Technology", "Risk", "Finance", etc. (Function names)
            JobCategoryID TEXT,                     -- "JC1", "JC2", "JC3", "JC10" (4 categories)
            JobCategory TEXT,                       -- "Support", "Revenue Generating", "Enabling", "Executive"
            Customer_Facing TEXT,                   -- "Customer Facing", "Non-Customer Facing" (nullable, 24 nulls)
            is_Banker TEXT,                         -- "Banker", "Non-Banker" (nullable, 24 nulls)
            Executive_Leadership_Group TEXT,        -- "Executive Leadership Group" (nullable, 2903 nulls)
            Accountability_Scope TEXT               -- "Direct", "Supports" (nullable)
        );
        """
        conn.execute(sql)
        logger.debug("Created enhanced jobs table with 16-column schema")
    
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
        """Create positions table - Workforce Context with Employee Number as primary key."""
        sql = """
        CREATE TABLE positions (
            "Employee Number" TEXT PRIMARY KEY,     -- Unique employee identifier (one row per employee)
            "Position Number" TEXT NOT NULL,        -- Position/role identifier (can be shared by multiple employees)
            "Position Name" TEXT,                   -- Human-readable position name/title
            JobProfileID TEXT,                      -- Direct link to jobs table (enriched during loading)
            
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
        logger.debug("Created positions table with Employee Number as primary key")
    
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
    
    def _create_colleague_movements_table(self, conn: sqlite3.Connection) -> None:
        """Create colleague_movements table - Pre-computed colleague movement data."""
        sql = """
        CREATE TABLE colleague_movements (
            movement_id INTEGER PRIMARY KEY,
            employee_number TEXT NOT NULL,
            jobprofile_id TEXT NOT NULL,
            movement_type TEXT NOT NULL,
            movement_date DATE NOT NULL,
            effective_date DATE NOT NULL,
            end_date DATE,
            change_reason TEXT,
            
            FOREIGN KEY (employee_number) REFERENCES positions("Employee Number"),
            FOREIGN KEY (jobprofile_id) REFERENCES jobs(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created colleague_movements table")

    def _create_position_history_table(self, conn: sqlite3.Connection) -> None:
        """Create position_history table - Historical position data from CSV files."""
        sql = """
        CREATE TABLE position_history (
            week_ending DATE,
            position_number TEXT NOT NULL,
            position_id_lookup_key TEXT,
            organisational_unit TEXT,
            cost_centre_number TEXT,
            position_title TEXT,
            people_leader TEXT,
            operational TEXT,
            org_unit_id_lookup_key TEXT
        );
        """
        conn.execute(sql)
        logger.debug("Created position_history table")

    def _create_workforce_context_table(self, conn: sqlite3.Connection) -> None:
        """Create workforce_context table - Workforce context and organisational hierarchy data."""
        sql = """
        CREATE TABLE workforce_context (
            week_ending DATE,
            position_number TEXT NOT NULL,
            position_name TEXT,
            employee_number TEXT,
            employee_name TEXT,
            location TEXT,
            region TEXT,
            country TEXT,
            employee_group TEXT,
            salary_group TEXT,
            division TEXT,
            business_unit TEXT,
            team TEXT,
            sub_team TEXT,
            function TEXT,
            sub_function TEXT,
            org_level_8 TEXT,
            org_level_9 TEXT,
            org_level_10 TEXT
        );
        """
        conn.execute(sql)
        logger.debug("Created workforce_context table")
    
    def _create_movement_fact_table(self, conn: sqlite3.Connection) -> None:
        """Create movement_fact table - Aggregated movement patterns for strategic analysis."""
        sql = """
        CREATE TABLE movement_fact (
            fact_id INTEGER PRIMARY KEY,
            movement_month TEXT NOT NULL,
            movement_year INTEGER NOT NULL,
            from_position TEXT NOT NULL,
            to_position TEXT NOT NULL,
            movement_pattern TEXT NOT NULL,
            movement_count INTEGER NOT NULL,
            pct_total_movements REAL,
            unique_employees INTEGER NOT NULL,
            avg_days_between REAL,
            monthly_total_movements INTEGER NOT NULL,
            predominant_movement_type TEXT,
            
            -- Indexes for performance
            UNIQUE(movement_month, from_position, to_position)
        );
        """
        conn.execute(sql)
        logger.debug("Created movement_fact table for aggregated movement patterns")
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create performance indexes for webapp queries."""
        indexes = [
            # Job exploration queries
            "CREATE INDEX idx_jobs_function ON jobs(JobFunction);",
            "CREATE INDEX idx_jobs_function_id ON jobs(JobFunctionID);",
            
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
            "CREATE INDEX idx_skills_category ON skills(Category, Subcategory);",

            # Movement analysis indexes
            "CREATE INDEX idx_colleague_movements_employee ON colleague_movements(employee_number);",
            "CREATE INDEX idx_colleague_movements_job ON colleague_movements(jobprofile_id);",
            "CREATE INDEX idx_position_history_employee ON position_history(employee_number);",
            "CREATE INDEX idx_position_history_job ON position_history(jobprofile_id);",
            "CREATE INDEX idx_workforce_context_employee ON workforce_context(employee_number);",
            "CREATE INDEX idx_workforce_context_job ON workforce_context(jobprofile_id);",
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
    
    def check_schema_version(self) -> Optional[str]:
        """Check current schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value FROM schema_metadata WHERE key = 'schema_version'"
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error:
            return None
    
    def migrate_schema(self, target_version: str) -> bool:
        """Migrate schema to target version."""
        current_version = self.check_schema_version()
        
        if current_version == target_version:
            logger.info(f"Schema already at version {target_version}")
            return True
        
        logger.info(f"Migrating schema from {current_version} to {target_version}")
        
        # Define migration paths
        migrations = {
            ("1.0", "1.1"): self._migrate_1_0_to_1_1,
            ("1.1", "1.2"): self._migrate_1_1_to_1_2,
        }
        
        migration_key = (current_version, target_version)
        if migration_key in migrations:
            return migrations[migration_key]()
        else:
            logger.error(f"No migration path from {current_version} to {target_version}")
            return False
    
    def _migrate_1_0_to_1_1(self) -> bool:
        """Migrate from version 1.0 to 1.1 - Add temporal tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Add position history table
                conn.execute("""
                    CREATE TABLE position_history (
                        history_id INTEGER PRIMARY KEY,
                        employee_number TEXT NOT NULL,
                        position_number TEXT NOT NULL,
                        jobprofile_id TEXT,
                        effective_date DATE NOT NULL,
                        end_date DATE,
                        change_type TEXT,
                        
                        FOREIGN KEY (employee_number) REFERENCES positions("Employee Number"),
                        FOREIGN KEY (jobprofile_id) REFERENCES jobs(JobProfileID)
                    );
                """)
                
                # Add org history table
                conn.execute("""
                    CREATE TABLE org_history (
                        org_history_id INTEGER PRIMARY KEY,
                        org_unit_id TEXT NOT NULL,
                        org_unit_name TEXT NOT NULL,
                        parent_org_unit_id TEXT,
                        org_level INTEGER,
                        effective_date DATE NOT NULL,
                        end_date DATE,
                        change_reason TEXT
                    );
                """)
                
                # Update schema version
                conn.execute(
                    "UPDATE schema_metadata SET value = '1.1' WHERE key = 'schema_version'"
                )
                
                conn.commit()
                logger.info("Successfully migrated to schema version 1.1")
                return True
                
        except Exception as e:
            logger.error(f"Migration to 1.1 failed: {e}")
            return False
    
    def _migrate_1_1_to_1_2(self) -> bool:
        """Migrate from version 1.1 to 1.2 - Add ML tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Add ML model metadata table
                conn.execute("""
                    CREATE TABLE ml_models (
                        model_id INTEGER PRIMARY KEY,
                        model_name TEXT NOT NULL,
                        model_type TEXT NOT NULL,
                        version TEXT NOT NULL,
                        parameters JSON,
                        performance_metrics JSON,
                        training_date DATE,
                        is_active BOOLEAN DEFAULT 1
                    );
                """)
                
                # Add skills clustering tables
                conn.execute("""
                    CREATE TABLE skills_clusters (
                        cluster_id INTEGER PRIMARY KEY,
                        cluster_name TEXT,
                        cluster_description TEXT,
                        model_version TEXT,
                        created_date DATE,
                        
                        FOREIGN KEY (model_version) REFERENCES ml_models(version)
                    );
                """)
                
                conn.execute("""
                    CREATE TABLE skill_cluster_membership (
                        skill_id TEXT,
                        cluster_id INTEGER,
                        membership_score REAL,
                        
                        PRIMARY KEY (skill_id, cluster_id),
                        FOREIGN KEY (skill_id) REFERENCES skills(Skill_ID),
                        FOREIGN KEY (cluster_id) REFERENCES skills_clusters(cluster_id)
                    );
                """)
                
                # Update schema version
                conn.execute(
                    "UPDATE schema_metadata SET value = '1.2' WHERE key = 'schema_version'"
                )
                
                conn.commit()
                logger.info("Successfully migrated to schema version 1.2")
                return True
                
        except Exception as e:
            logger.error(f"Migration to 1.2 failed: {e}")
            return False
    
    def validate_schema(self) -> bool:
        """
        Validate that schema was created correctly.
        
        Returns:
            True if schema is valid
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check all required tables exist
                required_tables = [
                    'jobs', 'job_similarities', 'positions', 'skills', 'job_skills', 'career_pathways',
                    'colleague_movements', 'position_history', 'workforce_context', 'movement_fact'
                ]
                
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
