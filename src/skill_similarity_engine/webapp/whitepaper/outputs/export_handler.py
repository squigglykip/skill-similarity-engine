"""
Multi-format export coordination for white paper generation.
"""

from typing import Dict, Any, List
from .word_generator import WordGenerator
from .powerpoint_generator import PowerPointGenerator
from .visualizations import VisualizationGenerator

class ExportHandler:
    """Coordinates multi-format export of white paper content."""
    
    def __init__(self):
        self.word_generator = WordGenerator()
        self.powerpoint_generator = PowerPointGenerator()
        self.viz_generator = VisualizationGenerator()
    
    def export_all_formats(self, content: Dict, analysis_data: Dict) -> Dict[str, Any]:
        """Export white paper in all available formats."""
        
        exports = {}
        
        # Generate Word document
        try:
            exports['word'] = self.word_generator.generate_document(content)
            exports['word_status'] = 'success'
        except Exception as e:
            exports['word_status'] = f'error: {str(e)}'
        
        # Generate PowerPoint summary
        try:
            exports['powerpoint'] = self.powerpoint_generator.generate_summary(content, analysis_data)
            exports['powerpoint_status'] = 'success'
        except Exception as e:
            exports['powerpoint_status'] = f'error: {str(e)}'
        
        # Generate visualizations
        try:
            exports['visualizations'] = self._generate_all_charts(analysis_data)
            exports['visualizations_status'] = 'success'
        except Exception as e:
            exports['visualizations_status'] = f'error: {str(e)}'
        
        return exports
    
    def _generate_all_charts(self, analysis_data: Dict) -> Dict[str, Any]:
        """Generate all visualization charts."""
        
        charts = {}
        
        # Skills gap chart
        charts['skills_gap'] = self.viz_generator.create_skills_gap_chart(analysis_data)
        
        # Similarity comparison chart
        charts['similarity_comparison'] = self.viz_generator.create_similarity_comparison(analysis_data)
        
        # Timeline chart
        charts['pathway_timeline'] = self.viz_generator.create_pathway_timeline(analysis_data)
        
        return charts
