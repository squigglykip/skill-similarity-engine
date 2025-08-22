#!/usr/bin/env python3
"""
Simple Webapp Launcher
======================

Quick launch script for the NAB Skills Intelligence Platform webapp.
Focuses on simplicity and auto-reload functionality.

Usage:
    python launch_webapp.py

Features:
- Auto-reload on file changes (Unix/Linux/Mac)
- Clean console output
- Simple error handling
"""

import os
import sys
from pathlib import Path

def main():
    """Launch the webapp with minimal configuration."""
    
    # Set up paths
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    
    # Add src to Python path
    sys.path.insert(0, str(src_path))
    
    try:
        # Import and create the Flask app
        from skill_similarity_engine.webapp.app import create_app
        
        app = create_app()
        
        print("🚀 NAB Skills Intelligence Platform")
        print("=" * 50)
        print(f"📂 Project: {project_root.name}")
        print(f"🌐 URL: http://127.0.0.1:5000")
        print("🔄 Auto-reload: Enabled")
        print("⏹️  Stop: Ctrl+C")
        print("=" * 50)
        print()
        
        # Launch with auto-reload
        app.run(
            debug=True,
            host='127.0.0.1',
            port=5000,
            use_reloader=True,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you're in the correct directory and dependencies are installed")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Webapp stopped by user")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
