#!/usr/bin/env python3
"""
Check actual location and region values in the database.
"""

import sqlite3

# Connect to database
conn = sqlite3.connect("models/2025-Q2/business_context.sqlite")
conn.row_factory = sqlite3.Row

print("🌍 AVAILABLE LOCATION VALUES:")
print("=" * 40)
cursor = conn.execute("SELECT DISTINCT Location FROM positions WHERE Location IS NOT NULL ORDER BY Location")
locations = cursor.fetchall()
for i, loc in enumerate(locations, 1):
    print(f"   {i:2d}. {loc['Location']}")

print()
print("🗺️  AVAILABLE REGION VALUES:")
print("=" * 40)
cursor = conn.execute("SELECT DISTINCT Rg FROM positions WHERE Rg IS NOT NULL ORDER BY Rg")
regions = cursor.fetchall()
for i, reg in enumerate(regions, 1):
    print(f"   {i:2d}. {reg['Rg']}")

print()
print("🔍 CHECKING SPECIFIC TEST VALUES:")
print("=" * 40)

# Check Brisbane City
brisbane_count = conn.execute("SELECT COUNT(*) as count FROM positions WHERE Location = 'Brisbane City'").fetchone()
print(f"   Positions with Location = 'Brisbane City': {brisbane_count['count']}")

# Check NSW region
nsw_count = conn.execute("SELECT COUNT(*) as count FROM positions WHERE Rg = 'NSW'").fetchone()
print(f"   Positions with Region = 'NSW': {nsw_count['count']}")

# Check what locations exist that contain "Brisbane"
brisbane_like = conn.execute("SELECT DISTINCT Location FROM positions WHERE Location LIKE '%Brisbane%'").fetchall()
print(f"   Locations containing 'Brisbane': {[loc['Location'] for loc in brisbane_like]}")

conn.close() 