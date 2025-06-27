from typing import Optional
import pandas as pd

class Exporter:
    def export_job_similarity_matrix(
        self,
        similarity_matrix: pd.DataFrame,
        department: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Export job similarity matrix, optionally filtered by department.
        
        Args:
            similarity_matrix: The similarity matrix DataFrame
            department: Optional department to filter by
            
        Returns:
            DataFrame containing the similarity matrix
        """
        if department:
            # Get jobs for the specified department
            dept_jobs = {job_id: job for job_id, job in self.job_arch.jobs.items() 
                        if job.department == department}
            dept_job_ids = list(dept_jobs.keys())
            
            # Filter similarity matrix to only include department jobs
            filtered_matrix = similarity_matrix.loc[dept_job_ids, dept_job_ids]
            return filtered_matrix
        
        return similarity_matrix 
