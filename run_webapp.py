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
    """Check and install all required packages from requirements.txt with enhanced feedback."""
    print("📦 Checking and installing required packages...")
    print("   ⏳ This may take a few moments...")
    print()
    
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print("   ❌ requirements.txt not found!")
        print("   💡 Falling back to basic package installation...")
        return install_essential_packages()
    
    # Install core requirements first
    print("   📋 Installing core dependencies from requirements.txt...")
    try:
        # Install main requirements (excluding commented optional ones)
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-q', '-r', str(requirements_file),
            '--disable-pip-version-check'
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print("   ✅ Core dependencies installed successfully")
            install_optional_packages()
            return True
        else:
            print("   ⚠️  Some core packages failed to install")
            if result.stderr:
                # Show only the most relevant error info
                error_lines = result.stderr.strip().split('\n')
                relevant_errors = [line for line in error_lines if 'ERROR' in line or 'Failed' in line]
                if relevant_errors:
                    print(f"   ⚠️  Key errors: {relevant_errors[-1][:100]}...")
            print("   🔄 Trying essential packages individually...")
            return install_essential_packages()
            
    except subprocess.TimeoutExpired:
        print("   ⚠️  Installation timeout - trying essential packages only...")
        return install_essential_packages()
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Installation error - trying essential packages only...")
        return install_essential_packages()

def install_essential_packages():
    """Install only the most critical packages needed for webapp functionality."""
    print("   📦 Installing essential packages individually...")
    
    # Core packages needed for basic webapp functionality
    essential_packages = [
        ('flask', 'Flask web framework'),
        ('jinja2', 'Template engine'), 
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical computing'),
        ('pyyaml', 'Configuration files'),
        ('requests', 'HTTP requests')
    ]
    
    failed_packages = []
    success_count = 0
    
    for package, description in essential_packages:
        try:
            print(f"   📦 Installing {package} ({description})...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-q', package,
                '--disable-pip-version-check'
            ], capture_output=True, text=True, check=True, timeout=60)
            print(f"   ✅ {package} installed")
            success_count += 1
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"   ❌ Failed to install {package}")
            failed_packages.append(package)
    
    print()
    print(f"   📊 Installation Summary: {success_count}/{len(essential_packages)} essential packages installed")
    
    if failed_packages:
        print(f"   ⚠️  Failed packages: {', '.join(failed_packages)}")
        print("   💡 The webapp may still work with existing packages")
        print("   💡 Manual installation: pip install " + " ".join(failed_packages))
        return success_count >= 4  # Need at least Flask, Jinja2, pandas, numpy
    else:
        print("   ✅ All essential packages installed successfully")
        install_optional_packages()
        return True

def install_optional_packages():
    """Install optional packages that enhance functionality but aren't critical."""
    print("   🔧 Installing optional enhancement packages...")
    
    # Windows-optimized optional packages (no system library dependencies)
    optional_packages = [
        ('reportlab', 'PDF generation (Windows-optimized)'),
        ('beautifulsoup4', 'HTML parsing for documents'),
        ('scikit-learn', 'Machine learning features'),
        ('matplotlib', 'Data visualisation'),
        ('seaborn', 'Statistical plotting'),
        ('xlsxwriter', 'Excel file generation'),
        ('joblib', 'Machine learning model persistence'),
        ('xgboost', 'Advanced gradient boosting'),
        ('optuna', 'Hyperparameter optimization'),
        ('networkx', 'Network analysis'),
        ('community', 'Community detection algorithms'),
        ('html2docx', 'HTML to Word conversion'),
        ('mammoth', 'Document conversion utilities')
    ]
    
    installed_optional = []
    
    # Install Windows-optimized optional packages
    for package, description in optional_packages:
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-q', package,
                '--disable-pip-version-check'
            ], capture_output=True, text=True, check=True, timeout=60)
            installed_optional.append(package)
            print(f"   ✅ {package} installed ({description})")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"   ⚠️  Optional package {package} skipped ({description})")
    
    # Windows-specific note about PDF generation
    print("   📝 Windows PDF Generation: Using reportlab (reliable, no system dependencies)")
    print("        Advanced PDF features available through reportlab library")
    
    if installed_optional:
        print(f"   🎉 {len(installed_optional)} optional enhancements installed")
    print()

def check_optional_features():
    """Check which optional features are available and inform the user (Windows-optimized)."""
    print("🔍 Checking available Windows-compatible features...")
    
    # Windows-friendly features only
    features = {
        'PDF Generation': 'reportlab',
        'Document Processing': 'bs4',  # beautifulsoup4 imports as bs4
        'Advanced Analytics': 'sklearn',  # scikit-learn imports as sklearn
        'Data Visualisation': 'matplotlib',
        'Statistical Plotting': 'seaborn',
        'Excel Generation': 'xlsxwriter',
        'YAML Processing': 'yaml',  # PyYAML imports as yaml
        'Data Processing': 'pandas',
        'Numerical Computing': 'numpy',
        'Machine Learning Models': 'joblib',
        'Gradient Boosting': 'xgboost',
        'Hyperparameter Tuning': 'optuna',
        'Network Analysis': 'networkx',
        'Community Detection': 'community',
        'HTML to Word': 'html2docx',
        'Document Conversion': 'mammoth'
    }
    
    available_features = []
    missing_features = []
    
    for feature, package in features.items():
        try:
            __import__(package.replace('-', '_'))
            available_features.append(feature)
        except ImportError:
            missing_features.append((feature, package))
    
    print(f"   ✅ Available features: {len(available_features)}")
    for feature in available_features:
        print(f"      ✓ {feature}")
    
    if missing_features:
        print(f"   ⚠️  Missing features: {len(missing_features)} (install to enable)")
        for feature, package in missing_features:
            print(f"      • {feature} (pip install {package})")
    
    # Windows-specific notes
    print("   📝 Windows Notes:")
    print("      • PDF generation uses reportlab (no system dependencies)")
    print("      • All selected packages are Windows-compatible")
    print("      • weasyprint skipped (requires GTK+ system libraries)")
    print()

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
    print("   💡 First-time setup may take 2-3 minutes")
    print("   💡 Subsequent startups will be much faster")
    print()
    
    setup_success = check_and_install_requirements()
    
    if not setup_success:
        print("❌ Setup incomplete. Some packages may be missing.")
        print("💡 The webapp may still work with basic functionality")
        print("💡 For full features, manually install missing packages")
        print()
        # Give user option to continue or exit
        try:
            response = input("Continue with limited functionality? (y/n): ").lower().strip()
            if response != 'y' and response != 'yes':
                print("Setup cancelled by user.")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\nSetup cancelled by user.")
            sys.exit(0)
    else:
        print("✅ System requirements setup complete!")
    
    # Check and report available Windows-compatible features
    check_optional_features()
    
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
    
    # Information about the clean operation mode
    print("🌍 Production Mode: Clean console output enabled")
    print("   ℹ️  Only important messages will be shown during operation")
    print("   🔄 To see code changes: Stop (Ctrl+C) and restart this script")
    print("   📊 Server requests will not be logged to keep console clean")
    print()
    
    # Configure logging to reduce verbosity during operation
    import logging
    
    # Reduce Flask's default logging verbosity
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Set up clean logging for our app
    app_logger = logging.getLogger('skill_similarity_engine')
    app_logger.setLevel(logging.INFO)
    
    try:
        # Run the development server with Windows-compatible configuration
        if os.name == 'nt':  # Windows
            # Use more stable configuration for Windows
            app.run(
                debug=False,          # Disable debug mode to reduce console output
                port=5000,
                host='127.0.0.1',     # Use 127.0.0.1 for Windows compatibility
                use_reloader=False,   # Disable reloader on Windows to prevent socket errors
                threaded=True         # Enable threading for better performance
            )
        else:  # Unix/Linux/Mac
            # Use production-like configuration for cleaner output
            app.run(
                debug=False,          # Disable debug mode to reduce console output
                port=5000,
                host='127.0.0.1',
                use_reloader=False,   # Disable auto-reload for cleaner experience
                threaded=True
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
