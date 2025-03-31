#!/usr/bin/env python3
"""
HRIS Analysis Script.

This script provides a simple interface to run the complete workflow from HRIS data to
analysis results, automatically handling the transformation of HRIS data into the format
expected by the skill similarity engine.
"""

import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Add the src directory to the path so we can import our package
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.hris_adapter import hris_workflow
from skill_similarity_engine.visualization.reports import ReportGenerator
from skill_similarity_engine.config.settings import get_config


def main():
    """
    Main entry point for the HRIS analysis script.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run analysis on HRIS data")
    parser.add_argument(
        "--analysis-type",
        required=True,
        choices=["job_similarity", "employee_job_similarity", "employee_similarity", "skill_gap_analysis"],
        help="Type of analysis to run"
    )
    parser.add_argument(
        "--config",
        help="Path to HRIS configuration file"
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for output files"
    )
    parser.add_argument(
        "--employee-id",
        help="ID of the employee to analyze (for skill gap analysis)"
    )
    parser.add_argument(
        "--job-id",
        help="ID of the job to analyze (for skill gap analysis)"
    )
    parser.add_argument(
        "--department",
        help="Filter by department"
    )
    parser.add_argument(
        "--output-format",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output file format"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging level
    log_level = "DEBUG" if args.verbose else "INFO"
    
    try:
        # Initialize workflow with config if provided
        workflow = hris_workflow
        if args.config:
            workflow = hris_workflow.__class__(args.config, log_level)
        
        # Prepare kwargs for analysis
        kwargs = {}
        if args.employee_id:
            kwargs["employee_id"] = args.employee_id
        if args.job_id:
            kwargs["job_id"] = args.job_id
        if args.department:
            kwargs["department"] = args.department
        
        # Run the pipeline
        result = workflow.run_pipeline(args.analysis_type, **kwargs)
        
        # Save results
        output_dir = args.output_dir or get_config().output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        if args.analysis_type == "job_similarity":
            similarity_matrix, job_ids = result
            df = pd.DataFrame(similarity_matrix, index=job_ids, columns=job_ids)
            output_file = os.path.join(output_dir, f"job_similarity.{args.output_format}")
        
        elif args.analysis_type == "employee_job_similarity":
            similarity_matrix, employee_ids, job_ids = result
            df = pd.DataFrame(similarity_matrix, index=employee_ids, columns=job_ids)
            output_file = os.path.join(output_dir, f"employee_job_similarity.{args.output_format}")
        
        elif args.analysis_type == "employee_similarity":
            similarity_matrix, employee_ids = result
            df = pd.DataFrame(similarity_matrix, index=employee_ids, columns=employee_ids)
            output_file = os.path.join(output_dir, f"employee_similarity.{args.output_format}")
        
        elif args.analysis_type == "skill_gap_analysis":
            # For skill gap analysis, result is already a DataFrame
            df = result
            parts = ["skill_gap"]
            if args.employee_id:
                parts.append(f"emp_{args.employee_id}")
            if args.job_id:
                parts.append(f"job_{args.job_id}")
            if args.department:
                parts.append(args.department)
            
            output_file = os.path.join(output_dir, f"{'_'.join(parts)}.{args.output_format}")
        
        # Save the results
        if args.output_format == "csv":
            df.to_csv(output_file)
        elif args.output_format == "json":
            df.to_json(output_file, orient="records")
        else:  # excel
            df.to_excel(output_file, index=True)
        
        print(f"Analysis completed successfully. Results saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 