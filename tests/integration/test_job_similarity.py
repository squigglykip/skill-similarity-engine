import sys
import os

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

print("Starting job similarity test with sample data...")

# Import necessary modules
from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator
import pandas as pd

# Create skill taxonomy
skill_taxonomy = SkillTaxonomy()

# Add skills directly
skill_taxonomy.add_skill(Skill(skill_id='S001', name='Python'))
skill_taxonomy.add_skill(Skill(skill_id='S002', name='Data Analysis'))
skill_taxonomy.add_skill(Skill(skill_id='S003', name='Machine Learning'))
skill_taxonomy.add_skill(Skill(skill_id='S004', name='Project Management'))
skill_taxonomy.add_skill(Skill(skill_id='S005', name='Communication'))

print(f"Created skill taxonomy with {len(skill_taxonomy.skills)} skills")

# Create job architecture
job_arch = JobArchitecture()

# Add jobs directly
job1 = Job(job_id='J001', title='Data Scientist', department='Data', level='Senior')
job1.add_skill('S001', 3)  # Python
job1.add_skill('S002', 3)  # Data Analysis
job1.add_skill('S003', 3)  # Machine Learning
job_arch.add_job(job1)

job2 = Job(job_id='J002', title='Data Analyst', department='Data', level='Mid-level')
job2.add_skill('S001', 2)  # Python
job2.add_skill('S002', 3)  # Data Analysis
job_arch.add_job(job2)

job3 = Job(job_id='J003', title='ML Engineer', department='Engineering', level='Senior')
job3.add_skill('S001', 3)  # Python
job3.add_skill('S003', 4)  # Machine Learning
job_arch.add_job(job3)

job4 = Job(job_id='J004', title='Project Manager', department='Management', level='Mid-level')
job4.add_skill('S004', 3)  # Project Management
job4.add_skill('S005', 3)  # Communication
job_arch.add_job(job4)

job5 = Job(job_id='J005', title='Business Analyst', department='Business', level='Mid-level')
job5.add_skill('S002', 3)  # Data Analysis
job5.add_skill('S004', 2)  # Project Management
job5.add_skill('S005', 3)  # Communication
job_arch.add_job(job5)

print(f"Created job architecture with {len(job_arch.jobs)} jobs")

# Calculate similarity
vectorizer = TfidfVectorizer(skill_taxonomy)
calculator = CosineSimilarityCalculator(
    vectorizer=vectorizer,
    skill_taxonomy=skill_taxonomy,
    job_architecture=job_arch
)

# Test job similarity for specific pairs
print('\nTesting job similarity for specific pairs:')
print(f"Data Scientist vs Data Analyst: {calculator.calculate_job_similarity('J001', 'J002'):.2f}")
print(f"Data Scientist vs ML Engineer: {calculator.calculate_job_similarity('J001', 'J003'):.2f}")
print(f"Data Analyst vs Business Analyst: {calculator.calculate_job_similarity('J002', 'J005'):.2f}")
print(f"Project Manager vs Business Analyst: {calculator.calculate_job_similarity('J004', 'J005'):.2f}")

# Get job similarity matrix
similarity_matrix = []
for i, job_id1 in enumerate(job_arch.jobs):
    row = []
    for j, job_id2 in enumerate(job_arch.jobs):
        if i == j:
            # Jobs are identical to themselves
            row.append(1.0)
        else:
            row.append(calculator.calculate_job_similarity(job_id1, job_id2))
    similarity_matrix.append(row)

print('\nJob Similarity Matrix:')
for i, row in enumerate(similarity_matrix):
    job_title = list(job_arch.jobs.values())[i].title
    print(f"{job_title}: {[round(val, 2) for val in row]}")

print('\nTop 3 most similar job pairs:')
job_pairs = []
job_ids = list(job_arch.jobs.keys())
for i in range(len(job_ids)):
    for j in range(i+1, len(job_ids)):
        job1_id = job_ids[i]
        job2_id = job_ids[j]
        similarity = calculator.calculate_job_similarity(job1_id, job2_id)
        job_pairs.append((job1_id, job2_id, similarity))

job_pairs.sort(key=lambda x: x[2], reverse=True)
for i in range(min(3, len(job_pairs))):
    job1_title = job_arch.jobs[job_pairs[i][0]].title
    job2_title = job_arch.jobs[job_pairs[i][1]].title
    print(f"{job1_title} <-> {job2_title}: {job_pairs[i][2]:.2f}")

print('\nBasic performance test:')
import time
start_time = time.time()
# Run the calculation again for all pairs
for job_id1 in job_arch.jobs:
    for job_id2 in job_arch.jobs:
        if job_id1 != job_id2:
            calculator.calculate_job_similarity(job_id1, job_id2)
end_time = time.time()
print(f'Time taken for {len(job_arch.jobs)**2 - len(job_arch.jobs)} similarity calculations: {end_time - start_time:.4f} seconds')

print('\nTest completed successfully!') 