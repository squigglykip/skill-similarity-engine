#!/usr/bin/env python3
"""
Fixed Webapp Starter for NAB Skills Intelligence Platform
========================================================

This script automatically applies import fixes before starting the webapp.
Use this instead of run_webapp.py if you're experiencing import issues.
"""

import sys
from pathlib import Path

# Apply import fixes
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / 'src'
career_analysis_dir = current_dir / 'src' / 'skill_similarity_engine' / 'webapp' / 'career_analysis'

if src_dir.exists() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

if career_analysis_dir.exists() and str(career_analysis_dir) not in sys.path:
    sys.path.insert(0, str(career_analysis_dir))

print("🔧 Import fixes applied automatically")

# Now start the webapp normally
from skill_similarity_engine.webapp import create_app

if __name__ == '__main__':
    # Create Flask app
    app = create_app()
    
    # Check if database exists
    if not app.config['DATABASE_PATH'].exists():
        print("⚠️ Database not found!")
        print(f"   Expected location: {app.config['DATABASE_PATH']}")
        print("   Please run the CLI to generate business context database first:")
        print("   python main.py")
        print("   Then select option 2: 'Generate Business Context Database'")
        sys.exit(1)
    
    print("✅ Database found!")
    print(f"   Location: {app.config['DATABASE_PATH']}")
    print()
    print("🚀 Starting Flask development server with import fixes...")
    print("   Available at: http://localhost:5000")
    print("   Career Analysis: http://localhost:5000/career-analysis")
    print()
    print("🔧 Development Mode: Auto-reload enabled")
    print("   Press Ctrl+C to stop")
    print()
    
    # Run the development server
    app.run(
        debug=True,
        port=5000,
        host='localhost',
        use_reloader=False,  # Disable auto-reload to prevent path issues
        threaded=True  # Enable threading for better performance
    )
