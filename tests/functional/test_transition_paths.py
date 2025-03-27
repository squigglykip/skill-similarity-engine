#!/usr/bin/env python3
"""
Functional tests for validating job transition pathways.

This module tests the identification of viable transition pathways between jobs,
focusing on reskilling opportunities and skill gap analysis.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger("test_transition_paths")

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.data.loaders import JobArchitectureLoader
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator
from skill_similarity_engine.analysis.gap import TeamGapAnalyzer
from skill_similarity_engine.analysis.pathways import CareerPathwayGenerator


class TestJobTransitionPathways(unittest.TestCase):
    """Test job transition pathway identification and validation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        # Define data paths
        cls.use_real_data = os.environ.get("USE_REAL_DATA", "False").lower() == "true"
        
        if cls.use_real_data:
            # Path to real data
            cls.data_dir = os.environ.get("REAL_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'real'))
            logger.info(f"Using real data from: {cls.data_dir}")
            
            # Check if real data directory exists
            if not os.path.exists(cls.data_dir):
                logger.warning(f"Real data directory does not exist: {cls.data_dir}")
                logger.warning("Falling back to sample data")
                cls.use_real_data = False
        
        # Use sample data as fallback
        if not cls.use_real_data:
            cls.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
            logger.info(f"Using sample data from: {cls.data_dir}")
        
        # Setup output directory for test artifacts
        cls.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output', 'tests', 'transition_paths')
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Load data
        logger.info("Loading skill taxonomy...")
        cls.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(cls.data_dir, 'skills.csv'))
        logger.info(f"Loaded {len(cls.skill_taxonomy.skills)} skills")
        
        logger.info("Loading job architecture...")
        job_loader = JobArchitectureLoader(cls.skill_taxonomy)
        cls.job_architecture = job_loader.load_from_csv(os.path.join(cls.data_dir, 'jobs.csv'))
        logger.info(f"Loaded {len(cls.job_architecture.jobs)} jobs")
        
        # Initialize similarity calculator
        cls.similarity_calculator = CosineSimilarityCalculator(
            vectorizer=None,  # Will be initialized within the calculator
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture
        )
        
        # Initialize gap analyzer
        cls.gap_analyzer = TeamGapAnalyzer(
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture
        )
        
        # Initialize pathway generator
        cls.pathway_generator = CareerPathwayGenerator(
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture,
            similarity_calculator=cls.similarity_calculator,
            gap_analyzer=cls.gap_analyzer
        )
        
        # Get departments for testing
        cls.departments = set(job.department for job in cls.job_architecture.jobs.values())
        logger.info(f"Found {len(cls.departments)} departments")
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Skip tests if using sample data but real data is required
        if not self.use_real_data and os.environ.get("REQUIRE_REAL_DATA", "False").lower() == "true":
            self.skipTest("These tests require real data.")
    
    def test_direct_transition_identification(self):
        """Test identification of direct job transitions based on similarity."""
        # Test parameters
        similarity_threshold = 0.6  # Minimum similarity for direct transition
        
        # Get job pairs with high similarity
        logger.info(f"Testing direct transition identification with similarity threshold: {similarity_threshold}")
        
        direct_transitions = []
        same_dept_transitions = []
        cross_dept_transitions = []
        
        # Sample a subset of jobs for testing
        sample_size = min(20, len(self.job_architecture.jobs))
        sample_jobs = list(self.job_architecture.jobs.keys())[:sample_size]
        
        # Find transitions between sampled jobs
        for job1_id in sample_jobs:
            job1 = self.job_architecture.jobs[job1_id]
            
            for job2_id in sample_jobs:
                if job1_id == job2_id:
                    continue
                    
                job2 = self.job_architecture.jobs[job2_id]
                similarity = self.similarity_calculator.calculate_job_similarity(job1_id, job2_id)
                
                # Record high-similarity transitions
                if similarity >= similarity_threshold:
                    transition = {
                        "source_id": job1_id,
                        "source_title": job1.title,
                        "source_department": job1.department,
                        "target_id": job2_id,
                        "target_title": job2.title,
                        "target_department": job2.department,
                        "similarity": similarity
                    }
                    
                    direct_transitions.append(transition)
                    
                    # Categorize as same-department or cross-department
                    if job1.department == job2.department:
                        same_dept_transitions.append(transition)
                    else:
                        cross_dept_transitions.append(transition)
        
        # Log results
        logger.info(f"Found {len(direct_transitions)} direct transitions above threshold")
        logger.info(f"Same department transitions: {len(same_dept_transitions)}")
        logger.info(f"Cross department transitions: {len(cross_dept_transitions)}")
        
        # Visualize transition network
        if direct_transitions:
            self._visualize_transition_network(direct_transitions, "direct_transitions")
            
            # Export transition data
            df = pd.DataFrame(direct_transitions)
            export_path = os.path.join(self.output_dir, "direct_transitions.csv")
            df.to_csv(export_path, index=False)
            logger.info(f"Exported direct transitions to: {export_path}")
            
            # Verify we found at least some valid transitions
            self.assertGreater(len(direct_transitions), 0, 
                            "No direct transitions found with similarity threshold")
    
    def test_skill_gap_analysis_for_transitions(self):
        """Test skill gap analysis for potential job transitions."""
        # Test parameters
        similarity_threshold = 0.5  # Lower threshold to get more transition candidates
        max_pairs_to_analyze = 5  # Limit for detailed analysis
        
        logger.info(f"Testing skill gap analysis for transitions with similarity threshold: {similarity_threshold}")
        
        # Sample a subset of jobs
        sample_size = min(10, len(self.job_architecture.jobs))
        sample_jobs = list(self.job_architecture.jobs.keys())[:sample_size]
        
        # Find transitions between sampled jobs
        transition_candidates = []
        
        for job1_id in sample_jobs:
            job1 = self.job_architecture.jobs[job1_id]
            
            for job2_id in sample_jobs:
                if job1_id == job2_id:
                    continue
                    
                job2 = self.job_architecture.jobs[job2_id]
                similarity = self.similarity_calculator.calculate_job_similarity(job1_id, job2_id)
                
                # Record potential transitions
                if similarity >= similarity_threshold:
                    transition_candidates.append({
                        "source_id": job1_id,
                        "source_title": job1.title,
                        "target_id": job2_id,
                        "target_title": job2.title,
                        "similarity": similarity
                    })
        
        # Sort by similarity and take top candidates
        transition_candidates.sort(key=lambda x: x["similarity"], reverse=True)
        top_candidates = transition_candidates[:max_pairs_to_analyze]
        
        logger.info(f"Analyzing skill gaps for {len(top_candidates)} transition candidates")
        
        # Analyze skill gaps for each candidate
        gap_analyses = []
        
        for candidate in top_candidates:
            source_id = candidate["source_id"]
            target_id = candidate["target_id"]
            
            # Get skill gaps
            skill_gaps = self.gap_analyzer.identify_job_transition_gaps(source_id, target_id)
            
            # Filter to gaps with positive gap (skills needed for target job)
            needed_skills = skill_gaps[skill_gaps["proficiency_gap"] > 0]
            
            # Calculate gap statistics
            gap_count = len(needed_skills)
            avg_gap = needed_skills["proficiency_gap"].mean() if not needed_skills.empty else 0
            max_gap = needed_skills["proficiency_gap"].max() if not needed_skills.empty else 0
            
            # Add to analysis results
            gap_analyses.append({
                "source_id": source_id,
                "source_title": candidate["source_title"],
                "target_id": target_id,
                "target_title": candidate["target_title"],
                "similarity": candidate["similarity"],
                "gap_count": gap_count,
                "avg_gap": avg_gap,
                "max_gap": max_gap,
                "total_gap": avg_gap * gap_count
            })
            
            # Log detailed gap for the first few candidates
            if len(gap_analyses) <= 3 and not needed_skills.empty:
                logger.info(f"Skill gaps for {candidate['source_title']} → {candidate['target_title']}:")
                for _, row in needed_skills.head(5).iterrows():
                    skill_name = self.skill_taxonomy.skills[row["skill_id"]].name
                    logger.info(f"  {skill_name}: gap = {row['proficiency_gap']:.2f}")
                if len(needed_skills) > 5:
                    logger.info(f"  ... and {len(needed_skills) - 5} more skills")
        
        # Create summary dataframe
        if gap_analyses:
            df = pd.DataFrame(gap_analyses)
            
            # Plot gap vs similarity
            plt.figure(figsize=(10, 6))
            plt.scatter(df["similarity"], df["total_gap"], alpha=0.7)
            
            for i, row in df.iterrows():
                plt.annotate(f"{row['source_title']} → {row['target_title']}", 
                           (row["similarity"], row["total_gap"]),
                           fontsize=8, alpha=0.8)
                
            plt.xlabel("Job Similarity")
            plt.ylabel("Total Skill Gap")
            plt.title("Job Transition Difficulty: Similarity vs. Skill Gap")
            plt.grid(True, alpha=0.3)
            
            plot_path = os.path.join(self.output_dir, "transition_difficulty.png")
            plt.savefig(plot_path, dpi=300)
            plt.close()
            logger.info(f"Saved transition difficulty plot to: {plot_path}")
            
            # Export analysis
            export_path = os.path.join(self.output_dir, "transition_gap_analysis.csv")
            df.to_csv(export_path, index=False)
            logger.info(f"Exported gap analysis to: {export_path}")
            
            # Verify some transitions have reasonable gaps
            self.assertTrue(any(analysis["gap_count"] > 0 for analysis in gap_analyses),
                          "No skill gaps identified for any transition")
    
    def test_multi_step_pathway_generation(self):
        """Test generation of multi-step career pathways between jobs."""
        # Test parameters
        similarity_threshold = 0.4  # Lower threshold for pathway steps
        max_path_length = 3  # Maximum steps in a pathway
        
        logger.info(f"Testing multi-step pathway generation with parameters:")
        logger.info(f"  Similarity threshold: {similarity_threshold}")
        logger.info(f"  Maximum path length: {max_path_length}")
        
        # Sample jobs from different departments
        departments = list(self.departments)[:3]  # Test with up to 3 departments
        source_jobs = []
        target_jobs = []
        
        # Get some jobs from each department
        for dept in departments:
            dept_jobs = [job_id for job_id, job in self.job_architecture.jobs.items() 
                       if job.department == dept][:3]  # Up to 3 jobs per department
            
            if dept_jobs:
                source_jobs.extend(dept_jobs)
                target_jobs.extend(dept_jobs)
        
        # Ensure we have jobs to test
        if not source_jobs or not target_jobs:
            self.skipTest("Not enough jobs in different departments for pathway testing")
        
        # Test pathways between selected jobs
        pathway_results = []
        
        # Limit the number of combinations to test
        test_pairs = []
        for i, source_id in enumerate(source_jobs):
            for target_id in target_jobs[i+1:]:  # Only test with jobs we haven't used as source
                if source_id != target_id:
                    test_pairs.append((source_id, target_id))
        
        # Limit to a reasonable number of pairs
        test_pairs = test_pairs[:10]
        
        for source_id, target_id in test_pairs:
            source_job = self.job_architecture.jobs[source_id]
            target_job = self.job_architecture.jobs[target_id]
            
            logger.info(f"Finding pathways from {source_job.title} to {target_job.title}")
            
            # Generate pathways
            try:
                pathways = self.pathway_generator.find_career_pathways(
                    source_job_id=source_id,
                    target_job_id=target_id,
                    similarity_threshold=similarity_threshold,
                    max_path_length=max_path_length
                )
                
                # Record results
                result = {
                    "source_id": source_id,
                    "source_title": source_job.title,
                    "source_department": source_job.department,
                    "target_id": target_id,
                    "target_title": target_job.title,
                    "target_department": target_job.department,
                    "direct_similarity": self.similarity_calculator.calculate_job_similarity(source_id, target_id),
                    "pathways_found": len(pathways),
                    "shortest_path_length": min([len(p) for p in pathways]) if pathways else 0,
                    "shortest_path": None
                }
                
                # Get detailed info on the best pathway
                if pathways:
                    # Sort by path length and quality
                    shortest_paths = sorted(pathways, key=lambda p: len(p))
                    best_path = shortest_paths[0]
                    
                    # Format path for display
                    path_steps = []
                    for step_idx, job_id in enumerate(best_path):
                        job = self.job_architecture.jobs[job_id]
                        
                        # Calculate similarity with next step
                        next_similarity = 0
                        if step_idx < len(best_path) - 1:
                            next_job_id = best_path[step_idx + 1]
                            next_similarity = self.similarity_calculator.calculate_job_similarity(job_id, next_job_id)
                            
                        path_steps.append({
                            "step": step_idx + 1,
                            "job_id": job_id,
                            "job_title": job.title,
                            "department": job.department,
                            "next_similarity": next_similarity
                        })
                    
                    # Store best path
                    result["shortest_path"] = path_steps
                    
                    # Log the best path
                    logger.info(f"Found {len(pathways)} pathways. Best pathway:")
                    path_str = " → ".join([self.job_architecture.jobs[j].title for j in best_path])
                    logger.info(f"  {path_str}")
                else:
                    logger.info(f"No pathways found")
                
                pathway_results.append(result)
                
            except Exception as e:
                logger.error(f"Error generating pathways: {e}")
        
        # Analyze results
        if pathway_results:
            # Count successful pathways
            successful_pathways = [r for r in pathway_results if r["pathways_found"] > 0]
            logger.info(f"Found pathways for {len(successful_pathways)} of {len(pathway_results)} job pairs")
            
            # Visualize best pathways
            self._visualize_pathways(pathway_results)
            
            # Export results
            df = pd.DataFrame(pathway_results)
            export_path = os.path.join(self.output_dir, "pathway_results.csv")
            
            # Handle nested path data
            df_export = df.drop(columns=["shortest_path"])
            df_export.to_csv(export_path, index=False)
            
            logger.info(f"Exported pathway results to: {export_path}")
            
            # Export detailed path steps
            all_steps = []
            for result in pathway_results:
                if result["shortest_path"]:
                    for step in result["shortest_path"]:
                        step_data = {
                            "source_id": result["source_id"],
                            "source_title": result["source_title"],
                            "target_id": result["target_id"],
                            "target_title": result["target_title"],
                            **step
                        }
                        all_steps.append(step_data)
            
            if all_steps:
                steps_df = pd.DataFrame(all_steps)
                steps_path = os.path.join(self.output_dir, "pathway_steps.csv")
                steps_df.to_csv(steps_path, index=False)
                logger.info(f"Exported pathway steps to: {steps_path}")
            
            # Verify that we found at least some pathways
            self.assertTrue(any(result["pathways_found"] > 0 for result in pathway_results),
                          "No valid pathways found between any job pairs")
    
    def _visualize_transition_network(self, transitions, filename_prefix):
        """Create a network visualization of job transitions."""
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes and edges
        for t in transitions:
            source_label = f"{t['source_title']}\n({t['source_department']})"
            target_label = f"{t['target_title']}\n({t['target_department']})"
            
            G.add_node(t['source_id'], label=source_label, department=t['source_department'])
            G.add_node(t['target_id'], label=target_label, department=t['target_department'])
            G.add_edge(t['source_id'], t['target_id'], weight=t['similarity'])
        
        # Set up the plot
        plt.figure(figsize=(12, 10))
        
        # Create position layout
        pos = nx.spring_layout(G, k=0.3, iterations=50)
        
        # Get departments for coloring
        departments = set(nx.get_node_attributes(G, 'department').values())
        dept_colors = plt.cm.tab10(np.linspace(0, 1, len(departments)))
        dept_color_map = dict(zip(departments, dept_colors))
        
        # Color nodes by department
        node_colors = [dept_color_map[G.nodes[n]['department']] for n in G.nodes()]
        
        # Draw the network
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color=node_colors, alpha=0.8)
        
        # Draw edges with width based on similarity
        edge_weights = [G[u][v]['weight'] * 3 for u, v in G.edges()]
        nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.7, 
                             edge_color='gray', arrows=True, arrowstyle='->', arrowsize=15)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, 'label'), 
                              font_size=8, font_family='sans-serif')
        
        # Add a legend for departments
        legend_patches = [plt.Line2D([0], [0], marker='o', color='w', 
                                   markerfacecolor=dept_color_map[dept], 
                                   markersize=10, label=dept) 
                        for dept in departments]
        plt.legend(handles=legend_patches, title="Departments", loc='upper right')
        
        plt.axis('off')
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(self.output_dir, f"{filename_prefix}_network.png")
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved transition network visualization to: {output_path}")
    
    def _visualize_pathways(self, pathway_results):
        """Visualize career pathways."""
        # Filter to results with valid pathways
        results_with_paths = [r for r in pathway_results if r.get("shortest_path")]
        
        if not results_with_paths:
            return
        
        # Create a directed graph for all pathways
        G = nx.DiGraph()
        
        # Add paths to graph
        for result in results_with_paths:
            path = result["shortest_path"]
            
            for i in range(len(path) - 1):
                current = path[i]
                next_step = path[i + 1]
                
                # Add nodes
                G.add_node(current["job_id"], 
                         label=f"{current['job_title']}\n({current['department']})",
                         department=current["department"])
                
                G.add_node(next_step["job_id"], 
                         label=f"{next_step['job_title']}\n({next_step['department']})",
                         department=next_step["department"])
                
                # Add edge
                G.add_edge(current["job_id"], next_step["job_id"], 
                         weight=current["next_similarity"])
        
        # Set up the plot
        plt.figure(figsize=(15, 12))
        
        # Create position layout
        pos = nx.spring_layout(G, k=0.3, iterations=100, seed=42)
        
        # Get departments for coloring
        departments = set(nx.get_node_attributes(G, 'department').values())
        dept_colors = plt.cm.tab10(np.linspace(0, 1, len(departments)))
        dept_color_map = dict(zip(departments, dept_colors))
        
        # Color nodes by department
        node_colors = [dept_color_map[G.nodes[n]['department']] for n in G.nodes()]
        
        # Draw the network
        nx.draw_networkx_nodes(G, pos, node_size=700, node_color=node_colors, alpha=0.8)
        
        # Draw edges with width based on similarity
        edge_weights = [G[u][v]['weight'] * 3 for u, v in G.edges()]
        nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.7, 
                             edge_color='gray', arrows=True, arrowstyle='->', arrowsize=15)
        
        # Draw labels
        nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, 'label'), 
                              font_size=8, font_family='sans-serif')
        
        # Add a legend for departments
        legend_patches = [plt.Line2D([0], [0], marker='o', color='w', 
                                   markerfacecolor=dept_color_map[dept], 
                                   markersize=10, label=dept) 
                        for dept in departments]
        plt.legend(handles=legend_patches, title="Departments", loc='upper right')
        
        plt.axis('off')
        plt.title("Career Transition Pathways", fontsize=16)
        plt.tight_layout()
        
        # Save the figure
        output_path = os.path.join(self.output_dir, "career_pathways.png")
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved career pathways visualization to: {output_path}")


if __name__ == "__main__":
    # Run specific test case with real data if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--real-data":
        # Set environment variable to use real data
        os.environ["USE_REAL_DATA"] = "True"
        # Remove the flag from args so unittest doesn't try to interpret it
        sys.argv.pop(1)
    
    unittest.main() 