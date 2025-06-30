# 🚀 NAB Skills Intelligence Platform - Quick Start Guide

## Double-Click Startup Experience

### For Windows Users

**Simply double-click `start_webapp.bat`** in the project root directory!

The startup script will automatically:
- ✅ Check for Python installation
- ✅ Launch the webapp (which installs packages sequentially)
- ✅ Start the webapp server
- ✅ Open your browser automatically

### What You'll See

1. **Welcome Banner** - Professional startup display
2. **Package Installation** - Automatic installation from requirements.txt
3. **Database Validation** - Ensures business context database exists
4. **⚠️ CRITICAL WARNING** - Big notice about keeping the window open
5. **Server Startup** - Flask development server launches
6. **Browser Opens** - Automatically opens http://localhost:5000

### ⚠️ IMPORTANT: Keep Command Window Open!

**DO NOT CLOSE THE COMMAND WINDOW** while using the webapp!

- 🚫 **Closing the window = Webapp stops working**
- ✅ **Keep window open = Webapp keeps running**
- 💡 **Can minimize the window** if it's in the way
- 🛑 **To stop properly**: Press `Ctrl+C` in the command window

### If Something Goes Wrong

#### Missing Python
```
[ERROR] Python is not installed or not in PATH
```
**Solution:** Install Python 3.8+ from https://python.org and add to PATH

#### Missing Database
```
❌ Database not found!
```
**Solution:** 
1. Run: `python main.py`
2. Select option 2: 'Generate Business Context Database'
3. Wait for completion, then restart webapp

#### Package Installation Issues
```
❌ Missing required packages
```
**Solution:** The startup script will try to install them automatically, or run:
```bash
pip install flask pandas numpy
```

### Manual Startup (Alternative)

If the .bat file doesn't work, you can start manually:

```bash
# Navigate to project directory
cd skill-similarity-engine

# Install requirements (system Python)
pip install -r requirements.txt

# Start webapp
python run_webapp.py
```

### Available Applications

Once started, you can access:

- 🏠 **Homepage**: http://localhost:5000/
- 🔍 **Job Search**: http://localhost:5000/job-search
- 📊 **Similarity Results**: http://localhost:5000/similarity-results
- 🛤️ **Career Pathways**: http://localhost:5000/career-pathways
- 📈 **Career Analysis**: http://localhost:5000/career-analysis
- 🧩 **Components**: http://localhost:5000/components

### Stopping the Server

- Press `Ctrl+C` in the command window
- Or simply close the command window

---

## 🎯 Professional Workforce Planning

This platform provides:
- **Career Transition Analysis** - Strategic workforce planning
- **Skills-Based Hiring Intelligence** - Data-driven recruitment
- **Real-Time Similarity Matching** - Pathway discovery
- **Mobility Insights** - Internal talent optimization

---

*For technical support or advanced configuration, please refer to the main project documentation.* 