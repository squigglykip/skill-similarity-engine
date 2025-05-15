import pandas as pd
import os
import sys

# Path to the output directory
output_dir = "data/poc/output/poc_run_20250515_122510"

# Check if the directory exists
if not os.path.exists(output_dir):
    print(f"Directory {output_dir} does not exist")
    sys.exit(1)

# Check the main job similarity file
main_file = os.path.join(output_dir, "job_similarity_all_departments.csv")
if os.path.exists(main_file):
    try:
        df = pd.read_csv(main_file)
        print(f"Main file columns: {df.columns.tolist()}")
        print(f"Main file shape: {df.shape}")
        print("\nMain file first 5 rows:")
        print(df.head())
    except Exception as e:
        print(f"Error reading main file: {e}")

# Check a department file
dept_file = os.path.join(output_dir, "similarity_matrix_Colleague Services.csv")
if os.path.exists(dept_file):
    try:
        df = pd.read_csv(dept_file)
        print(f"\nDepartment file columns: {df.columns.tolist()}")
        print(f"Department file shape: {df.shape}")
        print("\nDepartment file first 5 rows:")
        print(df.head())
    except Exception as e:
        print(f"Error reading department file: {e}")

# Check another department file with more data
for file in os.listdir(output_dir):
    if file.startswith("similarity_matrix_") and os.path.getsize(os.path.join(output_dir, file)) > 300:
        try:
            df = pd.read_csv(os.path.join(output_dir, file))
            print(f"\nLarger file {file} columns: {df.columns.tolist()}")
            print(f"Larger file {file} shape: {df.shape}")
            print(f"\nLarger file {file} first 5 rows:")
            print(df.head())
            break
        except Exception as e:
            print(f"Error reading larger file {file}: {e}") 