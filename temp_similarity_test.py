import sqlite3

conn = sqlite3.connect('models/2025-Q3/business_context.sqlite')
cursor = conn.cursor()

print("Testing literal similarity thresholds:")
for threshold in [0.5, 0.6, 0.7, 0.8]:
    cursor.execute('SELECT COUNT(*) FROM analytics_job_similarities WHERE job_from = ? AND similarity_score >= ? AND similarity_score IS NOT NULL', ('R0041.4', threshold))
    count = cursor.fetchone()[0]
    print(f'Literal similarity >= {threshold}: {count} results')

conn.close()
