#!/usr/bin/env python3
"""
Quick script to check column names in positions table.
"""

import sqlite3

# Connect to database
conn = sqlite3.connect("models/2025-Q2/business_context.sqlite")
conn.row_factory = sqlite3.Row

# Get column info
cursor = conn.execute("PRAGMA table_info(positions)")
columns = cursor.fetchall()

print("📋 POSITIONS TABLE COLUMNS:")
print("=" * 40)
for col in columns:
    print(f"   {col['cid']}: {col['name']} ({col['type']})")

print()

# Check some sample data
print("📊 SAMPLE POSITION DATA:")
print("=" * 40)
cursor = conn.execute("SELECT * FROM positions LIMIT 3")
sample_rows = cursor.fetchall()

if sample_rows:
    # Print column headers
    headers = list(sample_rows[0].keys())
    print("   " + " | ".join(headers))
    print("   " + "-" * (len(" | ".join(headers))))
    
    # Print sample data
    for row in sample_rows:
        values = [str(row[col])[:15] for col in headers]  # Truncate long values
        print("   " + " | ".join(values))

conn.close() 