#!/usr/bin/env python3
"""
Script for transforming HRIS data into formats compatible with the Skill Similarity Engine.
This uses the schema mapping configuration to transform data from any HRIS system.
"""

import os
import sys
import click
import pandas as pd
import yaml
import logging
from pathlib import Path
from datetime import datetime

# Add the src directory to the path so we can import our package
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)
from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel, RoleTrack

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('hris_transform')

class HRISTransformer:
    """Handles transformation of HRIS data based on schema mapping configuration."""
    
    def __init__(self, config_path):
        """Initialize with a schema mapping configuration file."""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.mapping_report = []
        
    def _load_config(self, config_path):
        """Load the schema mapping configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise
    
    def _setup_logging(self):
        """Configure logging based on settings in the config."""
        log_level = getattr(logging, self.config.get('logging', {}).get('level', 'INFO'))
        logger.setLevel(log_level)
        
        if self.config.get('logging', {}).get('log_details', True):
            logger.info("Detailed logging enabled")
    
    def _read_data_file(self, file_path):
        """Read a data file based on its format."""
        try:
            file_format = self.config['hris_data']['file_format'].lower()
            encoding = self.config['hris_data']['encoding']
            
            if file_format == 'csv':
                delimiter = self.config['hris_data']['delimiter']
                return pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
            elif file_format in ['xlsx', 'xls']:
                sheet_name = self.config['hris_data']['sheet_name']
                return pd.read_excel(file_path, sheet_name=sheet_name)
            elif file_format == 'json':
                return pd.read_json(file_path, encoding=encoding)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
        except Exception as e:
            logger.error(f"Failed to read data file {file_path}: {str(e)}")
            raise
    
    def _map_job_level(self, hris_level):
        """Map HRIS job level to engine JobLevel enum."""
        level_mapping = self.config.get('job_level_mapping', {})
        default_level = self.config['transformation_options']['default_job_level']
        
        mapped_level = level_mapping.get(hris_level, default_level)
        
        # Add to mapping report
        if hris_level != mapped_level:
            self.mapping_report.append({
                'type': 'job_level',
                'original_value': hris_level,
                'mapped_value': mapped_level
            })
        
        # Convert string to JobLevel enum
        return getattr(JobLevel, mapped_level)
    
    def _map_pay_scale(self, hris_pay_scale):
        """Map HRIS pay scale to engine PSA value."""
        psa_mapping = self.config.get('pay_scale_mapping', {})
        default_psa = self.config['transformation_options']['default_pay_scale_area']
        
        mapped_psa = psa_mapping.get(hris_pay_scale, default_psa)
        
        # Add to mapping report
        if hris_pay_scale != mapped_psa:
            self.mapping_report.append({
                'type': 'pay_scale',
                'original_value': hris_pay_scale,
                'mapped_value': mapped_psa
            })
        
        return mapped_psa
    
    def _map_role_track(self, hris_role_track):
        """Map HRIS role track to engine RoleTrack enum."""
        track_mapping = self.config.get('role_track_mapping', {})
        default_track = self.config['transformation_options']['default_role_track']
        
        mapped_track = track_mapping.get(hris_role_track, default_track)
        
        # Add to mapping report
        if hris_role_track != mapped_track:
            self.mapping_report.append({
                'type': 'role_track',
                'original_value': hris_role_track,
                'mapped_value': mapped_track
            })
        
        # Convert string to RoleTrack enum
        return getattr(RoleTrack, mapped_track)
    
    def _map_proficiency(self, hris_proficiency):
        """Map HRIS proficiency values to 1-5 scale."""
        prof_mapping = self.config.get('proficiency_mapping', {})
        default_prof = self.config['transformation_options']['default_proficiency']
        
        # Handle proficiency values of different types
        if isinstance(hris_proficiency, str) and hris_proficiency in prof_mapping:
            mapped_prof = prof_mapping[hris_proficiency]
        elif isinstance(hris_proficiency, (int, float)) and 1 <= hris_proficiency <= 5:
            mapped_prof = int(hris_proficiency)
        else:
            mapped_prof = default_prof
        
        # Add to mapping report if it's a string mapping
        if isinstance(hris_proficiency, str) and hris_proficiency in prof_mapping:
            self.mapping_report.append({
                'type': 'proficiency',
                'original_value': hris_proficiency,
                'mapped_value': mapped_prof
            })
        
        return mapped_prof
    
    def transform_jobs(self):
        """Transform HRIS job data to engine format."""
        logger.info("Transforming HRIS job data...")
        
        # Get file paths
        jobs_file = self.config['hris_data']['jobs_file']
        output_file = self.config['output_data']['jobs_file']
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Read HRIS job data
        jobs_df = self._read_data_file(jobs_file)
        logger.info(f"Loaded {len(jobs_df)} job records")
        
        # Create job architecture
        job_arch = JobArchitecture()
        
        # Get column mappings
        job_id_col = self.config['jobs_mapping']['job_id']
        title_col = self.config['jobs_mapping']['title']
        dept_col = self.config['jobs_mapping']['department']
        level_col = self.config['jobs_mapping']['level']
        
        # Optional columns
        psa_col = self.config['jobs_mapping'].get('pay_scale_area')
        role_track_col = self.config['jobs_mapping'].get('role_track')
        location_col = self.config['jobs_mapping'].get('location')
        active_col = self.config['jobs_mapping'].get('active')
        
        # Default values
        default_dept = self.config['transformation_options']['default_department']
        
        # Process each job
        job_count = 0
        skipped_count = 0
        
        for _, row in jobs_df.iterrows():
            # Check if job is active (if column exists)
            if active_col and active_col in row and not row[active_col]:
                skipped_count += 1
                continue
            
            # Extract required fields
            job_id = str(row[job_id_col])
            title = str(row[title_col])
            
            # Extract optional fields with defaults
            department = str(row.get(dept_col, default_dept))
            
            # Map job level
            hris_level = row.get(level_col)
            job_level = self._map_job_level(hris_level) if hris_level else JobLevel.ASSOCIATE
            
            # Map pay scale area
            hris_psa = row.get(psa_col) if psa_col else None
            psa = self._map_pay_scale(hris_psa) if hris_psa else self.config['transformation_options']['default_pay_scale_area']
            
            # Map role track
            hris_track = row.get(role_track_col) if role_track_col else None
            role_track = self._map_role_track(hris_track) if hris_track else RoleTrack.INDIVIDUAL_CONTRIBUTOR
            
            # Get location if available
            location = str(row.get(location_col, "")) if location_col else ""
            
            # Create Job object (skills will be added later)
            job = Job(
                job_id=job_id,
                title=title,
                department=department,
                level=job_level,
                skills={},  # Empty skills dict for now
                pay_scale_area=psa,
                role_track=role_track,
                location=location
            )
            
            # Add to job architecture
            job_arch.add_job(job)
            job_count += 1
        
        logger.info(f"Transformed {job_count} jobs (skipped {skipped_count} inactive jobs)")
        
        # Save the job architecture
        job_arch.to_file(output_file)
        logger.info(f"Job architecture saved to {output_file}")
        
        return job_arch
    
    def transform_skills(self):
        """Transform HRIS skill data to engine format."""
        logger.info("Transforming HRIS skill data...")
        
        # Get file paths
        skills_file = self.config['hris_data']['skills_file']
        output_file = self.config['output_data']['skills_file']
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Read HRIS skill data
        skills_df = self._read_data_file(skills_file)
        logger.info(f"Loaded {len(skills_df)} skill records")
        
        # Create skill taxonomy
        taxonomy = SkillTaxonomy()
        
        # Get column mappings
        skill_id_col = self.config['skills_mapping']['skill_id']
        name_col = self.config['skills_mapping']['name']
        
        # Optional columns
        category_col = self.config['skills_mapping'].get('category')
        subcategory_col = self.config['skills_mapping'].get('subcategory')
        difficulty_col = self.config['skills_mapping'].get('difficulty')
        
        # Process each skill
        for _, row in skills_df.iterrows():
            # Extract required fields
            skill_id = str(row[skill_id_col])
            name = str(row[name_col])
            
            # Extract optional fields with defaults
            category = str(row.get(category_col, "General")) if category_col else "General"
            subcategory = str(row.get(subcategory_col, "")) if subcategory_col else ""
            
            # Get difficulty (1-5 scale)
            if difficulty_col and difficulty_col in row:
                difficulty = min(5, max(1, int(row[difficulty_col])))
            else:
                difficulty = 3  # Default medium difficulty
            
            # Create Skill object
            skill = Skill(
                skill_id=skill_id,
                name=name,
                category=category,
                subcategory=subcategory,
                difficulty=difficulty
            )
            
            # Add to taxonomy
            taxonomy.add_skill(skill)
        
        logger.info(f"Transformed {len(taxonomy.skills)} skills")
        
        # Save the skill taxonomy
        taxonomy.to_file(output_file)
        logger.info(f"Skill taxonomy saved to {output_file}")
        
        return taxonomy
    
    def assign_skills_to_jobs(self, job_arch=None, taxonomy=None):
        """Assign skills to jobs based on HRIS job-skill mapping data."""
        logger.info("Assigning skills to jobs...")
        
        # Get file paths
        mapping_file = self.config['hris_data']['job_skills_file']
        jobs_file = self.config['output_data']['jobs_file']
        
        # Load job architecture and taxonomy if not provided
        if job_arch is None:
            job_arch = JobArchitecture.from_file(jobs_file)
        
        if taxonomy is None and os.path.exists(self.config['output_data']['skills_file']):
            taxonomy = SkillTaxonomy.from_file(self.config['output_data']['skills_file'])
        
        # Read HRIS job-skill mapping data
        mapping_df = self._read_data_file(mapping_file)
        logger.info(f"Loaded {len(mapping_df)} job-skill mapping records")
        
        # Get column mappings
        job_id_col = self.config['job_skills_mapping']['job_id']
        skill_id_col = self.config['job_skills_mapping']['skill_id']
        proficiency_col = self.config['job_skills_mapping'].get('proficiency')
        
        # Track stats
        assigned_count = 0
        skipped_count = 0
        
        # Process each mapping
        use_binary = self.config['transformation_options']['use_binary_skills']
        
        for _, row in mapping_df.iterrows():
            job_id = str(row[job_id_col])
            skill_id = str(row[skill_id_col])
            
            # Skip if job or skill doesn't exist
            if job_id not in job_arch.jobs:
                logger.warning(f"Job {job_id} not found in job architecture")
                skipped_count += 1
                continue
            
            if taxonomy and skill_id not in taxonomy.skills:
                logger.warning(f"Skill {skill_id} not found in skill taxonomy")
                skipped_count += 1
                continue
            
            # Get proficiency
            if proficiency_col and not use_binary:
                if proficiency_col in row:
                    proficiency = self._map_proficiency(row[proficiency_col])
                else:
                    proficiency = self.config['transformation_options']['default_proficiency']
            else:
                proficiency = 1  # Binary skill representation
            
            # Assign skill to job
            job_arch.jobs[job_id].skills[skill_id] = proficiency
            assigned_count += 1
        
        logger.info(f"Assigned {assigned_count} skills to jobs (skipped {skipped_count} invalid mappings)")
        
        # Save the updated job architecture
        job_arch.to_file(jobs_file)
        logger.info(f"Updated job architecture saved to {jobs_file}")
        
        return job_arch
    
    def save_mapping_report(self):
        """Save a report of all mappings performed during transformation."""
        if not self.config.get('logging', {}).get('save_mapping_report', False):
            return
        
        report_path = self.config['logging']['mapping_report_path']
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        # Create report dataframe
        if not self.mapping_report:
            logger.info("No mappings to report")
            return
        
        report_df = pd.DataFrame(self.mapping_report)
        report_df['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save report
        report_df.to_csv(report_path, index=False)
        logger.info(f"Mapping report saved to {report_path}")

@click.group()
@click.option(
    "--config-file", 
    type=click.Path(exists=True),
    default="config/hris_schema_mapping.yaml",
    help="Path to schema mapping configuration file"
)
@click.pass_context
def cli(ctx, config_file):
    """Transform HRIS data into formats compatible with the Skill Similarity Engine."""
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config_file

@cli.command()
@click.pass_context
def transform_all(ctx):
    """Transform all HRIS data into engine formats."""
    config_file = ctx.obj['config_file']
    transformer = HRISTransformer(config_file)
    
    try:
        # Execute full transformation pipeline
        job_arch = transformer.transform_jobs()
        taxonomy = transformer.transform_skills()
        transformer.assign_skills_to_jobs(job_arch, taxonomy)
        transformer.save_mapping_report()
        
        click.echo("HRIS data transformation completed successfully!")
    except Exception as e:
        click.echo(f"Error during transformation: {str(e)}")
        sys.exit(1)

@cli.command()
@click.pass_context
def transform_jobs(ctx):
    """Transform only HRIS job data."""
    config_file = ctx.obj['config_file']
    transformer = HRISTransformer(config_file)
    
    try:
        transformer.transform_jobs()
        transformer.save_mapping_report()
        click.echo("Job data transformation completed successfully!")
    except Exception as e:
        click.echo(f"Error during job transformation: {str(e)}")
        sys.exit(1)

@cli.command()
@click.pass_context
def transform_skills(ctx):
    """Transform only HRIS skill data."""
    config_file = ctx.obj['config_file']
    transformer = HRISTransformer(config_file)
    
    try:
        transformer.transform_skills()
        click.echo("Skill data transformation completed successfully!")
    except Exception as e:
        click.echo(f"Error during skill transformation: {str(e)}")
        sys.exit(1)

@cli.command()
@click.pass_context
def assign_skills(ctx):
    """Assign skills to jobs based on HRIS mapping data."""
    config_file = ctx.obj['config_file']
    transformer = HRISTransformer(config_file)
    
    try:
        transformer.assign_skills_to_jobs()
        transformer.save_mapping_report()
        click.echo("Skill assignment completed successfully!")
    except Exception as e:
        click.echo(f"Error during skill assignment: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    cli() 