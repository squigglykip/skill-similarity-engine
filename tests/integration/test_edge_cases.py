import sys
import os

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print("Starting edge case tests for job-to-job similarity...")

# Import necessary modules
from skill_similarity_engine.models.skills import Skill, SkillTaxonomy
from skill_similarity_engine.models.jobs import Job, JobArchitecture
from skill_similarity_engine.similarity.cosine import TfidfVectorizer, CosineSimilarityCalculator

# Test case 1: Empty skill sets
print("\n----- Test Case 1: Jobs with empty skill sets -----")
skill_taxonomy = SkillTaxonomy()
skill_taxonomy.add_skill(Skill(skill_id='S001', name='Python'))
skill_taxonomy.add_skill(Skill(skill_id='S002', name='Data Analysis'))

job_arch = JobArchitecture()
job1 = Job(job_id='J001', title='Normal Job', department='IT', level='Senior')
job1.add_skill('S001', 3)
job_arch.add_job(job1)

job2 = Job(job_id='J002', title='Empty Skills Job', department='IT', level='Senior')
# No skills added
job_arch.add_job(job2)

vectorizer = TfidfVectorizer(skill_taxonomy)
calculator = CosineSimilarityCalculator(
    vectorizer=vectorizer,
    skill_taxonomy=skill_taxonomy,
    job_architecture=job_arch
)

try:
    similarity = calculator.calculate_job_similarity('J001', 'J002')
    print(f"Similarity between job with skills and job without skills: {similarity:.2f}")
    print("✓ Successfully handled comparison with empty skill set")
except Exception as e:
    print(f"✗ Error handling empty skill set: {e}")

# Test case 2: Jobs with extremely high number of skills
print("\n----- Test Case 2: Jobs with many skills -----")
# Create a larger skill taxonomy
for i in range(3, 103):  # Add 100 more skills
    skill_id = f'S{i:03d}'
    skill_taxonomy.add_skill(Skill(skill_id=skill_id, name=f'Skill {i}'))

# Create a job with many skills
job3 = Job(job_id='J003', title='Job with many skills', department='IT', level='Senior')
for i in range(1, 101):  # Add 100 skills with varying proficiency
    skill_id = f'S{i:03d}'
    job3.add_skill(skill_id, i % 5 + 1)  # Proficiency between 1-5
job_arch.add_job(job3)

# Reset calculator with updated data
vectorizer = TfidfVectorizer(skill_taxonomy)
calculator = CosineSimilarityCalculator(
    vectorizer=vectorizer,
    skill_taxonomy=skill_taxonomy,
    job_architecture=job_arch
)

try:
    similarity = calculator.calculate_job_similarity('J001', 'J003')
    print(f"Similarity between normal job and job with 100 skills: {similarity:.2f}")
    print("✓ Successfully handled job with many skills")
    
    import time
    start_time = time.time()
    similarity = calculator.calculate_job_similarity('J003', 'J001')
    end_time = time.time()
    print(f"Time taken for calculation with 100 skills: {end_time - start_time:.4f} seconds")
except Exception as e:
    print(f"✗ Error handling job with many skills: {e}")

# Test case 3: Unusual skill taxonomy structure
print("\n----- Test Case 3: Unusual skill taxonomy structures -----")
# Create a taxonomy with duplicate skill names (different IDs)
unusual_taxonomy = SkillTaxonomy()
unusual_taxonomy.add_skill(Skill(skill_id='S001', name='Python'))
unusual_taxonomy.add_skill(Skill(skill_id='S002', name='Python Programming'))  # Similar name
unusual_taxonomy.add_skill(Skill(skill_id='S003', name='python'))  # Case variation

unusual_arch = JobArchitecture()
job4 = Job(job_id='J004', title='Job with Python', department='IT', level='Senior')
job4.add_skill('S001', 3)
unusual_arch.add_job(job4)

job5 = Job(job_id='J005', title='Job with python', department='IT', level='Senior')
job5.add_skill('S003', 3)  # Different skill ID, but similar name
unusual_arch.add_job(job5)

unusual_vectorizer = TfidfVectorizer(unusual_taxonomy)
unusual_calculator = CosineSimilarityCalculator(
    vectorizer=unusual_vectorizer,
    skill_taxonomy=unusual_taxonomy,
    job_architecture=unusual_arch
)

try:
    similarity = unusual_calculator.calculate_job_similarity('J004', 'J005')
    print(f"Similarity between jobs with similarly named but different skills: {similarity:.2f}")
    print("✓ Successfully handled unusual taxonomy with similar skill names")
except Exception as e:
    print(f"✗ Error handling unusual taxonomy: {e}")

# Test case 4: Jobs with missing or invalid data
print("\n----- Test Case 4: Jobs with missing or invalid data -----")
incomplete_arch = JobArchitecture()

# Add a normal job
job6 = Job(job_id='J006', title='Normal Job', department='IT', level='Senior')
job6.add_skill('S001', 3)
incomplete_arch.add_job(job6)

try:
    # Try to calculate similarity with non-existent job
    unusual_calculator = CosineSimilarityCalculator(
        vectorizer=unusual_vectorizer,
        skill_taxonomy=unusual_taxonomy,
        job_architecture=incomplete_arch
    )
    similarity = unusual_calculator.calculate_job_similarity('J006', 'NON_EXISTENT')
    print("✗ Failed to catch non-existent job")
except Exception as e:
    print(f"✓ Correctly handled non-existent job: {e}")

# Test case 5: Error handling for invalid input
print("\n----- Test Case 5: Error handling for invalid inputs -----")
try:
    # Try to add a skill with invalid proficiency
    job7 = Job(job_id='J007', title='Invalid Job', department='IT', level='Senior')
    job7.add_skill('S001', 10)  # Proficiency should be 0-5
    print("✗ Failed to catch invalid proficiency")
except Exception as e:
    print(f"✓ Correctly handled invalid proficiency: {e}")

try:
    # Try to create job with invalid level
    job8 = Job(job_id='J008', title='Invalid Level Job', department='IT', level='InvalidLevel')
    print("✗ Failed to catch invalid job level")
except Exception as e:
    print(f"✓ Correctly handled invalid job level: {e}")

print("\nEdge case tests completed!")
print("="*50) 