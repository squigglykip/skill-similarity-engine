#!/usr/bin/env python3
import sqlite3
from pathlib import Path

# Check both possible databases
databases = [
    'models/2025-Q3/workforce_intelligence.sqlite',
    'models/2025-Q3/business_context.sqlite'
]

for db_path in databases:
    print(f"\n=== Checking {db_path} ===")
    if not Path(db_path).exists():
        print(f"❌ Database file does not exist: {db_path}")
        continue
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Database found with {len(tables)} tables")
        
        # Show job/skill related tables
        job_skill_tables = [t for t in tables if 'job' in t.lower() or 'skill' in t.lower()]
        if job_skill_tables:
            print("📊 Job/Skill tables:")
            for table in job_skill_tables:
                print(f"  - {table}")
        else:
            print("❌ No job/skill tables found")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error accessing database: {e}")