import sqlite3
import os

def check_table_structure():
    db_path = 'user_data/wealth_lite_dev.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("数据库中的表:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # 检查portfolio_snapshots表结构
    print("\n=== portfolio_snapshots 表结构 ===")
    try:
        cursor.execute("PRAGMA table_info(portfolio_snapshots)")
        columns = cursor.fetchall()
        if columns:
            print("当前列:")
            for col in columns:
                print(f"  {col[1]} {col[2]} (NOT NULL: {col[3]}, DEFAULT: {col[4]}, PK: {col[5]})")
        else:
            print("表不存在")
    except Exception as e:
        print(f"检查表结构时出错: {e}")
    
    # 检查表的创建SQL
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='portfolio_snapshots'")
        result = cursor.fetchone()
        if result:
            print(f"\n表创建SQL:\n{result[0]}")
        else:
            print("\n表不存在")
    except Exception as e:
        print(f"获取创建SQL时出错: {e}")
    
    # 检查AI相关表是否存在
    print("\n=== AI相关表检查 ===")
    ai_tables = ['ai_analysis_configs', 'ai_analysis_results']
    for table_name in ai_tables:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        exists = cursor.fetchone()
        print(f"{table_name}: {'存在' if exists else '不存在'}")
    
    conn.close()

def drop_portfolio_snapshots():
    db_path = 'user_data/wealth_lite_dev.db'
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS portfolio_snapshots")
        conn.commit()
        print("portfolio_snapshots 表已删除")
    except Exception as e:
        print(f"删除表时出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_table_structure() 