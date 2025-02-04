import mysql.connector
from core.config import Config

def get_db_connection():
    """ 取得 MySQL 連線 """
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )

def init_db():
    """ 初始化 users 表 """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(50) PRIMARY KEY,
            consent TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def create_user_db(user_id):
    """ 
    1. 檢查用戶是否已經存在於 users 表
    2. 如果是新用戶，則建立一個專屬的聊天歷史表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 檢查 users 表是否存在
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result[0] == 0:
        # 新增用戶至 users 表
        cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        conn.commit()

        # 為該用戶建立專屬的聊天歷史表
        table_name = f"messages_{user_id.replace('-', '_')}"  # MySQL 表名不能有 "-"
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender VARCHAR(10),  /* 'user' or 'bot' */
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        conn.commit()

    conn.close()

def check_user_consent(user_id):
    """ 檢查用戶是否已同意隱私政策 """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT consent FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None and result[0] == 1

def set_user_consent(user_id):
    """ 設定使用者已同意隱私政策 """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, consent) 
        VALUES (%s, 1) 
        ON DUPLICATE KEY UPDATE consent=1
    ''', (user_id,))
    conn.commit()
    conn.close()
