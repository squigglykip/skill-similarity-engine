#!/usr/bin/env python3
"""
Development Server Runner for Skill Similarity Engine Webapp
Quick way to start the Flask development server
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from skill_similarity_engine.webapp import create_app

if __name__ == '__main__':
    # Create Flask app
    app = create_app()
    
    # Check if database exists
    if not app.config['DATABASE_PATH'].exists():
        print("âš ï¸  Database not found!")
        print(f"   Expected location: {app.config['DATABASE_PATH']}")
        print("   Please run the CLI to generate business context database first:")
        print("   python main.py")
        print("   Then select option 2: 'Generate Business Context Database'")
        sys.exit(1)
    
    print("âœ… Database found!")
    print(f"   Location: {app.config['DATABASE_PATH']}")
    print()
    print("ðŸš€ Starting Flask development server...")
    print("   Available at: http://localhost:5000")
    print()
    print("ðŸ“‹ Available pages:")
    print("   â€¢ http://localhost:5000/                (Homepage)")
    print("   â€¢ http://localhost:5000/components      (Component Library)")
    print("   â€¢ http://localhost:5000/job-search      (Job Search)")
    print("   â€¢ http://localhost:5000/similarity-results  (Similarity Results)")
    print("   â€¢ http://localhost:5000/career-pathways (Career Pathways)")
    print()
    print("ðŸ”§ Development Mode: Auto-reload enabled")
    print("   Press Ctrl+C to stop")
    print()
    
    # Run the development server
    app.run(
        debug=True,
        port=5000,
        host='localhost',
        use_reloader=False,  # Disable auto-reload
        threaded=True  # Enable threading for better performance
    ) 
