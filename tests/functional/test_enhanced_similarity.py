"""
Functional tests for enhanced similarity features.

These tests verify that the seniority, role track, and location enhancements
work correctly with real test data.
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import json

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel, RoleTrack
from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator, TfidfVectorizer
from skill_similarity_engine.config.settings import ConfigManager
from skill_similarity_engine.data.loaders import JobArchitectureLoader


class TestEnhancedSimilarityFunctional(unittest.TestCase):
    """Functional tests for enhanced similarity features."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data that will be shared across all tests."""
        # Set up output directory - change from test_output to output
        cls.output_dir = Path("output/test_output/enhanced_similarity")
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Load test data
        data_dir = Path("data/sample")
        
        # Load skill taxonomy directly using the class method
        cls.skill_taxonomy = SkillTaxonomy.from_file(str(data_dir / "skills.json"))
        
        # Load jobs from JSON file manually
        with open(data_dir / "jobs.json", "r") as f:
            jobs_data = json.load(f)
        
        cls.job_architecture = JobArchitecture()
        
        # Check if jobs_data is a list or dictionary and process accordingly
        if isinstance(jobs_data, list):
            # List format
            for job_data in jobs_data:
                job_id = job_data.get("job_id")
                if not job_id:
                    continue
                
                # Parse job level
                job_level = JobLevel.ASSOCIATE
                if "level" in job_data:
                    try:
                        job_level = JobLevel(job_data["level"])
                    except ValueError:
                        # Default to ASSOCIATE if invalid
                        pass
                
                job = Job(
                    job_id=job_id,
                    title=job_data.get("title", "Unknown"),
                    department=job_data.get("department", "Unknown"),
                    level=job_level,
                    skills=job_data.get("skills", {})
                )
                cls.job_architecture.add_job(job)
        else:
            # Dictionary format with job_id as keys
            for job_id, job_data in jobs_data.items():
                # Parse job level
                job_level = JobLevel.ASSOCIATE
                if "level" in job_data:
                    try:
                        job_level = JobLevel(job_data["level"])
                    except ValueError:
                        # Default to ASSOCIATE if invalid
                        pass
                
                job = Job(
                    job_id=job_id,
                    title=job_data.get("title", "Unknown"),
                    department=job_data.get("department", "Unknown"),
                    level=job_level,
                    skills=job_data.get("skills", {})
                )
                cls.job_architecture.add_job(job)
        
        # Add sample seniority, role track, and location data to jobs
        cls._enhance_job_data()
        
        # Create vectorizer
        cls.vectorizer = TfidfVectorizer(cls.skill_taxonomy)
        
        # Create config manager
        cls.config_manager = ConfigManager()
        
        # Initialize calculator
        cls.calculator = CosineSimilarityCalculator(
            vectorizer=cls.vectorizer,
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture,
            config_manager=cls.config_manager
        )
    
    @classmethod
    def _enhance_job_data(cls):
        """
        Add seniority, role track, and location data to the job architecture.
        
        This simulates how real job data would include these fields.
        """
        # Create a mapping of departments to common locations
        location_map = {
            "Sales": "London",
            "Marketing": "Manchester",
            "Engineering": "London",
            "Design": "Bristol",
            "Support": "Glasgow",
            "Finance": "Edinburgh",
            "HR": "London",
            "Operations": "Leeds"
        }
        
        # For jobs that don't have a department in the map
        default_location = "London"
        
        # Job titles that should always be leadership roles
        leadership_titles = ["Manager", "Director", "Lead", "Head", "Chief", "Executive", "VP", "President"]
        
        # Specific job IDs to set as leadership for testing
        leadership_job_ids = ["J006", "J008", "J010", "J012", "J014", "J020"]
        
        # Loop through all jobs and add the enhanced data
        for job_id, job in cls.job_architecture.jobs.items():
            # Set seniority based on job level
            level_to_seniority = {
                JobLevel.ENTRY: 1,
                JobLevel.ASSOCIATE: 2,
                JobLevel.MID_LEVEL: 3,
                JobLevel.SENIOR: 4,
                JobLevel.LEAD: 5,
                JobLevel.MANAGER: 5,
                JobLevel.DIRECTOR: 6,
                JobLevel.EXECUTIVE: 7
            }
            job.seniority = level_to_seniority.get(job.level, 3)
            
            # Set role track based on level, title, or specific job IDs
            is_leadership = False
            
            # Check by job level
            if job.level in [JobLevel.MANAGER, JobLevel.DIRECTOR, JobLevel.EXECUTIVE, JobLevel.LEAD]:
                is_leadership = True
            
            # Check by job title
            elif any(leadership_word in job.title for leadership_word in leadership_titles):
                is_leadership = True
            
            # Check by specific job ID (for testing purposes)
            elif job_id in leadership_job_ids:
                is_leadership = True
            
            # Assign role track
            job.role_track = RoleTrack.LEADERSHIP if is_leadership else RoleTrack.INDIVIDUAL_CONTRIBUTOR
            
            # Set location based on department
            job.location = location_map.get(job.department, default_location)
            
            # For some jobs, set a different location to test location similarity
            if job_id.endswith("4") or job_id.endswith("9"):
                # Assign a different location
                job.location = "Remote"
    
    def test_similarity_matrix_with_enhancements(self):
        """
        Test that the similarity matrix calculation works with enhancements.
        
        This test compares job-to-job similarity across all jobs in the sample set
        using different weighting combinations for the enhancement variables.
        
        The test creates a many-to-many comparison between all jobs in the dataset.
        """
        # Test different weight combinations
        weight_scenarios = [
            {
                "name": "skills_only",
                "weights": {"seniority": 0.0, "role_track": 0.0, "location": 0.0},
                "description": "Base skills only (no enhancements)"
            },
            {
                "name": "with_seniority",
                "weights": {"seniority": 1.0, "role_track": 0.0, "location": 0.0},
                "description": "Skills + Seniority"
            },
            {
                "name": "with_role_track",
                "weights": {"seniority": 0.0, "role_track": 1.0, "location": 0.0},
                "description": "Skills + Role Track"
            },
            {
                "name": "with_location",
                "weights": {"seniority": 0.0, "role_track": 0.0, "location": 1.0},
                "description": "Skills + Location"
            },
            {
                "name": "balanced",
                "weights": {"seniority": 0.5, "role_track": 0.5, "location": 0.5},
                "description": "Balanced weights for all factors"
            },
            {
                "name": "career_focused",
                "weights": {"seniority": 0.8, "role_track": 0.6, "location": 0.2},
                "description": "Career progression focus (higher seniority and role weight)"
            }
        ]
        
        results = []
        
        # Get a sample of job IDs for a more focused test
        sample_job_ids = list(self.job_architecture.jobs.keys())[:20]
        sample_jobs = [self.job_architecture.jobs[job_id] for job_id in sample_job_ids]
        
        # Store all pairwise similarity results in a consolidated dataframe
        consolidated_results = []
        
        # For each weight scenario
        for scenario in weight_scenarios:
            # Set weights
            self.config_manager.config.future_extensions.seniority_weight = scenario["weights"]["seniority"]
            self.config_manager.config.future_extensions.role_track_weight = scenario["weights"]["role_track"]
            self.config_manager.config.future_extensions.location_weight = scenario["weights"]["location"]
            
            # Create a subgraph of the job architecture with just the sample jobs
            sub_architecture = JobArchitecture()
            for job in sample_jobs:
                sub_architecture.add_job(job)
            
            # Create a calculator with the subset of jobs
            calculator = CosineSimilarityCalculator(
                vectorizer=self.vectorizer,
                skill_taxonomy=self.skill_taxonomy,
                job_architecture=sub_architecture,
                config_manager=self.config_manager
            )
            
            # Calculate similarity matrix
            matrix, ids = calculator.calculate_similarity_matrix("job")
            
            # Calculate average similarity
            avg_similarity = np.mean(matrix) if matrix.size > 0 else 0
            
            # Count high similarity pairs (>0.7)
            high_sim_count = np.sum(matrix > 0.7)
            
            # Record results
            results.append({
                "scenario": scenario["name"],
                "description": scenario["description"],
                "avg_similarity": avg_similarity,
                "high_similarity_count": high_sim_count,
                "matrix": matrix,
                "job_ids": ids
            })
            
            # Create a heatmap visualization
            self._create_similarity_heatmap(
                matrix, 
                ids, 
                f"{scenario['name']}_heatmap.png",
                scenario["description"]
            )
            
            # Add pairwise results to consolidated dataframe
            for i in range(len(ids)):
                job1_id = ids[i]
                job1 = self.job_architecture.jobs[job1_id]
                
                for j in range(len(ids)):
                    if i != j:  # Skip self-similarity
                        job2_id = ids[j]
                        job2 = self.job_architecture.jobs[job2_id]
                        
                        similarity = matrix[i, j]
                        
                        # Calculate individual component similarities for more detailed analysis
                        seniority_similarity = calculator._calculate_seniority_similarity(job1, job2)
                        role_track_similarity = calculator._calculate_role_track_similarity(job1, job2)
                        location_similarity = calculator._calculate_location_similarity(job1, job2)
                        
                        consolidated_results.append({
                            "Scenario": scenario["description"],
                            "Job1_ID": job1_id,
                            "Job1_Title": job1.title,
                            "Job1_Department": job1.department,
                            "Job1_Seniority": job1.seniority,
                            "Job1_RoleTrack": job1.role_track.value,
                            "Job1_Location": job1.location,
                            "Job2_ID": job2_id,
                            "Job2_Title": job2.title,
                            "Job2_Department": job2.department,
                            "Job2_Seniority": job2.seniority, 
                            "Job2_RoleTrack": job2.role_track.value,
                            "Job2_Location": job2.location,
                            "Similarity": similarity,
                            "Seniority_Weight": scenario["weights"]["seniority"],
                            "RoleTrack_Weight": scenario["weights"]["role_track"],
                            "Location_Weight": scenario["weights"]["location"],
                            "Seniority_Similarity": seniority_similarity,
                            "RoleTrack_Similarity": role_track_similarity,
                            "Location_Similarity": location_similarity
                        })
        
        # Create a consolidated dataframe with all pairwise similarities
        consolidated_df = pd.DataFrame(consolidated_results)
        
        # Save consolidated results to CSV
        consolidated_df.to_csv(self.output_dir / "consolidated_similarity_results.csv", index=False)
        
        # Create a comparison DataFrame for scenarios
        comparison_df = pd.DataFrame([
            {
                "Scenario": r["description"],
                "Average Similarity": r["avg_similarity"],
                "High Similarity Pairs": r["high_similarity_count"]
            }
            for r in results
        ])
        
        # Save comparison to CSV
        comparison_df.to_csv(self.output_dir / "scenario_comparison.csv", index=False)
        
        # Verify that enhancements have an effect
        base_avg = results[0]["avg_similarity"]
        
        # At least some scenarios should produce different results
        different_results_found = False
        for i in range(1, len(results)):
            if abs(results[i]["avg_similarity"] - base_avg) > 0.01:  # 1% difference threshold
                different_results_found = True
                break
        
        self.assertTrue(different_results_found, "Enhancements should affect similarity scores")
    
    def test_similar_jobs_with_enhancements(self):
        """
        Test finding similar jobs with different enhancement settings.
        
        This test takes a single job (the first job in the dataset) and compares
        it against all other jobs, using different enhancement scenarios.
        
        The test creates a one-to-many comparison (one reference job compared to many target jobs).
        """
        # Get a test job
        test_job_id = list(self.job_architecture.jobs.keys())[0]
        test_job = self.job_architecture.jobs[test_job_id]
        
        # Log information about the reference job
        print(f"\nReference job for similarity test: {test_job.title} (ID: {test_job_id})")
        print(f"Department: {test_job.department}, Level: {test_job.level.value}")
        print(f"Seniority: {test_job.seniority}, Role Track: {test_job.role_track.value}, Location: {test_job.location}")
        
        # Define scenarios
        scenarios = [
            {
                "name": "skills_only",
                "weights": {"seniority": 0.0, "role_track": 0.0, "location": 0.0},
                "description": "Base skills only"
            },
            {
                "name": "with_seniority_only",
                "weights": {"seniority": 1.0, "role_track": 0.0, "location": 0.0},
                "description": "With seniority only"
            },
            {
                "name": "with_role_track_only",
                "weights": {"seniority": 0.0, "role_track": 1.0, "location": 0.0},
                "description": "With role track only"
            },
            {
                "name": "with_location_only",
                "weights": {"seniority": 0.0, "role_track": 0.0, "location": 1.0},
                "description": "With location only"
            },
            {
                "name": "with_all_enhancements",
                "weights": {"seniority": 0.5, "role_track": 0.5, "location": 0.5},
                "description": "With all enhancements"
            },
            {
                "name": "career_focused",
                "weights": {"seniority": 0.8, "role_track": 0.6, "location": 0.2},
                "description": "Career progression focused"
            }
        ]
        
        all_results = {}
        all_similar_jobs = []
        
        # For each scenario
        for scenario in scenarios:
            # Set weights
            self.config_manager.config.future_extensions.seniority_weight = scenario["weights"]["seniority"]
            self.config_manager.config.future_extensions.role_track_weight = scenario["weights"]["role_track"]
            self.config_manager.config.future_extensions.location_weight = scenario["weights"]["location"]
            
            # Find similar jobs
            similar_jobs = self.calculator.find_similar_jobs(test_job_id, top_n=10)
            
            # Store results
            all_results[scenario["name"]] = similar_jobs
            
            # Create a more detailed DataFrame for analysis
            similar_jobs_df = pd.DataFrame([
                {
                    "Job ID": job_id,
                    "Title": self.job_architecture.jobs[job_id].title,
                    "Department": self.job_architecture.jobs[job_id].department,
                    "Level": self.job_architecture.jobs[job_id].level.value,
                    "Seniority": self.job_architecture.jobs[job_id].seniority,
                    "Role Track": self.job_architecture.jobs[job_id].role_track.value,
                    "Location": self.job_architecture.jobs[job_id].location,
                    "Similarity": similarity
                }
                for job_id, similarity in similar_jobs
            ])
            
            # Save to CSV
            similar_jobs_df.to_csv(
                self.output_dir / f"similar_jobs_{scenario['name']}.csv", 
                index=False
            )
            
            # Add to consolidated results
            for job_id, similarity in similar_jobs:
                job = self.job_architecture.jobs[job_id]
                all_similar_jobs.append({
                    "Scenario": scenario["description"],
                    "Job_ID": job_id,
                    "Title": job.title,
                    "Department": job.department,
                    "Level": job.level.value,
                    "Seniority": job.seniority,
                    "Role_Track": job.role_track.value,
                    "Location": job.location,
                    "Similarity": similarity,
                    "Seniority_Weight": scenario["weights"]["seniority"],
                    "RoleTrack_Weight": scenario["weights"]["role_track"],
                    "Location_Weight": scenario["weights"]["location"],
                    "Reference_Job": test_job_id,
                    "Reference_Title": test_job.title,
                })
        
        # Create a consolidated DataFrame for all scenarios
        all_similar_jobs_df = pd.DataFrame(all_similar_jobs)
        
        # Save consolidated results
        all_similar_jobs_df.to_csv(
            self.output_dir / "similar_jobs_all_scenarios.csv",
            index=False
        )
        
        # Compare the scenarios
        base_similar_jobs = set(job_id for job_id, _ in all_results["skills_only"])
        enhanced_similar_jobs = set(job_id for job_id, _ in all_results["with_all_enhancements"])
        
        # There should be some differences in the results
        self.assertNotEqual(
            base_similar_jobs, 
            enhanced_similar_jobs,
            "Enhancements should affect which jobs are considered similar"
        )
        
        # Create a comparison DataFrame
        comparison_df = pd.DataFrame([
            {
                "Job ID": job_id,
                "Title": self.job_architecture.jobs[job_id].title,
                "In Skills-Only": job_id in base_similar_jobs,
                "In Enhanced": job_id in enhanced_similar_jobs,
                "Skills-Only Similarity": next((sim for jid, sim in all_results["skills_only"] 
                                             if jid == job_id), None),
                "Enhanced Similarity": next((sim for jid, sim in all_results["with_all_enhancements"] 
                                          if jid == job_id), None)
            }
            for job_id in base_similar_jobs.union(enhanced_similar_jobs)
        ])
        
        # Save to CSV
        comparison_df.to_csv(
            self.output_dir / "similar_jobs_comparison.csv", 
            index=False
        )
    
    def _create_similarity_heatmap(self, matrix, job_ids, filename, title):
        """Create a heatmap visualization of the similarity matrix."""
        plt.figure(figsize=(12, 10))
        plt.imshow(matrix, cmap='viridis', interpolation='nearest')
        plt.colorbar(label="Similarity")
        plt.title(f"Job Similarity Heatmap - {title}")
        
        # Add job IDs as labels if not too many
        if len(job_ids) <= 20:
            plt.xticks(range(len(job_ids)), job_ids, rotation=90)
            plt.yticks(range(len(job_ids)), job_ids)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / filename, dpi=300)
        plt.close()


if __name__ == "__main__":
    unittest.main() 