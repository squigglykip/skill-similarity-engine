#!/usr/bin/env python3
"""
Compare Similarity Matrices Script
Compares two job similarity matrices to analyze differences in results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
from datetime import datetime
import json

def load_similarity_matrix(file_path: Path) -> pd.DataFrame:
    """Load similarity matrix from parquet file."""
    print(f"ðŸ“Š Loading similarity matrix from: {file_path}")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    df = pd.read_parquet(file_path)
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    
    return df

def analyze_basic_stats(df: pd.DataFrame, name: str) -> dict:
    """Analyze basic statistics of similarity matrix."""
    print(f"\nðŸ“ˆ Basic Statistics for {name}:")
    
    stats = {
        'total_pairs': len(df),
        'unique_jobs': len(set(df['job_from'].unique()) | set(df['job_to'].unique())),
        'similarity_stats': {
            'mean': df['similarity'].mean(),
            'median': df['similarity'].median(),
            'std': df['similarity'].std(),
            'min': df['similarity'].min(),
            'max': df['similarity'].max(),
            'q25': df['similarity'].quantile(0.25),
            'q75': df['similarity'].quantile(0.75)
        }
    }
    
    print(f"   Total job pairs: {stats['total_pairs']:,}")
    print(f"   Unique jobs: {stats['unique_jobs']:,}")
    print(f"   Similarity - Mean: {stats['similarity_stats']['mean']:.4f}")
    print(f"   Similarity - Median: {stats['similarity_stats']['median']:.4f}")
    print(f"   Similarity - Std: {stats['similarity_stats']['std']:.4f}")
    print(f"   Similarity - Range: [{stats['similarity_stats']['min']:.4f}, {stats['similarity_stats']['max']:.4f}]")
    
    return stats

def compare_matrices(old_df: pd.DataFrame, new_df: pd.DataFrame) -> dict:
    """Compare two similarity matrices."""
    print(f"\nðŸ” Comparing Similarity Matrices:")
    
    # Create comparison key for both dataframes
    old_df['pair_key'] = old_df['job_from'] + '|' + old_df['job_to']
    new_df['pair_key'] = new_df['job_from'] + '|' + new_df['job_to']
    
    # Find common pairs
    common_pairs = set(old_df['pair_key']) & set(new_df['pair_key'])
    old_only = set(old_df['pair_key']) - set(new_df['pair_key'])
    new_only = set(new_df['pair_key']) - set(old_df['pair_key'])
    
    print(f"   Common job pairs: {len(common_pairs):,}")
    print(f"   Old matrix only: {len(old_only):,}")
    print(f"   New matrix only: {len(new_only):,}")
    
    if len(common_pairs) == 0:
        print("   âš ï¸  No common pairs found - matrices may use different job sets")
        return {
            'common_pairs': 0,
            'old_only': len(old_only),
            'new_only': len(new_only),
            'correlation': None,
            'differences': None
        }
    
    # Merge on common pairs for comparison
    old_common = old_df[old_df['pair_key'].isin(common_pairs)].set_index('pair_key')['similarity']
    new_common = new_df[new_df['pair_key'].isin(common_pairs)].set_index('pair_key')['similarity']
    
    # Align the series
    comparison_df = pd.DataFrame({
        'old_similarity': old_common,
        'new_similarity': new_common
    }).dropna()
    
    # Calculate differences
    comparison_df['difference'] = comparison_df['new_similarity'] - comparison_df['old_similarity']
    comparison_df['abs_difference'] = comparison_df['difference'].abs()
    comparison_df['percent_change'] = (comparison_df['difference'] / comparison_df['old_similarity']) * 100
    
    # Statistics
    correlation = comparison_df['old_similarity'].corr(comparison_df['new_similarity'])
    
    diff_stats = {
        'mean_diff': comparison_df['difference'].mean(),
        'median_diff': comparison_df['difference'].median(),
        'std_diff': comparison_df['difference'].std(),
        'mean_abs_diff': comparison_df['abs_difference'].mean(),
        'max_abs_diff': comparison_df['abs_difference'].max(),
        'pairs_with_large_diff': len(comparison_df[comparison_df['abs_difference'] > 0.1]),
        'pairs_with_small_diff': len(comparison_df[comparison_df['abs_difference'] < 0.01])
    }
    
    print(f"   Correlation: {correlation:.4f}")
    print(f"   Mean difference: {diff_stats['mean_diff']:.4f}")
    print(f"   Mean absolute difference: {diff_stats['mean_abs_diff']:.4f}")
    print(f"   Max absolute difference: {diff_stats['max_abs_diff']:.4f}")
    print(f"   Pairs with large differences (>0.1): {diff_stats['pairs_with_large_diff']}")
    print(f"   Pairs with small differences (<0.01): {diff_stats['pairs_with_small_diff']}")
    
    return {
        'common_pairs': len(common_pairs),
        'old_only': len(old_only),
        'new_only': len(new_only),
        'correlation': correlation,
        'differences': diff_stats,
        'comparison_data': comparison_df
    }

def create_visualizations(comparison_results: dict, output_dir: Path):
    """Create comparison visualizations."""
    if comparison_results['correlation'] is None:
        print("   âš ï¸  Skipping visualizations - no common data to compare")
        return
    
    print(f"\nðŸ“Š Creating visualizations in: {output_dir}")
    output_dir.mkdir(exist_ok=True)
    
    comparison_df = comparison_results['comparison_data']
    
    # Set up the plotting style
    plt.style.use('default')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Similarity Matrix Comparison Analysis', fontsize=16, fontweight='bold')
    
    # 1. Scatter plot of old vs new similarities
    axes[0, 0].scatter(comparison_df['old_similarity'], comparison_df['new_similarity'], 
                       alpha=0.6, s=1)
    axes[0, 0].plot([0, 1], [0, 1], 'r--', alpha=0.8)
    axes[0, 0].set_xlabel('Old Similarity')
    axes[0, 0].set_ylabel('New Similarity')
    axes[0, 0].set_title(f'Similarity Correlation (r={comparison_results["correlation"]:.3f})')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Difference distribution
    axes[0, 1].hist(comparison_df['difference'], bins=50, alpha=0.7, edgecolor='black')
    axes[0, 1].axvline(comparison_df['difference'].mean(), color='red', linestyle='--', 
                       label=f'Mean: {comparison_df["difference"].mean():.4f}')
    axes[0, 1].set_xlabel('Similarity Difference (New - Old)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Distribution of Similarity Differences')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Absolute difference distribution
    axes[1, 0].hist(comparison_df['abs_difference'], bins=50, alpha=0.7, 
                    edgecolor='black', color='orange')
    axes[1, 0].axvline(comparison_df['abs_difference'].mean(), color='red', linestyle='--',
                       label=f'Mean: {comparison_df["abs_difference"].mean():.4f}')
    axes[1, 0].set_xlabel('Absolute Similarity Difference')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Distribution of Absolute Differences')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Box plot of similarities
    data_to_plot = [comparison_df['old_similarity'], comparison_df['new_similarity']]
    box_plot = axes[1, 1].boxplot(data_to_plot, labels=['Old Matrix', 'New Matrix'], patch_artist=True)
    box_plot['boxes'][0].set_facecolor('lightblue')
    box_plot['boxes'][1].set_facecolor('lightgreen')
    axes[1, 1].set_ylabel('Similarity Score')
    axes[1, 1].set_title('Similarity Score Distributions')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'similarity_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create a detailed difference analysis plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Sample data for readability if too many points
    if len(comparison_df) > 10000:
        sample_df = comparison_df.sample(n=10000, random_state=42)
    else:
        sample_df = comparison_df
    
    scatter = ax.scatter(sample_df['old_similarity'], sample_df['abs_difference'], 
                        c=sample_df['new_similarity'], cmap='viridis', alpha=0.6, s=1)
    ax.set_xlabel('Old Similarity Score')
    ax.set_ylabel('Absolute Difference')
    ax.set_title('Difference Magnitude vs Original Similarity\n(Color = New Similarity)')
    plt.colorbar(scatter, label='New Similarity')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'difference_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"   âœ… Saved: similarity_comparison.png")
    print(f"   âœ… Saved: difference_analysis.png")

def find_extreme_changes(comparison_results: dict, top_n: int = 20) -> dict:
    """Find job pairs with the most extreme changes."""
    if comparison_results['correlation'] is None:
        return {}
    
    comparison_df = comparison_results['comparison_data']
    
    # Largest increases
    largest_increases = comparison_df.nlargest(top_n, 'difference')[
        ['old_similarity', 'new_similarity', 'difference', 'percent_change']
    ]
    
    # Largest decreases
    largest_decreases = comparison_df.nsmallest(top_n, 'difference')[
        ['old_similarity', 'new_similarity', 'difference', 'percent_change']
    ]
    
    # Largest absolute changes
    largest_abs_changes = comparison_df.nlargest(top_n, 'abs_difference')[
        ['old_similarity', 'new_similarity', 'difference', 'abs_difference']
    ]
    
    print(f"\nðŸ” Top {top_n} Largest Increases in Similarity:")
    for idx, row in largest_increases.iterrows():
        job_a, job_b = idx.split('|')
        print(f"   {job_a} â†” {job_b}")
        print(f"      Old: {row['old_similarity']:.4f} â†’ New: {row['new_similarity']:.4f} "
              f"(+{row['difference']:.4f}, +{row['percent_change']:.1f}%)")
    
    print(f"\nðŸ”» Top {top_n} Largest Decreases in Similarity:")
    for idx, row in largest_decreases.iterrows():
        job_a, job_b = idx.split('|')
        print(f"   {job_a} â†” {job_b}")
        print(f"      Old: {row['old_similarity']:.4f} â†’ New: {row['new_similarity']:.4f} "
              f"({row['difference']:.4f}, {row['percent_change']:.1f}%)")
    
    return {
        'largest_increases': largest_increases,
        'largest_decreases': largest_decreases,
        'largest_abs_changes': largest_abs_changes
    }

def save_comparison_report(old_stats: dict, new_stats: dict, comparison_results: dict, 
                          extreme_changes: dict, output_dir: Path):
    """Save a comprehensive comparison report."""
    report = {
        'comparison_timestamp': datetime.now().isoformat(),
        'old_matrix_stats': old_stats,
        'new_matrix_stats': new_stats,
        'comparison_results': {
            'common_pairs': comparison_results['common_pairs'],
            'old_only': comparison_results['old_only'],
            'new_only': comparison_results['new_only'],
            'correlation': comparison_results['correlation'],
            'differences': comparison_results['differences']
        },
        'extreme_changes_summary': {
            'largest_increases_count': len(extreme_changes.get('largest_increases', [])),
            'largest_decreases_count': len(extreme_changes.get('largest_decreases', [])),
            'largest_abs_changes_count': len(extreme_changes.get('largest_abs_changes', []))
        }
    }
    
    report_file = output_dir / 'comparison_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nðŸ“„ Saved comprehensive report: {report_file}")

def main():
    parser = argparse.ArgumentParser(description='Compare two similarity matrices')
    parser.add_argument('--old', type=str, 
                       default='models/2025-Q2/precompute_20250613/job_similarity_matrix.parquet',
                       help='Path to old similarity matrix')
    parser.add_argument('--new', type=str,
                       default='models/2025-Q2_20250617/precompute_20250617/job_similarity_matrix.parquet',
                       help='Path to new similarity matrix')
    parser.add_argument('--output', type=str, default='comparison_output',
                       help='Output directory for results')
    parser.add_argument('--top-changes', type=int, default=20,
                       help='Number of top changes to display')
    
    args = parser.parse_args()
    
    # Convert to Path objects
    old_path = Path(args.old)
    new_path = Path(args.new)
    output_dir = Path(args.output)
    
    print("=" * 60)
    print("ðŸ” SIMILARITY MATRIX COMPARISON")
    print("=" * 60)
    print(f"Old matrix: {old_path}")
    print(f"New matrix: {new_path}")
    print(f"Output directory: {output_dir}")
    
    try:
        # Load matrices
        old_df = load_similarity_matrix(old_path)
        new_df = load_similarity_matrix(new_path)
        
        # Analyze basic statistics
        old_stats = analyze_basic_stats(old_df, "Old Matrix")
        new_stats = analyze_basic_stats(new_df, "New Matrix")
        
        # Compare matrices
        comparison_results = compare_matrices(old_df, new_df)
        
        # Create output directory
        output_dir.mkdir(exist_ok=True)
        
        # Create visualizations
        create_visualizations(comparison_results, output_dir)
        
        # Find extreme changes
        extreme_changes = find_extreme_changes(comparison_results, args.top_changes)
        
        # Save comprehensive report
        save_comparison_report(old_stats, new_stats, comparison_results, 
                              extreme_changes, output_dir)
        
        print("\n" + "=" * 60)
        print("âœ… COMPARISON COMPLETE!")
        print("=" * 60)
        print(f"ðŸ“ Results saved to: {output_dir}")
        print(f"ðŸ“Š Visualizations: similarity_comparison.png, difference_analysis.png")
        print(f"ðŸ“„ Report: comparison_report.json")
        
    except Exception as e:
        print(f"\nâŒ Error during comparison: {e}")
        raise

if __name__ == "__main__":
    main() 
