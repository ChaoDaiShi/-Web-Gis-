import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def check_tables():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # List all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"[OK] Found {len(tables)} tables in database:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
            
            # Show row count for each table
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]
            print(f"    Rows: {count}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_tables()
