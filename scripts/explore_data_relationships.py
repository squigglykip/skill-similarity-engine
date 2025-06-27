#!/usr/bin/env python3
"""
Data Exploration & Relationship Analysis Script
===============================================

Analyzes relationships across 6 key datasets for NAB Skill Similarity Engine
to inform SQLite schema design for the Flask webapp.

Datasets analyzed:
1. job_data.csv (717 jobs from similarity engine)
2. job_skill_mapping.csv (40K+ job-skill relationships) 
3. dummy_job_architecture.csv (717 job architecture records)
4. position_job_mapping.csv (5K position-to-job mappings)
5. lightcast_skills_comprehensive.csv (38K+ Lightcast skills)
6. dummy_workforce_context.csv (5K workforce/employee records)
7. job_similarity_matrix.parquet (pre-computed job-to-job similarities)

Author: Data Exploration Phase 8.1.2
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataExplorer:
    """Comprehensive data exploration and relationship analysis"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.datasets = {}
        self.analysis_results = {}
        
    def load_datasets(self):
        """Load all 6 core datasets for analysis"""
        logger.info("Loading core datasets...")
        
        # Dataset paths
        dataset_paths = {
            'job_data': self.data_dir / 'input_data' / 'job_data.csv',
            'job_skill_mapping': self.data_dir / 'input_data' / 'job_skill_mapping.csv',
            'skill_data': self.data_dir / 'input_data' / 'skill_data.csv',
            'job_architecture': self.data_dir / 'job_architecture' / 'dummy_job_architecture.csv',
            'position_job_mapping': self.data_dir / 'job_architecture_to_positions_mapping' / 'position_job_mapping.csv',
            'lightcast_skills': self.data_dir / 'skills_library' / 'lightcast_skills_comprehensive.csv',
            'workforce_context': self.data_dir / 'workforce_context' / 'dummy_workforce_context.csv',
            'job_similarity_matrix': Path('models') / '2025-Q2' / 'precompute_20250608_132404' / 'job_similarity_matrix.parquet'
        }
        
        # Load each dataset
        for name, path in dataset_paths.items():
            if path.exists():
                try:
                    # Handle parquet files differently
                    if path.suffix.lower() == '.parquet':
                        df = pd.read_parquet(path)
                    else:
                        df = pd.read_csv(path)
                    self.datasets[name] = df
                    logger.info(f"âœ… Loaded {name}: {len(df):,} rows, {len(df.columns)} columns")
                except Exception as e:
                    logger.error(f"âŒ Failed to load {name}: {e}")
            else:
                logger.warning(f"âš ï¸  File not found: {path}")
    
    def analyze_dataset_structure(self, df: pd.DataFrame, name: str) -> dict:
        """Analyze structure and basic stats for a dataset"""
        
        analysis = {
            'name': name,
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'column_info': {},
            'data_quality': {},
            'key_fields': []
        }
        
        # Column analysis
        for col in df.columns:
            col_info = {
                'dtype': str(df[col].dtype),
                'non_null_count': df[col].notna().sum(),
                'null_count': df[col].isna().sum(),
                'null_percentage': (df[col].isna().sum() / len(df)) * 100,
                'unique_values': df[col].nunique(),
                'uniqueness_ratio': df[col].nunique() / len(df) if len(df) > 0 else 0
            }
            
            # Sample values (first 5 non-null)
            sample_values = df[col].dropna().head(5).tolist()
            col_info['sample_values'] = sample_values
            
            analysis['column_info'][col] = col_info
            
            # Identify potential key fields
            if col_info['uniqueness_ratio'] > 0.95:  # High uniqueness suggests primary key
                analysis['key_fields'].append(col)
        
        # Data quality summary
        analysis['data_quality'] = {
            'total_missing_values': df.isna().sum().sum(),
            'columns_with_missing': (df.isna().sum() > 0).sum(),
            'duplicate_rows': df.duplicated().sum(),
            'data_completeness': ((df.notna().sum().sum()) / (len(df) * len(df.columns))) * 100
        }
        
        return analysis
    
    def analyze_relationships(self):
        """Analyze relationships between datasets"""
        logger.info("Analyzing cross-dataset relationships...")
        
        relationships = {}
        
        # 1. Job Data Consistency Analysis
        if 'job_data' in self.datasets and 'job_architecture' in self.datasets:
            job_data_ids = set(self.datasets['job_data']['JobProfileID'])
            job_arch_ids = set(self.datasets['job_architecture']['JobProfileID'])
            
            relationships['job_consistency'] = {
                'job_data_unique_ids': len(job_data_ids),
                'job_architecture_unique_ids': len(job_arch_ids),
                'common_ids': len(job_data_ids.intersection(job_arch_ids)),
                'job_data_only': len(job_data_ids - job_arch_ids),
                'job_arch_only': len(job_arch_ids - job_data_ids),
                'overlap_percentage': (len(job_data_ids.intersection(job_arch_ids)) / len(job_data_ids.union(job_arch_ids))) * 100
            }
        
        # 2. Skills Library Overlap Analysis  
        if 'skill_data' in self.datasets and 'lightcast_skills' in self.datasets:
            existing_skills = set(self.datasets['skill_data']['Skill_Name'].str.lower())
            lightcast_skills = set(self.datasets['lightcast_skills']['name'].str.lower())
            
            relationships['skills_overlap'] = {
                'existing_skills_count': len(existing_skills),
                'lightcast_skills_count': len(lightcast_skills),
                'common_skills': len(existing_skills.intersection(lightcast_skills)),
                'existing_only': len(existing_skills - lightcast_skills),
                'lightcast_only': len(lightcast_skills - existing_skills),
                'overlap_percentage': (len(existing_skills.intersection(lightcast_skills)) / len(existing_skills.union(lightcast_skills))) * 100
            }
        
        # 3. Position-Job Mapping Analysis
        if 'position_job_mapping' in self.datasets and 'workforce_context' in self.datasets:
            mapping_positions = set(self.datasets['position_job_mapping']['Position_Number'])
            workforce_positions = set(self.datasets['workforce_context']['Position Number'])
            
            relationships['position_mapping'] = {
                'mapping_positions_count': len(mapping_positions),
                'workforce_positions_count': len(workforce_positions),
                'mapped_positions': len(mapping_positions.intersection(workforce_positions)),
                'unmapped_workforce': len(workforce_positions - mapping_positions),
                'orphaned_mappings': len(mapping_positions - workforce_positions),
                'coverage_percentage': (len(mapping_positions.intersection(workforce_positions)) / len(workforce_positions)) * 100
            }
        
        # 4. Job-Skill Mapping Coverage
        if 'job_skill_mapping' in self.datasets and 'job_data' in self.datasets:
            mapped_jobs = set(self.datasets['job_skill_mapping']['JobProfileID'])
            all_jobs = set(self.datasets['job_data']['JobProfileID'])
            
            relationships['job_skill_coverage'] = {
                'total_jobs': len(all_jobs),
                'jobs_with_skills': len(mapped_jobs),
                'jobs_without_skills': len(all_jobs - mapped_jobs),
                'skill_coverage_percentage': (len(mapped_jobs) / len(all_jobs)) * 100,
                'avg_skills_per_job': self.datasets['job_skill_mapping'].groupby('JobProfileID').size().mean()
            }
        
        # 5. Organizational Hierarchy Analysis
        if 'workforce_context' in self.datasets:
            df = self.datasets['workforce_context']
            org_levels = [col for col in df.columns if 'ORG UNIT' in col.upper()]
            
            relationships['org_hierarchy'] = {
                'total_org_levels': len(org_levels) // 2,  # Number and Name pairs
                'level_analysis': {}
            }
            
            # Analyze each org level
            for i in range(1, 11):  # ORG UNIT NO_1 to ORG UNIT NO_10
                no_col = f'ORG UNIT NO_{i}'
                name_col = f'ORG UNIT NAME_{i}'
                
                if no_col in df.columns and name_col in df.columns:
                    level_info = {
                        'unique_units': df[no_col].nunique(),
                        'completeness': (df[no_col].notna().sum() / len(df)) * 100,
                        'sample_units': df[name_col].dropna().unique()[:5].tolist()
                    }
                    relationships['org_hierarchy']['level_analysis'][f'level_{i}'] = level_info
        
        # 6. Job Similarity Matrix Analysis
        if 'job_similarity_matrix' in self.datasets:
            sim_df = self.datasets['job_similarity_matrix']
            unique_jobs_in_matrix = set(sim_df['job_from'].unique()) | set(sim_df['job_to'].unique())
            
            if 'job_data' in self.datasets:
                all_jobs = set(self.datasets['job_data']['JobProfileID'])
                
                relationships['similarity_matrix_coverage'] = {
                    'total_similarity_pairs': len(sim_df),
                    'unique_jobs_in_matrix': len(unique_jobs_in_matrix),
                    'jobs_in_job_data': len(all_jobs),
                    'matrix_job_coverage': len(unique_jobs_in_matrix.intersection(all_jobs)),
                    'coverage_percentage': (len(unique_jobs_in_matrix.intersection(all_jobs)) / len(all_jobs)) * 100,
                    'avg_similarity': float(sim_df['similarity'].mean()),
                    'min_similarity': float(sim_df['similarity'].min()),
                    'max_similarity': float(sim_df['similarity'].max()),
                    'similarity_distribution': {
                        'high_similarity_pairs': int((sim_df['similarity'] >= 0.8).sum()),
                        'medium_similarity_pairs': int(((sim_df['similarity'] >= 0.5) & (sim_df['similarity'] < 0.8)).sum()),
                        'low_similarity_pairs': int((sim_df['similarity'] < 0.5).sum())
                    }
                }
        
        self.analysis_results['relationships'] = relationships
        return relationships
    
    def analyze_schema_requirements(self):
        """Analyze requirements for optimal SQLite schema design"""
        logger.info("Analyzing schema design requirements...")
        
        schema_analysis = {
            'table_candidates': {},
            'index_recommendations': [],
            'normalization_suggestions': [],
            'performance_considerations': []
        }
        
        # Table structure recommendations
        if 'workforce_context' in self.datasets:
            df = self.datasets['workforce_context']
            
            # Organizational hierarchy normalization
            org_levels = [col for col in df.columns if 'ORG UNIT NO_' in col]
            if len(org_levels) > 3:  # More than 3 levels suggests normalization needed
                schema_analysis['normalization_suggestions'].append({
                    'table': 'organizational_hierarchy',
                    'reason': f'10-level org hierarchy should be normalized into separate table',
                    'suggested_structure': 'org_unit_id, parent_unit_id, level, unit_number, unit_name'
                })
        
        # Index recommendations based on likely query patterns
        schema_analysis['index_recommendations'].extend([
            {'table': 'jobs', 'columns': ['JobProfileID'], 'type': 'PRIMARY KEY'},
            {'table': 'jobs', 'columns': ['JobFamily', 'Location'], 'type': 'COMPOSITE INDEX'},
            {'table': 'employees', 'columns': ['Position_Number'], 'type': 'PRIMARY KEY'},
            {'table': 'employees', 'columns': ['People_Leader_Flag', 'Salary_Group'], 'type': 'COMPOSITE INDEX'},
            {'table': 'job_skill_mapping', 'columns': ['JobProfileID', 'Skill_ID'], 'type': 'COMPOSITE PRIMARY KEY'},
            {'table': 'skills', 'columns': ['skill_id'], 'type': 'PRIMARY KEY'},
            {'table': 'skills', 'columns': ['category_name', 'subcategory_name'], 'type': 'COMPOSITE INDEX'}
        ])
        
        # Performance considerations
        if 'job_skill_mapping' in self.datasets:
            mapping_count = len(self.datasets['job_skill_mapping'])
            if mapping_count > 30000:
                schema_analysis['performance_considerations'].append(
                    f"Large job-skill mapping table ({mapping_count:,} rows) - consider partitioning or materialized views"
                )
        
        self.analysis_results['schema_analysis'] = schema_analysis
        return schema_analysis
    
    def generate_join_strategies(self):
        """Analyze and recommend optimal JOIN strategies"""
        logger.info("Analyzing JOIN strategies...")
        
        join_strategies = {}
        
        # Core job data joins
        join_strategies['job_data_integration'] = {
            'primary_table': 'job_architecture',
            'joins': [
                {
                    'table': 'job_data',
                    'join_type': 'LEFT JOIN',
                    'condition': 'job_architecture.JobProfileID = job_data.JobProfileID',
                    'purpose': 'Add location and leadership info to job architecture'
                },
                {
                    'table': 'job_skill_mapping',
                    'join_type': 'LEFT JOIN', 
                    'condition': 'job_architecture.JobProfileID = job_skill_mapping.JobProfileID',
                    'purpose': 'Connect jobs to their required skills'
                }
            ]
        }
        
        # Workforce to job mapping
        join_strategies['workforce_integration'] = {
            'primary_table': 'workforce_context',
            'joins': [
                {
                    'table': 'position_job_mapping',
                    'join_type': 'INNER JOIN',
                    'condition': 'workforce_context.Position_Number = position_job_mapping.Position_Number',
                    'purpose': 'Connect employees to job profiles'
                },
                {
                    'table': 'job_architecture',
                    'join_type': 'INNER JOIN',
                    'condition': 'position_job_mapping.JobProfileID = job_architecture.JobProfileID',
                    'purpose': 'Get job family and hierarchy information'
                }
            ]
        }
        
        # Skills integration strategy
        join_strategies['skills_integration'] = {
            'strategy': 'UNION with skill source indicator',
            'rationale': 'Low overlap between existing and Lightcast skills suggests separate sources',
            'implementation': 'CREATE VIEW unified_skills AS SELECT skill_id, skill_name, "existing" as source FROM skill_data UNION ALL SELECT skill_id, name, "lightcast" as source FROM lightcast_skills'
        }
        
        self.analysis_results['join_strategies'] = join_strategies
        return join_strategies
    
    def print_analysis_summary(self):
        """Print comprehensive analysis summary"""
        print("\n" + "="*80)
        print("NAB SKILL SIMILARITY ENGINE - DATA EXPLORATION SUMMARY")
        print("="*80)
        print(f"Analysis conducted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total datasets analyzed: {len(self.datasets)}")
        
        # Dataset overview
        print("\nðŸ“Š DATASET OVERVIEW")
        print("-" * 50)
        for name, df in self.datasets.items():
            analysis = self.analyze_dataset_structure(df, name)
            print(f"â€¢ {name.upper()}")
            print(f"  â”œâ”€ Rows: {analysis['rows']:,}")
            print(f"  â”œâ”€ Columns: {analysis['columns']}")
            print(f"  â”œâ”€ Memory: {analysis['memory_usage_mb']:.1f} MB")
            print(f"  â”œâ”€ Data Completeness: {analysis['data_quality']['data_completeness']:.1f}%")
            print(f"  â””â”€ Key Fields: {', '.join(analysis['key_fields']) if analysis['key_fields'] else 'None detected'}")
        
        # Relationship analysis
        if 'relationships' in self.analysis_results:
            print("\nðŸ”— RELATIONSHIP ANALYSIS")
            print("-" * 50)
            
            rel = self.analysis_results['relationships']
            
            if 'job_consistency' in rel:
                jc = rel['job_consistency']
                print(f"â€¢ Job Data Consistency:")
                print(f"  â”œâ”€ JobProfileID overlap: {jc['overlap_percentage']:.1f}%")
                print(f"  â”œâ”€ Common IDs: {jc['common_ids']:,}")
                print(f"  â””â”€ Unique to each: {jc['job_data_only']:,} | {jc['job_arch_only']:,}")
            
            if 'skills_overlap' in rel:
                so = rel['skills_overlap']
                print(f"â€¢ Skills Library Overlap:")
                print(f"  â”œâ”€ Name-based overlap: {so['overlap_percentage']:.1f}%")
                print(f"  â”œâ”€ Existing skills: {so['existing_skills_count']:,}")
                print(f"  â””â”€ Lightcast skills: {so['lightcast_skills_count']:,}")
            
            if 'position_mapping' in rel:
                pm = rel['position_mapping']
                print(f"â€¢ Position-Job Mapping:")
                print(f"  â”œâ”€ Coverage: {pm['coverage_percentage']:.1f}%")
                print(f"  â”œâ”€ Mapped positions: {pm['mapped_positions']:,}")
                print(f"  â””â”€ Unmapped workforce: {pm['unmapped_workforce']:,}")
            
            if 'job_skill_coverage' in rel:
                jsc = rel['job_skill_coverage']
                print(f"â€¢ Job-Skill Coverage:")
                print(f"  â”œâ”€ Jobs with skills: {jsc['skill_coverage_percentage']:.1f}%")
                print(f"  â””â”€ Avg skills per job: {jsc['avg_skills_per_job']:.1f}")
            
            if 'similarity_matrix_coverage' in rel:
                smc = rel['similarity_matrix_coverage']
                print(f"â€¢ Job Similarity Matrix:")
                print(f"  â”œâ”€ Total pairs: {smc['total_similarity_pairs']:,}")
                print(f"  â”œâ”€ Job coverage: {smc['coverage_percentage']:.1f}%")
                print(f"  â”œâ”€ Avg similarity: {smc['avg_similarity']:.3f}")
                print(f"  â””â”€ High similarity pairs (â‰¥0.8): {smc['similarity_distribution']['high_similarity_pairs']:,}")
        
        # Schema recommendations
        if 'schema_analysis' in self.analysis_results:
            print("\nðŸ—ï¸  SCHEMA DESIGN RECOMMENDATIONS")
            print("-" * 50)
            
            schema = self.analysis_results['schema_analysis']
            
            print("â€¢ Normalization Needs:")
            for suggestion in schema['normalization_suggestions']:
                print(f"  â”œâ”€ {suggestion['table']}: {suggestion['reason']}")
            
            print("â€¢ Key Indexes Required:")
            for idx in schema['index_recommendations'][:5]:  # Show first 5
                print(f"  â”œâ”€ {idx['table']}.{', '.join(idx['columns'])} ({idx['type']})")
            
            print("â€¢ Performance Considerations:")
            for consideration in schema['performance_considerations']:
                print(f"  â””â”€ {consideration}")
        
        # Integration strategies
        if 'join_strategies' in self.analysis_results:
            print("\nðŸ”„ INTEGRATION STRATEGIES")
            print("-" * 50)
            
            strategies = self.analysis_results['join_strategies']
            
            print("â€¢ Primary Integration Patterns:")
            for strategy_name, strategy in strategies.items():
                if isinstance(strategy, dict) and 'primary_table' in strategy:
                    print(f"  â”œâ”€ {strategy_name}: {strategy['primary_table']} as base")
                elif isinstance(strategy, dict) and 'strategy' in strategy:
                    print(f"  â”œâ”€ {strategy_name}: {strategy['strategy']}")
        
        print("\nâœ… Analysis Complete!")
        print("   Next steps: Use this analysis to design SQLite schema in docs/sqlite_schema_design.md")
        print("="*80)

def main():
    """Main execution function"""
    # Initialize explorer
    explorer = DataExplorer()
    
    # Load all datasets
    explorer.load_datasets()
    
    if not explorer.datasets:
        logger.error("No datasets loaded. Check file paths and try again.")
        return
    
    # Run comprehensive analysis
    explorer.analyze_relationships()
    explorer.analyze_schema_requirements()
    explorer.generate_join_strategies()
    
    # Print summary
    explorer.print_analysis_summary()
    
    # Export detailed analysis to JSON for reference
    analysis_file = "data_exploration_analysis.json"
    
    # Prepare serializable data
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'dataset_summaries': {},
        'relationships': explorer.analysis_results.get('relationships', {}),
        'schema_analysis': explorer.analysis_results.get('schema_analysis', {}),
        'join_strategies': explorer.analysis_results.get('join_strategies', {})
    }
    
    # Add dataset summaries
    for name, df in explorer.datasets.items():
        analysis = explorer.analyze_dataset_structure(df, name)
        export_data['dataset_summaries'][name] = analysis
    
    try:
        with open(analysis_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=lambda x: str(x) if not isinstance(x, (str, int, float, bool, type(None))) else x)
        logger.info(f"ðŸ“„ Detailed analysis exported to: {analysis_file}")
    except Exception as e:
        logger.warning(f"Could not export analysis: {e}")

if __name__ == "__main__":
    main()
