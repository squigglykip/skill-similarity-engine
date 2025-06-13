#!/usr/bin/env python3
"""
Quick Schema Check
==================
Check the actual column names in the database to fix our SQL queries.
"""

import sqlite3
from pathlib import Path

def main():
    # Database path
    db_path = Path(__file__).parent.parent.parent.parent / 'models' / '2025-Q2' / 'business_context.sqlite'
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    print("🔍 Checking actual database schema...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n📁 Found {len(tables)} tables:")
    
    for table in tables:
        table_name = table[0]
        print(f"\n🗂️  Table: {table_name}")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            pk_marker = " (PK)" if pk else ""
            print(f"   📄 {col_name} ({col_type}){pk_marker}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"   📊 Rows: {count:,}")
    
    # Check a few sample records from jobs table to understand the data
    print(f"\n🔍 Sample data from jobs table:")
    cursor.execute("SELECT * FROM jobs LIMIT 3;")
    sample_jobs = cursor.fetchall()
    
    if sample_jobs:
        # Get column names for jobs table
        cursor.execute("PRAGMA table_info(jobs);")
        job_columns = [col[1] for col in cursor.fetchall()]
        
        for i, job in enumerate(sample_jobs):
            print(f"\n   Job {i+1}:")
            for col_name, value in zip(job_columns, job):
                print(f"     {col_name}: {value}")
    
    conn.close()

if __name__ == '__main__':
    main() 