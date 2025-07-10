import sqlite3
import os

for db_file in ['user_data/wealth_lite.db', 'user_data/wealth_lite_dev.db']:
    print(f"\n=== Checking {db_file} ===")
    
    if os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print("Current tables:", tables)
        
        # Check if portfolio_snapshots table exists
        if 'portfolio_snapshots' in tables:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(portfolio_snapshots)").fetchall()]
            print("portfolio_snapshots columns:", columns)
        else:
            print("portfolio_snapshots table does not exist")
        
        conn.close()
    else:
        print("Database file does not exist") 