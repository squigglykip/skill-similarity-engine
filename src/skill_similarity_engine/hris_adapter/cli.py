"""
HRIS Adapter CLI Module.

This module provides the command-line interface for the HRIS adapter,
allowing users to transform HRIS data and run analyses directly from the
command line.
"""

import argparse
import os
import sys
import traceback
import pandas as pd
from typing import Dict, Any, Optional

from .workflow import hris_workflow, HRISWorkflow
from ..config.settings import get_config


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="HRIS Data Analysis - Transform and analyze HRIS data"
    )
    parser.add_argument(
        "--analysis-type", "-a",
        required=True,
        choices=["job_similarity", "employee_job_similarity", 
                "employee_similarity", "skill_gap_analysis"],
        help="Type of analysis to run"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to HRIS configuration file"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="Directory for output files"
    )
    parser.add_argument(
        "--employee-id", "-e",
        help="ID of the employee to analyze (for skill gap analysis)"
    )
    parser.add_argument(
        "--job-id", "-j",
        help="ID of the job to analyze (for skill gap analysis)"
    )
    parser.add_argument(
        "--department", "-d",
        help="Filter by department"
    )
    parser.add_argument(
        "--output-format", "-f",
        choices=["csv", "json", "excel"],
        default="csv",
        help="Output file format"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def save_results(args: argparse.Namespace, result: Any) -> str:
    """
    Save analysis results to a file.
    
    Args:
        args: Command-line arguments
        result: Analysis results
    
    Returns:
        Path to the saved file
    """
    # Determine output directory
    output_dir = args.output_dir or get_config().output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Format results based on analysis type
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
        df = result
        parts = ["skill_gap"]
        if args.employee_id:
            parts.append(f"emp_{args.employee_id}")
        if args.job_id:
            parts.append(f"job_{args.job_id}")
        if args.department:
            parts.append(args.department)
        
        output_file = os.path.join(output_dir, f"{'_'.join(parts)}.{args.output_format}")
    
    # Save to the requested format
    if args.output_format == "csv":
        df.to_csv(output_file)
    elif args.output_format == "json":
        df.to_json(output_file, orient="records")
    else:  # excel
        df.to_excel(output_file, index=True)
    
    return output_file


def main() -> int:
    """
    Main entry point for the HRIS CLI.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Configure the workflow
        workflow = hris_workflow
        if args.config:
            log_level = "DEBUG" if args.verbose else "INFO"
            workflow = HRISWorkflow(args.config, log_level)
        
        # Prepare analysis parameters
        kwargs = {}
        if args.employee_id:
            kwargs["employee_id"] = args.employee_id
        if args.job_id:
            kwargs["job_id"] = args.job_id
        if args.department:
            kwargs["department"] = args.department
        
        # Run the analysis
        print(f"Running {args.analysis_type} analysis...")
        result = workflow.run_pipeline(args.analysis_type, **kwargs)
        
        # Save the results
        output_file = save_results(args, result)
        print(f"Analysis completed successfully. Results saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if getattr(args, 'verbose', False):
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 