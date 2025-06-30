#!/usr/bin/env python3
"""
NAB Skills Intelligence Platform - Webapp Server
Professional career transition analysis and workforce planning tool
"""

import sys
import os
import subprocess
from pathlib import Path
import importlib.util

def check_and_install_requirements():
    """Check and install all required packages from requirements.txt or fallback list."""
    print("📦 Checking and installing required packages...")
    
    # Try to install from requirements.txt first
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if requirements_file.exists():
        print("   📋 Found requirements.txt - installing packages...")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-q', '-r', str(requirements_file)
            ], capture_output=True, text=True, check=True)
            print("   ✅ Successfully installed packages from requirements.txt")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Some packages from requirements.txt failed to install")
            print(f"   ⚠️  Error: {e.stderr.strip() if e.stderr else 'Unknown error'}")
            print("   🔄 Falling back to basic package installation...")
    else:
        print("   📄 No requirements.txt found - installing basic packages...")
    
    # Fallback: install essential packages individually
    essential_packages = ['flask', 'pandas', 'numpy']
    failed_packages = []
    
    for package in essential_packages:
        try:
            print(f"   📦 Installing {package}...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-q', package
            ], capture_output=True, text=True, check=True)
            print(f"   ✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {package}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"   ⚠️  Failed to install: {', '.join(failed_packages)}")
        print("   💡 The webapp may still work with existing packages")
        print("   💡 You can try installing manually: pip install " + " ".join(failed_packages))
        return False
    else:
        print("   ✅ All essential packages are installed")
        return True

def print_welcome_banner():
    """Print a professional welcome banner."""
    print("=" * 80)
    print("                    NAB SKILLS INTELLIGENCE PLATFORM")
    print("                   Professional Workforce Planning Tool")
    print("=" * 80)
    print()
    print("🎯 Career Transition Analysis & Strategic Workforce Planning")
    print("📊 Skills-Based Hiring Intelligence & Mobility Insights")
    print("🔍 Real-Time Similarity Matching & Pathway Discovery")
    print()

def print_startup_info(app):
    """Print startup information and available endpoints."""
    username = os.getenv('USERNAME', 'User')
    project_path = Path(__file__).parent.absolute()
    
    print(f"👤 User: {username}")
    print(f"📁 Project Path: {project_path}")
    print(f"🗄️  Database: {app.config['DATABASE_PATH']}")
    print()
    print("🚀 Starting Flask development server...")
    print("   🌐 Primary URL: http://localhost:5000")
    print("   🌍 Network URL: http://127.0.0.1:5000")
    print()
    print("📋 Available Applications:")
    print("   🏠 Homepage:           http://localhost:5000/")
    print("   🔍 Job Search:         http://localhost:5000/job-search")
    print("   📊 Similarity Results: http://localhost:5000/similarity-results")
    print("   🛤️  Career Pathways:   http://localhost:5000/career-pathways")
    print("   📈 Career Analysis:    http://localhost:5000/career-analysis")
    print("   🧩 Components:         http://localhost:5000/components")
    print()
    print()

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Import after path setup
try:
    from skill_similarity_engine.webapp import create_app
except ImportError as e:
    print("❌ Failed to import webapp module!")
    print(f"   Error: {e}")
    print(f"   Source path: {src_path}")
    print()
    print("🔧 Possible solutions:")
    print("   1. Ensure you're in the correct project directory")
    print("   2. Check that the 'src' directory exists")
    print("   3. Verify all source files are present")
    sys.exit(1)

if __name__ == '__main__':
    # Print welcome banner
    print_welcome_banner()
    
    # Check and install requirements
    print("🔍 Setting up system requirements...")
    if not check_and_install_requirements():
        print("❌ Setup incomplete. Some packages may be missing.")
        print("💡 The webapp may still work - proceeding with caution...")
    print()
    
    # Create Flask app
    try:
        app = create_app()
    except Exception as e:
        print("❌ Failed to create Flask application!")
        print(f"   Error: {e}")
        print()
        print("🔧 Possible solutions:")
        print("   1. Check that all source files are present")
        print("   2. Verify database configuration")
        print("   3. Ensure virtual environment is activated")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Check if database exists
    if not app.config['DATABASE_PATH'].exists():
        print("❌ Database not found!")
        print(f"   📍 Expected location: {app.config['DATABASE_PATH']}")
        print()
        print("🔧 To create the database:")
        print("   1. Run: python main.py")
        print("   2. Select option 2: 'Generate Business Context Database'")
        print("   3. Wait for completion, then restart this webapp")
        print()
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Print startup information
    print_startup_info(app)
    
    # Important warning before starting
    print("⚠️" * 30)
    print("                    *** CRITICAL WARNING ***")
    print()
    print("    🚫 DO NOT CLOSE THE COMMAND WINDOW WHILE USING THE WEBAPP!")
    print()
    print("    💡 This window must stay open for the webapp to function")
    print("    💡 Closing it will immediately stop the NAB Skills Platform")
    print("    💡 To stop properly: Press Ctrl+C in this window")
    print()
    print("⚠️" * 30)
    print()
    
    # Open browser automatically (optional)
    try:
        import webbrowser
        print("🌐 Opening browser automatically...")
        webbrowser.open('http://localhost:5000')
        print("   ✅ Browser opened")
    except Exception:
        print("   ℹ️  Could not open browser automatically")
        print("   🌐 Please manually navigate to: http://localhost:5000")
    print()
    
    print("🟢 Server is now running! You can use the webapp in your browser.")
    print("📌 Keep this window open and minimized if needed.")
    print()
    
    try:
        # Run the development server
        app.run(
            debug=False,
            port=5000,
            host='localhost',
            use_reloader=False,  # Disable auto-reload
            threaded=True  # Enable threading for better performance
        )
    except KeyboardInterrupt:
        print("\n\n" + "🛑" * 25)
        print("         SERVER STOPPED BY USER (Ctrl+C)")
        print("🛑" * 25)
        print()
        print("✅ NAB Skills Intelligence Platform stopped safely")
        print("👋 Thank you for using the platform!")
        print("💾 All data has been preserved")
    except Exception as e:
        print(f"\n\n❌ SERVER ERROR: {e}")
        print("🔧 Please check the error details above and try again")
        print("💡 You can restart by double-clicking start_webapp.bat again")
    finally:
        print("\n" + "📊" * 20)
        print("      SESSION COMPLETE - SAFE TO CLOSE")
        print("📊" * 20)
        print("\nPress Enter to close this window...")
        input() 
