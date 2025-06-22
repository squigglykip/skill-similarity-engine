"""
Visualization generation using matplotlib/seaborn for white papers.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import io
from typing import Dict, Any
import numpy as np

class VisualizationGenerator:
    """Generates charts and visualizations for white paper documents."""
    
    def __init__(self):
        # Set NAB color palette
        self.nab_colors = {
            'primary': '#2E8B57',      # NAB Green
            'secondary': '#1C1C1C',    # NAB Dark Grey
            'accent': '#FF6B6B',       # Red for gaps
            'neutral': '#4169E1'       # Blue for neutral
        }
        
        # Configure matplotlib for NAB styling
        plt.style.use('seaborn-v0_8')
        sns.set_palette([self.nab_colors['primary'], self.nab_colors['accent'], 
                        self.nab_colors['neutral'], self.nab_colors['secondary']])
    
    def create_skills_gap_chart(self, skills_data: Dict) -> io.BytesIO:
        """Create skills gap analysis chart."""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Skills overlap bar chart
        categories = ['Shared Skills', 'Skills to Develop', 'Transferable Only']
        values = [
            skills_data.get('shared_skills', 0),
            skills_data.get('skills_to_develop', 0),
            skills_data.get('transferable_skills', 0)
        ]
        
        ax1.bar(categories, values, color=[self.nab_colors['primary'], 
                                          self.nab_colors['accent'], 
                                          self.nab_colors['neutral']])
        ax1.set_title('Skills Gap Analysis', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Number of Skills')
        
        # Development priority heatmap (placeholder data)
        priority_data = np.random.rand(5, 3)  # TODO: Use real priority data
        sns.heatmap(priority_data, ax=ax2, cmap='RdYlGn_r', annot=True, 
                   xticklabels=['Importance', 'Difficulty', 'Timeline'],
                   yticklabels=[f'Skill {i+1}' for i in range(5)])
        ax2.set_title('Development Priority Matrix', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_stream = io.BytesIO()
        plt.savefig(img_stream, format='png', bbox_inches='tight', dpi=300)
        img_stream.seek(0)
        plt.close()
        
        return img_stream
    
    def create_similarity_comparison(self, similarity_data: Dict) -> io.BytesIO:
        """Create similarity score comparison chart."""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # TODO: Use real similarity data
        jobs = ['Target Job 1', 'Target Job 2', 'Target Job 3']
        similarities = [0.78, 0.65, 0.52]
        
        bars = ax.barh(jobs, similarities, color=self.nab_colors['primary'])
        ax.set_xlabel('Similarity Score')
        ax.set_title('Job Similarity Comparison', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 1)
        
        # Add percentage labels
        for i, (bar, score) in enumerate(zip(bars, similarities)):
            ax.text(score + 0.02, i, f'{score:.1%}', va='center')
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_stream = io.BytesIO()
        plt.savefig(img_stream, format='png', bbox_inches='tight', dpi=300)
        img_stream.seek(0)
        plt.close()
        
        return img_stream
    
    def create_pathway_timeline(self, timeline_data: Dict) -> io.BytesIO:
        """Create development pathway timeline chart."""
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # TODO: Use real timeline data
        phases = ['Assessment', 'Development', 'Transition', 'Integration']
        durations = [2, 12, 4, 6]  # weeks
        
        # Create Gantt-style chart
        start_positions = [0]
        for i in range(1, len(durations)):
            start_positions.append(start_positions[i-1] + durations[i-1])
        
        bars = ax.barh(phases, durations, left=start_positions, 
                      color=self.nab_colors['primary'], alpha=0.7)
        
        ax.set_xlabel('Timeline (Weeks)')
        ax.set_title('Development Pathway Timeline', fontsize=14, fontweight='bold')
        
        # Add duration labels
        for i, (bar, duration) in enumerate(zip(bars, durations)):
            ax.text(start_positions[i] + duration/2, i, f'{duration}w', 
                   ha='center', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Save to BytesIO
        img_stream = io.BytesIO()
        plt.savefig(img_stream, format='png', bbox_inches='tight', dpi=300)
        img_stream.seek(0)
        plt.close()
        
        return img_stream
