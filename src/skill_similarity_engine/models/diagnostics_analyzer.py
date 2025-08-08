#!/usr/bin/env python3
"""
Job Architecture & Skills Taxonomy Diagnostics Analyzer
========================================================

Modularized diagnostic measures for evaluating the health of the NAB job 
architecture and associated skills taxonomy. Provides actionable insights for 
HR stakeholders on taxonomic drift, functional distinctiveness, and governance.

Key Diagnostics:
- Silhouette Score Analysis (functional cohesion and separation)
- Skill Similarity Measures (redundancy detection)
- Graph-Based Structural Analysis (community detection)
- Entropy and Diversity Metrics (specialization vs generalization)

Output: CLI-focused reports with HR-friendly interpretations and actionable insights
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, Counter
import networkx as nx
from scipy import stats
from sklearn.metrics import silhouette_score, silhouette_samples, jaccard_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN

try:
    import community as community_louvain
except ImportError:
    community_louvain = None

warnings.filterwarnings('ignore')


class DiagnosticConfig:
    """Configuration for job architecture diagnostics"""
    
    # Diagnostic thresholds (HR-friendly interpretation boundaries)
    SILHOUETTE_THRESHOLDS = {
        'excellent': 0.7,      # Strong cohesion
        'good': 0.4,           # Mixed differentiation  
        'poor': 0.3            # Weak taxonomy integrity
    }
    
    SIMILARITY_THRESHOLDS = {
        'near_duplicate_jaccard': 0.85,     # Potential redundant roles
        'near_duplicate_cosine': 0.9,       # Semantic redundancy
        'low_variance': 0.1                 # Overfitted role families
    }
    
    DIVERSITY_THRESHOLDS = {
        'high_entropy': 4.0,              # Unfocused roles
        'low_entropy': 1.5,               # Over-specialized roles
        'skill_churn': 0.3                # Excessive skill turnover
    }
    
    # Analysis parameters
    MIN_JOBS_FOR_BU_ANALYSIS = 5         # Minimum jobs per BU for analysis
    TOP_N_ISSUES = 10                     # Top issues to highlight
    BRIDGE_SKILL_THRESHOLD = 0.3          # Centrality threshold for bridge skills


class JobArchitectureDiagnosticsAnalyzer:
    """
    Main analyzer class for job architecture health diagnostics.
    
    Provides comprehensive evaluation of organizational job architecture health
    with actionable insights for HR stakeholders and governance.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the diagnostics analyzer.
        
        Args:
            db_path: Path to the SQLite database containing job architecture data
        """
        self.db_path = db_path
        self.config = DiagnosticConfig()
    
    def analyze_full_diagnostics(self) -> Dict[str, Any]:
        """
        Run complete job architecture diagnostics analysis.
        
        Returns:
            Dictionary containing all diagnostic results and executive summary
        """
        print("🏥 JOB ARCHITECTURE & SKILLS TAXONOMY HEALTH DIAGNOSTICS")
        print("="*70)
        print("📊 Comprehensive evaluation of organizational job architecture health")
        print("🎯 Focus: Actionable insights for HR stakeholders and governance")
        print()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                print(f"✅ Connected to database: {self.db_path}")
                
                # Load diagnostic data
                job_skills_df, job_metadata, bu_df = self._load_diagnostic_data(conn)
                
                # Run all diagnostic analyses
                silhouette_results = self._analyze_silhouette_scores(job_skills_df, job_metadata)
                similarity_results = self._analyze_skill_similarity(job_skills_df, job_metadata)
                graph_results = self._analyze_graph_structure(job_skills_df, job_metadata)
                entropy_results = self._analyze_entropy_diversity(job_skills_df, job_metadata)
                
                # Generate executive summary
                executive_summary = self._generate_executive_summary(
                    silhouette_results, similarity_results, graph_results, entropy_results, job_metadata
                )
                
                return {
                    'silhouette_results': silhouette_results,
                    'similarity_results': similarity_results,
                    'graph_results': graph_results,
                    'entropy_results': entropy_results,
                    'executive_summary': executive_summary,
                    'overall_health': executive_summary['overall_health'],
                    'major_issues': executive_summary['major_issues'],
                    'minor_issues': executive_summary['minor_issues']
                }
                
        except Exception as e:
            print(f"❌ Diagnostics analysis failed: {str(e)}")
            raise
        finally:
            print(f"\n🔒 Database connection closed")
    
    def _load_diagnostic_data(self, conn) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load comprehensive data for diagnostic analysis"""
        print("📚 Loading diagnostic data...")
        
        # Load job-skill relationships with full context using correct schema
        job_skills_query = """
        SELECT 
            j.JobProfileID,
            j.JobProfile,
            j.JobFunction,
            j.JobSubFunction,
            j.JobCategory,
            j.ManagementLevel,
            j.Customer_Facing,
            j.is_Banker,
            js.Skill_ID,
            s.Skill_Name,
            s.Category as Skill_Category,
            s.SkillType
        FROM core_job_architecture j
        JOIN core_job_skill_requirements js ON j.JobProfileID = js.JobProfileID
        JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID
        ORDER BY j.JobProfileID, s.Skill_Name
        """
        
        job_skills_df = pd.read_sql_query(job_skills_query, conn)
        
        # Load business unit information (if available)
        try:
            bu_query = """
            SELECT DISTINCT
                JobFunction,
                COUNT(DISTINCT JobProfileID) as job_count
            FROM core_job_architecture
            GROUP BY JobFunction
            ORDER BY job_count DESC
            """
            bu_df = pd.read_sql_query(bu_query, conn)
        except:
            bu_df = pd.DataFrame()
        
        # Calculate job metadata
        job_metadata = job_skills_df[['JobProfileID', 'JobProfile', 'JobFunction', 
                                     'JobSubFunction', 'JobCategory', 'ManagementLevel']].drop_duplicates()
        
        print(f"   → Job profiles: {len(job_metadata):,}")
        print(f"   → Job-skill relationships: {len(job_skills_df):,}")
        print(f"   → Unique skills: {job_skills_df['Skill_Name'].nunique():,}")
        print(f"   → Job functions: {job_metadata['JobFunction'].nunique():,}")
        
        return job_skills_df, job_metadata, bu_df
    
    def _create_job_skill_matrix(self, job_skills_df: pd.DataFrame) -> pd.DataFrame:
        """Create binary job-skill matrix for analysis"""
        print("🔗 Creating job-skill matrix...")
        
        job_skill_matrix = job_skills_df.pivot_table(
            index='JobProfileID', 
            columns='Skill_Name', 
            values='Skill_ID',
            aggfunc='count',
            fill_value=0
        )
        job_skill_matrix = (job_skill_matrix > 0).astype(int)
        
        print(f"   → Matrix shape: {job_skill_matrix.shape}")
        print(f"   → Sparsity: {(job_skill_matrix == 0).sum().sum() / (job_skill_matrix.shape[0] * job_skill_matrix.shape[1]) * 100:.1f}%")
        
        return job_skill_matrix
    
    def _analyze_silhouette_scores(self, job_skills_df: pd.DataFrame, job_metadata: pd.DataFrame) -> Dict[str, Any]:
        """
        Silhouette Score Analysis
        Measures functional cohesion and separation between job profiles based on skill vectors
        """
        print("\n" + "="*60)
        print("🎯 SILHOUETTE SCORE ANALYSIS")
        print("="*60)
        print("📊 Measuring functional cohesion and separation between job profiles")
        
        # Create job-skill matrix
        job_skill_matrix = self._create_job_skill_matrix(job_skills_df)
        
        # Calculate distance matrix (1 - Jaccard similarity)
        print("   → Calculating job similarity matrix...")
        job_ids = job_skill_matrix.index.tolist()
        n_jobs = len(job_ids)
        
        similarity_matrix = np.zeros((n_jobs, n_jobs))
        for i, job_a in enumerate(job_ids):
            for j, job_b in enumerate(job_ids):
                if i <= j:
                    skills_a = set(job_skill_matrix.loc[job_a][job_skill_matrix.loc[job_a] == 1].index)
                    skills_b = set(job_skill_matrix.loc[job_b][job_skill_matrix.loc[job_b] == 1].index)
                    
                    if skills_a and skills_b:
                        jaccard_sim = len(skills_a & skills_b) / len(skills_a | skills_b)
                    else:
                        jaccard_sim = 0.0
                    
                    similarity_matrix[i, j] = jaccard_sim
                    similarity_matrix[j, i] = jaccard_sim
        
        distance_matrix = 1 - similarity_matrix
        
        # Create job function labels for clustering
        job_metadata_indexed = job_metadata.set_index('JobProfileID')
        job_function_labels = [job_metadata_indexed.loc[job_id, 'JobFunction'] for job_id in job_ids]
        
        # Convert function labels to numeric
        unique_functions = list(set(job_function_labels))
        function_to_numeric = {func: i for i, func in enumerate(unique_functions)}
        numeric_labels = [function_to_numeric[func] for func in job_function_labels]
        
        # Calculate overall silhouette score
        overall_silhouette = silhouette_score(distance_matrix, numeric_labels, metric='precomputed')
        
        # Calculate per-job silhouette scores
        job_silhouette_scores = silhouette_samples(distance_matrix, numeric_labels, metric='precomputed')
        
        # Calculate per-function (BU) statistics
        function_silhouettes = {}
        for func in unique_functions:
            func_indices = [i for i, f in enumerate(job_function_labels) if f == func]
            if len(func_indices) >= self.config.MIN_JOBS_FOR_BU_ANALYSIS:
                func_scores = [float(job_silhouette_scores[i]) for i in func_indices]
                function_silhouettes[func] = {
                    'mean': np.mean(func_scores),
                    'std': np.std(func_scores),
                    'min': np.min(func_scores),
                    'job_count': len(func_scores),
                    'poor_jobs': sum(1 for score in func_scores if score < self.config.SILHOUETTE_THRESHOLDS['poor'])
                }
        
        # Identify problem jobs
        problem_jobs = []
        for i, score in enumerate(job_silhouette_scores):
            if float(score) < self.config.SILHOUETTE_THRESHOLDS['poor']:
                job_id = job_ids[i]
                job_info = job_metadata_indexed.loc[job_id]
                problem_jobs.append({
                    'JobProfileID': job_id,
                    'JobProfile': job_info['JobProfile'],
                    'JobFunction': job_info['JobFunction'],
                    'silhouette_score': float(score)
                })
        
        # Sort problem jobs by severity
        problem_jobs.sort(key=lambda x: x['silhouette_score'])
        
        # Print results
        self._print_silhouette_results(overall_silhouette, function_silhouettes, problem_jobs)
        
        return {
            'overall_silhouette': float(overall_silhouette),
            'function_silhouettes': function_silhouettes,
            'problem_jobs': problem_jobs,
            'job_silhouette_scores': [float(x) for x in job_silhouette_scores],
            'distance_matrix': distance_matrix,
            'job_ids': job_ids
        }
    
    def _print_silhouette_results(self, overall_silhouette: float, function_silhouettes: Dict, problem_jobs: List):
        """Print silhouette analysis results"""
        print(f"\n📈 OVERALL TAXONOMIC HEALTH:")
        print(f"   → Overall Silhouette Score: {overall_silhouette:.3f}")
        print(f"   → HR Translation: {self._get_hr_interpretation(overall_silhouette)}")
        print(f"   → Recommendation: {self._get_action_recommendation(overall_silhouette)}")
        
        if overall_silhouette >= self.config.SILHOUETTE_THRESHOLDS['excellent']:
            print("   🟢 EXCELLENT: Strong functional differentiation across the organization")
        elif overall_silhouette >= self.config.SILHOUETTE_THRESHOLDS['good']:
            print("   🟡 MODERATE: Some roles need clarification but overall structure is sound")
        else:
            print("   🔴 ATTENTION NEEDED: Significant role overlap requiring strategic review")
        
        print(f"\n🏢 BUSINESS UNIT ANALYSIS:")
        if function_silhouettes:
            # Sort by mean silhouette score
            sorted_functions = sorted(function_silhouettes.items(), key=lambda x: x[1]['mean'], reverse=True)
            
            print(f"   → Analyzing {len(sorted_functions)} business units/functions")
            print(f"\n   Top Performing Units (Clear Role Differentiation):")
            for func, stats in sorted_functions[:5]:
                status = "🟢" if stats['mean'] >= self.config.SILHOUETTE_THRESHOLDS['excellent'] else "🟡" if stats['mean'] >= self.config.SILHOUETTE_THRESHOLDS['good'] else "🔴"
                print(f"   {status} {func}: {stats['mean']:.3f} avg ({stats['job_count']} roles)")
                print(f"      → {self._get_hr_interpretation(stats['mean'])}")
            
            print(f"\n   Units Needing Attention (Poor Role Differentiation):")
            attention_units = [item for item in sorted_functions if item[1]['mean'] < self.config.SILHOUETTE_THRESHOLDS['good']]
            for func, stats in attention_units[-5:]:
                print(f"   🔴 {func}: {stats['mean']:.3f} avg ({stats['job_count']} roles)")
                print(f"      → {stats['poor_jobs']} roles with poor differentiation")
                print(f"      → {self._get_action_recommendation(stats['mean'], 'role')}")
        
        print(f"\n⚠️  INDIVIDUAL ROLE ALERTS:")
        if problem_jobs:
            print(f"   → {len(problem_jobs)} roles with poor differentiation (silhouette < {self.config.SILHOUETTE_THRESHOLDS['poor']:.1f})")
            print(f"\n   Most Problematic Roles (requiring immediate review):")
            for job in problem_jobs[:self.config.TOP_N_ISSUES]:
                print(f"   🔴 {job['JobProfile']} ({job['JobFunction']})")
                print(f"      → Silhouette: {job['silhouette_score']:.3f}")
                print(f"      → Issue: Role not clearly differentiated from others in skill requirements")
        else:
            print("   🟢 No individual roles flagged for poor differentiation")
    
    def _analyze_skill_similarity(self, job_skills_df: pd.DataFrame, job_metadata: pd.DataFrame) -> Dict[str, Any]:
        """
        Skill Similarity Measures
        Detect near-duplicate profiles and excessive standardization using Jaccard and Cosine similarity
        """
        print("\n" + "="*60)
        print("🔍 SKILL SIMILARITY ANALYSIS")
        print("="*60)
        print("📊 Detecting role redundancy and excessive standardization")
        
        # Create job-skill matrix
        job_skill_matrix = self._create_job_skill_matrix(job_skills_df)
        job_ids = job_skill_matrix.index.tolist()
        
        # Calculate pairwise similarities
        print("   → Calculating pairwise job similarities...")
        
        jaccard_similarities = []
        cosine_similarities = []
        job_pairs = []
        
        # Calculate Jaccard similarity
        for i, job_a in enumerate(job_ids):
            for j, job_b in enumerate(job_ids):
                if i < j:  # Only calculate upper triangle
                    skills_a = set(job_skill_matrix.loc[job_a][job_skill_matrix.loc[job_a] == 1].index)
                    skills_b = set(job_skill_matrix.loc[job_b][job_skill_matrix.loc[job_b] == 1].index)
                    
                    if skills_a and skills_b:
                        jaccard_sim = len(skills_a & skills_b) / len(skills_a | skills_b)
                    else:
                        jaccard_sim = 0.0
                    
                    jaccard_similarities.append(jaccard_sim)
                    job_pairs.append((job_a, job_b))
        
        # Calculate Cosine similarity
        cosine_matrix = cosine_similarity(job_skill_matrix.values)
        for i in range(len(job_ids)):
            for j in range(i+1, len(job_ids)):
                cosine_similarities.append(cosine_matrix[i, j])
        
        # Identify near-duplicate pairs
        near_duplicate_jaccard = []
        near_duplicate_cosine = []
        
        job_metadata_indexed = job_metadata.set_index('JobProfileID')
        
        for idx, (job_a, job_b) in enumerate(job_pairs):
            jaccard_sim = jaccard_similarities[idx]
            cosine_sim = cosine_similarities[idx]
            
            if jaccard_sim > self.config.SIMILARITY_THRESHOLDS['near_duplicate_jaccard']:
                job_a_info = job_metadata_indexed.loc[job_a]
                job_b_info = job_metadata_indexed.loc[job_b]
                near_duplicate_jaccard.append({
                    'job_a': job_a_info['JobProfile'],
                    'job_b': job_b_info['JobProfile'],
                    'function_a': job_a_info['JobFunction'],
                    'function_b': job_b_info['JobFunction'],
                    'jaccard_similarity': jaccard_sim
                })
            
            if cosine_sim > self.config.SIMILARITY_THRESHOLDS['near_duplicate_cosine']:
                job_a_info = job_metadata_indexed.loc[job_a]
                job_b_info = job_metadata_indexed.loc[job_b]
                near_duplicate_cosine.append({
                    'job_a': job_a_info['JobProfile'],
                    'job_b': job_b_info['JobProfile'],
                    'function_a': job_a_info['JobFunction'],
                    'function_b': job_b_info['JobFunction'],
                    'cosine_similarity': cosine_sim
                })
        
        # Analyze role family variance
        function_variances = {}
        for function in job_metadata['JobFunction'].unique():
            function_jobs = job_metadata[job_metadata['JobFunction'] == function]['JobProfileID'].tolist()
            if len(function_jobs) >= self.config.MIN_JOBS_FOR_BU_ANALYSIS:
                # Calculate internal variance within function
                function_similarities = []
                for i, job_a in enumerate(function_jobs):
                    for j, job_b in enumerate(function_jobs):
                        if i < j and job_a in job_ids and job_b in job_ids:
                            idx_a = job_ids.index(job_a)
                            idx_b = job_ids.index(job_b)
                            function_similarities.append(cosine_matrix[idx_a, idx_b])
                
                if function_similarities:
                    variance = np.var(function_similarities)
                    function_variances[function] = {
                        'variance': variance,
                        'mean_similarity': np.mean(function_similarities),
                        'job_count': len(function_jobs)
                    }
        
        # Identify low-variance functions (potentially overfitted)
        low_variance_functions = [
            (func, stats) for func, stats in function_variances.items() 
            if stats['variance'] < self.config.SIMILARITY_THRESHOLDS['low_variance']
        ]
        
        # Print results
        self._print_similarity_results(jaccard_similarities, cosine_similarities, job_pairs, 
                                     near_duplicate_jaccard, near_duplicate_cosine, low_variance_functions)
        
        return {
            'jaccard_similarities': jaccard_similarities,
            'cosine_similarities': cosine_similarities,
            'near_duplicate_jaccard': near_duplicate_jaccard,
            'near_duplicate_cosine': near_duplicate_cosine,
            'function_variances': function_variances,
            'low_variance_functions': low_variance_functions
        }
    
    def _print_similarity_results(self, jaccard_similarities, cosine_similarities, job_pairs,
                                near_duplicate_jaccard, near_duplicate_cosine, low_variance_functions):
        """Print similarity analysis results"""
        print(f"\n📊 SIMILARITY ANALYSIS RESULTS:")
        print(f"   → Analyzed {len(job_pairs):,} job pairs")
        print(f"   → Average Jaccard similarity: {np.mean(jaccard_similarities):.3f}")
        print(f"   → Average Cosine similarity: {np.mean(cosine_similarities):.3f}")
        
        print(f"\n🔍 NEAR-DUPLICATE ROLE DETECTION:")
        if near_duplicate_jaccard:
            print(f"   🔴 ALERT: {len(near_duplicate_jaccard)} role pairs with high skill overlap (Jaccard > {self.config.SIMILARITY_THRESHOLDS['near_duplicate_jaccard']:.2f})")
            print(f"   HR Translation: These roles are almost identical—do we need both?")
            print(f"\n   Most Similar Role Pairs:")
            sorted_jaccard = sorted(near_duplicate_jaccard, key=lambda x: x['jaccard_similarity'], reverse=True)
            for pair in sorted_jaccard[:self.config.TOP_N_ISSUES]:
                print(f"   • {pair['job_a']} ↔ {pair['job_b']}")
                print(f"     Functions: {pair['function_a']} | {pair['function_b']}")
                print(f"     Similarity: {pair['jaccard_similarity']:.3f}")
        else:
            print("   🟢 No near-duplicate roles detected (good role differentiation)")
        
        if near_duplicate_cosine:
            print(f"\n   🔴 SEMANTIC REDUNDANCY: {len(near_duplicate_cosine)} pairs with high semantic similarity")
            print(f"   → These roles may have conceptual overlap requiring clarification")
        
        print(f"\n📈 ROLE FAMILY HOMOGENEITY ANALYSIS:")
        if low_variance_functions:
            print(f"   🔴 ALERT: {len(low_variance_functions)} functions with low internal variance")
            print(f"   HR Translation: These job families may be too homogenous—limited role clarity")
            for func, stats in low_variance_functions:
                print(f"   • {func}: {stats['variance']:.3f} variance ({stats['job_count']} roles)")
                print(f"     → Consider adding role differentiation or combining similar positions")
        else:
            print("   🟢 All job families show healthy internal role differentiation")
    
    def _analyze_graph_structure(self, job_skills_df: pd.DataFrame, job_metadata: pd.DataFrame) -> Dict[str, Any]:
        """
        Graph-Based Structural Analysis
        Community detection and centrality analysis using bipartite job-skill graph
        """
        print("\n" + "="*60)
        print("🕸️  GRAPH-BASED STRUCTURAL ANALYSIS")
        print("="*60)
        print("📊 Community detection and network analysis of job-skill relationships")
        
        # Create bipartite graph
        print("   → Building bipartite job-skill graph...")
        
        G = nx.Graph()
        
        # Add job nodes
        job_nodes = [(f"job_{row['JobProfileID']}", {
            'type': 'job',
            'profile': row['JobProfile'],
            'function': row['JobFunction']
        }) for _, row in job_metadata.iterrows()]
        G.add_nodes_from(job_nodes)
        
        # Add skill nodes
        skill_nodes = [(f"skill_{skill}", {'type': 'skill'}) 
                       for skill in job_skills_df['Skill_Name'].unique()]
        G.add_nodes_from(skill_nodes)
        
        # Add edges
        edges = [(f"job_{row['JobProfileID']}", f"skill_{row['Skill_Name']}") 
                 for _, row in job_skills_df.iterrows()]
        G.add_edges_from(edges)
        
        print(f"   → Graph created: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")
        
        # Calculate centrality measures for skills (hub detection)
        print("   → Calculating skill centrality measures...")
        
        skill_nodes_list = [node for node in G.nodes() if node.startswith('skill_')]
        skill_degrees = {node: G.degree[node] for node in skill_nodes_list}  # Fixed: G.degree is a dict-like view
        skill_betweenness = nx.betweenness_centrality(G, k=min(1000, G.number_of_nodes()))
        
        # Identify hub skills (assigned to many unrelated jobs)
        hub_skills = []
        for skill_node in skill_nodes_list:
            degree = skill_degrees[skill_node]
            betweenness = skill_betweenness.get(skill_node, 0)
            
            if degree > 10 and betweenness > self.config.BRIDGE_SKILL_THRESHOLD:
                skill_name = skill_node.replace('skill_', '')
                
                # Check if skill spans multiple functions
                connected_jobs = [neighbor for neighbor in G.neighbors(skill_node) if neighbor.startswith('job_')]
                job_functions = []
                for job_node in connected_jobs:
                    job_id = job_node.replace('job_', '')
                    function_match = job_metadata[job_metadata['JobProfileID'] == job_id]
                    if not function_match.empty:
                        function = function_match['JobFunction'].iloc[0]
                        job_functions.append(function)
                
                unique_functions = len(set(job_functions))
                
                if unique_functions >= 3:  # Skill spans multiple functions
                    hub_skills.append({
                        'skill': skill_name,
                        'degree': degree,
                        'betweenness': betweenness,
                        'functions_spanned': unique_functions,
                        'total_functions': list(set(job_functions))
                    })
        
        # Sort hub skills by degree
        hub_skills.sort(key=lambda x: x['degree'], reverse=True)
        
        # Project to job-only graph for community detection
        print("   → Performing community detection on job network...")
        
        job_graph = nx.Graph()
        job_ids = job_metadata['JobProfileID'].tolist()
        
        # Add job nodes with metadata
        for _, row in job_metadata.iterrows():
            job_graph.add_node(row['JobProfileID'], 
                              profile=row['JobProfile'],
                              function=row['JobFunction'])
        
        # Add edges between jobs that share skills (weighted by number of shared skills)
        job_to_skills = job_skills_df.groupby('JobProfileID')['Skill_Name'].apply(set).to_dict()
        
        for i, job_a in enumerate(job_ids):
            for j, job_b in enumerate(job_ids):
                if i < j:
                    skills_a = job_to_skills.get(job_a, set())
                    skills_b = job_to_skills.get(job_b, set())
                    shared_skills = len(skills_a & skills_b)
                    
                    if shared_skills >= 5:  # Minimum shared skills for connection
                        job_graph.add_edge(job_a, job_b, weight=shared_skills)
        
        # Detect communities
        communities = {}
        community_analysis = {}
        community_purity = {}
        
        if community_louvain is not None:
            try:
                communities = community_louvain.best_partition(job_graph, weight='weight', random_state=42)
                
                # Analyze community composition
                community_analysis = defaultdict(list)
                for job_id, community_id in communities.items():
                    job_info = job_metadata[job_metadata['JobProfileID'] == job_id].iloc[0]
                    community_analysis[community_id].append({
                        'job_id': job_id,
                        'profile': job_info['JobProfile'],
                        'function': job_info['JobFunction']
                    })
                
                # Calculate community purity (how much each community aligns with existing functions)
                for comm_id, jobs in community_analysis.items():
                    if len(jobs) >= 3:  # Only analyze communities with sufficient size
                        function_counts = Counter([job['function'] for job in jobs])
                        dominant_function_count = max(function_counts.values())
                        purity = dominant_function_count / len(jobs)
                        community_purity[comm_id] = {
                            'purity': purity,
                            'size': len(jobs),
                            'dominant_function': function_counts.most_common(1)[0][0],
                            'function_distribution': dict(function_counts)
                        }
                        
            except Exception as e:
                print(f"   ⚠️  Community detection failed: {str(e)}")
        else:
            print("   ⚠️  Community detection not available (python-louvain not installed)")
        
        # Print results
        self._print_graph_results(job_graph, hub_skills, community_purity)
        
        return {
            'graph': G,
            'job_graph': job_graph,
            'hub_skills': hub_skills,
            'communities': communities,
            'community_analysis': community_analysis,
            'community_purity': community_purity
        }
    
    def _print_graph_results(self, job_graph, hub_skills, community_purity):
        """Print graph analysis results"""
        print(f"\n🎯 NETWORK STRUCTURE INSIGHTS:")
        print(f"   → Network density: {nx.density(job_graph):.4f}")
        print(f"   → Connected components: {nx.number_connected_components(job_graph)}")
        print(f"   → Average clustering coefficient: {nx.average_clustering(job_graph):.3f}")
        
        print(f"\n🌟 HUB SKILLS ANALYSIS:")
        if hub_skills:
            print(f"   🔴 ALERT: {len(hub_skills)} skills are being overused across unrelated job families")
            print(f"   HR Translation: Some skills are assigned to many unrelated jobs—this may dilute their meaning")
            print(f"\n   Most Overused Skills:")
            for skill in hub_skills[:self.config.TOP_N_ISSUES]:
                print(f"   • {skill['skill']}")
                print(f"     → Used in {skill['degree']} jobs across {skill['functions_spanned']} functions")
                print(f"     → Functions: {', '.join(skill['total_functions'][:3])}{'...' if len(skill['total_functions']) > 3 else ''}")
                print(f"     → Recommendation: Consider if this skill is truly required across all these roles")
        else:
            print("   🟢 No skills identified as being overused across unrelated functions")
        
        print(f"\n🏘️  COMMUNITY STRUCTURE ANALYSIS:")
        if community_purity:
            print(f"   → Detected {len(community_purity)} natural job communities")
            print(f"   HR Translation: These roles naturally group together—they may form coherent job families")
            
            # Show communities with interesting patterns
            high_purity = [(comm_id, stats) for comm_id, stats in community_purity.items() if stats['purity'] >= 0.8]
            mixed_communities = [(comm_id, stats) for comm_id, stats in community_purity.items() if stats['purity'] < 0.6 and stats['size'] >= 5]
            
            if high_purity:
                print(f"\n   🟢 Strong Natural Families (align well with current structure):")
                for comm_id, stats in high_purity[:5]:
                    print(f"   • Community {comm_id}: {stats['size']} roles")
                    print(f"     → {stats['purity']:.1%} {stats['dominant_function']}")
                    print(f"     → Interpretation: Well-defined job family with clear boundaries")
            
            if mixed_communities:
                print(f"\n   🟡 Cross-Functional Communities (potential new job families):")
                for comm_id, stats in mixed_communities[:3]:
                    functions = ', '.join([f"{func} ({count})" for func, count in stats['function_distribution'].items()][:3])
                    print(f"   • Community {comm_id}: {stats['size']} roles")
                    print(f"     → Mixed functions: {functions}")
                    print(f"     → Interpretation: Skills-based grouping that transcends current boundaries")
        else:
            print("   ⚠️  Community detection not available")
    
    def _analyze_entropy_diversity(self, job_skills_df: pd.DataFrame, job_metadata: pd.DataFrame) -> Dict[str, Any]:
        """
        Entropy and Diversity Metrics
        Analyze skill entropy per job and diversity per business unit
        """
        print("\n" + "="*60)
        print("🌈 ENTROPY & DIVERSITY ANALYSIS")
        print("="*60)
        print("📊 Measuring role focus vs generality and business unit skill diversity")
        
        # Calculate skill entropy per job
        print("   → Calculating skill entropy per job...")
        
        job_entropies = []
        job_to_skills = job_skills_df.groupby('JobProfileID')['Skill_Name'].apply(list).to_dict()
        
        # Get skill categories for entropy calculation
        skill_categories = job_skills_df.groupby('Skill_Name')['Skill_Category'].first().to_dict()
        
        for job_id, skills in job_to_skills.items():
            # Calculate entropy based on skill category distribution
            categories = [skill_categories.get(skill, 'Unknown') for skill in skills]
            category_counts = Counter(categories)
            total_skills = len(skills)
            
            # Calculate Shannon entropy
            entropy = 0
            for count in category_counts.values():
                probability = count / total_skills
                if probability > 0:
                    entropy -= probability * np.log2(probability)
            
            job_info = job_metadata[job_metadata['JobProfileID'] == job_id].iloc[0]
            job_entropies.append({
                'job_id': job_id,
                'profile': job_info['JobProfile'],
                'function': job_info['JobFunction'],
                'entropy': entropy,
                'skill_count': total_skills,
                'category_count': len(category_counts)
            })
        
        # Identify high and low entropy jobs
        high_entropy_jobs = [job for job in job_entropies if job['entropy'] > self.config.DIVERSITY_THRESHOLDS['high_entropy']]
        low_entropy_jobs = [job for job in job_entropies if job['entropy'] < self.config.DIVERSITY_THRESHOLDS['low_entropy']]
        
        # Sort by entropy for reporting
        high_entropy_jobs.sort(key=lambda x: x['entropy'], reverse=True)
        low_entropy_jobs.sort(key=lambda x: x['entropy'])
        
        # Calculate skill diversity per business unit
        print("   → Analyzing skill diversity per business unit...")
        
        bu_diversity = {}
        for function in job_metadata['JobFunction'].unique():
            function_jobs = job_metadata[job_metadata['JobFunction'] == function]['JobProfileID'].tolist()
            
            if len(function_jobs) >= self.config.MIN_JOBS_FOR_BU_ANALYSIS:
                # Get all skills used in this function
                function_skills_df = job_skills_df[job_skills_df['JobProfileID'].isin(function_jobs)]
                
                # Calculate unique skills, categories, and skill types
                unique_skills = function_skills_df['Skill_Name'].nunique()
                unique_categories = function_skills_df['Skill_Category'].nunique()
                unique_skill_types = function_skills_df['SkillType'].nunique()
                total_relationships = len(function_skills_df)
                
                # Calculate diversity indices
                skill_diversity = unique_skills / len(function_jobs)  # Skills per job
                category_diversity = unique_categories / unique_skills if unique_skills > 0 else 0
                
                bu_diversity[function] = {
                    'job_count': len(function_jobs),
                    'unique_skills': unique_skills,
                    'unique_categories': unique_categories,
                    'unique_skill_types': unique_skill_types,
                    'skills_per_job': skill_diversity,
                    'category_diversity': category_diversity,
                    'total_relationships': total_relationships
                }
        
        # Identify high and low diversity business units
        high_diversity_bus = [(bu, stats) for bu, stats in bu_diversity.items() if stats['skills_per_job'] > 50]
        low_diversity_bus = [(bu, stats) for bu, stats in bu_diversity.items() if stats['skills_per_job'] < 20]
        
        # Print results
        self._print_entropy_results(job_entropies, high_entropy_jobs, low_entropy_jobs, 
                                  bu_diversity, high_diversity_bus, low_diversity_bus)
        
        mean_entropy = np.mean([job['entropy'] for job in job_entropies])
        
        return {
            'job_entropies': job_entropies,
            'high_entropy_jobs': high_entropy_jobs,
            'low_entropy_jobs': low_entropy_jobs,
            'bu_diversity': bu_diversity,
            'high_diversity_bus': high_diversity_bus,
            'low_diversity_bus': low_diversity_bus,
            'mean_entropy': mean_entropy
        }
    
    def _print_entropy_results(self, job_entropies, high_entropy_jobs, low_entropy_jobs,
                             bu_diversity, high_diversity_bus, low_diversity_bus):
        """Print entropy and diversity analysis results"""
        print(f"\n📊 JOB ROLE FOCUS ANALYSIS:")
        mean_entropy = np.mean([job['entropy'] for job in job_entropies])
        print(f"   → Average job entropy: {mean_entropy:.2f}")
        print(f"   → Jobs analyzed: {len(job_entropies)}")
        
        if high_entropy_jobs:
            print(f"\n   🔴 UNFOCUSED ROLES (high entropy > {self.config.DIVERSITY_THRESHOLDS['high_entropy']:.1f}):")
            print(f"   HR Translation: These roles try to do too many things—we may need to clarify their purpose")
            for job in high_entropy_jobs[:self.config.TOP_N_ISSUES]:
                print(f"   • {job['profile']} ({job['function']})")
                print(f"     → Entropy: {job['entropy']:.2f}, {job['skill_count']} skills across {job['category_count']} categories")
                print(f"     → Recommendation: Consider role specialization or splitting responsibilities")
        
        if low_entropy_jobs:
            print(f"\n   🟡 HIGHLY SPECIALIZED ROLES (low entropy < {self.config.DIVERSITY_THRESHOLDS['low_entropy']:.1f}):")
            for job in low_entropy_jobs[:5]:
                print(f"   • {job['profile']} ({job['function']})")
                print(f"     → Entropy: {job['entropy']:.2f}, {job['skill_count']} skills in {job['category_count']} categories")
                print(f"     → Note: High specialization may be appropriate for technical roles")
        
        if not high_entropy_jobs and not low_entropy_jobs:
            print("   🟢 All roles show appropriate focus levels")
        
        print(f"\n🏢 BUSINESS UNIT SKILL DIVERSITY:")
        if bu_diversity:
            print(f"   → Analyzed {len(bu_diversity)} business units")
            
            if high_diversity_bus:
                print(f"\n   🟢 HIGH SKILL DIVERSITY (rich capability mix):")
                for bu, stats in high_diversity_bus[:5]:
                    print(f"   • {bu}: {stats['skills_per_job']:.1f} skills per job")
                    print(f"     → {stats['unique_skills']} unique skills across {stats['job_count']} roles")
                    print(f"     → Interpretation: Rich skill ecosystem with diverse capabilities")
            
            if low_diversity_bus:
                print(f"\n   🔴 LOW SKILL DIVERSITY (potential risk of inflexibility):")
                print(f"   HR Translation: These units may be too skill-narrow—risk of inflexibility")
                for bu, stats in low_diversity_bus:
                    print(f"   • {bu}: {stats['skills_per_job']:.1f} skills per job")
                    print(f"     → {stats['unique_skills']} unique skills across {stats['job_count']} roles")
                    print(f"     → Recommendation: Consider cross-training and skill diversification")
            
            if not high_diversity_bus and not low_diversity_bus:
                print("   🟢 All business units show balanced skill diversity")
    
    def _generate_executive_summary(self, silhouette_results, similarity_results, graph_results, 
                                  entropy_results, job_metadata) -> Dict[str, Any]:
        """Generate executive summary and governance recommendations"""
        print("\n" + "="*70)
        print("📋 EXECUTIVE SUMMARY & GOVERNANCE RECOMMENDATIONS")
        print("="*70)
        
        overall_health = "HEALTHY"
        major_issues = []
        minor_issues = []
        
        # Assess overall health
        if silhouette_results['overall_silhouette'] < self.config.SILHOUETTE_THRESHOLDS['poor']:
            overall_health = "ATTENTION NEEDED"
            major_issues.append("Poor functional differentiation across roles")
        elif silhouette_results['overall_silhouette'] < self.config.SILHOUETTE_THRESHOLDS['good']:
            overall_health = "MODERATE"
            minor_issues.append("Some roles lack clear differentiation")
        
        if similarity_results['near_duplicate_jaccard']:
            if len(similarity_results['near_duplicate_jaccard']) > 10:
                major_issues.append(f"{len(similarity_results['near_duplicate_jaccard'])} near-duplicate role pairs")
            else:
                minor_issues.append(f"{len(similarity_results['near_duplicate_jaccard'])} potential duplicate roles")
        
        if graph_results['hub_skills']:
            if len(graph_results['hub_skills']) > 20:
                major_issues.append(f"{len(graph_results['hub_skills'])} overused skills across functions")
            else:
                minor_issues.append(f"{len(graph_results['hub_skills'])} skills may be overused")
        
        if entropy_results['high_entropy_jobs']:
            if len(entropy_results['high_entropy_jobs']) > 20:
                major_issues.append(f"{len(entropy_results['high_entropy_jobs'])} unfocused roles")
            else:
                minor_issues.append(f"{len(entropy_results['high_entropy_jobs'])} roles may be unfocused")
        
        # Print summary
        print(f"\n🎯 OVERALL ARCHITECTURE HEALTH: {overall_health}")
        
        if overall_health == "HEALTHY" and not major_issues and not minor_issues:
            print("   🟢 EXCELLENT: Job architecture shows strong structural integrity")
            print("   → Health is strong – no action required")
        elif overall_health == "HEALTHY" or overall_health == "MODERATE":
            print("   🟡 GOOD WITH MONITORING: Generally healthy with some areas for improvement")
            print("   → There are early signs of taxonomic drift – consider monitoring")
        else:
            print("   🔴 REQUIRES ATTENTION: Significant structural issues identified")
            print("   → These roles/families need targeted review or redesign")
        
        if major_issues:
            print(f"\n🔴 MAJOR ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for issue in major_issues:
                print(f"   • {issue}")
        
        if minor_issues:
            print(f"\n🟡 MINOR ISSUES FOR MONITORING:")
            for issue in minor_issues:
                print(f"   • {issue}")
        
        # Generate KPIs for ongoing governance
        print(f"\n📊 KEY PERFORMANCE INDICATORS (for ongoing monitoring):")
        
        poor_role_percentage = len(silhouette_results['problem_jobs']) / len(job_metadata) * 100
        print(f"   → % of roles with poor differentiation: {poor_role_percentage:.1f}%")
        print(f"     Target: <5% | Current Status: {'🟢' if poor_role_percentage < 5 else '🟡' if poor_role_percentage < 10 else '🔴'}")
        
        print(f"   → Overall silhouette score: {silhouette_results['overall_silhouette']:.3f}")
        print(f"     Target: >0.4 | Current Status: {'🟢' if silhouette_results['overall_silhouette'] > 0.4 else '🔴'}")
        
        duplicate_percentage = len(similarity_results['near_duplicate_jaccard']) / len(job_metadata) * 100
        print(f"   → % roles in near-duplicate pairs: {duplicate_percentage:.1f}%")
        print(f"     Target: <2% | Current Status: {'🟢' if duplicate_percentage < 2 else '🟡' if duplicate_percentage < 5 else '🔴'}")
        
        overused_skill_count = len(graph_results['hub_skills'])
        print(f"   → Number of overused skills: {overused_skill_count}")
        print(f"     Target: <10 | Current Status: {'🟢' if overused_skill_count < 10 else '🟡' if overused_skill_count < 20 else '🔴'}")
        
        print(f"\n📅 RECOMMENDED REPORTING CADENCE:")
        print(f"   → Monthly light-touch dashboard: Silhouette score, duplicate count, role changes")
        print(f"   → Quarterly in-depth audit: Full diagnostic analysis with trend analysis")
        print(f"   → Post-update validation: Run diagnostics after any job architecture changes")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Address any major issues identified above")
        print(f"   2. Set up automated monitoring for key metrics")
        print(f"   3. Establish quarterly review process with stakeholders")
        print(f"   4. Create intervention protocols for metric thresholds")
        
        return {
            'overall_health': overall_health,
            'major_issues': major_issues,
            'minor_issues': minor_issues,
            'kpis': {
                'poor_role_percentage': poor_role_percentage,
                'overall_silhouette': silhouette_results['overall_silhouette'],
                'duplicate_percentage': duplicate_percentage,
                'overused_skill_count': overused_skill_count
            }
        }
    
    def _get_hr_interpretation(self, silhouette_score: float) -> str:
        """Convert silhouette score to HR-friendly interpretation"""
        if silhouette_score >= self.config.SILHOUETTE_THRESHOLDS['excellent']:
            return "Roles within each area look distinct and well-structured"
        elif silhouette_score >= self.config.SILHOUETTE_THRESHOLDS['good']:
            return "These roles have moderate clarity but may benefit from review"
        else:
            return "These roles are not clearly different from others - potential redesign needed"
    
    def _get_action_recommendation(self, silhouette_score: float, issue_type: str = "general") -> str:
        """Provide actionable recommendations based on diagnostic results"""
        if silhouette_score >= self.config.SILHOUETTE_THRESHOLDS['excellent']:
            return "Health is strong – no action required"
        elif silhouette_score >= self.config.SILHOUETTE_THRESHOLDS['good']:
            return "There are early signs of taxonomic drift – consider monitoring"
        else:
            if issue_type == "role":
                return "These roles/families need targeted review or redesign"
            else:
                return "This unit's structure may not reflect skill reality – discussion warranted"


def analyze_job_architecture_health(db_path: str) -> Dict[str, Any]:
    """
    Main entry point for job architecture health diagnostics.
    
    Args:
        db_path: Path to the SQLite database containing job architecture data
        
    Returns:
        Dictionary containing all diagnostic results and executive summary
    """
    analyzer = JobArchitectureDiagnosticsAnalyzer(db_path)
    return analyzer.analyze_full_diagnostics()


def main():
    """Main execution function for standalone testing"""
    # Default to business_context.sqlite for correct data
    db_path = "models/2025-Q3/business_context.sqlite"
    
    print("🏥 JOB ARCHITECTURE & SKILLS TAXONOMY DIAGNOSTICS")
    print("="*70)
    print("📊 Comprehensive health evaluation with HR-friendly insights")
    print("🎯 Identifying taxonomic drift, redundancy, and governance opportunities")
    print()
    
    try:
        results = analyze_job_architecture_health(db_path)
        
        print(f"\n🎉 DIAGNOSTIC ANALYSIS COMPLETE!")
        print(f"📋 Use insights above for strategic workforce planning and governance")
        print(f"🔄 Recommend establishing regular diagnostic monitoring for ongoing health")
        
        return results
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return None


if __name__ == "__main__":
    results = main()