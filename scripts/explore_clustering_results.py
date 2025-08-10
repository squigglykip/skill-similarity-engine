#!/usr/bin/env python3
"""
Clustering Results Explorer
===========================

Comprehensive exploration script for the clustering analytics tables populated by the
NAB Workforce Intelligence platform. This script provides detailed insights into:

- Job families clustering results
- Skill bundles clustering results  
- Bundle characteristics and metadata
- Cluster quality metrics and distributions
- Data validation and integrity checks

Usage:
    python scripts/explore_clustering_results.py

Output:
    Detailed console report of clustering results with statistics and sample data
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import json
from collections import defaultdict, Counter

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class ClusteringResultsExplorer:
    """Comprehensive explorer for clustering analytics results."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Tables to explore
        self.clustering_tables = [
            'analytics_job_families',
            'analytics_skill_bundles', 
            'analytics_bundle_characteristics'
        ]
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
    
    def check_table_existence(self) -> Dict[str, bool]:
        """Check which clustering tables exist and have data."""
        results = {}
        
        for table_name in self.clustering_tables:
            try:
                # Check if table exists
                cursor = self.conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                
                table_exists = cursor.fetchone() is not None
                
                if table_exists:
                    # Check if table has data
                    cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    results[table_name] = {'exists': True, 'row_count': row_count}
                else:
                    results[table_name] = {'exists': False, 'row_count': 0}
                    
            except sqlite3.Error as e:
                results[table_name] = {'exists': False, 'error': str(e), 'row_count': 0}
        
        return results
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get detailed schema information for a table."""
        try:
            cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
            columns = []
            
            for row in cursor.fetchall():
                columns.append({
                    'name': row[1],
                    'type': row[2],
                    'not_null': bool(row[3]),
                    'default_value': row[4],
                    'is_primary_key': bool(row[5])
                })
            
            return columns
            
        except sqlite3.Error:
            return []
    
    def explore_job_families_table(self) -> Dict[str, Any]:
        """Comprehensive exploration of analytics_job_families table."""
        table_name = 'analytics_job_families'
        results = {
            'table_name': table_name,
            'schema': self.get_table_schema(table_name),
            'basic_stats': {},
            'cluster_analysis': {},
            'quality_metrics': {},
            'sample_data': []
        }
        
        try:
            # Basic statistics
            cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cursor.fetchone()[0]
            
            cursor = self.conn.execute(f"SELECT COUNT(DISTINCT cluster_id) FROM {table_name}")
            unique_clusters = cursor.fetchone()[0]
            
            cursor = self.conn.execute(f"SELECT COUNT(DISTINCT job_profile_id) FROM {table_name}")
            unique_jobs = cursor.fetchone()[0]
            
            results['basic_stats'] = {
                'total_records': total_records,
                'unique_clusters': unique_clusters,
                'unique_jobs': unique_jobs
            }
            
            # Cluster size distribution
            cursor = self.conn.execute(f"""
                SELECT cluster_id, cluster_name, cluster_size, 
                       cluster_confidence, silhouette_score, analysis_date
                FROM {table_name}
                GROUP BY cluster_id, cluster_name, cluster_size, 
                         cluster_confidence, silhouette_score, analysis_date
                ORDER BY cluster_size DESC
            """)
            
            cluster_info = []
            for row in cursor.fetchall():
                cluster_info.append({
                    'cluster_id': row[0],
                    'cluster_name': row[1],
                    'cluster_size': row[2],
                    'cluster_confidence': row[3],
                    'silhouette_score': row[4],
                    'analysis_date': row[5]
                })
            
            results['cluster_analysis'] = {
                'cluster_details': cluster_info,
                'size_distribution': self._analyze_cluster_sizes(cluster_info),
                'confidence_distribution': self._analyze_confidence_scores(cluster_info)
            }
            
            # Quality metrics analysis
            if cluster_info:
                silhouette_scores = [c['silhouette_score'] for c in cluster_info if c['silhouette_score'] is not None]
                confidence_scores = [c['cluster_confidence'] for c in cluster_info if c['cluster_confidence'] is not None]
                
                results['quality_metrics'] = {
                    'avg_silhouette_score': sum(silhouette_scores) / len(silhouette_scores) if silhouette_scores else 0,
                    'min_silhouette_score': min(silhouette_scores) if silhouette_scores else 0,
                    'max_silhouette_score': max(silhouette_scores) if silhouette_scores else 0,
                    'avg_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                    'min_confidence': min(confidence_scores) if confidence_scores else 0,
                    'max_confidence': max(confidence_scores) if confidence_scores else 0
                }
            
            # Sample data
            cursor = self.conn.execute(f"""
                SELECT job_profile_id, job_profile, cluster_id, cluster_name, 
                       cluster_confidence, job_function, job_category
                FROM {table_name}
                ORDER BY cluster_id, cluster_confidence DESC
                LIMIT 20
            """)
            
            results['sample_data'] = [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            results['error'] = str(e)
        
        return results
    
    def explore_skill_bundles_table(self) -> Dict[str, Any]:
        """Comprehensive exploration of analytics_skill_bundles table."""
        table_name = 'analytics_skill_bundles'
        results = {
            'table_name': table_name,
            'schema': self.get_table_schema(table_name),
            'basic_stats': {},
            'bundle_analysis': {},
            'sample_data': []
        }
        
        try:
            # Basic statistics
            cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cursor.fetchone()[0]
            
            cursor = self.conn.execute(f"SELECT COUNT(DISTINCT bundle_id) FROM {table_name}")
            unique_bundles = cursor.fetchone()[0]
            
            cursor = self.conn.execute(f"SELECT COUNT(DISTINCT skill_id) FROM {table_name}")
            unique_skills = cursor.fetchone()[0]
            
            results['basic_stats'] = {
                'total_records': total_records,
                'unique_bundles': unique_bundles,
                'unique_skills': unique_skills
            }
            
            # Bundle size distribution
            cursor = self.conn.execute(f"""
                SELECT bundle_id, bundle_name, COUNT(*) as bundle_size,
                       MIN(specialization_score) as min_specialization,
                       MAX(specialization_score) as max_specialization,
                       AVG(specialization_score) as avg_specialization
                FROM {table_name}
                GROUP BY bundle_id, bundle_name
                ORDER BY bundle_size DESC
            """)
            
            bundle_info = []
            for row in cursor.fetchall():
                bundle_info.append({
                    'bundle_id': row[0],
                    'bundle_name': row[1],
                    'bundle_size': row[2],
                    'min_specialization': row[3],
                    'max_specialization': row[4],
                    'avg_specialization': row[5]
                })
            
            results['bundle_analysis'] = {
                'bundle_details': bundle_info,
                'size_distribution': self._analyze_bundle_sizes(bundle_info)
            }
            
            # Sample data
            cursor = self.conn.execute(f"""
                SELECT skill_id, skill_name, bundle_id, bundle_name, 
                       specialization_score, skill_category
                FROM {table_name}
                ORDER BY bundle_id, specialization_score DESC
                LIMIT 30
            """)
            
            results['sample_data'] = [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            results['error'] = str(e)
        
        return results
    
    def explore_bundle_characteristics_table(self) -> Dict[str, Any]:
        """Comprehensive exploration of analytics_bundle_characteristics table."""
        table_name = 'analytics_bundle_characteristics'
        results = {
            'table_name': table_name,
            'schema': self.get_table_schema(table_name),
            'basic_stats': {},
            'characteristics_analysis': {},
            'sample_data': []
        }
        
        try:
            # Basic statistics
            cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cursor.fetchone()[0]
            
            cursor = self.conn.execute(f"SELECT COUNT(DISTINCT cluster_id) FROM {table_name}")
            unique_clusters = cursor.fetchone()[0]
            
            results['basic_stats'] = {
                'total_records': total_records,
                'unique_clusters': unique_clusters
            }
            
            # Characteristics analysis
            cursor = self.conn.execute(f"""
                SELECT cluster_id, cluster_name, cluster_description, 
                       cluster_size, cluster_confidence, silhouette_score,
                       intra_cluster_similarity, inter_cluster_distance,
                       clustering_algorithm, algorithm_parameters
                FROM {table_name}
                ORDER BY cluster_size DESC
            """)
            
            characteristics = []
            for row in cursor.fetchall():
                characteristics.append({
                    'cluster_id': row[0],
                    'cluster_name': row[1],
                    'cluster_description': row[2],
                    'cluster_size': row[3],
                    'cluster_confidence': row[4],
                    'silhouette_score': row[5],
                    'intra_cluster_similarity': row[6],
                    'inter_cluster_distance': row[7],
                    'clustering_algorithm': row[8],
                    'algorithm_parameters': row[9]
                })
            
            results['characteristics_analysis'] = {
                'cluster_characteristics': characteristics,
                'algorithm_summary': self._analyze_algorithm_usage(characteristics)
            }
            
            # Sample data (all records since this is metadata)
            cursor = self.conn.execute(f"""
                SELECT *
                FROM {table_name}
                ORDER BY cluster_size DESC
            """)
            
            results['sample_data'] = [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            results['error'] = str(e)
        
        return results
    
    def _analyze_cluster_sizes(self, cluster_info: List[Dict]) -> Dict[str, Any]:
        """Analyze cluster size distribution."""
        sizes = [c['cluster_size'] for c in cluster_info if c['cluster_size'] is not None]
        
        if not sizes:
            return {}
        
        size_distribution = Counter()
        for size in sizes:
            if size <= 5:
                size_distribution['small (≤5)'] += 1
            elif size <= 15:
                size_distribution['medium (6-15)'] += 1
            elif size <= 30:
                size_distribution['large (16-30)'] += 1
            else:
                size_distribution['very_large (>30)'] += 1
        
        return {
            'total_clusters': len(sizes),
            'avg_size': sum(sizes) / len(sizes),
            'min_size': min(sizes),
            'max_size': max(sizes),
            'size_categories': dict(size_distribution)
        }
    
    def _analyze_bundle_sizes(self, bundle_info: List[Dict]) -> Dict[str, Any]:
        """Analyze bundle size distribution."""
        sizes = [b['bundle_size'] for b in bundle_info if b['bundle_size'] is not None]
        
        if not sizes:
            return {}
        
        size_distribution = Counter()
        for size in sizes:
            if size <= 3:
                size_distribution['small (≤3)'] += 1
            elif size <= 8:
                size_distribution['medium (4-8)'] += 1
            elif size <= 15:
                size_distribution['large (9-15)'] += 1
            else:
                size_distribution['very_large (>15)'] += 1
        
        return {
            'total_bundles': len(sizes),
            'avg_size': sum(sizes) / len(sizes),
            'min_size': min(sizes),
            'max_size': max(sizes),
            'size_categories': dict(size_distribution)
        }
    
    def _analyze_confidence_scores(self, cluster_info: List[Dict]) -> Dict[str, Any]:
        """Analyze confidence score distribution."""
        scores = [c['cluster_confidence'] for c in cluster_info if c['cluster_confidence'] is not None]
        
        if not scores:
            return {}
        
        confidence_distribution = Counter()
        for score in scores:
            if score < 0.3:
                confidence_distribution['low (<0.3)'] += 1
            elif score < 0.6:
                confidence_distribution['medium (0.3-0.6)'] += 1
            elif score < 0.8:
                confidence_distribution['high (0.6-0.8)'] += 1
            else:
                confidence_distribution['very_high (≥0.8)'] += 1
        
        return {
            'avg_confidence': sum(scores) / len(scores),
            'min_confidence': min(scores),
            'max_confidence': max(scores),
            'confidence_categories': dict(confidence_distribution)
        }
    
    def _analyze_algorithm_usage(self, characteristics: List[Dict]) -> Dict[str, Any]:
        """Analyze clustering algorithm usage."""
        algorithms = [c['clustering_algorithm'] for c in characteristics if c['clustering_algorithm']]
        parameters = [c['algorithm_parameters'] for c in characteristics if c['algorithm_parameters']]
        
        algorithm_counts = Counter(algorithms)
        parameter_counts = Counter(parameters)
        
        return {
            'algorithm_distribution': dict(algorithm_counts),
            'parameter_distribution': dict(parameter_counts)
        }
    
    def validate_clustering_integrity(self) -> Dict[str, Any]:
        """Validate data integrity across clustering tables."""
        validation_results = {
            'job_families_validation': {},
            'skill_bundles_validation': {},
            'cross_table_validation': {}
        }
        
        try:
            # Job families validation
            cursor = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT job_profile_id) as unique_jobs,
                    COUNT(DISTINCT cluster_id) as unique_clusters,
                    COUNT(CASE WHEN cluster_name IS NULL OR cluster_name = '' THEN 1 END) as missing_cluster_names,
                    COUNT(CASE WHEN cluster_confidence IS NULL THEN 1 END) as missing_confidence,
                    COUNT(CASE WHEN silhouette_score IS NULL THEN 1 END) as missing_silhouette
                FROM analytics_job_families
            """)
            
            row = cursor.fetchone()
            if row:
                validation_results['job_families_validation'] = {
                    'total_records': row[0],
                    'unique_jobs': row[1],
                    'unique_clusters': row[2],
                    'missing_cluster_names': row[3],
                    'missing_confidence': row[4],
                    'missing_silhouette': row[5],
                    'data_completeness': {
                        'cluster_names': (row[0] - row[3]) / row[0] * 100 if row[0] > 0 else 0,
                        'confidence_scores': (row[0] - row[4]) / row[0] * 100 if row[0] > 0 else 0,
                        'silhouette_scores': (row[0] - row[5]) / row[0] * 100 if row[0] > 0 else 0
                    }
                }
            
            # Skill bundles validation
            cursor = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT skill_id) as unique_skills,
                    COUNT(DISTINCT bundle_id) as unique_bundles,
                    COUNT(CASE WHEN bundle_name IS NULL OR bundle_name = '' THEN 1 END) as missing_bundle_names,
                    COUNT(CASE WHEN specialization_score IS NULL THEN 1 END) as missing_specialization
                FROM analytics_skill_bundles
            """)
            
            row = cursor.fetchone()
            if row:
                validation_results['skill_bundles_validation'] = {
                    'total_records': row[0],
                    'unique_skills': row[1],
                    'unique_bundles': row[2],
                    'missing_bundle_names': row[3],
                    'missing_specialization': row[4],
                    'data_completeness': {
                        'bundle_names': (row[0] - row[3]) / row[0] * 100 if row[0] > 0 else 0,
                        'specialization_scores': (row[0] - row[4]) / row[0] * 100 if row[0] > 0 else 0
                    }
                }
            
            # Cross-table validation
            # Check if cluster_ids match between job_families and bundle_characteristics
            cursor = self.conn.execute("""
                SELECT COUNT(DISTINCT jf.cluster_id) as job_family_clusters,
                       COUNT(DISTINCT bc.cluster_id) as characteristic_clusters
                FROM analytics_job_families jf
                CROSS JOIN analytics_bundle_characteristics bc
            """)
            
            row = cursor.fetchone()
            if row:
                validation_results['cross_table_validation'] = {
                    'job_family_clusters': row[0],
                    'characteristic_clusters': row[1]
                }
            
        except sqlite3.Error as e:
            validation_results['error'] = str(e)
        
        return validation_results
    
    def generate_clustering_summary(self) -> Dict[str, Any]:
        """Generate comprehensive clustering results summary."""
        summary = {
            'analysis_timestamp': datetime.now().isoformat(),
            'database_path': str(self.db_path),
            'table_status': self.check_table_existence(),
            'data_validation': self.validate_clustering_integrity()
        }
        
        # Explore each table if it exists and has data
        for table_name in self.clustering_tables:
            if summary['table_status'][table_name]['exists'] and summary['table_status'][table_name]['row_count'] > 0:
                if table_name == 'analytics_job_families':
                    summary['job_families_analysis'] = self.explore_job_families_table()
                elif table_name == 'analytics_skill_bundles':
                    summary['skill_bundles_analysis'] = self.explore_skill_bundles_table()
                elif table_name == 'analytics_bundle_characteristics':
                    summary['bundle_characteristics_analysis'] = self.explore_bundle_characteristics_table()
        
        return summary


def print_exploration_results(results: Dict[str, Any]):
    """Print comprehensive exploration results in a readable format."""
    
    print("🧩 NAB Workforce Intelligence - Clustering Results Explorer")
    print("=" * 70)
    print(f"📊 Analysis Date: {results['analysis_timestamp']}")
    print(f"📂 Database: {results['database_path']}")
    print()
    
    # Table Status Overview
    print("📋 TABLE STATUS OVERVIEW")
    print("-" * 30)
    
    for table_name, status in results['table_status'].items():
        if status['exists']:
            print(f"✅ {table_name}: {status['row_count']:,} records")
        else:
            print(f"❌ {table_name}: Not found or empty")
            if 'error' in status:
                print(f"   Error: {status['error']}")
    
    print()
    
    # Data Validation Summary
    if 'data_validation' in results:
        print("🔍 DATA VALIDATION SUMMARY")
        print("-" * 30)
        
        validation = results['data_validation']
        
        if 'job_families_validation' in validation:
            jf_val = validation['job_families_validation']
            print(f"📊 Job Families Table:")
            print(f"   • Total Records: {jf_val.get('total_records', 0):,}")
            print(f"   • Unique Jobs: {jf_val.get('unique_jobs', 0):,}")
            print(f"   • Unique Clusters: {jf_val.get('unique_clusters', 0):,}")
            if 'data_completeness' in jf_val:
                completeness = jf_val['data_completeness']
                print(f"   • Data Completeness:")
                print(f"     - Cluster Names: {completeness.get('cluster_names', 0):.1f}%")
                print(f"     - Confidence Scores: {completeness.get('confidence_scores', 0):.1f}%")
                print(f"     - Silhouette Scores: {completeness.get('silhouette_scores', 0):.1f}%")
            print()
        
        if 'skill_bundles_validation' in validation:
            sb_val = validation['skill_bundles_validation']
            print(f"🎯 Skill Bundles Table:")
            print(f"   • Total Records: {sb_val.get('total_records', 0):,}")
            print(f"   • Unique Skills: {sb_val.get('unique_skills', 0):,}")
            print(f"   • Unique Bundles: {sb_val.get('unique_bundles', 0):,}")
            if 'data_completeness' in sb_val:
                completeness = sb_val['data_completeness']
                print(f"   • Data Completeness:")
                print(f"     - Bundle Names: {completeness.get('bundle_names', 0):.1f}%")
                print(f"     - Specialization Scores: {completeness.get('specialization_scores', 0):.1f}%")
            print()
    
    # Job Families Analysis
    if 'job_families_analysis' in results:
        print("👥 JOB FAMILIES CLUSTERING ANALYSIS")
        print("-" * 40)
        
        jf_analysis = results['job_families_analysis']
        
        if 'basic_stats' in jf_analysis:
            stats = jf_analysis['basic_stats']
            print(f"📊 Basic Statistics:")
            print(f"   • Total Job Assignments: {stats.get('total_records', 0):,}")
            print(f"   • Unique Job Profiles: {stats.get('unique_jobs', 0):,}")
            print(f"   • Total Job Families: {stats.get('unique_clusters', 0):,}")
            print()
        
        if 'cluster_analysis' in jf_analysis:
            cluster_analysis = jf_analysis['cluster_analysis']
            
            if 'size_distribution' in cluster_analysis:
                size_dist = cluster_analysis['size_distribution']
                print(f"📏 Cluster Size Distribution:")
                print(f"   • Average Cluster Size: {size_dist.get('avg_size', 0):.1f} jobs")
                print(f"   • Size Range: {size_dist.get('min_size', 0)} - {size_dist.get('max_size', 0)} jobs")
                if 'size_categories' in size_dist:
                    print(f"   • Size Categories:")
                    for category, count in size_dist['size_categories'].items():
                        print(f"     - {category}: {count} clusters")
                print()
            
            if 'confidence_distribution' in cluster_analysis:
                conf_dist = cluster_analysis['confidence_distribution']
                print(f"🎯 Confidence Score Distribution:")
                print(f"   • Average Confidence: {conf_dist.get('avg_confidence', 0):.3f}")
                print(f"   • Confidence Range: {conf_dist.get('min_confidence', 0):.3f} - {conf_dist.get('max_confidence', 0):.3f}")
                if 'confidence_categories' in conf_dist:
                    print(f"   • Confidence Categories:")
                    for category, count in conf_dist['confidence_categories'].items():
                        print(f"     - {category}: {count} clusters")
                print()
        
        if 'quality_metrics' in jf_analysis:
            quality = jf_analysis['quality_metrics']
            print(f"📈 Quality Metrics:")
            print(f"   • Average Silhouette Score: {quality.get('avg_silhouette_score', 0):.3f}")
            print(f"   • Silhouette Range: {quality.get('min_silhouette_score', 0):.3f} - {quality.get('max_silhouette_score', 0):.3f}")
            print()
        
        # Top 10 clusters by size
        if 'cluster_analysis' in jf_analysis and 'cluster_details' in jf_analysis['cluster_analysis']:
            clusters = jf_analysis['cluster_analysis']['cluster_details'][:10]
            print(f"🏆 Top 10 Largest Job Families:")
            for i, cluster in enumerate(clusters, 1):
                print(f"   {i:2d}. {cluster.get('cluster_name', 'Unnamed')} (ID: {cluster.get('cluster_id', 'N/A')})")
                print(f"       Size: {cluster.get('cluster_size', 0)} jobs | Confidence: {cluster.get('cluster_confidence', 0):.3f}")
            print()
    
    # Skill Bundles Analysis
    if 'skill_bundles_analysis' in results:
        print("🎯 SKILL BUNDLES CLUSTERING ANALYSIS")
        print("-" * 40)
        
        sb_analysis = results['skill_bundles_analysis']
        
        if 'basic_stats' in sb_analysis:
            stats = sb_analysis['basic_stats']
            print(f"📊 Basic Statistics:")
            print(f"   • Total Skill Assignments: {stats.get('total_records', 0):,}")
            print(f"   • Unique Skills: {stats.get('unique_skills', 0):,}")
            print(f"   • Total Skill Bundles: {stats.get('unique_bundles', 0):,}")
            print()
        
        if 'bundle_analysis' in sb_analysis:
            bundle_analysis = sb_analysis['bundle_analysis']
            
            if 'size_distribution' in bundle_analysis:
                size_dist = bundle_analysis['size_distribution']
                print(f"📏 Bundle Size Distribution:")
                print(f"   • Average Bundle Size: {size_dist.get('avg_size', 0):.1f} skills")
                print(f"   • Size Range: {size_dist.get('min_size', 0)} - {size_dist.get('max_size', 0)} skills")
                if 'size_categories' in size_dist:
                    print(f"   • Size Categories:")
                    for category, count in size_dist['size_categories'].items():
                        print(f"     - {category}: {count} bundles")
                print()
            
            # Top 10 bundles by size
            if 'bundle_details' in bundle_analysis:
                bundles = bundle_analysis['bundle_details'][:10]
                print(f"🏆 Top 10 Largest Skill Bundles:")
                for i, bundle in enumerate(bundles, 1):
                    print(f"   {i:2d}. {bundle.get('bundle_name', 'Unnamed')} (ID: {bundle.get('bundle_id', 'N/A')})")
                    print(f"       Size: {bundle.get('bundle_size', 0)} skills | Avg Specialization: {bundle.get('avg_specialization', 0):.3f}")
                print()
    
    # Bundle Characteristics Analysis
    if 'bundle_characteristics_analysis' in results:
        print("📋 BUNDLE CHARACTERISTICS ANALYSIS")
        print("-" * 40)
        
        bc_analysis = results['bundle_characteristics_analysis']
        
        if 'basic_stats' in bc_analysis:
            stats = bc_analysis['basic_stats']
            print(f"📊 Basic Statistics:")
            print(f"   • Total Characteristic Records: {stats.get('total_records', 0):,}")
            print(f"   • Unique Clusters: {stats.get('unique_clusters', 0):,}")
            print()
        
        if 'characteristics_analysis' in bc_analysis:
            char_analysis = bc_analysis['characteristics_analysis']
            
            if 'algorithm_summary' in char_analysis:
                algo_summary = char_analysis['algorithm_summary']
                print(f"🔬 Clustering Algorithm Summary:")
                if 'algorithm_distribution' in algo_summary:
                    print(f"   • Algorithms Used:")
                    for algo, count in algo_summary['algorithm_distribution'].items():
                        print(f"     - {algo}: {count} clusters")
                if 'parameter_distribution' in algo_summary:
                    print(f"   • Parameter Configurations:")
                    for params, count in algo_summary['parameter_distribution'].items():
                        print(f"     - {params}: {count} clusters")
                print()
    
    print("✅ Clustering exploration completed!")
    print(f"📊 Run python main.py → Option 7 to refresh clustering results")
    print(f"🎨 Ready for visualization implementation (Map of Reddit style)")


def main():
    """Main execution function."""
    # Find database file
    project_root = Path(__file__).parent.parent
    db_path = project_root / "models" / "2025-Q3" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("💡 Run 'python main.py' → Option 2 to generate the business context database first")
        return 1
    
    try:
        with ClusteringResultsExplorer(str(db_path)) as explorer:
            print("🔍 Exploring clustering results...")
            results = explorer.generate_clustering_summary()
            print_exploration_results(results)
            
        return 0
        
    except Exception as e:
        print(f"❌ Error exploring clustering results: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())