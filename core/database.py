import mysql.connector
from core.config import Config
from datetime import datetime
from core.emotion import analyze_emotion  # 更新導入

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
                emotion VARCHAR(50) DEFAULT NULL,  /* 新增情緒欄位 */
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

def save_message(user_id, sender, message):
    """
    儲存聊天記錄到 `messages_<user_id>` 表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 轉換表名（確保 `user_id` 無非法字符）
    table_name = f"messages_{user_id.replace('-', '_')}"

    try:
        # 插入對話
        insert_query = f"INSERT INTO {table_name} (sender, message) VALUES (%s, %s)"
        cursor.execute(insert_query, (sender, message))
        conn.commit()

        # Debug 訊息
        print(f"✅ 成功插入訊息到 {table_name}：{sender} - {message}")

    except mysql.connector.Error as e:
        print(f"❌ MySQL 插入錯誤：{e}")

    finally:
        conn.close()

def fetch_chat_history(user_id, limit=10):
    """
    取得最近的聊天記錄，讓 GPT-4 可以記住對話上下文
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = f"messages_{user_id.replace('-', '_')}"

    # 取得最近的對話記錄
    query = f"""
        SELECT sender, message FROM {table_name} 
        ORDER BY timestamp DESC 
        LIMIT %s
    """
    cursor.execute(query, (limit,))
    messages = cursor.fetchall()
    conn.close()

    # 格式化對話內容
    history = []
    for sender, message in reversed(messages):  # 反轉順序，讓最舊的記錄在前
        role = "User" if sender == "user" else "Lume"
        history.append(f"{role}: {message}")

    return "\n".join(history)  # 返回對話歷史作為 GPT-4 記憶

def set_user_profile(user_id, name=None, birth_date=None, interests=None, mood=None):
    """
    更新或新增用戶的基本資料，手動提供正確的 `created_at`
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 確保 user_profile 表存在
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) DEFAULT NULL,
            birth_date DATE DEFAULT NULL,
            interests TEXT DEFAULT NULL,
            mood VARCHAR(50) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 檢查用戶是否已經存在
    cursor.execute("SELECT COUNT(*) FROM user_profile WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    current_time = datetime.now()

    if result[0] == 0:
        # 新增用戶，手動傳遞 `created_at`
        cursor.execute("""
            INSERT INTO user_profile (user_id, name, birth_date, interests, mood, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, name, birth_date, interests, mood, current_time))
    else:
        # 更新用戶資料
        update_fields = []
        update_values = []

        if name is not None:
            update_fields.append("name = %s")
            update_values.append(name)
        if birth_date is not None:
            update_fields.append("birth_date = %s")
            update_values.append(birth_date)
        if interests is not None:
            update_fields.append("interests = %s")
            update_values.append(interests)
        if mood is not None:
            update_fields.append("mood = %s")
            update_values.append(mood)

        if update_fields:
            update_query = f"UPDATE user_profile SET {', '.join(update_fields)} WHERE user_id = %s"
            update_values.append(user_id)
            cursor.execute(update_query, update_values)

    conn.commit()
    conn.close()



def get_user_profile(user_id):
    """
    取得用戶的基本資料
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, birth_date, interests, mood FROM user_profile WHERE user_id = %s
    """, (user_id,))
    result = cursor.fetchone()
    
    conn.close()

    if result:
        return {
            "name": result[0],
            "birth_date": result[1],
            "interests": result[2],
            "mood": result[3]
        }
    return None

def save_message_with_emotion(user_id, sender, message):
    """
    儲存聊天記錄到 `messages_<user_id>` 表，並記錄情緒
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 表名轉換
    table_name = f"messages_{user_id.replace('-', '_')}"

    # 分析情緒
    emotion = analyze_emotion(message) if sender == "user" else None

    try:
        # 插入對話
        insert_query = f"INSERT INTO {table_name} (sender, message, emotion) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (sender, message, emotion))
        conn.commit()

        # Debug 訊息
        print(f"✅ 成功插入訊息到 {table_name}：{sender} - {message} - {emotion}")

    except mysql.connector.Error as e:
        print(f"❌ MySQL 插入錯誤：{e}")

    finally:
        conn.close()