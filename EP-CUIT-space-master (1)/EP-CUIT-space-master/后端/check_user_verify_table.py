import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "mapuser",
    "password": "123456",
    "database": "compus",
    "charset": "utf8mb4"
}

def check_user_verify_table():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # Check if user_verify table exists
        cursor.execute("SHOW TABLES LIKE 'user_verify'")
        result = cursor.fetchone()
        
        if result:
            print("[OK] user_verify table exists!")
            
            # Show table structure
            print("\n[Table Structure]:")
            cursor.execute("DESCRIBE user_verify")
            columns = cursor.fetchall()
            for col in columns:
                null_str = "NULL" if col['Null'] == 'YES' else "NOT NULL"
                print(f"  {col['Field']} - {col['Type']} - {null_str} - {col['Key']} - {col['Default'] or '-'}")
            
            # Check data count
            cursor.execute("SELECT COUNT(*) as count FROM user_verify")
            count_result = cursor.fetchone()
            print(f"\n[Data Count]: {count_result['count']} records")
            
            # Show recent records
            if count_result['count'] > 0:
                print("\n[Recent Records]:")
                cursor.execute("SELECT * FROM user_verify ORDER BY create_time DESC LIMIT 3")
                records = cursor.fetchall()
                for i, record in enumerate(records, 1):
                    status_text = "Pending" if record['status'] == 0 else "Approved" if record['status'] == 1 else "Rejected"
                    print(f"\nRecord {i}:")
                    print(f"  verify_id: {record['verify_id']}")
                    print(f"  user_id: {record['user_id']}")
                    print(f"  real_name: {record['real_name']}")
                    print(f"  identity: {record['identity']}")
                    print(f"  status: {record['status']} ({status_text})")
                    print(f"  create_time: {record['create_time']}")
        else:
            print("[ERROR] user_verify table does NOT exist!")
            
            # Show all tables in database
            print("\n[All Tables in Database]:")
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            for table in tables:
                table_name = list(table.values())[0]
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()['count']
                print(f"  - {table_name} ({count} records)")
                
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_user_verify_table()
