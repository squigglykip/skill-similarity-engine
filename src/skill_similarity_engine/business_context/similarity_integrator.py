"""
Similarity Data Integration Module

Loads pre-computed job similarity matrices from Parquet files and integrates 
them into the SQLite business context database.

Handles:
- Parquet similarity matrix loading
- Data transformation to SQLite format
- JobProfileID coverage validation
- Similarity score analysis and metadata
"""

import logging
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Import progress tracking utilities
from ..utils.progress import ProgressTracker, progress_context

logger = logging.getLogger(__name__)


class SimilarityIntegrator:
    """Integrates pre-computed similarity data into business context database."""
    
    def __init__(self, db_path: str):
        """
        Initialize similarity integrator.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.integration_stats = {}
        
    def load_similarity_matrix(self, 
                              similarity_file: str,
                              chunk_size: int = 50000) -> bool:
        """
        Load similarity matrix from Parquet file into database.
        
        Args:
            similarity_file: Path to job_similarity_matrix.parquet
            chunk_size: Number of rows to process at once
            
        Returns:
            True if integration successful
        """
        similarity_path = Path(similarity_file)
        
        if not similarity_path.exists():
            logger.error(f"Similarity file not found: {similarity_path}")
            return False
        
        try:
            logger.info(f"Loading similarity matrix from {similarity_path}")
            
            # Read parquet file
            df = pd.read_parquet(similarity_path)
            logger.info(f"Loaded {len(df):,} similarity pairs from parquet")
            
            # Validate required columns (allowing both naming conventions)
            required_columns = ['job_from', 'job_to']
            similarity_column = None
            
            # Check for similarity column (either 'similarity' or 'similarity_score')
            if 'similarity_score' in df.columns:
                similarity_column = 'similarity_score'
            elif 'similarity' in df.columns:
                similarity_column = 'similarity'
            
            if similarity_column is None:
                logger.error("Missing similarity column: expected 'similarity' or 'similarity_score'")
                return False
            
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            # Map columns to database schema
            column_mapping = {
                'job_from': 'job_from',
                'job_to': 'job_to', 
                similarity_column: 'similarity_score'  # Map actual column to database schema
            }
            
            # Add optional columns if they exist
            optional_mappings = {
                'skill_overlap_score': 'skill_overlap_score',
                'shared_skills_count': 'shared_skills_count',
                'total_skills_from': 'total_skills_from',
                'total_skills_to': 'total_skills_to'
            }
            
            for old_col, new_col in optional_mappings.items():
                if old_col in df.columns:
                    column_mapping[old_col] = new_col
            
            # Select and rename columns
            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            df_mapped = df[available_columns].rename(columns=column_mapping)
            
            # Add missing optional columns with defaults
            required_db_columns = ['job_from', 'job_to', 'similarity_score', 
                                 'skill_overlap_score', 'shared_skills_count', 
                                 'total_skills_from', 'total_skills_to']
            
            for col in required_db_columns:
                if col not in df_mapped.columns:
                    if col in ['shared_skills_count', 'total_skills_from', 'total_skills_to']:
                        df_mapped[col] = None  # Integer fields
                    else:
                        df_mapped[col] = None  # Real fields
            
            # Clean and validate data
            df_mapped = self._clean_similarity_data(df_mapped)
            
            # Verify job coverage before loading
            if not self._verify_job_coverage(df_mapped):
                logger.warning("Job coverage validation failed - proceeding with available data")
            
            # Load into database in chunks
            success = self._load_similarity_chunks(df_mapped, chunk_size)
            
            if success:
                # Calculate and store integration statistics
                self._calculate_integration_stats(df_mapped)
                logger.info("Similarity matrix integration completed successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to integrate similarity matrix: {e}")
            return False
    
    def _clean_similarity_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate similarity data."""
        logger.info("Cleaning similarity data...")
        
        original_count = len(df)
        
        # Remove rows with missing job IDs
        df = df.dropna(subset=['job_from', 'job_to'])
        
        # Remove self-similarities (job_from == job_to)
        df = df[df['job_from'] != df['job_to']]
        
        # Validate similarity scores (should be 0-1)
        df = df[(df['similarity_score'] >= 0) & (df['similarity_score'] <= 1)]
        
        # Remove duplicate pairs
        df = df.drop_duplicates(subset=['job_from', 'job_to'])
        
        cleaned_count = len(df)
        removed_count = original_count - cleaned_count
        
        if removed_count > 0:
            logger.info(f"Cleaned data: removed {removed_count:,} invalid records ({removed_count/original_count*100:.1f}%)")
        
        return df
    
    def _verify_job_coverage(self, df: pd.DataFrame) -> bool:
        """Verify that all JobProfileIDs in similarity data exist in jobs table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get all JobProfileIDs from jobs table
                cursor = conn.execute("SELECT JobProfileID FROM jobs")
                valid_job_ids = set(row[0] for row in cursor.fetchall())
                
            # Get unique job IDs from similarity data
            similarity_job_ids = set(df['job_from'].unique()) | set(df['job_to'].unique())
            
            # Find missing job IDs
            missing_job_ids = similarity_job_ids - valid_job_ids
            
            if missing_job_ids:
                logger.warning(f"Found {len(missing_job_ids)} job IDs in similarity data not in jobs table")
                logger.debug(f"Missing job IDs: {list(missing_job_ids)[:10]}...")  # Show first 10
                return False
            
            logger.info("✓ All job IDs in similarity data exist in jobs table")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify job coverage: {e}")
            return False
    
    def _load_similarity_chunks(self, df: pd.DataFrame, chunk_size: int) -> bool:
        """Load similarity data in chunks to handle large datasets."""
        try:
            total_rows = len(df)
            total_chunks = (total_rows + chunk_size - 1) // chunk_size
            logger.info(f"Loading {total_rows:,} similarity records in chunks of {chunk_size:,}")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing similarity data
                conn.execute("DELETE FROM job_similarities")
                logger.info("Cleared existing similarity data")
                
                # Load data in chunks with progress tracking
                with ProgressTracker(
                    total=total_chunks,
                    desc="Loading similarity records",
                    memory_tracking=False,  # Skip memory tracking for DB operations
                    show_tqdm=True
                ) as progress:
                    
                    for i in range(0, total_rows, chunk_size):
                        chunk = df.iloc[i:i+chunk_size]
                        
                        chunk.to_sql('job_similarities', conn, if_exists='append', index=False)
                        
                        # Update progress bar
                        progress.update(1)
                
                # Verify final row count
                cursor = conn.execute("SELECT COUNT(*) FROM job_similarities")
                final_count = cursor.fetchone()[0]
                
                if final_count == total_rows:
                    logger.info(f"✓ Successfully loaded {final_count:,} similarity records")
                    return True
                else:
                    logger.error(f"Row count mismatch: expected {total_rows}, got {final_count}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to load similarity chunks: {e}")
            return False
    
    def _calculate_integration_stats(self, df: pd.DataFrame) -> None:
        """Calculate and store integration statistics."""
        try:
            stats = {
                'total_similarity_pairs': len(df),
                'unique_jobs_from': df['job_from'].nunique(),
                'unique_jobs_to': df['job_to'].nunique(),
                'unique_jobs_total': len(set(df['job_from'].unique()) | set(df['job_to'].unique())),
                'avg_similarity_score': df['similarity_score'].mean(),
                'min_similarity_score': df['similarity_score'].min(),
                'max_similarity_score': df['similarity_score'].max(),
                'high_similarity_pairs': len(df[df['similarity_score'] >= 0.8]),  # Similar jobs
                'low_similarity_pairs': len(df[df['similarity_score'] < 0.2])     # Dissimilar jobs
            }
            
            # Add skill-based statistics if available
            if 'shared_skills_count' in df.columns and df['shared_skills_count'].notna().any():
                stats.update({
                    'avg_shared_skills': df['shared_skills_count'].mean(),
                    'max_shared_skills': df['shared_skills_count'].max(),
                    'pairs_with_skill_data': df['shared_skills_count'].notna().sum()
                })
            
            self.integration_stats = stats
            
            # Log key statistics
            logger.info(f"Integration Statistics:")
            logger.info(f"  Total similarity pairs: {stats['total_similarity_pairs']:,}")
            logger.info(f"  Unique jobs covered: {stats['unique_jobs_total']:,}")
            logger.info(f"  Average similarity: {stats['avg_similarity_score']:.3f}")
            logger.info(f"  High similarity pairs (≥0.8): {stats['high_similarity_pairs']:,}")
            
        except Exception as e:
            logger.error(f"Failed to calculate integration stats: {e}")
    
    def find_similarity_files(self, models_dir: str = "models") -> List[Path]:
        """
        Find available similarity matrix files in models directory.
        
        Args:
            models_dir: Base models directory
            
        Returns:
            List of paths to similarity matrix files
        """
        models_path = Path(models_dir)
        similarity_files = []
        
        if not models_path.exists():
            logger.warning(f"Models directory not found: {models_path}")
            return similarity_files
        
        # Search for parquet files in quarterly directories
        for quarter_dir in models_path.iterdir():
            if quarter_dir.is_dir() and quarter_dir.name != "current":
                parquet_file = quarter_dir / "job_similarity_matrix.parquet"
                if parquet_file.exists():
                    similarity_files.append(parquet_file)
                
                # Also check subdirectories
                for subdir in quarter_dir.iterdir():
                    if subdir.is_dir():
                        parquet_file = subdir / "job_similarity_matrix.parquet"
                        if parquet_file.exists():
                            similarity_files.append(parquet_file)
        
        # Sort by modification time (newest first)
        similarity_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return similarity_files
    
    def get_latest_similarity_file(self, models_dir: str = "models") -> Optional[Path]:
        """
        Get the most recent similarity matrix file.
        
        Args:
            models_dir: Base models directory
            
        Returns:
            Path to latest similarity file or None if not found
        """
        similarity_files = self.find_similarity_files(models_dir)
        
        if similarity_files:
            latest_file = similarity_files[0]
            logger.info(f"Found latest similarity file: {latest_file}")
            return latest_file
        else:
            logger.warning("No similarity matrix files found")
            return None
    
    def get_integration_statistics(self) -> Dict:
        """
        Get integration statistics.
        
        Returns:
            Dictionary with integration statistics
        """
        return self.integration_stats.copy()
    
    def analyze_similarity_distribution(self) -> Dict:
        """
        Analyze similarity score distribution in the database.
        
        Returns:
            Dictionary with distribution analysis
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get similarity score distribution
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_pairs,
                        AVG(similarity_score) as avg_score,
                        MIN(similarity_score) as min_score,
                        MAX(similarity_score) as max_score,
                        COUNT(CASE WHEN similarity_score >= 0.8 THEN 1 END) as high_similarity,
                        COUNT(CASE WHEN similarity_score >= 0.6 AND similarity_score < 0.8 THEN 1 END) as medium_similarity,
                        COUNT(CASE WHEN similarity_score >= 0.4 AND similarity_score < 0.6 THEN 1 END) as moderate_similarity,
                        COUNT(CASE WHEN similarity_score < 0.4 THEN 1 END) as low_similarity
                    FROM job_similarities
                """)
                
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    return {
                        'total_pairs': result[0],
                        'avg_score': result[1],
                        'min_score': result[2],
                        'max_score': result[3],
                        'high_similarity': result[4],
                        'medium_similarity': result[5],
                        'moderate_similarity': result[6],
                        'low_similarity': result[7],
                        'high_similarity_pct': (result[4] / result[0]) * 100 if result[0] > 0 else 0
                    }
                else:
                    return {'error': 'No similarity data found in database'}
                    
        except Exception as e:
            logger.error(f"Failed to analyze similarity distribution: {e}")
            return {'error': str(e)} 