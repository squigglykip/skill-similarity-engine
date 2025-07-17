import sqlite3

def main():
    conn = sqlite3.connect('models/2025-Q3/workforce_intelligence.sqlite')
    cursor = conn.cursor()
    
    # Query positions table
    cursor.execute('SELECT "Position Number" FROM positions LIMIT 10')
    print('Position Numbers from positions table:')
    for row in cursor.fetchall():
        print(row[0])
    
    # Query position_history table
    cursor.execute('SELECT position_number FROM position_history LIMIT 10')
    print('\nPosition Numbers from position_history table:')
    for row in cursor.fetchall():
        print(row[0])
    
    # Get count of each table
    cursor.execute('SELECT COUNT(*) FROM positions')
    positions_count = cursor.fetchone()[0]
    print(f'\nTotal positions in positions table: {positions_count:,}')
    
    cursor.execute('SELECT COUNT(*) FROM position_history')
    history_count = cursor.fetchone()[0]
    print(f'Total positions in position_history table: {history_count:,}')
    
    # Get unique position numbers from positions table
    cursor.execute('SELECT DISTINCT "Position Number" FROM positions')
    unique_positions = [row[0] for row in cursor.fetchall()]
    print(f'\nUnique position numbers in positions table: {len(unique_positions):,}')
    print(f'Sample unique positions: {unique_positions[:10]}')
    
    # Check JobProfileID relationship
    cursor.execute('SELECT "Position Number", JobProfileID FROM positions LIMIT 10')
    print('\nPosition Number -> JobProfileID mapping:')
    for row in cursor.fetchall():
        print(f'{row[0]} -> {row[1]}')
    
    # Get unique JobProfileIDs
    cursor.execute('SELECT DISTINCT JobProfileID FROM positions WHERE JobProfileID IS NOT NULL')
    unique_job_profiles = [row[0] for row in cursor.fetchall()]
    print(f'\nUnique JobProfileIDs in positions table: {len(unique_job_profiles):,}')
    print(f'Sample JobProfileIDs: {unique_job_profiles[:10]}')
    
    conn.close()

if __name__ == "__main__":
    main() 