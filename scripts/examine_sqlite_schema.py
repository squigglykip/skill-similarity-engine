#!/usr/bin/env python3
"""
Examine SQLite Schema for NAB Skill Similarity Engine
==================================================

This script examines the business_context.sqlite database schema
and provides detailed information about tables, columns, and sample data.

Usage:
    python scripts/examine_sqlite_schema.py
"""

import sqlite3
import os
import sys
from pathlib import Path

def main():
    """Main function to examine the SQLite database schema."""
    
    # Get the database path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("Please ensure the database has been created using the CLI tools.")
        sys.exit(1)
    
    print("🔍 NAB Skills Intelligence Platform - Database Schema Analysis")
    print("=" * 70)
    print(f"📍 Database Location: {db_path}")
    print(f"📊 Database Size: {db_path.stat().st_size / (1024*1024):.1f} MB")
    print()
    
    # Connect to database
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables:")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        print()
        
        # Examine each table in detail
        for table_name in tables:
            examine_table(cursor, table_name)
            print()
        
        # Show some key relationships
        print("🔗 Key Database Relationships:")
        print("=" * 50)
        show_relationships(cursor)
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

def examine_table(cursor, table_name):
    """Examine a specific table in detail."""
    
    print(f"📊 Table: {table_name}")
    print("-" * (len(table_name) + 10))
    
    # Get table info (columns, types, etc.)
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    print("Columns:")
    for col in columns:
        col_id, col_name, col_type, not_null, default_value, is_pk = col
        pk_indicator = " (PK)" if is_pk else ""
        not_null_indicator = " NOT NULL" if not_null else ""
        default_indicator = f" DEFAULT {default_value}" if default_value else ""
        print(f"  • {col_name}: {col_type}{pk_indicator}{not_null_indicator}{default_indicator}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    row_count = cursor.fetchone()[0]
    print(f"📈 Row Count: {row_count:,}")
    
    # Show sample data (first 3 rows)
    if row_count > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
        sample_rows = cursor.fetchall()
        
        if sample_rows:
            print("🔍 Sample Data (first 3 rows):")
            col_names = [desc[0] for desc in cursor.description]
            
            # Print header
            header = " | ".join([f"{name:<12}" for name in col_names[:5]])  # Limit to first 5 cols for readability
            print(f"  {header}")
            print(f"  {'-' * len(header)}")
            
            # Print sample rows
            for row in sample_rows:
                row_data = " | ".join([f"{str(val):<12}" for val in row[:5]])  # Limit to first 5 cols
                print(f"  {row_data}")
            
            if len(col_names) > 5:
                print(f"  ... ({len(col_names) - 5} more columns)")

def show_relationships(cursor):
    """Show key relationships and business insights."""
    
    # Check foreign key relationships
    print("🔗 Foreign Key Relationships:")
    
    # Get all foreign keys
    tables = ["jobs", "job_similarities", "positions", "position_job_mapping", "skills", "job_skills"]
    
    for table in tables:
        try:
            cursor.execute(f"PRAGMA foreign_key_list({table});")
            fks = cursor.fetchall()
            if fks:
                print(f"  {table}:")
                for fk in fks:
                    _, _, ref_table, from_col, to_col, _, _, _ = fk
                    print(f"    • {from_col} → {ref_table}.{to_col}")
        except sqlite3.Error:
            continue
    
    print()
    
    # Show some business insights
    print("💼 Business Context Analysis:")
    
    try:
        # Job families
        cursor.execute("SELECT JobFamily, COUNT(*) as count FROM jobs GROUP BY JobFamily ORDER BY count DESC LIMIT 5;")
        job_families = cursor.fetchall()
        print("  Top Job Families:")
        for family, count in job_families:
            print(f"    • {family}: {count} jobs")
        
        print()
        
        # Similarity score distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN similarity_score >= 0.8 THEN 'High (0.8+)'
                    WHEN similarity_score >= 0.6 THEN 'Medium (0.6-0.8)'
                    WHEN similarity_score >= 0.4 THEN 'Low (0.4-0.6)'
                    ELSE 'Very Low (<0.4)'
                END as similarity_range,
                COUNT(*) as count
            FROM job_similarities 
            GROUP BY similarity_range 
            ORDER BY MIN(similarity_score) DESC;
        """)
        similarity_dist = cursor.fetchall()
        print("  Similarity Score Distribution:")
        for range_name, count in similarity_dist:
            print(f"    • {range_name}: {count:,} pairs")
        
        print()
        
        # Position distribution
        cursor.execute("SELECT Division, COUNT(*) as count FROM positions GROUP BY Division ORDER BY count DESC LIMIT 5;")
        divisions = cursor.fetchall()
        print("  Top Divisions by Position Count:")
        for division, count in divisions:
            print(f"    • {division}: {count} positions")
        
        print()
        
        # Skills categories
        cursor.execute("SELECT Category, COUNT(*) as count FROM skills GROUP BY Category ORDER BY count DESC LIMIT 5;")
        skill_categories = cursor.fetchall()
        print("  Top Skill Categories:")
        for category, count in skill_categories:
            print(f"    • {category}: {count} skills")
            
    except sqlite3.Error as e:
        print(f"  ⚠️ Could not generate business insights: {e}")

if __name__ == "__main__":
    main() 