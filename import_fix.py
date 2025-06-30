#!/usr/bin/env python3
"""
Import Fix for NAB Skills Intelligence Platform
===============================================

This script fixes import issues that occur when the webapp is deployed 
across different environments. Run this script before starting the webapp
to ensure proper module resolution.

Usage:
    python import_fix.py
    
Then start the webapp normally:
    python run_webapp.py
"""

import sys
import os
from pathlib import Path

def fix_python_path():
    """Fix Python path to ensure proper module imports."""
    
    # Get the current directory (where this script is located)
    current_dir = Path(__file__).parent.absolute()
    
    # Add the src directory to Python path
    src_dir = current_dir / 'src'
    if src_dir.exists():
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
            print(f"✅ Added to Python path: {src_dir}")
    
    # Add the career_analysis directory to Python path  
    career_analysis_dir = current_dir / 'src' / 'skill_similarity_engine' / 'webapp' / 'career_analysis'
    if career_analysis_dir.exists():
        if str(career_analysis_dir) not in sys.path:
            sys.path.insert(0, str(career_analysis_dir))
            print(f"✅ Added to Python path: {career_analysis_dir}")
    
    # Set environment variable to help with imports
    os.environ['PYTHONPATH'] = os.pathsep.join(sys.path)
    
    print("🔧 Python path configuration completed")
    print("📋 Current Python path includes:")
    for i, path in enumerate(sys.path[:5]):  # Show first 5 paths
        print(f"   {i+1}. {path}")
    if len(sys.path) > 5:
        print(f"   ... and {len(sys.path) - 5} more paths")

def test_imports():
    """Test that critical imports work correctly."""
    
    print("\n🧪 Testing critical imports...")
    
    # Test 1: ContentFormatter import
    try:
        from skill_similarity_engine.webapp.career_analysis.formatter import ContentFormatter
        print("✅ ContentFormatter import: SUCCESS")
    except ImportError as e:
        print(f"❌ ContentFormatter import: FAILED - {e}")
    
    # Test 2: DocumentFormatter import  
    try:
        from skill_similarity_engine.webapp.career_analysis.formatter import DocumentFormatter
        print("✅ DocumentFormatter import: SUCCESS")
    except ImportError as e:
        print(f"❌ DocumentFormatter import: FAILED - {e}")
    
    # Test 3: Career Analysis Service import
    try:
        from skill_similarity_engine.webapp.career_analysis.services.career_analysis_service import CareerAnalysisService
        print("✅ CareerAnalysisService import: SUCCESS")
    except ImportError as e:
        print(f"❌ CareerAnalysisService import: FAILED - {e}")
        
    print("\n📝 Import testing completed")

def create_startup_script():
    """Create a startup script that applies the fix automatically."""
    
    startup_script = Path(__file__).parent / 'start_webapp_fixed.py'
    
    startup_content = '''#!/usr/bin/env python3
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
'''
    
    with open(startup_script, 'w', encoding='utf-8') as f:
        f.write(startup_content)
    
    print(f"📝 Created fixed startup script: {startup_script}")
    print("💡 Your coworker can use: python start_webapp_fixed.py")

if __name__ == '__main__':
    print("🔧 NAB Skills Intelligence Platform - Import Fix")
    print("=" * 50)
    
    fix_python_path()
    test_imports() 
    create_startup_script()
    
    print("\n🎯 SOLUTION FOR YOUR COWORKER:")
    print("=" * 40)
    print("1. Run this import fix script:")
    print("   python import_fix.py")
    print()
    print("2. Then use the fixed startup script:")
    print("   python start_webapp_fixed.py")
    print()
    print("3. Or manually run the original after the fix:")
    print("   python run_webapp.py")
    print()
    print("✅ This should resolve the ContentFormatter import errors!") 